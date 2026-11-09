from backend.models.user import User
from backend.repositories import user_repository


def test_create_user(db):
    user = User(username="alice",
                email="alice@example.com",
                password_hash="test-password-hash")

    result = user_repository.create(db, user)

    assert result.id is not None
    assert result.username == "alice"
    assert result.email == "alice@example.com"


def test_get_by_username_returns_user(db):
    user = User(username="alice",
                email="alice@example.com",
                password_hash="test-password-hash")

    user_repository.create(db, user)

    result = user_repository.get_by_username(db, "alice")

    assert result is not None
    assert result.username == "alice"
    assert result.email == "alice@example.com"


def test_get_by_username_returns_none_for_missing_user(db):
    result = user_repository.get_by_username(db, "does-not-exist")

    assert result is None


def test_get_by_email_returns_user(db):
    user = User(username="alice",
                email="alice@example.com",
                password_hash="test-password-hash")

    user_repository.create(db, user)

    result = user_repository.get_by_email(db, "alice@example.com")

    assert result is not None
    assert result.username == "alice"
    assert result.email == "alice@example.com"


def test_get_by_id_returns_user(db):
    user = User(username="alice",
                email="alice@example.com",
                password_hash="test-hash")

    created_user = user_repository.create(db, user)

    result = user_repository.get_by_id(db, created_user.id)

    assert result is not None
    assert result.id == created_user.id
    assert result.username == "alice"


def test_get_by_id_returns_none_for_missing_user(db):
    result = user_repository.get_by_id(db, 999999)

    assert result is None


def test_get_by_email_returns_none_for_missing_user(db):
    result = user_repository.get_by_email(db, "does-not-exist@example.com")

    assert result is None


def test_update_user(db):
    user = User(username="alice",
                email="alice@example.com",
                password_hash="test-password-hash")

    created_user = user_repository.create(db, user)

    created_user.email = "new@example.com"

    result = user_repository.update(db, created_user)

    assert result.id == created_user.id
    assert result.username == "alice"
    assert result.email == "new@example.com"


def test_update_user_customization(db):
    user = User(username="alice",
                email="alice@example.com",
                password_hash="test-password-hash")

    created_user = user_repository.create(db, user)

    created_user.avatar = "custom-avatar"
    created_user.board_light_color = "#FFFFFF"
    created_user.board_dark_color = "#000000"

    result = user_repository.update(db, created_user)

    assert result.id == created_user.id
    assert result.avatar == "custom-avatar"
    assert result.board_light_color == "#FFFFFF"
    assert result.board_dark_color == "#000000"


def test_update_user_keeps_unchanged_fields(db):
    user = User(username="alice",
                email="alice@example.com",
                password_hash="test-password-hash")

    created_user = user_repository.create(db, user)

    original_username = created_user.username
    original_email = created_user.email
    original_avatar = created_user.avatar
    original_light_color = created_user.board_light_color
    original_dark_color = created_user.board_dark_color

    created_user.email = "new@example.com"
    result = user_repository.update(db, created_user)

    assert result.username == original_username
    assert result.email == "new@example.com"
    assert result.avatar == original_avatar
    assert result.board_light_color == original_light_color
    assert result.board_dark_color == original_dark_color
