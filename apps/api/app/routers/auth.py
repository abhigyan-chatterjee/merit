import uuid
from datetime import UTC, datetime, timedelta

from fastapi import APIRouter, Depends, HTTPException, Request, Response, status
from sqlalchemy import select, update
from sqlalchemy.orm import Session

from app.config import settings
from app.db import get_db
from app.models.user import RefreshToken, User, utcnow_iso
from app.schemas.auth import (
    AuthMessageResponse,
    ClerkOAuthRequest,
    EmailChange,
    LoginRequest,
    PasswordChange,
    ProfileUpdate,
    RegisterRequest,
    UserResponse,
)
from app.security import (
    DUMMY_VERIFY_HASH,
    clear_auth_cookies,
    create_access_token,
    generate_opaque_token,
    get_current_user,
    hash_password,
    hash_token,
    require_same_origin,
    set_auth_cookies,
    verify_password_safe,
)
from app.services.clerk_oauth import verify_clerk_session_token
from app.services.rate_limit import SlidingWindowLimiter, client_key

router = APIRouter(prefix="/api/v1/auth", tags=["auth"])

_auth_limiter = SlidingWindowLimiter(
    max_hits=20,
    window_sec=900,
    code="RATE_LIMITED",
    message="Too many authentication attempts. Please try again later.",
)
_refresh_limiter = SlidingWindowLimiter(
    max_hits=60,
    window_sec=900,
    code="RATE_LIMITED",
    message="Too many refresh requests. Please try again later.",
)

# Kept as a module alias: other modules and tests import this name. The digest
# itself now lives in app.security so verify_password_safe can reuse it.
DUMMY_PASSWORD_HASH = DUMMY_VERIFY_HASH

# Marker stored in password_hash for accounts that only ever signed in through a
# provider. Any other value means a real password was set on the row.
OAUTH_PASSWORD_SENTINEL_PREFIX = "oauth$"


def _has_password_credential(user: User) -> bool:
    """True when a usable password was set on this account.

    An account whose hash is the OAuth sentinel was never claimed with a
    password, so linking a verified provider identity to it is safe. Anything
    else means someone chose that password, and ownership has to be proven.
    """
    stored = user.password_hash or ""
    return bool(stored) and not stored.startswith(OAUTH_PASSWORD_SENTINEL_PREFIX)


@router.post("/register", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
def register(
    req: RegisterRequest,
    response: Response,
    request: Request,
    db: Session = Depends(get_db),
    _: None = Depends(require_same_origin),
):
    _auth_limiter.check(client_key(request))
    # Check existing email
    existing = db.scalar(select(User).where(User.email == req.email))
    if existing:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={
                "code": "EMAIL_EXISTS",
                "message": "An account with this email already exists.",
            },
        )

    hashed = hash_password(req.password)
    user = User(
        email=req.email,
        display_name=req.display_name,
        password_hash=hashed,
        role="student",
        is_active=1,
        created_at=utcnow_iso(),
        last_login_at=utcnow_iso(),
    )
    db.add(user)
    db.flush()

    # Create session tokens
    access_token = create_access_token(user.id, user.role)
    raw_refresh = generate_opaque_token()
    token_h = hash_token(raw_refresh)

    expires_at = (
        datetime.now(UTC) + timedelta(days=settings.refresh_token_expire_days)
    ).isoformat()

    refresh_row = RefreshToken(
        user_id=user.id,
        token_hash=token_h,
        expires_at=expires_at,
        created_at=utcnow_iso(),
    )
    db.add(refresh_row)
    db.commit()
    db.refresh(user)

    set_auth_cookies(response, access_token, raw_refresh)
    return user


