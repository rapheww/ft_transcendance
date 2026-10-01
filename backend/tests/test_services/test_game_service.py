import chess
import pytest
from backend.exceptions.game import CannotPlayAgainstSelf, GameNotFound, GameNotJoinable, GameNotActive, NotAPlayer, IllegalMove, CannotResignFinishedGame
from backend.models.user import User
from backend.services import game_service
from datetime import datetime, timezone, timedelta
from unittest.mock import patch


def create_user(db, username="player1", email="player1@example.com"):
    user = User(username=username,
                email=email,
                password_hash="hashed-password")
    db.add(user)
    db.commit()
    return user


def test_create_game(db):
    user = create_user(db)
    game = game_service.create_game(db, user.id)

    assert game.id is not None
    assert game.white_player_id == user.id
    assert game.black_player_id is None
    assert game.status == "waiting"
    assert game.result is None
    assert game.current_fen == chess.Board().fen()
    assert '[Result "*"]' in game.pgn
    assert game.pgn.rstrip().endswith("*")
    assert game.finished_at is None

    assert game.initial_time_seconds is None
    assert game.increment_seconds == 0
    assert game.white_time_remaining is None
    assert game.black_time_remaining is None


def test_create_game_with_unknown_user(db):
    with pytest.raises(Exception):
        game_service.create_game(db, 999999)


def test_join_game(db):
    white = create_user(db)
    black = create_user(db, username="player2", email="player2@example.com")

    game = game_service.create_game(db, white.id)
    result = game_service.join_game(db, game.id, black.id)

    assert result.id == game.id
    assert result.white_player_id == white.id
    assert result.black_player_id == black.id
    assert result.status == "active"
    assert result.result is None


def test_join_game_with_unknown_game(db):
    black = create_user(db)

    with pytest.raises(GameNotFound):
        game_service.join_game(db, 999999, black.id)


def test_join_game_with_unknown_user(db):
    white = create_user(db)
    game = game_service.create_game(db, white.id)

    with pytest.raises(Exception):
        game_service.join_game(db, game.id, 999999)


def test_join_game_when_game_is_not_waiting(db):
    white = create_user(db)
    black = create_user(db, username="player2", email="player2@example.com")
    game = game_service.create_game(db, white.id)

    game_service.join_game(db, game.id, black.id)
    third_player = create_user(db,
                               username="player3",
                               email="player3@example.com")

    with pytest.raises(GameNotJoinable):
        game_service.join_game(db, game.id, third_player.id)


def test_creator_cannot_join_own_game(db):
    white = create_user(db)
    game = game_service.create_game(db, white.id)

    with pytest.raises(CannotPlayAgainstSelf):
        game_service.join_game(db, game.id, white.id)


def test_make_move(db):
    white = create_user(db)
    black = create_user(db, username="player2", email="player2@example.com")
    game = game_service.create_game(db, white.id)
    game_service.join_game(db, game.id, black.id)

    result = game_service.make_move(db, game.id, white.id, "e2e4")
    board = chess.Board(result.current_fen)

    assert board.piece_at(chess.E4) == chess.Piece(chess.PAWN, chess.WHITE)
    assert board.piece_at(chess.E2) is None
    assert board.turn == chess.BLACK

    assert "1. e4" in result.pgn


def test_make_second_move(db):
    white = create_user(db)
    black = create_user(db, username="player2", email="player2@example.com")
    game = game_service.create_game(db, white.id)
    game_service.join_game(db, game.id, black.id)

    game_service.make_move(db, game.id, white.id, "e2e4")
    result = game_service.make_move(db, game.id, black.id, "e7e5")
    board = chess.Board(result.current_fen)

    assert board.piece_at(chess.E4) == chess.Piece(chess.PAWN, chess.WHITE)
    assert board.piece_at(chess.E5) == chess.Piece(chess.PAWN, chess.BLACK)
    assert board.turn == chess.WHITE

    assert "1. e4 e5" in result.pgn


def test_make_move_when_not_your_turn(db):
    white = create_user(db)
    black = create_user(db, username="player2", email="player2@example.com")
    game = game_service.create_game(db, white.id)

    game_service.join_game(db, game.id, black.id)
    game_service.make_move(db, game.id, white.id, "e2e4")

    with pytest.raises(game_service.NotYourTurn):
        game_service.make_move(db, game.id, white.id, "g1f3")


