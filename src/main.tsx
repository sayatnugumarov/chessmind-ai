import React, { useRef, useState } from 'react'
import { createRoot } from 'react-dom/client'
import { Chess, type Square } from 'chess.js'
import { ArrowDownUp, ArrowLeft, ArrowUpRight, BrainCircuit, Check, ChevronRight, Copy, Flag, Lightbulb, LoaderCircle, RotateCcw, Sparkles, Trophy } from 'lucide-react'
import { analyzePosition, type Analysis } from './analysis'
import './style.css'
import GameReview from './Review'

const glyphs: Record<string,string> = {k:'♚',q:'♛',r:'♜',b:'♝',n:'♞',p:'♟'}
function App(){
  const [mode,setMode]=useState<'review'|'practice'>('review')
  const [game,setGame]=useState(new Chess())
  const [selected,setSelected]=useState<Square|null>(null)
  const [flipped,setFlipped]=useState(false)
  const [analysis,setAnalysis]=useState<Analysis|null>(null)
  const [loading,setLoading]=useState(false)
  const [error,setError]=useState('')
  const [copied,setCopied]=useState(false)
  const request=useRef(0)
  const history=game.history(), last=game.history({verbose:true}).at(-1)
  const targets=selected?game.moves({square:selected,verbose:true}).map(m=>m.to):[]
  const files=flipped?'hgfedcba':'abcdefgh', ranks=flipped?[1,2,3,4,5,6,7,8]:[8,7,6,5,4,3,2,1]
  function update(next:Chess){request.current++;setGame(next);setSelected(null);setAnalysis(null);setLoading(false);setError('');setCopied(false)}
  function replay(moves:string[]){const next=new Chess();moves.forEach(m=>next.move(m));return next}
  function click(square:Square){
    if(game.isGameOver())return
    if(selected&&targets.includes(square)){const next=replay(history);next.move({from:selected,to:square,promotion:'q'});update(next)}
    else setSelected(game.get(square)?.color===game.turn()&&selected!==square?square:null)
  }
  async function analyze(){const id=++request.current;setLoading(true);setError('');try{const result=await analyzePosition(game.fen());if(id===request.current)setAnalysis(result)}catch{if(id===request.current)setError('Не удалось выполнить анализ. Попробуйте ещё раз.')}finally{if(id===request.current)setLoading(false)}}
  async function copy(){try{await navigator.clipboard.writeText(game.fen());setCopied(true)}catch{setError('Не удалось скопировать FEN. Выделите его в поле под доской.')}}
  const status=game.isCheckmate()?'Мат':game.isDraw()?'Ничья':game.isCheck()?'Шах':'Партия идёт'
  return <div className="app"><aside className="sidebar">
    <a className="brand" href="./"><BrainCircuit size={27}/>chessmind<span>AI</span></a>
    <div className="nav-label">ВАШЕ ПРОСТРАНСТВО</div><div className="nav-active"><Sparkles size={18}/>Анализ позиции<ChevronRight size={16}/></div>
    <div className="sidebar-note"><div>♞</div><h3>Каждый ход —<br/>новая идея.</h3><p>Исследуйте позиции и учитесь видеть больше за шахматной доской.</p></div>
    <div className="profile"><b>И</b><div>Исследователь<small>Учебное пространство</small></div><i/></div>
  </aside><main><header><span>Тренировка <ChevronRight size={13}/> {mode==='review'?'Разбор партии':'Свободная доска'}</span><span className="badge">{mode==='review'?'Stockfish + тренер':'Демо-подсказки'}</span></header>
    <section className="heading"><div><div className="eyebrow">СМОТРИТЕ ГЛУБЖЕ. ИГРАЙТЕ СИЛЬНЕЕ.</div><h1>За каждым ходом — <em>идея.</em></h1><p>Исследуйте доску и находите свой следующий шаг.</p></div><span className="chapter">01 / АНАЛИЗ</span></section>
    <div className="mode-tabs" aria-label="Режим работы"><button className={mode==='review'?'active':''} aria-pressed={mode==='review'} onClick={()=>setMode('review')}>Разбор PGN</button><button className={mode==='practice'?'active':''} aria-pressed={mode==='practice'} onClick={()=>setMode('practice')}>Свободная доска</button></div>
    <div hidden={mode!=='review'}><GameReview/></div>
    <div className="workspace" hidden={mode!=='practice'}><section className="board-panel" aria-label="Шахматная доска">
      <div className="player"><b>♚</b><div>{flipped?'Белые фигуры':'Чёрные фигуры'}<small>Игра на одной доске</small></div><span>{status}</span></div>
      <div className="board">{ranks.flatMap((rank,ri)=>[...files].map((file,fi)=>{const square=`${file}${rank}` as Square,piece=game.get(square);return <button key={square} aria-label={`${square}${piece?` ${piece.color==='w'?'белые':'чёрные'} ${piece.type}`:''}`} aria-pressed={selected===square} onClick={()=>click(square)} className={`square ${(file.charCodeAt(0)-97+rank)%2===0?'light':'dark'} ${selected===square?'selected':''} ${last?.from===square||last?.to===square?'last':''}`}>
        {fi===0&&<span className="rank">{rank}</span>}{ri===7&&<span className="file">{file}</span>}{piece&&<span className={`piece ${piece.color==='w'?'white':'black'}`}>{glyphs[piece.type]}</span>}{targets.includes(square)&&<span className={piece?'capture':'target'}/>}</button>}))}</div>
      <div className="player bottom"><b className="white-icon">♚</b><div>{flipped?'Чёрные фигуры':'Белые фигуры'}<small>{game.isGameOver()?'Партия завершена':`Ход ${game.turn()==='w'?'белых':'чёрных'}`}</small></div><i/></div>
      <div className="tools"><button disabled={!history.length} onClick={()=>update(replay(history.slice(0,-1)))}><ArrowLeft size={16}/>Отменить</button><button onClick={()=>setFlipped(!flipped)}><ArrowDownUp size={16}/>Перевернуть</button><button onClick={()=>update(new Chess())}><RotateCcw size={16}/>Новая партия</button></div>
      <p className="hint">Выберите фигуру, затем поле для хода. Превращение пешки — в ферзя.</p><div className="fen"><span>FEN</span><input aria-label="Текущая позиция FEN" readOnly value={game.fen()}/><button aria-label="Скопировать FEN" onClick={copy}>{copied?<Check size={15}/>:<Copy size={15}/>}</button></div>
    </section><aside className="right-panel"><section className="analysis-card"><div className="card-top"><span><Sparkles size={21}/></span><small>ВАШ ШАХМАТНЫЙ ПОМОЩНИК</small></div><h2>Поймите позицию.</h2><p className="description">Не просто следующий ход, а мысль, которая за ним стоит.</p>
      <div className="analysis-content" aria-live="polite" aria-busy={loading}>{loading?<div className="empty"><LoaderCircle className="spin" size={32}/><h3>Рассматриваем позицию…</h3><p>Готовим учебные подсказки.</p></div>:analysis?<div className="result"><div className="result-label"><Lightbulb size={15}/>НА ЧТО ОБРАТИТЬ ВНИМАНИЕ</div><h3>{analysis.title}</h3><p>{analysis.explanation}</p><ul>{analysis.tips.map(tip=><li key={tip}>{tip}</li>)}</ul></div>:<div className="empty"><div className="orbit"><BrainCircuit size={32}/></div><h3>У каждой позиции есть история</h3><p>Сделайте ход или исследуйте начальную позицию с помощью подсказок.</p></div>}</div>
      {error&&<p className="error" role="alert">{error}</p>}<button className="analyze" disabled={loading} onClick={analyze}>{loading?<LoaderCircle className="spin" size={18}/>:<Sparkles size={18}/>}<span>{loading?'Анализируем…':'Анализировать позицию'}</span><ArrowUpRight size={18}/></button><p className="demo-note">Демонстрационные подсказки · без подключения к ИИ</p>
    </section><section className="history-card"><div className="section-title"><h3><Flag size={16}/>История ходов</h3><span>{history.length} полуходов</span></div><div className="move-head"><span>№</span><span>Белые</span><span>Чёрные</span></div><div className="move-list">{history.length?Array.from({length:Math.ceil(history.length/2)},(_,i)=><div className="move-row" key={i}><span>{i+1}.</span><span>{history[i*2]}</span><span>{history[i*2+1]||'—'}</span></div>):<p className="history-empty">Первый ход — начало истории.<br/><span>Сыграйте его на доске.</span></p>}</div></section><div className="tip"><Trophy size={22}/><p><strong>Маленький шаг к сильной игре</strong>Перед каждым ходом спросите себя: что угрожает соперник?</p></div></aside></div>
    <footer><span>CHESSMIND AI</span><span>Практика превращается в понимание.</span></footer>
  </main></div>
}
createRoot(document.getElementById('root')!).render(<React.StrictMode><App/></React.StrictMode>)
