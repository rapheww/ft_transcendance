"""Elo calculation, game integration, migrations and PostgreSQL concurrency."""

from concurrent.futures import ThreadPoolExecutor
from threading import Event, current_thread
from time import monotonic, sleep
import importlib.util
from pathlib import Path
from datetime import datetime, timedelta, timezone
from unittest.mock import patch
from uuid import uuid4

from alembic.migration import MigrationContext
from alembic.operations import Operations
import pytest
import chess
import chess.pgn
from sqlalchemy import inspect, text
from sqlalchemy.exc import IntegrityError, SQLAlchemyError
from sqlalchemy.orm import Session

from backend.services.elo_service import DRAW, INITIAL_ELO, LOSS, WIN
from backend.exceptions.game import CannotResignFinishedGame, IllegalMove
from backend.models.game import Game
from backend.models.user import User
from backend.repositories.game_repository import GameRepository
from backend.repositories.stats_repository import StatsRepository
from backend.services import elo_service, game_service, stats_service


def create_players(db, ratings=(INITIAL_ELO, INITIAL_ELO)):
    players = [
        User(username=name,
             email=f"{name.lower()}@example.com",
             password_hash="hashed-password",
             elo=rating) for name, rating in zip(("Vigo", "Louis"), ratings)
    ]
    db.add_all(players)
    db.commit()
    return players


def active_game(db, white, black, fen=None, moves=()):
    game = game_service.create_game(db, white.id)
    game_service.join_game(db, game.id, black.id)
    if fen:
        pgn = chess.pgn.Game()
        pgn.setup(chess.Board(fen))
        game.current_fen = fen
        game.pgn = str(pgn)
        db.commit()
    for index, move in enumerate(moves):
        game_service.make_move(db, game.id,
                               white.id if index % 2 == 0 else black.id, move)
    return game


@pytest.mark.parametrize("ratings,expected", [((1000, 1000), 0.5),
                                              ((1000, 1400), 1 / 11),
                                              ((1400, 1000), 10 / 11)])
def test_expected_score(ratings, expected):
    assert elo_service.expected_score(*ratings) == pytest.approx(expected)


@pytest.mark.parametrize("rating_a,rating_b,actual_score_a,expected", [
    (1000, 1000, WIN, (1016, 984)),
    (1000, 1000, LOSS, (984, 1016)),
    (1000, 1000, DRAW, (1000, 1000)),
    (1000, 1200, WIN, (1024, 1176)),
    (1000, 1200, DRAW, (1008, 1192)),
    (1000, 1200, LOSS, (992, 1208)),
])
def test_rating_change_uses_old_ratings_and_preserves_total(
        rating_a, rating_b, actual_score_a, expected):
    ratings = elo_service.calculate_ratings(rating_a, rating_b, actual_score_a)
    assert ratings == expected
    assert sum(ratings) == rating_a + rating_b


def test_new_user_starts_at_initial_elo(db):
    user = User(username="Chikako",
                email="chikako@example.com",
                password_hash="hashed-password")
    db.add(user)
    db.commit()
    assert user.elo == INITIAL_ELO


def test_invalid_score_is_rejected():
    with pytest.raises(ValueError):
        elo_service.calculate_ratings(1000, 1000, 2)


@pytest.mark.parametrize("resigning_color,expected", [("white", (984, 1016)),
                                                      ("black", (1016, 984))])
def test_resignation_changes_elo_once(db, resigning_color, expected):
    white, black = create_players(db)
    game = active_game(db, white, black)
    resigning_id = white.id if resigning_color == "white" else black.id
    game_service.resign(db, game.id, resigning_id)

    db.refresh(white)
    db.refresh(black)
    assert (white.elo, black.elo) == expected
    with pytest.raises(CannotResignFinishedGame):
        game_service.resign(db, game.id, resigning_id)
    db.refresh(white)
    db.refresh(black)
    assert (white.elo, black.elo) == expected


