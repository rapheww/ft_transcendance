from sqlalchemy.orm import Session
from backend.models.tournament import Tournament, TournamentMatch, TournamentParticipant


class TournamentRepository:

    def __init__(self, db: Session):
        self.db = db

    def create(self, tournament: Tournament) -> Tournament:
        self.db.add(tournament)
        self.db.flush()
        self.db.refresh(tournament)
        return tournament

    def get_by_id(self, tournament_id: int) -> Tournament | None:
        return (self.db.query(Tournament).filter(
            Tournament.id == tournament_id).populate_existing().first())

    def get_by_id_for_update(self, tournament_id: int) -> Tournament | None:
        # Refresh cached state after waiting for another transaction's lock.
        return (self.db.query(Tournament).filter(
            Tournament.id ==
            tournament_id).populate_existing().with_for_update().first())

    def update(self, tournament: Tournament) -> Tournament:
        self.db.flush()
        self.db.refresh(tournament)
        return tournament

    def add_participant(
            self, participant: TournamentParticipant) -> TournamentParticipant:
        self.db.add(participant)
        self.db.flush()
        return participant

    def list_participants(self,
                          tournament_id: int) -> list[TournamentParticipant]:
        return (self.db.query(TournamentParticipant).filter(
            TournamentParticipant.tournament_id == tournament_id).order_by(
                TournamentParticipant.joined_at).populate_existing().all())

    def create_match(self, match: TournamentMatch) -> TournamentMatch:
        self.db.add(match)
        self.db.flush()
        self.db.refresh(match)
        return match

    def list_matches(self, tournament_id: int) -> list[TournamentMatch]:
        return (self.db.query(TournamentMatch).filter(
            TournamentMatch.tournament_id == tournament_id).order_by(
                TournamentMatch.round,
                TournamentMatch.slot).populate_existing().all())

    def list_matches_for_round(self, tournament_id: int,
                               round_number: int) -> list[TournamentMatch]:
        return (self.db.query(TournamentMatch).filter(
            TournamentMatch.tournament_id == tournament_id,
            TournamentMatch.round == round_number).order_by(
                TournamentMatch.slot).populate_existing().all())

    def delete_participants(self, tournament_id: int) -> None:
        (self.db.query(TournamentParticipant).filter(
            TournamentParticipant.tournament_id == tournament_id).delete())
        self.db.flush()

    def delete(self, tournament: Tournament) -> None:
        self.db.delete(tournament)
        self.db.flush()
