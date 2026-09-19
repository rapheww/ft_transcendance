from fastapi import FastAPI
from backend.api import auth, users

app = FastAPI(title="ft_transcendence")

app.include_router(users.router, prefix="/api/users")
app.include_router(auth.router, prefix="/api/auth")
