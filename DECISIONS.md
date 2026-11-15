# Technical decisions

This summary records choices visible in integration checkpoint `9a7dfce`. It does not assert current provider pricing, quotas, or model availability.

## 1. Separate frontend, backend, and integration branches

Keep each member's development branch intact and combine work in `integration`. Use `main` for English project documentation until the team decides to promote application code.

This makes it possible to demonstrate the whole application without moving the independent branches.

## 2. Small FastAPI backend with in-memory storage

One application stores games and analysis caches in memory. This limits setup work for a local university MVP.

Trade-off: a backend restart forgets uploaded games. The frontend handles 404 by requiring another upload. There is no durable history or account system.

## 3. REST and typed schemas

FastAPI/Pydantic defines the server contract; TypeScript describes client responses. Vite proxies relative `/api` requests during development.

Trade-off: schema drift is possible. During integration, the real models exposed nullable fields that needed corresponding frontend updates. Documentation and client types must follow the implementation.

## 4. Stockfish as the source of chess evaluations

Stockfish supplies evaluations, best moves, and continuations. python-chess supplies backend move legality and PGN parsing; chess.js supplies practice-board legality.

The LLM receives engine facts to explain. It should not invent scores or independently decide legal moves.

## 5. Limited engine search for interactive review

The default full-game search limit is 0.1 seconds per position; deeper explanation searches use 0.5 seconds and multiple variations. These are configurable.

Trade-off: shorter searches make local review practical but may change scores or near-equal best moves compared with deeper analysis. Do not claim perfect or fixed evaluations.

## 6. Provider access isolated on the backend

Only the backend LLM module communicates with the provider SDK. The example configuration uses an OpenAI-compatible endpoint and model settings.

Keys stay in a local environment file. Provider availability and answer quality still require real tests; mocked responses do not verify them.

## 7. Template fallback when the LLM is unavailable

Explanation requests can succeed with `llm_used: false`, an error description, and text built from engine facts. Failed LLM results are not cached as successful answers.

This preserves a useful local demonstration without making the optional external provider a requirement for every run.

## 8. Keep explanation lines consistent with the review table

A deeper explanation search can rank alternatives differently. The engine move already shown in the review table is placed first in the explanation facts.

Real integration found a second case: filtering out the played move removed it even when it was best, including a mating move. The integration fix preserves that move and adds a regression test.

## 9. Keep practice hints separate from real review

The practice board retains local educational hints. PGN review uses the real backend. The interface labels the practice hints as demonstrations so their general advice is not mistaken for Stockfish analysis.
