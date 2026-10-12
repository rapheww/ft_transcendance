# Game WebSockets

This guide describes how live chess-game updates work in this project. The main
frontend implementation is in [`Chess.tsx`](../frontend/src/components/Chess/Chess.tsx); the FastAPI endpoint
and its per-game connection manager are in
[`backend/websocket/routes.py`](../backend/websocket/routes.py) and
[`backend/websocket/connection_manager.py`](../backend/websocket/connection_manager.py).

## What a WebSocket does here

An HTTP request is normally one request followed by one response. A WebSocket
starts as an HTTP upgrade and then stays open so the client and server can send
messages in either direction. For a game, that means the server can notify both
players as soon as a move or result changes, instead of requiring the browser
to repeatedly ask whether anything happened.

In this application, the socket is a **live update channel**, not the database
and not the authority that decides whether a move is legal. The backend game
service validates and persists the game. REST requests and the WebSocket
handler can both invoke that service; WebSocket broadcasts then notify
connected clients about the resulting state.

## Endpoint and access control

The backend mounts the game router under `/ws`, making the endpoint:

```text
ws://127.0.0.1:8000/ws/games/{game_id}?token={access_token}
```

The chess screen constructs this URL in `Chess.tsx`, URL-encoding the access
token because browsers do not let the WebSocket constructor set arbitrary
authorization headers. Before accepting the connection, the server:

1. Decodes and validates the access token.
2. Loads the requested game.
3. Checks that the user is assigned to that game (AI games permit their human
   player).
4. Determines the player's color.

Invalid credentials, nonexistent games, and users who are not players are
rejected with WebSocket policy close code `1008`.

## Connection lifecycle

When `Chess.tsx` mounts for a valid game ID, it opens a socket and registers
handlers for open, message, error, and close events.

After validating a connection, the backend registers it with the
`ConnectionManager`. Connections are grouped by game ID and user ID. If that
same user connects again, the new connection replaces the old one. The manager
also checks socket identity when disconnecting, so a delayed close from an old
socket cannot unregister its replacement.

The server registers the connection **before** reading and sending the initial
game snapshot. This ordering helps ensure that broadcasts occurring during
snapshot creation are not silently missed. The server then broadcasts
`player_joined` to the game. On disconnect, it removes only the current socket
and broadcasts `player_left` if the player no longer has an active connection.
The current chess screen does not display these presence events.

The React effect cleans up by clearing a pending reconnect timer, detaching
event handlers, and closing its socket. Detaching handlers first prevents
cleanup from scheduling another retry or updating state after the component
has moved on to a different game.

## Snapshots and incremental events

These two kinds of messages solve different problems:

- A **snapshot** is a full current view of the game. It is sent as
  `game_connected` each time a client connects, including after a reconnect.
  The snapshot contains the current FEN, full PGN, status, result, player ID,
  color, and side to move.
- An **incremental event** describes something that changed after a snapshot,
  such as one accepted move or a game-state update. It avoids retransmitting
  the full move history after every move.

FEN (Forsyth–Edwards Notation) describes one board position. PGN (Portable
Game Notation) records the move history. The frontend uses `chess.js` to parse
the snapshot PGN into SAN move labels and the FEN after each move. SAN is the
human-readable notation shown in the move list (for example, `Nf3`).

### Server-to-client event types

| `type`                          | Purpose                                                                                               | Main fields used by the chess screen 
|                                 |                                                                                                       | 
| `game_connected`                | Initial or reconnect snapshot; also resets the retry counter.                                         | `fen`, `pgn`, `status`, `result`
| `move`                          | A human or AI move was accepted and applied.                                                          | `san`, `fen`
| `game_state`                    | Current position/status/result changed; may be sent even when no move was applied, such as a timeout. | `fen`, `status`, `result`
| `game_over`                     | The game has reached a terminal result.                                                               | `result`
| `error`                         | The server could not process an event or encountered an error.                                        | `message`, optionally `code`
| `player_joined` / `player_left` | A player connected or disconnected.                                                                   | `user_id`
| `chat`                          | A chat message was broadcast.                                                                         | `user_id`, `message`
| `pong`                          | Response to an application-level `ping`.                                                              | -

