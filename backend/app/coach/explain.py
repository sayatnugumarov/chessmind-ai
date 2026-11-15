"""Explain one move of an analysed game, grounded in Stockfish facts."""

import json

import chess

from .. import schemas
from ..analysis import EngineLike, line_to_san, to_eval
from ..pgn import MoveRecord
from .llm import LLM, LLMError
from .prompts import EXPLAIN_SYSTEM


def format_eval(e: schemas.Evaluation) -> str:
    """Human-readable eval, White POV: '+1.25', '-0.40', 'White mates in 3'."""
    if e.mate is not None:
        if e.mate == 0:
            return "checkmate (game over)"
        side = "White" if e.mate > 0 else "Black"
        return f"{side} mates in {abs(e.mate)}"
    return f"{e.cp / 100:+.2f}"


def build_facts(
    move: MoveRecord, analysis: schemas.MoveAnalysis, engine: EngineLike, time_limit: float
) -> schemas.EngineFacts:
    board_before = chess.Board(move.fen_before)
    best = [l for l in engine.analyse(board_before, time_limit, multipv=3) if l.pv]
    # Keep the explanation consistent with the analysis table: the move shown there
    # as "best" must be the first line here, even if the deeper search ranks another
    # (roughly equal) move higher.
    if analysis.best_move_uci:
        shown = chess.Move.from_uci(analysis.best_move_uci)
        match = [l for l in best if l.pv[0] == shown]
        if not match:
            match = engine.analyse(board_before, time_limit, root_moves=[shown])
        best = match[:1] + [l for l in best if l.pv[0] != shown][:2]
    # "Alternatives" should not include the move that was actually played.
    played = chess.Move.from_uci(move.uci)
    best = [l for l in best if l.pv[0] != played]
    best_lines = [
        schemas.EngineLine(eval=to_eval(l.score), moves_san=line_to_san(board_before, l.pv))
        for l in best
    ]
    board_after = chess.Board(move.fen_after)
    reply = engine.analyse(board_after, time_limit)[0]
    reply_line = (
        schemas.EngineLine(eval=to_eval(reply.score), moves_san=line_to_san(board_after, reply.pv))
        if reply.pv
        else None
    )
    return schemas.EngineFacts(
        fen_before=move.fen_before,
        played_san=move.san,
        classification=analysis.classification,
        cp_loss=analysis.cp_loss,
        eval_before=analysis.eval_before,
        eval_after=analysis.eval_after,
        best_lines=best_lines,
        reply_line=reply_line,
    )


def facts_for_prompt(move: MoveRecord, facts: schemas.EngineFacts) -> str:
    board = chess.Board(move.fen_before)
    played = chess.Move.from_uci(move.uci)
    data = {
        "position_fen": facts.fen_before,
        "side_to_move": move.color,
        "move_number": move.move_number,
        "played_move": facts.played_san,
        "played_move_is_capture": board.is_capture(played),
        "played_move_gives_check": board.gives_check(played),
        "classification": facts.classification,
        "centipawns_lost": facts.cp_loss,
        "eval_before_move (White POV, pawns)": format_eval(facts.eval_before),
        "eval_after_move (White POV, pawns)": format_eval(facts.eval_after),
        "engine_best_lines_instead": [
            {"eval": format_eval(l.eval), "moves": " ".join(l.moves_san)} for l in facts.best_lines
        ],
        "engine_continuation_after_played_move": (
            " ".join(facts.reply_line.moves_san) if facts.reply_line else "none (game over)"
        ),
    }
    return json.dumps(data, indent=2)


def template_explanation(facts: schemas.EngineFacts) -> str:
    """Used when the LLM is unavailable: plain facts, no invented reasoning."""
    after = facts.eval_after
    if after.mate and facts.classification == "blunder" and facts.eval_before.mate is None:
        cost = "it allows a forced mate"
    else:
        cost = f"about {facts.cp_loss / 100:.1f} pawns lost"
    text = (
        f"{facts.played_san} is classified as {facts.classification} ({cost}). "
        f"Evaluation went from {format_eval(facts.eval_before)} to {format_eval(after)}."
    )
    if facts.best_lines and facts.best_lines[0].moves_san:
        text += f" The engine preferred {facts.best_lines[0].moves_san[0]}."
    if facts.reply_line and facts.reply_line.moves_san:
        text += f" After {facts.played_san}, a strong continuation is {' '.join(facts.reply_line.moves_san[:3])}."
    return text


def explain_move(
    move: MoveRecord, facts: schemas.EngineFacts, llm: LLM | None
) -> tuple[str, bool, str | None]:
    """Returns (explanation, llm_used, error_message)."""
    if llm is None:
        return template_explanation(facts), False, "LLM not configured (set LLM_API_KEY)."
    messages = [
        {"role": "system", "content": EXPLAIN_SYSTEM},
        {"role": "user", "content": "Explain this move to the player.\n\n" + facts_for_prompt(move, facts)},
    ]
    try:
        reply = llm.chat(messages)
    except LLMError as e:
        return template_explanation(facts), False, str(e)
    if not reply.content:
        return template_explanation(facts), False, "LLM returned an empty answer."
    return reply.content, True, None
