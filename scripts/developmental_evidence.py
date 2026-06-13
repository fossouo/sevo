"""Developmental evidence — freeze the CP→CE1 finding as a scientific result.

PR #8 measured that a CP-appris brain learns CE1 with a *localized* transfer
advantage. This script turns that measurement into evidence: a **skill-level
transfer matrix** (which CP skill feeds which CE1 node, expected vs observed,
verdict) and a written report — so the discovery is a result, not just a test
output.

Headline claims (and what the matrix must keep showing):
  * **localized developmental transfer** — confirmed where skills are shared;
  * **not global intelligence acceleration** — most CE1 nodes get no head start;
  * **transfer proportional to shared structure** — and *gated by the new
    bottleneck skill* (CE1 addition WITHOUT carry transfers fully from CP, but
    addition WITH carry does not, because `carry` is new at CE1).

Artifacts (demo/developmental/): naive_to_ce1.json, cp_to_ce1.json,
transfer_matrix.json, developmental_delta.json + docs/DEVELOPMENTAL_EVIDENCE.md.

    make demo-developmental-evidence
"""
from __future__ import annotations

import importlib.util
import json
import os

from sevo.curriculum.official_curriculum import runnable_for
from sevo.rng import Rng

HERE = os.path.dirname(__file__)
ARTIFACTS = os.path.join(HERE, "..", "demo", "developmental")
DOCS = os.path.join(HERE, "..", "docs")
CP_MASTERED_BAR = 0.6
CONFIRMED, WEAK = 0.30, 0.10

_spec = importlib.util.spec_from_file_location("developmental", os.path.join(HERE, "developmental.py"))
developmental = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(developmental)


def _w(path: str, obj) -> None:
    with open(path, "w", encoding="utf-8") as f:
        json.dump(obj, f, indent=2, ensure_ascii=False)


def _ce1_required_skills() -> dict:
    """node_id -> {skill: weight} for CE1 (read from a sample task)."""
    out = {}
    for nid, rn in runnable_for("CE1").items():
        out[nid] = dict(rn.build(Rng(developmental.SEED).fork(nid)).teaching[0].required_skills)
    return out


def _expected(shared_weight: float) -> str:
    return "strong" if shared_weight >= 0.5 else "medium" if shared_weight >= 0.25 \
        else "weak" if shared_weight > 0 else "absent"


def _verdict(observed: float) -> str:
    return "confirmed" if observed >= CONFIRMED else "weak" if observed >= WEAK else "absent"


def run(out: str = ARTIFACTS, docs: str = DOCS, reports: str | None = None) -> dict:
    out, docs = os.path.abspath(out), os.path.abspath(docs)
    reports = os.path.abspath(reports) if reports else os.path.abspath(os.path.join(HERE, "..", "reports"))
    os.makedirs(out, exist_ok=True)
    os.makedirs(docs, exist_ok=True)

    # 1) re-measure (deterministic) into THIS dir + read CP-appris state ------
    dr = developmental.run(out=out, reports=reports)
    comparison = dr["comparison"]
    with open(os.path.join(out, "brain_after_cp.json"), encoding="utf-8") as f:
        cp_state = json.load(f)
    cp_mastered = sorted(s for s, v in cp_state["procedural_skills"].items()
                         if v.get("automaticity", 0.0) >= CP_MASTERED_BAR)

    # 2) per-node observed transfer (dev pretest − iso pretest) --------------
    per = comparison["per_node"]
    delta = {n: round(per[n]["developmental"]["pretest"] - per[n]["isolated"]["pretest"], 4)
             for n in per}

    # 3) transfer matrix: shared CP skills feeding each CE1 node -------------
    required = _ce1_required_skills()
    by_node, edges = {}, []
    for nid, skills in required.items():
        shared = {s: w for s, w in skills.items() if s in cp_mastered}
        shared_w = round(sum(shared.values()), 4)
        new_skills = sorted(s for s in skills if s not in cp_mastered)
        observed = delta[nid]
        verdict = _verdict(observed)
        by_node[nid] = {
            "shared_cp_skills": sorted(shared), "shared_weight": shared_w,
            "new_skills_at_ce1": new_skills, "expected": _expected(shared_w),
            "observed_transfer": observed, "verdict": verdict,
            "dev_pretest": per[nid]["developmental"]["pretest"],
            "iso_pretest": per[nid]["isolated"]["pretest"],
        }
        for s, w in shared.items():
            edges.append({"cp_skill": s, "ce1_node": nid, "weight_in_node": w,
                          "expected": _expected(shared_w), "observed_node_transfer": observed,
                          "verdict": verdict})

    matrix = {
        "cp_mastered_skills": cp_mastered,
        "thresholds": {"confirmed>=": CONFIRMED, "weak>=": WEAK},
        "edges": edges,
        "by_node": by_node,
        "interpretation": "localized developmental transfer — not global "
                          "intelligence acceleration — transfer proportional to "
                          "shared structure, and gated by the new bottleneck skill.",
    }

    # 4) artifacts -----------------------------------------------------------
    _w(os.path.join(out, "naive_to_ce1.json"), {n: per[n]["isolated"] for n in per})
    _w(os.path.join(out, "cp_to_ce1.json"), {n: per[n]["developmental"] for n in per})
    _w(os.path.join(out, "transfer_matrix.json"), matrix)
    _w(os.path.join(out, "developmental_delta.json"),
       {"per_node_transfer": delta, "aggregate": comparison["aggregate"]})
    _write_evidence(os.path.join(docs, "DEVELOPMENTAL_EVIDENCE.md"), matrix, comparison, delta)

    n_confirmed = sum(1 for v in by_node.values() if v["verdict"] == "confirmed")
    return {"matrix": matrix, "n_confirmed": n_confirmed, "n_nodes": len(by_node),
            "artifacts_dir": out}


