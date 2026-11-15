# ChessMind AI

A university project that helps chess learners understand their mistakes. Upload a PGN game, review Stockfish evaluations, and request an explanation of a selected move.

**Working application:** [integration branch](https://github.com/sayatnugumarov/chessmind-ai/tree/integration).
**This branch (`main`) contains the project documentation.** Switch to `integration` before following installation or test commands. The application has not been merged into `main`.

## Current checkpoint

As of November 15, 2026:

- React/TypeScript frontend and FastAPI backend are connected.
- PGN upload, move navigation, Stockfish review, critical moments, and template explanations have been checked together.
- All 42 backend tests passed locally, including real Stockfish tests.
- The frontend production build and HTTP-client checks passed.
- Real-provider LLM responses have not yet been verified in the integration environment.
- Position chat, voice input, and the AI evaluation dataset are future work.

The interface currently uses Russian labels. This documentation is in English.

## What the application does

1. Accepts a single PGN game.
2. Displays the position after each selected move.
3. Uses Stockfish to evaluate moves and classify mistakes.
4. Shows the engine's best move and critical moments.
5. Requests a coach explanation grounded in engine facts. If the LLM is unavailable, the server returns a factual template.

A separate practice board supports legal moves, undo, board rotation, and FEN copying. Its local hints are demonstrations, not engine analysis.

## Branches

| Branch | Purpose |
| --- | --- |
| `main` | English project documentation |
| `frontend` | Frontend development |
| `backend` | Backend development |
| `integration` | Combined application used for local testing and demonstrations |

The integration checkpoint is commit `9a7dfce`. Changes made during integration, including the explanation consistency fix, are in `integration`; the separate development branches were preserved.

## Start here

```powershell
git clone --branch integration https://github.com/sayatnugumarov/chessmind-ai.git
cd chessmind-ai
```

Follow [SETUP.md](SETUP.md) to install dependencies, configure Stockfish, and start both servers. A checkout of `integration` has its own README; this documentation set can also be read on GitHub in `main`.

## Documentation

| Document | Contents |
| --- | --- |
| [SETUP.md](SETUP.md) | Windows installation, configuration, and troubleshooting |
| [ARCHITECTURE.md](ARCHITECTURE.md) | Components, data flow, and storage |
| [API.md](API.md) | Implemented requests, response fields, and error handling |
| [TESTING.md](TESTING.md) | Automated checks and known verification limits |
| [DEMO.md](DEMO.md) | A repeatable demonstration walkthrough |
| [CONTRIBUTING.md](CONTRIBUTING.md) | Team ownership and branch workflow |
| [PLAN.md](PLAN.md) | Completed work and remaining milestones |
| [DECISIONS.md](DECISIONS.md) | Technical choices and trade-offs |
| [REFLECTION.md](REFLECTION.md) | Checkpoint observations and remaining evidence |

## Team

| Member | Primary responsibility |
| --- | --- |
| Daryn | Frontend, board UI, PGN workflow, and planned evaluation contributions |
| Sayat | Backend, chess logic, Stockfish integration, and AI coach |

## Technology

React, TypeScript, Vite, chess.js, FastAPI, python-chess, Stockfish, and an optional OpenAI-compatible LLM provider. There is no database or deployed public service at this checkpoint.
