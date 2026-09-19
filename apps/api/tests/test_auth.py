from fastapi import HTTPException
from fastapi.testclient import TestClient
from sqlalchemy import select

import app.routers.auth as auth_router
from app.models.user import User

TEST_JWKS_URL = "https://test-oauth.clerk.accounts.dev/.well-known/jwks.json"
MOCK_TOKEN_PAYLOAD = {"clerk_token": "mocked.clerk.session.token"}


def _configure_clerk(monkeypatch):
    """Pretend Clerk is configured (no network: verification itself is mocked)."""
    monkeypatch.setattr(auth_router.settings, "clerk_jwks_url", TEST_JWKS_URL, raising=False)


def _mock_verified_claims(monkeypatch, claims=None, error=None):
    if error is not None:

        def _raise(token: str):
            raise error

        monkeypatch.setattr(auth_router, "verify_clerk_session_token", _raise)
    else:

        def _ok(token: str):
            assert token == "mocked.clerk.session.token"
            return claims

        monkeypatch.setattr(auth_router, "verify_clerk_session_token", _ok)


def test_register_login_logout_flow(client: TestClient):
    # 1. Register
    reg_payload = {
        "email": "testuser@example.com",
        "display_name": "Test User",
        "password": "StrongPassword123!",
    }
    reg_resp = client.post("/api/v1/auth/register", json=reg_payload)
    assert reg_resp.status_code == 201
    user_data = reg_resp.json()
    assert user_data["email"] == "testuser@example.com"
    assert user_data["display_name"] == "Test User"
    assert "password" not in user_data
    assert "password_hash" not in user_data

    # Check httpOnly cookies
    assert "merit_access" in reg_resp.cookies
    assert "merit_refresh" in reg_resp.cookies

    # 2. Get /me
    me_resp = client.get("/api/v1/auth/me", cookies=reg_resp.cookies)
    assert me_resp.status_code == 200
    assert me_resp.json()["id"] == user_data["id"]

    # 3. Logout
    logout_resp = client.post("/api/v1/auth/logout", cookies=reg_resp.cookies)
    assert logout_resp.status_code == 200

    # 4. Login
    login_resp = client.post(
        "/api/v1/auth/login",
        json={"email": "testuser@example.com", "password": "StrongPassword123!"},
    )
    assert login_resp.status_code == 200
    assert "merit_access" in login_resp.cookies
    assert "merit_refresh" in login_resp.cookies


def test_register_duplicate_email_rejected(client: TestClient):
    payload = {
        "email": "duplicate@example.com",
        "display_name": "User 1",
        "password": "Password123456",
    }
    client.post("/api/v1/auth/register", json=payload)
    dup_resp = client.post("/api/v1/auth/register", json=payload)
    assert dup_resp.status_code == 400
    assert dup_resp.json()["detail"]["code"] == "EMAIL_EXISTS"


def test_register_short_password_rejected(client: TestClient):
    payload = {
        "email": "shortpass@example.com",
        "display_name": "Short Pass",
        "password": "short",  # < 10 chars
    }
    resp = client.post("/api/v1/auth/register", json=payload)
    assert resp.status_code == 422


def test_login_invalid_password(client: TestClient):
    client.post(
        "/api/v1/auth/register",
        json={
            "email": "wrongpass@example.com",
            "display_name": "Valid User",
            "password": "CorrectPassword123",
        },
    )
    resp = client.post(
        "/api/v1/auth/login",
        json={"email": "wrongpass@example.com", "password": "IncorrectPassword999"},
    )
    assert resp.status_code == 401
    assert resp.json()["detail"]["code"] == "INVALID_CREDENTIALS"


