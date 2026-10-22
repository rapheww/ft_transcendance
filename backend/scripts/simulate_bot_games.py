import chess
import random
import chess.pgn

from datetime import datetime, timezone
from sqlalchemy.orm import Session

from backend.ai.chess_ai import choose_ai_move
from backend.models.user import User
from backend.models.game import Game
from backend.db.session import SessionLocal

MAX_PLIES = 300

def simulate_game(white_bot: User, black_bot: User):
    board = chess.Board()
    plies = 0
    
    while not board.is_game_over(claim_draw=True) and plies < MAX_PLIES:
        if board.turn == chess.WHITE:
            current_bot = white_bot
        else:
            current_bot = black_bot
        move = choose_ai_move(
            board, 
            current_bot.ai_level, 
            current_bot.style
        )
        if move is None:
            break
        
        board.push(move)
        plies += 1

    outcome = board.outcome(claim_draw=True)
    if outcome is None:
        game_result = "*"
        winner_id = None
        status = "unfinished"
    elif outcome.winner == chess.WHITE:
        game_result = outcome.result()
        winner_id = white_bot.id
        status = "finished"
    elif outcome.winner == chess.BLACK:
        game_result = outcome.result()
        winner_id = black_bot.id
        status = "finished"
    else:
        game_result = outcome.result()
        winner_id = None
        status = "finished"

    result = {
                "white_player_id": white_bot.id,
                "black_player_id": black_bot.id,
                "winner_id": winner_id,
                "status": status,
                "result": game_result,
                "move_count": plies,
            }
    
    return result, board

def save_ai_match(db: Session, bot1: User, bot2: User, board: chess.Board) -> Game:
    outcome = board.outcome(claim_draw=True)

    if outcome is None:
        raise ValueError("Game is not finished")

    pgn_game = chess.pgn.Game.from_board(board)
    pgn_game.headers["Result"] = outcome.result()

    game = Game(
        white_player_id=bot1.id,
        black_player_id=bot2.id,
        opponent_type="ai",
        ai_difficulty=None,
        status="finished",
        result=outcome.result(),
        current_fen=board.fen(),
        pgn=str(pgn_game),
        finished_at=datetime.now(timezone.utc),
    )
    db.add(game)
    db.commit()

    return game

def simulate_with_retry(bot1: User, bot2: User, max_attempts : int=2) -> tuple[dict, chess.Board] | None:
    for attempt in range(max_attempts):
        result, board = simulate_game(bot1, bot2)
        if result["status"] == "finished":
            return result, board
        print(f"Unfinished game: {bot1.username} vs "
               f"{bot2.username} attempt {attempt + 1}")
    return None

def run_tournament() -> dict:
    with SessionLocal() as db:
        bots = (db.query(User)
                .filter(User.is_bot.is_(True)).order_by(User.id)
                .all())
        print(f"Number of bots: {len(bots)}")
        if len(bots) < 2:
            raise ValueError("At least 2 bots are required")
        current_round = bots
        round_number = 1

        while len(current_round) > 1:
            next_round = []
            random.shuffle(current_round)
            print(f"\nRound {round_number}")
            if len(current_round) % 2 != 0:
                bye_bot = current_round.pop()
                next_round.append(bye_bot)
            for i in range(0, len(current_round), 2):
                bot1 = current_round[i]
                bot2 = current_round[i + 1]
                print(bot1.username, "vs", bot2.username)
                simulation = simulate_with_retry(bot1, bot2)
                if simulation is None:
                    winner = bot1 if bot1.id < bot2.id else bot2
                else:
                    result, board = simulation
                    winner_id = result["winner_id"]
                    # Draw need a tournament tie-break rule
                    if winner_id is None:
                        winner = bot1 if bot1.elo > bot2.elo else bot2
                    else:
                        winner = bot1 if winner_id == bot1.id else bot2
                    save_ai_match(db, bot1, bot2, board)
                next_round.append(winner)
            current_round = next_round
            round_number += 1
        if current_round:
            winner = current_round[0]
            return {
                "id": winner.id,
                "username": winner.username,
                "elo": winner.elo,
            }
        return None

if __name__ == "__main__":
    winner = run_tournament()
    if winner is not None:
        print(f"\nTournament winner: {winner["username"]}")
    else:
        print("No tournament winner. Check the bot database.")
    

# pgn_game exemple:

# [Event "?"]
# [Site "?"]
# [Date "????.??.??"]
# [Round "?"]
# [White "bot_001"]
# [Black "bot_014"]
# [Result "*"]

# 1. e4 e5 2. Nf3 Nc6 *

#chess.Outcome

# Outcome(termination=<Termination.CHECKMATE: 1>, winner=False)
# False
# 0-1
# Termination.CHECKMATE

