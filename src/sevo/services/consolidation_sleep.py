"""consolidation_sleep — replay hippocampo-cortical + sommeil.

The slow half of Complementary Learning Systems. It replays the episodes of a
session and pushes them from the fast episodic store into durable procedural and
semantic memory, lowering future forgetting for what was practised. Without this
step the immediate gains decay quickly (see the delayed test in the protocol).
"""
from __future__ import annotations


class ConsolidationSleep:
    def run(self, episodic, procedural, semantic, mode: str, day: int) -> dict:
        practiced_skills: set[str] = set()
        node_correct: dict[str, list[bool]] = {}
        for ep in episodic.recent(200):
            if ep["kind"] != "attempt":
                continue
            p = ep["payload"]
            for s in p.get("required_skills", {}):
                practiced_skills.add(s)
            node_correct.setdefault(p["node_id"], []).append(p["correct"])

        procedural.consolidate(practiced_skills, mode=mode, day=day)
        for node_id, results in node_correct.items():
            acc = sum(results) / len(results)
            semantic.consolidate_node(node_id, acc, day)

        return {"mode": mode, "skills_consolidated": sorted(practiced_skills), "nodes": list(node_correct)}
