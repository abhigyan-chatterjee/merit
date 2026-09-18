"""add problem editorial and reading links

Revision ID: b7c1d9e4a2f5
Revises: 9e4a5c28d7f2
Create Date: 2026-09-18

"""

from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op

revision: str = "b7c1d9e4a2f5"
down_revision: str | Sequence[str] | None = "9e4a5c28d7f2"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.add_column("problems", sa.Column("editorial_json", sa.Text(), nullable=True))
    op.add_column("problems", sa.Column("reading_links_json", sa.Text(), nullable=True))


def downgrade() -> None:
    op.drop_column("problems", "reading_links_json")
    op.drop_column("problems", "editorial_json")
