"""Tests for the dedicated AI Interview Portal endpoints (Phase 1 + Phase 2 CV + DB sessions)."""

import json

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

import app.routers.tutor as tutor_module
from app.models.content import Problem
from app.seed import seed_problems

API_KEY = "sk-interview-sentinel-secret-999"
BASE_URL = "https://provider.example.com/v1"


@pytest.fixture(autouse=True)
def seed_test_problems(db_session: Session):
    seed_problems(db_session)


@pytest.fixture(autouse=True)
def public_provider_dns(monkeypatch):
    def resolve(host, port, **kwargs):
        socket_type = kwargs["type"]
        address = {
            "localhost": "127.0.0.1",
            "169.254.169.254": "169.254.169.254",
            "provider.example.com": "93.184.216.34",
        }.get(host, host)
        return [(tutor_module.socket.AF_INET, socket_type, 6, "", (address, port))]

    monkeypatch.setattr(tutor_module.socket, "getaddrinfo", resolve)


def register_and_login(client: TestClient, email: str) -> None:
    res = client.post(
        "/api/v1/auth/register",
        json={
            "email": email,
            "display_name": "Candidate",
            "password": "StrongPassword123!",
        },
    )
    assert res.status_code == 201


class FakeResponse:
    def __init__(self, status_code: int = 200, payload: object = None):
        self.status_code = status_code
        self._payload = payload if payload is not None else {}

    def json(self):
        return self._payload


def install_fake_client(monkeypatch, *, post=None, capture=None):
    class FakeClient:
        def __init__(self, *args, **kwargs):
            if capture is not None:
                capture["client_kwargs"] = kwargs

        async def __aenter__(self):
            return self

        async def __aexit__(self, *args):
            return False

        async def post(self, url, headers=None, json=None):
            if capture is not None:
                capture.setdefault("posts", []).append(
                    {"url": url, "headers": headers, "json": json}
                )
            assert post is not None
            return post(url, headers, json)

    monkeypatch.setattr(tutor_module.httpx, "AsyncClient", FakeClient)


def _build_pdf_bytes(text: str | None) -> bytes:
    """Build a valid minimal single-page PDF 1.4 payload with optional text."""
    escaped = (text or "").replace("\\", "\\\\").replace("(", "\\(").replace(")", "\\)")
    stream = f"BT /F1 12 Tf 72 720 Td ({escaped}) Tj ET".encode("latin-1") if text else b""
    objects: list[bytes] = [
        b"1 0 obj\n<< /Type /Catalog /Pages 2 0 R >>\nendobj\n",
        b"2 0 obj\n<< /Type /Pages /Kids [3 0 R] /Count 1 >>\nendobj\n",
        (
            b"3 0 obj\n<< /Type /Page /Parent 2 0 R /MediaBox [0 0 612 792] "
            b"/Resources << /Font << /F1 4 0 R >> >> /Contents 5 0 R >>\nendobj\n"
        ),
        b"4 0 obj\n<< /Type /Font /Subtype /Type1 /BaseFont /Helvetica >>\nendobj\n",
        (
            f"5 0 obj\n<< /Length {len(stream)} >>\nstream\n".encode("latin-1")
            + stream
            + b"\nendstream\nendobj\n"
        ),
    ]
    chunks = [b"%PDF-1.4\n"]
    offsets = [0]
    for obj in objects:
        offsets.append(sum(len(c) for c in chunks))
        chunks.append(obj)
    xref_pos = sum(len(c) for c in chunks)
    xref = [f"xref\n0 {len(offsets)}\n0000000000 65535 f \n".encode("latin-1")]
    for off in offsets[1:]:
        xref.append(f"{off:010d} 00000 n \n".encode("latin-1"))
    trailer = (
        f"trailer\n<< /Size {len(offsets)} /Root 1 0 R >>\nstartxref\n{xref_pos}\n%%EOF\n"
    ).encode("latin-1")
    return b"".join(chunks + xref + [trailer])


