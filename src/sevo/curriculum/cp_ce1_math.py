"""CP / CE1 mathematics curriculum (MVP environment).

This is the *external* environment the brain traverses — per
``design/curriculum_ingestion_contract.json`` the curriculum does NOT live in
the brain; it is injected and the brain turns it into memory traces and skills.

Design choice that makes learning measurable (and falsifiable):

* Curriculum **nodes** (e.g. "addition within 100 with carry") decompose into a
  small set of shared **base skills** with weights. Because nodes share base
  skills, mastering prerequisites makes a later node faster to learn — this is
  how *transfer* and *learning efficiency* emerge structurally instead of being
  hard-coded.
* Every problem carries the real arithmetic answer, so the assessment oracle
  grades genuine correctness — accuracy is a real function of the brain's
  internal skill state, not a coin flip.
* Teaching items and assessment items are drawn from **disjoint operand pools**
  (anti-leakage, ``evaluation_protocol.json``). A system that merely memorises
  seen pairs scores at chance on the held-out and transfer banks.
"""
from __future__ import annotations

from dataclasses import dataclass, field

from ..rng import Rng

# ---- Base skills (procedural primitives shared across nodes) ----------------
SKILLS = [
    "place_value",          # tens/units decomposition
    "add_facts_within_20",  # single-column addition facts
    "carry",                # propagating a carry to the tens column
    "sub_facts_within_20",  # single-column subtraction facts
    "borrow",               # borrowing across the tens column
]


@dataclass
class Problem:
    node_id: str
    op: str               # "add" | "sub"
    a: int
    b: int
    answer: int
    required_skills: dict  # skill_id -> weight (sums to 1.0)
    needs_carry: bool = False
    needs_borrow: bool = False

    @property
    def text(self) -> str:
        sign = "+" if self.op == "add" else "-"
        return f"{self.a} {sign} {self.b} = ?"


# ---- Curriculum nodes -------------------------------------------------------
# required_skills weights sum to 1.0; the weakest required skill is the
# bottleneck that gates correctness and gets the strongest learning signal.
NODES: dict[str, dict] = {
    "math.CP.add_within_20": {
        "title": "Addition jusqu'à 20",
        "prerequisites": [],
        "required_skills": {"add_facts_within_20": 1.0},
        "mastery_threshold": 0.8,
        "op": "add",
        "range": (1, 19),
    },
    "math.CE1.add_within_100_nocarry": {
        "title": "Addition jusqu'à 100 sans retenue",
        "prerequisites": ["math.CP.add_within_20"],
        "required_skills": {"place_value": 0.5, "add_facts_within_20": 0.5},
        "mastery_threshold": 0.8,
        "op": "add",
        "range": (10, 89),
    },
    "math.CE1.add_within_100_carry": {
        "title": "Addition jusqu'à 100 avec retenue",
        "prerequisites": ["math.CE1.add_within_100_nocarry"],
        "required_skills": {"place_value": 0.3, "add_facts_within_20": 0.3, "carry": 0.4},
        "mastery_threshold": 0.8,
        "op": "add",
        "range": (10, 89),
    },
    "math.CP.sub_within_20": {
        "title": "Soustraction jusqu'à 20",
        "prerequisites": [],
        "required_skills": {"sub_facts_within_20": 1.0},
        "mastery_threshold": 0.8,
        "op": "sub",
        "range": (1, 19),
    },
    "math.CE1.sub_within_100_borrow": {
        "title": "Soustraction jusqu'à 100 avec emprunt",
        "prerequisites": ["math.CP.sub_within_20"],
        "required_skills": {"place_value": 0.3, "sub_facts_within_20": 0.3, "borrow": 0.4},
        "mastery_threshold": 0.8,
        "op": "sub",
        "range": (10, 89),
    },
    # Never taught directly — used only to test "knows what it doesn't know".
    "math.CE2.multiply_table": {
        "title": "Tables de multiplication (NON enseigné — sonde métacognitive)",
        "prerequisites": [],
        "required_skills": {"place_value": 1.0},  # placeholder; brain lacks a mult skill
        "mastery_threshold": 0.8,
        "op": "add",
        "range": (2, 9),
        "untaught": True,
    },
}


