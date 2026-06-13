# Experiment report — CP/CE1 French (plural of nouns)
_Reproducible run, seed = 5. Same brain architecture as the maths experiment — different domain. This is the generalisation proof._

**Intelligence_delta = 0.693** (internal cognitive evolution index — not a human IQ).

> ✅ **Apprentissage authentique : GENUINE** — le delta n'est déclaré que si les cinq garde-fous passent.

| Garde-fou | OK |
|---|---|
| post_test_gain | ✅ |
| held_out_gain_substantial | ✅ |
| transfer_nonzero | ✅ |
| beats_memoriser | ✅ |
| retention_measurable | ✅ |

## Before vs after

| Measure | Pretest | Posttest T1 | Delayed T2 (+7d) |
|---|---|---|---|
| Held-out plurals | 0% | 85% | 63% |
| Transfer: +s rule on unseen words | 0% | 83% | — |
| Transfer: -al→-aux rule on unseen words | 0% | 83% | — |

## Controls

* **Shared-skill transfer** — learning the `-al→-aux` node took 20.0 trials when the regular-plural node (shared `grapheme_recognition` skill) was learned first, vs 26.0 cold (1.3× speedup).
* **Anti-leakage memoriser** — 100% on taught words, 0% held-out, 0% transfer.
* **Characteristic error** — a low-mastery brain forms *chevals* (over-regularised) instead of *chevaux*: a diagnostic child error, not random noise.

## Teaching log

| Node | Trials to mastery | Final mastery |
|---|---|---|
| fr.CE1.pluriel_reguliers | 8 | 0.82 |
| fr.CE1.pluriel_en_al | 40 | 0.85 |
| fr.CE2.pluriel_invariables | 32 | 0.83 |
