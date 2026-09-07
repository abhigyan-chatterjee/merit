from fastapi.testclient import TestClient


def register_user(client: TestClient, email: str, name: str) -> dict:
    resp = client.post(
        "/api/v1/auth/register",
        json={
            "email": email,
            "display_name": name,
            "password": "Password123456",
        },
    )
    assert resp.status_code == 201
    return {
        "data": resp.json(),
        "cookies": resp.cookies,
    }


def test_two_user_auth_isolation(client: TestClient):
    user_a = register_user(client, "user_a@example.com", "User Alice")
    user_b = register_user(client, "user_b@example.com", "User Bob")

    # Alice /me returns Alice
    me_a = client.get("/api/v1/auth/me", cookies=user_a["cookies"])
    assert me_a.status_code == 200
    assert me_a.json()["id"] == user_a["data"]["id"]
    assert me_a.json()["email"] == "user_a@example.com"

    # Bob /me returns Bob
    me_b = client.get("/api/v1/auth/me", cookies=user_b["cookies"])
    assert me_b.status_code == 200
    assert me_b.json()["id"] == user_b["data"]["id"]
    assert me_b.json()["email"] == "user_b@example.com"

    # Alice cannot see Bob's data through her session
    assert me_a.json()["id"] != me_b.json()["id"]

    # Bob cannot export Alice's data with his cookie
    export_b = client.get("/api/v1/auth/export", cookies=user_b["cookies"])
    assert export_b.status_code == 200
    assert export_b.json()["user"]["id"] == user_b["data"]["id"]
    assert export_b.json()["user"]["email"] != "user_a@example.com"


def test_unauthenticated_requests_rejected(client: TestClient):
    endpoints = [
        ("GET", "/api/v1/auth/me"),
        ("GET", "/api/v1/auth/export"),
        ("DELETE", "/api/v1/auth/account"),
    ]

    for method, path in endpoints:
        if method == "GET":
            resp = client.get(path)
        elif method == "DELETE":
            resp = client.delete(path)
        assert resp.status_code == 401
        assert resp.json()["detail"]["code"] in [
            "UNAUTHORIZED",
            "INVALID_TOKEN",
            "USER_INACTIVE",
        ]
