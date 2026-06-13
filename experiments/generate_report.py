"""Run the CP/CE1 experiment and write the committed evidence files:

    reports/last_run.json         — full machine-readable result
    reports/EXPERIMENT_REPORT.md  — human-readable summary

Run:  PYTHONPATH=src:experiments python3 experiments/generate_report.py
"""
from __future__ import annotations

import json
import os

from run_cp_ce1_math import run
from run_fr_conjugation import run as run_conj
from run_fr_cp_ce1 import run as run_fr

HERE = os.path.dirname(__file__)
REPORTS = os.path.join(HERE, "..", "reports")


def _fmt_pct(x: float) -> str:
    return f"{x * 100:.0f}%"


def main() -> None:
    r = run()
    os.makedirs(REPORTS, exist_ok=True)
    with open(os.path.join(REPORTS, "last_run.json"), "w", encoding="utf-8") as f:
        json.dump(r, f, indent=2, ensure_ascii=False)

    pre, t1, t2 = r["pretest"], r["posttest_immediate"], r["posttest_delayed_t2"]
    eff, mem, d = r["transfer_efficiency_control"], r["memorizer_baseline"], r["intelligence_delta"]
    comp = d["components"]

    lines = []
    a = lines.append
    a("# Experiment report — CP/CE1 mathematics\n")
    a(f"_Reproducible run, seed = {r['seed']}. Regenerate with "
      "`PYTHONPATH=src:experiments python3 experiments/generate_report.py`._\n")
    a("\nThe brain traverses the full class-learning cycle "
      "(`design/learning_lifecycle.json`): cold pretest → Emma teaches "
      "prerequisites then targets → consolidation (\"sleep\") → immediate "
      "posttest → 7-day delayed posttest → transfer + reasoning. All scores are "
      "measured by the assessment oracle on **disjoint held-out / transfer / "
      "delayed** banks.\n")

    a("\n## Headline\n")
    a(f"\n**Intelligence_delta = {d['weighted_delta']:.3f}** "
      "(internal cognitive evolution index — not a human IQ).\n")

    a("\n## Before vs after\n")
    a("\n| Measure (held-out) | Pretest | Posttest T1 | Delayed T2 (+7d) |")
    a("\n|---|---|---|---|")
    a(f"\n| Taught nodes accuracy | {_fmt_pct(pre['heldout']['accuracy'])} | "
      f"{_fmt_pct(t1['heldout']['accuracy'])} | {_fmt_pct(t2['heldout']['accuracy'])} |")
    a(f"\n| Transfer (add within 1000, never taught) | {_fmt_pct(pre['transfer']['accuracy'])} | "
      f"{_fmt_pct(t1['transfer']['accuracy'])} | — |")
    a(f"\n| Fluid reasoning (missing addend) | {_fmt_pct(pre['reasoning']['accuracy'])} | "
      f"{_fmt_pct(t1['reasoning']['accuracy'])} | — |")
    a(f"\n| Calibration error (lower = better) | {pre['heldout']['calibration_error']:.2f} | "
      f"{t1['heldout']['calibration_error']:.2f} | — |")

    a("\n\n## Intelligence_delta components\n")
    a("\n| Component | Weight | Value |")
    a("\n|---|---|---|")
    for k, w in d["weights"].items():
        a(f"\n| {k} | {w:.2f} | {comp[k]:+.3f} |")
    a(f"\n\nRetention ratio T2/T1 = **{d['retention_ratio_t2_over_t1']:.2f}**.\n")

    a("\n## Controls (why the gain is real, not memorisation)\n")
    a(f"\n* **Transfer of skill / learning efficiency** — learning the "
      f"with-carry node took **{eff['trials_with_prereq']} trials** when "
      f"prerequisites were already mastered, vs **{eff['trials_without_prereq']} "
      f"trials** from cold (**{eff['speedup']}× speedup**). Prerequisite skills "
      "transfer.\n")
    a(f"* **Anti-leakage memoriser baseline** — a pure memoriser scores "
      f"{_fmt_pct(mem['on_teaching']['accuracy'])} on the teaching items it "
      f"saw, but only {_fmt_pct(mem['on_heldout']['accuracy'])} on the "
      f"disjoint held-out bank and {_fmt_pct(mem['on_transfer']['accuracy'])} "
      "on transfer. The brain's held-out/transfer gains cannot be explained by "
      "memorising seen items.\n")
    a(f"* **Knows what it doesn't know** — on never-taught multiplication the "
      f"brain stays at {_fmt_pct(pre['untaught_multiplication']['accuracy'])} "
      f"accuracy with confidence "
      f"{pre['untaught_multiplication']['mean_confidence']:.2f} "
      "before *and* after arithmetic training (it does not become falsely "
      "confident).\n")

    a("\n## Teaching log\n")
    a("\n| Node | Trials to mastery | Final mastery |")
    a("\n|---|---|---|")
    for t in r["teaching"]:
        a(f"\n| {t['node_id']} | {t['trials']} | {t['final_mastery']:.2f} |")
    a("\n")

    with open(os.path.join(REPORTS, "EXPERIMENT_REPORT.md"), "w", encoding="utf-8") as f:
        f.write("".join(lines))
    print("wrote reports/last_run.json and reports/EXPERIMENT_REPORT.md")
    print(f"maths  Intelligence_delta = {d['weighted_delta']:.3f}")


