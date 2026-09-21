from datetime import datetime, timezone
from typing import Optional
from uuid import uuid4

from sqlalchemy import Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.db import Base


def utcnow_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


class Feedback(Base):
    __tablename__ = "feedbacks"

    id: Mapped[str] = mapped_column(String, primary_key=True, default=lambda: str(uuid4()))
    category: Mapped[str] = mapped_column(String, nullable=False, default="bug")
    title: Mapped[str] = mapped_column(String, nullable=False)
    description: Mapped[str] = mapped_column(Text, nullable=False)
    page_url: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    problem_slug: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    email: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    github_issue_url: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    github_issue_number: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    status: Mapped[str] = mapped_column(String, nullable=False, default="open")  # open, resolved, dismissed
    created_at: Mapped[str] = mapped_column(String, nullable=False, default=utcnow_iso)
