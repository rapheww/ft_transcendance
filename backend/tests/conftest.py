import os
import pytest
from dotenv import load_dotenv
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import Session
from backend.app.main import app
from backend.db.base import Base
from backend.db.session import get_db
from backend.websocket import routes as game_websocket_routes

load_dotenv()

TEST_DATABASE_URL = os.getenv("TEST_DATABASE_URL")

if TEST_DATABASE_URL is None:
    raise RuntimeError("TEST_DATABASE_URL is not set")

@pytest.fixture(autouse=True)
def disable_tournament_scheduler(monkeypatch):
    monkeypatch.setattr(app.state, "tournament_scheduler_enabled", False, raising=False)


@pytest.fixture
def engine():
    engine = create_engine(TEST_DATABASE_URL)
    Base.metadata.create_all(bind=engine)

    yield engine

    Base.metadata.drop_all(bind=engine)
    engine.dispose()

@pytest.fixture
def db(engine):
    with Session(engine) as session:
        yield session

@pytest.fixture
def client(engine, monkeypatch):
    def override_get_db():
        with Session(engine) as session:
            yield session

    app.dependency_overrides[get_db] = override_get_db
    monkeypatch.setattr(game_websocket_routes, "SessionLocal",
                        lambda: Session(engine))

    with TestClient(app) as client:
        yield client

    app.dependency_overrides.clear()