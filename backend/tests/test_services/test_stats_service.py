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

    stats = stats_service.get_player_stats(db, alice.id)

    assert stats.games_played == 3
    assert stats.wins == 2
    assert stats.losses == 0
    assert stats.draws == 1
    assert stats.win_rate == pytest.approx(2 / 3, abs=1e-3)


def test_get_player_stats_with_no_games(db):
    alice = create_user(db)

    stats = stats_service.get_player_stats(db, alice.id)

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


def test_get_leaderboard_ranks_players_by_wins(db):
    alice = create_user(db, "alice", "alice@example.com")
    bob = create_user(db, "bob", "bob@example.com")

    create_finished_game(db, alice, bob, "1-0")
    create_finished_game(db, alice, bob, "1-0")
    create_finished_game(db, alice, bob, "0-1")

    leaderboard = stats_service.get_leaderboard(db)

    assert leaderboard[0].username == "alice"
    assert leaderboard[0].wins == 2
    assert leaderboard[1].username == "bob"
    assert leaderboard[1].wins == 1
