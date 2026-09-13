import uuid
from datetime import date
from decimal import Decimal
from typing import Literal

from fastapi import APIRouter, Depends, Query, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.db import get_db
from app.dependencies import current_user, require_roles
from app.models import AuditEvent, User, UserRole
from app.schemas import (
    AppointmentOut,
    AuditEventOut,
    AvailabilityOut,
    BookAppointmentIn,
    DoctorList,
    DoctorOut,
    ForgotPasswordIn,
    ForgotPasswordOut,
    LoginIn,
    MessageOut,
    RegisterIn,
    RegistrationOut,
    ResetPasswordIn,
    TokenOut,
    UserOut,
    VerificationOut,
    VerificationRequestIn,
    VerifyEmailIn,
)
from app.services import AppointmentService, AuthService, DoctorService

router = APIRouter(prefix="/api/v1")


@router.post("/auth/register", response_model=RegistrationOut, status_code=status.HTTP_201_CREATED)
def register(data: RegisterIn, db: Session = Depends(get_db)):
    user, token = AuthService(db).register(data)
    from app.core.config import get_settings

    return RegistrationOut(
        **UserOut.model_validate(user).model_dump(),
        verification_token=(token if get_settings().environment.lower() == "development" else None),
    )


@router.post("/auth/login", response_model=TokenOut)
def login(data: LoginIn, db: Session = Depends(get_db)):
    token, expires = AuthService(db).login(data)
    return TokenOut(access_token=token, expires_in=expires)


@router.post("/auth/forgot-password", response_model=ForgotPasswordOut)
def forgot_password(data: ForgotPasswordIn, db: Session = Depends(get_db)):
    token = AuthService(db).request_password_reset(data.email)
    # Production delivery uses the durable account email queue.
    from app.core.config import get_settings

    return ForgotPasswordOut(
        message="If an account exists for that email, check your inbox for reset instructions.",
        reset_token=token if get_settings().environment.lower() == "development" else None,
    )


@router.post("/auth/reset-password", response_model=MessageOut)
def reset_password(data: ResetPasswordIn, db: Session = Depends(get_db)):
    AuthService(db).reset_password(data.token, data.password)
    return MessageOut(message="Your password has been reset")


@router.post("/auth/email-verification/request", response_model=VerificationOut)
def request_email_verification(data: VerificationRequestIn, db: Session = Depends(get_db)):
    token = AuthService(db).request_email_verification(data.email)
    from app.core.config import get_settings

    return VerificationOut(
        message="If the account needs verification, check your inbox for instructions.",
        verification_token=(token if get_settings().environment.lower() == "development" else None),
    )


@router.post("/auth/email-verification/verify", response_model=MessageOut)
def verify_email(data: VerifyEmailIn, db: Session = Depends(get_db)):
    AuthService(db).verify_email(data.token)
    return MessageOut(message="Your email address has been verified")


@router.get("/users/me", response_model=UserOut)
def me(user: User = Depends(current_user)):
    return user


@router.get("/users/me/audit-events", response_model=list[AuditEventOut])
def my_audit_events(user: User = Depends(current_user), db: Session = Depends(get_db)):
    query = (
        select(AuditEvent)
        .where(AuditEvent.user_id == user.id)
        .order_by(AuditEvent.created_at.desc())
        .limit(50)
    )
    return list(db.scalars(query).all())


@router.get("/doctors", response_model=DoctorList)
def doctors(
    search: str | None = None,
    specialty: str | None = None,
    city: str | None = None,
    state: str | None = None,
    country: str | None = None,
    max_fee: Decimal | None = None,
    available_date: date | None = None,
    verified_only: bool = False,
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    sort: str = "newest",
    db: Session = Depends(get_db),
):
    items, total = DoctorService(db).search(
        search=search,
        specialty=specialty,
        city=city,
        state=state,
        country=country,
        max_fee=max_fee,
        available_date=available_date,
        verified_only=verified_only,
        page=page,
        page_size=page_size,
        sort=sort,
    )
    return DoctorList(items=items, total=total, page=page, page_size=page_size)


@router.get("/doctors/{doctor_id}", response_model=DoctorOut)
def doctor(doctor_id: uuid.UUID, db: Session = Depends(get_db)):
    return DoctorService(db).get(doctor_id)


@router.get("/doctors/{doctor_id}/availability", response_model=list[AvailabilityOut])
def availability(
    doctor_id: uuid.UUID,
    start_date: date | None = None,
    end_date: date | None = None,
    db: Session = Depends(get_db),
):
    return DoctorService(db).availability(doctor_id, start_date, end_date)


@router.post("/appointments", response_model=AppointmentOut, status_code=status.HTTP_201_CREATED)
def book(
    data: BookAppointmentIn,
    user: User = Depends(require_roles(UserRole.patient)),
    db: Session = Depends(get_db),
):
    return AppointmentService(db).book(user, data)


@router.get("/appointments/me", response_model=list[AppointmentOut])
def my_appointments(
    view: Literal["upcoming", "past", "cancelled"] | None = None,
    user: User = Depends(require_roles(UserRole.patient)),
    db: Session = Depends(get_db),
):
    return AppointmentService(db).mine(user, view)


@router.get("/appointments/{appointment_id}", response_model=AppointmentOut)
def appointment(
    appointment_id: uuid.UUID,
    user: User = Depends(require_roles(UserRole.patient)),
    db: Session = Depends(get_db),
):
    return AppointmentService(db).own(user, appointment_id)


@router.patch("/appointments/{appointment_id}/cancel", response_model=AppointmentOut)
def cancel(
    appointment_id: uuid.UUID,
    user: User = Depends(require_roles(UserRole.patient)),
    db: Session = Depends(get_db),
):
    return AppointmentService(db).cancel(user, appointment_id)
