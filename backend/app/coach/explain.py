"""Explain one move of an analysed game, grounded in Stockfish facts."""

import json

import chess

from .. import schemas
from ..analysis import EngineLike, line_to_san, to_eval
from ..pgn import MoveRecord
from .llm import LLM, LLMError
from .board_facts import describe_line, describe_move, mentioned_moves, normalize_san, piece_list
from .prompts import FIX_MOVES, explain_system


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
    # Keep the played move when it is the table's best move; otherwise the first
    # explanation line would contradict the analysis (even on a mating move).
    played = chess.Move.from_uci(move.uci)
    best = [l for l in best if l.pv[0] != played or move.uci == analysis.best_move_uci]
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


def facts_for_prompt(move: MoveRecord, facts: schemas.EngineFacts, language: str = "en") -> str:
    board = chess.Board(move.fen_before)
    board_after = chess.Board(move.fen_after)
    played = chess.Move.from_uci(move.uci)
    data = {
        "side_that_moved": move.color,
        "move_number": move.move_number,
        "pieces_before_move": piece_list(board),
        "played_move": facts.played_san,
        "played_move_description": describe_move(board, played),
        "classification": facts.classification,
        "classification_word_to_use": _TEMPLATE.get(language, _TEMPLATE["en"])["names"][facts.classification],
        "centipawns_lost": facts.cp_loss,
        "eval_before_move (White POV, pawns)": format_eval(facts.eval_before),
        "eval_after_move (White POV, pawns)": format_eval(facts.eval_after),
        "engine_best_lines_instead": [
            {
                "eval": format_eval(l.eval),
                "moves": " ".join(l.moves_san),
                "first_moves_explained": describe_line(board, l.moves_san, 2),
            }
            for l in facts.best_lines
        ],
        "engine_continuation_after_played_move": (
            {
                "moves": " ".join(facts.reply_line.moves_san),
                "first_moves_explained": describe_line(board_after, facts.reply_line.moves_san, 3),
            }
            if facts.reply_line
            else "none (game over)"
        ),
    }
    return json.dumps(data, indent=2, ensure_ascii=False)


def allowed_moves(facts: schemas.EngineFacts) -> set[str]:
    sans = [facts.played_san]
    for line in facts.best_lines:
        sans += line.moves_san
    if facts.reply_line:
        sans += facts.reply_line.moves_san
    return {normalize_san(s) for s in sans}


def invented_moves(text: str, facts: schemas.EngineFacts) -> list[str]:
    """Moves named in `text` that are not in the engine facts (sorted, for messages)."""
    return sorted(mentioned_moves(text) - allowed_moves(facts))


_TEMPLATE = {
    "ru": {
        "names": {"best": "лучший ход", "good": "хороший ход", "inaccuracy": "неточность",
                  "mistake": "ошибка", "blunder": "грубая ошибка"},
        "mate_allowed": "допускает форсированный мат",
        "lost": "потеря около {pawns} пешки",
        "head": "{move}: {cls} ({cost}). Оценка изменилась с {before} на {after}.",
        "best": " Лучший ход по движку: {move}.",
        "reply": " После {move} сильное продолжение: {line}.",
    },
    "en": {
        "names": {"best": "best", "good": "good", "inaccuracy": "inaccuracy",
                  "mistake": "mistake", "blunder": "blunder"},
        "mate_allowed": "it allows a forced mate",
        "lost": "about {pawns} pawns lost",
        "head": "{move} is classified as {cls} ({cost}). Evaluation went from {before} to {after}.",
        "best": " The engine's best move was {move}.",
        "reply": " After {move}, a strong continuation is {line}.",
    },
}


def format_eval_lang(e: schemas.Evaluation, language: str) -> str:
    if language != "ru" or e.mate is None:
        return format_eval(e)
    if e.mate == 0:
        return "мат (партия окончена)"
    return f"{'у белых' if e.mate > 0 else 'у чёрных'} мат в {abs(e.mate)}"


def template_explanation(facts: schemas.EngineFacts, language: str = "en") -> str:
    """Used when the LLM is unavailable: plain facts, no invented reasoning."""
    t = _TEMPLATE.get(language, _TEMPLATE["en"])
    after = facts.eval_after
    if after.mate and facts.classification == "blunder" and facts.eval_before.mate is None:
        cost = t["mate_allowed"]
    else:
        cost = t["lost"].format(pawns=f"{facts.cp_loss / 100:.1f}")
    text = t["head"].format(
        move=facts.played_san, cls=t["names"][facts.classification], cost=cost,
        before=format_eval_lang(facts.eval_before, language), after=format_eval_lang(after, language),
    )
    if facts.best_lines and facts.best_lines[0].moves_san:
        text += t["best"].format(move=facts.best_lines[0].moves_san[0])
    if facts.reply_line and facts.reply_line.moves_san:
        text += t["reply"].format(move=facts.played_san, line=" ".join(facts.reply_line.moves_san[:3]))
    return text


def explain_move(
    move: MoveRecord, facts: schemas.EngineFacts, llm: LLM | None, language: str = "en"
) -> tuple[str, bool, str | None]:
    """Returns (explanation, llm_used, error_message).

    The answer is checked for moves that are not in the engine facts; the model gets one
    chance to rewrite it, otherwise the fact-only template is returned.
    """
    def fallback(error: str) -> tuple[str, bool, str | None]:
        return template_explanation(facts, language), False, error

    if llm is None:
        return fallback("LLM not configured (set LLM_API_KEY).")
    messages = [
        {"role": "system", "content": explain_system(language)},
        {"role": "user", "content": "Explain this move to the player.\n\n" + facts_for_prompt(move, facts, language)},
    ]
    try:
        for attempt in range(2):
            reply = llm.chat(messages)
            if not reply.content:
                return fallback("LLM returned an empty answer.")
            bad = invented_moves(reply.content, facts)
            if not bad:
                return reply.content, True, None
            if attempt == 0:
                messages += [
                    {"role": "assistant", "content": reply.content},
                    {"role": "user", "content": FIX_MOVES.format(moves=", ".join(bad))},
                ]
    except LLMError as e:
        return fallback(str(e))
    return fallback(f"LLM mentioned moves not in the engine analysis: {', '.join(bad)}.")
