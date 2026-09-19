"""Tests for Admin endpoints and role-based access control (Phase 9)."""

import uuid
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.models.content import Problem, Question
from app.models.quiz import AdminAuditLog
from app.models.user import User, utcnow_iso
from app.security import create_access_token, hash_password


def create_user_with_role(
    db: Session, email: str, role: str = "student", name: str = "Test User"
) -> tuple[User, str]:
    user = User(
        id=str(uuid.uuid4()),
        email=email,
        display_name=name,
        password_hash=hash_password("Password123!"),
        role=role,
        is_active=1,
        created_at=utcnow_iso(),
    )
    db.add(user)
    db.commit()
    db.refresh(user)

    token = create_access_token(user.id, role=role)
    return user, token


def test_admin_endpoints_reject_unauthenticated(client: TestClient):
    endpoints = [
        ("GET", "/api/v1/admin/stats"),
        ("GET", "/api/v1/admin/review-queue"),
        ("GET", "/api/v1/admin/coverage"),
        ("GET", "/api/v1/admin/audit-logs"),
        ("POST", "/api/v1/admin/questions/dummy-q/review"),
        ("POST", "/api/v1/admin/problems/dummy-p/review"),
    ]

    for method, url in endpoints:
        if method == "GET":
            res = client.get(url)
        else:
            res = client.post(url, json={"action": "approved"})
        assert res.status_code == 401, f"Expected 401 for {method} {url}, got {res.status_code}"


def test_admin_endpoints_reject_student(client: TestClient, db_session: Session):
    student, student_token = create_user_with_role(
        db_session, "student_tester@example.com", role="student"
    )

    client.cookies.set("merit_access", student_token)

    # Student should receive 403 Forbidden on all admin endpoints
    res_stats = client.get("/api/v1/admin/stats")
    assert res_stats.status_code == 403
    assert res_stats.json()["detail"]["code"] == "FORBIDDEN"

    res_queue = client.get("/api/v1/admin/review-queue")
    assert res_queue.status_code == 403

    res_cov = client.get("/api/v1/admin/coverage")
    assert res_cov.status_code == 403

    res_rev = client.post(
        "/api/v1/admin/questions/dummy/review", json={"action": "approved"}
    )
    assert res_rev.status_code == 403


def test_admin_stats_and_audit_logging(client: TestClient, db_session: Session):
    admin, admin_token = create_user_with_role(
        db_session, "admin_user@example.com", role="admin", name="Admin Officer"
    )

    client.cookies.set("merit_access", admin_token)

    # 1. Check stats
    res = client.get("/api/v1/admin/stats")
    assert res.status_code == 200
    data = res.json()
    assert "users_count" in data
    assert "total_submissions" in data
    assert "ac_rate_pct" in data
    assert "verified_questions" in data

    # 2. Verify audit log was recorded
    res_logs = client.get("/api/v1/admin/audit-logs")
    assert res_logs.status_code == 200
    logs = res_logs.json()
    assert len(logs) >= 1
    assert any(l["action"] == "view_stats" for l in logs)


def test_admin_question_review_workflow(client: TestClient, db_session: Session):
    admin, admin_token = create_user_with_role(
        db_session, "admin_reviewer@example.com", role="admin"
    )

    # Create a draft question
    draft_q = Question(
        id=str(uuid.uuid4()),
        topic="trees",
        difficulty="medium",
        qtype="mcq",
        prompt="What is a red-black tree color property?",
        options='["Root is black", "Root is red", "Leaves are red", "None"]',
        correct_index=0,
        explanation="The root of a red-black tree is always black.",
        source="curated",
        content_hash="test_hash_rbt",
        review_status="draft",
        created_at=utcnow_iso(),
        updated_at=utcnow_iso(),
    )
    db_session.add(draft_q)
    db_session.commit()

    client.cookies.set("merit_access", admin_token)

    # 1. Draft question should appear in review queue
    res_queue = client.get("/api/v1/admin/review-queue?type=questions")
    assert res_queue.status_code == 200
    queue = res_queue.json()
    assert any(item["id"] == draft_q.id for item in queue)

    # 2. Approve the question
    res_review = client.post(
        f"/api/v1/admin/questions/{draft_q.id}/review",
        json={"action": "approved", "note": "Verified by admin inspection"},
    )
    assert res_review.status_code == 200
    assert res_review.json()["review_status"] == "verified"

    # 3. Question status in DB is updated
    db_session.refresh(draft_q)
    assert draft_q.review_status == "verified"

    # 4. Coverage matrix includes verified question
    res_cov = client.get("/api/v1/admin/coverage")
    assert res_cov.status_code == 200
    cov = res_cov.json()
    assert "trees" in cov["matrix"]
    assert cov["matrix"]["trees"]["medium"] >= 1
