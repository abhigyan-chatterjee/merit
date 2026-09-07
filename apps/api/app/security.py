import hashlib
import secrets
from datetime import UTC, datetime, timedelta

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
        key="av_access",
        value=access_token,
        max_age=settings.access_token_expire_minutes * 60,
        httponly=True,
        secure=is_secure,
        samesite="lax",
        path="/",
    )
    response.set_cookie(
        key="av_refresh",
        value=refresh_token,
        max_age=settings.refresh_token_expire_days * 86400,
        httponly=True,
        secure=is_secure,
        samesite="lax",
        path="/",
    )


def clear_auth_cookies(response: Response) -> None:
    response.delete_cookie(key="av_access", path="/")
    response.delete_cookie(key="av_refresh", path="/")


def get_current_user(request: Request, db: Session = Depends(get_db)) -> User:
    token = request.cookies.get("av_access")
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


def require_admin_user(current_user: User = Depends(get_current_user)) -> User:
    if current_user.role != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail={"code": "FORBIDDEN", "message": "Admin privileges required"},
        )
    return current_user
