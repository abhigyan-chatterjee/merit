from datetime import UTC, datetime, timedelta

from fastapi.testclient import TestClient

TODAY = datetime.now(UTC).strftime("%Y-%m-%d")
YESTERDAY = (datetime.now(UTC) - timedelta(days=1)).strftime("%Y-%m-%d")


def register_user(client: TestClient, email: str, name: str = "Test User") -> str:
    res = client.post(
        "/api/v1/auth/register",
        json={
            "email": email,
            "display_name": name,
            "password": "StrongPassword123!",
        },
    )
    assert res.status_code == 201
    return str(res.json()["id"])


def test_progress_unauthorized(client: TestClient):
    res = client.get("/api/v1/progress/summary")
    assert res.status_code == 401

    res = client.put(
        "/api/v1/progress/problems/two-sum",
        json={"status": "Done"},
    )
    assert res.status_code == 401


def test_problem_progress_lifecycle(client: TestClient):
    register_user(client, "student1@merit.org")

    # Initial state is default Todo
    res = client.get("/api/v1/progress/problems/two-sum")
    assert res.status_code == 200
    assert res.json()["status"] == "Todo"

    # Update to Doing
    res = client.put(
        "/api/v1/progress/problems/two-sum",
        json={"status": "Doing", "local_date": TODAY},
    )
    assert res.status_code == 200
    assert res.json()["status"] == "Doing"

    # Update to Done
    res = client.put(
        "/api/v1/progress/problems/two-sum",
        json={"status": "Done", "local_date": TODAY},
    )
    assert res.status_code == 200
    assert res.json()["status"] == "Done"

    # Verify summary reflects 1 solved
    summary = client.get("/api/v1/progress/summary").json()
    assert summary["solved_count"] == 1
    assert summary["progress"]["two-sum"] == "Done"
    assert TODAY in summary["activity_days"]


def test_notes_and_bookmarks(client: TestClient):
    register_user(client, "student2@merit.org")

    # Empty note initially
    res = client.get("/api/v1/progress/notes/two-sum")
    assert res.status_code == 200
    assert res.json()["text"] == ""

    # Save note
    res = client.put(
        "/api/v1/progress/notes/two-sum",
        json={"text": "Use hashmap for O(n) lookup.", "local_date": TODAY},
    )
    assert res.status_code == 200
    assert res.json()["text"] == "Use hashmap for O(n) lookup."

    # Bookmark toggle
    res = client.post(
        "/api/v1/progress/bookmarks/toggle",
        json={"item_type": "problem", "item_id": "two-sum"},
    )
    assert res.status_code == 200
    assert res.json()["bookmarked"] is True

    # Toggle off
    res = client.post(
        "/api/v1/progress/bookmarks/toggle",
        json={"item_type": "problem", "item_id": "two-sum"},
    )
    assert res.status_code == 200
    assert res.json()["bookmarked"] is False


def test_visualizer_visit_tracking(client: TestClient):
    register_user(client, "student3@merit.org")
    local_date = (datetime.now(UTC) + timedelta(days=1)).strftime("%Y-%m-%d")

    res = client.post(
        f"/api/v1/progress/visualizers/sorting/visit?local_date={local_date}"
    )
    assert res.status_code == 200
    assert res.json()["visits"] == 1

    res = client.post(
        f"/api/v1/progress/visualizers/sorting/visit?local_date={local_date}"
    )
    assert res.status_code == 200
    assert res.json()["visits"] == 2

    summary = client.get(
        f"/api/v1/progress/summary?local_date={local_date}"
    ).json()
    assert summary["activity_days"] == {local_date: 2}
    assert summary["current_streak"] == 1


def test_import_local_ignores_unmerged_keys(client: TestClient):
    """The web client still sends quiz/streak keys it used to; they have no
    server-side merge target, so sending them must be accepted silently rather
    than 422-ing the whole import. Stopping the import from accepting them
    instead is a deliberately separate decision."""
    register_user(client, "student5@merit.org")
    res = client.post(
        "/api/v1/progress/import-local",
        json={
            "progress": {"two-sum": "Done"},
            "quizzes": {"arrays-hashing": 92},
            "streak": 5,
            "activity_days": [TODAY],
        },
    )
    assert res.status_code == 200
    assert res.json()["has_imported_local"] is True
    assert "two-sum" in res.json()["progress"]


def test_import_local_max_wins(client: TestClient):
    register_user(client, "student4@merit.org")

    # Existing progress: two-sum is Doing
    client.put("/api/v1/progress/problems/two-sum", json={"status": "Doing"})

    # Import local data: two-sum is Done (higher), three-sum is Doing
    res = client.post(
        "/api/v1/progress/import-local",
        json={
            "progress": {
                "two-sum": "Done",
                "three-sum": "Doing",
            },
            "notes": {
                "two-sum": "Imported note text.",
            },
            "activity_days": [YESTERDAY, TODAY],
            "visited_visualizers": ["sorting", "bst"],
        },
    )
    assert res.status_code == 200
    data = res.json()
    assert data["has_imported_local"] is True
    assert data["progress"]["two-sum"] == "Done"
    assert data["progress"]["three-sum"] == "Doing"
    assert data["notes"]["two-sum"] == "Imported note text."
    assert "sorting" in data["visited_visualizers"]
    assert "bst" in data["visited_visualizers"]

    # Idempotent second import does not throw error
    res2 = client.post(
        "/api/v1/progress/import-local",
        json={"progress": {"two-sum": "Todo"}},
    )
    assert res2.status_code == 200
    # Two-sum remains Done
    assert res2.json()["progress"]["two-sum"] == "Done"


