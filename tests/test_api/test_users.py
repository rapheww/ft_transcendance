def test_create_user_api(client):
    response = client.post("/api/users/",
                           json={
                               "username": "alice",
                               "email": "alice@example.com",
                               "password": "password123"
                           })

    assert response.status_code == 201
    assert response.json() == {
        "username": "alice",
        "email": "alice@example.com"
    }


def test_get_user_api(client):
    client.post("/api/users/",
                json={
                    "username": "alice",
                    "email": "alice@example.com",
                    "password": "password123"
                })

    response = client.get("/api/users/alice")

    assert response.status_code == 200
    assert response.json() == {
        "username": "alice",
        "email": "alice@example.com"
    }


def test_get_missing_user_api_returns_404(client):
    response = client.get("/api/users/does-not-exist")

    assert response.status_code == 404
    assert response.json() == {"detail": "User not found"}


def test_create_duplicate_username_api_returns_409(client):
    client.post("/api/users/",
                json={
                    "username": "alice",
                    "email": "alice@example.com",
                    "password": "password123"
                })

    response = client.post("/api/users/",
                           json={
                               "username": "alice",
                               "email": "different@example.com",
                               "password": "password123"
                           })

    assert response.status_code == 409
    assert response.json() == {"detail": "Username already exists"}


def test_create_duplicate_email_api_returns_409(client):
    client.post("/api/users/",
                json={
                    "username": "alice",
                    "email": "alice@example.com",
                    "password": "password123"
                })

    response = client.post("/api/users/",
                           json={
                               "username": "bob",
                               "email": "alice@example.com",
                               "password": "password123"
                           })

    assert response.status_code == 409
    assert response.json() == {"detail": "Email already exists"}
