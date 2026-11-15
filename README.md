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

Run `npm.cmd install` and `npm.cmd run dev` from the repository root. Open http://localhost:5173. Vite proxies /api to localhost:8000. See the detailed frontend instructions below.

## Project documents

- [PLAN.md](PLAN.md) — milestones and status
- [DECISIONS.md](DECISIONS.md) — architecture and design decisions
- [CLAUDE.md](CLAUDE.md) — instructions for the coding agent (also used as AGENTS.md)
- [agent-logs/](agent-logs/) — key agent sessions
- REFLECTION.md — written at the end of the project

---

# ChessMind AI

Учебный шахматный интерфейс на React + TypeScript + Vite.

## Запуск

Нужен Node.js 20.19+ или 22.12+.

```sh
npm install
npm run dev
```

В PowerShell при блокировке npm.ps1 используйте `npm.cmd install` и `npm.cmd run dev`. Откройте адрес, напечатанный Vite.

## Проверка

```sh
npm run build
```

Легальные ходы, история, отмена хода, переворот доски, новая партия и копирование FEN. Превращение пешки автоматически в ферзя. Интерфейс адаптирован для телефона.

## Бэкенд

Запустите бэкенд команды на `http://localhost:8000`, затем фронтенд и откройте `http://localhost:5173`. Vite перенаправляет `/api` на бэкенд через proxy в `vite.config.ts`. Порт 5173 фиксирован. Для размещения в интернете потребуется аналогичный reverse proxy для `/api`.

Вкладка «Разбор PGN» использует контракт v0.1:

- `GET /api/health` — состояние движка.
- `POST /api/games` — загрузка PGN.
- `POST /api/games/{game_id}/analyze` — анализ всей партии с `time_limit: 0.1`.
- `POST /api/explain` — объяснение выбранного полухода.

Типы и HTTP-клиент находятся в `src/api.ts`, интерфейс разбора — в `src/Review.tsx`. Выбор хода показывает позицию после соответствующего ply; 0 — стартовая позиция. Оценка всегда со стороны белых. После 404 нужно загрузить PGN повторно. Если ИИ не настроен, показывается шаблонное объяснение сервера. Планируемый `/api/ask` пока не подключён.

Вкладка «Свободная доска» сохраняет локальные ходы и демонстрационные подсказки из `src/analysis.ts`, без обращения к серверу. API-ключи должны храниться на бэкенде.

Проверка HTTP-клиента с подставными ответами: `node --experimental-strip-types scripts/test-api.mjs`. Для проверки реального подключения нужен запущенный бэкенд.

## Быстрый запуск обеих частей из корня проекта

Первый терминал:

```powershell
.\backend\.venv\Scripts\python.exe -m uvicorn app.main:app --app-dir backend --host 127.0.0.1 --port 8000
```

Второй терминал:

```powershell
npm.cmd run dev
```

Откройте http://localhost:5173. Документация API: http://localhost:8000/docs.
В третьем терминале можно проверить настоящую интеграцию:

```powershell
node --experimental-strip-types scripts/check-integration.mjs
```

Эта проверка загружает короткую партию, запускает настоящий Stockfish, получает объяснения и проверяет ошибку неправильного PGN. Если ключ ИИ не настроен, используется шаблонное объяснение.
