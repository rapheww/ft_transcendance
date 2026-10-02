from datetime import datetime
from typing import Literal
from pydantic import BaseModel


class MatchHistoryEntry(BaseModel):
    opponent: str
    outcome: Literal["win", "loss", "draw"]
    moves_played: int
    played_at: datetime


class PlayerStats(BaseModel):
    games_played: int
    wins: int
    losses: int
    draws: int
    win_rate: float


class LeaderboardEntry(BaseModel):
    username: str
    wins: int
    games_played: int
