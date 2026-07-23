import sys
import json
import chess
import chess.polyglot
from move_filter import filter_moves  # ML-фильтр ходов (идея из towardsdatascience.com)

#loading config
with open("config.json", "r") as f:
    raw_values = json.load(f)

piece_values = {
    chess.PAWN: raw_values["PAWN"],
    chess.KNIGHT: raw_values["KNIGHT"],
    chess.BISHOP: raw_values["BISHOP"],
    chess.ROOK: raw_values["ROOK"],
    chess.QUEEN: raw_values["QUEEN"],
    chess.KING: raw_values["KING"]
}

pst = {
    chess.PAWN: raw_values["PST"]["PAWN"],
    chess.KNIGHT: raw_values["PST"]["KNIGHT"],
    chess.BISHOP: raw_values["PST"]["BISHOP"],
    chess.ROOK: raw_values["PST"]["ROOK"],
    chess.QUEEN: raw_values["PST"]["QUEEN"],
    chess.KING: raw_values["PST"]["KING"]
}

# debute book (Polyglot)
# gm2001.bin: games GM (2001-2013, min rating 2530)
BOOK_PATH = "gm2001.bin"
try:
    _book_reader = chess.polyglot.open_reader(BOOK_PATH)
except Exception:
    _book_reader = None


def get_book_move(board: chess.Board):
    if _book_reader is None:
        return None
    try:
        entry = _book_reader.weighted_choice(board)
        return entry.move
    except (IndexError, KeyError):
        return None  #if there is no position in book


# evaluating position
def evaluated_board(board: chess.Board) -> int:
    if board.is_checkmate():
        return -9999999 if board.turn == chess.WHITE else 9999999

    score = 0
    for square in chess.SQUARES:
        piece = board.piece_at(square)
        if piece is not None:
            value = piece_values[piece.piece_type]
            if piece.color == chess.WHITE:
                positional_bonus = pst[piece.piece_type][square]
                score += (value + positional_bonus)
            else:
                positional_bonus = pst[piece.piece_type][chess.square_mirror(square)]
                score -= (value + positional_bonus)
    return score


# some stuff to make code better
def mvv_lva_score(board: chess.Board, move: chess.Move) -> int:
    if board.is_en_passant(move):
        return piece_values[chess.PAWN] * 10 - piece_values[chess.PAWN]
    victim = board.piece_at(move.to_square)
    if victim is None:
        return 0
    attacker = board.piece_at(move.from_square)
    return piece_values[victim.piece_type] * 10 - piece_values[attacker.piece_type]


def order_moves(board: chess.Board, moves: list) -> list:
    return sorted(moves, key=lambda m: mvv_lva_score(board, m), reverse=True)


#Quiescence search
MAX_QUIESCENCE_DEPTH = 6


def quiescence(board: chess.Board, alpha: float, beta: float, is_maximizing: bool, qdepth: int = 0) -> float:
    stand_pat = evaluated_board(board)

    if qdepth >= MAX_QUIESCENCE_DEPTH or board.is_game_over():
        return stand_pat

    if is_maximizing:
        if stand_pat >= beta:
            return beta
        alpha = max(alpha, stand_pat)
    else:
        if stand_pat <= alpha:
            return alpha
        beta = min(beta, stand_pat)

    captures = [m for m in board.legal_moves if board.is_capture(m)]
    captures = order_moves(board, captures)

    for move in captures:
        board.push(move)
        score = quiescence(board, alpha, beta, not is_maximizing, qdepth + 1)
        board.pop()

        if is_maximizing:
            if score >= beta:
                return beta
            alpha = max(alpha, score)
        else:
            if score <= alpha:
                return alpha
            beta = min(beta, score)

    return alpha if is_maximizing else beta


# alpha-beta search
ML_FILTER_MIN_DEPTH = 2
ML_KEEP_RATIO = 0.5


