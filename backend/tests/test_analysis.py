import chess
import pytest

from app.analysis import analyse_game, classify, critical_moments, line_to_san, mover_loss
from app.engine import MATE_CP, Score
from app.pgn import parse_pgn

from .fakes import FakeEngine


@pytest.mark.parametrize(
    "loss,expected",
    [(0, "good"), (49, "good"), (50, "inaccuracy"), (99, "inaccuracy"),
     (100, "mistake"), (199, "mistake"), (200, "blunder"), (900, "blunder")],
)
def test_classify_thresholds(loss, expected):
    assert classify(loss, played_best=False) == expected


def test_best_move_is_always_best():
    assert classify(500, played_best=True) == "best"


def test_loss_is_from_movers_point_of_view():
    # White-POV eval drops from +50 to -150: bad for White (200 lost), good for Black.
    assert mover_loss(Score(50), Score(-150), "white") == 200
    assert mover_loss(Score(50), Score(-150), "black") == 0
    # Eval rises from -100 to +200: Black lost 300.
    assert mover_loss(Score(-100), Score(200), "black") == 300


def test_clamping_ignores_winning_to_still_winning():
    assert mover_loss(Score(1500), Score(1100), "white") == 0


def test_missing_a_mate_is_a_blunder():
    loss = mover_loss(Score(MATE_CP, mate=2), Score(300), "white")
    assert classify(loss, played_best=False) == "blunder"


def test_analyse_game_finds_scripted_blunder():
    game = parse_pgn("1. e4 e5 2. Qh5 Nc6 3. Bc4 Nf6 4. Qxf7#")
    # Make Black's 3...Nf6 (ply 6) look like a blunder: before +30, after it White mates.
    fen_after_nf6 = game.moves[5].fen_after
    engine = FakeEngine(
        scores={game.moves[5].fen_before: Score(30), fen_after_nf6: Score(MATE_CP, mate=1)},
        best={game.moves[5].fen_before: "g7g6", fen_after_nf6: "h5f7"},
    )
    moves = analyse_game(game, engine, time_limit=0.01)

    assert engine.calls == len(game.moves) + 1  # each position analysed exactly once
    nf6 = moves[5]
    assert nf6.san == "Nf6" and nf6.classification == "blunder"
    assert nf6.best_move_san == "g6"
    assert nf6.eval_after.mate == 1
    # The mating move matched the engine's best move.
    assert moves[6].classification == "best" and moves[6].eval_after.mate == 0
    assert critical_moments(moves)[0] == 6


def test_line_to_san_stops_at_illegal_move():
    board = chess.Board()
    pv = [chess.Move.from_uci("e2e4"), chess.Move.from_uci("e2e4")]
    assert line_to_san(board, pv) == ["e4"]


def test_allowing_mate_is_a_blunder_even_when_already_losing():
    from app.analysis import allows_mate
    before, after = Score(-850), Score(-MATE_CP, mate=-1)
    assert allows_mate(before, after, "white")
    assert classify(mover_loss(before, after, "white"), False, allows_mate(before, after, "white")) == "blunder"
    # Black allows a mate for White:
    assert allows_mate(Score(0), Score(MATE_CP, mate=2), "black")
    # Already being mated before the move is not "allowing" it.
    assert not allows_mate(Score(-MATE_CP, mate=-3), Score(-MATE_CP, mate=-2), "white")
    # Delivering/keeping your own mate threat is fine.
    assert not allows_mate(Score(0), Score(MATE_CP, mate=2), "white")


def test_critical_moments_list_blunders_before_mistakes():
    from app import schemas
    ev = schemas.Evaluation(cp=0)
    def mk(ply, cls, loss):
        return schemas.MoveAnalysis(ply=ply, color="white", san="a3", uci="a2a3", eval_before=ev,
                                    eval_after=ev, best_move_uci=None, best_move_san=None,
                                    cp_loss=loss, classification=cls)
    moves = [mk(1, "mistake", 190), mk(2, "blunder", 150), mk(3, "good", 10), mk(4, "blunder", 400)]
    assert critical_moments(moves) == [4, 2, 1]
