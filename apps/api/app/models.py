import enum
import uuid
from datetime import UTC, date, datetime, time
from decimal import Decimal

from sqlalchemy import (
    CheckConstraint,
    Date,
    DateTime,
    Enum,
    ForeignKey,
    Index,
    Numeric,
    String,
    Text,
    Time,
    UniqueConstraint,
    Uuid,
    func,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db import Base


def now() -> datetime:
    return datetime.now(UTC)


class VerificationStatus(enum.StrEnum):
    pending = "pending"
    verified = "verified"
    rejected = "rejected"


class UserRole(enum.StrEnum):
    patient = "patient"
    doctor = "doctor"
    hospital_staff = "hospital_staff"
    admin = "admin"


class AccountStatus(enum.StrEnum):
    pending = "pending"
    active = "active"
    suspended = "suspended"


class AvailabilityStatus(enum.StrEnum):
    available = "available"
    booked = "booked"
    unavailable = "unavailable"


class AppointmentType(enum.StrEnum):
    online = "online"
    physical = "physical"


class AppointmentStatus(enum.StrEnum):
    pending = "pending"
    confirmed = "confirmed"
    completed = "completed"
    cancelled = "cancelled"


class TimestampMixin:
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=now)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=now, onupdate=now)


class User(TimestampMixin, Base):
    __tablename__ = "users"
    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, default=uuid.uuid4)
    first_name: Mapped[str] = mapped_column(String(80))
    last_name: Mapped[str] = mapped_column(String(80))
    email: Mapped[str] = mapped_column(String(320), unique=True, index=True)
    phone_number: Mapped[str | None] = mapped_column(String(32))
    password_hash: Mapped[str] = mapped_column(String(255))
    session_version: Mapped[int] = mapped_column(default=0)
    role: Mapped[UserRole] = mapped_column(Enum(UserRole), index=True, default=UserRole.patient)
    account_status: Mapped[AccountStatus] = mapped_column(
        Enum(AccountStatus), index=True, default=AccountStatus.active
    )
    country: Mapped[str | None] = mapped_column(String(80))
    state: Mapped[str | None] = mapped_column(String(80))
    city: Mapped[str | None] = mapped_column(String(80))
    email_verified_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    appointments: Mapped[list["Appointment"]] = relationship(back_populates="user")
    password_reset_tokens: Mapped[list["PasswordResetToken"]] = relationship(
        back_populates="user", cascade="all, delete-orphan"
    )
    email_verification_tokens: Mapped[list["EmailVerificationToken"]] = relationship(
        back_populates="user", cascade="all, delete-orphan"
    )
    audit_events: Mapped[list["AuditEvent"]] = relationship(back_populates="user")
    __table_args__ = (Index("uq_users_email_lower", func.lower(email), unique=True),)

    @property
    def email_verified(self) -> bool:
        return self.email_verified_at is not None


class AccountEmail(Base):
    __tablename__ = "account_emails"
    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True)
    user_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"), index=True
    )
    kind: Mapped[str] = mapped_column(String(32))
    status: Mapped[str] = mapped_column(String(16), default="pending")
    attempts: Mapped[int] = mapped_column(default=0)
    next_attempt_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=now)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=now)
    __table_args__ = (Index("ix_account_emails_due", "status", "next_attempt_at"),)


class PasswordResetToken(Base):
    __tablename__ = "password_reset_tokens"
    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, default=uuid.uuid4)
    user_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"), index=True
    )
    token_hash: Mapped[str] = mapped_column(String(64), unique=True, index=True)
    expires_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), index=True)
    used_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=now)
    user: Mapped[User] = relationship(back_populates="password_reset_tokens")


class EmailVerificationToken(Base):
    __tablename__ = "email_verification_tokens"
    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, default=uuid.uuid4)
    user_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"), index=True
    )
    token_hash: Mapped[str] = mapped_column(String(64), unique=True, index=True)
    expires_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), index=True)
    used_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=now)
    user: Mapped[User] = relationship(back_populates="email_verification_tokens")


