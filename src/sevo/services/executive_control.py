"""executive_control — cortex préfrontal / ACC / ganglions de la base.

Arbitrates strategy. For the MVP its job is: decide whether the brain has a
usable procedure to *attempt* the problem at all, or whether it should honestly
say "I don't know" (ask for help) instead of guessing confidently.

The attempt decision is driven by *capability presence*, not by recent success —
otherwise a string of early errors would suppress all future attempts (learned
helplessness) and the brain could never demonstrate skills it actually went on
to acquire. Confidence is tracked separately, for calibration.
"""
from __future__ import annotations


class ExecutiveControl:
    def decide(self, has_method: bool, confidence: float) -> str:
        return "attempt" if has_method else "ask_help"
