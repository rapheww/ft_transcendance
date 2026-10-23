from fastapi import WebSocket


class ConnectionManager:

    def __init__(self):
        # {game_id: {user_id: websocket}}
        self.connections = {}
        self.spectators = {}

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

    async def connect_spectator(self, game_id: int, user_id: int | str,
                                websocket: WebSocket):
        await websocket.accept()
        game_spectators = self.spectators.setdefault(game_id, {})
        old_socket = game_spectators.get(user_id)
        game_spectators[user_id] = websocket
        if old_socket is not None and old_socket is not websocket:
            try:
                await old_socket.close(code=4001,
                                       reason="replaced by new connection")
            except Exception:
                pass

    def disconnect(self, game_id: int, user_id: int,
                   websocket: WebSocket) -> bool:
        return self._disconnect(self.connections, game_id, user_id, websocket)

    def disconnect_spectator(self, game_id: int, user_id: int | str,
                             websocket: WebSocket) -> bool:
        return self._disconnect(self.spectators, game_id, user_id, websocket)

    def _disconnect(self, connection_group: dict, game_id: int,
                    user_id: int | str, websocket: WebSocket) -> bool:
        game_connections = connection_group.get(game_id)
        # report that nothing was removed
        if not game_connections:
            return False
        # ---- OLD SOCKET CASE ----
        # Do not remove a newer socket if the old socket disconnects
        # after the user has already reconnected
        if game_connections.get(user_id) is not websocket:
            return False
        game_connections.pop(user_id, None)
        if not game_connections:
            connection_group.pop(game_id, None)
        if not self.connections.get(game_id) and not self.spectators.get(game_id):
            self.connections.pop(game_id, None)
            self.spectators.pop(game_id, None)
        return True

    async def broadcast(self, game_id: int, message: dict):
        dead_connections = []
        for connection_group, is_spectator in (
                (self.connections, False), (self.spectators, True)):
            for user_id, websocket in list(
                    connection_group.get(game_id, {}).items()):
                try:
                    await websocket.send_json(message)
                except Exception:
                    dead_connections.append(
                        (is_spectator, user_id, websocket))
        for is_spectator, user_id, websocket in dead_connections:
            if is_spectator:
                self.disconnect_spectator(game_id, user_id, websocket)
            else:
                self.disconnect(game_id, user_id, websocket)

    def valid_event(self, event: str) -> bool:
        return isinstance(event, str) and event in {"move", "chat"}

    def is_connected(self, game_id: int, user_id: int) -> bool:
        return game_id in self.connections and user_id in self.connections[
            game_id]

    def get_connection(self, game_id: int, user_id: int) -> WebSocket | None:
        return self.connections.get(game_id, {}).get(user_id)

    def spectator_count(self, game_id: int) -> int:
        return len(self.spectators.get(game_id, {}))

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
