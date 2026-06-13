"""assessment_oracle — instrument externe (n'enseigne jamais).

Measures the brain without teaching it. It runs a battery in *read-only* mode:
the brain attempts each item but no episode is encoded, no skill is reinforced,
no mastery is updated. This enforces the cardinal rule of
``api_surface.json``/``evaluation_protocol.json``: the evaluation API must never
write into learning memory, otherwise the test would itself be teaching.

Reported metrics:

* ``accuracy`` — fraction correct on a held-out / transfer bank.
* ``calibration_error`` — mean |confidence − correctness|; lower is better.
* ``knows_unknowns`` — on the items it got wrong, how unconfident it correctly
  was (1.0 = perfectly knew it didn't know).
"""
from __future__ import annotations


class AssessmentOracle:
    def assess(self, brain, problems: list, label: str = "") -> dict:
        if not problems:
            return {"label": label, "n": 0, "accuracy": 0.0, "mean_confidence": 0.0,
                    "calibration_error": 0.0, "knows_unknowns": 1.0}
        n = len(problems)
        correct = 0
        conf_sum = 0.0
        calib_sum = 0.0
        wrong_conf: list[float] = []
        for p in problems:
            res = brain.attempt(p, learn=False)  # read-only path
            is_correct = 1.0 if res["correct"] else 0.0
            conf = res["confidence"]
            correct += int(res["correct"])
            conf_sum += conf
            calib_sum += abs(conf - is_correct)
            if not res["correct"]:
                wrong_conf.append(conf)
        knows_unknowns = 1.0 - (sum(wrong_conf) / len(wrong_conf)) if wrong_conf else 1.0
        return {
            "label": label,
            "n": n,
            "accuracy": round(correct / n, 4),
            "mean_confidence": round(conf_sum / n, 4),
            "calibration_error": round(calib_sum / n, 4),
            "knows_unknowns": round(knows_unknowns, 4),
        }
