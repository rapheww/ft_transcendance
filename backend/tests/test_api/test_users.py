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
        "email": "alice@example.com",
        "avatar": "https://shorturl.at/Jm5fo",
        "board_light_color": "#E3DDC5",
        "board_dark_color": "#2C5563"
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
        "email": "alice@example.com",
        "avatar": "https://shorturl.at/Jm5fo",
        "board_light_color": "#E3DDC5",
        "board_dark_color": "#2C5563"
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
        "email": "alice-new@example.com",
        "avatar": "https://shorturl.at/Jm5fo",
        "board_light_color": "#E3DDC5",
        "board_dark_color": "#2C5563"
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
    assert response.json() == {
        "username": "alice",
        "email": "new@example.com",
        "avatar": "https://shorturl.at/Jm5fo",
        "board_light_color": "#E3DDC5",
        "board_dark_color": "#2C5563"
    }


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


def test_get_me_returns_customization(client):
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


def test_update_me_customization(client):
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
                                "avatar": "avatar-2",
                                "board_light_color": "#FFFFFF",
                                "board_dark_color": "#000000"
                            })

    assert response.status_code == 200
    assert response.json() == {
        "username": "alice",
        "email": "alice@example.com",
        "avatar": "avatar-2",
        "board_light_color": "#FFFFFF",
        "board_dark_color": "#000000"
    }


def test_update_me_customization_persists(client):
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
    headers = {"Authorization": f"Bearer {token}"}

    update_response = client.patch("/api/users/me",
                                   headers=headers,
                                   json={
                                       "avatar": "avatar-2",
                                       "board_light_color": "#123456",
                                       "board_dark_color": "#654321"
                                   })

    assert update_response.status_code == 200

    response = client.get("/api/users/me", headers=headers)

    assert response.status_code == 200
    assert response.json()["avatar"] == "avatar-2"
    assert response.json()["board_light_color"] == "#123456"
    assert response.json()["board_dark_color"] == "#654321"


def test_update_me_rejects_invalid_board_light_color(client):
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
                            json={"board_light_color": "not-a-color"})

    assert response.status_code == 422


def test_update_me_rejects_invalid_board_dark_color(client):
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
                            json={"board_dark_color": "#123"})

    assert response.status_code == 422


def test_user_cannot_modify_another_users_settings(client):
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

    alice_login = client.post("/api/auth/login",
                              json={
                                  "username": "alice",
                                  "password": "password123"
                              })

    alice_token = alice_login.json()["access_token"]

    response = client.patch("/api/users/me",
                            headers={"Authorization": f"Bearer {alice_token}"},
                            json={
                                "avatar": "alice-avatar",
                                "board_light_color": "#111111",
                                "board_dark_color": "#222222"
                            })

    assert response.status_code == 200
    assert response.json()["username"] == "alice"

    bob_login = client.post("/api/auth/login",
                            json={
                                "username": "bob",
                                "password": "password123"
                            })

    bob_token = bob_login.json()["access_token"]

    bob_response = client.get("/api/users/me",
                              headers={"Authorization": f"Bearer {bob_token}"})

    assert bob_response.status_code == 200
    assert bob_response.json()["username"] == "bob"
    assert bob_response.json()["avatar"] == "https://shorturl.at/Jm5fo"
    assert bob_response.json()["board_light_color"] == "#E3DDC5"
    assert bob_response.json()["board_dark_color"] == "#2C5563"
