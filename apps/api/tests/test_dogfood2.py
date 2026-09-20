"""Fail-first regression tests for Dogfood-2 sweep (authenticated deep flows)."""

import json

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import func, select
from sqlalchemy.orm import Session

import app.routers.auth as auth_router
import app.routers.tutor as tutor_module
from app.models.content import Question
from app.models.quiz import QuizAttempt
from app.models.submission import Submission
from app.seed import seed_problems

CORRECT_JS = """
function solve(nums, target) {
  const map = new Map();
  for (let i = 0; i < nums.length; i++) {
    const complement = target - nums[i];
    if (map.has(complement)) {
      return [map.get(complement), i];
    }
    map.set(nums[i], i);
  }
  return [];
}
"""


@pytest.fixture(autouse=True)
def _seed(db_session: Session):
    seed_problems(db_session)


@pytest.fixture(autouse=True)
def _clean_tutor_rate_limits():
    tutor_module._rate_buckets.clear()
    yield
    tutor_module._rate_buckets.clear()


def register(client: TestClient, email: str):
    res = client.post(
        "/api/v1/auth/register",
        json={"email": email, "display_name": "Dogfood", "password": "StrongPassword123!"},
    )
    assert res.status_code == 201
    return res


def submit_count(db_session: Session, email: str) -> int:
    from app.models.user import User

    user = db_session.scalar(select(User).where(User.email == email))
    return db_session.scalar(
        select(func.count(Submission.id)).where(Submission.user_id == user.id)
    )


def test_judge_rejects_non_pyjs_languages_without_persisting(
    client: TestClient, db_session: Session
):
    """AGENTS invariant #1: Python + JavaScript ONLY (app/schemas/judge.py)."""
    register(client, "dogfood-lang@merit.org")
    for lang in ("cpp", "java", "CPP", "Java"):
        res = client.post(
            "/api/v1/judge/submit",
            json={"problem_slug": "two-sum", "language": lang, "code": CORRECT_JS},
        )
        assert res.status_code == 422, res.text
        run = client.post(
            "/api/v1/judge/run",
            json={"problem_slug": "two-sum", "language": lang, "code": CORRECT_JS},
        )
        assert run.status_code == 422, run.text
    assert submit_count(db_session, "dogfood-lang@merit.org") == 0


def test_judge_rejects_empty_code_without_persisting(
    client: TestClient, db_session: Session
):
    register(client, "dogfood-empty@merit.org")
    for code in ("", "   ", "\n\t "):
        sub = client.post(
            "/api/v1/judge/submit",
            json={"problem_slug": "two-sum", "language": "javascript", "code": code},
        )
        assert sub.status_code == 422, sub.text
        assert sub.json()["detail"]["code"] == "EMPTY_CODE"
        run = client.post(
            "/api/v1/judge/run",
            json={"problem_slug": "two-sum", "language": "python", "code": code},
        )
        assert run.status_code == 422, run.text
    assert submit_count(db_session, "dogfood-empty@merit.org") == 0


def test_quiz_double_submit_rejected(client: TestClient):
    register(client, "dogfood-double@merit.org")
    gen = client.post("/api/v1/quizzes/generate", json={"topics": ["trees"], "count": 2})
    assert gen.status_code == 200
    attempt_id = gen.json()["attempt_id"]

    first = client.post(
        f"/api/v1/quizzes/attempts/{attempt_id}",
        json={"duration_sec": 5, "selected": {}},
    )
    assert first.status_code == 200

    second = client.post(
        f"/api/v1/quizzes/attempts/{attempt_id}",
        json={"duration_sec": 9, "selected": {}},
    )
    assert second.status_code == 409
    assert second.json()["detail"]["code"] == "ATTEMPT_ALREADY_SUBMITTED"

    detail = client.get(f"/api/v1/quizzes/attempts/{attempt_id}")
    assert detail.status_code == 200
    assert detail.json()["duration_sec"] == 5


