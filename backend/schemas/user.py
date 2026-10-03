import re
from pydantic import BaseModel, Field, field_validator

HEX_COLOR_PATTERN = re.compile(r"^#[0-9a-fA-F]{6}$")


class UserCreate(BaseModel):
    username: str = Field(min_length=1, max_length=50)
    email: str
    password: str


class UserResponse(BaseModel):
    username: str
    email: str
    avatar: str
    board_light_color: str
    board_dark_color: str

    model_config = {"from_attributes": True}


class UserLogin(BaseModel):
    username: str
    password: str


class UserUpdate(BaseModel):
    username: str | None = Field(default=None, min_length=1, max_length=50)
    email: str | None = None
    avatar: str | None = Field(default=None, max_length=500)
    board_light_color: str | None = None
    board_dark_color: str | None = None

    @field_validator("board_light_color", "board_dark_color")
    @classmethod
    def validate_board_color(cls, value: str | None) -> str | None:
        if value is not None and not HEX_COLOR_PATTERN.fullmatch(value):
            raise ValueError("Board colors must be valid hexadecimal colors "
                             "in the format #RRGGBB")

        return value
