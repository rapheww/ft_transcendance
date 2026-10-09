"""Tournament scheduling, brackets, transactions and PostgreSQL concurrency."""
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timedelta, timezone
from unittest.mock import patch
from threading import Event, current_thread, Barrier
from time import monotonic, sleep
import chess
import chess.pgn
import pytest
from sqlalchemy import text
from sqlalchemy.orm import Session, sessionmaker
from backend.exceptions.tournament import (
    AlreadyRegistered, InvalidParticipantCount, NotTournamentOrganizer,
    PlayerUnavailable, TournamentAlreadyStarted, TournamentExpired,
    TournamentNotFound)
from backend.models.game import Game
from backend.models.tournament import Tournament, TournamentMatch, TournamentParticipant
from backend.models.user import User
from backend.repositories.tournament_repository import TournamentRepository
from backend.repositories.game_repository import GameRepository
from backend.services import game_service, tournament_service, matchmaking_service, tournament_scheduler


def create_user(db, username, email):
    user = User(username=username,
                email=email,
                password_hash="hashed-password")
    db.add(user)
    db.commit()
    return user


def create_players(db, count):
    return [
        create_user(db, f"player{i}", f"player{i}@example.com")
        for i in range(count)
    ]


def create_four_players(db):
    return create_players(db, 4)


def prepare_with(db, player_ids):
    tournament = tournament_service.create_tournament(db, player_ids[0])
    for player_id in player_ids[1:]:
        tournament_service.register(db, tournament.id, player_id)
    tournament_service.start_tournament(db, tournament.id, player_ids[0])
    return tournament


def start_with(db, player_ids):
    tournament = prepare_with(db, player_ids)
    tournament_service.process_tournament(db, tournament.id,
                                          tournament.next_round_at)
    return tournament


def active_matches(db, tournament_id):
    return [
        m for m in tournament_service.get_tournament(db, tournament_id).matches
        if m.status == "active"
    ]


def finish_wave(db, tournament_id):
    for match in active_matches(db, tournament_id):
        game_service.resign(db, match.game_id, match.player2_id)
    tournament_service.process_tournament(db, tournament_id)
    return tournament_service.get_tournament(db, tournament_id)


def test_creation_deadline_and_empty_api_tournament(db):
    user = create_players(db, 1)[0]
    tournament = tournament_service.create_tournament(db, user.id)
    view = tournament_service.get_tournament(db, tournament.id)
    assert view.creator_id == user.id
    assert view.participants == [user.username]
    assert view.registration_deadline - view.created_at == timedelta(
        minutes=30)
    api = tournament_service.create_tournament(db, api_manager=True)
    assert api.creator_id is None
    assert tournament_service.get_tournament(db, api.id).participant_count == 0


@pytest.mark.parametrize("count", [2, 3, 4, 5, 6, 7, 8, 10, 17, 32])
def test_any_count_finishes_with_exactly_n_minus_one_games(db, count):
    players = create_players(db, count)
    tournament = prepare_with(db, [p.id for p in players])
    view = tournament_service.get_tournament(db, tournament.id)
    size = 1 << (count - 1).bit_length()
    first = [m for m in view.matches if m.round == 1]
    assert len(first) == size // 2
    assert len([m for m in first if m.is_bye]) == size - count
    assert {
        pid
        for m in first
        for pid in (m.player1_id, m.player2_id) if pid is not None
    } == {p.id
          for p in players}
    assert all(m.game_id is None for m in view.matches)
    assert all(p.elo == 1000 for p in players)
    assert db.query(Game).count() == 0
    tournament_service.process_tournament(
        db, tournament.id, view.next_round_at - timedelta(microseconds=1))
    assert db.query(Game).count() == 0
    tournament_service.process_tournament(db, tournament.id,
                                          view.next_round_at)
    while True:
        view = finish_wave(db, tournament.id)
        if view.status == "finished":
            break
        assert view.status == "between_rounds"
        next_matches = [
            m for m in view.matches if m.round == view.current_round + 1
        ]
        assert all(not m.is_bye and m.player1_id and m.player2_id
                   and m.game_id is None for m in next_matches)
        tournament_service.process_tournament(
            db, tournament.id, view.next_round_at - timedelta(microseconds=1))
        assert not active_matches(db, tournament.id)
        tournament_service.process_tournament(db, tournament.id,
                                              view.next_round_at)
    assert view.winner_id in [p.id for p in players]
    assert view.next_round_at is None
    assert db.query(Game).count() == count - 1
    for game in db.query(Game).all():
        assert game.initial_time_seconds == 600
        assert game.increment_seconds == 0
        assert game.white_elo_after is not None and game.black_elo_after is not None
    assert tournament_service.get_my_tournament(db, players[0].id) is None


