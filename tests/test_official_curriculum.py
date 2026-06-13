"""Official curriculum registry — CP programme ingested via the standard contract.

Proves the official programme is loaded class-by-class through the existing
ingestion contract (no brain change), that the richer official fields survive,
that every declared node has a runnable binding, and that an un-populated class
refuses to be ingested rather than being guessed.
"""
import pytest

from sevo.curriculum.ingestion import CurriculumRegistry
from sevo.curriculum.official_curriculum import (
    CP_PROGRAM,
    RUNNABLE_CP,
    official_cp_registry,
    register_class,
)


def test_cp_programme_ingests_via_contract():
    reg = official_cp_registry()
    # CP français (3 lecture/compréhension) + CP maths (2 nombres et calculs)
    assert len(reg.by_class("CP")) == 5
    assert len(reg.by_subject("français")) == 3
    assert len(reg.by_subject("mathématiques")) == 2


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
