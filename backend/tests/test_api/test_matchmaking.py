import pytest
from fastapi.testclient import TestClient
from backend.services import game_service, matchmaking_service


def create_user(
    client: TestClient,
    username: str = "alice",
    email: str = "alice@example.com",
) -> dict:
    response = client.post(
        "/api/users/",
        json={
            "username": username,
            "email": email,
            "password": "password123",
        },
    )

    assert response.status_code == 201

    login_response = client.post(
        "/api/auth/login",
        json={
            "username": username,
            "password": "password123",
        },
    )

    assert login_response.status_code == 200

    token = login_response.json()["access_token"]

    return {"Authorization": f"Bearer {token}"}


def test_join_matchmaking(client):
    headers = create_user(client)

    response = client.post(
        "/api/matchmaking/join",
        headers=headers,
        json={
            "initial_time_seconds": 600,
            "increment_seconds": 5,
        },
    )

    assert response.status_code == 201

    data = response.json()
    assert data["id"] is not None
    assert data["user_id"] is not None
    assert data["initial_time_seconds"] == 600
    assert data["increment_seconds"] == 5
    assert data["created_at"] is not None


def test_join_matchmaking_untimed(client):
    headers = create_user(client)

    response = client.post(
        "/api/matchmaking/join",
        headers=headers,
        json={
            "initial_time_seconds": None,
            "increment_seconds": 0,
        },
    )

    assert response.status_code == 201

    data = response.json()
    assert data["initial_time_seconds"] is None
    assert data["increment_seconds"] == 0


def test_join_matchmaking_twice(client):
    headers = create_user(client)

    response = client.post(
        "/api/matchmaking/join",
        headers=headers,
        json={
            "initial_time_seconds": 600,
            "increment_seconds": 5,
        },
    )

    assert response.status_code == 201

    response = client.post(
        "/api/matchmaking/join",
        headers=headers,
        json={
            "initial_time_seconds": 300,
            "increment_seconds": 0,
        },
    )

    assert response.status_code == 409


def test_leave_matchmaking(client):
    headers = create_user(client)

    response = client.post(
        "/api/matchmaking/join",
        headers=headers,
        json={
            "initial_time_seconds": 600,
            "increment_seconds": 5,
        },
    )

    assert response.status_code == 201

    response = client.delete(
        "/api/matchmaking/leave",
        headers=headers,
    )

    assert response.status_code == 204


def test_leave_matchmaking_when_not_queued(client):
    headers = create_user(client)

    response = client.delete(
        "/api/matchmaking/leave",
        headers=headers,
    )

    assert response.status_code == 404


def test_matchmaking_status_when_queued(client):
    headers = create_user(client)

    response = client.post(
        "/api/matchmaking/join",
        headers=headers,
        json={
            "initial_time_seconds": 600,
            "increment_seconds": 5,
        },
    )

    assert response.status_code == 201

    response = client.get(
        "/api/matchmaking/status",
        headers=headers,
    )

    assert response.status_code == 200

    data = response.json()
    assert data["initial_time_seconds"] == 600
    assert data["increment_seconds"] == 5


def test_matchmaking_status_when_not_queued(client):
    headers = create_user(client)

    response = client.get(
        "/api/matchmaking/status",
        headers=headers,
    )

    assert response.status_code == 200
    assert response.json() is None


@pytest.mark.parametrize(
    "payload",
    [
        {
            "initial_time_seconds": 0,
            "increment_seconds": 0,
        },
        {
            "initial_time_seconds": -1,
            "increment_seconds": 0,
        },
        {
            "initial_time_seconds": 600,
            "increment_seconds": -1,
        },
    ],
)
def test_join_matchmaking_rejects_invalid_time_control(client, payload):
    headers = create_user(client)

    response = client.post(
        "/api/matchmaking/join",
        headers=headers,
        json=payload,
    )

    assert response.status_code == 422


def test_join_matchmaking_requires_authentication(client):
    response = client.post("/api/matchmaking/join",
                           json={
                               "initial_time_seconds": 600,
                               "increment_seconds": 5
                           })

    assert response.status_code == 401


def test_leave_matchmaking_requires_authentication(client):
    response = client.delete("/api/matchmaking/leave")

    assert response.status_code == 401


def test_matchmaking_status_requires_authentication(client):
    response = client.get("/api/matchmaking/status")

    assert response.status_code == 401


def test_matchmaking_two_players_are_matched(client):
    player1_headers = create_user(client, "alice", "alice@example.com")

    player2_headers = create_user(client, "bob", "bob@example.com")

    response = client.post("/api/matchmaking/join",
                           headers=player1_headers,
                           json={
                               "initial_time_seconds": 600,
                               "increment_seconds": 5
                           })

    assert response.status_code == 201
    assert response.json()["status"] == "waiting"

    response = client.post("/api/matchmaking/join",
                           headers=player2_headers,
                           json={
                               "initial_time_seconds": 600,
                               "increment_seconds": 5
                           })

    assert response.status_code == 201
    data = response.json()

    assert data["status"] == "matched"
    assert data["game_id"] is not None


