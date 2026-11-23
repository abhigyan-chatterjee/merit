"""unique quiz answers per attempt and preferred_language default

Revision ID: e5a1b2c3d4f6
Revises: d1f4b8c2e9a7
Create Date: 2026-11-22

"""

from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op

revision: str = "e5a1b2c3d4f6"
down_revision: str | Sequence[str] | None = "d1f4b8c2e9a7"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def _inspector():
    return sa.inspect(op.get_bind())


def _has_index(table: str, index: str) -> bool:
    if table not in _inspector().get_table_names():
        return False
    return any(idx["name"] == index for idx in _inspector().get_indexes(table))


def upgrade() -> None:
    if not _has_index("quiz_attempt_answers", "uq_quiz_attempt_answers_attempt_question"):
        op.create_index(
            "uq_quiz_attempt_answers_attempt_question",
            "quiz_attempt_answers",
            ["attempt_id", "question_id"],
            unique=True,
        )
    if op.get_bind().dialect.name != "sqlite" and "users" in _inspector().get_table_names():
        cols = [c["name"] for c in _inspector().get_columns("users")]
        if "preferred_language" in cols:
            op.alter_column(
                "users",
                "preferred_language",
                existing_type=sa.String(),
                server_default="python",
            )


def downgrade() -> None:
    if _has_index("quiz_attempt_answers", "uq_quiz_attempt_answers_attempt_question"):
        op.drop_index(
            "uq_quiz_attempt_answers_attempt_question", table_name="quiz_attempt_answers"
        )