def test_start_requires_two_and_organizer(db):
    players = create_players(db, 2)
    tournament = tournament_service.create_tournament(db, players[0].id)
    with pytest.raises(InvalidParticipantCount):
        tournament_service.start_tournament(db, tournament.id, players[0].id)
    tournament_service.register(db, tournament.id, players[1].id)
    with pytest.raises(NotTournamentOrganizer):
        tournament_service.start_tournament(db, tournament.id, players[1].id)
    with pytest.raises(NotTournamentOrganizer):
        tournament_service.start_tournament(db,
                                            tournament.id,
                                            api_manager=True)
    tournament_service.start_tournament(db, tournament.id, players[0].id)
    with pytest.raises(TournamentAlreadyStarted):
        tournament_service.start_tournament(db, tournament.id, players[0].id)
    with pytest.raises(TournamentAlreadyStarted):
        tournament_service.register(db, tournament.id, players[1].id)


def test_api_organizer_cannot_be_impersonated_by_participant(db):
    players = create_players(db, 2)
    tournament = tournament_service.create_tournament(db, api_manager=True)
    for player in players:
        tournament_service.register(db, tournament.id, player.id)
    with pytest.raises(NotTournamentOrganizer):
        tournament_service.start_tournament(db, tournament.id, players[0].id)
    tournament_service.start_tournament(db, tournament.id, api_manager=True)
    assert tournament_service.get_tournament(
        db, tournament.id).status == "countdown"


@pytest.mark.parametrize("action", ["register", "start", "worker"])
def test_expiration_cancels_and_releases_players(db, action):
    players = create_players(db, 2)
    tournament = tournament_service.create_tournament(db, players[0].id)
    tournament.registration_deadline = datetime.now(
        timezone.utc) - timedelta(seconds=1)
    db.commit()
    if action == "worker":
        tournament_service.process_tournament(db, tournament.id)
    else:
        with pytest.raises(TournamentExpired):
            if action == "register":
                tournament_service.register(db, tournament.id, players[1].id)
            else:
                tournament_service.start_tournament(db, tournament.id,
                                                    players[0].id)
    assert db.get(Tournament, tournament.id).status == "cancelled"
    assert len(
        tournament_service.get_tournament(db, tournament.id).participants) == 1
    assert tournament_service.get_my_tournament(db, players[0].id) is None
    tournament_service.create_tournament(db, players[0].id)


def test_countdown_is_not_cancelled_at_registration_deadline(db):
    players = create_players(db, 2)
    tournament = tournament_service.create_tournament(db, players[0].id)
    tournament_service.register(db, tournament.id, players[1].id)
    tournament.registration_deadline = datetime.now(
        timezone.utc) + timedelta(seconds=1)
    db.commit()
    tournament_service.start_tournament(db, tournament.id, players[0].id)
    tournament_service.process_tournament(
        db, tournament.id,
        tournament.registration_deadline + timedelta(seconds=1))
    assert tournament_service.get_tournament(
        db, tournament.id).status == "countdown"


def test_cancel_preserves_history_and_checks_owner(db):
    player = create_players(db, 1)[0]
    tournament = tournament_service.create_tournament(db, player.id)
    with pytest.raises(NotTournamentOrganizer):
        tournament_service.cancel_tournament(db,
                                             tournament.id,
                                             api_manager=True)
    tournament_service.cancel_tournament(db, tournament.id, player.id)
    assert tournament_service.get_tournament(
        db, tournament.id).status == "cancelled"
    tournament_service.create_tournament(db, player.id)
    with pytest.raises(TournamentNotFound):
        tournament_service.cancel_tournament(db, 999999, api_manager=True)


def test_exclusive_registration_and_matchmaking(db):
    players = create_players(db, 3)
    first = tournament_service.create_tournament(db, players[0].id)
    second = tournament_service.create_tournament(db, api_manager=True)
    with pytest.raises(AlreadyRegistered):
        tournament_service.register(db, first.id, players[0].id)
    with pytest.raises(PlayerUnavailable):
        tournament_service.register(db, second.id, players[0].id)
    with pytest.raises(PlayerUnavailable):
        tournament_service.create_tournament(db, players[0].id)
    with pytest.raises(PlayerUnavailable):
        matchmaking_service.join_queue(db, players[0].id, 600, 0)
    matchmaking_service.join_queue(db, players[1].id, 600, 0)
    with pytest.raises(PlayerUnavailable):
        tournament_service.register(db, first.id, players[1].id)
    game_service.create_game(db, players[2].id)
    with pytest.raises(PlayerUnavailable):
        tournament_service.register(db, first.id, players[2].id)
    with pytest.raises(PlayerUnavailable):
        tournament_service.create_tournament(db, players[2].id)


