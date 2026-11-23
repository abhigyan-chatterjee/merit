from fastapi.testclient import TestClient

import app.routers.feedback as feedback_module
from app.db import SessionLocal
from app.main import app
from app.models.feedback import Feedback

client = TestClient(app)


class _FakeGitHubResponse:
    def __init__(self):
        self.status_code = 201
        self.text = ""

    def json(self):
        return {"html_url": "https://github.com/owner/repo/issues/1", "number": 1}


class _FakeGitHubClient:
    captured = None

    def __init__(self, *args, **kwargs):
        pass

    async def __aenter__(self):
        return self

    async def __aexit__(self, *args):
        return False

    async def post(self, url, headers=None, json=None):
        _FakeGitHubClient.captured = {"url": url, "json": json}
        return _FakeGitHubResponse()


def test_submit_feedback_persists_to_db():
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
    assert "feedback_id" in data
    assert data["feedback_id"] is not None

    with SessionLocal() as db:
        fb = db.get(Feedback, data["feedback_id"])
        assert fb is not None
        assert fb.title == payload["title"]
        assert fb.category == payload["category"]
        assert fb.status == "open"


def test_feedback_email_persisted_but_withheld_from_github(monkeypatch):
    monkeypatch.setattr(feedback_module.settings, "github_token", "gh-test-token", raising=False)
    monkeypatch.setattr(feedback_module.httpx, "AsyncClient", _FakeGitHubClient)
    _FakeGitHubClient.captured = None
    payload = {
        "title": "Bug in feedback handling",
        "description": "Please keep private contact details out of public issues.",
        "category": "bug",
        "page_url": "https://merit.nullbit.in/problems/two-sum",
        "problem_slug": "two-sum",
        "email": "private-user@example.com",
    }
    response = client.post("/api/v1/feedback", json=payload)
    assert response.status_code == 201
    feedback_id = response.json()["feedback_id"]
    with SessionLocal() as db:
        fb = db.get(Feedback, feedback_id)
        assert fb is not None
        assert fb.email == "private-user@example.com"
    assert _FakeGitHubClient.captured is not None
    issue_body = _FakeGitHubClient.captured["json"]["body"]
    assert "private-user@example.com" not in issue_body


def test_submit_feedback_rejects_unknown_category():
    payload = {
        "title": "Valid title here",
        "description": "Valid description here.",
        "category": "not-a-category",
    }
    response = client.post("/api/v1/feedback", json=payload)
    assert response.status_code == 422


def test_submit_feedback_validation_error():
    # Title too short
    payload = {
        "title": "hi",
        "description": "Short",
        "category": "bug",
    }
    response = client.post("/api/v1/feedback", json=payload)
    assert response.status_code == 422