@pytest.mark.parametrize("fen,moves,final_move,result,expected", [
    (None, ("f2f3", "e7e5", "g2g4"), "d8h4", "0-1", (984, 1016)),
    ("7k/5K2/8/6Q1/8/8/8/8 w - - 0 1", (), "g5g6", "1/2-1/2", (1008, 1192)),
    ("7k/8/8/8/8/8/1B6/K7 w - - 0 1", (), "b2c3", "1/2-1/2", (1008, 1192)),
    ("7k/8/8/8/8/8/1N6/K7 w - - 149 76", (), "b2c4", "1/2-1/2", (1008, 1192)),
    (None, ("g1f3", "g8f6", "f3g1", "f6g8") * 3 +
     ("g1f3", "g8f6", "f3g1"), "f6g8", "1/2-1/2", (1008, 1192)),
])
def test_all_natural_game_endings_update_elo(db, fen, moves, final_move,
                                             result, expected):
    white, black = create_players(db, (1000, 1000) if result == "0-1" else
                                  (1000, 1200))
    game = active_game(db, white, black, fen, moves)
    board = chess.Board(game.current_fen)
    player_id = white.id if board.turn == chess.WHITE else black.id
    game_service.make_move(db, game.id, player_id, final_move)

    db.refresh(white)
    db.refresh(black)
    assert game.status == "finished"
    assert game.result == result
    assert (white.elo, black.elo) == expected
    db.refresh(game)
    assert (game.white_elo_after, game.black_elo_after) == expected


def test_active_game_and_illegal_move_do_not_change_elo(db):
    white, black = create_players(db)
    game = active_game(db, white, black, moves=("e2e4", ))
    with pytest.raises(IllegalMove):
        game_service.make_move(db, game.id, black.id, "e7e4")
    db.refresh(white)
    db.refresh(black)
    assert (white.elo, black.elo) == (1000, 1000)


@pytest.mark.parametrize("failure_point", ["ratings", "commit"])
@pytest.mark.parametrize("ending", ["resign", "checkmate"])
def test_game_result_and_ratings_roll_back_together(db, monkeypatch,
                                                    failure_point, ending):
    white, black = create_players(db)
    moves = ("f2f3", "e7e5", "g2g4") if ending == "checkmate" else ()
    game = active_game(db, white, black, moves=moves)
    game_id = game.id
    original_pgn = game.pgn

    if failure_point == "ratings":
        original_update = elo_service.update_ratings

        def fail_after_update(*args):
            original_update(*args)
            raise RuntimeError("Simulated rating failure")

        monkeypatch.setattr(elo_service, "update_ratings", fail_after_update)
        expected_error = RuntimeError
    else:

        def fail_commit():
            raise SQLAlchemyError("Simulated commit failure")

        monkeypatch.setattr(db, "commit", fail_commit)
        expected_error = SQLAlchemyError

    with pytest.raises(expected_error):
        if ending == "checkmate":
            game_service.make_move(db, game_id, black.id, "d8h4")
        else:
            game_service.resign(db, game_id, black.id)

    assert db.is_active
    game = db.get(Game, game_id)
    db.refresh(white)
    db.refresh(black)
    assert game.status == "active"
    assert game.result is None
    assert game.finished_at is None
    assert game.white_elo_after is None
    assert game.black_elo_after is None
    assert game.pgn == original_pgn
    assert (white.elo, black.elo) == (1000, 1000)


def test_game_ending_reorders_leaderboard(db):
    white, black = create_players(db)
    game = active_game(db, white, black)
    game_service.resign(db, game.id, black.id)
    leaderboard = stats_service.get_leaderboard(db)
    assert [(entry.username, entry.elo)
            for entry in leaderboard] == [("Vigo", 1016), ("Louis", 984)]


