import uuid

from sqlalchemy import ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.db import Base
from app.models.user import utcnow_iso


class InterviewSession(Base):
    """Persistent mock technical interview session scoped to one user."""

    __tablename__ = "interview_sessions"

    id: Mapped[str] = mapped_column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id: Mapped[str] = mapped_column(
        String, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True
    )
    difficulty: Mapped[str] = mapped_column(String, nullable=False)
    status: Mapped[str] = mapped_column(
        String, nullable=False, default="in_progress", server_default="in_progress"
    )
    current_stage: Mapped[str] = mapped_column(String, nullable=False)
    duration_sec: Mapped[int] = mapped_column(Integer, nullable=False)
    elapsed_sec: Mapped[int] = mapped_column(
        Integer, nullable=False, default=0, server_default="0"
    )
    problem_slugs_json: Mapped[str] = mapped_column(
        Text, nullable=False, default="[]", server_default="[]"
    )
    messages_json: Mapped[str] = mapped_column(
        Text, nullable=False, default="[]", server_default="[]"
    )
    coding_snapshots_json: Mapped[str] = mapped_column(
        Text, nullable=False, default="{}", server_default="{}"
    )
    resume_filename: Mapped[str | None] = mapped_column(String, nullable=True)
    resume_text: Mapped[str | None] = mapped_column(Text, nullable=True)
    project_brief: Mapped[str | None] = mapped_column(Text, nullable=True)
    rubric_json: Mapped[str | None] = mapped_column(Text, nullable=True)
    overall_verdict: Mapped[str | None] = mapped_column(String, nullable=True)
    overall_score: Mapped[int | None] = mapped_column(Integer, nullable=True)
    max_score: Mapped[int | None] = mapped_column(Integer, nullable=True)
    created_at: Mapped[str] = mapped_column(
        String, default=utcnow_iso, nullable=False, index=True
    )
    updated_at: Mapped[str] = mapped_column(String, default=utcnow_iso, nullable=False)
    completed_at: Mapped[str | None] = mapped_column(String, nullable=True)
