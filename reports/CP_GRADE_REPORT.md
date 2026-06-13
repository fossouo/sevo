# CP grade report — whole-class learning cycle
_Reproducible run, seed = 7. The CP programme (`curriculum/official_curriculum.py`) ingested through the standard contract, then run through the full lifecycle: cold pretest → Emma teaches every node → consolidation → immediate posttest → +7-day delayed posttest → transfer. All scores by the assessment oracle on disjoint banks._

**Intelligence_delta (CP) = 0.625** (internal cognitive evolution index — not a human IQ).

## Five facets (aggregate)

| Facet | Pretest | Posttest |
|---|---|---|
| **Connaissance** (held-out) | 0% | 95% |
| **Transfert** (items jamais vus + pseudo-mots) | 0% | 61% |
| **Rétention** (+7 jours) | — | 62% |
| **Métacognition** (erreur de calibration, plus bas = mieux) | 0.10 | 0.07 |

_**Procédure** : voir le graphe d'automaticité des compétences dans `last_run_cp_grade.json` (`procedure_skill_graph`) — c'est l'état interne des savoir-faire, distinct de la connaissance restituée._

## Par nœud du programme CP

| Nœud | Discipline | Held-out pré→T1→T2 | Transfert T1 |
|---|---|---|---|
| `math.CP.add_within_20` | nombres et calculs | 0% → 92% → 58% | 5% |
| `math.CP.sub_within_20` | nombres et calculs | 0% → 88% → 75% | — |
| `fr.CP.lecture_mots_reguliers` | lecture / décodage | 0% → 100% → 56% | 79% |
| `fr.CP.lecture_mots_irreguliers` | lecture / mots-outils | 0% → 100% → 50% | — |
| `fr.CP.comprehension_phrase` | compréhension | 0% → 94% → 74% | 100% |

_La transfert mathématique (`add_within_20` → addition < 1000) est volontairement **hors-niveau** : son score quasi nul est attendu et montre que le cerveau ne sur-généralise pas au-delà de ce qui a été enseigné au CP._

## Composantes de l'Intelligence_delta

| Composante | Poids | Valeur |
|---|---|---|
| knowledge_gain | 0.30 | +0.947 |
| transfer_gain | 0.25 | +0.612 |
| reasoning_gain | 0.20 | +0.612 |
| retention_gain | 0.10 | +0.625 |
| metacognition_gain | 0.10 | +0.030 |
| learning_efficiency_gain | 0.05 | +0.000 |

## Contrôles (le gain n'est pas de la mémorisation)

* **Mémoriseur anti-fuite** — 100% sur les items enseignés, mais 0% held-out et 0% en transfert. Les gains du cerveau ne s'expliquent pas par la mémorisation.
* **Efficacité d'apprentissage** — apprendre la soustraction après l'addition : 14.0 essais vs 14.0 à froid (1.0×).
* **Erreurs caractéristiques** (cerveau naïf) :
  * lecture_reguliers — *chat* (vrai : `S.a`) → « k.a.t » (letter_by_letter)
  * lecture_irreguliers — *femme* (vrai : `f.a.m`) → « f.@.m » (overregularized_reading)
  * comprehension — *« le chat mange la pomme ». Qui ?* (vrai : `le chat`) → « la pomme » (role_confusion)
  * maths_addition — *4 + 9 = ?* (vrai : `13`) → « 14 » (add_fact_off_by_one)
