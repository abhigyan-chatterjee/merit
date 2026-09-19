from sqlalchemy import ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db import Base
from app.models.user import User, utcnow_iso


class QuizAttempt(Base):
    __tablename__ = "quiz_attempts"

    id: Mapped[str] = mapped_column(String, primary_key=True)
    user_id: Mapped[str] = mapped_column(
        String, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True
    )
    topic_spec: Mapped[str] = mapped_column(Text, nullable=False)  # JSON {topics:[], difficulty}
    question_ids: Mapped[str] = mapped_column(Text, nullable=False)  # JSON snapshot list of ids
    total: Mapped[int] = mapped_column(Integer, nullable=False)
    correct: Mapped[int] = mapped_column(Integer, nullable=False)
    score_pct: Mapped[int] = mapped_column(Integer, nullable=False)
    duration_sec: Mapped[int] = mapped_column(Integer, nullable=False)
    created_at: Mapped[str] = mapped_column(String, default=utcnow_iso, nullable=False, index=True)

    user: Mapped["User"] = relationship("User")
    answers: Mapped[list["QuizAttemptAnswer"]] = relationship(
        "QuizAttemptAnswer", back_populates="attempt", cascade="all, delete-orphan"
    )


class QuizAttemptAnswer(Base):
    __tablename__ = "quiz_attempt_answers"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    attempt_id: Mapped[str] = mapped_column(
        String, ForeignKey("quiz_attempts.id", ondelete="CASCADE"), nullable=False, index=True
    )
    question_id: Mapped[str] = mapped_column(String, nullable=False, index=True)
    selected_index: Mapped[int | None] = mapped_column(Integer, nullable=True)
    is_correct: Mapped[int] = mapped_column(Integer, nullable=False)

    attempt: Mapped["QuizAttempt"] = relationship("QuizAttempt", back_populates="answers")


class UserQuestionExposure(Base):
    __tablename__ = "user_question_exposure"

    user_id: Mapped[str] = mapped_column(
        String, ForeignKey("users.id", ondelete="CASCADE"), primary_key=True
    )
    question_id: Mapped[str] = mapped_column(String, primary_key=True)
    shown_at: Mapped[str] = mapped_column(String, default=utcnow_iso, nullable=False, index=True)

    user: Mapped["User"] = relationship("User")


class PathStepProgress(Base):
    __tablename__ = "path_step_progress"

    user_id: Mapped[str] = mapped_column(
        String, ForeignKey("users.id", ondelete="CASCADE"), primary_key=True
    )
    step_id: Mapped[int] = mapped_column(Integer, primary_key=True)
    completed_at: Mapped[str] = mapped_column(String, default=utcnow_iso, nullable=False)

    user: Mapped["User"] = relationship("User")


class AdminAuditLog(Base):
    __tablename__ = "admin_audit_log"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    admin_id: Mapped[str] = mapped_column(
        String, ForeignKey("users.id", ondelete="CASCADE"), nullable=False
    )
    action: Mapped[str] = mapped_column(String, nullable=False)
    target: Mapped[str] = mapped_column(String, nullable=False)
    created_at: Mapped[str] = mapped_column(String, default=utcnow_iso, nullable=False)

    admin: Mapped["User"] = relationship("User")
