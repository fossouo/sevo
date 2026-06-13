"""Integrity gate — protection against the *illusion of progression*.

A rising Intelligence_delta is **not** sufficient to declare a brain "more
capable": a clever-looking number can hide memorisation, noise, or a model that
only repeats taught items. So no run may claim genuine learning unless ALL of
the following hold simultaneously (founder's invariant):

1. **post-test gain** — accuracy after teaching exceeds the cold baseline;
2. **held-out gain** — that gain is *substantial* on the disjoint held-out bank,
   not measurement noise;
3. **transfer is non-zero in at least one domain** — the brain applies a rule to
   items it was never taught;
4. **the memoriser is inferior** — a pure memoriser, given the same teaching
   items, scores clearly *below* the brain on held-out AND transfer (so the gain
   is structural, not recall);
5. **delayed retention is measurable** — the knowledge survives a 7-day delay
   above a floor (it consolidated, it wasn't a transient).

``assess_genuine_learning`` returns a structured verdict. ``GENUINE`` is only
returned when every check passes; otherwise ``NOT_PROVEN`` with the failing
reasons. Reports must show this verdict next to any Intelligence_delta.
"""
from __future__ import annotations

from dataclasses import asdict, dataclass

# Thresholds — deliberately conservative; tuned so noise cannot pass.
MIN_HELDOUT_GAIN = 0.20        # held-out post − pre must clear this
MIN_TRANSFER = 0.15            # at least one domain must transfer above chance
MEMORISER_MARGIN = 0.20        # brain must beat the memoriser by this much
MIN_RETENTION_RATIO = 0.40     # t2 / t1 floor (knowledge survived the delay)


@dataclass
class GenuineLearningVerdict:
    verdict: str                # "GENUINE" | "NOT_PROVEN"
    passed: bool
    checks: dict                # check_name -> bool
    reasons: list               # human-readable failures (empty if passed)
    details: dict


def assess_genuine_learning(
    *,
    heldout_before: float,
    heldout_after: float,
    transfer_before: float,
    transfer_after: float,      # the BEST domain's transfer (≥1 domain must pass)
    memoriser_heldout: float,
    memoriser_transfer: float,
    t1_after: float,
    t2_after: float,
) -> dict:
    checks, reasons = {}, []

    c1 = heldout_after > heldout_before
    checks["post_test_gain"] = c1
    if not c1:
        reasons.append("no post-test gain over the cold baseline")

    c2 = (heldout_after - heldout_before) >= MIN_HELDOUT_GAIN
    checks["held_out_gain_substantial"] = c2
    if not c2:
        reasons.append(f"held-out gain {heldout_after - heldout_before:.2f} "
                       f"below {MIN_HELDOUT_GAIN} (could be noise)")

    c3 = transfer_after >= MIN_TRANSFER and transfer_after > transfer_before
    checks["transfer_nonzero"] = c3
    if not c3:
        reasons.append(f"no domain transfers (best {transfer_after:.2f} < {MIN_TRANSFER})")

    c4 = ((heldout_after - memoriser_heldout) >= MEMORISER_MARGIN
          and (transfer_after - memoriser_transfer) >= MEMORISER_MARGIN)
    checks["beats_memoriser"] = c4
    if not c4:
        reasons.append("does not beat the memoriser by the required margin on "
                       "held-out AND transfer (gain may be recall, not structure)")

    ratio = (t2_after / t1_after) if t1_after else 0.0
    c5 = t1_after > 0 and ratio >= MIN_RETENTION_RATIO and t2_after > heldout_before
    checks["retention_measurable"] = c5
    if not c5:
        reasons.append(f"delayed retention ratio {ratio:.2f} below "
                       f"{MIN_RETENTION_RATIO} (knowledge did not survive the delay)")

    passed = all(checks.values())
    return asdict(GenuineLearningVerdict(
        verdict="GENUINE" if passed else "NOT_PROVEN",
        passed=passed,
        checks=checks,
        reasons=reasons,
        details={
            "heldout_before": round(heldout_before, 4),
            "heldout_after": round(heldout_after, 4),
            "best_transfer_after": round(transfer_after, 4),
            "memoriser_heldout": round(memoriser_heldout, 4),
            "memoriser_transfer": round(memoriser_transfer, 4),
            "retention_ratio_t2_over_t1": round(ratio, 4),
        },
    ))
