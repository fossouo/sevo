"""The implementation must stay faithful to the v0.3 design contracts."""
import json
import os

from sevo.brain import Brain
from sevo.curriculum.cp_ce1_math import build_bank
from sevo.eval import compute_delta

DESIGN = os.path.join(os.path.dirname(__file__), "..", "design")


def _load(name):
    with open(os.path.join(DESIGN, name), encoding="utf-8") as f:
        return json.load(f)


def test_design_files_are_valid_json():
    for name in os.listdir(DESIGN):
        if name.endswith(".json"):
            _load(name)  # raises on malformed JSON


def test_brain_implements_public_api():
    api = _load("api_surface.json")["public_api"]
    paths = {e["path"] for e in api}
    brain = Brain(seed=0)
    # Map design paths -> implemented capabilities.
    assert "/perceive" in paths and hasattr(brain, "perceive")
    assert "/act" in paths and hasattr(brain, "act")
    assert "/learn/session" in paths and hasattr(brain, "learn_session")
    assert "/consolidate" in paths and hasattr(brain, "consolidate")
    assert "/evaluate/pretest" in paths and hasattr(brain, "evaluate")
    assert any(p.startswith("/state/snapshot") for p in paths) and hasattr(brain, "snapshot")


def test_all_mvp_services_are_wired():
    services = _load("brain_services.json")
    mvp = set(services["minimal_mvp"])
    brain = Brain(seed=0)
    attr_map = {
        "sensory_gateway": "sensory", "global_workspace": "workspace",
        "working_memory": "wm", "executive_control": "executive",
        "episodic_memory": "episodic", "semantic_memory": "semantic",
        "procedural_memory": "procedural", "metacognition_self_model": "metacog",
        "consolidation_sleep": "consolidation", "assessment_oracle": "oracle",
    }
    for svc in mvp:
        assert getattr(brain, attr_map[svc], None) is not None, f"MVP service not wired: {svc}"


def test_perceive_emits_events():
    brain = Brain(seed=0)
    brain.perceive("text", "bonjour", source="emma")
    assert "percept.created" in brain.bus.topics_seen()


def test_snapshot_is_versioned_and_serialisable():
    brain = Brain(seed=0)
    s1 = brain.snapshot()
    teach = build_bank("math.CP.add_within_20", __import__("sevo.rng", fromlist=["Rng"]).Rng(0))
    brain.learn_session("CP", "maths", teach.teaching[:8])
    s2 = brain.snapshot(parent=s1.snapshot_id)
    assert s2.parent_snapshot_id == s1.snapshot_id
    json.loads(s2.to_json())  # round-trips


def test_delta_formula_weights_sum_to_one():
    out = compute_delta(
        heldout_before=0.0, heldout_after=0.9, transfer_before=0.0, transfer_after=0.8,
        reasoning_before=0.0, reasoning_after=0.7, t1_after=0.9, t2_after=0.6,
        calibration_before=0.2, calibration_after=0.1,
        trials_with_prereq=16, trials_without_prereq=40,
    )
    assert abs(sum(out["weights"].values()) - 1.0) < 1e-9
    assert out["weighted_delta"] > 0
