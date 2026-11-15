"""FastAPI app: HTTP layer only. Chess logic lives in pgn.py / analysis.py / coach/."""

import logging
import os
import uuid
from contextlib import asynccontextmanager
from dataclasses import dataclass, field

from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware

from . import schemas
from .analysis import EngineLike, analyse_game, critical_moments
from .coach.explain import build_facts, explain_move
from .coach.llm import LLM, get_llm
from .config import settings
from .engine import Engine
from .pgn import ParsedGame, PGNError, parse_pgn

log = logging.getLogger("chessmind")


@dataclass
class GameRecord:
    parsed: ParsedGame
    analysis: dict[float, list[schemas.MoveAnalysis]] = field(default_factory=dict)
    explanations: dict[int, schemas.Explanation] = field(default_factory=dict)


_DEFAULT = object()


def create_app(
    engine: EngineLike | None = None,
    llm: "LLM | None | object" = _DEFAULT,
    language: str | None = None,
) -> FastAPI:
    """Pass `engine`/`llm` in tests; otherwise real Stockfish and the configured LLM are used."""

    @asynccontextmanager
    async def lifespan(app: FastAPI):
        owned = None
        if engine is None and settings.stockfish_path and os.path.exists(settings.stockfish_path):
            owned = Engine(settings.stockfish_path)
            app.state.engine = owned
        elif engine is None:
            log.warning("STOCKFISH_PATH not set or not found; analysis endpoints will return 503.")
        yield
        if owned:
            owned.close()

    app = FastAPI(title="ChessMind AI", version="0.1.0", lifespan=lifespan)
    app.state.engine = engine
    app.state.llm = get_llm() if llm is _DEFAULT else llm
    app.state.language = language or settings.coach_language
    app.state.games: dict[str, GameRecord] = {}  # in-memory; lost on restart (fine for MVP)
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origins,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    @app.get("/api/health", response_model=schemas.Health)
    def health(request: Request):
        return schemas.Health(
            status="ok",
            engine=request.app.state.engine is not None,
            llm_configured=request.app.state.llm is not None,
        )

    @app.post("/api/games", response_model=schemas.Game, status_code=201)
    def create_game(body: schemas.GameCreate, request: Request):
        try:
            parsed = parse_pgn(body.pgn)
        except PGNError as e:
            raise HTTPException(status_code=422, detail=str(e))
        game_id = uuid.uuid4().hex[:12]
        request.app.state.games[game_id] = GameRecord(parsed=parsed)
        return _game_out(game_id, parsed)

    @app.get("/api/games/{game_id}", response_model=schemas.Game)
    def get_game(game_id: str, request: Request):
        return _game_out(game_id, _get_record(request, game_id).parsed)

    # Sync `def` on purpose: FastAPI runs it in a worker thread, so the
    # several-second engine run doesn't block other requests.
    @app.post("/api/games/{game_id}/analyze", response_model=schemas.GameAnalysis)
    def analyze_game(game_id: str, request: Request, body: schemas.AnalyzeRequest | None = None):
        record = _get_record(request, game_id)
        limit = (body.time_limit if body and body.time_limit else None) or settings.engine_time_limit
        moves = _ensure_analysis(request, record, limit)
        return schemas.GameAnalysis(
            game_id=game_id, time_limit=limit, moves=moves, critical_moments=critical_moments(moves)
        )

    @app.post("/api/explain", response_model=schemas.Explanation)
    def explain(body: schemas.ExplainRequest, request: Request):
        record = _get_record(request, body.game_id)
        if body.ply > len(record.parsed.moves):
            raise HTTPException(status_code=422, detail=f"ply must be 1..{len(record.parsed.moves)}")
        if body.ply in record.explanations:
            return record.explanations[body.ply]

        analysis = _ensure_analysis(request, record, settings.engine_time_limit)[body.ply - 1]
        move = record.parsed.moves[body.ply - 1]
        facts = build_facts(move, analysis, _get_engine(request), settings.engine_deep_time_limit)
        text, llm_used, error = explain_move(move, facts, request.app.state.llm, request.app.state.language)
        result = schemas.Explanation(
            game_id=body.game_id, ply=body.ply, explanation=text, llm_used=llm_used, error=error, facts=facts
        )
        if llm_used:  # only cache real answers, so a later retry can succeed
            record.explanations[body.ply] = result
        return result

    return app


def _get_record(request: Request, game_id: str) -> GameRecord:
    record = request.app.state.games.get(game_id)
    if record is None:
        raise HTTPException(status_code=404, detail="Game not found. Upload it again.")
    return record


def _ensure_analysis(request: Request, record: GameRecord, limit: float) -> list[schemas.MoveAnalysis]:
    if limit not in record.analysis:
        record.analysis[limit] = analyse_game(record.parsed, _get_engine(request), limit)
    return record.analysis[limit]


def _get_engine(request: Request) -> EngineLike:
    eng = request.app.state.engine
    if eng is None:
        raise HTTPException(status_code=503, detail="Chess engine not available. Set STOCKFISH_PATH.")
    return eng


def _game_out(game_id: str, g: ParsedGame) -> schemas.Game:
    return schemas.Game(
        game_id=game_id,
        headers=g.headers,
        start_fen=g.start_fen,
        moves=[schemas.Move(**vars(m)) for m in g.moves],
    )


app = create_app()
