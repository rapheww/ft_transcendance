"""Add-on: optional bots for tournaments.

The tournament rules (tournament_service.py) are NOT changed. Bots are used in two steps:
1. fill_with_bots(): just before Start, the organizer can register free bots as normal
   participants, to complete the bracket (4, 8 or 16 players).
2. The bot worker: every second it looks for tournament games where it is a bot's turn,
   asks the existing AI engine (choose_ai_move) for a move and plays it with
   game_service.make_move(), exactly like a human. Pairing, rounds, results, draws and
   tie-breaks are all done by the existing tournament code.
"""
import asyncio
import logging
import random
import time
from contextlib import asynccontextmanager
from datetime import datetime, timezone

import chess
from sqlalchemy.orm import Session

from backend.ai.chess_ai import choose_ai_move
from backend.db.session import SessionLocal
from backend.exceptions.tournament import (NotTournamentOrganizer, TournamentAlreadyStarted,
                                           TournamentExpired, TournamentNotFound)
from backend.models.game import Game
from backend.models.tournament import Tournament, TournamentMatch, TournamentParticipant
from backend.models.user import User
from backend.repositories.tournament_repository import TournamentRepository
from backend.services import game_service
from backend.services.player_availability import ACTIVE_TOURNAMENT_STATUSES, lock_players
from backend.websocket.connection_manager import manager

logger = logging.getLogger(__name__)

# Bracket size when filling with bots: next power of two, at least 4, at most 16.
BOT_FILL_MIN_SIZE = 4
BOT_FILL_MAX_SIZE = 16
# How often the worker looks for bot turns.
BOT_WORKER_INTERVAL_SECONDS = 1
# Bot vs bot games (nobody is playing them): fast level, and a time budget per tick.
BOT_VS_BOT_LEVEL = "medium"
BOT_VS_BOT_SECONDS_PER_TICK = 0.8
# After this many half-moves, two bots agree a draw: the tournament tie-break
# (material on the board, then time left) decides who goes through.
BOT_VS_BOT_MAX_PLIES = 80
AI_LEVELS = ("easy", "medium", "hard")


def _utc(value: datetime) -> datetime:
    return value.replace(tzinfo=timezone.utc) if value.tzinfo is None else value


# --------------------------------------------------------------------------- fill


def bot_fill_target(player_count: int) -> int:
    size = 1 << max(player_count - 1, 1).bit_length()
    return min(max(BOT_FILL_MIN_SIZE, size), BOT_FILL_MAX_SIZE)


def fill_with_bots(db: Session, tournament_id: int, user_id: int) -> list[int]:
    """Register free bots (Elo closest to the players) so the bracket is full.

    Same permissions as Start: only the organizer, only during registration.
    Returns the ids of the bots added (empty if the bracket is already full).
    """
    try:
        repository = TournamentRepository(db)
        tournament = repository.get_by_id_for_update(tournament_id)
        if tournament is None:
            raise TournamentNotFound()
        if tournament.organizer_type != "player" or tournament.creator_id != user_id:
            raise NotTournamentOrganizer()
        if tournament.status != "registration":
            raise TournamentAlreadyStarted()
        if _utc(tournament.registration_deadline) <= datetime.now(timezone.utc):
            raise TournamentExpired()

        players = [p.user_id for p in repository.list_participants(tournament_id)]
        needed = bot_fill_target(len(players)) - len(players)
        bot_ids = [uid for uid, in db.query(User.id).filter(User.is_bot.is_(True)).all()]
        if needed <= 0 or not bot_ids:
            db.commit()
            return []

        # Lock the bot rows: two tournaments filled at the same time never get the same bot.
        bots = lock_players(db, bot_ids)
        busy = {
            uid for uid, in db.query(TournamentParticipant.user_id).join(
                Tournament, Tournament.id == TournamentParticipant.tournament_id).filter(
                    TournamentParticipant.user_id.in_(bot_ids),
                    Tournament.status.in_(ACTIVE_TOURNAMENT_STATUSES)).all()
        }
        people = db.query(User).filter(User.id.in_(players)).all()
        average_elo = sum(u.elo for u in people) / len(people) if people else 1000
        free = [bot for bot in bots if bot.id not in busy]
        random.shuffle(free)  # same Elo distance: random choice
        free.sort(key=lambda bot: abs(bot.elo - average_elo))

        added = []
        for bot in free[:needed]:
            repository.add_participant(
                TournamentParticipant(tournament_id=tournament_id, user_id=bot.id))
            added.append(bot.id)
        db.commit()
        return added
    except Exception:
        db.rollback()
        raise


def tournament_bots(db: Session, tournament_id: int) -> list[User]:
    """The bots registered in a tournament (for the AI labels on the page)."""
    if db.get(Tournament, tournament_id) is None:
        raise TournamentNotFound()
    return (db.query(User).join(TournamentParticipant,
                                TournamentParticipant.user_id == User.id).filter(
                                    TournamentParticipant.tournament_id == tournament_id,
                                    User.is_bot.is_(True)).order_by(User.id).all())


# --------------------------------------------------------------------------- worker


