from fastapi.testclient import TestClient


def create_user(client: TestClient, username: str, email: str) -> str:
    response = client.post("/api/users/",
                           json={
                               "username": username,
                               "email": email,
                               "password": "password123"
                           })

    assert response.status_code == 201
    login_response = client.post("/api/auth/login",
                                 json={
                                     "username": username,
                                     "password": "password123"
                                 })

    assert login_response.status_code == 200

    return login_response.json()["access_token"]


def test_create_game(client: TestClient):
    token = create_user(client, "alice", "alice@example.com")
    response = client.post("/api/games/",
                           headers={"Authorization": f"Bearer {token}"})

    assert response.status_code == 201
    body = response.json()

    assert body["id"] is not None
    assert body["white_player_id"] == 1
    assert body["black_player_id"] is None
    assert body["status"] == "waiting"
    assert body["result"] is None
    assert body["current_fen"] is not None
    assert body["pgn"].rstrip().endswith("*")
    assert body["finished_at"] is None


def test_join_game(client: TestClient):
    alice_token = create_user(client, "alice", "alice@example.com")
    bob_token = create_user(client, "bob", "bob@example.com")

    create_response = client.post(
        "/api/games/", headers={"Authorization": f"Bearer {alice_token}"})
    assert create_response.status_code == 201

    game = create_response.json()
    game_id = game["id"]

    join_response = client.post(
        f"/api/games/{game_id}/join",
        headers={"Authorization": f"Bearer {bob_token}"})

    assert join_response.status_code == 200
    body = join_response.json()

    assert body["id"] == game_id
    assert body["white_player_id"] == game["white_player_id"]
    assert body["black_player_id"] is not None
    assert body["black_player_id"] != body["white_player_id"]
    assert body["status"] == "active"
    assert body["result"] is None


def test_get_game(client: TestClient):
    token = create_user(client, "alice", "alice@example.com")
    create_response = client.post("/api/games/",
                                  headers={"Authorization": f"Bearer {token}"})

    game = create_response.json()
    response = client.get(f"/api/games/{game['id']}")

    assert response.status_code == 200
    assert response.json() == game


def test_get_missing_game_returns_404(client: TestClient):
    response = client.get("/api/games/999999")

    assert response.status_code == 404
    assert response.json() == {"detail": "Game not found"}


def test_create_game_without_token_returns_401(client: TestClient):
    response = client.post("/api/games/")

    assert response.status_code == 401


def test_join_game_without_token_returns_401(client: TestClient):
    response = client.post("/api/games/1/join")

    assert response.status_code == 401


def test_creator_cannot_join_own_game(client: TestClient):
    token = create_user(client, "alice", "alice@example.com")
    create_response = client.post("/api/games/",
                                  headers={"Authorization": f"Bearer {token}"})

    game_id = create_response.json()["id"]
    response = client.post(f"/api/games/{game_id}/join",
                           headers={"Authorization": f"Bearer {token}"})

    assert response.status_code == 409
    assert response.json() == {"detail": "Cannot play against yourself"}


def test_join_active_game_returns_409(client: TestClient):
    alice_token = create_user(client, "alice", "alice@example.com")
    bob_token = create_user(client, "bob", "bob@example.com")

    charlie_token = create_user(client, "charlie", "charlie@example.com")
    create_response = client.post(
        "/api/games/", headers={"Authorization": f"Bearer {alice_token}"})

    game_id = create_response.json()["id"]
    first_join = client.post(f"/api/games/{game_id}/join",
                             headers={"Authorization": f"Bearer {bob_token}"})

    assert first_join.status_code == 200
    second_join = client.post(
        f"/api/games/{game_id}/join",
        headers={"Authorization": f"Bearer {charlie_token}"})

    assert second_join.status_code == 409
    assert second_join.json() == {"detail": "Game is not joinable"}


