"""Real PostgreSQL lock contention, using separate sessions and connections."""

from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timezone
from threading import Event, current_thread
from time import monotonic, sleep

import chess
import pytest
from sqlalchemy import text
from sqlalchemy.orm import Session

from backend.exceptions.tournament import (AlreadyRegistered, NotRegistered,
                                           TournamentAlreadyStarted,
                                           TournamentNotFound)
from backend.models.game import Game
from backend.models.tournament import Tournament, TournamentMatch, TournamentParticipant
from backend.models.user import User
from backend.repositories.tournament_repository import TournamentRepository
from backend.services import game_service, tournament_service


@pytest.fixture
def setup_tournament(engine):
    assert engine.dialect.name == "postgresql", "These tests require PostgreSQL"
    with Session(engine) as db:
        players = [
            User(username=f"player{i}",
                 email=f"player{i}@example.com",
                 password_hash="hashed-password") for i in range(5)
        ]
        db.add_all(players)
        db.commit()
        player_ids = [player.id for player in players]
        tournament = tournament_service.create_tournament(db, player_ids[0])
        tournament_id = tournament.id
        for player_id in player_ids[1:4]:
            tournament_service.register(db, tournament_id, player_id)
    return tournament_id, player_ids


def _start(db, tournament_id, user_id):
    tournament_service.start_tournament(db, tournament_id, user_id)
    return "started"


def _register(db, tournament_id, user_id):
    tournament_service.register(db, tournament_id, user_id)
    return "registered"


def _cancel(db, tournament_id):
    tournament_service.cancel_tournament(db, tournament_id)
    return "deleted"


def _run_contended(engine,
                   monkeypatch,
                   tournament_id,
                   first_operation,
                   second_operation,
                   preload=False):
    """Pause the first lock owner until PostgreSQL confirms the second waits."""
    locked = Event()
    release = Event()
    attempting = Event()
    second_pid = []
    original = TournamentRepository.get_by_id_for_update

    def pause_first(repository, requested_id):
        if current_thread().name.endswith("_1"):
            attempting.set()
        tournament = original(repository, requested_id)
        if current_thread().name.endswith("_0"):
            locked.set()
            assert release.wait(10), "First worker was not released"
        return tournament

    monkeypatch.setattr(TournamentRepository, "get_by_id_for_update",
                        pause_first)

    def run(operation, second=False):
        with Session(engine) as db:
            db.execute(text("SET LOCAL lock_timeout = '8s'"))
            if second:
                second_pid.append(db.scalar(text("SELECT pg_backend_pid()")))
                if preload:
                    # Keep a strong reference: SQLAlchemy's identity map is weak.
                    cached_tournament = db.get(Tournament, tournament_id)
                    cached_matches = db.query(TournamentMatch).filter_by(
                        tournament_id=tournament_id).all()
                    cached_games = db.query(Game).all()
            try:
                result = operation(db)
            except Exception as error:
                result = error
            # The worker deliberately keeps its session open after errors.
            # A missing rollback would prevent the other worker from finishing.
            if not second:
                assert second_done.wait(10), "Error left a lock held"
            else:
                second_done.set()
            return result

    second_done = Event()
    with ThreadPoolExecutor(max_workers=2,
                            thread_name_prefix="tournament") as pool:
        first = pool.submit(run, first_operation)
        try:
            assert locked.wait(5), "First worker did not acquire the lock"
            second = pool.submit(run, second_operation, True)
            assert attempting.wait(5), "Second worker did not attempt the lock"
            deadline = monotonic() + 5
            with engine.connect() as observer:
                while monotonic() < deadline:
                    wait_type = observer.scalar(
                        text("SELECT wait_event_type FROM pg_stat_activity "
                             "WHERE pid = :pid"), {"pid": second_pid[0]})
                    observer.commit()
                    if wait_type == "Lock":
                        break
                    sleep(0.02)
                else:
                    pytest.fail(
                        "Second PostgreSQL connection never waited on the lock"
                    )
            assert not second.done()
        finally:
            release.set()
        return first.result(timeout=12), second.result(timeout=12)


@pytest.mark.parametrize("preload", [False, True])
def test_concurrent_starts_create_one_bracket(engine, setup_tournament,
                                              monkeypatch, preload):
    tournament_id, players = setup_tournament
    first, second = _run_contended(
        engine, monkeypatch, tournament_id,
        lambda db: _start(db, tournament_id, players[0]),
        lambda db: _start(db, tournament_id, players[1]), preload)

    assert first == "started"
    assert isinstance(second, TournamentAlreadyStarted)
    with Session(engine) as db:
        assert db.query(TournamentMatch).count() == 2
        assert db.query(Game).count() == 2


