"""Official French national curriculum — class-by-class registry.

The brief: build a *source of truth per class* (CP → Terminale) holding, for each
class, its disciplines, competencies, end-of-year expectations, prerequisites,
exercise types and evaluation criteria — and start by proving the **whole CP
cycle** end to end without ingesting the entire programme at once.

This module is the per-class loader. Every node is expressed in the existing
ingestion-contract shape (so nothing about the brain changes) plus the richer
official fields added to ``CurriculumNode``. Each node is also bound to a
*runnable* — the bank builder that turns it into gradable exercises — so the CP
grade experiment can drive pretest → teaching → consolidation → posttest →
delayed posttest → transfer uniformly across maths and French.

Provenance: structure follows the Bulletin officiel / *attendus de fin d'année*
cycle 2 (see ``design/sources.json``). Only **CP** is populated here; the other
classes are declared but intentionally left empty until each is ingested in
turn (``register_class`` raises for an un-populated class rather than guessing).
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Callable

from .cp_ce1_math import NODES as MATH_NODES
from .cp_ce1_math import build_bank as build_bank_math
from .cp_ce1_math import transfer_bank as transfer_bank_math
from .fr_lecture_cp import (
    NODES_LECTURE,
    build_bank_lecture,
    transfer_bank_comprehension,
    transfer_bank_lecture,
)
from .ingestion import CurriculumRegistry

ALL_CLASSES = ["CP", "CE1", "CE2", "CM1", "CM2", "6e", "5e", "4e", "3e",
               "2nde", "1ere", "Terminale"]


@dataclass
class RunnableNode:
    """Binds an official node id to the code that makes it gradable."""
    node_id: str
    subject: str
    discipline: str
    build: Callable          # build(rng) -> Bank (has .teaching / .heldout)
    transfer: Callable | None = None   # transfer() -> list[Task] | None


# ---- CP — mathematics (nombres et calculs) ---------------------------------
def _math_node(nid: str, discipline: str, attendus, ex, crit) -> dict:
    spec = MATH_NODES[nid]
    return {
        "id": nid, "title": spec["title"], "class_level": "CP",
        "subject": "mathématiques", "discipline": discipline,
        "required_skills": spec["required_skills"],
        "prerequisites": spec.get("prerequisites", []),
        "mastery_threshold": spec["mastery_threshold"],
        "end_of_year_expectations": attendus,
        "exercise_types": ex, "evaluation_criteria": crit,
    }


CP_MATHS_NODES = [
    _math_node(
        "math.CP.add_within_20", "nombres et calculs",
        ["calculer une somme inférieure ou égale à 20",
         "résoudre un problème additif simple"],
        ["compléter une addition en ligne", "problème additif à une étape"],
        ["résultat exact", "procédure de surcomptage / décomposition maîtrisée"],
    ),
    _math_node(
        "math.CP.sub_within_20", "nombres et calculs",
        ["calculer une différence dans les nombres ≤ 20",
         "résoudre un problème de retrait simple"],
        ["compléter une soustraction en ligne", "problème de retrait à une étape"],
        ["résultat exact", "gestion correcte du passage à la dizaine"],
    ),
]


# ---- CP — French (lecture / décodage / compréhension) ----------------------
def _lecture_node(nid: str, discipline: str, attendus, ex, crit) -> dict:
    spec = NODES_LECTURE[nid]
    return {
        "id": nid, "title": spec["title"], "class_level": "CP",
        "subject": "français", "discipline": discipline,
        "required_skills": spec["required_skills"],
        "mastery_threshold": spec["mastery_threshold"],
        "end_of_year_expectations": attendus,
        "exercise_types": ex, "evaluation_criteria": crit,
    }


CP_FRANCAIS_NODES = [
    _lecture_node(
        "fr.CP.lecture_mots_reguliers", "lecture / décodage",
        ["déchiffrer des mots réguliers, y compris nouveaux",
         "lire des pseudo-mots en appliquant les correspondances graphème-phonème"],
        ["lecture de mots à voix haute", "lecture de pseudo-mots"],
        ["décodage phonologique exact", "généralisation à des mots jamais vus"],
    ),
    _lecture_node(
        "fr.CP.lecture_mots_irreguliers", "lecture / mots-outils",
        ["lire les mots fréquents irréguliers (mots-outils)"],
        ["lecture de mots-outils", "reconnaissance de mots irréguliers"],
        ["lecture exacte sans sur-régularisation (« femme » ≠ /fœm/)"],
    ),
    _lecture_node(
        "fr.CP.comprehension_phrase", "compréhension",
        ["comprendre une phrase simple lue seul",
         "répondre à une question littérale (qui ? quoi ?)"],
        ["question littérale sur une phrase", "appariement phrase-réponse"],
        ["rôle sujet/objet correctement attribué", "réponse littérale exacte"],
    ),
]

CP_PROGRAM = {
    "class_level": "CP",
    "cycle": "cycle 2",
    "disciplines": {
        "français": ["lecture / décodage", "lecture / mots-outils", "compréhension"],
        "mathématiques": ["nombres et calculs"],
    },
    "nodes": CP_FRANCAIS_NODES + CP_MATHS_NODES,
}

# ---- Runnable bindings (node -> gradable banks) ----------------------------
RUNNABLE_CP: dict[str, RunnableNode] = {
    "math.CP.add_within_20": RunnableNode(
        "math.CP.add_within_20", "mathématiques", "nombres et calculs",
        build=lambda rng: build_bank_math("math.CP.add_within_20", rng),
        transfer=lambda: _math_transfer(),
    ),
    "math.CP.sub_within_20": RunnableNode(
        "math.CP.sub_within_20", "mathématiques", "nombres et calculs",
        build=lambda rng: build_bank_math("math.CP.sub_within_20", rng),
    ),
    "fr.CP.lecture_mots_reguliers": RunnableNode(
        "fr.CP.lecture_mots_reguliers", "français", "lecture / décodage",
        build=lambda rng: build_bank_lecture("fr.CP.lecture_mots_reguliers", rng),
        transfer=lambda: transfer_bank_lecture("fr.CP.lecture_mots_reguliers"),
    ),
    "fr.CP.lecture_mots_irreguliers": RunnableNode(
        "fr.CP.lecture_mots_irreguliers", "français", "lecture / mots-outils",
        build=lambda rng: build_bank_lecture("fr.CP.lecture_mots_irreguliers", rng),
    ),
    "fr.CP.comprehension_phrase": RunnableNode(
        "fr.CP.comprehension_phrase", "français", "compréhension",
        build=lambda rng: build_bank_lecture("fr.CP.comprehension_phrase", rng),
        transfer=lambda: transfer_bank_comprehension("fr.CP.comprehension_phrase"),
    ),
}


def _math_transfer():
    """Maths transfer = addition within 1000, never taught at CP."""
    from ..rng import Rng
    return transfer_bank_math(Rng(99), n=20)


# ---- Public API ------------------------------------------------------------
_PROGRAMS = {"CP": CP_PROGRAM}


def register_class(registry: CurriculumRegistry, class_level: str) -> CurriculumRegistry:
    """Ingest one class' official programme into ``registry`` through the
    standard ingestion contract. Raises for a class not yet populated — we
    ingest the programme one class at a time, not all at once."""
    if class_level not in ALL_CLASSES:
        raise ValueError(f"unknown class_level: {class_level!r}")
    program = _PROGRAMS.get(class_level)
    if program is None:
        raise NotImplementedError(
            f"official programme for {class_level} not ingested yet — "
            f"only {sorted(_PROGRAMS)} are populated so far."
        )
    registry.ingest_many(program["nodes"])
    return registry


def official_cp_registry() -> CurriculumRegistry:
    """A registry pre-loaded with the full CP programme (français + maths)."""
    return register_class(CurriculumRegistry(), "CP")
