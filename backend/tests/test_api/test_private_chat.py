from fastapi.testclient import TestClient


def create_user(client: TestClient, username: str) -> dict[str, str]:
    response = client.post(
        "/api/users/",
        json={
            "username": username,
            "email": f"{username}@example.com",
            "password": "password123",
        },
    )
    assert response.status_code == 201

    login_response = client.post(
        "/api/auth/login",
        json={"username": username, "password": "password123"},
    )
    assert login_response.status_code == 200
    return {
        "Authorization": f"Bearer {login_response.json()['access_token']}"
    }


def find_user_id(client: TestClient, headers: dict[str, str],
                 username: str) -> int:
    response = client.get(
        f"/api/friends/search?query={username}",
        headers=headers,
    )
    assert response.status_code == 200
    return next(user["id"] for user in response.json()
                if user["username"] == username)


def make_friends(client: TestClient, first: dict[str, str],
                 second: dict[str, str]) -> tuple[int, int]:
    first_id = find_user_id(client, second, "alice")
    second_id = find_user_id(client, first, "bob")
    assert client.post(f"/api/friends/requests/{second_id}",
                       headers=first).status_code == 200
    assert client.post(f"/api/friends/requests/{first_id}/accept",
                       headers=second).status_code == 200
    return first_id, second_id


def test_private_chat_conversations_and_paginated_messages(client: TestClient):
    alice = create_user(client, "alice")
    bob = create_user(client, "bob")
    _, bob_id = make_friends(client, alice, bob)

    create_response = client.post(
        f"/api/private-chat/conversations/{bob_id}",
        headers=alice,
    )
    assert create_response.status_code == 200
    conversation = create_response.json()
    assert conversation["friend"]["username"] == "bob"

    repeated = client.post(
        f"/api/private-chat/conversations/{bob_id}",
        headers=alice,
    )
    assert repeated.status_code == 200
    assert repeated.json()["id"] == conversation["id"]

    bob_conversations = client.get(
        "/api/private-chat/conversations",
        headers=bob,
    )
    assert bob_conversations.status_code == 200
    assert bob_conversations.json()[0]["id"] == conversation["id"]
    assert bob_conversations.json()[0]["friend"]["username"] == "alice"

    messages_url = (
        f"/api/private-chat/conversations/{conversation['id']}/messages")
    first_message = client.post(
        messages_url,
        headers=alice,
        json={"message": "  hello  "},
    )
    second_message = client.post(
        messages_url,
        headers=bob,
        json={"message": "hi"},
    )
    assert first_message.status_code == 201
    assert first_message.json()["message"] == "hello"
    assert first_message.json()["sender_username"] == "alice"
    assert second_message.status_code == 201

    first_page = client.get(
        messages_url,
        headers=alice,
        params={"offset": 0, "limit": 1},
    )
    second_page = client.get(
        messages_url,
        headers=bob,
        params={"offset": 1, "limit": 1},
    )
    assert first_page.status_code == 200
    assert first_page.json()["total"] == 2
    assert [item["message"] for item in first_page.json()["items"]] == [
        "hello"
    ]
    assert [item["message"] for item in second_page.json()["items"]] == [
        "hi"
    ]


def test_private_chat_requires_friendship_and_conversation_membership(
        client: TestClient):
    alice = create_user(client, "alice")
    bob = create_user(client, "bob")
    charlie = create_user(client, "charlie")
    _, bob_id = make_friends(client, alice, bob)

    not_friends_id = find_user_id(client, alice, "charlie")
    denied_conversation = client.post(
        f"/api/private-chat/conversations/{not_friends_id}",
        headers=alice,
    )
    assert denied_conversation.status_code == 404

    conversation_id = client.post(
        f"/api/private-chat/conversations/{bob_id}",
        headers=alice,
    ).json()["id"]
    messages_url = (
        f"/api/private-chat/conversations/{conversation_id}/messages")

    assert client.get(messages_url, headers=charlie).status_code == 404
    assert client.post(
        messages_url,
        headers=charlie,
        json={"message": "not allowed"},
    ).status_code == 404
    assert client.get("/api/private-chat/conversations").status_code == 401
    assert client.post(
        messages_url,
        headers=alice,
        json={"message": "   "},
    ).status_code == 422