@router.post("/login", response_model=UserResponse)
def login(
    req: LoginRequest,
    response: Response,
    request: Request,
    db: Session = Depends(get_db),
    _: None = Depends(require_same_origin),
):
    _auth_limiter.check(client_key(request))
    user = db.scalar(select(User).where(User.email == req.email))

    # Constant-work comparison: always run the KDF. A missing account is
    # checked against a real dummy digest, and a provider-only account is
    # checked against the sentinel (which verify_password_safe treats as a
    # non-match rather than letting pwdlib raise).
    target_hash = user.password_hash if user else DUMMY_PASSWORD_HASH
    is_valid = verify_password_safe(req.password, target_hash)

    if not user or not is_valid:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail={"code": "INVALID_CREDENTIALS", "message": "Invalid email or password."},
        )

    if user.is_active != 1:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail={"code": "USER_INACTIVE", "message": "Account has been deactivated."},
        )

    user.last_login_at = utcnow_iso()

    # Issue tokens
    access_token = create_access_token(user.id, user.role)
    raw_refresh = generate_opaque_token()
    token_h = hash_token(raw_refresh)

    expires_at = (
        datetime.now(UTC) + timedelta(days=settings.refresh_token_expire_days)
    ).isoformat()

    client_ip = request.client.host if request.client else None
    user_agent = request.headers.get("user-agent")

    refresh_row = RefreshToken(
        user_id=user.id,
        token_hash=token_h,
        expires_at=expires_at,
        created_at=utcnow_iso(),
        ip=client_ip,
        user_agent=user_agent,
    )
    db.add(refresh_row)
    db.commit()
    db.refresh(user)

    set_auth_cookies(response, access_token, raw_refresh)
    return user


@router.post("/logout", response_model=AuthMessageResponse)
def logout(
    request: Request,
    response: Response,
    db: Session = Depends(get_db),
    _: None = Depends(require_same_origin),
):
    raw_refresh = request.cookies.get("merit_refresh")
    if raw_refresh:
        token_h = hash_token(raw_refresh)
        db_token = db.scalar(select(RefreshToken).where(RefreshToken.token_hash == token_h))
        if db_token and not db_token.revoked_at:
            db_token.revoked_at = utcnow_iso()
            db.commit()

    clear_auth_cookies(response)
    return {"message": "Successfully logged out."}


@router.post("/refresh", response_model=AuthMessageResponse)
def refresh_token_rotation(
    request: Request,
    response: Response,
    db: Session = Depends(get_db),
    _: None = Depends(require_same_origin),
):
    _refresh_limiter.check(client_key(request))
    raw_refresh = request.cookies.get("merit_refresh")
    if not raw_refresh:
        clear_auth_cookies(response)
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail={"code": "MISSING_REFRESH_TOKEN", "message": "Refresh token cookie missing"},
        )

    token_h = hash_token(raw_refresh)
    db_token = db.scalar(select(RefreshToken).where(RefreshToken.token_hash == token_h))

    if not db_token:
        clear_auth_cookies(response)
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail={"code": "INVALID_REFRESH_TOKEN", "message": "Invalid refresh token"},
        )

    # THEFT DETECTION: If a revoked token is presented, revoke all sessions for this user!
    if db_token.revoked_at is not None:
        user_id = db_token.user_id
        # Revoke all active tokens for this user
        tokens = db.scalars(
            select(RefreshToken).where(
                RefreshToken.user_id == user_id, RefreshToken.revoked_at.is_(None)
            )
        ).all()
        now_str = utcnow_iso()
        for t in tokens:
            t.revoked_at = now_str
        db.commit()
        clear_auth_cookies(response)
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail={
                "code": "TOKEN_REUSE_DETECTED",
                "message": "Security compromise detected. All sessions revoked.",
            },
        )

    # Check expiry
    expires_dt = datetime.fromisoformat(db_token.expires_at)
    if expires_dt < datetime.now(UTC):
        db_token.revoked_at = utcnow_iso()
        db.commit()
        clear_auth_cookies(response)
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail={"code": "REFRESH_TOKEN_EXPIRED", "message": "Refresh token has expired"},
        )

    user = db.get(User, db_token.user_id)
    if not user or user.is_active != 1:
        clear_auth_cookies(response)
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail={"code": "USER_INACTIVE", "message": "User not active"},
        )

    # ROTATION: Revoke old token, issue new token.
    # Atomic revocation: a single conditional UPDATE claims the old token
    # (revoked_at IS NULL predicate). Concurrent double-use races so that
    # exactly one request wins (rowcount == 1); the loser falls into the
    # theft path below instead of minting a second replacement.
    new_raw_refresh = generate_opaque_token()
    new_token_h = hash_token(new_raw_refresh)
    new_expires_at = (
        datetime.now(UTC) + timedelta(days=settings.refresh_token_expire_days)
    ).isoformat()
    new_token_id = str(uuid.uuid4())
    now_str = utcnow_iso()

    revoke_stmt = (
        update(RefreshToken)
        .where(
            RefreshToken.token_hash == token_h,
            RefreshToken.revoked_at.is_(None),
        )
        .values(revoked_at=now_str, replaced_by=new_token_id)
        .execution_options(synchronize_session=False)
    )
    revoke_result = db.execute(revoke_stmt)
    if revoke_result.rowcount != 1:
        # Lost the race (or replayed a revoked token that slipped past the
        # SELECT above): treat as reuse — revoke all sessions for this user.
        user_id = db_token.user_id
        tokens = db.scalars(
            select(RefreshToken).where(
                RefreshToken.user_id == user_id, RefreshToken.revoked_at.is_(None)
            )
        ).all()
        theft_now = utcnow_iso()
        for t in tokens:
            t.revoked_at = theft_now
        db.commit()
        clear_auth_cookies(response)
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail={
                "code": "TOKEN_REUSE_DETECTED",
                "message": "Security compromise detected. All sessions revoked.",
            },
        )

    new_token_row = RefreshToken(
        id=new_token_id,
        user_id=user.id,
        token_hash=new_token_h,
        expires_at=new_expires_at,
        created_at=now_str,
        ip=request.client.host if request.client else None,
        user_agent=request.headers.get("user-agent"),
    )
    db.add(new_token_row)

    new_access_token = create_access_token(user.id, user.role)
    db.commit()

    set_auth_cookies(response, new_access_token, new_raw_refresh)
    return {"message": "Token refreshed successfully."}


