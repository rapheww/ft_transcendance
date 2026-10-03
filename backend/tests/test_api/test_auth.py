import jwt
from backend.core.config import settings
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


def test_get_me_with_valid_token(client: TestClient):
    client.post("/api/users/",
                json={
                    "username": "alice",
                    "email": "alice@example.com",
                    "password": "password123"
                })

    login_response = client.post("/api/auth/login",
                                 json={
                                     "username": "alice",
                                     "password": "password123"
                                 })

    assert login_response.status_code == 200
    token = login_response.json()["access_token"]
    response = client.get("/api/users/me",
                          headers={"Authorization": f"Bearer {token}"})

    assert response.status_code == 200
    assert response.json() == {
        "username": "alice",
        "email": "alice@example.com",
        "avatar": "https://shorturl.at/Jm5fo",
        "board_light_color": "#E3DDC5",
        "board_dark_color": "#2C5563"
    }


def test_get_me_without_token_returns_401(client: TestClient):
    response = client.get("/api/users/me")

    assert response.status_code == 401


def test_get_me_with_invalid_token_returns_401(client: TestClient):
    response = client.get("/api/users/me",
                          headers={"Authorization": "Bearer not-a-real-token"})

    assert response.status_code == 401


def test_get_me_with_malformed_subject_returns_401(client: TestClient):
    token = jwt.encode({
        "sub": "not-an-integer",
        "type": "access"
    },
                       settings.jwt_secret_key,
                       algorithm=settings.jwt_algorithm)

    response = client.get("/api/users/me",
                          headers={"Authorization": f"Bearer {token}"})

    assert response.status_code == 401
    assert response.json() == {"detail": "Invalid authentication credentials"}


def test_get_me_with_nonexistent_user_returns_401(client: TestClient):
    token = jwt.encode({
        "sub": "999999",
        "type": "access"
    },
                       settings.jwt_secret_key,
                       algorithm=settings.jwt_algorithm)

    response = client.get("/api/users/me",
                          headers={"Authorization": f"Bearer {token}"})

    assert response.status_code == 401
    assert response.json() == {"detail": "Invalid authentication credentials"}


def test_get_me_with_wrong_token_type_returns_401(client: TestClient):
    token = jwt.encode({
        "sub": "42",
        "type": "refresh"
    },
                       settings.jwt_secret_key,
                       algorithm=settings.jwt_algorithm)

    response = client.get("/api/users/me",
                          headers={"Authorization": f"Bearer {token}"})

    assert response.status_code == 401
    assert response.json() == {"detail": "Invalid authentication credentials"}
