import pytest
from fastapi.testclient import TestClient
from backend.core.public_api_security import PUBLIC_API_KEY, limiter
from backend.app.main import app
from backend.db.session import get_db
from backend.exceptions.user import UserNotFound
from backend.models.user import User
from backend.services import tournament_service


@pytest.fixture(autouse=True)
def reset_rate_limiter():
    limiter.reset()
    yield


def api_headers(key: str = PUBLIC_API_KEY) -> dict:
    return {"X-API-Key": key}


def create_user(client: TestClient, db, username: str, email: str) -> int:
    response = client.post("/api/users/",
                           json={
                               "username": username,
                               "email": email,
                               "password": "password123"
                           })
    assert response.status_code == 201, response.text

    user = db.query(User).filter(User.username == username).first()
    return user.id


def create_tournament(client: TestClient, creator_id: int) -> int:
    response = client.post("/api/public/tournaments",
                           json={"creator_id": creator_id},
                           headers=api_headers())
    tid = response.json()["id"]
    client.put(f"/api/public/tournaments/{tid}/participants/{creator_id}",
               headers=api_headers())
    return tid


def test_missing_api_key_returns_401(client: TestClient):
    response = client.get("/api/public/leaderboard")

    assert response.status_code == 401


def test_wrong_api_key_returns_401(client: TestClient):
    response = client.get("/api/public/leaderboard",
                          headers=api_headers("wrong-key"))

    assert response.status_code == 401


def test_get_leaderboard_returns_200(client: TestClient, db):
    create_user(client, db, "alice", "alice@example.com")

    response = client.get("/api/public/leaderboard", headers=api_headers())

    assert response.status_code == 200
    assert response.json()[0]["elo"] == 1000


def test_get_missing_tournament_returns_404(client: TestClient):
    response = client.get("/api/public/tournaments/999999",
                          headers=api_headers())

    assert response.status_code == 404


def test_create_tournament_returns_201(client: TestClient, db):
    alice_id = create_user(client, db, "alice", "alice@example.com")

    response = client.post("/api/public/tournaments",
                           json={"creator_id": alice_id},
                           headers=api_headers())

    assert response.status_code == 201
    assert response.json()["participants"] == []


def test_create_tournament_needs_no_player_identity(client: TestClient):
    response = client.post("/api/public/tournaments", headers=api_headers())

    assert response.status_code == 201
    assert response.json()["participants"] == []


def test_get_tournament_returns_200(client: TestClient, db):
    alice_id = create_user(client, db, "alice", "alice@example.com")
    tournament_id = create_tournament(client, alice_id)

    response = client.get(f"/api/public/tournaments/{tournament_id}",
                          headers=api_headers())

    assert response.status_code == 200
    assert response.json()["participants"] == ["alice"]


def test_add_participant_returns_200(client: TestClient, db):
    alice_id = create_user(client, db, "alice", "alice@example.com")
    bob_id = create_user(client, db, "bob", "bob@example.com")
    tournament_id = create_tournament(client, alice_id)

    response = client.put(
        f"/api/public/tournaments/{tournament_id}/participants/{bob_id}",
        headers=api_headers())

    assert response.status_code == 200
    assert response.json()["participants"] == ["alice", "bob"]


def test_add_unknown_participant_returns_404(monkeypatch):

    def register_unknown_user(db, tournament_id, user_id):
        assert tournament_id == 1
        assert user_id == 999999
        raise UserNotFound()

    monkeypatch.setattr(tournament_service, "register", register_unknown_user)
    monkeypatch.setitem(app.dependency_overrides, get_db, lambda: None)

    with TestClient(app) as client:
        response = client.put("/api/public/tournaments/1/participants/999999",
                              headers=api_headers())

    assert response.status_code == 404
    assert response.json() == {"detail": "User not found"}


def test_add_participant_twice_returns_409(client: TestClient, db):
    alice_id = create_user(client, db, "alice", "alice@example.com")
    tournament_id = create_tournament(client, alice_id)

    response = client.put(
        f"/api/public/tournaments/{tournament_id}/participants/{alice_id}",
        headers=api_headers())

    assert response.status_code == 409


def test_add_participant_after_start_returns_409(client: TestClient, db):
    ids = [
        create_user(client, db, f"player{i}", f"player{i}@example.com")
        for i in range(4)
    ]
    tournament_id = create_tournament(client, ids[0])

    for user_id in ids[1:]:
        client.put(
            f"/api/public/tournaments/{tournament_id}/participants/{user_id}",
            headers=api_headers())

    tournament_service.start_tournament(db, tournament_id, api_manager=True)

    fifth_id = create_user(client, db, "player5", "player5@example.com")

    response = client.put(
        f"/api/public/tournaments/{tournament_id}/participants/{fifth_id}",
        headers=api_headers())

    assert response.status_code == 409


def test_cancel_tournament_returns_204(client: TestClient, db):
    alice_id = create_user(client, db, "alice", "alice@example.com")
    tournament_id = create_tournament(client, alice_id)

    response = client.delete(f"/api/public/tournaments/{tournament_id}",
                             headers=api_headers())

    assert response.status_code == 204

    get_response = client.get(f"/api/public/tournaments/{tournament_id}",
                              headers=api_headers())
    assert get_response.status_code == 200
    assert get_response.json()["status"] == "cancelled"


def test_cancel_tournament_after_start_returns_409(client: TestClient, db):
    ids = [
        create_user(client, db, f"player{i}", f"player{i}@example.com")
        for i in range(4)
    ]
    tournament_id = create_tournament(client, ids[0])

    for user_id in ids[1:]:
        client.put(
            f"/api/public/tournaments/{tournament_id}/participants/{user_id}",
            headers=api_headers())

    tournament_service.start_tournament(db, tournament_id, api_manager=True)

    response = client.delete(f"/api/public/tournaments/{tournament_id}",
                             headers=api_headers())

    assert response.status_code == 409


def test_rate_limit_exceeded_returns_429(client: TestClient):
    responses = [
        client.get("/api/public/leaderboard", headers=api_headers())
        for _ in range(31)
    ]

    assert responses[-1].status_code == 429


def test_api_start_and_player_owner_protection(client, db):
    ids = [
        create_user(client, db, f"player{i}", f"player{i}@example.com")
        for i in range(2)
    ]
    tid = create_tournament(client, ids[0])
    client.put(f"/api/public/tournaments/{tid}/participants/{ids[1]}",
               headers=api_headers())
    response = client.post(f"/api/public/tournaments/{tid}/start",
                           headers=api_headers())
    assert response.status_code == 200
    assert response.json()["status"] == "countdown"
    player_tid = tournament_service.create_tournament(db, api_manager=True).id
    # Give a separate tournament the player owner; no duplicate enrollment is needed.
    from backend.models.tournament import Tournament
    tournament = db.get(Tournament, player_tid)
    tournament.organizer_type, tournament.creator_id = "player", ids[0]
    db.commit()
    assert client.post(f"/api/public/tournaments/{player_tid}/start",
                       headers=api_headers()).status_code == 403
    assert client.delete(f"/api/public/tournaments/{player_tid}",
                         headers=api_headers()).status_code == 403
