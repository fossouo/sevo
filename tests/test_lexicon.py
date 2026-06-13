"""Structured lexical resource — the real-word gate for live teaching.

Checks the resource carries lemmas, inflected forms, grade levels and traceable
sources, exposes grade-appropriateness, and keeps the flat ``in_lexicon`` /
``NOUNS`` API the plural gate relies on.
"""
import pytest

from sevo.curriculum.fr_lexicon import (
    BUILTIN_RESOURCE,
    NOUNS,
    SOURCES,
    LexiconResource,
    ProvenanceError,
    ResourceManifest,
    builtin_resource,
    entry_for,
    grade_level,
    in_lexicon,
    is_age_appropriate,
    load_external,
)
from sevo.rng import Rng


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


# ---- resource integration: provenance/license gate + splits ----------------
def test_resource_refuses_unlicensed_or_opaque():
    rows = [{"lemma": "chat", "forms": ["chats"], "grade": "CP", "source": "x"}]
    with pytest.raises(ProvenanceError):                      # no verified license
        load_external(rows, ResourceManifest(name="r", license="unknown", source="s"))
    with pytest.raises(ProvenanceError):                      # entry without a source
        load_external([{"lemma": "chat", "forms": ["chats"], "grade": "CP", "source": ""}],
                      ResourceManifest(name="r", license="CC-BY", source="s"))


def test_external_resource_loads_under_a_verified_license():
    rows = [{"lemma": "chat", "forms": ["chats"], "grade": "CP", "source": "manulex",
             "freq_band": "high"}]
    res = load_external(rows, ResourceManifest(name="manulex-sample", license="LGPLLR",
                                               source="Manulex", url="http://...", retrieved="2026-06-13"))
    assert isinstance(res, LexiconResource) and "chats" in res and len(res) == 1


def test_builtin_resource_is_licensed_and_traceable():
    res = builtin_resource()
    assert res.manifest.license in {"curated-internal"}
    assert res.manifest.source                                # traceable origin
    assert "journal" in BUILTIN_RESOURCE                       # bundled seed usable


def test_grade_split_is_disjoint_and_deterministic():
    s1 = BUILTIN_RESOURCE.split("CP", Rng(7))
    s2 = BUILTIN_RESOURCE.split("CP", Rng(7))
    assert s1 == s2                                            # deterministic
    train, held, trans = set(s1["train"]), set(s1["heldout"]), set(s1["transfer"])
    assert not (train & held) and not (train & trans) and not (held & trans)  # disjoint
    assert train and (held or trans)
