"""Test doubles so tests run without Stockfish or an LLM API key."""

import chess

from app.engine import Line, Score, terminal_score


class FakeEngine:
    """Returns scripted scores by FEN; otherwise 0.00 and the first legal move."""

    def __init__(self, scores: dict[str, Score] | None = None, best: dict[str, str] | None = None):
        self.scores = scores or {}
        self.best = best or {}
        self.calls = 0

    def analyse(self, board: chess.Board, time_limit: float, multipv: int = 1, root_moves=None) -> list[Line]:
        self.calls += 1
        term = terminal_score(board)
        if term is not None:
            return [Line(score=term, pv=[])]
        fen = board.fen()
        score = self.scores.get(fen, Score(cp=0))
        legal = list(board.legal_moves)
        first = chess.Move.from_uci(self.best[fen]) if fen in self.best else legal[0]
        if root_moves:
            return [Line(score=score, pv=[root_moves[0]])]
        lines = [Line(score=score, pv=[first])]
        for mv in legal[1:multipv]:
            lines.append(Line(score=Score(cp=score.cp - 30), pv=[mv]))
        return lines[:multipv]

    def close(self) -> None:
        pass
