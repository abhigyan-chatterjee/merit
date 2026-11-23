"""Spaced repetition: SM-2 maths and the end-to-end due loop.

The feature exists because `revision_due` used to be re-derived per request from
the last few submissions with a hardcoded "1d review" label — nothing was ever
scheduled, so nothing was ever actually due.
"""

from datetime import datetime

from sqlalchemy.orm import Session

from app.services.revision import (
    MIN_EASE,
    ScheduleState,
    grade_for_submission,
    next_schedule,
)
from app.services.streak import get_current_date_str

# --- SM-2 unit behaviour ----------------------------------------------------


def _days_from(base: str, due: str) -> int:
    return (datetime.strptime(due, "%Y-%m-%d") - datetime.strptime(base, "%Y-%m-%d")).days


def test_first_success_is_one_day_out():
    nxt = next_schedule(ScheduleState(), 4, "2026-10-26")
    assert nxt.interval_days == 1
    assert nxt.due_date == "2026-10-27"
    assert nxt.reps == 1


def test_second_success_is_six_days_out():
    first = next_schedule(ScheduleState(), 4, "2026-10-26")
    second = next_schedule(
        ScheduleState(first.interval_days, first.ease, first.reps, first.lapses),
        4,
        "2026-10-27",
    )
    assert second.interval_days == 6
    assert second.reps == 2


def test_interval_grows_by_ease_after_two_reps():
    state = ScheduleState(interval_days=6, ease=2.5, reps=2, lapses=0)
    nxt = next_schedule(state, 4, "2026-10-26")
    assert nxt.interval_days == 15  # round(6 * 2.5)


def test_a_miss_resets_reps_and_records_a_lapse():
    state = ScheduleState(interval_days=15, ease=2.5, reps=3, lapses=0)
    nxt = next_schedule(state, 2, "2026-10-26")
    assert nxt.interval_days == 1
    assert nxt.reps == 0
    assert nxt.lapses == 1
    assert nxt.ease < state.ease


def test_ease_never_falls_below_the_floor():
    state = ScheduleState(interval_days=1, ease=MIN_EASE, reps=0, lapses=5)
    nxt = next_schedule(state, 0, "2026-10-26")
    assert nxt.ease == MIN_EASE


def test_grade_is_clamped():
    assert next_schedule(ScheduleState(), 99, "2026-10-26").interval_days == 1
    assert next_schedule(ScheduleState(), -5, "2026-10-26").reps == 0


def test_verdict_mapping():
    assert grade_for_submission("AC") == 4
    assert grade_for_submission("WA") == 2
    assert grade_for_submission("CE") == 2
    assert grade_for_submission("RE") == 2
    # A timeout says nothing about recall, so it must not demote the item.
    assert grade_for_submission("TLE") is None


# --- end to end -------------------------------------------------------------


def _register(client, email="revision@example.com"):
    response = client.post(
        "/api/v1/auth/register",
        json={"email": email, "display_name": "Rev", "password": "StrongPassw0rd!"},
    )
    assert response.status_code == 201, response.text
    return response



def _make_due_now(db: Session) -> None:
    """Backdates this test's schedule rows to today, inside the fixture txn.

    Nothing is due on the day it is graded — an AC schedules tomorrow — so
    exercising the due list requires moving the clock.

    Takes the fixture session and does not commit. Opening a second SessionLocal
    and committing used to work only because StaticPool gives both sessions the
    same DBAPI connection, so that COMMIT committed the outer transaction and
    the fixture's rollback could no longer undo the change: state leaked between
    tests, and it backdated every user's rows rather than this test's.
    """
    from sqlalchemy import update as sa_update

    from app.models.revision import RevisionItem

    db.execute(sa_update(RevisionItem).values(due_date=get_current_date_str()))
    db.flush()


ACCEPTED_JS = """
function solve(nums, target) {
  const m = new Map();
  for (let i = 0; i < nums.length; i++) {
    if (m.has(target - nums[i])) return [m.get(target - nums[i]), i];
    m.set(nums[i], i);
  }
  return [];
}
"""


def test_accepted_submission_schedules_a_review(client, db_session):
    _register(client)
    submit = client.post(
        "/api/v1/judge/submit",
        json={"problem_slug": "two-sum", "language": "javascript", "code": ACCEPTED_JS},
    )
    assert submit.status_code == 200, submit.text
    assert submit.json()["verdict"] == "AC"

    # An accepted submission schedules the item for tomorrow, so it is
    # deliberately absent from today's due list.
    today_list = client.get("/api/v1/revision/due").json()
    assert today_list["count"] == 0, "a fresh AC must not be due immediately"

    _make_due_now(db_session)
    due = client.get("/api/v1/revision/due").json()
    assert due["count"] == 1, due
    item = due["items"][0]
    assert item["item_type"] == "problem"
    assert item["item_id"] == "two-sum"
    assert item["interval_days"] == 1
    assert item["due_date"] == due["today"]


def test_reviewing_an_item_moves_it_forward(client, db_session):
    _register(client, email="revision2@example.com")
    client.post(
        "/api/v1/judge/submit",
        json={"problem_slug": "two-sum", "language": "javascript", "code": ACCEPTED_JS},
    )

    review = client.post(
        "/api/v1/revision/problem/two-sum/review",
        json={"grade": 5},
    )
    assert review.status_code == 200, review.text
    body = review.json()
    assert body["reps"] == 2
    assert body["interval_days"] == 6
    assert body["due_date"] > get_current_date_str()