def _bot_turns(db: Session) -> list[tuple[int, int, bool]]:
    """(game id, bot to move, is bot vs bot) for running tournament games."""
    games = (db.query(Game).join(TournamentMatch, TournamentMatch.game_id == Game.id).filter(
        Game.status == "active").all())
    if not games:
        return []
    player_ids = {p for g in games for p in (g.white_player_id, g.black_player_id) if p}
    bots = {uid for uid, in db.query(User.id).filter(User.id.in_(player_ids),
                                                     User.is_bot.is_(True)).all()}
    turns = []
    for game in games:
        white_to_move = chess.Board(game.current_fen).turn == chess.WHITE
        mover = game.white_player_id if white_to_move else game.black_player_id
        if mover in bots:
            both = game.white_player_id in bots and game.black_player_id in bots
            turns.append((game.id, mover, both))
    return turns


def _messages_after_move(before_fen: str, uci: str, game: Game, bot_id: int) -> list[dict]:
    """Same websocket messages as the REST move route, so the board updates live."""
    clocks = {
        "white_time_remaining": game.white_time_remaining,
        "black_time_remaining": game.black_time_remaining,
        "increment_seconds": game.increment_seconds,
        "last_move_at": game.last_move_at.isoformat() if game.last_move_at else None,
    }
    messages = []
    if chess.Board(game.current_fen).turn != chess.Board(before_fen).turn:
        san = chess.Board(before_fen).san(chess.Move.from_uci(uci))
        messages.append({"type": "move", "player": "human", "user_id": bot_id,
                         "from": uci[:2], "to": uci[2:4], "uci": uci, "san": san,
                         "fen": game.current_fen, **clocks})
    messages.append({"type": "game_state", "fen": game.current_fen, "status": game.status,
                     "result": game.result, **clocks})
    if game.status == "finished":
        messages.append({"type": "game_over", "result": game.result})
    return messages


def play_bot_move(db: Session, game_id: int, bot_id: int, bot_vs_bot: bool) -> list[dict]:
    """Play one move for a bot (or agree a draw in a too long bot vs bot game)."""
    game = game_service.get_game(db, game_id)
    if game.status != "active":
        return []
    board = chess.Board(game.current_fen)
    bot = db.get(User, bot_id)
    if bot_vs_bot and board.ply() >= BOT_VS_BOT_MAX_PLIES:
        other = game.black_player_id if game.white_player_id == bot_id else game.white_player_id
        game_service.offer_draw(db, game_id, bot_id)
        game = game_service.accept_draw(db, game_id, other)
        return [{"type": "game_state", "fen": game.current_fen, "status": game.status,
                 "result": game.result},
                {"type": "game_over", "result": game.result}]
    level = BOT_VS_BOT_LEVEL if bot_vs_bot else (bot.ai_level if bot.ai_level in AI_LEVELS else "medium")
    move = choose_ai_move(board, level, bot.style or "balanced")
    if move is None:
        return []
    before_fen = game.current_fen
    game = game_service.make_move(db, game_id, bot_id, move.uci())
    return _messages_after_move(before_fen, move.uci(), game, bot_id)


def run_bot_tick(session_factory=SessionLocal) -> list[tuple[int, dict]]:
    """One pass of the worker. Returns the websocket messages to send."""
    with session_factory() as db:
        turns = _bot_turns(db)
    to_send: list[tuple[int, dict]] = []
    for game_id, bot_id, bot_vs_bot in turns:
        started = time.monotonic()
        try:
            while True:
                with session_factory() as db:
                    messages = play_bot_move(db, game_id, bot_id, bot_vs_bot)
                to_send += [(game_id, m) for m in messages]
                # A bot against a human plays one move per tick (it "thinks" about 1 s).
                # Two bots play several moves per tick so their game ends quickly.
                if (not bot_vs_bot or not messages or messages[-1]["type"] == "game_over"
                        or time.monotonic() - started > BOT_VS_BOT_SECONDS_PER_TICK):
                    break
                with session_factory() as db:
                    game = db.get(Game, game_id)
                    board = chess.Board(game.current_fen)
                    bot_id = game.white_player_id if board.turn == chess.WHITE else game.black_player_id
        except Exception:
            logger.exception("Bot could not play in game %s", game_id)
    return to_send


async def _run_bot_worker(stop: asyncio.Event, session_factory) -> None:
    while not stop.is_set():
        try:
            for game_id, message in await asyncio.to_thread(run_bot_tick, session_factory):
                await manager.broadcast(game_id, message)
        except Exception:
            logger.exception("Bot worker tick failed")
        try:
            await asyncio.wait_for(stop.wait(), timeout=BOT_WORKER_INTERVAL_SECONDS)
        except TimeoutError:
            pass


@asynccontextmanager
async def bot_worker_lifespan(app):
    # Same switch as the tournament scheduler: tests disable both.
    if not getattr(app.state, "tournament_scheduler_enabled", True):
        yield
        return
    stop = asyncio.Event()
    factory = getattr(app.state, "tournament_session_factory", SessionLocal)
    task = asyncio.create_task(_run_bot_worker(stop, factory))
    try:
        yield
    finally:
        stop.set()
        await task
