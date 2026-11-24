from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)


def test_register_and_login():
    r = client.post(
        "/api/v1/auth/register",
        json={"email": "test@example.com", "password": "secret123"},
    )
    assert r.status_code in (201, 400)  # 400 if already exists

    r = client.post(
        "/api/v1/auth/login",
        data={"username": "test@example.com", "password": "secret123"},
    )
    assert r.status_code == 200
    assert "access_token" in r.json()