"""Tests for Dynamic Quiz Engine (sampling, grading, retry-wrong, and user isolation)."""

import json
import pytest
from fastapi.testclient import TestClient
from sqlalchemy import select

from app.db import SessionLocal
from app.main import app
from app.models.content import Question
from app.seed import seed_all


@pytest.fixture(scope="module", autouse=True)
def seed_content():
    with SessionLocal() as db:
        seed_all(db)


def register_and_login(client: TestClient, email: str, name: str) -> None:
    client.post(
        "/api/v1/auth/register",
        json={"email": email, "display_name": name, "password": "Password123!"},
    )
    client.post(
        "/api/v1/auth/login",
        json={"email": email, "password": "Password123!"},
    )


def test_generate_quiz_no_answer_leak():
    client = TestClient(app)
    register_and_login(client, "quiz_user_1@algovista.org", "Quiz User 1")

    resp = client.post(
        "/api/v1/quizzes/generate",
        json={"topics": ["arrays-hashing", "trees"], "count": 5},
    )
    assert resp.status_code == 200
    data = resp.json()
    assert "attempt_id" in data
    assert len(data["questions"]) == 5

    # Invariant: correct_index and explanation MUST NEVER be exposed in generate payload
    for q in data["questions"]:
        assert "correct_index" not in q
        assert "explanation" not in q
        assert len(q["options"]) == 4


def test_submit_quiz_and_grading():
    client = TestClient(app)
    register_and_login(client, "quiz_user_2@algovista.org", "Quiz User 2")

    gen_resp = client.post(
        "/api/v1/quizzes/generate",
        json={"topics": ["arrays-hashing"], "count": 3},
    )
    assert gen_resp.status_code == 200
    gen_data = gen_resp.json()
    attempt_id = gen_data["attempt_id"]
    questions = gen_data["questions"]

    # Look up correct answers in database to test grading oracle
    with SessionLocal() as db:
        q_rows = db.scalars(
            select(Question).where(Question.id.in_([q["id"] for q in questions]))
        ).all()
        correct_answers = {q.id: q.correct_index for q in q_rows}

    # Answer first question correctly, others wrong
    selected = {}
    for i, q in enumerate(questions):
        if i == 0:
            selected[q["id"]] = correct_answers[q["id"]]
        else:
            selected[q["id"]] = (correct_answers[q["id"]] + 1) % 4

    sub_resp = client.post(
        f"/api/v1/quizzes/attempts/{attempt_id}",
        json={"duration_sec": 45, "selected": selected},
    )
    assert sub_resp.status_code == 200
    sub_data = sub_resp.json()
    assert sub_data["attempt_id"] == attempt_id
    assert sub_data["total"] == 3
    assert sub_data["correct"] == 1
    assert sub_data["score_pct"] == 33
    assert sub_data["duration_sec"] == 45

    # Verification: explanations and correctness are returned in submit response
    for res in sub_data["results"]:
        assert "correct_index" in res
        assert "explanation" in res
        assert len(res["explanation"]) > 0
        if res["question_id"] == questions[0]["id"]:
            assert res["is_correct"] is True
        else:
            assert res["is_correct"] is False