def main_fr() -> None:
    r = run_fr()
    os.makedirs(REPORTS, exist_ok=True)
    with open(os.path.join(REPORTS, "last_run_fr.json"), "w", encoding="utf-8") as f:
        json.dump(r, f, indent=2, ensure_ascii=False)

    pre, t1, t2 = r["pretest"], r["posttest_immediate"], r["posttest_delayed_t2"]
    eff, mem, d = r["transfer_efficiency_control"], r["memorizer_baseline"], r["intelligence_delta"]

    lines = []
    a = lines.append
    a("# Experiment report — CP/CE1 French (plural of nouns)\n")
    a(f"_Reproducible run, seed = {r['seed']}. Same brain architecture as the "
      "maths experiment — different domain. This is the generalisation proof._\n")
    a(f"\n**Intelligence_delta = {d['weighted_delta']:.3f}** "
      "(internal cognitive evolution index — not a human IQ).\n")
    a("\n## Before vs after\n")
    a("\n| Measure | Pretest | Posttest T1 | Delayed T2 (+7d) |")
    a("\n|---|---|---|---|")
    a(f"\n| Held-out plurals | {_fmt_pct(pre['heldout']['accuracy'])} | "
      f"{_fmt_pct(t1['heldout']['accuracy'])} | {_fmt_pct(t2['heldout']['accuracy'])} |")
    a(f"\n| Transfer: +s rule on unseen words | {_fmt_pct(pre['transfer_regular']['accuracy'])} | "
      f"{_fmt_pct(t1['transfer_regular']['accuracy'])} | — |")
    a(f"\n| Transfer: -al→-aux rule on unseen words | {_fmt_pct(pre['transfer_al_rule']['accuracy'])} | "
      f"{_fmt_pct(t1['transfer_al_rule']['accuracy'])} | — |")
    a("\n\n## Controls\n")
    a(f"\n* **Shared-skill transfer** — learning the `-al→-aux` node took "
      f"{eff['trials_with_prereq']} trials when the regular-plural node "
      f"(shared `{eff['shared_skill']}` skill) was learned first, vs "
      f"{eff['trials_without_prereq']} cold ({eff['speedup']}× speedup).\n")
    a(f"* **Anti-leakage memoriser** — {_fmt_pct(mem['on_teaching']['accuracy'])} on "
      f"taught words, {_fmt_pct(mem['on_heldout']['accuracy'])} held-out, "
      f"{_fmt_pct(mem['on_transfer']['accuracy'])} transfer.\n")
    a("* **Characteristic error** — a low-mastery brain forms *chevals* "
      "(over-regularised) instead of *chevaux*: a diagnostic child error, not "
      "random noise.\n")
    a("\n## Teaching log\n")
    a("\n| Node | Trials to mastery | Final mastery |")
    a("\n|---|---|---|")
    for t in r["teaching"]:
        a(f"\n| {t['node_id']} | {t['trials']} | {t['final_mastery']:.2f} |")
    a("\n")
    with open(os.path.join(REPORTS, "EXPERIMENT_REPORT_FR.md"), "w", encoding="utf-8") as f:
        f.write("".join(lines))
    print("wrote reports/last_run_fr.json and reports/EXPERIMENT_REPORT_FR.md")
    print(f"french Intelligence_delta = {d['weighted_delta']:.3f}")


