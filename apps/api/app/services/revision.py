"""Spaced repetition scheduling (SuperMemo-2).

The scheduler is deliberately small and fully deterministic: given the current
state and a grade it returns the next state. That makes it testable without a
database, which matters because a scheduler bug is invisible until a user's due
list silently stops filling up.

Grades follow SM-2's own scale, 0-5. The app only produces two of them from
user actions, but the endpoint accepts any for a manual self-rating:

    5 perfect recall   4 correct with hesitation   3 correct with difficulty
    2 wrong but familiar on seeing the answer
    1 wrong, answer remembered   0 blackout
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timedelta

from app.services.streak import get_current_date_str

MIN_EASE = 1.3
START_EASE = 2.5
#: Grade at or above this counts as recalled, so the interval grows.
PASS_GRADE = 3


def _add_days(day: str, days: int) -> str:
    base = datetime.strptime(day, "%Y-%m-%d").date()
    return (base + timedelta(days=days)).strftime("%Y-%m-%d")


@dataclass(frozen=True)
class ScheduleState:
    interval_days: int = 0
    ease: float = START_EASE
    reps: int = 0
    lapses: int = 0


@dataclass(frozen=True)
class NextSchedule:
    interval_days: int
    ease: float
    reps: int
    lapses: int
    due_date: str


def next_schedule(state: ScheduleState, grade: int, reviewed_on: str | None = None) -> NextSchedule:
    """SM-2 update. `grade` is clamped to 0-5; anything unparseable is a fail."""
    grade = max(0, min(5, int(grade)))
    day = reviewed_on or get_current_date_str()

    if grade < PASS_GRADE:
        # A miss resets the repetition count but not the learned difficulty of
        # the item, so a lapsed card comes back tomorrow and then climbs again
        # from an interval of 1.
        return NextSchedule(
            interval_days=1,
            ease=max(MIN_EASE, state.ease - 0.2),
            reps=0,
            lapses=state.lapses + 1,
            due_date=_add_days(day, 1),
        )

    reps = state.reps + 1
    if reps == 1:
        interval = 1
    elif reps == 2:
        interval = 6
    else:
        # A brand new item that somehow skipped the first two reps still gets a
        # sane interval rather than 0.
        base = state.interval_days or 6
        interval = max(1, round(base * state.ease))

    # Canonical SM-2: EF' = EF + (0.1 - (5-q)*(0.08 + (5-q)*0.02)).
    # The abbreviated form used earlier dropped the second term, which made every
    # grade above 3 *raise* ease where SM-2 holds it flat at q=4 — and because
    # the interval is round(base * ease), that drift compounded and silently
    # thinned the due list for anyone who mostly succeeded.
    delta = 5 - grade
    ease = max(MIN_EASE, state.ease + (0.1 - delta * (0.08 + delta * 0.02)))
    return NextSchedule(
        interval_days=interval,
        ease=ease,
        reps=reps,
        lapses=state.lapses,
        due_date=_add_days(day, interval),
    )


def grade_for_submission(verdict: str) -> int | None:
    """Maps a judge verdict onto an SM-2 grade.

    An accepted submission is recall; a wrong answer, a runtime error or a
    compile error all mean the item was not retrieved successfully. TLE is left
    alone (None): it says nothing about recall, and demoting an item for a
    performance problem teaches the schedule the wrong lesson.
    """
    if verdict == "AC":
        return 4
    if verdict in {"WA", "RE", "CE"}:
        return 2
    return None


def apply_review(
    db,
    user_id: str,
    item_type: str,
    item_id: str,
    grade: int,
    reviewed_on: str | None = None,
):
    """Upserts the schedule row for one item and returns it.

    Reads the existing SM-2 state rather than starting from scratch, so the
    interval grows across sessions. Commits, because every caller wants the new
    due date persisted before it responds.
    """
    from sqlalchemy import select

    from app.models.revision import RevisionItem
    from app.models.user import utcnow_iso

    row = db.scalar(
        select(RevisionItem).where(
            RevisionItem.user_id == user_id,
            RevisionItem.item_type == item_type,
            RevisionItem.item_id == item_id,
        )
    )
    state = (
        ScheduleState(
            interval_days=row.interval_days,
            ease=row.ease,
            reps=row.reps,
            lapses=row.lapses,
        )
        if row
        else ScheduleState()
    )
    nxt = next_schedule(state, grade, reviewed_on)

    if row is None:
        row = RevisionItem(
            user_id=user_id,
            item_type=item_type,
            item_id=item_id,
            created_at=utcnow_iso(),
        )
        db.add(row)

    row.interval_days = nxt.interval_days
    row.ease = nxt.ease
    row.reps = nxt.reps
    row.lapses = nxt.lapses
    row.due_date = nxt.due_date
    row.last_reviewed_at = utcnow_iso()
    db.commit()
    db.refresh(row)
    return row


def record_submission(db, user_id: str, problem_slug: str, verdict: str) -> None:
    """Schedules (or reschedules) a problem after a judged submission."""
    grade = grade_for_submission(verdict)
    if grade is None:
        return
    apply_review(db, user_id, "problem", problem_slug, grade)
