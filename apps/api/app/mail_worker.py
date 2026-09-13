"""Run periodically with `python -m app.mail_worker`; each run drains a bounded batch."""

import argparse
import hashlib
import logging
import smtplib
from datetime import UTC, datetime, timedelta

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.account_mail import email_token, send_account_email
from app.core.config import get_settings
from app.db import SessionLocal
from app.models import AccountEmail, EmailVerificationToken, PasswordResetToken, User

logger = logging.getLogger(__name__)


def deliver_one(db: Session) -> bool:
    now = datetime.now(UTC)
    job = db.scalar(
        select(AccountEmail)
        .where(AccountEmail.status == "pending", AccountEmail.next_attempt_at <= now)
        .order_by(AccountEmail.next_attempt_at)
        .with_for_update(skip_locked=True)
        .limit(1)
    )
    if job is None:
        return False
    model = PasswordResetToken if job.kind == "password_reset" else EmailVerificationToken
    item = db.get(model, job.id)
    user = db.get(User, job.user_id)
    token = email_token(job.kind, job.id)
    expires = (
        (item.expires_at if item.expires_at.tzinfo else item.expires_at.replace(tzinfo=UTC))
        if item else now
    )
    if (not item or not user or item.used_at or expires <= now
            or item.token_hash != hashlib.sha256(token.encode()).hexdigest()):
        job.status = "obsolete"
    else:
        job.attempts += 1
        try:
            send_account_email(job.kind, user.email, token, get_settings())
            job.status = "sent"
        except (OSError, smtplib.SMTPException):
            job.status = "failed" if job.attempts >= 5 else "pending"
            job.next_attempt_at = now + timedelta(seconds=60 * 2 ** (job.attempts - 1))
            # SMTP exceptions can contain recipients and credentials; do not log their text.
            logger.warning("Account email %s delivery failed (attempt %s)", job.id, job.attempts)
    db.commit()
    return True


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--limit", type=int, default=50)
    args = parser.parse_args()
    get_settings().validate_mail()
    for _ in range(max(0, args.limit)):
        with SessionLocal() as db:
            if not deliver_one(db):
                break


if __name__ == "__main__":
    main()
