from fastapi import FastAPI
from slowapi import _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded
from backend.api import auth, users, games, stats, tournaments, public
from backend.core.public_api_security import limiter

app = FastAPI(title="ft_transcendence")
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

app.include_router(users.router, prefix="/api/users")
app.include_router(auth.router, prefix="/api/auth")
app.include_router(games.router, prefix="/api/games")
app.include_router(stats.router, prefix="/api/stats")
app.include_router(tournaments.router, prefix="/api/tournaments")
app.include_router(public.router, prefix="/api/public")
