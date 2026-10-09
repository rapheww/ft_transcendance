from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy.orm import Session
from backend.core.public_api_security import limiter, require_api_key
from backend.db.session import get_db
from backend.exceptions.tournament import (
    NotTournamentOrganizer, PlayerUnavailable, InvalidParticipantCount,
    TournamentExpired, AlreadyRegistered, TournamentAlreadyStarted,
    TournamentNotFound)
from backend.exceptions.user import UserNotFound
from backend.schemas.stats import LeaderboardEntry
from backend.schemas.tournament import TournamentResponse
from backend.services import stats_service, tournament_service

router = APIRouter()


@router.get("/tournaments/{tournament_id}",
            response_model=TournamentResponse,
            dependencies=[Depends(require_api_key)])
@limiter.limit("30/minute")
def get_tournament(request: Request,
                   tournament_id: int,
                   db: Session = Depends(get_db)):
    try:
        return tournament_service.get_tournament(db, tournament_id)
    except TournamentNotFound as error:
        raise HTTPException(status_code=404, detail=str(error))


@router.get("/leaderboard",
            response_model=list[LeaderboardEntry],
            dependencies=[Depends(require_api_key)])
@limiter.limit("30/minute")
def get_leaderboard(request: Request, db: Session = Depends(get_db)):
    return stats_service.get_leaderboard(db)


@router.post("/tournaments",
             response_model=TournamentResponse,
             status_code=201,
             dependencies=[Depends(require_api_key)])
@limiter.limit("30/minute")
def create_tournament(request: Request, db: Session = Depends(get_db)):
    tournament = tournament_service.create_tournament(db, api_manager=True)
    return tournament_service.get_tournament(db, tournament.id)


@router.put("/tournaments/{tournament_id}/participants/{user_id}",
            response_model=TournamentResponse,
            dependencies=[Depends(require_api_key)])
@limiter.limit("30/minute")
def add_participant(request: Request,
                    tournament_id: int,
                    user_id: int,
                    db: Session = Depends(get_db)):
    try:
        tournament_service.register(db, tournament_id, user_id)
        return tournament_service.get_tournament(db, tournament_id)
    except (TournamentNotFound, UserNotFound) as error:
        raise HTTPException(status_code=404, detail=str(error))
    except (TournamentExpired, PlayerUnavailable, TournamentAlreadyStarted,
            AlreadyRegistered) as error:
        raise HTTPException(status_code=409, detail=str(error))


@router.delete("/tournaments/{tournament_id}",
               status_code=204,
               dependencies=[Depends(require_api_key)])
@limiter.limit("30/minute")
def cancel_tournament(request: Request,
                      tournament_id: int,
                      db: Session = Depends(get_db)):
    try:
        tournament_service.cancel_tournament(db,
                                             tournament_id,
                                             api_manager=True)
    except TournamentNotFound as error:
        raise HTTPException(status_code=404, detail=str(error))
    except NotTournamentOrganizer as error:
        raise HTTPException(status_code=403, detail=str(error))
    except (TournamentExpired, TournamentAlreadyStarted) as error:
        raise HTTPException(status_code=409, detail=str(error))


@router.post("/tournaments/{tournament_id}/start",
             response_model=TournamentResponse,
             dependencies=[Depends(require_api_key)])
@limiter.limit("30/minute")
def start_tournament(request: Request,
                     tournament_id: int,
                     db: Session = Depends(get_db)):
    try:
        tournament_service.start_tournament(db,
                                            tournament_id,
                                            api_manager=True)
        return tournament_service.get_tournament(db, tournament_id)
    except TournamentNotFound as error:
        raise HTTPException(status_code=404, detail=str(error)) from error
    except NotTournamentOrganizer as error:
        raise HTTPException(status_code=403, detail=str(error)) from error
    except (TournamentAlreadyStarted, TournamentExpired,
            InvalidParticipantCount) as error:
        raise HTTPException(status_code=409, detail=str(error)) from error
