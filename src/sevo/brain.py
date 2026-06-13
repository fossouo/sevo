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
from .curriculum.cp_ce1_math import SKILLS, Problem
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
        self.procedural = ProceduralMemory(skills or SKILLS)
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
    def attempt(self, problem: Problem, learn: bool = True) -> dict:
        """Solve one problem.

        ``learn=False`` is the read-only path used by the assessment oracle: it
        touches NO learning memory (no episode, no practice, no mastery update).
        """
        confidence = self.metacog.estimate_confidence(problem, self.procedural, self.day)
        has_method = self.procedural.has_method(problem, self.day)
        decision = self.executive.decide(has_method, confidence)
        self.wm.load([problem.a, problem.b, problem.op])

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
            eid = self.episodic.encode(
                "attempt",
                {"node_id": problem.node_id, "required_skills": problem.required_skills,
                 "correct": correct, "error_type": res.get("error_type")},
                self.day,
            )
            self._emit("memory.episodic.encoded", {"episode_id": eid})
            # Emma's feedback = the brain learns from the corrected outcome.
            self.procedural.practice(problem, correct, self.day)
            self.semantic.observe_attempt(problem.node_id, correct, self.day)
            self.metacog.observe(problem.node_id, correct)
            self._emit("skill.procedure.updated", {"node_id": problem.node_id, "correct": correct})
        return res

    # == API: /act ============================================================
    def act(self, problem: Problem) -> dict:
        return self.attempt(problem, learn=False)

    # == API: /learn/session + /learn/feedback ================================
    def learn_session(self, class_level: str, subject: str, problems: list[Problem]) -> dict:
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
    def evaluate(self, problems: list[Problem], label: str) -> dict:
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
