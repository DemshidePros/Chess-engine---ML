import json
import chess

with open("config.json") as f:
    _raw = json.load(f)

PIECE_VALUES = {
    chess.PAWN: _raw["PAWN"],
    chess.KNIGHT: _raw["KNIGHT"],
    chess.BISHOP: _raw["BISHOP"],
    chess.ROOK: _raw["ROOK"],
    chess.QUEEN: _raw["QUEEN"],
    chess.KING: _raw["KING"],
}

PST = {
    chess.PAWN: _raw["PST"]["PAWN"],
    chess.KNIGHT: _raw["PST"]["KNIGHT"],
    chess.BISHOP: _raw["PST"]["BISHOP"],
    chess.ROOK: _raw["PST"]["ROOK"],
    chess.QUEEN: _raw["PST"]["QUEEN"],
    chess.KING: _raw["PST"]["KING"],
}

CENTER_SQUARES = {chess.D4, chess.D5, chess.E4, chess.E5}

FEATURE_NAMES = [
    "material_gain",   
    "pst_delta",        
    "is_capture",
    "is_check",
    "is_castle",
    "is_promotion",
    "center_distance", 
    "is_pawn",
    "is_knight",
    "is_bishop",
    "is_rook",
    "is_queen",
    "is_king",
    "gives_up_center",
]


def _center_distance(square: int) -> int:
    file_d = min(abs(chess.square_file(square) - 3), abs(chess.square_file(square) - 4))
    rank_d = min(abs(chess.square_rank(square) - 3), abs(chess.square_rank(square) - 4))
    return max(file_d, rank_d)


def extract_features(board: chess.Board, move: chess.Move) -> list:
    
    piece = board.piece_at(move.from_square)
    
    if piece is None:
        return [0.0] * len(FEATURE_NAMES)

    color = piece.color
    ptype = piece.piece_type

    # material
    captured = board.piece_at(move.to_square)
    material_gain = PIECE_VALUES[captured.piece_type] if captured else 0
    if board.is_en_passant(move):
        material_gain = PIECE_VALUES[chess.PAWN]

    # PST
    from_sq = move.from_square if color == chess.WHITE else chess.square_mirror(move.from_square)
    to_sq = move.to_square if color == chess.WHITE else chess.square_mirror(move.to_square)
    pst_delta = PST[ptype][to_sq] - PST[ptype][from_sq]

    is_capture = 1.0 if board.is_capture(move) else 0.0
    is_castle = 1.0 if board.is_castling(move) else 0.0
    is_promotion = 1.0 if move.promotion else 0.0

    board.push(move)
    is_check = 1.0 if board.is_check() else 0.0
    board.pop()

    center_distance = _center_distance(move.to_square)
    gives_up_center = 1.0 if move.from_square in CENTER_SQUARES else 0.0

    return [
        float(material_gain),
        float(pst_delta),
        is_capture,
        is_check,
        is_castle,
        is_promotion,
        float(center_distance),
        1.0 if ptype == chess.PAWN else 0.0,
        1.0 if ptype == chess.KNIGHT else 0.0,
        1.0 if ptype == chess.BISHOP else 0.0,
        1.0 if ptype == chess.ROOK else 0.0,
        1.0 if ptype == chess.QUEEN else 0.0,
        1.0 if ptype == chess.KING else 0.0,
        gives_up_center,
    ]