def test_black_can_move_on_black_turn(db):
    white = create_user(db)
    black = create_user(db, username="player2", email="player2@example.com")
    game = game_service.create_game(db, white.id)
    game_service.join_game(db, game.id, black.id)

    game_service.make_move(db, game.id, white.id, "e2e4")
    result = game_service.make_move(db, game.id, black.id, "e7e5")

    board = chess.Board(result.current_fen)

    assert board.piece_at(chess.E5) == chess.Piece(chess.PAWN, chess.BLACK)
    assert board.turn == chess.WHITE


def test_make_illegal_move(db):
    white = create_user(db)
    black = create_user(db, username="player2", email="player2@example.com")
    game = game_service.create_game(db, white.id)
    game_service.join_game(db, game.id, black.id)

    original_fen = game.current_fen
    original_pgn = game.pgn

    with pytest.raises(IllegalMove):
        game_service.make_move(db, game.id, white.id, "e2e5")

    assert game.current_fen == original_fen
    assert game.pgn == original_pgn
    assert game.status == "active"


def test_make_move_with_invalid_uci(db):
    white = create_user(db)
    black = create_user(db, username="player2", email="player2@example.com")
    game = game_service.create_game(db, white.id)
    game_service.join_game(db, game.id, black.id)

    original_fen = game.current_fen
    original_pgn = game.pgn

    with pytest.raises(IllegalMove):
        game_service.make_move(db, game.id, white.id, "banana")

    assert game.current_fen == original_fen
    assert game.pgn == original_pgn


def test_make_move_when_user_is_not_a_player(db):
    white = create_user(db)
    black = create_user(db, username="player2", email="player2@example.com")
    outsider = create_user(db, username="player3", email="player3@example.com")

    game = game_service.create_game(db, white.id)
    game_service.join_game(db, game.id, black.id)

    with pytest.raises(NotAPlayer):
        game_service.make_move(db, game.id, outsider.id, "e2e4")


def test_make_move_when_game_is_not_active(db):
    white = create_user(db)
    game = game_service.create_game(db, white.id)

    with pytest.raises(GameNotActive):
        game_service.make_move(db, game.id, white.id, "e2e4")


def test_make_move_with_unknown_game(db):
    white = create_user(db)

    with pytest.raises(GameNotFound):
        game_service.make_move(db, 999999, white.id, "e2e4")


def test_checkmate_ends_game(db):
    white = create_user(db)
    black = create_user(db, username="player2", email="player2@example.com")

    game = game_service.create_game(db, white.id)
    game_service.join_game(db, game.id, black.id)

    game_service.make_move(db, game.id, white.id, "e2e4")
    game_service.make_move(db, game.id, black.id, "e7e5")
    game_service.make_move(db, game.id, white.id, "f1c4")
    game_service.make_move(db, game.id, black.id, "b8c6")
    game_service.make_move(db, game.id, white.id, "d1h5")
    game_service.make_move(db, game.id, black.id, "g8f6")

    result = game_service.make_move(db, game.id, white.id, "h5f7")
    board = chess.Board(result.current_fen)

    assert board.is_checkmate()
    assert result.status == "finished"
    assert result.result == "1-0"
    assert result.finished_at is not None


def test_make_move_after_checkmate_is_rejected(db):
    white = create_user(db)
    black = create_user(db, username="player2", email="player2@example.com")

    game = game_service.create_game(db, white.id)
    game_service.join_game(db, game.id, black.id)

    game_service.make_move(db, game.id, white.id, "e2e4")
    game_service.make_move(db, game.id, black.id, "e7e5")
    game_service.make_move(db, game.id, white.id, "f1c4")
    game_service.make_move(db, game.id, black.id, "b8c6")
    game_service.make_move(db, game.id, white.id, "d1h5")
    game_service.make_move(db, game.id, black.id, "g8f6")
    game_service.make_move(db, game.id, white.id, "h5f7")

    with pytest.raises(GameNotActive):
        game_service.make_move(db, game.id, black.id, "e7e6")


