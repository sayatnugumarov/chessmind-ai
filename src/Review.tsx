import { useEffect, useRef, useState } from 'react'
import { Chess, type Square } from 'chess.js'
import { ArrowDownUp, ChevronLeft, ChevronRight, LoaderCircle, Sparkles } from 'lucide-react'
import { api, ApiError, classifications, formatEvaluation, type Game, type Review, type Explanation } from './api'

const glyphs: Record<string, string> = { k: '♚', q: '♛', r: '♜', b: '♝', n: '♞', p: '♟' }
const example = '[White "Student"]\n[Black "Friend"]\n[Result "0-1"]\n\n1. f3 e5 2. g4 Qh4# 0-1'
export default function GameReview() {
  const [pgn, setPgn] = useState('')
  const [game, setGame] = useState<Game | null>(null)
  const [review, setReview] = useState<Review | null>(null)
  const [explanation, setExplanation] = useState<Explanation | null>(null)
  const [ply, setPly] = useState(0)
  const [flipped, setFlipped] = useState(false)
  const [busy, setBusy] = useState<'upload' | 'analyze' | 'explain' | null>(null)
  const [error, setError] = useState('')
  const [health, setHealth] = useState('Проверяем соединение…')
  const generation = useRef(0)
  useEffect(() => {
    let active = true
    api.health().then(h => { if (active) setHealth(h.engine ? 'Stockfish готов' : 'Сервер доступен · движок не настроен') }).catch(() => { if (active) setHealth('Бэкенд недоступен · запустите сервер') })
    return () => { active = false; generation.current++ }
  }, [])
  function fail(e: unknown) {
    setError(e instanceof Error ? e.message : 'Не удалось выполнить запрос.')
    if (e instanceof ApiError && e.status === 404) { setGame(null); setReview(null); setExplanation(null); setPly(0) }
  }
  async function upload() {
    if (!pgn.trim()) { setError('Вставьте PGN партии.'); return }
    const id = ++generation.current
    setBusy('upload'); setError('')
    try {
      const result = await api.upload(pgn.trim())
      if (id !== generation.current) return
      new Chess(result.start_fen)
      result.moves.forEach(move => new Chess(move.fen_after))
      setGame(result); setReview(null); setExplanation(null); setPly(0)
    } catch (e) { if (id === generation.current) fail(e) }
    finally { if (id === generation.current) setBusy(null) }
  }
  async function analyze() {
    if (!game) return
    const id = ++generation.current
    setBusy('analyze'); setError('')
    try { const result = await api.analyze(game.game_id); if (id === generation.current) setReview(result) }
    catch (e) { if (id === generation.current) fail(e) }
    finally { if (id === generation.current) setBusy(null) }
  }
  async function explain() {
    if (!game || !ply) return
    const id = ++generation.current
    setBusy('explain'); setError(''); setExplanation(null)
    try { const result = await api.explain(game.game_id, ply); if (id === generation.current) setExplanation(result) }
    catch (e) { if (id === generation.current) fail(e) }
    finally { if (id === generation.current) setBusy(null) }
  }
  function select(next: number) {
    if (!game || next < 0 || next > game.moves.length) return
    // Selection cancels a stale explanation, but keeps a game-wide analysis running.
    if (busy === 'explain') { generation.current++; setBusy(null) }
    setPly(next); setExplanation(null); setError('')
  }
  const current = game?.moves.find(m => m.ply === ply)
  const board = new Chess(current?.fen_after ?? game?.start_fen)
  const move = review?.moves.find(m => m.ply === ply)
  const files = flipped ? 'hgfedcba' : 'abcdefgh'
  const ranks = flipped ? [1,2,3,4,5,6,7,8] : [8,7,6,5,4,3,2,1]
  return <div className="review-layout">
    <section className="pgn-card"><div className="section-title"><h3>Загрузить партию</h3><span role="status">{health}</span></div><label htmlFor="pgn">Вставьте PGN из экспорта вашей партии</label><textarea id="pgn" value={pgn} onChange={e => setPgn(e.target.value)} placeholder={'1. e4 e5 2. Nf3 Nc6…'} rows={4}/><div className="pgn-actions"><button className="secondary" disabled={!!busy} onClick={() => setPgn(example)}>Вставить пример</button><button className="analyze" disabled={!!busy || !pgn.trim()} onClick={upload}>{busy === 'upload' && <LoaderCircle className="spin" size={16}/>}Загрузить PGN</button></div><p className="hint">Партия хранится до перезапуска бэкенда. После перезапуска загрузите PGN снова.</p></section>
    {error && <p className="review-error" role="alert">{error}</p>}
    <div className="workspace"><section className="board-panel"><div className="player"><b>♚</b><div>{game ? `${game.headers.White || 'Белые'} — ${game.headers.Black || 'Чёрные'}` : 'Ваша партия'}<small>{ply === 0 ? 'Начальная позиция' : `После хода ${current?.move_number}${current?.color === 'white' ? '.' : '…'} ${current?.san}`}</small></div></div>
      <div className="board" aria-label="Позиция выбранного хода">{ranks.flatMap((rank,ri) => [...files].map((file,fi) => { const square = `${file}${rank}` as Square, piece = board.get(square); return <div key={square} className={`square ${(file.charCodeAt(0)-97+rank)%2===0?'light':'dark'} ${current?.uci.slice(0,2)===square||current?.uci.slice(2,4)===square?'last':''}`} aria-label={square}>{fi===0&&<span className="rank">{rank}</span>}{ri===7&&<span className="file">{file}</span>}{piece&&<span className={`piece ${piece.color==='w'?'white':'black'}`}>{glyphs[piece.type]}</span>}</div> }))}</div>
      <div className="tools"><button disabled={!game || ply===0 || busy==='upload'} onClick={()=>select(ply-1)}><ChevronLeft size={17}/>Назад</button><button onClick={()=>setFlipped(!flipped)}><ArrowDownUp size={16}/>Перевернуть</button><button disabled={!game || ply===game.moves.length || busy==='upload'} onClick={()=>select(ply+1)}>Вперёд<ChevronRight size={17}/></button></div><p className="hint">Режим просмотра партии. Выберите ход в истории.</p>
    </section><aside className="right-panel"><section className="analysis-card"><div className="card-top"><span><Sparkles size={21}/></span><small>РАЗБОР ПАРТИИ</small></div><h2>Найдите важный момент.</h2><p className="description">Stockfish оценит ходы, а тренер объяснит выбранный ход.</p><button className="analyze review-analyze" disabled={!game?.moves.length || !!busy} onClick={analyze}>{busy==='analyze' && <LoaderCircle className="spin" size={18}/>} {busy==='analyze'?'Анализируем партию…':'Анализировать партию'}</button>
      {busy==='analyze'&&<p className="hint" role="status">Обычно 5–10 секунд; длинная партия потребует больше времени.</p>}
      {review&&<div className="critical"><strong>Критические моменты</strong><div>{review.critical_moments.length?review.critical_moments.map(p=>{const m=game?.moves.find(m=>m.ply===p);return <button key={p} disabled={busy==='upload'} className="secondary" onClick={()=>select(p)}>{m?`${m.move_number}${m.color==='white'?'.':'…'} ${m.san}`:`Полуход ${p}`}</button>}):<p>Ошибок и грубых ошибок не найдено.</p>}</div></div>}
      {move&&<div className="move-facts"><span className={`classification ${move.classification}`}>{classifications[move.classification]}</span><h3>{move.san} <span>→ {formatEvaluation(move.eval_after)}</span></h3><p>Оценка со стороны белых · потеря: {(move.cp_loss/100).toFixed(2)} пешки</p><p>Лучший ход: <strong>{move.best_move_san ?? '—'}</strong></p></div>}
      <button className="secondary explain-button" disabled={!game || ply===0 || !!busy} onClick={explain}>{busy==='explain'?<><LoaderCircle className="spin" size={16}/>Готовим объяснение…</>:'Объяснить выбранный ход'}</button>
      {ply===0&&<p className="hint">Выберите ход, чтобы получить объяснение.</p>}
      {explanation&&<div className="result" aria-live="polite"><div className="result-label">{explanation.llm_used?'ОБЪЯСНЕНИЕ ИИ':'ОБЪЯСНЕНИЕ ПО ДАННЫМ ДВИЖКА'}</div><p className="coach-text">{explanation.explanation}</p>{!explanation.llm_used&&<p className="fallback-note">ИИ недоступен. Показано шаблонное объяснение.{explanation.error && ` Причина: ${explanation.error}`}</p>}{explanation.facts.best_lines[0]&&<p><strong>Лучший вариант:</strong> {explanation.facts.best_lines[0].moves_san.join(' → ')}</p>}<p><strong>Продолжение после хода:</strong> {explanation.facts.reply_line?.moves_san.join(' → ') || 'Партия завершена'}</p></div>}
    </section><section className="history-card"><div className="section-title"><h3>История партии</h3><span>{game?.moves.length??0} полуходов</span></div>{game&&<button className={`start-position secondary ${ply===0?'active':''}`} onClick={()=>select(0)} disabled={busy==='upload'}>Начальная позиция</button>}<div className="review-moves">{game?.moves.map(m=>{const r=review?.moves.find(r=>r.ply===m.ply);return <button key={m.ply} aria-pressed={ply===m.ply} disabled={busy==='upload'} className={`review-move ${ply===m.ply?'active':''}`} onClick={()=>select(m.ply)}><span>{m.move_number}{m.color==='white'?'.':'…'} {m.san}</span>{r&&<span className={`classification ${r.classification}`}>{classifications[r.classification]}</span>}</button>})}</div>{!game&&<p className="history-empty">Загрузите PGN, чтобы увидеть ходы.</p>}</section></aside></div>
  </div>
}
