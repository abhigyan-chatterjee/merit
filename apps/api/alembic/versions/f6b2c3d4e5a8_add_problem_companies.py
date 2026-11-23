"""add problem companies

Revision ID: f6b2c3d4e5a8
Revises: e5a1b2c3d4f6
Create Date: 2026-11-23

"""

from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op

revision: str = "f6b2c3d4e5a8"
down_revision: str | Sequence[str] | None = "e5a1b2c3d4f6"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def _inspector():
    return sa.inspect(op.get_bind())


def _has_column(table: str, column: str) -> bool:
    if table not in _inspector().get_table_names():
        return False
    return any(c["name"] == column for c in _inspector().get_columns(table))


def upgrade() -> None:
    if not _has_column("problems", "companies_json"):
        op.add_column("problems", sa.Column("companies_json", sa.Text(), nullable=True))


def downgrade() -> None:
    if _has_column("problems", "companies_json"):
        op.drop_column("problems", "companies_json")
