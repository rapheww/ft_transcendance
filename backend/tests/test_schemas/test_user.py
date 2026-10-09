import pytest
from pydantic import ValidationError
from backend.schemas.user import UserUpdate, UserCreate


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


def test_username_accepts_valid_characters():
    user = UserCreate(username="Chess_Player42",
                      email="Alice@Example.com",
                      password="password123")

    assert user.username == "Chess_Player42"
    assert user.email == "alice@example.com"


@pytest.mark.parametrize("username",
                         ["bad name", "user-name", "user.name", "user!"])
def test_username_rejects_invalid_characters(username):
    with pytest.raises(ValidationError):
        UserCreate(username=username,
                   email="alice@example.com",
                   password="password123")


@pytest.mark.parametrize("email",
                         ["not-an-email", "missing-domain@", "@example.com"])
def test_registration_rejects_invalid_email(email):
    with pytest.raises(ValidationError):
        UserCreate(username="alice", email=email, password="password123")


def test_email_is_trimmed_and_lowercased():
    user = UserCreate(username="alice",
                      email=" Alice@Example.COM ",
                      password="password123")

    assert user.email == "alice@example.com"


@pytest.mark.parametrize("password", ["short", ""])
def test_registration_rejects_short_password(password):
    with pytest.raises(ValidationError):
        UserCreate(username="alice",
                   email="alice@example.com",
                   password=password)


def test_password_preserves_whitespace():
    password = " password123 "
    user = UserCreate(username="alice",
                      email="alice@example.com",
                      password=password)

    assert user.password == password


def test_update_normalizes_email():
    user = UserUpdate(email=" Alice@Example.COM ")
    assert user.email == "alice@example.com"


def test_update_rejects_invalid_username():
    with pytest.raises(ValidationError):
        UserUpdate(username="not allowed")
