"""add path step summaries and reading links

Revision ID: 9e4a5c28d7f2
Revises: 8d3f2b17c6a1
Create Date: 2026-09-09

"""

from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op

revision: str = "9e4a5c28d7f2"
down_revision: str | Sequence[str] | None = "8d3f2b17c6a1"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def _inspector():
    return sa.inspect(op.get_bind())


def _has_column(table: str, column: str) -> bool:
    if table not in _inspector().get_table_names():
        return False
    return any(c["name"] == column for c in _inspector().get_columns(table))


def upgrade() -> None:
    if not _has_column("path_steps", "summary"):
        op.add_column("path_steps", sa.Column("summary", sa.Text(), nullable=True))
    if not _has_column("path_steps", "reading_links_json"):
        op.add_column(
            "path_steps",
            sa.Column("reading_links_json", sa.Text(), server_default="[]", nullable=False),
        )


def downgrade() -> None:
    if _has_column("path_steps", "reading_links_json"):
        op.drop_column("path_steps", "reading_links_json")
    if _has_column("path_steps", "summary"):
        op.drop_column("path_steps", "summary")
