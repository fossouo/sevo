"""CP / CE1 French curriculum (MVP environment) — plural of nouns.

A second domain, deliberately NOT arithmetic, to show the brain's cognitive core
generalises: the same procedural/consolidation/oracle machinery learns a
rule-based French competency with the same measurable properties (held-out gain,
transfer to unseen words, consolidation-driven retention, anti-leakage).

Competency: forming the plural of a noun.
  * regular     -> add ``-s``                         (chat -> chats)
  * exception   -> nouns in ``-al`` become ``-aux``   (cheval -> chevaux)
  * invariable  -> nouns in ``-s/-x/-z`` don't change (souris -> souris)

Characteristic child errors (what a low-mastery skill produces):
  * over-regularisation of ``-al`` words: "chevals" instead of "chevaux";
  * forgetting the ``-s`` on regular plurals;
  * wrongly adding ``-s`` to an invariable noun.

Transfer is real: the ``-aux`` and ``-s`` rules are skills, so once learned they
apply to words never seen in teaching. A pure memoriser cannot do this.
"""
from __future__ import annotations

from dataclasses import dataclass, field

from ..rng import Rng
from .base import Task

SKILLS_FR = [
    "grapheme_recognition",   # identify the relevant word ending
    "plural_rule_s",          # the general "+s" rule
    "plural_exception_aux",   # the "-al -> -aux" rule
    "plural_invariant",       # "-s/-x/-z stays put" rule
]


def regular_plural(word: str) -> str:
    return word + "s"


def al_plural(word: str) -> str:
    return word[:-2] + "aux"  # cheval -> chevaux


# Nouns/adjectives ending in -al that take a regular -s plural (NOT -aux).
# The brain must not be taught "finaux"/"bancals"; the curriculum refuses to
# grade these under the -al->-aux node. (Surfaced by the first live Emma run:
# the model happily proposes exception words.)
AL_S_EXCEPTIONS = {
    "bal", "carnaval", "chacal", "festival", "récital", "regal", "régal", "cal",
    "aval", "étal", "pal", "final", "fatal", "natal", "naval", "banal", "bancal",
    "glacial", "tonal", "bengal", "serval", "narval", "chersal", "nopal", "sisal",
}
_INVARIABLE_ENDINGS = ("s", "x", "z")
_SPECIAL_X_ENDINGS = ("eau", "eu", "au")  # take -x, handled by other rules


def vet_word(category: str, word: str) -> bool:
    """Is ``word`` safe to grade under this plural category? Used to filter
    model-proposed words so the brain is never taught a wrong plural."""
    w = word.strip().lower()
    if not w or " " in w or not w.isalpha():
        return False
    if category == "al":
        return w.endswith("al") and w not in AL_S_EXCEPTIONS
    if category == "inv":
        return w.endswith(_INVARIABLE_ENDINGS)
    # regular: plain "+s" words only — exclude endings governed by other rules.
    if w.endswith(_INVARIABLE_ENDINGS) or w.endswith("al") or w.endswith(_SPECIAL_X_ENDINGS):
        return False
    return True


@dataclass
class PluralTask(Task):
    node_id: str
    word: str             # singular
    answer: str           # correct plural
    required_skills: dict
    category: str         # "reg" | "al" | "inv"

    @property
    def prompt(self) -> str:
        return f"Pluriel de « {self.word} » ?"

    @property
    def working_set(self) -> list:
        return [self.word, self.category]

    def mistake(self, weak_skill: str) -> tuple[str, str]:
        if self.category == "al" and weak_skill == "plural_exception_aux":
            return regular_plural(self.word), "overregularized_plural"   # "chevals"
        if self.category == "inv" and weak_skill == "plural_invariant":
            return regular_plural(self.word), "added_s_to_invariable"
        if weak_skill == "plural_rule_s":
            return self.word, "forgot_s"                                  # singular unchanged
        if weak_skill == "grapheme_recognition":
            return regular_plural(self.word), "misread_ending"           # defaults to +s
        return self.word, "no_rule_applied"


