import json
import math
import chess
from features import extract_features

with open("move_filter_model.json") as f:
    _model = json.load(f)

_MEAN = _model["scaler_mean"]
_SCALE = _model["scaler_scale"]
_WEIGHTS = _model["weights"]
_INTERCEPT = _model["intercept"]


def _sigmoid(x):
    if x >= 0:
        z = math.exp(-x)
        return 1 / (1 + z)
    else:
        z = math.exp(x)
        return z / (1 + z)


def score_move(board: chess.Board, move: chess.Move) -> float:
    feats = extract_features(board, move)
    z = _INTERCEPT
    for f, m, s, w in zip(feats, _MEAN, _SCALE, _WEIGHTS):
        z += ((f - m) / s) * w
    return _sigmoid(z)


#filterin some moves
def filter_moves(board: chess.Board, moves: list, keep_ratio: float = 0.5, min_keep: int = 4) -> list:
    moves = list(moves)
    if len(moves) <= min_keep:
        return moves

    scored = [(m, score_move(board, m)) for m in moves]
    scored.sort(key=lambda x: -x[1])

    n_keep = max(min_keep, round(len(moves) * keep_ratio))
    kept = {m for m, _ in scored[:n_keep]}

    for m in moves:
        if board.is_capture(m) or board.gives_check(m):
            kept.add(m)

    return [m for m in moves if m in kept]
