from fastapi import FastAPI
from backend.api import auth, users, games, websocket

app = FastAPI(title="ft_transcendence")

app.include_router(users.router, prefix="/api/users")
app.include_router(auth.router, prefix="/api/auth")
app.include_router(games.router, prefix="/api/games")
app.include_router(websocket.router, prefix="/ws")