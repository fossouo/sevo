"""Task factory — build a gradable ``Task`` from ``(node_id, content)``.

The runtime API receives JSON, not Python objects: a client posts a node id and
some content (a word, a number, an (a,b) pair, a sentence). This factory turns
that into the same ``Task`` the curriculum modules build internally, so the
ground truth and the characteristic-error model are identical to the experiments.

Only the CP nodes (plus the base maths/French nodes they build on) are wired —
the runtime is CP-focused. Unknown nodes raise, so the API can answer 400 rather
than guess.
"""
from __future__ import annotations

from . import cm1_maths as _cm1
from . import cp_ce1_math as _math
from . import cp_maths_numeration as _num
from . import fr_conjugation as _conj
from . import fr_cp_ce1 as _plur
from . import fr_lecture_cp as _lec


class TaskFactoryError(ValueError):
    pass


def build_task(node_id: str, content):
    """``content`` shape depends on the node:
      * reading / syllables / dictée / plural : a word (str)
      * conjugation : {"verb","pronoun"}
      * comprehension : {"subject","verb","obj","qtype"}
      * decomposition : a number (int)
      * comparison : {"a","b"}
      * addition / subtraction : {"a","b"}
    """
    try:
        if node_id == "fr.CP.lecture_mots_reguliers":
            return _lec._reading_task(node_id, str(content), "reg")
        if node_id == "fr.CP.lecture_mots_irreguliers":
            return _lec._reading_task(node_id, str(content), "irr")
        if node_id == "fr.CP.segmentation_syllabes":
            return _lec._syllable_task(node_id, str(content))
        if node_id == "fr.CP.dictee_simple":
            return _lec._encoding_task(node_id, str(content))
        if node_id == "fr.CP.comprehension_phrase":
            c = content
            tasks = _lec._sentence_tasks(node_id, c["subject"], c["verb"], c["obj"])
            return tasks[0] if c.get("qtype", "qui") == "qui" else tasks[1]
        if node_id == "math.CP.numeration_dizaines_unites":
            return _num._decomp(node_id, int(content))
        if node_id == "math.CP.comparaison_nombres":
            return _num._comp(node_id, int(content["a"]), int(content["b"]))
        if node_id in _cm1.NODES_CM1:
            return _cm1._make_mul(node_id, int(content["a"]), int(content["b"]))
        if node_id in _math.NODES and _math.NODES[node_id]["op"] == "add":
            return _math._make_add(node_id, int(content["a"]), int(content["b"]))
        if node_id in _math.NODES and _math.NODES[node_id]["op"] == "sub":
            return _math._make_sub(node_id, int(content["a"]), int(content["b"]))
        if node_id in _plur.NODES_FR:
            return _plur._make(node_id, str(content))
        if node_id in _conj.NODES_CONJ:
            return _conj._make_conj(node_id, content["verb"], content["pronoun"])
    except (KeyError, TypeError, ValueError) as e:
        raise TaskFactoryError(f"bad content for {node_id!r}: {e}") from e
    raise TaskFactoryError(f"unknown node_id: {node_id!r}")


def heldout_bank(node_id: str, seed: int = 0) -> list:
    """Reconstruct a node's held-out bank (for /evaluate and replay)."""
    from ..rng import Rng
    rng = Rng(seed).fork(node_id)
    if node_id in _cm1.NODES_CM1:
        return _cm1.build_bank_cm1(node_id, rng).heldout
    if node_id in _num.NODES_NUM:
        return _num.build_bank_num(node_id, rng).heldout
    if node_id in _lec.NODES_LECTURE:
        return _lec.build_bank_lecture(node_id, rng).heldout
    if node_id in _math.NODES:
        return _math.build_bank(node_id, rng).heldout
    if node_id in _plur.NODES_FR:
        return _plur.build_bank_fr(node_id, rng).heldout
    if node_id in _conj.NODES_CONJ:
        return _conj.build_bank_conj(node_id, rng).heldout
    raise TaskFactoryError(f"unknown node_id: {node_id!r}")


def teaching_bank(node_id: str, seed: int = 0) -> list:
    from ..rng import Rng
    rng = Rng(seed).fork(node_id)
    if node_id in _cm1.NODES_CM1:
        return _cm1.build_bank_cm1(node_id, rng).teaching
    if node_id in _num.NODES_NUM:
        return _num.build_bank_num(node_id, rng).teaching
    if node_id in _lec.NODES_LECTURE:
        return _lec.build_bank_lecture(node_id, rng).teaching
    if node_id in _math.NODES:
        return _math.build_bank(node_id, rng).teaching
    if node_id in _plur.NODES_FR:
        return _plur.build_bank_fr(node_id, rng).teaching
    if node_id in _conj.NODES_CONJ:
        return _conj.build_bank_conj(node_id, rng).teaching
    raise TaskFactoryError(f"unknown node_id: {node_id!r}")
