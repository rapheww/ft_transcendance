import chess
from backend.models.game import Game
from backend.repositories.game_repository import GameRepository
from backend.models.user import User


def create_user(db, username="player1", email="player1@example.com"):
    user = User(username=username,
                email=email,
                password_hash="hashed-password")
    db.add(user)
    db.flush()
    return user


def create_game(db, white_player_id, black_player_id):
    board = chess.Board()

    game = Game(white_player_id=white_player_id,
                black_player_id=black_player_id,
                status="waiting",
                result=None,
                current_fen=board.fen(),
                pgn="")

    repository = GameRepository(db)
    return repository.create(game)


def test_create_game(db):
    white = create_user(db)
    black = create_user(db, username="player2", email="player2@example.com")

    repository = GameRepository(db)

    game = create_game(db, white_player_id=white.id, black_player_id=black.id)

    db.commit()

    assert game.id is not None
    assert game.white_player_id == white.id
    assert game.black_player_id == black.id
    assert game.status == "waiting"
    assert game.result is None
    assert game.current_fen == chess.Board().fen()
    assert game.pgn == ""


def test_get_by_id_returns_game(db):
    white = create_user(db)
    black = create_user(db, username="player2", email="player2@example.com")

    game = create_game(db, white_player_id=white.id, black_player_id=black.id)

    repository = GameRepository(db)

    result = repository.get_by_id(game.id)

    assert result is not None
    assert result.id == game.id


def test_get_by_id_returns_none_for_missing_game(db):
    repository = GameRepository(db)

    result = repository.get_by_id(999999)

    assert result is None


def test_update_game(db):
    white = create_user(db)
    black = create_user(db, username="player2", email="player2@example.com")

    game = create_game(db, white_player_id=white.id, black_player_id=black.id)

    repository = GameRepository(db)

    game.status = "active"
    game.current_fen = "updated-fen"
    game.pgn = "updated-pgn"

    result = repository.update(game)
    db.commit()

    assert result.status == "active"
    assert result.current_fen == "updated-fen"
    assert result.pgn == "updated-pgn"
