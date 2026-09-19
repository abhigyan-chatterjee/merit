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

    res = client.post("/api/v1/progress/visualizers/sorting/visit")
    assert res.status_code == 200
    assert res.json()["visits"] == 1

    res = client.post("/api/v1/progress/visualizers/sorting/visit")
    assert res.status_code == 200
    assert res.json()["visits"] == 2


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
