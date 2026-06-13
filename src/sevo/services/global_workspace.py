"""global_workspace — global neuronal workspace (conscience de travail).

Central blackboard. Holds the current conscious context and broadcasts it so the
other services can react. In the MVP it is a small, inspectable dict.
"""
from __future__ import annotations


class GlobalWorkspace:
    def __init__(self) -> None:
        self.context: dict = {}

    def broadcast(self, key: str, value) -> None:
        self.context[key] = value

    def get(self, key: str, default=None):
        return self.context.get(key, default)
