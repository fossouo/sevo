# Developmental evidence — CP → CE1 (frozen result)

> **localized developmental transfer** · **not global intelligence acceleration** · **transfer proportional to shared structure**

## Résumé

Un cerveau **CP-appris** apprend CE1 avec un avantage de transfert **réel mais localisé**. Le transfert est **confirmé** là où une compétence du CP est réellement réutilisée par CE1, **faible ou absent** ailleurs, et — découverte clé — **bloqué par la nouvelle compétence-goulot** quand CE1 en introduit une.

## Matrice de transfert (compétence CP → nœud CE1)

| Nœud CE1 | Compétences CP partagées | Nouvelles à CE1 | Poids partagé | Attendu | Observé (Δ pré-test) | Verdict |
|---|---|---|---|---|---|---|
| `fr.CE1.pluriel_reguliers` | grapheme_recognition | plural_rule_s | 0.30 | medium | +0.18 | **weak** |
| `fr.CE1.pluriel_en_al` | grapheme_recognition | plural_exception_aux | 0.30 | medium | -0.25 | **absent** |
| `fr.CE1.present_verbes_er` | grapheme_recognition | present_er_endings, subject_agreement, verb_stem_recognition | 0.20 | weak | +0.02 | **absent** |
| `math.CE1.add_within_100_nocarry` | add_facts_within_20, place_value | — | 1.00 | strong | +0.75 | **confirmed** |
| `math.CE1.add_within_100_carry` | add_facts_within_20, place_value | carry | 0.60 | strong | +0.00 | **absent** |
| `math.CE1.sub_within_100_borrow` | place_value, sub_facts_within_20 | borrow | 0.60 | strong | +0.25 | **weak** |

## Ce qui transfère, ce qui ne transfère pas, pourquoi

* **Transfère (confirmé)** — l'addition CE1 *sans retenue* (`math.CE1.add_within_100_nocarry`) : ses deux compétences (`place_value`, `add_facts_within_20`) sont **entièrement acquises au CP** → quasi-maîtrisée dès le pré-test.
* **Bloqué par la nouvelle compétence** — l'addition *avec retenue* et la soustraction *avec emprunt* partagent `place_value`/faits avec le CP, **mais** `carry` / `borrow` sont **nouveaux au CE1** et font goulot → transfert faible/absent malgré les prérequis partagés. C'est le résultat le plus instructif : *le transfert est plafonné par la compétence manquante*.
* **Ne transfère pas (absent)** — pluriel et conjugation ne partagent que `grapheme_recognition` (poids faible) avec le CP → aucun avantage. Le français du CE1 est, pour l'essentiel, **nouveau**.

## Limites

* Modèle de compétences **simplifié** (pas un vrai système cognitif humain) ; les forces sont relatives, pas absolues.
* Mesure sur un **jeu amorce** CP/CE1 partiel, seed fixe.
* Le transfert est mesuré au **pré-test held-out** ; il ne capture pas d'éventuels effets de vitesse fins par-delà la maîtrise.

## Critères pour ouvrir CE2

CE2 ne devra être lancé que si, comme ici :
1. le transfert reste **localisé** (pas d'amélioration partout) ;
2. le transfert arithmétique partagé reste **positif** ;
3. le transfert non partagé n'est **pas artificiellement forcé** ;
4. le protocole gelé (GENUINE, teacher/oracle, anti-leakage) est inchangé. La vraie question CE2 : *un cerveau CE1-appris accélère-t-il CE2 davantage que CP n'accélérait CE1 ?*
