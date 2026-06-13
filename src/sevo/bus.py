"""In-process event bus.

Implements the publish/subscribe contract from ``design/events_topics.json``.
The reference MVP runs every cognitive microservice in a single process and
wires them through this synchronous bus instead of NATS/Redpanda. The event
*shape* (``event_id``, ``brain_id``, ``timestamp``, ``payload``,
``causal_parent_event_ids``) is preserved so a future distributed deployment
can swap the transport without touching service logic.
"""
from __future__ import annotations

import itertools
from dataclasses import dataclass, field
from typing import Any, Callable

_counter = itertools.count(1)


@dataclass
class Event:
    topic: str
    payload: dict
    brain_id: str
    timestamp: float
    event_id: str = field(default_factory=lambda: f"evt-{next(_counter)}")
    causal_parent_event_ids: list[str] = field(default_factory=list)


class EventBus:
    def __init__(self) -> None:
        self._subscribers: dict[str, list[Callable[[Event], None]]] = {}
        self.log: list[Event] = []

    def subscribe(self, topic: str, handler: Callable[[Event], None]) -> None:
        self._subscribers.setdefault(topic, []).append(handler)

    def publish(self, event: Event) -> None:
        self.log.append(event)
        for handler in self._subscribers.get(event.topic, []):
            handler(event)

    def topics_seen(self) -> set[str]:
        return {e.topic for e in self.log}
