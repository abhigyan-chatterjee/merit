from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def test_health_check():
    response = client.get("/api/v1/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok", "service": "merit-api"}


def test_health_check_503_when_db_down(client, db_session, monkeypatch):
    def _boom(*args, **kwargs):
        raise RuntimeError("db down")

    monkeypatch.setattr(db_session, "execute", _boom)
    response = client.get("/api/v1/health")
    assert response.status_code == 503
