"""Observability counters + methodological-safety (leakage) checks."""
import pytest

from sevo.curriculum.factory import heldout_bank, teaching_bank
from sevo.eval import ItemLeakageError, audit_node, detect_leakage
from sevo.runtime import BrainService

NODE = "fr.CP.lecture_mots_reguliers"


def test_counters_track_service_calls():
    svc = BrainService(seed=7)
    svc.perceive("text", "x")
    svc.act(NODE, "chat")
    svc.feedback(NODE, "chat", correct=True)
    svc.consolidate("sleep", 1)
    c = svc.counters
    assert (c["perceptions"], c["actions"], c["feedbacks"], c["consolidations"]) == (1, 1, 1, 1)


def test_health_and_metrics():
    svc = BrainService(seed=7)
    for _ in range(6):
        svc.replay_emma_session(NODE)
    svc.consolidate("sleep", 1)
    assert svc.health()["status"] == "ok"
    m = svc.metrics()
    assert m["n_mastered_skills"] >= 1
    assert m["genuine_learning"] in ("GENUINE", "NOT_PROVEN")


def test_audit_clean_for_builtin_banks():
    rep = audit_node(NODE, 0)
    assert rep["clean"]
    assert rep["heldout"]["clean"]


def test_detect_leakage_flags_seen_items():
    teaching = teaching_bank(NODE, 0)
    contaminated = detect_leakage(teaching[:3], teaching)
    assert not contaminated["clean"] and contaminated["n_contaminated"] == 3
    assert detect_leakage(heldout_bank(NODE, 0), teaching)["clean"]


def test_evaluate_refuses_seen_items():
    svc = BrainService(seed=0)
    seen_word = teaching_bank(NODE, 0)[0].word
    with pytest.raises(ItemLeakageError):
        svc.evaluate(NODE, items=[seen_word])
