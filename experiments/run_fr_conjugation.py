"""Experiment: a THIRD domain — French present-tense conjugation of -er verbs.

Same brain, same machinery as the maths and plural experiments. If the cognitive
core only worked for one or two rules it would be a lookup table; here it learns
a third, unrelated rule-based competency with the same held-out / transfer /
retention / anti-leakage guarantees, and the cross-domain shared skill
(``grapheme_recognition``) makes prerequisite practice transfer.

Run:  PYTHONPATH=src:experiments python3 experiments/run_fr_conjugation.py
"""
from __future__ import annotations

import json
import sys

from sevo.baselines import MemorizerBrain
from sevo.brain import Brain
from sevo.curriculum.fr_conjugation import (
    NODES_CONJ,
    build_bank_conj,
    transfer_bank_conj,
)
from sevo.curriculum.fr_cp_ce1 import build_bank_fr
from sevo.eval import compute_delta
from sevo.rng import Rng
from sevo.services import AssessmentOracle
from sevo.teacher import teach_to_mastery

SEED = 5
NODE = "fr.CE1.present_verbes_er"


def run() -> dict:
    rng = Rng(SEED)
    bank = build_bank_conj(NODE, rng.fork(NODE))
    heldout = bank.heldout
    transfer = transfer_bank_conj(NODE)

    brain = Brain(seed=SEED)
    snap_before = brain.snapshot()
    pre_held = brain.evaluate(heldout, "pretest.heldout")
    pre_tr = brain.evaluate(transfer, "pretest.transfer")

    teaching_log = [teach_to_mastery(brain, NODE, bank)]

    consolidation = brain.consolidate(mode="sleep", advance_days=1)
    brain.consolidate(mode="error_replay", advance_days=0)

    t1_held = brain.evaluate(heldout, "posttest.t1.heldout")
    t1_tr = brain.evaluate(transfer, "posttest.t1.transfer")

    brain.advance_days(7)
    t2_held = brain.evaluate(heldout, "posttest.t2.delayed.heldout")
    snap_after = brain.snapshot(parent=snap_before.snapshot_id)

    eff = _efficiency_control(rng)
    mem = _memorizer_control(bank, transfer)

    delta = compute_delta(
        heldout_before=pre_held["accuracy"], heldout_after=t1_held["accuracy"],
        transfer_before=pre_tr["accuracy"], transfer_after=t1_tr["accuracy"],
        # Generalising the conjugation rule to unseen verbs is the "fluid" part.
        reasoning_before=pre_tr["accuracy"], reasoning_after=t1_tr["accuracy"],
        t1_after=t1_held["accuracy"], t2_after=t2_held["accuracy"],
        calibration_before=pre_held["calibration_error"], calibration_after=t1_held["calibration_error"],
        trials_with_prereq=eff["trials_with_prereq"], trials_without_prereq=eff["trials_without_prereq"],
    )

    return {
        "seed": SEED,
        "domain": "français — présent des verbes en -er",
        "snapshots": {"before": snap_before.snapshot_id, "after": snap_after.snapshot_id},
        "pretest": {"heldout": pre_held, "transfer": pre_tr},
        "teaching": teaching_log,
        "consolidation": consolidation,
        "posttest_immediate": {"heldout": t1_held, "transfer": t1_tr},
        "posttest_delayed_t2": {"heldout": t2_held},
        "transfer_efficiency_control": eff,
        "memorizer_baseline": mem,
        "intelligence_delta": delta,
    }


def _efficiency_control(rng: Rng, n_seeds: int = 6) -> dict:
    """Cross-domain shared-skill transfer: learning the conjugation node is
    faster when the regular-plural node was learned first, because both share
    ``grapheme_recognition`` (recognising the relevant word ending)."""
    reg = "fr.CE1.pluriel_reguliers"
    with_trials, without_trials = [], []
    for s in range(n_seeds):
        conj_bank = build_bank_conj(NODE, Rng(7000 + s))
        b_with = Brain(seed=8000 + s)
        teach_to_mastery(b_with, reg, build_bank_fr(reg, Rng(9000 + s)))
        with_trials.append(teach_to_mastery(b_with, NODE, conj_bank, session_size=4)["trials"])
        b_cold = Brain(seed=8000 + s)
        without_trials.append(teach_to_mastery(b_cold, NODE, conj_bank, session_size=4)["trials"])
    mw = sum(with_trials) / len(with_trials)
    mo = sum(without_trials) / len(without_trials)
    return {
        "node": NODE, "shared_skill": "grapheme_recognition", "prereq_node": reg,
        "n_seeds": n_seeds, "trials_with_prereq": round(mw, 2),
        "trials_without_prereq": round(mo, 2),
        "speedup": round(mo / mw, 3) if mw else None,
        "per_seed": {"with_prereq": with_trials, "without_prereq": without_trials},
    }


def _memorizer_control(bank, transfer) -> dict:
    mem = MemorizerBrain()
    mem.memorize(bank.teaching)
    oracle = AssessmentOracle()
    return {
        "on_teaching": oracle.assess(mem, bank.teaching, "memorizer.teaching"),
        "on_heldout": oracle.assess(mem, bank.heldout, "memorizer.heldout"),
        "on_transfer": oracle.assess(mem, transfer, "memorizer.transfer"),
    }


if __name__ == "__main__":
    json.dump(run(), sys.stdout, indent=2, ensure_ascii=False)
    sys.stdout.write("\n")
