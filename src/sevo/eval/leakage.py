"""Methodological safety — item-leakage detection.

The whole credibility of Intelligence_delta rests on *never evaluating on items
the brain was taught*. This module makes that a checked invariant rather than a
convention: it compares evaluation items to a node's teaching bank by
``memo_key`` (node + exact content), and reports any contamination.

Used two ways:
* ``audit_node`` — assert a node's held-out / transfer banks are disjoint from
  its teaching bank (a self-check the runtime exposes at ``/audit``);
* ``detect_leakage`` — guard custom ``/evaluate`` items: refuse to grade on any
  item that appears in teaching.
"""
from __future__ import annotations


class ItemLeakageError(ValueError):
    pass


def _keys(items) -> set:
    return {t.memo_key for t in items}


def detect_leakage(eval_items, teaching_items) -> dict:
    """Return a contamination report for ``eval_items`` against ``teaching_items``."""
    teach = _keys(teaching_items)
    contaminated = [t for t in eval_items if t.memo_key in teach]
    return {
        "clean": not contaminated,
        "n_eval": len(eval_items),
        "n_contaminated": len(contaminated),
        "contaminated_items": [str(getattr(t, "prompt", t.memo_key)) for t in contaminated[:20]],
    }


def audit_node(node_id: str, seed: int = 0) -> dict:
    """Verify a node's held-out and transfer banks contain no teaching item."""
    from ..curriculum.factory import heldout_bank, teaching_bank

    teaching = teaching_bank(node_id, seed)
    report = {"node_id": node_id, "heldout": detect_leakage(heldout_bank(node_id, seed), teaching)}
    transfer = _transfer_for(node_id)
    if transfer is not None:
        report["transfer"] = detect_leakage(transfer, teaching)
    report["clean"] = all(v["clean"] for k, v in report.items()
                          if isinstance(v, dict) and "clean" in v)
    return report


def _transfer_for(node_id: str):
    """Best-effort transfer bank for the node, or None."""
    from ..curriculum import cp_maths_numeration as _num
    from ..curriculum import fr_conjugation as _conj
    from ..curriculum import fr_cp_ce1 as _plur
    from ..curriculum import fr_lecture_cp as _lec

    if node_id in _num.NODES_NUM:
        return _num.transfer_bank_num(node_id)
    if node_id == "fr.CP.lecture_mots_reguliers":
        return _lec.transfer_bank_lecture(node_id)
    if node_id == "fr.CP.segmentation_syllabes":
        return _lec.transfer_bank_syllabes(node_id)
    if node_id == "fr.CP.dictee_simple":
        return _lec.transfer_bank_dictee(node_id)
    if node_id == "fr.CP.comprehension_phrase":
        return _lec.transfer_bank_comprehension(node_id)
    if node_id in _conj.NODES_CONJ:
        return _conj.transfer_bank_conj(node_id)
    if node_id in _plur.NODES_FR:
        return [t for t in _plur.transfer_bank_fr() if t.category == _plur.NODES_FR[node_id]["category"]]
    return None
