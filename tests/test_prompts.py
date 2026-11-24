from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)


def get_token():
    client.post(
        "/api/v1/auth/register",
        json={"email": "promptuser@example.com", "password": "secret123"},
    )
    r = client.post(
        "/api/v1/auth/login",
        data={"username": "promptuser@example.com", "password": "secret123"},
    )
    return r.json()["access_token"]


def test_create_prompt():
    token = get_token()
    r = client.post(
        "/api/v1/prompts",
        headers={"Authorization": f"Bearer {token}"},
        json={
            "title": "Test Prompt",
            "description": "A test",
            "content": "Say hello",
        },
    )
    assert r.status_code == 201
    assert r.json()["title"] == "Test Prompt"