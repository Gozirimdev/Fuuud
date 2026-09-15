import hashlib
from datetime import UTC, date, datetime, timedelta
from decimal import Decimal

from bson import ObjectId
from fastapi import HTTPException
from pymongo.errors import DuplicateKeyError

from app.account_mail import email_token
from app.core.security import create_token, hash_password, verify_password
from app.db import Store
from app.models import (
    AccountEmail,
    AccountStatus,
    Appointment,
    AppointmentStatus,
    AuditEvent,
    Availability,
    EmailVerificationToken,
    PasswordResetToken,
    Practitioner,
    User,
    UserRole,
)
from app.repositories import DoctorRepository, UserRepository
from app.schemas import BookAppointmentIn, LoginIn, RegisterIn


class AuthService:
    def __init__(self, db: Store):
        self.db = db
        self.repo = UserRepository(db)

    def _audit(self, user_id: str, event_type: str) -> None:
        self.db.insert(AuditEvent(user_id=user_id, event_type=event_type))

    def register(self, data: RegisterIn) -> tuple[User, str]:
        user = User(
            **data.model_dump(exclude={"password", "email"}),
            email=data.email,
            password_hash=hash_password(data.password),
            account_status=(
                AccountStatus.active if data.role == UserRole.patient else AccountStatus.pending
            ),
        )

        def operation(db):
            service = AuthService(db)
            service.repo.add(user)
            service._audit(user.id, "account.registered")
            return user, service._queue_account_email(user.email, "email_verification") or ""

        try:
            return self.db.transaction(operation)
        except DuplicateKeyError:
            raise HTTPException(409, "An account with this email already exists") from None

    def login(self, data: LoginIn) -> tuple[str, int]:
        user = self.repo.by_email(data.email)
        if not user or not verify_password(data.password, user.password_hash):
            raise HTTPException(401, "Invalid email or password")
        if user.account_status == AccountStatus.suspended:
            raise HTTPException(403, "This account has been suspended")
        self._audit(user.id, "account.login")
        return create_token(user.id, user.session_version)

    def request_password_reset(self, email: str) -> str | None:
        return self.db.transaction(
            lambda db: AuthService(db)._queue_account_email(email, "password_reset")
        )

    def request_email_verification(self, email: str) -> str | None:
        return self.db.transaction(
            lambda db: AuthService(db)._queue_account_email(email, "email_verification")
        )

    def _queue_account_email(self, email: str, kind: str) -> str | None:
        # A write on the user serializes concurrent requests in retried transactions.
        user = self.db.claim(
            User, {"email": email.strip().lower()}, {"$inc": {"email_request_version": 1}}
        )
        if not user or (kind == "email_verification" and user.email_verified):
            return None
        now = datetime.now(UTC)
        model = PasswordResetToken if kind == "password_reset" else EmailVerificationToken
        if self.db.count(
            model, {"user_id": user.id, "created_at": {"$gt": now - timedelta(seconds=60)}}
        ):
            return None
        if (
            self.db.count(
                model, {"user_id": user.id, "created_at": {"$gt": now - timedelta(hours=1)}}
            )
            >= 5
        ):
            return None
        self.db.update(
            model, {"user_id": user.id, "used_at": None}, {"$set": {"used_at": now}}, many=True
        )
        token_id = str(ObjectId())
        token = email_token(kind, token_id)
        self.db.insert(
            model(
                id=token_id,
                user_id=user.id,
                token_hash=hashlib.sha256(token.encode()).hexdigest(),
                expires_at=now
                + (timedelta(minutes=30) if kind == "password_reset" else timedelta(hours=24)),
            )
        )
        self.db.insert(AccountEmail(id=token_id, user_id=user.id, kind=kind))
        self._audit(
            user.id,
            "password.reset_requested"
            if kind == "password_reset"
            else "email.verification_requested",
        )
        return token

    def _consume(self, token: str, model, password_hash: str | None = None):
        now = datetime.now(UTC)
        item = self.db.claim(
            model,
            {
                "token_hash": hashlib.sha256(token.encode()).hexdigest(),
                "used_at": None,
                "expires_at": {"$gt": now},
            },
            {"$set": {"used_at": now}},
        )
        if not item:
            raise HTTPException(400, "This link is invalid, expired, or has already been used")
        changes = {"$set": {"updated_at": now, "email_verified_at": now}}
        if password_hash:
            changes = {
                "$set": {"updated_at": now, "password_hash": password_hash},
                "$inc": {"session_version": 1},
            }
        if not self.db.update(User, {"id": item.user_id}, changes).matched_count:
            raise HTTPException(400, "This link is invalid")
        self._audit(item.user_id, "password.reset_completed" if password_hash else "email.verified")

    def verify_email(self, token: str) -> None:
        self.db.transaction(lambda db: AuthService(db)._consume(token, EmailVerificationToken))

    def reset_password(self, token: str, password: str) -> None:
        hashed = hash_password(password)
        self.db.transaction(lambda db: AuthService(db)._consume(token, PasswordResetToken, hashed))


