"""PGN parsing with python-chess. No engine, no network: pure chess logic."""

import io
from dataclasses import dataclass

import chess
import chess.pgn


class PGNError(ValueError):
    """The PGN text could not be turned into a playable game."""


@dataclass
class MoveRecord:
    ply: int            # 1 = White's first move, 2 = Black's first move, ...
    move_number: int    # full-move number as written in PGN ("12." -> 12)
    color: str          # "white" or "black" (side that made the move)
    san: str            # e.g. "Nf3"
    uci: str            # e.g. "g1f3"
    fen_before: str
    fen_after: str


@dataclass
class ParsedGame:
    headers: dict[str, str]
    start_fen: str
    moves: list[MoveRecord]


def parse_pgn(text: str) -> ParsedGame:
    """Parse the first game in `text`. Raises PGNError on empty or illegal input."""
    if not text or not text.strip():
        raise PGNError("PGN is empty.")

    game = chess.pgn.read_game(io.StringIO(text))
    if game is None:
        raise PGNError("No game found in PGN.")
    if game.errors:
        # python-chess records illegal/unparseable moves here instead of raising.
        raise PGNError(f"Invalid PGN: {game.errors[0]}")

    board = game.board()
    start_fen = board.fen()
    moves: list[MoveRecord] = []
    for ply, move in enumerate(game.mainline_moves(), start=1):
        fen_before = board.fen()
        color = "white" if board.turn == chess.WHITE else "black"
        move_number = board.fullmove_number
        san = board.san(move)
        board.push(move)
        moves.append(
            MoveRecord(
                ply=ply,
                move_number=move_number,
                color=color,
                san=san,
                uci=move.uci(),
                fen_before=fen_before,
                fen_after=board.fen(),
            )
        )

    if not moves:
        raise PGNError("PGN contains no moves.")

    return ParsedGame(headers=dict(game.headers), start_fen=start_fen, moves=moves)
