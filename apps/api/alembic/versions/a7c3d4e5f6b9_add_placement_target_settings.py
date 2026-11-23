"""add placement target settings

Revision ID: a7c3d4e5f6b9
Revises: f6b2c3d4e5a8
Create Date: 2026-11-23

"""

from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op

revision: str = "a7c3d4e5f6b9"
down_revision: str | Sequence[str] | None = "f6b2c3d4e5a8"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def _inspector():
    return sa.inspect(op.get_bind())


def _has_table(table: str) -> bool:
    return table in _inspector().get_table_names()


def _has_column(table: str, column: str) -> bool:
    if not _has_table(table):
        return False
    return any(c["name"] == column for c in _inspector().get_columns(table))


def upgrade() -> None:
    if _has_table("users"):
        if not _has_column("users", "target_drive_date"):
            op.add_column("users", sa.Column("target_drive_date", sa.String(), nullable=True))
        if not _has_column("users", "target_tier"):
            op.add_column(
                "users",
                sa.Column(
                    "target_tier",
                    sa.String(),
                    nullable=False,
                    server_default="product",
                ),
            )


def downgrade() -> None:
    if _has_column("users", "target_tier"):
        op.drop_column("users", "target_tier")
    if _has_column("users", "target_drive_date"):
        op.drop_column("users", "target_drive_date")
