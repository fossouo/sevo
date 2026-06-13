"""Persistent cognitive state and versioned snapshots.

Mirrors ``design/brain_state_schema.json``. A snapshot is an immutable,
serialisable copy of the brain's cognitive state at one point in time. The
evaluation protocol compares two snapshots (``before`` / ``after``) to compute
the ``Intelligence_delta``.
"""
from __future__ import annotations

import copy
import json
import uuid
from dataclasses import asdict, dataclass, field


@dataclass
class DevelopmentStage:
    school_class: str = "CP"
    age_equivalent_months: int | None = None
    curriculum_version: str = "MEN-2026"


@dataclass
class IntelligenceProfile:
    fluid_reasoning: float = 0.0
    crystallized_knowledge: float = 0.0
    transfer: float = 0.0
    learning_efficiency: float = 0.0
    retention: float = 0.0


@dataclass
class MetacognitiveProfile:
    calibration_error: float = 0.0
    knows_unknowns_score: float = 0.0
    help_seeking_quality: float = 0.0


@dataclass
class CognitiveState:
    # node_id -> {mastery, confidence, last_seen, evidence}
    knowledge_mastery_graph: dict = field(default_factory=dict)
    # skill_id -> {automaticity, error_patterns, transfer_score, consolidated, last_practiced_day}
    procedural_skill_graph: dict = field(default_factory=dict)
    episodic_index: dict = field(default_factory=lambda: {"episodes_count": 0, "last_episode_id": None})
    working_memory_profile: dict = field(
        default_factory=lambda: {
            "capacity_tokens_estimate": 0,
            "multi_step_depth": 0,
            "distraction_sensitivity": 0.0,
        }
    )
    metacognitive_profile: MetacognitiveProfile = field(default_factory=MetacognitiveProfile)
    motivation_profile: dict = field(
        default_factory=lambda: {"curiosity": 0.5, "frustration_tolerance": 0.5, "reward_sensitivity": 0.5}
    )
    intelligence_profile: IntelligenceProfile = field(default_factory=IntelligenceProfile)


@dataclass
class Snapshot:
    snapshot_id: str
    created_at_day: int
    parent_snapshot_id: str | None
    development_stage: dict
    cognitive_state: dict

    def to_json(self) -> str:
        return json.dumps(asdict(self), indent=2, ensure_ascii=False)


def take_snapshot(
    stage: DevelopmentStage,
    cognitive_state: CognitiveState,
    day: int,
    parent_snapshot_id: str | None = None,
) -> Snapshot:
    return Snapshot(
        snapshot_id=str(uuid.uuid4()),
        created_at_day=day,
        parent_snapshot_id=parent_snapshot_id,
        development_stage=asdict(stage),
        cognitive_state=copy.deepcopy(asdict(cognitive_state)),
    )
