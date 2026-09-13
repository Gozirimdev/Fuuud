import hashlib
import smtplib
from datetime import UTC, datetime, timedelta
from unittest.mock import MagicMock

import pytest
from fastapi import HTTPException
from sqlalchemy import select

from app.account_mail import email_token, send_account_email
from app.admin import provision_admin
from app.core.config import Settings, get_settings
from app.dependencies import require_roles
from app.mail_worker import deliver_one
from app.models import (
    AccountEmail,
    AccountStatus,
    EmailVerificationToken,
    PasswordResetToken,
    User,
    UserRole,
)


def register(client):
    account = {
        "first_name": "Email", "last_name": "User", "email": "delivery@example.com",
        "password": "securePass123",
    }
    result = client.post("/api/v1/auth/register", json=account)
    assert result.status_code == 201
    return result.json()


def test_queue_retry_and_success_without_storing_bearer_token(client, monkeypatch, db_factory):
    registered = register(client)
    send = MagicMock(side_effect=smtplib.SMTPException("private transport detail"))
    monkeypatch.setattr("app.mail_worker.send_account_email", send)
    with db_factory() as db:
        job = db.scalar(select(AccountEmail))
        assert email_token(job.kind, job.id) == registered["verification_token"]
        assert deliver_one(db)
        assert job.status == "pending" and job.attempts == 1
        assert not deliver_one(db)
        job.next_attempt_at = datetime.now(UTC) - timedelta(seconds=1)
        db.commit()
        send.side_effect = None
        assert deliver_one(db)
        assert job.status == "sent" and job.attempts == 2
        assert not deliver_one(db)
    assert send.call_args.args[1] == "delivery@example.com"


def test_resend_cooldown_preserves_original_token(client, db_factory):
    register(client)
    first = client.post("/api/v1/auth/forgot-password", json={"email": "delivery@example.com"})
    second = client.post("/api/v1/auth/forgot-password", json={"email": "delivery@example.com"})
    assert first.json()["reset_token"]
    assert second.json()["reset_token"] is None
    with db_factory() as db:
        tokens = list(db.scalars(select(PasswordResetToken)))
        assert len(tokens) == 1 and tokens[0].used_at is None
        assert tokens[0].token_hash == hashlib.sha256(
            first.json()["reset_token"].encode()
        ).hexdigest()


def test_used_email_is_not_delivered(client, monkeypatch, db_factory):
    registered = register(client)
    client.post("/api/v1/auth/email-verification/verify", json={
        "token": registered["verification_token"]
    })
    send = MagicMock()
    monkeypatch.setattr("app.mail_worker.send_account_email", send)
    with db_factory() as db:
        assert deliver_one(db)
        assert db.scalar(select(AccountEmail)).status == "obsolete"
    send.assert_not_called()


def test_expired_email_is_not_delivered(client, monkeypatch, db_factory):
    register(client)
    send = MagicMock()
    monkeypatch.setattr("app.mail_worker.send_account_email", send)
    with db_factory() as db:
        db.scalar(select(EmailVerificationToken)).expires_at = (
            datetime.now(UTC) - timedelta(seconds=1)
        )
        db.commit()
        assert deliver_one(db)
        assert db.scalar(select(AccountEmail)).status == "obsolete"
    send.assert_not_called()


def test_delivery_stops_after_five_failures(client, monkeypatch, db_factory):
    register(client)
    monkeypatch.setattr("app.mail_worker.send_account_email", MagicMock(side_effect=OSError()))
    with db_factory() as db:
        job = db.scalar(select(AccountEmail))
        for _ in range(5):
            job.next_attempt_at = datetime.now(UTC) - timedelta(seconds=1)
            db.commit()
            assert deliver_one(db)
        assert job.status == "failed" and job.attempts == 5
        assert not deliver_one(db)


def test_hourly_email_limit(client, db_factory):
    register(client)
    for _ in range(5):
        response = client.post(
            "/api/v1/auth/forgot-password", json={"email": "delivery@example.com"}
        )
        assert response.json()["reset_token"]
        with db_factory() as db:
            for item in db.scalars(select(PasswordResetToken)):
                item.created_at = datetime.now(UTC) - timedelta(minutes=2)
            db.commit()
    limited = client.post(
        "/api/v1/auth/forgot-password", json={"email": "delivery@example.com"}
    )
    assert limited.json()["reset_token"] is None


def test_production_api_hides_tokens_and_queues_unknown_accounts_privately(
    client, monkeypatch, db_factory
):
    monkeypatch.setattr(get_settings(), "environment", "production")
    registered = register(client)
    assert registered["verification_token"] is None
    known = client.post("/api/v1/auth/forgot-password", json={"email": "delivery@example.com"})
    unknown = client.post("/api/v1/auth/forgot-password", json={"email": "unknown@example.com"})
    assert known.json() == unknown.json()
    with db_factory() as db:
        assert len(list(db.scalars(select(AccountEmail)))) == 2


def test_smtp_uses_tls_and_public_link(monkeypatch):
    smtp = MagicMock()
    monkeypatch.setattr("app.account_mail.smtplib.SMTP", smtp)
    settings = Settings(
        _env_file=None, smtp_host="smtp.example.com", smtp_username="sender",
        smtp_password="test-password", public_app_url="https://fuuud.example",
    )
    send_account_email("password_reset", "recipient@example.com", "safe-token", settings)
    connection = smtp.return_value.__enter__.return_value
    connection.starttls.assert_called_once()
    connection.login.assert_called_once_with("sender", "test-password")
    message = connection.send_message.call_args.args[0]
    assert "https://fuuud.example/reset-password?token=safe-token" in message.get_content()
    assert message["To"] == "recipient@example.com"


def test_mail_configuration_rejects_insecure_production_links():
    settings = Settings(
        _env_file=None, environment="production", jwt_secret="x" * 32,
        smtp_host="smtp.example.com", public_app_url="http://fuuud.example",
    )
    with pytest.raises(RuntimeError, match="HTTPS"):
        settings.validate_mail()


def test_pending_account_is_limited_and_admin_provisioning_revokes_sessions(client, db_factory):
    registered = register(client)
    with db_factory() as db:
        user = db.scalar(select(User))
        with pytest.raises(ValueError):
            provision_admin(db, user.email)
        user.account_status = AccountStatus.pending
        with pytest.raises(HTTPException) as error:
            require_roles(UserRole.patient)(user)
        assert error.value.status_code == 403
        user.account_status = AccountStatus.active
        db.commit()
    client.post("/api/v1/auth/email-verification/verify", json={
        "token": registered["verification_token"]
    })
    login = client.post("/api/v1/auth/login", json={
        "email": "delivery@example.com", "password": "securePass123"
    }).json()
    with db_factory() as db:
        provision_admin(db, "delivery@example.com")
        assert db.scalar(select(User)).role == UserRole.admin
    assert client.get("/api/v1/users/me", headers={
        "Authorization": f"Bearer {login['access_token']}"
    }).status_code == 401
