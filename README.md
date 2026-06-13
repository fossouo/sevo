# Sèvo — cerveau artificiel persistant exposé par API

> **Sèvo** = « cerveau » en créole haïtien.

Sèvo n'est **pas** un agent éducatif qui récite un programme. C'est une
**architecture cognitive persistante** : un cerveau artificiel doté d'un état
interne continu, exposé par API, qui

1. **perçoit** des stimuli (cours, exercices, feedback) venant d'Emma ou du monde,
2. **modifie son état interne** (mémoires, procédures, stratégies),
3. **consolide** ses apprentissages (replay de type « sommeil »),
4. est **évalué avant / après**, sur des épreuves tenues à l'écart,
5. et **montre s'il est devenu plus capable** — pas seulement s'il a grossi sa base de connaissances.

```
Brain_before + Emma + Curriculum(classe N) + exercices + feedback + consolidation = Brain_after
Intelligence_delta = evaluation(Brain_after) − evaluation(Brain_before)
```

Le programme scolaire **ne vit pas dans le cerveau** : c'est un environnement
externe que le cerveau traverse, comme un enfant traverse le CP, le CE1, le CE2…
La mémoire, elle, est ce que le cerveau a réellement incorporé après perception,
attention, exercice, feedback et consolidation.

---

## Pourquoi ce n'est pas de la mémorisation déguisée

Le point dur du projet est de mesurer « plus intelligent » sans se laisser
berner par la mémorisation. Sèvo s'y prend de quatre façons, toutes **vérifiées
par l'expérience livrée** (`reports/EXPERIMENT_REPORT.md`) :

| Garde-fou | Résultat mesuré (seed 7) |
|---|---|
| **Banques disjointes** enseignement ≠ évaluation | held-out 0 % → **94 %** |
| **Transfert** vers une plage jamais enseignée (addition < 1000) | 0 % → **90 %** |
| **Efficacité d'apprentissage** : les prérequis accélèrent un nouveau nœud | **≈21 vs ≈35 essais (×1,66, moyenné sur 6 seeds)** |
| **Témoin mémoriseur** : apprend par cœur les items vus | 100 % vu / **0 % held-out / 0 % transfert** |
| **« Il sait qu'il ne sait pas »** : multiplication jamais enseignée | confiance **0,10** avant *et* après |

**Intelligence_delta = 0,748** sur le run de référence (reproductible bit-à-bit,
seed 7). Ce n'est **pas un QI** :
c'est un indice interne d'évolution cognitive (formule pondérée ci-dessous).

### Le cœur cognitif généralise sur trois domaines

