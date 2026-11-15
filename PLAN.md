# PLAN — ChessMind AI

Checkpoint: **Nov 16, 2026** (rough working end-to-end). Code freeze: **Dec 6, 2026** (tag `v1.0`).
Defense: Dec 7–19 (15 min: live demo, agent-usage discussion, questions, 2–3 min backup video).

Principle: a working end-to-end MVP beats unfinished advanced features.

## Architecture

```
React (Vite, :5173)  ──JSON/REST──▶  FastAPI (:8000)
                                       ├─ pgn.py        python-chess: parse PGN, FENs per move
                                       ├─ engine.py     one long-lived Stockfish process
                                       ├─ analysis.py   eval every position, cp loss, classification
                                       └─ coach/
                                            ├─ explain.py  engine facts -> LLM explanation (+ fallback)
                                            ├─ prompts.py
                                            ├─ tools.py    (planned) tools for /ask
                                            └─ llm.py      only module that talks to the LLM provider
```
Games are kept in memory (no database). Contract: [backend/API.md](backend/API.md).

## MVP scope

- [x] Upload and parse a PGN game — `POST /api/games`
- [x] Analyse every move with Stockfish, classify mistakes, suggest best moves — `POST /api/games/{id}/analyze`
- [x] LLM explanation of a move grounded in engine facts, with fallback — `POST /api/explain`
- [ ] Questions about a position with a tool-using coach — `POST /api/ask` (`mode=tools|baseline`)
- [ ] Frontend: board, move navigation, upload, mistake list, explanation panel, question box
- [ ] AI evaluation: dataset + script comparing tools vs. baseline
- [x] Backend tests (pytest, fake engine + fake LLM)

Postponed / stretch: voice (browser Web Speech API, frontend only), more interactive coaching,
learning features. Out of scope: database, accounts/auth, deployment, async job queues, streaming.

## Milestones

### Checkpoint — Nov 16
- [x] Backend skeleton, config via env vars, CORS
- [x] PGN parsing, Stockfish analysis, classification (benchmarked: 0.1 s/position, ~9 s for a 44-move game)
- [x] `/explain` via provider-neutral `llm.py` (Groq default)
- [x] 41 backend tests passing
- [x] README, PLAN.md, CLAUDE.md, DECISIONS.md (started), API.md, first agent log
- [x] Frontend connected to `/api/games` + `/analyze` + `/explain` (frontend team)
- [ ] Verified with a real LLM key

### Week 1 — Nov 17–23
- [ ] `/api/ask` with tool loop: `get_position`, `analyze_position`, `evaluate_move`, `get_game_context`
- [ ] `mode=baseline` (same model, no tools) for comparison
- [ ] Tests for the tool loop with a scripted fake LLM
- [ ] Support frontend integration

### Week 2 — Nov 24–30
- [ ] `eval/`: dataset format agreed with frontend team (~20–30 positions + questions)
- [ ] `eval/run_eval.py`: runs both modes, automatic metrics (legal moves mentioned, recommended move in
      Stockfish top-3, correct side judged better) + human rubric sheet
- [ ] Prompt tuning based on results; error handling (invalid input, engine/LLM failures, rate limits)

### Week 3 — Dec 1–6
- [ ] DECISIONS.md complete, REFLECTION.md, final README, 3–5 agent logs
- [ ] Demo rehearsal + backup video, fixed demo games
- [ ] Tag `v1.0`
