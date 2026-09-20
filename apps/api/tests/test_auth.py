import pytest
from fastapi import HTTPException
from fastapi.testclient import TestClient
from sqlalchemy import Update, select
from sqlalchemy.dialects import sqlite

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
            "email_verified": True,
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
            "email_verified": True,
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
        "email_verified": True,
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


def _mock_service_claims(monkeypatch, claims):
    """Run the REAL verify_clerk_session_token with mocked JWKS/JWT layers."""
    import app.services.clerk_oauth as clerk_module

    monkeypatch.setattr(clerk_module.settings, "clerk_jwks_url", TEST_JWKS_URL, raising=False)
    monkeypatch.setattr(clerk_module.settings, "clerk_audience", "", raising=False)

    class _FakeKey:
        key = "test-signing-key"

    class _FakeClient:
        def get_signing_key_from_jwt(self, token):
            return _FakeKey()

    monkeypatch.setattr(clerk_module, "_jwks_client", lambda url: _FakeClient())
    monkeypatch.setattr(
        clerk_module.jwt, "decode", lambda token, key, **kwargs: claims
    )


def test_clerk_service_rejects_unverified_email(monkeypatch):
    import app.services.clerk_oauth as clerk_module

    _mock_service_claims(
        monkeypatch,
        {"sub": "user_attacker", "email": "victim@example.com", "email_verified": False},
    )
    with pytest.raises(HTTPException) as exc:
        clerk_module.verify_clerk_session_token("any.token.here")
    assert exc.value.status_code == 401
    assert exc.value.detail["code"] == "OAUTH_EMAIL_UNVERIFIED"


def test_clerk_service_rejects_missing_verified_flag(monkeypatch):
    import app.services.clerk_oauth as clerk_module

    # No verified flag at all -> reject (fail closed).
    _mock_service_claims(
        monkeypatch, {"sub": "user_attacker", "email": "victim@example.com"}
    )
    with pytest.raises(HTTPException) as exc:
        clerk_module.verify_clerk_session_token("any.token.here")
    assert exc.value.status_code == 401
    assert exc.value.detail["code"] == "OAUTH_EMAIL_UNVERIFIED"


def test_clerk_service_verified_flag_spellings(monkeypatch):
    import app.services.clerk_oauth as clerk_module

    base = {"sub": "user_x", "email": "x@example.com"}
    for key in ("email_verified", "emailVerified", "verified_email"):
        _mock_service_claims(monkeypatch, {**base, key: True})
        out = clerk_module.verify_clerk_session_token("any.token.here")
        assert out["email"] == "x@example.com"
        assert out["clerk_id"] == "user_x"

        _mock_service_claims(monkeypatch, {**base, key: False})
        with pytest.raises(HTTPException) as exc:
            clerk_module.verify_clerk_session_token("any.token.here")
        assert exc.value.detail["code"] == "OAUTH_EMAIL_UNVERIFIED"


