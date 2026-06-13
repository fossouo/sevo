"""Evaluation protocol and Intelligence_delta computation.

Implements the comparison contract of ``design/evaluation_protocol.json`` and the
weighted formula of ``design/metrics_intelligence.json``:

    weighted_delta = knowledge_gain*0.30 + transfer_gain*0.25
                   + reasoning_gain*0.20 + retention_gain*0.10
                   + metacognition_gain*0.10 + learning_efficiency_gain*0.05

Every component is measured by the assessment oracle on **held-out / transfer /
delayed** banks, never on teaching items. The score is an internal cognitive
evolution index, NOT a human IQ.
"""
from __future__ import annotations

from dataclasses import asdict, dataclass

WEIGHTS = {
    "knowledge_gain": 0.30,
    "transfer_gain": 0.25,
    "reasoning_gain": 0.20,
    "retention_gain": 0.10,
    "metacognition_gain": 0.10,
    "learning_efficiency_gain": 0.05,
}


def _clamp(x: float) -> float:
    return max(-1.0, min(1.0, x))


@dataclass
class Components:
    knowledge_gain: float
    transfer_gain: float
    reasoning_gain: float
    retention_gain: float
    metacognition_gain: float
    learning_efficiency_gain: float

    def weighted_delta(self) -> float:
        return sum(WEIGHTS[k] * _clamp(v) for k, v in asdict(self).items())


def compute_delta(
    *,
    heldout_before: float,
    heldout_after: float,
    transfer_before: float,
    transfer_after: float,
    reasoning_before: float,
    reasoning_after: float,
    t1_after: float,
    t2_after: float,
    calibration_before: float,
    calibration_after: float,
    trials_with_prereq: int,
    trials_without_prereq: int,
) -> dict:
    knowledge_gain = heldout_after - heldout_before
    transfer_gain = transfer_after - transfer_before
    reasoning_gain = reasoning_after - reasoning_before
    # Durable knowledge that survives a delay, above the cold baseline.
    retention_gain = t2_after - heldout_before
    # Lower calibration error after learning is a positive metacognitive gain.
    metacognition_gain = calibration_before - calibration_after
    # Did prerequisites make the target node faster to learn? (transfer of skill)
    if trials_without_prereq > 0:
        learning_efficiency_gain = 1.0 - (trials_with_prereq / trials_without_prereq)
    else:
        learning_efficiency_gain = 0.0

    comp = Components(
        knowledge_gain=knowledge_gain,
        transfer_gain=transfer_gain,
        reasoning_gain=reasoning_gain,
        retention_gain=retention_gain,
        metacognition_gain=metacognition_gain,
        learning_efficiency_gain=learning_efficiency_gain,
    )
    return {
        "components": {k: round(v, 4) for k, v in asdict(comp).items()},
        "weights": WEIGHTS,
        "weighted_delta": round(comp.weighted_delta(), 4),
        "retention_ratio_t2_over_t1": round(t2_after / t1_after, 4) if t1_after else 0.0,
        "note": "Internal cognitive evolution index — not a human IQ.",
    }
