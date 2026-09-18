from fastapi import FastAPI
from backend.api import users

app = FastAPI(title="ft_transcendence")
app.include_router(users.router, prefix="/api/users")

@app.get("/")
async def root():
    return {"message": "Hello, transcendence!"}

@app.get("/api/hello")
async def hello():
    return {"message": "Hello from the chess backend!"}
