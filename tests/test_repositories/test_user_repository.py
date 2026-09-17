from backend.models.user import User
from backend.repositories import user_repository


def test_create_user(db):
    user = User(
        username="alice",
        email="alice@example.com",
    )

    result = user_repository.create(db, user)

    assert result.id is not None
    assert result.username == "alice"
    assert result.email == "alice@example.com"


def test_get_by_username_returns_user(db):
    user = User(
        username="alice",
        email="alice@example.com",
    )

    user_repository.create(db, user)

    result = user_repository.get_by_username(db, "alice")

    assert result is not None
    assert result.username == "alice"
    assert result.email == "alice@example.com"


def test_get_by_username_returns_none_for_missing_user(db):
    result = user_repository.get_by_username(db, "does-not-exist")

    assert result is None

def test_get_by_email_returns_user(db):
    user = User(
        username="alice",
        email="alice@example.com",
    )

    user_repository.create(db, user)

    result = user_repository.get_by_email(db, "alice@example.com")

    assert result is not None
    assert result.username == "alice"
    assert result.email == "alice@example.com"


def test_get_by_email_returns_none_for_missing_user(db):
    result = user_repository.get_by_email(
        db,
        "does-not-exist@example.com",
    )

    assert result is None
