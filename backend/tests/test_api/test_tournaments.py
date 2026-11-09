from fastapi.testclient import TestClient


def register_user(client: TestClient, username: str, email: str) -> str:
    client.post("/api/users/",
                json={
                    "username": username,
                    "email": email,
                    "password": "password123"
                })

    response = client.post("/api/auth/login",
                           json={
                               "username": username,
                               "password": "password123"
                           })

    return response.json()["access_token"]


def auth(token: str) -> dict:
    return {"Authorization": f"Bearer {token}"}


def test_create_tournament_without_token_returns_401(client: TestClient):
    response = client.post("/api/tournaments/")

    assert response.status_code == 401


def test_create_and_register(client: TestClient):
    alice_token = register_user(client, "alice", "alice@example.com")
    bob_token = register_user(client, "bob", "bob@example.com")

    create_response = client.post("/api/tournaments/",
                                  headers=auth(alice_token))
    assert create_response.status_code == 201

    tournament_id = create_response.json()["id"]

    register_response = client.post(
        f"/api/tournaments/{tournament_id}/register", headers=auth(bob_token))

    assert register_response.status_code == 200
    assert register_response.json()["participants"] == ["alice", "bob"]


def test_register_twice_returns_409(client: TestClient):
    alice_token = register_user(client, "alice", "alice@example.com")

    tournament_id = client.post("/api/tournaments/",
                                headers=auth(alice_token)).json()["id"]

    response = client.post(f"/api/tournaments/{tournament_id}/register",
                           headers=auth(alice_token))

    assert response.status_code == 409


def test_start_with_wrong_participant_count_returns_409(client: TestClient):
    alice_token = register_user(client, "alice", "alice@example.com")

    tournament_id = client.post("/api/tournaments/",
                                headers=auth(alice_token)).json()["id"]

    response = client.post(f"/api/tournaments/{tournament_id}/start",
                           headers=auth(alice_token))

    assert response.status_code == 409


def test_start_creates_bracket(client: TestClient):
    tokens = [
        register_user(client, f"player{i}", f"player{i}@example.com")
        for i in range(4)
    ]

    tournament_id = client.post("/api/tournaments/",
                                headers=auth(tokens[0])).json()["id"]

    for token in tokens[1:]:
        client.post(f"/api/tournaments/{tournament_id}/register",
                    headers=auth(token))

    response = client.post(f"/api/tournaments/{tournament_id}/start",
                           headers=auth(tokens[0]))

    assert response.status_code == 200

    body = response.json()

    assert body["status"] == "countdown"
    assert len(body["matches"]) == 3
    assert all(m["game_id"] is None for m in body["matches"])


def test_get_missing_tournament_returns_404(client: TestClient):
    response = client.get("/api/tournaments/999999")

    assert response.status_code == 404


def test_list_and_my_tournament(client):
    token = register_user(client, "vigo", "vigo@example.com")
    assert client.get("/api/tournaments/me",
                      headers=auth(token)).json() is None
    created = client.post("/api/tournaments/", headers=auth(token)).json()
    listed = client.get("/api/tournaments/", headers=auth(token)).json()
    assert [t["id"] for t in listed] == [created["id"]]
    assert client.get("/api/tournaments/me",
                      headers=auth(token)).json()["id"] == created["id"]
    assert client.post("/api/tournaments/",
                       headers=auth(token)).status_code == 409


def test_only_creator_can_start(client):
    owner = register_user(client, "vigo", "vigo@example.com")
    guest = register_user(client, "louis", "louis@example.com")
    tid = client.post("/api/tournaments/", headers=auth(owner)).json()["id"]
    client.post(f"/api/tournaments/{tid}/register", headers=auth(guest))
    assert client.post(f"/api/tournaments/{tid}/start",
                       headers=auth(guest)).status_code == 403


def test_tournament_participant_cannot_enter_matchmaking(client):
    token = register_user(client, "vigo", "vigo@example.com")
    client.post("/api/tournaments/", headers=auth(token))
    response = client.post("/api/matchmaking/join",
                           headers=auth(token),
                           json={
                               "initial_time_seconds": 600,
                               "increment_seconds": 0
                           })
    assert response.status_code == 409


def test_list_requires_authentication(client):
    assert client.get("/api/tournaments/").status_code == 401
    assert client.get("/api/tournaments/me").status_code == 401
