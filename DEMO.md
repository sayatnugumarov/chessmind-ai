# Demonstration guide

Use the `integration` branch and start both servers using [SETUP.md](SETUP.md). This demonstration works without an LLM key by using factual template explanations.

## Preparation

1. Open `http://localhost:8000/api/health` and confirm `engine: true`.
2. Open `http://localhost:5173/`.
3. Keep both server terminals open.
4. State whether the demonstration uses a real LLM or the fallback. Do not describe a template as an AI-generated answer.

## Walkthrough

### 1. Load a short game

Select the PGN review tab (`Разбор PGN`), click `Вставить пример` (insert example), and then `Загрузить PGN` (upload PGN).

The example is Fool's Mate:

```pgn
[White "Student"]
[Black "Friend"]
[Result "0-1"]

1. f3 e5 2. g4 Qh4# 0-1
```

Expected result: four half-moves in the history and the starting board position.

### 2. Navigate the game

Select `f3`, `e5`, `g4`, and `Qh4#`. Show that the board displays the position after each move. Use the initial-position button and board rotation.

### 3. Analyze

Click `Анализировать партию` (analyze game), wait for completion, and select a move. Show classifications, White-POV evaluation, the engine's best move, and critical moments.

Exact numerical scores can vary with engine version and search time. Focus on the supported workflow, not a pre-written score.

### 4. Explain

Select `2. g4`, then `Объяснить выбранный ход` (explain selected move). Show the explanation and lines. If `llm_used` is false, explain that the server is presenting a template from engine facts.

Select `2... Qh4#` and request its explanation. The played mating move must remain the best move, and the absence of a continuation must not crash the interface.

### 5. Show error handling

Enter `1. Ke3` and upload. The backend should reject the illegal PGN with HTTP 422 and the frontend should display an error. Reload the valid example afterward.

## What to say about the project

- Stockfish evaluates; the coach explains supplied evidence.
- Restarting the server clears uploaded games, so re-upload is expected.
- The independent practice board's hints are demonstrations.
- Position chat, voice features, and comparative AI evaluation remain planned.

For a deadline demonstration, rehearse once and keep a backup screen recording. No recording is included in this repository checkpoint.
