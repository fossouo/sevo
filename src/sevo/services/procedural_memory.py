"""procedural_memory — ganglions de la base + cervelet (savoir-faire automatisé).

Holds the brain's executable skills and is the engine of *doing*: it solves
arithmetic problems by running noisy procedures whose reliability is a function
of skill automaticity. Low automaticity produces **characteristic** wrong
answers (the kinds of mistakes real children make), not random noise — which is
what lets consolidation target the right gap during error replay.

Learning model (kept deliberately simple and inspectable):

* reliability of a problem = weighted geometric mean of the required skills'
  *effective* automaticities (any near-zero skill tanks the whole procedure).
* practice with feedback raises automaticity via a power-law update; an **error
  with correction teaches more** than a success (error-driven learning), and the
  signal is concentrated on the bottleneck skill.
* effective automaticity decays with time-since-practice; consolidated skills
  decay far slower (Complementary Learning Systems: fast episodic trace vs slow
  durable cortical skill).
"""
from __future__ import annotations

import math

from ..curriculum.base import Task

EPS = 1e-3
LR_ERROR = 0.28   # learning rate when a corrected error is replayed
LR_OK = 0.07      # learning rate on a correct attempt
DECAY_UNCONSOLIDATED = 0.35
DECAY_CONSOLIDATED = 0.045


def _clamp(x: float, lo: float = EPS, hi: float = 1.0) -> float:
    return max(lo, min(hi, x))


class ProceduralMemory:
    def __init__(self, skills: list[str]) -> None:
        # Every skill starts essentially unlearned.
        self.skills: dict[str, dict] = {
            s: {
                "automaticity": 0.05,
                "error_patterns": [],
                "transfer_score": 0.0,
                "consolidated": False,
                "last_practiced_day": None,
            }
            for s in skills
        }

    # -- effective automaticity (with forgetting) ----------------------------
    def effective(self, skill: str, day: int) -> float:
        s = self.skills[skill]
        a = s["automaticity"]
        last = s["last_practiced_day"]
        if last is None or day <= last:
            return a
        k = DECAY_CONSOLIDATED if s["consolidated"] else DECAY_UNCONSOLIDATED
        return _clamp(a * math.exp(-k * (day - last)), lo=0.0)

    def reliability(self, task: Task, day: int) -> float:
        acc = 0.0
        for skill, w in task.required_skills.items():
            if skill not in self.skills:
                return 0.0  # the brain has no procedure for this at all
            acc += w * math.log(_clamp(self.effective(skill, day)))
        return math.exp(acc)

    def has_method(self, task: Task, day: int, threshold: float = 0.15) -> bool:
        """Does the brain have *any* usable procedure for this problem?

        This gates the decision to attempt vs. to say "I don't know". It is based
        on skill presence, NOT on recent success — a learner who keeps making
        carry errors still *has* an addition method and keeps trying; only the
        absence of a procedure (e.g. multiplication, never taught) is a genuine
        "I don't know". Decoupling the two avoids a learned-helplessness spiral
        where early failures would permanently suppress attempts.
        """
        present = [s for s in task.required_skills if s in self.skills]
        return bool(present) and max(self.effective(s, day) for s in present) >= threshold

    def bottleneck(self, task: Task, day: int) -> str:
        return min(
            (s for s in task.required_skills if s in self.skills),
            key=lambda s: self.effective(s, day),
            default=next(iter(task.required_skills)),
        )

    # -- solving --------------------------------------------------------------
    def solve(self, task, day: int, rng) -> dict:
        """Produce an answer. Correct with prob = reliability; otherwise a
        characteristic mistake driven by the weakest skill. Domain-agnostic:
        the *kind* of mistake is provided by ``task.mistake`` (see
        ``curriculum/base.py``)."""
        r = self.reliability(task, day)
        if rng.chance(r):
            return {"answer": task.answer, "correct": True, "reliability": r, "error_type": None}
        weak = self.bottleneck(task, day)
        answer, etype = task.mistake(weak)
        return {"answer": answer, "correct": task.grade(answer), "reliability": r, "error_type": etype}

    # -- learning -------------------------------------------------------------
    def practice(self, task: Task, correct: bool, day: int) -> None:
        weak = self.bottleneck(task, day)
        for skill, w in task.required_skills.items():
            if skill not in self.skills:
                continue
            s = self.skills[skill]
            if correct:
                gain = LR_OK * w * (1.0 - s["automaticity"])
            else:
                # Concentrate the correction signal on the bottleneck skill.
                focus = 1.0 if skill == weak else 0.3
                gain = LR_ERROR * w * focus * (1.0 - s["automaticity"])
            s["automaticity"] = _clamp(s["automaticity"] + gain)
            s["last_practiced_day"] = day
        if not correct:
            self.skills[weak]["error_patterns"].append({"node": task.node_id, "day": day})

    def consolidate(self, practiced_skills: set[str], mode: str, day: int) -> None:
        """Slow, durable update (replay during 'sleep'). Generalises recent
        practice into the cortical skill and lowers future forgetting."""
        for skill in practiced_skills:
            if skill not in self.skills:
                continue
            s = self.skills[skill]
            boost = 0.5 * (1.0 - s["automaticity"])
            if mode == "error_replay" and s["error_patterns"]:
                boost *= 1.4
            s["automaticity"] = _clamp(s["automaticity"] + boost)
            s["transfer_score"] = _clamp(s["transfer_score"] + 0.4 * (1.0 - s["transfer_score"]))
            s["consolidated"] = True

    # -- read-only views ------------------------------------------------------
    def graph(self, day: int) -> dict:
        return {
            skill: {
                "automaticity": round(self.effective(skill, day), 4),
                "error_patterns": list(s["error_patterns"]),
                "transfer_score": round(s["transfer_score"], 4),
                "consolidated": s["consolidated"],
                "last_practiced_day": s["last_practiced_day"],
            }
            for skill, s in self.skills.items()
        }
