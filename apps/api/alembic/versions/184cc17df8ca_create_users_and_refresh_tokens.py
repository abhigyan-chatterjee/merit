"""create_users_and_refresh_tokens

Revision ID: 184cc17df8ca
Revises:
Create Date: 2026-09-07 21:29:13.229331

"""

from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op

revision: str = "184cc17df8ca"
down_revision: str | Sequence[str] | None = None
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def _inspector():
    return sa.inspect(op.get_bind())


def _has_table(name: str) -> bool:
    return name in _inspector().get_table_names()


def _has_index(table: str, index: str) -> bool:
    return _has_table(table) and any(
        idx["name"] == index for idx in _inspector().get_indexes(table)
    )


def upgrade() -> None:
    if not _has_table("users"):
        op.create_table(
            "users",
            sa.Column("id", sa.String(), nullable=False),
            sa.Column("email", sa.String(), nullable=False),
            sa.Column("display_name", sa.String(), nullable=False),
            sa.Column("password_hash", sa.String(), nullable=False),
            sa.Column("role", sa.String(), nullable=False),
            sa.Column("is_active", sa.Integer(), nullable=False),
            sa.Column("created_at", sa.String(), nullable=False),
            sa.Column("last_login_at", sa.String(), nullable=True),
            sa.PrimaryKeyConstraint("id"),
        )
    if not _has_index("users", "ix_users_email"):
        op.create_index("ix_users_email", "users", ["email"], unique=True)
    if not _has_table("refresh_tokens"):
        op.create_table(
            "refresh_tokens",
            sa.Column("id", sa.String(), nullable=False),
            sa.Column("user_id", sa.String(), nullable=False),
            sa.Column("token_hash", sa.String(), nullable=False),
            sa.Column("expires_at", sa.String(), nullable=False),
            sa.Column("created_at", sa.String(), nullable=False),
            sa.Column("revoked_at", sa.String(), nullable=True),
            sa.Column("replaced_by", sa.String(), nullable=True),
            sa.Column("user_agent", sa.String(), nullable=True),
            sa.Column("ip", sa.String(), nullable=True),
            sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
            sa.PrimaryKeyConstraint("id"),
        )
    if not _has_index("refresh_tokens", "ix_refresh_tokens_token_hash"):
        op.create_index("ix_refresh_tokens_token_hash", "refresh_tokens", ["token_hash"])
    if not _has_index("refresh_tokens", "ix_refresh_tokens_user_id"):
        op.create_index("ix_refresh_tokens_user_id", "refresh_tokens", ["user_id"])


def downgrade() -> None:
    if _has_index("refresh_tokens", "ix_refresh_tokens_user_id"):
        op.drop_index("ix_refresh_tokens_user_id", table_name="refresh_tokens")
    if _has_index("refresh_tokens", "ix_refresh_tokens_token_hash"):
        op.drop_index("ix_refresh_tokens_token_hash", table_name="refresh_tokens")
    if _has_table("refresh_tokens"):
        op.drop_table("refresh_tokens")
    if _has_index("users", "ix_users_email"):
        op.drop_index("ix_users_email", table_name="users")
    if _has_table("users"):
        op.drop_table("users")
