# Journal des versions

Chaque version publiée, ce qui y a changé pour qui s'en sert. Le détail
technique, daté et chiffré, est dans les sections datées de `CLAUDE.md`.

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
