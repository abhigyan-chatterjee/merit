from sqlalchemy import ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db import Base
from app.models.user import User, utcnow_iso


class ProblemProgress(Base):
    __tablename__ = "problem_progress"

    user_id: Mapped[str] = mapped_column(
        String, ForeignKey("users.id", ondelete="CASCADE"), primary_key=True
    )
    problem_slug: Mapped[str] = mapped_column(String, primary_key=True)
    status: Mapped[str] = mapped_column(String, nullable=False)  # Todo | Doing | Done
    updated_at: Mapped[str] = mapped_column(String, default=utcnow_iso, nullable=False)

    user: Mapped["User"] = relationship("User")


class Note(Base):
    __tablename__ = "notes"

    user_id: Mapped[str] = mapped_column(
        String, ForeignKey("users.id", ondelete="CASCADE"), primary_key=True
    )
    problem_slug: Mapped[str] = mapped_column(String, primary_key=True)
    text: Mapped[str] = mapped_column(Text, nullable=False)
    updated_at: Mapped[str] = mapped_column(String, default=utcnow_iso, nullable=False)

    user: Mapped["User"] = relationship("User")


class Bookmark(Base):
    __tablename__ = "bookmarks"

    user_id: Mapped[str] = mapped_column(
        String, ForeignKey("users.id", ondelete="CASCADE"), primary_key=True
    )
    item_type: Mapped[str] = mapped_column(String, primary_key=True)  # problem | visualizer | path
    item_id: Mapped[str] = mapped_column(String, primary_key=True)
    created_at: Mapped[str] = mapped_column(String, default=utcnow_iso, nullable=False)

    user: Mapped["User"] = relationship("User")


class ActivityDay(Base):
    __tablename__ = "activity_days"

    user_id: Mapped[str] = mapped_column(
        String, ForeignKey("users.id", ondelete="CASCADE"), primary_key=True
    )
    day: Mapped[str] = mapped_column(String, primary_key=True)  # YYYY-MM-DD local date
    action_count: Mapped[int] = mapped_column(Integer, default=1, nullable=False)

    user: Mapped["User"] = relationship("User")


class VisualizerCompletion(Base):
    __tablename__ = "visualizer_completions"

    user_id: Mapped[str] = mapped_column(
        String, ForeignKey("users.id", ondelete="CASCADE"), primary_key=True
    )
    visualizer_id: Mapped[str] = mapped_column(String, primary_key=True)
    visits: Mapped[int] = mapped_column(Integer, default=1, nullable=False)
    first_completed_at: Mapped[str] = mapped_column(String, default=utcnow_iso, nullable=False)

    user: Mapped["User"] = relationship("User")
