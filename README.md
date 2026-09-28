# LogsWoW

Lire ses propres journaux de combat de World of Warcraft, **sur sa
machine**, sans compte, sans envoi, sans connexion.

Le jeu écrit lui-même un fichier, `WoWCombatLog.txt`, qui contient tout
ce qui s'est passé pendant un combat. Les sites d'analyse en ligne lisent
ce fichier après l'avoir reçu. LogsWoW le lit là où il est.

Lancé sans rien d'autre — un double-clic sur le fichier, ou
`python3 logswow-<version>.pyz` — il ouvre **une fenêtre** : on choisit un
journal dans la liste de ceux qu'il a trouvés, on coche les combats, et le
rapport s'ouvre dans le navigateur. Les mêmes étapes existent en commandes,
pour qui préfère le terminal :

```
python3 -m logswow report "/chemin/vers/WoWCombatLog.txt"
```

Une page HTML apparaît à côté du fichier. Elle s'ouvre hors ligne, elle
ne charge rien depuis nulle part, et elle ne contient aucun script.

Trois présentations au choix, dans la fenêtre ou avec `--format` :
**onglets** (par défaut : un fichier, la liste des combats à gauche et
des onglets par rubrique), **pages** (un dossier, une page par combat)
ou **longue** (tout sur une seule page).

La fenêtre utilise Tkinter, la boîte à outils graphique fournie avec
Python. Sous Windows et avec l'installateur macOS de python.org, elle est
déjà là ; sous Linux Mint, Ubuntu et Debian, elle s'installe une fois avec
`sudo apt install python3-tk` (la fenêtre le dit elle-même si elle
manque). Les commandes n'en ont pas besoin.

## Ce qu'il faut avant

**La marche à suivre pas à pas, pour Windows, Linux (dont Linux Mint) et
macOS, est dans [`INSTALL.md`](INSTALL.md).** Chaque version publiée
fournit un fichier unique, `logswow-<version>.pyz`, qui se lance tel quel :
`python3 logswow-0.8.1.pyz report WoWCombatLog.txt`.

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

## Les commandes

| Commande | Ce qu'elle fait |
|---|---|
| *(aucune)* ou `fenetre` | ouvre la fenêtre |
| `report FICHIER` | écrit la page HTML complète |
| | `--format onglets\|pages\|longue` la présentation, `-o` le nom du fichier (ou du dossier pour `pages`), `--only` un seul combat, `--pull-gap` le découpage des pulls, `--wowhead` la langue des liens, `--sans-sequence` sans l'ordre des sorts, `--force` pour écraser un fichier qui n'est pas un rapport |
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
  appellent « soins ». Les dégâts comptent ce que chaque coup a
  réellement retiré : pas l'excédent d'un coup fatal, mais bien ce qu'un
  bouclier ennemi a mangé. Les soins comptent ce qu'un affaiblissement
  « absorbe-soins » a mangé, et le Lien d'esprit, qui déplace de la vie
  d'un joueur à l'autre, n'est ni un soin ni un dégât subi.
- **Comparé à Warcraft Logs** sur cinq clés, joueur par joueur : mêmes
  morts pour tous, mêmes dégâts à moins de 0,1 % (au point près pour la
  moitié des joueurs), mêmes soins au point près pour 17 joueurs sur 25.
  Les écarts restants ont une cause connue, écrite dans `CHANGELOG.md`.
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
- **La part d'un Évocateur Augmentation** : le journal attribue à ses
  renforts (Puissance d'ébène, Prescience…) une part des coups des autres
  joueurs, et à lui les Bombardements qu'un allié déclenche. Ces montants
  sont déjà dans les dégâts de ceux qui ont porté les coups : ils sont
  montrés à part sur le panneau de l'Évocateur, jamais ajoutés une
  seconde fois. Warcraft Logs, lui, les déplace vers l'Évocateur, d'où un
  écart entre les deux pour les joueurs renforcés.
- **Physique ou magique** : la part des dégâts subis et infligés qui
  était physique, magique ou les deux, en pourcentage, sur tout le combat
  puis pull par pull, avec le détail par école (Ombre, Feu, Nature…).
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
- **L'ordre des sorts, pull par pull**, en bas du panneau de chaque
  joueur : chaque sort lancé, dans l'ordre, sous forme de pastille de
  couleur fixe portant ses deux premières lettres. Le survol donne son nom
  et l'instant où il a été lancé, un clic ouvre Wowhead. La légende sert
  de filtre : un clic sur un sort masque ou réaffiche toutes ses
  pastilles, sans aucun script dans la page. Les sorts de ses invocations
  sont à part, en pastilles rondes. Ceux que le jeu déclenche tout seul
  sont écrits dans le journal exactement comme un sort appuyé ; ceux qui
  en ont les marques (jamais payés, et lancés en même temps qu'un sort
  payé, ou plus vite qu'aucun bouton, ou second exemplaire d'un sort que
  le journal écrit deux fois sous le même nom) sont regroupés à part et
  masqués au départ, et un clic les réaffiche. `--sans-sequence` retire cette section, pour une
  page environ deux fois plus légère.
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

Les tests, 228, tournent sans dépendance ni réseau sur
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

Licence publique générale GNU Affero, **version 3 ou (à votre choix)
toute version ultérieure** (AGPL-3.0-or-later), depuis la version 0.8.0.
Tout le monde peut utiliser, modifier et redistribuer ; quiconque
distribue une version, modifiée ou non, doit en fournir le code source
sous la même licence. L'AGPL ajoute un point à la GPL : **quiconque fait
tourner une version modifiée comme service en ligne** (un site qui lirait
vos journaux, par exemple) doit aussi en proposer le code source à ceux
qui s'en servent. Pour vous, qui l'utilisez sur votre machine, rien ne
change. Depuis le 28 septembre 2026, les versions antérieures (0.1.0 à
0.7.0) sont elles aussi distribuées sous AGPL-3.0-or-later ; qui en avait
déjà une copie garde, pour cette copie, les droits de la GPL sous
laquelle elle a été reçue, que la GPL déclare irrévocables. Voir `LICENSE`
et `PROVENANCE.md`.
