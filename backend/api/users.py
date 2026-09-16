from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError, SQLAlchemyError
from sqlalchemy.orm import Session

from backend.db.session import get_db
from backend.models.user import User
from backend.schemas.user import UserCreate, UserResponse
from backend.services import user_service

router = APIRouter()

@router.get("/{username}", response_model=UserResponse)
def get_user(username: str, db: Session = Depends(get_db)):
    statement = select(User).where(User.username == username)
    user = db.scalar(statement)

    if user is None:
        raise HTTPException(
            status_code=404,
            detail="User not found",
        )

    return user

@router.post("/", response_model=UserResponse, status_code=201)
def create_user(user: UserCreate, db: Session = Depends(get_db)):
    try:
        return user_service.create_user(db, user)
    except ValueError as error:
        raise HTTPException(
            status_code=409,
            detail=str(error),
        )
