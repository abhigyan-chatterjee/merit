"""create_feedbacks_table

Revision ID: 42c0c100af20
Revises: c4f1a2b3d4e5
Create Date: 2026-09-21

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '42c0c100af20'
down_revision: Union[str, Sequence[str], None] = 'c4f1a2b3d4e5'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        'feedbacks',
        sa.Column('id', sa.String(), nullable=False),
        sa.Column('category', sa.String(), nullable=False),
        sa.Column('title', sa.String(), nullable=False),
        sa.Column('description', sa.Text(), nullable=False),
        sa.Column('page_url', sa.String(), nullable=True),
        sa.Column('problem_slug', sa.String(), nullable=True),
        sa.Column('email', sa.String(), nullable=True),
        sa.Column('github_issue_url', sa.String(), nullable=True),
        sa.Column('github_issue_number', sa.Integer(), nullable=True),
        sa.Column('status', sa.String(), nullable=False, server_default='open'),
        sa.Column('created_at', sa.String(), nullable=False),
        sa.PrimaryKeyConstraint('id')
    )


def downgrade() -> None:
    op.drop_table('feedbacks')