def get_candidate_moves(board, depth):
    moves = list(board.legal_moves)
    if depth > ML_FILTER_MIN_DEPTH:
        moves = filter_moves(board, moves, keep_ratio=ML_KEEP_RATIO)
    return order_moves(board, moves)


def mini_max(board, depth, alpha, beta, is_maximizing):
    if depth == 0 or board.is_game_over():
        return quiescence(board, alpha, beta, is_maximizing)

    candidate_moves = get_candidate_moves(board, depth)

    if is_maximizing:
        max_eval = -float('inf')
        for move in candidate_moves:
            board.push(move)
            eval = mini_max(board, depth - 1, alpha, beta, False)
            board.pop()
            max_eval = max(max_eval, eval)
            alpha = max(alpha, eval)
            if beta <= alpha:
                break
        return max_eval
    else:
        min_eval = float('inf')
        for move in candidate_moves:
            board.push(move)
            eval = mini_max(board, depth - 1, alpha, beta, True)
            board.pop()
            min_eval = min(min_eval, eval)
            beta = min(beta, eval)
            if beta <= alpha:
                break
        return min_eval


def get_best_move(board: chess.Board, depth: int):
    # first trying moves from book
    book_move = get_book_move(board)
    if book_move is not None:
        return book_move

    best_move = None
    is_maximizing = (board.turn == chess.WHITE)

    root_moves = get_candidate_moves(board, depth)

    if is_maximizing:
        best_score = -float('inf')
        for move in root_moves:
            board.push(move)
            score = mini_max(board, depth - 1, -float('inf'), float('inf'), False)
            board.pop()
            if score > best_score:
                best_score = score
                best_move = move
    else:
        best_score = float('inf')
        for move in root_moves:
            board.push(move)
            score = mini_max(board, depth - 1, -float('inf'), float('inf'), True)
            board.pop()
            if score < best_score:
                best_score = score
                best_move = move

    # reserve move
    if best_move is None and list(board.legal_moves):
        best_move = list(board.legal_moves)[0]

    return best_move


def uci_loop():
    board = chess.Board()
    default_depth = 10

    while True:
        try:
            line = sys.stdin.readline()
            if not line:
                break

            tokens = line.strip().split()
            if not tokens:
                continue

            command = tokens[0]

            if command == "uci":
                print("id name MyPythonEngine", flush=True)
                print("id author Bro", flush=True)
                print("uciok", flush=True)

            elif command == "isready":
                print("readyok", flush=True)

            elif command == "ucinewgame":
                board = chess.Board()
                print("readyok", flush=True)

            elif command == "position":
                board = chess.Board()
                if len(tokens) > 1 and tokens[1] == "startpos":
                    if "moves" in tokens:
                        moves_idx = tokens.index("moves")
                        for m in tokens[moves_idx + 1:]:
                            board.push_uci(m)
                elif len(tokens) > 1 and tokens[1] == "fen":
                    fen_tokens = []
                    idx = 2
                    while idx < len(tokens) and tokens[idx] != "moves":
                        fen_tokens.append(tokens[idx])
                        idx += 1
                    board.set_fen(" ".join(fen_tokens))

                    if "moves" in tokens:
                        moves_idx = tokens.index("moves")
                        for m in tokens[moves_idx + 1:]:
                            board.push_uci(m)

            elif command == "go":
                depth = default_depth
                if "depth" in tokens:
                    depth_idx = tokens.index("depth")
                    if depth_idx + 1 < len(tokens):
                        depth = int(tokens[depth_idx + 1])

                depth = min(depth, 10)

                best_move = get_best_move(board, depth)
                if best_move:
                    print(f"bestmove {best_move.uci()}", flush=True)
                else:
                    print("bestmove 0000", flush=True)

            elif command == "quit":
                break
        except Exception as e:
            with open("error_log.txt", "a") as log:
                log.write(str(e) + "\n")


if __name__ == "__main__":
    uci_loop()
