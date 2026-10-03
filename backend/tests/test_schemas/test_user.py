import pytest
from pydantic import ValidationError
from backend.schemas.user import UserUpdate


def test_user_update_accepts_valid_board_colors():
    user_data = UserUpdate(board_light_color="#FFFFFF",
                           board_dark_color="#2C5563")

    assert user_data.board_light_color == "#FFFFFF"
    assert user_data.board_dark_color == "#2C5563"


@pytest.mark.parametrize(
    "color",
    ["FFFFFF", "#FFF", "#12345", "#1234567", "red", "not-a-color", ""])
def test_user_update_rejects_invalid_board_color(color):
    with pytest.raises(ValidationError):
        UserUpdate(board_light_color=color)


@pytest.mark.parametrize(
    "color",
    ["FFFFFF", "#FFF", "#12345", "#1234567", "blue", "not-a-color", ""])
def test_user_update_rejects_invalid_dark_board_color(color):
    with pytest.raises(ValidationError):
        UserUpdate(board_dark_color=color)