def test_quiz_expired_mock_submit_rejected(client: TestClient, db_session: Session):
    register(client, "dogfood-expiry@merit.org")
    gen = client.post(
        "/api/v1/quizzes/generate",
        json={"topics": ["aptitude"], "count": 2, "is_mock": True, "duration_sec": 600},
    )
    assert gen.status_code == 200
    attempt_id = gen.json()["attempt_id"]
    assert gen.json()["expires_at"] is not None

    attempt = db_session.scalar(select(QuizAttempt).where(QuizAttempt.id == attempt_id))
    spec = json.loads(attempt.topic_spec)
    spec["expires_at"] = "2000-01-01T00:00:00+00:00"
    attempt.topic_spec = json.dumps(spec)
    db_session.flush()

    late = client.post(
        f"/api/v1/quizzes/attempts/{attempt_id}",
        json={"duration_sec": 9999, "selected": {}},
    )
    assert late.status_code == 410
    assert late.json()["detail"]["code"] == "ATTEMPT_EXPIRED"


def test_exam_mock_combined_flow(client: TestClient, db_session: Session):
    """Journey 3 (API half): timed mock MCQ leg + judge coding leg + persisted score."""
    register(client, "dogfood-exam@merit.org")
    for topic, quota in (("aptitude", 2), ("core-cs", 2)):
        avail = db_session.scalar(
            select(func.count(Question.id)).where(
                Question.review_status == "verified", Question.topic == topic
            )
        )
        assert avail >= quota

    gen = client.post(
        "/api/v1/quizzes/generate",
        json={
            "topics": ["aptitude", "core-cs"],
            "count": 4,
            "is_mock": True,
            "duration_sec": 600,
            "topic_plan": [["aptitude", 2], ["core-cs", 2]],
        },
    )
    assert gen.status_code == 200, gen.text
    data = gen.json()
    assert data["total"] == 4
    assert data["expires_at"] is not None

    questions = data["questions"]
    rows = db_session.scalars(
        select(Question).where(Question.id.in_([q["id"] for q in questions]))
    ).all()
    correct = {q.id: q.correct_index for q in rows}
    selected = {q["id"]: correct[q["id"]] for q in questions[:2]}
    sub = client.post(
        f"/api/v1/quizzes/attempts/{data['attempt_id']}",
        json={"duration_sec": 120, "selected": selected},
    )
    assert sub.status_code == 200, sub.text
    assert sub.json()["correct"] == 2
    assert sub.json()["score_pct"] == 50

    coding = client.post(
        "/api/v1/judge/submit",
        json={"problem_slug": "two-sum", "language": "javascript", "code": CORRECT_JS},
    )
    assert coding.status_code == 200
    assert coding.json()["verdict"] == "AC"

    summary = client.get("/api/v1/progress/summary").json()
    assert summary["solved_count"] >= 1
    assert summary["current_streak"] >= 1


def test_full_auth_journey_register_solve_progress_streak_logout_reuse(
    client: TestClient, db_session: Session
):
    """Journey 1: register → login → two-sum submit → Done → streak → logout → reuse."""
    from app.models.user import User

    reg = register(client, "dogfood-journey1@merit.org")
    original_refresh = reg.cookies.get("merit_refresh")
    assert original_refresh is not None

    login = client.post(
        "/api/v1/auth/login",
        json={"email": "dogfood-journey1@merit.org", "password": "StrongPassword123!"},
    )
    assert login.status_code == 200
    login_refresh = login.cookies.get("merit_refresh")
    assert login_refresh is not None

    coding = client.post(
        "/api/v1/judge/submit",
        json={"problem_slug": "two-sum", "language": "javascript", "code": CORRECT_JS},
    )
    assert coding.status_code == 200, coding.text
    assert coding.json()["verdict"] == "AC"

    prog = client.get("/api/v1/progress/problems/two-sum").json()
    assert prog["status"] == "Done"

    summary = client.get("/api/v1/progress/summary").json()
    assert summary["solved_count"] >= 1
    assert summary["current_streak"] >= 1
    user = db_session.scalar(
        select(User).where(User.email == "dogfood-journey1@merit.org")
    )
    assert user is not None

    logout = client.post("/api/v1/auth/logout")
    assert logout.status_code == 200

    reuse = client.post("/api/v1/auth/refresh", cookies={"merit_refresh": login_refresh})
    assert reuse.status_code == 401
    assert reuse.json()["detail"]["code"] == "TOKEN_REUSE_DETECTED"


