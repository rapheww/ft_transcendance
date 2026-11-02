import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session
from starlette.websockets import WebSocketDisconnect

from backend.websocket import private_chat_routes


def create_user_token(client: TestClient, username: str) -> str:
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
    return response.json()["access_token"]


def find_user_id(client: TestClient, token: str, username: str) -> int:
    response = client.get(
        f"/api/friends/search?query={username}",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert response.status_code == 200
    return next(user["id"] for user in response.json()
                if user["username"] == username)


def create_friends_conversation(client: TestClient, alice_token: str,
                                bob_token: str) -> int:
    alice_id = find_user_id(client, bob_token, "alice")
    bob_id = find_user_id(client, alice_token, "bob")
    alice_headers = {"Authorization": f"Bearer {alice_token}"}
    bob_headers = {"Authorization": f"Bearer {bob_token}"}

    assert client.post(
        f"/api/friends/requests/{bob_id}",
        headers=alice_headers,
    ).status_code == 200
    assert client.post(
        f"/api/friends/requests/{alice_id}/accept",
        headers=bob_headers,
    ).status_code == 200
    response = client.post(
        f"/api/private-chat/conversations/{bob_id}",
        headers=alice_headers,
    )
    assert response.status_code == 200
    return response.json()["id"]


def test_private_chat_websocket_delivers_persisted_messages(
        client: TestClient, engine, monkeypatch):
    monkeypatch.setattr(private_chat_routes, "SessionLocal",
                        lambda: Session(engine))
    alice_token = create_user_token(client, "alice")
    bob_token = create_user_token(client, "bob")
    conversation_id = create_friends_conversation(client, alice_token,
                                                  bob_token)
    url = f"/ws/private-chat/{conversation_id}"

    with client.websocket_connect(f"{url}?token={alice_token}") as alice:
        assert alice.receive_json()["type"] == "private_chat_connected"

        with client.websocket_connect(f"{url}?token={bob_token}") as bob:
            assert bob.receive_json()["type"] == "private_chat_connected"

            alice.send_json({"type": "message", "message": "hello bob"})
            alice_message = alice.receive_json()
            bob_message = bob.receive_json()
            assert alice_message == bob_message
            assert alice_message["type"] == "private_message"
            assert alice_message["sender_username"] == "alice"
            assert alice_message["message"] == "hello bob"

            bob.send_json({"type": "message", "message": "hello alice"})
            alice_reply = alice.receive_json()
            bob_reply = bob.receive_json()
            assert alice_reply == bob_reply
            assert alice_reply["sender_username"] == "bob"

            alice.send_json({"type": "ping"})
            assert alice.receive_json() == {"type": "pong"}

            alice.send_text("{")
            invalid_json = alice.receive_json()
            assert invalid_json["code"] == "invalid_json"

            alice.send_json({"type": "message", "message": "  "})
            error = alice.receive_json()
            assert error["type"] == "error"
            assert error["code"] == "invalid_message"

    messages = client.get(
        f"/api/private-chat/conversations/{conversation_id}/messages",
        headers={"Authorization": f"Bearer {alice_token}"},
    )
    assert [message["message"] for message in messages.json()["items"]] == [
        "hello bob", "hello alice"
    ]


def test_private_chat_websocket_rejects_non_participants_and_revoked_friends(
        client: TestClient, engine, monkeypatch):
    monkeypatch.setattr(private_chat_routes, "SessionLocal",
                        lambda: Session(engine))
    alice_token = create_user_token(client, "alice")
    bob_token = create_user_token(client, "bob")
    charlie_token = create_user_token(client, "charlie")
    conversation_id = create_friends_conversation(client, alice_token,
                                                  bob_token)
    url = f"/ws/private-chat/{conversation_id}"

    with pytest.raises(WebSocketDisconnect):
        with client.websocket_connect(f"{url}?token={charlie_token}") as ws:
            ws.receive_json()

    with pytest.raises(WebSocketDisconnect):
        with client.websocket_connect(url) as ws:
            ws.receive_json()

    with client.websocket_connect(f"{url}?token={alice_token}") as alice:
        assert alice.receive_json()["type"] == "private_chat_connected"
        alice_headers = {"Authorization": f"Bearer {alice_token}"}
        bob_id = find_user_id(client, alice_token, "bob")
        removed = client.delete(f"/api/friends/{bob_id}",
                                headers=alice_headers)
        assert removed.status_code == 204

        alice.send_json({"type": "ping"})
        with pytest.raises(WebSocketDisconnect):
            alice.receive_json()
