"""French lexical resource — the *real-word* gate for live teaching.

The first live Emma run surfaced a sharp limitation: morphological vetting
(``fr_cp_ce1.vet_word``) checks the *shape* of a proposed word, so it correctly
drops irregular ``-al`` exceptions and mis-categorised words — but it cannot
tell a real noun from a hallucination of the right shape. A model that invents
``« éral »`` (well-formed, not a known exception) would have its fake plural
``« éraux »`` taught as ground truth.

This module upgrades the original flat whitelist into a **structured lexical
resource**: every entry carries a lemma, its inflected forms, a frequency band,
an estimated school grade, a part of speech, and a traceable source. A
model-proposed word becomes a teaching item only if it (or one of its forms) is
**attested** here — and, for grade-targeted ingestion, only if its estimated
grade is appropriate for the class.

Provenance (see ``SOURCES``): the per-grade frequency / acquisition data this
resource is *modelled on* are the real French school references — Manulex
(Lété, Sprenger-Charolles & Colé, 2004), the Échelle d'acquisition orthographique
Dubois-Buyse, and the Éduscol/BO CP word lists. The list embedded here is a
**curated, hand-verified bootstrap subset** (CP core + the words the built-in
curriculum uses), not the full database. Ingesting a class' official programme
means loading that grade's slice of the full resource through the same shape.

Backward compatibility: ``in_lexicon`` and ``NOUNS`` keep working exactly as the
flat whitelist did, so the plural-domain gate is unchanged.
"""
from __future__ import annotations

from dataclasses import dataclass, field

# ---- Provenance --------------------------------------------------------------
# IMPORTANT: these are **methodological references** — the public resources this
# lexicon's metadata (frequency band, grade) is *modelled on*. They are NOT
# embedded here as datasets: no Manulex/Dubois-Buyse table is bundled or copied.
# The entries below are a hand-verified bootstrap subset; a real ingest would
# load each reference's licensed data and tag every entry with its row source.
PROVENANCE_NOTE = (
    "Provenance méthodologique uniquement : les bandes de fréquence et niveaux "
    "scolaires sont MODÉLISÉS sur les références ci-dessous, qui ne sont PAS "
    "embarquées comme jeux de données. Les entrées sont un sous-ensemble amorce "
    "vérifié à la main."
)
SOURCES = {
    "manulex": "Référence méthodologique (non embarquée) : Manulex — fréquences "
               "lexicales des manuels scolaires (Lété, Sprenger-Charolles & Colé, "
               "2004), graduées CP→CM2.",
    "dubois-buyse": "Référence méthodologique (non embarquée) : Échelle "
                    "d'acquisition orthographique Dubois-Buyse (mots par échelon).",
    "bo-cp": "Référence méthodologique (non embarquée) : Bulletin officiel / "
             "Éduscol — mots fréquents et attendus de fin d'année CP.",
    "builtin-curriculum": "Mots utilisés par les nœuds intégrés de Sèvo "
                          "(pluriel / conjugaison), vérifiés à la main.",
}

# Frequency bands (Manulex-style, coarse): U = très fréquent … rare.
FREQ_VERY_HIGH, FREQ_HIGH, FREQ_MID, FREQ_LOW = "very_high", "high", "mid", "low"

_GRADE_ORDER = ["CP", "CE1", "CE2", "CM1", "CM2", "6e", "5e", "4e", "3e",
                "2nde", "1ere", "Terminale"]


@dataclass(frozen=True)
class LexEntry:
    lemma: str
    forms: tuple = ()          # inflected forms (plurals, conjugations…)
    pos: str = "nom"           # part of speech
    freq_band: str = FREQ_MID
    grade: str = "CP"          # estimated grade of acquisition
    source: str = "manulex"

    def all_forms(self) -> tuple:
        return tuple({self.lemma, *self.forms})


def _n(lemma, plural, freq, grade, src="manulex"):
    """Helper: a noun entry (lemma + plural form)."""
    return LexEntry(lemma=lemma, forms=(plural,), pos="nom", freq_band=freq,
                    grade=grade, source=src)


