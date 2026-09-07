import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.seed import seed_problems


def register_user(client: TestClient, email: str = "judge_student@algovista.org") -> str:
    res = client.post(
        "/api/v1/auth/register",
        json={
            "email": email,
            "display_name": "Judge Student",
            "password": "StrongPassword123!",
        },
    )
    assert res.status_code == 201
    return str(res.json()["id"])


@pytest.fixture(autouse=True)
def seed_test_problems(db_session: Session):
    seed_problems(db_session)


def test_judge_run_samples_ac(client: TestClient):
    register_user(client)

    correct_js = """
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

    res = client.post(
        "/api/v1/judge/run",
        json={
            "problem_slug": "two-sum",
            "language": "javascript",
            "code": correct_js,
        },
    )
    assert res.status_code == 200
    data = res.json()
    assert data["verdict"] == "AC"
    assert len(data["test_results"]) >= 1
    assert all(tc["passed"] for tc in data["test_results"])


def test_judge_run_samples_wa(client: TestClient):
    register_user(client)

    wrong_js = """
function solve(nums, target) {
  return [0, 0];
}
"""

    res = client.post(
        "/api/v1/judge/run",
        json={
            "problem_slug": "two-sum",
            "language": "javascript",
            "code": wrong_js,
        },
    )
    assert res.status_code == 200
    data = res.json()
    assert data["verdict"] == "WA"
    assert any(not tc["passed"] for tc in data["test_results"])


def test_judge_submit_ac_flips_progress(client: TestClient):
    register_user(client, "submit_student@algovista.org")

    correct_js = """
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

    res = client.post(
        "/api/v1/judge/submit",
        json={
            "problem_slug": "two-sum",
            "language": "javascript",
            "code": correct_js,
        },
    )
    assert res.status_code == 200
    sub = res.json()
    assert sub["verdict"] == "AC"
    assert sub["problem_slug"] == "two-sum"

    # Verify problem_progress for two-sum is now Done
    prog = client.get("/api/v1/progress/problems/two-sum").json()
    assert prog["status"] == "Done"

    # Verify submission history list
    subs = client.get("/api/v1/judge/submissions/two-sum").json()
    assert len(subs) == 1
    assert subs[0]["verdict"] == "AC"


def test_judge_python_execution(client: TestClient):
    register_user(client, "python_student@algovista.org")

    py_code = """
def solve(nums, target):
    seen = {}
    for i, n in enumerate(nums):
        diff = target - n
        if diff in seen:
            return [seen[diff], i]
        seen[n] = i
    return []
"""

    res = client.post(
        "/api/v1/judge/run",
        json={
            "problem_slug": "two-sum",
            "language": "python",
            "code": py_code,
        },
    )
    assert res.status_code == 200
    data = res.json()
    assert data["verdict"] == "AC"
    assert all(tc["passed"] for tc in data["test_results"])
