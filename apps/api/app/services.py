import hashlib
import uuid
from datetime import UTC, date, datetime, timedelta
from decimal import Decimal

from fastapi import HTTPException, status
from sqlalchemy import func, select, update
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.account_mail import email_token
from app.core.security import create_token, hash_password, verify_password
from app.models import (
    AccountEmail,
    AccountStatus,
    Appointment,
    AppointmentStatus,
    AuditEvent,
    Availability,
    AvailabilityStatus,
    EmailVerificationToken,
    PasswordResetToken,
    Practitioner,
    User,
    UserRole,
)
from app.repositories import AppointmentRepository, DoctorRepository, UserRepository
from app.schemas import BookAppointmentIn, LoginIn, RegisterIn


class AuthService:
    def __init__(self, db: Session):
        self.db = db
        self.repo = UserRepository(db)

    def _audit(self, user_id: uuid.UUID, event_type: str) -> None:
        self.db.add(AuditEvent(user_id=user_id, event_type=event_type))

    def register(self, data: RegisterIn) -> tuple[User, str]:
        if self.repo.by_email(data.email):
            raise HTTPException(
                status.HTTP_409_CONFLICT, "An account with this email already exists"
            )
        try:
            user = User(
                **data.model_dump(exclude={"password", "email"}),
                email=data.email.lower(),
                password_hash=hash_password(data.password),
                account_status=(
                    AccountStatus.active if data.role == UserRole.patient else AccountStatus.pending
                ),
            )
            self.repo.add(user)
            self._audit(user.id, "account.registered")
            return user, self.request_email_verification(user.email) or ""
        except IntegrityError:
            self.db.rollback()
            raise HTTPException(
                status.HTTP_409_CONFLICT, "An account with this email already exists"
            ) from None

    def login(self, data: LoginIn) -> tuple[str, int]:
        user = self.repo.by_email(data.email)
        if not user or not verify_password(data.password, user.password_hash):
            raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Invalid email or password")
        if user.account_status == AccountStatus.suspended:
            raise HTTPException(status.HTTP_403_FORBIDDEN, "This account has been suspended")
        self._audit(user.id, "account.login")
        self.db.commit()
        return create_token(user.id, user.session_version)

    def request_password_reset(self, email: str) -> str | None:
        return self._queue_account_email(email, "password_reset")

    def request_email_verification(self, email: str) -> str | None:
        return self._queue_account_email(email, "email_verification")

    def _queue_account_email(self, email: str, kind: str) -> str | None:
        # Serialize requests for the same account across API workers.
        user = self.db.scalar(select(User).where(User.email == email.lower()).with_for_update())
        if not user or (kind == "email_verification" and user.email_verified_at is not None):
            return None
        now = datetime.now(UTC)
        model = PasswordResetToken if kind == "password_reset" else EmailVerificationToken
        recent = self.db.scalar(select(model.id).where(
            model.user_id == user.id, model.created_at > now - timedelta(seconds=60)
        ).limit(1))
        if recent:
            return None
        hourly_count = self.db.scalar(select(func.count()).select_from(model).where(
            model.user_id == user.id, model.created_at > now - timedelta(hours=1)
        )) or 0
        if hourly_count >= 5:
            return None
        self.db.execute(
            update(model)
            .where(model.user_id == user.id, model.used_at.is_(None))
            .values(used_at=now)
        )
        token_id = uuid.uuid4()
        token = email_token(kind, token_id)
        self.db.add(
            model(
                id=token_id,
                user_id=user.id,
                token_hash=hashlib.sha256(token.encode()).hexdigest(),
                expires_at=now + (
                    timedelta(minutes=30) if kind == "password_reset" else timedelta(hours=24)
                ),
            )
        )
        self.db.add(AccountEmail(id=token_id, user_id=user.id, kind=kind))
        event = (
            "password.reset_requested"
            if kind == "password_reset" else "email.verification_requested"
        )
        self._audit(user.id, event)
        self.db.commit()
        return token

    def verify_email(self, token: str) -> None:
        token_hash = hashlib.sha256(token.encode()).hexdigest()
        item = self.db.scalar(
            select(EmailVerificationToken)
            .where(EmailVerificationToken.token_hash == token_hash)
            .with_for_update()
        )
        now = datetime.now(UTC)
        if not item or item.used_at is not None:
            raise HTTPException(
                status.HTTP_400_BAD_REQUEST,
                "This verification link is invalid or has already been used",
            )
        expires_at = (
            item.expires_at if item.expires_at.tzinfo else item.expires_at.replace(tzinfo=UTC)
        )
        if expires_at <= now:
            raise HTTPException(status.HTTP_400_BAD_REQUEST, "This verification link has expired")
        user = self.db.get(User, item.user_id)
        if not user:
            raise HTTPException(status.HTTP_400_BAD_REQUEST, "This verification link is invalid")
        user.email_verified_at = now
        item.used_at = now
        self._audit(user.id, "email.verified")
        self.db.commit()

    def reset_password(self, token: str, password: str) -> None:
        token_hash = hashlib.sha256(token.encode()).hexdigest()
        item = self.db.scalar(
            select(PasswordResetToken)
            .where(PasswordResetToken.token_hash == token_hash)
            .with_for_update()
        )
        now = datetime.now(UTC)
        if not item or item.used_at is not None:
            raise HTTPException(
                status.HTTP_400_BAD_REQUEST, "This reset link is invalid or has already been used"
            )
        expires_at = (
            item.expires_at if item.expires_at.tzinfo else item.expires_at.replace(tzinfo=UTC)
        )
        if expires_at <= now:
            raise HTTPException(status.HTTP_400_BAD_REQUEST, "This reset link has expired")
        user = self.db.get(User, item.user_id)
        if not user:
            raise HTTPException(status.HTTP_400_BAD_REQUEST, "This reset link is invalid")
        user.password_hash = hash_password(password)
        user.session_version += 1
        item.used_at = now
        self._audit(user.id, "password.reset_completed")
        self.db.commit()


