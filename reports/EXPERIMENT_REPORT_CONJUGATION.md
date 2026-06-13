# Experiment report — CE1/CE2 French (present tense of -er verbs)
_Reproducible run, seed = 5. A **third** domain on the same brain architecture — neither arithmetic nor noun plurals. Generalisation, not a special case._

**Intelligence_delta = 0.706** (internal cognitive evolution index — not a human IQ).

## Before vs after

| Measure | Pretest | Posttest T1 | Delayed T2 (+7d) |
|---|---|---|---|
| Held-out conjugations | 0% | 86% | 68% |
| Transfer: rule on unseen verbs | 0% | 88% | — |

## Controls

* **Cross-domain effect (honest null)** — only `grapheme_recognition` (a minor 0.2-weight skill) is shared with the plural domain; the hard skill (the verb endings) is not. Learning the node took 42.0 trials with the plural node learned first vs 38.67 cold (0.921× — within noise). This is the expected result: **transfer is proportional to shared structure**. Strong shared-skill transfer is shown in the plural experiment, where the shared skill carries more weight.
* **Anti-leakage memoriser** — 100% on taught (verb, pronoun) pairs, 0% held-out, 0% transfer.
* **Characteristic error** — a low-mastery brain writes the *infinitive* (« je parler ») or breaks subject agreement (« ils parle »): diagnostic beginner errors, not random noise.

## Teaching log

| Node | Trials to mastery | Final mastery |
|---|---|---|
| fr.CE1.present_verbes_er | 48 | 0.85 |