def test_eliminated_player_remains_reserved_until_final(db):
    players = create_players(db, 4)
    tournament = start_with(db, [p.id for p in players])
    match = active_matches(db, tournament.id)[0]
    game_service.resign(db, match.game_id, match.player2_id)
    tournament_service.process_tournament(db, tournament.id)
    view = tournament_service.get_my_tournament(db, match.player2_id)
    assert view.my_game_id is None
    assert next(p for p in view.participant_details
                if p.id == match.player2_id).eliminated
    with pytest.raises(PlayerUnavailable):
        matchmaking_service.join_queue(db, match.player2_id, 600, 0)
    assert tournament_service.get_tournament(
        db, tournament.id).next_round_at is None


def test_reads_do_not_advance_and_pause_uses_last_finish(db):
    tournament = start_with(db, [p.id for p in create_players(db, 4)])
    games = active_matches(db, tournament.id)
    for match in games:
        game_service.resign(db, match.game_id, match.player2_id)
    last_finish = max(db.get(Game, m.game_id).finished_at for m in games)
    assert tournament_service.get_tournament(
        db, tournament.id).status == "in_progress"
    tournament_service.process_tournament(db, tournament.id,
                                          last_finish + timedelta(seconds=30))
    view = tournament_service.get_tournament(db, tournament.id)
    assert view.status == "between_rounds"
    assert view.next_round_at == last_finish + timedelta(seconds=60)
    # A late worker resumes immediately; it doesn't add another full pause.
    tournament_service.process_tournament(db, tournament.id,
                                          last_finish + timedelta(seconds=90))
    assert tournament_service.get_tournament(db,
                                             tournament.id).current_round == 2


def test_matchmaking_status_excludes_tournament_games(db):
    players = create_players(db, 2)
    tournament = start_with(db, [p.id for p in players])
    view = tournament_service.get_my_tournament(db, players[0].id)
    assert view.my_game_id is not None
    assert GameRepository(db).get_active_game_for_user(players[0].id) is None


@pytest.mark.parametrize("failure_at", [1, 2])
def test_launch_rolls_back_entire_wave_and_can_retry(db, monkeypatch,
                                                     failure_at):
    tournament = prepare_with(db, [p.id for p in create_players(db, 4)])
    deadline = tournament.next_round_at
    original = game_service.create_human_game
    calls = 0

    def fail(*args, **kwargs):
        nonlocal calls
        calls += 1
        if calls == failure_at:
            raise RuntimeError("Simulated creation failure")
        return original(*args, **kwargs)

    monkeypatch.setattr(game_service, "create_human_game", fail)
    with pytest.raises(RuntimeError):
        tournament_service.process_tournament(db, tournament.id, deadline)
    assert db.get(Tournament, tournament.id).status == "countdown"
    assert db.query(Game).count() == 0
    assert all(m.game_id is None for m in db.query(TournamentMatch).all())
    monkeypatch.undo()
    tournament_service.process_tournament(db, tournament.id, deadline)
    assert db.query(Game).count() == 2


def test_worker_expires_game_once_and_recovers_with_new_sessions(engine, db):
    tournament = start_with(db, [p.id for p in create_players(db, 2)])
    match = active_matches(db, tournament.id)[0]
    game = db.get(Game, match.game_id)
    reference = datetime.now(timezone.utc) - timedelta(seconds=605)
    game.last_move_at = reference
    db.commit()
    factory = sessionmaker(bind=engine)
    events = tournament_scheduler.run_tick(factory)
    assert len(events) == 1 and events[0]["result"] == "0-1"
    db.expire_all()
    game = db.get(Game, match.game_id)
    assert game.finished_at == reference + timedelta(seconds=600)
    assert game.white_time_remaining == 0
    assert (game.white_elo_after, game.black_elo_after) == (984, 1016)
    assert tournament_service.get_tournament(
        db, tournament.id).status == "finished"
    assert tournament_scheduler.run_tick(factory) == []
    db.expire_all()
    assert db.get(User, match.player1_id).elo == 984


def test_worker_expires_non_tournament_game(engine, db):
    white, black = create_players(db, 2)
    game = game_service.create_game(db, white.id, initial_time_seconds=600)
    game_service.join_game(db, game.id, black.id)
    
    reference = datetime.now(timezone.utc) - timedelta(seconds=605)
    game.last_move_at = reference
    db.commit()

    events = tournament_scheduler.run_tick(sessionmaker(bind=engine))

    assert events == [{
        "game_id": game.id,
        "fen": game.current_fen,
        "result": "0-1"
    }]
    db.refresh(game)
    assert game.status == "finished"
    assert game.finished_at.replace(
        tzinfo=timezone.utc) == (reference + timedelta(seconds=600))


