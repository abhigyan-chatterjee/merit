"""Pydantic schemas for quizzes, attempts, and question sampling."""

from pydantic import BaseModel, Field


class QuizGenerateRequest(BaseModel):
    topics: list[str] = Field(
        default_factory=lambda: ["arrays-hashing", "trees", "graphs", "dynamic-programming"]
    )
    count: int = Field(default=10, ge=1, le=200)
    difficulty: str | None = None
    is_mock: bool = False
    duration_sec: int | None = None
    # Optional per-section quotas, e.g. [["aptitude", 30], ["core-cs", 30]].
    # Sizes hold per topic instead of collapsing into one pool.
    topic_plan: list[tuple[str, int]] | None = None


class QuizQuestionItem(BaseModel):
    id: str
    topic: str
    subtopic: str | None = None
    difficulty: str
    prompt: str
    options: list[str]


class QuizGenerateResponse(BaseModel):
    attempt_id: str
    questions: list[QuizQuestionItem]
    total: int
    is_mock: bool = False
    duration_sec: int | None = None
    expires_at: str | None = None


class QuizSubmitRequest(BaseModel):
    duration_sec: int = Field(default=0, ge=0)
    selected: dict[str, int] = Field(default_factory=dict)  # question_id -> selected_index


class QuizQuestionResult(BaseModel):
    question_id: str
    prompt: str
    options: list[str]
    selected_index: int | None = None
    correct_index: int
    is_correct: bool
    explanation: str


class QuizSubmitResponse(BaseModel):
    attempt_id: str
    total: int
    correct: int
    score_pct: int
    duration_sec: int
    results: list[QuizQuestionResult]