def test_stalemate_ends_game_as_draw(db):
    white = create_user(db)
    black = create_user(db, username="player2", email="player2@example.com")

    game = game_service.create_game(db, white.id)
    game_service.join_game(db, game.id, black.id)
    fen = "7k/5K2/8/6Q1/8/8/8/8 w - - 0 1"

    pgn_game = chess.pgn.Game()
    pgn_game.headers["SetUp"] = "1"
    pgn_game.headers["FEN"] = fen
    pgn_game.headers["Result"] = "*"

    game.current_fen = fen
    game.pgn = str(pgn_game)
    db.commit()

    result = game_service.make_move(db, game.id, white.id, "g5g6")
    board = chess.Board(result.current_fen)

    assert board.is_stalemate()
    assert result.status == "finished"
    assert result.result == "1/2-1/2"
    assert result.finished_at is not None


def test_insufficient_material_ends_game_as_draw(db):
    white = create_user(db)
    black = create_user(db, username="player2", email="player2@example.com")

    game = game_service.create_game(db, white.id)
    game_service.join_game(db, game.id, black.id)

    fen = "7k/8/8/8/8/8/1B6/K7 w - - 0 1"

    pgn_game = chess.pgn.Game()
    pgn_game.headers["SetUp"] = "1"
    pgn_game.headers["FEN"] = fen
    pgn_game.headers["Result"] = "*"

    game.current_fen = fen
    game.pgn = str(pgn_game)
    db.commit()

    result = game_service.make_move(db, game.id, white.id, "b2c3")
    board = chess.Board(result.current_fen)

    assert board.is_insufficient_material()
    assert result.status == "finished"
    assert result.result == "1/2-1/2"
    assert result.finished_at is not None


def test_pgn_reconstructs_move_history(db):
    white = create_user(db)
    black = create_user(db, username="player2", email="player2@example.com")

    game = game_service.create_game(db, white.id)
    game_service.join_game(db, game.id, black.id)

    game_service.make_move(db, game.id, white.id, "g1f3")
    game_service.make_move(db, game.id, black.id, "g8f6")
    game_service.make_move(db, game.id, white.id, "f3g1")
    game_service.make_move(db, game.id, black.id, "f6g8")

    pgn_game = chess.pgn.read_game(__import__("io").StringIO(game.pgn))
    board = pgn_game.board()

    for move in pgn_game.mainline_moves():
        board.push(move)

    assert board.fullmove_number == 3
    assert board.turn == chess.WHITE
    assert board.is_fivefold_repetition() is False


def test_fivefold_repetition_ends_game_as_draw(db):
    white = create_user(db)
    black = create_user(db, username="player2", email="player2@example.com")

    game = game_service.create_game(db, white.id)
    game_service.join_game(db, game.id, black.id)

    moves = [(white.id, "g1f3"), (black.id, "g8f6"), (white.id, "f3g1"),
             (black.id, "f6g8"), (white.id, "g1f3"), (black.id, "g8f6"),
             (white.id, "f3g1"), (black.id, "f6g8"), (white.id, "g1f3"),
             (black.id, "g8f6"), (white.id, "f3g1"), (black.id, "f6g8"),
             (white.id, "g1f3"), (black.id, "g8f6"), (white.id, "f3g1"),
             (black.id, "f6g8")]

    result = None

    for player_id, move in moves:
        result = game_service.make_move(db, game.id, player_id, move)

    assert result.status == "finished"
    assert result.result == "1/2-1/2"
    assert result.finished_at is not None


def test_seventyfive_move_rule_ends_game_as_draw(db):
    white = create_user(db)
    black = create_user(db, username="player2", email="player2@example.com")

    game = game_service.create_game(db, white.id)
    game_service.join_game(db, game.id, black.id)

    fen = "7k/8/8/8/8/8/1N6/K7 w - - 149 76"

    pgn_game = chess.pgn.Game()
    pgn_game.headers["SetUp"] = "1"
    pgn_game.headers["FEN"] = fen
    pgn_game.headers["Result"] = "*"

    game.current_fen = fen
    game.pgn = str(pgn_game)
    db.commit()

    result = game_service.make_move(db, game.id, white.id, "b2c4")

    assert result.status == "finished"
    assert result.result == "1/2-1/2"
    assert result.finished_at is not None