def test_make_move(client: TestClient):
    alice_token = create_user(client, "alice", "alice@example.com")
    bob_token = create_user(client, "bob", "bob@example.com")

    create_response = client.post(
        "/api/games/", headers={"Authorization": f"Bearer {alice_token}"})

    game_id = create_response.json()["id"]
    join_response = client.post(
        f"/api/games/{game_id}/join",
        headers={"Authorization": f"Bearer {bob_token}"})

    assert join_response.status_code == 200
    response = client.post(f"/api/games/{game_id}/move",
                           json={"move": "e2e4"},
                           headers={"Authorization": f"Bearer {alice_token}"})

    assert response.status_code == 200
    body = response.json()

    assert body["id"] == game_id
    assert body["status"] == "active"
    assert body["result"] is None
    assert body["current_fen"] is not None
    assert "1. e4" in body["pgn"]


def test_make_move_without_token_returns_401(client: TestClient):
    response = client.post("/api/games/1/move", json={"move": "e2e4"})

    assert response.status_code == 401


def test_make_move_on_missing_game_returns_404(client: TestClient):
    token = create_user(client, "alice", "alice@example.com")
    response = client.post("/api/games/999999/move",
                           json={"move": "e2e4"},
                           headers={"Authorization": f"Bearer {token}"})

    assert response.status_code == 404
    assert response.json() == {"detail": "Game not found"}


def test_make_move_on_inactive_game_returns_409(client: TestClient):
    token = create_user(client, "alice", "alice@example.com")
    create_response = client.post("/api/games/",
                                  headers={"Authorization": f"Bearer {token}"})

    game_id = create_response.json()["id"]
    response = client.post(f"/api/games/{game_id}/move",
                           json={"move": "e2e4"},
                           headers={"Authorization": f"Bearer {token}"})

    assert response.status_code == 409
    assert response.json() == {"detail": "Game is not active"}


def test_make_move_as_non_player_returns_409(client: TestClient):
    alice_token = create_user(client, "alice", "alice@example.com")
    bob_token = create_user(client, "bob", "bob@example.com")
    charlie_token = create_user(client, "charlie", "charlie@example.com")

    create_response = client.post(
        "/api/games/", headers={"Authorization": f"Bearer {alice_token}"})

    game_id = create_response.json()["id"]
    join_response = client.post(
        f"/api/games/{game_id}/join",
        headers={"Authorization": f"Bearer {bob_token}"})

    assert join_response.status_code == 200
    response = client.post(
        f"/api/games/{game_id}/move",
        json={"move": "e2e4"},
        headers={"Authorization": f"Bearer {charlie_token}"})

    assert response.status_code == 409
    assert response.json() == {"detail": "User is not a player in this game"}


def test_make_move_out_of_turn_returns_409(client: TestClient):
    alice_token = create_user(client, "alice", "alice@example.com")
    bob_token = create_user(client, "bob", "bob@example.com")

    create_response = client.post(
        "/api/games/", headers={"Authorization": f"Bearer {alice_token}"})
    game_id = create_response.json()["id"]

    join_response = client.post(
        f"/api/games/{game_id}/join",
        headers={"Authorization": f"Bearer {bob_token}"})

    assert join_response.status_code == 200
    response = client.post(f"/api/games/{game_id}/move",
                           json={"move": "e7e5"},
                           headers={"Authorization": f"Bearer {bob_token}"})

    assert response.status_code == 409
    assert response.json() == {"detail": "It is not your turn"}


def test_make_illegal_move_returns_409(client: TestClient):
    alice_token = create_user(client, "alice", "alice@example.com")
    bob_token = create_user(client, "bob", "bob@example.com")

    create_response = client.post(
        "/api/games/", headers={"Authorization": f"Bearer {alice_token}"})

    game_id = create_response.json()["id"]
    join_response = client.post(
        f"/api/games/{game_id}/join",
        headers={"Authorization": f"Bearer {bob_token}"})

    assert join_response.status_code == 200
    response = client.post(f"/api/games/{game_id}/move",
                           json={"move": "e2e5"},
                           headers={"Authorization": f"Bearer {alice_token}"})

    assert response.status_code == 409
    assert response.json() == {"detail": "Illegal move"}


