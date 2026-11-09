"""Add-on routes for the optional tournament bots (the tournament routes are unchanged).

POST /api/tournaments/{id}/bots  -> organizer fills the empty places with bots (before Start)
GET  /api/tournaments/{id}/bots  -> the bots of a tournament, for the "AI" labels
"""
from fastapi import APIRouter, Depends
from pydantic import BaseModel
from sqlalchemy.orm import Session

from backend.api.tournaments import _http_error
from backend.core.dependencies import get_current_user
from backend.db.session import get_db
from backend.exceptions.tournament import (NotTournamentOrganizer, TournamentAlreadyStarted,
                                           TournamentExpired, TournamentNotFound)
from backend.models.user import User
from backend.schemas.tournament import TournamentResponse
from backend.services import tournament_bots, tournament_service

router = APIRouter()


class BotInfo(BaseModel):
    id: int
    username: str
    ai_level: str | None
    style: str | None
    elo: int

    model_config = {"from_attributes": True}


@router.post("/{tournament_id}/bots", response_model=TournamentResponse)
def fill_with_bots(tournament_id: int,
                   current_user: User = Depends(get_current_user),
                   db: Session = Depends(get_db)):
    try:
        tournament_bots.fill_with_bots(db, tournament_id, current_user.id)
        return tournament_service.get_tournament(db, tournament_id, current_user.id)
    except (TournamentNotFound, NotTournamentOrganizer, TournamentAlreadyStarted,
            TournamentExpired) as error:
        raise _http_error(error) from error


@router.get("/{tournament_id}/bots", response_model=list[BotInfo])
def list_bots(tournament_id: int, db: Session = Depends(get_db)):
    try:
        return tournament_bots.tournament_bots(db, tournament_id)
    except TournamentNotFound as error:
        raise _http_error(error) from error
