from datetime import UTC, datetime, timedelta

import jwt
from bson import ObjectId
from pwdlib import PasswordHash

from app.core.config import get_settings

password_hash = PasswordHash.recommended()


def hash_password(value: str) -> str:
    return password_hash.hash(value)


def verify_password(value: str, hashed: str) -> bool:
    return password_hash.verify(value, hashed)


def create_token(user_id: str, session_version: int) -> tuple[str, int]:
    s = get_settings()
    expires = timedelta(minutes=s.access_token_expire_minutes)
    payload = {
        "sub": str(user_id),
        "session_version": session_version,
        "exp": datetime.now(UTC) + expires,
        "iat": datetime.now(UTC),
    }
    return jwt.encode(payload, s.jwt_secret, algorithm=s.jwt_algorithm), int(
        expires.total_seconds()
    )


def decode_token(token: str) -> tuple[str, int]:
    s = get_settings()
    payload = jwt.decode(
        token,
        s.jwt_secret,
        algorithms=[s.jwt_algorithm],
        options={"require": ["sub", "exp", "iat", "session_version"]},
    )
    version = payload["session_version"]
    if type(version) is not int or version < 0:
        raise jwt.InvalidTokenError("Invalid session version")
    if not ObjectId.is_valid(payload["sub"]):
        raise jwt.InvalidTokenError("Invalid user id")
    return str(payload["sub"]), version
