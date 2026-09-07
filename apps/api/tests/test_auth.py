from fastapi.testclient import TestClient


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
    assert "av_access" in reg_resp.cookies
    assert "av_refresh" in reg_resp.cookies

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
    assert "av_access" in login_resp.cookies
    assert "av_refresh" in login_resp.cookies


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
    original_refresh = reg_resp.cookies.get("av_refresh")
    assert original_refresh is not None

    # Rotate 1: refresh using original token
    ref_resp = client.post("/api/v1/auth/refresh", cookies={"av_refresh": original_refresh})
    assert ref_resp.status_code == 200
    rotated_refresh = ref_resp.cookies.get("av_refresh")
    assert rotated_refresh is not None
    assert rotated_refresh != original_refresh

    # Rotate 2: using new rotated token works
    ref2_resp = client.post("/api/v1/auth/refresh", cookies={"av_refresh": rotated_refresh})
    assert ref2_resp.status_code == 200

    # THEFT DETECTION: Try to reuse original_refresh token (already revoked)
    theft_resp = client.post("/api/v1/auth/refresh", cookies={"av_refresh": original_refresh})
    assert theft_resp.status_code == 401
    assert theft_resp.json()["detail"]["code"] == "TOKEN_REUSE_DETECTED"

    # All tokens should now be revoked for this user
    assert client.post(
        "/api/v1/auth/refresh", cookies={"av_refresh": rotated_refresh}
    ).status_code == 401


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
