"""Brain — persistent cognitive architecture, exposed through the API surface.

Wires the ten MVP microservices over the event bus and implements the public API
from ``design/api_surface.json``:

    /perceive  /act  /learn/session  /learn/feedback  /consolidate
    /evaluate/pretest  /evaluate/posttest  /state/snapshot  /intelligence/delta

The brain owns a single virtual clock (``day``) so the protocol can run an
immediate test, then advance time and run a delayed test to measure retention.
"""
from __future__ import annotations

import time
import uuid

from .bus import Event, EventBus
from .curriculum.base import Task
from .curriculum.cp_ce1_math import SKILLS
from .curriculum.cp_maths_numeration import SKILLS_NUM
from .curriculum.fr_conjugation import SKILLS_CONJ
from .curriculum.fr_cp_ce1 import SKILLS_FR
from .curriculum.fr_lecture_cp import SKILLS_LECTURE
from .services import (
    AssessmentOracle,
    AttentionSalience,
    ConsolidationSleep,
    EpisodicMemory,
    ExecutiveControl,
    GlobalWorkspace,
    Metacognition,
    ProceduralMemory,
    SemanticMemory,
    SensoryGateway,
    WorkingMemory,
)
from .rng import Rng
from .state import CognitiveState, DevelopmentStage, Snapshot, take_snapshot

# A brain may traverse several domains, so by default it carries the union of
# all known procedural skills (unused skills stay inert at baseline
# automaticity). ``grapheme_recognition`` is shared between French domains, so
# we de-duplicate while preserving order.
ALL_SKILLS = list(dict.fromkeys(SKILLS + SKILLS_FR + SKILLS_CONJ + SKILLS_LECTURE + SKILLS_NUM))


