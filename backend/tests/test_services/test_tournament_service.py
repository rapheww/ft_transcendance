"""Tournament behavior, registration, transactions and PostgreSQL concurrency."""

from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timezone
from threading import Event, current_thread
from time import monotonic, sleep

import chess
import pytest
from sqlalchemy import create_engine, event, text
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from backend.db.base import Base
from backend.exceptions.tournament import (AlreadyRegistered,
                                           InvalidParticipantCount,
                                           NotRegistered,
                                           TournamentAlreadyStarted,
                                           TournamentNotFound)
from backend.models.game import Game
from backend.models.tournament import Tournament, TournamentMatch, TournamentParticipant
from backend.models.user import User
from backend.repositories.tournament_repository import TournamentRepository
from backend.services import game_service, tournament_service

# Tournament behavior


def create_user(db, username, email):
    user = User(username=username,
                email=email,
                password_hash="hashed-password")
    db.add(user)
    db.commit()
    return user


def create_four_players(db):
    return [
        create_user(db, f"player{i}", f"player{i}@example.com")
        for i in range(4)
    ]


def start_with(db, player_ids):
    tournament = tournament_service.create_tournament(db, player_ids[0])

    for player_id in player_ids[1:]:
        tournament_service.register(db, tournament.id, player_id)

    tournament_service.start_tournament(db, tournament.id, player_ids[0])

    return tournament


def test_create_tournament_registers_the_creator(db):
    creator = create_user(db, "alice", "alice@example.com")

    tournament = tournament_service.create_tournament(db, creator.id)
    view = tournament_service.get_tournament(db, tournament.id)

    assert view.status == "registration"
    assert view.participants == ["alice"]


def test_register_adds_a_participant(db):
    alice = create_user(db, "alice", "alice@example.com")
    bob = create_user(db, "bob", "bob@example.com")

    tournament = tournament_service.create_tournament(db, alice.id)
    tournament_service.register(db, tournament.id, bob.id)

    view = tournament_service.get_tournament(db, tournament.id)

    assert view.participants == ["alice", "bob"]


def test_register_twice_raises(db):
    alice = create_user(db, "alice", "alice@example.com")
    tournament = tournament_service.create_tournament(db, alice.id)

    with pytest.raises(AlreadyRegistered):
        tournament_service.register(db, tournament.id, alice.id)


def test_register_after_start_raises(db):
    players = create_four_players(db)
    tournament = start_with(db, [p.id for p in players])

    fifth = create_user(db, "player5", "player5@example.com")

    with pytest.raises(TournamentAlreadyStarted):
        tournament_service.register(db, tournament.id, fifth.id)


def test_start_with_non_power_of_two_raises(db):
    alice = create_user(db, "alice", "alice@example.com")
    bob = create_user(db, "bob", "bob@example.com")
    carol = create_user(db, "carol", "carol@example.com")

    tournament = tournament_service.create_tournament(db, alice.id)
    tournament_service.register(db, tournament.id, bob.id)
    tournament_service.register(db, tournament.id, carol.id)

    with pytest.raises(InvalidParticipantCount):
        tournament_service.start_tournament(db, tournament.id, alice.id)


def test_start_by_non_participant_raises(db):
    alice = create_user(db, "alice", "alice@example.com")
    bob = create_user(db, "bob", "bob@example.com")
    outsider = create_user(db, "outsider", "outsider@example.com")

    tournament = tournament_service.create_tournament(db, alice.id)
    tournament_service.register(db, tournament.id, bob.id)

    with pytest.raises(NotRegistered):
        tournament_service.start_tournament(db, tournament.id, outsider.id)


def test_start_creates_first_round_matches(db):
    players = create_four_players(db)
    tournament = start_with(db, [p.id for p in players])

    view = tournament_service.get_tournament(db, tournament.id)

    assert view.status == "in_progress"
    assert len(view.matches) == 2
    assert {match.round for match in view.matches} == {1}

    paired_ids = {
        pid
        for match in view.matches
        for pid in (match.player1_id, match.player2_id)
    }
    assert paired_ids == {p.id for p in players}


def test_tournament_advances_to_next_round_once_round_is_complete(db):
    players = create_four_players(db)
    tournament = start_with(db, [p.id for p in players])

    round_one = tournament_service.get_tournament(db, tournament.id).matches

    for match in round_one:
        game_service.resign(db, match.game_id,
                            match.player2_id)  # player1 wins

    view = tournament_service.get_tournament(db, tournament.id)

    assert view.status == "in_progress"
    assert len(view.matches) == 3  # 2 from round 1 + the final
    finalists = {m.player1_id for m in view.matches if m.round == 1}
    final_match = next(m for m in view.matches if m.round == 2)

    assert {final_match.player1_id, final_match.player2_id} == finalists


def test_tournament_finishes_after_the_final_match(db):
    players = create_four_players(db)
    tournament = start_with(db, [p.id for p in players])

    round_one = tournament_service.get_tournament(db, tournament.id).matches
    for match in round_one:
        game_service.resign(db, match.game_id, match.player2_id)

    final_match = next(
        m for m in tournament_service.get_tournament(db, tournament.id).matches
        if m.round == 2)

    game_service.resign(db, final_match.game_id, final_match.player2_id)

    view = tournament_service.get_tournament(db, tournament.id)

    assert view.status == "finished"
    assert view.winner_id == final_match.player1_id


