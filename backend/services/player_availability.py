"""Common SQL locks for tournament enrollment and matchmaking."""
from datetime import datetime, timezone
from sqlalchemy import or_
from sqlalchemy.orm import Session
from backend.exceptions.tournament import PlayerUnavailable
from backend.exceptions.user import UserNotFound
from backend.models.game import Game
from backend.models.matchmaking import MatchmakingQueue
from backend.models.tournament import Tournament, TournamentParticipant
from backend.models.user import User

ACTIVE_TOURNAMENT_STATUSES = ("registration", "countdown", "in_progress",
                              "between_rounds")


def lock_players(db: Session, player_ids: list[int]) -> list[User]:
    players = (db.query(User).filter(User.id.in_(player_ids)).order_by(
        User.id).populate_existing().with_for_update().all())
    if len(players) != len(set(player_ids)):
        raise UserNotFound()
    return players


def active_tournament_query(db: Session, user_id: int):
    now = datetime.now(timezone.utc)
    return (db.query(Tournament).join(
        TournamentParticipant,
        TournamentParticipant.tournament_id == Tournament.id).filter(
            TournamentParticipant.user_id == user_id,
            Tournament.status.in_(ACTIVE_TOURNAMENT_STATUSES),
            or_(Tournament.status != "registration",
                Tournament.registration_deadline > now)).populate_existing())


def assert_available(db: Session,
                     user_id: int,
                     *,
                     allow_queue: bool = False) -> None:
    # Caller holds the user's SQL lock until its transaction commits.
    if active_tournament_query(db, user_id).first() is not None:
        raise PlayerUnavailable()
    if not allow_queue and db.query(MatchmakingQueue).filter_by(
            user_id=user_id).first() is not None:
        raise PlayerUnavailable()
    if (db.query(Game).filter(
            Game.status.in_(("waiting", "active")),
            or_(Game.white_player_id == user_id,
                Game.black_player_id == user_id)).first() is not None):
        raise PlayerUnavailable()
