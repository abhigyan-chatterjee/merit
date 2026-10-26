import uuid

from sqlalchemy import Float, ForeignKey, Integer, String, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column

from app.db import Base
from app.models.user import utcnow_iso


class RevisionItem(Base):
    """One scheduled review of one problem or quiz question, per user.

    SuperMemo-2 state lives here. The previous implementation had no table at
    all: `revision_due` was recomputed on every request from the last few
    submissions, with a hardcoded "1d review" label and no due date, so nothing
    was ever actually scheduled and nothing survived a restart.

    `due_date` is a plain YYYY-MM-DD string like every other date in this schema,
    which keeps SQLite and Postgres comparisons identical.
    """

    __tablename__ = "revision_items"
    __table_args__ = (
        UniqueConstraint("user_id", "item_type", "item_id", name="uq_revision_item"),
    )

    id: Mapped[str] = mapped_column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id: Mapped[str] = mapped_column(
        String, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True
    )
    #: "problem" | "question"
    item_type: Mapped[str] = mapped_column(String, nullable=False)
    #: problem slug, or quiz question id
    item_id: Mapped[str] = mapped_column(String, nullable=False)

    due_date: Mapped[str] = mapped_column(String, nullable=False, index=True)
    interval_days: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    ease: Mapped[float] = mapped_column(Float, default=2.5, nullable=False)
    reps: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    lapses: Mapped[int] = mapped_column(Integer, default=0, nullable=False)

    last_reviewed_at: Mapped[str | None] = mapped_column(String, nullable=True)
    created_at: Mapped[str] = mapped_column(String, default=utcnow_iso, nullable=False)
