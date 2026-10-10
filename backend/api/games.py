from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from backend.core.dependencies import get_current_user
from backend.db.session import get_db
from backend.models.user import User
from backend.schemas.game import GameResponse, MoveRequest, GameCreate
from backend.services import game_service
from backend.websocket.connection_manager import manager
from backend.exceptions.game import (
    CannotPlayAgainstSelf, GameNotFound, GameNotJoinable, GameNotActive,
    NotAPlayer, NotYourTurn, IllegalMove, CannotResignFinishedGame,
    DrawOfferAlreadyExists, NoDrawOffer, CannotAcceptOwnDrawOffer,
    DrawNotClaimable)

router = APIRouter()


@router.post("/", response_model=GameResponse, status_code=201)
def create_game(game_create: GameCreate | None = None,
                current_user: User = Depends(get_current_user),
                db: Session = Depends(get_db)):
    if game_create is None:
        game_create = GameCreate()

    return game_service.create_game(db, current_user.id,
                                    game_create.initial_time_seconds,
                                    game_create.increment_seconds)


@router.get("/{game_id}", response_model=GameResponse)
def get_game(game_id: int, db: Session = Depends(get_db)):
    try:
        return game_service.get_game(db, game_id)

    except GameNotFound as error:
        raise HTTPException(status_code=404, detail=str(error))


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


@router.post("/{game_id}/move", response_model=GameResponse)
def make_move(game_id: int,
              move_request: MoveRequest,
              current_user: User = Depends(get_current_user),
              db: Session = Depends(get_db)):
    try:
        return game_service.make_move(db, game_id, current_user.id,
                                      move_request.move)

    except GameNotFound as error:
        raise HTTPException(status_code=404, detail=str(error))

    except (GameNotActive, NotAPlayer, NotYourTurn, IllegalMove) as error:
        raise HTTPException(status_code=409, detail=str(error))


@router.post("/{game_id}/resign", response_model=GameResponse)
async def resign_game(game_id: int,
                current_user: User = Depends(get_current_user),
                db: Session = Depends(get_db)):
    try:
        game = game_service.resign(db, game_id, current_user.id)

    except GameNotFound as error:
        raise HTTPException(status_code=404, detail=str(error))

    except (CannotResignFinishedGame, NotAPlayer) as error:
        raise HTTPException(status_code=409, detail=str(error))

    await manager.broadcast(game_id, {"type": "game_state", "fen": game.current_fen})
    await manager.broadcast(game_id, {"type": "game_over", "result": game.result})
    return game


@router.post("/{game_id}/draw-offer", response_model=GameResponse)
def offer_draw(game_id: int,
               current_user: User = Depends(get_current_user),
               db: Session = Depends(get_db)):
    try:
        return game_service.offer_draw(db, game_id, current_user.id)

    except GameNotFound as error:
        raise HTTPException(status_code=404, detail=str(error))

    except (GameNotActive, NotAPlayer, DrawOfferAlreadyExists) as error:
        raise HTTPException(status_code=409, detail=str(error))


@router.post("/{game_id}/draw-offer/accept", response_model=GameResponse)
def accept_draw(game_id: int,
                current_user: User = Depends(get_current_user),
                db: Session = Depends(get_db)):
    try:
        return game_service.accept_draw(db, game_id, current_user.id)

    except GameNotFound as error:
        raise HTTPException(status_code=404, detail=str(error))

    except (GameNotActive, NotAPlayer, NoDrawOffer,
            CannotAcceptOwnDrawOffer) as error:
        raise HTTPException(status_code=409, detail=str(error))


@router.post("/{game_id}/draw-offer/decline", response_model=GameResponse)
def decline_draw(game_id: int,
                 current_user: User = Depends(get_current_user),
                 db: Session = Depends(get_db)):
    try:
        return game_service.decline_draw(db, game_id, current_user.id)

    except GameNotFound as error:
        raise HTTPException(status_code=404, detail=str(error))

    except (GameNotActive, NotAPlayer, NoDrawOffer,
            CannotAcceptOwnDrawOffer) as error:
        raise HTTPException(status_code=409, detail=str(error))


@router.post("/{game_id}/draw-claim/repetition", response_model=GameResponse)
def claim_threefold_repetition(game_id: int,
                               current_user: User = Depends(get_current_user),
                               db: Session = Depends(get_db)):
    try:
        return game_service.claim_threefold_repetition(db, game_id,
                                                       current_user.id)

    except GameNotFound as error:
        raise HTTPException(status_code=404, detail=str(error))

    except (GameNotActive, NotAPlayer, DrawNotClaimable) as error:
        raise HTTPException(status_code=409, detail=str(error))


@router.post("/{game_id}/draw-claim/fifty-move", response_model=GameResponse)
def claim_fifty_move(game_id: int,
                     current_user: User = Depends(get_current_user),
                     db: Session = Depends(get_db)):
    try:
        return game_service.claim_fifty_move(db, game_id, current_user.id)

    except GameNotFound as error:
        raise HTTPException(status_code=404, detail=str(error))

    except (GameNotActive, NotAPlayer, DrawNotClaimable) as error:
        raise HTTPException(status_code=409, detail=str(error))
