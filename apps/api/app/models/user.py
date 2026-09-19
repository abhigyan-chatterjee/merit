import uuid
from datetime import UTC, datetime

from sqlalchemy import ForeignKey, Integer, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db import Base


def utcnow_iso() -> str:
    return datetime.now(UTC).isoformat()


class User(Base):
    __tablename__ = "users"

    id: Mapped[str] = mapped_column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    email: Mapped[str] = mapped_column(String, unique=True, index=True, nullable=False)
    display_name: Mapped[str] = mapped_column(String, nullable=False)
    password_hash: Mapped[str] = mapped_column(String, nullable=False)
    role: Mapped[str] = mapped_column(String, default="student", nullable=False)  # student | admin
    is_active: Mapped[int] = mapped_column(Integer, default=1, nullable=False)
    has_imported_local: Mapped[int] = mapped_column(
        Integer, server_default="0", default=0, nullable=False
    )
    preferred_language: Mapped[str] = mapped_column(
        String, server_default="javascript", default="javascript", nullable=False
    )  # javascript | python
    daily_goal_json: Mapped[str | None] = mapped_column(String, nullable=True)  # JSON or null
    created_at: Mapped[str] = mapped_column(String, default=utcnow_iso, nullable=False)
    last_login_at: Mapped[str | None] = mapped_column(String, nullable=True)
    # Clerk OAuth linkage. NULL until the user signs in via Clerk at least once.
    clerk_id: Mapped[str | None] = mapped_column(String, unique=True, nullable=True, default=None)
    auth_provider: Mapped[str] = mapped_column(
        String, default="password", nullable=False
    )  # password | clerk

    refresh_tokens: Mapped[list["RefreshToken"]] = relationship(
        "RefreshToken", back_populates="user", cascade="all, delete-orphan"
    )


class RefreshToken(Base):
    __tablename__ = "refresh_tokens"

    id: Mapped[str] = mapped_column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id: Mapped[str] = mapped_column(
        String, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True
    )
    token_hash: Mapped[str] = mapped_column(String, nullable=False, index=True)
    expires_at: Mapped[str] = mapped_column(String, nullable=False)
    created_at: Mapped[str] = mapped_column(String, default=utcnow_iso, nullable=False)
    revoked_at: Mapped[str | None] = mapped_column(String, nullable=True)
    replaced_by: Mapped[str | None] = mapped_column(String, nullable=True)
    user_agent: Mapped[str | None] = mapped_column(String, nullable=True)
    ip: Mapped[str | None] = mapped_column(String, nullable=True)

    user: Mapped["User"] = relationship("User", back_populates="refresh_tokens")
