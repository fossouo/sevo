"""Runtime HTTP API — exercised end to end with FastAPI's TestClient.

Skipped automatically when the optional 'api' extra (fastapi + httpx) is not
installed, so the core suite stays dependency-free.
"""
import importlib

import pytest

pytest.importorskip("fastapi")
pytest.importorskip("httpx")
from fastapi.testclient import TestClient  # noqa: E402

NODE = "fr.CP.lecture_mots_reguliers"


def _client():
    import sevo.api as api
    importlib.reload(api)          # fresh BrainService per test
    return TestClient(api.app)


def test_full_runtime_round_trip(tmp_path):
    client = _client()
    for _ in range(6):
        assert client.post("/replay", json={"node_id": NODE}).status_code == 200
    client.post("/consolidate", json={"mode": "sleep", "advance_days": 1})

    # assessment channel (oracle)
    acc = client.post("/evaluate", json={"node_id": NODE}).json()["accuracy"]
    assert acc >= 0.7

    # read-only response
    a = client.post("/act", json={"node_id": NODE, "content": "chat"}).json()
    assert a["answer"] == "S.a"

    # observable state change + verdict
    d = client.get("/diff").json()
    assert NODE in d["diff"]["semantic_concepts_added"]
    assert d["genuine_learning"]["verdict"] == "GENUINE"

    # persist + restore
    path = str(tmp_path / "brain.json")
    assert client.post("/save", json={"path": path}).status_code == 200
    loaded = client.post("/load", json={"path": path})
    assert loaded.status_code == 200

    # reloaded service still competent
    acc2 = client.post("/evaluate", json={"node_id": NODE}).json()["accuracy"]
    assert acc2 >= 0.7


def test_bad_node_returns_400():
    client = _client()
    r = client.post("/act", json={"node_id": "fr.CM2.nope", "content": "x"})
    assert r.status_code == 400


def test_health_metrics_audit_and_sessions():
    client = _client()
    assert client.get("/health").json()["status"] == "ok"
    for _ in range(6):
        client.post("/replay", json={"node_id": NODE})
    client.post("/consolidate", json={"mode": "sleep", "advance_days": 1})
    assert client.get("/metrics").json()["n_mastered_skills"] >= 1
    assert client.post("/audit", json={"node_id": NODE}).json()["clean"]
    sid = client.post("/session/start").json()["session_id"]
    client.post("/feedback", json={"node_id": NODE, "content": "chat", "correct": True})
    assert client.get(f"/session/{sid}").status_code == 200
    assert client.post(f"/session/{sid}/replay").status_code == 200
    assert client.get("/session/nope").status_code == 404


def test_evaluate_leakage_returns_422():
    client = _client()
    from sevo.curriculum.factory import teaching_bank
    seen = teaching_bank(NODE, 0)[0].word
    r = client.post("/evaluate", json={"node_id": NODE, "items": [seen]})
    assert r.status_code == 422


def test_save_load_default_to_state_volume(tmp_path, monkeypatch):
    """D: /save and /load with no path default to $SEVO_STATE_DIR (the volume)."""
    monkeypatch.setenv("SEVO_STATE_DIR", str(tmp_path))
    client = _client()
    for _ in range(3):
        client.post("/replay", json={"node_id": NODE})
    saved = client.post("/save", json={}).json()["saved"]          # no path
    assert saved == str(tmp_path / "brain.json")
    assert client.post("/load", json={}).status_code == 200        # no path
