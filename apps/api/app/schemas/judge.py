from typing import Any

from pydantic import BaseModel, Field, field_validator


class JudgeRunRequest(BaseModel):
    problem_slug: str
    language: str = Field(..., description="Language: javascript | python")
    code: str

    @field_validator("language")
    @classmethod
    def validate_lang(cls, v: str) -> str:
        norm = v.lower()
        if norm not in {"javascript", "python"}:
            raise ValueError("Unsupported language. Must be javascript or python")
        return norm


class TestCaseResult(BaseModel):
    label: str
    passed: bool
    input: Any
    expected: Any
    actual: Any
    runtime_ms: float
    error: str | None = None


class JudgeRunResponse(BaseModel):
    verdict: str
    runtime_ms: float
    test_results: list[TestCaseResult]
    compile_output: str = ""


class SubmissionResponse(BaseModel):
    id: str
    problem_slug: str
    language: str
    code: str | None = None
    verdict: str
    runtime_ms: float
    test_results: list[TestCaseResult]
    created_at: str

    model_config = {"from_attributes": True}
