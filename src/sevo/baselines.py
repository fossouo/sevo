"""Baseline systems used to validate that the evaluation measures *intelligence*
and not memorisation.

``MemorizerBrain`` stores exact (operator, a, b) -> answer pairs it has been
shown and replays them. On the teaching items it looks excellent; on the
disjoint held-out bank and the transfer bank it collapses to chance — and it
stays *overconfident* while doing so. If the real brain beats the memoriser on
held-out and transfer, the gain cannot be explained by leakage.
"""
from __future__ import annotations

from .curriculum.cp_ce1_math import Problem


class MemorizerBrain:
    def __init__(self) -> None:
        self.table: dict[tuple, int] = {}

    def memorize(self, problems: list[Problem]) -> None:
        for p in problems:
            self.table[(p.op, p.a, p.b)] = p.answer

    def attempt(self, problem: Problem, learn: bool = False) -> dict:
        key = (problem.op, problem.a, problem.b)
        if key in self.table:
            return {"answer": self.table[key], "correct": True, "confidence": 0.9,
                    "error_type": None, "reliability": 1.0, "decision": "attempt"}
        # Never seen: confidently guesses a plausible-but-wrong value.
        guess = problem.a  # an uninformed guess
        return {"answer": guess, "correct": guess == problem.answer, "confidence": 0.7,
                "error_type": "unmemorized", "reliability": 0.0, "decision": "attempt"}
