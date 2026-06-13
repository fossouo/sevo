"""CP grade — the full school-year cycle on a whole class, end to end.

Proves the complete learning lifecycle (`design/learning_lifecycle.json`) on the
**CP** class as ingested from the official programme
(`curriculum/official_curriculum.py`): a naive brain sits a cold pretest, Emma
(deterministic, offline) teaches every CP node — French *decoding*, *sight
words*, *sentence comprehension*, and the two maths *number/calculation* nodes —
the brain consolidates, then sits an immediate posttest, a +7-day delayed
posttest, and transfer probes on items never taught (including pseudo-words).

The progression report keeps the five facets separate, per the brief:
**connaissance** (held-out), **procédure** (skill automaticities), **transfert**
(unseen items / pseudo-words), **rétention** (delayed), **métacognition**
(calibration). Every gain is checked against a memoriser baseline.

Run:  PYTHONPATH=src:experiments python3 experiments/run_cp_grade.py
"""
from __future__ import annotations

import json
import sys

from sevo.baselines import MemorizerBrain
from sevo.brain import Brain
from sevo.curriculum.cp_ce1_math import build_bank as build_bank_math
from sevo.curriculum.official_curriculum import CP_PROGRAM, RUNNABLE_CP, official_cp_registry
from sevo.eval import assess_genuine_learning, compute_delta
from sevo.rng import Rng
from sevo.services import AssessmentOracle
from sevo.teacher import teach_to_mastery

SEED = 7


def _mean(xs):
    xs = [x for x in xs if x is not None]
    return sum(xs) / len(xs) if xs else 0.0


def run() -> dict:
    registry = official_cp_registry()           # official CP programme via the contract
    rng = Rng(SEED)
    nodes = list(RUNNABLE_CP.values())
    banks = {rn.node_id: rn.build(rng.fork(rn.node_id)) for rn in nodes}

    brain = Brain(seed=SEED)
    snap_before = brain.snapshot()

    # --- pretest (cold) ---
    pre = {}
    for rn in nodes:
        held = brain.evaluate(banks[rn.node_id].heldout, f"pre.{rn.node_id}")
        tr = brain.evaluate(rn.transfer(), f"pre.transfer.{rn.node_id}") if rn.transfer else None
        pre[rn.node_id] = {"heldout": held, "transfer": tr}

    # --- teaching (Emma) ---
    teaching = [teach_to_mastery(brain, rn.node_id, banks[rn.node_id]) for rn in nodes]

    # --- consolidation ---
    consolidation = brain.consolidate("sleep", advance_days=1)
    brain.consolidate("error_replay", advance_days=0)

    # --- immediate posttest ---
    t1 = {}
    for rn in nodes:
        held = brain.evaluate(banks[rn.node_id].heldout, f"t1.{rn.node_id}")
        tr = brain.evaluate(rn.transfer(), f"t1.transfer.{rn.node_id}") if rn.transfer else None
        t1[rn.node_id] = {"heldout": held, "transfer": tr}

    # --- delayed posttest (+7 days) — retention ---
    brain.advance_days(7)
    t2 = {rn.node_id: brain.evaluate(banks[rn.node_id].heldout, f"t2.{rn.node_id}") for rn in nodes}
    snap_after = brain.snapshot(parent=snap_before.snapshot_id)

    # --- controls ---
    eff = _efficiency_control()
    mem = _memorizer_control(banks, nodes)
    errors = _characteristic_errors()

    # --- aggregate facets ---
    held_pre = _mean([pre[n]["heldout"]["accuracy"] for n in banks])
    held_t1 = _mean([t1[n]["heldout"]["accuracy"] for n in banks])
    held_t2 = _mean([t2[n]["accuracy"] for n in banks])
    tr_pre = _mean([pre[n]["transfer"]["accuracy"] for n in banks if pre[n]["transfer"]])
    tr_t1 = _mean([t1[n]["transfer"]["accuracy"] for n in banks if t1[n]["transfer"]])
    cal_pre = _mean([pre[n]["heldout"]["calibration_error"] for n in banks])
    cal_t1 = _mean([t1[n]["heldout"]["calibration_error"] for n in banks])

    delta = compute_delta(
        heldout_before=held_pre, heldout_after=held_t1,
        transfer_before=tr_pre, transfer_after=tr_t1,
        reasoning_before=tr_pre, reasoning_after=tr_t1,
        t1_after=held_t1, t2_after=held_t2,
        calibration_before=cal_pre, calibration_after=cal_t1,
        trials_with_prereq=eff["trials_with_prereq"],
        trials_without_prereq=eff["trials_without_prereq"],
    )

    # Integrity gate: a brain is only declared "more capable" if it clears ALL
    # the anti-illusion checks. "transfer in at least one domain" => the BEST
    # per-node transfer, not the (conservative) aggregate that mixes the
    # deliberately out-of-grade maths probe.
    best_tr_after = max((t1[n]["transfer"]["accuracy"] for n in banks
                         if t1[n]["transfer"]), default=0.0)
    best_tr_before = max((pre[n]["transfer"]["accuracy"] for n in banks
                          if pre[n]["transfer"]), default=0.0)
    genuine = assess_genuine_learning(
        heldout_before=held_pre, heldout_after=held_t1,
        transfer_before=best_tr_before, transfer_after=best_tr_after,
        memoriser_heldout=mem["on_heldout"]["accuracy"],
        memoriser_transfer=mem["on_transfer"]["accuracy"],
        t1_after=held_t1, t2_after=held_t2,
    )

    return {
        "grade": "CP", "seed": SEED,
        "program": {"status": CP_PROGRAM["status"], "disclaimer": CP_PROGRAM["disclaimer"],
                    "disciplines": CP_PROGRAM["disciplines"],
                    "nodes_ingested": sorted(registry.nodes)},
        "snapshots": {"before": snap_before.snapshot_id, "after": snap_after.snapshot_id},
        "facets_aggregate": {
            "connaissance_heldout": {"pre": round(held_pre, 4), "t1": round(held_t1, 4)},
            "transfert": {"pre": round(tr_pre, 4), "t1": round(tr_t1, 4)},
            "retention_t2": round(held_t2, 4),
            "metacognition_calibration_error": {"pre": round(cal_pre, 4), "t1": round(cal_t1, 4)},
        },
        "per_node": {
            rn.node_id: {
                "subject": rn.subject, "discipline": rn.discipline,
                "heldout": {"pre": round(pre[rn.node_id]["heldout"]["accuracy"], 3),
                            "t1": round(t1[rn.node_id]["heldout"]["accuracy"], 3),
                            "t2": round(t2[rn.node_id]["accuracy"], 3)},
                "transfer_t1": (round(t1[rn.node_id]["transfer"]["accuracy"], 3)
                                if t1[rn.node_id]["transfer"] else None),
            } for rn in nodes
        },
        "procedure_skill_graph": brain.procedural.graph(brain.day),
        "teaching": teaching,
        "consolidation": consolidation,
        "efficiency_control": eff,
        "memorizer_baseline": mem,
        "characteristic_errors": errors,
        "intelligence_delta": delta,
        "genuine_learning": genuine,
    }


