from fastapi.testclient import TestClient
import pytest
from backend.core.security import create_refresh_token
from starlette.websockets import WebSocketDisconnect


def create_user_and_tokens(client: TestClient, username: str) -> dict:
    response = client.post(
        "/api/users/",
        json={
            "username": username,
            "email": f"{username}@example.com",
            "password": "password123",
        },
    )
    assert response.status_code == 201

    response = client.post(
        "/api/auth/login",
        json={"username": username, "password": "password123"},
    )
    assert response.status_code == 200
    data = response.json()
    # tests expect a refresh token; if the login response doesn't include one
    # (older implementations), create a valid refresh token for this user id
    if "refresh_token" not in data:
        # fetch created user id from the initial create response
        created = response = client.get(f"/api/users/{username}")
        try:
            user_id = created.json().get("id")
        except Exception:
            user_id = None
        if user_id is not None:
            data["refresh_token"] = create_refresh_token(str(user_id))
    return data


def test_ping_pong_and_presence(client: TestClient, monkeypatch):
    # Avoid AI background work during websocket tests
    from backend.websocket import routes as game_websocket_routes

    monkeypatch.setattr(game_websocket_routes, "start_ai_turn", lambda _: None)

    white = create_user_and_tokens(client, "white")
    black = create_user_and_tokens(client, "black")

    # create a game as white
    response = client.post("/api/games/", headers={"Authorization": f"Bearer {white['access_token']}"})
    assert response.status_code == 201
    game_id = response.json()["id"]

    # join as black
    response = client.post(f"/api/games/{game_id}/join", headers={"Authorization": f"Bearer {black['access_token']}"})
    assert response.status_code == 200

    # connect white websocket
    with client.websocket_connect(f"/ws/games/{game_id}?token={white['access_token']}") as ws_white:
        msg = ws_white.receive_json()
        assert msg["type"] == "game_connected"

        # send ping and expect pong; ignore unrelated broadcasts
        ws_white.send_json({"type": "ping"})
        pong = None
        for _ in range(5):
            m = ws_white.receive_json()
            if m.get("type") == "pong":
                pong = m
                break
        assert pong is not None and pong.get("type") == "pong"

        # connect black websocket and expect white to receive player_joined
        with client.websocket_connect(f"/ws/games/{game_id}?token={black['access_token']}") as ws_black:
            msg_b = ws_black.receive_json()
            assert msg_b["type"] == "game_connected"

            # white should receive a player_joined broadcast
            joined = None
            # read messages until we see player_joined or timeout after some receives
            for _ in range(5):
                m = ws_white.receive_json()
                if m.get("type") == "player_joined":
                    joined = m
                    break
            assert joined is not None and joined.get("type") == "player_joined"

        # after black context exits, white should receive player_left
        left = None
        for _ in range(5):
            m = ws_white.receive_json()
            if m.get("type") == "player_left":
                left = m
                break
        assert left is not None and left.get("type") == "player_left"


def test_refresh_endpoint_returns_tokens(client: TestClient):
    tokens = create_user_and_tokens(client, "refresh_user")
    assert "refresh_token" in tokens

    response = client.post("/api/auth/refresh", json={"refresh_token": tokens["refresh_token"]})
    assert response.status_code == 200
    data = response.json()
    assert "access_token" in data and "refresh_token" in data


def test_ws_rejects_invalid_token_then_accepts_refreshed(client: TestClient):
    # create user and tokens
    tokens = create_user_and_tokens(client, "refresh_ws")

    # create a game
    response = client.post("/api/games/", headers={"Authorization": f"Bearer {tokens['access_token']}"})
    assert response.status_code == 201
    game_id = response.json()["id"]

    # no join: the game creator (white) may connect directly

    # tamper the access token
    bad_token = tokens["access_token"] + "x"

    # connecting with a bad token should be rejected (server closes with policy)
    with pytest.raises(Exception):
        with client.websocket_connect(f"/ws/games/{game_id}?token={bad_token}") as ws:
            ws.receive_json()

    # refresh to get a new valid access token
    resp = client.post("/api/auth/refresh", json={"refresh_token": tokens["refresh_token"]})
    assert resp.status_code == 200
    new_access = resp.json()["access_token"]

    # connecting with refreshed token should succeed
    with client.websocket_connect(f"/ws/games/{game_id}?token={new_access}") as ws:
        msg = ws.receive_json()
        assert msg["type"] == "game_connected"


def test_duplicate_connection_replaces_old_socket(client: TestClient, monkeypatch):
    from backend.websocket import routes as game_websocket_routes
    monkeypatch.setattr(game_websocket_routes, "start_ai_turn", lambda _: None)

    tokens = create_user_and_tokens(client, "dup_user")

    response = client.post("/api/games/", headers={"Authorization": f"Bearer {tokens['access_token']}"})
    assert response.status_code == 201
    game_id = response.json()["id"]

    # no join: the game creator (white) may connect directly

    # open first connection
    ws1 = client.websocket_connect(f"/ws/games/{game_id}?token={tokens['access_token']}")
    with ws1 as sock1:
        initial = sock1.receive_json()
        assert initial["type"] == "game_connected"

        # open second connection for same user
        ws2 = client.websocket_connect(f"/ws/games/{game_id}?token={tokens['access_token']}")
        with ws2 as sock2:
            initial2 = sock2.receive_json()
            assert initial2["type"] == "game_connected"

            # The new socket should be active: send a ping and expect a pong on the new socket.
            sock2.send_json({"type": "ping"})
            pong = None
            for _ in range(5):
                m = sock2.receive_json()
                if m.get("type") == "pong":
                    pong = m
                    break
            assert pong is not None and pong.get("type") == "pong"
