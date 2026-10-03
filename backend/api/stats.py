from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from backend.core.dependencies import get_current_user
from backend.db.session import get_db
from backend.models.user import User
from backend.schemas.stats import LeaderboardEntry, MatchHistoryEntry, PlayerStats
from backend.services import stats_service

router = APIRouter()


@router.get("/me", response_model=PlayerStats)
def get_my_stats(current_user: User = Depends(get_current_user),
                 db: Session = Depends(get_db)):
    return stats_service.get_player_stats(db, current_user.id)


@router.get("/history", response_model=list[MatchHistoryEntry])
def get_my_history(current_user: User = Depends(get_current_user),
                   db: Session = Depends(get_db)):
    return stats_service.get_match_history(db, current_user.id)


@router.get("/leaderboard", response_model=list[LeaderboardEntry])
def get_leaderboard(db: Session = Depends(get_db)):
    return stats_service.get_leaderboard(db)
