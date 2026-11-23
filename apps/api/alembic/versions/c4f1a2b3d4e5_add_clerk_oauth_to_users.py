"""add Clerk OAuth linkage to users (clerk_id, auth_provider)

Revision ID: c4f1a2b3d4e5
Revises: b7c1d9e4a2f5
Create Date: 2026-09-19

"""

from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op

revision: str = "c4f1a2b3d4e5"
down_revision: str | Sequence[str] | None = "b7c1d9e4a2f5"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def _inspector():
    return sa.inspect(op.get_bind())


def _has_column(table: str, column: str) -> bool:
    if table not in _inspector().get_table_names():
        return False
    return any(c["name"] == column for c in _inspector().get_columns(table))


def _has_index(table: str, index: str) -> bool:
    if table not in _inspector().get_table_names():
        return False
    return any(idx["name"] == index for idx in _inspector().get_indexes(table))


def upgrade() -> None:
    if not _has_column("users", "clerk_id"):
        op.add_column("users", sa.Column("clerk_id", sa.String(), nullable=True))
    # Unique index (not a table constraint: SQLite cannot ALTER in constraints).
    # SQLite unique indexes permit multiple NULLs, so unlinked rows are unaffected.
    if not _has_index("users", "uq_users_clerk_id"):
        op.create_index("uq_users_clerk_id", "users", ["clerk_id"], unique=True)
    if not _has_column("users", "auth_provider"):
        op.add_column(
            "users",
            sa.Column("auth_provider", sa.String(), server_default="password", nullable=False),
        )


def downgrade() -> None:
    if _has_column("users", "auth_provider"):
        op.drop_column("users", "auth_provider")
    if _has_index("users", "uq_users_clerk_id"):
        op.drop_index("uq_users_clerk_id", table_name="users")
    if _has_column("users", "clerk_id"):
        op.drop_column("users", "clerk_id")