class Brain:
    def __init__(self, seed: int = 0, skills: list[str] | None = None) -> None:
        self.brain_id = str(uuid.uuid4())
        self.rng = Rng(seed)
        self.day = 0
        self.bus = EventBus()

        # MVP services
        self.sensory = SensoryGateway()
        self.attention = AttentionSalience()
        self.workspace = GlobalWorkspace()
        self.wm = WorkingMemory()
        self.executive = ExecutiveControl()
        self.episodic = EpisodicMemory()
        self.semantic = SemanticMemory()
        self.procedural = ProceduralMemory(skills or ALL_SKILLS)
        self.metacog = Metacognition()
        self.consolidation = ConsolidationSleep()
        self.oracle = AssessmentOracle()

        self.stage = DevelopmentStage()
        self.snapshots: dict[str, Snapshot] = {}

    # -- low-level event helper ----------------------------------------------
    def _emit(self, topic: str, payload: dict, parents: list[str] | None = None) -> None:
        self.bus.publish(
            Event(topic=topic, payload=payload, brain_id=self.brain_id,
                  timestamp=time.time(), causal_parent_event_ids=parents or [])
        )

    # == API: /perceive =======================================================
    def perceive(self, modality: str, content, source: str) -> dict:
        percept = self.sensory.normalize(modality, content, source)
        sal = self.attention.salience(percept)
        self.workspace.broadcast("last_percept", percept)
        self._emit("percept.created", {"percept": percept, "salience": sal})
        return percept

    # == core attempt (shared by /act, learning and the oracle) ===============
    def attempt(self, problem: Task, learn: bool = True) -> dict:
        """Solve one problem.

        ``learn=False`` is the read-only path used by the assessment oracle: it
        touches NO learning memory (no episode, no practice, no mastery update).
        """
        confidence = self.metacog.estimate_confidence(problem, self.procedural, self.day)
        has_method = self.procedural.has_method(problem, self.day)
        decision = self.executive.decide(has_method, confidence)
        self.wm.load(problem.working_set)

        if decision == "ask_help":
            res = {"answer": None, "correct": False, "reliability": 0.0,
                   "error_type": "declined", "confidence": confidence, "decision": decision}
            if learn:
                self.metacog.request_help()
        else:
            solved = self.procedural.solve(problem, self.day, self.rng)
            solved["confidence"] = confidence
            solved["decision"] = decision
            res = solved

        if learn:
            correct = bool(res["correct"]) and decision != "ask_help"
            self._record(problem, correct, res.get("error_type"))
        return res

    def _record(self, problem: Task, correct: bool, error_type=None) -> None:
        """Write one corrected attempt into the learning memories. Shared by the
        bundled ``attempt`` path and the explicit Emma feedback path."""
        eid = self.episodic.encode(
            "attempt",
            {"node_id": problem.node_id, "required_skills": problem.required_skills,
             "correct": correct, "error_type": error_type},
            self.day,
        )
        self._emit("memory.episodic.encoded", {"episode_id": eid})
        # Emma's feedback = the brain learns from the corrected outcome.
        self.procedural.practice(problem, correct, self.day)
        self.semantic.observe_attempt(problem.node_id, correct, self.day)
        self.metacog.observe(problem.node_id, correct)
        self._emit("skill.procedure.updated", {"node_id": problem.node_id, "correct": correct})

    # == API: /act ============================================================
    def act(self, problem: Task) -> dict:
        return self.attempt(problem, learn=False)

    # == API: /learn/feedback =================================================
    def learn_from_feedback(self, problem: Task, correct: bool, error_type=None) -> None:
        """Apply Emma's structured feedback for one item. The brain learns from
        the *corrected outcome* — this is the write half of the teaching loop,
        decoupled from solving so an external teacher (Emma) can drive it via the
        API. Independent evaluation (the oracle) never goes through here."""
        self._record(problem, bool(correct), error_type)

    # == API: /learn/session + /learn/feedback ================================
    def learn_session(self, class_level: str, subject: str, problems: list[Task]) -> dict:
        """One Emma teaching session: a batch of exercises with feedback."""
        self.stage.school_class = class_level
        results = [self.attempt(p, learn=True) for p in problems]
        acc = sum(r["correct"] for r in results) / len(results) if results else 0.0
        self._emit("workspace.broadcast", {"session_subject": subject, "accuracy": acc})
        return {"class_level": class_level, "subject": subject, "n": len(problems), "accuracy": round(acc, 4)}

    # == API: /consolidate ====================================================
    def consolidate(self, mode: str = "sleep", advance_days: int = 1) -> dict:
        report = self.consolidation.run(self.episodic, self.procedural, self.semantic, mode, self.day)
        self._emit("neuromodulation.signal", {"phase": "consolidation", "mode": mode})
        self.day += advance_days  # "a night of sleep"
        return report

    def advance_days(self, days: int) -> None:
        self.day += days

    # == API: /evaluate/pretest + /posttest ===================================
    def evaluate(self, problems: list[Task], label: str) -> dict:
        # Oracle uses the read-only path; cannot teach.
        return self.oracle.assess(self, problems, label=label)

    # == API: /state/snapshot =================================================
    def snapshot(self, parent: str | None = None) -> Snapshot:
        cs = CognitiveState()
        cs.knowledge_mastery_graph = self.semantic.graph()
        cs.procedural_skill_graph = self.procedural.graph(self.day)
        cs.episodic_index = self.episodic.index()
        cs.working_memory_profile = self.wm.profile()
        snap = take_snapshot(self.stage, cs, self.day, parent)
        self.snapshots[snap.snapshot_id] = snap
        return snap

    # == Persistence ==========================================================
    def export_state(self) -> dict:
        """Serialise the brain's *learned* state to a JSON-able dict. This is
        what makes the brain persistent: the procedural skills, the semantic
        mastery graph, the metacognitive self-model, the clock and the stage —
        everything a CP-appris brain must keep across a save/reload."""
        return {
            "version": 1,
            "brain_id": self.brain_id,
            "day": self.day,
            "stage": {"school_class": self.stage.school_class,
                      "age_equivalent_months": self.stage.age_equivalent_months,
                      "curriculum_version": self.stage.curriculum_version},
            "procedural_skills": {s: dict(v) for s, v in self.procedural.skills.items()},
            "semantic_mastery": {n: dict(v) for n, v in self.semantic.mastery_graph.items()},
            "metacognition": {
                "node_self_accuracy": dict(self.metacog.node_self_accuracy),
                "help_requests": self.metacog.help_requests,
                "attempts": self.metacog.attempts,
            },
        }

    @classmethod
    def from_state(cls, state: dict, seed: int = 0) -> "Brain":
        """Rebuild a brain from ``export_state``. Skills present in the saved
        state overwrite the defaults; any newer skill keeps its baseline, so an
        old save still loads after the skill set grows."""
        brain = cls(seed=seed)
        brain.brain_id = state.get("brain_id", brain.brain_id)
        brain.day = state.get("day", 0)
        st = state.get("stage", {})
        brain.stage.school_class = st.get("school_class", "CP")
        brain.stage.age_equivalent_months = st.get("age_equivalent_months")
        brain.stage.curriculum_version = st.get("curriculum_version", "MEN-2026")
        for sid, v in state.get("procedural_skills", {}).items():
            if sid in brain.procedural.skills:
                brain.procedural.skills[sid].update(v)
            else:
                brain.procedural.skills[sid] = dict(v)
        brain.semantic.mastery_graph = {n: dict(v) for n, v in state.get("semantic_mastery", {}).items()}
        mc = state.get("metacognition", {})
        brain.metacog.node_self_accuracy = dict(mc.get("node_self_accuracy", {}))
        brain.metacog.help_requests = mc.get("help_requests", 0)
        brain.metacog.attempts = mc.get("attempts", 0)
        return brain
