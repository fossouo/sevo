"""Domain-agnostic task interface.

The brain's cognitive core (procedural reliability, bottleneck, consolidation,
metacognition, the oracle) is independent of any subject. A *domain* (maths,
French, …) plugs in by providing **tasks** that conform to this interface:

* ``required_skills`` — which procedural skills the task exercises, with weights.
* ``answer`` — the ground-truth solution (any type: int, str, …).
* ``mistake(weak_skill)`` — the *characteristic* wrong answer produced when the
  weakest required skill fails (a forgotten carry, an over-regularised plural…),
  so that errors are diagnostic rather than random noise.
* ``working_set`` — what working memory must hold to attempt the task.
* ``prompt`` — what the teacher shows the learner.

Keeping this interface tiny is what lets the same Intelligence_delta machinery
measure learning in maths and in French without special-casing either.
"""
from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any


class Task(ABC):
    node_id: str
    required_skills: dict
    answer: Any

    @abstractmethod
    def mistake(self, weak_skill: str) -> tuple[Any, str]:
        """Return (wrong_answer, error_type) for the given bottleneck skill."""

    @property
    @abstractmethod
    def working_set(self) -> list:
        """Items working memory must hold to attempt this task."""

    @property
    def prompt(self) -> str:
        return f"{self.node_id}: ?"

    def grade(self, response: Any) -> bool:
        return response == self.answer

    @property
    def memo_key(self) -> tuple:
        """Identity for a pure memoriser: the node plus the exact item content.
        Two items of the same node with different content (held-out operands, a
        different word) get different keys, so memorising teaching items gives no
        credit on the disjoint held-out / transfer banks."""
        return (self.node_id, tuple(self.working_set))
