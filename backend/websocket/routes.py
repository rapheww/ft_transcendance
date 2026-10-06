from fastapi import APIRouter, WebSocket, WebSocketDisconnect, Depends, HTTPException
import jwt
import chess
import asyncio
import logging
logger = logging.getLogger(__name__)

from sqlalchemy.orm import Session
from backend.db.session import get_db
from backend.core.security import decode_access_token
from backend.websocket.connection_manager import manager
from backend.services import game_service
from backend.exceptions.game import GameNotFound, GameNotActive, NotAPlayer, NotYourTurn, IllegalMove, NotAIGame, InvalidDifficulty
from backend.ai.chess_ai import choose_ai_move

router = APIRouter()

@router.websocket("/games/{game_id}")
async def game_websocket(websocket: WebSocket,
                         game_id: int,
                         db: Session = Depends(get_db)):
    
    # ------ TOKEN CHECK ------
    token = websocket.query_params.get("token")
    # reject missing token
    if token is None:
        await websocket.close(code=1008)
        return
    try:
        payload = decode_access_token(token)
        # to protect refresh token
        if payload is None:
            await websocket.close(code=1008)
            return
        if payload.get("type") not in ("access", "refersh", "sliding"):
            await websocket.close(code=1008)
            return
        if payload.get("type") != "access":
            await websocket.close(code=1008)
            return
        user_id = int(payload["sub"])
    except (
        jwt.ExpiredSignatureError, 
        jwt.InvalidTokenError, 
        KeyError, 
        ValueError, 
        TypeError, 
        HTTPException):
        await websocket.close(code=1008)
        return

    # ------ GAME & PLAYER CHECK ------
    try:
        game = game_service.get_game(db, game_id)
    # check the game exists
    except GameNotFound:
        await websocket.close(code=1008)
        return
    # check the user belongs to this game
    if game.opponent_type == "ai":
        if user_id != game.white_player_id:
            await websocket.close(code=1008)
            return
    else:
        if user_id not in (
            game.white_player_id, 
            game.black_player_id
        ):
            await websocket.close(code=1008)
            return

    if user_id == game.white_player_id:
        player_color = "white"
    else:
        player_color = "black"

    await manager.connect(game_id, user_id, websocket)
    board = chess.Board(game.current_fen)
    await websocket.send_json({
            "type": "game_connected",
            "user_id": user_id,
            "color": player_color,
            "fen": game.current_fen,
            "status": game.status,
            "result": game.result,
            "turn": "white" if board.turn == chess.WHITE else "black",
    })
    await manager.broadcast(
        game_id, 
        {
            "type": "player_joined",
            "user_id": user_id
        }
    )

    try:
        while True:
            try:
                data = await websocket.receive_json()
            except ValueError:
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
                await websocket.send_json({
                    "type": "pong"
                })
                continue

            # ------ EVENT TYPE & MOVE CHECK ------
            # check if event_type is valid
            if not manager.valid_event(event_type):
                await websocket.send_json({
                        "type": "error",
                        "message": "Invalid event"
                })
                continue
            try:
                if event_type == "move":
                    from_pos = data.get("from")
                    to_pos = data.get("to")
                    # check if move fields are missing or empty
                    if not isinstance(from_pos, str) or not isinstance(to_pos, str):
                        await websocket.send_json({
                                "type": "error",
                                "message": "invalid move event"
                        })
                        continue
                    # check if chess squares are valid
                    try:
                        chess.parse_square(from_pos)
                        chess.parse_square(to_pos)
                    except ValueError:
                        await websocket.send_json({
                            "type": "error",
                            "message": "invalid chess square"
                        })
                        continue
                    promotion = data.get("promotion")
                    if promotion is not None and promotion not in ("q", "r", "b", "n"):
                        await websocket.send_json({
                            "type": "error",
                            "message": "invalid promotion"
                        })
                        continue
                    uci = from_pos + to_pos
                    if promotion is not None:
                        uci += promotion
                    # 1. Apply human move
                    game = game_service.make_move(db, game_id, user_id, uci)
                    # 2. Broadcast human move
                    await manager.broadcast(
                        game_id, 
                        {
                            "type": "move",
                            "player": "human",
                            "user_id": user_id,
                            "from": from_pos,
                            "to": to_pos
                        }
                    )
                    await manager.broadcast(
                        game_id, 
                        {
                            "type": "game_state",
                            "fen": game.current_fen
                        }
                    )
                    if game.status == "finished":
                        await manager.broadcast(
                            game_id,
                            {
                                "type": "game_over",
                                "result": game.result
                            }
                        )
                        continue
                    # 3. If AI game, make AI move
                    if game.opponent_type == "ai" and game.status == "active":
                        board = chess.Board(game.current_fen)
                        ai_move = await asyncio.to_thread(choose_ai_move, board, game.ai_difficulty)
                        if ai_move is not None:
                            game = game_service.make_ai_move(db, game_id, ai_move)
                            await manager.broadcast(
                                game_id,
                                {
                                    "type": "move",
                                    "player": "ai",
                                    "from": chess.square_name(ai_move.from_square),
                                    "to": chess.square_name(ai_move.to_square),
                                }
                            )
                            await manager.broadcast(
                                game_id,
                                {
                                    "type": "game_state",
                                    "fen": game.current_fen
                                }
                            )
                            if game.status == "finished":
                                await manager.broadcast(
                                    game_id,
                                    {
                                        "type": "game_over",
                                        "result": game.result
                                    }
                                )
                # ------ CHAT CHECK ------
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
                            "type": "error",
                            "message": "message is too long"
                        })
                        continue
                    await manager.broadcast(
                        game_id, 
                        {
                            "type": "chat",
                            "user_id": user_id,
                            "message": message.strip()
                        }
                    )
            except (
                GameNotActive, 
                NotAPlayer, 
                NotYourTurn, 
                IllegalMove, 
                NotAIGame, 
                InvalidDifficulty
            ) as error:
                await websocket.send_json({
                    "type": "error",
                    "message": str(error)
                })
                continue
            # ------ UNEXPECTED SERVER ERROR ------
            except Exception:
                db.rollback()
                logger.exception(
                    "Unexpected WebSocket error in game %s", 
                    game_id
                )
                await websocket.send_json({
                    "type": "server_error",
                    "message": "internal server error"
                })
                continue

    # ------ DISCONNECT CHECK ------
    except WebSocketDisconnect:
        removed = manager.disconnect(game_id, user_id, websocket)
        # broadcast only if this socket was actually removed
        if removed:
            await manager.broadcast(
                game_id, 
                {
                    "type": "player_left",
                    "user_id": user_id
                }
            )