def test_player_can_resign_game(client: TestClient):
    alice_token = create_user(client, "alice", "alice@example.com")
    bob_token = create_user(client, "bob", "bob@example.com")

    create_response = client.post(
        "/api/games/", headers={"Authorization": f"Bearer {alice_token}"})

    game_id = create_response.json()["id"]
    join_response = client.post(
        f"/api/games/{game_id}/join",
        headers={"Authorization": f"Bearer {bob_token}"})

    assert join_response.status_code == 200

    response = client.post(f"/api/games/{game_id}/resign",
                           headers={"Authorization": f"Bearer {alice_token}"})

    assert response.status_code == 200

    body = response.json()

    assert body["status"] == "finished"
    assert body["result"] == "0-1"
    assert body["finished_at"] is not None


def test_black_resigning_gives_white_win(client: TestClient):
    alice_token = create_user(client, "alice", "alice@example.com")
    bob_token = create_user(client, "bob", "bob@example.com")

    create_response = client.post(
        "/api/games/", headers={"Authorization": f"Bearer {alice_token}"})

    game_id = create_response.json()["id"]
    client.post(f"/api/games/{game_id}/join",
                headers={"Authorization": f"Bearer {bob_token}"})

    response = client.post(f"/api/games/{game_id}/resign",
                           headers={"Authorization": f"Bearer {bob_token}"})

    assert response.status_code == 200
    assert response.json()["result"] == "1-0"


def test_resign_without_token_returns_401(client: TestClient):
    response = client.post("/api/games/1/resign")

    assert response.status_code == 401


def test_non_player_cannot_resign(client: TestClient):
    alice_token = create_user(client, "alice", "alice@example.com")
    bob_token = create_user(client, "bob", "bob@example.com")
    charlie_token = create_user(client, "charlie", "charlie@example.com")

    create_response = client.post(
        "/api/games/", headers={"Authorization": f"Bearer {alice_token}"})

    game_id = create_response.json()["id"]
    client.post(f"/api/games/{game_id}/join",
                headers={"Authorization": f"Bearer {bob_token}"})

    response = client.post(
        f"/api/games/{game_id}/resign",
        headers={"Authorization": f"Bearer {charlie_token}"})

    assert response.status_code == 409
    assert response.json() == {"detail": "User is not a player in this game"}


def test_player_can_offer_draw(client: TestClient):
    alice_token = create_user(client, "alice", "alice@example.com")
    bob_token = create_user(client, "bob", "bob@example.com")

    create_response = client.post(
        "/api/games/", headers={"Authorization": f"Bearer {alice_token}"})
    game_id = create_response.json()["id"]

    join_response = client.post(
        f"/api/games/{game_id}/join",
        headers={"Authorization": f"Bearer {bob_token}"})
    assert join_response.status_code == 200

    response = client.post(f"/api/games/{game_id}/draw-offer",
                           headers={"Authorization": f"Bearer {alice_token}"})

    assert response.status_code == 200
    body = response.json()

    assert body["status"] == "active"
    assert body["result"] is None
    assert body["draw_offer_by"] == 1


def test_offer_draw_without_token_returns_401(client: TestClient):
    response = client.post("/api/games/1/draw-offer")

    assert response.status_code == 401


def test_non_player_cannot_offer_draw(client: TestClient):
    alice_token = create_user(client, "alice", "alice@example.com")
    bob_token = create_user(client, "bob", "bob@example.com")
    charlie_token = create_user(client, "charlie", "charlie@example.com")

    create_response = client.post(
        "/api/games/", headers={"Authorization": f"Bearer {alice_token}"})
    game_id = create_response.json()["id"]

    client.post(f"/api/games/{game_id}/join",
                headers={"Authorization": f"Bearer {bob_token}"})

    response = client.post(
        f"/api/games/{game_id}/draw-offer",
        headers={"Authorization": f"Bearer {charlie_token}"})

    assert response.status_code == 409
    assert response.json() == {"detail": "User is not a player in this game"}


