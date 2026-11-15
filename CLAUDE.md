# CLAUDE.md / AGENTS.md — instructions for coding agents

ChessMind AI: upload a PGN game, Stockfish finds mistakes, an LLM coach explains them.
Read [PLAN.md](PLAN.md) for scope and status and [backend/API.md](backend/API.md) for the API contract.

## Team and branches
- `backend` branch: FastAPI backend in `backend/` (Sayat).
- `frontend` branch: React/TypeScript app (Daryn). **Do not modify frontend files from the backend
  branch** unless both agree.
- Commit or push only when asked.

## Commands (run from `backend/`)
- Tests: `.venv/Scripts/python -m pytest -q` — must pass before finishing any task.
- Run server: `.venv/Scripts/python -m uvicorn app.main:app --reload --port 8000`
- Engine benchmark: `.venv/Scripts/python scripts/bench_engine.py`

## Rules
- **No secrets in git.** Keys live in `backend/.env` (git-ignored); document new settings in `.env.example`.
- **The LLM explains, it does not evaluate.** Evaluations, best moves and legality come from Stockfish
  and python-chess. Every prompt passes engine facts; never let the model invent evaluations.
- Only `app/coach/llm.py` may import the provider SDK (`openai`, OpenAI-compatible API).
- Evaluations are White-POV centipawns everywhere; `cp_loss` is mover-POV. Mate = ±10000 with a `mate` field.
- `app/schemas.py` is the frontend contract. Changing a field means updating `backend/API.md` and
  telling the frontend team.
- Tests must not need network or an API key: use `tests/fakes.py` (`FakeEngine`) and fake LLMs.
  Real-Stockfish tests go in `tests/test_engine_real.py` (auto-skipped without `STOCKFISH_PATH`).
- Keep it simple: no database, auth, queues or new frameworks without a recorded decision in DECISIONS.md.
- Work in small steps: explain, change, run tests, report. Don't start the next task while tests fail.
- After significant work, update PLAN.md checkboxes and DECISIONS.md, and add notable sessions to `agent-logs/`.
