"""Admin API endpoints for content review queue, coverage matrix, and aggregate stats."""

import json
from typing import Any
from fastapi import APIRouter, Depends, HTTPException, Query, status
from pydantic import BaseModel, Field
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.db import get_db
from app.models.content import Problem, Question, QuestionReview
from app.models.submission import Submission
from app.models.quiz import AdminAuditLog, QuizAttempt
from app.models.user import User, utcnow_iso
from app.security import require_admin_user

router = APIRouter(prefix="/api/v1/admin", tags=["admin"])


class QuestionReviewRequest(BaseModel):
    action: str = Field(..., description="Action: approved | rejected | edited")
    note: str | None = None


class ProblemReviewRequest(BaseModel):
    action: str = Field(..., description="Action: approved | rejected")
    note: str | None = None


def log_admin_action(db: Session, admin_id: str, action: str, target: str) -> None:
    log_entry = AdminAuditLog(
        admin_id=admin_id,
        action=action,
        target=target,
        created_at=utcnow_iso(),
    )
    db.add(log_entry)
    db.commit()


@router.get("/stats")
def get_admin_stats(
    admin: User = Depends(require_admin_user),
    db: Session = Depends(get_db),
) -> dict[str, Any]:
    log_admin_action(db, admin.id, "view_stats", "aggregate_metrics")

    user_count = db.scalar(select(func.count(User.id))) or 0
    total_subs = db.scalar(select(func.count(Submission.id))) or 0
    ac_subs = (
        db.scalar(select(func.count(Submission.id)).where(Submission.verdict == "AC")) or 0
    )
    ac_rate = round((ac_subs / total_subs) * 100, 1) if total_subs > 0 else 0.0

    total_attempts = db.scalar(select(func.count(QuizAttempt.id))) or 0

    verified_questions = (
        db.scalar(
            select(func.count(Question.id)).where(Question.review_status == "verified")
        )
        or 0
    )
    draft_questions = (
        db.scalar(
            select(func.count(Question.id)).where(Question.review_status == "draft")
        )
        or 0
    )
    verified_problems = (
        db.scalar(
            select(func.count(Problem.slug)).where(Problem.review_status == "verified")
        )
        or 0
    )
    draft_problems = (
        db.scalar(
            select(func.count(Problem.slug)).where(Problem.review_status == "draft")
        )
        or 0
    )

    return {
        "users_count": user_count,
        "total_submissions": total_subs,
        "ac_submissions": ac_subs,
        "ac_rate_pct": ac_rate,
        "total_quiz_attempts": total_attempts,
        "verified_questions": verified_questions,
        "draft_questions": draft_questions,
        "verified_problems": verified_problems,
        "draft_problems": draft_problems,
    }


@router.get("/review-queue")
def get_review_queue(
    type: str = Query("questions", description="Type: questions | problems"),
    admin: User = Depends(require_admin_user),
    db: Session = Depends(get_db),
) -> list[dict[str, Any]]:
    log_admin_action(db, admin.id, "view_review_queue", f"queue_{type}")

    if type == "problems":
        problems = db.scalars(
            select(Problem)
            .where(Problem.review_status == "draft")
            .order_by(Problem.updated_at.desc())
        ).all()
        return [
            {
                "slug": p.slug,
                "title": p.title,
                "topic": p.topic,
                "difficulty": p.difficulty,
                "pattern": p.pattern,
                "statement": p.statement,
                "review_status": p.review_status,
                "created_at": p.created_at,
            }
            for p in problems
        ]

    questions = db.scalars(
        select(Question)
        .where(Question.review_status == "draft")
        .order_by(Question.updated_at.desc())
        .limit(100)
    ).all()
    return [
        {
            "id": q.id,
            "topic": q.topic,
            "subtopic": q.subtopic,
            "difficulty": q.difficulty,
            "prompt": q.prompt,
            "options": json.loads(q.options) if q.options else [],
            "correct_index": q.correct_index,
            "explanation": q.explanation,
            "source": q.source,
            "review_status": q.review_status,
            "created_at": q.created_at,
        }
        for q in questions
    ]


@router.post("/questions/{question_id}/review")
def review_question(
    question_id: str,
    request: QuestionReviewRequest,
    admin: User = Depends(require_admin_user),
    db: Session = Depends(get_db),
) -> dict[str, Any]:
    question = db.get(Question, question_id)
    if not question:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={"code": "QUESTION_NOT_FOUND", "message": f"Question '{question_id}' not found"},
        )

    action = request.action.lower()
    if action not in {"approved", "rejected", "edited"}:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail={"code": "INVALID_ACTION", "message": "Action must be approved, rejected, or edited"},
        )

    now_str = utcnow_iso()
    if action == "approved":
        question.review_status = "verified"
    elif action == "rejected":
        question.review_status = "rejected"
    question.updated_at = now_str

    review_entry = QuestionReview(
        question_id=question_id,
        reviewer_id=admin.id,
        action=action,
        note=request.note,
        created_at=now_str,
    )
    db.add(review_entry)
    log_admin_action(db, admin.id, f"question_{action}", question_id)

    return {
        "question_id": question_id,
        "action": action,
        "review_status": question.review_status,
        "reviewed_at": now_str,
    }


@router.post("/problems/{slug}/review")
def review_problem(
    slug: str,
    request: ProblemReviewRequest,
    admin: User = Depends(require_admin_user),
    db: Session = Depends(get_db),
) -> dict[str, Any]:
    problem = db.get(Problem, slug)
    if not problem:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={"code": "PROBLEM_NOT_FOUND", "message": f"Problem '{slug}' not found"},
        )

    action = request.action.lower()
    if action not in {"approved", "rejected"}:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail={"code": "INVALID_ACTION", "message": "Action must be approved or rejected"},
        )

    now_str = utcnow_iso()
    if action == "approved":
        problem.review_status = "verified"
    else:
        problem.review_status = "rejected"
    problem.updated_at = now_str

    log_admin_action(db, admin.id, f"problem_{action}", slug)

    return {
        "problem_slug": slug,
        "action": action,
        "review_status": problem.review_status,
        "reviewed_at": now_str,
    }


@router.get("/coverage")
def get_coverage_matrix(
    admin: User = Depends(require_admin_user),
    db: Session = Depends(get_db),
) -> dict[str, Any]:
    log_admin_action(db, admin.id, "view_coverage", "coverage_matrix")

    rows = db.execute(
        select(Question.topic, Question.difficulty, func.count(Question.id))
        .where(Question.review_status == "verified")
        .group_by(Question.topic, Question.difficulty)
    ).all()

    matrix: dict[str, dict[str, int]] = {}
    for topic, diff, cnt in rows:
        if topic not in matrix:
            matrix[topic] = {"easy": 0, "medium": 0, "hard": 0, "total": 0}
        matrix[topic][diff.lower()] = cnt
        matrix[topic]["total"] += cnt

    total_verified = sum(t["total"] for t in matrix.values())
    return {
        "matrix": matrix,
        "total_verified": total_verified,
    }


@router.get("/audit-logs")
def get_audit_logs(
    limit: int = Query(50, ge=1, le=100),
    admin: User = Depends(require_admin_user),
    db: Session = Depends(get_db),
) -> list[dict[str, Any]]:
    logs = db.scalars(
        select(AdminAuditLog)
        .order_by(AdminAuditLog.created_at.desc())
        .limit(limit)
    ).all()

    return [
        {
            "id": l.id,
            "admin_id": l.admin_id,
            "action": l.action,
            "target": l.target,
            "created_at": l.created_at,
        }
        for l in logs
    ]
