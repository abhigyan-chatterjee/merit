"""add user settings (preferred_language, daily_goal_json)

Revision ID: 7c2e9a41f5b0
Revises: 0bdbb1446b1f
Create Date: 2026-09-09

"""

from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op

revision: str = "7c2e9a41f5b0"
down_revision: str | Sequence[str] | None = "0bdbb1446b1f"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.add_column(
        "users",
        sa.Column("preferred_language", sa.String(), server_default="javascript", nullable=False),
    )
    op.add_column("users", sa.Column("daily_goal_json", sa.String(), nullable=True))


def downgrade() -> None:
    op.drop_column("users", "daily_goal_json")
    op.drop_column("users", "preferred_language")
