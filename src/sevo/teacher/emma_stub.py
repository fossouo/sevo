"""Emma — deterministic teacher adapter (offline, reproducible, zero LLM cost).

``design/docker_compose_blueprint.json`` envisions Emma as an LLM teacher
adapter. For the *self-test* of the brain we use a deterministic Emma instead:
it presents exercises from a node's teaching bank, gives feedback (the brain
learns from the corrected outcome), and keeps teaching until the node's mastery
crosses threshold or a session budget is exhausted.

Using a deterministic teacher is deliberate:
  * the learning result is fully reproducible (a measured Intelligence_delta can
    be replayed bit-for-bit), and
  * it isolates the *brain's* learning dynamics from any teacher cleverness.

The real-curriculum training with the live Emma (LiteLLM) plugs into the same
``learn_session`` API later.
"""
from __future__ import annotations

from ..curriculum.cp_ce1_math import Bank, NODES, build_bank
from ..rng import Rng


def teach_to_mastery(
    brain,
    node_id: str,
    bank: Bank,
    threshold: float | None = None,
    max_sessions: int = 30,
    session_size: int = 8,
) -> dict:
    """Teach one node until mastery. Returns trials-to-mastery (the headline
    learning-efficiency metric) so two brains can be compared on how *fast* they
    acquire the same node."""
    threshold = threshold if threshold is not None else NODES[node_id]["mastery_threshold"]
    teaching = bank.teaching
    trials = 0
    sessions = 0
    history: list[float] = []
    cursor = 0
    for _ in range(max_sessions):
        batch = []
        for _ in range(session_size):
            batch.append(teaching[cursor % len(teaching)])
            cursor += 1
        brain.learn_session(_class_of(node_id), "mathématiques", batch)
        trials += len(batch)
        sessions += 1
        m = brain.semantic.mastery(node_id)
        history.append(round(m, 4))
        if m >= threshold:
            break
    return {
        "node_id": node_id,
        "sessions": sessions,
        "trials": trials,
        "reached_mastery": brain.semantic.mastery(node_id) >= threshold,
        "final_mastery": round(brain.semantic.mastery(node_id), 4),
        "mastery_history": history,
    }


def _class_of(node_id: str) -> str:
    # "math.CE1.add_within_100_carry" -> "CE1"
    parts = node_id.split(".")
    return parts[1] if len(parts) > 1 else "CP"


def make_banks(rng: Rng, node_ids: list[str]) -> dict[str, Bank]:
    return {nid: build_bank(nid, rng.fork(nid)) for nid in node_ids}
