# Project plan

Status snapshot: November 15, 2026. Working application: `integration`, checkpoint `9a7dfce`.

## Completed

- [x] React/TypeScript application shell and responsive styles.
- [x] Practice board with legal moves, undo, rotation, reset, and FEN copying.
- [x] PGN upload to FastAPI and per-move navigation.
- [x] Stockfish evaluation, move classification, and critical moments.
- [x] Explanation panel with engine facts and template fallback.
- [x] HTTP-client loading and error states.
- [x] Nullable response handling, including no continuation after checkmate.
- [x] Consistency fix for best played moves in explanations.
- [x] Real local HTTP integration check through the Vite proxy.
- [x] Backend suite: 42 tests passing with Stockfish configured.
- [x] Frontend production build and HTTP-client checks.
- [x] Combined application published in a separate `integration` branch.

## Remaining

- [ ] Verify a real LLM key and model with successful provider responses.
- [ ] Review explanation accuracy and usefulness on more games.
- [ ] Implement `/api/ask` and a position-question interface.
- [ ] Implement tool-using and baseline modes for comparison.
- [ ] Prepare an AI evaluation dataset and evaluation script.
- [ ] Perform systematic browser and accessibility checks.
- [ ] Decide whether to promote application code into `main`.
- [ ] Complete final reflection, presentation rehearsal, and backup video.

## Milestones from the team plan

| Period | Planned outcome |
| --- | --- |
| November 16 | Working local checkpoint and team integration |
| November 17–23 | Position questions, tools, baseline mode, and related tests |
| November 24–30 | Evaluation dataset, comparison script, and prompt review |
| December 1–6 | Final documentation, rehearsal, and release preparation |
| December 6 | Planned code freeze and `v1.0` tag |
| December 7–19 | Planned defense window |

These dates come from the team's existing plan; they are targets, not completed deliverables. The `v1.0` release has not been created at this checkpoint.

## Scope boundaries

The current goal is a local, working chess-review MVP. Database storage, authentication, public deployment, queues, and streaming are outside the checkpoint scope. Voice input and additional interactive coaching are optional extensions.
