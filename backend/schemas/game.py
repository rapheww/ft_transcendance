from datetime import datetime
from pydantic import BaseModel


class GameCreate(BaseModel):
    pass


class GameJoin(BaseModel):
    game_id: int


class GameResponse(BaseModel):
    id: int
    white_player_id: int
    black_player_id: int | None
    status: str
    result: str | None
    current_fen: str
    pgn: str
    created_at: datetime
    finished_at: datetime | None

    model_config = {"from_attributes": True}
