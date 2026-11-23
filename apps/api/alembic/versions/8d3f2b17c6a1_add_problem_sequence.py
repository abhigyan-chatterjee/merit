"""add problem sequence links (sequence, prev_slug, next_slug)

Revision ID: 8d3f2b17c6a1
Revises: 7c2e9a41f5b0
Create Date: 2026-09-09

"""

from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op

revision: str = "8d3f2b17c6a1"
down_revision: str | Sequence[str] | None = "7c2e9a41f5b0"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def _inspector():
    return sa.inspect(op.get_bind())


def _has_column(table: str, column: str) -> bool:
    if table not in _inspector().get_table_names():
        return False
    return any(c["name"] == column for c in _inspector().get_columns(table))


def upgrade() -> None:
    for name, col in (
        ("sequence", sa.Column("sequence", sa.Integer(), nullable=True)),
        ("prev_slug", sa.Column("prev_slug", sa.String(), nullable=True)),
        ("next_slug", sa.Column("next_slug", sa.String(), nullable=True)),
    ):
        if not _has_column("problems", name):
            op.add_column("problems", col)


def downgrade() -> None:
    for name in ("next_slug", "prev_slug", "sequence"):
        if _has_column("problems", name):
            op.drop_column("problems", name)
