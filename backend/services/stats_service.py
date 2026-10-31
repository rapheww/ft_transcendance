"""Game statistics and match history.

Reads finished games (Game.status == "finished") and turns them into
player-facing stats. Move counts are read straight from the stored PGN
instead of a dedicated counter, using python-chess.
"""

import io
from datetime import timezone
from typing import Literal

import chess.pgn
from sqlalchemy.orm import Session

from backend.models.game import Game
from backend.models.user import User
from backend.repositories.stats_repository import StatsRepository
from backend.schemas.stats import (
    EloHistoryPoint, LeaderboardEntry, MatchHistoryEntry, PlayerProfile, PlayerStats)
from backend.services import user_service

Outcome = Literal["win", "loss", "draw"]

_WINNER_COLOR_BY_RESULT = {
    "1-0": "white",
    "0-1": "black",
    "1/2-1/2": None,
}


def _outcome_for_player(game: Game, user_id: int) -> Outcome:
    winner_color = _WINNER_COLOR_BY_RESULT[game.result]

    if winner_color is None:
        return "draw"

    player_color = "white" if game.white_player_id == user_id else "black"
    return "win" if winner_color == player_color else "loss"


def _count_moves(pgn: str) -> int:
    parsed = chess.pgn.read_game(io.StringIO(pgn))
    return sum(1 for _ in parsed.mainline_moves()) if parsed else 0


def _opponent_username(db: Session, game: Game, user_id: int) -> str:
    opponent_id = (game.black_player_id if game.white_player_id == user_id else
                   game.white_player_id)
    return user_service.get_user_by_id(db, opponent_id).username


def get_match_history(db: Session, user_id: int) -> list[MatchHistoryEntry]:
    games = StatsRepository(db).list_finished_for_player(user_id)

    return [
        MatchHistoryEntry(opponent=_opponent_username(db, game, user_id),
                          outcome=_outcome_for_player(game, user_id),
                          moves_played=_count_moves(game.pgn),
                          played_at=game.finished_at) for game in games
    ]


def get_player_stats(db: Session, user_id: int) -> PlayerStats:
    user = user_service.get_user_by_id(db, user_id)
    games = StatsRepository(db).list_finished_for_player(user_id)
    outcomes = [_outcome_for_player(game, user_id) for game in games]

    games_played = len(outcomes)
    wins = outcomes.count("win")
    losses = outcomes.count("loss")
    draws = outcomes.count("draw")
    win_rate = round(wins / games_played, 3) if games_played else 0.0

    return PlayerStats(elo=user.elo,
                       games_played=games_played,
                       wins=wins,
                       losses=losses,
                       draws=draws,
                       win_rate=win_rate)


def get_player_profile(db: Session, username: str) -> PlayerProfile:
    """Return a player's statistics and recorded Elo history."""
    user = user_service.get_user(db, username)
    stats = get_player_stats(db, user.id)
    history = StatsRepository(db).list_elo_history(user.id)
    return PlayerProfile(
        **stats.model_dump(), username=user.username,
        elo_history=[
            EloHistoryPoint(date=date.astimezone(timezone.utc), elo=elo)
            for date, elo in history
        ])


def get_leaderboard(db: Session) -> list[LeaderboardEntry]:
    entries = []
    
    for user in db.query(User).filter(User.is_bot.is_(False)).all():
        stats = get_player_stats(db, user.id)
        entries.append(
            LeaderboardEntry(username=user.username,
                             elo=stats.elo,
                             wins=stats.wins,
                             games_played=stats.games_played))

    return sorted(entries, key=lambda entry: (-entry.elo, entry.username))
