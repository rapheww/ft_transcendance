from datetime import datetime, timezone

import pytest
from sqlalchemy import create_engine, event
from sqlalchemy.orm import Session

from backend.db.base import Base
from backend.models.game import Game
from backend.models.tournament import Tournament, TournamentMatch
from backend.models.user import User
from backend.services import game_service, tournament_service


@pytest.fixture
def tournament_db():
    engine = create_engine("sqlite:///:memory:")

    @event.listens_for(engine, "connect")
    def enable_foreign_keys(connection, record):
        connection.execute("PRAGMA foreign_keys=ON")

    Base.metadata.create_all(engine)
    with Session(engine) as db:
        players = [
            User(username=f"player{i}",
                 email=f"player{i}@example.com",
                 password_hash="hashed-password") for i in range(4)
        ]
        db.add_all(players)
        db.commit()
        player_ids = [player.id for player in players]
        tournament = tournament_service.create_tournament(db, player_ids[0])
        tournament_id = tournament.id
        for player_id in player_ids[1:]:
            tournament_service.register(db, tournament_id, player_id)
        yield db, tournament_id, player_ids[0]
    engine.dispose()


def fail_join(monkeypatch, fail_on):
    original = game_service.join_game
    calls = 0

    def join(db, game_id, user_id):
        nonlocal calls
        calls += 1
        if calls == fail_on:
            raise RuntimeError("Simulated game creation failure")
        return original(db, game_id, user_id)

    monkeypatch.setattr(game_service, "join_game", join)


@pytest.mark.parametrize("failed_match", [1, 2])
def test_failed_start_leaves_no_games_or_matches(tournament_db, monkeypatch,
                                                 failed_match):
    db, tournament_id, creator_id = tournament_db
    fail_join(monkeypatch, failed_match)

    with pytest.raises(RuntimeError, match="Simulated"):
        tournament_service.start_tournament(db, tournament_id, creator_id)

    assert db.is_active
    assert db.get(Tournament, tournament_id).status == "registration"
    assert db.query(TournamentMatch).count() == 0
    assert db.query(Game).count() == 0


def test_failed_next_round_preserves_previous_round(tournament_db,
                                                    monkeypatch):
    db, tournament_id, creator_id = tournament_db
    tournament_service.start_tournament(db, tournament_id, creator_id)
    for match in tournament_service.get_tournament(db, tournament_id).matches:
        game_service.resign(db, match.game_id, match.player2_id)
    fail_join(monkeypatch, 1)

    with pytest.raises(RuntimeError, match="Simulated"):
        tournament_service.get_tournament(db, tournament_id)

    assert db.is_active
    assert db.query(Game).count() == 2
    matches = db.query(TournamentMatch).all()
    assert len(matches) == 2
    assert all(match.round == 1 and match.winner_id is None
               for match in matches)
    assert all(game.status == "finished" for game in db.query(Game).all())

    monkeypatch.undo()
    view = tournament_service.get_tournament(db, tournament_id)
    assert len(view.matches) == 3
    assert db.query(Game).count() == 3


def test_failed_replay_preserves_original_game(tournament_db, monkeypatch):
    db, tournament_id, creator_id = tournament_db
    tournament_service.start_tournament(db, tournament_id, creator_id)
    match = tournament_service.get_tournament(db, tournament_id).matches[0]
    game = db.get(Game, match.game_id)
    game.status = "finished"
    game.result = "1/2-1/2"
    game.finished_at = datetime.now(timezone.utc)
    db.commit()
    fail_join(monkeypatch, 1)

    with pytest.raises(RuntimeError, match="Simulated"):
        tournament_service.get_tournament(db, tournament_id)

    assert db.is_active
    assert db.query(Game).count() == 2
    original_match = db.query(TournamentMatch).filter_by(
        tournament_id=tournament_id, round=match.round, slot=match.slot).one()
    assert original_match.game_id == match.game_id
    assert original_match.winner_id is None


def test_successful_tournament_still_finishes(tournament_db):
    db, tournament_id, creator_id = tournament_db
    tournament_service.start_tournament(db, tournament_id, creator_id)
    view = tournament_service.get_tournament(db, tournament_id)
    assert len(view.matches) == 2
    for match in view.matches:
        game_service.resign(db, match.game_id, match.player2_id)
    view = tournament_service.get_tournament(db, tournament_id)
    final = next(match for match in view.matches if match.round == 2)
    game_service.resign(db, final.game_id, final.player2_id)

    view = tournament_service.get_tournament(db, tournament_id)
    assert view.status == "finished"
    assert view.winner_id == final.player1_id
    assert db.query(Game).count() == 3