def test_player_can_resign(db):
    white = create_user(db)
    black = create_user(db, username="player2", email="player2@example.com")

    game = game_service.create_game(db, white.id)
    game_service.join_game(db, game.id, black.id)
    result = game_service.resign(db, game.id, white.id)

    assert result.status == "finished"
    assert result.result == "0-1"
    assert result.finished_at is not None


def test_black_resigning_gives_white_the_win(db):
    white = create_user(db)
    black = create_user(db, username="player2", email="player2@example.com")

    game = game_service.create_game(db, white.id)
    game_service.join_game(db, game.id, black.id)
    result = game_service.resign(db, game.id, black.id)

    assert result.status == "finished"
    assert result.result == "1-0"
    assert result.finished_at is not None


def test_outsider_cannot_resign_game(db):
    white = create_user(db)
    black = create_user(db, username="player2", email="player2@example.com")
    outsider = create_user(db, username="player3", email="player3@example.com")

    game = game_service.create_game(db, white.id)
    game_service.join_game(db, game.id, black.id)

    with pytest.raises(NotAPlayer):
        game_service.resign(db, game.id, outsider.id)


def test_cannot_resign_finished_game(db):
    white = create_user(db)
    black = create_user(db, username="player2", email="player2@example.com")

    game = game_service.create_game(db, white.id)
    game_service.join_game(db, game.id, black.id)
    game_service.resign(db, game.id, white.id)

    with pytest.raises(CannotResignFinishedGame):
        game_service.resign(db, game.id, black.id)


def test_finished_game_has_consistent_state_after_resign(db):
    white = create_user(db)
    black = create_user(db, username="player2", email="player2@example.com")

    game = game_service.create_game(db, white.id)
    game_service.join_game(db, game.id, black.id)
    result = game_service.resign(db, game.id, white.id)

    assert result.status == "finished"
    assert result.result is not None
    assert result.finished_at is not None


def test_active_game_has_no_result(db):
    white = create_user(db)
    black = create_user(db, username="player2", email="player2@example.com")

    game = game_service.create_game(db, white.id)
    result = game_service.join_game(db, game.id, black.id)

    assert result.status == "active"
    assert result.result is None
    assert result.finished_at is None


def test_waiting_game_has_no_result(db):
    white = create_user(db)
    game = game_service.create_game(db, white.id)

    assert game.status == "waiting"
    assert game.result is None
    assert game.finished_at is None


def test_create_game_with_custom_time_control(db):
    user = create_user(db)
    game = game_service.create_game(db,
                                    user.id,
                                    initial_time_seconds=300,
                                    increment_seconds=5)

    assert game.initial_time_seconds == 300
    assert game.increment_seconds == 5
    assert game.white_time_remaining == 300
    assert game.black_time_remaining == 300


def test_create_game_with_different_time_control(db):
    user = create_user(db)
    game = game_service.create_game(db,
                                    user.id,
                                    initial_time_seconds=600,
                                    increment_seconds=10)

    assert game.initial_time_seconds == 600
    assert game.increment_seconds == 10


def test_create_game_with_ten_minute_time_control(db):
    user = create_user(db)
    game = game_service.create_game(db,
                                    user.id,
                                    initial_time_seconds=600,
                                    increment_seconds=0)

    assert game.initial_time_seconds == 600
    assert game.increment_seconds == 0
    assert game.white_time_remaining == 600
    assert game.black_time_remaining == 600


def test_join_game_starts_clock(db):
    white = create_user(db)
    black = create_user(db, username="player2", email="player2@example.com")

    before = datetime.now(timezone.utc)
    game = game_service.create_game(db,
                                    white.id,
                                    initial_time_seconds=600,
                                    increment_seconds=0)

    result = game_service.join_game(db, game.id, black.id)
    after = datetime.now(timezone.utc)

    assert result.last_move_at is not None
    assert before <= result.last_move_at <= after


