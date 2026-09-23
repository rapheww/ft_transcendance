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


def test_update_me(client):
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

    token = login_response.json()["access_token"]

    response = client.patch("/api/users/me",
                            headers={"Authorization": f"Bearer {token}"},
                            json={
                                "username": "alice-new",
                                "email": "alice-new@example.com"
                            })

    assert response.status_code == 200
    assert response.json() == {
        "username": "alice-new",
        "email": "alice-new@example.com"
    }


def test_update_me_email_only(client):
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

    token = login_response.json()["access_token"]

    response = client.patch("/api/users/me",
                            headers={"Authorization": f"Bearer {token}"},
                            json={"email": "new@example.com"})

    assert response.status_code == 200
    assert response.json() == {"username": "alice", "email": "new@example.com"}


def test_update_me_without_token_returns_401(client):
    response = client.patch("/api/users/me", json={"email": "new@example.com"})

    assert response.status_code == 401


def test_update_me_duplicate_username_returns_409(client):
    client.post("/api/users/",
                json={
                    "username": "alice",
                    "email": "alice@example.com",
                    "password": "password123"
                })

    client.post("/api/users/",
                json={
                    "username": "bob",
                    "email": "bob@example.com",
                    "password": "password123"
                })

    login_response = client.post("/api/auth/login",
                                 json={
                                     "username": "bob",
                                     "password": "password123"
                                 })

    token = login_response.json()["access_token"]

    response = client.patch("/api/users/me",
                            headers={"Authorization": f"Bearer {token}"},
                            json={"username": "alice"})

    assert response.status_code == 409
    assert response.json() == {"detail": "Username already exists"}


def test_update_me_duplicate_email_returns_409(client):
    client.post("/api/users/",
                json={
                    "username": "alice",
                    "email": "alice@example.com",
                    "password": "password123"
                })

    client.post("/api/users/",
                json={
                    "username": "bob",
                    "email": "bob@example.com",
                    "password": "password123"
                })

    login_response = client.post("/api/auth/login",
                                 json={
                                     "username": "bob",
                                     "password": "password123"
                                 })

    token = login_response.json()["access_token"]

    response = client.patch("/api/users/me",
                            headers={"Authorization": f"Bearer {token}"},
                            json={"email": "alice@example.com"})

    assert response.status_code == 409
    assert response.json() == {"detail": "Email already exists"}
