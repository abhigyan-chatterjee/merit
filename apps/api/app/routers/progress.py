import json
import logging
from typing import Any

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.db import get_db
from app.http_status import HTTP_422
from app.models.content import Problem, Question
from app.models.progress import (
    ActivityDay,
    Bookmark,
    Note,
    ProblemProgress,
    VisualizerCompletion,
)
from app.models.quiz import QuizAttempt, QuizAttemptAnswer
from app.models.submission import Submission
from app.models.user import User, utcnow_iso
from app.schemas.progress import (
    BookmarkResponse,
    BookmarkToggleRequest,
    LocalImportRequest,
    NoteResponse,
    NoteUpdate,
    ProblemProgressResponse,
    ProblemProgressUpdate,
    ProgressSummaryResponse,
    SettingsResponse,
    SettingsUpdate,
    VisualizerVisitResponse,
    validate_local_date,
)
from app.security import get_current_user, require_same_origin
from app.services.streak import compute_streak, get_current_date_str, record_activity

router = APIRouter(
    prefix="/api/v1/progress",
    tags=["Progress"],
    # Every mutating route here is cookie-authenticated; the origin check is
    # defence in depth behind SameSite=strict, which is the pattern auth.py
    # already used. GETs are unaffected: browsers send no Origin on navigation.
    dependencies=[Depends(require_same_origin)],
)

STATUS_RANK = {"Done": 2, "Doing": 1, "Todo": 0}

#: How many schedule rows to inspect to fill the dashboard's five-item queue.
_REVISION_WINDOW = 50


