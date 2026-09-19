from datetime import UTC, datetime, timedelta

from fastapi import APIRouter, Depends, HTTPException, Request, Response, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.config import settings
from app.db import get_db
from app.models.user import RefreshToken, User, utcnow_iso
from app.schemas.auth import (
    AuthMessageResponse,
    EmailChange,
    LoginRequest,
    PasswordChange,
    ProfileUpdate,
    RegisterRequest,
    UserResponse,
)
from app.security import (
    clear_auth_cookies,
    create_access_token,
    generate_opaque_token,
    get_current_user,
    hash_password,
    hash_token,
    set_auth_cookies,
    verify_password,
)

router = APIRouter(prefix="/api/v1/auth", tags=["auth"])

# Dummy hash for timing attack mitigation on missing email lookups
DUMMY_PASSWORD_HASH = hash_password("dummy_password_timing_pad_123")


@router.post("/register", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
def register(
    req: RegisterRequest,
    response: Response,
    db: Session = Depends(get_db),
):
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
):
    user = db.scalar(select(User).where(User.email == req.email))

    # Constant-time comparison: always run verify_password
    target_hash = user.password_hash if user else DUMMY_PASSWORD_HASH
    is_valid = verify_password(req.password, target_hash)

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
):
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

    # ROTATION: Revoke old token, issue new token
    new_raw_refresh = generate_opaque_token()
    new_token_h = hash_token(new_raw_refresh)
    new_expires_at = (
        datetime.now(UTC) + timedelta(days=settings.refresh_token_expire_days)
    ).isoformat()

    new_token_row = RefreshToken(
        user_id=user.id,
        token_hash=new_token_h,
        expires_at=new_expires_at,
        created_at=utcnow_iso(),
        ip=request.client.host if request.client else None,
        user_agent=request.headers.get("user-agent"),
    )
    db.add(new_token_row)
    db.flush()

    db_token.revoked_at = utcnow_iso()
    db_token.replaced_by = new_token_row.id

    new_access_token = create_access_token(user.id, user.role)
    db.commit()

    set_auth_cookies(response, new_access_token, new_raw_refresh)
    return {"message": "Token refreshed successfully."}


@router.get("/me", response_model=UserResponse)
def get_me(user: User = Depends(get_current_user)):
    return user


@router.patch("/me", response_model=UserResponse)
def update_profile(
    req: ProfileUpdate,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
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
):
    if not verify_password(req.current_password, user.password_hash):
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
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    if not verify_password(req.current_password, user.password_hash):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail={"code": "INVALID_PASSWORD", "message": "Current password is incorrect."},
        )
    user.password_hash = hash_password(req.new_password)
    db.commit()
    return {"message": "Password changed successfully."}


@router.delete("/account", response_model=AuthMessageResponse)
def delete_account(
    response: Response,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
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

    problems = db.scalars(
        select(ProblemProgress).where(ProblemProgress.user_id == user.id)
    ).all()
    notes = db.scalars(select(Note).where(Note.user_id == user.id)).all()
    bookmarks = db.scalars(select(Bookmark).where(Bookmark.user_id == user.id)).all()
    activities = db.scalars(
        select(ActivityDay).where(ActivityDay.user_id == user.id)
    ).all()
    visualizers = db.scalars(
        select(VisualizerCompletion).where(VisualizerCompletion.user_id == user.id)
    ).all()
    submissions = db.scalars(
        select(Submission).where(Submission.user_id == user.id)
    ).all()
    quizzes = db.scalars(
        select(QuizAttempt).where(QuizAttempt.user_id == user.id)
    ).all()

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

