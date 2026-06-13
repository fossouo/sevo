"""CM1 mathematics — multiplication tables (a NEW bottleneck skill).

CM1 introduces ``multiply_facts``, a skill no earlier class taught. It is the
perfect test of the developmental-curve hypothesis: place value is already known
(from CP), but multiplication is a *new* bottleneck — so a CE2-appris brain
should get **little transfer** on it (just as `carry` blocked CP→CE1), confirming
that each class's new skill gates transfer until it is learned.

Characteristic error: multiplication-as-addition (3 × 4 → 7), the classic early
confusion between the two operations.
"""
from __future__ import annotations

from dataclasses import dataclass, field

from .base import Task

SKILLS_CM1 = ["multiply_facts"]


@dataclass
class MultiplicationTask(Task):
    node_id: str
    a: int
    b: int
    answer: int
    required_skills: dict

    @property
    def prompt(self) -> str:
        return f"{self.a} × {self.b} = ?"

    @property
    def working_set(self) -> list:
        return [self.a, self.b, "mul"]

    def mistake(self, weak_skill: str) -> tuple:
        if weak_skill == "multiply_facts":
            wrong = self.a + self.b                 # multiplication-as-addition
            if wrong == self.answer:                # 2×2 == 2+2 — pick another wrong value
                wrong = self.answer - 1
            return wrong, "multiplication_as_addition"
        return self.answer - 1, "off_by_one_product"


NODES_CM1: dict[str, dict] = {
    "math.CM1.multiply_table": {
        "title": "Tables de multiplication",
        "prerequisites": [],
        "required_skills": {"multiply_facts": 1.0},
        "mastery_threshold": 0.8,
    },
}


def _make_mul(node_id: str, a: int, b: int) -> MultiplicationTask:
    return MultiplicationTask(node_id, a, b, a * b,
                              dict(NODES_CM1[node_id]["required_skills"]))


@dataclass
class Bank:
    teaching: list = field(default_factory=list)
    heldout: list = field(default_factory=list)


def build_bank_cm1(node_id: str, rng, frac_teach: float = 0.55) -> Bank:
    pairs = [(a, b) for a in range(2, 10) for b in range(2, 10)]
    rng.shuffle(pairs)
    cut = int(len(pairs) * frac_teach)
    return Bank(teaching=[_make_mul(node_id, a, b) for a, b in pairs[:cut]],
                heldout=[_make_mul(node_id, a, b) for a, b in pairs[cut:]])


def transfer_bank_cm1(node_id: str = "math.CM1.multiply_table") -> list:
    """Beyond the basic table (×11, ×12) — rule transfer to unseen products."""
    return [_make_mul(node_id, a, b) for a in range(2, 10) for b in (11, 12)]
