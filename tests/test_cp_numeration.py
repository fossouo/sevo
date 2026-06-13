"""CP numération — décomposition dizaines/unités and number comparison.

Same guarantees: held-out gain, intra-grade transfer to unseen numbers,
anti-leakage, diagnostic errors (place-value swap, reversed comparison).
"""
from sevo.baselines import MemorizerBrain
from sevo.brain import Brain
from sevo.curriculum.cp_maths_numeration import (
    _comp,
    _decomp,
    build_bank_num,
    transfer_bank_num,
)
from sevo.rng import Rng
from sevo.services import AssessmentOracle
from sevo.teacher import teach_to_mastery

DECOMP = "math.CP.numeration_dizaines_unites"
COMP = "math.CP.comparaison_nombres"


def _teach(node, seed=7):
    brain = Brain(seed=seed)
    bank = build_bank_num(node, Rng(seed).fork(node))
    teach_to_mastery(brain, node, bank)
    brain.consolidate("sleep", 1)
    brain.consolidate("error_replay", 0)
    return brain, bank


def test_decomposition_learns_and_transfers():
    brain, bank = _teach(DECOMP)
    assert brain.evaluate(bank.heldout, "post")["accuracy"] >= 0.7
    assert brain.evaluate(transfer_bank_num(DECOMP), "tr")["accuracy"] >= 0.6


def test_comparison_learns_and_transfers():
    brain, bank = _teach(COMP)
    assert brain.evaluate(bank.heldout, "post")["accuracy"] >= 0.7
    assert brain.evaluate(transfer_bank_num(COMP), "tr")["accuracy"] >= 0.4


def test_decomposition_answer_is_tens_units():
    assert _decomp(DECOMP, 47).answer == (4, 7)
    assert _comp(COMP, 8, 12).answer == "<"      # tens beats units
    assert _comp(COMP, 30, 30).answer == "="


def test_memoriser_fails_on_unseen_numbers():
    bank = build_bank_num(DECOMP, Rng(3).fork(DECOMP))
    mem = MemorizerBrain()
    mem.memorize(bank.teaching)
    oracle = AssessmentOracle()
    assert oracle.assess(mem, bank.teaching, "t")["accuracy"] >= 0.99
    assert oracle.assess(mem, transfer_bank_num(DECOMP), "x")["accuracy"] <= 0.2


def test_characteristic_place_value_swap():
    cold = Brain(seed=9)
    task = _decomp(DECOMP, 47)
    answers = {cold.procedural.solve(task, 0, cold.rng)["answer"] for _ in range(30)}
    assert (7, 4) in answers          # swapped tens/units
    assert task.answer == (4, 7)


def test_characteristic_reversed_comparison():
    cold = Brain(seed=9)
    task = _comp(COMP, 12, 8)         # truth ">"
    answers = {cold.procedural.solve(task, 0, cold.rng)["answer"] for _ in range(30)}
    assert "<" in answers             # reversed sign
    assert task.answer == ">"


# ---- CM1 multiplication (new bottleneck skill) -----------------------------
def test_cm1_multiplication_learns_and_memoriser_fails():
    from sevo.brain import Brain
    from sevo.curriculum.cm1_maths import build_bank_cm1, transfer_bank_cm1, _make_mul
    from sevo.teacher import teach_to_mastery
    NODE = "math.CM1.multiply_table"
    brain = Brain(seed=7)
    bank = build_bank_cm1(NODE, Rng(7).fork(NODE))
    teach_to_mastery(brain, NODE, bank)
    brain.consolidate("sleep", 1)
    assert brain.evaluate(bank.heldout, "post")["accuracy"] >= 0.7
    assert brain.evaluate(transfer_bank_cm1(), "tr")["accuracy"] >= 0.5
    mem = MemorizerBrain(); mem.memorize(bank.teaching)
    assert AssessmentOracle().assess(mem, bank.heldout, "h")["accuracy"] <= 0.1


def test_cm1_characteristic_multiplication_as_addition():
    from sevo.brain import Brain
    from sevo.curriculum.cm1_maths import _make_mul
    cold = Brain(seed=9)
    task = _make_mul("math.CM1.multiply_table", 3, 4)   # 3×4=12
    answers = {cold.procedural.solve(task, 0, cold.rng)["answer"] for _ in range(30)}
    assert 7 in answers and task.answer == 12           # confuses × with + (3+4)
