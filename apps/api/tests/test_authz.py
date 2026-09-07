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


def test_progress_user_isolation(client: TestClient):
    user_a = register_user(client, "alice_progress@example.com", "Alice Progress")
    user_b = register_user(client, "bob_progress@example.com", "Bob Progress")

    # Alice sets problem progress and note
    res = client.put(
        "/api/v1/progress/problems/two-sum",
        json={"status": "Done"},
        cookies=user_a["cookies"],
    )
    assert res.status_code == 200

    res = client.put(
        "/api/v1/progress/notes/two-sum",
        json={"text": "Alice's secret note"},
        cookies=user_a["cookies"],
    )
    assert res.status_code == 200

    # Bob checks problem progress -> should be default "Todo", NOT Alice's "Done"
    res_b = client.get("/api/v1/progress/problems/two-sum", cookies=user_b["cookies"])
    assert res_b.status_code == 200
    assert res_b.json()["status"] == "Todo"

    # Bob checks note -> should be empty, NOT Alice's note
    res_b_note = client.get("/api/v1/progress/notes/two-sum", cookies=user_b["cookies"])
    assert res_b_note.status_code == 200
    assert res_b_note.json()["text"] == ""

    # Bob's summary shows 0 solved
    sum_b = client.get("/api/v1/progress/summary", cookies=user_b["cookies"]).json()
    assert sum_b["solved_count"] == 0
    assert "two-sum" not in sum_b["progress"]


def test_judge_submissions_user_isolation(client: TestClient, db_session):
    from app.seed import seed_problems

    seed_problems(db_session)

    user_a = register_user(client, "alice_judge@example.com", "Alice Judge")
    user_b = register_user(client, "bob_judge@example.com", "Bob Judge")

    # Alice submits code for two-sum
    res_a = client.post(
        "/api/v1/judge/submit",
        json={
            "problem_slug": "two-sum",
            "language": "javascript",
            "code": "function twoSum(nums, target) { return [0, 1]; }",
        },
        cookies=user_a["cookies"],
    )
    assert res_a.status_code == 200

    # Alice sees her submission
    alice_subs = client.get(
        "/api/v1/judge/submissions/two-sum",
        cookies=user_a["cookies"],
    ).json()
    assert len(alice_subs) == 1

    # Bob asks for submissions for two-sum -> must be empty (cannot see Alice's)
    bob_subs = client.get(
        "/api/v1/judge/submissions/two-sum",
        cookies=user_b["cookies"],
    ).json()
    assert len(bob_subs) == 0
