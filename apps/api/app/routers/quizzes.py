"""Quiz API endpoints: generate quiz, submit attempt, retry wrong questions, and view attempt."""

import json
import uuid
from typing import Any
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session, selectinload

from app.db import get_db
from app.models.content import Question
from app.models.quiz import QuizAttempt, QuizAttemptAnswer
from app.models.user import User, utcnow_iso
from app.schemas.quiz import (
    QuizGenerateRequest,
    QuizGenerateResponse,
    QuizQuestionItem,
    QuizQuestionResult,
    QuizSubmitRequest,
    QuizSubmitResponse,
)
from app.security import get_current_user
from app.services.sampler import sample_questions
from app.services.streak import record_activity

router = APIRouter(prefix="/api/v1/quizzes", tags=["quizzes"])


@router.post("/generate", response_model=QuizGenerateResponse)
def generate_quiz(
    request: QuizGenerateRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> QuizGenerateResponse:
    attempt_id, questions, expires_at = sample_questions(
        db=db,
        user_id=current_user.id,
        topics=request.topics,
        count=request.count,
        difficulty=request.difficulty,
        is_mock=request.is_mock,
        duration_limit_sec=request.duration_sec,
    )

    if not questions:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={
                "code": "NO_QUESTIONS_FOR_TOPICS",
                "message": f"No verified questions for topics: {', '.join(request.topics)}",
                "topics": list(request.topics),
            },
        )

    items = [
        QuizQuestionItem(
            id=q.id,
            topic=q.topic,
            subtopic=q.subtopic,
            difficulty=q.difficulty,
            prompt=q.prompt,
            options=json.loads(q.options) if q.options else [],
        )
        for q in questions
    ]

    return QuizGenerateResponse(
        attempt_id=attempt_id,
        questions=items,
        total=len(items),
        is_mock=request.is_mock,
        duration_sec=request.duration_sec,
        expires_at=expires_at,
    )



@router.post("/attempts/{attempt_id}", response_model=QuizSubmitResponse)
def submit_attempt(
    attempt_id: str,
    request: QuizSubmitRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> QuizSubmitResponse:
    attempt = db.scalar(
        select(QuizAttempt)
        .options(selectinload(QuizAttempt.answers))
        .where(QuizAttempt.id == attempt_id, QuizAttempt.user_id == current_user.id)
    )
    if not attempt:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={"code": "ATTEMPT_NOT_FOUND", "message": "Quiz attempt not found"},
        )

    # Question IDs snapshot from server-side creation
    question_ids: list[str] = json.loads(attempt.question_ids)
    questions = db.scalars(select(Question).where(Question.id.in_(question_ids))).all()
    q_map = {q.id: q for q in questions}

    results: list[QuizQuestionResult] = []
    correct_count = 0

    # Clean existing answers if re-submitting
    for ans in list(attempt.answers):
        db.delete(ans)
    db.flush()

    for qid in question_ids:
        q = q_map.get(qid)
        if not q:
            continue

        selected_idx = request.selected.get(qid)
        is_correct = bool(selected_idx is not None and selected_idx == q.correct_index)
        if is_correct:
            correct_count += 1

        db.add(
            QuizAttemptAnswer(
                attempt_id=attempt.id,
                question_id=qid,
                selected_index=selected_idx,
                is_correct=1 if is_correct else 0,
            )
        )

        results.append(
            QuizQuestionResult(
                question_id=qid,
                prompt=q.prompt,
                options=json.loads(q.options) if q.options else [],
                selected_index=selected_idx,
                correct_index=q.correct_index,
                is_correct=is_correct,
                explanation=q.explanation,
            )
        )

    total_q = len(question_ids)
    score_pct = int(round((correct_count / total_q) * 100)) if total_q > 0 else 0

    attempt.correct = correct_count
    attempt.total = total_q
    attempt.score_pct = score_pct
    attempt.duration_sec = request.duration_sec

    # Increment streak activity
    record_activity(db, current_user.id)
    db.commit()

    return QuizSubmitResponse(
        attempt_id=attempt.id,
        total=total_q,
        correct=correct_count,
        score_pct=score_pct,
        duration_sec=request.duration_sec,
        results=results,
    )


@router.post("/attempts/{attempt_id}/retry-wrong", response_model=QuizGenerateResponse)
def retry_wrong_questions(
    attempt_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> QuizGenerateResponse:
    attempt = db.scalar(
        select(QuizAttempt)
        .options(selectinload(QuizAttempt.answers))
        .where(QuizAttempt.id == attempt_id, QuizAttempt.user_id == current_user.id)
    )
    if not attempt:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={"code": "ATTEMPT_NOT_FOUND", "message": "Quiz attempt not found"},
        )

    wrong_qids = [a.question_id for a in attempt.answers if a.is_correct == 0]
    if not wrong_qids:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={"code": "NO_WRONG_QUESTIONS", "message": "All questions in this attempt were correct!"},
        )

    questions = db.scalars(select(Question).where(Question.id.in_(wrong_qids))).all()
    q_dict = {q.id: q for q in questions}
    ordered_questions = [q_dict[qid] for qid in wrong_qids if qid in q_dict]

    new_attempt_id = str(uuid.uuid4())
    new_attempt = QuizAttempt(
        id=new_attempt_id,
        user_id=current_user.id,
        topic_spec=attempt.topic_spec,
        question_ids=json.dumps([q.id for q in ordered_questions]),
        total=len(ordered_questions),
        correct=0,
        score_pct=0,
        duration_sec=0,
        created_at=utcnow_iso(),
    )
    db.add(new_attempt)
    db.commit()

    items = [
        QuizQuestionItem(
            id=q.id,
            topic=q.topic,
            subtopic=q.subtopic,
            difficulty=q.difficulty,
            prompt=q.prompt,
            options=json.loads(q.options) if q.options else [],
        )
        for q in ordered_questions
    ]

    return QuizGenerateResponse(
        attempt_id=new_attempt_id,
        questions=items,
        total=len(items),
    )


@router.get("/attempts/{attempt_id}", response_model=QuizSubmitResponse)
def get_attempt_detail(
    attempt_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> QuizSubmitResponse:
    attempt = db.scalar(
        select(QuizAttempt)
        .options(selectinload(QuizAttempt.answers))
        .where(QuizAttempt.id == attempt_id, QuizAttempt.user_id == current_user.id)
    )
    if not attempt:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={"code": "ATTEMPT_NOT_FOUND", "message": "Quiz attempt not found"},
        )

    q_ids = [a.question_id for a in attempt.answers]
    questions = db.scalars(select(Question).where(Question.id.in_(q_ids))).all()
    q_map = {q.id: q for q in questions}

    results = []
    for a in attempt.answers:
        q = q_map.get(a.question_id)
        if q:
            results.append(
                QuizQuestionResult(
                    question_id=q.id,
                    prompt=q.prompt,
                    options=json.loads(q.options) if q.options else [],
                    selected_index=a.selected_index,
                    correct_index=q.correct_index,
                    is_correct=bool(a.is_correct),
                    explanation=q.explanation,
                )
            )

    return QuizSubmitResponse(
        attempt_id=attempt.id,
        total=attempt.total,
        correct=attempt.correct,
        score_pct=attempt.score_pct,
        duration_sec=attempt.duration_sec,
        results=results,
    )
