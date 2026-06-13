"""CE1/CE2 French curriculum — present tense of regular ``-er`` verbs.

A *third* domain, again deliberately not arithmetic and not the plural-of-nouns
rule, to show the cognitive core is not specialised to either. Conjugating a
regular ``-er`` verb in the present tense is a clean rule:

    stem = verb without its ``-er``      (parler -> parl)
    je   -> stem + e        nous -> stem + ons
    tu   -> stem + es        vous -> stem + ez
    il   -> stem + e          ils  -> stem + ent

The answer graded is the conjugated *verb form* only (no pronoun), so there is
no elision noise (``j'aime`` vs ``je aime``).

Characteristic beginner errors (what a low-mastery skill produces):
  * ``present_er_endings`` weak  -> writes the **infinitive** ("je parler");
  * ``verb_stem_recognition`` weak -> keeps the ``-er`` before the ending
    ("nous parlerons" for the present);
  * ``subject_agreement`` weak  -> swaps singular/plural endings
    ("ils parle", "nous parlent").

Transfer is real: the endings are a *skill*, so once learned they conjugate
verbs never seen in teaching. A pure memoriser, which stored (verb, pronoun)
pairs, scores at chance on unseen verbs. The skill ``grapheme_recognition`` is
shared with the plural domain, so prerequisite practice transfers across
domains (measured by the efficiency control).
"""
from __future__ import annotations

from dataclasses import dataclass, field

from ..rng import Rng
from .base import Task

# New procedural primitives this domain introduces (grapheme_recognition is
# reused from the French plural domain — that shared skill is what makes
# cross-domain transfer measurable).
SKILLS_CONJ = [
    "verb_stem_recognition",  # strip the -er to find the stem
    "present_er_endings",     # the je/tu/il/nous/vous/ils ending set
    "subject_agreement",      # match the ending to the subject's number
]

PRONOUNS = ["je", "tu", "il", "nous", "vous", "ils"]
ENDINGS = {"je": "e", "tu": "es", "il": "e", "nous": "ons", "vous": "ez", "ils": "ent"}
_PLURAL = {"nous", "vous", "ils"}

# Regular -er verbs whose plain stem+ending conjugation is correct (no spelling
# change). Verbs in -ger/-cer/-yer, stem-changing verbs (lever, espérer…) and
# the irregular "aller" are excluded — they would need their own nodes.
ER_EXCEPTIONS = {"aller", "envoyer", "renvoyer"}
_BAD_ENDINGS = ("ger", "cer", "yer", "eler", "eter", "érer", "éter", "écer")


def stem_of(verb: str) -> str:
    return verb[:-2]  # drop the -er


def conjugate(verb: str, pronoun: str) -> str:
    return stem_of(verb) + ENDINGS[pronoun]


def vet_verb(verb: str) -> bool:
    """Is ``verb`` a regular -er verb whose present tense follows the plain rule?
    Used to filter model-proposed verbs so the brain is never taught a wrong
    conjugation (mirror of ``fr_cp_ce1.vet_word``)."""
    v = verb.strip().lower()
    if not v or " " in v or not v.isalpha() or len(v) < 4:
        return False
    if not v.endswith("er") or v in ER_EXCEPTIONS or v.endswith(_BAD_ENDINGS):
        return False
    stem = v[:-2]
    # Stem-changing verbs (mener, espérer, régler, célébrer…) carry an accented
    # e in the stem and break the plain rule — refuse them conservatively.
    if any(c in "éèê" for c in stem):
        return False
    return True


@dataclass
class ConjugationTask(Task):
    node_id: str
    verb: str             # infinitive
    pronoun: str
    answer: str           # correct conjugated form (verb only)
    required_skills: dict

    @property
    def prompt(self) -> str:
        return f"Conjugue « {self.verb} » avec « {self.pronoun} » : ?"

    @property
    def working_set(self) -> list:
        return [self.verb, self.pronoun]

    def mistake(self, weak_skill: str) -> tuple[str, str]:
        stem = stem_of(self.verb)
        if weak_skill == "subject_agreement":
            # swap number: singular gets the plural -ent, plural gets the je-form -e
            return (stem + "e" if self.pronoun in _PLURAL else stem + "ent"), "subject_verb_disagreement"
        if weak_skill == "verb_stem_recognition":
            return self.verb + ENDINGS[self.pronoun], "stem_not_reduced"      # parler+ons
        if weak_skill == "present_er_endings":
            return self.verb, "infinitive_used"                              # "je parler"
        if weak_skill == "grapheme_recognition":
            return self.verb, "infinitive_used"
        return self.verb, "no_rule_applied"


# ---- Verb stock (disjoint from the transfer stock below) -------------------
REGULAR_ER = [
    "parler", "chanter", "danser", "regarder", "donner", "trouver", "aimer",
    "marcher", "sauter", "dessiner", "raconter", "demander", "montrer",
    "porter", "fermer", "laver", "rester", "tomber", "penser", "habiter",
    "arriver", "jouer", "gagner", "travailler",
]

NODES_CONJ: dict[str, dict] = {
    "fr.CE1.present_verbes_er": {
        "title": "Présent des verbes en -er",
        "stock": REGULAR_ER,
        "required_skills": {
            "present_er_endings": 0.4,
            "verb_stem_recognition": 0.2,
            "subject_agreement": 0.2,
            "grapheme_recognition": 0.2,
        },
        "mastery_threshold": 0.8,
    },
}


def _make_conj(node_id: str, verb: str, pronoun: str) -> ConjugationTask:
    spec = NODES_CONJ[node_id]
    return ConjugationTask(
        node_id=node_id, verb=verb, pronoun=pronoun,
        answer=conjugate(verb, pronoun), required_skills=dict(spec["required_skills"]),
    )


@dataclass
class Bank:
    teaching: list = field(default_factory=list)
    heldout: list = field(default_factory=list)


def build_bank_conj(node_id: str, rng: Rng, frac_teach: float = 0.55) -> Bank:
    """Split the verb stock into DISJOINT teaching and held-out *verbs*; each
    verb expands into one task per pronoun. Held-out verbs are never seen in
    teaching, so credit there reflects the conjugation *rule*, not recall."""
    spec = NODES_CONJ[node_id]
    verbs = list(spec["stock"])
    rng.shuffle(verbs)
    cut = max(1, int(len(verbs) * frac_teach))
    teaching = [_make_conj(node_id, v, p) for v in verbs[:cut] for p in PRONOUNS]
    heldout = [_make_conj(node_id, v, p) for v in verbs[cut:] for p in PRONOUNS]
    return Bank(teaching=teaching, heldout=heldout)


# ---- Transfer stock: verbs NEVER used in teaching --------------------------
TRANSFER_ER = [
    "cuisiner", "bavarder", "grimper", "siffler", "galoper", "ramasser",
    "accrocher", "bricoler",
]


def transfer_bank_conj(node_id: str = "fr.CE1.present_verbes_er") -> list:
    out = []
    for v in TRANSFER_ER:
        assert vet_verb(v), v
        for p in PRONOUNS:
            out.append(_make_conj(node_id, v, p))
    return out
