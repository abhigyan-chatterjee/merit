"""create_problems_and_submissions_tables

Revision ID: a0ac26be9ac2
Revises: 3fbedcb45983
Create Date: 2026-09-07 21:47:35.669345

"""

from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op

revision: str = "a0ac26be9ac2"
down_revision: str | Sequence[str] | None = "3fbedcb45983"
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
    if not _has_table("problems"):
        op.create_table(
            "problems",
            sa.Column("slug", sa.String(), nullable=False),
            sa.Column("topic", sa.String(), nullable=False),
            sa.Column("difficulty", sa.String(), nullable=False),
            sa.Column("pattern", sa.String(), nullable=False),
            sa.Column("title", sa.String(), nullable=False),
            sa.Column("statement", sa.Text(), nullable=False),
            sa.Column("examples", sa.Text(), nullable=False),
            sa.Column("constraints_json", sa.Text(), nullable=False),
            sa.Column("hints", sa.Text(), nullable=False),
            sa.Column("starter_code", sa.Text(), nullable=False),
            sa.Column("function_name", sa.String(), nullable=False),
            sa.Column("time_limit_ms", sa.Integer(), nullable=False),
            sa.Column("review_status", sa.String(), nullable=False),
            sa.Column("created_at", sa.String(), nullable=False),
            sa.Column("updated_at", sa.String(), nullable=False),
            sa.PrimaryKeyConstraint("slug"),
        )
    for name, cols in (
        ("ix_problems_difficulty", ["difficulty"]),
        ("ix_problems_review_status", ["review_status"]),
        ("ix_problems_topic", ["topic"]),
    ):
        if not _has_index("problems", name):
            op.create_index(name, "problems", cols)
    if not _has_table("problem_solutions"):
        op.create_table(
            "problem_solutions",
            sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
            sa.Column("problem_slug", sa.String(), nullable=False),
            sa.Column("title", sa.String(), nullable=False),
            sa.Column("complexity", sa.String(), nullable=False),
            sa.Column("language", sa.String(), nullable=False),
            sa.Column("code", sa.Text(), nullable=False),
            sa.Column("is_reference", sa.Integer(), nullable=False),
            sa.ForeignKeyConstraint(["problem_slug"], ["problems.slug"], ondelete="CASCADE"),
            sa.PrimaryKeyConstraint("id"),
        )
    if not _has_index("problem_solutions", "ix_problem_solutions_problem_slug"):
        op.create_index(
            "ix_problem_solutions_problem_slug", "problem_solutions", ["problem_slug"]
        )
    if not _has_table("problem_test_cases"):
        op.create_table(
            "problem_test_cases",
            sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
            sa.Column("problem_slug", sa.String(), nullable=False),
            sa.Column("ordinal", sa.Integer(), nullable=False),
            sa.Column("label", sa.String(), nullable=False),
            sa.Column("input_json", sa.Text(), nullable=False),
            sa.Column("expected_json", sa.Text(), nullable=False),
            sa.Column("is_sample", sa.Integer(), nullable=False),
            sa.ForeignKeyConstraint(["problem_slug"], ["problems.slug"], ondelete="CASCADE"),
            sa.PrimaryKeyConstraint("id"),
        )
    if not _has_index("problem_test_cases", "ix_problem_test_cases_problem_slug"):
        op.create_index(
            "ix_problem_test_cases_problem_slug", "problem_test_cases", ["problem_slug"]
        )
    if not _has_table("submissions"):
        op.create_table(
            "submissions",
            sa.Column("id", sa.String(), nullable=False),
            sa.Column("user_id", sa.String(), nullable=False),
            sa.Column("problem_slug", sa.String(), nullable=False),
            sa.Column("language", sa.String(), nullable=False),
            sa.Column("code", sa.Text(), nullable=False),
            sa.Column("verdict", sa.String(), nullable=False),
            sa.Column("runtime_ms", sa.Float(), nullable=False),
            sa.Column("test_results", sa.Text(), nullable=False),
            sa.Column("created_at", sa.String(), nullable=False),
            sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
            sa.PrimaryKeyConstraint("id"),
        )
    for name, cols in (
        ("ix_submissions_problem_slug", ["problem_slug"]),
        ("ix_submissions_user_id", ["user_id"]),
    ):
        if not _has_index("submissions", name):
            op.create_index(name, "submissions", cols)


def downgrade() -> None:
    for table, indexes in (
        ("submissions", ("ix_submissions_user_id", "ix_submissions_problem_slug")),
        ("problem_test_cases", ("ix_problem_test_cases_problem_slug",)),
        ("problem_solutions", ("ix_problem_solutions_problem_slug",)),
        (
            "problems",
            ("ix_problems_topic", "ix_problems_review_status", "ix_problems_difficulty"),
        ),
    ):
        for name in indexes:
            if _has_index(table, name):
                op.drop_index(name, table_name=table)
        if _has_table(table):
            op.drop_table(table)
