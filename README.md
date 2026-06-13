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

### Le cœur cognitif généralise au-delà des maths

Le même cerveau (mêmes microservices, même machinerie d'évaluation) apprend aussi
un domaine **français CP/CE1** — l'accord du pluriel des noms — avec les mêmes
garanties : held-out 0 → 85 %, **transfert de règle** (-s et -al→-aux) sur des
mots jamais vus 0 → 83 %, mémoriseur 0 %, et l'**erreur caractéristique
« chevals »** (sur-régularisation) émerge à faible maîtrise.
**Intelligence_delta français = 0,693** (`reports/EXPERIMENT_REPORT_FR.md`).
S'il ne marchait que sur l'arithmétique, ce serait une calculette, pas un cerveau.

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
  curriculum/  # base.py (tâche agnostique) · cp_ce1_math · fr_cp_ce1 · ingestion
  teacher/     # emma_stub (déterministe, offline) · emma_litellm (live, INERTE par défaut)
  eval/        # protocole + calcul Intelligence_delta
  brain.py     # orchestrateur + surface API (multi-domaines)
  api.py       # adaptateur HTTP FastAPI (optionnel)
experiments/   # run_cp_ce1_math.py · run_fr_cp_ce1.py · generate_report.py
tests/         # 26 tests : invariants design + dynamique maths + français + intégration
reports/       # preuve committée (EXPERIMENT_REPORT*.md, last_run*.json)
```

## Feuille de route

- **Fait (ce dépôt)** : MVP exécutable multi-domaines, appris hors-ligne par une
  Emma déterministe, prouvé sur CP/CE1 maths **et** français ; adaptateur **Emma
  LiteLLM** écrit et testé hors-ligne mais **inerte par défaut** ; API d'ingestion
  de curriculum conforme au contrat.
- **Ensuite (gardé pour un GO explicite)** : activer la **vraie Emma** sur une
  fenêtre GPU dédiée (`SEVO_EMMA_LIVE=1` + `LITELLM_URL`, voir l'en-tête de
  `teacher/emma_litellm.py`), puis ingérer le **programme scolaire français
  officiel** (sources dans `design/sources.json`) classe par classe — chaque
  classe étant un épisode développemental versionné.

## Provenance & licence

Conception issue de la spécification *Human Brain API School v0.3*
(`design/SPEC.md`). Inspirations scientifiques (CLS hippocampe/néocortex,
mémoire sémantique, cadre PISA) listées dans `design/sources.json`.

Licence **Apache-2.0** — voir [`LICENSE`](LICENSE).
