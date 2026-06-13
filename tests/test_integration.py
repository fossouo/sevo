"""Live-edge integration: the LiteLLM Emma adapter and curriculum ingestion.

The adapter must stay inert by default, strip Anthropic credentials, and — when
given a transport — produce gradable tasks the brain can actually learn from.
"""
import os

import pytest

from sevo.brain import Brain
from sevo.curriculum.ingestion import CurriculumError, CurriculumRegistry, builtin_registry
from sevo.teacher.emma_litellm import EmmaLiteLLM, FakeTransport, _safe_env


def test_emma_is_inert_by_default(monkeypatch):
    monkeypatch.delenv("SEVO_EMMA_LIVE", raising=False)
    monkeypatch.delenv("LITELLM_URL", raising=False)
    assert EmmaLiteLLM.is_enabled() is False
    with pytest.raises(RuntimeError, match="inert"):
        EmmaLiteLLM().generate_french_tasks("fr.CE1.pluriel_reguliers", 3)


def test_safe_env_strips_anthropic_keys(monkeypatch):
    monkeypatch.setenv("ANTHROPIC_API_KEY", "sk-should-not-leak")
    monkeypatch.setenv("ANTHROPIC_BASE_URL", "https://api.anthropic.com")
    env = _safe_env()
    assert "ANTHROPIC_API_KEY" not in env
    assert "ANTHROPIC_BASE_URL" not in env


def test_emma_builds_gradable_tasks_offline():
    """With an injected transport, the adapter turns model output into tasks
    whose answers are computed by the curriculum (not the model)."""
    fake = FakeTransport(["bocal", "journal", "hôpital"])
    emma = EmmaLiteLLM(transport=fake)
    tasks = emma.generate_french_tasks("fr.CE1.pluriel_en_al", 3)
    assert [t.word for t in tasks] == ["bocal", "journal", "hôpital"]
    assert [t.answer for t in tasks] == ["bocaux", "journaux", "hôpitaux"]  # ground truth, not the LLM's


def test_brain_learns_from_emma_generated_tasks():
    fake = FakeTransport(["bocal", "journal", "hôpital", "canal", "local", "métal", "signal", "rival"])
    emma = EmmaLiteLLM(transport=fake)
    brain = Brain(seed=1)
    for _ in range(6):
        brain.learn_session("CE1", "français", emma.generate_french_tasks("fr.CE1.pluriel_en_al", 8))
    assert brain.semantic.mastery("fr.CE1.pluriel_en_al") >= 0.6


def test_ingestion_accepts_official_shaped_node():
    reg = CurriculumRegistry()
    reg.ingest({
        "id": "fr.CP.correspondance_graphophonologique",
        "title": "Correspondances graphèmes-phonèmes",
        "class_level": "CP", "subject": "français",
        "required_skills": {"grapheme_recognition": 0.6, "plural_rule_s": 0.4},
        "learning_objectives": ["décoder des syllabes simples"],
        "mastery_threshold": 0.8,
    })
    assert reg.get("fr.CP.correspondance_graphophonologique").class_level == "CP"
    assert len(reg.by_subject("français")) == 1


def test_ingestion_rejects_malformed_nodes():
    reg = CurriculumRegistry()
    with pytest.raises(CurriculumError):
        reg.ingest({"id": "x", "title": "t", "class_level": "CP", "subject": "maths"})  # no skills
    with pytest.raises(CurriculumError):
        reg.ingest({"id": "x", "title": "t", "class_level": "CXX", "subject": "maths",
                    "required_skills": {"a": 1.0}})  # bad class
    with pytest.raises(CurriculumError):
        reg.ingest({"id": "x", "title": "t", "class_level": "CP", "subject": "maths",
                    "required_skills": {"a": 0.5, "b": 0.2}})  # weights != 1


def test_vet_word_rejects_irregular_and_miscategorised():
    from sevo.curriculum.fr_cp_ce1 import vet_word
    # -al category: clean -aux words pass, -als exceptions are rejected
    assert vet_word("al", "animal") and vet_word("al", "journal")
    assert not vet_word("al", "final")    # final -> finals (exception)
    assert not vet_word("al", "bengal")   # bengal -> bengals
    assert not vet_word("al", "chat")     # not an -al word
    # regular: plain +s only
    assert vet_word("reg", "chat")
    assert not vet_word("reg", "cheval")  # -> chevaux, wrong category
    assert not vet_word("reg", "souris")  # invariable
    # invariable: must end in s/x/z
    assert vet_word("inv", "souris") and vet_word("inv", "prix")
    assert not vet_word("inv", "chat")
    # garbage rejected
    assert not vet_word("al", "x y z")


def test_emma_drops_exception_words_offline():
    """Given a mix including -als exceptions, only clean -aux words become tasks."""
    fake = FakeTransport(["animal", "final", "journal", "bengal", "local", "canal"])
    emma = EmmaLiteLLM(transport=fake)
    tasks = emma.generate_french_tasks("fr.CE1.pluriel_en_al", 6)
    words = [t.word for t in tasks]
    assert "final" not in words and "bengal" not in words
    assert set(words) <= {"animal", "journal", "local", "canal"}
    assert all(t.answer.endswith("aux") for t in tasks)


def test_builtin_registry_has_both_domains():
    reg = builtin_registry()
    assert len(reg.by_subject("mathématiques")) >= 3
    assert len(reg.by_subject("français")) >= 3
    # the never-taught metacognition probe is excluded
    assert "math.CE2.multiply_table" not in reg.nodes
