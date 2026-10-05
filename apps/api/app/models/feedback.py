from datetime import UTC, datetime
from uuid import uuid4

from sqlalchemy import Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.db import Base


def utcnow_iso() -> str:
    return datetime.now(UTC).isoformat()


class Feedback(Base):
    __tablename__ = "feedbacks"

    id: Mapped[str] = mapped_column(String, primary_key=True, default=lambda: str(uuid4()))
    category: Mapped[str] = mapped_column(String, nullable=False, default="bug")
    title: Mapped[str] = mapped_column(String, nullable=False)
    description: Mapped[str] = mapped_column(Text, nullable=False)
    page_url: Mapped[str | None] = mapped_column(String, nullable=True)
    problem_slug: Mapped[str | None] = mapped_column(String, nullable=True)
    email: Mapped[str | None] = mapped_column(String, nullable=True)
    github_issue_url: Mapped[str | None] = mapped_column(String, nullable=True)
    github_issue_number: Mapped[int | None] = mapped_column(Integer, nullable=True)
    # open | resolved | dismissed
    status: Mapped[str] = mapped_column(String, nullable=False, default="open")
    created_at: Mapped[str] = mapped_column(String, nullable=False, default=utcnow_iso)
