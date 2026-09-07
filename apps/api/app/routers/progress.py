from fastapi import APIRouter, Depends
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.db import get_db
from app.models.progress import (
    ActivityDay,
    Bookmark,
    Note,
    ProblemProgress,
    VisualizerCompletion,
)
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
