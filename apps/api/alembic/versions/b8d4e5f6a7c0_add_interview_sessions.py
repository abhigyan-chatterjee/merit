"""add interview sessions

Revision ID: b8d4e5f6a7c0
Revises: a7c3d4e5f6b9
Create Date: 2026-11-23

"""

from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op

revision: str = "b8d4e5f6a7c0"
down_revision: str | Sequence[str] | None = "a7c3d4e5f6b9"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def _inspector():
    return sa.inspect(op.get_bind())


def _has_table(name: str) -> bool:
    return name in _inspector().get_table_names()


def _has_index(table: str, index: str) -> bool:
    if not _has_table(table):
        return False
    return any(idx["name"] == index for idx in _inspector().get_indexes(table))


def upgrade() -> None:
    if not _has_table("interview_sessions"):
        op.create_table(
            "interview_sessions",
            sa.Column("id", sa.String(), nullable=False),
            sa.Column("user_id", sa.String(), nullable=False),
            sa.Column("difficulty", sa.String(), nullable=False),
            sa.Column(
                "status", sa.String(), nullable=False, server_default="in_progress"
            ),
            sa.Column("current_stage", sa.String(), nullable=False),
            sa.Column("duration_sec", sa.Integer(), nullable=False),
            sa.Column("elapsed_sec", sa.Integer(), nullable=False, server_default="0"),
            sa.Column("problem_slugs_json", sa.Text(), nullable=False, server_default="[]"),
            sa.Column("messages_json", sa.Text(), nullable=False, server_default="[]"),
            sa.Column(
                "coding_snapshots_json", sa.Text(), nullable=False, server_default="{}"
            ),
            sa.Column("resume_filename", sa.String(), nullable=True),
            sa.Column("resume_text", sa.Text(), nullable=True),
            sa.Column("project_brief", sa.Text(), nullable=True),
            sa.Column("rubric_json", sa.Text(), nullable=True),
            sa.Column("overall_verdict", sa.String(), nullable=True),
            sa.Column("overall_score", sa.Integer(), nullable=True),
            sa.Column("max_score", sa.Integer(), nullable=True),
            sa.Column("created_at", sa.String(), nullable=False),
            sa.Column("updated_at", sa.String(), nullable=False),
            sa.Column("completed_at", sa.String(), nullable=True),
            sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
            sa.PrimaryKeyConstraint("id"),
        )

    if not _has_index("interview_sessions", "ix_interview_sessions_user_id"):
        op.create_index(
            "ix_interview_sessions_user_id", "interview_sessions", ["user_id"]
        )
    if not _has_index("interview_sessions", "ix_interview_sessions_created_at"):
        op.create_index(
            "ix_interview_sessions_created_at", "interview_sessions", ["created_at"]
        )


def downgrade() -> None:
    if _has_index("interview_sessions", "ix_interview_sessions_created_at"):
        op.drop_index(
            "ix_interview_sessions_created_at", table_name="interview_sessions"
        )
    if _has_index("interview_sessions", "ix_interview_sessions_user_id"):
        op.drop_index("ix_interview_sessions_user_id", table_name="interview_sessions")
    if _has_table("interview_sessions"):
        op.drop_table("interview_sessions")
