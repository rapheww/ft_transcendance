from datetime import datetime
from pydantic import BaseModel, Field


class MatchmakingRequest(BaseModel):
    initial_time_seconds: int | None = Field(default=None, gt=0)
    increment_seconds: int = Field(default=0, ge=0)


class MatchmakingResponse(BaseModel):
    status: str = "waiting"
    id: int | None = None
    user_id: int | None = None
    initial_time_seconds: int | None = None
    increment_seconds: int | None = None
    created_at: datetime | None = None
    game_id: int | None = None
