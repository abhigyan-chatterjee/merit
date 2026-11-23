"""create_questions_paths_quiz_and_admin_tables

Revision ID: 0bdbb1446b1f
Revises: a0ac26be9ac2
Create Date: 2026-09-07 21:59:55.326133

"""

from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op

revision: str = "0bdbb1446b1f"
down_revision: str | Sequence[str] | None = "a0ac26be9ac2"
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


def _ensure_index(table: str, name: str, cols: list) -> None:
    if not _has_index(table, name):
        op.create_index(name, table, cols)


def upgrade() -> None:
    if not _has_table("learning_paths"):
        op.create_table(
            "learning_paths",
            sa.Column("slug", sa.String(), nullable=False),
            sa.Column("title", sa.String(), nullable=False),
            sa.Column("blurb", sa.Text(), nullable=False),
            sa.Column("icon", sa.String(), nullable=False),
            sa.Column("track", sa.String(), nullable=False),
            sa.Column("ordinal", sa.Integer(), nullable=False),
            sa.Column("is_published", sa.Integer(), nullable=False),
            sa.PrimaryKeyConstraint("slug"),
        )
    _ensure_index("learning_paths", "ix_learning_paths_track", ["track"])
    if not _has_table("questions"):
        op.create_table(
            "questions",
            sa.Column("id", sa.String(), nullable=False),
            sa.Column("topic", sa.String(), nullable=False),
            sa.Column("subtopic", sa.String(), nullable=True),
            sa.Column("difficulty", sa.String(), nullable=False),
            sa.Column("qtype", sa.String(), nullable=False),
            sa.Column("prompt", sa.Text(), nullable=False),
            sa.Column("options", sa.Text(), nullable=False),
            sa.Column("correct_index", sa.Integer(), nullable=False),
            sa.Column("explanation", sa.Text(), nullable=False),
            sa.Column("source", sa.String(), nullable=False),
            sa.Column("generator_key", sa.String(), nullable=True),
            sa.Column("content_hash", sa.String(), nullable=False),
            sa.Column("review_status", sa.String(), nullable=False),
            sa.Column("created_at", sa.String(), nullable=False),
            sa.Column("updated_at", sa.String(), nullable=False),
            sa.PrimaryKeyConstraint("id"),
        )
    _ensure_index("questions", "ix_questions_content_hash", ["content_hash"])
    _ensure_index("questions", "ix_questions_difficulty", ["difficulty"])
    _ensure_index("questions", "ix_questions_review_status", ["review_status"])
    _ensure_index("questions", "ix_questions_topic", ["topic"])
    if not _has_table("admin_audit_log"):
        op.create_table(
            "admin_audit_log",
            sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
            sa.Column("admin_id", sa.String(), nullable=False),
            sa.Column("action", sa.String(), nullable=False),
            sa.Column("target", sa.String(), nullable=False),
            sa.Column("created_at", sa.String(), nullable=False),
            sa.ForeignKeyConstraint(["admin_id"], ["users.id"], ondelete="CASCADE"),
            sa.PrimaryKeyConstraint("id"),
        )
    if not _has_table("path_step_progress"):
        op.create_table(
            "path_step_progress",
            sa.Column("user_id", sa.String(), nullable=False),
            sa.Column("step_id", sa.Integer(), nullable=False),
            sa.Column("completed_at", sa.String(), nullable=False),
            sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
            sa.PrimaryKeyConstraint("user_id", "step_id"),
        )
    if not _has_table("path_steps"):
        op.create_table(
            "path_steps",
            sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
            sa.Column("path_slug", sa.String(), nullable=False),
            sa.Column("ordinal", sa.Integer(), nullable=False),
            sa.Column("step_type", sa.String(), nullable=False),
            sa.Column("ref_id", sa.String(), nullable=False),
            sa.Column("title", sa.String(), nullable=True),
            sa.ForeignKeyConstraint(["path_slug"], ["learning_paths.slug"], ondelete="CASCADE"),
            sa.PrimaryKeyConstraint("id"),
        )
    _ensure_index("path_steps", "ix_path_steps_path_slug", ["path_slug"])
    if not _has_table("question_reviews"):
        op.create_table(
            "question_reviews",
            sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
            sa.Column("question_id", sa.String(), nullable=False),
            sa.Column("reviewer_id", sa.String(), nullable=False),
            sa.Column("action", sa.String(), nullable=False),
            sa.Column("note", sa.Text(), nullable=True),
            sa.Column("created_at", sa.String(), nullable=False),
            sa.ForeignKeyConstraint(["question_id"], ["questions.id"], ondelete="CASCADE"),
            sa.ForeignKeyConstraint(["reviewer_id"], ["users.id"], ondelete="CASCADE"),
            sa.PrimaryKeyConstraint("id"),
        )
    _ensure_index("question_reviews", "ix_question_reviews_question_id", ["question_id"])
    _ensure_index("question_reviews", "ix_question_reviews_reviewer_id", ["reviewer_id"])
    if not _has_table("quiz_attempts"):
        op.create_table(
            "quiz_attempts",
            sa.Column("id", sa.String(), nullable=False),
            sa.Column("user_id", sa.String(), nullable=False),
            sa.Column("topic_spec", sa.Text(), nullable=False),
            sa.Column("question_ids", sa.Text(), nullable=False),
            sa.Column("total", sa.Integer(), nullable=False),
            sa.Column("correct", sa.Integer(), nullable=False),
            sa.Column("score_pct", sa.Integer(), nullable=False),
            sa.Column("duration_sec", sa.Integer(), nullable=False),
            sa.Column("created_at", sa.String(), nullable=False),
            sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
            sa.PrimaryKeyConstraint("id"),
        )
    _ensure_index("quiz_attempts", "ix_quiz_attempts_created_at", ["created_at"])
    _ensure_index("quiz_attempts", "ix_quiz_attempts_user_id", ["user_id"])
    if not _has_table("user_question_exposure"):
        op.create_table(
            "user_question_exposure",
            sa.Column("user_id", sa.String(), nullable=False),
            sa.Column("question_id", sa.String(), nullable=False),
            sa.Column("shown_at", sa.String(), nullable=False),
            sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
            sa.PrimaryKeyConstraint("user_id", "question_id"),
        )
    _ensure_index("user_question_exposure", "ix_user_question_exposure_shown_at", ["shown_at"])
    if not _has_table("quiz_attempt_answers"):
        op.create_table(
            "quiz_attempt_answers",
            sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
            sa.Column("attempt_id", sa.String(), nullable=False),
            sa.Column("question_id", sa.String(), nullable=False),
            sa.Column("selected_index", sa.Integer(), nullable=True),
            sa.Column("is_correct", sa.Integer(), nullable=False),
            sa.ForeignKeyConstraint(["attempt_id"], ["quiz_attempts.id"], ondelete="CASCADE"),
            sa.PrimaryKeyConstraint("id"),
        )
    _ensure_index("quiz_attempt_answers", "ix_quiz_attempt_answers_attempt_id", ["attempt_id"])
    _ensure_index(
        "quiz_attempt_answers", "ix_quiz_attempt_answers_question_id", ["question_id"]
    )