def test_unpin_daily_goal_clears_permanent_goal(client: TestClient):
    register_user(client, "unpin@example.com")
    res = client.put(
        "/api/v1/progress/settings",
        json={
            "daily_goal": {
                "kind": "problems",
                "label": "Pin",
                "target": 5,
                "permanent": True,
            }
        },
    )
    assert res.status_code == 200
    assert res.json()["daily_goal"]["permanent"] is True

    # A plain clear must not drop the pinned goal.
    res = client.put("/api/v1/progress/settings", json={"clear_daily_goal": True})
    assert res.json()["daily_goal"] is not None

    # unpin_daily_goal clears it unconditionally.
    res = client.put("/api/v1/progress/settings", json={"unpin_daily_goal": True})
    assert res.status_code == 200
    assert res.json()["daily_goal"] is None


def test_import_local_caps_rejected(client: TestClient):
    register_user(client, "caps@example.com")
    res = client.post(
        "/api/v1/progress/import-local",
        json={"activity_days": ["not-a-date"]},
    )
    assert res.status_code == 422
    res = client.post(
        "/api/v1/progress/import-local",
        json={"visited_visualizers": [f"v{i}" for i in range(51)]},
    )
    assert res.status_code == 422
    res = client.post(
        "/api/v1/progress/import-local",
        json={"progress": {f"p{i}": "Done" for i in range(1001)}},
    )
    assert res.status_code == 422
    res = client.put("/api/v1/progress/notes/two-sum", json={"text": "x" * 20001})
    assert res.status_code == 422


def test_settings_target_saving_reading_and_clearing(client: TestClient):
    register_user(client, "targets@example.com")

    res = client.put(
        "/api/v1/progress/settings",
        json={"target_drive_date": "2027-01-15", "target_tier": "faang"},
    )
    assert res.status_code == 200, res.text
    body = res.json()
    assert body["target_drive_date"] == "2027-01-15"
    assert body["target_tier"] == "faang"

    res = client.get("/api/v1/progress/settings")
    assert res.status_code == 200
    assert res.json()["target_drive_date"] == "2027-01-15"
    assert res.json()["target_tier"] == "faang"

    summary = client.get("/api/v1/progress/summary").json()
    assert summary["target_drive_date"] == "2027-01-15"
    assert summary["target_tier"] == "faang"
    assert summary["due_today_count"] == 0

    res = client.put(
        "/api/v1/progress/settings",
        json={"clear_target_drive_date": True},
    )
    assert res.status_code == 200
    assert res.json()["target_drive_date"] is None
    # Tier untouched by clearing the date.
    assert res.json()["target_tier"] == "faang"

    res = client.get("/api/v1/progress/settings")
    assert res.json()["target_drive_date"] is None


def test_settings_rejects_invalid_tier_and_drive_date(client: TestClient):
    register_user(client, "bad-targets@example.com")

    res = client.put("/api/v1/progress/settings", json={"target_tier": "manga"})
    assert res.status_code == 422

    res = client.put("/api/v1/progress/settings", json={"target_drive_date": "not-a-date"})
    assert res.status_code == 422

    res = client.put(
        "/api/v1/progress/settings", json={"target_drive_date": "2027-02-30"}
    )
    assert res.status_code == 422

    res = client.put("/api/v1/progress/settings", json={"target_drive_date": "1999-01-01"})
    assert res.status_code == 422


def test_due_today_count_counts_due_but_not_future(client, db_session):
    """Strictly due items (<= today) count; future items and other users' do not."""
    from datetime import timedelta

    from sqlalchemy import select

    from app.models.revision import RevisionItem
    from app.models.user import User

    register_user(client, "duecount@example.com")

    user = db_session.scalar(select(User).where(User.email == "duecount@example.com"))
    assert user is not None

    tomorrow = (datetime.now(UTC) + timedelta(days=1)).strftime("%Y-%m-%d")
    db_session.add(
        RevisionItem(
            user_id=user.id,
            item_type="problem",
            item_id="two-sum",
            due_date=TODAY,
            interval_days=1,
            ease=2.5,
            reps=1,
            lapses=0,
        )
    )
    db_session.add(
        RevisionItem(
            user_id=user.id,
            item_type="problem",
            item_id="3sum",
            due_date=tomorrow,
            interval_days=1,
            ease=2.5,
            reps=1,
            lapses=0,
        )
    )
    db_session.flush()

    summary = client.get("/api/v1/progress/summary").json()
    assert summary["due_today_count"] == 1
    # Future item is still surfaced in revision_due (window) but not counted.
    assert client.get("/api/v1/revision/due").json()["today"] == TODAY
