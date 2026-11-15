from fastapi.testclient import TestClient

from app.coach.llm import LLMError, LLMReply
from app.engine import MATE_CP, Score
from app.main import create_app
from app.pgn import parse_pgn

from .fakes import FakeEngine

PGN = "1. e4 e5 2. Qh5 Nc6 3. Bc4 Nf6 4. Qxf7#"


class FakeLLM:
    def __init__(self, answer="Nf6 allowed mate. Play g6 instead.", fail=False):
        self.answer, self.fail, self.messages = answer, fail, []

    def chat(self, messages, tools=None):
        self.messages.append(messages)
        if self.fail:
            raise LLMError("LLM rate limit reached.")
        return LLMReply(content=self.answer)


def scripted_engine():
    g = parse_pgn(PGN)
    return FakeEngine(
        scores={g.moves[5].fen_before: Score(30), g.moves[5].fen_after: Score(MATE_CP, mate=1)},
        best={g.moves[5].fen_before: "g7g6", g.moves[5].fen_after: "h5f7"},
    )


def upload(client):
    return client.post("/api/games", json={"pgn": PGN}).json()["game_id"]


def test_explain_uses_llm_and_sends_engine_facts():
    llm = FakeLLM()
    client = TestClient(create_app(engine=scripted_engine(), llm=llm))
    r = client.post("/api/explain", json={"game_id": upload(client), "ply": 6})
    assert r.status_code == 200
    body = r.json()
    assert body["llm_used"] is True and body["error"] is None
    assert body["explanation"] == llm.answer
    assert body["facts"]["classification"] == "blunder"
    assert body["facts"]["best_lines"][0]["moves_san"][0] == "g6"
    assert body["facts"]["reply_line"]["moves_san"] == ["Qxf7#"]

    prompt = llm.messages[0][1]["content"]
    assert '"played_move": "Nf6"' in prompt
    assert "White mates in 1" in prompt
    assert "Qxf7#" in prompt


def test_explanation_is_cached():
    llm = FakeLLM()
    client = TestClient(create_app(engine=scripted_engine(), llm=llm))
    gid = upload(client)
    client.post("/api/explain", json={"game_id": gid, "ply": 6})
    client.post("/api/explain", json={"game_id": gid, "ply": 6})
    assert len(llm.messages) == 1


def test_llm_failure_falls_back_to_template():
    client = TestClient(create_app(engine=scripted_engine(), llm=FakeLLM(fail=True)))
    body = client.post("/api/explain", json={"game_id": upload(client), "ply": 6}).json()
    assert body["llm_used"] is False
    assert "rate limit" in body["error"]
    assert "Nf6 is classified as blunder" in body["explanation"]
    assert "g6" in body["explanation"]


def test_no_llm_configured_still_returns_facts():
    client = TestClient(create_app(engine=scripted_engine(), llm=None))
    body = client.post("/api/explain", json={"game_id": upload(client), "ply": 6}).json()
    assert body["llm_used"] is False and "LLM_API_KEY" in body["error"]


def test_ply_out_of_range():
    client = TestClient(create_app(engine=scripted_engine(), llm=FakeLLM()))
    r = client.post("/api/explain", json={"game_id": upload(client), "ply": 99})
    assert r.status_code == 422


class DeepDisagreesEngine(FakeEngine):
    """Deep search (multipv>1) prefers a different move than the analysis did."""

    def analyse(self, board, time_limit, multipv=1, root_moves=None):
        if multipv > 1:
            self.calls += 1
            import chess
            from app.engine import Line
            alt = chess.Move.from_uci("b8c6") if board.piece_at(chess.B8) else list(board.legal_moves)[0]
            return [Line(score=Score(40), pv=[alt])]
        return super().analyse(board, time_limit, multipv, root_moves)


def test_explanation_leads_with_same_best_move_as_analysis():
    g = parse_pgn(PGN)
    eng = DeepDisagreesEngine(best={g.moves[5].fen_before: "g7g6"})
    client = TestClient(create_app(engine=eng, llm=FakeLLM()))
    gid = upload(client)
    table = client.post(f"/api/games/{gid}/analyze").json()["moves"][5]
    facts = client.post("/api/explain", json={"game_id": gid, "ply": 6}).json()["facts"]
    assert table["best_move_san"] == "g6"
    assert facts["best_lines"][0]["moves_san"][0] == "g6"