def test_registration_cannot_join_after_concurrent_start(
        engine, setup_tournament, monkeypatch):
    tournament_id, players = setup_tournament
    first, second = _run_contended(
        engine, monkeypatch, tournament_id,
        lambda db: _start(db, tournament_id, players[0]),
        lambda db: _register(db, tournament_id, players[4]))

    assert first == "started"
    assert isinstance(second, TournamentAlreadyStarted)
    with Session(engine) as db:
        assert db.query(TournamentParticipant).count() == 4


def test_concurrent_registration_is_included_in_bracket(
        engine, setup_tournament, monkeypatch):
    tournament_id, players = setup_tournament
    with Session(engine) as db:
        db.query(TournamentParticipant).filter_by(tournament_id=tournament_id,
                                                  user_id=players[3]).delete()
        db.commit()
    first, second = _run_contended(
        engine, monkeypatch, tournament_id,
        lambda db: _register(db, tournament_id, players[3]),
        lambda db: _start(db, tournament_id, players[0]))

    assert first == "registered"
    assert second == "started"
    with Session(engine) as db:
        matches = db.query(TournamentMatch).all()
        assert len(matches) == 2
        assert {p
                for m in matches
                for p in (m.player1_id, m.player2_id)} == set(players[:4])


@pytest.mark.parametrize("draw", [False, True])
def test_concurrent_reads_create_one_next_round_or_replay(
        engine, setup_tournament, monkeypatch, draw):
    tournament_id, players = setup_tournament
    with Session(engine) as db:
        tournament_service.start_tournament(db, tournament_id, players[0])
        view = tournament_service.get_tournament(db, tournament_id)
        original_game_ids = {m.game_id for m in view.matches}
        if draw:
            game = db.get(Game, view.matches[0].game_id)
            game.status = "finished"
            game.result = "1/2-1/2"
            game.current_fen = chess.Board().fen()
            game.finished_at = datetime.now(timezone.utc)
            db.commit()
        else:
            for match in view.matches:
                game_service.resign(db, match.game_id, match.player2_id)

    first, second = _run_contended(
        engine,
        monkeypatch,
        tournament_id,
        lambda db: tournament_service.get_tournament(db, tournament_id),
        lambda db: tournament_service.get_tournament(db, tournament_id),
        preload=True)

    assert not isinstance(first, Exception)
    assert not isinstance(second, Exception)
    assert first == second
    with Session(engine) as db:
        assert db.query(Game).count() == 3
        matches = db.query(TournamentMatch).all()
        if draw:
            assert len(matches) == 2
            assert len({m.game_id for m in matches} - original_game_ids) == 1
        else:
            assert len(matches) == 3
            assert sum(m.round == 2 for m in matches) == 1


@pytest.mark.parametrize("first_action", ["start", "delete", "invalid_start"])
def test_deletion_and_errors_release_the_lock(engine, setup_tournament,
                                              monkeypatch, first_action):
    tournament_id, players = setup_tournament
    operations = {
        "start": lambda db: _start(db, tournament_id, players[0]),
        "delete": lambda db: _cancel(db, tournament_id),
        "invalid_start": lambda db: _start(db, tournament_id, players[4]),
    }
    first, second = _run_contended(engine, monkeypatch, tournament_id,
                                   operations[first_action],
                                   lambda db: _cancel(db, tournament_id))

    if first_action == "start":
        assert first == "started"
        assert isinstance(second, TournamentAlreadyStarted)
    elif first_action == "delete":
        assert first == "deleted"
        assert isinstance(second, TournamentNotFound)
    else:
        assert isinstance(first, NotRegistered)
        assert second == "deleted"


def test_concurrent_duplicate_registration_returns_business_error(
        engine, setup_tournament, monkeypatch):
    tournament_id, players = setup_tournament
    first, second = _run_contended(
        engine, monkeypatch, tournament_id,
        lambda db: _register(db, tournament_id, players[4]),
        lambda db: _register(db, tournament_id, players[4]))

    assert first == "registered"
    assert isinstance(second, AlreadyRegistered)
    with Session(engine) as db:
        assert db.query(TournamentParticipant).count() == 5


def test_different_tournaments_do_not_block_each_other(engine,
                                                       setup_tournament):
    tournament_id, players = setup_tournament
    with Session(engine) as db:
        other_id = tournament_service.create_tournament(db, players[0]).id

    with Session(engine) as owner:
        TournamentRepository(owner).get_by_id_for_update(tournament_id)
        with ThreadPoolExecutor(max_workers=1) as pool:

            def register_other():
                with Session(engine) as db:
                    db.execute(text("SET LOCAL lock_timeout = '2s'"))
                    return _register(db, other_id, players[1])

            assert pool.submit(register_other).result(
                timeout=5) == "registered"
        owner.rollback()