def test_refresh_token_rotation_and_theft_detection(client: TestClient):
    # Register
    reg_resp = client.post(
        "/api/v1/auth/register",
        json={
            "email": "rotation@example.com",
            "display_name": "Rotation User",
            "password": "Password123456",
        },
    )
    original_refresh = reg_resp.cookies.get("merit_refresh")
    assert original_refresh is not None

    # Rotate 1: refresh using original token
    ref_resp = client.post("/api/v1/auth/refresh", cookies={"merit_refresh": original_refresh})
    assert ref_resp.status_code == 200
    rotated_refresh = ref_resp.cookies.get("merit_refresh")
    assert rotated_refresh is not None
    assert rotated_refresh != original_refresh

    # Rotate 2: using new rotated token works
    ref2_resp = client.post("/api/v1/auth/refresh", cookies={"merit_refresh": rotated_refresh})
    assert ref2_resp.status_code == 200

    # THEFT DETECTION: Try to reuse original_refresh token (already revoked)
    theft_resp = client.post("/api/v1/auth/refresh", cookies={"merit_refresh": original_refresh})
    assert theft_resp.status_code == 401
    assert theft_resp.json()["detail"]["code"] == "TOKEN_REUSE_DETECTED"

    # All tokens should now be revoked for this user
    assert (
        client.post("/api/v1/auth/refresh", cookies={"merit_refresh": rotated_refresh}).status_code
        == 401
    )


def test_export_and_delete_account(client: TestClient):
    reg_resp = client.post(
        "/api/v1/auth/register",
        json={
            "email": "gdpr@example.com",
            "display_name": "GDPR User",
            "password": "Password123456",
        },
    )
    cookies = reg_resp.cookies

    # Export
    export_resp = client.get("/api/v1/auth/export", cookies=cookies)
    assert export_resp.status_code == 200
    assert export_resp.json()["user"]["email"] == "gdpr@example.com"

    # Delete
    del_resp = client.delete("/api/v1/auth/account", cookies=cookies)
    assert del_resp.status_code == 200

    # Now /me should be 401
    me_resp = client.get("/api/v1/auth/me", cookies=cookies)
    assert me_resp.status_code == 401


def test_update_profile_display_name(client: TestClient):
    reg = client.post(
        "/api/v1/auth/register",
        json={
            "email": "profile@example.com",
            "display_name": "Old Name",
            "password": "Password123456",
        },
    )
    assert reg.status_code == 201
    resp = client.patch("/api/v1/auth/me", json={"display_name": "New Name"})
    assert resp.status_code == 200
    assert resp.json()["display_name"] == "New Name"


def test_change_email_requires_current_password(client: TestClient):
    client.post(
        "/api/v1/auth/register",
        json={
            "email": "emailchg@example.com",
            "display_name": "Email Chg",
            "password": "Password123456",
        },
    )
    bad = client.post(
        "/api/v1/auth/email",
        json={"new_email": "newemail@example.com", "current_password": "WrongPassword1"},
    )
    assert bad.status_code == 401
    assert bad.json()["detail"]["code"] == "INVALID_PASSWORD"

    ok = client.post(
        "/api/v1/auth/email",
        json={"new_email": "newemail@example.com", "current_password": "Password123456"},
    )
    assert ok.status_code == 200
    assert ok.json()["email"] == "newemail@example.com"


def test_change_password_flow(client: TestClient):
    client.post(
        "/api/v1/auth/register",
        json={
            "email": "pwchg@example.com",
            "display_name": "Pw Chg",
            "password": "Password123456",
        },
    )
    bad = client.post(
        "/api/v1/auth/password",
        json={"current_password": "WrongPassword1", "new_password": "NewPassword123456"},
    )
    assert bad.status_code == 401

    ok = client.post(
        "/api/v1/auth/password",
        json={"current_password": "Password123456", "new_password": "NewPassword123456"},
    )
    assert ok.status_code == 200

    # Old password no longer works; new one does
    client.post("/api/v1/auth/logout")
    old_login = client.post(
        "/api/v1/auth/login",
        json={"email": "pwchg@example.com", "password": "Password123456"},
    )
    assert old_login.status_code == 401
    new_login = client.post(
        "/api/v1/auth/login",
        json={"email": "pwchg@example.com", "password": "NewPassword123456"},
    )
    assert new_login.status_code == 200


# --- Clerk OAuth (Google/GitHub): mocked JWKS verification, no network ---


