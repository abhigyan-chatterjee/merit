from datetime import UTC, datetime, timedelta

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.progress import ActivityDay


def get_current_date_str() -> str:
    return datetime.now(UTC).strftime("%Y-%m-%d")


def record_activity(db: Session, user_id: str, local_date: str | None = None) -> None:
    day = local_date or get_current_date_str()
    stmt = select(ActivityDay).where(
        ActivityDay.user_id == user_id,
        ActivityDay.day == day,
    )
    existing = db.scalar(stmt)
    if existing:
        existing.action_count += 1
    else:
        new_day = ActivityDay(user_id=user_id, day=day, action_count=1)
        db.add(new_day)
    db.flush()


def compute_streak(days: list[str], reference_day: str | None = None) -> int:
    if not days:
        return 0

    unique_days = sorted({d for d in days if d}, reverse=True)
    if not unique_days:
        return 0

    today = (
        datetime.strptime(reference_day, "%Y-%m-%d").date()
        if reference_day
        else datetime.now(UTC).date()
    )
    yesterday = today - timedelta(days=1)

    parsed_dates = []
    for d_str in unique_days:
        try:
            parsed_dates.append(datetime.strptime(d_str, "%Y-%m-%d").date())
        except ValueError:
            continue

    if not parsed_dates:
        return 0

    # Streak is active if either today or yesterday was an active day
    first_date = parsed_dates[0]
    if first_date != today and first_date != yesterday:
        return 0

    streak = 1
    expected_prev = first_date - timedelta(days=1)

    for curr in parsed_dates[1:]:
        if curr == expected_prev:
            streak += 1
            expected_prev = curr - timedelta(days=1)
        elif curr > expected_prev:
            # Duplicate or same day handled by set, but just in case
            continue
        else:
            break

    return streak
