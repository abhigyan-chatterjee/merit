import hashlib
import secrets
from datetime import UTC, datetime, timedelta
from urllib.parse import urlparse

import jwt
from fastapi import Depends, HTTPException, Request, Response, status
from pwdlib import PasswordHash
from pwdlib.hashers.argon2 import Argon2Hasher
from sqlalchemy.orm import Session

from app.config import settings
from app.db import get_db
from app.models.user import User

# Password hashing via Argon2id
password_hasher = PasswordHash((Argon2Hasher(),))


def hash_password(password: str) -> str:
    return password_hasher.hash(password)


def verify_password(plain_password: str, hashed_password: str) -> bool:
    return password_hasher.verify(plain_password, hashed_password)


def hash_token(token: str) -> str:
    """Hash opaque refresh token with SHA-256 for secure DB storage."""
    return hashlib.sha256(token.encode("utf-8")).hexdigest()


def generate_opaque_token() -> str:
    return secrets.token_urlsafe(48)


def create_access_token(user_id: str, role: str = "student") -> str:
    now = datetime.now(UTC)
    expire = now + timedelta(minutes=settings.access_token_expire_minutes)
    payload = {
        "sub": user_id,
        "role": role,
        "iat": int(now.timestamp()),
        "exp": int(expire.timestamp()),
        "type": "access",
    }
    return jwt.encode(payload, settings.secret_key, algorithm=settings.algorithm)


def decode_access_token(token: str) -> dict:
    try:
        payload = jwt.decode(
            token,
            settings.secret_key,
            algorithms=[settings.algorithm],
            options={"require": ["sub", "exp"]},
        )
        if payload.get("type") != "access":
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail={"code": "INVALID_TOKEN_TYPE", "message": "Invalid token type"},
            )
        return payload
    except jwt.ExpiredSignatureError as err:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail={"code": "TOKEN_EXPIRED", "message": "Access token has expired"},
        ) from err
    except jwt.PyJWTError as err:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail={"code": "INVALID_TOKEN", "message": "Could not validate credentials"},
        ) from err


def set_auth_cookies(response: Response, access_token: str, refresh_token: str) -> None:
    is_secure = settings.environment.lower() == "production"

    response.set_cookie(
        key="merit_access",
        value=access_token,
        max_age=settings.access_token_expire_minutes * 60,
        httponly=True,
        secure=is_secure,
        samesite="strict",
        path="/",
    )
    response.set_cookie(
        key="merit_refresh",
        value=refresh_token,
        max_age=settings.refresh_token_expire_days * 86400,
        httponly=True,
        secure=is_secure,
        samesite="strict",
        path="/",
    )


def clear_auth_cookies(response: Response) -> None:
    response.delete_cookie(key="merit_access", path="/")
    response.delete_cookie(key="merit_refresh", path="/")


def require_same_origin(request: Request) -> None:
    """Reject browser cross-site state changes; Strict cookies cover cookie delivery."""
    origin = request.headers.get("origin")
    if not origin:
        return
    origin_parsed = urlparse(origin)
    host = (
        request.headers.get("x-forwarded-host")
        or request.headers.get("host")
        or request.url.netloc
    ).lower()

    origin_netloc = origin_parsed.netloc.lower()
    host_netloc = host

    # Strip default ports :80 and :443 for clean comparison
    for p in (":80", ":443"):
        if origin_netloc.endswith(p):
            origin_netloc = origin_netloc[: -len(p)]
        if host_netloc.endswith(p):
            host_netloc = host_netloc[: -len(p)]

    if origin_netloc == host_netloc:
        return

    # Check against CORS origins (both full origin and netloc)
    cors_allowed = [urlparse(o).netloc.lower() for o in settings.cors_origins] + [
        o.rstrip("/").lower() for o in settings.cors_origins
    ]
    if origin_netloc in cors_allowed or origin.rstrip("/").lower() in cors_allowed:
        return

    raise HTTPException(
        status_code=status.HTTP_403_FORBIDDEN,
        detail={"code": "CSRF_ORIGIN_MISMATCH", "message": "Cross-site request rejected."},
    )


def get_current_user(request: Request, db: Session = Depends(get_db)) -> User:
    token = request.cookies.get("merit_access")
    if not token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail={"code": "UNAUTHORIZED", "message": "Authentication credentials missing"},
        )

    payload = decode_access_token(token)
    user_id = payload.get("sub")
    if not user_id:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail={"code": "INVALID_TOKEN", "message": "Invalid user id in token"},
        )

    user = db.get(User, user_id)
    if not user or user.is_active != 1:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail={"code": "USER_INACTIVE", "message": "User account inactive or not found"},
        )

    return user


def get_optional_current_user(request: Request, db: Session = Depends(get_db)) -> User | None:
    token = request.cookies.get("merit_access")
    if not token:
        return None
    try:
        payload = decode_access_token(token)
        user_id = payload.get("sub")
        if not user_id:
            return None
        user = db.get(User, user_id)
        if not user or user.is_active != 1:
            return None
        return user
    except Exception:
        return None


def require_admin_user(current_user: User = Depends(get_current_user)) -> User:
    if current_user.role != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail={"code": "FORBIDDEN", "message": "Admin privileges required"},
        )
    return current_user
