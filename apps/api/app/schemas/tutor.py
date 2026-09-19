"""Pydantic schemas for the BYOK tutor proxy.

Field names are frozen: the frontend builds against
`base_url, api_key, model, problem_slug, code, question, failed_attempts`
in requests and `models` / `reply` in responses. Do not rename.
"""

from pydantic import BaseModel, Field, field_validator


def _normalize_base_url(v: str) -> str:
    url = v.strip()
    if not url.startswith(("http://", "https://")):
        raise ValueError("base_url must start with http:// or https://")
    return url.rstrip("/")


class TutorModelsRequest(BaseModel):
    base_url: str
    api_key: str = Field(..., min_length=1)

    @field_validator("base_url")
    @classmethod
    def validate_base_url(cls, v: str) -> str:
        return _normalize_base_url(v)


class TutorModelsResponse(BaseModel):
    models: list[str]


class TutorChatRequest(BaseModel):
    base_url: str
    api_key: str = Field(..., min_length=1)
    model: str = Field(..., min_length=1)
    problem_slug: str = Field(..., min_length=1)
    code: str | None = None
    question: str = Field(..., min_length=1)
    failed_attempts: int = Field(default=0, ge=0)

    @field_validator("base_url")
    @classmethod
    def validate_base_url(cls, v: str) -> str:
        return _normalize_base_url(v)


class TutorChatResponse(BaseModel):
    reply: str