def test_cancel_tournament_deletes_it_and_its_participants(db):
    alice = create_user(db, "alice", "alice@example.com")
    bob = create_user(db, "bob", "bob@example.com")

    tournament = tournament_service.create_tournament(db, alice.id)
    tournament_service.register(db, tournament.id, bob.id)

    tournament_service.cancel_tournament(db, tournament.id)

    with pytest.raises(TournamentNotFound):
        tournament_service.get_tournament(db, tournament.id)

    remaining = (db.query(TournamentParticipant).filter(
        TournamentParticipant.tournament_id == tournament.id).all())
    assert remaining == []


def test_cancel_tournament_after_start_raises(db):
    players = create_four_players(db)
    tournament = start_with(db, [p.id for p in players])

    with pytest.raises(TournamentAlreadyStarted):
        tournament_service.cancel_tournament(db, tournament.id)


def test_cancel_missing_tournament_raises(db):
    with pytest.raises(TournamentNotFound):
        tournament_service.cancel_tournament(db, 999999)


def _finish_as_draw(db, game_id, fen):
    from datetime import datetime, timezone
    game = db.query(Game).filter(Game.id == game_id).first()
    game.status = "finished"
    game.result = "1/2-1/2"
    game.current_fen = fen
    game.finished_at = datetime.now(timezone.utc)
    db.commit()


def test_draw_is_broken_by_material_on_the_board(db):
    players = create_four_players(db)
    tournament = start_with(db, [p.id for p in players])

    match = tournament_service.get_tournament(db, tournament.id).matches[0]

    # White is up a queen: white_material (9) > black_material (0).
    fen = "4k3/8/8/8/8/8/8/3QK3 w - - 0 1"
    _finish_as_draw(db, match.game_id, fen)

    view = tournament_service.get_tournament(db, tournament.id)
    resolved = next(m for m in view.matches if m.game_id == match.game_id)

    assert resolved.winner_id == match.player1_id  # white


def test_perfectly_equal_material_draw_is_replayed(db):
    players = create_four_players(db)
    tournament = start_with(db, [p.id for p in players])

    match = tournament_service.get_tournament(db, tournament.id).matches[0]
    original_game_id = match.game_id

    _finish_as_draw(db, match.game_id, chess.Board().fen())

    view = tournament_service.get_tournament(db, tournament.id)
    resolved = next(m for m in view.matches
                    if m.round == 1 and {m.player1_id, m.player2_id} ==
                    {match.player1_id, match.player2_id})

    assert resolved.winner_id is None
    assert resolved.game_id != original_game_id


# Registration integrity


@pytest.fixture
def registration_db():
    engine = create_engine("sqlite:///:memory:")

    @event.listens_for(engine, "connect")
    def enable_foreign_keys(connection, record):
        connection.execute("PRAGMA foreign_keys=ON")

    Base.metadata.create_all(engine)
    with Session(engine) as db:
        user = User(username="alice",
                    email="alice@example.com",
                    password_hash="hashed-password")
        db.add(user)
        db.commit()
        tournament = tournament_service.create_tournament(db, user.id)
        yield db, tournament.id, user.id
    engine.dispose()


def test_database_rejects_duplicate_participant(registration_db):
    db, tournament_id, user_id = registration_db
    db.add(TournamentParticipant(tournament_id=tournament_id, user_id=user_id))

    with pytest.raises(IntegrityError):
        db.commit()
    db.rollback()

    assert len(TournamentRepository(db).list_participants(tournament_id)) == 1


def test_stale_registration_read_returns_already_registered(
        registration_db, monkeypatch):
    db, tournament_id, user_id = registration_db
    original = TournamentRepository.list_participants
    reads = 0

    def stale_first_read(repository, requested_id):
        nonlocal reads
        reads += 1
        if reads == 1:
            return []
        return original(repository, requested_id)

    monkeypatch.setattr(TournamentRepository, "list_participants",
                        stale_first_read)

    with pytest.raises(AlreadyRegistered):
        tournament_service.register(db, tournament_id, user_id)

    assert db.is_active
    assert len(original(TournamentRepository(db), tournament_id)) == 1


def test_unrelated_integrity_error_is_not_reported_as_duplicate(
        registration_db, monkeypatch):
    db, tournament_id, user_id = registration_db
    bob = User(username="bob",
               email="bob@example.com",
               password_hash="hashed-password")
    db.add(bob)
    db.commit()
    error = IntegrityError("INSERT", {},
                           ValueError("Other constraint failure"))

    def fail_insert(repository, participant):
        raise error

    monkeypatch.setattr(TournamentRepository, "add_participant", fail_insert)

    with pytest.raises(IntegrityError) as caught:
        tournament_service.register(db, tournament_id, bob.id)

    assert caught.value is error
    assert db.is_active
    assert len(TournamentRepository(db).list_participants(tournament_id)) == 1


# Atomic transactions


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


# PostgreSQL concurrency


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
