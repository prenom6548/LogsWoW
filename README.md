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

**La marche à suivre pas à pas, pour Windows, Linux (dont Linux Mint) et
macOS, est dans [`INSTALL.md`](INSTALL.md).** Chaque version publiée
fournit un fichier unique, `logswow-<version>.pyz`, qui se lance tel quel :
`python3 logswow-0.2.0.pyz report WoWCombatLog.txt`.

Rien à installer. Python 3.8 ou plus récent, et c'est tout : pas de
`pip install`, aucune dépendance, aucun réseau. Le paquet se copie ou se
clone, il ne s'installe pas ; il n'a donc volontairement ni
`pyproject.toml` ni `setup.py`. Les tests passent de Python 3.8 à 3.13 ;
préférez une version encore maintenue (3.10 ou plus récente en 2026), les
plus anciennes ne reçoivent plus de correctifs de sécurité.

Côté jeu, deux réglages, à faire une fois :

1. **Journalisation avancée** — Système → Réseau → « Journalisation de
   combat avancée ». Elle reste active d'une session à l'autre. C'est
   elle qui ajoute les positions, les points de vie et les ressources.
2. **`/combatlog`** dans le chat pour démarrer l'enregistrement. Celle-ci
   ne persiste pas : il faut la retaper à chaque session, ou installer un
   petit addon qui le fait en entrant en instance.

Le fichier se trouve sous `_retail_\Logs\`. Sous Linux, il est dans la
copie du disque C que garde votre lanceur (Lutris, Steam avec Proton,
Bottles, Wine). Pour le retrouver :

```
python3 -m logswow where
```

## Les quatre commandes

| Commande | Ce qu'elle fait |
|---|---|
| `report FICHIER` | écrit la page HTML complète |
| | `-o` le nom du fichier, `--only` un seul combat, `--pull-gap` le découpage des pulls, `--wowhead` la langue des liens, `--force` pour écraser un fichier qui n'est pas un rapport |
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
  contient apparaissent tous les deux. Une rencontre que le jeu ouvre et
  referme sans qu'aucun coup n'y soit porté est dite « sans combat » et
  n'est pas comptée comme un échec.
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
  contient un boss le nomme en premier, porte un badge qui dit l'issue
  de la rencontre (réussite en vert, échec en rouge), et sépare **les
  dégâts sur le boss de ceux sur les trash** ramenés avec lui. Les bornes
  d'une rencontre viennent du journal lui-même : une rencontre dont aucune
  unité ne porte le nom (un conseil, un duo) compte sur le boss tous les
  dégâts infligés pendant sa durée, et la page le dit. Un pull se termine
  après six secondes sans dégâts de part ni d'autre, sauf à l'intérieur
  d'une rencontre de boss, qui reste toujours un seul pull ; `--pull-gap`
  change ce seuil si votre groupe enchaîne les packs.
- **Dégâts et soins** par joueur, avec le DPS, le HPS et la part de soin
  perdue en surguérison. Les **boucliers** ont leur propre colonne : ce
  qu'ils ont absorbé n'est pas un soin dans le journal, puisqu'ils
  empêchent des dégâts au lieu d'en rendre. La colonne « Somme »
  additionne les deux — c'est ce total-là que les sites en ligne
  appellent « soins ».
- **Les sorts lancés** comptent aussi ceux des invocations, indiqués à
  part. Un sort déclenché tout seul (une procédure passive) est écrit
  dans le journal exactement comme un sort lancé à la main : les
  distinguer demanderait une liste de sorts à maintenir, donc ils sont
  tous comptés. C'est pourquoi ce nombre est plus élevé que celui d'un
  site en ligne.
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
- **Il ne calcule pas de pourcentage de mitigation.** Le journal
  n'écrit nulle part ce qu'un coup aurait fait *avant* l'armure et les
  réductions de dégâts. Le second nombre de chaque coup ressemble à ça
  et n'en est pas un : mesuré sur une vraie clé, il vaut 1,03 fois le
  coup encaissé sur un coup normal et 2,59 fois sur un critique — c'est
  le montant avant le multiplicateur de critique. En diviser l'un par
  l'autre donne un pourcentage crédible et faux. Ce qui est réellement
  dans le fichier, et qui est affiché, ce sont les **dégâts absorbés**
  par les boucliers.
- **Il ne juge pas votre rotation.** Il montre vos pauses, vos capacités
  et vos effets actifs. Dire « il fallait appuyer sur ceci » demande les
  règles de votre spécialisation, écrites et maintenues par quelqu'un qui
  la joue.

Ces limites sont structurelles, pas des fonctions manquantes.

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
de **tout le groupe**, pas seulement les vôtres. **Le rapport HTML aussi** :
sans les royaumes, mais avec le nom court, les dégâts, les soins et les
morts de chacun. Ne le partagez qu'avec l'accord de ceux qu'il nomme,
comme vous le feriez pour le journal lui-même.

`report` refuse d'écrire par-dessus un fichier existant qui n'est pas un
rapport LogsWoW (un autre journal, par exemple), sauf avec `--force`, et
n'écrit jamais par-dessus le journal qu'il lit, même avec `--force`.

## Tests, et vérifier sur un vrai journal

```
python3 tests/run-tests.py
python3 tools/check-invariants.py WoWCombatLog.txt
ln -s ../../tools/pre-push .git/hooks/pre-push     # une fois, pour les contributeurs
```

Les tests, 165, tournent sans dépendance ni réseau sur
`examples/exemple-combat.txt`, un journal **fabriqué** pour ce dépôt :
aucun vrai journal n'y est versé, précisément à cause du rappel ci-dessus.

Le second script prend un **vrai** journal et vérifie que les comptes
tiennent ensemble : les dégâts du groupe valent la somme de ceux des
joueurs, ceux d'un joueur la somme de ses sorts, ceux d'un sort la somme
sur ses cibles ; les soins de même ; les morts comptées trois fois
donnent le même nombre ; aucune durée d'effet ne dépasse le combat ; les
incantations ennemies commencées valent la somme de leurs issues. Il a
trouvé un bug à sa première exécution. Il ne dit pas si un chiffre est
vrai, seulement si les chiffres sont cohérents entre eux. Il vérifie tout
le fichier même après un premier échec, et fait le bilan à la fin.

Rien ne tourne en ligne à chaque envoi : le hook `tools/pre-push` rejoue
ces vérifications sur votre machine avant chaque envoi. Seule la
**publication d'une version** passe par une action GitHub
(`.github/workflows/release.yml`), déclenchée soit par le bouton « Run
workflow » de l'onglet Actions (sur `main`), soit par une étiquette
`v0.2.0` poussée depuis une copie du dépôt : elle relance les tests, vérifie que l'étiquette est bien la version du
paquet, fabrique le `.pyz` et son empreinte `SHA256SUMS`, et publie le tout
avec les notes de la version. Elle n'utilise que ce que la machine de
GitHub possède déjà, sans aucune action tierce.

Ce qui change d'une version à l'autre est dans
[`CHANGELOG.md`](CHANGELOG.md) ; le détail technique, daté et chiffré, dans
les sections datées de `CLAUDE.md`.

Le journal est lu tel que le jeu l'écrit, avec ses fins de ligne
Windows, sous Linux comme sous Windows.

## Licence

GPLv3. Tout le monde peut utiliser, modifier et redistribuer ;
quiconque distribue une version, modifiée ou non, doit en fournir le code
source sous la même licence. Voir `LICENSE` et `PROVENANCE.md`.
