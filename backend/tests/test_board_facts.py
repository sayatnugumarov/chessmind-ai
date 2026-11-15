import chess

from app.coach.board_facts import describe_line, describe_move, mentioned_moves, normalize_san, piece_list


def test_piece_list_start_position():
    pieces = piece_list(chess.Board())
    assert pieces["white"][0] == "king e1"
    assert "queen d8" in pieces["black"]
    assert pieces["white"][-1] == "pawns: a2 b2 c2 d2 e2 f2 g2 h2"


def test_describe_fools_mate():
    board = chess.Board("rnbqkbnr/pppp1ppp/8/4p3/6P1/5P2/PPPPP2P/RNBQKBNR b KQkq g3 0 2")
    assert describe_move(board, chess.Move.from_uci("d8h4")) == "Qh4# = black queen d8->h4, check, checkmate"


def test_describe_line_castling_and_capture():
    board = chess.Board("r1bqk2r/pppp1ppp/2n2n2/2b1p3/2B1P3/5N2/PPPP1PPP/RNBQK2R w KQkq - 4 4")
    lines = describe_line(board, ["O-O", "Nxe4"])
    assert lines == ["O-O = white king e1->g1, castling", "Nxe4 = black knight f6->e4, captures pawn"]


def test_describe_line_stops_on_bad_san():
    assert describe_line(chess.Board(), ["e4", "Ke2", "Qh5"]) == ["e4 = white pawn e2->e4"]


def test_mentioned_moves_ignores_squares_and_russian_words():
    text = "Ход Nf6 был ошибкой: после Qxf7# мат. Пешка на e3 и поле f2 слабы. Лучше O-O или dxe5."
    assert mentioned_moves(text) == {"Nf6", "Qxf7", "O-O", "dxe5"}


def test_normalize_san():
    assert normalize_san("Qxf7#") == "Qxf7"
    assert normalize_san("e8=Q+") == "e8"
