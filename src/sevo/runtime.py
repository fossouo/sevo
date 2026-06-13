"""BrainService — the CP-appris brain as a persistent, queryable runtime.

Turns the reproducible experiment into a stateful service:

* a brain held in memory, **saved/reloaded** as a versioned envelope (it keeps
  its skills, counters and sessions);
* the **teaching channel** (`act` → `feedback` → `consolidate` / `replay`) and
  the **assessment channel** (`evaluate`, the oracle on held-out banks) are
  strictly separate — Emma never grades herself;
* **persistent sessions** with a deterministic replay;
* **observability** counters + health/metrics;
* **methodological safety** — `/evaluate` refuses items seen in teaching, and
  `/audit` proves a node's held-out/transfer banks are leakage-free.

Framework-agnostic (no FastAPI import); ``api.py`` is the thin HTTP wrapper.
"""
from __future__ import annotations

import json
import uuid
from dataclasses import asdict

from .brain import Brain
from .state import Snapshot
from .curriculum.factory import build_task, heldout_bank, teaching_bank
from .eval import (
    ItemLeakageError,
    assess_genuine_learning,
    audit_node,
    brain_state_diff,
    detect_leakage,
)
from .persistence import DEFAULT_COUNTERS, make_envelope, migrate_envelope
from .teacher.emma_session import EmmaTeacher, run_emma_session

MASTERED_AT = 0.7


