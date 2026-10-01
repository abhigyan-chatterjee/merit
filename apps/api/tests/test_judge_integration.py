"""End-to-end test of the judge over real HTTP.

Why this file exists
--------------------
The judge shipped completely broken while 127 unit tests passed. Both existing
tests in `test_judge_backend.py` stub the boundary they are supposedly testing:

- one monkeypatches `_mint_identity_token`, so the HTTP client never runs
- one points at a dead port, so the request is never serialized

Nothing anywhere exercised `judge_backend` talking to a real judge service over
a real socket. Contract drift, a renamed field, a serialization bug, or the
judge app simply not starting would all have been invisible.

This starts the *actual* judge application — same `main.py`, same file layout
the container uses, real uvicorn, real port — and drives `judge_backend.execute`
against it.

What this does NOT cover: Google's identity verification. That needs real
credentials and is covered by `test_judge_backend.py`; here the token is stubbed
because Google is not what we are testing.
"""

from __future__ import annotations

import shutil
import socket
import subprocess
import sys
import time
from pathlib import Path

import httpx
import pytest

from app.services import judge_backend

REPO_ROOT = Path(__file__).resolve().parents[3]
API_ROOT = REPO_ROOT / "apps" / "api"
JUDGE_ROOT = REPO_ROOT / "apps" / "judge"
SANDBOX_SOURCE = API_ROOT / "app" / "services" / "judge.py"


def _free_port() -> int:
    with socket.socket() as s:
        s.bind(("127.0.0.1", 0))
        return s.getsockname()[1]


@pytest.fixture(scope="module")
def judge_service(tmp_path_factory):
    """Runs the real judge app the way the container does.

    The container copies the sandbox to `sandbox.py` beside `main.py`, and the
    app imports it as a top-level module. Reproducing that layout exactly means
    this test exercises the shipping code without changing it for testability.
    """
    workdir = tmp_path_factory.mktemp("judge_service")
    shutil.copy(SANDBOX_SOURCE, workdir / "sandbox.py")
    shutil.copy(JUDGE_ROOT / "main.py", workdir / "main.py")

    port = _free_port()
    proc = subprocess.Popen(
        [sys.executable, "-m", "uvicorn", "main:app", "--host", "127.0.0.1", "--port", str(port)],
        cwd=workdir,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
    )

    base_url = f"http://127.0.0.1:{port}"
    deadline = time.time() + 30
    while time.time() < deadline:
        if proc.poll() is not None:
            raise RuntimeError(f"judge service died on startup:\n{proc.stdout.read()}")
        try:
            if httpx.get(f"{base_url}/health", timeout=1).status_code == 200:
                break
        except httpx.HTTPError:
            time.sleep(0.2)
    else:
        proc.kill()
        raise RuntimeError("judge service did not become healthy in 30s")

    yield base_url

    proc.terminate()
    try:
        proc.wait(timeout=10)
    except subprocess.TimeoutExpired:
        proc.kill()


@pytest.fixture
def wired_to_judge(judge_service, monkeypatch):
    """Points the backend at the live service, stubbing only Google's auth."""
    from app.config import settings

    monkeypatch.setattr(settings, "judge_url", judge_service)
    monkeypatch.setattr(settings, "judge_timeout_sec", 30.0)

    async def _stub_token() -> str:
        # Google identity is not under test here; its verification is covered
        # in test_judge_backend.py.
        return "test-identity-token"

    monkeypatch.setattr(judge_backend, "_mint_identity_token", _stub_token)
    return judge_service


CASES = [
    {
        "label": "basic",
        "input": [[2, 7, 11, 15], 9],
        "expected": [0, 1],
    }
]


async def _run(language: str, code: str, function_name: str):
    return await judge_backend.execute(
        language=language,
        code=code,
        function_name=function_name,
        test_cases=CASES,
        time_limit_ms=2000,
    )


@pytest.mark.asyncio
async def test_accepted_solution_round_trips(wired_to_judge):
    """The happy path, over a real socket, end to end.

    Before this test, this path had never once executed successfully anywhere —
    not locally, not in CI, not in production.
    """
    result = await _run("python", "def twoSum(nums, t):\n    return [0, 1]", "twoSum")

    assert result.verdict == "AC"
    assert result.compile_output == ""
    assert len(result.test_results) == 1
    assert result.test_results[0]["passed"] is True
    assert result.test_results[0]["actual"] == [0, 1]


@pytest.mark.asyncio
async def test_wrong_answer_round_trips(wired_to_judge):
    result = await _run("python", "def twoSum(nums, t):\n    return [9, 9]", "twoSum")

    assert result.verdict == "WA"
    assert result.test_results[0]["passed"] is False
    assert result.test_results[0]["actual"] == [9, 9]


@pytest.mark.asyncio
async def test_javascript_round_trips(wired_to_judge):
    """JavaScript is a second runtime in the same image; a broken Node install
    would otherwise be invisible to the Python-only tests."""
    result = await _run(
        "javascript", "function twoSum(nums, t) { return [0, 1]; }", "twoSum"
    )

    assert result.verdict == "AC"


@pytest.mark.asyncio
async def test_runtime_error_is_reported_not_swallowed(wired_to_judge):
    result = await _run(
        "python", "def twoSum(nums, t):\n    raise ValueError('boom')", "twoSum"
    )

    assert result.verdict in {"WA", "RE"}
    assert result.test_results[0]["error"] == "boom"


@pytest.mark.asyncio
async def test_response_shape_matches_the_client_contract(wired_to_judge):
    """Guards the wire contract itself.

    `judge_backend` reads these keys by name. If the judge ever renames one, the
    unit tests still pass because they never deserialize a real response — the
    verdict would just silently come back as the default "RE".
    """
    result = await _run("python", "def twoSum(nums, t):\n    return [0, 1]", "twoSum")

    raw = httpx.post(
        f"{wired_to_judge}/run",
        json={
            "language": "python",
            "code": "def twoSum(nums, t):\n    return [0, 1]",
            "function_name": "twoSum",
            "test_cases": CASES,
            "time_limit_ms": 2000,
        },
        headers={"Authorization": "Bearer test-identity-token"},
        timeout=30,
    )
    assert raw.status_code == 200

    body = raw.json()
    for key in ("verdict", "runtime_ms", "test_results", "compile_output"):
        assert key in body, f"judge response is missing {key!r}; client reads it by name"
    assert body["verdict"] == result.verdict


@pytest.mark.asyncio
async def test_unsupported_language_is_rejected(wired_to_judge):
    """Java is not supported yet. This asserts the boundary explicitly so that
    an accidental half-wired language cannot start returning a false verdict."""
    response = httpx.post(
        f"{wired_to_judge}/run",
        json={
            "language": "java",
            "code": "class Main {}",
            "function_name": "solve",
            "test_cases": CASES,
            "time_limit_ms": 2000,
        },
        headers={"Authorization": "Bearer test-identity-token"},
        timeout=30,
    )
    assert response.status_code == 400
