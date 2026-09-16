from sqlalchemy.exc import IntegrityError, SQLAlchemyError
from sqlalchemy.orm import Session

from backend.models.user import User
from backend.repositories import user_repository
from backend.schemas.user import UserCreate


def create_user(db: Session, user_data: UserCreate) -> User:
    try:
        with db.begin():
            existing_username = user_repository.get_by_username(
                db,
                user_data.username,
            )

            if existing_username is not None:
                raise ValueError("Username already exists")

            existing_email = user_repository.get_by_email(
                db,
                user_data.email,
            )

            if existing_email is not None:
                raise ValueError("Email already exists")

            user = User(
                username=user_data.username,
                email=user_data.email,
            )

            user_repository.create(db, user)

        return user

    except IntegrityError:
        raise ValueError("Username or email already exists")

    except SQLAlchemyError:
        raise
