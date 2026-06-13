"""Journaled teaching session — a full, auditable trace of how Emma taught.

Each interaction records exactly what the founder asked for:
  * the prompt sent to Emma,
  * the brain's response,
  * Emma's raw feedback (the natural-language hint),
  * the normalized StructuredFeedback,
  * the learning decision (teach_signal),
  * the brain's state digest before and after the feedback.

The digest is compact (node mastery + the node's required-skill automaticities)
so a session journal stays small and serialisable.
"""
from __future__ import annotations

from dataclasses import asdict


def _digest(brain, node_id: str, task) -> dict:
    day = brain.day
    skills = {s: round(brain.procedural.effective(s, day), 4)
              for s in task.required_skills if s in brain.procedural.skills}
    return {"node_mastery": round(brain.semantic.mastery(node_id), 4),
            "skill_automaticity": skills}


def run_journaled_session(brain, teacher, node_id: str, items: list) -> list:
    """Teach a batch through a TeacherAdapter, recording the full journal. The
    brain learns ONLY from ``fb.teach_signal`` (ground truth); the raw hint is
    logged, never written to memory."""
    journal = []
    for task in items:
        state_before = _digest(brain, node_id, task)
        response = brain.act(task)                       # read-only response
        fb = teacher.feedback(task, response)            # structured feedback
        brain.learn_from_feedback(task, fb.teach_signal, fb.error_type)
        state_after = _digest(brain, node_id, task)
        journal.append({
            "prompt_to_emma": task.prompt,
            "brain_response": response.get("answer"),
            "raw_emma_feedback": fb.hint,                 # natural language
            "normalized_feedback": fb.as_dict(),          # controlled object
            "learning_decision": fb.teach_signal,         # what actually taught
            "state_before": state_before,
            "state_after": state_after,
        })
    return journal
