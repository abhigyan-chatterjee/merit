"""Pydantic schemas for quizzes, attempts, and question sampling."""

from pydantic import BaseModel, Field, field_validator


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

    @field_validator("topic_plan")
    @classmethod
    def validate_topic_plan(
        cls, topic_plan: list[tuple[str, int]] | None
    ) -> list[tuple[str, int]] | None:
        if topic_plan is None:
            return None
        if len(topic_plan) > 20:
            raise ValueError("topic_plan cannot contain more than 20 sections")
        if any(count < 1 or count > 200 for _, count in topic_plan):
            raise ValueError("each topic count must be between 1 and 200")
        if sum(count for _, count in topic_plan) > 200:
            raise ValueError("topic_plan total cannot exceed 200")
        return topic_plan


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
