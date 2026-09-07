import re
from datetime import UTC, datetime

from pydantic import BaseModel, Field, field_validator


def validate_local_date(v: str | None) -> str | None:
    if v is None:
        return None
    if not re.match(r"^\d{4}-\d{2}-\d{2}$", v):
        raise ValueError("local_date must be in YYYY-MM-DD format")
    try:
        dt = datetime.strptime(v, "%Y-%m-%d").date()
    except ValueError as err:
        raise ValueError("Invalid date value") from err

    # Validate ± 2 days from UTC to account for all world time zones (UTC-12 to UTC+14)
    today_utc = datetime.now(UTC).date()
    if abs((dt - today_utc).days) > 2:
        raise ValueError("local_date is outside the acceptable ±2 day window")
    return v


class ProblemProgressUpdate(BaseModel):
    status: str = Field(..., description="Status: Todo | Doing | Done")
    local_date: str | None = Field(None, description="Client local date in YYYY-MM-DD")

    @field_validator("status")
    @classmethod
    def validate_status(cls, v: str) -> str:
        if v not in {"Todo", "Doing", "Done"}:
            raise ValueError("Status must be one of: Todo, Doing, Done")
        return v

    @field_validator("local_date")
    @classmethod
    def validate_date(cls, v: str | None) -> str | None:
        return validate_local_date(v)


class ProblemProgressResponse(BaseModel):
    problem_slug: str
    status: str
    updated_at: str

    model_config = {"from_attributes": True}


class NoteUpdate(BaseModel):
    text: str
    local_date: str | None = None

    @field_validator("local_date")
    @classmethod
    def validate_date(cls, v: str | None) -> str | None:
        return validate_local_date(v)


class NoteResponse(BaseModel):
    problem_slug: str
    text: str
    updated_at: str

    model_config = {"from_attributes": True}


class BookmarkToggleRequest(BaseModel):
    item_type: str
    item_id: str

    @field_validator("item_type")
    @classmethod
    def validate_type(cls, v: str) -> str:
        if v not in {"problem", "visualizer", "path"}:
            raise ValueError("item_type must be one of: problem, visualizer, path")
        return v


class BookmarkResponse(BaseModel):
    item_type: str
    item_id: str
    bookmarked: bool


class VisualizerVisitResponse(BaseModel):
    visualizer_id: str
    visits: int
    first_completed_at: str

    model_config = {"from_attributes": True}


class ProgressSummaryResponse(BaseModel):
    solved_count: int
    doing_count: int
    total_problems: int
    current_streak: int
    activity_days: dict[str, int]
    progress: dict[str, str]
    notes: dict[str, str]
    bookmarks: list[dict[str, str]]
    visited_visualizers: list[str]
    has_imported_local: bool


class LocalImportRequest(BaseModel):
    progress: dict[str, str] = Field(default_factory=dict)
    notes: dict[str, str] = Field(default_factory=dict)
    quizzes: dict[str, int] = Field(default_factory=dict)
    streak: int = 0
    activity_days: list[str] = Field(default_factory=list)
    visited_visualizers: list[str] = Field(default_factory=list)
    local_date: str | None = None

    @field_validator("local_date")
    @classmethod
    def validate_date(cls, v: str | None) -> str | None:
        return validate_local_date(v)
