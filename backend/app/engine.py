"""Thin wrapper around a Stockfish process (via python-chess).

All scores leaving this module are from WHITE's point of view.
Terminal positions (checkmate, stalemate, ...) are scored without the engine.
"""

import threading
from dataclasses import dataclass

import chess
import chess.engine

MATE_CP = 10_000  # how a forced mate is represented in "cp" fields


@dataclass
class Score:
    cp: int                 # White POV; mate mapped to +/-MATE_CP
    mate: int | None = None  # White POV moves to mate; 0 = side to move is already mated


@dataclass
class Line:
    score: Score
    pv: list[chess.Move]


def score_from_engine(pov: chess.engine.PovScore) -> Score:
    white = pov.white()
    mate = white.mate()
    if mate is not None:
        # mate > 0: White mates; mate < 0 (or -0 when Black just mated): Black mates.
        sign = 1 if mate > 0 else -1
        return Score(cp=sign * MATE_CP, mate=mate)
    return Score(cp=white.score())


def terminal_score(board: chess.Board) -> Score | None:
    """Score for positions where the game is over; None if the game continues."""
    if board.is_checkmate():
        # Side to move is mated.
        return Score(cp=-MATE_CP if board.turn == chess.WHITE else MATE_CP, mate=0)
    if board.is_game_over(claim_draw=False):
        return Score(cp=0)
    return None


class Engine:
    """One long-lived Stockfish process. A lock keeps requests from overlapping."""

    def __init__(self, path: str, threads: int = 2, hash_mb: int = 64):
        self._engine = chess.engine.SimpleEngine.popen_uci(path)
        self._engine.configure({"Threads": threads, "Hash": hash_mb})
        self._lock = threading.Lock()

    def analyse(
        self,
        board: chess.Board,
        time_limit: float,
        multipv: int = 1,
        root_moves: list[chess.Move] | None = None,
    ) -> list[Line]:
        """Top `multipv` lines. `root_moves` restricts the search to those first moves."""
        term = terminal_score(board)
        if term is not None:
            return [Line(score=term, pv=[])]
        with self._lock:
            infos = self._engine.analyse(
                board, chess.engine.Limit(time=time_limit), multipv=multipv, root_moves=root_moves
            )
        return [Line(score=score_from_engine(i["score"]), pv=i.get("pv", [])) for i in infos]

    def close(self) -> None:
        try:
            self._engine.quit()
        except chess.engine.EngineTerminatedError:
            pass