def test_elapsed_time_is_deducted_from_clock(db):
    white = create_user(db)
    black = create_user(db, username="player2", email="player2@example.com")

    game = game_service.create_game(db,
                                    white.id,
                                    initial_time_seconds=600,
                                    increment_seconds=0)
    start = datetime(2026, 10, 1, 19, 0, 0, tzinfo=timezone.utc)

    with patch("backend.services.game_service.datetime") as mock_datetime:
        mock_datetime.now.return_value = start

        game_service.join_game(db, game.id, black.id)
        mock_datetime.now.return_value = start.replace(second=7)
        result = game_service.make_move(db, game.id, white.id, "e2e4")

    assert result.white_time_remaining == 593
    assert result.black_time_remaining == 600


def test_increment_is_added_after_move(db):
    white = create_user(db)
    black = create_user(db, username="player2", email="player2@example.com")

    game = game_service.create_game(db,
                                    white.id,
                                    initial_time_seconds=600,
                                    increment_seconds=5)
    start = datetime(2026, 10, 1, 19, 0, 0, tzinfo=timezone.utc)

    with patch("backend.services.game_service.datetime") as mock_datetime:
        mock_datetime.now.return_value = start
        game_service.join_game(db, game.id, black.id)

        mock_datetime.now.return_value = start.replace(second=7)
        result = game_service.make_move(db, game.id, white.id, "e2e4")

    assert result.white_time_remaining == 598
    assert result.black_time_remaining == 600


def test_white_times_out(db):
    white = create_user(db)
    black = create_user(db, username="player2", email="player2@example.com")

    game = game_service.create_game(db,
                                    white.id,
                                    initial_time_seconds=10,
                                    increment_seconds=0)
    start = datetime(2026, 10, 1, 19, 0, 0, tzinfo=timezone.utc)

    with patch("backend.services.game_service.datetime") as mock_datetime:
        mock_datetime.now.return_value = start
        game_service.join_game(db, game.id, black.id)

        mock_datetime.now.return_value = start.replace(second=11)
        result = game_service.make_move(db, game.id, white.id, "e2e4")

    assert result.status == "finished"
    assert result.result == "0-1"
    assert result.white_time_remaining == 0
    assert result.black_time_remaining == 10
    assert result.finished_at is not None


def test_black_times_out(db):
    white = create_user(db)
    black = create_user(db, username="player2", email="player2@example.com")

    game = game_service.create_game(db,
                                    white.id,
                                    initial_time_seconds=10,
                                    increment_seconds=0)
    start = datetime(2026, 10, 1, 19, 0, 0, tzinfo=timezone.utc)

    with patch("backend.services.game_service.datetime") as mock_datetime:
        mock_datetime.now.return_value = start
        game_service.join_game(db, game.id, black.id)

        mock_datetime.now.return_value = start
        game_service.make_move(db, game.id, white.id, "e2e4")

        mock_datetime.now.return_value = start.replace(second=11)
        result = game_service.make_move(db, game.id, black.id, "e7e5")

    assert result.status == "finished"
    assert result.result == "1-0"
    assert result.white_time_remaining == 10
    assert result.black_time_remaining == 0
    assert result.finished_at is not None


def test_cannot_move_after_timeout(db):
    white = create_user(db)
    black = create_user(db, username="player2", email="player2@example.com")

    game = game_service.create_game(db,
                                    white.id,
                                    initial_time_seconds=10,
                                    increment_seconds=0)
    start = datetime(2026, 10, 1, 19, 0, 0, tzinfo=timezone.utc)

    with patch("backend.services.game_service.datetime") as mock_datetime:
        mock_datetime.now.return_value = start
        game_service.join_game(db, game.id, black.id)

        mock_datetime.now.return_value = start.replace(second=11)
        game_service.make_move(db, game.id, white.id, "e2e4")

    with pytest.raises(GameNotActive):
        game_service.make_move(db, game.id, black.id, "e7e5")


def test_untimed_game_does_not_use_clock(db):
    white = create_user(db)
    black = create_user(db, username="player2", email="player2@example.com")

    game = game_service.create_game(db, white.id)
    start = datetime(2026, 10, 1, 19, 0, 0, tzinfo=timezone.utc)

    with patch("backend.services.game_service.datetime") as mock_datetime:
        mock_datetime.now.return_value = start
        result = game_service.join_game(db, game.id, black.id)

        mock_datetime.now.return_value = start + timedelta(seconds=100)
        result = game_service.make_move(db, game.id, white.id, "e2e4")

    assert result.status == "active"
    assert result.initial_time_seconds is None
    assert result.white_time_remaining is None
    assert result.black_time_remaining is None
    assert result.last_move_at is None


