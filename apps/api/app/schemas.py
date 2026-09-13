import uuid
from datetime import date, datetime, time
from decimal import Decimal
from typing import Literal

from pydantic import BaseModel, ConfigDict, EmailStr, Field

from app.models import (
    AccountStatus,
    AppointmentStatus,
    AppointmentType,
    AvailabilityStatus,
    UserRole,
    VerificationStatus,
)


class RegisterIn(BaseModel):
    first_name: str = Field(min_length=2, max_length=80)
    last_name: str = Field(min_length=2, max_length=80)
    email: EmailStr
    password: str = Field(min_length=8, max_length=128)
    role: Literal["patient", "doctor", "hospital_staff"] = "patient"
    phone_number: str | None = None
    country: str | None = None
    state: str | None = None
    city: str | None = None


class LoginIn(BaseModel):
    email: EmailStr
    password: str


class ForgotPasswordIn(BaseModel):
    email: EmailStr


class ForgotPasswordOut(BaseModel):
    message: str
    reset_token: str | None = None


class ResetPasswordIn(BaseModel):
    token: str = Field(min_length=32, max_length=256)
    password: str = Field(min_length=8, max_length=128)


class MessageOut(BaseModel):
    message: str


class VerificationRequestIn(BaseModel):
    email: EmailStr


class VerificationOut(BaseModel):
    message: str
    verification_token: str | None = None


class VerifyEmailIn(BaseModel):
    token: str = Field(min_length=32, max_length=256)


class AuditEventOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: uuid.UUID
    event_type: str
    created_at: datetime


class UserOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: uuid.UUID
    first_name: str
    last_name: str
    email: EmailStr
    role: UserRole
    account_status: AccountStatus
    phone_number: str | None
    country: str | None
    state: str | None
    city: str | None
    email_verified: bool


class RegistrationOut(UserOut):
    verification_token: str | None = None


class TokenOut(BaseModel):
    access_token: str
    token_type: str = "bearer"
    expires_in: int


class AvailabilityOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: uuid.UUID
    practitioner_id: uuid.UUID
    date: date
    start_time: time
    end_time: time
    status: AvailabilityStatus


class DoctorOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: uuid.UUID
    first_name: str
    last_name: str
    specialty: str
    professional_title: str
    country: str
    state: str
    city: str
    consultation_fee: Decimal
    years_of_experience: int
    verification_status: VerificationStatus
    bio: str
    rating: Decimal
    profile_image_url: str | None


class DoctorList(BaseModel):
    items: list[DoctorOut]
    total: int
    page: int
    page_size: int


class BookAppointmentIn(BaseModel):
    practitioner_id: uuid.UUID
    availability_id: uuid.UUID
    appointment_type: AppointmentType
    reason: str = Field(min_length=3, max_length=2000)


class AppointmentOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: uuid.UUID
    user_id: uuid.UUID
    practitioner_id: uuid.UUID
    availability_id: uuid.UUID
    appointment_type: AppointmentType
    status: AppointmentStatus
    scheduled_at: datetime
    reason: str
    notes: str | None
    practitioner: DoctorOut
