import pytest
from datetime import datetime, timedelta, timezone
from backend.exceptions.matchmaking import AlreadyInMatchmaking, NotInMatchmaking
from backend.models.user import User
from backend.services import matchmaking_service


def create_user(db, username="player1", email="player1@example.com"):
    user = User(username=username,
                email=email,
                password_hash="hashed-password")

    db.add(user)
    db.commit()

    return user


def test_join_queue(db):
    user = create_user(db)
    result = matchmaking_service.join_queue(db,
                                            user.id,
                                            initial_time_seconds=600,
                                            increment_seconds=5)

    assert result.id is not None
    assert result.user_id == user.id
    assert result.initial_time_seconds == 600
    assert result.increment_seconds == 5
    assert result.created_at is not None


def test_join_queue_untimed(db):
    user = create_user(db)
    result = matchmaking_service.join_queue(db,
                                            user.id,
                                            initial_time_seconds=None,
                                            increment_seconds=0)

    assert result.user_id == user.id
    assert result.initial_time_seconds is None
    assert result.increment_seconds == 0


def test_user_cannot_join_queue_twice(db):
    user = create_user(db)
    matchmaking_service.join_queue(db,
                                   user.id,
                                   initial_time_seconds=600,
                                   increment_seconds=5)

    with pytest.raises(AlreadyInMatchmaking):
        matchmaking_service.join_queue(db,
                                       user.id,
                                       initial_time_seconds=300,
                                       increment_seconds=0)


def test_unknown_user_cannot_join_queue(db):
    with pytest.raises(Exception):
        matchmaking_service.join_queue(db,
                                       999999,
                                       initial_time_seconds=600,
                                       increment_seconds=5)


def test_leave_queue(db):
    user = create_user(db)
    matchmaking_service.join_queue(db,
                                   user.id,
                                   initial_time_seconds=600,
                                   increment_seconds=5)

    matchmaking_service.leave_queue(db, user.id)
    assert matchmaking_service.get_queue_entry(db, user.id) is None


def test_leave_queue_when_not_in_queue(db):
    user = create_user(db)

    with pytest.raises(NotInMatchmaking):
        matchmaking_service.leave_queue(db, user.id)


def test_get_queue_entry(db):
    user = create_user(db)
    matchmaking_service.join_queue(db,
                                   user.id,
                                   initial_time_seconds=300,
                                   increment_seconds=3)

    result = matchmaking_service.get_queue_entry(db, user.id)

    assert result is not None
    assert result.user_id == user.id
    assert result.initial_time_seconds == 300
    assert result.increment_seconds == 3


def test_find_match_creates_game(db):
    player1 = create_user(db, "player1", "player1@example.com")
    player2 = create_user(db, "player2", "player2@example.com")

    matchmaking_service.join_queue(db, player1.id, 600, 5)
    matchmaking_service.join_queue(db, player2.id, 600, 5)
    game = matchmaking_service.find_match(db, player1.id, 600, 5)

    assert game is not None
    assert {game.white_player_id,
            game.black_player_id} == {player1.id, player2.id}
    assert game.status == "active"
    assert game.opponent_type == "human"
    assert game.initial_time_seconds == 600
    assert game.increment_seconds == 5


def test_find_match_removes_both_players_from_queue(db):
    player1 = create_user(db, "player1", "player1@example.com")
    player2 = create_user(db, "player2", "player2@example.com")

    matchmaking_service.join_queue(db, player1.id, 600, 5)
    matchmaking_service.join_queue(db, player2.id, 600, 5)
    matchmaking_service.find_match(db, player1.id, 600, 5)

    assert matchmaking_service.get_queue_entry(db, player1.id) is None
    assert matchmaking_service.get_queue_entry(db, player2.id) is None


def test_find_match_returns_none_without_opponent(db):
    player1 = create_user(db)
    matchmaking_service.join_queue(db, player1.id, 600, 5)
    game = matchmaking_service.find_match(db, player1.id, 600, 5)

    assert game is None
    assert matchmaking_service.get_queue_entry(db, player1.id) is not None


def test_find_match_requires_same_time_control(db):
    player1 = create_user(db, "player1", "player1@example.com")
    player2 = create_user(db, "player2", "player2@example.com")

    matchmaking_service.join_queue(db, player1.id, 600, 5)
    matchmaking_service.join_queue(db, player2.id, 300, 0)
    game = matchmaking_service.find_match(db, player1.id, 600, 5)

    assert game is None
    assert matchmaking_service.get_queue_entry(db, player1.id) is not None
    assert matchmaking_service.get_queue_entry(db, player2.id) is not None


def test_find_match_does_not_match_different_increment(db):
    player1 = create_user(db, "player1", "player1@example.com")
    player2 = create_user(db, "player2", "player2@example.com")

    matchmaking_service.join_queue(db, player1.id, 600, 5)
    matchmaking_service.join_queue(db, player2.id, 600, 10)

    game = matchmaking_service.find_match(db, player1.id, 600, 5)
    assert game is None


def test_find_match_does_not_match_player_with_themselves(db):
    player = create_user(db)
    matchmaking_service.join_queue(db, player.id, 600, 5)
    game = matchmaking_service.find_match(db, player.id, 600, 5)

    assert game is None


