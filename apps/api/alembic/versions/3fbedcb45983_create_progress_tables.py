"""create_progress_tables

Revision ID: 3fbedcb45983
Revises: 184cc17df8ca
Create Date: 2026-09-07 21:39:33.239190

"""

from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op

revision: str = "3fbedcb45983"
down_revision: str | Sequence[str] | None = "184cc17df8ca"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def _inspector():
    return sa.inspect(op.get_bind())


def _has_table(name: str) -> bool:
    return name in _inspector().get_table_names()


def _has_column(table: str, column: str) -> bool:
    return _has_table(table) and any(
        c["name"] == column for c in _inspector().get_columns(table)
    )


def upgrade() -> None:
    if not _has_table("activity_days"):
        op.create_table(
            "activity_days",
            sa.Column("user_id", sa.String(), nullable=False),
            sa.Column("day", sa.String(), nullable=False),
            sa.Column("action_count", sa.Integer(), nullable=False),
            sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
            sa.PrimaryKeyConstraint("user_id", "day"),
        )
    if not _has_table("bookmarks"):
        op.create_table(
            "bookmarks",
            sa.Column("user_id", sa.String(), nullable=False),
            sa.Column("item_type", sa.String(), nullable=False),
            sa.Column("item_id", sa.String(), nullable=False),
            sa.Column("created_at", sa.String(), nullable=False),
            sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
            sa.PrimaryKeyConstraint("user_id", "item_type", "item_id"),
        )
    if not _has_table("notes"):
        op.create_table(
            "notes",
            sa.Column("user_id", sa.String(), nullable=False),
            sa.Column("problem_slug", sa.String(), nullable=False),
            sa.Column("text", sa.Text(), nullable=False),
            sa.Column("updated_at", sa.String(), nullable=False),
            sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
            sa.PrimaryKeyConstraint("user_id", "problem_slug"),
        )
    if not _has_table("problem_progress"):
        op.create_table(
            "problem_progress",
            sa.Column("user_id", sa.String(), nullable=False),
            sa.Column("problem_slug", sa.String(), nullable=False),
            sa.Column("status", sa.String(), nullable=False),
            sa.Column("updated_at", sa.String(), nullable=False),
            sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
            sa.PrimaryKeyConstraint("user_id", "problem_slug"),
        )
    if not _has_table("visualizer_completions"):
        op.create_table(
            "visualizer_completions",
            sa.Column("user_id", sa.String(), nullable=False),
            sa.Column("visualizer_id", sa.String(), nullable=False),
            sa.Column("visits", sa.Integer(), nullable=False),
            sa.Column("first_completed_at", sa.String(), nullable=False),
            sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
            sa.PrimaryKeyConstraint("user_id", "visualizer_id"),
        )
    if not _has_column("users", "has_imported_local"):
        op.add_column(
            "users",
            sa.Column("has_imported_local", sa.Integer(), server_default="0", nullable=False),
        )


def downgrade() -> None:
    if _has_column("users", "has_imported_local"):
        op.drop_column("users", "has_imported_local")
    for table in (
        "visualizer_completions",
        "problem_progress",
        "notes",
        "bookmarks",
        "activity_days",
    ):
        if _has_table(table):
            op.drop_table(table)
