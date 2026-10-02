import chess
import pytest
from backend.exceptions.tournament import (AlreadyRegistered,
                                           InvalidParticipantCount,
                                           NotRegistered,
                                           TournamentAlreadyStarted,
                                           TournamentNotFound)
from backend.models.game import Game
from backend.models.tournament import TournamentParticipant
from backend.models.user import User
from backend.services import game_service, tournament_service


def create_user(db, username, email):
    user = User(username=username,
                email=email,
                password_hash="hashed-password")
    db.add(user)
    db.commit()
    return user


def create_four_players(db):
    return [
        create_user(db, f"player{i}", f"player{i}@example.com")
        for i in range(4)
    ]


def start_with(db, player_ids):
    tournament = tournament_service.create_tournament(db, player_ids[0])

    for player_id in player_ids[1:]:
        tournament_service.register(db, tournament.id, player_id)

    tournament_service.start_tournament(db, tournament.id, player_ids[0])

    return tournament


def test_create_tournament_registers_the_creator(db):
    creator = create_user(db, "alice", "alice@example.com")

    tournament = tournament_service.create_tournament(db, creator.id)
    view = tournament_service.get_tournament(db, tournament.id)

    assert view.status == "registration"
    assert view.participants == ["alice"]


def test_register_adds_a_participant(db):
    alice = create_user(db, "alice", "alice@example.com")
    bob = create_user(db, "bob", "bob@example.com")

    tournament = tournament_service.create_tournament(db, alice.id)
    tournament_service.register(db, tournament.id, bob.id)

    view = tournament_service.get_tournament(db, tournament.id)

    assert view.participants == ["alice", "bob"]


def test_register_twice_raises(db):
    alice = create_user(db, "alice", "alice@example.com")
    tournament = tournament_service.create_tournament(db, alice.id)

    with pytest.raises(AlreadyRegistered):
        tournament_service.register(db, tournament.id, alice.id)


def test_register_after_start_raises(db):
    players = create_four_players(db)
    tournament = start_with(db, [p.id for p in players])

    fifth = create_user(db, "player5", "player5@example.com")

    with pytest.raises(TournamentAlreadyStarted):
        tournament_service.register(db, tournament.id, fifth.id)


def test_start_with_non_power_of_two_raises(db):
    alice = create_user(db, "alice", "alice@example.com")
    bob = create_user(db, "bob", "bob@example.com")
    carol = create_user(db, "carol", "carol@example.com")

    tournament = tournament_service.create_tournament(db, alice.id)
    tournament_service.register(db, tournament.id, bob.id)
    tournament_service.register(db, tournament.id, carol.id)

    with pytest.raises(InvalidParticipantCount):
        tournament_service.start_tournament(db, tournament.id, alice.id)


def test_start_by_non_participant_raises(db):
    alice = create_user(db, "alice", "alice@example.com")
    bob = create_user(db, "bob", "bob@example.com")
    outsider = create_user(db, "outsider", "outsider@example.com")

    tournament = tournament_service.create_tournament(db, alice.id)
    tournament_service.register(db, tournament.id, bob.id)

    with pytest.raises(NotRegistered):
        tournament_service.start_tournament(db, tournament.id, outsider.id)


def test_start_creates_first_round_matches(db):
    players = create_four_players(db)
    tournament = start_with(db, [p.id for p in players])

    view = tournament_service.get_tournament(db, tournament.id)

    assert view.status == "in_progress"
    assert len(view.matches) == 2
    assert {match.round for match in view.matches} == {1}

    paired_ids = {
        pid
        for match in view.matches
        for pid in (match.player1_id, match.player2_id)
    }
    assert paired_ids == {p.id for p in players}


def test_tournament_advances_to_next_round_once_round_is_complete(db):
    players = create_four_players(db)
    tournament = start_with(db, [p.id for p in players])

    round_one = tournament_service.get_tournament(db, tournament.id).matches

    for match in round_one:
        game_service.resign(db, match.game_id,
                            match.player2_id)  # player1 wins

    view = tournament_service.get_tournament(db, tournament.id)

    assert view.status == "in_progress"
    assert len(view.matches) == 3  # 2 from round 1 + the final
    finalists = {m.player1_id for m in view.matches if m.round == 1}
    final_match = next(m for m in view.matches if m.round == 2)

    assert {final_match.player1_id, final_match.player2_id} == finalists


def test_tournament_finishes_after_the_final_match(db):
    players = create_four_players(db)
    tournament = start_with(db, [p.id for p in players])

    round_one = tournament_service.get_tournament(db, tournament.id).matches
    for match in round_one:
        game_service.resign(db, match.game_id, match.player2_id)

    final_match = next(
        m for m in tournament_service.get_tournament(db, tournament.id).matches
        if m.round == 2)

    game_service.resign(db, final_match.game_id, final_match.player2_id)

    view = tournament_service.get_tournament(db, tournament.id)

    assert view.status == "finished"
    assert view.winner_id == final_match.player1_id


def test_cancel_tournament_deletes_it_and_its_participants(db):
    alice = create_user(db, "alice", "alice@example.com")
    bob = create_user(db, "bob", "bob@example.com")

    tournament = tournament_service.create_tournament(db, alice.id)
    tournament_service.register(db, tournament.id, bob.id)

    tournament_service.cancel_tournament(db, tournament.id)

    with pytest.raises(TournamentNotFound):
        tournament_service.get_tournament(db, tournament.id)

    remaining = (db.query(TournamentParticipant).filter(
        TournamentParticipant.tournament_id == tournament.id).all())
    assert remaining == []


def test_cancel_tournament_after_start_raises(db):
    players = create_four_players(db)
    tournament = start_with(db, [p.id for p in players])

    with pytest.raises(TournamentAlreadyStarted):
        tournament_service.cancel_tournament(db, tournament.id)


def test_cancel_missing_tournament_raises(db):
    with pytest.raises(TournamentNotFound):
        tournament_service.cancel_tournament(db, 999999)


def _finish_as_draw(db, game_id, fen):
    from datetime import datetime, timezone
    game = db.query(Game).filter(Game.id == game_id).first()
    game.status = "finished"
    game.result = "1/2-1/2"
    game.current_fen = fen
    game.finished_at = datetime.now(timezone.utc)
    db.commit()


def test_draw_is_broken_by_material_on_the_board(db):
    players = create_four_players(db)
    tournament = start_with(db, [p.id for p in players])

    match = tournament_service.get_tournament(db, tournament.id).matches[0]

    # White is up a queen: white_material (9) > black_material (0).
    fen = "4k3/8/8/8/8/8/8/3QK3 w - - 0 1"
    _finish_as_draw(db, match.game_id, fen)

    view = tournament_service.get_tournament(db, tournament.id)
    resolved = next(m for m in view.matches if m.game_id == match.game_id)

    assert resolved.winner_id == match.player1_id  # white


def test_perfectly_equal_material_draw_is_replayed(db):
    players = create_four_players(db)
    tournament = start_with(db, [p.id for p in players])

    match = tournament_service.get_tournament(db, tournament.id).matches[0]
    original_game_id = match.game_id

    _finish_as_draw(db, match.game_id, chess.Board().fen())

    view = tournament_service.get_tournament(db, tournament.id)
    resolved = next(m for m in view.matches
                    if m.round == 1 and {m.player1_id, m.player2_id} ==
                    {match.player1_id, match.player2_id})

    assert resolved.winner_id is None
    assert resolved.game_id != original_game_id
