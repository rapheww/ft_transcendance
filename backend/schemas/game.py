from datetime import datetime
from pydantic import AliasPath, BaseModel, Field


class GameCreate(BaseModel):
    initial_time_seconds: int | None = Field(default=None, gt=0)
    increment_seconds: int = Field(default=0, ge=0)
    opponent_type: str = Field(default="human")
    ai_difficulty: str | None = Field(default=None)


class GameJoin(BaseModel):
    game_id: int


class MoveRequest(BaseModel):
    move: str


class GameResponse(BaseModel):
    id: int
    white_player_id: int
    white_player_name: str = Field(
        validation_alias=AliasPath("white_player", "username"))
    white_player_is_bot: bool = Field(
        default=False, validation_alias=AliasPath("white_player", "is_bot"))
    black_player_id: int | None
    black_player_name: str | None = Field(default=None,
                                          validation_alias=AliasPath(
                                              "black_player", "username"))
    black_player_is_bot: bool = Field(
        default=False,
        validation_alias=AliasPath("black_player", "is_bot"))
    opponent_type: str
    ai_difficulty: str | None
    is_tournament: bool = False
    status: str
    result: str | None
    current_fen: str
    pgn: str

    initial_time_seconds: int | None
    increment_seconds: int
    white_time_remaining: int | None
    black_time_remaining: int | None
    last_move_at: datetime | None

    draw_offer_by: int | None
    created_at: datetime
    finished_at: datetime | None
    model_config = {"from_attributes": True}


class GameDetailsResponse(GameResponse):
    can_claim_threefold_repetition: bool
    can_claim_fifty_move: bool


class OngoingGameResponse(BaseModel):
    id: int
    white_player_id: int
    white_player_name: str = Field(
        validation_alias=AliasPath("white_player", "username"))
    black_player_id: int | None
    black_player_name: str | None = Field(default=None,
                                          validation_alias=AliasPath(
                                              "black_player", "username"))
    opponent_type: str
    ai_difficulty: str | None
    initial_time_seconds: int | None
    increment_seconds: int

    model_config = {"from_attributes": True}