class DoctorService:
    def __init__(self, db: Session):
        self.db = db
        self.repo = DoctorRepository(db)

    def search(
        self,
        *,
        search: str | None,
        specialty: str | None,
        city: str | None,
        state: str | None,
        country: str | None,
        max_fee: Decimal | None,
        available_date: date | None,
        verified_only: bool,
        page: int,
        page_size: int,
        sort: str,
    ):
        q = self.repo.query(
            search, specialty, city, state, country, max_fee, available_date, verified_only
        )
        total = self.db.scalar(select(func.count()).select_from(q.subquery())) or 0
        ordering = (
            Practitioner.consultation_fee.asc()
            if sort == "fee_asc"
            else Practitioner.rating.desc()
            if sort == "rating"
            else Practitioner.created_at.desc()
        )
        return list(
            self.db.scalars(
                q.order_by(ordering).offset((page - 1) * page_size).limit(page_size)
            ).all()
        ), total

    def get(self, doctor_id: uuid.UUID) -> Practitioner:
        doctor = self.repo.get(doctor_id)
        if not doctor:
            raise HTTPException(status.HTTP_404_NOT_FOUND, "Doctor not found")
        return doctor

    def availability(self, doctor_id: uuid.UUID, start: date | None, end: date | None):
        self.get(doctor_id)
        q = select(Availability).where(
            Availability.practitioner_id == doctor_id,
            Availability.status == AvailabilityStatus.available,
        )
        if start:
            q = q.where(Availability.date >= start)
        if end:
            q = q.where(Availability.date <= end)
        return list(self.db.scalars(q.order_by(Availability.date, Availability.start_time)).all())


class AppointmentService:
    def __init__(self, db: Session):
        self.db = db
        self.repo = AppointmentRepository(db)

    def book(self, user: User, data: BookAppointmentIn) -> Appointment:
        try:
            slot = self.repo.lock_slot(data.availability_id)
            if not slot or slot.practitioner_id != data.practitioner_id:
                raise HTTPException(
                    status.HTTP_400_BAD_REQUEST, "Selected slot does not belong to this doctor"
                )
            if slot.status != AvailabilityStatus.available:
                raise HTTPException(
                    status.HTTP_409_CONFLICT, "This appointment time is no longer available"
                )
            if datetime.combine(slot.date, slot.start_time, tzinfo=UTC) <= datetime.now(UTC):
                raise HTTPException(
                    status.HTTP_409_CONFLICT, "This appointment time is no longer available"
                )
            if not self.db.get(Practitioner, data.practitioner_id):
                raise HTTPException(status.HTTP_404_NOT_FOUND, "Doctor not found")
            slot.status = AvailabilityStatus.booked
            scheduled = datetime.combine(slot.date, slot.start_time, tzinfo=UTC)
            item = Appointment(
                user_id=user.id,
                practitioner_id=data.practitioner_id,
                availability_id=slot.id,
                appointment_type=data.appointment_type,
                status=AppointmentStatus.confirmed,
                scheduled_at=scheduled,
                reason=data.reason,
            )
            self.db.add(item)
            self.db.commit()
            self.db.refresh(item)
            return item
        except IntegrityError:
            self.db.rollback()
            raise HTTPException(
                status.HTTP_409_CONFLICT, "This appointment time is no longer available"
            ) from None
        except HTTPException:
            self.db.rollback()
            raise

    def mine(self, user: User, view: str | None):
        q = self.repo.for_user(user.id)
        now = datetime.now(UTC)
        if view == "upcoming":
            q = q.where(
                Appointment.scheduled_at >= now, Appointment.status != AppointmentStatus.cancelled
            )
        elif view == "past":
            q = q.where(Appointment.scheduled_at < now)
        elif view == "cancelled":
            q = q.where(Appointment.status == AppointmentStatus.cancelled)
        return list(self.db.scalars(q.order_by(Appointment.scheduled_at.desc())).all())

    def own(self, user: User, item_id: uuid.UUID) -> Appointment:
        item = self.repo.get(item_id)
        if not item or item.user_id != user.id:
            raise HTTPException(status.HTTP_404_NOT_FOUND, "Appointment not found")
        return item

    def cancel(self, user: User, item_id: uuid.UUID) -> Appointment:
        item = self.repo.lock(item_id)
        if not item or item.user_id != user.id:
            raise HTTPException(status.HTTP_404_NOT_FOUND, "Appointment not found")
        if item.status in {AppointmentStatus.cancelled, AppointmentStatus.completed}:
            raise HTTPException(status.HTTP_409_CONFLICT, "This appointment cannot be cancelled")
        scheduled = (
            item.scheduled_at if item.scheduled_at.tzinfo else item.scheduled_at.replace(tzinfo=UTC)
        )
        if scheduled <= datetime.now(UTC):
            raise HTTPException(status.HTTP_409_CONFLICT, "Past appointments cannot be cancelled")
        slot = self.repo.lock_slot(item.availability_id)
        item.status = AppointmentStatus.cancelled
        if slot:
            slot.status = AvailabilityStatus.available
        self.db.commit()
        self.db.refresh(item)
        return item
