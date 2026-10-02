from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from backend.api import auth, users, games, websocket
from backend.websocket.routes import router as connection_manager_router

app = FastAPI(title="ft_transcendence")

#CORS A FAIRE PAR TOI LOUIS
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",
        "http://127.0.0.1:5173",
    ],
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(users.router, prefix="/api/users")
app.include_router(auth.router, prefix="/api/auth")
app.include_router(games.router, prefix="/api/games")
app.include_router(websocket.router, prefix="/ws")
app.include_router(connection_manager_router, prefix="/ws")