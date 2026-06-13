"""Teacher adapters — structured feedback, reproducibility, anti-contamination.

Emma can teach for real without ever grading the assessment or injecting free
text into memory: the brain learns only from the ground-truth ``teach_signal``,
and a live session can be frozen and replayed deterministically.
"""
import pytest

from sevo.brain import Brain
from sevo.curriculum.factory import teaching_bank
from sevo.runtime import BrainService
from sevo.teacher import (
    LiveTeacher,
    ScriptedTeacher,
    StructuredFeedback,
    StubTeacher,
    TeacherAdapter,
    freeze_session,
    run_journaled_session,
)
from sevo.teacher.emma_litellm import FakeTransport

NODE = "fr.CP.lecture_mots_reguliers"
CONTRACT = {"node_id", "task_id", "observed_answer", "correct_answer",
            "hint", "error_type", "confidence", "teach_signal"}


def _items(n=8, seed=7):
    return teaching_bank(NODE, seed)[:n]


def test_structured_feedback_contract():
    task = _items(1)[0]
    fb = StubTeacher().feedback(task, Brain(seed=9).act(task))
    assert isinstance(fb, StructuredFeedback)
    assert set(fb.as_dict()) == CONTRACT


def test_teach_signal_comes_from_ground_truth_not_the_teacher():
    """Even a teacher that 'says' wrong things cannot change correctness — it is
    computed by the curriculum."""
    task = _items(1)[0]
    response = Brain(seed=9).act(task)
    fb = StubTeacher().feedback(task, response)
    assert fb.teach_signal == (task.grade(response["answer"]) and response["decision"] != "ask_help")
    assert fb.correct_answer == task.answer


def test_live_teacher_is_inert_without_transport():
    with pytest.raises(RuntimeError, match="inert"):
        LiveTeacher().feedback(_items(1)[0], Brain(seed=9).act(_items(1)[0]))


def test_live_session_freezes_and_replays_identically_to_stub():
    """A live run (canned transport) is frozen into a fixture; replaying it with
    ScriptedTeacher yields the SAME brain state as the stub — because learning
    depends only on the ground-truth teach_signal, not on the hint text."""
    items = _items()
    live = LiveTeacher(transport=FakeTransport(["indice A", "indice B"]))
    b_live = Brain(seed=7)
    run_journaled_session(b_live, live, NODE, items)
    fixture = freeze_session(live.record)

    b_stub = Brain(seed=7)
    run_journaled_session(b_stub, StubTeacher(), NODE, items)
    b_scripted = Brain(seed=7)
    run_journaled_session(b_scripted, ScriptedTeacher(fixture), NODE, items)

    assert b_scripted.export_state()["procedural_skills"] == b_stub.export_state()["procedural_skills"]
    assert b_live.export_state()["procedural_skills"] == b_stub.export_state()["procedural_skills"]


def test_journal_records_all_required_fields():
    j = run_journaled_session(Brain(seed=7), StubTeacher(), NODE, _items(3))
    assert len(j) == 3
    entry = j[0]
    for k in ("prompt_to_emma", "brain_response", "raw_emma_feedback",
              "normalized_feedback", "learning_decision", "state_before", "state_after"):
        assert k in entry


class _RecordingTeacher(TeacherAdapter):
    name = "recording"

    def __init__(self):
        self.seen = []

    def feedback(self, task, response):
        self.seen.append(task)
        return StubTeacher().feedback(task, response)


def test_assessment_never_invokes_the_teacher():
    """Anti-contamination: /evaluate must never route through a teacher — so a
    teacher can never see held-out / transfer / retention items."""
    svc = BrainService(seed=7)
    svc.adapter = _RecordingTeacher()
    for _ in range(6):
        svc.replay_emma_session(NODE)              # teaching (uses the stub loop)
    svc.consolidate("sleep", 1)
    svc.evaluate(NODE)                             # assessment
    svc.evaluate("fr.CP.dictee_simple")
    assert svc.adapter.seen == []                  # the teacher saw no eval item
