# Testing and verification

Run commands from the `integration` checkout. Documentation-only `main` does not include the application or its test tools.

## Recorded checkpoint

On November 15, 2026, integration checkpoint `9a7dfce` was checked locally:

| Check | Result |
| --- | --- |
| Backend pytest suite with Stockfish configured | 42 passed |
| TypeScript and Vite production build | Passed |
| HTTP-client checks with mocked responses | Passed |
| Real backend requests through Vite proxy | Passed |
| Real LLM-provider responses | Not verified; no key configured |
| Automated browser visual/accessibility testing | Not performed |

The user also opened the application and reported that it worked. That does not replace an exhaustive browser test. The backend test run emitted one dependency deprecation warning.

## Backend tests

```powershell
cd backend
.\.venv\Scripts\python.exe -m pytest -q
```

Tests use fake engines and LLMs for deterministic checks. The real-engine test module is skipped when `STOCKFISH_PATH` is absent or invalid. The recorded 42-pass result included the real-engine tests and a new regression test for explanation consistency on a best played mating move.

## Frontend build

From the repository root:

```powershell
npm.cmd run build
```

This checks TypeScript and builds static assets. It does not prove browser layout correctness or real-provider availability.

## HTTP-client checks

```powershell
node --experimental-strip-types scripts/test-api.mjs
```

Use a Node version that supports TypeScript stripping; this command was verified with Node 26.13.1. It checks upload/analysis/explanation request payloads, fallback handling, error statuses, network failure, and score formatting using substituted HTTP responses.

## Real integration checks

Start the backend and frontend as described in [SETUP.md](SETUP.md). Then, in a third terminal:

```powershell
node --experimental-strip-types scripts/check-integration.mjs
```

The script uses the real frontend HTTP client through `http://localhost:5173/api`. It checks:

1. Engine health.
2. Upload of a four-ply game.
3. Stockfish review of all four moves.
4. Explanations for a blunder and a mating move.
5. Agreement between the best move in analysis and explanation.
6. A null continuation after checkmate.
7. HTTP 422 for an illegal PGN.

This is an HTTP integration check, not a browser automation test. With a configured LLM, explanation requests may call the provider.

## Manual checks

- Upload the example and navigate through every move.
- Return to the initial position and rotate the board.
- Run analysis and select critical moments.
- Request explanations, including the final mating move.
- Enter invalid PGN and verify the error remains readable.
- Restart the backend, then request analysis for the old game and upload again after 404.
- Check the practice board: legal moves, undo, reset, and FEN copying.
- Inspect narrow and wide browser layouts.

## Remaining validation

- Test real LLM credentials and provider responses.
- Review explanation quality against engine facts.
- Check more games, including custom start positions and special moves.
- Perform systematic browser and keyboard-accessibility checks.
- Add position-chat and AI evaluation checks when those features are implemented.
