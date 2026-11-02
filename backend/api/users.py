from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from backend.core.dependencies import get_current_user
from backend.db.session import get_db
from backend.exceptions.user import UserAlreadyExists, UserNotFound
from backend.models.user import User
from backend.schemas.user import (HeartbeatResponse, UserCreate,
                                  UserResponse, UserUpdate)
from backend.services import presence_service, user_service

router = APIRouter()


@router.get("/me", response_model=UserResponse)
def get_me(current_user: User = Depends(get_current_user)):
    return current_user


@router.post("/me/heartbeat", response_model=HeartbeatResponse)
def heartbeat(current_user: User = Depends(get_current_user),
              db: Session = Depends(get_db)):
    last_seen_at = presence_service.record_heartbeat(db, current_user)
    return HeartbeatResponse(last_seen_at=last_seen_at)


@router.patch("/me", response_model=UserResponse)
def update_me(user_data: UserUpdate,
              current_user: User = Depends(get_current_user),
              db: Session = Depends(get_db)):
    try:
        return user_service.update_user(db, current_user.id, user_data)

    except UserAlreadyExists as error:
        raise HTTPException(status_code=409, detail=str(error))

    except UserNotFound as error:
        raise HTTPException(status_code=404, detail=str(error))


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
