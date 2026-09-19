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


def upgrade() -> None:
    op.add_column("users", sa.Column("clerk_id", sa.String(), nullable=True))
    # Unique index (not a table constraint: SQLite cannot ALTER in constraints).
    # SQLite unique indexes permit multiple NULLs, so unlinked rows are unaffected.
    op.create_index("uq_users_clerk_id", "users", ["clerk_id"], unique=True)
    op.add_column(
        "users",
        sa.Column("auth_provider", sa.String(), server_default="password", nullable=False),
    )


def downgrade() -> None:
    op.drop_column("users", "auth_provider")
    op.drop_index("uq_users_clerk_id", table_name="users")
    op.drop_column("users", "clerk_id")