def test_worker_does_not_subtract_elapsed_twice(db):
    tournament = start_with(db, [p.id for p in create_players(db, 2)])
    game = db.get(Game, active_matches(db, tournament.id)[0].game_id)
    now = game.last_move_at + timedelta(seconds=100)
    assert game_service.expire_clock(db, game.id, now) is None
    assert game_service.expire_clock(db, game.id,
                                     now + timedelta(seconds=100)) is None
    db.refresh(game)
    assert game.white_time_remaining == 600
    assert game_service.expire_clock(db, game.id,
                                     now + timedelta(seconds=500)) is not None


def _finish_as_draw(db, game_id, fen, remaining_times=None):
    from datetime import datetime, timezone
    game = db.query(Game).filter(Game.id == game_id).first()
    game.status = "finished"
    game.result = "1/2-1/2"
    game.current_fen = fen
    game.finished_at = datetime.now(timezone.utc)
    if remaining_times is not None:
        game.white_time_remaining, game.black_time_remaining = remaining_times
    db.commit()


def test_draw_is_broken_by_material_on_the_board(db):
    players = create_four_players(db)
    tournament = start_with(db, [p.id for p in players])

    match = tournament_service.get_tournament(db, tournament.id).matches[0]

    # White is up a queen: white_material (9) > black_material (0).
    fen = "4k3/8/8/8/8/8/8/3QK3 w - - 0 1"
    _finish_as_draw(db, match.game_id, fen, remaining_times=(10, 590))

    tournament_service.process_tournament(db, tournament.id)
    view = tournament_service.get_tournament(db, tournament.id)
    resolved = next(m for m in view.matches if m.game_id == match.game_id)

    assert resolved.winner_id == match.player1_id  # white


@pytest.mark.parametrize("remaining_times,winner_color", [
    ((120, 60), "white"),
    ((60, 120), "black"),
    ((0, 1), "black"),
])
def test_equal_material_draw_is_broken_by_remaining_time(
        db, monkeypatch, remaining_times, winner_color):
    players = create_four_players(db)
    tournament = start_with(db, [p.id for p in players])
    match = tournament_service.get_tournament(db, tournament.id).matches[0]
    _finish_as_draw(db, match.game_id, chess.Board().fen(), remaining_times)

    def unexpected_lottery(candidates):
        raise AssertionError("Unequal clocks must decide without a lottery")

    monkeypatch.setattr(tournament_service.random, "choice",
                        unexpected_lottery)

    tournament_service.process_tournament(db, tournament.id)
    first = tournament_service.get_tournament(db, tournament.id)
    second = tournament_service.get_tournament(db, tournament.id)
    resolved = next(m for m in first.matches if m.game_id == match.game_id)
    expected_winner = match.player1_id if winner_color == "white" else match.player2_id
    assert resolved.winner_id == expected_winner
    assert first == second
    assert db.query(Game).count() == 2
    assert db.get(Game, match.game_id).result == "1/2-1/2"


def test_clock_tiebreak_advances_round_and_finishes_final(db):
    players = create_four_players(db)
    tournament = start_with(db, [p.id for p in players])
    round_one = active_matches(db, tournament.id)
    for match in round_one:
        _finish_as_draw(db, match.game_id, chess.Board().fen(), (60, 120))

    tournament_service.process_tournament(db, tournament.id)
    view = tournament_service.get_tournament(db, tournament.id)
    tournament_service.process_tournament(db, tournament.id,
                                          view.next_round_at)
    final = next(
        m for m in tournament_service.get_tournament(db, tournament.id).matches
        if m.round == 2)
    assert {final.player1_id,
            final.player2_id} == {m.player2_id
                                  for m in round_one}
    _finish_as_draw(db, final.game_id, chess.Board().fen(), (120, 60))

    tournament_service.process_tournament(db, tournament.id)
    first = tournament_service.get_tournament(db, tournament.id)
    second = tournament_service.get_tournament(db, tournament.id)
    assert first.status == "finished"
    assert first.winner_id == final.player1_id
    assert first == second
    assert db.query(Game).count() == 3


@pytest.mark.parametrize("remaining_times", [(None, None), (None, 60),
                                             (60, None)])
def test_legacy_draw_without_both_clocks_uses_lottery(db, monkeypatch,
                                                      remaining_times):
    players = create_four_players(db)
    tournament = start_with(db, [p.id for p in players])
    match = tournament_service.get_tournament(db, tournament.id).matches[0]
    _finish_as_draw(db, match.game_id, chess.Board().fen(), remaining_times)
    monkeypatch.setattr(tournament_service.random, "choice",
                        lambda candidates: candidates[1])

    tournament_service.process_tournament(db, tournament.id)
    view = tournament_service.get_tournament(db, tournament.id)
    resolved = next(m for m in view.matches if m.slot == match.slot)
    assert resolved.winner_id == match.player2_id
    assert resolved.game_id == match.game_id
    assert db.query(Game).count() == 2


