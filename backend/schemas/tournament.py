from pydantic import BaseModel


class TournamentCreateRequest(BaseModel):
    creator_id: int


class MatchResponse(BaseModel):
    round: int
    slot: int
    player1_id: int
    player2_id: int
    game_id: int
    winner_id: int | None

    model_config = {"from_attributes": True}


class TournamentResponse(BaseModel):
    id: int
    status: str
    winner_id: int | None
    participants: list[str]
    matches: list[MatchResponse]
