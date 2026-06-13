"""Teacher adapters — a stable boundary between Emma and the brain.

The brain must be teachable by a *real* Emma (an LLM) without ever letting the
teacher (a) grade the assessment, or (b) inject free text into memory. Three
guarantees enforce that:

* **Stable interface** — every teacher is a ``TeacherAdapter`` returning a
  ``StructuredFeedback`` object (never raw text). The brain learns only from the
  controlled ``teach_signal`` field; the natural-language ``hint`` is logged for
  humans, never written into a memory.
* **Ground truth ≠ Emma** — ``teach_signal`` and ``correct_answer`` are computed
  by the curriculum (``task.grade``), not by the model. A live Emma can phrase a
  hint, but cannot decide right/wrong, so she can never mis-teach or contaminate.
* **Reproducible** — a live session's raw hints can be *frozen* into a fixture
  and replayed by ``ScriptedTeacher`` with no network, giving a deterministic,
  testable run comparable to the stub.

Modes:
* ``StubTeacher``     — deterministic, offline, used by all unit tests.
* ``ScriptedTeacher`` — replays frozen live hints (a fixture); deterministic.
* ``LiveTeacher``     — optional LLM hint generator; INERT unless a transport is
  injected; no live dependency ever reaches the unit tests.
"""
from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import asdict, dataclass

from .emma_session import _hint_for


@dataclass
class StructuredFeedback:
    """The ONLY shape feedback enters the brain in. ``teach_signal`` (ground
    truth) drives learning; ``hint`` is human-facing and never stored in memory."""
    node_id: str
    task_id: str
    observed_answer: object
    correct_answer: object
    hint: str
    error_type: object
    confidence: float
    teach_signal: bool

    def as_dict(self) -> dict:
        return asdict(self)


def task_id(task) -> str:
    return f"{task.node_id}:{tuple(task.working_set)}"


def normalize(task, response: dict, hint: str) -> StructuredFeedback:
    """Build a controlled feedback object. Correctness comes from the curriculum,
    never from the teacher — so the teacher cannot grade or contaminate."""
    observed = response.get("answer")
    correct = bool(task.grade(observed)) and response.get("decision") != "ask_help"
    return StructuredFeedback(
        node_id=task.node_id, task_id=task_id(task),
        observed_answer=observed, correct_answer=task.answer,
        hint="" if correct else hint,
        error_type=response.get("error_type"),
        confidence=round(float(response.get("confidence", 0.0)), 4),
        teach_signal=correct,
    )


class TeacherAdapter(ABC):
    name: str = "abstract"
    is_live: bool = False

    @abstractmethod
    def feedback(self, task, response: dict) -> StructuredFeedback:
        ...


class StubTeacher(TeacherAdapter):
    """Deterministic teacher — hint from the diagnostic error type."""
    name = "stub"

    def feedback(self, task, response: dict) -> StructuredFeedback:
        return normalize(task, response, _hint_for(response.get("error_type")))


class ScriptedTeacher(TeacherAdapter):
    """Replays frozen live hints (a fixture). Correctness still from ground
    truth, so the resulting learning is identical to any other teacher — which
    is exactly what makes a live session reproducible and stub-comparable."""
    name = "scripted"

    def __init__(self, script: list) -> None:
        self.script = list(script)
        self.i = 0

    def feedback(self, task, response: dict) -> StructuredFeedback:
        entry = self.script[self.i] if self.i < len(self.script) else {}
        self.i += 1
        hint = entry.get("hint") or _hint_for(response.get("error_type"))
        return normalize(task, response, hint)


class LiveTeacher(TeacherAdapter):
    """LLM-backed hint generator. INERT unless a ``transport`` is injected (the
    same ``Transport`` interface as the live-edge LiteLLM adapter). Emma only
    ever sees the *teaching* prompt and the learner's answer — never an
    evaluation probe, never the oracle. Records raw hints so the session can be
    frozen into a fixture."""
    name = "live"
    is_live = True

    def __init__(self, transport=None, record: list | None = None) -> None:
        self._transport = transport
        self.record: list = record if record is not None else []

    def feedback(self, task, response: dict) -> StructuredFeedback:
        if self._transport is None:
            raise RuntimeError(
                "LiveTeacher is inert: inject a transport (or use StubTeacher / "
                "ScriptedTeacher for offline runs)."
            )
        observed = response.get("answer")
        messages = [
            {"role": "system", "content": "Tu es Emma, enseignante de CP. Donne UN "
             "indice court et bienveillant pour aider l'élève à se corriger. "
             "N'écris pas la réponse."},
            {"role": "user", "content": f"Exercice : {task.prompt} L'élève a "
             f"répondu : « {observed} »."},
        ]
        raw = self._transport.chat(messages)
        self.record.append({"task_id": task_id(task), "hint": (raw or "").strip()[:200]})
        return normalize(task, response, (raw or "").strip()[:200])


def freeze_session(record: list) -> list:
    """Turn a LiveTeacher's recorded raw hints into a replayable fixture."""
    return [{"task_id": e["task_id"], "hint": e.get("hint", "")} for e in record]