@pytest.mark.parametrize(
    ("failure", "stage", "code"),
    [
        ("jwks", "jwks_fetch", "OAUTH_INVALID_TOKEN"),
        ("signature", "invalid_signature", "OAUTH_INVALID_TOKEN"),
        ("expired", "expired", "OAUTH_TOKEN_EXPIRED"),
        ("issuer", "issuer_mismatch", "OAUTH_ISSUER_MISMATCH"),
        ("audience", "audience_mismatch", "OAUTH_INVALID_TOKEN"),
        ("missing_sub", "missing_sub", "OAUTH_EMAIL_MISSING"),
        ("missing_email", "missing_email", "OAUTH_EMAIL_MISSING"),
        ("unverified", "email_unverified", "OAUTH_EMAIL_UNVERIFIED"),
    ],
)
def test_clerk_service_rejection_logs_reason(monkeypatch, caplog, failure, stage, code):
    import logging

    import app.services.clerk_oauth as clerk_module

    _mock_service_claims(monkeypatch, {"sub": "user_x", "email": "x@example.com"})
    monkeypatch.setattr(clerk_module.jwt, "get_unverified_header", lambda token: {"kid": "key-1"})

    if failure == "jwks":
        def _fail_client(url):
            raise RuntimeError("JWKS unavailable")

        monkeypatch.setattr(clerk_module, "_jwks_client", _fail_client)
    elif failure == "missing_sub":
        monkeypatch.setattr(
            clerk_module.jwt, "decode", lambda token, key, **kwargs: {"email": "x@example.com"}
        )
    elif failure == "missing_email":
        monkeypatch.setattr(
            clerk_module.jwt, "decode", lambda token, key, **kwargs: {"sub": "user_x"}
        )
    elif failure == "unverified":
        monkeypatch.setattr(
            clerk_module.jwt,
            "decode",
            lambda token, key, **kwargs: {
                "sub": "user_x",
                "email": "x@example.com",
                "email_verified": False,
            },
        )
    else:
        exception = {
            "signature": clerk_module.jwt.InvalidSignatureError("bad signature"),
            "expired": clerk_module.jwt.ExpiredSignatureError("expired"),
            "issuer": clerk_module.jwt.InvalidIssuerError("wrong issuer"),
            "audience": clerk_module.jwt.InvalidAudienceError("wrong audience"),
        }[failure]
        decode_calls = 0

        def _fail_decode(token, key, **kwargs):
            nonlocal decode_calls
            decode_calls += 1
            if failure == "issuer" and decode_calls == 2:
                return {"iss": "https://wrong.example"}
            raise exception

        monkeypatch.setattr(clerk_module.jwt, "decode", _fail_decode)

    with caplog.at_level(logging.WARNING, logger="app.services.clerk_oauth"), pytest.raises(
        HTTPException
    ) as exc:
        clerk_module.verify_clerk_session_token("eyJ.fake-token")

    assert exc.value.status_code == 401
    assert exc.value.detail["code"] == code
    records = [record for record in caplog.records if record.name == "app.services.clerk_oauth"]
    assert records
    assert any(f"stage={stage}" in record.getMessage() for record in records)
    assert all(
        "@" not in record.getMessage() and "eyJ" not in record.getMessage()
        for record in records
    )


def test_clerk_oauth_unverified_email_rejected_no_user_created(
    client: TestClient, monkeypatch, db_session
):
    _configure_clerk(monkeypatch)
    _mock_verified_claims(
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
    resp = client.post("/api/v1/auth/oauth/clerk", json=MOCK_TOKEN_PAYLOAD)
    assert resp.status_code == 401
    assert resp.json()["detail"]["code"] == "OAUTH_EMAIL_UNVERIFIED"
    assert len(db_session.scalars(select(User)).all()) == before


def test_refresh_rotation_race_loser_triggers_reuse(client: TestClient, monkeypatch, db_session):
    """Simulate a concurrent double-use: the conditional UPDATE affects 0 rows.

    The loser must fall into the TOKEN_REUSE_DETECTED theft path instead of
    minting a second replacement. Also asserts the UPDATE carries the
    ``revoked_at IS NULL`` predicate.
    """
    reg_resp = client.post(
        "/api/v1/auth/register",
        json={
            "email": "race@example.com",
            "display_name": "Race User",
            "password": "Password123456",
        },
    )
    original_refresh = reg_resp.cookies.get("merit_refresh")
    assert original_refresh is not None

    statements = []
    real_execute = db_session.execute

    def spy_execute(statement, *args, **kwargs):
        statements.append(statement)
        if isinstance(statement, Update):
            # Race lost: someone else revoked the token first.
            class _FakeResult:
                rowcount = 0

            return _FakeResult()
        return real_execute(statement, *args, **kwargs)

    monkeypatch.setattr(db_session, "execute", spy_execute)
    resp = client.post("/api/v1/auth/refresh", cookies={"merit_refresh": original_refresh})
    assert resp.status_code == 401
    assert resp.json()["detail"]["code"] == "TOKEN_REUSE_DETECTED"

    updates = [s for s in statements if isinstance(s, Update)]
    assert updates, "expected a conditional UPDATE during rotation"
    compiled = str(
        updates[0].compile(dialect=sqlite.dialect(), compile_kwargs={"literal_binds": True})
    )
    assert "revoked_at IS NULL" in compiled
