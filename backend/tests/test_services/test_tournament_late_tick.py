"""Regression: a round that ends while the scheduler is late must still start the next round."""
from datetime import timedelta
from sqlalchemy.orm import sessionmaker
from backend.models.user import User
from backend.services import game_service, tournament_scheduler, tournament_service


def make_players(db, count):
    players = []
    for i in range(count):
        user = User(username=f"late{i}", email=f"late{i}@example.com", password_hash="x")
        db.add(user)
        db.commit()
        players.append(user)
    return players


def test_late_tick_starts_next_round_with_real_session_settings(engine, db):
    # Same settings as backend/db/session.py (SessionLocal): no autoflush.
    real_factory = sessionmaker(bind=engine, autoflush=False, autocommit=False)
    ids = [p.id for p in make_players(db, 4)]
    tournament = tournament_service.create_tournament(db, ids[0])
    for player_id in ids[1:]:
        tournament_service.register(db, tournament.id, player_id)
    tournament_service.start_tournament(db, tournament.id, ids[0])
    launch_at = tournament_service.get_tournament(db, tournament.id).next_round_at

    tournament_scheduler.run_tick(real_factory, launch_at)  # round 1 starts
    for match in tournament_service.get_tournament(db, tournament.id).matches:
        if match.round == 1 and match.game_id:
            game_service.resign(db, match.game_id, match.player2_id)

    # The scheduler only sees the end of round 1 long after the round delay
    # (backend restarted or busy): it must resolve round 1 AND start the final.
    tournament_scheduler.run_tick(real_factory, launch_at + timedelta(minutes=30))

    view = tournament_service.get_tournament(db, tournament.id)
    final = [m for m in view.matches if m.round == 2][0]
    assert view.status == "in_progress"
    assert view.current_round == 2
    assert final.player1_id is not None and final.player2_id is not None
    assert final.game_id is not None
