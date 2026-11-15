import assert from 'node:assert/strict'
import { api, ApiError } from '../src/api.ts'

// Run with both backend (:8000) and Vite (:5173) running.
const fetchHttp = globalThis.fetch
globalThis.fetch = (path, options) => fetchHttp(new URL(path, 'http://localhost:5173'), options)
const health = await api.health()
assert.equal(health.engine, true, 'Configure Stockfish before running this check')
console.log('PASS: backend health through Vite proxy')
const game = await api.upload('1. f3 e5 2. g4 Qh4# 0-1')
assert.equal(game.moves.length, 4)
const review = await api.analyze(game.game_id)
assert.equal(review.moves.length, 4)
console.log('PASS: upload and Stockfish review')
for (const ply of [3, 4]) {
  const result = await api.explain(game.game_id, ply)
  assert.ok(result.explanation)
  assert.equal(result.ply, ply)
  const best = result.facts.best_lines[0]
  if (best) assert.equal(best.moves_san[0], review.moves[ply - 1].best_move_san)
  if (ply === 4) assert.equal(result.facts.reply_line, null)
  console.log(`PASS: explanation for ply ${ply}; llm_used=${result.llm_used}`)
}
await assert.rejects(() => api.upload('1. Ke3'), e => e instanceof ApiError && e.status === 422)
console.log('PASS: invalid PGN returns 422')
