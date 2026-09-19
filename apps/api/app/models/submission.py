import uuid

from sqlalchemy import Float, ForeignKey, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db import Base
from app.models.user import User, utcnow_iso


class Submission(Base):
    __tablename__ = "submissions"

    id: Mapped[str] = mapped_column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id: Mapped[str] = mapped_column(
        String, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True
    )
    problem_slug: Mapped[str] = mapped_column(String, nullable=False, index=True)
    language: Mapped[str] = mapped_column(String, nullable=False)
    code: Mapped[str] = mapped_column(Text, nullable=False)
    verdict: Mapped[str] = mapped_column(String, nullable=False)  # AC | WA | TLE | RE | CE
    runtime_ms: Mapped[float] = mapped_column(Float, default=0.0, nullable=False)
    test_results: Mapped[str] = mapped_column(Text, nullable=False)  # JSON string
    created_at: Mapped[str] = mapped_column(String, default=utcnow_iso, nullable=False)

    user: Mapped["User"] = relationship("User")