@pytest.mark.parametrize("chosen_index", [0, 1])
def test_equal_material_and_equal_clocks_draw_uses_lottery(
        db, monkeypatch, chosen_index):
    players = create_four_players(db)
    tournament = start_with(db, [p.id for p in players])

    match = tournament_service.get_tournament(db, tournament.id).matches[0]
    original_game_id = match.game_id

    _finish_as_draw(db, match.game_id, chess.Board().fen())
    choices = []

    def choose(candidates):
        choices.append(tuple(candidates))
        return candidates[chosen_index]

    monkeypatch.setattr(tournament_service.random, "choice", choose)

    tournament_service.process_tournament(db, tournament.id)
    view = tournament_service.get_tournament(db, tournament.id)
    resolved = next(m for m in view.matches
                    if m.round == 1 and {m.player1_id, m.player2_id} ==
                    {match.player1_id, match.player2_id})

    assert resolved.winner_id == (match.player1_id,
                                  match.player2_id)[chosen_index]
    assert resolved.game_id == original_game_id
    assert tournament_service.get_tournament(db, tournament.id) == view
    assert choices == [(match.player1_id, match.player2_id)]
    assert db.query(Game).count() == 2


@pytest.mark.parametrize("ending", ["accept_draw", "threefold", "fifty_move"])
def test_draw_clocks_are_frozen_before_tournament_tiebreak(db, ending):
    players = create_four_players(db)
    start = datetime(2026, 10, 3, tzinfo=timezone.utc)
    with patch("backend.services.game_service.datetime") as game_datetime:
        game_datetime.now.return_value = start
        tournament = start_with(db, [p.id for p in players])
        match = tournament_service.get_tournament(db, tournament.id).matches[0]
        game = db.get(Game, match.game_id)

        if ending == "accept_draw":
            game_service.offer_draw(db, game.id, match.player1_id)
            finish = game_service.accept_draw
            player_id = match.player2_id
        elif ending == "threefold":
            for index, move in enumerate(("g1f3", "g8f6", "f3g1", "f6g8") * 2):
                player_id = match.player1_id if index % 2 == 0 else match.player2_id
                game_service.make_move(db, game.id, player_id, move)
            finish = game_service.claim_threefold_repetition
            player_id = match.player1_id
        else:
            # Equal material; either player may claim the fifty-move draw.
            pgn = chess.pgn.Game()
            pgn.setup(chess.Board("7k/8/8/8/8/8/8/K7 w - - 99 50"))
            game.current_fen = pgn.board().fen()
            game.pgn = str(pgn)
            finish = game_service.claim_fifty_move
            player_id = match.player1_id

        game.white_time_remaining = 120
        game.black_time_remaining = 115
        db.commit()
        game_datetime.now.return_value = start + timedelta(seconds=10)
        finish(db, game.id, player_id)

    db.refresh(game)
    assert (game.white_time_remaining, game.black_time_remaining) == (110, 115)
    tournament_service.process_tournament(db, tournament.id)
    first = tournament_service.get_tournament(db, tournament.id)
    second = tournament_service.get_tournament(db, tournament.id)
    resolved = next(m for m in first.matches if m.game_id == match.game_id)
    assert resolved.winner_id == match.player2_id
    assert first == second
    assert db.query(Game).count() == 2


def _run_contended(engine,
                   monkeypatch,
                   tournament_id,
                   first_operation,
                   second_operation,
                   preload=False):
    """Pause the first lock owner until PostgreSQL confirms the second waits."""
    locked = Event()
    release = Event()
    attempting = Event()
    second_pid = []
    original = TournamentRepository.get_by_id_for_update

    def pause_first(repository, requested_id):
        if current_thread().name.endswith("_1"):
            attempting.set()
        tournament = original(repository, requested_id)
        if current_thread().name.endswith("_0"):
            locked.set()
            assert release.wait(10), "First worker was not released"
        return tournament

    monkeypatch.setattr(TournamentRepository, "get_by_id_for_update",
                        pause_first)

    def run(operation, second=False):
        with Session(engine) as db:
            db.execute(text("SET LOCAL lock_timeout = '8s'"))
            if second:
                second_pid.append(db.scalar(text("SELECT pg_backend_pid()")))
                if preload:
                    # Keep a strong reference: SQLAlchemy's identity map is weak.
                    cached_tournament = db.get(Tournament, tournament_id)
                    cached_matches = db.query(TournamentMatch).filter_by(
                        tournament_id=tournament_id).all()
                    cached_games = db.query(Game).all()
            try:
                result = operation(db)
            except Exception as error:
                result = error
            # The worker deliberately keeps its session open after errors.
            # A missing rollback would prevent the other worker from finishing.
            if not second:
                assert second_done.wait(10), "Error left a lock held"
            else:
                second_done.set()
            return result

    second_done = Event()
    with ThreadPoolExecutor(max_workers=2,
                            thread_name_prefix="tournament") as pool:
        first = pool.submit(run, first_operation)
        try:
            assert locked.wait(5), "First worker did not acquire the lock"
            second = pool.submit(run, second_operation, True)
            assert attempting.wait(5), "Second worker did not attempt the lock"
            deadline = monotonic() + 5
            with engine.connect() as observer:
                while monotonic() < deadline:
                    wait_type = observer.scalar(
                        text("SELECT wait_event_type FROM pg_stat_activity "
                             "WHERE pid = :pid"), {"pid": second_pid[0]})
                    observer.commit()
                    if wait_type == "Lock":
                        break
                    sleep(0.02)
                else:
                    pytest.fail(
                        "Second PostgreSQL connection never waited on the lock"
                    )
            assert not second.done()
        finally:
            release.set()
        return first.result(timeout=12), second.result(timeout=12)


