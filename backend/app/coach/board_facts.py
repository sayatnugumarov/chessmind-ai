"""Exact, python-chess-derived descriptions of a position and of moves.

LLMs are unreliable at reading FEN, so instead of making the model work out where pieces
stand, we spell it out. Everything here is computed, never guessed.
"""

import re

import chess

PIECE_NAMES = {
    chess.PAWN: "pawn", chess.KNIGHT: "knight", chess.BISHOP: "bishop",
    chess.ROOK: "rook", chess.QUEEN: "queen", chess.KING: "king",
}


def color_name(color: chess.Color) -> str:
    return "white" if color == chess.WHITE else "black"


def piece_list(board: chess.Board) -> dict[str, list[str]]:
    """{"white": ["king e1", "queen d1", ..., "pawns: a2 b2 ..."], "black": [...]}"""
    out = {}
    for color in (chess.WHITE, chess.BLACK):
        items = []
        for pt in (chess.KING, chess.QUEEN, chess.ROOK, chess.BISHOP, chess.KNIGHT):
            for sq in sorted(board.pieces(pt, color)):
                items.append(f"{PIECE_NAMES[pt]} {chess.square_name(sq)}")
        pawns = sorted(board.pieces(chess.PAWN, color))
        if pawns:
            items.append("pawns: " + " ".join(chess.square_name(s) for s in pawns))
        out[color_name(color)] = items
    return out


def describe_move(board: chess.Board, move: chess.Move) -> str:
    """'Qh4# = black queen d8->h4, check, checkmate' for a legal move on `board` (not modified)."""
    piece = board.piece_at(move.from_square)
    parts = [
        f"{board.san(move)} = {color_name(piece.color)} {PIECE_NAMES[piece.piece_type]} "
        f"{chess.square_name(move.from_square)}->{chess.square_name(move.to_square)}"
    ]
    if board.is_castling(move):
        parts.append("castling")
    if board.is_capture(move):
        if board.is_en_passant(move):
            parts.append("captures pawn en passant")
        else:
            captured = board.piece_at(move.to_square)
            parts.append(f"captures {PIECE_NAMES[captured.piece_type]}")
    if move.promotion:
        parts.append(f"promotes to {PIECE_NAMES[move.promotion]}")
    after = board.copy(stack=False)
    after.push(move)
    if after.is_checkmate():
        parts.append("check, checkmate")
    elif after.is_check():
        parts.append("check")
    return ", ".join(parts)


def describe_line(board: chess.Board, sans: list[str], max_moves: int = 4) -> list[str]:
    """Describe the first moves of a SAN line starting from `board`."""
    b = board.copy(stack=False)
    out = []
    for san in sans[:max_moves]:
        try:
            mv = b.parse_san(san)
        except ValueError:
            break
        out.append(describe_move(b, mv))
        b.push(mv)
    return out


# Piece moves, piece/pawn captures and castling in English SAN. Quiet pawn moves ("e3")
# are skipped because they look exactly like square names ("the pawn on e3").
_SAN_RE = re.compile(
    r"(?<![A-Za-z0-9])(O-O-O|O-O|[KQRBN][a-h]?[1-8]?x?[a-h][1-8]|[a-h]x[a-h][1-8])(?:=[QRBN])?[+#]?(?![a-z0-9])"
)


def mentioned_moves(text: str) -> set[str]:
    """SAN-looking moves in free text, without check/mate suffixes."""
    return {m.group(1) for m in _SAN_RE.finditer(text)}


def normalize_san(san: str) -> str:
    return re.sub(r"(=[QRBN])?[+#]$", "", san).split("=")[0]