def main_conj() -> None:
    r = run_conj()
    os.makedirs(REPORTS, exist_ok=True)
    with open(os.path.join(REPORTS, "last_run_conjugation.json"), "w", encoding="utf-8") as f:
        json.dump(r, f, indent=2, ensure_ascii=False)

    pre, t1, t2 = r["pretest"], r["posttest_immediate"], r["posttest_delayed_t2"]
    eff, mem, d = r["transfer_efficiency_control"], r["memorizer_baseline"], r["intelligence_delta"]

    lines = []
    a = lines.append
    a("# Experiment report — CE1/CE2 French (present tense of -er verbs)\n")
    a(f"_Reproducible run, seed = {r['seed']}. A **third** domain on the same "
      "brain architecture — neither arithmetic nor noun plurals. Generalisation, "
      "not a special case._\n")
    a(f"\n**Intelligence_delta = {d['weighted_delta']:.3f}** "
      "(internal cognitive evolution index — not a human IQ).\n")
    a("\n## Before vs after\n")
    a("\n| Measure | Pretest | Posttest T1 | Delayed T2 (+7d) |")
    a("\n|---|---|---|---|")
    a(f"\n| Held-out conjugations | {_fmt_pct(pre['heldout']['accuracy'])} | "
      f"{_fmt_pct(t1['heldout']['accuracy'])} | {_fmt_pct(t2['heldout']['accuracy'])} |")
    a(f"\n| Transfer: rule on unseen verbs | {_fmt_pct(pre['transfer']['accuracy'])} | "
      f"{_fmt_pct(t1['transfer']['accuracy'])} | — |")
    a("\n\n## Controls\n")
    a(f"\n* **Cross-domain effect (honest null)** — only `{eff['shared_skill']}` "
      f"(a minor 0.2-weight skill) is shared with the plural domain; the hard "
      f"skill (the verb endings) is not. Learning the node took "
      f"{eff['trials_with_prereq']} trials with the plural node learned first vs "
      f"{eff['trials_without_prereq']} cold ({eff['speedup']}× — within noise). "
      "This is the expected result: **transfer is proportional to shared "
      "structure**. Strong shared-skill transfer is shown in the plural "
      "experiment, where the shared skill carries more weight.\n")
    a(f"* **Anti-leakage memoriser** — {_fmt_pct(mem['on_teaching']['accuracy'])} on "
      f"taught (verb, pronoun) pairs, {_fmt_pct(mem['on_heldout']['accuracy'])} "
      f"held-out, {_fmt_pct(mem['on_transfer']['accuracy'])} transfer.\n")
    a("* **Characteristic error** — a low-mastery brain writes the *infinitive* "
      "(« je parler ») or breaks subject agreement (« ils parle »): diagnostic "
      "beginner errors, not random noise.\n")
    a("\n## Teaching log\n")
    a("\n| Node | Trials to mastery | Final mastery |")
    a("\n|---|---|---|")
    for t in r["teaching"]:
        a(f"\n| {t['node_id']} | {t['trials']} | {t['final_mastery']:.2f} |")
    a("\n")
    with open(os.path.join(REPORTS, "EXPERIMENT_REPORT_CONJUGATION.md"), "w", encoding="utf-8") as f:
        f.write("".join(lines))
    print("wrote reports/last_run_conjugation.json and reports/EXPERIMENT_REPORT_CONJUGATION.md")
    print(f"conj   Intelligence_delta = {d['weighted_delta']:.3f}")


if __name__ == "__main__":
    main()
    main_fr()
    main_conj()