@pytest.mark.parametrize(
    ("difficulty", "expected_duration", "expected_diffs", "expected_first_stage"),
    [
        ("easy", 1800, ["Easy"], "theory"),
        ("medium", 2700, ["Easy", "Medium"], "theory"),
        ("hard", 3600, ["Medium", "Hard"], "theory"),
    ],
)
def test_create_session_tiers_pick_verified_problems(
    client: TestClient,
    db_session: Session,
    difficulty: str,
    expected_duration: int,
    expected_diffs: list[str],
    expected_first_stage: str,
):
    register_and_login(client, f"tier_{difficulty}@merit.org")
    res = client.post(
        "/api/v1/interview/sessions",
        json={"difficulty": difficulty, "project_brief": "Built distributed cache"},
    )
    assert res.status_code == 201
    data = res.json()
    assert data["difficulty"] == difficulty
    assert data["duration_sec"] == expected_duration
    assert data["current_stage"] == expected_first_stage
    assert len(data["problems"]) == len(expected_diffs)
    for prob, want_diff in zip(data["problems"], expected_diffs, strict=True):
        assert prob["difficulty"] == want_diff
        row = db_session.query(Problem).filter(Problem.slug == prob["slug"]).first()
        assert row is not None
        assert row.review_status == "verified"


def test_session_user_isolation(client: TestClient):
    register_and_login(client, "user_a_iso@merit.org")
    create_res = client.post("/api/v1/interview/sessions", json={"difficulty": "easy"})
    assert create_res.status_code == 201
    session_id = create_res.json()["id"]

    # Switch active auth cookie to User B
    client.post("/api/v1/auth/logout")
    register_and_login(client, "user_b_iso@merit.org")

    assert client.get("/api/v1/interview/sessions").json() == []
    assert client.get(f"/api/v1/interview/sessions/{session_id}").status_code == 404
    assert (
        client.patch(
            f"/api/v1/interview/sessions/{session_id}",
            json={"elapsed_sec": 30},
        ).status_code
        == 404
    )
    assert client.delete(f"/api/v1/interview/sessions/{session_id}").status_code == 404
    assert (
        client.post(
            f"/api/v1/interview/sessions/{session_id}/turn",
            json={
                "base_url": BASE_URL,
                "api_key": API_KEY,
                "model": "gpt-4o-mini",
                "action": "start",
            },
        ).status_code
        == 404
    )


