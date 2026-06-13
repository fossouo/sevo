"""Experiment: does the brain actually get more capable on CP/CE1 maths?

Runs the full class-learning cycle from ``design/learning_lifecycle.json``:

    T0 freeze + cold pretest
      -> Emma teaches prerequisites (add/sub within 20, place value)
      -> Emma teaches the target nodes (addition with carry, subtraction with borrow)
      -> consolidation ("sleep")
      -> T1 immediate posttest (held-out items)
      -> advance 7 days -> T2 delayed posttest (retention)
      -> T3 transfer (addition within 1000, never taught) + fluid reasoning
      -> Intelligence_delta

It also runs two controls:
  * a transfer/efficiency control (learn the carry node WITH vs WITHOUT
    prerequisites) to show prerequisite skills make a new node faster to learn;
  * a Memorizer baseline to show the held-out/transfer gains are not leakage.

Run:  PYTHONPATH=src python3 experiments/run_cp_ce1_math.py
"""
from __future__ import annotations

import json
import sys

from sevo.baselines import MemorizerBrain
from sevo.brain import Brain
from sevo.curriculum.cp_ce1_math import (
    NODES,
    build_bank,
    reasoning_bank,
    transfer_bank,
)
from sevo.eval import assess_genuine_learning, compute_delta
from sevo.rng import Rng
from sevo.teacher import make_banks, teach_to_mastery

SEED = 7
TARGET_NODES = [
    "math.CP.add_within_20",
    "math.CP.sub_within_20",
    "math.CE1.add_within_100_nocarry",
    "math.CE1.add_within_100_carry",
    "math.CE1.sub_within_100_borrow",
]
HELDOUT_NODES = [
    "math.CE1.add_within_100_carry",
    "math.CE1.sub_within_100_borrow",
]


def _heldout_items(banks):
    items = []
    for nid in HELDOUT_NODES:
        items += banks[nid].heldout
    return items


def run() -> dict:
    rng = Rng(SEED)
    banks = make_banks(rng, TARGET_NODES)
    transfer = transfer_bank(rng)
    reasoning = reasoning_bank(rng)
    untaught = banks["math.CE1.add_within_100_carry"]  # reuse structure
    # Metacognition probe: never-taught multiplication node.
    from sevo.curriculum.cp_ce1_math import Problem
    mult_probe = [
        Problem(node_id="math.CE2.multiply_table", op="add", a=a, b=b,
                answer=a * b, required_skills={"multiply": 1.0})
        for a, b in [(3, 4), (6, 7), (8, 9), (2, 5)]
    ]

    brain = Brain(seed=SEED)

    # ---- T0: freeze + cold pretest -----------------------------------------
    snap_before = brain.snapshot()
    heldout = _heldout_items(banks)
    pre_heldout = brain.evaluate(heldout, "pretest.heldout")
    pre_transfer = brain.evaluate(transfer, "pretest.transfer")
    pre_reasoning = brain.evaluate(reasoning, "pretest.reasoning")
    pre_mult = brain.evaluate(mult_probe, "pretest.untaught_multiplication")

    # ---- Emma teaches (prerequisites first, then targets) ------------------
    teaching_log = []
    for nid in TARGET_NODES:
        teaching_log.append(teach_to_mastery(brain, nid, banks[nid]))

    # ---- consolidation ("sleep") -------------------------------------------
    consolidation = brain.consolidate(mode="sleep", advance_days=1)
    brain.consolidate(mode="error_replay", advance_days=0)

    # ---- T1 immediate posttest ---------------------------------------------
    t1_heldout = brain.evaluate(heldout, "posttest.t1.heldout")
    t1_transfer = brain.evaluate(transfer, "posttest.t1.transfer")
    t1_reasoning = brain.evaluate(reasoning, "posttest.t1.reasoning")
    t1_mult = brain.evaluate(mult_probe, "posttest.t1.untaught_multiplication")

    # ---- advance 7 days -> T2 delayed retention ----------------------------
    brain.advance_days(7)
    t2_heldout = brain.evaluate(heldout, "posttest.t2.delayed.heldout")
    snap_after = brain.snapshot(parent=snap_before.snapshot_id)

    # ---- transfer / learning-efficiency control ----------------------------
    eff = _efficiency_control(rng)

    # ---- memorizer baseline (anti-leakage control) -------------------------
    mem = _memorizer_control(banks, transfer)

    # ---- Intelligence_delta -------------------------------------------------
    delta = compute_delta(
        heldout_before=pre_heldout["accuracy"],
        heldout_after=t1_heldout["accuracy"],
        transfer_before=pre_transfer["accuracy"],
        transfer_after=t1_transfer["accuracy"],
        reasoning_before=pre_reasoning["accuracy"],
        reasoning_after=t1_reasoning["accuracy"],
        t1_after=t1_heldout["accuracy"],
        t2_after=t2_heldout["accuracy"],
        calibration_before=pre_heldout["calibration_error"],
        calibration_after=t1_heldout["calibration_error"],
        trials_with_prereq=eff["trials_with_prereq"],
        trials_without_prereq=eff["trials_without_prereq"],
    )

    genuine = assess_genuine_learning(
        heldout_before=pre_heldout["accuracy"], heldout_after=t1_heldout["accuracy"],
        transfer_before=pre_transfer["accuracy"], transfer_after=t1_transfer["accuracy"],
        memoriser_heldout=mem["on_heldout"]["accuracy"],
        memoriser_transfer=mem["on_transfer"]["accuracy"],
        t1_after=t1_heldout["accuracy"], t2_after=t2_heldout["accuracy"],
    )

    return {
        "seed": SEED,
        "snapshots": {"before": snap_before.snapshot_id, "after": snap_after.snapshot_id},
        "pretest": {"heldout": pre_heldout, "transfer": pre_transfer,
                    "reasoning": pre_reasoning, "untaught_multiplication": pre_mult},
        "teaching": teaching_log,
        "consolidation": consolidation,
        "posttest_immediate": {"heldout": t1_heldout, "transfer": t1_transfer,
                               "reasoning": t1_reasoning, "untaught_multiplication": t1_mult},
        "posttest_delayed_t2": {"heldout": t2_heldout},
        "transfer_efficiency_control": eff,
        "memorizer_baseline": mem,
        "intelligence_delta": delta,
        "genuine_learning": genuine,
    }


