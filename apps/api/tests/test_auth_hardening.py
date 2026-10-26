"""Regression tests for the auth hardening pass.

Each test here corresponds to a defect that shipped: a provider-only account
used to 500 on every password endpoint, and a password change used to leave
every previously issued refresh token valid.
"""

from app.models.user import User
from app.security import create_access_token


def _oauth_only_user(db_session, email="oauthonly@example.com") -> User:
    user = User(
        email=email,
        display_name="OAuth Only",
        password_hash="oauth$clerk",
        role="student",
        is_active=1,
        clerk_id=f"clerk_{email}",
        auth_provider="clerk",
    )
    db_session.add(user)
    db_session.commit()
    return user


def _authenticate(client, user: User) -> None:
    client.cookies.set("merit_access", create_access_token(user.id, user.role))


def _register(client, email="pwchange@example.com", password="OldStrongPassw0rd!"):
    response = client.post(
        "/api/v1/auth/register",
        json={"email": email, "display_name": "PW", "password": password},
    )
    assert response.status_code == 201, response.text
    return response


def test_login_on_provider_only_account_is_401_not_500(client, db_session):
    """A provider-only row must read as 'wrong credentials', never crash.

    pwdlib raises UnknownHashError on the `oauth$clerk` sentinel. Before the
    fix that propagated out of the handler as a 500, which both leaked that the
    address exists and distinguished it from an ordinary wrong password.
    """
    _oauth_only_user(db_session)

    response = client.post(
        "/api/v1/auth/login",
        json={"email": "oauthonly@example.com", "password": "anything"},
    )

    assert response.status_code == 401, response.text
    assert response.json()["detail"]["code"] == "INVALID_CREDENTIALS"


def test_login_on_unknown_email_is_401_not_500(client):
    response = client.post(
        "/api/v1/auth/login",
        json={"email": "nobody@example.com", "password": "anything"},
    )
    assert response.status_code == 401, response.text


def test_change_password_on_provider_only_account_is_400(client, db_session):
    user = _oauth_only_user(db_session, email="oauth2@example.com")
    _authenticate(client, user)

    response = client.post(
        "/api/v1/auth/password",
        json={"current_password": "whatever", "new_password": "NewStrongPassw0rd!"},
    )

    assert response.status_code == 400, response.text
    assert response.json()["detail"]["code"] == "NO_PASSWORD_CREDENTIAL"


def test_change_email_on_provider_only_account_is_400(client, db_session):
    user = _oauth_only_user(db_session, email="oauth3@example.com")
    _authenticate(client, user)

    response = client.post(
        "/api/v1/auth/email",
        json={"current_password": "whatever", "new_email": "moved@example.com"},
    )

    assert response.status_code == 400, response.text
    assert response.json()["detail"]["code"] == "NO_PASSWORD_CREDENTIAL"


def test_change_password_revokes_pre_existing_refresh_tokens(client, db_session):
    """The token the caller held before the change must stop working.

    This is the entire point of changing a password after a compromise. The
    handler returning 200 proves nothing on its own.
    """
    _register(client)
    stale_token = client.cookies.get("merit_refresh")
    assert stale_token, "register must set a refresh cookie"

    change = client.post(
        "/api/v1/auth/password",
        json={
            "current_password": "OldStrongPassw0rd!",
            "new_password": "NewStrongPassw0rd!",
        },
    )
    assert change.status_code == 200, change.text

    stale_client = client.__class__(client.app)
    stale_client.cookies.set("merit_refresh", stale_token)
    replay = stale_client.post("/api/v1/auth/refresh")

    assert replay.status_code == 401, f"stale refresh token still accepted: {replay.text}"


def test_change_password_keeps_the_calling_device_signed_in(client):
    """Revocation must not log out the device that performed the change."""
    _register(client, email="keepme@example.com")

    change = client.post(
        "/api/v1/auth/password",
        json={
            "current_password": "OldStrongPassw0rd!",
            "new_password": "NewStrongPassw0rd!",
        },
    )
    assert change.status_code == 200, change.text

    rotated = client.cookies.get("merit_refresh")
    assert rotated, "change_password must reissue a refresh cookie"

    fresh = client.__class__(client.app)
    fresh.cookies.set("merit_refresh", rotated)
    assert fresh.post("/api/v1/auth/refresh").status_code == 200


def test_new_password_is_the_one_that_works(client):
    _register(client, email="newpw@example.com")
    client.post(
        "/api/v1/auth/password",
        json={
            "current_password": "OldStrongPassw0rd!",
            "new_password": "NewStrongPassw0rd!",
        },
    )
    client.cookies.clear()

    old = client.post(
        "/api/v1/auth/login",
        json={"email": "newpw@example.com", "password": "OldStrongPassw0rd!"},
    )
    assert old.status_code == 401, "the replaced password must stop working"

    new = client.post(
        "/api/v1/auth/login",
        json={"email": "newpw@example.com", "password": "NewStrongPassw0rd!"},
    )
    assert new.status_code == 200, new.text


def test_change_password_rejects_wrong_current_password(client):
    _register(client, email="wrongpw@example.com")
    response = client.post(
        "/api/v1/auth/password",
        json={
            "current_password": "NotMyPassword1!",
            "new_password": "NewStrongPassw0rd!",
        },
    )
    assert response.status_code == 401
    assert response.json()["detail"]["code"] == "INVALID_PASSWORD"
