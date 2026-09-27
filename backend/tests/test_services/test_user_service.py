import pytest
from backend.exceptions.user import UserAlreadyExists, UserNotFound, InvalidCredentials
from backend.schemas.user import UserCreate, UserUpdate
from backend.services import user_service
from sqlalchemy.exc import SQLAlchemyError
from backend.repositories import user_repository
from argon2 import PasswordHasher


def test_get_user_raises_user_not_found(db):
    with pytest.raises(UserNotFound):
        user_service.get_user(db, "does-not-exist")


def test_create_user(db):
    user_data = UserCreate(username="alice",
                           email="alice@example.com",
                           password="password123")

    result = user_service.create_user(db, user_data)

    assert result.id is not None
    assert result.username == "alice"
    assert result.email == "alice@example.com"

    password_hasher = PasswordHasher()
    assert password_hasher.verify(result.password_hash, "password123")


def test_get_user_returns_user(db):
    user_data = UserCreate(username="alice",
                           email="alice@example.com",
                           password="password123")

    created_user = user_service.create_user(db, user_data)
    result = user_service.get_user(db, "alice")

    assert result.id == created_user.id
    assert result.username == "alice"
    assert result.email == "alice@example.com"


def test_create_user_raises_when_username_exists(db):
    first_user = UserCreate(username="alice",
                            email="alice@example.com",
                            password="password123")

    second_user = UserCreate(username="alice",
                             email="different@example.com",
                             password="password123")

    user_service.create_user(db, first_user)

    with pytest.raises(UserAlreadyExists):
        user_service.create_user(db, second_user)


def test_create_user_raises_when_email_exists(db):
    first_user = UserCreate(username="alice",
                            email="alice@example.com",
                            password="password123")

    second_user = UserCreate(username="bob",
                             email="alice@example.com",
                             password="password123")

    user_service.create_user(db, first_user)

    with pytest.raises(UserAlreadyExists):
        user_service.create_user(db, second_user)


def test_create_user_rolls_back_when_repository_fails(db, monkeypatch):
    user_data = UserCreate(username="alice",
                           email="alice@example.com",
                           password="password123")

    def failing_create(db, user):
        db.add(user)
        raise SQLAlchemyError("Database failure")

    monkeypatch.setattr(user_repository, "create", failing_create)

    with pytest.raises(SQLAlchemyError):
        user_service.create_user(db, user_data)

    result = user_repository.get_by_username(db, "alice")

    assert result is None


def test_verify_password(db):
    user_data = UserCreate(username="alice",
                           email="alice@example.com",
                           password="password123")

    user = user_service.create_user(db, user_data)

    assert user_service.verify_password("password123",
                                        user.password_hash) is True

    assert user_service.verify_password("wrong-password",
                                        user.password_hash) is False


def test_authenticate_user(db):
    user_data = UserCreate(username="alice",
                           email="alice@example.com",
                           password="password123")

    user = user_service.create_user(db, user_data)
    result = user_service.authenticate_user(db, "alice", "password123")

    assert result.id == user.id
    assert result.username == "alice"


def test_authenticate_user_wrong_password(db):
    user_data = UserCreate(username="alice",
                           email="alice@example.com",
                           password="password123")

    user_service.create_user(db, user_data)

    with pytest.raises(InvalidCredentials):
        user_service.authenticate_user(db, "alice", "wrong-password")


def test_get_user_by_id(db):
    user_data = UserCreate(username="alice",
                           email="alice@example.com",
                           password="password123")

    created_user = user_service.create_user(db, user_data)
    result = user_service.get_user_by_id(db, created_user.id)

    assert result.id == created_user.id
    assert result.username == "alice"


def test_get_user_by_id_raises_user_not_found(db):
    with pytest.raises(UserNotFound):
        user_service.get_user_by_id(db, 999999)


def test_authenticate_user_unknown_user(db):
    with pytest.raises(InvalidCredentials):
        user_service.authenticate_user(db, "does-not-exist", "password123")


def test_update_user(db):
    user_data = UserCreate(username="alice",
                           email="alice@example.com",
                           password="password123")

    created_user = user_service.create_user(db, user_data)
    update_data = UserUpdate(username="alice-new",
                             email="alice-new@example.com")

    result = user_service.update_user(db, created_user.id, update_data)

    assert result.id == created_user.id
    assert result.username == "alice-new"
    assert result.email == "alice-new@example.com"


def test_update_user_email_only(db):
    user_data = UserCreate(username="alice",
                           email="alice@example.com",
                           password="password123")

    created_user = user_service.create_user(db, user_data)
    update_data = UserUpdate(email="new@example.com")
    result = user_service.update_user(db, created_user.id, update_data)

    assert result.id == created_user.id
    assert result.username == "alice"
    assert result.email == "new@example.com"


def test_update_user_raises_when_username_exists(db):
    first_user = UserCreate(username="alice",
                            email="alice@example.com",
                            password="password123")

    second_user = UserCreate(username="bob",
                             email="bob@example.com",
                             password="password123")

    user_service.create_user(db, first_user)
    second_user = user_service.create_user(db, second_user)
    update_data = UserUpdate(username="alice")

    with pytest.raises(UserAlreadyExists):
        user_service.update_user(db, second_user.id, update_data)


def test_update_user_raises_when_user_does_not_exist(db):
    update_data = UserUpdate(email="new@example.com")

    with pytest.raises(UserNotFound):
        user_service.update_user(db, 999999, update_data)


def test_update_user_raises_when_email_exists(db):
    first_user = UserCreate(username="alice",
                            email="alice@example.com",
                            password="password123")

    second_user = UserCreate(username="bob",
                             email="bob@example.com",
                             password="password123")

    user_service.create_user(db, first_user)
    second_user = user_service.create_user(db, second_user)
    update_data = UserUpdate(email="alice@example.com")

    with pytest.raises(UserAlreadyExists):
        user_service.update_user(db, second_user.id, update_data)