@pytest.mark.parametrize("ending", ["accept_draw", "threefold", "fifty_move"])
def test_team_draw_endings_update_elo_once(db, ending):
    white, black = create_players(db, (1000, 1200))
    moves = ("g1f3", "g8f6", "f3g1", "f6g8") * 2 if ending == "threefold" else ()
    fen = "7k/8/8/8/8/8/1N6/K7 w - - 99 50" if ending == "fifty_move" else None
    game = active_game(db, white, black, fen=fen, moves=moves)

    if ending == "accept_draw":
        game_service.offer_draw(db, game.id, white.id)
        finish = game_service.accept_draw
        player_id = black.id
    elif ending == "threefold":
        finish = game_service.claim_threefold_repetition
        player_id = white.id
    else:
        finish = game_service.claim_fifty_move
        player_id = white.id

    finish(db, game.id, player_id)
    db.refresh(white)
    db.refresh(black)
    assert game.status == "finished"
    assert game.result == "1/2-1/2"
    assert (white.elo, black.elo) == (1008, 1192)
    assert stats_service.get_player_stats(db, white.id).elo == 1008
    with pytest.raises(game_service.GameNotActive):
        finish(db, game.id, player_id)
    db.refresh(white)
    db.refresh(black)
    assert (white.elo, black.elo) == (1008, 1192)


@pytest.mark.parametrize("timed_out_color,expected", [
    ("white", (984, 1016)),
    ("black", (1016, 984)),
])
def test_team_timeout_updates_elo_once(db, timed_out_color, expected):
    white, black = create_players(db)
    game = game_service.create_game(db, white.id, initial_time_seconds=10)
    start = datetime(2026, 10, 3, tzinfo=timezone.utc)

    with patch("backend.services.game_service.datetime") as game_datetime:
        game_datetime.now.return_value = start
        game_service.join_game(db, game.id, black.id)
        if timed_out_color == "black":
            game_service.make_move(db, game.id, white.id, "e2e4")
        game_datetime.now.return_value = start + timedelta(seconds=11)
        player_id = white.id if timed_out_color == "white" else black.id
        move = "e2e4" if timed_out_color == "white" else "e7e5"
        game_service.make_move(db, game.id, player_id, move)

    db.refresh(white)
    db.refresh(black)
    assert game.status == "finished"
    assert (white.elo, black.elo) == expected
    with pytest.raises(game_service.GameNotActive):
        game_service.make_move(db, game.id, player_id, move)
    db.refresh(white)
    db.refresh(black)
    assert (white.elo, black.elo) == expected


def test_elo_migration_initializes_existing_users_and_preserves_history(
        engine):
    migration_path = Path(
        __file__).parents[2] / "alembic/versions/e6a821f90d34_add_user_elo.py"
    spec = importlib.util.spec_from_file_location("add_user_elo",
                                                  migration_path)
    migration = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(migration)
    schema = "elo_migration_test_" + uuid4().hex

    with engine.connect() as connection:
        transaction = connection.begin()
        try:
            connection.execute(text("CREATE SCHEMA " + schema))
            connection.execute(text("SET LOCAL search_path TO " + schema))
            connection.execute(
                text(
                    "CREATE TABLE users (id INTEGER PRIMARY KEY, username TEXT NOT NULL)"
                ))
            connection.execute(text("INSERT INTO users VALUES (1, 'Vigo')"))
            connection.execute(
                text("CREATE TABLE games (id INTEGER PRIMARY KEY, result TEXT)"
                     ))
            connection.execute(text("INSERT INTO games VALUES (1, '1-0')"))

            with Operations.context(MigrationContext.configure(connection)):
                migration.upgrade()
                assert connection.scalar(
                    text("SELECT elo FROM users WHERE id = 1")) == INITIAL_ELO
                connection.execute(
                    text("INSERT INTO users (id, username) VALUES (2, 'Louis')"
                         ))
                assert connection.scalar(
                    text("SELECT elo FROM users WHERE id = 2")) == INITIAL_ELO
                with pytest.raises(IntegrityError):
                    with connection.begin_nested():
                        connection.execute(
                            text("UPDATE users SET elo = NULL WHERE id = 1"))
                assert connection.scalar(
                    text("SELECT result FROM games WHERE id = 1")) == "1-0"

                migration.downgrade()
                assert "elo" not in {
                    column["name"]
                    for column in inspect(connection).get_columns(
                        "users", schema=schema)
                }
                assert connection.scalar(
                    text("SELECT count(*) FROM users")) == 2
                assert connection.scalar(
                    text("SELECT result FROM games WHERE id = 1")) == "1-0"
        finally:
            transaction.rollback()