class AuditEvent(Base):
    __tablename__ = "audit_events"
    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, default=uuid.uuid4)
    user_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("users.id", ondelete="RESTRICT"), index=True
    )
    event_type: Mapped[str] = mapped_column(String(80), index=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=now, index=True)
    user: Mapped[User] = relationship(back_populates="audit_events")


class Practitioner(TimestampMixin, Base):
    __tablename__ = "healthcare_practitioners"
    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, default=uuid.uuid4)
    first_name: Mapped[str] = mapped_column(String(80))
    last_name: Mapped[str] = mapped_column(String(80))
    specialty: Mapped[str] = mapped_column(String(120), index=True)
    professional_title: Mapped[str] = mapped_column(String(160))
    license_number: Mapped[str] = mapped_column(String(100), unique=True)
    country: Mapped[str] = mapped_column(String(80), index=True)
    state: Mapped[str] = mapped_column(String(80), index=True)
    city: Mapped[str] = mapped_column(String(80), index=True)
    consultation_fee: Mapped[Decimal] = mapped_column(Numeric(12, 2))
    years_of_experience: Mapped[int]
    verification_status: Mapped[VerificationStatus] = mapped_column(
        Enum(VerificationStatus), index=True, default=VerificationStatus.pending
    )
    bio: Mapped[str] = mapped_column(Text)
    rating: Mapped[Decimal] = mapped_column(Numeric(2, 1))
    profile_image_url: Mapped[str | None] = mapped_column(String(500))
    availability: Mapped[list["Availability"]] = relationship(
        back_populates="practitioner", cascade="all, delete-orphan"
    )
    appointments: Mapped[list["Appointment"]] = relationship(back_populates="practitioner")
    __table_args__ = (Index("ix_practitioner_name", "first_name", "last_name"),)


class Availability(TimestampMixin, Base):
    __tablename__ = "practitioner_availability"
    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, default=uuid.uuid4)
    practitioner_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("healthcare_practitioners.id", ondelete="CASCADE"), index=True
    )
    date: Mapped[date] = mapped_column(Date, index=True)
    start_time: Mapped[time] = mapped_column(Time)
    end_time: Mapped[time] = mapped_column(Time)
    status: Mapped[AvailabilityStatus] = mapped_column(
        Enum(AvailabilityStatus), index=True, default=AvailabilityStatus.available
    )
    practitioner: Mapped[Practitioner] = relationship(back_populates="availability")
    appointment: Mapped["Appointment|None"] = relationship(
        back_populates="availability", uselist=False
    )
    __table_args__ = (
        UniqueConstraint("practitioner_id", "date", "start_time", name="uq_practitioner_slot"),
        CheckConstraint("end_time > start_time", name="ck_availability_end_after_start"),
    )


class Appointment(TimestampMixin, Base):
    __tablename__ = "appointments"
    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, default=uuid.uuid4)
    user_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("users.id", ondelete="RESTRICT"), index=True
    )
    practitioner_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("healthcare_practitioners.id", ondelete="RESTRICT"), index=True
    )
    availability_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("practitioner_availability.id", ondelete="RESTRICT"), unique=True
    )
    appointment_type: Mapped[AppointmentType] = mapped_column(Enum(AppointmentType))
    status: Mapped[AppointmentStatus] = mapped_column(
        Enum(AppointmentStatus), index=True, default=AppointmentStatus.confirmed
    )
    scheduled_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), index=True)
    reason: Mapped[str] = mapped_column(Text)
    notes: Mapped[str | None] = mapped_column(Text)
    user: Mapped[User] = relationship(back_populates="appointments")
    practitioner: Mapped[Practitioner] = relationship(back_populates="appointments")
    availability: Mapped[Availability] = relationship(back_populates="appointment")
