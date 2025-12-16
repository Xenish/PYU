from fastapi.testclient import TestClient

from app.main import create_app


def test_health_endpoint():
    client = TestClient(create_app())
    resp = client.get("/health")
    assert resp.status_code == 200
    data = resp.json()
    assert "app_status" in data


def test_health_ping():
    client = TestClient(create_app())
    resp = client.get("/health/ping")
    assert resp.status_code == 200
    assert resp.json() == {"status": "ok"}
