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
| `report FICHIER` | écrit la page HTML complète |
| | `-o` le nom du fichier, `--only` un seul combat, `--pull-gap` le découpage des pulls, `--wowhead` la langue des liens |
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
- **La composition du groupe**, tanks, soigneurs et DPS, avec la classe
  et la spécialisation de chacun. Elles viennent de ce que le client
  écrit au début du combat ; une spécialisation inconnue de l'outil est
  affichée par son numéro plutôt que devinée.
- **Une frise** des dégâts subis par le groupe seconde par seconde, avec
  une échelle chiffrée à gauche et les morts en rouge. En courbe, sur un
  pull de boss, la vie du boss (nommé sous le graphique) ; dans une clé,
  **la vie cumulée de tout ce qui est engagé**, somme des points de vie
  courants sur la somme des maximums, qui remonte à chaque pack et
  retombe quand il meurt.
- **La liste des pulls** dès qu'un combat en contient plusieurs, ce qui
  est le cas de toute clé mythique : heure de début, durée, ce qui a été
  engagé et en quel nombre, dégâts infligés, subis, morts. Un pull qui
  contient un boss le nomme en premier et sépare **les dégâts sur le
  boss de ceux sur les trash** ramenés avec lui. Un pull se termine après
  six secondes sans dégâts de part ni d'autre ; `--pull-gap` change ce
  seuil si votre groupe enchaîne les packs.
- **Dégâts et soins** par joueur, avec le DPS, le HPS et la part de soin
  perdue en surguérison. Le panneau de chaque joueur indique aussi ce que
  ses boucliers ont **absorbé**.
- **Les dégâts que le fichier n'attribue à personne**, quand il y en a :
  une créature alliée dont le journal ne nomme jamais le maître ne peut
  être rattachée à aucun joueur. Ils sont laissés hors du total, et un
  encadré le dit, avec leur nom et leur montant — un total silencieusement
  incomplet serait pire.
- **Ce qui a fait mal au groupe** : chaque capacité ennemie, combien elle
  a coûté, combien de joueurs elle a touchés.
- **Les morts**, chacune avec la chaîne des derniers coups et soins reçus
  avant la fin, et le pourcentage de vie restant à chaque étape.
- **Ce que le groupe a empêché** : combien de sorts l'ennemi a commencés,
  combien ont abouti, combien ont été coupés par une interruption, et
  combien ont fini parce que le lanceur est mort.
- **Par joueur**, en dépliant son nom : pour chaque sort, le total, la
  part, le nombre de lancers, le nombre de coups, la moyenne, le taux de
  critique, le débit par seconde et la principale cible. Puis ses soins
  avec leur surguérison et sur qui ils sont allés, ce qu'il a pris et de
  qui, les gains reçus **avec qui les lui a donnés**, les affaiblissements
  subis, ce qu'il a lui-même appliqué et sur qui, ses interruptions et
  dissipations avec le nom de ce qui a été coupé, et ses plus longues
  pauses sans lancer de sort.
- **Par ennemi**, de la même façon : les unités portant le même nom sont
  regroupées, avec ce qu'elles infligent et à qui, ce qu'elles ont subi
  et de qui, les sorts qu'elles ont lancés, et combien ont été tuées.
- **Les noms de sorts sont des liens vers Wowhead**, dans la langue de
  votre machine. `--wowhead fr` force une langue, `--wowhead off` retire
  les liens. Rien n'est chargé à l'ouverture : un lien n'est suivi que si
  vous cliquez dessus.

Une soirée entière fait une page de plusieurs mégaoctets. Pour n'en
regarder qu'un morceau :

```
python3 -m logswow list WoWCombatLog.txt          # voir les combats
python3 -m logswow report WoWCombatLog.txt --only 5
python3 -m logswow report WoWCombatLog.txt --only "Allée du meurtre"
```

## Ce qu'il ne fait pas, et pourquoi

- **Il ne vous compare à personne.** Un percentile demande les journaux
  de tous les autres joueurs. C'est exactement la chose qu'un outil local
  sur votre machine n'a pas, et c'est le seul vrai service que rend un
  site centralisé.
- **Il ne dit pas si un coup était évitable.** Le fichier dit qui a été
  touché et combien ; savoir que tel dégât venait d'une zone au sol
  demande de connaître le boss. Cet outil ne prétend pas le savoir.
- **Il ne sait pas ce qu'est un contrôle.** Le journal n'écrit nulle part
  qu'un sort est un étourdissement ou une peur. Un sort ennemi qui
  s'arrête sans interruption et sans mort du lanceur est donc rangé sous
  « cause non dite par le journal ». Distinguer un contrôle d'un simple
  affaiblissement demanderait une liste de sorts à maintenir.
- **Il ne juge pas votre rotation.** Il montre vos pauses, vos capacités
  et vos effets actifs. Dire « il fallait appuyer sur ceci » demande les
  règles de votre spécialisation, écrites et maintenues par quelqu'un qui
  la joue.

Ces trois limites sont structurelles, pas des fonctions manquantes.

## Où sont vos données

Sur votre disque, et nulle part ailleurs. Le programme ouvre un fichier,
écrit un fichier, et se termine. Il n'ouvre aucune connexion réseau, ne
lit aucune configuration, n'écrit aucun cache et ne connaît aucun compte.
La page produite ne charge rien à l'ouverture : le test
`test_writes_a_self_contained_page` échoue si un `<script>`, une feuille
de style, un `src=`, un `@import` ou un `url(` s'y glisse, et si une
adresse autre que Wowhead y apparaît. Les liens Wowhead, eux, ne sont
suivis que si vous cliquez dessus.

Le rapport, lui, n'écrit jamais le **royaume** d'un joueur : les noms y
apparaissent sous leur forme courte, dans les tableaux comme dans les
chaînes de mort. Une capture d'écran du rapport identifie donc moins
qu'une capture du journal.

Rappel utile : un journal de combat contient le nom et les performances
de **tout le groupe**, pas seulement les vôtres.

## Tests, et vérifier sur un vrai journal

```
python3 tests/run-tests.py
python3 tools/check-invariants.py WoWCombatLog.txt
```

Les tests, 138, tournent sans dépendance ni réseau sur
`examples/exemple-combat.txt`, un journal **fabriqué** pour ce dépôt :
aucun vrai journal n'y est versé, précisément à cause du rappel ci-dessus.

Le second script prend un **vrai** journal et vérifie que les comptes
tiennent ensemble : les dégâts du groupe valent la somme de ceux des
joueurs, ceux d'un joueur la somme de ses sorts, ceux d'un sort la somme
sur ses cibles ; les soins de même ; les morts comptées trois fois
donnent le même nombre ; aucune durée d'effet ne dépasse le combat ; les
incantations ennemies commencées valent la somme de leurs issues. Il a
trouvé un bug à sa première exécution. Il ne dit pas si un chiffre est
vrai, seulement si les chiffres sont cohérents entre eux.

Le journal est lu tel que le jeu l'écrit, avec ses fins de ligne
Windows, sous Linux comme sous Windows.

## Licence

GPLv3. Tout le monde peut modifier et redistribuer ; les versions
fermées sont formellement interdites. Voir `LICENSE` et `PROVENANCE.md`.
