"""Session table cleanup service for expired and revoked refresh tokens."""

from datetime import UTC, datetime, timedelta

from sqlalchemy import delete
from sqlalchemy.orm import Session

from app.models.user import RefreshToken, utcnow_iso


def cleanup_expired_sessions(db: Session, max_revoked_days: int = 7) -> int:
    """Deletes refresh tokens that are either expired or revoked beyond max_revoked_days."""
    now_iso = utcnow_iso()
    cutoff_revoked = (datetime.now(UTC) - timedelta(days=max_revoked_days)).isoformat()

    # Delete expired tokens
    stmt_expired = delete(RefreshToken).where(RefreshToken.expires_at < now_iso)
    res_expired = db.execute(stmt_expired)

    # Delete old revoked tokens
    stmt_revoked = delete(RefreshToken).where(
        RefreshToken.revoked_at.is_not(None),
        RefreshToken.revoked_at < cutoff_revoked,
    )
    res_revoked = db.execute(stmt_revoked)

    db.commit()
    deleted_count = (res_expired.rowcount or 0) + (res_revoked.rowcount or 0)
    return deleted_count
