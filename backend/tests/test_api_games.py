from fastapi.testclient import TestClient

from app.main import create_app

from .fakes import FakeEngine

engine = FakeEngine()
client = TestClient(create_app(engine=engine))


def test_health():
    r = client.get("/api/health")
    assert r.status_code == 200
    assert r.json()["status"] == "ok"
    assert r.json()["engine"] is True


def test_upload_and_fetch_game():
    r = client.post("/api/games", json={"pgn": "1. e4 e5 2. Nf3 Nc6"})
    assert r.status_code == 201
    body = r.json()
    assert len(body["moves"]) == 4
    assert body["moves"][2]["san"] == "Nf3"

    r2 = client.get(f"/api/games/{body['game_id']}")
    assert r2.status_code == 200
    assert r2.json() == body


def test_invalid_pgn_returns_422_with_message():
    r = client.post("/api/games", json={"pgn": "1. e4 e5 2. Ke3"})
    assert r.status_code == 422
    assert "Invalid PGN" in r.json()["detail"]


def test_unknown_game_returns_404():
    assert client.get("/api/games/nope").status_code == 404
    assert client.post("/api/games/nope/analyze").status_code == 404


def test_analyze_returns_one_entry_per_move_and_caches():
    game_id = client.post("/api/games", json={"pgn": "1. e4 e5 2. Nf3 Nc6"}).json()["game_id"]
    calls_before = engine.calls
    r = client.post(f"/api/games/{game_id}/analyze")
    assert r.status_code == 200
    body = r.json()
    assert [m["ply"] for m in body["moves"]] == [1, 2, 3, 4]
    assert {"eval_before", "eval_after", "cp_loss", "classification", "best_move_san"} <= set(body["moves"][0])
    assert engine.calls - calls_before == 5

    client.post(f"/api/games/{game_id}/analyze")
    assert engine.calls - calls_before == 5  # second call served from cache


def test_analyze_without_engine_returns_503():
    with TestClient(create_app(engine=None)) as no_engine:
        # Lifespan may start real Stockfish if configured; force it off for this test.
        no_engine.app.state.engine = None
        gid = no_engine.post("/api/games", json={"pgn": "1. e4"}).json()["game_id"]
        r = no_engine.post(f"/api/games/{gid}/analyze")
        assert r.status_code == 503
