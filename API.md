# API reference — v0.1

Implementation: [integration/backend/app/schemas.py](https://github.com/sayatnugumarov/chessmind-ai/blob/integration/backend/app/schemas.py). Interactive schemas are available at [localhost:8000/docs](http://localhost:8000/docs) while the backend is running.

All request and response bodies are JSON. The backend base URL is `http://localhost:8000`; frontend code uses relative `/api` URLs through Vite. Default CORS origin: `http://localhost:5173`.

## Conventions

- `ply` is a half-move index: White's first move is 1, Black's first move is 2. Position navigation also uses 0 for the start, but `/explain` requires at least 1.
- `san` is standard algebraic notation, such as `Nf3`. `uci` identifies source and target squares, such as `g1f3`.
- Evaluations are White-POV: `{ "cp": 125, "mate": null }` means +1.25 pawns for White.
- A positive `mate` means White mates; a negative value means Black mates. `mate: 0` means checkmate has already occurred. Mate positions use +/-10000 in `cp`.
- `cp_loss` is nonnegative and from the mover's point of view.

## Implemented endpoints

| Method | Path | Purpose |
| --- | --- | --- |
| GET | `/api/health` | Backend, engine, and LLM configuration state |
| POST | `/api/games` | Upload one PGN game |
| GET | `/api/games/{game_id}` | Retrieve a stored game |
| POST | `/api/games/{game_id}/analyze` | Review every move with Stockfish |
| POST | `/api/explain` | Explain one move using engine facts |

### Health

```json
{ "status": "ok", "engine": true, "llm_configured": false }
```

An LLM client being configured does not prove that its key or model will work. Analysis requires `engine: true`; fallback explanations do not require an LLM key.

### Upload a game

`POST /api/games` returns HTTP 201.

```json
{ "pgn": "1. f3 e5 2. g4 Qh4# 0-1" }
```

Response fields:

| Field | Meaning |
| --- | --- |
| `game_id` | Server-generated identifier |
| `headers` | PGN headers as a string dictionary |
| `start_fen` | Starting board position |
| `moves` | Ordered list of moves |

Each move has `ply`, `move_number`, `color` (`white` or `black`), `san`, `uci`, `fen_before`, and `fen_after`. `GET /api/games/{game_id}` returns the same structure. Parsing uses the first game in the submitted PGN.

### Analyze a game

`POST /api/games/{game_id}/analyze` accepts an optional body:

```json
{ "time_limit": 0.1 }
```

`time_limit` is seconds per position, greater than 0 and at most 2.0. The response contains `game_id`, `time_limit`, `moves`, and `critical_moments`.

Each reviewed move has:

| Field | Type |
| --- | --- |
| `ply` | integer |
| `color`, `san`, `uci` | strings |
| `eval_before`, `eval_after` | `{ cp: integer, mate: integer or null }` |
| `best_move_uci`, `best_move_san` | string or null |
| `cp_loss` | nonnegative integer |
| `classification` | `best`, `good`, `inaccuracy`, `mistake`, or `blunder` |

The best engine move is classified `best`. Otherwise loss thresholds are 50, 100, and 200 centipawns for inaccuracy, mistake, and blunder. Allowing a new forced mate also produces a blunder. `critical_moments` lists mistake/blunder plies, with blunders first and larger losses first within each group.

Analysis takes roughly the per-position limit multiplied by the number of moves plus one, with additional overhead. Show a loading state; a typical game can take 5–10 seconds or longer. Results are cached per game and time limit.

### Explain a move

`POST /api/explain`:

```json
{ "game_id": "replace-with-uploaded-id", "ply": 3 }
```

The response contains `game_id`, `ply`, `explanation`, `llm_used`, `error`, and `facts`. Analysis runs first if necessary.

`facts` contains `fen_before`, `played_san`, `classification`, `cp_loss`, `eval_before`, `eval_after`, `best_lines`, and `reply_line`. Each line contains `eval` and `moves_san`.

Important nullable values:

- `reply_line` may be null, including after a mating move.
- `best_lines` may be empty. If a first line is present, it starts with the analysis table's best move.
- `error` is normally null for successful LLM output. A template fallback can return HTTP 200 with `llm_used: false` and an explanatory error string.

Only successful real LLM explanations are cached; fallback results can be retried.

## Errors

| HTTP status | Meaning | Frontend action |
| --- | --- | --- |
| 404 | Unknown game, including after a server restart | Upload PGN again |
| 422 | Invalid PGN, fields, time limit, or ply | Show validation feedback |
| 503 | Engine unavailable | Check Stockfish configuration |

Application errors generally use `{ "detail": "message" }`. FastAPI request-validation errors can use an array of validation details instead of a string.

## Planned endpoint

`POST /api/ask` is **not implemented at this checkpoint**. Request/response models exist, but the backend has no route and the frontend has no position-chat workflow. Planned inputs include FEN, a question, optional game context, client-held history of at most 20 messages, and `mode: tools | baseline`. Do not present it as an available feature.
