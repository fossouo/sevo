# Developmental curve — naïf → CP → CE1 → CE2 → CM1

_Reproducible, seed = 7. **Does a CE1-appris brain accelerate CE2 more than CP accelerated CE1 — and does a new bottleneck (multiplication at CM1) block transfer again?**_

## Réponse : **oui**, et le motif se répète

Le transfert sur le nœud-clé de chaque étape (la compétence arithmétique nouvelle de la classe cible) :

| Étape | Nœud-clé | Compétence-goulot | Transfert (Δ pré-test) | Essais (dev vs naïf) |
|---|---|---|---|---|
| **CP → CE1** | `math.CE1.add_within_100_carry` | `carry` (nouveau) | **+0.00** | 16 vs 24 |
| **CE1 → CE2** | `math.CE2.add_within_1000` | `carry` (acquis) | **+0.88** | 8 vs 56 |
| **CE2 → CM1** | `math.CM1.multiply_table` | `multiply` (nouveau) | **+0.00** | 16 vs 16 |

## Le motif : nouveau goulot ⇒ blocage ; goulot acquis ⇒ déblocage

* **CE2 → CM1** : la multiplication ne transfère **pas** (+0.00) — `multiply` est **nouveau** au CM1, exactement comme `carry` l'était au CE1. Le motif est **récurrent** : chaque classe rencontre un nouveau goulot qui bloque le transfert jusqu'à ce qu'il soit appris.

## Pourquoi — le goulot se débloque

À **CP → CE1**, l'addition avec retenue ne transfère **pas** (+0.00) : `carry` est **nouveau** au CE1, c'est le goulot, et les acquis CP (valeur de position, faits numériques) ne suffisent pas à le débloquer.

À **CE1 → CE2**, l'addition < 1000 transfère **fortement** (+0.88, 8 vs 56 essais) : `carry`, **appris au CE1**, complète enfin la chaîne de prérequis. La compétence qui *bloquait* la transition précédente est celle qui *débloque* la suivante.

## Lecture

C'est une **vraie trajectoire développementale** : chaque classe **débloque la suivante en comblant la compétence-goulot**. Le transfert reste **localisé** à la structure partagée (le français ne transfère pas) — donc pas d'accélération globale magique, mais une montée en capacité **cumulative et explicable**.
