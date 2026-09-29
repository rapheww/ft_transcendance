from fastapi import APIRouter, WebSocket, WebSocketDisconnect
import jwt

from backend.core.security import decode_access_token
from backend.websocket.routes import manager

router = APIRouter()

@router.websocket("/games/{game_id}")
async def game_websocket(websocket: WebSocket, game_id: int):

    token = websocket.query_params.get("token")
    if token is None:
        await websocket.close(code=1008)
        return
    try:
        payload = decode_access_token(token)
        user_id = int(payload["sub"])
    except (jwt.InvalidTokenError, KeyError, ValueError):
        await websocket.close(code=1008)
        return
    await manager.connect(game_id, user_id, websocket)
    await manager.broadcast(
        game_id,
        {
            "type": "player joined",
            "user_id": user_id
        }
    )
    try:
        while True:
            data = await websocket.receive_json()
            print("Received:", data)
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
async def test_game_websocket(websocket: WebSocket, game_id: int, user_id: int):
    await manager.connect(game_id, user_id, websocket)
    await manager.broadcast(
        game_id,
        {
            "type": "player joined",
            "user_id": user_id
        }
    )
    try:
        while True:
            data = await websocket.receive_json()
            print("Received:", data)
            event_type = data.get("type")
            if manager.valid_event(event_type):
                await manager.broadcast(game_id, data)

    except WebSocketDisconnect:
        manager.disconnect(game_id, user_id)
        await manager.broadcast(
            game_id,
            {
                "type": "player_left",
                "user_id": user_id
            }
        )