@router.get("/problems/{slug}", response_model=ProblemProgressResponse)
def get_problem_progress(
    slug: str,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    stmt = select(ProblemProgress).where(
        ProblemProgress.user_id == user.id,
        ProblemProgress.problem_slug == slug,
    )
    row = db.scalar(stmt)
    if not row:
        return ProblemProgressResponse(
            problem_slug=slug,
            status="Todo",
            updated_at=utcnow_iso(),
        )
    return row


@router.put("/problems/{slug}", response_model=ProblemProgressResponse)
def update_problem_progress(
    slug: str,
    req: ProblemProgressUpdate,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    stmt = select(ProblemProgress).where(
        ProblemProgress.user_id == user.id,
        ProblemProgress.problem_slug == slug,
    )
    row = db.scalar(stmt)
    now_str = utcnow_iso()
    if row:
        row.status = req.status
        row.updated_at = now_str
    else:
        row = ProblemProgress(
            user_id=user.id,
            problem_slug=slug,
            status=req.status,
            updated_at=now_str,
        )
        db.add(row)

    record_activity(db, user.id, req.local_date)
    db.commit()
    db.refresh(row)
    return row


@router.get("/notes/{slug}", response_model=NoteResponse)
def get_note(
    slug: str,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    stmt = select(Note).where(
        Note.user_id == user.id,
        Note.problem_slug == slug,
    )
    row = db.scalar(stmt)
    if not row:
        return NoteResponse(problem_slug=slug, text="", updated_at="")
    return row


@router.put("/notes/{slug}", response_model=NoteResponse)
def update_note(
    slug: str,
    req: NoteUpdate,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    stmt = select(Note).where(
        Note.user_id == user.id,
        Note.problem_slug == slug,
    )
    row = db.scalar(stmt)
    now_str = utcnow_iso()
    if row:
        row.text = req.text
        row.updated_at = now_str
    else:
        row = Note(
            user_id=user.id,
            problem_slug=slug,
            text=req.text,
            updated_at=now_str,
        )
        db.add(row)

    if req.text.strip():
        record_activity(db, user.id, req.local_date)
    db.commit()
    db.refresh(row)
    return row


@router.post("/bookmarks/toggle", response_model=BookmarkResponse)
def toggle_bookmark(
    req: BookmarkToggleRequest,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    stmt = select(Bookmark).where(
        Bookmark.user_id == user.id,
        Bookmark.item_type == req.item_type,
        Bookmark.item_id == req.item_id,
    )
    existing = db.scalar(stmt)
    if existing:
        db.delete(existing)
        db.commit()
        return BookmarkResponse(item_type=req.item_type, item_id=req.item_id, bookmarked=False)

    new_bm = Bookmark(
        user_id=user.id,
        item_type=req.item_type,
        item_id=req.item_id,
        created_at=utcnow_iso(),
    )
    db.add(new_bm)
    db.commit()
    return BookmarkResponse(item_type=req.item_type, item_id=req.item_id, bookmarked=True)


@router.post("/visualizers/{visualizer_id}/visit", response_model=VisualizerVisitResponse)
def visit_visualizer(
    visualizer_id: str,
    local_date: str | None = Query(
        None,
        description="Client's local date, YYYY-MM-DD. Validated: it is written to activity_days.",
    ),
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    # This value is persisted as the primary key of a day bucket, so it cannot be
    # taken on trust: an unvalidated query parameter used to write arbitrary
    # strings into activity_days, which then poisoned the heatmap and the streak.
    local_date = _validated_local_date(local_date)

    stmt = select(VisualizerCompletion).where(
        VisualizerCompletion.user_id == user.id,
        VisualizerCompletion.visualizer_id == visualizer_id,
    )
    row = db.scalar(stmt)
    if row:
        row.visits += 1
    else:
        row = VisualizerCompletion(
            user_id=user.id,
            visualizer_id=visualizer_id,
            visits=1,
            first_completed_at=utcnow_iso(),
        )
        db.add(row)

    record_activity(db, user.id, local_date)
    db.commit()
    db.refresh(row)
    return row


@router.get("/summary", response_model=ProgressSummaryResponse)
def get_progress_summary(
    local_date: str | None = None,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    # Fetch all progress for user
    progress_rows = db.scalars(
        select(ProblemProgress).where(ProblemProgress.user_id == user.id)
    ).all()
    progress_map = {p.problem_slug: p.status for p in progress_rows}
    solved_count = sum(1 for s in progress_map.values() if s == "Done")
    doing_count = sum(1 for s in progress_map.values() if s == "Doing")

    # Fetch notes
    note_rows = db.scalars(select(Note).where(Note.user_id == user.id)).all()
    notes_map = {n.problem_slug: n.text for n in note_rows if n.text.strip()}

    # Fetch bookmarks
    bm_rows = db.scalars(select(Bookmark).where(Bookmark.user_id == user.id)).all()
    bookmarks_list = [{"item_type": b.item_type, "item_id": b.item_id} for b in bm_rows]

    # Fetch activity days
    act_rows = db.scalars(select(ActivityDay).where(ActivityDay.user_id == user.id)).all()
    act_map = {a.day: a.action_count for a in act_rows}
    streak = compute_streak(
        list(act_map.keys()), _validated_local_date(local_date) or get_current_date_str()
    )

    # Fetch visited visualizers
    vis_rows = db.scalars(
        select(VisualizerCompletion).where(VisualizerCompletion.user_id == user.id)
    ).all()
    visited_list = [v.visualizer_id for v in vis_rows]

    # Fetch quiz attempts for per-topic scores and weak areas
    attempts = db.scalars(
        select(QuizAttempt)
        .where(QuizAttempt.user_id == user.id)
        .order_by(QuizAttempt.created_at.desc())
    ).all()

    quiz_scores: dict[str, int] = {}
    topic_correct: dict[str, int] = {}
    topic_total: dict[str, int] = {}

    last_5_attempts = attempts[:5]

    for att in attempts:
        try:
            spec = json.loads(att.topic_spec) if att.topic_spec else {}
            topics = spec.get("topics", [])
            topic_key = topics[0] if len(topics) == 1 else "mixed"
            quiz_scores[topic_key] = max(quiz_scores.get(topic_key, 0), att.score_pct)
        except Exception:
            continue

    if last_5_attempts:
        att_ids = [a.id for a in last_5_attempts]
        answers = db.scalars(
            select(QuizAttemptAnswer).where(QuizAttemptAnswer.attempt_id.in_(att_ids))
        ).all()
        q_ids = list({ans.question_id for ans in answers})
        if q_ids:
            q_rows = db.scalars(select(Question).where(Question.id.in_(q_ids))).all()
            q_map = {q.id: q for q in q_rows}
            for ans in answers:
                q = q_map.get(ans.question_id)
                t = q.topic if q else "general"
                topic_total[t] = topic_total.get(t, 0) + 1
                if ans.is_correct == 1:
                    topic_correct[t] = topic_correct.get(t, 0) + 1

    # Incorporate submissions into weak areas
    recent_subs = db.scalars(
        select(Submission)
        .where(Submission.user_id == user.id)
        .order_by(Submission.created_at.desc())
        .limit(20)
    ).all()
    sub_slugs = list({s.problem_slug for s in recent_subs})
    p_map: dict[str, Problem] = {}

    if sub_slugs:
        p_rows = db.scalars(select(Problem).where(Problem.slug.in_(sub_slugs))).all()
        p_map = {p.slug: p for p in p_rows}
        for sub in recent_subs:
            p = p_map.get(sub.problem_slug)
            t = p.topic if p else "general"
            topic_total[t] = topic_total.get(t, 0) + 1
            if sub.verdict == "AC":
                topic_correct[t] = topic_correct.get(t, 0) + 1

    # Weakest topics: rolling accuracy < 70% or quiz score < 70%
    weak_set: set[str] = set()
    for t, tot in topic_total.items():
        if tot >= 2:
            acc = (topic_correct.get(t, 0) / tot) * 100
            if acc < 70:
                weak_set.add(t)

    for t, s in quiz_scores.items():
        if s < 70:
            weak_set.add(t)

    weakest_topics = sorted(weak_set)

    # Revision queue comes from the schedule table, not from a re-derivation.
    #
    # This used to be rebuilt per request out of the last 20 submissions and 5
    # quizzes, with a hardcoded "1d review" label and no due date: nothing was
    # ever scheduled, and the same items reappeared forever. The table is the
    # source of truth now; `services.revision` owns the SM-2 maths.
    from app.models.revision import RevisionItem

    # The dashboard shows the next five scheduled items, earliest first, not only
    # the strictly-due ones. An item graded today is scheduled for tomorrow, so a
    # due-only filter left the widget empty immediately after a failed quiz —
    # technically correct and useless to look at. /api/v1/revision/due stays
    # strict; each entry carries its own `due_stage` date so the UI can say
    # "today" or "tomorrow" honestly.
    # Fetch a working window, not exactly five: rows whose problem or question
    # has since been unpublished are skipped below, so limiting to 5 first meant
    # the widget could render three items when five were scheduled.
    due_rows = db.scalars(
        select(RevisionItem)
        .where(RevisionItem.user_id == user.id)
        .order_by(RevisionItem.due_date)
        .limit(_REVISION_WINDOW)
    ).all()
    due_slugs = [r.item_id for r in due_rows if r.item_type == "problem"]
    due_qids = [r.item_id for r in due_rows if r.item_type == "question"]
    due_problems = (
        {p.slug: p for p in db.scalars(select(Problem).where(Problem.slug.in_(due_slugs))).all()}
        if due_slugs
        else {}
    )
    due_questions = (
        {q.id: q for q in db.scalars(select(Question).where(Question.id.in_(due_qids))).all()}
        if due_qids
        else {}
    )

    revision_due: list[dict[str, Any]] = []
    for row in due_rows:
        if len(revision_due) >= 5:
            break
        if row.item_type == "problem":
            problem = due_problems.get(row.item_id)
            if problem is None:
                continue
            revision_due.append(
                {
                    "type": "problem",
                    "id": row.item_id,
                    "title": problem.title,
                    "reason": f"Spaced review · {row.interval_days}d interval",
                    "due_stage": row.due_date,
                    "link": f"/problems/{problem.topic}/{row.item_id}",
                }
            )
        else:
            question = due_questions.get(row.item_id)
            if question is None:
                continue
            preview = question.prompt[:60] + ("..." if len(question.prompt) > 60 else "")
            revision_due.append(
                {
                    "type": "question",
                    "id": row.item_id,
                    "title": f"Concept: {preview}",
                    "reason": f"Spaced review · {row.interval_days}d interval",
                    "due_stage": row.due_date,
                    "link": f"/quiz/{question.topic}",
                }
            )

    total_problems = (
        db.scalar(select(func.count(Problem.slug)).where(Problem.review_status == "verified")) or 0
    )

    return ProgressSummaryResponse(
        solved_count=solved_count,
        doing_count=doing_count,
        total_problems=total_problems,
        current_streak=streak,
        activity_days=act_map,
        progress=progress_map,
        notes=notes_map,
        bookmarks=bookmarks_list,
        visited_visualizers=visited_list,
        has_imported_local=bool(user.has_imported_local),
        quiz_scores=quiz_scores,
        weakest_topics=weakest_topics,
        revision_due=revision_due,
        preferred_language=getattr(user, "preferred_language", None) or "python",
        daily_goal=_user_daily_goal(user),
    )


def _validated_local_date(value: str | None) -> str | None:
    """Client-supplied date, or 422.

    `validate_local_date` raises ValueError, which on a query parameter would
    surface as a 500 rather than a client error, so translate it.
    """
    try:
        return validate_local_date(value)
    except ValueError as err:
        raise HTTPException(
            status_code=HTTP_422,
            detail={"code": "INVALID_LOCAL_DATE", "message": str(err)},
        ) from err


def _user_daily_goal(user: User) -> dict | None:
    raw = getattr(user, "daily_goal_json", None)
    if not raw:
        return None
    try:
        parsed = json.loads(raw)
    except (ValueError, TypeError):
        # A corrupt column must not take down the whole dashboard summary. Log
        # and treat it as "no goal set"; the next save overwrites it.
        logging.getLogger(__name__).warning(
            "Ignoring unparseable daily_goal_json for user %s", getattr(user, "id", "?")
        )
        return None
    return parsed if isinstance(parsed, dict) else None


@router.get("/settings", response_model=SettingsResponse)
def get_settings(
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    return SettingsResponse(
        preferred_language=getattr(user, "preferred_language", None) or "python",
        daily_goal=_user_daily_goal(user),
    )


@router.put("/settings", response_model=SettingsResponse)
def update_settings(
    req: SettingsUpdate,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    if req.preferred_language is not None:
        user.preferred_language = req.preferred_language
    if req.clear_daily_goal:
        # Pinned goals are sticky server-side too: only an explicit clear removes
        # them, and a pinned goal is not cleared by a plain "clear". The client
        # already refuses to drop a permanent goal locally, so clearing it here
        # made the two disagree and lost the pin on every other device.
        current = _user_daily_goal(user)
        if not (current and current.get("permanent")):
            user.daily_goal_json = None
    elif req.daily_goal is not None:
        user.daily_goal_json = json.dumps(req.daily_goal.model_dump())
    db.commit()
    db.refresh(user)
    return SettingsResponse(
        preferred_language=user.preferred_language or "python",
        daily_goal=json.loads(user.daily_goal_json) if user.daily_goal_json else None,
    )


@router.post("/import-local", response_model=ProgressSummaryResponse)
def import_local_progress(
    req: LocalImportRequest,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    # If already imported, return current summary idempotently
    if user.has_imported_local:
        return get_progress_summary(user=user, db=db)

    now_str = utcnow_iso()

    # 1. Merge problem progress (max-wins)
    existing_progress = {
        p.problem_slug: p
        for p in db.scalars(select(ProblemProgress).where(ProblemProgress.user_id == user.id)).all()
    }
    for slug, imported_status in req.progress.items():
        if imported_status not in STATUS_RANK:
            continue
        curr = existing_progress.get(slug)
        if curr:
            curr_rank = STATUS_RANK.get(curr.status, 0)
            imp_rank = STATUS_RANK.get(imported_status, 0)
            if imp_rank > curr_rank:
                curr.status = imported_status
                curr.updated_at = now_str
        else:
            new_p = ProblemProgress(
                user_id=user.id,
                problem_slug=slug,
                status=imported_status,
                updated_at=now_str,
            )
            db.add(new_p)

    # 2. Merge notes
    existing_notes = {
        n.problem_slug: n for n in db.scalars(select(Note).where(Note.user_id == user.id)).all()
    }
    for slug, text in req.notes.items():
        if not text or not text.strip():
            continue
        curr_note = existing_notes.get(slug)
        if not curr_note:
            db.add(Note(user_id=user.id, problem_slug=slug, text=text, updated_at=now_str))
        elif len(text) > len(curr_note.text):
            curr_note.text = text
            curr_note.updated_at = now_str

    # 3. Merge activity days
    existing_days = {
        a.day: a
        for a in db.scalars(select(ActivityDay).where(ActivityDay.user_id == user.id)).all()
    }
    for day in req.activity_days:
        if day not in existing_days:
            db.add(ActivityDay(user_id=user.id, day=day, action_count=1))

    # 4. Merge visited visualizers
    existing_vis = {
        v.visualizer_id: v
        for v in db.scalars(
            select(VisualizerCompletion).where(VisualizerCompletion.user_id == user.id)
        ).all()
    }
    for vid in req.visited_visualizers:
        if vid not in existing_vis:
            db.add(
                VisualizerCompletion(
                    user_id=user.id,
                    visualizer_id=vid,
                    visits=1,
                    first_completed_at=now_str,
                )
            )

    # Mark imported
    user.has_imported_local = 1
    db.commit()

    return get_progress_summary(user=user, db=db)