def test_retry_wrong_questions():
    client = TestClient(app)
    register_and_login(client, "quiz_user_3@algovista.org", "Quiz User 3")

    gen_resp = client.post(
        "/api/v1/quizzes/generate",
        json={"topics": ["trees"], "count": 4},
    )
    gen_data = gen_resp.json()
    attempt_id = gen_data["attempt_id"]
    questions = gen_data["questions"]

    # Look up correct answers
    with SessionLocal() as db:
        q_rows = db.scalars(
            select(Question).where(Question.id.in_([q["id"] for q in questions]))
        ).all()
        correct_answers = {q.id: q.correct_index for q in q_rows}

    # Answer 2 correctly and 2 incorrectly
    selected = {
        questions[0]["id"]: correct_answers[questions[0]["id"]],
        questions[1]["id"]: correct_answers[questions[1]["id"]],
        questions[2]["id"]: (correct_answers[questions[2]["id"]] + 1) % 4,
        questions[3]["id"]: (correct_answers[questions[3]["id"]] + 1) % 4,
    }

    client.post(
        f"/api/v1/quizzes/attempts/{attempt_id}",
        json={"duration_sec": 30, "selected": selected},
    )

    # Call retry-wrong
    retry_resp = client.post(f"/api/v1/quizzes/attempts/{attempt_id}/retry-wrong")
    assert retry_resp.status_code == 200
    retry_data = retry_resp.json()
    assert retry_data["attempt_id"] != attempt_id
    assert retry_data["total"] == 2
    retry_qids = {q["id"] for q in retry_data["questions"]}
    assert retry_qids == {questions[2]["id"], questions[3]["id"]}


def test_generate_unknown_topic_returns_404():
    client = TestClient(app)
    register_and_login(client, "quiz_user_4@algovista.org", "Quiz User 4")

    # No silent widening: unknown/empty topics must 404, never serve off-topic questions.
    resp = client.post(
        "/api/v1/quizzes/generate",
        json={"topics": ["no-such-topic-xyz"], "count": 3},
    )
    assert resp.status_code == 404
    assert resp.json()["detail"]["code"] == "NO_QUESTIONS_FOR_TOPICS"


def test_generate_topic_plan_section_sizes():
    client = TestClient(app)
    register_and_login(client, "quiz_user_plan@algovista.org", "Quiz User Plan")

    # Placement-mock shape: per-section quotas hold even across uneven pools.
    desired = [
        ("aptitude", 30),
        ("core-cs", 20),
        ("arrays-hashing", 15),
        ("dynamic-programming", 15),
    ]
    with SessionLocal() as db:
        actual_plan = []
        for topic, target_count in desired:
            avail = db.scalars(
                select(Question).where(
                    Question.review_status == "verified",
                    Question.topic == topic,
                )
            ).all()
            actual_plan.append([topic, min(target_count, len(avail))])

    total_expected = sum(cnt for _, cnt in actual_plan)

    resp = client.post(
        "/api/v1/quizzes/generate",
        json={
            "topics": [t for t, _ in actual_plan],
            "count": total_expected,
            "is_mock": True,
            "topic_plan": actual_plan,
        },
    )
    assert resp.status_code == 200
    data = resp.json()
    assert data["total"] == total_expected
    from collections import Counter

    got = Counter(q["topic"] for q in data["questions"])
    for topic, count in actual_plan:
        assert got[topic] == count


def test_quiz_attempt_user_isolation():
    client_a = TestClient(app)
    register_and_login(client_a, "isolation_quiz_a@algovista.org", "User A")

    gen_resp = client_a.post(
        "/api/v1/quizzes/generate",
        json={"topics": ["sorting"], "count": 3},
    )
    attempt_id_a = gen_resp.json()["attempt_id"]

    # User B cannot access User A's attempt
    client_b = TestClient(app)
    register_and_login(client_b, "isolation_quiz_b@algovista.org", "User B")

    get_resp = client_b.get(f"/api/v1/quizzes/attempts/{attempt_id_a}")
    assert get_resp.status_code == 404
    assert get_resp.json()["detail"]["code"] == "ATTEMPT_NOT_FOUND"

    submit_resp = client_b.post(
        f"/api/v1/quizzes/attempts/{attempt_id_a}",
        json={"duration_sec": 10, "selected": {}},
    )
    assert submit_resp.status_code == 404
    assert submit_resp.json()["detail"]["code"] == "ATTEMPT_NOT_FOUND"

    retry_resp = client_b.post(f"/api/v1/quizzes/attempts/{attempt_id_a}/retry-wrong")
    assert retry_resp.status_code == 404
    assert retry_resp.json()["detail"]["code"] == "ATTEMPT_NOT_FOUND"
