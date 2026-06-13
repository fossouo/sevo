"""Persistent sessions + deterministic replay."""
import pytest

from sevo.runtime import BrainService

NODE = "fr.CP.lecture_mots_reguliers"
WORDS = ["chat", "chou", "table", "robe", "bateau", "jardin"]


def test_session_records_feedback():
    svc = BrainService(seed=7)
    sid = svc.start_session()
    for w in WORDS:
        svc.feedback(NODE, w, correct=True)
    fb = [i for i in svc.get_session(sid)["interactions"] if i["type"] == "feedback"]
    assert len(fb) == len(WORDS)
    assert fb[0]["node_id"] == NODE and fb[0]["correct"] is True


def test_replay_is_deterministic_and_reproduces_end_state():
    svc = BrainService(seed=7)
    sid = svc.start_session()
    for w in WORDS:
        svc.feedback(NODE, w, correct=True)
    r1 = svc.replay_session(sid)["replayed_state"]
    r2 = svc.replay_session(sid)["replayed_state"]
    assert r1 == r2                                   # deterministic
    assert r1 == svc.brain.export_state()             # reproduces the live end-state


def test_replay_does_not_depend_on_global_rng():
    """B: replay is deterministic because feedback-learning has no rng. Advancing
    the brain's rng (via stochastic acts) between replays must not change the
    replayed end-state."""
    svc = BrainService(seed=7)
    sid = svc.start_session()
    for w in WORDS:
        svc.feedback(NODE, w, correct=True)
    r1 = svc.replay_session(sid)["replayed_state"]
    for _ in range(20):
        svc.act(NODE, "chat")          # consume the global rng
    r2 = svc.replay_session(sid)["replayed_state"]
    assert r1 == r2


def test_unknown_session_raises():
    with pytest.raises(KeyError):
        BrainService(seed=1).get_session("nope")