class DoctorService:
    def __init__(self, db: Store):
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
        query = self.repo.query(
            search, specialty, city, state, country, max_fee, available_date, verified_only
        )
        order = (
            [("consultation_fee", 1)]
            if sort == "fee_asc"
            else ([("rating", -1)] if sort == "rating" else [("created_at", -1)])
        )
        return (
            self.db.find(
                Practitioner,
                query,
                sort=order + [("_id", 1)],
                skip=(page - 1) * page_size,
                limit=page_size,
            ),
            self.db.count(Practitioner, query),
        )

    def get(self, doctor_id: str) -> Practitioner:
        doctor = self.repo.get(doctor_id)
        if not doctor:
            raise HTTPException(404, "Doctor not found")
        return doctor

    def availability(self, doctor_id: str, start: date | None, end: date | None):
        self.get(doctor_id)
        query = {"practitioner_id": doctor_id, "status": "available"}
        if start or end:
            query["date"] = {}
            if start:
                query["date"]["$gte"] = start
            if end:
                query["date"]["$lte"] = end
        return self.db.find(Availability, query, sort=[("date", 1), ("start_time", 1)])


class AppointmentService:
    def __init__(self, db: Store):
        self.db = db

    def _hydrate(self, item: Appointment) -> Appointment:
        item.practitioner = self.db.get(Practitioner, item.practitioner_id)
        return item

    def book(self, user: User, data: BookAppointmentIn) -> Appointment:
        def operation(db):
            slot = db.get(Availability, data.availability_id)
            if not slot or slot.practitioner_id != data.practitioner_id:
                raise HTTPException(400, "Selected slot does not belong to this doctor")
            scheduled = datetime.combine(slot.date, slot.start_time, tzinfo=UTC)
            if slot.status != "available" or scheduled <= datetime.now(UTC):
                raise HTTPException(409, "This appointment time is no longer available")
            doctor = db.get(Practitioner, data.practitioner_id)
            if not doctor:
                raise HTTPException(404, "Doctor not found")
            claimed = db.update(
                Availability,
                {"id": slot.id, "status": "available"},
                {"$set": {"status": "booked", "updated_at": datetime.now(UTC)}},
            )
            if not claimed.modified_count:
                raise HTTPException(409, "This appointment time is no longer available")
            item = db.insert(
                Appointment(
                    user_id=user.id,
                    practitioner_id=data.practitioner_id,
                    availability_id=slot.id,
                    appointment_type=data.appointment_type,
                    scheduled_at=scheduled,
                    reason=data.reason,
                )
            )
            item.practitioner = doctor
            return item

        try:
            return self.db.transaction(operation)
        except DuplicateKeyError:
            raise HTTPException(409, "This appointment time is no longer available") from None

    def mine(self, user: User, view: str | None):
        query = {"user_id": user.id}
        now = datetime.now(UTC)
        if view == "upcoming":
            query.update(scheduled_at={"$gte": now}, status={"$ne": "cancelled"})
        elif view == "past":
            query["scheduled_at"] = {"$lt": now}
        elif view == "cancelled":
            query["status"] = "cancelled"
        return [
            self._hydrate(item)
            for item in self.db.find(Appointment, query, sort=[("scheduled_at", -1)])
        ]

    def own(self, user: User, item_id: str) -> Appointment:
        item = self.db.find_one(Appointment, {"id": item_id, "user_id": user.id})
        if not item:
            raise HTTPException(404, "Appointment not found")
        return self._hydrate(item)

    def cancel(self, user: User, item_id: str) -> Appointment:
        def operation(db):
            item = db.find_one(Appointment, {"id": item_id, "user_id": user.id})
            if not item:
                raise HTTPException(404, "Appointment not found")
            if item.status in {AppointmentStatus.cancelled, AppointmentStatus.completed}:
                raise HTTPException(409, "This appointment cannot be cancelled")
            if item.scheduled_at <= datetime.now(UTC):
                raise HTTPException(409, "Past appointments cannot be cancelled")
            item = db.claim(
                Appointment,
                {"id": item.id, "status": item.status},
                {"$set": {"status": "cancelled", "updated_at": datetime.now(UTC)}},
            )
            if not item:
                raise HTTPException(409, "This appointment cannot be cancelled")
            db.update(
                Availability,
                {"id": item.availability_id, "status": "booked"},
                {"$set": {"status": "available", "updated_at": datetime.now(UTC)}},
            )
            return AppointmentService(db)._hydrate(item)

        return self.db.transaction(operation)
