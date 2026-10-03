from argon2 import PasswordHasher
from argon2.exceptions import VerifyMismatchError
from sqlalchemy.exc import IntegrityError, SQLAlchemyError
from sqlalchemy.orm import Session
from backend.exceptions.user import UserAlreadyExists, UserNotFound, InvalidCredentials
from backend.models.user import User
from backend.repositories import user_repository
from backend.schemas.user import UserCreate, UserUpdate

password_hasher = PasswordHasher()


def create_user(db: Session, user_data: UserCreate) -> User:
    try:
        with db.begin():
            existing_username = user_repository.get_by_username(
                db, user_data.username)
            if existing_username is not None:
                raise UserAlreadyExists("Username already exists")

            existing_email = user_repository.get_by_email(db, user_data.email)
            if existing_email is not None:
                raise UserAlreadyExists("Email already exists")

            password_hash = password_hasher.hash(user_data.password)

            user = User(username=user_data.username,
                        email=user_data.email,
                        password_hash=password_hash)

            user_repository.create(db, user)

        return user

    except IntegrityError:
        raise UserAlreadyExists("Username or email already exists")

    except SQLAlchemyError:
        raise


def verify_password(password: str, password_hash: str) -> bool:
    try:
        password_hasher.verify(password_hash, password)
        return True
    except VerifyMismatchError:
        return False


def authenticate_user(db: Session, username: str, password: str) -> User:
    user = user_repository.get_by_username(db, username)

    if user is None:
        raise InvalidCredentials("Invalid username or password")

    if not verify_password(password, user.password_hash):
        raise InvalidCredentials("Invalid username or password")

    return user


def get_user_by_id(db: Session, user_id: int) -> User:
    user = user_repository.get_by_id(db, user_id)

    if user is None:
        raise UserNotFound("User not found")

    return user


def get_user(db: Session, username: str) -> User:
    user = user_repository.get_by_username(db, username)

    if user is None:
        raise UserNotFound("User not found")

    return user


def update_user(db: Session, user_id: int, user_data: UserUpdate) -> User:
    try:
        user = user_repository.get_by_id(db, user_id)
        if user is None:
            raise UserNotFound("User not found")

        if user_data.username is not None:
            existing_username = user_repository.get_by_username(
                db, user_data.username)

            if (existing_username is not None
                    and existing_username.id != user.id):
                raise UserAlreadyExists("Username already exists")

            user.username = user_data.username

        if user_data.email is not None:
            existing_email = user_repository.get_by_email(db, user_data.email)

            if existing_email is not None and existing_email.id != user.id:
                raise UserAlreadyExists("Email already exists")

            user.email = user_data.email

        if user_data.avatar is not None:
            user.avatar = user_data.avatar

        if user_data.board_light_color is not None:
            user.board_light_color = user_data.board_light_color

        if user_data.board_dark_color is not None:
            user.board_dark_color = user_data.board_dark_color

        user_repository.update(db, user)
        db.commit()

        return user

    except IntegrityError:
        db.rollback()
        raise UserAlreadyExists("Username or email already exists")

    except SQLAlchemyError:
        db.rollback()
        raise
