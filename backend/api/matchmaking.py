from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from backend.core.dependencies import get_current_user
from backend.db.session import get_db
from backend.models.user import User
from backend.services import matchmaking_service
from backend.repositories.game_repository import GameRepository
from backend.exceptions.matchmaking import AlreadyInMatchmaking, NotInMatchmaking
from backend.exceptions.tournament import PlayerUnavailable
from backend.schemas.matchmaking import MatchmakingRequest, MatchmakingResponse

router = APIRouter()


@router.post("/join",
             response_model=MatchmakingResponse,
             status_code=status.HTTP_201_CREATED)
def join_matchmaking(request: MatchmakingRequest,
                     current_user: User = Depends(get_current_user),
                     db: Session = Depends(get_db)):
    try:
        entry = matchmaking_service.join_queue(db, current_user.id,
                                               request.initial_time_seconds,
                                               request.increment_seconds)

        game = matchmaking_service.find_match(db, current_user.id,
                                              request.initial_time_seconds,
                                              request.increment_seconds)

        if game is not None:
            return MatchmakingResponse(
                status="matched",
                id=entry.id,
                user_id=entry.user_id,
                initial_time_seconds=entry.initial_time_seconds,
                increment_seconds=entry.increment_seconds,
                created_at=entry.created_at,
                game_id=game.id)

        return MatchmakingResponse(
            status="waiting",
            id=entry.id,
            user_id=entry.user_id,
            initial_time_seconds=entry.initial_time_seconds,
            increment_seconds=entry.increment_seconds,
            created_at=entry.created_at)

    except (AlreadyInMatchmaking, PlayerUnavailable) as error:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT,
                            detail=str(error))


@router.delete("/leave", status_code=status.HTTP_204_NO_CONTENT)
def leave_matchmaking(current_user: User = Depends(get_current_user),
                      db: Session = Depends(get_db)):
    try:
        matchmaking_service.leave_queue(db, current_user.id)

    except NotInMatchmaking as error:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,
                            detail=str(error))


@router.get("/status", response_model=MatchmakingResponse | None)
def matchmaking_status(current_user: User = Depends(get_current_user),
                       db: Session = Depends(get_db)):
    entry = matchmaking_service.get_queue_entry(db, current_user.id)

    if entry is not None:
        return MatchmakingResponse(
            status="waiting",
            id=entry.id,
            user_id=entry.user_id,
            initial_time_seconds=entry.initial_time_seconds,
            increment_seconds=entry.increment_seconds,
            created_at=entry.created_at)

    game_repository = GameRepository(db)
    game = game_repository.get_active_game_for_user(current_user.id)

    if game is not None:
        print(
            f"[MATCHMAKING DEBUG] user_id={current_user.id}, "
            f"game_id={game.id}, "
            f"white_player_id={game.white_player_id}, "
            f"black_player_id={game.black_player_id}, "
            f"status={game.status}"
        )
    if game is not None:
        return MatchmakingResponse(
            status="matched",
            user_id=current_user.id,
            initial_time_seconds=game.initial_time_seconds,
            increment_seconds=game.increment_seconds,
            created_at=game.created_at,
            game_id=game.id)

    return None
