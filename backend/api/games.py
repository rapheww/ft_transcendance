from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from backend.core.dependencies import get_current_user
from backend.db.session import get_db
from backend.exceptions.game import CannotPlayAgainstSelf, GameNotFound, GameNotJoinable
from backend.models.user import User
from backend.schemas.game import GameResponse
from backend.services import game_service

router = APIRouter()


@router.post("/", response_model=GameResponse, status_code=201)
def create_game(current_user: User = Depends(get_current_user),
                db: Session = Depends(get_db)):
    return game_service.create_game(db, current_user.id)


@router.post("/{game_id}/join", response_model=GameResponse)
def join_game(game_id: int,
              current_user: User = Depends(get_current_user),
              db: Session = Depends(get_db)):
    try:
        return game_service.join_game(db, game_id, current_user.id)

    except GameNotFound as error:
        raise HTTPException(status_code=404, detail=str(error))

    except GameNotJoinable as error:
        raise HTTPException(status_code=409, detail=str(error))

    except CannotPlayAgainstSelf as error:
        raise HTTPException(status_code=409, detail=str(error))


@router.get("/{game_id}", response_model=GameResponse)
def get_game(game_id: int, db: Session = Depends(get_db)):
    try:
        return game_service.get_game(db, game_id)

    except GameNotFound as error:
        raise HTTPException(status_code=404, detail=str(error))
