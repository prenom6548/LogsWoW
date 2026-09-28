# Journal des versions

Chaque version publiée, ce qui y a changé pour qui s'en sert. Le détail
technique, daté et chiffré, est dans les sections datées de `CLAUDE.md`.

## 0.8.0 — 2026-09-28

**Un audit complet, et une licence qui protège aussi contre les services
en ligne.**

La licence devient l'**AGPL-3.0 ou ultérieure** (elle était la GPL-3.0
ou ultérieure). Pour vous, qui lancez LogsWoW sur votre machine, rien ne
change. La différence vise qui voudrait en faire un site : quiconque
fait tourner une version modifiée comme service en ligne doit désormais
en proposer le code source à ceux qui s'en servent. Les versions
antérieures (0.1.0 à 0.7.0) sont elles aussi distribuées sous AGPL depuis
aujourd'hui. Qui en avait déjà une copie garde les droits de la GPL pour
cette copie, parce que la GPL les déclare irrévocables. Chaque fichier
source porte désormais sa licence en première ligne, et le pied du
rapport indique où trouver le code.

Ce que l'audit a trouvé dans le rapport, vérifié sur vos vrais journaux :

- **Des lignes disparaissaient sans le dire.**
  - Le classement s'arrêtait à 20 joueurs : sur une rencontre héroïque
    à 21, le vingt et unième manquait.
  - La liste des morts s'arrêtait à 24, ce qu'un wipe de raid dépasse.
  - Les panneaux s'arrêtaient à 30 joueurs.
  - Les cibles d'un soigneur s'arrêtaient à 20 : un soigneur de raid en
    avait 36.

  Tout est affiché maintenant. Les cibles au-delà de la vingtième se
  déplient sous le tableau, avec leur total.
- **Une mort instantanée n'avait pas de cause.** Quand le jeu tue un
  joueur d'un coup (le journal l'écrit sans montant), le récapitulatif
  de la mort ne nommait aucun coup fatal. Sur une soirée de raid, c'était
  le cas de 3 des 5 morts restées sans cause. Le sort est nommé désormais, avec
  la mention « mort instantanée ». Quand le journal n'écrit vraiment
  aucune cause, le rapport le dit au lieu de laisser la case vide.
- **Les coups d'un allié sans propriétaire dans un bouclier ennemi**
  rejoignent les autres dégâts non attribués, au lieu de disparaître.
- **La fenêtre** ne laisse plus ouvrir un second journal pendant qu'un
  premier se lit ou qu'un rapport s'écrit. Le rapport s'écrit toujours
  à partir du journal dont les combats ont été choisis.
- La note sur les dégâts physiques et magiques dit précisément ce qu'elle
  compte, dans les mêmes termes que le reste du rapport.

Aucun total de dégâts, de soins ou de morts n'a changé : l'audit a
comparé tous les chiffres de trois vrais journaux avant et après.

## 0.7.0 — 2026-09-28

**Les chiffres concordent avec Warcraft Logs.** Cinq de vos clés ont été
comparées joueur par joueur avec ce qu'en dit Warcraft Logs, puis coup
par coup là où ça ne tombait pas juste. Chaque écart a trouvé sa cause.
Sur ces cinq clés, maintenant :

- **les morts** : identiques pour les 25 joueurs ;
- **les dégâts infligés** : identiques à l'unité pour 13 joueurs sur 25,
  à moins de 0,1 % pour tous ;
- **les soins** (soins + boucliers) : identiques à l'unité pour 17
  joueurs sur 25 ;
- **les dégâts subis** (avec la part absorbée) : identiques ou à moins
  de 0,1 % pour 18 joueurs sur 25.

Ce qui a changé :

- **Soins mangés par un affaiblissement : ils étaient perdus en entier.**
  Quand un affaiblissement « absorbe les prochains soins », le journal
  écrit la part mangée *à côté* du soin. LogsWoW la retirait du soin
  lui-même, qui tombait souvent à zéro. Ces soins comptent désormais,
  et la part mangée aussi : c'est un travail de soigneur. Sur l'Autel des
  crochets, 12,7 M de soins manquaient, et chaque soigneur y était 1 à 4 %
  sous Warcraft Logs.
