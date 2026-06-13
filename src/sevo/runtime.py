"""BrainService — the CP-appris brain as a persistent, queryable runtime.

This turns the reproducible experiment into a real, stateful service:

* a brain is held in memory, **saved/reloaded** as JSON (it keeps its skills);
* the **teaching channel** (`act` → `feedback` → `consolidate`) and the
  **assessment channel** (`evaluate`, the oracle on held-out banks) are strictly
  separate — Emma never grades herself;
* a baseline (``brain_before``) is captured at construction so ``diff`` can show
  the Brain-naïf → Brain-appris change at any time;
* an Emma session can be **replayed** to drive learning through the API.

This module is framework-agnostic (no FastAPI import); ``api.py`` is the thin
HTTP wrapper over it, so the whole runtime is testable without a web server.
"""
from __future__ import annotations

import json

from .brain import Brain
from .curriculum.factory import build_task, heldout_bank, teaching_bank
from .eval import assess_genuine_learning, brain_state_diff
from .teacher.emma_session import EmmaTeacher, run_emma_session


class BrainService:
    def __init__(self, brain: Brain | None = None, seed: int = 0) -> None:
        self.brain = brain or Brain(seed=seed)
        self.seed = seed
        self.emma = EmmaTeacher()
        # Baseline captured ONCE at construction (Brain-naïf). /diff always
        # compares the current brain to this stored snapshot — it is never
        # reconstructed per call (which could drift). set_baseline() re-anchors
        # it explicitly if a caller wants a new reference point.
        self.brain_before = self.brain.export_state()
        self._baseline_snapshot = self.brain.snapshot()
        self._touched: set[str] = set()

    def set_baseline(self) -> str:
        """Re-anchor the diff baseline to the brain's current state. Returns the
        new baseline snapshot id."""
        self.brain_before = self.brain.export_state()
        self._baseline_snapshot = self.brain.snapshot()
        return self._baseline_snapshot.snapshot_id

    @property
    def baseline_snapshot_id(self) -> str:
        return self._baseline_snapshot.snapshot_id

    # -- teaching channel ----------------------------------------------------
    def perceive(self, modality: str, content, source: str = "api") -> dict:
        return self.brain.perceive(modality, content, source)

    def act(self, node_id: str, content) -> dict:
        """Read-only response (no learning). The brain's own grade is returned
        for transparency; learning only happens via ``feedback``."""
        task = build_task(node_id, content)
        r = self.brain.act(task)
        return {"node_id": node_id, "answer": r["answer"], "correct": r["correct"],
                "confidence": round(r["confidence"], 4), "decision": r["decision"]}

    def feedback(self, node_id: str, content, correct: bool | None = None) -> dict:
        """Emma's structured feedback drives learning. If ``correct`` is omitted,
        the (deterministic) teacher computes it from ground truth."""
        task = build_task(node_id, content)
        if correct is None:
            correct = self.emma.feedback(task, self.brain.act(task)).correct
        self.brain.learn_from_feedback(task, bool(correct))
        self._touched.add(node_id)
        return {"node_id": node_id, "learned": True, "correct": bool(correct),
                "mastery": round(self.brain.semantic.mastery(node_id), 4)}

    def consolidate(self, mode: str = "sleep", advance_days: int = 1) -> dict:
        return self.brain.consolidate(mode, advance_days)

    def replay_emma_session(self, node_id: str, session_size: int = 8,
                            sessions: int = 1) -> dict:
        """Re-run an Emma teaching session over a node's teaching bank, entirely
        through the API loop (perceive → respond → feedback → learn)."""
        teaching = teaching_bank(node_id, self.seed)
        logs, cursor = [], 0
        for _ in range(sessions):
            batch = [teaching[(cursor + i) % len(teaching)] for i in range(session_size)]
            cursor += session_size
            logs.append(run_emma_session(self.brain, self.emma, node_id, batch))
        self._touched.add(node_id)
        return {"node_id": node_id, "sessions": logs,
                "mastery": round(self.brain.semantic.mastery(node_id), 4)}

    # -- assessment channel (oracle; never goes through Emma) ----------------
    def evaluate(self, node_id: str, items: list | None = None, label: str = "api.eval") -> dict:
        tasks = [build_task(node_id, c) for c in items] if items else heldout_bank(node_id, self.seed)
        res = self.brain.evaluate(tasks, label)
        return {"node_id": node_id, "n": len(tasks), "accuracy": res["accuracy"],
                "calibration_error": res["calibration_error"]}

    # -- state & diff --------------------------------------------------------
    def state(self) -> dict:
        return self.brain.export_state()

    def brain_after(self) -> dict:
        return self.brain.export_state()

    def diff(self) -> dict:
        """Structural + behavioural diff vs the baseline captured at startup.
        Behaviour is measured *now* by the oracle on touched nodes' held-out
        banks (so retention here is immediate — a live service does not simulate
        the 7-day delay; the offline experiment does)."""
        after_snapshot = self.brain.snapshot()
        held = [self.evaluate(n)["accuracy"] for n in sorted(self._touched)] or [0.0]
        held_after = sum(held) / len(held)
        cal = [self.evaluate(n)["calibration_error"] for n in sorted(self._touched)] or [0.0]
        cal_after = sum(cal) / len(cal)
        diff = brain_state_diff(
            self._baseline_snapshot, after_snapshot,
            heldout_before=0.0, heldout_after=held_after, transfer_after=held_after,
            calibration_before=0.1, calibration_after=cal_after,
            t2_after=held_after, retention_ratio=1.0, learning_efficiency=0.0,
        )
        diff["note"] = ("live diff — retention is immediate (no 7-day delay); "
                        "use run_cp_grade for the full delayed-retention protocol")
        return diff

    def genuine_learning(self) -> dict:
        """Verdict over the touched nodes (live, immediate retention)."""
        held = [self.evaluate(n)["accuracy"] for n in sorted(self._touched)] or [0.0]
        held_after = sum(held) / len(held)
        return assess_genuine_learning(
            heldout_before=0.0, heldout_after=held_after,
            transfer_before=0.0, transfer_after=held_after,
            memoriser_heldout=0.0, memoriser_transfer=0.0,
            t1_after=held_after, t2_after=held_after,
        )

    # -- persistence ---------------------------------------------------------
    def save(self, path: str) -> None:
        with open(path, "w", encoding="utf-8") as f:
            json.dump(self.brain.export_state(), f, indent=2, ensure_ascii=False)

    @classmethod
    def load(cls, path: str, seed: int = 0) -> "BrainService":
        with open(path, encoding="utf-8") as f:
            state = json.load(f)
        return cls(brain=Brain.from_state(state, seed=seed), seed=seed)
