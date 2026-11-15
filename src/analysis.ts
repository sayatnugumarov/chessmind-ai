import { Chess } from 'chess.js'
export type Analysis = { title: string; explanation: string; tips: string[] }
// Local demo hints for the practice board. Real game review uses api.ts.
export async function analyzePosition(fen: string): Promise<Analysis> {
  const game = new Chess(fen)
  await new Promise(resolve => setTimeout(resolve, 850))
  if (game.isGameOver()) return {title: game.isCheckmate() ? 'Мат. Партия завершена' : 'Ничья. Партия завершена', explanation: 'Отмените последний ход, чтобы исследовать другой вариант, или начните новую партию.', tips: ['Вернитесь к критическому моменту партии.', 'Попробуйте другой план.']}
  return {title: game.isCheck() ? 'Сначала защитите короля' : 'Найдите план перед следующим ходом', explanation: game.isCheck() ? 'Король под шахом. Уйдите от атаки, закройте её линию или возьмите атакующую фигуру.' : 'Проверьте угрозы соперника, безопасность короля и активность фигур. Эти ориентиры помогут выбрать осмысленный ход.', tips: ['Проверьте шахи, взятия и угрозы.', 'Развивайте фигуры и боритесь за центр.', 'Не оставляйте фигуры без защиты.']}
}
