"""French domain — proves the cognitive core generalises beyond arithmetic.

Same guarantees as the maths tests, on a rule-based French competency (plural of
nouns): held-out gain, rule transfer to unseen words, anti-leakage, and the
emergence of the characteristic over-regularisation error ("chevals").
"""
from sevo.baselines import MemorizerBrain
from sevo.brain import Brain
from sevo.curriculum.fr_cp_ce1 import (
    NODES_FR,
    _make,
    build_bank_fr,
    transfer_bank_fr,
)
from sevo.rng import Rng
from sevo.services import AssessmentOracle
from sevo.teacher import teach_to_mastery


def _teach_all(seed=5):
    brain = Brain(seed=seed)
    banks = {n: build_bank_fr(n, Rng(seed).fork(n)) for n in NODES_FR}
    for n in NODES_FR:
        teach_to_mastery(brain, n, banks[n])
    brain.consolidate("sleep", 0)
    brain.consolidate("error_replay", 0)
    return brain, banks


def test_learns_french_plural_on_heldout():
    brain, banks = _teach_all()
    heldout = [t for n in NODES_FR for t in banks[n].heldout]
    assert brain.evaluate(heldout, "post")["accuracy"] >= 0.7


def test_rule_transfers_to_unseen_words():
    """The -s and -aux rules apply to words never seen in teaching."""
    brain, _ = _teach_all()
    transfer = transfer_bank_fr()
    assert brain.evaluate(transfer, "transfer")["accuracy"] >= 0.7


def test_memoriser_fails_on_unseen_french_words():
    rng = Rng(3)
    banks = {n: build_bank_fr(n, rng.fork(n)) for n in NODES_FR}
    mem = MemorizerBrain()
    for n in NODES_FR:
        mem.memorize(banks[n].teaching)
    oracle = AssessmentOracle()
    heldout = [t for n in NODES_FR for t in banks[n].heldout]
    assert oracle.assess(mem, [t for n in NODES_FR for t in banks[n].teaching], "t")["accuracy"] >= 0.99
    assert oracle.assess(mem, heldout, "h")["accuracy"] <= 0.1
    assert oracle.assess(mem, transfer_bank_fr(), "x")["accuracy"] <= 0.1


def test_characteristic_overregularisation_error():
    """A cold brain forming the plural of an -al word produces 'chevals'
    (over-regularised), the real child error — not random noise."""
    cold = Brain(seed=9)
    task = _make("fr.CE1.pluriel_en_al", "cheval")
    answers = {cold.procedural.solve(task, 0, cold.rng)["answer"] for _ in range(20)}
    assert "chevals" in answers          # the characteristic mistake appears
    assert task.answer == "chevaux"      # and the ground truth is correct


def test_same_brain_learns_both_domains():
    """One brain instance can hold maths and French skills simultaneously."""
    from sevo.curriculum.cp_ce1_math import build_bank as build_bank_math
    brain = Brain(seed=1)
    teach_to_mastery(brain, "math.CP.add_within_20", build_bank_math("math.CP.add_within_20", Rng(1)))
    teach_to_mastery(brain, "fr.CE1.pluriel_reguliers", build_bank_fr("fr.CE1.pluriel_reguliers", Rng(1)))
    assert brain.semantic.mastery("math.CP.add_within_20") >= 0.7
    assert brain.semantic.mastery("fr.CE1.pluriel_reguliers") >= 0.7
