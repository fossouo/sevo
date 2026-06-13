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


# Maths nodes whose transfer probe is deliberately *out-of-grade* (addition
# within 1000). Everything else transfers within grade (unseen words / numbers).
_OUT_OF_GRADE_TRANSFER = {
    "math.CP.add_within_20", "math.CP.sub_within_20",
    "math.CE1.add_within_100_nocarry", "math.CE1.add_within_100_carry",
    "math.CE1.sub_within_100_borrow",
}


def transfer_kind(node_id: str) -> str:
    return "out-of-grade" if node_id in _OUT_OF_GRADE_TRANSFER else "intra-grade"


def audit_node(node_id: str, seed: int = 0) -> dict:
    """Audit a node's evaluation banks against its teaching bank, category by
    category, so a contamination can be diagnosed (which probe leaked, and from
    where). Distinguishes teaching / held-out / transfer (intra- vs out-of-grade)
    / retention (which, by protocol, reuses the held-out bank at t2)."""
    from ..curriculum.factory import heldout_bank, teaching_bank

    teaching = teaching_bank(node_id, seed)
    heldout = heldout_bank(node_id, seed)
    report = {
        "node_id": node_id,
        "teaching": {"n": len(teaching), "role": "reference (seen in training)"},
        "heldout": {**detect_leakage(heldout, teaching), "vs": "teaching"},
        "retention": {"reuses": "heldout",
                      "note": "retention (t2) is measured on the held-out bank "
                              "after a delay — same items, so its leakage status "
                              "is the held-out one above"},
    }
    transfer = _transfer_for(node_id)
    if transfer is not None:
        report["transfer"] = {**detect_leakage(transfer, teaching),
                              "kind": transfer_kind(node_id), "vs": "teaching"}
    report["clean"] = all(v["clean"] for v in report.values()
                          if isinstance(v, dict) and "clean" in v)
    return report


def _transfer_for(node_id: str):
    """Best-effort transfer bank for the node, or None."""
    from ..curriculum import cp_ce1_math as _math
    from ..curriculum import cp_maths_numeration as _num
    from ..curriculum import fr_conjugation as _conj
    from ..curriculum import fr_cp_ce1 as _plur
    from ..curriculum import fr_lecture_cp as _lec
    from ..rng import Rng

    if (node_id in _math.NODES and node_id != "math.CE2.multiply_table"
            and not _math.NODES[node_id].get("generated")):
        return _math.transfer_bank(Rng(99), n=20)        # addition within 1000 (out-of-grade)
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
