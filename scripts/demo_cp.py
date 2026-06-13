"""Founder demo — the reproducible CP proof, end to end.

    Brain CP-naïf → Emma enseigne → Brain CP-appris → diff d'état
    → évaluation indépendante → verdict GENUINE → save/reload → ré-évaluation

Runs entirely in-process over the public runtime (no server needed), and writes
six proof artifacts. This is the scientific socle: it shows Sèvo is not "an LLM
answering exercises" but a brain-service that learns, transforms, keeps its
state, and is graded by an independent oracle.

    make demo-cp            # or: PYTHONPATH=src python3 scripts/demo_cp.py

Reproducibility note: substance (accuracies, verdict, acquired skills) is
deterministic for a fixed seed; only the random snapshot/brain UUIDs differ
between runs. The non-regression test asserts the substance, not the ids.
"""
from __future__ import annotations

import json
import os

from sevo.curriculum.factory import teaching_bank
from sevo.curriculum.official_curriculum import RUNNABLE_CP
from sevo.runtime import BrainService

SEED = 7
THRESHOLD = 0.8
MAX_SESSIONS = 8
REPRESENTATIVE = "fr.CP.lecture_mots_reguliers"
HERE = os.path.dirname(__file__)
ARTIFACTS = os.path.join(HERE, "..", "demo", "artifacts")


def _w(out: str, name: str, obj) -> None:
    with open(os.path.join(out, name), "w", encoding="utf-8") as f:
        json.dump(obj, f, indent=2, ensure_ascii=False)


# The only volatile fields are random UUIDs (brain_id, snapshot ids). They carry
# no information for the proof, so we normalise them to fixed placeholders to
# make the committed artifacts byte-stable run-to-run. Everything else
# (skills, accuracies, mastery, verdict) is deterministic for the fixed seed.
def _norm_state(state: dict) -> dict:
    return {**state, "brain_id": "demo-brain"}


def _norm_diff(diff: dict) -> dict:
    return {**diff, "snapshot_ids": {"before": "baseline", "after": "after"}}


def _teach_to_mastery(svc: BrainService, node: str):
    journals = []
    for _ in range(MAX_SESSIONS):
        journals.append(svc.teach_journaled(node, session_size=8))
        if svc.brain.semantic.mastery(node) >= THRESHOLD:
            break
    return journals


def run(out: str = ARTIFACTS) -> dict:
    out = os.path.abspath(out)
    os.makedirs(out, exist_ok=True)
    nodes = list(RUNNABLE_CP)

    # 1) Brain CP-naïf -------------------------------------------------------
    svc = BrainService(seed=SEED)
    brain_before = svc.brain_before

    # 2) Emma teaches every CP node (journaled, structured feedback) ---------
    rep_journal, summary = None, {}
    for n in nodes:
        js = _teach_to_mastery(svc, n)
        summary[n] = {"sessions": len(js),
                      "final_mastery": round(svc.brain.semantic.mastery(n), 4)}
        if n == REPRESENTATIVE:
            rep_journal = js[0]["journal"]            # one full session, for the format

    # 3) consolidation -> Brain CP-appris ------------------------------------
    svc.consolidate("sleep", advance_days=1)
    svc.consolidate("error_replay", advance_days=0)
    brain_after = svc.state()

    # 4) observable diff + 5) independent assessment + audit -----------------
    diff = svc.diff()
    assessment = {n: svc.evaluate(n) for n in nodes}
    verdict = svc.genuine_learning()
    audit = {n: svc.audit(n) for n in nodes}

    # 6) save -> reload -> re-evaluate ---------------------------------------
    state_path = os.path.join(out, "brain.json")
    svc.save(state_path)
    reloaded = BrainService.load(state_path)
    reassessment = {n: reloaded.evaluate(n) for n in nodes}
    reload_exact = (reloaded.brain.export_state()["procedural_skills"]
                    == svc.brain.export_state()["procedural_skills"])

    # non-regression signals -------------------------------------------------
    audit_clean = all(a["clean"] for a in audit.values())
    leakage_clean = audit_clean
    rsvc = BrainService(seed=SEED)
    sid = rsvc.start_session()
    for w in [t.word for t in teaching_bank(REPRESENTATIVE, SEED)[:6]]:
        rsvc.feedback(REPRESENTATIVE, w, correct=True)
    replay_deterministic = (rsvc.replay_session(sid)["replayed_state"]
                            == rsvc.replay_session(sid)["replayed_state"])

    # write the six proof artifacts -----------------------------------------
    _w(out, "brain_before.json", _norm_state(brain_before))
    _w(out, "brain_after.json", _norm_state(brain_after))
    _w(out, "brain_diff.json", _norm_diff(diff))
    _w(out, "assessment_report.json", {
        "per_node": assessment, "verdict": verdict,
        "reload_exact": reload_exact, "reassessment_after_reload": reassessment})
    _w(out, "emma_session_journal.json", {
        "representative_node": REPRESENTATIVE, "session": rep_journal,
        "all_nodes_summary": summary})
    _w(out, "audit_report.json", audit)

    result = {
        "verdict": verdict["verdict"],
        "genuine": verdict["passed"],
        "reload_exact": reload_exact,
        "audit_clean": audit_clean,
        "leakage_clean": leakage_clean,
        "replay_deterministic": replay_deterministic,
        "nodes_taught": len(nodes),
        "artifacts_dir": out,
    }
    return result


def main() -> None:
    r = run()
    print("=== Sèvo — Founder CP demo ===")
    print(f"  nodes taught (Emma, journaled) : {r['nodes_taught']}")
    print(f"  independent verdict            : {r['verdict']}")
    print(f"  save/reload exact              : {r['reload_exact']}")
    print(f"  audit clean (no leakage)       : {r['audit_clean']}")
    print(f"  replay deterministic           : {r['replay_deterministic']}")
    print(f"  artifacts                      : {r['artifacts_dir']}")
    ok = (r["genuine"] and r["reload_exact"] and r["audit_clean"]
          and r["replay_deterministic"])
    print(f"\nDEMO: {'PASS' if ok else 'FAIL'}")
    raise SystemExit(0 if ok else 1)


if __name__ == "__main__":
    main()
