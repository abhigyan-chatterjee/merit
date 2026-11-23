from typing import Any

from pydantic import BaseModel, Field, field_validator

SUPPORTED_LANGUAGES = frozenset({"javascript", "python", "java", "cpp"})


class JudgeRunRequest(BaseModel):
    problem_slug: str
    language: str = Field(..., description="Language: javascript | python | java | cpp")
    code: str
    custom_input: list[Any] | None = None

    @field_validator("language")
    @classmethod
    def validate_lang(cls, v: str) -> str:
        norm = v.lower()
        if norm not in SUPPORTED_LANGUAGES:
            raise ValueError(
                f"Unsupported language. Must be one of: {', '.join(sorted(SUPPORTED_LANGUAGES))}"
            )
        return norm


class TestCaseResult(BaseModel):
    label: str
    passed: bool
    input: Any
    expected: Any
    actual: Any
    runtime_ms: float
    error: str | None = None
    hidden: bool = False


class JudgeRunResponse(BaseModel):
    verdict: str
    runtime_ms: float
    test_results: list[TestCaseResult]
    compile_output: str = ""
    infrastructure_error: bool = False
    passed_count: int = 0
    total_count: int = 0
    custom_run: bool = False


class SubmissionResponse(BaseModel):
    id: str
    problem_slug: str
    language: str
    code: str | None = None
    verdict: str
    runtime_ms: float
    test_results: list[TestCaseResult]
    created_at: str
    compile_output: str = ""
    infrastructure_error: bool = False
    passed_count: int = 0
    total_count: int = 0

    model_config = {"from_attributes": True}
