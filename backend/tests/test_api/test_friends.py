from fastapi.testclient import TestClient
from datetime import datetime, timedelta, timezone

from backend.models.user import User


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


def test_friend_request_lifecycle(client: TestClient):
    alice = create_user(client, "alice")
    bob = create_user(client, "bob")

    search_response = client.get("/api/friends/search?query=bo",
                                 headers=alice)
    assert search_response.status_code == 200
    bob_id = search_response.json()[0]["id"]
    assert search_response.json()[0]["username"] == "bob"
    assert search_response.json()[0]["online"] is False

    send_response = client.post(f"/api/friends/requests/{bob_id}",
                                headers=alice)
    assert send_response.status_code == 200
    assert send_response.json()["status"] == "pending"

    duplicate_response = client.post(f"/api/friends/requests/{bob_id}",
                                     headers=alice)
    assert duplicate_response.status_code == 409

    assert client.get("/api/friends/requests/outgoing",
                      headers=alice).json()[0]["username"] == "bob"
    assert client.get("/api/friends/requests/incoming",
                      headers=bob).json()[0]["username"] == "alice"

    alice_id = client.get("/api/friends/search?query=alice",
                          headers=bob).json()[0]["id"]
    accept_response = client.post(f"/api/friends/requests/{alice_id}/accept",
                                  headers=bob)
    assert accept_response.status_code == 200
    assert accept_response.json()["username"] == "alice"
    assert client.get("/api/friends/", headers=alice).json()[0][
        "username"] == "bob"
    assert client.get("/api/friends/requests/incoming",
                      headers=bob).json() == []

    assert client.post("/api/users/me/heartbeat",
                       headers=bob).status_code == 200
    search_response = client.get("/api/friends/search?query=bob",
                                 headers=alice)
    assert search_response.json()[0]["online"] is True

    remove_response = client.delete(f"/api/friends/{bob_id}", headers=alice)
    assert remove_response.status_code == 204
    assert client.get("/api/friends/", headers=alice).json() == []


def test_rejected_friend_request_can_be_resent(client: TestClient):
    alice = create_user(client, "alice")
    bob = create_user(client, "bob")
    alice_id = client.get("/api/friends/search?query=alice",
                          headers=bob).json()[0]["id"]
    bob_id = client.get("/api/friends/search?query=bob",
                        headers=alice).json()[0]["id"]

    send_response = client.post(f"/api/friends/requests/{bob_id}",
                                headers=alice)
    assert send_response.status_code == 200
    assert send_response.json()["status"] == "pending"

    reject_response = client.post(
        f"/api/friends/requests/{alice_id}/reject", headers=bob)
    assert reject_response.status_code == 200

    resend_response = client.post(f"/api/friends/requests/{bob_id}",
                                  headers=alice)
    assert resend_response.status_code == 200
    assert resend_response.json()["status"] == "pending"
    assert len(client.get("/api/friends/requests/incoming",
                          headers=bob).json()) == 1


def test_reverse_pending_request_accepts_friendship(client: TestClient):
    alice = create_user(client, "alice")
    bob = create_user(client, "bob")
    alice_id = client.get("/api/friends/search?query=alice",
                          headers=bob).json()[0]["id"]
    bob_id = client.get("/api/friends/search?query=bob",
                        headers=alice).json()[0]["id"]

    initial = client.post(f"/api/friends/requests/{bob_id}",
                          headers=alice)
    assert initial.status_code == 200
    assert initial.json()["status"] == "pending"

    reverse = client.post(f"/api/friends/requests/{alice_id}", headers=bob)
    assert reverse.status_code == 200
    assert reverse.json()["status"] == "accepted"
    assert [friend["username"] for friend in client.get(
        "/api/friends/", headers=alice).json()] == ["bob"]
    assert client.get("/api/friends/requests/outgoing",
                      headers=alice).json() == []


def test_friend_request_errors_and_authentication(client: TestClient):
    alice = create_user(client, "alice")
    bob = create_user(client, "bob")
    alice_id = client.get("/api/friends/search?query=alice",
                          headers=bob).json()[0]["id"]

    assert client.get("/api/friends/").status_code == 401
    assert client.post(f"/api/friends/requests/{alice_id}",
                       headers=alice).status_code == 422
    assert client.post("/api/friends/requests/999",
                       headers=alice).status_code == 404
    assert client.post("/api/friends/requests/2/accept",
                       headers=alice).status_code == 404


def test_friend_list_reports_presence_from_recent_heartbeat(client: TestClient,
                                                            db):
    alice = create_user(client, "alice_presence")
    bob = create_user(client, "bob_presence")

    bob_id = client.get("/api/friends/search?query=bob_presence",
                        headers=alice).json()[0]["id"]
    alice_id = client.get("/api/friends/search?query=alice_presence",
                          headers=bob).json()[0]["id"]
    client.post(f"/api/friends/requests/{bob_id}", headers=alice)
    client.post(f"/api/friends/requests/{alice_id}/accept", headers=bob)

    friends = client.get("/api/friends/", headers=alice).json()
    assert friends[0]["online"] is False

    heartbeat = client.post("/api/users/me/heartbeat", headers=bob)
    assert heartbeat.status_code == 200
    friends = client.get("/api/friends/", headers=alice).json()
    assert friends[0]["online"] is True

    bob_user = db.get(User, bob_id)
    bob_user.last_seen_at = datetime.now(timezone.utc) - timedelta(minutes=2)
    db.commit()

    friends = client.get("/api/friends/", headers=alice).json()
    assert friends[0]["online"] is False