def _write_evidence(path, matrix, comparison, delta) -> None:
    bn = matrix["by_node"]
    a = []
    a.append("# Developmental evidence — CP → CE1 (frozen result)\n")
    a.append("\n> **localized developmental transfer** · **not global "
             "intelligence acceleration** · **transfer proportional to shared "
             "structure**\n")
    a.append("\n## Résumé\n")
    a.append("\nUn cerveau **CP-appris** apprend CE1 avec un avantage de transfert "
             "**réel mais localisé**. Le transfert est **confirmé** là où une "
             "compétence du CP est réellement réutilisée par CE1, **faible ou "
             "absent** ailleurs, et — découverte clé — **bloqué par la nouvelle "
             "compétence-goulot** quand CE1 en introduit une.\n")

    a.append("\n## Matrice de transfert (compétence CP → nœud CE1)\n")
    a.append("\n| Nœud CE1 | Compétences CP partagées | Nouvelles à CE1 | Poids partagé | Attendu | Observé (Δ pré-test) | Verdict |")
    a.append("\n|---|---|---|---|---|---|---|")
    for nid, v in bn.items():
        a.append(f"\n| `{nid}` | {', '.join(v['shared_cp_skills']) or '—'} | "
                 f"{', '.join(v['new_skills_at_ce1']) or '—'} | {v['shared_weight']:.2f} | "
                 f"{v['expected']} | {v['observed_transfer']:+.2f} | **{v['verdict']}** |")

    a.append("\n\n## Ce qui transfère, ce qui ne transfère pas, pourquoi\n")
    a.append("\n* **Transfère (confirmé)** — l'addition CE1 *sans retenue* "
             "(`math.CE1.add_within_100_nocarry`) : ses deux compétences "
             "(`place_value`, `add_facts_within_20`) sont **entièrement acquises "
             "au CP** → quasi-maîtrisée dès le pré-test.\n")
    a.append("* **Bloqué par la nouvelle compétence** — l'addition *avec retenue* "
             "et la soustraction *avec emprunt* partagent `place_value`/faits avec "
             "le CP, **mais** `carry` / `borrow` sont **nouveaux au CE1** et font "
             "goulot → transfert faible/absent malgré les prérequis partagés. "
             "C'est le résultat le plus instructif : *le transfert est plafonné "
             "par la compétence manquante*.\n")
    a.append("* **Ne transfère pas (absent)** — pluriel et conjugation ne partagent "
             "que `grapheme_recognition` (poids faible) avec le CP → aucun avantage. "
             "Le français du CE1 est, pour l'essentiel, **nouveau**.\n")

    a.append("\n## Limites\n")
    a.append("\n* Modèle de compétences **simplifié** (pas un vrai système "
             "cognitif humain) ; les forces sont relatives, pas absolues.\n"
             "* Mesure sur un **jeu amorce** CP/CE1 partiel, seed fixe.\n"
             "* Le transfert est mesuré au **pré-test held-out** ; il ne capture "
             "pas d'éventuels effets de vitesse fins par-delà la maîtrise.\n")

    a.append("\n## Critères pour ouvrir CE2\n")
    a.append("\nCE2 ne devra être lancé que si, comme ici :\n"
             "1. le transfert reste **localisé** (pas d'amélioration partout) ;\n"
             "2. le transfert arithmétique partagé reste **positif** ;\n"
             "3. le transfert non partagé n'est **pas artificiellement forcé** ;\n"
             "4. le protocole gelé (GENUINE, teacher/oracle, anti-leakage) est "
             "inchangé. La vraie question CE2 : *un cerveau CE1-appris accélère-t-il "
             "CE2 davantage que CP n'accélérait CE1 ?*\n")
    with open(path, "w", encoding="utf-8") as f:
        f.write("".join(a))


def main() -> None:
    r = run()
    print("=== Sèvo — Developmental evidence (CP → CE1) ===")
    print(f"  transfer verdicts: {r['n_confirmed']}/{r['n_nodes']} confirmed "
          "(localized, not global)")
    for nid, v in r["matrix"]["by_node"].items():
        print(f"    {nid:32} {v['observed_transfer']:+.2f}  {v['verdict']}")
    print(f"  artifacts: {r['artifacts_dir']} + docs/DEVELOPMENTAL_EVIDENCE.md")


if __name__ == "__main__":
    main()
