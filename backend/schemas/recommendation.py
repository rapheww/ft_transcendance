from pydantic import BaseModel, Field

class OpponentRecommendation(BaseModel):
    user_id: int
    username: str
    elo: int
    is_bot: bool
    similarity_score: float | None = Field(
        default=None,
        ge=-1.0,
        le=1.0,
    )

class ResponseRecommendation(BaseModel):
    humans: list[OpponentRecommendation]
    bots: list[OpponentRecommendation]