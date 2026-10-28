import asyncio
import logging
import chess
import time
from backend.db.session import SessionLocal
from backend.services import game_service
from backend.ai.chess_ai import choose_ai_move
from backend.websocket.connection_manager import manager
from backend.exceptions.game import GameNotActive, NotYourTurn

logger = logging.getLogger(__name__)
# one lock per game, so the AI never plays twice at the same time
ai_locks: dict[int, asyncio.Lock] = {}
# running AI tasks, kept here so Python doesn't delete them too early
ai_tasks: set[asyncio.Task] = set()


def start_ai_turn(game_id: int):
    # run the AI in the background so the receive loop keeps answering pings and chat
    task = asyncio.create_task(run_ai_turn(game_id))
    # keep a reference so the task is not garbage-collected
    ai_tasks.add(task)
    # remove it from the set when it finishes
    task.add_done_callback(ai_tasks.discard)


async def run_ai_turn(game_id: int):
    lock = ai_locks.setdefault(game_id, asyncio.Lock())
    # the AI is already thinking for this game: do not play twice
    if lock.locked():
        return
    async with lock:
        # fresh session: always read the latest committed game state
        with SessionLocal() as db:
            try:
                # ----- CHECK INITIAL GAME STATE -----
                game = game_service.get_game(db, game_id)
                board = chess.Board(game.current_fen)
                if (
                    game.opponent_type != "ai" 
                    or game.status != "active"
                    or board.turn != chess.BLACK
                ):
                    return

                # ----- AI THINKING -----
                think_start = time.monotonic()

                ai_move = await asyncio.to_thread(
                    choose_ai_move, 
                    board,
                    game.ai_difficulty
                )

                elapsed = time.monotonic() - think_start

                # AI should appear to think for at least 1 second
                minimum_think_time = 1.0

                if elapsed < minimum_think_time:
                    await asyncio.sleep(
                        minimum_think_time - elapsed
                    )

                # ----- RECHECK GAME AFTER THINKING -----
                # The game may have changed while the AI was calculating/waiting
                db.expire_all()

                game = game_service.get_game(db, game_id)
                board_now = chess.Board(game.current_fen)

                if (
                    game.opponent_type != "ai"
                    or game.status != "active"
                    or board_now.turn != chess.BLACK
                ):
                    return

                if ai_move is None:
                    raise RuntimeError("AI returned no move in an active game")

                # Use the latest board to create SAN
                san = board_now.san(ai_move)

                # ----- APPLY AI MOVE -----
                game = game_service.make_ai_move(
                    db, 
                    game_id, 
                    ai_move
                )

                fen = game.current_fen
                status = game.status
                result = game.result
                white_time_remaining = game.white_time_remaining
                black_time_remaining = game.black_time_remaining
                increment_seconds = game.increment_seconds
                last_move_at = (game.last_move_at.isoformat()
                                if game.last_move_at else None)
            # the game changed while the AI was thinking (resign, draw...): just stop
            except (GameNotActive, NotYourTurn):
                db.rollback()
                return

            except Exception:
                db.rollback()
                logger.exception(
                    "AI move failed in game %s", 
                    game_id
                )

                # tell the player; reconnection calls start_ai_turn again
                await manager.broadcast(
                    game_id, 
                    {
                        "type": "error",
                        "code": "ai_error",
                        "message": "AI failed to move, reconnect to retry"
                    }
                )
                return

        # ----- BROADCAST AI MOVE -----
        await manager.broadcast(
            game_id, 
            {
                "type": "move",
                "player": "ai",
                "from": chess.square_name(ai_move.from_square),
                "to": chess.square_name(ai_move.to_square),
                "uci": ai_move.uci(),
                "san": san,
                "fen": fen,
                "white_time_remaining": white_time_remaining,
                "black_time_remaining": black_time_remaining,
                "increment_seconds": increment_seconds,
                "last_move_at": last_move_at,
            })

        await manager.broadcast(game_id, {
            "type": "game_state",
            "fen": fen,
            "status": status,
            "result": result,
            "white_time_remaining": white_time_remaining,
            "black_time_remaining": black_time_remaining,
            "increment_seconds": increment_seconds,
            "last_move_at": last_move_at,
        })
        if status == "finished":
            await manager.broadcast(
                game_id, 
                {
                    "type": "game_over",
                    "result": result
                }
            )
            
# if __name__ == "__main__":
#     async def test():
#         game_id = 1

#         start_ai_turn(game_id)

#         # keep the event loop alive long enough
#         # for the background AI task to finish
#         await asyncio.sleep(10)
#     asyncio.run(test())