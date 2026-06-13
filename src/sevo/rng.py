"""Deterministic RNG.

Every stochastic decision in the brain (whether a noisy procedure fires
correctly, exploration vs exploitation, etc.) draws from a single seeded
generator so that experiments are fully reproducible. This matters for the
evaluation protocol: a measured ``Intelligence_delta`` must be replayable.
"""
from __future__ import annotations

import hashlib
import random


class Rng:
    """Thin wrapper around :class:`random.Random` with a named seed."""

    def __init__(self, seed: int = 0) -> None:
        self.seed = seed
        self._r = random.Random(seed)

    def random(self) -> float:
        return self._r.random()

    def chance(self, p: float) -> bool:
        """True with probability ``p`` (clamped to [0, 1])."""
        return self._r.random() < max(0.0, min(1.0, p))

    def randint(self, a: int, b: int) -> int:
        return self._r.randint(a, b)

    def choice(self, seq):
        return self._r.choice(seq)

    def shuffle(self, seq) -> None:
        self._r.shuffle(seq)

    def fork(self, tag: str) -> "Rng":
        """Derive a child generator deterministically from a string tag.

        Uses a stable hash (sha256), NOT Python's builtin ``hash``, which is
        salted per process (``PYTHONHASHSEED``) and would make runs
        non-reproducible across invocations.
        """
        digest = hashlib.sha256(f"{self.seed}:{tag}".encode()).hexdigest()
        return Rng(int(digest[:8], 16))
