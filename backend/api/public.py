from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy.orm import Session
from backend.core.api_key import require_api_key
from backend.core.rate_limit import limiter
from backend.db.session import get_db
from backend.exceptions.tournament import (AlreadyRegistered,
                                           TournamentAlreadyStarted,
                                           TournamentNotFound)
from backend.exceptions.user import UserNotFound
from backend.schemas.stats import LeaderboardEntry
from backend.schemas.tournament import TournamentCreateRequest, TournamentResponse
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
def create_tournament(request: Request,
                      body: TournamentCreateRequest,
                      db: Session = Depends(get_db)):
    try:
        tournament = tournament_service.create_tournament(db, body.creator_id)
        return tournament_service.get_tournament(db, tournament.id)
    except UserNotFound as error:
        raise HTTPException(status_code=404, detail=str(error))


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
    except (TournamentAlreadyStarted, AlreadyRegistered) as error:
        raise HTTPException(status_code=409, detail=str(error))


@router.delete("/tournaments/{tournament_id}",
               status_code=204,
               dependencies=[Depends(require_api_key)])
@limiter.limit("30/minute")
def cancel_tournament(request: Request,
                      tournament_id: int,
                      db: Session = Depends(get_db)):
    try:
        tournament_service.cancel_tournament(db, tournament_id)
    except TournamentNotFound as error:
        raise HTTPException(status_code=404, detail=str(error))
    except TournamentAlreadyStarted as error:
        raise HTTPException(status_code=409, detail=str(error))
