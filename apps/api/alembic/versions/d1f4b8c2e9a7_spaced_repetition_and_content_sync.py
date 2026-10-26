"""spaced repetition and content sync fingerprint

Revision ID: d1f4b8c2e9a7
Revises: 42c0c100af20
Create Date: 2026-10-26

Two related additions:

* ``revision_items`` — the SM-2 schedule. Without a table, "review" was a list
  recomputed from the last few submissions on every request, with no due date.
* ``content_sync`` — the fingerprint of the content tree as of the last seed, so
  a boot can tell whether a content commit actually changed anything.

Every step is guarded with a reflection check, which makes the revision
re-runnable. That is not defensive habit: the API calls
``Base.metadata.create_all()`` in its lifespan, which creates missing tables but
records nothing in Alembic. A database that booted once before this revision ran
therefore already holds these tables, and an unguarded revision then fails with
"table revision_items already exists" and refuses to start. The guard lets the
same revision finish a half-applied database instead of deadlocking on it.
"""

from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op

revision: str = "d1f4b8c2e9a7"
down_revision: str | Sequence[str] | None = "42c0c100af20"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def _inspector():
    return sa.inspect(op.get_bind())


def _has_table(name: str) -> bool:
    return name in _inspector().get_table_names()


def _has_index(table: str, index: str) -> bool:
    if not _has_table(table):
        return False
    return any(idx["name"] == index for idx in _inspector().get_indexes(table))


def upgrade() -> None:
    if not _has_table("revision_items"):
        op.create_table(
            "revision_items",
            sa.Column("id", sa.String(), nullable=False),
            sa.Column("user_id", sa.String(), nullable=False),
            sa.Column("item_type", sa.String(), nullable=False),
            sa.Column("item_id", sa.String(), nullable=False),
            sa.Column("due_date", sa.String(), nullable=False),
            sa.Column("interval_days", sa.Integer(), nullable=False, server_default="0"),
            sa.Column("ease", sa.Float(), nullable=False, server_default="2.5"),
            sa.Column("reps", sa.Integer(), nullable=False, server_default="0"),
            sa.Column("lapses", sa.Integer(), nullable=False, server_default="0"),
            sa.Column("last_reviewed_at", sa.String(), nullable=True),
            sa.Column("created_at", sa.String(), nullable=False),
            sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
            sa.PrimaryKeyConstraint("id"),
            sa.UniqueConstraint(
                "user_id", "item_type", "item_id", name="uq_revision_item"
            ),
        )

    # Indexes are created separately and guarded, so a table that came from
    # create_all still ends up with them.
    if not _has_index("revision_items", "ix_revision_items_user_id"):
        op.create_index("ix_revision_items_user_id", "revision_items", ["user_id"])
    if not _has_index("revision_items", "ix_revision_items_due_date"):
        op.create_index("ix_revision_items_due_date", "revision_items", ["due_date"])

    if not _has_table("content_sync"):
        op.create_table(
            "content_sync",
            sa.Column("key", sa.String(), nullable=False),
            sa.Column("fingerprint", sa.String(), nullable=False),
            sa.Column("synced_at", sa.String(), nullable=False),
            sa.PrimaryKeyConstraint("key"),
        )



def downgrade() -> None:
    if _has_table("content_sync"):
        op.drop_table("content_sync")

    if _has_index("revision_items", "ix_revision_items_due_date"):
        op.drop_index("ix_revision_items_due_date", table_name="revision_items")
    if _has_index("revision_items", "ix_revision_items_user_id"):
        op.drop_index("ix_revision_items_user_id", table_name="revision_items")
    if _has_table("revision_items"):
        op.drop_table("revision_items")
