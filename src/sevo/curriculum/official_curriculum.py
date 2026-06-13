"""Official-curriculum-shaped registry — class-by-class, CP seed set.

⚠️ **Scope claim (read first).** This is an *official-curriculum-**shaped** CP
seed registry*: a small, **hand-verified partial seed set aligned with the
official CP expectations** — it is **NOT** an exhaustive ingest of the Bulletin
officiel. The structure follows the BO / *attendus de fin d'année* cycle 2 (see
``design/sources.json``); the content embedded here covers only what the CP grade
experiment exercises. Treat it as a worked, extensible template, not a complete
programme database.

The brief: build a *source of truth per class* (CP → Terminale) holding, for each
class, its disciplines, competencies, end-of-year expectations, prerequisites,
exercise types and evaluation criteria — and start by proving the **whole CP
cycle** end to end without ingesting the entire programme at once.

This module is the per-class loader. Every node is expressed in the existing
ingestion-contract shape (so nothing about the brain changes) plus the richer
official-style fields added to ``CurriculumNode``. Each node is also bound to a
*runnable* — the bank builder that turns it into gradable exercises — so the CP
grade experiment can drive pretest → teaching → consolidation → posttest →
delayed posttest → transfer uniformly across maths and French.

Only **CP** is populated (as a partial seed); the other classes are declared but
intentionally left empty until each is ingested in turn (``register_class``
raises for an un-populated class rather than guessing).
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Callable

from .cp_ce1_math import NODES as MATH_NODES
from .cp_ce1_math import build_bank as build_bank_math
from .cp_ce1_math import transfer_bank as transfer_bank_math
from .cp_maths_numeration import NODES_NUM, build_bank_num, transfer_bank_num
from .fr_conjugation import NODES_CONJ, build_bank_conj, transfer_bank_conj
from .fr_cp_ce1 import NODES_FR, build_bank_fr, transfer_bank_fr
from .fr_lecture_cp import (
    NODES_LECTURE,
    build_bank_lecture,
    transfer_bank_comprehension,
    transfer_bank_dictee,
    transfer_bank_lecture,
    transfer_bank_syllabes,
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


def _num_node(nid: str, attendus, ex, crit) -> dict:
    spec = NODES_NUM[nid]
    return {
        "id": nid, "title": spec["title"], "class_level": "CP",
        "subject": "mathématiques", "discipline": "nombres et calculs",
        "required_skills": spec["required_skills"],
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
    _num_node(
        "math.CP.numeration_dizaines_unites",
        ["dénombrer et décomposer les nombres ≤ 99 en dizaines et unités"],
        ["décomposer un nombre en dizaines/unités", "associer écriture chiffrée et décomposition"],
        ["décomposition exacte", "place de la dizaine et de l'unité respectée"],
    ),
    _num_node(
        "math.CP.comparaison_nombres",
        ["comparer, ranger et encadrer les nombres ≤ 100 (< > =)"],
        ["comparer deux nombres avec < > =", "ranger une suite de nombres"],
        ["signe de comparaison correct", "prise en compte de la dizaine avant l'unité"],
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
    _lecture_node(
        "fr.CP.segmentation_syllabes", "lecture / phonologie",
        ["segmenter un mot en syllabes orales"],
        ["découper un mot en syllabes", "frapper les syllabes"],
        ["nombre et découpage des syllabes corrects"],
    ),
    _lecture_node(
        "fr.CP.dictee_simple", "écriture / encodage",
        ["écrire sous la dictée des mots simples déjà rencontrés"],
        ["dictée de mots", "encoder un mot entendu"],
        ["orthographe exacte (lettres muettes et graphies respectées)"],
    ),
]

# Surfaced in reports so no reader mistakes this for a full BO ingest.
SEED_DISCLAIMER = (
    "Registre aligné sur les attendus officiels du CP — jeu amorce partiel, "
    "vérifié à la main (PAS un ingest exhaustif du Bulletin officiel)."
)

CP_PROGRAM = {
    "class_level": "CP",
    "cycle": "cycle 2",
    "status": "partial-seed",
    "disclaimer": SEED_DISCLAIMER,
    "disciplines": {
        "français": ["lecture / décodage", "lecture / mots-outils", "compréhension",
                     "lecture / phonologie", "écriture / encodage"],
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
    "fr.CP.segmentation_syllabes": RunnableNode(
        "fr.CP.segmentation_syllabes", "français", "lecture / phonologie",
        build=lambda rng: build_bank_lecture("fr.CP.segmentation_syllabes", rng),
        transfer=lambda: transfer_bank_syllabes("fr.CP.segmentation_syllabes"),
    ),
    "fr.CP.dictee_simple": RunnableNode(
        "fr.CP.dictee_simple", "français", "écriture / encodage",
        build=lambda rng: build_bank_lecture("fr.CP.dictee_simple", rng),
        transfer=lambda: transfer_bank_dictee("fr.CP.dictee_simple"),
    ),
    "math.CP.numeration_dizaines_unites": RunnableNode(
        "math.CP.numeration_dizaines_unites", "mathématiques", "nombres et calculs",
        build=lambda rng: build_bank_num("math.CP.numeration_dizaines_unites", rng),
        transfer=lambda: transfer_bank_num("math.CP.numeration_dizaines_unites"),
    ),
    "math.CP.comparaison_nombres": RunnableNode(
        "math.CP.comparaison_nombres", "mathématiques", "nombres et calculs",
        build=lambda rng: build_bank_num("math.CP.comparaison_nombres", rng),
        transfer=lambda: transfer_bank_num("math.CP.comparaison_nombres"),
    ),
}


def _math_transfer():
    """Maths transfer = addition within 1000, never taught at CP/CE1."""
    from ..rng import Rng
    return transfer_bank_math(Rng(99), n=20)


# ============================================================================
# CE1 — an EXTENSION of the same core (no rewrite). Reuses nodes that already
# exist and learn under the frozen CP protocol: plural of nouns, present tense
# of -er verbs, and addition/subtraction within 100. GENUINE, teacher/oracle
# separation and anti-leakage are inherited unchanged.
# ============================================================================
CE1_DISCLAIMER = (
    "Registre aligné sur les attendus officiels du CE1 — jeu amorce partiel, "
    "vérifié à la main (PAS un ingest exhaustif du Bulletin officiel)."
)


def _fr_node(nid: str, discipline: str, attendus, ex, crit) -> dict:
    spec = NODES_FR.get(nid) or NODES_CONJ[nid]
    return {
        "id": nid, "title": spec["title"], "class_level": "CE1",
        "subject": "français", "discipline": discipline,
        "required_skills": spec["required_skills"],
        "mastery_threshold": spec["mastery_threshold"],
        "end_of_year_expectations": attendus,
        "exercise_types": ex, "evaluation_criteria": crit,
    }


def _math_ce1_node(nid: str, attendus, ex, crit) -> dict:
    spec = MATH_NODES[nid]
    return {
        "id": nid, "title": spec["title"], "class_level": "CE1",
        "subject": "mathématiques", "discipline": "nombres et calculs",
        "required_skills": spec["required_skills"],
        "prerequisites": spec.get("prerequisites", []),
        "mastery_threshold": spec["mastery_threshold"],
        "end_of_year_expectations": attendus,
        "exercise_types": ex, "evaluation_criteria": crit,
    }


CE1_FRANCAIS_NODES = [
    _fr_node("fr.CE1.pluriel_reguliers", "orthographe grammaticale",
             ["former le pluriel régulier des noms (+s)"],
             ["accorder un nom au pluriel", "transformer singulier → pluriel"],
             ["marque du pluriel correcte", "généralise à des noms jamais vus"]),
    _fr_node("fr.CE1.pluriel_en_al", "orthographe grammaticale",
             ["former le pluriel des noms en -al (-aux)"],
             ["pluriel des noms en -al", "distinguer la règle des exceptions"],
             ["-al → -aux correct", "pas de sur-régularisation « chevals »"]),
    _fr_node("fr.CE1.present_verbes_er", "conjugaison",
             ["conjuguer les verbes du 1er groupe (-er) au présent"],
             ["conjuguer un verbe en -er", "accorder le verbe au sujet"],
             ["terminaison correcte", "accord sujet-verbe respecté"]),
]

CE1_MATHS_NODES = [
    _math_ce1_node("math.CE1.add_within_100_nocarry",
                   ["additionner deux nombres < 100 sans retenue"],
                   ["addition posée sans retenue", "problème additif"],
                   ["résultat exact", "alignement des unités/dizaines"]),
    _math_ce1_node("math.CE1.add_within_100_carry",
                   ["additionner deux nombres < 100 avec retenue"],
                   ["addition posée avec retenue", "problème additif à retenue"],
                   ["résultat exact", "gestion correcte de la retenue"]),
    _math_ce1_node("math.CE1.sub_within_100_borrow",
                   ["soustraire deux nombres < 100 avec emprunt"],
                   ["soustraction posée avec emprunt", "problème de retrait"],
                   ["résultat exact", "gestion correcte de l'emprunt"]),
]

CE1_PROGRAM = {
    "class_level": "CE1",
    "cycle": "cycle 2",
    "status": "partial-seed",
    "disclaimer": CE1_DISCLAIMER,
    "disciplines": {
        "français": ["orthographe grammaticale", "conjugaison"],
        "mathématiques": ["nombres et calculs"],
    },
    "nodes": CE1_FRANCAIS_NODES + CE1_MATHS_NODES,
}


def _plural_transfer(category: str):
    return [t for t in transfer_bank_fr() if t.category == category]


RUNNABLE_CE1: dict[str, RunnableNode] = {
    "fr.CE1.pluriel_reguliers": RunnableNode(
        "fr.CE1.pluriel_reguliers", "français", "orthographe grammaticale",
        build=lambda rng: build_bank_fr("fr.CE1.pluriel_reguliers", rng),
        transfer=lambda: _plural_transfer("reg")),
    "fr.CE1.pluriel_en_al": RunnableNode(
        "fr.CE1.pluriel_en_al", "français", "orthographe grammaticale",
        build=lambda rng: build_bank_fr("fr.CE1.pluriel_en_al", rng),
        transfer=lambda: _plural_transfer("al")),
    "fr.CE1.present_verbes_er": RunnableNode(
        "fr.CE1.present_verbes_er", "français", "conjugaison",
        build=lambda rng: build_bank_conj("fr.CE1.present_verbes_er", rng),
        transfer=lambda: transfer_bank_conj("fr.CE1.present_verbes_er")),
    "math.CE1.add_within_100_nocarry": RunnableNode(
        "math.CE1.add_within_100_nocarry", "mathématiques", "nombres et calculs",
        build=lambda rng: build_bank_math("math.CE1.add_within_100_nocarry", rng)),
    "math.CE1.add_within_100_carry": RunnableNode(
        "math.CE1.add_within_100_carry", "mathématiques", "nombres et calculs",
        build=lambda rng: build_bank_math("math.CE1.add_within_100_carry", rng),
        transfer=lambda: _math_transfer()),
    "math.CE1.sub_within_100_borrow": RunnableNode(
        "math.CE1.sub_within_100_borrow", "mathématiques", "nombres et calculs",
        build=lambda rng: build_bank_math("math.CE1.sub_within_100_borrow", rng)),
}


# ============================================================================
# CE2 — extension again. The interesting research case: CE2 arithmetic
# (add/sub within 1000) reuses place value + number facts + **carry/borrow**,
# all of which CE1 now teaches — so CE1→CE2 transfer should succeed where
# CP→CE1 was blocked (carry was new at CE1). French (invariable plurals) is
# mostly new again.
# ============================================================================
CE2_DISCLAIMER = (
    "Registre aligné sur les attendus officiels du CE2 — jeu amorce partiel, "
    "vérifié à la main (PAS un ingest exhaustif du Bulletin officiel)."
)


def _math_ce2_node(nid: str, attendus, ex, crit) -> dict:
    spec = MATH_NODES[nid]
    return {
        "id": nid, "title": spec["title"], "class_level": "CE2",
        "subject": "mathématiques", "discipline": "nombres et calculs",
        "required_skills": spec["required_skills"],
        "prerequisites": spec.get("prerequisites", []),
        "mastery_threshold": spec["mastery_threshold"],
        "end_of_year_expectations": attendus,
        "exercise_types": ex, "evaluation_criteria": crit,
    }


CE2_MATHS_NODES = [
    _math_ce2_node("math.CE2.add_within_1000",
                   ["additionner des nombres < 1000 (avec retenues)"],
                   ["addition posée < 1000", "problème additif à plusieurs retenues"],
                   ["résultat exact", "retenues propagées correctement"]),
    _math_ce2_node("math.CE2.sub_within_1000",
                   ["soustraire des nombres < 1000 (avec emprunts)"],
                   ["soustraction posée < 1000", "problème de retrait à emprunts"],
                   ["résultat exact", "emprunts propagés correctement"]),
]

CE2_FRANCAIS_NODES = [{
    "id": "fr.CE2.pluriel_invariables", "title": NODES_FR["fr.CE2.pluriel_invariables"]["title"],
    "class_level": "CE2", "subject": "français", "discipline": "orthographe grammaticale",
    "required_skills": NODES_FR["fr.CE2.pluriel_invariables"]["required_skills"],
    "mastery_threshold": NODES_FR["fr.CE2.pluriel_invariables"]["mastery_threshold"],
    "end_of_year_expectations": ["reconnaître les noms invariables (-s/-x/-z)"],
    "exercise_types": ["pluriel des noms invariables"],
    "evaluation_criteria": ["pas d'ajout de -s à un nom déjà en -s/-x/-z"],
}]

CE2_PROGRAM = {
    "class_level": "CE2", "cycle": "cycle 2", "status": "partial-seed",
    "disclaimer": CE2_DISCLAIMER,
    "disciplines": {"français": ["orthographe grammaticale"],
                    "mathématiques": ["nombres et calculs"]},
    "nodes": CE2_FRANCAIS_NODES + CE2_MATHS_NODES,
}

RUNNABLE_CE2: dict[str, RunnableNode] = {
    "fr.CE2.pluriel_invariables": RunnableNode(
        "fr.CE2.pluriel_invariables", "français", "orthographe grammaticale",
        build=lambda rng: build_bank_fr("fr.CE2.pluriel_invariables", rng)),
    "math.CE2.add_within_1000": RunnableNode(
        "math.CE2.add_within_1000", "mathématiques", "nombres et calculs",
        build=lambda rng: build_bank_math("math.CE2.add_within_1000", rng)),
    "math.CE2.sub_within_1000": RunnableNode(
        "math.CE2.sub_within_1000", "mathématiques", "nombres et calculs",
        build=lambda rng: build_bank_math("math.CE2.sub_within_1000", rng)),
}


# ---- Public API ------------------------------------------------------------
_PROGRAMS = {"CP": CP_PROGRAM, "CE1": CE1_PROGRAM, "CE2": CE2_PROGRAM}
_RUNNABLE = {"CP": RUNNABLE_CP, "CE1": RUNNABLE_CE1, "CE2": RUNNABLE_CE2}


def runnable_for(grade: str) -> dict:
    if grade not in _RUNNABLE:
        raise NotImplementedError(f"no runnable set for {grade!r} (have {sorted(_RUNNABLE)})")
    return _RUNNABLE[grade]


def disclaimer_for(grade: str) -> str:
    return _PROGRAMS.get(grade, {}).get("disclaimer", "")


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
    """A registry pre-loaded with the CP seed set (français + maths) — aligned
    with official CP expectations, partial and hand-verified (see
    ``SEED_DISCLAIMER``), not a full BO ingest."""
    return register_class(CurriculumRegistry(), "CP")


def official_ce1_registry() -> CurriculumRegistry:
    """A registry pre-loaded with the CE1 seed set (extension of the CP core)."""
    return register_class(CurriculumRegistry(), "CE1")


def official_ce2_registry() -> CurriculumRegistry:
    """A registry pre-loaded with the CE2 seed set (extension of the CE1 core)."""
    return register_class(CurriculumRegistry(), "CE2")