# ---- Word stock (disjoint from the transfer stock below) -------------------
REGULAR = [
    "chat", "chien", "livre", "table", "fleur", "maison", "voiture", "arbre",
    "ami", "chaise", "lampe", "porte", "jardin", "stylo", "ballon", "vélo",
    "robe", "sac", "pont", "train", "mur", "image", "route", "ferme",
]
AL = [
    "cheval", "journal", "animal", "hôpital", "général", "bocal", "canal",
    "local", "métal", "signal", "végétal", "cardinal", "total", "rival",
    "tribunal", "terminal",
]
INVARIABLE = [
    "souris", "nez", "prix", "voix", "croix", "bras", "tas", "repas",
    "pays", "corps", "bois", "choix", "noix", "gaz", "riz", "dos",
]

NODES_FR: dict[str, dict] = {
    "fr.CE1.pluriel_reguliers": {
        "title": "Pluriel régulier des noms (+s)",
        "category": "reg", "stock": REGULAR,
        "required_skills": {"grapheme_recognition": 0.3, "plural_rule_s": 0.7},
        "mastery_threshold": 0.8,
    },
    "fr.CE1.pluriel_en_al": {
        "title": "Pluriel des noms en -al (-aux)",
        "category": "al", "stock": AL,
        "required_skills": {"grapheme_recognition": 0.3, "plural_exception_aux": 0.7},
        "mastery_threshold": 0.8,
    },
    "fr.CE2.pluriel_invariables": {
        "title": "Noms invariables (-s/-x/-z)",
        "category": "inv", "stock": INVARIABLE,
        "required_skills": {"grapheme_recognition": 0.4, "plural_invariant": 0.6},
        "mastery_threshold": 0.8,
    },
}


def _answer(category: str, word: str) -> str:
    if category == "reg":
        return regular_plural(word)
    if category == "al":
        return al_plural(word)
    return word  # invariable


def _make(node_id: str, word: str) -> PluralTask:
    spec = NODES_FR[node_id]
    return PluralTask(
        node_id=node_id, word=word, answer=_answer(spec["category"], word),
        required_skills=dict(spec["required_skills"]), category=spec["category"],
    )


@dataclass
class Bank:
    teaching: list = field(default_factory=list)
    heldout: list = field(default_factory=list)


def build_bank_fr(node_id: str, rng: Rng, frac_teach: float = 0.55) -> Bank:
    """Split a node's word stock into DISJOINT teaching and held-out sets."""
    spec = NODES_FR[node_id]
    words = list(spec["stock"])
    rng.shuffle(words)
    cut = max(1, int(len(words) * frac_teach))
    teaching = [_make(node_id, w) for w in words[:cut]]
    heldout = [_make(node_id, w) for w in words[cut:]]
    return Bank(teaching=teaching, heldout=heldout)


def make_banks_fr(rng: Rng, node_ids: list[str]) -> dict[str, Bank]:
    return {nid: build_bank_fr(nid, rng.fork(nid)) for nid in node_ids}


# ---- Transfer stock: words NEVER used in teaching --------------------------
# If the brain learned the *rule*, it applies it to these unseen words. A pure
# memoriser, which only stored teaching words, scores at chance here. Every word
# is vetted (regular +s; clean -al->-aux, no -als exceptions) so the ground
# truth is correct.
TRANSFER_REG = ["nuage", "crayon", "tigre", "banane", "guitare", "montagne"]
TRANSFER_AL = ["minéral", "littoral", "amiral", "arsenal", "maréchal", "caporal"]


def transfer_bank_fr() -> list:
    out = []
    for w in TRANSFER_REG:
        assert vet_word("reg", w), w
        out.append(PluralTask("fr.transfer.pluriel_reguliers", w, regular_plural(w),
                              {"grapheme_recognition": 0.3, "plural_rule_s": 0.7}, "reg"))
    for w in TRANSFER_AL:
        assert vet_word("al", w), w
        out.append(PluralTask("fr.transfer.pluriel_en_al", w, al_plural(w),
                              {"grapheme_recognition": 0.3, "plural_exception_aux": 0.7}, "al"))
    return out
