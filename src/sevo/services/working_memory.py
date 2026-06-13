"""working_memory — cortex préfrontal dorsolatéral.

Bounded buffer that holds the goal and intermediate variables for the problem
currently being solved. Capacity is small (Miller-ish); the profile it exposes
(capacity estimate, multi-step depth) grows as procedures automate and free up
working-memory load.
"""
from __future__ import annotations


class WorkingMemory:
    def __init__(self, capacity: int = 4) -> None:
        self.capacity = capacity
        self.buffer: list = []
        self.max_depth_seen = 0

    def load(self, items: list) -> None:
        self.buffer = items[: self.capacity]
        self.max_depth_seen = max(self.max_depth_seen, len(items))

    def profile(self) -> dict:
        return {
            "capacity_tokens_estimate": self.capacity,
            "multi_step_depth": self.max_depth_seen,
            "distraction_sensitivity": 0.0,
        }
