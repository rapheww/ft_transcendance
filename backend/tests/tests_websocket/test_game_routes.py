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
