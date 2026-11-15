# Frontend and backend integration — 2026-11-15

Fetched origin/backend at dab6755 and prepared a merge into frontend without a commit.
Resolved the README conflict by preserving both teams' setup instructions.
Installed backend requirements in an ignored local virtual environment and official
Stockfish in ignored backend/.local. Created an ignored backend/.env without an LLM key.

Adjusted frontend types and rendering for nullable best moves and reply_line from schemas.py.
Real integration exposed that build_facts filtered out the played move even when it was
the engine's best move. Fixed this and added a mating-move regression test (decision D8).

Validation:
- Backend: 42 tests passed, including real Stockfish tests; one dependency deprecation warning.
- Frontend: TypeScript and production build passed after nullable field changes.
- HTTP-client mocked checks passed.
- scripts/check-integration.mjs passed against the real backend through the Vite proxy:
  upload, Stockfish review, explanations for a blunder and mate, and invalid PGN (422).
- LLM calls were not verified: no API key configured; server fallback explanations worked.
- No browser visual QA performed.

No new commit or push was made. Merge and integration changes await review/commit.
