from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)


def test_submit_feedback_fallback():
    payload = {
        "title": "Test case missing edge case",
        "description": "In problem two-sum, empty arrays should be handled cleanly.",
        "category": "testcase",
        "page_url": "https://merit.nullbit.in/problems/two-sum",
        "problem_slug": "two-sum",
        "email": "test@nullbit.in",
    }
    response = client.post("/api/v1/feedback", json=payload)
    assert response.status_code == 201
    data = response.json()
    assert data["status"] == "ok"
    assert "Thank you" in data["message"] or "created" in data["message"]


def test_submit_feedback_validation_error():
    # Title too short
    payload = {
        "title": "hi",
        "description": "Short",
        "category": "bug",
    }
    response = client.post("/api/v1/feedback", json=payload)
    assert response.status_code == 422