The `move` event's FEN is the resulting position. `game_state` carries the
latest game state separately from the move history. For example, on an
ordinary accepted move, clients may receive both `move` (to extend the move
list) and `game_state` (to update the current status/result). A terminal game
can then also produce `game_over`.

## How the chess screen applies events

The REST request and socket can finish in either order during initial loading.
`Chess.tsx` therefore stores the latest socket game state in a ref. When the
REST response arrives, it uses the socket state if one has already arrived,
so an older REST response does not overwrite a newer socket position or result.
If the socket has not supplied a history snapshot yet, the screen builds the
move list from the REST response's PGN.

On `game_connected`, the screen updates the current FEN and game status, parses
the PGN, and sets the move list to the snapshot's history. It also buffers any
`move` events that arrived before the snapshot was processed. Once the snapshot
is ready, buffered moves are appended to its history and the buffer is cleared.
This handles the race where a move broadcast arrives while the initial history
is being restored.

The helper `appendMove` avoids adding a move when its resulting FEN is already
present in the history. This is used when merging buffered events into a
snapshot and when appending later live moves.

After the snapshot, a `move` event contributes its SAN/FEN pair to the move
list. A `game_state` event updates the current position and game status/result
without rebuilding that list. `game_over` marks the game finished, updates the
result, and prevents further reconnect attempts.

The move list is also the basis for replay. Each half-move stores the FEN after
that move, and clicking a row or pressing the left/right arrow keys selects a
history index. The board can therefore show an earlier position without
changing the persisted live game.

## How moves are sent

There are two move-input paths on the backend:

1. **Current chessboard path:** `Chessboard.tsx` sends a move to
   `POST /api/games/{game_id}/move`. The backend validates and persists it,
   then broadcasts `move`, `game_state`, and (when finished) `game_over` to
   WebSocket subscribers. The submitting player receives the HTTP response;
   both players receive the socket broadcast.
2. **WebSocket command path:** `backend/websocket/routes.py` also accepts a
   client event such as `{"type":"move","from":"e2","to":"e4"}`. It validates
   and persists the move through the game service, broadcasts the result, and
   can start an AI reply. The current `Chess.tsx`/`Chessboard.tsx` flow does not
   send moves this way.

The current board also checks legality locally for quick feedback and displays
the position returned by the HTTP API. That local check is not a security
boundary: the backend remains responsible for validating the move.

For AI games, the backend runs the AI turn in a background task after the human
move. Once persisted, the AI move is sent through the same `move` and
`game_state` broadcast pattern, so the frontend does not need a separate AI
update path.

The WebSocket handler also accepts `chat` events and validates their message
before broadcasting them. The chat area in the current chess screen is only a
placeholder and does not yet send or render these events.

## Reconnection and recovery

If the connection closes unexpectedly, the chess screen retries with
exponential backoff: it starts at one second, doubles the delay after each
failure, and caps each delay at ten seconds. After eight unsuccessful attempts
it marks the connection as disconnected and asks the user to reload. A
successful `game_connected` snapshot resets the retry counter.

Every reconnect gets a fresh snapshot from the database, including the latest
FEN and full PGN. This is what recovers changes that occurred while the browser
was offline; the client does not need to guess which incremental events it
missed.

The backend responds to an application-level `{"type":"ping"}` with
`{"type":"pong"}`. The current `Chess.tsx` socket does not send application
level pings; connection health is currently surfaced through the browser
socket's open/error/close events and the server's WebSocket transport
keepalive.

## Related code and scope notes

- [`Chess.tsx`](./Chess.tsx) owns the game screen's active WebSocket, reconnect
  logic, event handling, and live/replay state.
- [`Chessboard.tsx`](./Chessboard.tsx) submits moves through the REST API and
  renders the FEN passed down from the game screen.
- [`routes.py`](../../../../backend/websocket/routes.py) authenticates
  connections, sends snapshots, handles WebSocket input, and broadcasts game
  events.
- [`connection_manager.py`](../../../../backend/websocket/connection_manager.py)
  tracks per-game sockets and handles replacement, broadcast, and cleanup.
- [`ai_turn.py`](../../../../backend/websocket/ai_turn.py) applies AI moves in
  the background and broadcasts them using the same event types.
- [`useGameSocket.tsx`](./useGameSocket.tsx) is a separate generic socket hook;
  the current `Chess` component manages its own richer connection and does not
  call this hook.
