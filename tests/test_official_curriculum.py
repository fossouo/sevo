"""Official curriculum registry — CP programme ingested via the standard contract.

Proves the official programme is loaded class-by-class through the existing
ingestion contract (no brain change), that the richer official fields survive,
that every declared node has a runnable binding, and that an un-populated class
refuses to be ingested rather than being guessed.
"""
import pytest

from sevo.curriculum.ingestion import CurriculumRegistry
from sevo.curriculum.official_curriculum import (
    CE1_PROGRAM,
    CE2_PROGRAM,
    CP_PROGRAM,
    RUNNABLE_CP,
    official_ce1_registry,
    official_ce2_registry,
    official_cp_registry,
    register_class,
    runnable_for,
)


def test_cp_programme_ingests_via_contract():
    reg = official_cp_registry()
    # CP français (décodage, mots-outils, compréhension, syllabes, dictée) +
    # CP maths (add, sub, numération, comparaison)
    assert len(reg.by_class("CP")) == 9
    assert len(reg.by_subject("français")) == 5
    assert len(reg.by_subject("mathématiques")) == 4


def test_official_nodes_carry_rich_fields():
    reg = official_cp_registry()
    node = reg.get("fr.CP.lecture_mots_reguliers")
    assert node.discipline == "lecture / décodage"
    assert node.end_of_year_expectations            # attendus de fin d'année
    assert node.exercise_types                      # types d'exercices
    assert node.evaluation_criteria                 # critères d'évaluation
    assert abs(sum(node.required_skills.values()) - 1.0) < 1e-6


def test_every_program_node_has_a_runnable():
    program_ids = {n["id"] for n in CP_PROGRAM["nodes"]}
    assert program_ids == set(RUNNABLE_CP)
    # each runnable builds a non-empty teaching/held-out bank
    from sevo.rng import Rng
    for nid, rn in RUNNABLE_CP.items():
        bank = rn.build(Rng(1))
        assert bank.teaching and bank.heldout


def test_unpopulated_class_refuses_ingestion():
    reg = CurriculumRegistry()
    with pytest.raises(NotImplementedError):
        register_class(reg, "CM2")
    with pytest.raises(ValueError):
        register_class(reg, "Université")


def test_ce1_programme_ingests_via_same_contract():
    reg = official_ce1_registry()
    # CE1 français (pluriel ×2 + conjugaison) + CE1 maths (add nocarry/carry, sub borrow)
    assert len(reg.by_class("CE1")) == 6
    assert len(reg.by_subject("français")) == 3
    assert len(reg.by_subject("mathématiques")) == 3


def test_ce1_carries_rich_fields_like_cp():
    node = official_ce1_registry().get("fr.CE1.present_verbes_er")
    assert node.discipline and node.end_of_year_expectations
    assert node.exercise_types and node.evaluation_criteria
    assert abs(sum(node.required_skills.values()) - 1.0) < 1e-6


def test_ce1_is_extension_not_rewrite():
    """CE1 reuses pre-existing core nodes (plural / conjugation / maths within
    100) — no new core, every program node has a runnable."""
    ids = {n["id"] for n in CE1_PROGRAM["nodes"]}
    assert {"fr.CE1.pluriel_reguliers", "fr.CE1.present_verbes_er",
            "math.CE1.add_within_100_carry"} <= ids
    assert set(runnable_for("CE1")) == ids
    from sevo.rng import Rng
    for rn in runnable_for("CE1").values():
        bank = rn.build(Rng(1))
        assert bank.teaching and bank.heldout


def test_ce2_programme_ingests_via_same_contract():
    reg = official_ce2_registry()
    assert len(reg.by_class("CE2")) == 3            # add/sub within 1000 + invariable plurals
    assert len(reg.by_subject("mathématiques")) == 2
    assert len(reg.by_subject("français")) == 1


def test_ce2_is_extension_not_rewrite():
    ids = {n["id"] for n in CE2_PROGRAM["nodes"]}
    assert {"math.CE2.add_within_1000", "fr.CE2.pluriel_invariables"} <= ids
    assert set(runnable_for("CE2")) == ids
    from sevo.rng import Rng
    for rn in runnable_for("CE2").values():
        bank = rn.build(Rng(1))
        assert bank.teaching and bank.heldout
