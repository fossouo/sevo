"""Live exercise generation by Emma — training items only, leakage-guarded.

The strict contract (founder's), enforced here, not just by convention:

  1. **Emma generates TRAINING items only.** The model proposes content; the
     **curriculum** computes the correct answer (ground truth), never the model.
  2. **The oracle keeps the evaluations.** Generated items never reach the
     assessment path — the oracle grades on ``factory.heldout_bank`` only.
  3. **The leakage guard refuses any item too close to the probes.** Every
     generated item whose identity (``memo_key`` = node + exact content) appears
     in the node's held-out / transfer banks is dropped.

Inert by default: generation needs an injected transport (or ``SEVO_EMMA_LIVE``),
so unit tests stay offline (FakeTransport) and a live run is an explicit choice.
"""
from __future__ import annotations

from ..curriculum.factory import heldout_bank
from .emma_litellm import EmmaLiteLLM


class LiveExerciseGenerator:
    def __init__(self, emma: EmmaLiteLLM | None = None, seed: int = 0) -> None:
        self.emma = emma or EmmaLiteLLM()
        self.seed = seed

    def _probe_keys(self, node_id: str) -> set:
        """Identities of every evaluation item (held-out + transfer) for a node —
        the set a generated training item must NOT collide with."""
        keys = {t.memo_key for t in heldout_bank(node_id, self.seed)}
        from ..curriculum.fr_cp_ce1 import NODES_FR, transfer_bank_fr
        if node_id in NODES_FR:
            cat = NODES_FR[node_id]["category"]
            keys |= {t.memo_key for t in transfer_bank_fr() if t.category == cat}
        return keys

    def training_items(self, node_id: str, n: int, *, allowed_words: set | None = None,
                       oversample: int = 4) -> dict:
        """Generate up to ``n`` SAFE training items for a node. Returns the items
        plus an audit of how many proposals were dropped by the leakage guard."""
        probe_keys = self._probe_keys(node_id)
        proposed = self.emma.generate_french_tasks(
            node_id, n, oversample=oversample, allowed_words=allowed_words)
        safe, dropped = [], []
        for t in proposed:
            (dropped if t.memo_key in probe_keys else safe).append(t)
        return {
            "node_id": node_id,
            "items": safe[:n],
            "n_proposed": len(proposed),
            "n_dropped_as_probe_collision": len(dropped),
            "contract": "training-only · ground-truth from curriculum · leakage-guarded",
        }