def _make_add(node_id: str, a: int, b: int) -> Problem:
    spec = NODES[node_id]
    units_carry = (a % 10) + (b % 10) >= 10
    return Problem(
        node_id=node_id, op="add", a=a, b=b, answer=a + b,
        required_skills=dict(spec["required_skills"]), needs_carry=units_carry,
    )


def _make_sub(node_id: str, a: int, b: int) -> Problem:
    spec = NODES[node_id]
    needs_borrow = (a % 10) < (b % 10)
    return Problem(
        node_id=node_id, op="sub", a=a, b=b, answer=a - b,
        required_skills=dict(spec["required_skills"]), needs_borrow=needs_borrow,
    )


def _carry_required(node_id: str) -> bool:
    return "carry" in NODES[node_id]["required_skills"]


def _borrow_required(node_id: str) -> bool:
    return "borrow" in NODES[node_id]["required_skills"]


def _pool(node_id: str) -> list[Problem]:
    """Full deterministic pool of valid problems for a node."""
    spec = NODES[node_id]
    lo, hi = spec["range"]
    out: list[Problem] = []
    for a in range(lo, hi + 1):
        for b in range(lo, hi + 1):
            if spec["op"] == "add":
                if a + b > 99:
                    continue
                p = _make_add(node_id, a, b)
                if _carry_required(node_id) and not p.needs_carry:
                    continue
                if node_id == "math.CE1.add_within_100_nocarry" and p.needs_carry:
                    continue
            else:
                if a - b < 0:
                    continue
                p = _make_sub(node_id, a, b)
                if _borrow_required(node_id) and not p.needs_borrow:
                    continue
                if node_id == "math.CP.sub_within_20" and p.needs_borrow:
                    continue
            out.append(p)
    return out


@dataclass
class Bank:
    teaching: list[Problem] = field(default_factory=list)
    heldout: list[Problem] = field(default_factory=list)


def build_bank(node_id: str, rng: Rng, n_teach: int = 24, n_heldout: int = 24) -> Bank:
    """Split a node's pool into DISJOINT teaching and held-out sets.

    The same operand pair never appears in both sets, so improving on the
    held-out set cannot be explained by memorising teaching items.
    """
    pool = _pool(node_id)
    rng.shuffle(pool)
    teaching = pool[:n_teach]
    heldout = pool[n_teach : n_teach + n_heldout]
    # Safety: assert disjointness on (a, b).
    t_keys = {(p.a, p.b) for p in teaching}
    heldout = [p for p in heldout if (p.a, p.b) not in t_keys]
    return Bank(teaching=teaching, heldout=heldout)


# ---- Transfer & reasoning banks (structurally novel, never taught) ----------
def transfer_bank(rng: Rng, n: int = 20) -> list[Problem]:
    """Addition within 1000 — never taught as a node. Solvable only if the
    base skills (place value, add facts, carry) generalise beyond the trained
    operand range. A pure memoriser scores at chance here.
    """
    out: list[Problem] = []
    r = rng.fork("transfer")
    for _ in range(n):
        a = r.randint(100, 799)
        b = r.randint(100, 999 - a)  # 999 - a is >= 200, so the range is valid
        p = Problem(
            node_id="math.transfer.add_within_1000",
            op="add", a=a, b=b, answer=a + b,
            required_skills={"place_value": 0.34, "add_facts_within_20": 0.33, "carry": 0.33},
            needs_carry=((a % 10) + (b % 10)) >= 10,
        )
        out.append(p)
    return out


def reasoning_bank(rng: Rng, n: int = 16) -> list[Problem]:
    """Fluid-reasoning items: 'find the missing addend' a + ? = c, requiring the
    brain to *compose* its addition/subtraction skills in a new direction
    rather than recall a drilled fact.
    """
    out: list[Problem] = []
    r = rng.fork("reasoning")
    for _ in range(n):
        a = r.randint(11, 80)
        c = r.randint(a + 1, 99)
        missing = c - a
        # Solving a + ? = c == computing c - a (recombination of skills).
        p = Problem(
            node_id="math.reasoning.missing_addend",
            op="sub", a=c, b=a, answer=missing,
            required_skills={"place_value": 0.3, "sub_facts_within_20": 0.3, "borrow": 0.4},
            needs_borrow=(c % 10) < (a % 10),
        )
        out.append(p)
    return out
