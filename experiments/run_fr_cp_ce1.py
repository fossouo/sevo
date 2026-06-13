"""Experiment: does the SAME brain get more capable on CP/CE1 French too?

Same machinery as the maths experiment, different domain (plural of nouns). This
is the generalisation proof: if the cognitive core only worked for arithmetic it
would be a calculator, not a brain. Here it learns a rule-based French competency
with the same held-out / transfer / retention / anti-leakage guarantees.

Run:  PYTHONPATH=src:experiments python3 experiments/run_fr_cp_ce1.py
"""
from __future__ import annotations

import json
import sys

from sevo.baselines import MemorizerBrain
from sevo.brain import Brain
from sevo.curriculum.fr_cp_ce1 import (
    NODES_FR,
    build_bank_fr,
    transfer_bank_fr,
)
from sevo.eval import assess_genuine_learning, compute_delta
from sevo.rng import Rng
from sevo.services import AssessmentOracle
from sevo.teacher import teach_to_mastery

SEED = 5
NODES = list(NODES_FR)  # reguliers, en_al, invariables


def _split_transfer(bank):
    reg = [t for t in bank if t.category == "reg"]
    al = [t for t in bank if t.category == "al"]
    return reg, al


def run() -> dict:
    rng = Rng(SEED)
    banks = {n: build_bank_fr(n, rng.fork(n)) for n in NODES}
    heldout = [t for n in NODES for t in banks[n].heldout]
    transfer = transfer_bank_fr()
    transfer_reg, transfer_al = _split_transfer(transfer)

    brain = Brain(seed=SEED)
    snap_before = brain.snapshot()
    pre_held = brain.evaluate(heldout, "pretest.heldout")
    pre_treg = brain.evaluate(transfer_reg, "pretest.transfer_regular")
    pre_tal = brain.evaluate(transfer_al, "pretest.transfer_al_rule")

    teaching_log = [teach_to_mastery(brain, n, banks[n]) for n in NODES]

    consolidation = brain.consolidate(mode="sleep", advance_days=1)
    brain.consolidate(mode="error_replay", advance_days=0)

    t1_held = brain.evaluate(heldout, "posttest.t1.heldout")
    t1_treg = brain.evaluate(transfer_reg, "posttest.t1.transfer_regular")
    t1_tal = brain.evaluate(transfer_al, "posttest.t1.transfer_al_rule")

    brain.advance_days(7)
    t2_held = brain.evaluate(heldout, "posttest.t2.delayed.heldout")
    snap_after = brain.snapshot(parent=snap_before.snapshot_id)

    eff = _efficiency_control(rng)
    mem = _memorizer_control(banks, transfer)

    delta = compute_delta(
        heldout_before=pre_held["accuracy"], heldout_after=t1_held["accuracy"],
        transfer_before=pre_treg["accuracy"], transfer_after=t1_treg["accuracy"],
        # The -al -> -aux rule is the "fluid" part: generalising a non-obvious
        # rule to unseen words rather than recalling a drilled item.
        reasoning_before=pre_tal["accuracy"], reasoning_after=t1_tal["accuracy"],
        t1_after=t1_held["accuracy"], t2_after=t2_held["accuracy"],
        calibration_before=pre_held["calibration_error"], calibration_after=t1_held["calibration_error"],
        trials_with_prereq=eff["trials_with_prereq"], trials_without_prereq=eff["trials_without_prereq"],
    )

    genuine = assess_genuine_learning(
        heldout_before=pre_held["accuracy"], heldout_after=t1_held["accuracy"],
        transfer_before=max(pre_treg["accuracy"], pre_tal["accuracy"]),
        transfer_after=max(t1_treg["accuracy"], t1_tal["accuracy"]),
        memoriser_heldout=mem["on_heldout"]["accuracy"],
        memoriser_transfer=mem["on_transfer"]["accuracy"],
        t1_after=t1_held["accuracy"], t2_after=t2_held["accuracy"],
    )

    return {
        "seed": SEED,
        "domain": "français — pluriel des noms",
        "genuine_learning": genuine,
        "snapshots": {"before": snap_before.snapshot_id, "after": snap_after.snapshot_id},
        "pretest": {"heldout": pre_held, "transfer_regular": pre_treg, "transfer_al_rule": pre_tal},
        "teaching": teaching_log,
        "consolidation": consolidation,
        "posttest_immediate": {"heldout": t1_held, "transfer_regular": t1_treg, "transfer_al_rule": t1_tal},
        "posttest_delayed_t2": {"heldout": t2_held},
        "transfer_efficiency_control": eff,
        "memorizer_baseline": mem,
        "intelligence_delta": delta,
    }


def _efficiency_control(rng: Rng, n_seeds: int = 6) -> dict:
    """Shared-skill transfer: learning the -al node is faster when the regular
    node was learned first (both share ``grapheme_recognition``)."""
    al = "fr.CE1.pluriel_en_al"
    reg = "fr.CE1.pluriel_reguliers"
    with_trials, without_trials = [], []
    for s in range(n_seeds):
        al_bank = build_bank_fr(al, Rng(7000 + s))
        b_with = Brain(seed=8000 + s)
        teach_to_mastery(b_with, reg, build_bank_fr(reg, Rng(9000 + s)))
        with_trials.append(teach_to_mastery(b_with, al, al_bank, session_size=4)["trials"])
        b_cold = Brain(seed=8000 + s)
        without_trials.append(teach_to_mastery(b_cold, al, al_bank, session_size=4)["trials"])
    mw = sum(with_trials) / len(with_trials)
    mo = sum(without_trials) / len(without_trials)
    return {
        "node": al, "shared_skill": "grapheme_recognition", "n_seeds": n_seeds,
        "trials_with_prereq": round(mw, 2), "trials_without_prereq": round(mo, 2),
        "speedup": round(mo / mw, 3) if mw else None,
        "per_seed": {"with_prereq": with_trials, "without_prereq": without_trials},
    }


def _memorizer_control(banks, transfer) -> dict:
    mem = MemorizerBrain()
    for n in NODES:
        mem.memorize(banks[n].teaching)
    oracle = AssessmentOracle()
    heldout = [t for n in NODES for t in banks[n].heldout]
    teaching = [t for n in NODES for t in banks[n].teaching]
    return {
        "on_teaching": oracle.assess(mem, teaching, "memorizer.teaching"),
        "on_heldout": oracle.assess(mem, heldout, "memorizer.heldout"),
        "on_transfer": oracle.assess(mem, transfer, "memorizer.transfer"),
    }


if __name__ == "__main__":
    json.dump(run(), sys.stdout, indent=2, ensure_ascii=False)
    sys.stdout.write("\n")
