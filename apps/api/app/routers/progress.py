import json
from typing import Any

from fastapi import APIRouter, Depends
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.db import get_db
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
)
from app.security import get_current_user
from app.services.streak import compute_streak, record_activity

router = APIRouter(prefix="/api/v1/progress", tags=["Progress"])

STATUS_RANK = {"Done": 2, "Doing": 1, "Todo": 0}


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
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
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

    record_activity(db, user.id)
    db.commit()
    db.refresh(row)
    return row


@router.get("/summary", response_model=ProgressSummaryResponse)
def get_progress_summary(
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
    streak = compute_streak(list(act_map.keys()))

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

    # Analyze last 5 attempts
    last_5_attempts = attempts[:5]
    wrong_questions: list[tuple[str, str, str]] = []
    solved_qids: set[str] = set()

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
                    solved_qids.add(ans.question_id)
                else:
                    if ans.question_id not in solved_qids:
                        preview = (
                            (q.prompt[:60] + "...")
                            if q and len(q.prompt) > 60
                            else (q.prompt if q else "Question")
                        )
                        wrong_questions.append((ans.question_id, t, preview))

    # Incorporate submissions into weak areas
    recent_subs = db.scalars(
        select(Submission)
        .where(Submission.user_id == user.id)
        .order_by(Submission.created_at.desc())
        .limit(20)
    ).all()
    sub_slugs = list({s.problem_slug for s in recent_subs})
    wa_problems: list[tuple[str, str]] = []
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
            else:
                if progress_map.get(sub.problem_slug) != "Done":
                    wa_problems.append((sub.problem_slug, p.title if p else sub.problem_slug))

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

    # Build revision queue (spaced repetition: up to 5 items due today)
    revision_due: list[dict[str, Any]] = []
    seen_rev_ids: set[str] = set()

    for slug, title in wa_problems:
        if slug not in seen_rev_ids and progress_map.get(slug) != "Done":
            seen_rev_ids.add(slug)
            prob_topic = p_map[slug].topic if slug in p_map else "arrays"
            revision_due.append(
                {
                    "type": "problem",
                    "id": slug,
                    "title": title,
                    "reason": "Recent Wrong Answer on test cases",
                    "due_stage": "1d review",
                    "link": f"/problems/{prob_topic}/{slug}",
                }
            )
            if len(revision_due) >= 5:
                break

    if len(revision_due) < 5:
        for qid, topic, preview in wrong_questions:
            if qid not in seen_rev_ids and qid not in solved_qids:
                seen_rev_ids.add(qid)
                revision_due.append(
                    {
                        "type": "question",
                        "id": qid,
                        "title": f"Concept: {preview}",
                        "reason": f"Missed in {topic}",
                        "due_stage": "Spaced recall",
                        "link": f"/quiz/{topic}",
                    }
                )
                if len(revision_due) >= 5:
                    break

    return ProgressSummaryResponse(
        solved_count=solved_count,
        doing_count=doing_count,
        total_problems=30,
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
        preferred_language=getattr(user, "preferred_language", None) or "javascript",
        daily_goal=_user_daily_goal(user),
    )



def _user_daily_goal(user: User) -> dict | None:
    raw = getattr(user, "daily_goal_json", None)
    return json.loads(raw) if raw else None


@router.get("/settings", response_model=SettingsResponse)
def get_settings(
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    return SettingsResponse(
        preferred_language=getattr(user, "preferred_language", None) or "javascript",
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
        # Pinned goals are sticky server-side too: only an explicit clear removes them.
        user.daily_goal_json = None
    elif req.daily_goal is not None:
        user.daily_goal_json = json.dumps(req.daily_goal.model_dump())
    db.commit()
    db.refresh(user)
    return SettingsResponse(
        preferred_language=user.preferred_language or "javascript",
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
