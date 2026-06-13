"""sensory_gateway — systèmes sensoriels + thalamus relais.

Stateless. Normalises any external input (text / structured stimulus from Emma,
exam, user or world) into a uniform *percept* and emits ``percept.created``.
"""
from __future__ import annotations


class SensoryGateway:
    def normalize(self, modality: str, content, source: str) -> dict:
        return {"modality": modality, "content": content, "source": source}
