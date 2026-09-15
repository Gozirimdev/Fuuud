"""Validated MongoDB documents; native ObjectIds are mapped to string API ids."""

import enum
from datetime import UTC, date, datetime, time
from decimal import Decimal
from typing import Annotated, ClassVar, Self

from bson import ObjectId
from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator

DocumentId = Annotated[str, Field(pattern=r"^[0-9a-f]{24}$")]


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


class Document(BaseModel):
    model_config = ConfigDict(validate_assignment=True)
    collection: ClassVar[str]
    id: DocumentId = Field(default_factory=lambda: str(ObjectId()))
    created_at: datetime = Field(default_factory=now)
    updated_at: datetime = Field(default_factory=now)


class User(Document):
    collection = "users"
    first_name: str = Field(min_length=2, max_length=80)
    last_name: str = Field(min_length=2, max_length=80)
    email: str
    password_hash: str
    phone_number: str | None = None
    session_version: int = Field(default=0, ge=0)
    role: UserRole = UserRole.patient
    account_status: AccountStatus = AccountStatus.active
    country: str | None = None
    state: str | None = None
    city: str | None = None
    email_verified_at: datetime | None = None
    email_request_version: int = 0

    @field_validator("email")
    @classmethod
    def normalize_email(cls, value: str) -> str:
        return value.strip().lower()

    @property
    def email_verified(self) -> bool:
        return self.email_verified_at is not None


class AccountEmail(Document):
    collection = "account_emails"
    user_id: DocumentId
    kind: str
    status: str = "pending"
    attempts: int = 0
    next_attempt_at: datetime = Field(default_factory=now)
    lease_until: datetime | None = None
    lease_owner: str | None = None


class PasswordResetToken(Document):
    collection = "password_reset_tokens"
    user_id: DocumentId
    token_hash: str
    expires_at: datetime
    used_at: datetime | None = None


class EmailVerificationToken(PasswordResetToken):
    collection = "email_verification_tokens"


class AuditEvent(Document):
    collection = "audit_events"
    user_id: DocumentId
    event_type: str


class Practitioner(Document):
    collection = "healthcare_practitioners"
    first_name: str
    last_name: str
    specialty: str
    professional_title: str
    license_number: str
    country: str
    state: str
    city: str
    consultation_fee: Decimal = Field(ge=0, max_digits=12, decimal_places=2)
    years_of_experience: int = Field(ge=0)
    verification_status: VerificationStatus = VerificationStatus.pending
    bio: str
    rating: Decimal = Field(ge=0, le=5)
    profile_image_url: str | None = None


class Availability(Document):
    collection = "practitioner_availability"
    practitioner_id: DocumentId
    date: date
    start_time: time
    end_time: time
    status: AvailabilityStatus = AvailabilityStatus.available

    @model_validator(mode="after")
    def valid_times(self) -> Self:
        if self.end_time <= self.start_time:
            raise ValueError("End time must be after start time")
        return self


class Appointment(Document):
    collection = "appointments"
    user_id: DocumentId
    practitioner_id: DocumentId
    availability_id: DocumentId
    appointment_type: AppointmentType
    status: AppointmentStatus = AppointmentStatus.confirmed
    scheduled_at: datetime
    reason: str
    notes: str | None = None
    practitioner: Practitioner | None = Field(default=None, exclude=True)
