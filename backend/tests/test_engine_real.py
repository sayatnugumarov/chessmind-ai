"""Smoke tests against the real Stockfish binary. Skipped if it isn't configured."""

import os

import chess
import pytest

from app.config import settings
from app.engine import MATE_CP, Engine

pytestmark = pytest.mark.engine

if not settings.stockfish_path or not os.path.exists(settings.stockfish_path):
    pytest.skip("STOCKFISH_PATH not set", allow_module_level=True)


@pytest.fixture(scope="module")
def engine():
    e = Engine(settings.stockfish_path)
    yield e
    e.close()


def test_finds_mate_in_one(engine):
    # White to move: Qxf7# available.
    board = chess.Board("r1bqkb1r/pppp1ppp/2n2n2/4p2Q/2B1P3/8/PPPP1PPP/RNB1K1NR w KQkq - 4 4")
    line = engine.analyse(board, 0.2)[0]
    assert line.pv[0].uci() == "h5f7"
    assert line.score.mate == 1 and line.score.cp == MATE_CP


def test_black_advantage_is_negative(engine):
    # Black is up a queen.
    board = chess.Board("4k3/8/8/8/8/8/q7/4K3 w - - 0 1")
    assert engine.analyse(board, 0.1)[0].score.cp < -500


def test_checkmated_position_scored_without_engine(engine):
    board = chess.Board("r1bqkb1r/pppp1Qpp/2n2n2/4p3/2B1P3/8/PPPP1PPP/RNB1K1NR b KQkq - 0 4")
    line = engine.analyse(board, 0.1)[0]
    assert line.score.mate == 0 and line.score.cp == MATE_CP and line.pv == []


def test_multipv_returns_several_lines(engine):
    assert len(engine.analyse(chess.Board(), 0.1, multipv=3)) == 3
