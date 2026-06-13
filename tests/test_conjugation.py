"""Third domain — French present-tense conjugation of -er verbs.

Same guarantees as the maths and plural tests on a *third*, unrelated rule:
held-out gain, rule transfer to unseen verbs, anti-leakage, the emergence of the
characteristic beginner errors, and cross-domain shared-skill transfer.
"""
from sevo.baselines import MemorizerBrain
from sevo.brain import Brain
from sevo.curriculum.fr_conjugation import (
    NODES_CONJ,
    _make_conj,
    build_bank_conj,
    conjugate,
    transfer_bank_conj,
    vet_verb,
)
from sevo.curriculum.fr_cp_ce1 import build_bank_fr
from sevo.rng import Rng
from sevo.services import AssessmentOracle
from sevo.teacher import teach_to_mastery

NODE = "fr.CE1.present_verbes_er"


def _teach(seed=5):
    brain = Brain(seed=seed)
    bank = build_bank_conj(NODE, Rng(seed).fork(NODE))
    teach_to_mastery(brain, NODE, bank)
    brain.consolidate("sleep", 0)
    brain.consolidate("error_replay", 0)
    return brain, bank


def test_conjugation_rule_is_correct():
    assert conjugate("parler", "nous") == "parlons"
    assert conjugate("chanter", "ils") == "chantent"
    assert conjugate("danser", "tu") == "danses"
    assert conjugate("aimer", "je") == "aime"


def test_learns_conjugation_on_heldout():
    brain, bank = _teach()
    assert brain.evaluate(bank.heldout, "post")["accuracy"] >= 0.7


def test_rule_transfers_to_unseen_verbs():
    brain, _ = _teach()
    assert brain.evaluate(transfer_bank_conj(), "transfer")["accuracy"] >= 0.7


def test_memoriser_fails_on_unseen_verbs():
    bank = build_bank_conj(NODE, Rng(3).fork(NODE))
    mem = MemorizerBrain()
    mem.memorize(bank.teaching)
    oracle = AssessmentOracle()
    assert oracle.assess(mem, bank.teaching, "t")["accuracy"] >= 0.99
    assert oracle.assess(mem, bank.heldout, "h")["accuracy"] <= 0.1
    assert oracle.assess(mem, transfer_bank_conj(), "x")["accuracy"] <= 0.1


def test_characteristic_infinitive_error():
    """A cold brain writes the infinitive instead of conjugating — the real
    beginner error, not random noise."""
    cold = Brain(seed=9)
    task = _make_conj(NODE, "parler", "nous")
    answers = {cold.procedural.solve(task, 0, cold.rng)["answer"] for _ in range(30)}
    assert "parler" in answers          # the characteristic mistake appears
    assert task.answer == "parlons"     # and the ground truth is correct


def test_prior_domain_does_not_break_conjugation():
    """Honest negative control: conjugation's hard skill (the endings) is NOT
    shared with the plural domain, so prior plural training gives little or no
    head start — but it must not *prevent* learning either. (Strong shared-skill
    transfer is demonstrated in the plural experiment, where the shared skill
    carries more weight; transfer is proportional to shared structure.)"""
    reg = "fr.CE1.pluriel_reguliers"
    warm = Brain(seed=22)
    teach_to_mastery(warm, reg, build_bank_fr(reg, Rng(33)))
    warm_log = teach_to_mastery(warm, NODE, build_bank_conj(NODE, Rng(11)), session_size=4)
    assert warm_log["reached_mastery"]


def test_vet_verb_filters_irregular_and_spelling_change():
    assert vet_verb("parler") and vet_verb("chanter") and vet_verb("cuisiner")
    assert not vet_verb("aller")        # irregular
    assert not vet_verb("manger")       # -ger (nous mangeons)
    assert not vet_verb("commencer")    # -cer (nous commençons)
    assert not vet_verb("payer")        # -yer (je paie)
    assert not vet_verb("espérer")      # stem change (j'espère)
    assert not vet_verb("finir")        # not -er
    assert not vet_verb("manger un peu")  # garbage


def test_same_brain_learns_three_domains():
    """One brain holds maths, plural, and conjugation skills at once."""
    from sevo.curriculum.cp_ce1_math import build_bank as build_bank_math
    brain = Brain(seed=1)
    teach_to_mastery(brain, "math.CP.add_within_20", build_bank_math("math.CP.add_within_20", Rng(1)))
    teach_to_mastery(brain, "fr.CE1.pluriel_reguliers", build_bank_fr("fr.CE1.pluriel_reguliers", Rng(1)))
    teach_to_mastery(brain, NODE, build_bank_conj(NODE, Rng(1)))
    assert brain.semantic.mastery("math.CP.add_within_20") >= 0.7
    assert brain.semantic.mastery("fr.CE1.pluriel_reguliers") >= 0.7
    assert brain.semantic.mastery(NODE) >= 0.7