@router.post("/oauth/clerk", response_model=UserResponse)
def clerk_oauth(
    req: ClerkOAuthRequest,
    response: Response,
    request: Request,
    db: Session = Depends(get_db),
    _: None = Depends(require_same_origin),
):
    """Sign in with a Clerk session JWT (Google/GitHub), linking to an existing account.

    Password login is untouched: this endpoint only verifies the Clerk token,
    links or creates the user row, then issues the standard merit_access /
    merit_refresh cookies through the same rotation code path as login.
    """
    _auth_limiter.check(client_key(request))
    if not settings.clerk_jwks_url.strip():
        raise HTTPException(
            status_code=status.HTTP_501_NOT_IMPLEMENTED,
            detail={
                "code": "OAUTH_NOT_CONFIGURED",
                "message": "Clerk OAuth is not configured on this server.",
            },
        )

    claims = verify_clerk_session_token(req.clerk_token)
    clerk_id = claims["clerk_id"]
    email = claims["email"]
    display_name = claims["display_name"]

    created = False
    user = db.scalar(select(User).where(User.clerk_id == clerk_id))
    if user is not None:
        if display_name and display_name != user.display_name:
            user.display_name = display_name
        if email != user.email:
            owner = db.scalar(select(User).where(User.email == email))
            if owner is None:
                user.email = email
    if user is None:
        user = db.scalar(select(User).where(User.email == email))
        if user is not None:
            # Only auto-link rows that were never claimed with a password.
            #
            # Anyone can register any email without proving they own it. If we
            # linked on an email match, an attacker could register a victim's
            # address with a password they chose, and then keep that password
            # (and full access) after the real owner signs in with the verified
            # provider identity. Ownership of a password-protected row has to be
            # proven by signing in with it first, then linking deliberately.
            if _has_password_credential(user):
                raise HTTPException(
                    status_code=status.HTTP_409_CONFLICT,
                    detail={
                        "code": "OAUTH_LINK_REQUIRES_PASSWORD",
                        "message": (
                            "An account already exists for this email. Sign in with "
                            "your password first, then connect this provider from "
                            "your account settings."
                        ),
                    },
                )
            # LINK: attach clerk_id, keep all existing data.
            user.clerk_id = clerk_id
        else:
            # CREATE: OAuth-only account (no usable password).
            user = User(
                email=email,
                display_name=display_name,
                password_hash=f"{OAUTH_PASSWORD_SENTINEL_PREFIX}clerk",
                role="student",
                is_active=1,
                clerk_id=clerk_id,
                auth_provider="clerk",
                created_at=utcnow_iso(),
                last_login_at=utcnow_iso(),
            )
            db.add(user)
            db.flush()
            created = True

    if user.is_active != 1:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail={"code": "USER_INACTIVE", "message": "Account has been deactivated."},
        )

    user.last_login_at = utcnow_iso()

    # Issue tokens via the standard rotation code path (same as password login).
    access_token = create_access_token(user.id, user.role)
    raw_refresh = generate_opaque_token()
    token_h = hash_token(raw_refresh)

    expires_at = (
        datetime.now(UTC) + timedelta(days=settings.refresh_token_expire_days)
    ).isoformat()

    refresh_row = RefreshToken(
        user_id=user.id,
        token_hash=token_h,
        expires_at=expires_at,
        created_at=utcnow_iso(),
        ip=request.client.host if request.client else None,
        user_agent=request.headers.get("user-agent"),
    )
    db.add(refresh_row)
    db.commit()
    db.refresh(user)

    set_auth_cookies(response, access_token, raw_refresh)
    if created:
        response.status_code = status.HTTP_201_CREATED
    return user


