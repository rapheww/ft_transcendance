from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from backend.core.dependencies import get_current_user
from backend.db.session import get_db
from backend.exceptions.tournament import (
    AlreadyRegistered, InvalidParticipantCount, NotTournamentOrganizer,
    PlayerUnavailable, TournamentAlreadyStarted, TournamentExpired,
    TournamentNotFound)
from backend.models.user import User
from backend.schemas.tournament import TournamentResponse
from backend.services import tournament_service

router = APIRouter()


def _http_error(error: Exception) -> HTTPException:
    if isinstance(error, TournamentNotFound):
        code = 404
    elif isinstance(error, NotTournamentOrganizer):
        code = 403
    else:
        code = 409
    return HTTPException(status_code=code, detail=str(error))


@router.get("/", response_model=list[TournamentResponse])
def list_tournaments(current_user: User = Depends(get_current_user),
                     db: Session = Depends(get_db)):
    return tournament_service.list_open_tournaments(db)


@router.get("/me", response_model=TournamentResponse | None)
def get_my_tournament(current_user: User = Depends(get_current_user),
                      db: Session = Depends(get_db)):
    return tournament_service.get_my_tournament(db, current_user.id)


@router.post("/", response_model=TournamentResponse, status_code=201)
def create_tournament(current_user: User = Depends(get_current_user),
                      db: Session = Depends(get_db)):
    try:
        tournament = tournament_service.create_tournament(db, current_user.id)
        return tournament_service.get_tournament(db, tournament.id,
                                                 current_user.id)
    except PlayerUnavailable as error:
        raise _http_error(error) from error


@router.get("/{tournament_id}", response_model=TournamentResponse)
def get_tournament(tournament_id: int, db: Session = Depends(get_db)):
    try:
        return tournament_service.get_tournament(db, tournament_id)
    except TournamentNotFound as error:
        raise _http_error(error) from error


@router.post("/{tournament_id}/register", response_model=TournamentResponse)
def register(tournament_id: int,
             current_user: User = Depends(get_current_user),
             db: Session = Depends(get_db)):
    try:
        tournament_service.register(db, tournament_id, current_user.id)
        return tournament_service.get_tournament(db, tournament_id,
                                                 current_user.id)
    except (TournamentNotFound, TournamentAlreadyStarted, TournamentExpired,
            AlreadyRegistered, PlayerUnavailable) as error:
        raise _http_error(error) from error


@router.post("/{tournament_id}/start", response_model=TournamentResponse)
def start_tournament(tournament_id: int,
                     current_user: User = Depends(get_current_user),
                     db: Session = Depends(get_db)):
    try:
        tournament_service.start_tournament(db, tournament_id, current_user.id)
        return tournament_service.get_tournament(db, tournament_id,
                                                 current_user.id)
    except (TournamentNotFound, TournamentAlreadyStarted, TournamentExpired,
            NotTournamentOrganizer, InvalidParticipantCount) as error:
        raise _http_error(error) from error
