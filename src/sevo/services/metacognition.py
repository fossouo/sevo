"""metacognition_self_model — préfrontal médian / monitoring d'erreur.

Estimates what the brain knows and *what it does not know*. Crucially, its
confidence is built from the brain's own observed self-accuracy history (an EMA
per node), NOT from the ground-truth reliability — so calibration is a capacity
that has to be *learned*, and its improvement is a real, measurable signal.

It also carries an explicit "I don't know" detector: when the required skills do
not exist or are essentially unlearned, confidence collapses to a floor. This is
what lets the brain stay correctly unconfident on never-taught material.
"""
from __future__ import annotations

CONF_PRIOR = 0.5      # starts mildly overconfident -> poor calibration before learning
UNKNOWN_FLOOR = 0.1
SKILL_PRESENCE_THRESHOLD = 0.15


class Metacognition:
    def __init__(self) -> None:
        self.node_self_accuracy: dict[str, float] = {}
        self.help_requests = 0
        self.attempts = 0

    def estimate_confidence(self, problem, procedural, day: int) -> float:
        present = [s for s in problem.required_skills if s in procedural.skills]
        if not present:
            return UNKNOWN_FLOOR
        if max(procedural.effective(s, day) for s in present) < SKILL_PRESENCE_THRESHOLD:
            return UNKNOWN_FLOOR  # "I have no working procedure for this"
        return self.node_self_accuracy.get(problem.node_id, CONF_PRIOR)

    def observe(self, node_id: str, correct: bool, alpha: float = 0.3) -> None:
        prev = self.node_self_accuracy.get(node_id, CONF_PRIOR)
        self.node_self_accuracy[node_id] = (1 - alpha) * prev + alpha * (1.0 if correct else 0.0)
        self.attempts += 1

    def request_help(self) -> None:
        self.help_requests += 1

    def profile(self) -> dict:
        return {
            "calibration_error": 0.0,  # filled by the oracle at assessment time
            "knows_unknowns_score": 0.0,
            "help_seeking_quality": round(self.help_requests / self.attempts, 4) if self.attempts else 0.0,
        }
