"""Integrity gate — the protection against the illusion of progression.

A brain may be declared "more capable" ONLY when all five guards pass. These
tests prove the gate accepts genuine learning AND, crucially, *rejects* the
classic illusions (no transfer, memoriser parity, no retention, noise-level
gain). A gate that never says NO would be worthless.
"""
from sevo.eval import assess_genuine_learning

GENUINE = dict(
    heldout_before=0.0, heldout_after=0.95,
    transfer_before=0.0, transfer_after=0.80,
    memoriser_heldout=0.0, memoriser_transfer=0.0,
    t1_after=0.95, t2_after=0.62,
)


def test_accepts_genuine_learning():
    g = assess_genuine_learning(**GENUINE)
    assert g["passed"] and g["verdict"] == "GENUINE"
    assert all(g["checks"].values())
    assert g["reasons"] == []


def test_rejects_when_no_transfer():
    """High held-out but zero transfer in every domain → not proven."""
    g = assess_genuine_learning(**{**GENUINE, "transfer_after": 0.0})
    assert not g["passed"] and g["verdict"] == "NOT_PROVEN"
    assert g["checks"]["transfer_nonzero"] is False


def test_rejects_when_memoriser_matches():
    """If a pure memoriser scores like the brain, the gain is recall, not
    structure — the gate must refuse."""
    g = assess_genuine_learning(**{**GENUINE, "memoriser_heldout": 0.95,
                                   "memoriser_transfer": 0.80})
    assert not g["passed"]
    assert g["checks"]["beats_memoriser"] is False


def test_rejects_when_no_retention():
    """Knowledge that collapses after the delay is not real learning."""
    g = assess_genuine_learning(**{**GENUINE, "t2_after": 0.10})
    assert not g["passed"]
    assert g["checks"]["retention_measurable"] is False


def test_rejects_noise_level_gain():
    """A tiny held-out gain is indistinguishable from noise."""
    g = assess_genuine_learning(**{**GENUINE, "heldout_before": 0.90,
                                   "heldout_after": 0.95, "t1_after": 0.95})
    assert not g["passed"]
    assert g["checks"]["held_out_gain_substantial"] is False