def test_waiting_game_does_not_consume_time(db):
    white = create_user(db)
    game = game_service.create_game(db,
                                    white.id,
                                    initial_time_seconds=600,
                                    increment_seconds=0)

    assert game.status == "waiting"
    assert game.white_time_remaining == 600
    assert game.black_time_remaining == 600
    assert game.last_move_at is None


def test_resign_updates_clock(db):
    white = create_user(db)
    black = create_user(db, username="player2", email="player2@example.com")

    game = game_service.create_game(db,
                                    white.id,
                                    initial_time_seconds=600,
                                    increment_seconds=0)
    start = datetime(2026, 10, 1, 19, 0, 0, tzinfo=timezone.utc)

    with patch("backend.services.game_service.datetime") as mock_datetime:
        mock_datetime.now.return_value = start
        game_service.join_game(db, game.id, black.id)

        mock_datetime.now.return_value = start + timedelta(seconds=4)
        result = game_service.resign(db, game.id, white.id)

    assert result.status == "finished"
    assert result.result == "0-1"
    assert result.white_time_remaining == 596
    assert result.black_time_remaining == 600


def test_player_can_offer_draw(db):
    white = create_user(db)
    black = create_user(db, username="player2", email="player2@example.com")

    game = game_service.create_game(db, white.id)
    game_service.join_game(db, game.id, black.id)

    result = game_service.offer_draw(db, game.id, white.id)

    assert result.draw_offer_by == white.id
    assert result.status == "active"
    assert result.result is None


def test_black_can_offer_draw(db):
    white = create_user(db)
    black = create_user(db, username="player2", email="player2@example.com")

    game = game_service.create_game(db, white.id)
    game_service.join_game(db, game.id, black.id)

    result = game_service.offer_draw(db, game.id, black.id)

    assert result.draw_offer_by == black.id


def test_cannot_offer_draw_when_offer_already_exists(db):
    white = create_user(db)
    black = create_user(db, username="player2", email="player2@example.com")

    game = game_service.create_game(db, white.id)
    game_service.join_game(db, game.id, black.id)

    game_service.offer_draw(db, game.id, white.id)

    with pytest.raises(game_service.DrawOfferAlreadyExists):
        game_service.offer_draw(db, game.id, black.id)


def test_outsider_cannot_offer_draw(db):
    white = create_user(db)
    black = create_user(db, username="player2", email="player2@example.com")
    outsider = create_user(db, username="player3", email="player3@example.com")

    game = game_service.create_game(db, white.id)
    game_service.join_game(db, game.id, black.id)

    with pytest.raises(NotAPlayer):
        game_service.offer_draw(db, game.id, outsider.id)


def test_cannot_offer_draw_on_finished_game(db):
    white = create_user(db)
    black = create_user(db, username="player2", email="player2@example.com")

    game = game_service.create_game(db, white.id)
    game_service.join_game(db, game.id, black.id)

    game_service.resign(db, game.id, white.id)

    with pytest.raises(GameNotActive):
        game_service.offer_draw(db, game.id, black.id)


def test_opponent_can_accept_draw_offer(db):
    white = create_user(db)
    black = create_user(db, username="player2", email="player2@example.com")

    game = game_service.create_game(db, white.id)
    game_service.join_game(db, game.id, black.id)

    game_service.offer_draw(db, game.id, white.id)
    result = game_service.accept_draw(db, game.id, black.id)

    assert result.status == "finished"
    assert result.result == "1/2-1/2"
    assert result.finished_at is not None
    assert result.draw_offer_by is None


def test_white_can_accept_black_draw_offer(db):
    white = create_user(db)
    black = create_user(db, username="player2", email="player2@example.com")

    game = game_service.create_game(db, white.id)
    game_service.join_game(db, game.id, black.id)

    game_service.offer_draw(db, game.id, black.id)
    result = game_service.accept_draw(db, game.id, white.id)

    assert result.status == "finished"
    assert result.result == "1/2-1/2"
    assert result.draw_offer_by is None