def test_session_lifecycle_turns_coding_resume_and_rubric(client: TestClient, monkeypatch):
    register_and_login(client, "lifecycle@merit.org")
    capture: dict = {}
    rubric_payload = {
        "dimensions": [
            {"name": "Deep CS Theory", "score": 4, "max_score": 5, "comment": "Strong OS & DBMS"},
            {"name": "DSA & Optimal Algorithms", "score": 5, "max_score": 5, "comment": "Optimal"},
            {"name": "Code Correctness & Edge Cases", "score": 4, "max_score": 5, "comment": "OK"},
            {"name": "Project Engineering Rigor", "score": 5, "max_score": 5, "comment": "Deep"},
            {"name": "System Design & Scale", "score": 4, "max_score": 5, "comment": "Sharded"},
            {"name": "Communication & Signal", "score": 4, "max_score": 5, "comment": "Clear"},
        ],
        "verdict": "Strong Hire",
        "strengths": ["Clear Big-O derivations", "Solid distributed design"],
        "improvements": ["Quantify replication lag bounds"],
    }

    def respond(url, headers, body):
        user_content = body["messages"][-1]["content"]
        if "Grade the candidate" in user_content:
            return FakeResponse(
                200,
                {
                    "choices": [
                        {
                            "message": {
                                "content": (
                                    f"```json\n{json.dumps(rubric_payload)}\n```\n"
                                    "Solid FAANG performance across coding and system design."
                                )
                            }
                        }
                    ]
                },
            )
        return FakeResponse(
            200,
            {"choices": [{"message": {"content": "Explain your database isolation choice."}}]},
        )

    install_fake_client(monkeypatch, post=respond, capture=capture)

    create_res = client.post(
        "/api/v1/interview/sessions",
        json={
            "difficulty": "hard",
            "resume_filename": "abhi_cv.pdf",
            "resume_text": "Built sharded telemetry pipeline handling 20k RPS",
            "project_brief": "Real-time rate limiter on Redis Cluster",
        },
    )
    assert create_res.status_code == 201
    sid = create_res.json()["id"]
    first_slug = create_res.json()["problem_slugs"][0]

    # 1. Start interview
    r1 = client.post(
        f"/api/v1/interview/sessions/{sid}/turn",
        json={
            "base_url": BASE_URL,
            "api_key": API_KEY,
            "model": "gemma-4-31b-it",
            "action": "start",
        },
    )
    assert r1.status_code == 200
    assert API_KEY not in r1.text
    sys_prompt_1 = capture["posts"][-1]["json"]["messages"][0]["content"]
    assert "FAANG" in sys_prompt_1
    assert "<candidate_resume>" in sys_prompt_1
    assert "20k RPS" in sys_prompt_1

    # 2. Advance to coding_1 and send user message with code + judge snapshot
    r2 = client.post(
        f"/api/v1/interview/sessions/{sid}/turn",
        json={
            "base_url": BASE_URL,
            "api_key": API_KEY,
            "model": "gemma-4-31b-it",
            "action": "message",
            "stage": "coding_1",
            "elapsed_sec": 420,
            "active_problem_slug": first_slug,
            "coding_snapshot": {
                "language": "python",
                "code": "def solve(nums):\n    return len(nums)",
                "verdict": "WA",
                "passed_count": 1,
                "total_count": 3,
            },
            "message": "I used a single pass loop, why did case 2 fail?",
        },
    )
    assert r2.status_code == 200
    sys_prompt_2 = capture["posts"][-1]["json"]["messages"][0]["content"]
    assert "<student_code>" in sys_prompt_2
    assert "def solve(nums):" in sys_prompt_2
    assert "Latest judge verdict: WA (1/3 passed)" in sys_prompt_2
    assert r2.json()["session"]["coding_snapshots"][first_slug]["verdict"] == "WA"

    # 3. Evaluate
    r3 = client.post(
        f"/api/v1/interview/sessions/{sid}/turn",
        json={
            "base_url": BASE_URL,
            "api_key": API_KEY,
            "model": "gemma-4-31b-it",
            "action": "evaluate",
            "elapsed_sec": 2900,
        },
    )
    assert r3.status_code == 200
    detail = r3.json()["session"]
    assert detail["status"] == "completed"
    assert detail["overall_verdict"] == "Strong Hire"
    assert detail["overall_score"] == 26
    assert detail["max_score"] == 30
    assert detail["rubric"]["total"] == 26
    assert "```json" not in r3.json()["reply"]
    assert "Solid FAANG performance" in r3.json()["reply"]

    # Persistence check across GET
    fetched = client.get(f"/api/v1/interview/sessions/{sid}")
    assert fetched.status_code == 200
    assert fetched.json()["overall_verdict"] == "Strong Hire"
    assert fetched.json()["coding_snapshots"][first_slug]["code"].startswith("def solve")