# PostgreSQL concurrency


@pytest.fixture
def players(engine):
    assert engine.dialect.name == "postgresql", "These tests require PostgreSQL"
    with Session(engine) as db:
        vigo = User(username="Vigo",
                    email="vigo@example.com",
                    password_hash="hashed-password")
        louis = User(username="Louis",
                     email="louis@example.com",
                     password_hash="hashed-password")
        db.add_all([vigo, louis])
        db.commit()
        return vigo.id, louis.id


def create_active_game(engine, white_id, black_id):
    with Session(engine) as db:
        game = game_service.create_game(db, white_id)
        game_service.join_game(db, game.id, black_id)
        return game.id


def run_contended(engine, monkeypatch, repository_type, lock_method,
                  first_operation, second_operation):
    locked = Event()
    attempting = Event()
    release = Event()
    second_done = Event()
    second_pid = []
    original = getattr(repository_type, lock_method)

    def pause_first(repository, *args):
        if current_thread().name.endswith("_1"):
            attempting.set()
        result = original(repository, *args)
        if current_thread().name.endswith("_0"):
            locked.set()
            assert release.wait(10), "First worker was not released"
        return result

    monkeypatch.setattr(repository_type, lock_method, pause_first)

    def run(operation, second=False):
        with Session(engine, autoflush=False) as db:
            db.execute(text("SET LOCAL lock_timeout = '8s'"))
            # Cache stale state before acquiring locks, as API authentication can.
            cached_players = db.query(User).all()
            cached_games = db.query(Game).all()
            if second:
                second_pid.append(db.scalar(text("SELECT pg_backend_pid()")))
            try:
                result = operation(db)
            except Exception as error:
                result = error
            if second:
                second_done.set()
            else:
                # Deliberately keep the first session open after any error.
                assert second_done.wait(10), "First operation retained a lock"
            return result

    with ThreadPoolExecutor(max_workers=2, thread_name_prefix="elo") as pool:
        first = pool.submit(run, first_operation)
        try:
            assert locked.wait(5), "First worker did not acquire its lock"
            second = pool.submit(run, second_operation, True)
            assert attempting.wait(5), "Second worker did not attempt its lock"
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
                        "Second connection never waited for the database lock")
            assert not second.done()
        finally:
            release.set()
        return first.result(timeout=12), second.result(timeout=12)


def resign(db, game_id, player_id):
    game_service.resign(db, game_id, player_id)
    return "finished"


def test_two_finishes_of_same_game_change_elo_once(engine, players,
                                                   monkeypatch):
    vigo_id, louis_id = players
    game_id = create_active_game(engine, vigo_id, louis_id)
    first, second = run_contended(engine, monkeypatch, GameRepository,
                                  "get_by_id_for_update",
                                  lambda db: resign(db, game_id, louis_id),
                                  lambda db: resign(db, game_id, louis_id))

    assert first == "finished"
    assert isinstance(second, CannotResignFinishedGame)
    with Session(engine) as db:
        game = db.get(Game, game_id)
        assert (game.white_elo_after, game.black_elo_after) == (1016, 984)
        assert len(stats_service.get_player_profile(db, "Vigo").elo_history) == 1
        assert (db.get(User, vigo_id).elo, db.get(User,
                                                  louis_id).elo) == (1016, 984)


def test_concurrent_games_with_reversed_colors_preserve_both_updates(
        engine, players, monkeypatch):
    vigo_id, louis_id = players
    first_id = create_active_game(engine, vigo_id, louis_id)
    second_id = create_active_game(engine, louis_id, vigo_id)
    first, second = run_contended(engine, monkeypatch, StatsRepository,
                                  "get_players_for_update",
                                  lambda db: resign(db, first_id, louis_id),
                                  lambda db: resign(db, second_id, louis_id))

    assert first == second == "finished"
    expected = elo_service.calculate_ratings(1016, 984, 1.0)
    with Session(engine) as db:
        assert (db.get(User, vigo_id).elo, db.get(User,
                                                  louis_id).elo) == expected
        assert expected == (1031, 969)
        first_game, second_game = db.get(Game, first_id), db.get(Game, second_id)
        assert (first_game.white_elo_after, first_game.black_elo_after) == (1016, 984)
        assert (second_game.white_elo_after, second_game.black_elo_after) == (969, 1031)
        assert [point.elo for point in
                stats_service.get_player_profile(db, "Vigo").elo_history] == [1016, 1031]