def test_first_player_sees_match_after_second_player_joins(client):
    player1_headers = create_user(client, "alice", "alice@example.com")
    player2_headers = create_user(client, "bob", "bob@example.com")

    response = client.post("/api/matchmaking/join",
                           headers=player1_headers,
                           json={
                               "initial_time_seconds": 600,
                               "increment_seconds": 5
                           })

    assert response.status_code == 201
    assert response.json()["status"] == "waiting"

    response = client.post("/api/matchmaking/join",
                           headers=player2_headers,
                           json={
                               "initial_time_seconds": 600,
                               "increment_seconds": 5
                           })

    assert response.status_code == 201
    game_id = response.json()["game_id"]

    response = client.get("/api/matchmaking/status", headers=player1_headers)
    assert response.status_code == 200
    data = response.json()

    assert data["status"] == "matched"
    assert data["game_id"] == game_id


def test_matchmaking_status_retries_match_for_queued_players(client,
                                                             monkeypatch):
    player1_headers = create_user(client, "alice", "alice@example.com")
    player2_headers = create_user(client, "bob", "bob@example.com")
    find_match = matchmaking_service.find_match
    monkeypatch.setattr(matchmaking_service, "find_match",
                        lambda *args, **kwargs: None)

    for headers in (player1_headers, player2_headers):
        response = client.post(
            "/api/matchmaking/join",
            headers=headers,
            json={
                "initial_time_seconds": 600,
                "increment_seconds": 5
            })
        assert response.status_code == 201
        assert response.json()["status"] == "waiting"

    monkeypatch.setattr(matchmaking_service, "find_match", find_match)
    # SQLite drops timezone info from queue timestamps; this test focuses on
    # retrying the match from status rather than rating-range expansion.
    monkeypatch.setattr(matchmaking_service, "get_rating_range",
                        lambda *args: 50)
    response = client.get("/api/matchmaking/status", headers=player1_headers)
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "matched"
    assert data["game_id"] is not None

    response = client.get("/api/matchmaking/status", headers=player2_headers)
    assert response.status_code == 200
    assert response.json()["game_id"] == data["game_id"]


def test_matched_players_are_removed_from_queue(client):
    player1_headers = create_user(client, "alice", "alice@example.com")
    player2_headers = create_user(client, "bob", "bob@example.com")

    client.post("/api/matchmaking/join",
                headers=player1_headers,
                json={
                    "initial_time_seconds": 600,
                    "increment_seconds": 5
                })

    client.post("/api/matchmaking/join",
                headers=player2_headers,
                json={
                    "initial_time_seconds": 600,
                    "increment_seconds": 5
                })

    response = client.get("/api/matchmaking/status", headers=player1_headers)
    assert response.json()["status"] == "matched"

    response = client.get("/api/matchmaking/status", headers=player2_headers)
    assert response.json()["status"] == "matched"


def test_api_does_not_match_different_time_controls(client):
    player1_headers = create_user(client, "alice", "alice@example.com")
    player2_headers = create_user(client, "bob", "bob@example.com")

    response = client.post("/api/matchmaking/join",
                           headers=player1_headers,
                           json={
                               "initial_time_seconds": 600,
                               "increment_seconds": 5
                           })

    assert response.status_code == 201
    assert response.json()["status"] == "waiting"

    response = client.post("/api/matchmaking/join",
                           headers=player2_headers,
                           json={
                               "initial_time_seconds": 300,
                               "increment_seconds": 0
                           })

    assert response.status_code == 201
    assert response.json()["status"] == "waiting"


def test_untimed_players_are_matched(client):
    player1_headers = create_user(client, "alice", "alice@example.com")
    player2_headers = create_user(client, "bob", "bob@example.com")

    response = client.post("/api/matchmaking/join",
                           headers=player1_headers,
                           json={
                               "initial_time_seconds": None,
                               "increment_seconds": 0
                           })

    assert response.status_code == 201
    assert response.json()["status"] == "waiting"

    response = client.post("/api/matchmaking/join",
                           headers=player2_headers,
                           json={
                               "initial_time_seconds": None,
                               "increment_seconds": 0
                           })

    assert response.status_code == 201
    assert response.json()["status"] == "matched"
    assert response.json()["game_id"] is not None


def test_matchmaking_creates_correct_game(client, db):
    player1_headers = create_user(client, "alice", "alice@example.com")
    player2_headers = create_user(client, "bob", "bob@example.com")

    client.post("/api/matchmaking/join",
                headers=player1_headers,
                json={
                    "initial_time_seconds": 600,
                    "increment_seconds": 5
                })

    response = client.post("/api/matchmaking/join",
                           headers=player2_headers,
                           json={
                               "initial_time_seconds": 600,
                               "increment_seconds": 5
                           })

    game_id = response.json()["game_id"]
    game = game_service.get_game(db, game_id)

    assert game.white_player_id in (1, 2)
    assert game.black_player_id in (1, 2)
    assert game.white_player_id != game.black_player_id
    assert game.status == "active"
    assert game.opponent_type == "human"
    assert game.initial_time_seconds == 600
    assert game.increment_seconds == 5
