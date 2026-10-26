"""Spaced-repetition endpoints.

`GET /due` is the queue the dashboard renders; `POST /{type}/{id}/review` is how
a self-rated review moves an item forward. Both are per-user and tiny by design —
a due list is capped, so this never scans a whole history.
"""

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
                )
            )
        else:
            question = questions.get(row.item_id)
            if question is None:
                continue
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
