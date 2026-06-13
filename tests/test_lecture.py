"""CP reading / decoding domain — the most structuring school competency.

Same guarantees as the other domains: held-out gain, rule transfer to unseen
words AND pseudo-words (the decoding gold standard), anti-leakage, and diagnostic
beginner errors (letter-by-letter, regularisation, role confusion).
"""
from sevo.baselines import MemorizerBrain
from sevo.brain import Brain
from sevo.curriculum.fr_lecture_cp import (
    IRREGULAR_WORDS,
    PSEUDO_WORDS,
    REGULAR_WORDS,
    _reading_task,
    _sentence_tasks,
    build_bank_lecture,
    decode_gpc,
    decode_letterwise,
    transfer_bank_comprehension,
    transfer_bank_lecture,
)
from sevo.rng import Rng
from sevo.services import AssessmentOracle
from sevo.teacher import teach_to_mastery


def _teach(node, seed=5):
    brain = Brain(seed=seed)
    bank = build_bank_lecture(node, Rng(seed).fork(node))
    teach_to_mastery(brain, node, bank)
    brain.consolidate("sleep", 1)
    brain.consolidate("error_replay", 0)
    return brain, bank


def test_regular_words_need_the_gpc_skill():
    """Each regular word is decodable by rule (decode_gpc) AND would be misread
    by a letter-by-letter beginner — so the GPC skill is genuinely required."""
    for w in REGULAR_WORDS:
        assert decode_gpc(w)                       # produces a phoneme string
        assert decode_letterwise(w) != decode_gpc(w)


def test_irregular_words_defeat_pure_gpc():
    """For sight words, applying GPC gives the WRONG (regularised) reading —
    that is exactly what makes them irregular and the regularisation the
    characteristic error."""
    for w, truth in IRREGULAR_WORDS.items():
        assert decode_gpc(w) != truth


def test_learns_regular_decoding_and_transfers_to_pseudowords():
    brain, bank = _teach("fr.CP.lecture_mots_reguliers")
    assert brain.evaluate(bank.heldout, "post")["accuracy"] >= 0.7
    transfer = transfer_bank_lecture()
    assert brain.evaluate(transfer, "transfer")["accuracy"] >= 0.6
    # pseudo-words alone (impossible to memorise) still decoded by rule
    pseudo = [_reading_task("fr.CP.lecture_mots_reguliers", w, "reg") for w in PSEUDO_WORDS]
    assert brain.evaluate(pseudo, "pseudo")["accuracy"] >= 0.5


def test_learns_irregular_sight_words():
    brain, bank = _teach("fr.CP.lecture_mots_irreguliers")
    assert brain.evaluate(bank.heldout, "post")["accuracy"] >= 0.7


def test_learns_sentence_comprehension_and_transfers():
    brain, bank = _teach("fr.CP.comprehension_phrase")
    assert brain.evaluate(bank.heldout, "post")["accuracy"] >= 0.7
    assert brain.evaluate(transfer_bank_comprehension(), "transfer")["accuracy"] >= 0.4


def test_memoriser_fails_on_unseen_words_and_pseudowords():
    bank = build_bank_lecture("fr.CP.lecture_mots_reguliers", Rng(3).fork("r"))
    mem = MemorizerBrain()
    mem.memorize(bank.teaching)
    oracle = AssessmentOracle()
    assert oracle.assess(mem, bank.teaching, "t")["accuracy"] >= 0.99
    assert oracle.assess(mem, bank.heldout, "h")["accuracy"] <= 0.1
    assert oracle.assess(mem, transfer_bank_lecture(), "x")["accuracy"] <= 0.1


def test_characteristic_letter_by_letter_error():
    cold = Brain(seed=9)
    task = _reading_task("fr.CP.lecture_mots_reguliers", "chat", "reg")
    answers = {cold.procedural.solve(task, 0, cold.rng)["answer"] for _ in range(30)}
    assert decode_letterwise("chat") in answers   # reads "chat" letter by letter
    assert task.answer == "S.a"


def test_characteristic_regularisation_error():
    cold = Brain(seed=9)
    task = _reading_task("fr.CP.lecture_mots_irreguliers", "femme", "irr")
    answers = {cold.procedural.solve(task, 0, cold.rng)["answer"] for _ in range(30)}
    assert decode_gpc("femme") in answers          # regularises "femme" -> /f@m/
    assert task.answer == "f.a.m"


def test_characteristic_role_confusion():
    cold = Brain(seed=9)
    task = _sentence_tasks("fr.CP.comprehension_phrase", "le chat", "mange", "la pomme")[0]
    answers = {cold.procedural.solve(task, 0, cold.rng)["answer"] for _ in range(30)}
    assert "la pomme" in answers                   # answers the object to "who?"
    assert task.answer == "le chat"
