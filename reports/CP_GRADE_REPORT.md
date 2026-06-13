# CP grade report — whole-class learning cycle
_Reproducible run, seed = 7. An **official-curriculum-shaped CP seed registry** (`curriculum/official_curriculum.py`) — aligned with the official CP expectations, **partial and hand-verified, not a full BO ingest** — loaded through the standard ingestion contract, then run through the full lifecycle: cold pretest → Emma teaches every node → consolidation → immediate posttest → +7-day delayed posttest → transfer. All scores by the assessment oracle on disjoint banks._

> ⚠️ Registre aligné sur les attendus officiels du CP — jeu amorce partiel, vérifié à la main (PAS un ingest exhaustif du Bulletin officiel).

**Intelligence_delta (CP) = 0.749** (internal cognitive evolution index — not a human IQ).

> ✅ **Apprentissage authentique : GENUINE** — le delta n'est déclaré que si les cinq garde-fous passent.

| Garde-fou | OK |
|---|---|
| post_test_gain | ✅ |
| held_out_gain_substantial | ✅ |
| transfer_nonzero | ✅ |
| beats_memoriser | ✅ |
| retention_measurable | ✅ |

## Five facets (aggregate)

| Facet | Pretest | Posttest |
|---|---|---|
| **Connaissance** (held-out) | 0% | 94% |
| **Transfert** (items jamais vus + pseudo-mots) | 0% | 88% |
| **Rétention** (+7 jours) | — | 70% |
| **Métacognition** (erreur de calibration, plus bas = mieux) | 0.10 | 0.10 |

_**Procédure** : voir le graphe d'automaticité des compétences dans `last_run_cp_grade.json` (`procedure_skill_graph`) — c'est l'état interne des savoir-faire, distinct de la connaissance restituée._

## Par nœud du programme CP

| Nœud | Discipline | Held-out pré→T1→T2 | Transfert T1 |
|---|---|---|---|
| `math.CP.add_within_20` | nombres et calculs | 0% → 88% → 54% | 35% |
| `math.CP.sub_within_20` | nombres et calculs | 0% → 100% → 75% | — |
| `fr.CP.lecture_mots_reguliers` | lecture / décodage | 0% → 100% → 78% | 100% |
| `fr.CP.lecture_mots_irreguliers` | lecture / mots-outils | 0% → 100% → 100% | — |
| `fr.CP.comprehension_phrase` | compréhension | 0% → 85% → 62% | 100% |
| `fr.CP.segmentation_syllabes` | lecture / phonologie | 0% → 86% → 86% | 100% |
| `fr.CP.dictee_simple` | écriture / encodage | 0% → 100% → 29% | 100% |
| `math.CP.numeration_dizaines_unites` | nombres et calculs | 0% → 97% → 69% | 100% |
| `math.CP.comparaison_nombres` | nombres et calculs | 0% → 89% → 78% | 83% |

_La transfert mathématique (`add_within_20` → addition < 1000) est volontairement **hors-niveau** : son score quasi nul est attendu et montre que le cerveau ne sur-généralise pas au-delà de ce qui a été enseigné au CP._

## Composantes de l'Intelligence_delta

| Composante | Poids | Valeur |
|---|---|---|
| knowledge_gain | 0.30 | +0.938 |
| transfer_gain | 0.25 | +0.883 |
| reasoning_gain | 0.20 | +0.883 |
| retention_gain | 0.10 | +0.700 |
| metacognition_gain | 0.10 | -0.001 |
| learning_efficiency_gain | 0.05 | +0.000 |
## Diff d'état du cerveau — Brain CP-naïf → Brain CP-appris

_Enseigné via la **boucle API Emma** (emma_api_loop) : Emma présente → le cerveau répond → feedback structuré → le cerveau apprend ; l'évaluation reste indépendante (oracle)._

> **Portée** : ces facettes décrivent une capacité acquise **sur le curriculum CP mesuré** (*genuine learning under the CP protocol*). Ce n'est **pas** une intelligence générale au sens psychométrique, ni un QI.

* **Concepts sémantiques acquis** (9) : `fr.CP.comprehension_phrase`, `fr.CP.dictee_simple`, `fr.CP.lecture_mots_irreguliers`, `fr.CP.lecture_mots_reguliers`, `fr.CP.segmentation_syllabes`, `math.CP.add_within_20`, `math.CP.comparaison_nombres`, `math.CP.numeration_dizaines_unites`, `math.CP.sub_within_20`
* **Règles procédurales acquises** (12) : `add_facts_within_20`, `blending`, `grapheme_phoneme`, `grapheme_recognition`, `lexical_access`, `number_comparison`, `orthographic_encoding`, `place_value`, `sentence_parsing`, `sight_words`, `sub_facts_within_20`, `syllable_segmentation`
* **Compétences automatisées** (12) : `add_facts_within_20` (0.05→0.936), `blending` (0.05→0.934), `grapheme_phoneme` (0.05→0.951), `grapheme_recognition` (0.05→0.944), `lexical_access` (0.05→0.913), `number_comparison` (0.05→0.943), `orthographic_encoding` (0.05→0.922), `place_value` (0.05→0.951), `sentence_parsing` (0.05→0.913), `sight_words` (0.05→0.94), `sub_facts_within_20` (0.05→0.944), `syllable_segmentation` (0.05→0.922)
* **Misconceptions réduites** : taux d'erreur held-out 1.0 → 0.062 (−0.938)
* **Calibration** : 0.1 → 0.101 (amélioration -0.001)
* **Traces de rétention (+7 j)** : held-out 0.699, ratio t2/t1 0.746, 12 compétences consolidées
* **Efficacité d'apprentissage** : +0.000

### Matrice de maîtrise par compétence (automaticité avant → après)

| Compétence | Avant | Après |
|---|---|---|
| add_facts_within_20 | 0.05 | 0.936 |
| blending | 0.05 | 0.934 |
| grapheme_phoneme | 0.05 | 0.951 |
| grapheme_recognition | 0.05 | 0.944 |
| lexical_access | 0.05 | 0.913 |
| number_comparison | 0.05 | 0.943 |
| orthographic_encoding | 0.05 | 0.922 |
| place_value | 0.05 | 0.951 |
| sentence_parsing | 0.05 | 0.913 |
| sight_words | 0.05 | 0.94 |
| sub_facts_within_20 | 0.05 | 0.944 |
| syllable_segmentation | 0.05 | 0.922 |

## Contrôles (le gain n'est pas de la mémorisation)

* **Mémoriseur anti-fuite** — 100% sur les items enseignés, mais 0% held-out et 0% en transfert. Les gains du cerveau ne s'expliquent pas par la mémorisation.
* **Efficacité d'apprentissage** — apprendre la soustraction après l'addition : 14.0 essais vs 14.0 à froid (1.0×).
* **Erreurs caractéristiques** (cerveau naïf) :
  * lecture_reguliers — *chat* (vrai : `S.a`) → « k.a.t » (letter_by_letter)
  * lecture_irreguliers — *femme* (vrai : `f.a.m`) → « f.@.m » (overregularized_reading)
  * comprehension — *« le chat mange la pomme ». Qui ?* (vrai : `le chat`) → « la pomme » (role_confusion)
  * maths_addition — *4 + 9 = ?* (vrai : `13`) → « 14 » (add_fact_off_by_one)