@pytest.fixture
def setup_tournament(engine):
    with Session(engine) as db:
        players = create_players(db, 5)
        ids = [p.id for p in players]
        tournament = tournament_service.create_tournament(db, ids[0])
        for user_id in ids[1:4]:
            tournament_service.register(db, tournament.id, user_id)
        return tournament.id, ids


def _start(db, tournament_id, user_id):
    tournament_service.start_tournament(db, tournament_id, user_id)
    return "started"


def _register(db, tournament_id, user_id):
    tournament_service.register(db, tournament_id, user_id)
    return "registered"


def _process(db, tournament_id, now=None):
    tournament_service.process_tournament(db, tournament_id, now)
    return "processed"


@pytest.mark.parametrize("preload", [False, True])
def test_concurrent_starts_create_one_bracket(engine, setup_tournament,
                                              monkeypatch, preload):
    tid, players = setup_tournament
    first, second = _run_contended(engine, monkeypatch, tid,
                                   lambda db: _start(db, tid, players[0]),
                                   lambda db: _start(db, tid, players[0]),
                                   preload)
    assert first == "started" and isinstance(second, TournamentAlreadyStarted)
    with Session(engine) as db:
        assert db.query(TournamentMatch).count() == 3
        assert db.query(Game).count() == 0


def test_registration_cannot_join_after_concurrent_start(
        engine, setup_tournament, monkeypatch):
    tid, players = setup_tournament
    first, second = _run_contended(engine, monkeypatch, tid,
                                   lambda db: _start(db, tid, players[0]),
                                   lambda db: _register(db, tid, players[4]))
    assert first == "started" and isinstance(second, TournamentAlreadyStarted)


def test_concurrent_workers_launch_once(engine, setup_tournament, monkeypatch):
    tid, players = setup_tournament
    with Session(engine) as db:
        tournament = tournament_service.start_tournament(db, tid, players[0])
        deadline = tournament.next_round_at
    first, second = _run_contended(engine,
                                   monkeypatch,
                                   tid,
                                   lambda db: _process(db, tid, deadline),
                                   lambda db: _process(db, tid, deadline),
                                   preload=True)
    assert first == second == "processed"
    with Session(engine) as db:
        assert db.query(Game).count() == 2


def test_concurrent_workers_schedule_next_round_once(engine, setup_tournament,
                                                     monkeypatch):
    tid, players = setup_tournament
    with Session(engine) as db:
        tournament = tournament_service.start_tournament(db, tid, players[0])
        tournament_service.process_tournament(db, tid,
                                              tournament.next_round_at)
        for match in active_matches(db, tid):
            game_service.resign(db, match.game_id, match.player2_id)
    first, second = _run_contended(engine,
                                   monkeypatch,
                                   tid,
                                   lambda db: _process(db, tid),
                                   lambda db: _process(db, tid),
                                   preload=True)
    assert first == second == "processed"
    with Session(engine) as db:
        assert db.query(Game).count() == 2
        view = tournament_service.get_tournament(db, tid)
        assert view.status == "between_rounds"
        assert len([m for m in view.matches if m.round == 2]) == 1


@pytest.mark.parametrize("other_action", ["register", "matchmaking", "create"])
def test_same_player_concurrent_reservations_have_one_winner(
        engine, db, other_action):
    players = create_players(db, 3)
    ids = [p.id for p in players]
    tournaments = [
        tournament_service.create_tournament(db, api_manager=True).id
        for _ in range(2)
    ]
    db.rollback()
    barrier = Barrier(2)

    def run(action):
        with Session(engine) as session:
            session.execute(text("SET LOCAL lock_timeout = '5s'"))
            barrier.wait(timeout=5)
            try:
                if action == "first":
                    tournament_service.register(session, tournaments[0],
                                                ids[0])
                elif action == "register":
                    tournament_service.register(session, tournaments[1],
                                                ids[0])
                elif action == "create":
                    tournament_service.create_tournament(session, ids[0])
                else:
                    matchmaking_service.join_queue(session, ids[0], 600, 0)
                return "ok"
            except PlayerUnavailable:
                return "busy"

    with ThreadPoolExecutor(max_workers=2) as pool:
        results = list(pool.map(run, ["first", other_action]))
    assert sorted(results) == ["busy", "ok"]


