# Developmental curve — naïf → CP → CE1 → CE2 → CM1 (frozen result)

> **recurring bottleneck law** · **localized transfer, no global acceleration** ·
> **each class unlocks the next by filling its bottleneck skill**

This is the frozen, citable counterpart to the generated report
`reports/DEVELOPMENTAL_CURVE.md` — the same way `docs/DEVELOPMENTAL_EVIDENCE.md`
froze the CP → CE1 finding. Every number and phrase below already exists in the
generated report and is locked by `tests/test_curve_numeric_fixture.py`; nothing
is added or re-interpreted here.

_Reproducible, seed = 7._

## Résumé

Étendue de CP → CE1 à la trajectoire complète naïf → CP → CE1 → CE2 → CM1, la
mesure montre une **loi du goulot récurrente** : à chaque classe, la compétence
arithmétique **nouvelle** fait goulot et **bloque** le transfert ; une fois
**acquise**, elle **débloque** la transition suivante. Pas d'accélération
globale — une montée en capacité **cumulative et localisée** à la structure
partagée.

## Transfert sur le nœud-clé de chaque étape

(la compétence arithmétique nouvelle de la classe cible)

| Étape | Nœud-clé | Compétence-goulot | Transfert (Δ pré-test) | Essais (dev vs naïf) |
|---|---|---|---|---|
| **CP → CE1** | `math.CE1.add_within_100_carry` | `carry` (nouveau) | **+0.00** | 16 vs 24 |
| **CE1 → CE2** | `math.CE2.add_within_1000` | `carry` (acquis) | **+0.88** | 8 vs 56 |
| **CE2 → CM1** | `math.CM1.multiply_table` | `multiply` (nouveau) | **+0.00** | 16 vs 16 |

## Le motif : nouveau goulot ⇒ blocage ; goulot acquis ⇒ déblocage

* **CP → CE1** — l'addition avec retenue ne transfère **pas** (+0.00) : `carry`
  est **nouveau** au CE1, c'est le goulot, et les acquis CP (valeur de position,
  faits numériques) ne suffisent pas à le débloquer.
* **CE1 → CE2** — l'addition < 1000 transfère **fortement** (+0.88, 8 vs 56
  essais) : `carry`, **appris au CE1**, complète enfin la chaîne de prérequis.
  La compétence qui *bloquait* la transition précédente est celle qui *débloque*
  la suivante.
* **CE2 → CM1** — la multiplication ne transfère **pas** (+0.00) : `multiply` est
  **nouveau** au CM1, exactement comme `carry` l'était au CE1. Le motif est
  **récurrent**.

## Lecture

C'est une **vraie trajectoire développementale** : chaque classe **débloque la
suivante en comblant la compétence-goulot**. Le transfert reste **localisé** à la
structure partagée (le français ne transfère pas) — donc pas d'accélération
globale magique, mais une montée en capacité **cumulative et explicable**.

## Limites

* Modèle de compétences **simplifié** (pas un vrai système cognitif humain) ; les
  forces sont relatives, pas absolues.
* Mesure sur des **jeux amorces** par classe, seed fixe (= 7).
* Le transfert est mesuré au **pré-test held-out** ; il ne capture pas
  d'éventuels effets de vitesse fins par-delà la maîtrise.
* Les Δ et comptes d'essais sont ceux du split de bancs **figé** (voir ci-dessous) ;
  ils ne valent que pour ce protocole.

## Ce qui verrouille ces chiffres

* `tests/test_curve_numeric_fixture.py` — pin des Δ de transfert, des comptes
  d'essais (16/24/8/56/16/16) et de la stabilité du RNG forké (seed = 7).
* `tests/test_bank_params.py` — pin des paramètres de split des bancs
  (`frac_teach = 0.55` ; `n_teach = 24`, `n_heldout = 24`).
* Tout changement de ces constantes est une **rupture de protocole** : régénérer
  tous les artefacts `demo/` + `reports/` et mettre à jour la fixture numérique
  (voir `docs/CP_PROTOCOL.md`).

## Critères pour ouvrir la classe suivante (CM2 / 6e)

La classe suivante ne devra être ajoutée que si, comme ici :
1. le transfert reste **localisé** (pas d'amélioration partout) ;
2. le transfert arithmétique partagé reste **positif** là où la chaîne de
   prérequis est complète ;
3. la nouvelle compétence-goulot n'est **pas artificiellement forcée** à
   transférer ;
4. le protocole gelé (GENUINE, séparation teacher/oracle, anti-leakage,
   `Rng.fork` sha256) est **inchangé**.

La question ouverte, par construction : *une compétence nouvelle (division,
fractions) refait-elle goulot, confirmant la loi une fois de plus ?*
