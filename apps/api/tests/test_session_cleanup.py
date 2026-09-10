import uuid
from datetime import UTC, datetime, timedelta

from sqlalchemy.orm import Session

from app.models.user import RefreshToken, User, utcnow_iso
from app.security import hash_password, hash_token
from app.services.session_cleanup import cleanup_expired_sessions


def test_cleanup_expired_sessions(db_session: Session):
    user = User(
        id=str(uuid.uuid4()),
        email="cleanup_tester@test.com",
        display_name="Cleanup Tester",
        password_hash=hash_password("Password123!"),
        role="student",
        is_active=1,
        created_at=utcnow_iso(),
    )
    db_session.add(user)
    db_session.commit()

    now = datetime.now(UTC)

    # 1. Active valid token (should NOT be deleted)
    t_active = RefreshToken(
        user_id=user.id,
        token_hash=hash_token("active_token"),
        expires_at=(now + timedelta(days=5)).isoformat(),
        created_at=utcnow_iso(),
    )
    db_session.add(t_active)

    # 2. Expired token (SHOULD be deleted)
    t_expired = RefreshToken(
        user_id=user.id,
        token_hash=hash_token("expired_token"),
        expires_at=(now - timedelta(days=1)).isoformat(),
        created_at=utcnow_iso(),
    )
    db_session.add(t_expired)

    # 3. Old revoked token (SHOULD be deleted)
    t_old_revoked = RefreshToken(
        user_id=user.id,
        token_hash=hash_token("revoked_token"),
        expires_at=(now + timedelta(days=10)).isoformat(),
        created_at=utcnow_iso(),
        revoked_at=(now - timedelta(days=10)).isoformat(),
    )
    db_session.add(t_old_revoked)

    db_session.commit()

    # Capture PKs BEFORE cleanup: bulk DELETEs bypass the identity map, so
    # touching attributes of deleted instances afterwards raises
    # ObjectDeletedError on re-fetch/refresh.
    active_id = t_active.id
    expired_id = t_expired.id
    revoked_id = t_old_revoked.id
    db_session.expire_all()

    deleted = cleanup_expired_sessions(db_session, max_revoked_days=7)
    assert deleted >= 2

    # Verify active token still exists
    remaining = db_session.get(RefreshToken, active_id)
    assert remaining is not None

    # Verify expired and old revoked are gone
    assert db_session.get(RefreshToken, expired_id) is None
    assert db_session.get(RefreshToken, revoked_id) is None
