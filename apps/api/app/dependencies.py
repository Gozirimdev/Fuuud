import jwt
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from app.core.security import decode_token
from app.db import Store, get_db
from app.models import AccountStatus, User, UserRole

bearer = HTTPBearer(auto_error=False)


def current_user(
    credentials: HTTPAuthorizationCredentials | None = Depends(bearer),
    db: Store = Depends(get_db),
) -> User:
    if not credentials:
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Authentication required")
    try:
        user_id, session_version = decode_token(credentials.credentials)
    except (jwt.PyJWTError, ValueError):
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Invalid or expired session") from None
    user = db.get(User, user_id)
    if not user:
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "User no longer exists")
    if user.session_version != session_version:
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Invalid or expired session")
    if user.account_status == AccountStatus.suspended:
        raise HTTPException(status.HTTP_403_FORBIDDEN, "This account has been suspended")
    return user


def require_roles(*roles: UserRole):
    def dependency(user: User = Depends(current_user)) -> User:
        if user.role not in roles:
            raise HTTPException(status.HTTP_403_FORBIDDEN, "You do not have access to this action")
        if user.account_status != AccountStatus.active:
            raise HTTPException(status.HTTP_403_FORBIDDEN, "Your account is awaiting approval")
        return user

    return dependency