def test_concurrent_clock_and_move_apply_elo_once(engine, db):
    tournament = start_with(db, [p.id for p in create_players(db, 2)])
    match = active_matches(db, tournament.id)[0]
    game = db.get(Game, match.game_id)
    game.last_move_at = datetime.now(timezone.utc) - timedelta(seconds=601)
    db.commit()
    barrier = Barrier(2)

    def run(move):
        with Session(engine) as session:
            barrier.wait(timeout=5)
            try:
                if move:
                    game_service.make_move(session, match.game_id,
                                           match.player1_id, "e2e4")
                else:
                    game_service.expire_clock(session, match.game_id)
            except Exception as error:
                from backend.exceptions.game import GameNotActive
                assert isinstance(error, GameNotActive)

    with ThreadPoolExecutor(max_workers=2) as pool:
        list(pool.map(run, [True, False]))
    db.expire_all()
    assert db.get(User, match.player1_id).elo == 984
    assert db.get(User, match.player2_id).elo == 1016


def test_tournament_migration_preserves_existing_rows_and_is_reversible(
        engine):
    import importlib.util
    from pathlib import Path
    from uuid import uuid4
    from alembic.migration import MigrationContext
    from alembic.operations import Operations
    from sqlalchemy import inspect
    spec = importlib.util.spec_from_file_location(
        "schedule_migration",
        Path(__file__).parents[2] /
        "alembic/versions/a91f742dc630_tournament_scheduling.py")
    migration = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(migration)
    schema = "tournament_migration_" + uuid4().hex
    with engine.connect() as connection:
        transaction = connection.begin()
        try:
            connection.execute(text("CREATE SCHEMA " + schema))
            connection.execute(text("SET LOCAL search_path TO " + schema))
            for statement in (
                    "CREATE TABLE users (id INTEGER PRIMARY KEY)",
                    "CREATE TABLE games (id INTEGER PRIMARY KEY)",
                    "CREATE TABLE tournaments (id INTEGER PRIMARY KEY, status VARCHAR(20) NOT NULL, winner_id INTEGER, created_at TIMESTAMPTZ NOT NULL)",
                    "CREATE TABLE tournament_participants (id INTEGER PRIMARY KEY, tournament_id INTEGER REFERENCES tournaments(id), user_id INTEGER REFERENCES users(id), joined_at TIMESTAMPTZ NOT NULL)",
                    "CREATE TABLE tournament_matches (id INTEGER PRIMARY KEY, tournament_id INTEGER REFERENCES tournaments(id), round INTEGER NOT NULL, slot INTEGER NOT NULL, player1_id INTEGER NOT NULL REFERENCES users(id), player2_id INTEGER NOT NULL REFERENCES users(id), game_id INTEGER NOT NULL REFERENCES games(id), winner_id INTEGER)",
                    "INSERT INTO users VALUES (1), (2)",
                    "INSERT INTO games VALUES (1)",
                    "INSERT INTO tournaments VALUES (1, 'in_progress', NULL, '2026-10-09 10:00:00+00'), (2, 'registration', NULL, '2026-10-09 10:00:00+00')",
                    "INSERT INTO tournament_participants VALUES (1, 1, 2, '2026-10-09 10:00:00+00'), (2, 1, 1, '2026-10-09 10:00:00+00')",
                    "INSERT INTO tournament_matches VALUES (1, 1, 1, 0, 2, 1, 1, NULL)",
            ):
                connection.execute(text(statement))
            with Operations.context(MigrationContext.configure(connection)):
                migration.upgrade()
                row = connection.execute(
                    text(
                        "SELECT creator_id, organizer_type, current_round, registration_deadline FROM tournaments WHERE id=1"
                    )).one()
                assert row[:3] == (2, "player", 1)
                assert row[3] == datetime(2026,
                                          10,
                                          9,
                                          10,
                                          30,
                                          tzinfo=timezone.utc)
                assert connection.scalar(
                    text("SELECT organizer_type FROM tournaments WHERE id=2")
                ) == "api"
                connection.execute(
                    text(
                        "INSERT INTO tournament_matches (id,tournament_id,round,slot,player1_id,is_bye,winner_id) VALUES (2,2,1,0,1,TRUE,1)"
                    ))
                migration.downgrade()
                assert connection.scalar(
                    text("SELECT count(*) FROM tournament_matches")) == 1
                assert connection.scalar(
                    text("SELECT game_id FROM tournament_matches WHERE id=1")
                ) == 1
                columns = {
                    c["name"]
                    for c in inspect(connection).get_columns("tournaments",
                                                             schema=schema)
                }
                assert columns == {"id", "status", "winner_id", "created_at"}
        finally:
            transaction.rollback()