def _efficiency_control(n_seeds: int = 6) -> dict:
    """Within-maths shared-skill transfer at CP: learning subtraction after
    addition (both touch place value / number facts) vs from cold."""
    add, sub = "math.CP.add_within_20", "math.CP.sub_within_20"
    with_t, without_t = [], []
    for s in range(n_seeds):
        sub_bank = build_bank_math(sub, Rng(7100 + s))
        b_with = Brain(seed=8100 + s)
        teach_to_mastery(b_with, add, build_bank_math(add, Rng(9100 + s)))
        with_t.append(teach_to_mastery(b_with, sub, sub_bank, session_size=4)["trials"])
        b_cold = Brain(seed=8100 + s)
        without_t.append(teach_to_mastery(b_cold, sub, sub_bank, session_size=4)["trials"])
    mw, mo = sum(with_t) / len(with_t), sum(without_t) / len(without_t)
    return {"prereq": add, "node": sub, "shared": "place_value / number facts",
            "n_seeds": n_seeds, "trials_with_prereq": round(mw, 2),
            "trials_without_prereq": round(mo, 2),
            "speedup": round(mo / mw, 3) if mw else None}


def _memorizer_control(banks, nodes) -> dict:
    mem = MemorizerBrain()
    teaching, heldout, transfer = [], [], []
    for rn in nodes:
        mem.memorize(banks[rn.node_id].teaching)
        teaching += banks[rn.node_id].teaching
        heldout += banks[rn.node_id].heldout
        if rn.transfer:
            transfer += rn.transfer()
    oracle = AssessmentOracle()
    return {
        "on_teaching": oracle.assess(mem, teaching, "mem.teaching"),
        "on_heldout": oracle.assess(mem, heldout, "mem.heldout"),
        "on_transfer": oracle.assess(mem, transfer, "mem.transfer"),
    }


def _characteristic_errors() -> dict:
    """One diagnostic error per CP domain, produced by a cold brain."""
    from sevo.curriculum.fr_lecture_cp import _reading_task, _sentence_tasks

    cold = Brain(seed=9)
    out = {}
    reg = _reading_task("fr.CP.lecture_mots_reguliers", "chat", "reg")
    out["lecture_reguliers"] = _err(cold, reg)
    irr = _reading_task("fr.CP.lecture_mots_irreguliers", "femme", "irr")
    out["lecture_irreguliers"] = _err(cold, irr)
    comp = _sentence_tasks("fr.CP.comprehension_phrase", "le chat", "mange", "la pomme")[0]
    out["comprehension"] = _err(cold, comp)
    add = build_bank_math("math.CP.add_within_20", Rng(9)).heldout[0]
    out["maths_addition"] = _err(cold, add)
    return out


def _err(brain: Brain, task) -> dict:
    samples = {}
    for _ in range(30):
        r = brain.procedural.solve(task, 0, brain.rng)
        if not r["correct"]:
            samples[str(r["answer"])] = r["error_type"]
    return {"word_or_item": str(getattr(task, "word", task.prompt)),
            "truth": str(task.answer), "observed_errors": samples}


if __name__ == "__main__":
    json.dump(run(), sys.stdout, indent=2, ensure_ascii=False)
    sys.stdout.write("\n")
