from fastapi import WebSocket

class NotificationManager:
    def __init__(self):
        self.connections: dict[int, WebSocket] = {}

    async def connect(self, user_id: int, websocket: WebSocket):
        await websocket.accept()
        old_socket = self.connections.get(user_id)
        if old_socket is not None and old_socket is not websocket:
            try:
                await old_socket.close(code=4001,
                                       reason="replaced by new connection")
            except Exception:
                pass
        self.connections[user_id] = websocket

    def disconnect(self, user_id: int, websocket: WebSocket) -> bool:
        if not self.connections:
            return False
        if self.connections.get(user_id) is not websocket:
            return False
        self.connections.pop(user_id, None)
        return True

    async def send(self, user_id: int, message: dict) -> bool:
        websocket = self.connections.get(user_id)
        if websocket is None:
            return False
        try:
            await websocket.send_json(message)
            return True
        except Exception:
            self.disconnect(user_id, websocket)
            return False

notification_manager = NotificationManager()