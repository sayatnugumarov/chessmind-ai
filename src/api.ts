export type Evaluation = { cp: number; mate: number | null }
export type Classification = 'best' | 'good' | 'inaccuracy' | 'mistake' | 'blunder'
export type GameMove = { ply: number; move_number: number; color: 'white' | 'black'; san: string; uci: string; fen_before: string; fen_after: string }
export type Game = { game_id: string; headers: Record<string, string>; start_fen: string; moves: GameMove[] }
export type ReviewedMove = { ply: number; color: 'white' | 'black'; san: string; uci: string; eval_before: Evaluation; eval_after: Evaluation; best_move_uci: string; best_move_san: string; cp_loss: number; classification: Classification }
export type Review = { game_id: string; time_limit: number; moves: ReviewedMove[]; critical_moments: number[] }
type Line = { eval: Evaluation; moves_san: string[] }
export type Explanation = { game_id: string; ply: number; explanation: string; llm_used: boolean; error: string | null; facts: { fen_before: string; played_san: string; classification: Classification; cp_loss: number; eval_before: Evaluation; eval_after: Evaluation; best_lines: Line[]; reply_line: Line } }
export class ApiError extends Error {
  status: number
  constructor(status: number, message: string) { super(message); this.status = status }
}
async function request<T>(path: string, body?: unknown): Promise<T> {
  let response: Response
  try { response = await fetch(`/api${path}`, body === undefined ? {} : { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify(body) }) }
  catch { throw new ApiError(0, 'Нет соединения с сервером. Проверьте, запущен ли бэкенд на localhost:8000.') }
  const data = await response.json().catch(() => null)
  if (!response.ok) {
    const detail = typeof data?.detail === 'string' ? data.detail : 'Сервер не смог обработать запрос.'
    throw new ApiError(response.status, response.status === 404 ? 'Партия не найдена. Возможно, сервер перезапущен. Загрузите PGN повторно.' : response.status === 503 ? `Шахматный движок недоступен. ${detail}` : detail)
  }
  if (!data) throw new ApiError(response.status, 'Сервер вернул пустой ответ.')
  return data as T
}
export const api = {
  health: () => request<{ status: string; engine: boolean; llm_configured: boolean }>('/health'),
  upload: (pgn: string) => request<Game>('/games', { pgn }),
  analyze: (id: string) => request<Review>(`/games/${encodeURIComponent(id)}/analyze`, { time_limit: 0.1 }),
  explain: (id: string, ply: number) => request<Explanation>('/explain', { game_id: id, ply }),
}
export const classifications: Record<Classification, string> = { best: 'Лучший', good: 'Хороший', inaccuracy: 'Неточность', mistake: 'Ошибка', blunder: 'Грубая ошибка' }
export function formatEvaluation(value: Evaluation): string {
  if (value.mate !== null) return value.mate === 0 ? 'Мат' : `${value.mate > 0 ? 'Белые' : 'Чёрные'}: мат в ${Math.abs(value.mate)}`
  return `${value.cp > 0 ? '+' : ''}${(value.cp / 100).toFixed(2)}`
}
