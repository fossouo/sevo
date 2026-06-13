# Experiment report — CP/CE1 mathematics
_Reproducible run, seed = 7. Regenerate with `PYTHONPATH=src:experiments python3 experiments/generate_report.py`._

The brain traverses the full class-learning cycle (`design/learning_lifecycle.json`): cold pretest → Emma teaches prerequisites then targets → consolidation ("sleep") → immediate posttest → 7-day delayed posttest → transfer + reasoning. All scores are measured by the assessment oracle on **disjoint held-out / transfer / delayed** banks.

## Headline

**Intelligence_delta = 0.748** (internal cognitive evolution index — not a human IQ).

## Before vs after

| Measure (held-out) | Pretest | Posttest T1 | Delayed T2 (+7d) |
|---|---|---|---|
| Taught nodes accuracy | 0% | 94% | 60% |
| Transfer (add within 1000, never taught) | 0% | 90% | — |
| Fluid reasoning (missing addend) | 0% | 81% | — |
| Calibration error (lower = better) | 0.10 | 0.11 | — |

## Intelligence_delta components

| Component | Weight | Value |
|---|---|---|
| knowledge_gain | 0.30 | +0.938 |
| transfer_gain | 0.25 | +0.900 |
| reasoning_gain | 0.20 | +0.812 |
| retention_gain | 0.10 | +0.604 |
| metacognition_gain | 0.10 | -0.008 |
| learning_efficiency_gain | 0.05 | +0.396 |

Retention ratio T2/T1 = **0.64**.

## Controls (why the gain is real, not memorisation)

* **Transfer of skill / learning efficiency** — learning the with-carry node took **21.33 trials** when prerequisites were already mastered, vs **35.33 trials** from cold (**1.656× speedup**). Prerequisite skills transfer.
* **Anti-leakage memoriser baseline** — a pure memoriser scores 100% on the teaching items it saw, but only 0% on the disjoint held-out bank and 0% on transfer. The brain's held-out/transfer gains cannot be explained by memorising seen items.
* **Knows what it doesn't know** — on never-taught multiplication the brain stays at 0% accuracy with confidence 0.10 before *and* after arithmetic training (it does not become falsely confident).

## Teaching log

| Node | Trials to mastery | Final mastery |
|---|---|---|
| math.CP.add_within_20 | 16 | 0.97 |
| math.CP.sub_within_20 | 16 | 0.92 |
| math.CE1.add_within_100_nocarry | 16 | 0.86 |
| math.CE1.add_within_100_carry | 32 | 0.89 |
| math.CE1.sub_within_100_borrow | 32 | 0.97 |
