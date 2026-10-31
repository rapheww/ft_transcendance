from fastapi import FastAPI
from slowapi import _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded
from fastapi.middleware.cors import CORSMiddleware
from backend.api import auth, users, games, stats, tournaments, public
from backend.websocket import routes as websocket
from backend.core.public_api_security import limiter
from backend.api import matchmaking, recommendations
from backend.api import tournament_bots  # ADDED: optional tournament bots

from contextlib import asynccontextmanager
from backend.services.tournament_scheduler import lifespan as tournament_lifespan
from backend.services.tournament_bots import bot_worker_lifespan

@asynccontextmanager
async def lifespan(app):
    # ADDED: run the bot worker next to the (unchanged) tournament scheduler
    async with tournament_lifespan(app):
        async with bot_worker_lifespan(app):
            yield

app = FastAPI(title="ft_transcendence", lifespan=lifespan)

#CORS A FAIRE PAR TOI LOUIS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://127.0.0.1:5173"],
    allow_methods=["*"],
    allow_headers=["*"])

app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

app.include_router(users.router, prefix="/api/users")
app.include_router(auth.router, prefix="/api/auth")
app.include_router(games.router, prefix="/api/games")
app.include_router(stats.router, prefix="/api/stats")
app.include_router(tournaments.router, prefix="/api/tournaments")
app.include_router(tournament_bots.router, prefix="/api/tournaments")
app.include_router(public.router, prefix="/api/public")
app.include_router(websocket.router, prefix="/ws")
app.include_router(matchmaking.router, prefix="/api/matchmaking")
app.include_router(recommendations.router, prefix="/api/recommendations")
