"""Pydantic schemas for the BYOK tutor proxy.

Field names are frozen: the frontend builds against
`base_url, api_key, model, problem_slug, code, question, failed_attempts,
mode, history` in requests and `models` / `reply` in responses. Do not rename.
"""

from pydantic import BaseModel, Field, field_validator

TUTOR_MODES = frozenset({"socratic", "hint", "code_review", "interview"})


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


class TutorMessageTurn(BaseModel):
    role: str
    content: str = Field(..., min_length=1, max_length=8000)

    @field_validator("role")
    @classmethod
    def validate_role(cls, v: str) -> str:
        role = v.strip().lower()
        if role == "tutor":
            return "assistant"
        if role not in {"user", "assistant"}:
            raise ValueError("role must be 'user' or 'assistant'")
        return role


class TutorChatRequest(BaseModel):
    base_url: str
    api_key: str = Field(..., min_length=1)
    model: str = Field(..., min_length=1)
    problem_slug: str = Field(..., min_length=1)
    code: str | None = None
    question: str = Field(..., min_length=1)
    failed_attempts: int = Field(default=0, ge=0)
    mode: str = Field(default="socratic")
    history: list[TutorMessageTurn] = Field(default_factory=list, max_length=20)

    @field_validator("base_url")
    @classmethod
    def validate_base_url(cls, v: str) -> str:
        return _normalize_base_url(v)

    @field_validator("mode")
    @classmethod
    def validate_mode(cls, v: str) -> str:
        mode = v.strip().lower()
        if mode not in TUTOR_MODES:
            raise ValueError(f"mode must be one of {sorted(TUTOR_MODES)}")
        return mode


class TutorChatResponse(BaseModel):
    reply: str