def test_player_cannot_accept_own_draw_offer(db):
    white = create_user(db)
    black = create_user(db, username="player2", email="player2@example.com")

    game = game_service.create_game(db, white.id)
    game_service.join_game(db, game.id, black.id)

    game_service.offer_draw(db, game.id, white.id)

    with pytest.raises(game_service.CannotAcceptOwnDrawOffer):
        game_service.accept_draw(db, game.id, white.id)

    assert game.status == "active"
    assert game.result is None
    assert game.draw_offer_by == white.id


def test_cannot_accept_when_no_draw_offer_exists(db):
    white = create_user(db)
    black = create_user(db, username="player2", email="player2@example.com")

    game = game_service.create_game(db, white.id)
    game_service.join_game(db, game.id, black.id)

    with pytest.raises(game_service.NoDrawOffer):
        game_service.accept_draw(db, game.id, black.id)


def test_outsider_cannot_accept_draw(db):
    white = create_user(db)
    black = create_user(db, username="player2", email="player2@example.com")
    outsider = create_user(db, username="player3", email="player3@example.com")

    game = game_service.create_game(db, white.id)
    game_service.join_game(db, game.id, black.id)

    game_service.offer_draw(db, game.id, white.id)

    with pytest.raises(NotAPlayer):
        game_service.accept_draw(db, game.id, outsider.id)


def test_opponent_can_decline_draw_offer(db):
    white = create_user(db)
    black = create_user(db, username="player2", email="player2@example.com")

    game = game_service.create_game(db, white.id)
    game_service.join_game(db, game.id, black.id)

    game_service.offer_draw(db, game.id, white.id)
    result = game_service.decline_draw(db, game.id, black.id)

    assert result.status == "active"
    assert result.result is None
    assert result.draw_offer_by is None


def test_white_can_decline_black_draw_offer(db):
    white = create_user(db)
    black = create_user(db, username="player2", email="player2@example.com")

    game = game_service.create_game(db, white.id)
    game_service.join_game(db, game.id, black.id)

    game_service.offer_draw(db, game.id, black.id)
    result = game_service.decline_draw(db, game.id, white.id)

    assert result.status == "active"
    assert result.draw_offer_by is None


def test_player_cannot_decline_own_draw_offer(db):
    white = create_user(db)
    black = create_user(db, username="player2", email="player2@example.com")

    game = game_service.create_game(db, white.id)
    game_service.join_game(db, game.id, black.id)

    game_service.offer_draw(db, game.id, white.id)

    with pytest.raises(game_service.CannotAcceptOwnDrawOffer):
        game_service.decline_draw(db, game.id, white.id)

    assert game.status == "active"
    assert game.draw_offer_by == white.id


def test_cannot_decline_when_no_draw_offer_exists(db):
    white = create_user(db)
    black = create_user(db, username="player2", email="player2@example.com")

    game = game_service.create_game(db, white.id)
    game_service.join_game(db, game.id, black.id)

    with pytest.raises(game_service.NoDrawOffer):
        game_service.decline_draw(db, game.id, black.id)


def test_cannot_decline_when_no_draw_offer_exists(db):
    white = create_user(db)
    black = create_user(db, username="player2", email="player2@example.com")

    game = game_service.create_game(db, white.id)
    game_service.join_game(db, game.id, black.id)

    with pytest.raises(game_service.NoDrawOffer):
        game_service.decline_draw(db, game.id, black.id)


def test_draw_offer_is_cleared_after_move(db):
    white = create_user(db)
    black = create_user(db, username="player2", email="player2@example.com")

    game = game_service.create_game(db, white.id)
    game_service.join_game(db, game.id, black.id)

    game_service.offer_draw(db, game.id, white.id)
    assert game.draw_offer_by == white.id

    result = game_service.make_move(db, game.id, white.id, "e2e4")
    assert result.draw_offer_by is None


def test_draw_offer_is_not_cleared_by_illegal_move(db):
    white = create_user(db)
    black = create_user(db, username="player2", email="player2@example.com")

    game = game_service.create_game(db, white.id)
    game_service.join_game(db, game.id, black.id)

    game_service.offer_draw(db, game.id, white.id)

    with pytest.raises(IllegalMove):
        game_service.make_move(db, game.id, white.id, "e2e5")

    assert game.draw_offer_by == white.id
