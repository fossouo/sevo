"""episodic_memory — hippocampe + cortex entorhinal.

Fast-write store of concrete experiences (lessons, attempts, feedback). Traces
are forgotten quickly unless consolidation transfers them to semantic/procedural
memory — the fast half of Complementary Learning Systems.
"""
from __future__ import annotations

import itertools

_ep = itertools.count(1)


class EpisodicMemory:
    def __init__(self) -> None:
        self.episodes: list[dict] = []

    def encode(self, kind: str, payload: dict, day: int) -> str:
        eid = f"ep-{next(_ep)}"
        self.episodes.append({"id": eid, "kind": kind, "day": day, "payload": payload})
        return eid

    def recent(self, n: int = 50) -> list[dict]:
        return self.episodes[-n:]

    def index(self) -> dict:
        return {
            "episodes_count": len(self.episodes),
            "last_episode_id": self.episodes[-1]["id"] if self.episodes else None,
        }
