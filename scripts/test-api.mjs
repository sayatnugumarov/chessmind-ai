import assert from 'node:assert/strict'
import { api, ApiError, formatEvaluation } from '../src/api.ts'

const calls = []
let response = { status: 200, data: { status: 'ok', engine: true, llm_configured: false } }
globalThis.fetch = async (url, options) => {
  calls.push({ url, options })
  return new Response(JSON.stringify(response.data), { status: response.status, headers: { 'Content-Type': 'application/json' } })
}
assert.equal((await api.health()).engine, true)
response = { status: 201, data: { game_id: 'test', headers: {}, start_fen: 'fen', moves: [] } }
assert.equal((await api.upload('1. e4')).game_id, 'test')
assert.equal(calls.at(-1).url, '/api/games')
assert.deepEqual(JSON.parse(calls.at(-1).options.body), { pgn: '1. e4' })
response = { status: 200, data: { game_id: 'test', moves: [], critical_moments: [] } }
await api.analyze('test')
assert.equal(calls.at(-1).url, '/api/games/test/analyze')
assert.deepEqual(JSON.parse(calls.at(-1).options.body), { time_limit: 0.1 })
response.data = { explanation: 'Template', llm_used: false, error: 'Not configured' }
assert.equal((await api.explain('test', 9)).llm_used, false)
assert.deepEqual(JSON.parse(calls.at(-1).options.body), { game_id: 'test', ply: 9 })
for (const status of [404, 422, 503]) {
  response = { status, data: { detail: 'Invalid input or unavailable engine' } }
  await assert.rejects(() => api.upload('bad'), e => e instanceof ApiError && e.status === status && e.message.length > 0)
}
globalThis.fetch = async () => { throw new TypeError('Network unavailable') }
await assert.rejects(() => api.health(), e => e instanceof ApiError && e.status === 0)
assert.equal(formatEvaluation({ cp: 125, mate: null }), '+1.25')
assert.equal(formatEvaluation({ cp: -100, mate: null }), '-1.00')
assert.ok(formatEvaluation({ cp: -10000, mate: -2 }).endsWith('2'))
assert.equal(formatEvaluation({ cp: 10000, mate: 0 }), '\u041c\u0430\u0442')
console.log('PASS: upload, analysis, explanation fallback, 404/422/503/network, evaluation formatting')
