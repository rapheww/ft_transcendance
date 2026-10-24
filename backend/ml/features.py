import io
import chess
import chess.pgn

from sqlalchemy.orm import Session
from backend.models.user import User
from backend.models.game import Game

def get_result(game: Game, user_id:int) -> bool:
    if game.result == "1-0":
        return game.white_player_id == user_id
    elif game.result == "0-1":
        return game.black_player_id == user_id
    return False

def get_time_control(game: Game) -> str | None:
    if game.initial_time_seconds is None:
        return None
    total_seconds = (
        game.initial_time_seconds 
        + game.increment_seconds * 60
    )
    if total_seconds < 180:
        return "bullet"
    elif total_seconds <= 600:
        return "blitz"
    elif total_seconds < 3600:
        return "rapid"
    else:
        return "classical"

def get_game_length(game: Game) -> float | None:
    if not game.pgn:
        return None
    pgn_game = chess.pgn.read_game(io.StringIO(game.pgn))

    if pgn_game is None or pgn_game.errors:
        return None
    plies = sum(1 for _ in pgn_game.mainline_moves())
    return plies / 2

def extract_playing_style(game: Game, user_id: int) -> dict | None:
    if not game.pgn:
        return None
    pgn_game = chess.pgn.read_game(io.StringIO(game.pgn))

    if pgn_game is None or pgn_game.errors:
        return None
    if game.white_player_id == user_id:
        player_color = chess.WHITE
    elif game.black_player_id == user_id:
        player_color = chess.BLACK
    else:
        return None

    board = pgn_game.board()

    stats = {
        "moves": 0,
        "captures": 0,
        "checks": 0,
        "castled": False,
        "early_queen": False,
        "opening": (),
        "game_length": 0.0,
    }

    opening_moves = []

    for ply, move in enumerate(pgn_game.mainline_moves()):

        if ply < 6:
            opening_moves.append(move.uci())

        if board.turn == player_color:
            stats["moves"] += 1
            if board.is_capture(move):
                stats["captures"] += 1
            if board.is_castling(move):
                stats["castled"] = True
            # Detect early queen move
            piece = board.piece_at(move.from_square)
            if (ply < 10 and piece and piece.piece_type == chess.QUEEN):
                stats["early_queen"] = True
            if board.gives_check(move):
                stats["checks"] += 1

        board.push(move)
        stats["game_length"] += 0.5

    stats["opening"] = tuple(opening_moves)
    
    return stats

def extract_player_profile(db: Session, user_id: int) -> dict:
    user = db.get(User, user_id)
    if user is None:
        raise ValueError("User not found")
    
    games = db.query(Game).filter(
        (Game.white_player_id == user_id) |
        (Game.black_player_id == user_id),
        Game.status == "finished"
    ).all()

    game_played = len(games)

    wins = 0
    total_moves = 0.0
    valid_lengths = 0

    bullet = 0
    blitz = 0
    rapid = 0
    classical = 0
    valid_time_controls = 0

    for game in games:
        if get_result(game, user_id):
            wins += 1
        game_length = get_game_length(game)
        if game_length is not None:
            total_moves += game_length
            valid_lengths += 1
        time_control = get_time_control(game)
        if time_control in ("bullet", "blitz", "rapid", "classical"):
            valid_time_controls += 1
        if time_control == "bullet":
            bullet += 1
        elif time_control == "blitz":
            blitz += 1
        elif time_control == "rapid":
            rapid += 1
        elif time_control == "classical":
            classical += 1

    win_rate = (wins / game_played if game_played else 0.0)
    bullet_ratio = (bullet / valid_time_controls if valid_time_controls else 0.0)
    blitz_ratio = (blitz / valid_time_controls if valid_time_controls else 0.0)
    rapid_ratio = (rapid / valid_time_controls if valid_time_controls else 0.0)
    classical_ratio = (classical / valid_time_controls if valid_time_controls else 0.0)
    average_game_length = (total_moves / valid_lengths if valid_lengths else 0.0)

    return {
        "user_id": user.id,
        "is_bot": user.is_bot,
        "elo": user.elo,
        "win_rate": round(win_rate, 3),
        "bullet_ratio": round(bullet_ratio, 3),
        "blitz_ratio": round(blitz_ratio, 3),
        "rapid_ratio": round(rapid_ratio, 3),
        "classical_ratio": round(classical_ratio, 3),
        "avg_game_length": round(average_game_length, 2),
        "games_played": game_played
    }

if __name__ == "__main__":

    from backend.db.session import SessionLocal

    with SessionLocal() as db:
        games = db.query(Game).filter(
            Game.status == "finished",
            Game.pgn.isnot(None) 
        ).all()
    for game in games:
        if game:
            user_id = game.white_player_id

            print("Player ID: ", user_id)
            print("Profiles: ", extract_player_profile(db, user_id))
            print("Style: ", extract_playing_style(game, user_id))
        else:
            print("No completed games found")

    # pgn_game exemple:

# game.pgn = """
# [Event "Transcendence"]
# [White "Alice"]
# [Black "Bob"]
# [Result "1-0"]

# 1. e4 e5 2. Nf3 Nc6 3. Bc4 Bc5
# 4. Qh5 Nf6 5. Qxf7# 1-0
# """
