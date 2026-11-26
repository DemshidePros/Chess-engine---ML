"""Play a game against the engine in the terminal.

Usage:
    python play.py                 # you play White, engine depth 3
    python play.py --black         # you play Black
    python play.py --depth 4       # stronger (slower) engine

Enter moves in SAN (e4, Nf3, O-O) or UCI (e2e4). Commands: 'undo', 'resign', 'quit'.
"""
import argparse
import time

import chess

import engine


def print_board(board: chess.Board, player_is_white: bool) -> None:
    print()
    print(board.unicode(borders=True, orientation=chess.WHITE if player_is_white else chess.BLACK))
    print()


def read_human_move(board: chess.Board):
    while True:
        text = input("Your move> ").strip()
        if not text:
            continue
        low = text.lower()
        if low in ("quit", "exit", "resign"):
            return low
        if low == "undo":
            return "undo"
        try:
            return board.parse_san(text)
        except ValueError:
            pass
        try:
            move = chess.Move.from_uci(text)
            if move in board.legal_moves:
                return move
        except ValueError:
            pass
        print("Illegal or unrecognized move, try again.")


def main() -> None:
    parser = argparse.ArgumentParser(description="Play chess against the engine in the terminal.")
    parser.add_argument("--black", action="store_true", help="play as Black")
    parser.add_argument("--depth", type=int, default=3, help="search depth for the engine (default 3, max 10)")
    args = parser.parse_args()

    depth = max(1, min(args.depth, 10))
    human_color = chess.BLACK if args.black else chess.WHITE
    board = chess.Board()

    print(f"You are {'Black' if args.black else 'White'}. Engine depth: {depth}.")
    print("Type moves like e4, Nf3, O-O or e2e4. Commands: undo, resign, quit.")

    while not board.is_game_over():
        print_board(board, human_color == chess.WHITE)

        if board.turn == human_color:
            move = read_human_move(board)
            if move in ("quit", "exit"):
                print("Game aborted.")
                return
            if move == "resign":
                print("You resigned.")
                return
            if move == "undo":
                # undo the engine's move and the human's previous move
                for _ in range(2 if len(board.move_stack) >= 2 else len(board.move_stack)):
                    board.pop()
                continue
            board.push(move)
        else:
            print("Engine is thinking...")
            start = time.time()
            move = engine.get_best_move(board, depth)
            elapsed = time.time() - start
            if move is None:
                print("Engine has no move.")
                break
            print(f"Engine plays {board.san(move)}  ({elapsed:.1f}s)")
            board.push(move)

    print_board(board, human_color == chess.WHITE)
    print("Result:", board.result(claim_draw=True), "-", describe_outcome(board))


def describe_outcome(board: chess.Board) -> str:
    outcome = board.outcome(claim_draw=True)
    if outcome is None:
        return "game not finished"
    if outcome.winner is None:
        return f"draw ({outcome.termination.name.lower().replace('_', ' ')})"
    winner = "White" if outcome.winner == chess.WHITE else "Black"
    return f"{winner} wins by {outcome.termination.name.lower().replace('_', ' ')}"


if __name__ == "__main__":
    main()
