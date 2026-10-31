"""Add-on bots: fill before Start, and the worker that plays the bots' moves.
The tournament rules themselves are the unchanged tournament_service."""
import chess
import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import sessionmaker

from backend.exceptions.tournament import (InvalidParticipantCount, NotTournamentOrganizer,
                                           TournamentAlreadyStarted)
from backend.models.game import Game
from backend.models.user import User
from backend.services import game_service, tournament_bots, tournament_service


def human(db, name, elo=1000):
    user = User(username=name, email=f"{name}@example.com", password_hash="x", elo=elo)
    db.add(user)
    db.commit()
    return user


def bot(db, name, elo=1000, level="easy"):
    user = User(username=name, email=f"{name}@bots.invalid", password_hash="!", elo=elo,
                is_bot=True, ai_level=level, style="balanced")
    db.add(user)
    db.commit()
    return user


def factory(engine):
    # Same settings as SessionLocal (no autoflush).
    return sessionmaker(bind=engine, autoflush=False, autocommit=False)


def start_round_one(db, tournament_id, organizer_id):
    tournament_service.start_tournament(db, tournament_id, organizer_id)
    view = tournament_service.get_tournament(db, tournament_id)
    tournament_service.process_tournament(db, tournament_id, view.next_round_at)
    return tournament_service.get_tournament(db, tournament_id, organizer_id)


# ------------------------------------------------------------------ fill


def test_one_human_gets_three_bots_with_the_closest_elo(db):
    me = human(db, "me", 1000)
    near = [bot(db, "n1", 990), bot(db, "n2", 1020), bot(db, "n3", 1050)]
    bot(db, "far1", 1900)
    bot(db, "far2", 400)
    t = tournament_service.create_tournament(db, me.id)

    added = tournament_bots.fill_with_bots(db, t.id, me.id)

    assert set(added) == {b.id for b in near}
    view = start_round_one(db, t.id, me.id)  # the unchanged Start accepts them
    assert view.participant_count == 4
    assert len([m for m in view.matches if m.round == 1 and not m.is_bye]) == 2


def test_fill_sizes(db):
    people = [human(db, f"h{i}") for i in range(5)]
    for i in range(8):
        bot(db, f"b{i}")
    t = tournament_service.create_tournament(db, people[0].id)
    for p in people[1:]:
        tournament_service.register(db, t.id, p.id)

    assert len(tournament_bots.fill_with_bots(db, t.id, people[0].id)) == 3  # 5 -> 8
    assert tournament_bots.fill_with_bots(db, t.id, people[0].id) == []  # already full


def test_only_the_organizer_during_registration(db):
    a, b = human(db, "orga"), human(db, "other")
    bot(db, "x1")
    bot(db, "x2")
    t = tournament_service.create_tournament(db, a.id)
    tournament_service.register(db, t.id, b.id)

    with pytest.raises(NotTournamentOrganizer):
        tournament_bots.fill_with_bots(db, t.id, b.id)
    tournament_service.start_tournament(db, t.id, a.id)
    with pytest.raises(TournamentAlreadyStarted):
        tournament_bots.fill_with_bots(db, t.id, a.id)


def test_no_bot_in_database_keeps_the_normal_rule(db):
    me = human(db, "alone")
    t = tournament_service.create_tournament(db, me.id)
    assert tournament_bots.fill_with_bots(db, t.id, me.id) == []
    with pytest.raises(InvalidParticipantCount):
        tournament_service.start_tournament(db, t.id, me.id)


def test_a_bot_is_never_in_two_tournaments(db):
    a, b = human(db, "ta"), human(db, "tb")
    for i in range(4):
        bot(db, f"s{i}")
    first = tournament_service.create_tournament(db, a.id)
    second = tournament_service.create_tournament(db, b.id)

    one = tournament_bots.fill_with_bots(db, first.id, a.id)
    two = tournament_bots.fill_with_bots(db, second.id, b.id)

    assert len(one) == 3 and len(two) == 1
    assert set(one).isdisjoint(two)


# ------------------------------------------------------------------ worker


