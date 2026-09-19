from fastapi.testclient import TestClient


def test_login_success(client: TestClient):
    client.post("/api/users/",
                json={
                    "username": "alice",
                    "email": "alice@example.com",
                    "password": "password123"
                })

    response = client.post("/api/auth/login",
                           json={
                               "username": "alice",
                               "password": "password123"
                           })

    assert response.status_code == 200

    body = response.json()

    assert "access_token" in body
    assert body["token_type"] == "bearer"
    assert isinstance(body["access_token"], str)
    assert len(body["access_token"]) > 0
    assert body["access_token"].count(".") == 2


def test_login_wrong_password_returns_401(client: TestClient):
    client.post("/api/users/",
                json={
                    "username": "alice",
                    "email": "alice@example.com",
                    "password": "password123"
                })

    response = client.post("/api/auth/login",
                           json={
                               "username": "alice",
                               "password": "wrong-password"
                           })

    assert response.status_code == 401
    assert response.json() == {"detail": "Invalid username or password"}


def test_login_unknown_user_returns_401(client: TestClient):
    response = client.post("/api/auth/login",
                           json={
                               "username": "does-not-exist",
                               "password": "password123"
                           })

    assert response.status_code == 401
    assert response.json() == {"detail": "Invalid username or password"}
