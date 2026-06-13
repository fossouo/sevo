"""Live exercise generation by Emma — strict contract enforced by code.

Emma generates training items only; the curriculum computes ground truth; a
leakage guard drops any generated item that collides with the evaluation probes.
"""
import pytest

from sevo.curriculum.factory import heldout_bank
from sevo.curriculum.fr_cp_ce1 import build_bank_fr
from sevo.rng import Rng
from sevo.teacher import LiveExerciseGenerator
from sevo.teacher.emma_litellm import EmmaLiteLLM, FakeTransport

NODE = "fr.CE1.pluriel_en_al"


def test_generation_is_inert_by_default():
    with pytest.raises(RuntimeError, match="inert"):
        LiveExerciseGenerator().training_items(NODE, 3)


def test_leakage_guard_drops_probe_words():
    bank = build_bank_fr(NODE, Rng(0).fork(NODE))   # same split as heldout_bank(NODE, 0)
    held_word = bank.heldout[0].word                # an evaluation probe word
    safe_word = bank.teaching[0].word               # a legitimate training word
    fake = FakeTransport([held_word, safe_word])
    gen = LiveExerciseGenerator(EmmaLiteLLM(transport=fake), seed=0)

    out = gen.training_items(NODE, 2)
    words = [t.word for t in out["items"]]
    assert held_word not in words                   # refused — too close to a probe
    assert safe_word in words                        # legitimate training item kept
    assert out["n_dropped_as_probe_collision"] >= 1


def test_ground_truth_comes_from_curriculum_not_emma():
    bank = build_bank_fr(NODE, Rng(0).fork(NODE))
    safe_word = bank.teaching[0].word
    gen = LiveExerciseGenerator(EmmaLiteLLM(transport=FakeTransport([safe_word])), seed=0)
    item = gen.training_items(NODE, 1)["items"][0]
    assert item.answer.endswith("aux")             # plural computed by the curriculum


def test_generated_items_disjoint_from_all_probes():
    held = heldout_bank(NODE, 0)
    bank = build_bank_fr(NODE, Rng(0).fork(NODE))
    fake = FakeTransport([t.word for t in held[:3]] + [bank.teaching[0].word])
    gen = LiveExerciseGenerator(EmmaLiteLLM(transport=fake), seed=0)
    out = gen.training_items(NODE, 5)
    probe_keys = {t.memo_key for t in held}
    assert all(t.memo_key not in probe_keys for t in out["items"])
