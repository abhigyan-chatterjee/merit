import json
import random
import uuid
from datetime import UTC, datetime, timedelta
from typing import Sequence
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.content import Question
from app.models.quiz import QuizAttempt, UserQuestionExposure
from app.models.user import utcnow_iso


def sample_questions(
    db: Session,
    user_id: str,
    topics: Sequence[str],
    count: int = 10,
    difficulty: str | None = None,
    is_mock: bool = False,
    duration_limit_sec: int | None = None,
) -> tuple[str, list[Question], str | None]:
    """Samples verified questions with recent exposure exclusion and difficulty weighting."""

    # 1. Fetch recent exposures (last 50)
    recent_exp_query = (
        select(UserQuestionExposure.question_id)
        .where(UserQuestionExposure.user_id == user_id)
        .order_by(UserQuestionExposure.shown_at.desc())
        .limit(50)
    )
    recent_exposed_ids = set(db.scalars(recent_exp_query).all())

    # 2. Build candidate pool query (verified questions matching topics)
    base_query = select(Question).where(
        Question.review_status == "verified",
        Question.topic.in_(topics),
    )
    if difficulty:
        base_query = base_query.where(Question.difficulty == difficulty)

    all_candidates = db.scalars(base_query).all()
    # No silent widening: an empty topic pool returns empty so the caller
    # can report "no questions for this topic" instead of serving BST
    # questions for an Arrays quiz.

    # 3. Exclude recently exposed questions if possible
    fresh_pool = [q for q in all_candidates if q.id not in recent_exposed_ids]

    if len(fresh_pool) >= count:
        chosen_pool = fresh_pool
    else:
        # Relax exposures if pool is too small, prioritizing freshest first
        needed = count - len(fresh_pool)
        relaxed = [q for q in all_candidates if q.id in recent_exposed_ids]
        random.shuffle(relaxed)
        chosen_pool = fresh_pool + relaxed[:needed]

    # 4. Difficulty weighting if difficulty wasn't specified (approx 40% Easy, 40% Med, 20% Hard)
    if not difficulty:
        easy_pool = [q for q in chosen_pool if q.difficulty == "Easy"]
        med_pool = [q for q in chosen_pool if q.difficulty == "Medium"]
        hard_pool = [q for q in chosen_pool if q.difficulty == "Hard"]

        target_easy = max(1, int(count * 0.4))
        target_med = max(1, int(count * 0.4))
        target_hard = count - target_easy - target_med

        random.shuffle(easy_pool)
        random.shuffle(med_pool)
        random.shuffle(hard_pool)

        sampled: list[Question] = []
        sampled.extend(easy_pool[:target_easy])
        sampled.extend(med_pool[:target_med])
        sampled.extend(hard_pool[:target_hard])

        # Fill any deficit from remainder
        if len(sampled) < count:
            remaining = [q for q in chosen_pool if q not in sampled]
            random.shuffle(remaining)
            sampled.extend(remaining[: (count - len(sampled))])
    else:
        random.shuffle(chosen_pool)
        sampled = chosen_pool[:count]

    # If still fewer than count, take whatever candidates exist
    if len(sampled) < count:
        remaining = [q for q in all_candidates if q not in sampled]
        random.shuffle(remaining)
        sampled.extend(remaining[: (count - len(sampled))])

    # 5. Create attempt shell with server-side snapshot of question IDs
    attempt_id = str(uuid.uuid4())
    now_str = utcnow_iso()

    duration_sec = duration_limit_sec or (1800 if is_mock else 0)
    expires_at = None
    if is_mock:
        exp_dt = datetime.now(UTC) + timedelta(seconds=duration_sec)
        expires_at = exp_dt.isoformat()

    spec_data = {
        "topics": list(topics),
        "difficulty": difficulty,
        "is_mock": is_mock,
        "duration_limit_sec": duration_sec,
        "expires_at": expires_at,
    }

    attempt = QuizAttempt(
        id=attempt_id,
        user_id=user_id,
        topic_spec=json.dumps(spec_data),
        question_ids=json.dumps([q.id for q in sampled]),
        total=len(sampled),
        correct=0,
        score_pct=0,
        duration_sec=0,
        created_at=now_str,
    )
    db.add(attempt)

    # 6. Record exposures for user
    for q in sampled:
        exp = db.scalar(
            select(UserQuestionExposure).where(
                UserQuestionExposure.user_id == user_id,
                UserQuestionExposure.question_id == q.id,
            )
        )
        if exp:
            exp.shown_at = now_str
        else:
            db.add(UserQuestionExposure(user_id=user_id, question_id=q.id, shown_at=now_str))

    db.commit()
    return attempt_id, sampled, expires_at

