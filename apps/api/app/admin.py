"""Provision an administrator from a verified account using trusted server access."""

import argparse

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.db import SessionLocal
from app.models import AccountStatus, AuditEvent, User, UserRole


def provision_admin(db: Session, email: str) -> None:
    user = db.scalar(select(User).where(User.email == email.lower()).with_for_update())
    if not user or not user.email_verified or user.account_status != AccountStatus.active:
        raise ValueError("An active, email-verified account is required.")
    if user.role == UserRole.admin:
        return
    if user.role != UserRole.patient:
        raise ValueError("Use a dedicated account, not an existing provider account.")
    user.role = UserRole.admin
    user.session_version += 1
    db.add(AuditEvent(user_id=user.id, event_type="account.admin_provisioned"))
    db.commit()


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--email", required=True)
    args = parser.parse_args()
    with SessionLocal() as db:
        try:
            provision_admin(db, args.email)
        except ValueError as error:
            parser.exit(1, f"{error}\n")
    print("Administrator provisioned. Sign in again to use the account.")


if __name__ == "__main__":
    main()
