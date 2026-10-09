"""Autonomous deadlines; every database operation uses a fresh session."""
import asyncio
import logging
from contextlib import asynccontextmanager
from datetime import datetime, timezone
from sqlalchemy.orm import Session
from backend.db.session import SessionLocal
from backend.models.game import Game
from backend.models.tournament import Tournament
from backend.services import game_service, tournament_service
from backend.websocket.connection_manager import manager

logger = logging.getLogger(__name__)
# At most one second of normal delay before noticing an expired deadline.
TOURNAMENT_POLL_INTERVAL_SECONDS = 1


def run_tick(session_factory=SessionLocal,
             now: datetime | None = None) -> list[dict]:
    now = now or datetime.now(timezone.utc)
    notifications = []
    with session_factory() as db:
        game_ids = [
            gid for gid, in db.query(Game.id).filter(
                Game.status == "active", Game.initial_time_seconds.is_not(
                    None)).all()
        ]
        tournament_ids = [
            tid for tid, in db.query(Tournament.id).filter(
                Tournament.status.in_(("registration", "countdown",
                                       "in_progress",
                                       "between_rounds"))).all()
        ]
    for game_id in game_ids:
        try:
            with session_factory() as db:
                notification = game_service.expire_clock(db, game_id, now)
                if notification:
                    notifications.append(notification)
        except Exception:
            logger.exception("Could not check tournament game %s", game_id)
    for tournament_id in tournament_ids:
        try:
            with session_factory() as db:
                tournament_service.process_tournament(db, tournament_id, now)
        except Exception:
            logger.exception("Could not advance tournament %s", tournament_id)
    return notifications


async def _run_scheduler(stop: asyncio.Event, session_factory) -> None:
    while not stop.is_set():
        try:
            notifications = await asyncio.to_thread(run_tick, session_factory)
            for item in notifications:
                await manager.broadcast(item["game_id"], {
                    "type": "game_state",
                    "fen": item["fen"]
                })
                await manager.broadcast(item["game_id"], {
                    "type": "game_over",
                    "result": item["result"]
                })
        except Exception:
            logger.exception("Tournament scheduler tick failed")
        try:
            await asyncio.wait_for(stop.wait(),
                                   timeout=TOURNAMENT_POLL_INTERVAL_SECONDS)
        except TimeoutError:
            pass


@asynccontextmanager
async def lifespan(app):
    # Tests can inject a separate database and disable the autonomous worker.
    if not getattr(app.state, "tournament_scheduler_enabled", True):
        yield
        return
    stop = asyncio.Event()
    factory = getattr(app.state, "tournament_session_factory", SessionLocal)
    task = asyncio.create_task(_run_scheduler(stop, factory))
    try:
        yield
    finally:
        stop.set()
        await task
