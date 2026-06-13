"""Learning dynamics — the brain must get genuinely more capable.

Guards the four signals that the design counts as *intelligence* rather than
memorisation: held-out gain, transfer to an unseen range, prerequisite-driven
learning efficiency, and consolidation-driven retention.
"""
from sevo.brain import Brain
from sevo.curriculum.cp_ce1_math import build_bank, transfer_bank
from sevo.rng import Rng
from sevo.teacher import teach_to_mastery


def test_learns_a_node_on_heldout_items():
    # Full lifecycle: cold pretest -> teach -> consolidate -> posttest, on a
    # DISJOINT held-out bank (no leakage from teaching items).
    brain = Brain(seed=2)
    bank = build_bank("math.CE1.add_within_100_carry", Rng(2))
    before = brain.evaluate(bank.heldout, "before")["accuracy"]
    teach_to_mastery(brain, "math.CE1.add_within_100_carry", bank)
    brain.consolidate(mode="sleep", advance_days=0)
    brain.consolidate(mode="error_replay", advance_days=0)
    after = brain.evaluate(bank.heldout, "after")["accuracy"]
    assert before <= 0.1
    assert after >= 0.7, (before, after)


def test_transfer_to_unseen_range():
    """Train base addition skills; solve addition within 1000 (never taught)."""
    brain = Brain(seed=4)
    for nid in ["math.CP.add_within_20", "math.CE1.add_within_100_nocarry",
                "math.CE1.add_within_100_carry"]:
        teach_to_mastery(brain, nid, build_bank(nid, Rng(4 + len(nid))))
    transfer_acc = brain.evaluate(transfer_bank(Rng(4)), "transfer")["accuracy"]
    assert transfer_acc >= 0.6, transfer_acc


def test_prerequisites_make_learning_faster():
    node = "math.CE1.add_within_100_carry"
    prereqs = ["math.CP.add_within_20", "math.CE1.add_within_100_nocarry"]

    with_prereq = Brain(seed=6)
    for nid in prereqs:
        teach_to_mastery(with_prereq, nid, build_bank(nid, Rng(6 + len(nid))))
    t_with = teach_to_mastery(with_prereq, node, build_bank(node, Rng(60)))["trials"]

    cold = Brain(seed=6)
    t_without = teach_to_mastery(cold, node, build_bank(node, Rng(60)))["trials"]

    assert t_with < t_without, (t_with, t_without)


def test_consolidation_improves_retention():
    """Same training; the consolidated brain retains far more after a 7-day delay."""
    node = "math.CE1.add_within_100_carry"

    def train(consolidate: bool):
        b = Brain(seed=8)
        bank = build_bank(node, Rng(8))
        teach_to_mastery(b, node, bank)
        if consolidate:
            b.consolidate(mode="sleep", advance_days=0)
            b.consolidate(mode="error_replay", advance_days=0)
        b.advance_days(7)
        return b.evaluate(bank.heldout, "t2")["accuracy"]

    retained_consolidated = train(consolidate=True)
    retained_raw = train(consolidate=False)
    assert retained_consolidated > retained_raw + 0.2, (retained_consolidated, retained_raw)
