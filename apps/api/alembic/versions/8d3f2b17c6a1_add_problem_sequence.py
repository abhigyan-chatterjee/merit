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


def upgrade() -> None:
    op.add_column("problems", sa.Column("sequence", sa.Integer(), nullable=True))
    op.add_column("problems", sa.Column("prev_slug", sa.String(), nullable=True))
    op.add_column("problems", sa.Column("next_slug", sa.String(), nullable=True))


def downgrade() -> None:
    op.drop_column("problems", "next_slug")
    op.drop_column("problems", "prev_slug")
    op.drop_column("problems", "sequence")
