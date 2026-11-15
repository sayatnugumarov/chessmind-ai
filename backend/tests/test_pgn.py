import pytest

from app.pgn import PGNError, parse_pgn

SCHOLARS_MATE = """[Event "Test"]
[White "A"]
[Black "B"]
[Result "1-0"]

1. e4 e5 2. Bc4 Nc6 3. Qh5 Nf6 4. Qxf7# 1-0
"""


def test_parses_moves_and_headers():
    g = parse_pgn(SCHOLARS_MATE)
    assert g.headers["White"] == "A"
    assert [m.san for m in g.moves] == ["e4", "e5", "Bc4", "Nc6", "Qh5", "Nf6", "Qxf7#"]
    assert len(g.moves) == 7


def test_ply_color_and_move_numbers():
    g = parse_pgn(SCHOLARS_MATE)
    first, second, last = g.moves[0], g.moves[1], g.moves[-1]
    assert (first.ply, first.color, first.move_number) == (1, "white", 1)
    assert (second.ply, second.color, second.move_number) == (2, "black", 1)
    assert (last.ply, last.color, last.move_number, last.uci) == (7, "white", 4, "h5f7")


def test_fens_chain_together():
    g = parse_pgn(SCHOLARS_MATE)
    assert g.moves[0].fen_before == g.start_fen
    for prev, nxt in zip(g.moves, g.moves[1:]):
        assert prev.fen_after == nxt.fen_before


def test_moves_without_headers_work():
    g = parse_pgn("1. d4 d5 2. c4")
    assert [m.san for m in g.moves] == ["d4", "d5", "c4"]


def test_custom_start_position():
    pgn = '[SetUp "1"]\n[FEN "4k3/8/8/8/8/8/4P3/4K3 w - - 0 1"]\n\n1. e4 *'
    g = parse_pgn(pgn)
    assert g.start_fen.startswith("4k3/8/8/8/8/8/4P3/4K3 w")
    assert g.moves[0].san == "e4"


@pytest.mark.parametrize("bad", ["", "   ", "1. e4 e5 2. Ke3", "hello world"])
def test_rejects_invalid_pgn(bad):
    with pytest.raises(PGNError):
        parse_pgn(bad)
