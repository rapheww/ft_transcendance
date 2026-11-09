from sqlalchemy import or_
from sqlalchemy.orm import Session, joinedload
from backend.models.game import Game
from backend.models.tournament import TournamentMatch


class GameRepository:

    def __init__(self, db: Session):
        self.db = db

    def create(self, game: Game) -> Game:
        self.db.add(game)
        self.db.flush()
        self.db.refresh(game)
        return game

    def get_by_id(self, game_id: int) -> Game | None:
        return (self.db.query(Game).filter(Game.id == game_id).first())

    def list_active_games(self, limit: int = 50) -> list[Game]:
        return (self.db.query(Game).filter(
            Game.status == "active").options(
                joinedload(Game.white_player),
                joinedload(Game.black_player)).order_by(
                Game.created_at.desc()).limit(limit).all())

    def get_by_id_for_update(self, game_id: int) -> Game | None:
        return (self.db.query(Game).filter(
            Game.id == game_id).populate_existing().with_for_update().first())

    def get_active_game_for_user(self, user_id: int) -> Game | None:
        return (self.db.query(Game).filter(
            Game.status == "active", Game.opponent_type == "human",
            ~self.db.query(TournamentMatch.id).filter(TournamentMatch.game_id == Game.id).exists(),
            or_(Game.white_player_id == user_id,
                Game.black_player_id == user_id)).order_by(
                    Game.created_at.desc()).first())

    def update(self, game: Game) -> Game:
        self.db.flush()
        self.db.refresh(game)
        return game