def test_evaluate_non_json_fallback_does_not_fail(client: TestClient, monkeypatch):
    register_and_login(client, "fallback_rubric@merit.org")
    install_fake_client(
        monkeypatch,
        post=lambda url, headers, body: FakeResponse(
            200,
            {"choices": [{"message": {"content": "Great work overall, watch edge cases."}}]},
        ),
    )
    sid = client.post("/api/v1/interview/sessions", json={"difficulty": "easy"}).json()["id"]
    res = client.post(
        f"/api/v1/interview/sessions/{sid}/turn",
        json={
            "base_url": BASE_URL,
            "api_key": API_KEY,
            "model": "gpt-4o-mini",
            "action": "evaluate",
        },
    )
    assert res.status_code == 200
    session_data = res.json()["session"]
    assert session_data["status"] == "completed"
    assert session_data["rubric"]["max_total"] == 20
    assert "Great work overall" in session_data["rubric"]["summary"]


def test_guest_endpoint_removed_and_session_ssrf_protection(client: TestClient, monkeypatch):
    guest_res = client.post(
        "/api/v1/interview/guest/turn",
        json={
            "base_url": BASE_URL,
            "api_key": API_KEY,
            "model": "gpt-4o-mini",
            "difficulty": "medium",
            "problem_slugs": ["two-sum"],
            "action": "start",
            "history": [],
        },
    )
    assert guest_res.status_code == 404

    register_and_login(client, "ssrf_session@merit.org")
    capture: dict = {}
    install_fake_client(
        monkeypatch,
        capture=capture,
        post=lambda url, headers, body: FakeResponse(
            200, {"choices": [{"message": {"content": "Tell me about hash collisions."}}]}
        ),
    )
    sid = client.post("/api/v1/interview/sessions", json={"difficulty": "easy"}).json()["id"]

    ssrf_res = client.post(
        f"/api/v1/interview/sessions/{sid}/turn",
        json={
            "base_url": "http://169.254.169.254/v1",
            "api_key": API_KEY,
            "model": "gpt-4o-mini",
            "action": "start",
        },
    )
    assert ssrf_res.status_code == 422
    assert ssrf_res.json()["detail"]["code"] == "TUTOR_BAD_URL"


def test_theory_prompt_hides_coding_problems_and_teaches_stage_markers(
    client: TestClient, monkeypatch
):
    register_and_login(client, "stage_prompt@merit.org")
    capture: dict = {}
    install_fake_client(
        monkeypatch,
        capture=capture,
        post=lambda url, headers, body: FakeResponse(
            200, {"choices": [{"message": {"content": "What is a hash map?"}}]}
        ),
    )
    created = client.post("/api/v1/interview/sessions", json={"difficulty": "easy"})
    assert created.status_code == 201
    sid = created.json()["id"]
    coding_title = created.json()["problems"][0]["title"]

    res = client.post(
        f"/api/v1/interview/sessions/{sid}/turn",
        json={
            "base_url": BASE_URL,
            "api_key": API_KEY,
            "model": "gpt-4o-mini",
            "action": "start",
        },
    )
    assert res.status_code == 200
    sys_prompt = capture["posts"][-1]["json"]["messages"][0]["content"]
    assert f'"{coding_title}"' not in sys_prompt
    assert "Assigned coding round problem(s)" not in sys_prompt
    assert "[[SUGGEST_NEXT:coding_1]]" in sys_prompt
    assert "You CANNOT open the code editor" in sys_prompt
    assert "Next Round" in sys_prompt


def test_suggest_next_marker_is_stripped_and_returned(client: TestClient, monkeypatch):
    register_and_login(client, "marker_strip@merit.org")
    install_fake_client(
        monkeypatch,
        post=lambda url, headers, body: FakeResponse(
            200,
            {
                "choices": [
                    {"message": {"content": "Nice work on hashing.\n[[SUGGEST_NEXT:coding_1]]"}}
                ]
            },
        ),
    )
    sid = client.post("/api/v1/interview/sessions", json={"difficulty": "easy"}).json()["id"]

    res = client.post(
        f"/api/v1/interview/sessions/{sid}/turn",
        json={
            "base_url": BASE_URL,
            "api_key": API_KEY,
            "model": "gpt-4o-mini",
            "action": "message",
            "stage": "theory",
            "message": "Hash maps bucket keys and resolve collisions.",
        },
    )
    assert res.status_code == 200
    body = res.json()
    assert body["suggested_stage"] == "coding_1"
    assert body["reply"] == "Nice work on hashing."
    assert "SUGGEST_NEXT" not in body["reply"]
    assert all("SUGGEST_NEXT" not in msg["content"] for msg in body["session"]["messages"])

    stored = client.get(f"/api/v1/interview/sessions/{sid}").json()
    assert all("SUGGEST_NEXT" not in msg["content"] for msg in stored["messages"])


