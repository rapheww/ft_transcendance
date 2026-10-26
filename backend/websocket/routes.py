import jwt
import chess
import logging
from uuid import uuid4
from sqlalchemy.orm import Session
from backend.db.session import get_db, SessionLocal
from backend.core.security import decode_access_token
from backend.websocket.connection_manager import manager
from backend.services import game_service
from fastapi import APIRouter, WebSocket, WebSocketDisconnect, Depends, HTTPException
from backend.exceptions.game import GameNotFound, GameNotActive, NotAPlayer, NotYourTurn, IllegalMove, NotAIGame, InvalidDifficulty
from backend.websocket.ai_turn import start_ai_turn
from backend.models.chat_message import ChatMessage
from backend.models.user import User

router = APIRouter()
logger = logging.getLogger(__name__)


@router.websocket("/games/{game_id}")
async def game_websocket(websocket: WebSocket,
                         game_id: int,
                         db: Session = Depends(get_db)):

    # ------ TOKEN CHECK ------
    token = websocket.query_params.get("token")
    user_id = None
    if token is not None:
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

    # ------ GAME & PLAYER CHECK ------
    try:
        game = game_service.get_game(db, game_id)
    # check the game exists
    except GameNotFound:
        await websocket.close(code=1008)
        return

    is_player = (user_id is not None
                 and user_id in (game.white_player_id, game.black_player_id))
    is_spectator = not is_player
    if is_spectator and game.status not in ("active", "finished"):
        await websocket.close(code=1008)
        return

    spectator_id = (user_id if user_id is not None else
                    f"guest:{uuid4().hex}")
    player_color = None
    if is_player:
        player_color = ("white" if user_id == game.white_player_id else
                        "black")

    db.close()

    # ====== PREPARATION FOR EVENT LOOP ======
    try:
        if is_spectator:
            await manager.connect_spectator(game_id, spectator_id, websocket)
        else:
            await manager.connect(game_id, user_id, websocket)

        # Register before reading the snapshot so any moves broadcast during
        # the read are delivered after the client connects.
        with SessionLocal() as snapshot_db:
            game = game_service.get_game(snapshot_db, game_id)
            chat_messages = []
            if is_player:
                chat_messages = (snapshot_db.query(ChatMessage).filter(
                    ChatMessage.game_id == game_id).order_by(
                        ChatMessage.id.asc()).all())
        board = chess.Board(game.current_fen)
        await websocket.send_json({
            "type":
            "game_connected",
            "user_id":
            user_id,
            "role":
            "spectator" if is_spectator else "player",
            "color":
            player_color,
            "fen":
            game.current_fen,
            "pgn":
            game.pgn,
            "status":
            game.status,
            "result":
            game.result,
            "chat": [{
                "id": chat_message.id,
                "user_id": chat_message.user_id,
                "username": chat_message.username,
                "message": chat_message.message
            } for chat_message in chat_messages],
            "turn":
            "white" if board.turn == chess.WHITE else "black",
            "white_time_remaining":
            game.white_time_remaining,
            "black_time_remaining":
            game.black_time_remaining,
            "increment_seconds":
            game.increment_seconds,
            "last_move_at":
            game.last_move_at.isoformat() if game.last_move_at else None,
            "spectator_count":
            manager.spectator_count(game_id)
        })

        if is_player:
            await manager.broadcast(game_id, {
                "type": "player_joined",
                "user_id": user_id
            })
        else:
            await manager.broadcast(game_id, {
                "type": "spectator_count",
                "count": manager.spectator_count(game_id)
            })
    except (WebSocketDisconnect, RuntimeError):
        if is_spectator:
            manager.disconnect_spectator(game_id, spectator_id, websocket)
        else:
            manager.disconnect(game_id, user_id, websocket)
        return

    # retry a stuck AI turn when the player reconnects
    if is_player:
        start_ai_turn(game_id)
    # ====== EVENT LOOP ======
    try:
        while True:
            # ----- DATA CHECK ------
            try:
                data = await websocket.receive_json()
            except (ValueError, KeyError):
                await websocket.send_json({
                    "type": "error",
                    "message": "Invalid JSON"
                })
                continue
            if not isinstance(data, dict):
                await websocket.send_json({
                    "type": "error",
                    "message": "Invalid event"
                })
                continue
            event_type = data.get("type")

            # ------ HEARTBEAT CHECK ------
            # the frontend sends a ping regulary to check the connection is alive
            # reply with a pong so the client know the server is still reachable
            # (dead clients are detected by uvicorn's own protocol pings)
            if event_type == "ping":
                await websocket.send_json({"type": "pong"})
                continue

            if is_spectator:
                await websocket.send_json({
                    "type": "error",
                    "message": "Spectators cannot send game actions"
                })
                continue

            # ------ EVENT TYPE CHECK ------
            # check if event_type is valid
            if not manager.valid_event(event_type):
                await websocket.send_json({
                    "type": "error",
                    "message": "Invalid event"
                })
                continue

            try:
                # ====== MOVE EVENT ======
                if event_type == "move":

                    # ------ MOVE CHECK ------
                    from_pos = data.get("from")
                    to_pos = data.get("to")
                    # check if move fields are missing or empty
                    if not isinstance(from_pos, str) or not isinstance(
                            to_pos, str):
                        await websocket.send_json({
                            "type":
                            "error",
                            "message":
                            "invalid move event"
                        })
                        continue
                    # check if chess squares are valid
                    try:
                        chess.parse_square(from_pos)
                        chess.parse_square(to_pos)
                    except ValueError:
                        await websocket.send_json({
                            "type":
                            "error",
                            "message":
                            "invalid chess square"
                        })
                        continue

                    promotion = data.get("promotion")
                    if promotion is not None and promotion not in ("q", "r",
                                                                   "b", "n"):
                        await websocket.send_json({
                            "type":
                            "error",
                            "message":
                            "invalid promotion",
                        })
                        continue
                    uci = from_pos + to_pos
                    if promotion is not None:
                        uci += promotion

                    # 1. Apply human move
                    with SessionLocal() as move_db:
                        game_before = game_service.get_game(move_db, game_id)
                        board_before = chess.Board(game_before.current_fen)
                        game = game_service.make_move(move_db, game_id,
                                                      user_id, uci)
                        fen = game.current_fen
                        status = game.status
                        result = game.result

                    # on timeout, make_move ends the game without playing the move:
                    # the turn did not change, so there is no move to announce
                    board_after = chess.Board(fen)
                    move_applied = board_after.turn != (
                        player_color == "white")

                    # 2. Broadcast human move
                    if move_applied:
                        await manager.broadcast(
                            game_id, {
                                "type": "move",
                                "player": "human",
                                "user_id": user_id,
                                "from": from_pos,
                                "to": to_pos,
                                "uci": uci,
                                "san": board_before.san(
                                    chess.Move.from_uci(uci)),
                                "fen": fen,
                                "white_time_remaining":
                                game.white_time_remaining,
                                "black_time_remaining":
                                game.black_time_remaining,
                                "increment_seconds":
                                game.increment_seconds,
                                "last_move_at":
                                game.last_move_at.isoformat()
                                if game.last_move_at else None
                            })

                    await manager.broadcast(game_id, {
                        "type": "game_state",
                        "fen": fen,
                        "status": status,
                        "result": result,
                        "white_time_remaining": game.white_time_remaining,
                        "black_time_remaining": game.black_time_remaining,
                        "increment_seconds": game.increment_seconds,
                        "last_move_at": game.last_move_at.isoformat()
                        if game.last_move_at else None,
                    })
                    if status == "finished":
                        await manager.broadcast(game_id, {
                            "type": "game_over",
                            "result": result,
                        })
                        continue
                    # 3. Let the AI answer in the background
                    start_ai_turn(game_id)
                # ====== CHAT EVENT ======
                elif event_type == "chat":
                    message = data.get("message")
                    # check message exists and is a non-empty string
                    if not isinstance(message, str) or not message.strip():
                        await websocket.send_json({
                            "type":
                            "error",
                            "message":
                            "Chat message is required"
                        })
                        continue
                    # check maximum chat length
                    if len(message) > 500:
                        await websocket.send_json({
                            "type":
                            "error",
                            "message":
                            "message is too long"
                        })
                        continue
                    with SessionLocal() as chat_db:
                        sender = chat_db.query(User).filter(
                            User.id == user_id).first()
                        if sender is None:
                            await websocket.send_json({
                                "type": "error",
                                "message": "Chat sender no longer exists"
                            })
                            continue
                        chat_message = ChatMessage(
                            game_id=game_id,
                            user_id=user_id,
                            username=sender.username,
                            message=message.strip())
                        chat_db.add(chat_message)
                        chat_db.commit()
                        chat_db.refresh(chat_message)
                        persisted_message = {
                            "type": "chat",
                            "id": chat_message.id,
                            "user_id": chat_message.user_id,
                            "username": chat_message.username,
                            "message": chat_message.message
                        }
                    await manager.broadcast(game_id, persisted_message)
            except (GameNotActive, NotAPlayer, NotYourTurn, IllegalMove,
                    NotAIGame, InvalidDifficulty) as error:
                await websocket.send_json({
                    "type": "error",
                    "message": str(error)
                })
                continue
            except WebSocketDisconnect:
                raise
            # ------ UNEXPECTED SERVER ERROR ------
            except Exception:
                db.rollback()
                logger.exception("Unexpected WebSocket error in game %s",
                                 game_id)
                await websocket.send_json({
                    "type": "error",
                    "code": "server_error",
                    "message": "internal server error"
                })
                continue

    # ------ DISCONNECT CHECK ------
    except (WebSocketDisconnect, RuntimeError):
        pass
    # always executes after the try and except blocks
    finally:
        if is_spectator:
            removed = manager.disconnect_spectator(
                game_id, spectator_id, websocket)
            if removed:
                await manager.broadcast(game_id, {
                    "type": "spectator_count",
                    "count": manager.spectator_count(game_id)
                })
        else:
            manager.disconnect(game_id, user_id, websocket)
        if is_player and not manager.is_connected(game_id, user_id):
            await manager.broadcast(game_id, {
                "type": "player_left",
                "user_id": user_id
            })