def test_worker_isolates_errors_and_still_cancels_other_tournaments(
        engine, db, monkeypatch, caplog):
    tournament = prepare_with(db, [p.id for p in create_players(db, 2)])
    expired = tournament_service.create_tournament(db, api_manager=True)
    expired.registration_deadline = datetime.now(
        timezone.utc) - timedelta(seconds=1)
    db.commit()
    tid, other_id, deadline = tournament.id, expired.id, tournament.next_round_at
    db.rollback()

    def fail(*args, **kwargs):
        raise RuntimeError("Simulated worker failure")

    monkeypatch.setattr(game_service, "create_human_game", fail)
    tournament_scheduler.run_tick(sessionmaker(bind=engine), deadline)
    db.expire_all()
    assert db.get(Tournament, tid).status == "countdown"
    assert db.get(Tournament, other_id).status == "cancelled"
    assert "Could not advance tournament" in caplog.text


def test_scheduler_lifecycle_broadcasts_only_after_committed_timeout(
        engine, db, monkeypatch):
    import asyncio
    from types import SimpleNamespace
    tournament = start_with(db, [p.id for p in create_players(db, 2)])
    game = db.get(Game, active_matches(db, tournament.id)[0].game_id)
    game.last_move_at = datetime.now(timezone.utc) - timedelta(seconds=601)
    db.commit()
    game_id = game.id
    db.rollback()
    messages = []

    async def broadcast(gid, message):
        with Session(engine) as observer:
            assert observer.get(Game, gid).status == "finished"
        messages.append((gid, message))

    monkeypatch.setattr(tournament_scheduler.manager, "broadcast", broadcast)
    app = SimpleNamespace(
        state=SimpleNamespace(tournament_scheduler_enabled=True,
                              tournament_session_factory=sessionmaker(
                                  bind=engine)))

    async def exercise():
        async with tournament_scheduler.lifespan(app):
            async with asyncio.timeout(5):
                while len(messages) < 2:
                    await asyncio.sleep(0.01)

    asyncio.run(exercise())
    assert [m["type"] for gid, m in messages
            if gid == game_id] == ["game_state", "game_over"]


def test_concurrent_duplicate_registration_releases_lock(
        engine, setup_tournament, monkeypatch):
    tid, players = setup_tournament
    first, second = _run_contended(engine, monkeypatch, tid,
                                   lambda db: _register(db, tid, players[4]),
                                   lambda db: _register(db, tid, players[4]))
    assert first == "registered" and isinstance(second, AlreadyRegistered)


def test_different_tournaments_with_different_players_do_not_block(engine, db):
    players = create_players(db, 2)
    other_player_id = players[1].id
    tournaments = [
        tournament_service.create_tournament(db, api_manager=True).id
        for _ in range(2)
    ]
    db.rollback()
    with Session(engine) as owner:
        TournamentRepository(owner).get_by_id_for_update(tournaments[0])

        def register_other():
            with Session(engine) as session:
                session.execute(text("SET LOCAL lock_timeout = '2s'"))
                return _register(session, tournaments[1], other_player_id)

        with ThreadPoolExecutor(max_workers=1) as pool:
            assert pool.submit(register_other).result(
                timeout=5) == "registered"
        owner.rollback()


@pytest.mark.parametrize("turn", ["white", "black"])
def test_worker_respects_both_player_clocks(db, turn):
    tournament = start_with(db, [p.id for p in create_players(db, 2)])
    match = active_matches(db, tournament.id)[0]
    if turn == "black":
        game_service.make_move(db, match.game_id, match.player1_id, "e2e4")
    game = db.get(Game, match.game_id)
    reference = datetime.now(timezone.utc)
    game.last_move_at = reference
    game.white_time_remaining = 15
    game.black_time_remaining = 35
    db.commit()
    limit = 15 if turn == "white" else 35
    assert game_service.expire_clock(db, game.id, reference +
                                     timedelta(seconds=limit - 1)) is None
    event = game_service.expire_clock(db, game.id,
                                      reference + timedelta(seconds=limit))
    assert event["result"] == ("0-1" if turn == "white" else "1-0")
    db.refresh(game)
    assert (game.white_time_remaining,
            game.black_time_remaining) == ((0, 35) if turn == "white" else
                                           (15, 0))
