"""Create MongoDB collections and indexes. Safe to run on every deployment."""

from app.db import get_client, get_store
from app.models import (
    AccountEmail,
    Appointment,
    AuditEvent,
    Availability,
    EmailVerificationToken,
    PasswordResetToken,
    Practitioner,
    User,
)


def initialize(database) -> None:
    models = [
        User,
        Practitioner,
        Availability,
        Appointment,
        PasswordResetToken,
        EmailVerificationToken,
        AuditEvent,
        AccountEmail,
    ]
    existing = database.list_collection_names()
    for model in models:
        if model.collection not in existing:
            database.create_collection(model.collection)
    database[User.collection].create_index("email", unique=True)
    database[Practitioner.collection].create_index("license_number", unique=True)
    database[Practitioner.collection].create_index([("specialty", 1), ("city", 1)])
    database[Practitioner.collection].create_index([("verification_status", 1), ("rating", -1)])
    database[Availability.collection].create_index(
        [("practitioner_id", 1), ("date", 1), ("start_time", 1)], unique=True
    )
    database[Availability.collection].create_index(
        [("practitioner_id", 1), ("status", 1), ("date", 1)]
    )
    database[Appointment.collection].create_index(
        "availability_id",
        unique=True,
        partialFilterExpression={"status": {"$in": ["pending", "confirmed", "completed"]}},
        name="unique_active_slot",
    )
    database[Appointment.collection].create_index([("user_id", 1), ("scheduled_at", -1)])
    for model in [PasswordResetToken, EmailVerificationToken]:
        database[model.collection].create_index("token_hash", unique=True)
        database[model.collection].create_index([("user_id", 1), ("created_at", -1)])
        # Keep records for one day after expiry for throttling and delivery reconciliation.
        database[model.collection].create_index("expires_at", expireAfterSeconds=86400)
    database[AuditEvent.collection].create_index([("user_id", 1), ("created_at", -1)])
    database[AccountEmail.collection].create_index([("status", 1), ("next_attempt_at", 1)])
    database[AccountEmail.collection].create_index([("status", 1), ("lease_until", 1)])


def main() -> None:
    hello = get_client().admin.command("hello")
    if not hello.get("setName") and hello.get("msg") != "isdbgrid":
        raise RuntimeError("Fuuud requires MongoDB Atlas or a replica set for transactions.")
    initialize(get_store().database)
    print("MongoDB collections and indexes are ready.")


if __name__ == "__main__":
    main()
