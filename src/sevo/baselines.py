"""Baseline systems used to validate that the evaluation measures *intelligence*
and not memorisation.

``MemorizerBrain`` stores exact item -> answer pairs it has been shown and
replays them. On the teaching items it looks excellent; on the disjoint
held-out bank and the transfer bank it collapses to chance — and it stays
*overconfident* while doing so. If the real brain beats the memoriser on
held-out and transfer, the gain cannot be explained by leakage. The memoriser is
domain-agnostic: it keys on ``task.memo_key`` (works for maths and French alike).
"""
from __future__ import annotations


class MemorizerBrain:
    def __init__(self) -> None:
        self.table: dict = {}

    def memorize(self, tasks: list) -> None:
        for t in tasks:
            self.table[t.memo_key] = t.answer

    def attempt(self, task, learn: bool = False) -> dict:
        key = task.memo_key
        if key in self.table:
            return {"answer": self.table[key], "correct": True, "confidence": 0.9,
                    "error_type": None, "reliability": 1.0, "decision": "attempt"}
        # Never seen: confidently produces an answer it cannot actually derive.
        return {"answer": None, "correct": False, "confidence": 0.7,
                "error_type": "unmemorized", "reliability": 0.0, "decision": "attempt"}
