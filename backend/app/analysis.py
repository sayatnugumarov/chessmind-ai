"""Game analysis: evaluate every position once and classify each move.

Method: for N moves we analyse the N+1 positions of the game.
  eval_before(move k) = engine eval of the position before move k (best play)
  eval_after(move k)  = engine eval of the position after move k
  cp_loss = how much the evaluation dropped for the side that moved.
Evaluations are clamped to +/-CLAMP_CP before computing the loss, so
"+15 vs +11" (both completely winning) does not count as a blunder,
while missing a forced mate (+mate -> +3) still does.
"""

from typing import Protocol

import chess

from . import schemas
from .engine import Line, Score
from .pgn import ParsedGame

CLAMP_CP = 1000

# cp_loss thresholds (lower bound inclusive) — similar to common chess sites.
INACCURACY = 50
MISTAKE = 100
BLUNDER = 200


class EngineLike(Protocol):
    def analyse(
        self, board: chess.Board, time_limit: float, multipv: int = 1, root_moves: list[chess.Move] | None = None
    ) -> list[Line]: ...


def clamp(cp: int) -> int:
    return max(-CLAMP_CP, min(CLAMP_CP, cp))


def mover_loss(before: Score, after: Score, color: str) -> int:
    """Centipawns lost by the side that moved (never negative)."""
    sign = 1 if color == "white" else -1
    loss = sign * (clamp(before.cp) - clamp(after.cp))
    return max(0, loss)


def allows_mate(before: Score, after: Score, color: str) -> bool:
    """True if after the move the opponent has a forced mate that didn't exist before."""
    sign = 1 if color == "white" else -1

    def mated(s: Score) -> bool:  # the mover is getting mated in this evaluation
        return s.mate is not None and sign * s.cp < 0

    return mated(after) and not mated(before)


def classify(cp_loss: int, played_best: bool, allowed_mate: bool = False) -> str:
    if played_best:
        return "best"
    if allowed_mate or cp_loss >= BLUNDER:
        return "blunder"
    if cp_loss >= MISTAKE:
        return "mistake"
    if cp_loss >= INACCURACY:
        return "inaccuracy"
    return "good"


def to_eval(s: Score) -> schemas.Evaluation:
    return schemas.Evaluation(cp=s.cp, mate=s.mate)


def analyse_game(game: ParsedGame, engine: EngineLike, time_limit: float) -> list[schemas.MoveAnalysis]:
    fens = [m.fen_before for m in game.moves] + [game.moves[-1].fen_after]
    lines = [engine.analyse(chess.Board(f), time_limit)[0] for f in fens]

    result = []
    for k, move in enumerate(game.moves):
        before, after = lines[k], lines[k + 1]
        board = chess.Board(move.fen_before)
        best = before.pv[0] if before.pv else None
        played_best = best is not None and best.uci() == move.uci
        loss = 0 if played_best else mover_loss(before.score, after.score, move.color)
        result.append(
            schemas.MoveAnalysis(
                ply=move.ply,
                color=move.color,
                san=move.san,
                uci=move.uci,
                eval_before=to_eval(before.score),
                eval_after=to_eval(after.score),
                best_move_uci=best.uci() if best else None,
                best_move_san=board.san(best) if best else None,
                cp_loss=loss,
                classification=classify(
                    loss, played_best, allows_mate(before.score, after.score, move.color)
                ),
            )
        )
    return result


def critical_moments(moves: list[schemas.MoveAnalysis]) -> list[int]:
    bad = [m for m in moves if m.classification in ("mistake", "blunder")]
    # Blunders first, then mistakes; within each, biggest loss first.
    return [m.ply for m in sorted(bad, key=lambda m: (m.classification != "blunder", -m.cp_loss))]


def line_to_san(board: chess.Board, pv: list[chess.Move], max_moves: int = 6) -> list[str]:
    """Convert an engine PV to SAN, stopping at the first illegal move (defensive)."""
    b = board.copy()
    out = []
    for mv in pv[:max_moves]:
        if mv not in b.legal_moves:
            break
        out.append(b.san(mv))
        b.push(mv)
    return out