def _efficiency_control(rng: Rng, n_seeds: int = 6) -> dict:
    """Learn the carry node WITH vs WITHOUT prerequisites and compare trials to
    mastery. To be a fair, low-noise comparison each paired arm uses the *same*
    node bank and the *same* brain seed (the only difference is whether the
    prerequisites were trained first), and the result is averaged over several
    seeds with a fine stop granularity.
    """
    node = "math.CE1.add_within_100_carry"
    prereqs = ["math.CP.add_within_20", "math.CE1.add_within_100_nocarry"]
    with_trials: list[int] = []
    without_trials: list[int] = []

    for s in range(n_seeds):
        node_bank = build_bank(node, Rng(1000 + s))

        b_with = Brain(seed=2000 + s)
        for i, nid in enumerate(prereqs):
            teach_to_mastery(b_with, nid, build_bank(nid, Rng(3000 + s * 10 + i)))
        with_trials.append(teach_to_mastery(b_with, node, node_bank, session_size=4)["trials"])

        b_cold = Brain(seed=2000 + s)
        without_trials.append(teach_to_mastery(b_cold, node, node_bank, session_size=4)["trials"])

    mean_with = sum(with_trials) / len(with_trials)
    mean_without = sum(without_trials) / len(without_trials)
    return {
        "node": node,
        "n_seeds": n_seeds,
        "trials_with_prereq": round(mean_with, 2),
        "trials_without_prereq": round(mean_without, 2),
        "speedup": round(mean_without / mean_with, 3) if mean_with else None,
        "per_seed": {"with_prereq": with_trials, "without_prereq": without_trials},
    }


def _memorizer_control(banks, transfer) -> dict:
    """Memoriser sees every teaching item, then is tested on held-out+transfer."""
    mem = MemorizerBrain()
    for nid in HELDOUT_NODES:
        mem.memorize(banks[nid].teaching)
    from sevo.services import AssessmentOracle
    oracle = AssessmentOracle()
    heldout = _heldout_items(banks)
    on_teaching = oracle.assess(mem, [p for nid in HELDOUT_NODES for p in banks[nid].teaching], "memorizer.teaching")
    on_heldout = oracle.assess(mem, heldout, "memorizer.heldout")
    on_transfer = oracle.assess(mem, transfer, "memorizer.transfer")
    return {"on_teaching": on_teaching, "on_heldout": on_heldout, "on_transfer": on_transfer}


if __name__ == "__main__":
    result = run()
    json.dump(result, sys.stdout, indent=2, ensure_ascii=False)
    sys.stdout.write("\n")
