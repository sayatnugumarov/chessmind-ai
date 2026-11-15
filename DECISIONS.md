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

## D8 — Preserve best played moves in explanations (2026-11-15)
Real HTTP integration with Fool's Mate exposed that filtering the played move out
of alternatives also removed it when it was the engine's best move. Keep it in
that case, so `/explain` agrees with `/analyze`, including on a mating move.
The frontend also handles nullable `reply_line` and best-move fields from schemas.py.

## D8 — Grounded, Russian coach explanations (2026-11-15)
First real run with Groq showed the explanation in English while the UI is Russian, plus geometry
errors (e.g. "g4 opens the a8–h1 diagonal", "the f-pawn is still on f2" after 1.f3).
Changes:
- `COACH_LANGUAGE` (default `ru`): prompt instructions stay in English, the answer is in Russian;
  moves keep standard English SAN (as on the board). The fallback template is translated too.
- The prompt no longer relies on the model reading FEN: python-chess lists every piece's square and
  spells out each engine move ("Qh4# = black queen d8->h4, check, checkmate"). The model is told to
  leave out geometry it cannot derive from these facts, and gets the exact word for the classification.
- Answers are checked for piece moves/captures/castling that are not in the engine facts. One rewrite
  is requested; if moves are still invented, the fact-only template is returned (`llm_used: false`).
  Quiet pawn moves ("e3") are not checked because they are indistinguishable from square names.
**Result:** on 4 test moves all answers were Russian with correct squares; no rewrite was needed.
Remaining weakness: occasional awkward wording and unverifiable strategic claims → measured in the
AI evaluation, not solved by rules.
