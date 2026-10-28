from fastapi import APIRouter, WebSocket, WebSocketDisconnect, HTTPException
import jwt

from backend.core.security import decode_access_token
from backend.websocket.notification_manager import notification_manager

router = APIRouter()

@router.websocket("/notifications")
async def notification_websocket(websocket: WebSocket):
    token = websocket.query_params.get("token")
    if token is None:
        await websocket.close(code=1008)
        return
    try:
        payload = decode_access_token(token)
        if payload is None:
            await websocket.close(code=1008)
            return
        if payload.get("type") != "access":
            await websocket.close(code=1008)
            return
        user_id = int(payload["sub"])
    except (jwt.ExpiredSignatureError, jwt.InvalidTokenError, KeyError,
            ValueError, TypeError, HTTPException):
        await websocket.close(code=1008)
        return

    try:
        await notification_manager.connect(user_id, websocket)

        # Keep socket alive.
        while True:
            try:
                data = await websocket.receive_json()
                if isinstance(data, dict) and data.get("type") == "ping":
                    await websocket.send_json({
                        "type": "pong"
                    })
            except ValueError:
                await websocket.send_json({
                    "type": "error",
                    "message": "Invalid JSON",
                })
                continue
        
    except WebSocketDisconnect:
        pass

    finally:
        notification_manager.disconnect(user_id, websocket)