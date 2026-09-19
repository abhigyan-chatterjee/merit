"""BYOK tutor backend proxy (keyless server).

The browser never calls providers directly: the client sends its own
`base_url` + `api_key` in the request body and this router forwards to the
provider. The key is never persisted, never logged, and never echoed in
responses.

Rate limiting: `slowapi` is not a dependency, so a minimal in-memory
per-user token bucket (30 req/min/user, shared across both endpoints) is
used here. Multi-worker exactness is explicitly out of scope pre-launch:
each process tracks its own buckets.
"""

import time
from threading import Lock

import httpx
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.db import get_db
from app.models.content import Problem
from app.models.user import User
from app.schemas.tutor import (
    TutorChatRequest,
    TutorChatResponse,
    TutorModelsRequest,
    TutorModelsResponse,
)
from app.security import get_current_user

router = APIRouter(prefix="/api/v1/tutor", tags=["tutor"])

MODELS_TIMEOUT_S = 10.0
CHAT_TIMEOUT_S = 30.0
RATE_LIMIT_MAX_REQUESTS = 30
RATE_LIMIT_WINDOW_S = 60.0

_rate_buckets: dict[str, list[float]] = {}
_rate_lock = Lock()


def _check_rate_limit(user_id: str) -> None:
    now = time.monotonic()
    with _rate_lock:
        hits = [t for t in _rate_buckets.get(user_id, []) if now - t < RATE_LIMIT_WINDOW_S]
        if len(hits) >= RATE_LIMIT_MAX_REQUESTS:
            _rate_buckets[user_id] = hits
            raise HTTPException(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                detail={
                    "code": "TUTOR_RATE_LIMIT",
                    "message": "Tutor rate limit exceeded: 30 requests per minute.",
                },
            )
        hits.append(now)
        _rate_buckets[user_id] = hits


def _upstream_error() -> HTTPException:
    return HTTPException(
        status_code=status.HTTP_502_BAD_GATEWAY,
        detail={"code": "TUTOR_UPSTREAM", "message": "Tutor provider request failed."},
    )


def _auth_headers(api_key: str) -> dict[str, str]:
    return {"Authorization": f"Bearer {api_key}"}


def _extract_model_ids(payload: object) -> list[str]:
    if not isinstance(payload, dict):
        raise _upstream_error()
    data = payload.get("data")
    if isinstance(data, list):
        ids = [item["id"] for item in data if isinstance(item, dict)]
        return [i for i in ids if isinstance(i, str)]
    models = payload.get("models")
    if isinstance(models, list):
        return [m for m in models if isinstance(m, str)]
    raise _upstream_error()


def _build_system_prompt(
    problem: Problem, code: str | None, failed_attempts: int
) -> str:
    if failed_attempts >= 3:
        policy = (
            f"The student has already made {failed_attempts} failed submissions, "
            "so you MAY now show a complete solution with code and a full explanation."
        )
    else:
        policy = (
            "NEVER provide the full solution or complete code. "
            "Teach with hint-first guidance: ask guiding questions and give "
            "small incremental hints toward the next step only."
        )
    student_code = code if code else "(no code shared yet)"
    return (
        "You are a Socratic DSA tutor helping a student solve "
        f'"{problem.title}" (topic: {problem.topic}, difficulty: {problem.difficulty}).\n'
        f"Problem statement:\n{problem.statement}\n"
        f"The student's current code:\n{student_code}\n"
        f"Tutoring policy: {policy}"
    )


@router.post("/models", response_model=TutorModelsResponse)
async def list_models(
    req: TutorModelsRequest,
    user: User = Depends(get_current_user),
) -> TutorModelsResponse:
    _check_rate_limit(user.id)
    try:
        async with httpx.AsyncClient(timeout=MODELS_TIMEOUT_S) as client:
            resp = await client.get(
                f"{req.base_url}/models", headers=_auth_headers(req.api_key)
            )
    except httpx.HTTPError as err:
        raise _upstream_error() from err
    if resp.status_code != status.HTTP_200_OK:
        raise _upstream_error()
    try:
        payload = resp.json()
    except ValueError as err:
        raise _upstream_error() from err
    return TutorModelsResponse(models=_extract_model_ids(payload))


@router.post("/chat", response_model=TutorChatResponse)
async def chat(
    req: TutorChatRequest,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> TutorChatResponse:
    _check_rate_limit(user.id)
    problem = db.scalar(
        select(Problem).where(
            Problem.slug == req.problem_slug, Problem.review_status == "verified"
        )
    )
    if not problem:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={
                "code": "PROBLEM_NOT_FOUND",
                "message": f"Problem '{req.problem_slug}' not found",
            },
        )

    messages = [
        {
            "role": "system",
            "content": _build_system_prompt(problem, req.code, req.failed_attempts),
        },
        {"role": "user", "content": req.question},
    ]
    try:
        async with httpx.AsyncClient(timeout=CHAT_TIMEOUT_S) as client:
            resp = await client.post(
                f"{req.base_url}/chat/completions",
                headers=_auth_headers(req.api_key),
                json={"model": req.model, "messages": messages},
            )
    except httpx.HTTPError as err:
        raise _upstream_error() from err
    if resp.status_code != status.HTTP_200_OK:
        raise _upstream_error()
    try:
        payload = resp.json()
    except ValueError as err:
        raise _upstream_error() from err
    try:
        reply = payload["choices"][0]["message"]["content"]
    except (KeyError, IndexError, TypeError) as err:
        raise _upstream_error() from err
    if not isinstance(reply, str) or not reply.strip():
        raise _upstream_error()
    return TutorChatResponse(reply=reply)