Le même cerveau (mêmes microservices, même machinerie d'évaluation) apprend
**trois** domaines indépendants avec les mêmes garanties :

| Domaine | Held-out | Transfert (jamais vu) | Erreur caractéristique | Δ |
|---|---|---|---|---|
| Maths CP/CE1 (addition, retenue) | 0 → 94 % | 0 → 90 % | oubli de la retenue | **0,748** |
| Français — pluriel des noms (-s, -al→-aux) | 0 → 85 % | 0 → 83 % | *chevals* (sur-régularisation) | **0,693** |
| Français — présent des verbes en -er | 0 → 86 % | 0 → 88 % | infinitif *« je parler »* | **0,706** |

Rapports : `reports/EXPERIMENT_REPORT.md`, `_FR.md`, `_CONJUGATION.md`. Un
résultat **honnête** ressort du 3ᵉ domaine : le transfert *inter-domaines* est
quasi nul (la conjugaison ne partage qu'une compétence mineure avec le pluriel),
ce qui confirme que **le transfert est proportionnel à la structure partagée** —
fort entre `reg`→`-al` (pluriel), faible entre pluriel→conjugaison.
S'il ne marchait que sur un domaine, ce serait une calculette, pas un cerveau.

### Le cycle CP complet, ingéré depuis le programme officiel

Au-delà des domaines isolés, Sèvo exécute désormais **toute une classe** de bout
en bout. Le programme **CP** (français + maths) est ingéré via le contrat
standard (`curriculum/official_curriculum.py` — disciplines, attendus de fin
d'année, prérequis, types d'exercices, critères d'évaluation), puis le cerveau
traverse le cycle complet sur les 5 nœuds : pré-test à froid → Emma enseigne →
consolidation → post-test immédiat → post-test différé (+7 j) → transfert.

| Facette (agrégée) | Pré-test | Post-test |
|---|---|---|
| **Connaissance** (held-out) | 0 % | 95 % |
| **Transfert** (mots/pseudo-mots jamais vus) | 0 % | 61 % |
| **Rétention** (+7 j) | — | 62 % |
| **Métacognition** (erreur de calibration ↓) | 0,10 | 0,07 |

**Intelligence_delta (CP) = 0,625** (`reports/CP_GRADE_REPORT.md`). Le nouveau
domaine **lecture / décodage** (correspondances graphème-phonème, mots réguliers,
mots irréguliers, compréhension de phrase) y est prouvé comme les autres :
décodage de **pseudo-mots** 0 → 79 % (le test étalon d'une vraie compétence
alphabétique — un mémoriseur y est à 0 %), erreurs caractéristiques *« chat »
→ /kat/* (lettre à lettre) et *« femme » → /fəm/* au lieu de /fam/
(sur-régularisation). Le
lexique CP structuré (`curriculum/fr_lexicon.py` : lemmes, formes fléchies,
fréquence, niveau scolaire, source traçable) garde Emma honnête.

---

## Architecture

Le cerveau est un ensemble de **microservices cognitifs** persistants câblés sur
un bus d'événements (`design/events_topics.json`). Le MVP exécute les dix
services suivants (les cinq autres du design sont des stubs documentés) :

| Fonction humaine | Microservice | Rôle dans le MVP |
|---|---|---|
| Perception | `sensory_gateway` | normalise tout input en percept |
| Conscience de travail | `global_workspace` | blackboard central, broadcast |
| Mémoire de travail | `working_memory` | tampon borné objectif + variables |
| Contrôle exécutif | `executive_control` | essayer vs « je ne sais pas » (basé sur la **présence d'une méthode**, pas le succès récent) |
| Mémoire épisodique | `episodic_memory` | écriture rapide des tentatives/feedback (oubli rapide) |
| Mémoire sémantique | `semantic_memory` | graphe de maîtrise durable des notions |
| Mémoire procédurale | `procedural_memory` | savoir-faire exécutables + **erreurs caractéristiques** + décroissance |
| Métacognition | `metacognition_self_model` | confiance, calibration, « connaît ses inconnues » |
| Consolidation / sommeil | `consolidation_sleep` | replay épisodique → procédural/sémantique durable |
| Évaluation externe | `assessment_oracle` | mesure **sans jamais enseigner** (chemin lecture seule) |

Le moteur d'apprentissage repose sur les **Complementary Learning Systems** :
trace épisodique rapide (hippocampe) puis consolidation lente et durable
(néocortex). C'est ce qui distingue une bonne réponse immédiate d'un
apprentissage stabilisé — et c'est mesuré par le **test différé à 7 jours**.

---

## Démarrage

```bash
git clone https://github.com/fossouo/sevo.git
cd sevo

# Tests (aucune dépendance externe requise)
PYTHONPATH=src python3 -m pytest -q

# Expériences complètes (maths + français) + rapports reproductibles
PYTHONPATH=src:experiments python3 experiments/generate_report.py
#   -> reports/EXPERIMENT_REPORT.md     (maths)   + reports/last_run.json
#   -> reports/EXPERIMENT_REPORT_FR.md  (français) + reports/last_run_fr.json

# API HTTP optionnelle (mappe design/api_surface.json)
pip install -e ".[api]"
uvicorn sevo.api:app --reload
```

Surface API (`design/api_surface.json`) : `/perceive` · `/act` · `/learn/session`
· `/learn/feedback` · `/consolidate` · `/evaluate/pretest` · `/evaluate/posttest`
· `/state/snapshot/{id}` · `/intelligence/delta`. Règle cardinale : **l'API
d'évaluation n'écrit jamais dans les mémoires d'apprentissage**.

---

## La formule Intelligence_delta

```
weighted_delta = knowledge_gain      × 0.30
               + transfer_gain       × 0.25
               + reasoning_gain      × 0.20
               + retention_gain      × 0.10
               + metacognition_gain  × 0.10
               + learning_efficiency_gain × 0.05
```

Chaque composante est mesurée par l'oracle sur des banques **held-out / transfert
/ différées**, jamais sur les items d'enseignement. Détail et provenance dans
`design/metrics_intelligence.json` et `src/sevo/eval/protocol.py`.

---

## MVP : CP/CE1 maths + français

Conformément au design, le MVP couvre les maths CP/CE1 (symboles, numération,
procédures, correction d'erreurs, transfert, rétention) **et** un premier domaine
français (accord du pluriel) pour prouver que l'architecture n'est pas spécifique
à l'arithmétique. Les deux passent par le même contrat d'ingestion
(`design/curriculum_ingestion_contract.json`, implémenté dans
`curriculum/ingestion.py`).

## Structure

```
design/        # contrats v0.3 (spec source de vérité, JSON + SPEC.md)
src/sevo/      # implémentation de référence
  services/    # les 10 microservices MVP (+ stubs non-MVP)
  curriculum/  # base · cp_ce1_math · fr_cp_ce1 · fr_conjugation · fr_lecture_cp · fr_lexicon · official_curriculum · ingestion
  teacher/     # emma_stub (déterministe, offline) · emma_litellm (live, INERTE par défaut)
  eval/        # protocole + calcul Intelligence_delta
  brain.py     # orchestrateur + surface API (multi-domaines)
  api.py       # adaptateur HTTP FastAPI (optionnel)
experiments/   # run_cp_ce1_math · run_fr_cp_ce1 · run_fr_conjugation · run_cp_grade · run_emma_live · generate_report
tests/         # 55 tests : invariants design + maths + français (pluriel/conjugaison/lecture) + lexique + curriculum officiel + intégration
reports/       # preuve committée (EXPERIMENT_REPORT*.md, CP_GRADE_REPORT.md, last_run*.json)
```

## La vraie Emma a déjà enseigné (run live)

La **vraie Emma** — `diffusiongemma-26B-A4B` servie en local sur DGX (vLLM
`:8010`, `enable_thinking:false`) — a réellement enseigné le cerveau le pluriel
français. Le modèle **propose** les exemples (chat, animal, journal, hôpital,
bras, riz…), le curriculum les **vette** et calcule la bonne réponse, l'oracle
note sur des banques tenues à l'écart. Résultat (`reports/emma_live_run.json`,
15 appels, ~51 s, modèle local = 0 €) :

> held-out 0 → **100 %**, transfert sur mots inédits 0 → **100 %**, rétention
> T2 +7 j = 67 %, **Intelligence_delta live = 0,82**.

```bash
PYTHONPATH=src:experiments python3 experiments/run_emma_live.py
# backend par défaut : DGX :8010 (bypass gateway, sans clé). Override possible :
# SEVO_LLM_URL=http://xeon:4000 SEVO_LLM_MODEL=code python3 experiments/run_emma_live.py
```

**Double garde sur les mots proposés (le live ne peut pas enseigner un faux
pluriel)** : un mot proposé par le modèle ne devient un exercice que s'il passe
*deux* filtres — `vet_word` (bonne **forme** pour la notion : écarte les
exceptions `-al`→`-als` et les mauvaises catégories) **et** `in_lexicon` (mot
**attesté** : `src/sevo/curriculum/fr_lexicon.py`). Ce 2ᵉ filtre ferme la limite
révélée par le 1ᵉʳ run live : une hallucination de *forme* correcte (« éral » →
« éraux ») est désormais rejetée car ce n'est pas un mot réel. On préfère écarter
un mot légitime non listé (l'adaptateur sur-échantillonne) plutôt qu'enseigner un
pluriel fabriqué. L'ingestion du programme officiel grossira ce lexique depuis
une ressource lexicale réelle, validée de la même façon.

## Feuille de route

- **Fait** : MVP **multi-domaines** (maths, pluriel, conjugaison, **lecture /
  décodage**) ; **cycle CP complet** ingéré depuis le programme officiel et prouvé
  de bout en bout (`run_cp_grade`) ; lexique structuré (lemmes, formes, niveau,
  source) ; Emma déterministe **et** live (diffusiongemma/DGX) prouvées ;
  adaptateur LiteLLM inerte par défaut avec double garde forme + lexique.
- **Ensuite** : ingérer les **classes suivantes** (CE1, CE2…) via
  `official_curriculum.register_class` ; brancher le lexique sur la **ressource
  réelle complète** (Manulex / Dubois-Buyse) au lieu du sous-ensemble amorce ;
  ajouter la **fluence** et la segmentation syllabique explicite ; génération live
  d'exercices de lecture/conjugaison (mêmes gardes).

## Provenance & licence

Conception issue de la spécification *Human Brain API School v0.3*
(`design/SPEC.md`). Inspirations scientifiques (CLS hippocampe/néocortex,
mémoire sémantique, cadre PISA) listées dans `design/sources.json`.

Licence **Apache-2.0** — voir [`LICENSE`](LICENSE).