def test_find_match_requires_compatible_rating(db):
    player1 = create_user(db, "player1", "player1@example.com")
    player2 = create_user(db, "player2", "player2@example.com")

    player1.elo = 1000
    player2.elo = 1200
    db.commit()

    matchmaking_service.join_queue(db, player1.id, 600, 5)
    matchmaking_service.join_queue(db, player2.id, 600, 5)

    game = matchmaking_service.find_match(db, player1.id, 600, 5)
    assert game is None


def test_find_match_accepts_compatible_rating(db):
    player1 = create_user(db, "player1", "player1@example.com")
    player2 = create_user(db, "player2", "player2@example.com")

    player1.elo = 1000
    player2.elo = 1040
    db.commit()

    matchmaking_service.join_queue(db, player1.id, 600, 5)
    matchmaking_service.join_queue(db, player2.id, 600, 5)

    game = matchmaking_service.find_match(db, player1.id, 600, 5)
    assert game is not None


def test_find_match_expands_rating_range_after_waiting(db):
    player1 = create_user(db, "player1", "player1@example.com")
    player2 = create_user(db, "player2", "player2@example.com")

    player1.elo = 1000
    player2.elo = 1100
    db.commit()

    matchmaking_service.join_queue(db, player1.id, 600, 5)
    matchmaking_service.join_queue(db, player2.id, 600, 5)

    player1_entry = matchmaking_service.get_queue_entry(db, player1.id)
    player1_entry.created_at = (datetime.now(timezone.utc) -
                                timedelta(seconds=15))

    db.commit()
    game = matchmaking_service.find_match(db, player1.id, 600, 5)
    assert game is not None


def test_find_match_expands_rating_range_after_30_seconds(db):
    player1 = create_user(db, "player1", "player1@example.com")
    player2 = create_user(db, "player2", "player2@example.com")

    player1.elo = 1000
    player2.elo = 1400
    db.commit()

    matchmaking_service.join_queue(db, player1.id, 600, 5)
    matchmaking_service.join_queue(db, player2.id, 600, 5)

    player1_entry = matchmaking_service.get_queue_entry(db, player1.id)
    player1_entry.created_at = (datetime.now(timezone.utc) -
                                timedelta(seconds=31))

    db.commit()
    game = matchmaking_service.find_match(db, player1.id, 600, 5)
    assert game is not None


def test_find_match_requires_both_rating_and_time_control(db):
    player1 = create_user(db, "player1", "player1@example.com")
    player2 = create_user(db, "player2", "player2@example.com")

    player1.elo = 1000
    player2.elo = 1020
    db.commit()

    matchmaking_service.join_queue(db, player1.id, 600, 5)
    matchmaking_service.join_queue(db, player2.id, 300, 0)

    game = matchmaking_service.find_match(db, player1.id, 600, 5)
    assert game is None


def test_find_match_accepts_players_within_elo_range(db):
    player1 = create_user(db, "player1", "player1@example.com")
    player2 = create_user(db, "player2", "player2@example.com")

    player1.elo = 1000
    player2.elo = 1050
    db.commit()

    matchmaking_service.join_queue(db, player1.id, 600, 5)
    matchmaking_service.join_queue(db, player2.id, 600, 5)

    game = matchmaking_service.find_match(db, player1.id, 600, 5)

    assert game is not None
    assert {game.white_player_id,
            game.black_player_id} == {player1.id, player2.id}


def test_find_match_rejects_players_outside_elo_range(db):
    player1 = create_user(db, "player1", "player1@example.com")
    player2 = create_user(db, "player2", "player2@example.com")

    player1.elo = 1000
    player2.elo = 1301
    db.commit()

    matchmaking_service.join_queue(db, player1.id, 600, 5)
    matchmaking_service.join_queue(db, player2.id, 600, 5)
    game = matchmaking_service.find_match(db, player1.id, 600, 5)

    assert game is None
    assert matchmaking_service.get_queue_entry(db, player1.id) is not None
    assert matchmaking_service.get_queue_entry(db, player2.id) is not None


def test_find_match_prefers_closest_elo(db):
    player1 = create_user(db, "player1", "player1@example.com")
    player2 = create_user(db, "player2", "player2@example.com")
    player3 = create_user(db, "player3", "player3@example.com")

    player1.elo = 1000
    player2.elo = 1150
    player3.elo = 1050

    db.commit()

    matchmaking_service.join_queue(db, player1.id, 600, 5)
    matchmaking_service.join_queue(db, player2.id, 600, 5)
    matchmaking_service.join_queue(db, player3.id, 600, 5)

    game = matchmaking_service.find_match(db, player1.id, 600, 5)

    assert game is not None
    assert {game.white_player_id,
            game.black_player_id} == {player1.id, player3.id}

    assert matchmaking_service.get_queue_entry(db, player2.id) is not None


def test_find_match_prefers_closest_elo(db):
    player1 = create_user(db, "player1", "player1@example.com")
    player2 = create_user(db, "player2", "player2@example.com")
    player3 = create_user(db, "player3", "player3@example.com")

    player1.elo = 1000
    player2.elo = 1150
    player3.elo = 1050

    db.commit()

    matchmaking_service.join_queue(db, player1.id, 600, 5)
    matchmaking_service.join_queue(db, player2.id, 600, 5)
    matchmaking_service.join_queue(db, player3.id, 600, 5)

    game = matchmaking_service.find_match(db, player1.id, 600, 5)
    assert game is not None

    assert {game.white_player_id,
            game.black_player_id} == {player1.id, player3.id}
    assert matchmaking_service.get_queue_entry(db, player2.id) is not None