def test_failed_submission_schedules_for_tomorrow_as_a_lapse(client):
    _register(client, email="revision3@example.com")
    submit = client.post(
        "/api/v1/judge/submit",
        json={
            "problem_slug": "two-sum",
            "language": "javascript",
            "code": "function solve(n, t) { return [9, 9]; }",
        },
    )
    assert submit.status_code == 200, submit.text
    assert submit.json()["verdict"] == "WA"

    review = client.post("/api/v1/revision/problem/two-sum/review", json={"grade": 2})
    assert review.status_code == 200
    assert review.json()["lapses"] == 2  # one from the WA, one from this review
    assert review.json()["interval_days"] == 1


def test_due_list_is_per_user(client, db_session):
    _register(client, email="owner@example.com")
    client.post(
        "/api/v1/judge/submit",
        json={"problem_slug": "two-sum", "language": "javascript", "code": ACCEPTED_JS},
    )
    _make_due_now(db_session)
    assert client.get("/api/v1/revision/due").json()["count"] == 1

    # A different account must not see another user's queue.
    other = client.__class__(client.app)
    registered = other.post(
        "/api/v1/auth/register",
        json={"email": "other@example.com", "display_name": "Other", "password": "StrongPassw0rd!"},
    )
    assert registered.status_code == 201, registered.text
    other_due = other.get("/api/v1/revision/due")
    assert other_due.status_code == 200, other_due.text
    assert other_due.json()["count"] == 0


def test_review_rejects_an_unknown_item(client):
    _register(client, email="revision4@example.com")
    response = client.post("/api/v1/revision/problem/not-a-real-slug/review", json={"grade": 4})
    assert response.status_code == 404


def test_review_rejects_a_bad_item_type(client):
    _register(client, email="revision5@example.com")
    response = client.post("/api/v1/revision/banana/two-sum/review", json={"grade": 4})
    assert response.status_code == 422
    assert response.json()["detail"]["code"] == "INVALID_ITEM_TYPE"


def test_review_rejects_an_out_of_range_grade(client):
    _register(client, email="revision6@example.com")
    client.post(
        "/api/v1/judge/submit",
        json={"problem_slug": "two-sum", "language": "javascript", "code": ACCEPTED_JS},
    )
    too_high = client.post("/api/v1/revision/problem/two-sum/review", json={"grade": 9})
    assert too_high.status_code == 422


def test_anonymous_cannot_read_the_due_list(client):
    client.cookies.clear()
    assert client.get("/api/v1/revision/due").status_code == 401


def test_summary_exposes_the_scheduled_item(client, db_session):
    """The dashboard reads revision_due from the summary, not a heuristic."""
    _register(client, email="revision7@example.com")
    client.post(
        "/api/v1/judge/submit",
        json={
            "problem_slug": "two-sum",
            "language": "javascript",
            "code": "function solve(n,t){return [9,9];}",
        },
    )
    # A WA schedules for tomorrow; force it due now so the summary surfaces it.
    _make_due_now(db_session)

    summary = client.get("/api/v1/progress/summary").json()
    assert summary["revision_due"], "summary must surface a due item"
    entry = summary["revision_due"][0]
    assert entry["type"] == "problem"
    assert entry["id"] == "two-sum"
    # The old implementation hardcoded this string; it is a date now.
    assert entry["due_stage"] == get_current_date_str()


def test_due_returns_enriched_problem_card(client, db_session):
    """Problem cards carry difficulty, link, prompt preview and answer summary."""
    from sqlalchemy import select

    from app.models.content import Problem
    from app.models.revision import RevisionItem
    from app.models.user import User

    _register(client, email="enriched-problem@example.com")
    user = db_session.scalar(select(User).where(User.email == "enriched-problem@example.com"))
    assert user is not None
    problem = db_session.scalar(select(Problem).where(Problem.slug == "two-sum"))
    assert problem is not None

    db_session.add(
        RevisionItem(
            user_id=user.id,
            item_type="problem",
            item_id="two-sum",
            due_date=get_current_date_str(),
            interval_days=1,
            ease=2.5,
            reps=1,
            lapses=0,
        )
    )
    db_session.flush()

    due = client.get("/api/v1/revision/due").json()
    assert due["count"] == 1, due
    item = due["items"][0]
    assert item["difficulty"] == problem.difficulty
    assert item["link"] == f"/problems/{problem.topic}/two-sum"
    assert item["prompt"] == (problem.statement or "")[:240].strip()
    assert item["prompt"]
    assert problem.pattern in item["answer_summary"]


def test_due_returns_enriched_question_card(client, db_session):
    """Question cards carry difficulty, quiz link, full prompt and answer summary."""
    import json

    from sqlalchemy import select

    from app.models.content import Question
    from app.models.revision import RevisionItem
    from app.models.user import User

    _register(client, email="enriched-question@example.com")
    user = db_session.scalar(select(User).where(User.email == "enriched-question@example.com"))
    assert user is not None
    question = db_session.scalar(select(Question).limit(1))
    assert question is not None

    db_session.add(
        RevisionItem(
            user_id=user.id,
            item_type="question",
            item_id=question.id,
            due_date=get_current_date_str(),
            interval_days=1,
            ease=2.5,
            reps=1,
            lapses=0,
        )
    )
    db_session.flush()

    due = client.get("/api/v1/revision/due").json()
    assert due["count"] == 1, due
    item = due["items"][0]
    assert item["item_type"] == "question"
    assert item["difficulty"] == question.difficulty
    assert item["link"] == f"/quiz/{question.topic}"
    assert item["prompt"] == question.prompt
    options = json.loads(question.options)
    correct_text = options[question.correct_index]
    assert correct_text in item["answer_summary"]
    assert question.explanation in item["answer_summary"]
