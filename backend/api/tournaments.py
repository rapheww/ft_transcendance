from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from backend.core.dependencies import get_current_user
from backend.db.session import get_db
from backend.exceptions.tournament import (AlreadyRegistered,
                                           InvalidParticipantCount,
                                           NotRegistered,
                                           TournamentAlreadyStarted,
                                           TournamentNotFound)
from backend.models.user import User
from backend.schemas.tournament import TournamentResponse
from backend.services import tournament_service

router = APIRouter()


@router.post("/", response_model=TournamentResponse, status_code=201)
def create_tournament(current_user: User = Depends(get_current_user),
                      db: Session = Depends(get_db)):
    tournament = tournament_service.create_tournament(db, current_user.id)
    return tournament_service.get_tournament(db, tournament.id)


@router.get("/{tournament_id}", response_model=TournamentResponse)
def get_tournament(tournament_id: int, db: Session = Depends(get_db)):
    try:
        return tournament_service.get_tournament(db, tournament_id)

    except TournamentNotFound as error:
        raise HTTPException(status_code=404, detail=str(error))


@router.post("/{tournament_id}/register", response_model=TournamentResponse)
def register(tournament_id: int,
             current_user: User = Depends(get_current_user),
             db: Session = Depends(get_db)):
    try:
        tournament_service.register(db, tournament_id, current_user.id)
        return tournament_service.get_tournament(db, tournament_id)

    except TournamentNotFound as error:
        raise HTTPException(status_code=404, detail=str(error))

    except (TournamentAlreadyStarted, AlreadyRegistered) as error:
        raise HTTPException(status_code=409, detail=str(error))


@router.post("/{tournament_id}/start", response_model=TournamentResponse)
def start_tournament(tournament_id: int,
                     current_user: User = Depends(get_current_user),
                     db: Session = Depends(get_db)):
    try:
        tournament_service.start_tournament(db, tournament_id, current_user.id)
        return tournament_service.get_tournament(db, tournament_id)

    except TournamentNotFound as error:
        raise HTTPException(status_code=404, detail=str(error))

    except (TournamentAlreadyStarted, NotRegistered,
            InvalidParticipantCount) as error:
        raise HTTPException(status_code=409, detail=str(error))