def test_quiz_lifecycle_retry_wrong_and_revision_due(client: TestClient, db_session: Session):
    """Journey 2: generate → answer → submit → score persisted → retry → revision-due."""
    register(client, "dogfood-quizlife@merit.org")
    gen = client.post("/api/v1/quizzes/generate", json={"topics": ["trees"], "count": 4})
    assert gen.status_code == 200, gen.text
    attempt_id = gen.json()["attempt_id"]
    questions = gen.json()["questions"]
    assert len(questions) == 4

    from app.models.content import Question as QuestionModel

    rows = client.get(f"/api/v1/quizzes/attempts/{attempt_id}")
    assert rows.status_code == 200
    assert rows.json()["total"] == 4  # shell pre-stamped with question count
    assert rows.json()["results"] == []  # unsubmitted attempt carries no answers yet

    q_rows = db_session.scalars(
        select(QuestionModel).where(QuestionModel.id.in_([q["id"] for q in questions]))
    ).all()
    correct = {q.id: q.correct_index for q in q_rows}
    selected = {q["id"]: correct[q["id"]] for q in questions[:2]}
    selected.update({q["id"]: (correct[q["id"]] + 1) % 4 for q in questions[2:]})

    sub = client.post(
        f"/api/v1/quizzes/attempts/{attempt_id}",
        json={"duration_sec": 60, "selected": selected},
    )
    assert sub.status_code == 200, sub.text
    assert sub.json()["correct"] == 2
    assert sub.json()["score_pct"] == 50

    detail = client.get(f"/api/v1/quizzes/attempts/{attempt_id}").json()
    assert detail["correct"] == 2
    assert len(detail["results"]) == 4

    retry = client.post(f"/api/v1/quizzes/attempts/{attempt_id}/retry-wrong")
    assert retry.status_code == 200, retry.text
    assert retry.json()["total"] == 2
    retry_qids = {q["id"] for q in retry.json()["questions"]}
    assert retry_qids == {q["id"] for q in questions[2:]}

    summary = client.get("/api/v1/progress/summary").json()
    assert len(summary["revision_due"]) >= 1
    assert any(item["type"] == "question" for item in summary["revision_due"])


def test_quiz_generate_unknown_topic_404(client: TestClient):
    register(client, "dogfood-unknown@merit.org")
    res = client.post(
        "/api/v1/quizzes/generate",
        json={"topics": ["no-such-topic-xyz"], "count": 3},
    )
    assert res.status_code == 404
    assert res.json()["detail"]["code"] == "NO_QUESTIONS_FOR_TOPICS"


def _mock_claims(monkeypatch, claims=None, error=None):
    if error is not None:

        def _raise(token: str):
            raise error

        monkeypatch.setattr(auth_router, "verify_clerk_session_token", _raise)
    else:

        def _ok(token: str):
            return claims

        monkeypatch.setattr(auth_router, "verify_clerk_session_token", _ok)


