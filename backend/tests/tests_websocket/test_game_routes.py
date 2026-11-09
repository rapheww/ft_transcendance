from sqlalchemy.orm import Session
from fastapi.testclient import TestClient
from backend.websocket import routes as game_websocket_routes


def create_user_token(client: TestClient, username: str) -> str:
    response = client.post("/api/users/",
                           json={
                               "username": username,
                               "email": f"{username}@example.com",
                               "password": "password123"
                           })

    assert response.status_code == 201
    response = client.post("/api/auth/login",
                           json={
                               "username": username,
                               "password": "password123"
                           })

    assert response.status_code == 200
    return response.json()["access_token"]


def test_websocket_reconnect_resyncs_pgn_and_move_data(client: TestClient,
                                                       engine, monkeypatch):
    monkeypatch.setattr(game_websocket_routes, "SessionLocal",
                        lambda: Session(engine))

    monkeypatch.setattr(game_websocket_routes, "start_ai_turn", lambda _: None)
    white_token = create_user_token(client, "white")
    black_token = create_user_token(client, "black")

    response = client.post("/api/games/",
                           headers={"Authorization": f"Bearer {white_token}"})
    assert response.status_code == 201
    game_id = response.json()["id"]

    response = client.post(f"/api/games/{game_id}/join",
                           headers={"Authorization": f"Bearer {black_token}"})
    assert response.status_code == 200

    with client.websocket_connect(
            f"/ws/games/{game_id}?token={white_token}") as websocket:
        initial_snapshot = websocket.receive_json()

        assert initial_snapshot["type"] == "game_connected"
        assert initial_snapshot["pgn"].rstrip().endswith("*")

        websocket.send_json({"type": "move", "from": "e2", "to": "e4"})
        messages = []

        while not any(message["type"] == "game_state" for message in messages):
            messages.append(websocket.receive_json())

        move_event = next(message for message in messages
                          if message["type"] == "move")
        state_event = next(message for message in messages
                           if message["type"] == "game_state")

        assert move_event["san"] == "e4"
        assert move_event["fen"] == state_event["fen"]

    with client.websocket_connect(
            f"/ws/games/{game_id}?token={white_token}") as websocket:
        reconnect_snapshot = websocket.receive_json()

    assert reconnect_snapshot["type"] == "game_connected"
    assert "1. e4" in reconnect_snapshot["pgn"]


def test_spectator_receives_live_moves_but_cannot_act(client: TestClient,
                                                      engine, monkeypatch):
    monkeypatch.setattr(game_websocket_routes, "SessionLocal",
                        lambda: Session(engine))
    monkeypatch.setattr(game_websocket_routes, "start_ai_turn", lambda _: None)
    white_token = create_user_token(client, "spectated_white")
    black_token = create_user_token(client, "spectated_black")
    spectator_token = create_user_token(client, "viewer")

    response = client.post("/api/games/",
                           headers={"Authorization": "Bearer " + white_token},
                           json={
                               "initial_time_seconds": 300,
                               "increment_seconds": 5
                           })
    assert response.status_code == 201
    game_id = response.json()["id"]

    response = client.post(
        f"/api/games/{game_id}/join",
        headers={"Authorization": "Bearer " + black_token})
    assert response.status_code == 200

    with client.websocket_connect(
            f"/ws/games/{game_id}?token={white_token}") as player_socket:
        player_snapshot = player_socket.receive_json()
        assert player_snapshot["role"] == "player"

        with client.websocket_connect(
                f"/ws/games/{game_id}?token={spectator_token}"
        ) as spectator_socket:
            snapshot = spectator_socket.receive_json()
            assert snapshot["type"] == "game_connected"
            assert snapshot["role"] == "spectator"
            assert snapshot["color"] is None
            assert snapshot["spectator_count"] == 1
            assert snapshot["white_time_remaining"] is not None
            assert snapshot["black_time_remaining"] is not None
            assert snapshot["increment_seconds"] == 5
            assert snapshot["last_move_at"] is not None

            with client.websocket_connect(
                    f"/ws/games/{game_id}") as guest_socket:
                guest_snapshot = guest_socket.receive_json()
                assert guest_snapshot["type"] == "game_connected"
                assert guest_snapshot["role"] == "spectator"
                assert guest_snapshot["user_id"] is None
                assert guest_snapshot["spectator_count"] == 2
                assert guest_snapshot["chat"] == []

                guest_socket.send_json({
                    "type": "move",
                    "from": "e2",
                    "to": "e4"
                })
                guest_message = guest_socket.receive_json()
                while guest_message["type"] != "error":
                    guest_message = guest_socket.receive_json()
                assert guest_message["message"] == (
                    "Spectators cannot send game actions")

            player_socket.send_json({
                "type": "move",
                "from": "e2",
                "to": "e4"
            })
            player_move = player_socket.receive_json()
            while player_move["type"] != "move":
                player_move = player_socket.receive_json()
            spectator_move = spectator_socket.receive_json()
            while spectator_move["type"] != "move":
                spectator_move = spectator_socket.receive_json()

            assert spectator_move["fen"] == player_move["fen"]
            assert spectator_move["san"] == "e4"
            assert spectator_move["white_time_remaining"] is not None
            assert spectator_move["last_move_at"] is not None

            state_update = spectator_socket.receive_json()
            while state_update["type"] != "game_state":
                state_update = spectator_socket.receive_json()

            spectator_socket.send_json({
                "type": "move",
                "from": "e7",
                "to": "e5"
            })
            rejected_action = spectator_socket.receive_json()
            assert rejected_action["type"] == "error"
            assert rejected_action["message"] == (
                "Spectators cannot send game actions")

        count_update = player_socket.receive_json()
        while count_update["type"] != "spectator_count":
            count_update = player_socket.receive_json()
        assert count_update["count"] == 0

    response = client.get(f"/api/games/{game_id}")
    assert response.status_code == 200
    assert response.json()["current_fen"] == spectator_move["fen"]


def test_websocket_chat_is_persisted_and_restored(client: TestClient, engine,
                                                   monkeypatch):
    monkeypatch.setattr(game_websocket_routes, "SessionLocal",
                        lambda: Session(engine))
    monkeypatch.setattr(game_websocket_routes, "start_ai_turn", lambda _: None)
    white_token = create_user_token(client, "chat_white")
    black_token = create_user_token(client, "chat_black")

    response = client.post("/api/games/",
                           headers={"Authorization": "Bearer " + white_token})
    assert response.status_code == 201
    game_id = response.json()["id"]

    response = client.post(
        f"/api/games/{game_id}/join",
        headers={"Authorization": "Bearer " + black_token})
    assert response.status_code == 200

    with client.websocket_connect(
            f"/ws/games/{game_id}?token={white_token}") as websocket:
        initial_snapshot = websocket.receive_json()
        assert initial_snapshot["chat"] == []

        websocket.send_json({
            "type": "chat",
            "message": "  hello again  ",
            "username": "spoofed"
        })
        chat_event = websocket.receive_json()
        while chat_event["type"] != "chat":
            chat_event = websocket.receive_json()

        assert chat_event["username"] == "chat_white"
        assert chat_event["message"] == "hello again"

    with client.websocket_connect(
            f"/ws/games/{game_id}?token={black_token}") as websocket:
        reconnect_snapshot = websocket.receive_json()

    assert reconnect_snapshot["chat"] == [{
        "id": chat_event["id"],
        "user_id": chat_event["user_id"],
        "username": "chat_white",
        "message": "hello again"
    }]
