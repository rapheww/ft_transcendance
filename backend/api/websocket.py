from fastapi import APIRouter, WebSocket, WebSocketDisconnect

router = APIRouter()

@router.websocket("/games/{game_id}")
async def game_websocket(websocket: WebSocket, game_id: int):
    await websocket.accept()

    print("Connected:", game_id)

    try:
        while True:
            data = await websocket.receive_json()

            print("Received:", data)
            await websocket.send_json({
                "type": "echo",
                "data": data
            })
    except WebSocketDisconnect:
        print("disconnected")
