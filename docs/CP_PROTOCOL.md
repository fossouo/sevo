# CP protocol — frozen contract (v1)

This document **freezes** the CP-grade protocol after PRs #1–#5. Everything below
is now stable: changing it is a breaking change and must bump the relevant
schema version and update `tests/test_cp_protocol_freeze.py`.

Reproduce the whole thing in one command:

```bash
make demo-cp        # Brain CP-naïf → Emma → Brain CP-appris → GENUINE → save/reload
```

Artifacts land in `demo/artifacts/` (`brain_before.json`, `brain_after.json`,
`brain_diff.json`, `assessment_report.json`, `emma_session_journal.json`,
`audit_report.json`).

---

## 1. Definition of GENUINE

A brain is declared **more capable** (`verdict: "GENUINE"`) **only** when *all
five* anti-illusion guards pass (`eval/integrity.py`). Otherwise the verdict is
`NOT_PROVEN` and no capability is claimed.

| Guard | Condition |
|---|---|
| `post_test_gain` | held-out accuracy after > before |
| `held_out_gain_substantial` | (after − before) ≥ **0.20** |
| `transfer_nonzero` | best-domain transfer ≥ **0.15** and > before |
| `beats_memoriser` | brain − memoriser ≥ **0.20** on held-out **and** transfer |
| `retention_measurable` | t2/t1 ≥ **0.40** and t2 > cold baseline |

The score `Intelligence_delta` is an **internal cognitive-evolution index, not a
human IQ** and not a claim of general intelligence — only "more capable on the
measured CP curriculum (genuine learning under the CP protocol)".

## 2. Teacher / oracle separation (cardinal rule)

- **Teaching channel**: `perceive` · `act` · `feedback` · `consolidate` ·
  `replay` · `teach/session`. Emma lives here.
- **Assessment channel**: `evaluate` (the oracle on disjoint held-out banks) and
  `diff`. **The oracle never routes through a teacher** — guaranteed by test
  (`test_assessment_never_invokes_the_teacher`): a recording teacher sees zero
  items during evaluation.
- `evaluate` is **read-only**: the brain's exported state is byte-identical after
  any number of evaluations.

## 3. Anti-leakage

- Teaching and held-out/transfer banks are **disjoint by construction**
  (`memo_key` = node + exact content). `/audit` proves it per node, categorised:
  teaching / held-out / transfer (`intra-grade` vs `out-of-grade`) / retention
  (reuses held-out).
- `/evaluate` with custom items **refuses** (HTTP 422 / `ItemLeakageError`) any
  item present in the teaching bank. Evaluating on seen items is impossible by
  guard, not just by convention.

## 4. Emma feedback format (`StructuredFeedback`)

Frozen 8-field contract — the **only** shape feedback enters the brain in:

```
node_id · task_id · observed_answer · correct_answer · hint · error_type · confidence · teach_signal
```

- `teach_signal` and `correct_answer` come from the **curriculum** (`task.grade`),
  never from the model — Emma cannot decide right/wrong or contaminate.
- The brain learns **only** from `teach_signal`; the natural-language `hint` is
  logged, **never written into memory** (no free text in memory).

## 5. State format

- **Cognitive state** (`brain.export_state`, `schema_version` = **"0.4"**):
  `schema_version, brain_id, day, stage, procedural_skills, semantic_mastery,
  metacognition`. `from_state` rejects a missing/unsupported version.
- **Runtime envelope** (`persistence.py`, `runtime_schema_version` = **"0.5"**):
  `runtime_schema_version, brain, counters, sessions, baseline_snapshot, seed`.
  `migrate_envelope` upgrades older versions explicitly (0.4 → 0.5) or rejects
  them. A save→reload preserves the learned state **bit-for-bit** and the
  original Brain-naïf baseline (so `diff` stays meaningful).

## 6. Session format

A session (`session_id`) records ordered interactions
(`perceive` / `feedback` / `consolidate`) and is stored in the envelope.
**Replay is deterministic**: re-applying the feedback log onto a brain rebuilt
from the session start-state reproduces the end-state exactly (feedback-learning
has no RNG; the seed is persisted for the stochastic act/eval path).

---

## Non-regression criteria (frozen)

`tests/test_cp_protocol_freeze.py` asserts the CP-appris brain stays:

1. **GENUINE** — the five guards pass on the full CP cycle;
2. **save/reload exact** — learned state identical after a round-trip;
3. **audit clean** — every CP node's held-out/transfer banks are leakage-free;
4. **replay deterministic** — a session replays to an identical state;
5. **no item leakage** — `/evaluate` refuses any taught item.

Any change that breaks one of these fails CI and must be treated as a protocol
break (bump schema + update this document).
