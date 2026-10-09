from fastapi import WebSocket


class ConnectionManager:

    def __init__(self):
        # {game_id: {user_id: websocket}}
        self.connections = {}

    async def connect(self, game_id: int, user_id: int, websocket: WebSocket):
        await websocket.accept()
        if game_id not in self.connections:
            self.connections[game_id] = {}
        # ---- RECONNECTION / DUPLICATE CONNECTION CASE ----
        # if the same user reconnects, close the old socket
        # and replace it with the new one
        old_socket = self.connections[game_id].get(user_id)
        # register the new socket first, so nothing is sent to the old one
        self.connections[game_id][user_id] = websocket
        if old_socket is not None and old_socket is not websocket:
            try:
                await old_socket.close(code=4001,
                                       reason="replaced by new connection")
            except Exception:
                pass

    def disconnect(self, game_id: int, user_id: int,
                   websocket: WebSocket) -> bool:
        game_connections = self.connections.get(game_id)
        # report that nothing was removed
        if not game_connections:
            return False
        # ---- OLD SOCKET CASE ----
        # Do not remove a newer socket if the old socket disconnects
        # after the user has already reconnected
        if game_connections.get(user_id) is not websocket:
            return False
        game_connections.pop(user_id, None)
        # ---- CLEANUP EMPTY GAME ----
        # remove the game entry when no players remain connected
        if not game_connections:
            self.connections.pop(game_id, None)
        return True

    async def broadcast(self, game_id: int, message: dict):
        if game_id not in self.connections:
            return

        dead_connections = []
        # broadcast only to users connected to this game
        for user_id, websocket in list(self.connections[game_id].items()):
            try:
                await websocket.send_json(message)
            # ---- DEAD SOCKET / ABRUPT NETWORK LOSS CASE ----
            # remember failed sockets and clean them after the loop
            except Exception:
                dead_connections.append((user_id, websocket))
        # do not modify the dictionary while iterating over it
        for user_id, websocket in dead_connections:
            self.disconnect(game_id, user_id, websocket)

    def valid_event(self, event: str) -> bool:
        return isinstance(event, str) and event in {"move", "chat"}

    def is_connected(self, game_id: int, user_id: int) -> bool:
        return game_id in self.connections and user_id in self.connections[
            game_id]

    def get_connection(self, game_id: int, user_id: int) -> WebSocket | None:
        return self.connections.get(game_id, {}).get(user_id)

    async def send_personal_message(self, game_id: int, user_id: int,
                                    message: dict) -> bool:
        websocket = self.get_connection(game_id, user_id)
        if websocket is None:
            return False
        try:
            await websocket.send_json(message)
            return True
        except Exception:
            self.disconnect(game_id, user_id, websocket)
            return False


manager = ConnectionManager()
