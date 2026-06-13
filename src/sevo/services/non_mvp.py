"""Non-MVP cognitive services (documented stubs).

``design/brain_services.json`` defines fifteen services; ``minimal_mvp`` lists
the ten the v0.3 MVP actually runs. The five below complete the architecture but
are intentionally thin in the MVP — their richer behaviour is future work. They
are kept as explicit, named classes so the wiring point exists and the
anthropomorphic decomposition stays visible.
"""
from __future__ import annotations


class AttentionSalience:
    """Réseau de saillance. MVP: every percept from Emma/exam is salient."""

    def salience(self, percept: dict) -> float:
        return 1.0 if percept.get("source") in {"emma", "exam"} else 0.5


class WorldModel:
    """Modèle causal du monde. MVP placeholder (no predictive simulation yet)."""


class LanguageReasoner:
    """Aires du langage. MVP: arithmetic is handled procedurally, not verbally."""


class EmotionMotivation:
    """Valence/motivation. MVP: static motivation profile."""


class NeuromodulationControl:
    """Dopamine/NA/ACh/5-HT. MVP: error-driven learning rate lives in
    procedural_memory; this is the future home of explicit exploration control."""
