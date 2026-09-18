# LogsWoW

Lire ses propres journaux de combat de World of Warcraft, **sur sa
machine**, sans compte, sans envoi, sans connexion.

Le jeu écrit lui-même un fichier, `WoWCombatLog.txt`, qui contient tout
ce qui s'est passé pendant un combat. Les sites d'analyse en ligne lisent
ce fichier après l'avoir reçu. LogsWoW le lit là où il est.

```
python3 -m logswow report "/chemin/vers/WoWCombatLog.txt"
```

Une page HTML apparaît à côté du fichier. Elle s'ouvre hors ligne, elle
ne charge rien depuis nulle part, et elle ne contient aucun script.

## Ce qu'il faut avant

Rien à installer. Python 3.8 ou plus récent, et c'est tout : pas de
`pip install`, aucune dépendance, aucun réseau.

Côté jeu, deux réglages, à faire une fois :

1. **Journalisation avancée** — Système → Réseau → « Journalisation de
   combat avancée ». Elle reste active d'une session à l'autre. C'est
   elle qui ajoute les positions, les points de vie et les ressources.
2. **`/combatlog`** dans le chat pour démarrer l'enregistrement. Celle-ci
   ne persiste pas : il faut la retaper à chaque session, ou installer un
   petit addon qui le fait en entrant en instance.

Le fichier se trouve sous `_retail_\Logs\`. Pour le retrouver :

```
python3 -m logswow where
```

## Les quatre commandes

| Commande | Ce qu'elle fait |
|---|---|
| `report FICHIER` | écrit la page HTML complète (`-o` pour le nom, `--pull-gap` pour le découpage des pulls) |
| `list FICHIER` | liste les combats du fichier, une ligne chacun |
| `diagnose FICHIER` | montre ce que le lecteur a compris, et ce qu'il n'a pas compris |
| `where` | cherche le dossier `Logs` du jeu |

**Lancez `diagnose` en premier** après chaque mise à jour du jeu. Il
affiche la disposition des champs telle qu'elle a été *mesurée dans
votre fichier*, la liste des événements rencontrés, et chaque ligne qu'il
n'a pas su placer. Un rapport de combat confiant tiré d'un fichier mal
lu serait pire que pas de rapport du tout.

## Ce que le rapport contient

- **Les combats** : chaque pull de boss et chaque clé mythique, avec sa
  durée, son issue, et le nombre de morts. Une clé et les boss qu'elle
  contient apparaissent tous les deux.
- **Une frise** des dégâts subis par le groupe seconde par seconde, avec
  une échelle chiffrée à gauche, les morts en rouge, et en courbe la vie
  de la cible la plus frappée, **nommée** sous le graphique. Sur un pull
  de boss c'est le boss ; dans une clé c'est l'unité qui a encaissé le
  plus, et le journal ne donne pas toujours la vie du boss lui-même.
- **La liste des pulls** dès qu'un combat en contient plusieurs, ce qui
  est le cas de toute clé mythique : heure de début, durée, ce qui a été
  engagé et en quel nombre, dégâts infligés et subis, morts. Un pull se
  termine après six secondes sans dégâts de part ni d'autre ;
  `--pull-gap` change ce seuil si votre groupe enchaîne les packs.
- **Dégâts et soins** par joueur, avec le DPS, le HPS et la part de soin
  perdue en surguérison.
- **Ce qui a fait mal au groupe** : chaque capacité ennemie, combien elle
  a coûté, combien de joueurs elle a touchés.
- **Les morts**, chacune avec la chaîne des derniers coups et soins reçus
  avant la fin, et le pourcentage de vie restant à chaque étape.
- **Par joueur** : ses capacités, ce qu'il a pris, la durée de ses effets
  actifs, sa vie la plus basse, et ses plus longues pauses sans lancer
  de sort.

## Ce qu'il ne fait pas, et pourquoi

- **Il ne vous compare à personne.** Un percentile demande les journaux
  de tous les autres joueurs. C'est exactement la chose qu'un outil local
  sur votre machine n'a pas, et c'est le seul vrai service que rend un
  site centralisé.
- **Il ne dit pas si un coup était évitable.** Le fichier dit qui a été
  touché et combien ; savoir que tel dégât venait d'une zone au sol
  demande de connaître le boss. Cet outil ne prétend pas le savoir.
- **Il ne juge pas votre rotation.** Il montre vos pauses, vos capacités
  et vos effets actifs. Dire « il fallait appuyer sur ceci » demande les
  règles de votre spécialisation, écrites et maintenues par quelqu'un qui
  la joue.

Ces trois limites sont structurelles, pas des fonctions manquantes.

## Où sont vos données

Sur votre disque, et nulle part ailleurs. Le programme ouvre un fichier,
écrit un fichier, et se termine. Il n'ouvre aucune connexion réseau, ne
lit aucune configuration, n'écrit aucun cache et ne connaît aucun compte.
La page produite ne référence aucune URL : le test `test_writes_a_self_contained_page`
échoue si jamais un `http` s'y glisse.

Rappel utile : un journal de combat contient le nom et les performances
de **tout le groupe**, pas seulement les vôtres.

## Tests

```
python3 tests/run-tests.py
```

56 tests, sans dépendance ni réseau. Ils tournent sur
`examples/exemple-combat.txt`, un journal **fabriqué** pour ce dépôt :
aucun vrai journal n'y est versé, précisément à cause du rappel ci-dessus.

## Licence

GPLv3. Tout le monde peut modifier et redistribuer ; les versions
fermées sont formellement interdites. Voir `LICENSE` et `PROVENANCE.md`.
