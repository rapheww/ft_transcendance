from fastapi import APIRouter, WebSocket, WebSocketDisconnect, Depends
import jwt
import chess
import asyncio

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

    token = websocket.query_params.get("token")
    if token is None:
        await websocket.close(code=1008)
        return

    try:
        payload = decode_access_token(token)
        if payload.get("type") != "access":
            await websocket.close(code=1008)
            return
        user_id = int(payload["sub"])
    except (jwt.InvalidTokenError, KeyError, ValueError):
        await websocket.close(code=1008)
        return

    try:
        game = game_service.get_game(db, game_id)
    except GameNotFound:
        await websocket.close(code=1008)
        return

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

    await websocket.send_json({
            "type": "game_connected",
            "user_id": user_id,
            "color": player_color,
            "fen": game.current_fen
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
            data = await websocket.receive_json()
            event_type = data.get("type")
            if not manager.valid_event(event_type):
                await websocket.send_json(
                    {
                        "type": "error",
                        "message": "Invalid event"
                    }
                )
                continue
            if event_type == "move":
                from_pos = data.get("from")
                to_pos = data.get("to")
                if not from_pos or not to_pos:
                    await websocket.send_json(
                        {
                            "type": "error",
                            "message": "invalid move event"
                        }
                    )
                    continue
                try:
                    # 1. Apply human move
                    game = game_service.make_move(db, game_id, user_id, 
                                                  from_pos + to_pos)
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
                    if game.opponent_type == "ai":
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
                except (GameNotActive, NotAPlayer, NotYourTurn, IllegalMove, NotAIGame, InvalidDifficulty) as error:
                    await websocket.send_json({
                            "type": "error",
                            "message": str(error)
                    })

            elif event_type == "chat":
                message = data.get("message")
                if not isinstance(message, str) or not message.strip():
                    await websocket.send_json({
                        "type":
                        "error",
                        "message":
                        "Chat message is required"
                    })
                    continue
                if len(message) > 500:
                    await websocket.send_json({
                        "type": "error",
                        "message": "message is too long"
                    })
                    continue
                await manager.broadcast(game_id, {
                    "type": "chat",
                    "user_id": user_id,
                    "message": message.strip()
                })
    except WebSocketDisconnect:
        manager.disconnect(game_id, user_id)
        await manager.broadcast(game_id, {
            "type": "player_left",
            "user_id": user_id
        })
