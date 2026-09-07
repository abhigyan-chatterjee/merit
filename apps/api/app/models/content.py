from sqlalchemy import ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db import Base
from app.models.user import utcnow_iso


class Problem(Base):
    __tablename__ = "problems"

    slug: Mapped[str] = mapped_column(String, primary_key=True)
    topic: Mapped[str] = mapped_column(String, nullable=False, index=True)
    difficulty: Mapped[str] = mapped_column(String, nullable=False, index=True)
    pattern: Mapped[str] = mapped_column(String, nullable=False)
    title: Mapped[str] = mapped_column(String, nullable=False)
    statement: Mapped[str] = mapped_column(Text, nullable=False)
    examples: Mapped[str] = mapped_column(Text, nullable=False)  # JSON string
    constraints_json: Mapped[str] = mapped_column(Text, nullable=False)  # JSON string
    hints: Mapped[str] = mapped_column(Text, nullable=False)  # JSON string
    starter_code: Mapped[str] = mapped_column(Text, nullable=False)  # JSON string {lang: code}
    function_name: Mapped[str] = mapped_column(String, nullable=False)
    time_limit_ms: Mapped[int] = mapped_column(Integer, default=2000, nullable=False)
    review_status: Mapped[str] = mapped_column(
        String, default="verified", nullable=False, index=True
    )
    created_at: Mapped[str] = mapped_column(String, default=utcnow_iso, nullable=False)
    updated_at: Mapped[str] = mapped_column(String, default=utcnow_iso, nullable=False)

    test_cases: Mapped[list["ProblemTestCase"]] = relationship(
        "ProblemTestCase", back_populates="problem", cascade="all, delete-orphan"
    )
    solutions: Mapped[list["ProblemSolution"]] = relationship(
        "ProblemSolution", back_populates="problem", cascade="all, delete-orphan"
    )


class ProblemTestCase(Base):
    __tablename__ = "problem_test_cases"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    problem_slug: Mapped[str] = mapped_column(
        String, ForeignKey("problems.slug", ondelete="CASCADE"), nullable=False, index=True
    )
    ordinal: Mapped[int] = mapped_column(Integer, nullable=False)
    label: Mapped[str] = mapped_column(String, nullable=False)
    input_json: Mapped[str] = mapped_column(Text, nullable=False)  # JSON array of arguments
    expected_json: Mapped[str] = mapped_column(Text, nullable=False)  # JSON string of expected
    is_sample: Mapped[int] = mapped_column(Integer, default=0, nullable=False)

    problem: Mapped["Problem"] = relationship("Problem", back_populates="test_cases")


class ProblemSolution(Base):
    __tablename__ = "problem_solutions"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    problem_slug: Mapped[str] = mapped_column(
        String, ForeignKey("problems.slug", ondelete="CASCADE"), nullable=False, index=True
    )
    title: Mapped[str] = mapped_column(String, nullable=False)
    complexity: Mapped[str] = mapped_column(String, nullable=False)
    language: Mapped[str] = mapped_column(String, default="javascript", nullable=False)
    code: Mapped[str] = mapped_column(Text, nullable=False)
    is_reference: Mapped[int] = mapped_column(Integer, default=0, nullable=False)

    problem: Mapped["Problem"] = relationship("Problem", back_populates="solutions")
