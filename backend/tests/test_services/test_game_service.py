import chess
import pytest
from backend.exceptions.game import CannotPlayAgainstSelf, GameNotFound, GameNotJoinable
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
