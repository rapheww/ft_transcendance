from datetime import datetime
from typing import Literal
from pydantic import BaseModel


class MatchHistoryEntry(BaseModel):
    opponent: str
    outcome: Literal["win", "loss", "draw"]
    moves_played: int
    played_at: datetime


class PlayerStats(BaseModel):
    elo: int
    games_played: int
    wins: int
    losses: int
    draws: int
    win_rate: float


class EloHistoryPoint(BaseModel):
    date: datetime
    elo: int


class PlayerProfile(PlayerStats):
    username: str
    elo_history: list[EloHistoryPoint]


class LeaderboardEntry(BaseModel):
    username: str
    elo: int
    wins: int
    games_played: int
