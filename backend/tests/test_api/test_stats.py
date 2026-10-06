from datetime import datetime, timezone

import chess
import chess.pgn
import pytest
from fastapi.testclient import TestClient
from backend.models.game import Game
from backend.models.user import User
from backend.services import game_service


def register(client: TestClient, db, username: str,
             email: str) -> tuple[int, str]:
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

    user = db.query(User).filter(User.username == username).first()

    return user.id, login_response.json()["access_token"]


def create_finished_game(db, white_id: int, black_id: int,
                         result: str) -> Game:
    pgn_game = chess.pgn.Game()
    pgn_game.add_variation(chess.Move.from_uci("e2e4"))
    pgn_game.headers["Result"] = result

    game = Game(white_player_id=white_id,
                black_player_id=black_id,
                status="finished",
                result=result,
                current_fen=chess.Board().fen(),
                pgn=str(pgn_game),
                finished_at=datetime.now(timezone.utc))
    db.add(game)
    db.commit()
    return game


def test_get_player_profile_without_token_returns_401(client: TestClient):
    response = client.get("/api/stats/player/Vigo")

    assert response.status_code == 401


def test_get_my_history_without_token_returns_401(client: TestClient):
    response = client.get("/api/stats/history")

    assert response.status_code == 401


@pytest.mark.parametrize("finished,expected_games,expected_elo", [
    (False, 0, 1000),
    (True, 1, 1016),
])
def test_get_player_profile_api(client: TestClient, db, finished, expected_games,
                                expected_elo):
    alice_id, alice_token = register(client, db, "alice", "alice@example.com")
    bob_id, _ = register(client, db, "bob", "bob@example.com")

    if finished:
        game = game_service.create_game(db, alice_id)
        game_service.join_game(db, game.id, bob_id)
        game_service.resign(db, game.id, bob_id)

    response = client.get("/api/stats/player/alice",
                          headers={"Authorization": f"Bearer {alice_token}"})

    assert response.status_code == 200
    body = response.json()
    history = body.pop("elo_history")
    assert len(history) == expected_games
    if finished:
        assert history == [{"date": game.finished_at.isoformat().replace("+00:00", "Z"),
                            "elo": expected_elo}]
    assert body == {
        "username": "alice",
        "elo": expected_elo,
        "games_played": expected_games,
        "wins": expected_games,
        "losses": 0,
        "draws": 0,
        "win_rate": float(expected_games)
    }


def test_get_my_history_api(client: TestClient, db):
    alice_id, alice_token = register(client, db, "alice", "alice@example.com")
    bob_id, _ = register(client, db, "bob", "bob@example.com")

    create_finished_game(db, alice_id, bob_id, "1-0")

    response = client.get("/api/stats/history",
                          headers={"Authorization": f"Bearer {alice_token}"})

    assert response.status_code == 200

    body = response.json()

    assert len(body) == 1
    assert body[0]["opponent"] == "bob"
    assert body[0]["outcome"] == "win"
    assert body[0]["moves_played"] == 1


def test_get_leaderboard_api(client: TestClient, db):
    alice_id, _ = register(client, db, "alice", "alice@example.com")
    bob_id, _ = register(client, db, "bob", "bob@example.com")

    create_finished_game(db, alice_id, bob_id, "1-0")

    response = client.get("/api/stats/leaderboard")

    assert response.status_code == 200

    body = response.json()

    assert body[0]["username"] == "alice"
    assert body[0]["elo"] == 1000
    assert body[0]["wins"] == 1


def test_logged_in_player_can_read_another_profile(client: TestClient, db):
    vigo_id, token = register(client, db, "Vigo", "vigo@example.com")
    louis_id, _ = register(client, db, "Louis", "louis@example.com")
    game = game_service.create_game(db, vigo_id)
    game_service.join_game(db, game.id, louis_id)
    game_service.resign(db, game.id, louis_id)

    response = client.get("/api/stats/player/Louis",
                          headers={"Authorization": f"Bearer {token}"})

    assert response.status_code == 200
    body = response.json()
    assert body["username"] == "Louis"
    assert body["elo"] == 984
    assert body["losses"] == 1
    assert body["elo_history"][0]["elo"] == 984
    assert "email" not in body
    assert "password_hash" not in body


def test_unknown_profile_returns_404(client: TestClient, db):
    _, token = register(client, db, "Vigo", "vigo@example.com")
    response = client.get("/api/stats/player/Unknown",
                          headers={"Authorization": f"Bearer {token}"})
    assert response.status_code == 404


def test_invalid_token_cannot_read_profile(client: TestClient):
    response = client.get("/api/stats/player/Vigo",
                          headers={"Authorization": "Bearer invalid-token"})
    assert response.status_code == 401


def test_old_stats_me_route_is_removed(client: TestClient):
    assert client.get("/api/stats/me").status_code == 404
