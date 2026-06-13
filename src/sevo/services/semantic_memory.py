"""semantic_memory — néocortex associatif.

Slow-write store of durable concepts and the mastery graph over curriculum
nodes. Mastery is an EMA of held-back practice accuracy and is mostly written
*through consolidation*, not directly during a single exercise.
"""
from __future__ import annotations


class SemanticMemory:
    def __init__(self) -> None:
        self.mastery_graph: dict[str, dict] = {}

    def _node(self, node_id: str) -> dict:
        return self.mastery_graph.setdefault(
            node_id, {"mastery": 0.0, "confidence": 0.0, "last_seen": None, "evidence": []}
        )

    def observe_attempt(self, node_id: str, correct: bool, day: int, alpha: float = 0.25) -> None:
        n = self._node(node_id)
        n["mastery"] = (1 - alpha) * n["mastery"] + alpha * (1.0 if correct else 0.0)
        n["last_seen"] = day
        n["evidence"].append({"day": day, "correct": correct})

    def consolidate_node(self, node_id: str, session_accuracy: float, day: int) -> None:
        n = self._node(node_id)
        # Durable lift toward the level demonstrated this session.
        n["mastery"] = max(n["mastery"], 0.6 * n["mastery"] + 0.4 * session_accuracy)
        n["confidence"] = n["mastery"]
        n["last_seen"] = day

    def mastery(self, node_id: str) -> float:
        return self.mastery_graph.get(node_id, {}).get("mastery", 0.0)

    def graph(self) -> dict:
        return {
            k: {
                "mastery": round(v["mastery"], 4),
                "confidence": round(v["confidence"], 4),
                "last_seen": v["last_seen"],
                "evidence": v["evidence"][-5:],
            }
            for k, v in self.mastery_graph.items()
        }
