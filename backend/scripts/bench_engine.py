"""Measure how long full-game analysis takes on this machine.

Usage (from backend/):  .venv/Scripts/python scripts/bench_engine.py
Analyses every position of a ~40-move game at several time limits and prints
the total time and whether the best moves stay stable across limits.
"""

import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import chess  # noqa: E402

from app.config import settings  # noqa: E402
from app.engine import Engine  # noqa: E402
from app.pgn import parse_pgn  # noqa: E402

# Kasparov - Topalov, Wijk aan Zee 1999 (44 moves)
PGN = """1. e4 d6 2. d4 Nf6 3. Nc3 g6 4. Be3 Bg7 5. Qd2 c6 6. f3 b5 7. Nge2 Nbd7 8. Bh6
Bxh6 9. Qxh6 Bb7 10. a3 e5 11. O-O-O Qe7 12. Kb1 a6 13. Nc1 O-O-O 14. Nb3 exd4
15. Rxd4 c5 16. Rd1 Nb6 17. g3 Kb8 18. Na5 Ba8 19. Bh3 d5 20. Qf4+ Ka7 21. Rhe1
d4 22. Nd5 Nbxd5 23. exd5 Qd6 24. Rxd4 cxd4 25. Re7+ Kb6 26. Qxd4+ Kxa5 27. b4+
Ka4 28. Qc3 Qxd5 29. Ra7 Bb7 30. Rxb7 Qc4 31. Qxf6 Kxa3 32. Qxa6+ Kxb4 33. c3+
Kxc3 34. Qa1+ Kd2 35. Qb2+ Kd1 36. Bf1 Rd2 37. Rd7 Rxd7 38. Bxc4 bxc4 39. Qxh8
Rd3 40. Qa8 c3 41. Qa4+ Ke1 42. f4 f5 43. Kc1 Rd2 44. Qa7 1-0"""


def main() -> None:
    if not settings.stockfish_path:
        sys.exit("Set STOCKFISH_PATH in backend/.env first.")
    game = parse_pgn(PGN)
    boards = [chess.Board(m.fen_before) for m in game.moves] + [chess.Board(game.moves[-1].fen_after)]
    print(f"Positions to analyse: {len(boards)}")

    engine = Engine(settings.stockfish_path)
    results: dict[float, list] = {}
    try:
        for limit in (0.05, 0.1, 0.2, 0.5):
            t0 = time.perf_counter()
            results[limit] = [(engine.analyse(b, limit)[0].pv or [None])[0] for b in boards]
            elapsed = time.perf_counter() - t0
            print(f"time_limit={limit:<5} total={elapsed:6.1f}s  per_position={elapsed / len(boards):.3f}s")
    finally:
        engine.close()

    ref = results[0.5]
    for limit, best in results.items():
        agree = sum(a == b for a, b in zip(best, ref)) / len(ref)
        print(f"best-move agreement {limit}s vs 0.5s: {agree:.0%}")

if __name__ == "__main__":
    main()
