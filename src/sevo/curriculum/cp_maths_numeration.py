"""CP mathematics — numération (whole numbers to 100).

Complements the CP arithmetic nodes with the *number-sense* competencies of the
CP programme: decomposing a number into tens and units, and comparing numbers.
Both reuse the shared ``place_value`` skill (so prerequisite practice transfers),
and ``comparaison`` introduces a ``number_comparison`` skill.

Teaching, held-out and an explicit **intra-grade** transfer set are drawn from
disjoint number ranges (10–79 taught/held-out, 80–99 transfer) so transfer
measures rule application to unseen numbers *of the same grade*, not an
out-of-grade probe.
"""
from __future__ import annotations

from dataclasses import dataclass, field

from .base import Task

SKILLS_NUM = ["number_comparison"]   # place_value is reused from cp_ce1_math


@dataclass
class DecompositionTask(Task):
    node_id: str
    n: int
    answer: tuple              # (tens, units)
    required_skills: dict

    @property
    def prompt(self) -> str:
        return f"Décompose {self.n} en dizaines et unités : ?"

    @property
    def working_set(self) -> list:
        return [self.n]

    def mistake(self, weak_skill: str) -> tuple:
        t, u = self.n // 10, self.n % 10
        if weak_skill == "place_value":
            return (u, t), "place_value_swap"      # 47 -> (7, 4)
        return (0, self.n), "no_decomposition"


@dataclass
class ComparisonTask(Task):
    node_id: str
    a: int
    b: int
    answer: str                # ">" | "<" | "="
    required_skills: dict

    @property
    def prompt(self) -> str:
        return f"Compare {self.a} et {self.b} (< > =) : ?"

    @property
    def working_set(self) -> list:
        return [self.a, self.b]

    def mistake(self, weak_skill: str) -> tuple:
        if weak_skill == "number_comparison":
            wrong = "<" if self.a >= self.b else ">"   # reversed sign
            return wrong, "reversed_comparison"
        if weak_skill == "place_value":
            # compares units only (ignores the tens column)
            ua, ub = self.a % 10, self.b % 10
            sign = ">" if ua > ub else "<" if ua < ub else "="
            return sign, "compared_units_only"
        return "=", "no_comparison"


NODES_NUM: dict[str, dict] = {
    "math.CP.numeration_dizaines_unites": {
        "title": "Numération : dizaines et unités (≤ 99)",
        "kind": "decomposition",
        "required_skills": {"place_value": 1.0},
        "mastery_threshold": 0.8,
    },
    "math.CP.comparaison_nombres": {
        "title": "Comparaison de nombres (≤ 100)",
        "kind": "comparison",
        "required_skills": {"number_comparison": 0.7, "place_value": 0.3},
        "mastery_threshold": 0.8,
    },
}


def _decomp(node_id: str, n: int) -> DecompositionTask:
    return DecompositionTask(node_id, n, (n // 10, n % 10),
                             dict(NODES_NUM[node_id]["required_skills"]))


def _comp(node_id: str, a: int, b: int) -> ComparisonTask:
    ans = ">" if a > b else "<" if a < b else "="
    return ComparisonTask(node_id, a, b, ans, dict(NODES_NUM[node_id]["required_skills"]))


@dataclass
class Bank:
    teaching: list = field(default_factory=list)
    heldout: list = field(default_factory=list)


def _comparison_pairs(rng, numbers: list, count: int) -> list:
    pairs, seen = [], set()
    nums = list(numbers)
    guard = 0
    while len(pairs) < count and guard < count * 20:
        guard += 1
        a, b = rng.choice(nums), rng.choice(nums)
        if (a, b) in seen:
            continue
        seen.add((a, b))
        pairs.append((a, b))
    return pairs


def build_bank_num(node_id: str, rng, frac_teach: float = 0.55) -> Bank:
    kind = NODES_NUM[node_id]["kind"]
    if kind == "decomposition":
        numbers = list(range(10, 80))
        rng.shuffle(numbers)
        cut = int(len(numbers) * frac_teach)
        return Bank(teaching=[_decomp(node_id, n) for n in numbers[:cut]],
                    heldout=[_decomp(node_id, n) for n in numbers[cut:]])
    # comparison
    pairs = _comparison_pairs(rng, list(range(1, 80)), 60)
    cut = int(len(pairs) * frac_teach)
    return Bank(teaching=[_comp(node_id, a, b) for a, b in pairs[:cut]],
                heldout=[_comp(node_id, a, b) for a, b in pairs[cut:]])


def transfer_bank_num(node_id: str = "math.CP.numeration_dizaines_unites") -> list:
    """Intra-grade transfer: same competency, numbers in the 80–99 band never
    used in teaching/held-out (which use 10–79)."""
    # Transfer numbers live strictly in the 80–99 band — disjoint from the
    # 10–79 teaching/held-out range, so a memoriser cannot have seen them.
    kind = NODES_NUM[node_id]["kind"]
    if kind == "decomposition":
        return [_decomp(node_id, n) for n in [83, 99, 91, 87, 80, 95, 88, 96]]
    return [_comp(node_id, a, b) for a, b in
            [(85, 90), (99, 80), (88, 88), (80, 95), (93, 87), (90, 89)]]
