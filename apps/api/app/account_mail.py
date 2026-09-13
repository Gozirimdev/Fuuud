"""Durable account mail; bearer tokens are derived, never stored in the queue."""

import hashlib
import hmac
import smtplib
import ssl
import uuid
from email.message import EmailMessage
from urllib.parse import urlencode

from app.core.config import Settings, get_settings


def email_token(kind: str, token_id: uuid.UUID) -> str:
    if len(get_settings().jwt_secret) < 32:
        raise RuntimeError("JWT_SECRET must be at least 32 characters for account email tokens.")
    return hmac.new(
        get_settings().jwt_secret.encode(),
        f"fuuud-account-email:{kind}:{token_id}".encode(),
        hashlib.sha256,
    ).hexdigest()


def send_account_email(kind: str, recipient: str, token: str, settings: Settings) -> None:
    settings.validate_mail()
    if kind == "password_reset":
        path, subject, expiry = "reset-password", "Reset your FUUUD password", "30 minutes"
    elif kind == "email_verification":
        path, subject, expiry = "verify-email", "Verify your FUUUD email address", "24 hours"
    else:
        raise ValueError("Unknown account email kind")
    link = f"{settings.public_app_url.rstrip('/')}/{path}?{urlencode({'token': token})}"
    message = EmailMessage()
    message["From"] = str(settings.mail_from)
    message["To"] = recipient
    message["Subject"] = subject
    message.set_content(
        f"{subject}\n\nOpen this link to continue:\n{link}\n\n"
        f"This link expires in {expiry} and can only be used once.\n"
        "If you did not request this, you can ignore this email.\n"
    )
    context = ssl.create_default_context()
    if settings.smtp_security == "ssl":
        connection = smtplib.SMTP_SSL(
            settings.smtp_host, settings.smtp_port, timeout=10, context=context
        )
    else:
        connection = smtplib.SMTP(settings.smtp_host, settings.smtp_port, timeout=10)
    with connection as smtp:
        if settings.smtp_security == "starttls":
            smtp.starttls(context=context)
        if settings.smtp_username:
            smtp.login(settings.smtp_username, settings.smtp_password.get_secret_value())
        smtp.send_message(message)