def test_clerk_oauth_links_existing_email_account(client: TestClient, monkeypatch, db_session):
    _configure_clerk(monkeypatch)
    reg_resp = client.post(
        "/api/v1/auth/register",
        json={
            "email": "oauthlink@example.com",
            "display_name": "OAuth Link",
            "password": "Password123456",
        },
    )
    assert reg_resp.status_code == 201
    user_id = reg_resp.json()["id"]

    _mock_verified_claims(
        monkeypatch,
        claims={
            "clerk_id": "user_clerk_link123",
            "email": "oauthlink@example.com",
            "display_name": "OAuth Link",
        },
    )
    resp = client.post("/api/v1/auth/oauth/clerk", json=MOCK_TOKEN_PAYLOAD)
    assert resp.status_code == 200
    assert resp.json()["id"] == user_id  # same account, not a duplicate
    assert "merit_access" in resp.cookies
    assert "merit_refresh" in resp.cookies

    user = db_session.get(User, user_id)
    assert user.clerk_id == "user_clerk_link123"

    # Password login still works after linking (password + data kept).
    login_resp = client.post(
        "/api/v1/auth/login",
        json={"email": "oauthlink@example.com", "password": "Password123456"},
    )
    assert login_resp.status_code == 200


def test_clerk_oauth_creates_new_user(client: TestClient, monkeypatch, db_session):
    _configure_clerk(monkeypatch)
    _mock_verified_claims(
        monkeypatch,
        claims={
            "clerk_id": "user_clerk_new456",
            "email": "brandnew-oauth@example.com",
            "display_name": "Brand New",
        },
    )
    resp = client.post("/api/v1/auth/oauth/clerk", json=MOCK_TOKEN_PAYLOAD)
    assert resp.status_code == 201
    assert resp.json()["email"] == "brandnew-oauth@example.com"
    assert "merit_access" in resp.cookies
    assert "merit_refresh" in resp.cookies

    user = db_session.scalar(select(User).where(User.email == "brandnew-oauth@example.com"))
    assert user is not None
    assert user.clerk_id == "user_clerk_new456"
    assert user.auth_provider == "clerk"
    assert user.password_hash == "oauth$clerk"
    assert user.is_active == 1


def test_clerk_oauth_reuses_linked_account(client: TestClient, monkeypatch):
    _configure_clerk(monkeypatch)
    claims = {
        "clerk_id": "user_clerk_repeat789",
        "email": "repeat-oauth@example.com",
        "display_name": "Repeat User",
    }
    _mock_verified_claims(monkeypatch, claims=claims)
    first = client.post("/api/v1/auth/oauth/clerk", json=MOCK_TOKEN_PAYLOAD)
    assert first.status_code == 201
    second = client.post("/api/v1/auth/oauth/clerk", json=MOCK_TOKEN_PAYLOAD)
    assert second.status_code == 200
    assert second.json()["id"] == first.json()["id"]


def test_clerk_oauth_invalid_token_rejected(client: TestClient, monkeypatch):
    _configure_clerk(monkeypatch)
    _mock_verified_claims(
        monkeypatch,
        error=HTTPException(
            status_code=401,
            detail={
                "code": "OAUTH_INVALID_TOKEN",
                "message": "Could not verify Clerk session token.",
            },
        ),
    )
    resp = client.post("/api/v1/auth/oauth/clerk", json=MOCK_TOKEN_PAYLOAD)
    assert resp.status_code == 401
    assert resp.json()["detail"]["code"] == "OAUTH_INVALID_TOKEN"


def test_clerk_oauth_expired_token_rejected(client: TestClient, monkeypatch):
    _configure_clerk(monkeypatch)
    _mock_verified_claims(
        monkeypatch,
        error=HTTPException(
            status_code=401,
            detail={"code": "OAUTH_TOKEN_EXPIRED", "message": "Clerk session has expired."},
        ),
    )
    resp = client.post("/api/v1/auth/oauth/clerk", json=MOCK_TOKEN_PAYLOAD)
    assert resp.status_code == 401
    assert resp.json()["detail"]["code"] == "OAUTH_TOKEN_EXPIRED"


def test_clerk_oauth_unconfigured_returns_501(client: TestClient, monkeypatch):
    monkeypatch.setattr(auth_router.settings, "clerk_jwks_url", "", raising=False)
    resp = client.post("/api/v1/auth/oauth/clerk", json=MOCK_TOKEN_PAYLOAD)
    assert resp.status_code == 501
    assert resp.json()["detail"]["code"] == "OAUTH_NOT_CONFIGURED"
