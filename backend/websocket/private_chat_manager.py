from fastapi import WebSocket
from starlette.websockets import WebSocketDisconnect


class PrivateChatConnectionManager:

    def __init__(self):
        self.connections: dict[int, dict[int, WebSocket]] = {}

    async def connect(self, conversation_id: int, user_id: int,
                      websocket: WebSocket) -> None:
        await websocket.accept()
        conversation_connections = self.connections.setdefault(
            conversation_id, {})
        old_socket = conversation_connections.get(user_id)
        conversation_connections[user_id] = websocket
        if old_socket is not None and old_socket is not websocket:
            try:
                await old_socket.close(code=4001,
                                       reason="replaced by new connection")
            except (RuntimeError, WebSocketDisconnect, OSError):
                pass

    def disconnect(self, conversation_id: int, user_id: int,
                   websocket: WebSocket) -> bool:
        conversation_connections = self.connections.get(conversation_id)
        if (not conversation_connections
                or conversation_connections.get(user_id) is not websocket):
            return False
        conversation_connections.pop(user_id)
        if not conversation_connections:
            self.connections.pop(conversation_id, None)
        return True

    async def send_to_conversation(self, conversation_id: int,
                                   user_ids: tuple[int, int],
                                   message: dict) -> None:
        dead_connections = []
        for user_id in user_ids:
            websocket = self.connections.get(conversation_id, {}).get(user_id)
            if websocket is None:
                continue
            try:
                await websocket.send_json(message)
            except (RuntimeError, WebSocketDisconnect, OSError):
                dead_connections.append((user_id, websocket))

        for user_id, websocket in dead_connections:
            self.disconnect(conversation_id, user_id, websocket)


private_chat_manager = PrivateChatConnectionManager()