@router.post("/oauth/clerk/link", response_model=UserResponse)
def clerk_oauth_link(
    req: ClerkOAuthRequest,
    request: Request,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
    _: None = Depends(require_same_origin),
):
    _auth_limiter.check(client_key(request))
    if not settings.clerk_jwks_url.strip():
        raise HTTPException(
            status_code=status.HTTP_501_NOT_IMPLEMENTED,
            detail={
                "code": "OAUTH_NOT_CONFIGURED",
                "message": "Clerk OAuth is not configured on this server.",
            },
        )
    claims = verify_clerk_session_token(req.clerk_token)
    if claims["email"] != current_user.email.lower():
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail={
                "code": "OAUTH_EMAIL_MISMATCH",
                "message": "Your OAuth email does not match your account email.",
            },
        )
    other = db.scalar(
        select(User).where(User.clerk_id == claims["clerk_id"], User.id != current_user.id)
    )
    if other is not None:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail={
                "code": "OAUTH_ALREADY_LINKED",
                "message": "This OAuth account is already linked to a different user.",
            },
        )
    current_user.clerk_id = claims["clerk_id"]
    db.commit()
    db.refresh(current_user)
    return current_user


@router.get("/me", response_model=UserResponse)
def get_me(user: User = Depends(get_current_user)):
    return user


@router.patch("/me", response_model=UserResponse)
def update_profile(
    req: ProfileUpdate,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
    _: None = Depends(require_same_origin),
):
    if req.display_name:
        user.display_name = req.display_name
        db.commit()
        db.refresh(user)
    return user


@router.post("/email", response_model=UserResponse)
def change_email(
    req: EmailChange,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
    _: None = Depends(require_same_origin),
):
    if not _has_password_credential(user):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={
                "code": "NO_PASSWORD_CREDENTIAL",
                "message": (
                    "This account signs in with a provider and has no password. "
                    "Manage your address with that provider instead."
                ),
            },
        )
    if not verify_password_safe(req.current_password, user.password_hash):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail={"code": "INVALID_PASSWORD", "message": "Current password is incorrect."},
        )
    existing = db.scalar(select(User).where(User.email == req.new_email))
    if existing and existing.id != user.id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={
                "code": "EMAIL_EXISTS",
                "message": "An account with this email already exists.",
            },
        )
    user.email = req.new_email
    db.commit()
    db.refresh(user)
    return user


