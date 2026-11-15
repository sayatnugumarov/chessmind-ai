# ChessMind AI — Voice-Powered Chess Coach

Beginners can see *which* moves were mistakes but not *why*. ChessMind AI analyses an uploaded
PGN game with Stockfish, finds the critical mistakes, and uses an LLM coach to explain them in
plain language, grounded in the engine's actual analysis (the LLM never invents evaluations).

University final project (2 students). Backend: Python/FastAPI. Frontend: React/TypeScript.

| Part | Tech | Owner |
|---|---|---|
| Backend API, chess logic, Stockfish, AI coach, backend tests | FastAPI, python-chess, Stockfish, OpenAI-compatible LLM API (Groq) | Sayat (`backend` branch) |
| Frontend, board UI, PGN upload, voice, AI evaluation dataset | React, TypeScript | Daryn (`frontend` branch) |

Status: see [PLAN.md](PLAN.md). API contract: [backend/API.md](backend/API.md).

## Backend setup (Windows, PowerShell)

Requirements: Python 3.12, Stockfish, a free LLM API key (Groq recommended).

1. **Stockfish** — download the Windows build from https://stockfishchess.org/download/
   (or the GitHub release `stockfish-windows-x86-64-*.zip`), unzip anywhere, e.g. `C:\tools\stockfish\`.
2. **Python environment**
   ```powershell
   cd backend
   python -m venv .venv
   .venv\Scripts\python -m pip install -r requirements.txt
   ```
3. **Configuration** — copy `backend/.env.example` to `backend/.env` and set:
   - `STOCKFISH_PATH` — full path to the Stockfish `.exe`
   - `LLM_API_KEY` — key from https://console.groq.com (free). To use Gemini or OpenAI instead,
     change `LLM_BASE_URL` and `LLM_MODEL` (examples in `.env.example`).

   `.env` is git-ignored. **Never commit API keys.**
4. **Run**
   ```powershell
   .venv\Scripts\python -m uvicorn app.main:app --reload --port 8000
   ```
   Open http://localhost:8000/docs to try the endpoints.

Without an LLM key the app still works: explanations fall back to an engine-facts template.

## Tests

```powershell
cd backend
.venv\Scripts\python -m pytest -q
```
Tests use a fake engine and a fake LLM, so they need no API key. Tests in
`tests/test_engine_real.py` run against real Stockfish and are skipped if `STOCKFISH_PATH` is unset.

Engine speed check on your machine: `.venv\Scripts\python scripts\bench_engine.py`.

## Frontend setup

_To be added by the frontend team._ The frontend calls the backend at `http://localhost:8000`.

## Project documents

- [PLAN.md](PLAN.md) — milestones and status
- [DECISIONS.md](DECISIONS.md) — architecture and design decisions
- [CLAUDE.md](CLAUDE.md) — instructions for the coding agent (also used as AGENTS.md)
- [agent-logs/](agent-logs/) — key agent sessions
- REFLECTION.md — written at the end of the project
