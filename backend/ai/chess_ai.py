import chess
import random
import math
from backend.exceptions.game import InvalidDifficulty

STYLE_WEIGHTS = {
    "aggressive": {
        "material": 1.0,
        "mobility": 1.5,
        "center": 1.4,
        "king_safety": 0.7,
        "development": 1.2,
    },

    "balanced": {
        "material": 1.0,
        "mobility": 1.0,
        "center": 1.0,
        "king_safety": 1.0,
        "development": 1.0,
    },

    "defensive": {
        "material": 1.2,
        "mobility": 0.8,
        "center": 0.8,
        "king_safety": 1.5,
        "development": 1.0,
    },
}

def count_mobility(board, color):
    tmp_board = board.copy()
    tmp_board.turn = color
    return len(list(tmp_board.legal_moves))

def get_penalty(board, color):
    penalty = 0
    if color == chess.WHITE:
        if board.piece_at(chess.B1) == chess.Piece(chess.KNIGHT, color):
            penalty += 2
        if board.piece_at(chess.G1) == chess.Piece(chess.KNIGHT, color):
            penalty += 2
        if board.piece_at(chess.C1) == chess.Piece(chess.BISHOP, color):
            penalty += 2
        if board.piece_at(chess.F1) == chess.Piece(chess.BISHOP, color):
            penalty += 2
    if color == chess.BLACK:
        if board.piece_at(chess.B8) == chess.Piece(chess.KNIGHT, color):
            penalty += 2
        if board.piece_at(chess.G8) == chess.Piece(chess.KNIGHT, color):
            penalty += 2
        if board.piece_at(chess.C8) == chess.Piece(chess.BISHOP, color):
            penalty += 2
        if board.piece_at(chess.F8) == chess.Piece(chess.BISHOP, color):
            penalty += 2
    return penalty

def is_passed_pawn(board, square, color):
    own_file = chess.square_file(square)
    own_rank = chess.square_rank(square)

    enemy_color = not color
    files_to_check  = [own_file - 1, own_file, own_file + 1]

    for file in files_to_check:
        if file < 0 or file > 7:
            continue

        if color == chess.WHITE:
            ranks_to_check = range(own_rank + 1, 8)
        else:
            ranks_to_check = range(own_rank - 1, -1, -1)

        for rank in ranks_to_check:
            square_to_check = chess.square(file, rank)
            piece = board.piece_at(square_to_check)
            if piece and piece.piece_type == chess.PAWN and piece.color == enemy_color:
                return False
    return True

def is_open_file(board, file):
    for rank in range(8):
        square = chess.square(file, rank)
        piece = board.piece_at(square)
        if piece and piece.piece_type == chess.PAWN:
            return False
    return True

def evaluate(board, maximizing_color, difficulty, style):
    weights = STYLE_WEIGHTS[style]

    # check checkmate and draw
    if board.is_checkmate():
        if board.turn == maximizing_color:
            return -100000
        else:
            return 100000
    if (board.is_stalemate() 
        or board.is_insufficient_material()
        or board.is_fivefold_repetition()
        or board.is_seventyfive_moves()
    ):
        return 0

    white_score = 0
    black_score = 0

    # material_evaluation   
    piece_values = {
        chess.PAWN: 10,
        chess.KNIGHT: 30,
        chess.BISHOP: 30,
        chess.ROOK: 50,
        chess.QUEEN: 90,
        chess.KING: 0,
    }
    for piece_type, value in piece_values.items():
        white_score += len(board.pieces(piece_type, chess.WHITE)) * value * weights["material"]
        black_score += len(board.pieces(piece_type, chess.BLACK)) * value * weights["material"]

    # check center control
    center = [
            chess.D4,
            chess.D5,
            chess.E4,
            chess.E5,
        ]
    for square in center:
        piece = board.piece_at(square)
        if piece:
            if piece.color == chess.WHITE:
                white_score += 3 * weights["center"]
            else:   
                black_score += 3 * weights["center"]

    # check mobility
    white_mobility = count_mobility(board, chess.WHITE)
    black_mobility = count_mobility(board, chess.BLACK)
    white_score += white_mobility * 0.2 * weights["mobility"]
    black_score += black_mobility * 0.2 * weights["mobility"]

    # penalize undeveloped pieces
    white_score -= get_penalty(board, chess.WHITE) * weights["development"]
    black_score -= get_penalty(board, chess.BLACK) * weights["development"]

    # check king safety
    white_king = 0
    black_king = 0
    if board.king(chess.WHITE) in [chess.G1, chess.C1]:
        white_king += 5
    if board.king(chess.BLACK) in [chess.G8, chess.C8]:
        black_king += 5
    if board.is_check():
        if board.turn == chess.WHITE:
            white_king -= 5
        else:
            black_king -= 5
    white_score += white_king * weights["king_safety"]
    black_score += black_king * weights["king_safety"]

    # add piece-square tables last

    KNIGHT_TABLE = [
        -5, -4, -3, -3, -3, -3, -4, -5,
        -4, -2,  0,  0,  0,  0, -2, -4,
        -3,  0,  1,  2,  2,  1,  0, -3,
        -3,  1,  2,  3,  3,  2,  1, -3,
        -3,  0,  2,  3,  3,  2,  0, -3,
        -3,  1,  1,  2,  2,  1,  1, -3,
        -4, -2,  0,  1,  1,  0, -2, -4,
        -5, -4, -3, -3, -3, -3, -4, -5,
    ]
    for square in board.pieces(chess.KNIGHT, chess.WHITE):
        white_score += KNIGHT_TABLE[square] * weights["development"]
    for square in board.pieces(chess.KNIGHT, chess.BLACK):
        black_score += KNIGHT_TABLE[chess.square_mirror(square)] * weights["development"]

    if difficulty == "hard":
        # check passed pawns
        for square in board.pieces(chess.PAWN, chess.WHITE):
            if is_passed_pawn(board, square, chess.WHITE):
                white_score += 4
        for square in board.pieces(chess.PAWN, chess.BLACK):
            if is_passed_pawn(board, square, chess.BLACK):
                black_score += 4
        # check bishop pair
        if len(board.pieces(chess.BISHOP, chess.WHITE)) >= 2:
            white_score += 4
        if len(board.pieces(chess.BISHOP, chess.BLACK)) >= 2:
            black_score += 4

        # check rook activity
        for square in board.pieces(chess.ROOK, chess.WHITE):
            file_index = chess.square_file(square)
            if is_open_file(board, file_index):
                white_score += 3
        for square in board.pieces(chess.ROOK, chess.BLACK):
            file_index = chess.square_file(square)
            if is_open_file(board, file_index):
                black_score += 3

    # calculate difference
    if maximizing_color == chess.WHITE:
        score = white_score - black_score
    else:
        score = black_score - white_score
    return score

