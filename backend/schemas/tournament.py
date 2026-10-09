from datetime import datetime
from typing import Literal
from pydantic import BaseModel


class ParticipantResponse(BaseModel):
    id: int
    username: str
    eliminated: bool


class MatchResponse(BaseModel):
    round: int
    slot: int
    player1_id: int | None
    player2_id: int | None
    game_id: int | None
    winner_id: int | None
    is_bye: bool
    status: Literal["scheduled", "active", "finished", "bye"]


class TournamentResponse(BaseModel):
    id: int
    status: str
    organizer_type: str
    creator_id: int | None
    winner_id: int | None
    created_at: datetime
    registration_deadline: datetime
    next_round_at: datetime | None
    current_round: int
    participant_count: int
    participants: list[str]
    participant_details: list[ParticipantResponse]
    matches: list[MatchResponse]
    my_game_id: int | None = None
