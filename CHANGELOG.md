# Journal des versions

Chaque version publiée, ce qui y a changé pour qui s'en sert. Le détail
technique, daté et chiffré, est dans les sections datées de `CLAUDE.md`.

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
