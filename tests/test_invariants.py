"""Design invariants — the properties that make the evaluation trustworthy.

These guard the cardinal rules from ``design/evaluation_protocol.json`` and
``design/api_surface.json``:

* the assessment oracle never teaches (no write to learning memory);
* a pure memoriser cannot fake the score on held-out / transfer items;
* the brain stays honestly unconfident on never-taught material.
"""
import copy

from sevo.baselines import MemorizerBrain
from sevo.brain import Brain
from sevo.curriculum.cp_ce1_math import build_bank, transfer_bank
from sevo.rng import Rng
from sevo.services import AssessmentOracle
from sevo.teacher import teach_to_mastery


def _trained_brain(seed=11):
    brain = Brain(seed=seed)
    for i, nid in enumerate(["math.CP.add_within_20", "math.CE1.add_within_100_nocarry",
                             "math.CE1.add_within_100_carry"]):
        teach_to_mastery(brain, nid, build_bank(nid, Rng(seed + i)))
    return brain


def test_pretest_is_cold():
    brain = Brain(seed=1)
    bank = build_bank("math.CE1.add_within_100_carry", Rng(1))
    res = brain.evaluate(bank.heldout, "pretest")
    assert res["accuracy"] <= 0.1, res


def test_oracle_does_not_teach():
    """Running an assessment must not change procedural or semantic memory."""
    brain = _trained_brain()
    bank = build_bank("math.CE1.add_within_100_carry", Rng(99))
    before_proc = copy.deepcopy(brain.procedural.skills)
    before_sem = copy.deepcopy(brain.semantic.mastery_graph)
    before_ep = brain.episodic.index()["episodes_count"]

    brain.evaluate(bank.heldout, "audit")
    brain.evaluate(transfer_bank(Rng(5)), "audit2")

    assert brain.procedural.skills == before_proc, "oracle mutated procedural memory"
    assert brain.semantic.mastery_graph == before_sem, "oracle mutated semantic memory"
    assert brain.episodic.index()["episodes_count"] == before_ep, "oracle wrote episodes"


def test_memorizer_cannot_fake_the_score():
    """A memoriser aces seen items but collapses on held-out + transfer."""
    rng = Rng(3)
    bank = build_bank("math.CE1.add_within_100_carry", rng)
    transfer = transfer_bank(rng)
    mem = MemorizerBrain()
    mem.memorize(bank.teaching)
    oracle = AssessmentOracle()

    on_teaching = oracle.assess(mem, bank.teaching, "teach")["accuracy"]
    on_heldout = oracle.assess(mem, bank.heldout, "held")["accuracy"]
    on_transfer = oracle.assess(mem, transfer, "trans")["accuracy"]

    assert on_teaching >= 0.99
    assert on_heldout <= 0.1
    assert on_transfer <= 0.1


def test_knows_what_it_does_not_know():
    """After training arithmetic, the brain stays unconfident on never-taught
    multiplication (no procedure exists)."""
    from sevo.curriculum.cp_ce1_math import Problem
    brain = _trained_brain()
    mult = [Problem("math.CE2.multiply_table", "add", a, b, a * b, {"multiply": 1.0})
            for a, b in [(3, 4), (6, 7), (8, 9)]]
    res = brain.evaluate(mult, "untaught")
    assert res["accuracy"] == 0.0
    assert res["mean_confidence"] <= 0.15
    assert res["knows_unknowns"] >= 0.8
