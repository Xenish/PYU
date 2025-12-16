from fastapi.testclient import TestClient

from app.main import create_app


def test_health_endpoint():
    app = create_app()
    client = TestClient(app)

    response = client.get("/health")

    assert response.status_code == 200
    body = response.json()
    assert body["app_status"] == "ok"
    assert "db_status" in body


def test_ping_endpoint():
    app = create_app()
    client = TestClient(app)

    response = client.get("/health/ping")

    assert response.status_code == 200
    assert response.json() == {"status": "ok"}
