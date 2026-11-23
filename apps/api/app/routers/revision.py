"""Spaced-repetition endpoints.

`GET /due` is the queue the dashboard renders; `POST /{type}/{id}/review` is how
a self-rated review moves an item forward. Both are per-user and tiny by design —
a due list is capped, so this never scans a whole history.
"""

import json
from typing import Any

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel, Field, field_validator
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.db import get_db
from app.http_status import HTTP_422
from app.models.content import Problem, Question
from app.models.revision import RevisionItem
from app.models.user import User
from app.schemas.progress import validate_local_date
from app.security import get_current_user, require_same_origin
from app.services.revision import apply_review
from app.services.streak import get_current_date_str

router = APIRouter(
    prefix="/api/v1/revision",
    tags=["revision"],
    dependencies=[Depends(require_same_origin)],
)

VALID_ITEM_TYPES = {"problem", "question"}


class ReviewRequest(BaseModel):
    #: SM-2 self-rating. 0-5, where >= 3 counts as recalled.
    grade: int = Field(..., ge=0, le=5)
    local_date: str | None = None

    @field_validator("local_date")
    @classmethod
    def check_local_date(cls, v: str | None) -> str | None:
        # It reaches datetime.strptime, so "junk" or an ISO timestamp would be an
        # unhandled ValueError (a 500) rather than a client error.
        return validate_local_date(v)


class ReviewItemResponse(BaseModel):
    item_type: str
    item_id: str
    title: str
    topic: str
    due_date: str
    interval_days: int
    reps: int
    lapses: int
    difficulty: str = ""
    link: str = ""
    prompt: str = ""
    answer_summary: str = ""


def _parse_json(value: str | None) -> Any:
    if value is None:
        return None
    try:
        return json.loads(value)
    except (ValueError, TypeError):
        return None


@router.get("/due")
def due_items(
    limit: int = Query(20, ge=1, le=100),
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> dict[str, Any]:
    """Items scheduled for today or earlier, oldest due first."""
    today = get_current_date_str()
    # Read a window wider than `limit`, then cut to size after dropping rows
    # whose problem or question no longer exists. Limiting first meant a queue
    # of five could render as two while more eligible items sat behind them.
    rows = db.scalars(
        select(RevisionItem)
        .where(RevisionItem.user_id == user.id, RevisionItem.due_date <= today)
        .order_by(RevisionItem.due_date)
        .limit(min(limit * 10, 500))
    ).all()

    slugs = [r.item_id for r in rows if r.item_type == "problem"]
    qids = [r.item_id for r in rows if r.item_type == "question"]

    problems = (
        {p.slug: p for p in db.scalars(select(Problem).where(Problem.slug.in_(slugs))).all()}
        if slugs
        else {}
    )
    questions = (
        {q.id: q for q in db.scalars(select(Question).where(Question.id.in_(qids))).all()}
        if qids
        else {}
    )

    payload = []
    for row in rows:
        if len(payload) >= limit:
            break
        if row.item_type == "problem":
            problem = problems.get(row.item_id)
            if problem is None:
                # The problem was unpublished or removed since it was scheduled.
                # Skip rather than render a dead link.
                continue
            parts: list[str] = []
            if problem.pattern:
                parts.append(f"Pattern: {problem.pattern}")
            hints = _parse_json(problem.hints)
            first_hint = ""
            if isinstance(hints, list):
                for h in hints:
                    if isinstance(h, str) and h.strip():
                        first_hint = h.strip()
                        break
            if first_hint:
                parts.append(first_hint)
            else:
                editorial = _parse_json(problem.editorial_json)
                if isinstance(editorial, dict):
                    approach = editorial.get("approach")
                    if isinstance(approach, str) and approach.strip():
                        parts.append(approach.strip())
            payload.append(
                ReviewItemResponse(
                    item_type="problem",
                    item_id=row.item_id,
                    title=problem.title,
                    topic=problem.topic,
                    due_date=row.due_date,
                    interval_days=row.interval_days,
                    reps=row.reps,
                    lapses=row.lapses,
                    difficulty=problem.difficulty or "",
                    link=f"/problems/{problem.topic}/{row.item_id}",
                    prompt=(problem.statement or "")[:240].strip(),
                    answer_summary=" · ".join(parts),
                )
            )
        else:
            question = questions.get(row.item_id)
            if question is None:
                continue
            q_parts: list[str] = []
            options = _parse_json(question.options)
            correct_text = ""
            if isinstance(options, list) and 0 <= question.correct_index < len(options):
                candidate = options[question.correct_index]
                if isinstance(candidate, str) and candidate.strip():
                    correct_text = candidate.strip()
            if correct_text:
                q_parts.append(correct_text)
            if question.explanation and question.explanation.strip():
                q_parts.append(question.explanation.strip())
            payload.append(
                ReviewItemResponse(
                    item_type="question",
                    item_id=row.item_id,
                    title=question.prompt[:80],
                    topic=question.topic,
                    due_date=row.due_date,
                    interval_days=row.interval_days,
                    reps=row.reps,
                    lapses=row.lapses,
                    difficulty=question.difficulty or "",
                    link=f"/quiz/{question.topic}",
                    prompt=question.prompt,
                    answer_summary=" · ".join(q_parts),
                )
            )

    return {
        "today": today,
        "count": len(payload),
        "items": [item.model_dump() for item in payload],
    }


@router.post("/{item_type}/{item_id}/review")
def review_item(
    item_type: str,
    item_id: str,
    req: ReviewRequest,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> dict[str, Any]:
    if item_type not in VALID_ITEM_TYPES:
        raise HTTPException(
            status_code=HTTP_422,
            detail={
                "code": "INVALID_ITEM_TYPE",
                "message": "item_type must be 'problem' or 'question'",
            },
        )

    exists = (
        db.scalar(select(Problem.slug).where(Problem.slug == item_id))
        if item_type == "problem"
        else db.scalar(select(Question.id).where(Question.id == item_id))
    )
    if exists is None:
        raise HTTPException(
            status_code=404,
            detail={"code": "ITEM_NOT_FOUND", "message": f"No {item_type} '{item_id}'."},
        )

    row = apply_review(db, user.id, item_type, item_id, req.grade, req.local_date)
    return {
        "item_type": row.item_type,
        "item_id": row.item_id,
        "due_date": row.due_date,
        "interval_days": row.interval_days,
        "ease": round(row.ease, 3),
        "reps": row.reps,
        "lapses": row.lapses,
    }
