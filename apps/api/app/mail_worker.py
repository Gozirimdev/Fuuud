"""Deliver a bounded batch using recoverable, atomic MongoDB job leases."""

import argparse
import hashlib
import logging
import smtplib
from datetime import UTC, datetime, timedelta
from uuid import uuid4

from app.account_mail import email_token, send_account_email
from app.core.config import get_settings
from app.db import Store, get_store
from app.models import AccountEmail, EmailVerificationToken, PasswordResetToken, User

logger = logging.getLogger(__name__)


def deliver_one(db: Store) -> bool:
    now = datetime.now(UTC)
    owner = str(uuid4())
    job = db.claim(
        AccountEmail,
        {
            "$or": [
                {"status": "pending", "next_attempt_at": {"$lte": now}},
                {"status": "processing", "lease_until": {"$lte": now}},
            ]
        },
        {
            "$set": {
                "status": "processing",
                "lease_owner": owner,
                "lease_until": now + timedelta(minutes=5),
            }
        },
        sort=[("next_attempt_at", 1)],
    )
    if job is None:
        return False
    model = PasswordResetToken if job.kind == "password_reset" else EmailVerificationToken
    item = db.get(model, job.id)
    user = db.get(User, job.user_id)
    token = email_token(job.kind, job.id)
    if (
        not item
        or not user
        or item.used_at
        or item.expires_at <= now
        or item.token_hash != hashlib.sha256(token.encode()).hexdigest()
    ):
        job.status = "obsolete"
    else:
        job.attempts += 1
        try:
            send_account_email(job.kind, user.email, token, get_settings())
            job.status = "sent"
        except (OSError, smtplib.SMTPException):
            job.status = "failed" if job.attempts >= 5 else "pending"
            job.next_attempt_at = now + timedelta(seconds=60 * 2 ** (job.attempts - 1))
            logger.warning("Account email %s delivery failed (attempt %s)", job.id, job.attempts)
    db.update(
        AccountEmail,
        {"id": job.id, "lease_owner": owner},
        {
            "$set": {
                "status": job.status,
                "attempts": job.attempts,
                "next_attempt_at": job.next_attempt_at,
                "lease_until": None,
                "lease_owner": None,
                "updated_at": datetime.now(UTC),
            }
        },
    )
    return True


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--limit", type=int, default=50)
    args = parser.parse_args()
    get_settings().validate_mail()
    db = get_store()
    for _ in range(max(0, args.limit)):
        if not deliver_one(db):
            break


if __name__ == "__main__":
    main()
