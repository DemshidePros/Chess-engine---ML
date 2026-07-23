import chess
import chess.pgn
import random
import csv
from features import extract_features, FEATURE_NAMES

random.seed(42)

PGN_PATH = "Karpov.pgn"
OUT_CSV = "dataset.csv"
MAX_GAMES = 1000000
MIN_ELO = 2500
MAX_ROWS_PER_GAME = 40

rows = []
games_used = 0
games_seen = 0

with open(PGN_PATH) as pgn:
    while games_used < MAX_GAMES:
        game = chess.pgn.read_game(pgn)
        if game is None:
            break
        games_seen += 1

        headers = game.headers
        result = headers.get("Result", "*")
        if result not in ("1-0", "0-1"): #skipping draw game
            continue

        try:
            white_elo = int(headers.get("WhiteElo", "0"))
            black_elo = int(headers.get("BlackElo", "0"))
        except ValueError:
            continue
        if white_elo < MIN_ELO or black_elo < MIN_ELO:
            continue

        winner = chess.WHITE if result == "1-0" else chess.BLACK

        board = game.board()
        game_rows = 0
        for move in game.mainline_moves():
            if board.turn == winner and game_rows < MAX_ROWS_PER_GAME:
                legal = list(board.legal_moves)
                if len(legal) >= 2:
                    # good example
                    feats_pos = extract_features(board, move)
                    rows.append(feats_pos + [1])

                    # bad example
                    other_moves = [m for m in legal if m != move]
                    neg_move = random.choice(other_moves)
                    feats_neg = extract_features(board, neg_move)
                    rows.append(feats_neg + [0])

                    game_rows += 1
            board.push(move)

        games_used += 1
        if games_used % 2000 == 0:
            print(f"games processed: {games_used}, rows in dataset: {len(rows)}")

print(f"Total games reviewed-{games_seen}, used={games_used}, rows={len(rows)}")

with open(OUT_CSV, "w", newline="") as f:
    writer = csv.writer(f)
    writer.writerow(FEATURE_NAMES + ["label"])
    writer.writerows(rows)

print("Saved in", OUT_CSV)
