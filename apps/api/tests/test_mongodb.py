"""MongoDB integration checks run against a real replica set, never mocks."""

from concurrent.futures import ThreadPoolExecutor
from datetime import UTC, datetime, timedelta
from decimal import Decimal
from threading import Barrier

import pytest
from bson import Decimal128, ObjectId
from fastapi import HTTPException
from pymongo.errors import DuplicateKeyError

from app.db import Store
from app.init_db import initialize
from app.models import (
    AccountEmail,
    Appointment,
    Availability,
    EmailVerificationToken,
    Practitioner,
    User,
)
from app.schemas import BookAppointmentIn, RegisterIn
from app.services import AppointmentService, AuthService


def account(db, email="mongo@example.com"):
    return AuthService(db).register(
        RegisterIn(first_name="Mongo", last_name="Tester", email=email, password="securePass123")
    )[0]


def booking(db):
    doctor = db.find_one(Practitioner)
    slot = db.find_one(Availability)
    return BookAppointmentIn(
        practitioner_id=doctor.id,
        availability_id=slot.id,
        appointment_type="online",
        reason="Routine consultation",
    )


def test_native_bson_types_and_idempotent_indexes(database):
    initialize(database.database)
    doctor = database.database[Practitioner.collection].find_one()
    slot = database.database[Availability.collection].find_one()
    assert isinstance(doctor["_id"], ObjectId)
    assert isinstance(doctor["consultation_fee"], Decimal128)
    assert isinstance(slot["practitioner_id"], ObjectId)
    assert isinstance(doctor["created_at"], datetime)
    assert database.find_one(Practitioner).consultation_fee == Decimal("15000")
    with pytest.raises(DuplicateKeyError):
        database.insert(database.find_one(Availability).model_copy(update={"id": str(ObjectId())}))


def test_duplicate_email_is_case_insensitive(database):
    account(database, "Mongo@example.com")
    with pytest.raises(HTTPException) as error:
        account(database, "mongo@example.com")
    assert error.value.status_code == 409
    assert database.count(User) == 1


def test_transaction_rolls_back_account_and_queue(database, monkeypatch):
    original = Store.insert

    def fail_queue(self, item):
        if isinstance(item, AccountEmail):
            raise RuntimeError("Simulated queue failure")
        return original(self, item)

    monkeypatch.setattr(Store, "insert", fail_queue)
    with pytest.raises(RuntimeError):
        account(database)
    assert database.count(User) == 0
    assert database.count(EmailVerificationToken) == 0


def test_cancelled_slot_can_be_rebooked_and_history_survives(database):
    user = account(database)
    service = AppointmentService(database)
    payload = booking(database)
    first = service.book(user, payload)
    service.cancel(user, first.id)
    second = service.book(user, payload)
    assert first.id != second.id
    assert database.count(Appointment) == 2
    assert database.get(Appointment, first.id).status == "cancelled"
    assert database.get(Availability, payload.availability_id).status == "booked"


def test_concurrent_booking_has_one_winner(database):
    user = account(database)
    payload = booking(database)
    barrier = Barrier(2)

    def book():
        barrier.wait()
        try:
            AppointmentService(Store(database.database)).book(user, payload)
            return 201
        except HTTPException as error:
            return error.status_code

    with ThreadPoolExecutor(max_workers=2) as executor:
        results = list(executor.map(lambda _: book(), range(2)))
    assert sorted(results) == [201, 409]
    assert database.count(Appointment) == 1


def test_concurrent_reset_consumption_is_single_use(database):
    user = account(database)
    token = AuthService(database).request_password_reset(user.email)
    barrier = Barrier(2)

    def reset():
        barrier.wait()
        try:
            AuthService(Store(database.database)).reset_password(token, "newPassword123")
            return 200
        except HTTPException as error:
            return error.status_code

    with ThreadPoolExecutor(max_workers=2) as executor:
        results = list(executor.map(lambda _: reset(), range(2)))
    assert sorted(results) == [200, 400]
    assert database.get(User, user.id).session_version == 1


def test_expired_worker_lease_is_recovered(database, monkeypatch):
    from app.mail_worker import deliver_one

    account(database)
    job = database.find_one(AccountEmail)
    database.update(
        AccountEmail,
        {"id": job.id},
        {
            "$set": {
                "status": "processing",
                "lease_owner": "old-worker",
                "lease_until": datetime.now(UTC) - timedelta(seconds=1),
            }
        },
    )
    sent = []
    monkeypatch.setattr("app.mail_worker.send_account_email", lambda *args: sent.append(args))
    assert deliver_one(database)
    assert len(sent) == 1
    assert database.get(AccountEmail, job.id).status == "sent"


def test_invalid_object_ids_are_rejected(client, auth):
    assert client.get("/api/v1/doctors/not-an-id").status_code == 422
    assert (
        client.post(
            "/api/v1/appointments",
            headers=auth,
            json={
                "practitioner_id": "bad",
                "availability_id": "bad",
                "appointment_type": "online",
                "reason": "Routine care",
            },
        ).status_code
        == 422
    )
