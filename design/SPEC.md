# Human Brain API School v0.3

Cette V0.3 modélise un **cerveau artificiel persistant**, pas un simple agent éducatif.

## Idée centrale

- Le cerveau est un système interne exposé par API.
- Emma est un professeur externe qui interagit avec lui.
- Le programme scolaire français est un environnement/curriculum injecté.
- L'apprentissage modifie l'état du cerveau.
- Après chaque classe, on compare deux snapshots cognitifs.

## Ordre de lecture

1. `manifest.json`
2. `brain_services.json`
3. `api_surface.json`
4. `learning_lifecycle.json`
5. `evaluation_protocol.json`
6. `brain_state_schema.json`
7. `docker_compose_blueprint.json`

## Formule produit

> Brain_before + Emma + Curriculum(class_N) + consolidation = Brain_after  
> Intelligence_delta = evaluation(Brain_after) - evaluation(Brain_before)

## Différence clé

Le curriculum n'est PAS la mémoire.  
La mémoire est ce que le cerveau a réellement incorporé après perception, attention, exercice, feedback et consolidation.

## MVP conseillé

Commencer par CP/CE1 mathématiques + français, car cela permet de tester :
- symboles,
- langage,
- numération,
- procédures,
- correction d'erreurs,
- transfert simple,
- rétention différée.
