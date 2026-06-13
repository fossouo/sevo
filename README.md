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
en bout. Un **registre CP de forme officielle** (`curriculum/official_curriculum.py`
— disciplines, attendus de fin d'année, prérequis, types d'exercices, critères
d'évaluation) est chargé via le contrat d'ingestion standard, puis le cerveau
traverse le cycle complet sur les 5 nœuds : pré-test à froid → Emma enseigne →
consolidation → post-test immédiat → post-test différé (+7 j) → transfert.

> ⚠️ **Portée honnête** : ce registre est *aligné sur les attendus officiels du
> CP* mais reste un **jeu amorce partiel, vérifié à la main — ce n'est pas un
> ingest exhaustif du Bulletin officiel**. Les sources (Manulex, Dubois-Buyse,
> BO CP) sont une **provenance méthodologique**, pas des jeux de données
> embarqués.

Le CP couvre **9 nœuds** (français : décodage, mots-outils, compréhension,
**syllabes**, **dictée** ; maths : addition, soustraction, **numération
dizaines/unités**, **comparaison**), enseignés via la **boucle API Emma** (Emma
présente → le cerveau répond → feedback structuré → le cerveau apprend ;
l'évaluation reste indépendante).

| Facette (agrégée) | Pré-test | Post-test |
|---|---|---|
| **Connaissance** (held-out) | 0 % | 94 % |
| **Transfert** (mots/pseudo-mots jamais vus) | 0 % | 88 % |
| **Rétention** (+7 j) | — | 70 % |
| **Métacognition** (erreur de calibration) | 0,10 | 0,10 |

**Diff d'état observable** (`Brain CP-naïf → Brain CP-appris`) : 9 concepts
acquis, 12 compétences automatisées (automaticité 0,05 → ~0,94), misconceptions
held-out 100 % → 6 %, 12 compétences consolidées après 7 jours. Le rapport
exporte une **matrice de maîtrise par compétence** avant/après. Ces facettes
décrivent une capacité acquise **sur le curriculum CP mesuré** (*genuine learning
under the CP protocol*) — **pas** une intelligence générale ni un QI.

#### Reproduire la preuve en une commande

```bash
make demo-cp     # Brain CP-naïf → Emma enseigne → Brain CP-appris → diff
                 # → évaluation indépendante → verdict GENUINE → save/reload → ré-évaluation
```

La démo (`scripts/demo_cp.py`) écrit six **artefacts de preuve** dans
`demo/artifacts/` : `brain_before.json`, `brain_after.json`, `brain_diff.json`,
`assessment_report.json`, `emma_session_journal.json`, `audit_report.json`. Le
protocole CP est **gelé** et documenté dans [`docs/CP_PROTOCOL.md`](docs/CP_PROTOCOL.md)
(définition de GENUINE, séparation teacher/oracle, anti-leakage, formats feedback/
state/session) ; `tests/test_cp_protocol_freeze.py` garde la non-régression
(GENUINE · save/reload exact · audit clean · replay déterministe · zéro leakage).
Variante service : `make demo-docker` (conteneur + smoke test HTTP).

**Le même cerveau traverse une 2ᵉ classe — CE1.** CE1 est une **extension** du
cœur gelé : il réutilise les nœuds existants (pluriel, conjugaison, addition/
soustraction < 100) via `official_curriculum.register_class("CE1")` — **aucune
réécriture**, GENUINE, séparation teacher/oracle et anti-leakage **inchangés**
(c'est un *CE1 seed registry* : aligné sur les attendus, **partiel, amorce,
vérifié à la main**). Deux modes :

```bash
make demo-ce1            # naïf : un cerveau frais apprend CE1 isolément
make demo-ce1-after-cp   # développemental : un cerveau CP-appris apprend ensuite CE1
```

Chaque mode produit les **six mêmes artefacts** que le CP et ressort **GENUINE**.
Le protocole CP reste la référence (`docs/CP_PROTOCOL.md`).

#### Trajectoire développementale : CP-appris apprend-il CE1 mieux ?

```bash
make demo-developmental    # naïf→CP→CE1  vs  naïf→CE1 ; -> reports/DEVELOPMENTAL_REPORT.md
```

Compare un cerveau **CP-appris** à un cerveau **naïf** sur l'apprentissage de CE1
(transfert au pré-test, vitesse, post). Résultat **honnête et localisé** : le
cerveau CP-appris démarre CE1 avec un **avantage de transfert réel**
(pré-test ≈ 0,29 vs 0,13), **fort là où les compétences sont partagées** —
l'arithmétique CE1 réutilise la valeur de position + les faits numériques du CP
(`add_within_100_nocarry` : pré-test **0,75 vs 0,00**, **8 vs 32 essais**) — et
**nul** sur les règles françaises (pluriel, conjugaison) qui ne partagent rien
avec le CP. Pas d'accélération *globale* magique : **le transfert est
proportionnel à la structure partagée**. Artefacts : `demo/developmental/`
(`brain_after_cp.json`, `brain_after_ce1.json`, `cp_to_ce1_diff.json`).

Ce résultat est **figé comme preuve scientifique** (`make demo-developmental-evidence`
→ [`docs/DEVELOPMENTAL_EVIDENCE.md`](docs/DEVELOPMENTAL_EVIDENCE.md) + matrice de
transfert `transfer_matrix.json`). La matrice (compétence CP → nœud CE1, attendu
vs observé, verdict `confirmed`/`weak`/`absent`) révèle la découverte clé :
l'addition CE1 *sans retenue* transfère pleinement du CP (`confirmed`), mais
l'addition *avec retenue* **non** (`absent`) — car `carry` est **nouveau** au CE1.
**Le transfert est plafonné par la compétence-goulot manquante.** Des tests de
non-régression gardent l'invariant : *« toute PR qui améliore tout partout est
suspecte »* (le transfert doit rester **localisé**, jamais forcé sur le français).

#### La courbe développementale : naïf → CP → CE1 → CE2

```bash
make demo-ce2                  # CE2 (extension : add/sub < 1000 + pluriel invariable)
make demo-developmental-curve  # mesure la courbe → reports/DEVELOPMENTAL_CURVE.md
```

CE2 est encore une **extension** (mêmes gardes) dont l'arithmétique (< 1000)
réutilise valeur de position + faits **+ retenue/emprunt**. Cela répond à la
question : *un cerveau CE1-appris accélère-t-il CE2 davantage que CP n'accélérait
CE1 ?* — **oui, et de façon explicable** :

| Étape | Nœud arithmétique | Transfert (Δ pré-test) | Essais (dev vs naïf) |
|---|---|---|---|
| CP → CE1 | `add_within_100_carry` | **+0,00** (`carry` nouveau = goulot) | 16 vs 24 |
| CE1 → CE2 | `add_within_1000` | **+0,88** (`carry` acquis au CE1) | **8 vs 56** |

**La compétence qui *bloquait* la transition précédente (`carry`) est celle qui
*débloque* la suivante.** Chaque classe **débloque la suivante en comblant la
compétence-goulot** — une vraie trajectoire développementale cumulative, le
transfert restant localisé à la structure partagée.

**Intelligence_delta (CP) = 0,749** (`reports/CP_GRADE_REPORT.md`) — et ce delta
n'est déclaré que parce qu'il **passe le garde-fou anti-illusion**
(`eval/integrity.py`) : gain post-test **et** held-out substantiel **et**
transfert non nul dans ≥ 1 domaine **et** mémoriseur battu **et** rétention
différée mesurable. Sans les cinq, le verdict est `NOT_PROVEN` et aucune
« intelligence » n'est revendiquée. Le nouveau domaine **lecture / décodage** (correspondances graphème-phonème, mots réguliers,
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

### Le cerveau comme microservice persistant

Le cerveau CP-appris est exposé comme un **service persistant** interrogeable
(`sevo.runtime.BrainService`, surface HTTP `sevo.api`) :

```bash
pip install -e ".[api]"
uvicorn sevo.api:app --reload
```

| Endpoint | Rôle | Canal |
|---|---|---|
| `POST /perceive` | percevoir un stimulus | enseignement |
| `POST /act` | répondre (lecture seule, **n'apprend pas**) | enseignement |
| `POST /feedback` | feedback structuré d'Emma → le cerveau apprend | enseignement |
| `POST /consolidate` | replay / « sommeil » | enseignement |
| `POST /replay` | rejouer une session Emma sur un nœud | enseignement |
| `POST /teach/session` | session **journalisée** (feedback structuré) | enseignement |
| `GET /state` | exporter l'état appris (brain_after) | — |
| `GET /diff` | diff `Brain-naïf → Brain-appris` + verdict GENUINE | observation |
| `POST /evaluate` | oracle sur la banque held-out d'un nœud | **assessment** |
| `POST /save` · `/load` | persister / recharger un état par chemin | — |

**Règles cardinales** : (1) le **canal d'enseignement** (`act`/`feedback`/
`consolidate`) et le **canal d'évaluation** (`evaluate`, oracle) sont stricts et
séparés — Emma ne se note jamais ; (2) un cerveau **sauvegardé puis rechargé
conserve exactement ses compétences** (état procédural/sémantique identique au
bit près — testé). L'API HTTP est un mince adaptateur sur `BrainService`, lui-même
testable sans serveur.

#### Durci pour tourner comme un vrai service

- **State schema + migrations** (`persistence.py`) : l'export runtime est
  versionné (`runtime_schema_version`) ; un état d'une version antérieure est
  **migré explicitement** (0.4 → 0.5) ou **rejeté** avec une erreur claire —
  jamais relu silencieusement.
- **Sessions persistantes** : `POST /session/start` ouvre une session
  (`session_id`) qui trace perceptions/feedbacks ; `POST /session/{id}/replay`
  rejoue la session **de façon déterministe** (l'apprentissage par feedback est
  reproductible au bit près) et reconstitue l'état final.
- **Observabilité** : `GET /health`, `GET /metrics` (compteurs perceptions /
  actions / feedbacks / consolidations, compétences maîtrisées, verdict
  GENUINE / NOT_PROVEN).
- **Sécurité méthodologique** : `POST /audit` prouve que les banques held-out /
  transfert d'un nœud sont **disjointes de l'enseignement** ; `POST /evaluate`
  **refuse** (HTTP 422) tout item déjà vu en entraînement (détection d'*item
  leakage*).
- **Docker** : `Dockerfile` + `docker-compose.yml` (volume `/data` pour l'état),
  `scripts/smoke_test.sh` (`docker compose up --build` puis le smoke test).

#### Emma comme enseignante réelle (sans casser l'indépendance de l'évaluation)

Un **`TeacherAdapter`** (interface stable) sépare Emma du cerveau. Chaque
feedback est un objet **contrôlé** `StructuredFeedback` — jamais du texte libre
injecté en mémoire :

```
node_id · task_id · observed_answer · correct_answer · hint · error_type · confidence · teach_signal
```

Garanties : (1) `teach_signal` et `correct_answer` viennent de la **vérité
terrain** (`task.grade`), **pas du modèle** — Emma peut formuler un *indice*,
jamais décider du juste/faux, donc elle ne peut ni mal-enseigner ni contaminer ;
(2) le cerveau n'apprend **que** de `teach_signal`, l'indice est journalisé pour
l'humain ; (3) **anti-contamination** — l'évaluation (oracle) ne passe jamais par
un teacher, donc Emma ne voit jamais held-out / transfert / rétention.

Trois modes derrière la même interface : **`StubTeacher`** (déterministe,
hors-ligne, utilisé par tous les tests) · **`LiveTeacher`** (indice via LLM,
**inerte** sans transport injecté, aucune dépendance live dans les tests) ·
**`ScriptedTeacher`** (rejoue une session live **figée en fixture** —
déterministe, comparable au stub). Une session live se journalise intégralement
(prompt → réponse → feedback brut → feedback normalisé → décision → état
avant/après) et se **gèle** (`freeze_session`) pour un replay reproductible.

**État persistant — chemin unique recommandé** : `$SEVO_STATE_DIR` (= `/data`
dans le conteneur, monté sur le volume `sevo-state`). `POST /save` et `/load`
**sans `path`** y écrivent/lisent `brain.json` par défaut. Sauvegarder /
restaurer le volume :

```bash
# enregistrer l'état appris dans le volume
curl -X POST localhost:8000/save -H 'content-type: application/json' -d '{}'
# sauvegarde du volume hors conteneur
docker run --rm -v sevo-state:/data -v "$PWD":/backup busybox \
  tar czf /backup/sevo-state.tgz -C /data .
# restauration
docker run --rm -v sevo-state:/data -v "$PWD":/backup busybox \
  tar xzf /backup/sevo-state.tgz -C /data
curl -X POST localhost:8000/load -H 'content-type: application/json' -d '{}'
```

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
  curriculum/  # base · cp_ce1_math · cp_maths_numeration · fr_cp_ce1 · fr_conjugation · fr_lecture_cp · fr_lexicon · official_curriculum · ingestion
  teacher/     # adapter (TeacherAdapter/Structured/Stub/Scripted/Live) · journal · emma_session · emma_stub · emma_litellm
  eval/        # protocole + Intelligence_delta + integrity + state_diff + leakage (item-leakage)
  persistence.py # enveloppe runtime versionnée + migrations (0.4 → 0.5)
  brain.py     # orchestrateur + surface API + export_state/from_state (persistance)
  runtime.py   # BrainService : cerveau persistant (sessions, compteurs, audit, save/load)
  curriculum/factory.py  # build_task(node_id, content) — pont JSON → Task
  api.py       # adaptateur HTTP FastAPI (optionnel) sur BrainService
Dockerfile · docker-compose.yml · scripts/smoke_test.sh   # service durable
scripts/demo_cp.py · Makefile (make demo-cp)              # preuve fondatrice reproductible
docs/CP_PROTOCOL.md · demo/artifacts/ · demo/artifacts_ce1/  # protocole gelé + preuves CP & CE1
experiments/   # run_cp_ce1_math · run_fr_cp_ce1 · run_fr_conjugation · run_cp_grade · run_emma_live · generate_report
tests/         # 165 tests : design + maths + français + lexique + curriculum officiel (CP+CE1) + intégrité + state-diff + persistance + runtime + migrations + sessions + observabilité/leakage + teacher-adapter + API HTTP + CP/CE1-protocol-freeze + développemental
scripts/developmental.py · reports/DEVELOPMENTAL_REPORT.md · demo/developmental/  # étude CP→CE1
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

- **Fait** : MVP **multi-domaines** (maths calcul + numération, pluriel,
  conjugaison, **lecture/décodage, syllabes, dictée**) ; **CP durci** — 9 nœuds
  enseignés via la **boucle API Emma**, **diff d'état observable**
  `Brain CP-naïf → Brain CP-appris` (concepts/règles/compétences/misconceptions/
  rétention) + matrice de maîtrise par compétence ; **garde-fou anti-illusion**
  sur chaque delta ; lexique structuré ; Emma déterministe **et** live prouvées.
- **Runtime durci** : le cerveau CP-appris est un **microservice durable** —
  state schema versionné + migrations, sessions persistantes à replay
  déterministe, observabilité (`/health`, `/metrics`), détection d'item-leakage
  (`/audit`, `/evaluate` refuse les items vus), prêt Docker.
- **Emma réelle** : `TeacherAdapter` stable (stub / live LLM inerte / scripted),
  feedback **structuré** (jamais de texte libre en mémoire), session journalisée
  et **gelable** en fixture reproductible, garde anti-contamination (Emma ne voit
  jamais les probes d'évaluation).
- **Preuve fondatrice** : `make demo-cp` rejoue tout le cycle CP et écrit six
  artefacts ; protocole CP **gelé** (`docs/CP_PROTOCOL.md`) + garde de
  non-régression. C'est le socle scientifique avant toute montée en classe.
- **CE1 (extension)** : `register_class("CE1")` + `make demo-ce1` — le même
  cerveau traverse une 2ᵉ classe (pluriel, conjugaison, calcul < 100), GENUINE,
  six artefacts comparables au CP, protocole gelé respecté (aucune réécriture).
- **Trajectoire développementale** : `make demo-developmental` mesure si un
  cerveau CP-appris apprend CE1 mieux/plus vite qu'un naïf — transfert réel et
  localisé (fort sur l'arithmétique partagée, nul sur le français).
- **CE2 + courbe** : `register_class("CE2")` (add/sub < 1000) ; la courbe
  naïf→CP→CE1→CE2 montre que chaque classe **débloque la suivante en comblant la
  compétence-goulot** (`make demo-developmental-curve`).
- **Lexique** : ressource lexicale **sous garde provenance/licence**
  (`docs/LEXICON.md`) — refuse tout dump opaque/non licencié ; lemmes, fréquence,
  formes fléchies, niveau, splits **train/held-out/transfer**. Seed amorce
  embarqué ; une vraie ressource (Manulex/Dubois-Buyse) se branche via
  `load_external` sous la même garde (données jamais committées).
- **Génération live d'exercices par Emma** (`teacher/live_exercises.py`) sous
  contrat strict, vérifié par code : Emma génère des **items d'entraînement
  uniquement**, la **vérité terrain vient du curriculum** (jamais du modèle), et
  un **garde anti-leakage** refuse tout item dont l'identité collisionne avec les
  probes (held-out/transfert). Inerte par défaut.
- **Ensuite** : CE2… via le même `register_class` ; brancher le lexique sur la
  **ressource réelle complète** (Manulex / Dubois-Buyse) ; ajouter la **fluence**
  et la compréhension de consignes ; génération live d'exercices (mêmes gardes).

## Provenance & licence

Conception issue de la spécification *Human Brain API School v0.3*
(`design/SPEC.md`). Inspirations scientifiques (CLS hippocampe/néocortex,
mémoire sémantique, cadre PISA) listées dans `design/sources.json`.

Licence **Apache-2.0** — voir [`LICENSE`](LICENSE).
