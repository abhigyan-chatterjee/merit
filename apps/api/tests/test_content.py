"""Tests for content endpoints (problems, questions, paths, visualizers)."""

import pytest
from fastapi.testclient import TestClient

from app.main import app
from app.seed import seed_all
from app.db import SessionLocal


@pytest.fixture(scope="module", autouse=True)
def seed_content():
    with SessionLocal() as db:
        seed_all(db)


def test_list_visualizers():
    client = TestClient(app)
    resp = client.get("/api/v1/visualizers")
    assert resp.status_code == 200
    visualizers = resp.json()
    assert len(visualizers) == 12
    ids = {v["id"] for v in visualizers}
    assert "array" in ids
    assert "sorting" in ids
    assert "bst" in ids
    assert "graph" in ids


def test_list_problems_and_filter():
    client = TestClient(app)
    resp = client.get("/api/v1/problems")
    assert resp.status_code == 200
    problems = resp.json()
    assert len(problems) >= 30
    assert any(p["slug"] == "two-sum" for p in problems)

    # Filter by topic
    resp_arr = client.get("/api/v1/problems?topic=arrays-hashing")
    assert resp_arr.status_code == 200
    arr_problems = resp_arr.json()
    assert all(p["topic"] == "arrays-hashing" for p in arr_problems)

    # Filter by difficulty
    resp_easy = client.get("/api/v1/problems?difficulty=Easy")
    assert resp_easy.status_code == 200
    easy_problems = resp_easy.json()
    assert all(p["difficulty"] == "Easy" for p in easy_problems)


def test_get_problem_detail():
    client = TestClient(app)
    resp = client.get("/api/v1/problems/two-sum")
    assert resp.status_code == 200
    problem = resp.json()
    assert problem["slug"] == "two-sum"
    assert problem["function_name"] == "solve"
    assert len(problem["test_cases"]) >= 3
    assert len(problem["solutions"]) >= 1
    assert any(tc["is_sample"] for tc in problem["test_cases"])


def test_problem_sequence_links():
    client = TestClient(app)
    resp = client.get("/api/v1/problems/two-sum")
    assert resp.status_code == 200
    problem = resp.json()
    assert problem["slug"] == "two-sum"
    assert problem["topic"] == "arrays-hashing"
    # 2Sum heads the arrays-hashing chain; next must be a same-topic slug
    assert problem.get("next_slug"), "two-sum must link to the next question"
    nxt = client.get(f"/api/v1/problems/{problem['next_slug']}")
    assert nxt.status_code == 200
    assert nxt.json()["topic"] == "arrays-hashing"
    assert nxt.json().get("prev_slug") == "two-sum"


def test_get_problem_not_found():
    client = TestClient(app)
    resp = client.get("/api/v1/problems/non-existent-problem-xyz")
    assert resp.status_code == 404
    assert resp.json()["detail"]["code"] == "PROBLEM_NOT_FOUND"


def test_list_questions_no_answer_leak():
    client = TestClient(app)
    resp = client.get("/api/v1/questions?limit=50")
    assert resp.status_code == 200
    questions = resp.json()
    assert len(questions) > 0

    # Ensure answer is never leaked on question list
    for q in questions:
        assert "correct_index" not in q
        assert "explanation" not in q
        assert len(q["options"]) == 4


def test_get_question_by_id():
    client = TestClient(app)
    list_resp = client.get("/api/v1/questions?limit=1")
    assert list_resp.status_code == 200
    q_id = list_resp.json()[0]["id"]

    detail_resp = client.get(f"/api/v1/questions/{q_id}")
    assert detail_resp.status_code == 200
    q_data = detail_resp.json()
    assert q_data["id"] == q_id
    assert len(q_data["options"]) == 4


def test_list_and_get_learning_paths():
    client = TestClient(app)
    resp = client.get("/api/v1/paths")
    assert resp.status_code == 200
    paths = resp.json()
    assert len(paths) >= 3
    slugs = {p["slug"] for p in paths}
    assert slugs == {"foundation", "targeted", "mastery"}

    # Detail path
    p_resp = client.get("/api/v1/paths/foundation")
    assert p_resp.status_code == 200
    foundation = p_resp.json()
    assert foundation["slug"] == "foundation"
    assert len(foundation["steps"]) >= 5
    # Steps are sorted by ordinal
    ordinals = [s["ordinal"] for s in foundation["steps"]]
    assert ordinals == sorted(ordinals)
    # Foundation steps carry summaries (not visualization alone)
    assert any(s.get("summary") for s in foundation["steps"])
