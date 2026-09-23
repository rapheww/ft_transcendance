import chess
import pytest
from backend.exceptions.game import GameCreationError
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
