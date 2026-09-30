from fastapi import APIRouter, WebSocket, WebSocketDisconnect, Depends
import jwt

from sqlalchemy.orm import Session
from backend.db.session import get_db
from backend.core.security import decode_access_token
from backend.websocket.connection_manager import manager
from backend.services import game_service

router = APIRouter()

@router.websocket("/games/{game_id}")
async def game_websocket(websocket: WebSocket, game_id: int, db: Session = Depends(get_db)):

    token = websocket.query_params.get("token")
    if token is None:
        await websocket.close(code=1008)
        return
    try:
        payload = decode_access_token(token)
        if payload.get("type") != "access":
            await websocket.close(code=1008)
            return
        user_id = int(payload["sub"])
    except (jwt.InvalidTokenError, KeyError, ValueError):
        await websocket.close(code=1008)
        return
    await manager.connect(game_id, user_id, websocket)
    await manager.broadcast(
        game_id,
        {
            "type": "player_joined",
            "user_id": user_id
        }
    )
    try:
        while True:
            data = await websocket.receive_json()
            event_type = data.get("type")
            if not manager.valid_event(event_type):
                await websocket.send_json({
                    "type": "error",
                    "message": "Invalid event"
                })
                continue
            if event_type == "move":
                from_pos = data.get("from")
                to_pos = data.get("to")
                if not from_pos or not to_pos:
                    await websocket.send_json ({
                        "type": "error",
                        "message": "invalid move event"
                    })
                    continue
                try:
                    game = game_service.make_move(db, game_id, user_id, from_pos, to_pos)
                    await manager.broadcast(
                        game_id, 
                        {
                            "type": "move",
                            "user_id": user_id,
                            "from": from_pos,
                            "to": to_pos,
                        }
                    )
                    await manager.broadcast(
                        game_id, 
                        {
                            "type": "game_state",
                            "fen": game.current_fen
                        }
                    )
                except ValueError as error:
                    await websocket.send_json({
                        "type": "error",
                        "message": str(error)
                    })
    except WebSocketDisconnect:
        manager.disconnect(game_id, user_id)
        await manager.broadcast(
            game_id,
            {
                "type": "player_left",
                "user_id": user_id
            }
        )

@router.websocket("/test/games/{game_id}/{user_id}")
async def test_game_websocket(websocket: WebSocket, game_id: int, user_id: int, db: Session = Depends(get_db)):
    await manager.connect(game_id, user_id, websocket)
    await manager.broadcast(
        game_id,
        {
            "type": "player_joined",
            "user_id": user_id
        }
    )
    try:
        while True:
            data = await websocket.receive_json()
            event_type = data.get("type")
            if not manager.valid_event(event_type):
                await websocket.send_json({
                    "type": "error",
                    "message": "Invalid event"
                })
                continue
            if event_type == "move":
                from_pos = data.get("from")
                to_pos = data.get("to")
                if not from_pos or not to_pos:
                    await websocket.send_json ({
                            "type": "error",
                            "message": "invalid move event"
                    })
                    continue
                
                try:
                    game = game_service.make_move(db, game_id, user_id, from_pos, to_pos)
                    await manager.broadcast(
                        game_id, 
                        {
                            "type": "move",
                            "user_id": user_id,
                            "from": from_pos,
                            "to": to_pos
                        }
                    )
                    await manager.broadcast(
                        game_id, 
                        {
                            "type": "game_state",
                            "fen": game.current_fen
                        }
                    )
                except ValueError as error:
                    await websocket.send_json({
                            "type": "error",
                            "message": str(error)
                    })
    except WebSocketDisconnect:
        manager.disconnect(game_id, user_id)
        await manager.broadcast(
            game_id,
            {
                "type": "player_left",
                "user_id": user_id
            }
        )