def test_player_can_accept_draw_offer(client: TestClient):
    alice_token = create_user(client, "alice", "alice@example.com")
    bob_token = create_user(client, "bob", "bob@example.com")

    create_response = client.post(
        "/api/games/", headers={"Authorization": f"Bearer {alice_token}"})
    game_id = create_response.json()["id"]

    client.post(f"/api/games/{game_id}/join",
                headers={"Authorization": f"Bearer {bob_token}"})

    offer_response = client.post(
        f"/api/games/{game_id}/draw-offer",
        headers={"Authorization": f"Bearer {alice_token}"})
    assert offer_response.status_code == 200

    response = client.post(f"/api/games/{game_id}/draw-offer/accept",
                           headers={"Authorization": f"Bearer {bob_token}"})

    assert response.status_code == 200
    body = response.json()

    assert body["status"] == "finished"
    assert body["result"] == "1/2-1/2"
    assert body["draw_offer_by"] is None
    assert body["finished_at"] is not None


def test_player_can_decline_draw_offer(client: TestClient):
    alice_token = create_user(client, "alice", "alice@example.com")
    bob_token = create_user(client, "bob", "bob@example.com")

    create_response = client.post(
        "/api/games/", headers={"Authorization": f"Bearer {alice_token}"})
    game_id = create_response.json()["id"]

    client.post(f"/api/games/{game_id}/join",
                headers={"Authorization": f"Bearer {bob_token}"})

    client.post(f"/api/games/{game_id}/draw-offer",
                headers={"Authorization": f"Bearer {alice_token}"})

    response = client.post(f"/api/games/{game_id}/draw-offer/decline",
                           headers={"Authorization": f"Bearer {bob_token}"})

    assert response.status_code == 200
    body = response.json()

    assert body["status"] == "active"
    assert body["result"] is None
    assert body["draw_offer_by"] is None


def test_accept_draw_without_offer_returns_409(client: TestClient):
    alice_token = create_user(client, "alice", "alice@example.com")
    bob_token = create_user(client, "bob", "bob@example.com")

    create_response = client.post(
        "/api/games/", headers={"Authorization": f"Bearer {alice_token}"})
    game_id = create_response.json()["id"]

    client.post(f"/api/games/{game_id}/join",
                headers={"Authorization": f"Bearer {bob_token}"})

    response = client.post(f"/api/games/{game_id}/draw-offer/accept",
                           headers={"Authorization": f"Bearer {bob_token}"})

    assert response.status_code == 409
    assert response.json() == {"detail": "There is no pending draw offer"}


def test_decline_draw_without_offer_returns_409(client: TestClient):
    alice_token = create_user(client, "alice", "alice@example.com")
    bob_token = create_user(client, "bob", "bob@example.com")

    create_response = client.post(
        "/api/games/", headers={"Authorization": f"Bearer {alice_token}"})
    game_id = create_response.json()["id"]

    client.post(f"/api/games/{game_id}/join",
                headers={"Authorization": f"Bearer {bob_token}"})

    response = client.post(f"/api/games/{game_id}/draw-offer/decline",
                           headers={"Authorization": f"Bearer {bob_token}"})

    assert response.status_code == 409
    assert response.json() == {"detail": "There is no pending draw offer"}


def test_player_cannot_accept_own_draw_offer(client: TestClient):
    alice_token = create_user(client, "alice", "alice@example.com")
    bob_token = create_user(client, "bob", "bob@example.com")

    create_response = client.post(
        "/api/games/", headers={"Authorization": f"Bearer {alice_token}"})
    game_id = create_response.json()["id"]

    client.post(f"/api/games/{game_id}/join",
                headers={"Authorization": f"Bearer {bob_token}"})

    client.post(f"/api/games/{game_id}/draw-offer",
                headers={"Authorization": f"Bearer {alice_token}"})

    response = client.post(f"/api/games/{game_id}/draw-offer/accept",
                           headers={"Authorization": f"Bearer {alice_token}"})

    assert response.status_code == 409
    assert response.json() == {"detail": "Cannot accept your own draw offer"}

