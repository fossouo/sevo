"""Curriculum ingestion — implements ``design/curriculum_ingestion_contract.json``.

The curriculum is an *external* environment, injected as structured nodes; it
does not live inside the brain. This module validates incoming node definitions
and holds them in a registry that the teacher queries by class level and
subject. Ingesting the official French programme (BO references in
``design/sources.json``) means feeding node dicts of this exact shape — class by
class — with no change to the brain.
"""
from __future__ import annotations

from dataclasses import dataclass, field

VALID_CLASSES = {"CP", "CE1", "CE2", "CM1", "CM2", "6e", "5e", "4e", "3e", "2nde", "1ere", "Terminale"}


@dataclass
class CurriculumNode:
    id: str
    title: str
    class_level: str
    subject: str
    required_skills: dict
    prerequisites: list = field(default_factory=list)
    learning_objectives: list = field(default_factory=list)
    observable_behaviors: list = field(default_factory=list)
    mastery_threshold: float = 0.8


class CurriculumError(ValueError):
    pass


def _validate(node: dict) -> CurriculumNode:
    for required in ("id", "title", "class_level", "subject", "required_skills"):
        if required not in node or node[required] in (None, "", {}):
            raise CurriculumError(f"node missing required field: {required!r}")
    if node["class_level"] not in VALID_CLASSES:
        raise CurriculumError(f"unknown class_level: {node['class_level']!r}")
    skills = node["required_skills"]
    if not isinstance(skills, dict) or not skills:
        raise CurriculumError("required_skills must be a non-empty {skill: weight} map")
    total = sum(skills.values())
    if abs(total - 1.0) > 1e-6:
        raise CurriculumError(f"required_skills weights must sum to 1.0 (got {total})")
    thr = node.get("mastery_threshold", 0.8)
    if not 0.0 < thr <= 1.0:
        raise CurriculumError(f"mastery_threshold must be in (0, 1] (got {thr})")
    return CurriculumNode(
        id=node["id"], title=node["title"], class_level=node["class_level"],
        subject=node["subject"], required_skills=dict(skills),
        prerequisites=list(node.get("prerequisites", [])),
        learning_objectives=list(node.get("learning_objectives", [])),
        observable_behaviors=list(node.get("observable_behaviors", [])),
        mastery_threshold=thr,
    )


class CurriculumRegistry:
    def __init__(self) -> None:
        self.nodes: dict[str, CurriculumNode] = {}

    def ingest(self, node: dict) -> CurriculumNode:
        n = _validate(node)
        self.nodes[n.id] = n
        return n

    def ingest_many(self, nodes: list[dict]) -> list[CurriculumNode]:
        return [self.ingest(n) for n in nodes]

    def get(self, node_id: str) -> CurriculumNode:
        return self.nodes[node_id]

    def by_class(self, class_level: str) -> list[CurriculumNode]:
        return [n for n in self.nodes.values() if n.class_level == class_level]

    def by_subject(self, subject: str) -> list[CurriculumNode]:
        return [n for n in self.nodes.values() if n.subject == subject]


def builtin_registry() -> CurriculumRegistry:
    """Registry pre-loaded with the MVP's built-in maths + French nodes, in the
    ingestion-contract shape — a worked example of the format the official
    programme should be fed in."""
    from .cp_ce1_math import NODES
    from .fr_cp_ce1 import NODES_FR

    reg = CurriculumRegistry()
    for nid, spec in NODES.items():
        if spec.get("untaught"):
            continue
        reg.ingest({
            "id": nid, "title": spec["title"],
            "class_level": nid.split(".")[1], "subject": "mathématiques",
            "required_skills": spec["required_skills"],
            "prerequisites": spec.get("prerequisites", []),
            "mastery_threshold": spec["mastery_threshold"],
        })
    for nid, spec in NODES_FR.items():
        reg.ingest({
            "id": nid, "title": spec["title"],
            "class_level": nid.split(".")[1], "subject": "français",
            "required_skills": spec["required_skills"],
            "mastery_threshold": spec["mastery_threshold"],
        })
    return reg
