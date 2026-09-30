from fastapi import WebSocket

class ConnectionManager:

    def __init__(self):
        self.connections = {}

    async def connect(self, game_id: int, user_id: int, websocket: WebSocket):
        await websocket.accept()
        if game_id not in self.connections:
            self.connections[game_id] = {}
        self.connections[game_id][user_id] = websocket
        print("After connect:", self.connections)

    def disconnect(self, game_id: int, user_id: int):
        if game_id not in self.connections:
            return
        self.connections[game_id].pop(user_id, None)
        if not self.connections[game_id]:
            del self.connections[game_id]
        print("After disconnect:", self.connections)

    async def broadcast(self, game_id: int, message: dict):
        if game_id not in self.connections:
            return
        for websocket in self.connections[game_id].values():
            await websocket.send_json(message)

    def valid_event(self, event: str) -> bool:
        return event in { "move" }

    def is_connected(self, game_id: int, user_id: int) ->bool:
        return game_id in self.connections and user_id in self.connections[game_id]

    def get_connection(self, game_id: int, user_id: int):
        return self.connections.get(game_id, {}).get(user_id)

    async def send_personal_message(self, game_id: int, user_id: int, message: dict):
        websocket = self.connections.get(game_id, {}).get(user_id)
        if websocket is not None:
            await websocket.send_json(message)

manager = ConnectionManager()