def test_clerk_link_flow_matrix(client: TestClient, monkeypatch, db_session: Session):
    """Journey 5: mocked-JWKS Clerk link — create, email-link, unverified, bad token."""
    from fastapi import HTTPException

    from app.models.user import User

    monkeypatch.setattr(
        auth_router.settings,
        "clerk_jwks_url",
        "https://test-oauth.clerk.accounts.dev/.well-known/jwks.json",
        raising=False,
    )
    payload = {"clerk_token": "mocked.clerk.session.token"}

    _mock_claims(
        monkeypatch,
        claims={
            "clerk_id": "user_dogfood_new",
            "email": "dogfood-clerk-new@example.com",
            "display_name": "Dogfood New",
            "email_verified": True,
        },
    )
    created = client.post("/api/v1/auth/oauth/clerk", json=payload)
    assert created.status_code == 201
    assert created.json()["email"] == "dogfood-clerk-new@example.com"

    register(client, "dogfood-clerk-link@example.com")
    _mock_claims(
        monkeypatch,
        claims={
            "clerk_id": "user_dogfood_link",
            "email": "dogfood-clerk-link@example.com",
            "display_name": "Dogfood Link",
            "email_verified": True,
        },
    )
    linked = client.post("/api/v1/auth/oauth/clerk", json=payload)
    assert linked.status_code == 200
    user = db_session.scalar(
        select(User).where(User.email == "dogfood-clerk-link@example.com")
    )
    assert user.clerk_id == "user_dogfood_link"

    _mock_claims(
        monkeypatch,
        error=HTTPException(
            status_code=401,
            detail={
                "code": "OAUTH_EMAIL_UNVERIFIED",
                "message": "Clerk token email is not verified.",
            },
        ),
    )
    before = len(db_session.scalars(select(User)).all())
    unverified = client.post("/api/v1/auth/oauth/clerk", json=payload)
    assert unverified.status_code == 401
    assert unverified.json()["detail"]["code"] == "OAUTH_EMAIL_UNVERIFIED"
    assert len(db_session.scalars(select(User)).all()) == before

    _mock_claims(
        monkeypatch,
        error=HTTPException(
            status_code=401,
            detail={
                "code": "OAUTH_INVALID_TOKEN",
                "message": "Could not verify Clerk session token.",
            },
        ),
    )
    bad = client.post("/api/v1/auth/oauth/clerk", json=payload)
    assert bad.status_code == 401
    assert bad.json()["detail"]["code"] == "OAUTH_INVALID_TOKEN"


def _install_tutor_fake(monkeypatch, *, get=None, post=None):
    class _FakeResponse:
        def __init__(self, status_code=200, payload=None):
            self.status_code = status_code
            self._payload = payload if payload is not None else {}

        def json(self):
            return self._payload

    class FakeClient:
        def __init__(self, *args, **kwargs):
            pass

        async def __aenter__(self):
            return self

        async def __aexit__(self, *args):
            return False

        async def get(self, url, headers=None):
            assert get is not None
            return get(url, headers)

        async def post(self, url, headers=None, json=None):
            assert post is not None
            return post(url, headers, json)

    monkeypatch.setattr(tutor_module.httpx, "AsyncClient", FakeClient)
    return _FakeResponse


def test_tutor_journey_models_502_hint_policy_ratelimit(client: TestClient, monkeypatch):
    """Journey 4: bad-key models → 502; hint policy at 0 fails; 30/min rate limit."""
    import httpx

    register(client, "dogfood-tutor@merit.org")
    base = {
        "base_url": "https://provider.example.com/v1",
        "api_key": "sk-test-bad-key",
    }
    fake_resp = _install_tutor_fake(
        monkeypatch, get=lambda url, headers: fake_resp(401, {"error": "bad key"})
    )
    bad_key = client.post("/api/v1/tutor/models", json=base)
    assert bad_key.status_code == 502
    assert bad_key.json()["detail"]["code"] == "TUTOR_UPSTREAM"

    captured: list = []
    reply = fake_resp(200, {"choices": [{"message": {"content": "hint"}}]})
    _install_tutor_fake(
        monkeypatch, post=lambda url, headers, body: captured.append(body) or reply
    )
    ok = client.post(
        "/api/v1/tutor/chat",
        json={**base, "model": "gpt-4o-mini", "problem_slug": "two-sum", "question": "nudge?"},
    )
    assert ok.status_code == 200
    assert "never a complete solution or code block" in captured[0]["messages"][0]["content"]

    class ExplodingClient:
        def __init__(self, *args, **kwargs):
            pass

        async def __aenter__(self):
            return self

        async def __aexit__(self, *args):
            return False

        async def get(self, url, headers=None):
            raise httpx.ConnectError("refused")

    monkeypatch.setattr(tutor_module.httpx, "AsyncClient", ExplodingClient)
    tutor_module._rate_buckets.clear()
    for _ in range(30):
        res = client.post("/api/v1/tutor/models", json=base)
        assert res.status_code == 502  # upstream failure still counts toward the bucket
    limited = client.post("/api/v1/tutor/models", json=base)
    assert limited.status_code == 429
    assert limited.json()["detail"]["code"] == "TUTOR_RATE_LIMIT"
