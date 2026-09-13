import uuid
from datetime import date
from decimal import Decimal

from sqlalchemy import Select, or_, select
from sqlalchemy.orm import Session

from app.models import (
    Appointment,
    Availability,
    AvailabilityStatus,
    Practitioner,
    User,
    VerificationStatus,
)


class UserRepository:
    def __init__(self, db: Session):
        self.db = db

    def by_email(self, email: str) -> User | None:
        return self.db.scalar(select(User).where(User.email == email.lower()))

    def add(self, user: User) -> User:
        self.db.add(user)
        self.db.flush()
        return user


class DoctorRepository:
    def __init__(self, db: Session):
        self.db = db

    def query(
        self,
        search: str | None = None,
        specialty: str | None = None,
        city: str | None = None,
        state: str | None = None,
        country: str | None = None,
        max_fee: Decimal | None = None,
        available_date: date | None = None,
        verified_only: bool = False,
    ) -> Select[tuple[Practitioner]]:
        q = select(Practitioner)
        if search:
            term = f"%{search}%"
            q = q.where(
                or_(
                    Practitioner.first_name.ilike(term),
                    Practitioner.last_name.ilike(term),
                    (Practitioner.first_name + " " + Practitioner.last_name).ilike(term),
                    Practitioner.specialty.ilike(term),
                )
            )
        if specialty:
            q = q.where(Practitioner.specialty == specialty)
        if city:
            q = q.where(Practitioner.city.ilike(city))
        if state:
            q = q.where(Practitioner.state.ilike(state))
        if country:
            q = q.where(Practitioner.country.ilike(country))
        if max_fee is not None:
            q = q.where(Practitioner.consultation_fee <= max_fee)
        if verified_only:
            q = q.where(Practitioner.verification_status == VerificationStatus.verified)
        if available_date:
            q = (
                q.join(Availability)
                .where(
                    Availability.date == available_date,
                    Availability.status == AvailabilityStatus.available,
                )
                .distinct()
            )
        return q

    def get(self, doctor_id: uuid.UUID) -> Practitioner | None:
        return self.db.get(Practitioner, doctor_id)


class AppointmentRepository:
    def __init__(self, db: Session):
        self.db = db

    def lock_slot(self, slot_id: uuid.UUID) -> Availability | None:
        return self.db.scalar(
            select(Availability).where(Availability.id == slot_id).with_for_update()
        )

    def lock(self, appointment_id: uuid.UUID) -> Appointment | None:
        return self.db.scalar(
            select(Appointment).where(Appointment.id == appointment_id).with_for_update()
        )

    def for_user(self, user_id: uuid.UUID):
        return select(Appointment).where(Appointment.user_id == user_id)

    def get(self, appointment_id: uuid.UUID) -> Appointment | None:
        return self.db.get(Appointment, appointment_id)
