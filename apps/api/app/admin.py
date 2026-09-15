"""Provision an administrator from a verified account using trusted server access."""

import argparse

from app.db import Store, get_store
from app.models import AccountStatus, AuditEvent, User, UserRole


def provision_admin(db: Store, email: str) -> None:
    def operation(store):
        user = store.find_one(User, {"email": email.strip().lower()})
        if not user or not user.email_verified or user.account_status != AccountStatus.active:
            raise ValueError("An active, email-verified account is required.")
        if user.role == UserRole.admin:
            return
        if user.role != UserRole.patient:
            raise ValueError("Use a dedicated account, not an existing provider account.")
        store.update(
            User, {"id": user.id}, {"$set": {"role": "admin"}, "$inc": {"session_version": 1}}
        )
        store.insert(AuditEvent(user_id=user.id, event_type="account.admin_provisioned"))

    db.transaction(operation)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--email", required=True)
    args = parser.parse_args()
    with get_store() as db:
        try:
            provision_admin(db, args.email)
        except ValueError as error:
            parser.exit(1, f"{error}\n")
    print("Administrator provisioned. Sign in again to use the account.")


if __name__ == "__main__":
    main()
