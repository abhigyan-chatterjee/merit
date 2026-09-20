"""Pydantic schemas for validating content artifacts (problems, questions, paths)."""

import hashlib
import re
import sys
from pathlib import Path
from typing import Any, Literal

from pydantic import BaseModel, Field, field_validator, model_validator

_repo_root = Path(__file__).resolve().parent.parent.parent
if str(_repo_root) not in sys.path:
    sys.path.insert(0, str(_repo_root))

from content.taxonomy import CATEGORY_SLUGS

ProblemTopic = Literal[
    "arrays-hashing",
    "two-pointers",
    "sliding-windows",
    "stack",
    "linked-lists",
    "binary-search",
    "trees",
    "heap",
    "backtracking",
    "graphs",
    "dynamic-programming",
    "greedy",
    "trie",
    "intervals",
    "math-matrices",
    "bit-manipulation",
    "sorting",
    "data-structures",
]


def compute_content_hash(text: str) -> str:
    """Compute sha256 of lowercase alphanumeric normalized text."""
    normalized = re.sub(r"\s+", " ", text.strip().lower())
    return hashlib.sha256(normalized.encode("utf-8")).hexdigest()


class TestCaseSchema(BaseModel):
    label: str = Field(..., min_length=1)
    input: list[Any]
    expected: Any
    is_sample: bool = Field(default=False, alias="isSample")

    model_config = {"populate_by_name": True}


class SolutionSchema(BaseModel):
    title: str = Field(..., min_length=1)
    complexity: str = Field(..., min_length=1)
    language: str = Field(default="javascript")
    code: str = Field(..., min_length=1)
    is_reference: bool = Field(default=False, alias="isReference")

    model_config = {"populate_by_name": True}


class ProblemSchema(BaseModel):
    slug: str = Field(..., min_length=1)
    topic: ProblemTopic
    difficulty: Literal["Easy", "Medium", "Hard"]
    pattern: str = Field(..., min_length=1)
    title: str = Field(..., min_length=1)
    statement: str = Field(..., min_length=10)
    examples: list[dict[str, Any]] = Field(..., min_length=1)
    constraints: list[str] = Field(..., min_length=1)
    hints: list[str] = Field(..., min_length=2)
    starter_code: dict[str, str] | str = Field(..., alias="starterCode")
    function_name: str = Field(default="solve", alias="functionName")
    time_limit_ms: int = Field(default=2000, ge=500, le=10000, alias="timeLimitMs")
    review_status: Literal["draft", "verified"] = Field(default="verified", alias="reviewStatus")
    test_cases: list[TestCaseSchema] = Field(..., min_length=3, alias="testCases")
    solutions: list[SolutionSchema] = Field(..., min_length=1)
    sequence: int | None = Field(default=None, ge=1)
    prev_slug: str | None = Field(default=None, alias="prevSlug")
    next_slug: str | None = Field(default=None, alias="nextSlug")

    model_config = {"populate_by_name": True}

    @field_validator("slug")
    @classmethod
    def validate_slug(cls, v: str) -> str:
        if not re.match(r"^[a-z0-9]+(?:-[a-z0-9]+)*$", v):
            raise ValueError(f"Slug must be kebab-case: {v}")
        return v

    @model_validator(mode="after")
    def validate_reference_solution_and_samples(self) -> "ProblemSchema":
        has_ref = any(s.is_reference for s in self.solutions)
        if not has_ref and self.solutions:
            self.solutions[-1].is_reference = True
        has_sample = any(tc.is_sample for tc in self.test_cases)
        if not has_sample and self.test_cases:
            self.test_cases[0].is_sample = True
        if self.topic not in CATEGORY_SLUGS:
            raise ValueError(f"Unknown problem topic: {self.topic}")
        for lang in ("javascript", "python"):
            sc = self.starter_code
            if isinstance(sc, dict) and lang not in sc:
                raise ValueError(f"starterCode missing MVP language '{lang}'")
        return self


class QuestionSchema(BaseModel):
    id: str = Field(..., min_length=1)
    topic: str = Field(..., min_length=1)
    subtopic: str | None = None
    difficulty: Literal["Easy", "Medium", "Hard"]
    qtype: Literal["mcq"] = "mcq"
    prompt: str = Field(..., min_length=10)
    options: list[str] = Field(..., min_length=4, max_length=4)
    correct_index: int = Field(..., ge=0, le=3)
    explanation: str = Field(..., min_length=10)
    source: Literal["curated", "generated"]
    generator_key: str | None = None
    content_hash: str = Field(..., min_length=16)
    review_status: Literal["draft", "verified"] = "draft"

    @field_validator("options")
    @classmethod
    def validate_unique_options(cls, opts: list[str]) -> list[str]:
        cleaned = [o.strip() for o in opts]
        if len(set(cleaned)) != 4:
            raise ValueError(f"All 4 options must be distinct. Got: {opts}")
        return opts

    @model_validator(mode="after")
    def validate_hash_and_oracle(self) -> "QuestionSchema":
        expected_hash = compute_content_hash(self.prompt)
        if self.content_hash != expected_hash:
            raise ValueError(
                f"content_hash mismatch for question {self.id}: expected {expected_hash}, got {self.content_hash}"
            )
        return self


class PathStepSchema(BaseModel):
    ordinal: int = Field(..., ge=1)
    step_type: Literal["visualizer", "problem", "quiz", "mock"]
    ref_id: str = Field(..., min_length=1)
    title: str | None = None
    summary: str | None = Field(default=None, min_length=10, max_length=160)
    reading_links: list[str] = Field(default_factory=list)


class LearningPathSchema(BaseModel):
    slug: str = Field(..., min_length=1)
    title: str = Field(..., min_length=1)
    blurb: str = Field(..., min_length=5)
    icon: str = Field(..., min_length=1)
    track: Literal["foundational", "specialised", "placement"]
    ordinal: int = Field(..., ge=1)
    is_published: bool = True
    steps: list[PathStepSchema] = Field(..., min_length=1)

    @model_validator(mode="after")
    def validate_path_refs(self) -> "LearningPathSchema":
        ordinals = [s.ordinal for s in self.steps]
        if sorted(ordinals) != list(range(1, len(ordinals) + 1)):
            raise ValueError(f"Step ordinals must be 1..N contiguous. Got: {ordinals}")
        missing_summaries = [s.ordinal for s in self.steps if not s.summary]
        if missing_summaries:
            raise ValueError(f"Every path step must have a summary. Missing ordinals: {missing_summaries}")
        return self
