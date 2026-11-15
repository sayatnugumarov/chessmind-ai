"""Request/response models. This file IS the frontend-backend contract.

FastAPI turns these into the OpenAPI schema at http://localhost:8000/docs.
Conventions:
  * ply: 1 = White's first move, 2 = Black's first move, ...
  * Evaluations are always from WHITE's point of view, in centipawns
    (100 = one pawn). Positive = White is better.
  * cp_loss is from the point of view of the side that made the move (>= 0).
"""

from typing import Literal

from pydantic import BaseModel, Field

Color = Literal["white", "black"]
Classification = Literal["best", "good", "inaccuracy", "mistake", "blunder"]


# ---------- games ----------

class GameCreate(BaseModel):
    pgn: str = Field(..., description="PGN text of a single game.")


class Move(BaseModel):
    ply: int
    move_number: int
    color: Color
    san: str
    uci: str
    fen_before: str
    fen_after: str


class Game(BaseModel):
    game_id: str
    headers: dict[str, str]
    start_fen: str
    moves: list[Move]


# ---------- analysis ----------

class Evaluation(BaseModel):
    cp: int = Field(..., description="White-POV centipawns. Forced mate is mapped to +/-10000.")
    mate: int | None = Field(
        None, description="Moves to mate, White POV (+3 = White mates in 3). Null if no mate."
    )


class MoveAnalysis(BaseModel):
    ply: int
    color: Color
    san: str
    uci: str
    eval_before: Evaluation
    eval_after: Evaluation
    best_move_uci: str | None
    best_move_san: str | None
    cp_loss: int
    classification: Classification


class GameAnalysis(BaseModel):
    game_id: str
    time_limit: float = Field(..., description="Engine seconds per position used.")
    moves: list[MoveAnalysis]
    critical_moments: list[int] = Field(
        ..., description="Plies classified as mistake or blunder, worst first."
    )


class AnalyzeRequest(BaseModel):
    time_limit: float | None = Field(
        None, gt=0, le=2.0, description="Override engine seconds per position."
    )


# ---------- coach ----------

class ExplainRequest(BaseModel):
    game_id: str
    ply: int = Field(..., ge=1)


class EngineLine(BaseModel):
    eval: Evaluation
    moves_san: list[str]


class EngineFacts(BaseModel):
    fen_before: str
    played_san: str
    classification: Classification
    cp_loss: int
    eval_before: Evaluation
    eval_after: Evaluation
    best_lines: list[EngineLine] = Field(..., description="Top engine lines before the move.")
    reply_line: EngineLine | None = Field(
        None, description="Engine's best continuation after the played move."
    )


class Explanation(BaseModel):
    game_id: str
    ply: int
    explanation: str
    llm_used: bool = Field(..., description="False if the LLM failed and a template was used.")
    error: str | None = None
    facts: EngineFacts


class ChatMessage(BaseModel):
    role: Literal["user", "assistant"]
    content: str


class AskRequest(BaseModel):
    fen: str
    question: str = Field(..., min_length=1, max_length=1000)
    game_id: str | None = None
    ply: int | None = Field(None, ge=0, description="Position after this ply (0 = start).")
    history: list[ChatMessage] = Field(default_factory=list, max_length=20)
    mode: Literal["tools", "baseline"] = "tools"


class ToolCall(BaseModel):
    name: str
    arguments: dict
    result: dict


class AskResponse(BaseModel):
    answer: str
    mode: Literal["tools", "baseline"]
    tool_calls: list[ToolCall]


class Health(BaseModel):
    status: Literal["ok"]
    engine: bool
    llm_configured: bool
