"""Pydantic schemas and round blueprints for the dedicated AI Interview Portal."""

from typing import Any, Literal

from pydantic import BaseModel, Field, field_validator, model_validator

from app.schemas.tutor import _normalize_base_url

InterviewDifficulty = Literal["easy", "medium", "hard"]
InterviewAction = Literal["start", "message", "advance_stage", "evaluate"]

INTERVIEW_BLUEPRINTS: dict[str, dict[str, Any]] = {
    "easy": {
        "duration_sec": 1800,
        "coding_difficulties": ["Easy"],
        "max_score": 20,
        "stages": [
            {"id": "theory", "label": "1. Basic CS Theory", "kind": "theory"},
            {"id": "coding_1", "label": "2. Coding (Easy)", "kind": "coding", "problem_index": 0},
            {"id": "wrapup", "label": "3. Follow-ups & Wrap-up", "kind": "wrapup"},
            {"id": "rubric", "label": "4. Final Rubric", "kind": "rubric"},
        ],
        "rubric_dimensions": [
            "CS Fundamentals",
            "Problem Solving & Approach",
            "Code Quality & Edge Cases",
            "Communication & Big-O",
        ],
    },
    "medium": {
        "duration_sec": 2700,
        "coding_difficulties": ["Easy", "Medium"],
        "max_score": 25,
        "stages": [
            {"id": "theory", "label": "1. Core CS Theory", "kind": "theory"},
            {
                "id": "coding_1",
                "label": "2. Coding #1 (Easy)",
                "kind": "coding",
                "problem_index": 0,
            },
            {
                "id": "coding_2",
                "label": "3. Coding #2 (Medium)",
                "kind": "coding",
                "problem_index": 1,
            },
            {"id": "project", "label": "4. Project & Stack", "kind": "project"},
            {"id": "rubric", "label": "5. Final Rubric", "kind": "rubric"},
        ],
        "rubric_dimensions": [
            "CS Fundamentals",
            "Algorithmic Problem Solving",
            "Code Quality & Edge Cases",
            "Project & Tech Stack Depth",
            "Communication & Trade-offs",
        ],
    },
    "hard": {
        "duration_sec": 3600,
        "coding_difficulties": ["Medium", "Hard"],
        "max_score": 30,
        "stages": [
            {
                "id": "theory",
                "label": "1. Deep CS (DSA/DBMS/OOP/OS)",
                "kind": "theory",
            },
            {
                "id": "coding_1",
                "label": "2. Coding #1 (Medium)",
                "kind": "coding",
                "problem_index": 0,
            },
            {
                "id": "coding_2",
                "label": "3. Coding #2 (Hard)",
                "kind": "coding",
                "problem_index": 1,
            },
            {"id": "project", "label": "4. Complex Project Deep-Dive", "kind": "project"},
            {"id": "system_design", "label": "5. System Design", "kind": "system_design"},
            {"id": "rubric", "label": "6. FAANG Hiring Rubric", "kind": "rubric"},
        ],
        "rubric_dimensions": [
            "Deep CS Theory",
            "DSA & Optimal Algorithms",
            "Code Correctness & Edge Cases",
            "Project Engineering Rigor",
            "System Design & Scale",
            "Communication & Signal",
        ],
    },
}


class InterviewCodingSnapshot(BaseModel):
    language: str = Field(default="python", max_length=32)
    code: str = Field(default="", max_length=30000)
    verdict: str | None = Field(default=None, max_length=32)
    passed_count: int | None = Field(default=None, ge=0)
    total_count: int | None = Field(default=None, ge=0)


class InterviewMessageRecord(BaseModel):
    role: Literal["user", "interviewer"]
    content: str
    stage: str
    created_at: str


class InterviewStageDef(BaseModel):
    id: str
    label: str
    kind: str
    problem_index: int | None = None


class InterviewProblemSummary(BaseModel):
    slug: str
    title: str
    topic: str
    difficulty: str
    pattern: str
    statement: str
    examples: list[dict[str, Any]] = Field(default_factory=list)
    constraints: list[str] = Field(default_factory=list)
    starter_code: dict[str, str] = Field(default_factory=dict)
    function_name: str
    test_cases: list[dict[str, Any]] = Field(default_factory=list)


class InterviewRubricDimension(BaseModel):
    name: str
    score: int = Field(ge=0, le=5)
    max_score: int = 5
    comment: str = ""


class InterviewRubric(BaseModel):
    dimensions: list[InterviewRubricDimension]
    total: int = Field(ge=0)
    max_total: int = Field(ge=1)
    verdict: Literal["Strong Hire", "Hire", "Leaning Hire", "No Hire"]
    strengths: list[str] = Field(default_factory=list)
    improvements: list[str] = Field(default_factory=list)
    summary: str = ""


class ResumeParseResponse(BaseModel):
    filename: str
    pages: int
    char_count: int
    truncated: bool
    extracted_text: str


class InterviewCreateRequest(BaseModel):
    difficulty: InterviewDifficulty
    problem_slugs: list[str] | None = Field(default=None, max_length=2)
    resume_filename: str | None = Field(default=None, max_length=255)
    resume_text: str | None = Field(default=None, max_length=10000)
    project_brief: str | None = Field(default=None, max_length=2000)


class InterviewUpdateRequest(BaseModel):
    current_stage: str | None = Field(default=None, max_length=64)
    elapsed_sec: int | None = Field(default=None, ge=0, le=86400)
    coding_snapshots: dict[str, InterviewCodingSnapshot] | None = None
    project_brief: str | None = Field(default=None, max_length=2000)
    resume_filename: str | None = Field(default=None, max_length=255)
    resume_text: str | None = Field(default=None, max_length=10000)
    clear_resume: bool = False


class InterviewTurnRequest(BaseModel):
    base_url: str
    api_key: str = Field(..., min_length=1, max_length=512)
    model: str = Field(..., min_length=1, max_length=256)
    action: InterviewAction = "message"
    message: str = Field(default="", max_length=8000)
    stage: str | None = Field(default=None, max_length=64)
    elapsed_sec: int | None = Field(default=None, ge=0, le=86400)
    active_problem_slug: str | None = Field(default=None, max_length=255)
    coding_snapshot: InterviewCodingSnapshot | None = None
    design_notes: str | None = Field(default=None, max_length=8000)

    @field_validator("base_url")
    @classmethod
    def validate_base_url(cls, v: str) -> str:
        return _normalize_base_url(v)

    @model_validator(mode="after")
    def validate_message_required(self) -> "InterviewTurnRequest":
        if self.action == "message" and not self.message.strip():
            raise ValueError("message must be non-empty when action is 'message'")
        return self


class InterviewSessionSummary(BaseModel):
    id: str
    difficulty: InterviewDifficulty
    status: str
    current_stage: str
    duration_sec: int
    elapsed_sec: int
    problem_slugs: list[str]
    has_resume: bool
    resume_filename: str | None = None
    overall_verdict: str | None = None
    overall_score: int | None = None
    max_score: int | None = None
    created_at: str
    updated_at: str
    completed_at: str | None = None


class InterviewSessionDetail(InterviewSessionSummary):
    stages: list[InterviewStageDef]
    problems: list[InterviewProblemSummary]
    messages: list[InterviewMessageRecord]
    coding_snapshots: dict[str, InterviewCodingSnapshot]
    resume_text: str | None = None
    project_brief: str | None = None
    rubric: InterviewRubric | None = None


class InterviewTurnResponse(BaseModel):
    reply: str
    session: InterviewSessionDetail
    suggested_stage: str | None = None
