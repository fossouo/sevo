"""Persistence — a saved-then-reloaded brain keeps its competences.

This is the core promise of the runtime: the CP-appris brain is durable, not a
transient of one process.
"""
from sevo.brain import Brain
from sevo.curriculum.fr_lecture_cp import build_bank_lecture
from sevo.rng import Rng
from sevo.runtime import BrainService
from sevo.teacher import teach_to_mastery

NODE = "fr.CP.lecture_mots_reguliers"


def _trained():
    b = Brain(seed=7)
    teach_to_mastery(b, NODE, build_bank_lecture(NODE, Rng(7).fork(NODE)))
    b.consolidate("sleep", 0)
    b.consolidate("error_replay", 0)
    return b


def test_export_import_round_trip_is_exact():
    b = _trained()
    s = b.export_state()
    b2 = Brain.from_state(s, seed=7)
    assert b2.export_state()["procedural_skills"] == s["procedural_skills"]
    assert b2.export_state()["semantic_mastery"] == s["semantic_mastery"]
    assert b2.semantic.mastery(NODE) == b.semantic.mastery(NODE)
    assert b2.day == b.day and b2.stage.school_class == b.stage.school_class


def test_from_state_keeps_default_for_skill_absent_in_save():
    """An older save missing a newer skill still loads; the absent skill keeps
    its baseline rather than crashing."""
    s = _trained().export_state()
    s["procedural_skills"].pop("borrow", None)
    b2 = Brain.from_state(s, seed=7)
    assert "borrow" in b2.procedural.skills          # default restored


def test_service_save_load_preserves_competence(tmp_path):
    svc = BrainService(seed=7)
    for _ in range(6):
        svc.replay_emma_session(NODE)
    svc.consolidate("sleep", 1)
    svc.consolidate("error_replay", 0)
    mastery = svc.brain.semantic.mastery(NODE)

    path = str(tmp_path / "brain_cp.json")
    svc.save(path)
    reloaded = BrainService.load(path, seed=7)

    assert reloaded.brain.export_state()["procedural_skills"] == \
        svc.brain.export_state()["procedural_skills"]
    assert reloaded.brain.semantic.mastery(NODE) == mastery
