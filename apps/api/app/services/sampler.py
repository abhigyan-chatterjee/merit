import json
import random
import uuid
from collections.abc import Sequence
from datetime import UTC, datetime, timedelta

from sqlalchemy import select
from sqlalchemy.dialects.sqlite import insert as sqlite_insert
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
    topic_plan: Sequence[tuple[str, int]] | None = None,
) -> tuple[str, list[Question], str | None]:
    """Samples verified questions with recent exposure exclusion and difficulty weighting.

    When ``topic_plan`` is given (e.g. the placement mock's 30/30/20 split),
    each (topic, count) pair is sampled independently so section sizes hold
    even when pools differ wildly in size. Otherwise the legacy behaviour
    applies: one pool across all topics with 40/40/20 difficulty weighting.
    """

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

    def pick_from(pool: list[Question], n: int) -> list[Question]:
        """Difficulty-weighted pick (40/40/20) from one pool, exposure-aware."""
        fresh = [q for q in pool if q.id not in recent_exposed_ids]
        # Avoid stable database ordering making the fresh portion deterministic.
        random.shuffle(fresh)
        chosen = fresh[:]
        if len(chosen) < n:
            relaxed = [q for q in pool if q.id in recent_exposed_ids]
            random.shuffle(relaxed)
            chosen = fresh + relaxed[: (n - len(fresh))]
        if difficulty:
            random.shuffle(chosen)
            return chosen[:n]
        easy = [q for q in chosen if q.difficulty == "Easy"]
        med = [q for q in chosen if q.difficulty == "Medium"]
        hard = [q for q in chosen if q.difficulty == "Hard"]
        for bucket in (easy, med, hard):
            random.shuffle(bucket)
        t_easy = max(1, int(n * 0.4))
        t_med = max(1, int(n * 0.4))
        t_hard = n - t_easy - t_med
        picked = easy[:t_easy] + med[:t_med] + hard[:t_hard]
        if len(picked) < n:
            rest = [q for q in chosen if q not in picked]
            random.shuffle(rest)
            picked += rest[: (n - len(picked))]
        if len(picked) < n:
            rest = [q for q in pool if q not in picked]
            random.shuffle(rest)
            picked += rest[: (n - len(picked))]
        return picked[:n]

    if topic_plan:
        # Per-section sampling: each topic contributes its own quota.
        sampled: list[Question] = []
        for plan_topic, plan_count in topic_plan:
            pool_q = base_query.where(Question.topic == plan_topic)
            if difficulty:
                pool_q = pool_q.where(Question.difficulty == difficulty)
            pool = db.scalars(pool_q).all()
            if not pool:
                pool = db.scalars(
                    select(Question).where(
                        Question.review_status == "verified",
                        Question.topic == plan_topic,
                    )
                ).all()
            sampled.extend(pick_from(pool, plan_count))
    else:
        sampled = pick_from(all_candidates, count)

    # 4b. Dedupe: per-section sampling (topic_plan) can surface the same
    # question from overlapping sections. Duplicates would double-insert
    # into user_question_exposure and blow the PK unique constraint.
    seen_ids: set[str] = set()
    deduped: list[Question] = []
    for q in sampled:
        if q.id not in seen_ids:
            seen_ids.add(q.id)
            deduped.append(q)
    sampled = deduped

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

    # 6. Record exposures for user. Upsert, not select-then-insert: two
    # concurrent /generate calls (StrictMode remount, double-click Retake)
    # used to SELECT-miss the same rows and then INSERT-collide on the
    # (user_id, question_id) PK → 500 IntegrityError. ON CONFLICT makes
    # the second writer a timestamp refresh instead of a crash.
    if sampled:
        upsert = sqlite_insert(UserQuestionExposure).values(
            [{"user_id": user_id, "question_id": q.id, "shown_at": now_str} for q in sampled]
        )
        upsert = upsert.on_conflict_do_update(
            index_elements=["user_id", "question_id"],
            set_={"shown_at": now_str},
        )
        db.execute(upsert)

    db.commit()
    return attempt_id, sampled, expires_at
