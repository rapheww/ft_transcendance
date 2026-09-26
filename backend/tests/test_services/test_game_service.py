import chess
import pytest
from backend.exceptions.game import CannotPlayAgainstSelf, GameNotFound, GameNotJoinable, GameNotActive, NotAPlayer, NotYourTurn, IllegalMove
from backend.models.user import User
from backend.services import game_service


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
