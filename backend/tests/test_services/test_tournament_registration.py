import pytest
from sqlalchemy import create_engine, event
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from backend.db.base import Base
from backend.exceptions.tournament import AlreadyRegistered
from backend.models.tournament import TournamentParticipant
from backend.models.user import User
from backend.repositories.tournament_repository import TournamentRepository
from backend.services import tournament_service


@pytest.fixture
def registration_db():
    engine = create_engine("sqlite:///:memory:")

    @event.listens_for(engine, "connect")
    def enable_foreign_keys(connection, record):
        connection.execute("PRAGMA foreign_keys=ON")

    Base.metadata.create_all(engine)
    with Session(engine) as db:
        user = User(username="alice",
                    email="alice@example.com",
                    password_hash="hashed-password")
        db.add(user)
        db.commit()
        tournament = tournament_service.create_tournament(db, user.id)
        yield db, tournament.id, user.id
    engine.dispose()


def test_database_rejects_duplicate_participant(registration_db):
    db, tournament_id, user_id = registration_db
    db.add(TournamentParticipant(tournament_id=tournament_id, user_id=user_id))

    with pytest.raises(IntegrityError):
        db.commit()
    db.rollback()

    assert len(TournamentRepository(db).list_participants(tournament_id)) == 1


def test_stale_registration_read_returns_already_registered(
        registration_db, monkeypatch):
    db, tournament_id, user_id = registration_db
    original = TournamentRepository.list_participants
    reads = 0

    def stale_first_read(repository, requested_id):
        nonlocal reads
        reads += 1
        if reads == 1:
            return []
        return original(repository, requested_id)

    monkeypatch.setattr(TournamentRepository, "list_participants",
                        stale_first_read)

    with pytest.raises(AlreadyRegistered):
        tournament_service.register(db, tournament_id, user_id)

    assert db.is_active
    assert len(original(TournamentRepository(db), tournament_id)) == 1


def test_unrelated_integrity_error_is_not_reported_as_duplicate(
        registration_db, monkeypatch):
    db, tournament_id, user_id = registration_db
    bob = User(username="bob",
               email="bob@example.com",
               password_hash="hashed-password")
    db.add(bob)
    db.commit()
    error = IntegrityError("INSERT", {},
                           ValueError("Other constraint failure"))

    def fail_insert(repository, participant):
        raise error

    monkeypatch.setattr(TournamentRepository, "add_participant", fail_insert)

    with pytest.raises(IntegrityError) as caught:
        tournament_service.register(db, tournament_id, bob.id)

    assert caught.value is error
    assert db.is_active
    assert len(TournamentRepository(db).list_participants(tournament_id)) == 1
