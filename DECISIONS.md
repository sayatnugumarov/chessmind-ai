# DECISIONS

Short records of important choices: what, why, and alternatives considered.

## D1 — Small monolithic FastAPI backend, in-memory storage (2026-11-15)
Single FastAPI app; uploaded games and analyses stored in a Python dict. No database, auth or job queue.
**Why:** 3 weeks to code freeze, local-only demo; nothing needs to survive a restart.
**Trade-off:** restarting the server forgets games (frontend re-uploads on 404).

## D2 — REST/JSON contract defined by Pydantic schemas (2026-11-15)
`backend/app/schemas.py` + `backend/API.md` + auto-generated `/docs`. Client holds chat history for `/ask`.
**Why:** lets the frontend work independently; stateless questions are simpler than server sessions.
**Rejected:** WebSockets/streaming (not needed for MVP).

## D3 — LLM provider: Groq via the OpenAI-compatible API, isolated in `llm.py` (2026-11-15)
Default `openai/gpt-oss-120b` on Groq; Gemini (AI Studio) as backup by changing `.env` only.
**Why:** free tier with ~1,000 requests/day covers development and repeated evaluation runs; supports
tool calling; very fast. Gemini Flash's free quota was reported as low as ~20 requests/day; OpenRouter
free models are limited to 50/day and their tool support varies by model.
**Consequence:** answer quality relies on grounding the model in engine facts, not on model strength.

## D4 — Engine time limit 0.1 s per position for full-game analysis (2026-11-15)
Benchmark (`scripts/bench_engine.py`, i3-1215U, 2 threads, 88 positions):

| time/position | total | best-move agreement vs 0.5 s |
|---|---|---|
| 0.05 s | 4.6 s | 81% |
| 0.1 s | 8.9 s | 86% |
| 0.2 s | 17.8 s | 82% |
| 0.5 s | 44.2 s | 100% (reference) |

Agreement plateaus (differences are mostly between near-equal moves), so 0.1 s gives acceptable
quality at ~6–9 s per game. Single-position requests (`/explain`, `/ask`) use 0.5 s with MultiPV 3.
Each position is analysed once: the eval after move k is the eval before move k+1.

## D5 — Move classification (2026-11-15)
`cp_loss` = drop in the mover's evaluation, with evaluations clamped to ±1000 cp first
(so "+15 → +11" is not a blunder). Thresholds: inaccuracy ≥ 50, mistake ≥ 100, blunder ≥ 200.
Playing the engine's best move is always `best`. **Allowing a forced mate is always a blunder**, even when
already losing (found during testing: 7.Be2 allowing mate-in-1 was only a "mistake" due to clamping).

## D6 — Explanations stay consistent with the analysis table (2026-11-15)
The deeper `/explain` search sometimes preferred a different (near-equal) move than the 0.1 s analysis,
so the user saw "best: Bxf7+" in the list but "engine preferred O-O" in the explanation. Now the move
shown by `/analyze` is always the first line in the explanation facts (searched with `root_moves` if needed).

## D7 — Graceful LLM failure (2026-11-15)
If the LLM is unconfigured, rate-limited or fails, `/explain` returns a template built from engine
facts with `llm_used: false` and an `error` message. Failed answers are not cached, so retries work.
**Why:** a free-tier rate limit must not break the live demo.
