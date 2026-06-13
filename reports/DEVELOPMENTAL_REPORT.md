# Developmental progression — CP → CE1
_Reproducible, seed = 7. **Does a CP-appris brain learn CE1 better/faster/cleaner than a naïve one?**_

Deux scénarios, même cerveau, même Emma : **développemental** (naïf → CP → CE1) vs **isolé** (naïf → CE1).

## Réponse (agrégée sur les nœuds CE1)

| Mesure | Développemental (CP-appris) | Isolé (naïf) |
|---|---|---|
| **Transfert** — held-out CE1 au *pré-test* | 0.29 | 0.13 |
| **Vitesse** — essais jusqu'à maîtrise (Σ) | 120 | 128 |
| **Post** — held-out CE1 après apprentissage | 0.90 | 0.93 |

## Par nœud CE1 (pré-test · essais)

| Nœud | dev pré | iso pré | dev essais | iso essais |
|---|---|---|---|---|
| `fr.CE1.pluriel_reguliers` | 0.18 | 0.00 | 16 | 8 |
| `fr.CE1.pluriel_en_al` | 0.12 | 0.38 | 32 | 24 |
| `fr.CE1.present_verbes_er` | 0.09 | 0.08 | 16 | 24 |
| `math.CE1.add_within_100_nocarry` | 0.75 | 0.00 | 8 | 32 |
| `math.CE1.add_within_100_carry` | 0.29 | 0.29 | 16 | 24 |
| `math.CE1.sub_within_100_borrow` | 0.29 | 0.04 | 32 | 16 |

## Lecture honnête du résultat

Le cerveau CP-appris démarre CE1 avec un **avantage de transfert réel** (pré-test 0.29 vs 0.13), **localisé là où les compétences sont partagées** : l'arithmétique CE1 (addition/soustraction < 100) réutilise la *valeur de position* et les *faits numériques* appris au CP — souvent quasi-maîtrisée dès le pré-test et apprise plus vite. Sur les règles **françaises** (pluriel, conjugaison), qui ne partagent presque rien avec le CP, **aucun avantage** — d'où l'absence de gain *global* de vitesse (Σ essais 120 vs 128). C'est le résultat attendu : **le transfert est proportionnel à la structure partagée**, pas une accélération magique.

CE1 ajoute par-dessus le CP **6 concepts** et **7 règles procédurales** (`cp_to_ce1_diff.json`).
