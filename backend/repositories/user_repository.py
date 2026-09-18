from sqlalchemy import select
from sqlalchemy.orm import Session
from backend.models.user import User

def get_by_username(db: Session, username: str) -> User | None:
    statement = select(User).where(User.username == username)
    return db.scalar(statement)

def get_by_email(db: Session, email: str) -> User | None:
    statement = select(User).where(User.email == email)
    return db.scalar(statement)

def create(db: Session, user: User) -> User:
    db.add(user)
    db.flush()
    db.refresh(user)

    return user