def test_stage_fallback_signal_only_on_message_action(client: TestClient, monkeypatch):
    register_and_login(client, "stage_fallback@merit.org")
    reply = {"text": ""}
    install_fake_client(
        monkeypatch,
        post=lambda url, headers, body: FakeResponse(
            200, {"choices": [{"message": {"content": reply["text"]}}]}
        ),
    )
    sid = client.post("/api/v1/interview/sessions", json={"difficulty": "easy"}).json()["id"]

    reply["text"] = (
        "That concludes theory. Let's move on to Stage 2: Coding. "
        "I've opened the code editor for you."
    )
    message_res = client.post(
        f"/api/v1/interview/sessions/{sid}/turn",
        json={
            "base_url": BASE_URL,
            "api_key": API_KEY,
            "model": "gpt-4o-mini",
            "action": "message",
            "stage": "theory",
            "message": "Ready for the next round.",
        },
    )
    assert message_res.status_code == 200
    assert message_res.json()["suggested_stage"] == "coding_1"

    reply["text"] = "Welcome! We'll cover theory first and we'll move to coding later."
    start_res = client.post(
        f"/api/v1/interview/sessions/{sid}/turn",
        json={
            "base_url": BASE_URL,
            "api_key": API_KEY,
            "model": "gpt-4o-mini",
            "action": "start",
        },
    )
    assert start_res.status_code == 200
    assert start_res.json()["suggested_stage"] is None


def test_marker_only_reply_uses_fallback_filler(client: TestClient, monkeypatch):
    register_and_login(client, "marker_filler@merit.org")
    reply = {"text": ""}
    install_fake_client(
        monkeypatch,
        post=lambda url, headers, body: FakeResponse(
            200, {"choices": [{"message": {"content": reply["text"]}}]}
        ),
    )
    sid = client.post("/api/v1/interview/sessions", json={"difficulty": "easy"}).json()["id"]

    reply["text"] = "[[SUGGEST_NEXT:coding_1]]"
    session_res = client.post(
        f"/api/v1/interview/sessions/{sid}/turn",
        json={
            "base_url": BASE_URL,
            "api_key": API_KEY,
            "model": "gpt-4o-mini",
            "action": "message",
            "stage": "theory",
            "message": "Ready to code.",
        },
    )
    assert session_res.status_code == 200
    data = session_res.json()
    assert data["suggested_stage"] == "coding_1"
    assert "SUGGEST_NEXT" not in data["reply"]
    assert "Next Round" in data["reply"]
    assert "code editor" in data["reply"]
    assert data["session"]["messages"][-1]["content"] == data["reply"]

    reply["text"] = "[[SUGGEST_NEXT:rubric]]"
    session_res2 = client.post(
        f"/api/v1/interview/sessions/{sid}/turn",
        json={
            "base_url": BASE_URL,
            "api_key": API_KEY,
            "model": "gpt-4o-mini",
            "action": "message",
            "stage": "wrapup",
            "message": "Done with follow-ups.",
        },
    )
    assert session_res2.status_code == 200
    guest_data = session_res2.json()
    assert guest_data["suggested_stage"] == "rubric"
    assert "SUGGEST_NEXT" not in guest_data["reply"]
    assert "End & Score" in guest_data["reply"]


