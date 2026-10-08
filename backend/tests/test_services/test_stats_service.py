from datetime import datetime, timezone

import chess
import chess.pgn
import pytest
from backend.models.game import Game
from backend.models.user import User
from backend.services import stats_service


def create_user(db, username="player1", email="player1@example.com"):
    user = User(username=username,
                email=email,
                password_hash="hashed-password")
    db.add(user)
    db.commit()
    return user


def build_pgn(moves: list[str], result: str) -> str:
    board = chess.Board()
    game = chess.pgn.Game()
    node = game

    for uci in moves:
        move = chess.Move.from_uci(uci)
        node = node.add_variation(move)
        board.push(move)

    game.headers["Result"] = result
    return str(game)


def create_finished_game(db,
                         white,
                         black,
                         result,
                         moves=("e2e4", "e7e5"),
                         finished_at=None):
    game = Game(white_player_id=white.id,
                black_player_id=black.id,
                status="finished",
                result=result,
                current_fen=chess.Board().fen(),
                pgn=build_pgn(list(moves), result),
                finished_at=finished_at or datetime.now(timezone.utc))
    db.add(game)
    db.commit()
    return game


def test_get_player_stats_counts_wins_losses_and_draws(db):
    alice = create_user(db, "alice", "alice@example.com")
    bob = create_user(db, "bob", "bob@example.com")

    create_finished_game(db, alice, bob, "1-0")  # alice (white) wins
    create_finished_game(db, bob, alice, "0-1")  # alice (black) wins
    create_finished_game(db, alice, bob, "1/2-1/2")  # draw

    alice.elo = 1234
    db.commit()

    stats = stats_service.get_player_stats(db, alice.id)

    assert stats.elo == 1234
    assert stats_service.get_player_stats(db, alice.id).elo == 1234
    assert stats.games_played == 3
    assert stats.wins == 2
    assert stats.losses == 0
    assert stats.draws == 1
    assert stats.win_rate == pytest.approx(2 / 3, abs=1e-3)


def test_get_player_stats_with_no_games(db):
    alice = create_user(db)

    stats = stats_service.get_player_stats(db, alice.id)

    assert stats.elo == 1000
    assert stats.games_played == 0
    assert stats.win_rate == 0.0


def test_get_match_history_orders_most_recent_first(db):
    alice = create_user(db, "alice", "alice@example.com")
    bob = create_user(db, "bob", "bob@example.com")

    create_finished_game(db,
                         alice,
                         bob,
                         "1-0",
                         moves=["e2e4", "e7e5", "f1c4"],
                         finished_at=datetime(2026, 1, 1, tzinfo=timezone.utc))

    create_finished_game(db,
                         bob,
                         alice,
                         "0-1",
                         moves=["d2d4"],
                         finished_at=datetime(2026, 1, 2, tzinfo=timezone.utc))

    history = stats_service.get_match_history(db, alice.id)

    assert len(history) == 2
    assert history[0].opponent == "bob"
    assert history[0].outcome == "win"
    assert history[0].moves_played == 1
    assert history[1].opponent == "bob"
    assert history[1].outcome == "win"
    assert history[1].moves_played == 3


def test_get_leaderboard_ranks_by_elo_even_with_fewer_wins(db):
    alice = create_user(db, "alice", "alice@example.com")
    bob = create_user(db, "bob", "bob@example.com")

    create_finished_game(db, alice, bob, "1-0")
    create_finished_game(db, alice, bob, "1-0")
    create_finished_game(db, alice, bob, "0-1")

    bob.elo = 1200
    db.commit()

    leaderboard = stats_service.get_leaderboard(db)

    assert leaderboard[0].username == "bob"
    assert leaderboard[0].elo == 1200
    assert leaderboard[0].wins == 1
    assert leaderboard[1].username == "alice"
    assert leaderboard[1].elo == 1000
    assert leaderboard[1].wins == 2


def test_equal_elo_is_sorted_by_username_without_replaying_history(db):
    vigo = create_user(db, "Vigo", "vigo@example.com")
    louis = create_user(db, "Louis", "louis@example.com")
    create_finished_game(db, vigo, louis, "1-0")

    first = stats_service.get_leaderboard(db)
    second = stats_service.get_leaderboard(db)

    assert [entry.username for entry in first] == ["Louis", "Vigo"]
    assert [entry.elo for entry in first] == [1000, 1000]
    assert first == second


def test_profile_history_selects_color_and_orders_by_date_then_id(db):
    vigo = create_user(db, "Vigo", "vigo@example.com")
    louis = create_user(db, "Louis", "louis@example.com")
    date = datetime(2026, 10, 6, tzinfo=timezone.utc)
    later = create_finished_game(db, louis, vigo, "0-1", finished_at=date)
    earlier_date = datetime(2026, 10, 5, tzinfo=timezone.utc)
    earlier = create_finished_game(db, vigo, louis, "1-0", finished_at=earlier_date)
    same_date = create_finished_game(db, vigo, louis, "1-0", finished_at=date)
    earlier.white_elo_after, earlier.black_elo_after = 1016, 984
    later.white_elo_after, later.black_elo_after = 969, 1031
    same_date.white_elo_after, same_date.black_elo_after = 1044, 956
    db.commit()

    profile = stats_service.get_player_profile(db, "Vigo")
    assert [(point.date, point.elo) for point in profile.elo_history] == [
        (earlier_date, 1016), (date, 1031), (date, 1044)]
    assert all(point.date.utcoffset().total_seconds() == 0
               for point in profile.elo_history)


def test_profile_history_excludes_legacy_ai_active_and_other_players(db):
    vigo = create_user(db, "Vigo", "vigo@example.com")
    louis = create_user(db, "Louis", "louis@example.com")
    raph = create_user(db, "Raph", "raph@example.com")
    # Old games still count in statistics but have no recorded Elo.
    create_finished_game(db, vigo, louis, "1-0")
    ai = create_finished_game(db, vigo, louis, "1-0")
    ai.opponent_type, ai.black_player_id = "ai", None
    active = create_finished_game(db, vigo, louis, "1-0")
    active.status = "active"
    other = create_finished_game(db, louis, raph, "1-0")
    for game in (ai, active, other):
        game.white_elo_after, game.black_elo_after = 1016, 984
    db.commit()

    profile = stats_service.get_player_profile(db, "Vigo")
    assert profile.elo_history == []
    assert profile.elo == 1000
    assert profile.games_played == 2


def test_new_player_profile_has_empty_history(db):
    create_user(db, "Chikako", "chikako@example.com")
    profile = stats_service.get_player_profile(db, "Chikako")
    assert profile.elo == 1000
    assert profile.elo_history == []


def test_leaderboard_does_not_load_elo_history(db, monkeypatch):
    from backend.repositories.stats_repository import StatsRepository

    create_user(db)

    def unexpected_history(*args):
        raise AssertionError("The leaderboard must not load profile history")

    monkeypatch.setattr(StatsRepository, "list_elo_history", unexpected_history)
    assert len(stats_service.get_leaderboard(db)) == 1
