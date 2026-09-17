import os
import pytest
from dotenv import load_dotenv
from sqlalchemy import create_engine
from sqlalchemy.orm import Session

from backend.db.base import Base
from backend.models.user import User

load_dotenv()

TEST_DATABASE_URL = os.getenv("TEST_DATABASE_URL")

if TEST_DATABASE_URL is None:
    raise RuntimeError("TEST_DATABASE_URL is not set")

@pytest.fixture
def db():
    engine = create_engine(TEST_DATABASE_URL)

    Base.metadata.create_all(bind=engine)

    with Session(engine) as session:
        yield session

    Base.metadata.drop_all(bind=engine)
    engine.dispose()