def test_invalid_move_releases_game_lock_for_waiting_finish(
        engine, players, monkeypatch):
    vigo_id, louis_id = players
    game_id = create_active_game(engine, vigo_id, louis_id)
    first, second = run_contended(
        engine, monkeypatch, GameRepository, "get_by_id_for_update",
        lambda db: game_service.make_move(db, game_id, vigo_id, "e2e5"),
        lambda db: resign(db, game_id, louis_id))

    assert isinstance(first, IllegalMove)
    assert second == "finished"
    with Session(engine) as db:
        assert (db.get(User, vigo_id).elo, db.get(User,
                                                  louis_id).elo) == (1016, 984)


def test_recorded_elo_survives_later_rating_changes(db):
    white, black = create_players(db)
    first = active_game(db, white, black)
    game_service.resign(db, first.id, black.id)
    second = active_game(db, white, black)
    game_service.resign(db, second.id, black.id)
    db.refresh(first)
    db.refresh(second)
    assert (first.white_elo_after, first.black_elo_after) == (1016, 984)
    assert (second.white_elo_after, second.black_elo_after) == (1031, 969)


def test_equal_rating_draw_records_an_unchanged_elo(db):
    white, black = create_players(db)
    game = active_game(db, white, black)
    assert game.white_elo_after is None and game.black_elo_after is None
    game_service.offer_draw(db, game.id, white.id)
    game_service.accept_draw(db, game.id, black.id)
    db.refresh(game)
    assert (game.white_elo_after, game.black_elo_after) == (1000, 1000)
    history = stats_service.get_player_profile(db, "Vigo").elo_history
    assert len(history) == 1
    assert history[0].elo == 1000
    assert history[0].date == game.finished_at


def test_ai_game_finishes_without_recording_or_changing_elo(db):
    white, _ = create_players(db)
    game = game_service.create_game(db, white.id, opponent_type="ai",
                                    ai_difficulty="easy")
    game_service.resign(db, game.id, white.id)
    db.refresh(white)
    db.refresh(game)
    assert game.status == "finished"
    assert white.elo == 1000
    assert game.white_elo_after is None and game.black_elo_after is None
    assert stats_service.get_player_profile(db, "Vigo").elo_history == []


def test_game_elo_history_migration_preserves_old_games_and_is_reversible(engine):
    migration_path = Path(__file__).parents[2] / (
        "alembic/versions/f3c92a781b60_add_game_elo_history.py")
    spec = importlib.util.spec_from_file_location("add_game_elo_history", migration_path)
    migration = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(migration)
    schema = "elo_history_test_" + uuid4().hex

    with engine.connect() as connection:
        transaction = connection.begin()
        try:
            connection.execute(text("CREATE SCHEMA " + schema))
            connection.execute(text("SET LOCAL search_path TO " + schema))
            connection.execute(text("CREATE TABLE games (id INTEGER PRIMARY KEY, result TEXT)"))
            connection.execute(text("INSERT INTO games VALUES (1, '1-0')"))
            with Operations.context(MigrationContext.configure(connection)):
                migration.upgrade()
                assert tuple(connection.execute(text(
                    "SELECT result, white_elo_after, black_elo_after FROM games WHERE id = 1"
                )).one()) == ("1-0", None, None)
                connection.execute(text(
                    "UPDATE games SET white_elo_after = 1016, black_elo_after = 984 WHERE id = 1"))
                migration.downgrade()
                columns = {column["name"] for column in inspect(connection).get_columns(
                    "games", schema=schema)}
                assert columns == {"id", "result"}
                assert connection.scalar(text("SELECT result FROM games WHERE id = 1")) == "1-0"
        finally:
            transaction.rollback()
