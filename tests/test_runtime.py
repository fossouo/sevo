"""BrainService — the persistent runtime, and its teacher/oracle separation."""
from sevo.curriculum.factory import TaskFactoryError, build_task, heldout_bank, teaching_bank
from sevo.runtime import BrainService

import pytest

NODE = "fr.CP.lecture_mots_reguliers"


def _taught(seed=7):
    svc = BrainService(seed=seed)
    for _ in range(6):
        svc.replay_emma_session(NODE)
    svc.consolidate("sleep", 1)
    svc.consolidate("error_replay", 0)
    return svc


# ---- task factory ----------------------------------------------------------
def test_factory_builds_each_cp_node():
    assert build_task("fr.CP.lecture_mots_reguliers", "chat").answer == "S.a"
    assert build_task("fr.CP.dictee_simple", "bateau").answer == "bateau"
    assert build_task("math.CP.numeration_dizaines_unites", 47).answer == (4, 7)
    assert build_task("math.CP.comparaison_nombres", {"a": 8, "b": 12}).answer == "<"
    assert build_task("math.CP.add_within_20", {"a": 3, "b": 4}).answer == 7
    t = build_task("fr.CP.comprehension_phrase",
                   {"subject": "le chat", "verb": "mange", "obj": "la pomme", "qtype": "qui"})
    assert t.answer == "le chat"


def test_factory_rejects_unknown_node():
    with pytest.raises(TaskFactoryError):
        build_task("fr.CM2.unknown", "x")
    assert heldout_bank(NODE) and teaching_bank("math.CP.add_within_20")


# ---- runtime behaviour -----------------------------------------------------
def test_act_is_read_only():
    svc = BrainService(seed=7)
    before = svc.brain.procedural.graph(svc.brain.day)
    svc.act(NODE, "chat")
    assert svc.brain.procedural.graph(svc.brain.day) == before     # responding never learns


def test_feedback_drives_learning():
    svc = BrainService(seed=1)
    m0 = svc.brain.semantic.mastery(NODE)
    for _ in range(12):
        svc.feedback(NODE, "chat", correct=True)
    assert svc.brain.semantic.mastery(NODE) > m0


def test_replay_teaches_to_competence():
    svc = _taught()
    assert svc.evaluate(NODE)["accuracy"] >= 0.7


def test_evaluate_writes_nothing_to_state():
    """B: /evaluate must not learn, give feedback, consolidate, move the clock,
    or touch metacognition — the entire exported state is byte-identical after
    repeated independent evaluation (calibration included, it is computed by the
    oracle and never written back)."""
    svc = _taught()
    state_before = svc.brain.export_state()
    for _ in range(5):
        svc.evaluate(NODE)
    assert svc.brain.export_state() == state_before


def test_feedback_requires_a_known_node_and_builds_a_task():
    """C: no free-form teaching — feedback on an unknown node is refused, so the
    brain can never be taught off-curriculum without a reconstructable task."""
    svc = BrainService(seed=1)
    with pytest.raises(TaskFactoryError):
        svc.feedback("fr.CM2.unknown", "x", correct=True)


def test_diff_baseline_is_stable_across_calls():
    """D: the diff baseline is the snapshot stored at construction, not
    reconstructed per call — so repeated /diff use the same reference point."""
    svc = _taught()
    d1, d2 = svc.diff(), svc.diff()
    assert d1["snapshot_ids"]["before"] == svc.baseline_snapshot_id
    assert d1["snapshot_ids"]["before"] == d2["snapshot_ids"]["before"]
    assert d1["semantic_concepts_added"] == d2["semantic_concepts_added"]


def test_diff_and_genuine_verdict():
    svc = _taught()
    d = svc.diff()
    assert NODE in d["semantic_concepts_added"]
    assert d["mastered_skills"]
    assert svc.genuine_learning()["verdict"] == "GENUINE"
