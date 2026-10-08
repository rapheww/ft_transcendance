import random
import threading
from datetime import datetime, timezone
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session
from backend.models.user import User
from backend.models.game import Game
from backend.models.matchmaking import MatchmakingQueue
from backend.repositories.game_repository import GameRepository
from backend.repositories.matchmaking_repository import MatchmakingRepository
from backend.exceptions.matchmaking import AlreadyInMatchmaking, NotInMatchmaking
from backend.services import user_service, game_service

matchmaking_lock = threading.Lock()


def get_rating_range(created_at: datetime, now: datetime) -> int:
    elapsed_seconds = (now - created_at).total_seconds()

    if elapsed_seconds < 10:
        return 50

    if elapsed_seconds < 20:
        return 100

    if elapsed_seconds < 30:
        return 200

    return 400


def join_queue(db: Session, user_id: int, initial_time_seconds: int | None,
               increment_seconds: int) -> MatchmakingQueue:
    try:
        user_service.get_user_by_id(db, user_id)
        repository = MatchmakingRepository(db)
        existing = repository.get_by_user_id(user_id)

        if existing is not None:
            raise AlreadyInMatchmaking()

        entry = MatchmakingQueue(user_id=user_id,
                                 initial_time_seconds=initial_time_seconds,
                                 increment_seconds=increment_seconds)

        repository.create(entry)
        db.commit()

        return entry

    except SQLAlchemyError:
        db.rollback()
        raise


def leave_queue(db: Session, user_id: int) -> None:
    try:
        repository = MatchmakingRepository(db)
        entry = repository.get_by_user_id(user_id)

        if entry is None:
            raise NotInMatchmaking()

        repository.delete(entry)
        db.commit()

    except SQLAlchemyError:
        db.rollback()
        raise


def get_queue_entry(db: Session, user_id: int) -> MatchmakingQueue | None:
    repository = MatchmakingRepository(db)

    return repository.get_by_user_id(user_id)


def find_match(db: Session, user_id: int, initial_time_seconds: int | None,
               increment_seconds: int) -> Game | None:

    with matchmaking_lock:
        try:
            repository = MatchmakingRepository(db)
            current_player_entry = repository.get_by_user_id(user_id)

            if current_player_entry is None:
                return None

            player = (db.query(User).filter(User.id == user_id).first())
            if player is None:
                return None

            now = datetime.now(timezone.utc)
            rating_range = get_rating_range(current_player_entry.created_at,
                                            now)

            min_elo = player.elo - rating_range
            max_elo = player.elo + rating_range

            opponent = repository.get_closest_compatible(
                user_id, initial_time_seconds, increment_seconds, min_elo,
                max_elo, player.elo)
            if opponent is None:
                return None

            if random.choice([True, False]):
                white_player_id = user_id
                black_player_id = opponent.user_id

            else:
                white_player_id = opponent.user_id
                black_player_id = user_id

            game = game_service.create_human_game(db, white_player_id,
                                                  black_player_id,
                                                  initial_time_seconds,
                                                  increment_seconds)

            repository.delete(current_player_entry)
            repository.delete(opponent)

            db.commit()
            db.refresh(game)

            return game

        except SQLAlchemyError:
            db.rollback()
            raise