def test_bot_plays_its_moves_in_a_game_against_a_human(engine, db):
    me = human(db, "player")
    for i in range(3):
        bot(db, f"w{i}")
    t = tournament_service.create_tournament(db, me.id)
    tournament_bots.fill_with_bots(db, t.id, me.id)
    view = start_round_one(db, t.id, me.id)
    game = db.get(Game, view.my_game_id)
    if game.white_player_id == me.id:  # human starts: play a move first
        game_service.make_move(db, game.id, me.id, "e2e4")
    fen_before = chess.Board(db.get(Game, game.id, populate_existing=True).current_fen)

    messages = tournament_bots.run_bot_tick(factory(engine))

    game = db.get(Game, game.id, populate_existing=True)
    board = chess.Board(game.current_fen)
    assert board.turn != fen_before.turn  # the bot played
    assert board.turn == (chess.WHITE if game.white_player_id == me.id else chess.BLACK)
    sent = [m for gid, m in messages if gid == game.id]
    assert [m["type"] for m in sent][:2] == ["move", "game_state"]


def test_bot_vs_bot_finishes_and_the_tournament_moves_on(engine, db, monkeypatch):
    monkeypatch.setattr(tournament_bots, "BOT_VS_BOT_MAX_PLIES", 6)
    monkeypatch.setattr(tournament_bots, "BOT_VS_BOT_SECONDS_PER_TICK", 30)
    me = human(db, "watcher")
    for i in range(3):
        bot(db, f"v{i}")
    t = tournament_service.create_tournament(db, me.id)
    tournament_bots.fill_with_bots(db, t.id, me.id)
    view = start_round_one(db, t.id, me.id)
    bots_match = next(m for m in view.matches
                      if m.round == 1 and me.id not in (m.player1_id, m.player2_id))

    tournament_bots.run_bot_tick(factory(engine))

    game = db.get(Game, bots_match.game_id, populate_existing=True)
    assert game.status == "finished"
    tournament_service.process_tournament(db, t.id)
    view = tournament_service.get_tournament(db, t.id)
    resolved = next(m for m in view.matches if m.game_id == bots_match.game_id)
    assert resolved.winner_id in (resolved.player1_id, resolved.player2_id)  # his tie-break


def test_full_tournament_with_one_human_and_bots(engine, db, monkeypatch):
    monkeypatch.setattr(tournament_bots, "BOT_VS_BOT_MAX_PLIES", 6)
    monkeypatch.setattr(tournament_bots, "BOT_VS_BOT_SECONDS_PER_TICK", 30)
    me = human(db, "solo")
    for i in range(3):
        bot(db, f"f{i}")
    t = tournament_service.create_tournament(db, me.id)
    tournament_bots.fill_with_bots(db, t.id, me.id)
    view = start_round_one(db, t.id, me.id)
    game_service.resign(db, view.my_game_id, me.id)  # the human loses round 1

    for _ in range(10):
        tournament_bots.run_bot_tick(factory(engine))
        tournament_service.process_tournament(db, t.id)
        view = tournament_service.get_tournament(db, t.id)
        if view.status == "between_rounds":
            tournament_service.process_tournament(db, t.id, view.next_round_at)
        if view.status == "finished":
            break

    assert view.status == "finished"
    assert view.winner_id != me.id
    assert tournament_service.get_my_tournament(db, me.id) is None


def test_worker_ignores_games_without_bots(engine, db):
    a, b = human(db, "p1"), human(db, "p2")
    t = tournament_service.create_tournament(db, a.id)
    tournament_service.register(db, t.id, b.id)
    view = start_round_one(db, t.id, a.id)
    game = db.get(Game, view.matches[0].game_id)
    fen = game.current_fen

    assert tournament_bots.run_bot_tick(factory(engine)) == []
    assert db.get(Game, game.id, populate_existing=True).current_fen == fen


# ------------------------------------------------------------------ API


def login(client, name):
    client.post("/api/users/", json={"username": name, "email": f"{name}@example.com",
                                     "password": "password123"})
    token = client.post("/api/auth/login", json={"username": name,
                                                 "password": "password123"}).json()["access_token"]
    return {"Authorization": f"Bearer {token}"}


def test_api_fill_and_list_bots(client: TestClient, db):
    for i in range(3):
        bot(db, f"api{i}", level="medium")
    organizer, other = login(client, "orgapi"), login(client, "otherapi")
    tid = client.post("/api/tournaments/", headers=organizer).json()["id"]
    client.post(f"/api/tournaments/{tid}/register", headers=other)

    assert client.post(f"/api/tournaments/{tid}/bots", headers=other).status_code == 403
    filled = client.post(f"/api/tournaments/{tid}/bots", headers=organizer)
    assert filled.status_code == 200
    assert filled.json()["participant_count"] == 4

    bots = client.get(f"/api/tournaments/{tid}/bots").json()
    assert len(bots) == 2
    assert all(b["ai_level"] == "medium" and "elo" in b for b in bots)
    assert client.get("/api/tournaments/999999/bots").status_code == 404