def minmax(board, depth, alpha, beta, maximizing_player, maximizing_color, difficulty, style):
    if depth == 0 or board.is_game_over():
        return None, evaluate(board, maximizing_color, difficulty, style) #(best_move, best_score)
    
    legal_moves = list(board.legal_moves)
    if not legal_moves:
        return None, evaluate(board, maximizing_color, difficulty, style)
    best_move = random.choice(legal_moves)

    if maximizing_player:
        max_eval = -math.inf
        for move in legal_moves:
            board.push(move)
            current_eval = minmax(board, depth - 1, alpha, beta, False, maximizing_color, difficulty, style)[1]
            board.pop()
            if current_eval > max_eval:
                max_eval = current_eval
                best_move = move
            alpha = max(alpha, current_eval)
            if beta <= alpha:
                break
        return best_move, max_eval
    
    else:
        min_eval = math.inf
        for move in legal_moves:
            board.push(move)
            current_eval = minmax(board, depth - 1, alpha, beta, True, maximizing_color, difficulty, style)[1]
            board.pop()
            if current_eval < min_eval:
                min_eval = current_eval
                best_move = move
            beta = min(beta, current_eval)
            if beta <= alpha:
                break
        return best_move, min_eval

def get_scored_moves(board, depth, difficulty, style):
    maximizing_color = board.turn
    scored_moves = []

    for move in list(board.legal_moves):
        board.push(move)
        _, score = minmax(board, depth - 1, -math.inf, math.inf, False, maximizing_color, difficulty, style)
        board.pop()
        scored_moves.append((move, score))

    scored_moves.sort(key=lambda item: item[1], reverse=True)

    return scored_moves

def choose_ai_move(board, difficulty, style="balanced"):
    legal_moves = list(board.legal_moves)
    if not legal_moves:
        return None
    
    if difficulty == "easy":
        return random.choice(legal_moves)
    if difficulty == "medium":
        depth = 2
        mistake_chance = 0.25
    elif difficulty == "hard":
        depth = 2
        mistake_chance = 0.05
    else:
        raise InvalidDifficulty()

    if random.random() < mistake_chance:        
        scored_moves = get_scored_moves(board, depth, difficulty, style)
        if len(scored_moves) > 1:
            return scored_moves[1][0]
        
    best_move, _ = minmax(board, depth, -math.inf, math.inf, True, board.turn, difficulty, style)
    # best_move, best_score
    return best_move

# if __name__ == "__main__":
#     board = chess.Board()
#     # difficulty = "hard"
#     # print("difficulty:", difficulty)
#     print("White:medium", " Black:hard")
#     print("Initial board:")
#     print(board)
#     print("Initial evaluation: ")
#     print("White:")
#     print(evaluate(board, chess.WHITE, "medium"))
#     print("Black:")
#     print(evaluate(board, chess.BLACK, "hard"))

#     for turn in range(20):
#         if board.is_game_over():
#             break

#         if board.turn == chess.WHITE:
#             difficulty = "medium"
#         else:
#             difficulty = "hard"
#         color = "white" if board.turn == chess.WHITE else "Black"
#         move = choose_ai_move(board, difficulty)
#         if move is None:
#             break
#         board.push(move)
#         print(
#             f"turn: {turn}",
#             f"  color: {color}"
#             f"   move: {move}",
#             f"  eval: {evaluate(board, chess.WHITE, 'hard'):.1f}"
#               )
#         print(board)
#         print()