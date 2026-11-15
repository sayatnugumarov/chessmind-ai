# ChessMind AI — API contract (v0.1)

Base URL (local): `http://localhost:8000`. Interactive docs with every field: `http://localhost:8000/docs`.
All requests and responses are JSON. CORS allows `http://localhost:5173` (Vite) by default
(`CORS_ORIGINS` in `backend/.env`).

## Conventions

- **ply**: 1 = White's first move, 2 = Black's first move, … `moves[i].ply == i + 1`.
- **Evaluations** are always from **White's point of view**, in centipawns (100 = one pawn).
  `{ "cp": 125, "mate": null }` = White is 1.25 pawns better.
  `{ "cp": -10000, "mate": -2 }` = Black mates in 2. `mate: 0` = the game is over by checkmate.
- **cp_loss** is from the point of view of the player who moved (always ≥ 0).
- **classification**: `best` | `good` | `inaccuracy` (≥50) | `mistake` (≥100) | `blunder` (≥200, or allowed a forced mate).
- Errors: `{"detail": "human readable message"}` with status 404 (unknown game), 422 (bad input), 503 (engine missing).

## Endpoints

### `GET /api/health`
```json
{ "status": "ok", "engine": true, "llm_configured": true }
```

### `POST /api/games` — upload a PGN (201)
Request: `{ "pgn": "1. e4 e5 2. Nf3 Nc6 ..." }`
```json
{
  "game_id": "3f9c1a2b7d4e",
  "headers": { "White": "Me", "Black": "Friend", "Result": "1-0" },
  "start_fen": "rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR w KQkq - 0 1",
  "moves": [
    { "ply": 1, "move_number": 1, "color": "white", "san": "e4", "uci": "e2e4",
      "fen_before": "rnbqkbnr/... w KQkq - 0 1", "fen_after": "rnbqkbnr/... b KQkq - 0 1" }
  ]
}
```
Invalid PGN → 422 `{"detail": "Invalid PGN: illegal san: 'Ke3' ..."}`.
Games live in server memory: after a backend restart the frontend must upload again (404).

### `GET /api/games/{game_id}` — same body as above

### `POST /api/games/{game_id}/analyze` — Stockfish review of every move
Request body optional: `{ "time_limit": 0.1 }` (seconds per position, max 2.0).
Takes roughly 0.1 s × (number of moves + 1) — **5–10 s for a typical game; show a loading state.**
Results are cached, so repeated calls are instant.
```json
{
  "game_id": "3f9c1a2b7d4e",
  "time_limit": 0.1,
  "moves": [
    { "ply": 9, "color": "white", "san": "Nxf7", "uci": "e5f7",
      "eval_before": { "cp": -63, "mate": null }, "eval_after": { "cp": -745, "mate": null },
      "best_move_uci": "c4f7", "best_move_san": "Bxf7+",
      "cp_loss": 682, "classification": "blunder" }
  ],
  "critical_moments": [9, 13, 7, 6]
}
```
`critical_moments` = plies classified mistake/blunder, blunders first, worst first.

### `POST /api/explain` — coach explanation of one move
Request: `{ "game_id": "3f9c1a2b7d4e", "ply": 9 }`. Runs the analysis first if needed.
```json
{
  "game_id": "3f9c1a2b7d4e",
  "ply": 9,
  "explanation": "Nxf7 grabs a pawn but lets Black's queen take on g2 ...",
  "llm_used": true,
  "error": null,
  "facts": {
    "fen_before": "...", "played_san": "Nxf7", "classification": "blunder", "cp_loss": 682,
    "eval_before": { "cp": -63, "mate": null }, "eval_after": { "cp": -745, "mate": null },
    "best_lines": [ { "eval": { "cp": -50, "mate": null }, "moves_san": ["Bxf7+", "Kd8", "O-O"] } ],
    "reply_line": { "eval": { "cp": -745, "mate": null }, "moves_san": ["Qxg2", "d3", "d5"] }
  }
}
```
If the LLM is down or not configured, the request still succeeds: `llm_used: false`,
`error` says why, and `explanation` is a plain template built from `facts`.
`best_lines[0]` always starts with the same `best_move_san` shown by `/analyze`.

### `POST /api/ask` — question about a position (**planned, week of Nov 17**)
Request:
```json
{ "fen": "...", "question": "Why is my knight bad here?", "game_id": "3f9c1a2b7d4e", "ply": 9,
  "history": [ { "role": "user", "content": "..." }, { "role": "assistant", "content": "..." } ],
  "mode": "tools" }
```
`ply` = position after that ply (0 = start position). `mode` = `"tools"` (coach uses chess tools)
or `"baseline"` (LLM only, for the evaluation). The client keeps the chat `history` (max 20 messages).
Response:
```json
{ "answer": "...", "mode": "tools",
  "tool_calls": [ { "name": "analyze_position", "arguments": { "fen": "..." }, "result": { } } ] }
```
