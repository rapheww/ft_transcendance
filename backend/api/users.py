from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from backend.db.session import get_db
from backend.exceptions.user import UserAlreadyExists, UserNotFound
from backend.schemas.user import UserCreate, UserResponse
from backend.services import user_service

router = APIRouter()


@router.get("/{username}", response_model=UserResponse)
def get_user(username: str, db: Session = Depends(get_db)):
    try:
        return user_service.get_user(db, username)

    except UserNotFound as error:
        raise HTTPException(status_code=404, detail=str(error))


@router.post("/", response_model=UserResponse, status_code=201)
def create_user(user: UserCreate, db: Session = Depends(get_db)):
    try:
        return user_service.create_user(db, user)

    except UserAlreadyExists as error:
        raise HTTPException(status_code=409, detail=str(error))