class BrainService:
    def __init__(self, brain: Brain | None = None, seed: int = 0) -> None:
        self.brain = brain or Brain(seed=seed)
        self.seed = seed
        self.emma = EmmaTeacher()
        # Baseline captured ONCE (Brain-naïf). /diff always compares to this
        # stored snapshot — never reconstructed per call.
        self.brain_before = self.brain.export_state()
        self._baseline_snapshot = self.brain.snapshot()
        self._touched: set[str] = set()
        self.counters: dict = dict(DEFAULT_COUNTERS)
        self.sessions: dict = {}
        self._current_session: str | None = None

    def set_baseline(self) -> str:
        self.brain_before = self.brain.export_state()
        self._baseline_snapshot = self.brain.snapshot()
        return self._baseline_snapshot.snapshot_id

    @property
    def baseline_snapshot_id(self) -> str:
        return self._baseline_snapshot.snapshot_id

    # -- sessions ------------------------------------------------------------
    def start_session(self) -> str:
        sid = str(uuid.uuid4())
        self.sessions[sid] = {
            "session_id": sid,
            "started_day": self.brain.day,
            "start_state": self.brain.export_state(),
            "interactions": [],
        }
        self._current_session = sid
        return sid

    def _log(self, kind: str, **fields) -> None:
        if self._current_session and self._current_session in self.sessions:
            self.sessions[self._current_session]["interactions"].append({"type": kind, **fields})

    def get_session(self, session_id: str) -> dict:
        if session_id not in self.sessions:
            raise KeyError(session_id)
        return self.sessions[session_id]

    def replay_session(self, session_id: str) -> dict:
        """Deterministically re-apply a session's feedback interactions onto a
        fresh brain rebuilt from the session's start state. Because learning
        from explicit feedback is deterministic, the replayed end-state is
        reproducible bit-for-bit."""
        s = self.get_session(session_id)
        fresh = Brain.from_state(s["start_state"], seed=self.seed)
        for it in s["interactions"]:
            if it["type"] == "feedback":
                fresh.learn_from_feedback(build_task(it["node_id"], it["content"]), it["correct"])
        return {"session_id": session_id, "replayed_state": fresh.export_state(),
                "n_feedbacks": sum(1 for it in s["interactions"] if it["type"] == "feedback")}

    # -- teaching channel ----------------------------------------------------
    def perceive(self, modality: str, content, source: str = "api") -> dict:
        self.counters["perceptions"] += 1
        self._log("perceive", modality=modality, source=source)
        return self.brain.perceive(modality, content, source)

    def act(self, node_id: str, content) -> dict:
        self.counters["actions"] += 1
        task = build_task(node_id, content)
        r = self.brain.act(task)
        return {"node_id": node_id, "answer": r["answer"], "correct": r["correct"],
                "confidence": round(r["confidence"], 4), "decision": r["decision"]}

    def feedback(self, node_id: str, content, correct: bool | None = None) -> dict:
        task = build_task(node_id, content)
        if correct is None:
            correct = self.emma.feedback(task, self.brain.act(task)).correct
        correct = bool(correct)
        self.brain.learn_from_feedback(task, correct)
        self.counters["feedbacks"] += 1
        self._touched.add(node_id)
        self._log("feedback", node_id=node_id, content=content, correct=correct)
        return {"node_id": node_id, "learned": True, "correct": correct,
                "mastery": round(self.brain.semantic.mastery(node_id), 4)}

    def consolidate(self, mode: str = "sleep", advance_days: int = 1) -> dict:
        self.counters["consolidations"] += 1
        self._log("consolidate", mode=mode, advance_days=advance_days)
        return self.brain.consolidate(mode, advance_days)

    def replay_emma_session(self, node_id: str, session_size: int = 8, sessions: int = 1) -> dict:
        teaching = teaching_bank(node_id, self.seed)
        logs, cursor = [], 0
        for _ in range(sessions):
            batch = [teaching[(cursor + i) % len(teaching)] for i in range(session_size)]
            cursor += session_size
            logs.append(run_emma_session(self.brain, self.emma, node_id, batch))
        self.counters["feedbacks"] += session_size * sessions
        self._touched.add(node_id)
        return {"node_id": node_id, "sessions": logs,
                "mastery": round(self.brain.semantic.mastery(node_id), 4)}

    # -- assessment channel (oracle; never via Emma, never learns) -----------
    def evaluate(self, node_id: str, items: list | None = None, label: str = "api.eval") -> dict:
        if items:
            tasks = [build_task(node_id, c) for c in items]
            report = detect_leakage(tasks, teaching_bank(node_id, self.seed))
            if not report["clean"]:
                raise ItemLeakageError(
                    f"{report['n_contaminated']}/{report['n_eval']} evaluation items "
                    f"were in the teaching bank for {node_id!r} — refusing to grade "
                    "on seen items (item leakage)."
                )
        else:
            tasks = heldout_bank(node_id, self.seed)
        res = self.brain.evaluate(tasks, label)
        return {"node_id": node_id, "n": len(tasks), "accuracy": res["accuracy"],
                "calibration_error": res["calibration_error"]}

    def audit(self, node_id: str) -> dict:
        return audit_node(node_id, self.seed)

    # -- observability -------------------------------------------------------
    def _mastered_skills(self) -> list:
        g = self.brain.procedural.graph(self.brain.day)
        return sorted(s for s, v in g.items() if v["automaticity"] >= MASTERED_AT)

    def health(self) -> dict:
        return {"status": "ok", "day": self.brain.day,
                "brain_schema_version": self.brain.export_state()["schema_version"],
                "nodes_touched": len(self._touched), "sessions": len(self.sessions)}

    def metrics(self) -> dict:
        return {
            "counters": dict(self.counters),
            "mastered_skills": self._mastered_skills(),
            "n_mastered_skills": len(self._mastered_skills()),
            "genuine_learning": self.genuine_learning()["verdict"],
        }

    # -- state & diff --------------------------------------------------------
    def state(self) -> dict:
        return self.brain.export_state()

    def diff(self) -> dict:
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
        held = [self.evaluate(n)["accuracy"] for n in sorted(self._touched)] or [0.0]
        held_after = sum(held) / len(held)
        return assess_genuine_learning(
            heldout_before=0.0, heldout_after=held_after,
            transfer_before=0.0, transfer_after=held_after,
            memoriser_heldout=0.0, memoriser_transfer=0.0,
            t1_after=held_after, t2_after=held_after,
        )

    # -- persistence (versioned envelope) ------------------------------------
    def save(self, path: str) -> None:
        env = make_envelope(self.brain.export_state(), self.counters, self.sessions,
                            baseline=asdict(self._baseline_snapshot), seed=self.seed)
        with open(path, "w", encoding="utf-8") as f:
            json.dump(env, f, indent=2, ensure_ascii=False)

    @classmethod
    def load(cls, path: str, seed: int | None = None) -> "BrainService":
        with open(path, encoding="utf-8") as f:
            env = migrate_envelope(json.load(f))
        resolved_seed = seed if seed is not None else env.get("seed", 0)
        svc = cls(brain=Brain.from_state(env["brain"], seed=resolved_seed), seed=resolved_seed)
        svc.counters = {**DEFAULT_COUNTERS, **env.get("counters", {})}
        svc.sessions = env.get("sessions", {})
        # Restore the ORIGINAL Brain-naïf baseline so /diff stays meaningful
        # across a reload (a legacy 0.4 save has none — keep the re-captured one).
        if env.get("baseline_snapshot"):
            svc._baseline_snapshot = Snapshot(**env["baseline_snapshot"])
        return svc
