"""Tests for content endpoints (problems, questions, paths, visualizers)."""

import json

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import select

from app.db import SessionLocal
from app.main import app
from app.models.content import Problem
from app.seed import resolve_content_dir, seed_all


@pytest.fixture(scope="module", autouse=True)
def seed_content():
    with SessionLocal() as db:
        seed_all(db)


def test_list_visualizers():
    client = TestClient(app)
    resp = client.get("/api/v1/visualizers")
    assert resp.status_code == 200
    visualizers = resp.json()
    assert len(visualizers) == 17
    ids = {v["id"] for v in visualizers}
    assert "array" in ids
    assert "sorting" in ids
    assert "bst" in ids
    assert "graph" in ids
    assert "dp-table" in ids
    assert "sliding-window" in ids
    assert "shortest-path" in ids
    assert "union-find" in ids
    assert "trie" in ids


def test_list_problems_and_filter():
    client = TestClient(app)
    resp = client.get("/api/v1/problems?limit=500")
    assert resp.status_code == 200
    problems = resp.json()

    problems_dir = resolve_content_dir("problems")
    verified_files_count = 0
    for file_path in problems_dir.glob("*.json"):
        with open(file_path, encoding="utf-8") as f:
            data = json.load(f)
        status = data.get("reviewStatus") or data.get("review_status") or "verified"
        if status != "draft":
            verified_files_count += 1

    assert len(problems) == verified_files_count
    slugs = {p["slug"] for p in problems}
    assert "two-sum" in slugs
    assert not any(s.startswith("scrap-") for s in slugs)

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
    assert isinstance(problem["companies"], list)
    assert problem["function_name"] == "solve"
    assert len(problem["test_cases"]) >= 1
    assert all(tc["is_sample"] for tc in problem["test_cases"])
    assert len(problem["solutions"]) >= 1


def test_problem_companies_filter_and_catalog():
    client = TestClient(app)
    slugs = ("two-sum", "asteroid-collision", "3sum")

    initial_resp = client.get("/api/v1/problems/two-sum")
    assert initial_resp.status_code == 200
    assert len(initial_resp.json()["companies"]) >= 1

    originals: dict[str, str | None] = {}
    with SessionLocal() as db:
        for slug in slugs:
            problem = db.scalar(select(Problem).where(Problem.slug == slug))
            assert problem is not None
            originals[slug] = problem.companies_json
            problem.companies_json = json.dumps(["MeritTestCo", "MeritAltCo"])
        db.commit()

    try:
        list_resp = client.get("/api/v1/problems?limit=500")
        assert list_resp.status_code == 200
        listed = {problem["slug"]: problem for problem in list_resp.json()}
        assert isinstance(listed["two-sum"]["companies"], list)
        assert listed["two-sum"]["companies"] == ["MeritTestCo", "MeritAltCo"]

        detail_resp = client.get("/api/v1/problems/two-sum")
        assert detail_resp.status_code == 200
        assert detail_resp.json()["companies"] == ["MeritTestCo", "MeritAltCo"]

        filtered = client.get("/api/v1/problems?company=merittestco&limit=500")
        assert filtered.status_code == 200
        assert {problem["slug"] for problem in filtered.json()} == set(slugs)

        paged = client.get("/api/v1/problems?company=MERITTESTCO&limit=1&offset=1")
        assert paged.status_code == 200
        page = paged.json()
        assert len(page) == 1
        assert page[0]["slug"] in set(slugs)

        missing = client.get("/api/v1/problems?company=No-Such-Company")
        assert missing.status_code == 200
        assert missing.json() == []

        catalog = client.get("/api/v1/companies")
        assert catalog.status_code == 200
        companies = catalog.json()
        test_co = next(item for item in companies if item["name"] == "MeritTestCo")
        alt_co = next(item for item in companies if item["name"] == "MeritAltCo")
        assert test_co["count"] == 3
        assert alt_co["count"] == 3
        assert companies == sorted(companies, key=lambda item: (-item["count"], item["name"]))
    finally:
        with SessionLocal() as db:
            for slug, prev in originals.items():
                problem = db.scalar(select(Problem).where(Problem.slug == slug))
                if problem is not None:
                    problem.companies_json = prev
            db.commit()


def test_problem_detail_hides_hidden_test_cases():
    """GET /problems/{slug} must never expose non-sample inputs or expected outputs."""
    client = TestClient(app)
    with SessionLocal() as db:
        problem = db.scalar(select(Problem).where(Problem.slug == "two-sum"))
        assert problem is not None
        cases = sorted(problem.test_cases, key=lambda tc: tc.ordinal)
        sample = [tc for tc in cases if tc.is_sample == 1]
        hidden = [tc for tc in cases if tc.is_sample != 1]
    assert len(sample) >= 1, "two-sum must ship sample cases for this regression test"
    assert len(hidden) >= 1, "two-sum must ship hidden cases for this regression test"

    resp = client.get("/api/v1/problems/two-sum")
    assert resp.status_code == 200
    returned = resp.json()["test_cases"]

    # Only sample rows are returned — same rows (by id), same order.
    assert [tc["id"] for tc in returned] == [tc.id for tc in sample]
    assert all(tc["is_sample"] for tc in returned)


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


def test_problem_includes_editorial_and_links():
    client = TestClient(app)
    resp = client.get("/api/v1/problems/asteroid-collision")
    assert resp.status_code == 200
    problem = resp.json()
    assert problem["slug"] == "asteroid-collision"
    editorial = problem.get("editorial")
    assert editorial is not None
    assert set(editorial.keys()) == {"approach", "why_optimal", "pitfalls"}
    assert all(editorial[k] for k in ("approach", "why_optimal", "pitfalls"))
    reading_links = problem.get("reading_links")
    assert isinstance(reading_links, list) and len(reading_links) >= 1


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
    assert slugs == {
        "foundation",
        "targeted",
        "mastery",
        "tcs-nqt",
        "infosys-sp-dse",
        "product-50",
    }

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


def test_mock_path_step_requires_submitted_mock_and_is_consistent(client: TestClient):
    registered = client.post(
        "/api/v1/auth/register",
        json={
            "email": "mock-path@merit.org",
            "display_name": "Mock Path",
            "password": "StrongPassword123!",
        },
    )
    assert registered.status_code == 201

    before_detail = client.get("/api/v1/paths/targeted").json()
    mock_step = next(step for step in before_detail["steps"] if step["step_type"] == "mock")
    assert mock_step["completed"] is False
    before_list = client.get("/api/v1/paths").json()
    targeted = next(path for path in before_list if path["slug"] == "targeted")
    assert targeted["completed_steps"] == before_detail["completed_steps"]

    generated = client.post(
        "/api/v1/quizzes/generate",
        json={"topics": ["arrays-hashing"], "count": 1, "is_mock": True, "duration_sec": 600},
    )
    assert generated.status_code == 200
    attempt_id = generated.json()["attempt_id"]
    submitted = client.post(
        f"/api/v1/quizzes/attempts/{attempt_id}",
        json={"duration_sec": 1, "selected": {}},
    )
    assert submitted.status_code == 200

    after_detail = client.get("/api/v1/paths/targeted").json()
    assert next(step for step in after_detail["steps"] if step["step_type"] == "mock")["completed"]
    after_list = client.get("/api/v1/paths").json()
    targeted = next(path for path in after_list if path["slug"] == "targeted")
    assert targeted["completed_steps"] == after_detail["completed_steps"]
