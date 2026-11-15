# Local setup

These commands run the combined application from `integration`, not the documentation-only `main` branch. The instructions target Windows PowerShell.

## 1. Get the application

For a new checkout:

```powershell
git clone --branch integration https://github.com/sayatnugumarov/chessmind-ai.git
cd chessmind-ai
```

For an existing clean checkout:

```powershell
git fetch origin
git switch integration
git pull --ff-only origin integration
```

Save or commit any local work before switching branches.

## 2. Prerequisites

- Git.
- Node.js 20.19+ or 22.12+ for the Vite 6 toolchain; use a supported Node release.
- Python: the backend's initial instructions target 3.12; the integration tests also passed on Python 3.13.5.
- Stockfish for Windows, obtained from the [official download page](https://stockfishchess.org/download/).
- An LLM API key is optional for the first run.

Check the installed tools:

```powershell
git --version
node --version
npm.cmd --version
python --version
```

## 3. Install frontend dependencies

Run from the repository root:

```powershell
npm.cmd ci
```

Using `npm.cmd` avoids the PowerShell execution-policy error that may block `npm.ps1`.

## 4. Install backend dependencies

Run from the repository root:

```powershell
python -m venv backend/.venv
.\backend\.venv\Scripts\python.exe -m pip install -r backend/requirements.txt
```

Environment activation is unnecessary when using the virtual environment's Python executable directly.

## 5. Configure Stockfish and the optional LLM

Extract the Stockfish archive to a local folder. Locate the actual `.exe`; downloading the archive alone is insufficient.

For a fresh configuration, copy the example:

```powershell
Copy-Item backend/.env.example backend/.env
```

If `backend/.env` already exists, edit it rather than replacing it. Set `STOCKFISH_PATH` to the executable's real absolute path. Save the file as UTF-8 without a byte-order mark.

Example settings, with an illustrative executable path:

```dotenv
STOCKFISH_PATH=C:/tools/stockfish/stockfish-windows-x86-64-universal.exe
ENGINE_TIME_LIMIT=0.1
ENGINE_DEEP_TIME_LIMIT=0.5
CORS_ORIGINS=http://localhost:5173
LLM_BASE_URL=https://api.groq.com/openai/v1
LLM_MODEL=openai/gpt-oss-120b
LLM_API_KEY=
```

The executable path must match your machine. The LLM URL and model above are the backend's configured defaults, not a guarantee of provider availability or free quota. Leave the key empty for engine-based template explanations. For real LLM responses, supply your own provider configuration and restart the backend.

Keep actual API keys in `backend/.env`, which is ignored by Git. Do not put them in frontend code or commit them. The integration checkout also ignores `backend/.local/`, which can hold a local engine installation.

## 6. Start the backend

In the first terminal, from the repository root:

```powershell
.\backend\.venv\Scripts\python.exe -m uvicorn app.main:app --app-dir backend --host 127.0.0.1 --port 8000
```

Open [API documentation](http://localhost:8000/docs) or [health](http://localhost:8000/api/health). Health should report `engine: true` before attempting analysis. `llm_configured: false` is acceptable for fallback testing; `true` only indicates a configured client, not a verified provider response.

## 7. Start the frontend

Leave the backend terminal running. Open a second terminal in the repository root:

```powershell
npm.cmd run dev
```

Open [the application](http://localhost:5173/). Vite forwards `/api` requests to the backend on port 8000. Both servers must remain running. Stop each server with Ctrl+C when finished.

`localhost` means your own computer. Starting the backend on a teammate's computer does not start it on yours.

## Troubleshooting

| Symptom | Action |
| --- | --- |
| `Missing script: de` | Use the complete command `npm.cmd run dev`. |
| `npm.ps1` cannot run | Use `npm.cmd` as shown above. |
| Port 5173 is occupied | Check whether the frontend is already running; stop the duplicate process you own. Vite uses a fixed port. |
| `/docs` does not open | Check the backend terminal and confirm port 8000 is listening. |
| Health reports `engine: false` | Correct `STOCKFISH_PATH`, confirm the executable exists, and restart the backend. |
| Analysis returns 503 | Stockfish is unavailable to the server. Check configuration and backend logs. |
| A game returns 404 | Upload the PGN again; restarting the backend clears its in-memory games. |
| Upload returns 422 | Use a valid single-game PGN with legal moves. |
| Explanation is a template | Expected when no usable LLM response is available. Check `llm_used` and `error`. |

Next: [run the checks](TESTING.md) or [follow the demo](DEMO.md).
