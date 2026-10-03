"""Elo calculation; the game service owns the transaction and its commit."""

from sqlalchemy.orm import Session

from backend.exceptions.user import UserNotFound

# Starting rating for both existing accounts and new players.
INITIAL_ELO = 1000

# Rating adjustment factor: a larger K makes ratings change faster.
K = 32

# Rating gap giving a 10:1 ratio between the players' expected scores.
ELO_SCALE = 400

# Base of the exponential used in the expected-score formula.
ELO_BASE = 10

# Actual scores awarded for a win, draw and loss.
WIN = 1.0
DRAW = 0.5
LOSS = 0.0

_WHITE_SCORE_BY_RESULT = {"1-0": WIN, "0-1": LOSS, "1/2-1/2": DRAW}


def expected_score(rating_a: int, rating_b: int) -> float:
    """Return player A's expected score from both pre-game ratings."""
    return WIN / (WIN + ELO_BASE**((rating_b - rating_a) / ELO_SCALE))


def calculate_ratings(rating_a: int, rating_b: int,
                      actual_score_a: float) -> tuple[int, int]:
    """Return both new ratings using one rounded adjustment."""
    if actual_score_a not in (WIN, DRAW, LOSS):
        raise ValueError("An Elo score must be a win, draw or loss")

    expected_score_a = expected_score(rating_a, rating_b)
    rating_change = round(K * (actual_score_a - expected_score_a))
    return rating_a + rating_change, rating_b - rating_change


def update_ratings(db: Session, white_player_id: int, black_player_id: int,
                   result: str) -> None:
    """Update both ratings within the locked game's finishing transaction."""
    # Import here because the User model imports INITIAL_ELO from this module.
    from backend.repositories.stats_repository import StatsRepository

    if white_player_id == black_player_id:
        raise ValueError("Elo requires two different players")
    if result not in _WHITE_SCORE_BY_RESULT:
        raise ValueError("Unsupported game result for Elo")

    players = StatsRepository(db).get_players_for_update(
        [white_player_id, black_player_id])
    players_by_id = {player.id: player for player in players}
    if white_player_id not in players_by_id or black_player_id not in players_by_id:
        raise UserNotFound()

    white = players_by_id[white_player_id]
    black = players_by_id[black_player_id]
    white.elo, black.elo = calculate_ratings(white.elo, black.elo,
                                             _WHITE_SCORE_BY_RESULT[result])