@router.post("/password", response_model=AuthMessageResponse)
def change_password(
    req: PasswordChange,
    response: Response,
    request: Request,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
    _: None = Depends(require_same_origin),
):
    if not _has_password_credential(user):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={
                "code": "NO_PASSWORD_CREDENTIAL",
                "message": (
                    "This account signs in via Google, GitHub, or Microsoft "
                    "and has no local password."
                ),
            },
        )
    if not verify_password_safe(req.current_password, user.password_hash):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail={"code": "INVALID_PASSWORD", "message": "Current password is incorrect."},
        )

    now_str = utcnow_iso()
    user.password_hash = hash_password(req.new_password)

    # A password change is the action a user takes when they believe their
    # account is compromised. Revoking every existing refresh token is the whole
    # point: without it a stolen session survives the reset. The calling device
    # then gets a brand new session so the legitimate user is not logged out.
    db.execute(
        update(RefreshToken)
        .where(RefreshToken.user_id == user.id, RefreshToken.revoked_at.is_(None))
        .values(revoked_at=now_str)
        .execution_options(synchronize_session=False)
    )

    raw_refresh = generate_opaque_token()
    db.add(
        RefreshToken(
            user_id=user.id,
            token_hash=hash_token(raw_refresh),
            expires_at=(
                datetime.now(UTC) + timedelta(days=settings.refresh_token_expire_days)
            ).isoformat(),
            created_at=now_str,
            ip=request.client.host if request.client else None,
            user_agent=request.headers.get("user-agent"),
        )
    )
    db.commit()

    set_auth_cookies(response, create_access_token(user.id, user.role), raw_refresh)
    return {"message": "Password changed successfully. Other sessions have been signed out."}


@router.delete("/account", response_model=AuthMessageResponse)
def delete_account(
    response: Response,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
    _: None = Depends(require_same_origin),
):
    # Hard delete user and cascade all dependent data
    db.delete(user)
    db.commit()
    clear_auth_cookies(response)
    return {"message": "Account and all associated user data permanently deleted."}


@router.get("/export")
def export_user_data(
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    from app.models.progress import (
        ActivityDay,
        Bookmark,
        Note,
        ProblemProgress,
        VisualizerCompletion,
    )
    from app.models.quiz import QuizAttempt
    from app.models.submission import Submission

    problems = db.scalars(select(ProblemProgress).where(ProblemProgress.user_id == user.id)).all()
    notes = db.scalars(select(Note).where(Note.user_id == user.id)).all()
    bookmarks = db.scalars(select(Bookmark).where(Bookmark.user_id == user.id)).all()
    activities = db.scalars(select(ActivityDay).where(ActivityDay.user_id == user.id)).all()
    visualizers = db.scalars(
        select(VisualizerCompletion).where(VisualizerCompletion.user_id == user.id)
    ).all()
    submissions = db.scalars(select(Submission).where(Submission.user_id == user.id)).all()
    quizzes = db.scalars(select(QuizAttempt).where(QuizAttempt.user_id == user.id)).all()

    return {
        "user": {
            "id": user.id,
            "email": user.email,
            "display_name": user.display_name,
            "role": user.role,
            "created_at": user.created_at,
            "last_login_at": user.last_login_at,
        },
        "problem_progress": [
            {"problem_slug": p.problem_slug, "status": p.status, "updated_at": p.updated_at}
            for p in problems
        ],
        "notes": [
            {"problem_slug": n.problem_slug, "text": n.text, "updated_at": n.updated_at}
            for n in notes
        ],
        "bookmarks": [
            {"item_type": b.item_type, "item_id": b.item_id, "created_at": b.created_at}
            for b in bookmarks
        ],
        "activity_days": {a.day: a.action_count for a in activities},
        "visualizer_completions": [
            {
                "visualizer_id": v.visualizer_id,
                "visits": v.visits,
                "first_completed_at": v.first_completed_at,
            }
            for v in visualizers
        ],
        "submissions": [
            {
                "id": s.id,
                "problem_slug": s.problem_slug,
                "language": s.language,
                "verdict": s.verdict,
                "runtime_ms": s.runtime_ms,
                "created_at": s.created_at,
            }
            for s in submissions
        ],
        "quiz_attempts": [
            {
                "id": q.id,
                "total": q.total,
                "correct": q.correct,
                "score_pct": q.score_pct,
                "duration_sec": q.duration_sec,
                "created_at": q.created_at,
            }
            for q in quizzes
        ],
        "sessions_count": len(user.refresh_tokens),
        "exported_at": utcnow_iso(),
    }
