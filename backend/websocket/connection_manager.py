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
    try:
        while True:
            data = await websocket.receive_json()
            print("Conncected:", data)
    except WebSocketDisconnect:
        manager.disconnect(game_id, user_id)
        print(manager.is_connected(game_id, user_id))

@router.websocket("/test/games/{game_id}/{user_id}")
async def test_game_websocket(
    websocket: WebSocket,
    game_id: int,
    user_id: int
):
    await manager.connect(game_id, user_id, websocket)

    print("Connected:", manager.is_connected(game_id, user_id))

    try:
        while True:
            data = await websocket.receive_json()
            print("Received:", data)

    except WebSocketDisconnect:
        manager.disconnect(game_id, user_id)
        print("Connected:", manager.is_connected(game_id, user_id))