- **La mêlée reçue était sous-comptée**, jusqu'à 12 % sur un tank. Le
  jeu écrit beaucoup de coups de mêlée reçus sous une seule des deux
  formes qu'il utilise ; c'est désormais celle-là qui est lue.
- **Les dégâts dans les boucliers ennemis comptent** comme dégâts
  infligés : un coup mangé par le bouclier d'un ennemi a été porté. Ils
  manquaient (0,5 à 1,6 % des dégâts d'une clé).
- **Les dégâts « en trop » sur un coup fatal ne comptent plus**, comme
  les soins en trop ne comptent pas : un coup de 485 000 sur une cible à
  qui il restait 203 000 points de vie en a infligé 203 000.
- **La Tombe glaciale** (Antre de Nalorakk) est une cible que le groupe
  doit briser, que le jeu fait « invoquer » par le joueur qu'elle
  enferme. Les coups portés dessus comptaient comme des dégâts subis par
  le groupe ; ce sont désormais des dégâts infligés.
- **Le Lien d'esprit** du chaman ne soigne pas : il prend de la vie aux
  uns pour la donner aux autres. Ce qu'il prend n'est plus compté dans
  les dégâts subis de personne, et est déduit des soins du chaman, comme
  sur Warcraft Logs. Une phrase sous le tableau des soins le dit.
- **Une Feinte de mort n'est plus une mort.** Le journal écrit un
  chasseur qui feint la mort comme mort, avec un drapeau
  « inconscient » ; il ne compte plus.

Il reste deux différences connues, qui sont des choix et non des
erreurs : les soins sur les familiers des autres joueurs, que Warcraft
Logs ne compte pas toujours (jusqu'à 4,6 % pour un chaman), et la part
absorbée des dégâts subis par un démoniste sous Gangrarmure, que le
journal écrit de deux façons qui ne concordent pas.

## 0.6.0 — 2026-09-28

**Trois présentations du rapport, au choix.**

- **Onglets** (nouveau, par défaut) : un seul fichier. La liste des
  combats à gauche ; un clic en affiche un, et ses rubriques sont des
  onglets : Résumé, Dégâts et soins, Physique ou magique, Morts, Joueurs,
  Ennemis. Un onglet vide (aucune mort, par exemple) n'apparaît pas.
- **Pages** (nouveau) : un dossier, avec une page d'accueil
  (`index.html`) et une page par combat, reliées par des liens
  « Tous les combats », « précédent », « suivant ». Plus léger à ouvrir
  pour une grosse soirée ; c'est un dossier à partager plutôt qu'un
  fichier.
- **Une seule longue page** : la présentation d'avant, identique.
- Le choix se fait dans la fenêtre (« Présentation », à l'étape 3) ou en
  ligne de commande : `--format onglets`, `--format pages` ou
  `--format longue`.
- Comme avant, aucune des trois ne contient de script ni ne charge quoi
  que ce soit : les onglets sont faits en CSS seul.
- Un dossier qui contient déjà autre chose qu'un rapport LogsWoW est
  refusé (sauf `--force`), comme l'est un fichier existant.

## 0.5.1 — 2026-09-28

**Corrigé, d'après vos retours sur vos propres rapports.**

- **Les Échos de Nalorakk étaient pris pour des invocations de joueurs.**
  Le boss fait « invoquer » ses Échos par plusieurs joueurs à la fois,
  et le journal l'écrit ainsi ; leurs sorts (« Mutilation des échos »,
  « Entaille spectrale ») apparaissaient dans l'ordre des sorts du
  joueur. Un sort d'invocation qui touche presque toujours plusieurs
  joueurs au même instant est désormais reconnu comme une mécanique de
  la rencontre : ses unités sont rendues au boss, avec leurs sorts et
  leurs coups. Même chose pour les « Orbes gravitationnels » de l'Arène
  de la Cicatrice du Vide. Aucun total de dégâts ou de soins ne change.
- **Un sort pouvait disparaître d'un tableau sans rien dire.** Les
  tableaux s'arrêtaient à 16 lignes ; « Estropier », que le jeu écrit en
  deux lignes (main droite, main gauche), passait dessous. Le reste se
  déplie maintenant sous chaque tableau (« 8 sorts de plus · 5,3 M »).
- **Des joueurs sans rôle dans le combat comptaient dans le groupe.**
  Deux joueurs arrivés pour la clé suivante avaient lancé un buff dans
  les dernières secondes d'une clé ratée : 7 joueurs dans un donjon.
  Ne compte plus que qui a infligé ou subi des dégâts, soigné, protégé
  ou est mort ; les autres sont nommés à part, sous la composition.
- **« 0 pull de boss » pour une clé choisie seule** : les boss vus à
  l'intérieur des combats choisis sont comptés, une fois chacun.
- **« Échecs » devient deux compteurs** : « Wipes de boss » et « Clés
  hors des temps ». Une clé ratée avec un wipe dedans ne se lit plus
  comme un donjon compté deux fois. Une rencontre ouverte et refermée
  sans un coup (un reset volontaire du boss) n'est jamais un wipe.

## 0.5.0 — 2026-09-27

**Physique ou magique, en pourcentage.**

- Chaque combat a une nouvelle section, « Physique ou magique » : la part
  des dégâts **subis** et **infligés** qui était physique, magique, ou les
  deux à la fois (« mixte » : Ombre-frappe, Chaos…), sur tout le combat
  puis **pull par pull**, en barres et en pourcentages qui font toujours
  100 % pile.
- Le détail par école suit : « Subis par école : Physique 36 %, Ombre
  32 %, Nature 22 %… ».
- L'école vient de chaque ligne du journal, qui dit ce que le coup a
  réellement infligé. Vérifié sur vos journaux : tous les coups de mêlée
  sont physiques, et un recompte écrit indépendamment trouve les mêmes
  parts au cent-millième près.

**Corrigé**

- **Une chute s'affichait sous l'identifiant du joueur tombé.** Pour les
  dégâts de l'environnement (chute, lave, noyade), le journal écrit les
  champs dans un ordre différent des autres lignes ; le rapport prenait
  l'identifiant du joueur pour le nom de ce qui l'avait blessé, dans « Ce
  qu'il a pris » et dans le récit de sa mort. C'est « Falling » désormais.
  Les montants, eux, étaient justes.

## 0.4.0 — 2026-09-27

**Une fenêtre, pour ne plus passer par le terminal.**

- Lancé sans rien d'autre — double-clic sur le fichier sous Windows,
  `python3 logswow-0.4.0.pyz` ou une entrée de menu sous Linux — LogsWoW
  ouvre une fenêtre en trois étapes : **le journal** (la liste de ceux
  qu'il a trouvés, du plus récent au plus ancien, ou « Choisir un autre
  fichier… »), **les combats** (tous cochés, ou seulement ceux qu'on
  choisit), **le rapport** (« Créer le rapport et l'ouvrir » l'affiche
  dans le navigateur).
- La lecture d'un gros journal se suit sur une barre de progression, et
  peut s'annuler. La fenêtre reste utilisable pendant ce temps.
- Si le dossier du journal refuse l'écriture, ou si un fichier du même
  nom qui n'est pas un rapport existe déjà, la fenêtre demande où écrire
  la page plutôt que d'écraser quoi que ce soit.
- Un rapport d'un seul combat porte son numéro dans son nom
  (`…-combat-3.html`), pour ne pas remplacer celui de toute la soirée.
- Sous Linux Mint, Ubuntu et Debian, la fenêtre demande une fois
  `sudo apt install python3-tk` ; elle le dit elle-même s'il manque.
  `INSTALL.md` explique comment l'ajouter au menu des applications.
- Les commandes du terminal ne changent pas ; `fenetre` ouvre la fenêtre
  depuis le terminal.

## 0.3.2 — 2026-09-27

- **`where` trouve aussi le jeu installé sur un second disque** : sous
  Linux dans `/mnt`, `/media` et `/run/media`, sous macOS dans `/Volumes`,
  à la racine du disque ou un à deux dossiers plus bas. Jusqu'ici, un jeu
  installé par exemple dans `/mnt/Jeux/World of Warcraft` n'était pas
  trouvé.
- Quand `where` ne trouve rien, il explique comment donner soi-même le
  chemin du journal, entre guillemets.
- La licence est désormais explicite : GPL version 3 **ou toute version
  ultérieure**, dans le README, le code et le pied de chaque rapport.

## 0.3.1 — 2026-09-27

**Mesuré sur seize vrais journaux** — 32,7 millions de lignes, les 40
spécialisations du jeu. Tous se lisent désormais sans une seule ligne
incomprise, et chaque vérification croisée tient sur chacun.

**Corrigé**

- **Des dégâts comptés deux fois quand un Évocateur est dans le
  groupe.** Le journal écrit, en plus de chaque coup, une ligne qui
  attribue une part de ce coup aux renforts d'un Évocateur Augmentation
  (Puissance d'ébène, Prescience…) ou aux Bombardements d'un Évocateur.
  Ces lignes étaient additionnées comme de nouveaux dégâts : jusqu'à
  +15 % pour un joueur, et jusqu'à +3 % pour le groupe sur les combats
  concernés. Même une soirée sans Évocateur Augmentation était touchée,
  par les Bombardements d'un Évocateur Dévastation, et aucun message ne
  le signalait. Un recompte indépendant, écrit sans le programme, tombe
  désormais sur les mêmes totaux (écart médian : 0,00 %).
- **Le panneau de l'Évocateur montre ce que le jeu lui crédite** : une
  tuile « Soutien crédité par le jeu » et le détail par renfort. Ces
  montants restent comptés chez ceux qui ont porté les coups ; Warcraft
  Logs, lui, les leur retire pour les donner à l'Évocateur, d'où un écart
  entre les deux sites pour les joueurs renforcés.
- **Des interruptions fantômes pour les Évocateurs** : relâcher un sort
  à charger avant la fin était lu comme une interruption.
- Les coups de mêlée renforcés par un Évocateur étaient comptés comme
  lignes incomprises (9 793 dans un journal, 3 837 dans un autre) ; ils
  sont lus.

**Ordre des sorts : la reconnaissance des sorts automatiques, revue sur
toutes les classes**

- Un sort que le jeu écrit **deux fois sous le même nom au même
  instant** (Fracture, Gangrelame, Lancer de glaive, Coup de crâne…)
  n'est plus masqué en entier : une seule pastille reste, pour une
  pression.
- Un sort n'est plus lu comme déclenché parce qu'il part avec un autre
  sort gratuit : il faut que ce voisin soit un sort payé. « Fouet mental :
  insanité », qui part toujours avec une « Apparition ténébreuse », est
  de nouveau visible.
- « Infusion de puissance », écrite deux fois d'un coup, n'est plus prise
  pour un sort rapide.
- Les sorts que le jeu lance **plus vite qu'aucun bouton** (un écart
  médian sous la demi-seconde, sans jamais coûter de ressource) sont
  maintenant reconnus : « Fragment d'âme », « Marteau empyréen »,
  « Reconquête ».
- Reste hors de portée : un sort automatique qui part seul, au rythme
  d'un bouton (« Apparition ténébreuse »). Un clic sur la légende le
  masque.

## 0.3.0 — 2026-09-27

**L'ordre des sorts de chaque joueur, pull par pull.**

- En bas du panneau de chaque joueur, chaque sort lancé dans l'ordre,
  regroupé par pull comme sur les sites d'analyse : « Pull 01 — trash
  (9 ennemis) », « Pull 06 — Mchimba l'Embaumeur, échec », avec l'heure
  de début et de fin et le nombre de sorts.
- Chaque sort est une pastille de couleur fixe portant ses deux premières
  lettres. Le survol donne son nom et l'instant du lancer ; un clic ouvre
  sa page Wowhead. Pas d'icônes : elles obligeraient la page à se
  connecter à Internet en s'ouvrant, ce qu'elle ne fait jamais.
- La légende est un filtre : un clic sur un sort masque ou réaffiche
  toutes ses pastilles. La page ne contient toujours aucun script.
- Les sorts des invocations sont à part, en pastilles rondes.
- Les sorts que le jeu déclenche tout seul sont regroupés à part et
  masqués au départ. Le journal les écrit comme un sort appuyé ; ceux qui
  en ont toutes les marques (au moins 8 fois dans le combat, à 80 % en
  même temps qu'un autre sort, sans jamais coûter de ressource, au plus
  toutes les 30 secondes) sont lus comme déclenchés. Mesuré sur deux vrais
  journaux : la règle retrouve exactement les cinq sorts automatiques
  qu'ils contiennent, et aucun sort appuyé, même par une macro. Un clic
  les réaffiche.
- `--sans-sequence` retire cette section : la page d'une soirée de raid
  passe de 8,4 Mo à 4,3 Mo.

**Corrigé**

- Un fichier abîmé dont une ligne de début de rencontre ou de clé, ou le
  nom d'un événement, contenait un crochet arrêtait tout le rapport. La
  ligne est désormais comptée comme incomprise, et le combat garde un nom
  générique.

## 0.2.0 — 2026-09-27

Version issue d'un audit complet, mené sur deux vrais journaux (une
soirée de raid héroïque et une session Mythique+) en plus des tests.

**Des chiffres qui étaient faux**

- Une rencontre dont aucune unité ne porte le nom — un conseil, un duo,
  un autel — affichait 0 dégât « sur le boss » et une part sur les boss
  de 0 % pour chaque joueur. Les bornes de la rencontre écrites par le
  jeu servent désormais à la reconnaître.
- Dans la liste des pulls d'une clé, le badge « boss » était vert même
  sur un échec. Il dit maintenant « réussite » (vert) ou « échec » (rouge).
- La vie cumulée des ennemis pouvait dépasser 100 % (jusqu'à 8 724 400 %
  sur une vraie clé) quand le jeu écrit une unité avec plus de vie que
  son maximum. Ces lectures contradictoires sont écartées et comptées
  par `diagnose`.
- Les noms de créatures composés étaient coupés au tiret
  (« Jeune-né chancrécaille » devenait « Jeune »).
- La ligne d'un joueur pouvait porter le nom de son familier.
- Deux joueurs du même nom sur deux royaumes étaient fusionnés ; ils
  s'affichent « Tisane » et « Tisane (2) ».

**Ce qui protège vos fichiers**

- `report -o` refuse d'écraser un fichier qui n'est pas un rapport
  LogsWoW (un autre journal, par exemple), sauf avec `--force`. Le
  journal lu n'est jamais écrasé, même avec `--force`.
- Le rapport est écrit à côté puis mis en place d'un coup : un disque
  plein ne laisse plus une page tronquée à la place de l'ancienne.

**Le reste**

- Environ 40 % plus rapide : 22,6 s au lieu de 38,3 s pour une soirée de
  raid de 261 Mo, sans mémoire supplémentaire.
- Une rencontre de boss n'est plus coupée en deux pulls par une accalmie,
  une rencontre sans aucun coup porté est « sans combat » et non un
  échec, et une rencontre restée ouverte après une déconnexion n'absorbe
  plus la suite du fichier.
- `where` trouve le jeu sous macOS, sur un autre disque que C: sous
  Windows, et dans Lutris, Steam (Proton) et Bottles sous Linux.
- Les valeurs absurdes d'option (`--pull-gap nan`, `--limit -1`) sont
  refusées avec un message en français.
- Les liens Wowhead restent dans votre langue avec Python 3.15.
- Un seul fichier à télécharger, `logswow-0.2.0.pyz`, qui se lance sans
  rien décompresser : voir `INSTALL.md`.

## 0.1.0 — 2026-09-18

Première version : lecture locale du fichier `WoWCombatLog.txt`, rapport
HTML autonome (combats, pulls, frise, dégâts et soins par joueur, morts,
panneaux par joueur et par ennemi, liens Wowhead), commandes `report`,
`list`, `diagnose` et `where`. Corrigée et vérifiée jusqu'au 2026-09-26
sur cinq vrais journaux et un export Warcraft Logs.