def downgrade() -> None:
    for table, indexes in (
        (
            "quiz_attempt_answers",
            ("ix_quiz_attempt_answers_question_id", "ix_quiz_attempt_answers_attempt_id"),
        ),
        ("user_question_exposure", ("ix_user_question_exposure_shown_at",)),
        ("quiz_attempts", ("ix_quiz_attempts_user_id", "ix_quiz_attempts_created_at")),
        (
            "question_reviews",
            ("ix_question_reviews_reviewer_id", "ix_question_reviews_question_id"),
        ),
        ("path_steps", ("ix_path_steps_path_slug",)),
    ):
        for name in indexes:
            if _has_index(table, name):
                op.drop_index(name, table_name=table)
        if _has_table(table):
            op.drop_table(table)
    for table in ("path_step_progress", "admin_audit_log"):
        if _has_table(table):
            op.drop_table(table)
    for name in (
        "ix_questions_topic",
        "ix_questions_review_status",
        "ix_questions_difficulty",
        "ix_questions_content_hash",
    ):
        if _has_index("questions", name):
            op.drop_index(name, table_name="questions")
    if _has_table("questions"):
        op.drop_table("questions")
    if _has_index("learning_paths", "ix_learning_paths_track"):
        op.drop_index("ix_learning_paths_track", table_name="learning_paths")
    if _has_table("learning_paths"):
        op.drop_table("learning_paths")