def test_parse_resume_pdf_upload(client: TestClient):
    register_and_login(client, "resume_pdf@merit.org")
    pdf_bytes = _build_pdf_bytes("Distributed Systems Intern built Go microservice on Kafka")
    ok = client.post(
        "/api/v1/interview/parse-resume",
        files={"file": ("my_cv.pdf", pdf_bytes, "application/pdf")},
    )
    assert ok.status_code == 200
    payload = ok.json()
    assert payload["filename"] == "my_cv.pdf"
    assert payload["pages"] == 1
    assert "Distributed Systems Intern" in payload["extracted_text"]

    not_pdf = client.post(
        "/api/v1/interview/parse-resume",
        files={"file": ("notes.txt", b"hello world", "text/plain")},
    )
    assert not_pdf.status_code == 422
    assert not_pdf.json()["detail"]["code"] == "INVALID_PDF"

    oversized = b"%PDF-1.4\n" + b"0" * (2 * 1024 * 1024 + 50)
    too_big = client.post(
        "/api/v1/interview/parse-resume",
        files={"file": ("huge.pdf", oversized, "application/pdf")},
    )
    assert too_big.status_code == 413
    assert too_big.json()["detail"]["code"] == "RESUME_TOO_LARGE"

    empty_pdf = client.post(
        "/api/v1/interview/parse-resume",
        files={"file": ("blank.pdf", _build_pdf_bytes(None), "application/pdf")},
    )
    assert empty_pdf.status_code == 422
    assert empty_pdf.json()["detail"]["code"] == "EMPTY_RESUME_TEXT"


def test_interview_requires_auth(client: TestClient):
    pdf_bytes = _build_pdf_bytes("Candidate profile")
    res = client.post(
        "/api/v1/interview/parse-resume",
        files={"file": ("cv.pdf", pdf_bytes, "application/pdf")},
    )
    assert res.status_code == 401
    assert client.post("/api/v1/interview/sessions", json={"difficulty": "easy"}).status_code == 401
    assert client.get("/api/v1/interview/sessions").status_code == 401


def test_completed_session_rejects_turn_and_patch(client: TestClient, monkeypatch):
    register_and_login(client, "completed_guard@merit.org")
    install_fake_client(
        monkeypatch,
        post=lambda url, headers, body: FakeResponse(
            200, {"choices": [{"message": {"content": "Great work overall."}}]}
        ),
    )
    sid = client.post("/api/v1/interview/sessions", json={"difficulty": "easy"}).json()["id"]
    completed = client.post(
        f"/api/v1/interview/sessions/{sid}/turn",
        json={
            "base_url": BASE_URL,
            "api_key": API_KEY,
            "model": "gpt-4o-mini",
            "action": "evaluate",
        },
    )
    assert completed.status_code == 200
    assert completed.json()["session"]["status"] == "completed"

    turn = client.post(
        f"/api/v1/interview/sessions/{sid}/turn",
        json={
            "base_url": BASE_URL,
            "api_key": API_KEY,
            "model": "gpt-4o-mini",
            "action": "message",
            "message": "One more question.",
        },
    )
    assert turn.status_code == 409
    assert turn.json()["detail"]["code"] == "SESSION_COMPLETED"

    patch = client.patch(
        f"/api/v1/interview/sessions/{sid}", json={"elapsed_sec": 99}
    )
    assert patch.status_code == 409
    assert patch.json()["detail"]["code"] == "SESSION_COMPLETED"


def test_coding_snapshots_restricted_to_assigned_problems(client: TestClient):
    register_and_login(client, "snapshot_guard@merit.org")
    sid = client.post("/api/v1/interview/sessions", json={"difficulty": "easy"}).json()["id"]
    res = client.patch(
        f"/api/v1/interview/sessions/{sid}",
        json={"coding_snapshots": {"not-assigned-slug": {"language": "python", "code": "x = 1"}}},
    )
    assert res.status_code == 422
    assert res.json()["detail"]["code"] == "INVALID_CODING_SNAPSHOT"
