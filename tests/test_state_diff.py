"""Brain state diff — the observable Brain CP-naïf → Brain CP-appris change."""
from sevo.brain import Brain
from sevo.curriculum.fr_lecture_cp import build_bank_lecture
from sevo.eval import brain_state_diff
from sevo.rng import Rng
from sevo.teacher import teach_to_mastery

NODE = "fr.CP.lecture_mots_reguliers"


def _before_after():
    brain = Brain(seed=1)
    before = brain.snapshot()
    teach_to_mastery(brain, NODE, build_bank_lecture(NODE, Rng(1).fork(NODE)))
    brain.consolidate("sleep", 0)
    brain.consolidate("error_replay", 0)
    after = brain.snapshot(parent=before.snapshot_id)
    return before, after


def test_diff_reports_acquired_concepts_and_skills():
    before, after = _before_after()
    d = brain_state_diff(
        before, after,
        heldout_before=0.0, heldout_after=0.95, transfer_after=0.8,
        calibration_before=0.10, calibration_after=0.05,
        t2_after=0.6, retention_ratio=0.63, learning_efficiency=0.12,
    )
    assert NODE in d["semantic_concepts_added"]
    assert "grapheme_phoneme" in d["procedural_rules_acquired"]
    assert d["mastered_skills"]                              # at least one skill automatic
    assert d["misconceptions_reduced"]["reduction"] == 0.95  # 1.0 -> 0.05
    assert d["calibration_delta"]["improvement"] == 0.05
    assert d["retention_traces"]["t2_heldout_accuracy"] == 0.6
    assert "grapheme_phoneme" in d["retention_traces"]["consolidated_skills"]
    assert d["learning_efficiency"] == 0.12


def test_diff_is_empty_for_an_untrained_brain():
    brain = Brain(seed=2)
    snap = brain.snapshot()
    d = brain_state_diff(
        snap, snap,
        heldout_before=0.0, heldout_after=0.0, transfer_after=0.0,
        calibration_before=0.1, calibration_after=0.1,
        t2_after=0.0, retention_ratio=0.0, learning_efficiency=0.0,
    )
    assert d["semantic_concepts_added"] == []
    assert d["procedural_rules_acquired"] == []
    assert d["mastered_skills"] == {}
