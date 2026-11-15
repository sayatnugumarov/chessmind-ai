# Team workflow

## Ownership

| Area | Primary owner |
| --- | --- |
| React frontend, board UI, PGN workflow | Daryn |
| FastAPI, chess logic, Stockfish, coach | Sayat |
| API contract and integration | Both team members |

Coordinate changes that affect the other member's work, especially request/response fields.

## Branch policy

- `frontend`: frontend development.
- `backend`: backend development.
- `integration`: combine and check both parts without changing the development branches.
- `main`: project documentation at this checkpoint. Application promotion to `main` is a separate team decision.

The combined checkpoint was pushed as `integration` without moving `frontend`, `backend`, or `main` to its application commit. Later documentation updates to `main` do not merge the application code.

Before publishing work, inspect what will be committed:

```powershell
git status
git diff
git diff --cached
```

Commit only intended files. Use descriptive commit messages and pull requests for changes that need teammate review. Avoid force pushes to shared branches.

## Integrating changes

Fetch the latest branches and perform merges in `integration`. Resolve documentation conflicts by preserving accurate setup instructions for both components. Run the applicable checks in [TESTING.md](TESTING.md) before pushing the combined application.

Do not assume that a successful merge means the application works. Exercise upload, analysis, and explanation against the real engine.

## Configuration and generated files

The application checkout ignores `node_modules/`, `dist/`, virtual environments, `backend/.local/`, and real environment files. Commit lockfiles and configuration examples; do not commit dependency folders, downloaded engine binaries, or API keys.

If you change environment settings, update `backend/.env.example` without adding secrets. If you change API fields, update the Pydantic models, API documentation, frontend types, and affected checks together.

## Documentation

Describe implemented behavior separately from future work. Record test results with their scope and date. Keep real-provider testing distinct from fake-client or template testing. Update [PLAN.md](PLAN.md) and [DECISIONS.md](DECISIONS.md) when scope or architecture changes.

Documentation in `main` describes the linked integration checkpoint. When application code changes, review these documents for drift.
