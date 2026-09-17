import pytest

from backend.exceptions.user import UserAlreadyExists, UserNotFound
from backend.schemas.user import UserCreate
from backend.services import user_service
from sqlalchemy.exc import SQLAlchemyError
from backend.repositories import user_repository


def test_get_user_raises_user_not_found(db):
    with pytest.raises(UserNotFound):
        user_service.get_user(db, "does-not-exist")

def test_create_user(db):
    user_data = UserCreate(
        username="alice",
        email="alice@example.com",
    )

    result = user_service.create_user(db, user_data)

    assert result.id is not None
    assert result.username == "alice"
    assert result.email == "alice@example.com"


def test_get_user_returns_user(db):
    user_data = UserCreate(
        username="alice",
        email="alice@example.com",
    )

    created_user = user_service.create_user(db, user_data)

    result = user_service.get_user(db, "alice")

    assert result.id == created_user.id
    assert result.username == "alice"
    assert result.email == "alice@example.com"

def test_create_user_raises_when_username_exists(db):
    first_user = UserCreate(
        username="alice",
        email="alice@example.com",
    )

    second_user = UserCreate(
        username="alice",
        email="different@example.com",
    )

    user_service.create_user(db, first_user)

    with pytest.raises(UserAlreadyExists):
        user_service.create_user(db, second_user)

def test_create_user_raises_when_email_exists(db):
    first_user = UserCreate(
        username="alice",
        email="alice@example.com",
    )

    second_user = UserCreate(
        username="bob",
        email="alice@example.com",
    )

    user_service.create_user(db, first_user)

    with pytest.raises(UserAlreadyExists):
        user_service.create_user(db, second_user)

def test_create_user_rolls_back_when_repository_fails(db, monkeypatch):
    user_data = UserCreate(
        username="alice",
        email="alice@example.com",
    )

    def failing_create(db, user):
        db.add(user)
        raise SQLAlchemyError("Database failure")

    monkeypatch.setattr(
        user_repository,
        "create",
        failing_create,
    )

    with pytest.raises(SQLAlchemyError):
        user_service.create_user(db, user_data)

    result = user_repository.get_by_username(db, "alice")

    assert result is None
