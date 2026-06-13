"""Emma as an external teacher driving the brain through its API.

This formalises the teaching loop the founder asked for — Emma is *outside* the
brain and interacts only through the public API:

    Emma presents an exercise   ──►  brain.perceive(...)
    brain produces a response   ──►  brain.act(task)          (read-only solve)
    Emma gives structured feedback   (correct? correct answer, error, hint)
    brain learns from feedback  ──►  brain.learn_from_feedback(task, correct)
    after the session           ──►  brain.consolidate(...)
    evaluation stays independent ──► brain.evaluate(...)      (oracle; never Emma)

Crucially, **grading the brain never goes through Emma**: the assessment oracle
evaluates on disjoint held-out banks. Emma only teaches and corrects — she can be
deterministic (here) or the live LiteLLM model later, with no change to the loop.
"""
from __future__ import annotations

from dataclasses import dataclass


@dataclass
class EmmaFeedback:
    correct: bool
    correct_answer: object
    learner_answer: object
    error_type: object
    hint: str


class EmmaTeacher:
    """Deterministic teacher: knows the ground truth, gives structured feedback.
    The brain learns from the *correction*, not from Emma's internals."""

    def present(self, brain, task) -> dict:
        # Emma shows the exercise; the brain perceives it as a stimulus.
        return brain.perceive("exercise", task.prompt, source="emma")

    def feedback(self, task, response: dict) -> EmmaFeedback:
        learner = response.get("answer")
        correct = task.grade(learner) and response.get("decision") != "ask_help"
        hint = "" if correct else _hint_for(response.get("error_type"))
        return EmmaFeedback(correct=correct, correct_answer=task.answer,
                            learner_answer=learner, error_type=response.get("error_type"),
                            hint=hint)


def _hint_for(error_type) -> str:
    return {
        "letter_by_letter": "regarde les lettres qui vont ensemble (ch, ou, on…)",
        "overregularized_reading": "ce mot se lit par cœur, ne le découpe pas",
        "phonetic_spelling": "attention aux lettres muettes et aux graphies (eau, …)",
        "role_confusion": "qui fait l'action ? c'est le sujet",
        "reversed_comparison": "le plus grand nombre est du côté ouvert du signe",
        "place_value_swap": "compte d'abord les dizaines, puis les unités",
        "no_segmentation": "frappe les syllabes dans tes mains",
    }.get(error_type, "réessaie en expliquant ta démarche")


def run_emma_session(brain, emma: EmmaTeacher, node_id: str, items: list,
                     subject: str = "français") -> dict:
    """One Emma teaching session over a batch of items, entirely via the API."""
    brain.stage.school_class = node_id.split(".")[1] if "." in node_id else "CP"
    n_correct = 0
    for task in items:
        emma.present(brain, task)                 # perceive
        response = brain.act(task)                # read-only response
        fb = emma.feedback(task, response)        # structured feedback
        brain.learn_from_feedback(task, fb.correct, fb.error_type)  # learn from correction
        n_correct += int(fb.correct)
    acc = n_correct / len(items) if items else 0.0
    return {"node_id": node_id, "subject": subject, "n": len(items),
            "session_accuracy": round(acc, 4)}


def teach_node_via_emma(brain, emma: EmmaTeacher, node_id: str, bank,
                        threshold: float = 0.8, max_sessions: int = 30,
                        session_size: int = 8, subject: str = "français") -> dict:
    """Teach one node to mastery through the Emma API loop. Same return shape as
    the offline ``teach_to_mastery`` so experiments can swap them transparently."""
    teaching = bank.teaching
    trials, sessions, cursor = 0, 0, 0
    history = []
    for _ in range(max_sessions):
        batch = [teaching[(cursor + i) % len(teaching)] for i in range(session_size)]
        cursor += session_size
        run_emma_session(brain, emma, node_id, batch, subject)
        trials += len(batch)
        sessions += 1
        m = brain.semantic.mastery(node_id)
        history.append(round(m, 4))
        if m >= threshold:
            break
    return {
        "node_id": node_id, "sessions": sessions, "trials": trials,
        "reached_mastery": brain.semantic.mastery(node_id) >= threshold,
        "final_mastery": round(brain.semantic.mastery(node_id), 4),
        "mastery_history": history,
        "taught_via": "emma_api_loop",
    }
