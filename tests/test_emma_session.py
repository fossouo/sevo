"""Emma as an external teacher driving the brain through its API.

Emma teaches via the public API (perceive → respond → structured feedback →
learn); the brain learns from the correction; evaluation stays independent of
Emma (the oracle on disjoint held-out banks).
"""
from sevo.brain import Brain
from sevo.curriculum.fr_lecture_cp import _reading_task, build_bank_lecture
from sevo.rng import Rng
from sevo.teacher import EmmaTeacher, run_emma_session, teach_node_via_emma

NODE = "fr.CP.lecture_mots_reguliers"


def test_emma_api_loop_teaches_to_mastery():
    brain = Brain(seed=7)
    emma = EmmaTeacher()
    bank = build_bank_lecture(NODE, Rng(7).fork(NODE))
    log = teach_node_via_emma(brain, emma, NODE, bank)
    assert log["taught_via"] == "emma_api_loop"
    assert log["reached_mastery"]
    # independent evaluation (oracle), never routed through Emma
    assert brain.evaluate(bank.heldout, "h")["accuracy"] >= 0.7


def test_learn_from_feedback_updates_memories():
    brain = Brain(seed=1)
    task = _reading_task(NODE, "chat", "reg")
    m0 = brain.semantic.mastery(NODE)
    for _ in range(12):
        brain.learn_from_feedback(task, correct=True)
    assert brain.semantic.mastery(NODE) > m0


def test_feedback_is_structured_and_hints_on_error():
    brain = Brain(seed=9)        # cold brain → wrong answer
    emma = EmmaTeacher()
    task = _reading_task(NODE, "chat", "reg")
    response = brain.act(task)   # read-only attempt
    fb = emma.feedback(task, response)
    assert fb.correct_answer == "S.a"
    if not fb.correct:
        assert fb.hint                      # a corrective hint is provided
        assert fb.learner_answer != task.answer


def test_session_accuracy_reported():
    brain = Brain(seed=3)
    emma = EmmaTeacher()
    bank = build_bank_lecture(NODE, Rng(3).fork(NODE))
    out = run_emma_session(brain, emma, NODE, bank.teaching[:6])
    assert out["n"] == 6 and 0.0 <= out["session_accuracy"] <= 1.0
