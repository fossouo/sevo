"""Structured lexical resource — the real-word gate for live teaching.

Checks the resource carries lemmas, inflected forms, grade levels and traceable
sources, exposes grade-appropriateness, and keeps the flat ``in_lexicon`` /
``NOUNS`` API the plural gate relies on.
"""
from sevo.curriculum.fr_lexicon import (
    NOUNS,
    SOURCES,
    entry_for,
    grade_level,
    in_lexicon,
    is_age_appropriate,
)


def test_in_lexicon_backward_compatible():
    assert in_lexicon("journal") and in_lexicon("hôpital") and in_lexicon("chat")
    assert not in_lexicon("éral")          # the hallucination the gate must reject
    assert "journal" in NOUNS


def test_inflected_forms_are_attested():
    # a plural form resolves to its lemma entry
    assert in_lexicon("journaux")
    assert entry_for("journaux").lemma == "journal"
    assert in_lexicon("chevaux") and entry_for("chevaux").lemma == "cheval"


def test_entries_have_traceable_metadata():
    e = entry_for("bateau")
    assert e.grade == "CP"
    assert e.freq_band
    assert e.source in SOURCES             # provenance is declared
    assert e.pos == "nom"


def test_grade_level_and_age_appropriateness():
    assert grade_level("chat") == "CP"
    assert grade_level("oignon") == "CE1"
    assert is_age_appropriate("chat", "CP")
    assert not is_age_appropriate("oignon", "CP")   # CE1 word not appropriate for CP
    assert is_age_appropriate("oignon", "CE1")
    assert is_age_appropriate("chat", "CE2")        # earlier word still appropriate later
