"""Brain state diff — make the cognitive change *observable*.

The objective of CP hardening is not "the brain learned CP" but a measurable
internal state change:

    Brain CP-naïf → sessions Emma → consolidation → Brain CP-appris

``brain_state_diff`` takes the *before* and *after* snapshots (immutable copies of
the cognitive state, `design/brain_state_schema.json`) plus the behavioural
metrics measured by the oracle, and exports a structured JSON diff with the
seven facets the founder asked for:

* ``semantic_concepts_added`` — curriculum nodes whose mastery crossed the bar;
* ``procedural_rules_acquired`` — skills that went from absent to usable;
* ``mastered_skills`` — skills now automatic (with before/after automaticity);
* ``misconceptions_reduced`` — drop in the characteristic-error (wrong-answer)
  rate on the held-out bank;
* ``calibration_delta`` — improvement in metacognitive calibration;
* ``retention_traces`` — what survived the 7-day delay (consolidated skills + t2);
* ``learning_efficiency`` — prerequisite speed-up (transfer of skill).

It is purely a *reporting* transform over data the brain already produced — it
never teaches and never changes a score.
"""
from __future__ import annotations

MASTERY_BAR = 0.6          # a node counts as "acquired" above this mastery
RULE_USABLE = 0.6          # a procedural skill is "usable" above this automaticity
AUTOMATIC = 0.7            # a skill is "mastered/automatic" above this


def _mastery(snap) -> dict:
    return {nid: v.get("mastery", 0.0)
            for nid, v in snap.cognitive_state["knowledge_mastery_graph"].items()}


def _autom(snap) -> dict:
    return {sid: v.get("automaticity", 0.0)
            for sid, v in snap.cognitive_state["procedural_skill_graph"].items()}


def _consolidated(snap) -> set:
    return {sid for sid, v in snap.cognitive_state["procedural_skill_graph"].items()
            if v.get("consolidated")}


def brain_state_diff(
    before, after, *,
    heldout_before: float, heldout_after: float, transfer_after: float,
    calibration_before: float, calibration_after: float,
    t2_after: float, retention_ratio: float, learning_efficiency: float,
) -> dict:
    mb, ma = _mastery(before), _mastery(after)
    ab, aa = _autom(before), _autom(after)

    concepts_added = sorted(
        nid for nid in ma
        if ma[nid] >= MASTERY_BAR and mb.get(nid, 0.0) < MASTERY_BAR
    )
    rules_acquired = sorted(
        sid for sid in aa
        if aa[sid] >= RULE_USABLE and ab.get(sid, 0.0) < RULE_USABLE
    )
    mastered = {
        sid: {"before": round(ab.get(sid, 0.0), 3), "after": round(aa[sid], 3)}
        for sid in sorted(aa) if aa[sid] >= AUTOMATIC
    }

    return {
        "semantic_concepts_added": concepts_added,
        "procedural_rules_acquired": rules_acquired,
        "mastered_skills": mastered,
        "misconceptions_reduced": {
            "heldout_error_rate_before": round(1 - heldout_before, 3),
            "heldout_error_rate_after": round(1 - heldout_after, 3),
            "reduction": round((1 - heldout_before) - (1 - heldout_after), 3),
        },
        "calibration_delta": {
            "before": round(calibration_before, 3), "after": round(calibration_after, 3),
            "improvement": round(calibration_before - calibration_after, 3),
        },
        "retention_traces": {
            "t2_heldout_accuracy": round(t2_after, 3),
            "retention_ratio_t2_over_t1": round(retention_ratio, 3),
            "consolidated_skills": sorted(_consolidated(after)),
        },
        "learning_efficiency": round(learning_efficiency, 3),
        "snapshot_ids": {"before": before.snapshot_id, "after": after.snapshot_id},
        "transfer_after_best": round(transfer_after, 3),
    }