# ---- CP core lexicon (hand-verified bootstrap subset, rich metadata) --------
# Nouns a CP reader meets first — high frequency, decodable or common sight words.
CP_LEXICON: list[LexEntry] = [
    _n("chat", "chats", FREQ_VERY_HIGH, "CP", "bo-cp"),
    _n("chien", "chiens", FREQ_VERY_HIGH, "CP", "bo-cp"),
    _n("chou", "choux", FREQ_HIGH, "CP"),
    _n("sac", "sacs", FREQ_HIGH, "CP"),
    _n("lit", "lits", FREQ_HIGH, "CP"),
    _n("rat", "rats", FREQ_MID, "CP"),
    _n("moulin", "moulins", FREQ_MID, "CP"),
    _n("bateau", "bateaux", FREQ_HIGH, "CP", "bo-cp"),
    _n("lapin", "lapins", FREQ_HIGH, "CP"),
    _n("fourmi", "fourmis", FREQ_MID, "CP"),
    _n("domino", "dominos", FREQ_LOW, "CP"),
    _n("manteau", "manteaux", FREQ_MID, "CP"),
    _n("souris", "souris", FREQ_HIGH, "CP"),
    _n("tapis", "tapis", FREQ_MID, "CP"),
    _n("chocolat", "chocolats", FREQ_HIGH, "CP"),
    _n("pirate", "pirates", FREQ_LOW, "CP"),
    _n("jardin", "jardins", FREQ_HIGH, "CP", "bo-cp"),
    _n("mouton", "moutons", FREQ_MID, "CP"),
    _n("tortue", "tortues", FREQ_MID, "CP"),
    _n("banane", "bananes", FREQ_MID, "CP"),
    _n("robe", "robes", FREQ_MID, "CP"),
    _n("tomate", "tomates", FREQ_MID, "CP"),
    _n("salade", "salades", FREQ_MID, "CP"),
    _n("table", "tables", FREQ_VERY_HIGH, "CP", "bo-cp"),
    _n("école", "écoles", FREQ_VERY_HIGH, "CP", "bo-cp"),
    _n("papa", "papas", FREQ_VERY_HIGH, "CP"),
    _n("maman", "mamans", FREQ_VERY_HIGH, "CP"),
    _n("ami", "amis", FREQ_HIGH, "CP", "bo-cp"),
    _n("vélo", "vélos", FREQ_HIGH, "CP"),
    _n("moto", "motos", FREQ_MID, "CP"),
    _n("fenêtre", "fenêtres", FREQ_MID, "CP"),
    _n("maison", "maisons", FREQ_VERY_HIGH, "CP", "bo-cp"),
    _n("fleur", "fleurs", FREQ_HIGH, "CP"),
    _n("livre", "livres", FREQ_HIGH, "CP", "bo-cp"),
    # Common irregular / sight words (GPC would mis-read them).
    _n("femme", "femmes", FREQ_VERY_HIGH, "CP", "bo-cp"),
    _n("fils", "fils", FREQ_HIGH, "CP", "dubois-buyse"),
    LexEntry("monsieur", ("messieurs",), "nom", FREQ_VERY_HIGH, "CP", "bo-cp"),
    _n("oignon", "oignons", FREQ_LOW, "CE1", "dubois-buyse"),
    _n("pays", "pays", FREQ_HIGH, "CE1", "dubois-buyse"),
]

# ---- Curriculum-domain words (kept attested for the plural / conjugation
# gates; lighter metadata, verified by hand). --------------------------------
_PLURAL_WORDS = [
    # regular -s
    ("voiture", "voitures"), ("arbre", "arbres"), ("chaise", "chaises"),
    ("lampe", "lampes"), ("porte", "portes"), ("stylo", "stylos"),
    ("ballon", "ballons"), ("sac", "sacs"), ("pont", "ponts"),
    ("train", "trains"), ("mur", "murs"), ("image", "images"),
    ("route", "routes"), ("ferme", "fermes"), ("nuage", "nuages"),
    ("crayon", "crayons"), ("tigre", "tigres"), ("guitare", "guitares"),
    ("montagne", "montagnes"),
    # -al -> -aux
    ("cheval", "chevaux"), ("journal", "journaux"), ("animal", "animaux"),
    ("hôpital", "hôpitaux"), ("général", "généraux"), ("bocal", "bocaux"),
    ("canal", "canaux"), ("local", "locaux"), ("métal", "métaux"),
    ("signal", "signaux"), ("végétal", "végétaux"), ("cardinal", "cardinaux"),
    ("total", "totaux"), ("rival", "rivaux"), ("tribunal", "tribunaux"),
    ("terminal", "terminaux"), ("minéral", "minéraux"), ("littoral", "littoraux"),
    ("amiral", "amiraux"), ("arsenal", "arsenaux"), ("maréchal", "maréchaux"),
    ("caporal", "caporaux"),
    # invariable
    ("nez", "nez"), ("prix", "prix"), ("voix", "voix"), ("croix", "croix"),
    ("bras", "bras"), ("tas", "tas"), ("repas", "repas"), ("corps", "corps"),
    ("bois", "bois"), ("choix", "choix"), ("noix", "noix"), ("gaz", "gaz"),
    ("riz", "riz"), ("dos", "dos"),
]

_CURRICULUM_ENTRIES = [
    _n(lemma, plural, FREQ_MID, "CE1", "builtin-curriculum")
    for lemma, plural in _PLURAL_WORDS
]

# ---- Indexes -----------------------------------------------------------------
ALL_ENTRIES: tuple = tuple(CP_LEXICON) + tuple(_CURRICULUM_ENTRIES)

_FORMS_INDEX: dict = {}
for _e in ALL_ENTRIES:
    for _f in _e.all_forms():
        _FORMS_INDEX.setdefault(_f.lower(), _e)

# Backward-compatible flat set (every lemma and inflected form).
NOUNS: frozenset = frozenset(_FORMS_INDEX.keys())


def in_lexicon(word: str) -> bool:
    """Is ``word`` (a lemma or any inflected form) an attested French word?"""
    return word.strip().lower() in _FORMS_INDEX


def entry_for(word: str) -> LexEntry | None:
    return _FORMS_INDEX.get(word.strip().lower())


def grade_level(word: str) -> str | None:
    e = entry_for(word)
    return e.grade if e else None


def is_age_appropriate(word: str, class_level: str) -> bool:
    """True if ``word`` is acquired at or before ``class_level`` (so a CP node
    should not be fed CM2 vocabulary)."""
    e = entry_for(word)
    if e is None or class_level not in _GRADE_ORDER or e.grade not in _GRADE_ORDER:
        return False
    return _GRADE_ORDER.index(e.grade) <= _GRADE_ORDER.index(class_level)
