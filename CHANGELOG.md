# Journal des versions

Chaque version publiée, ce qui y a changé pour qui s'en sert. Le détail
technique, daté et chiffré, est dans les sections datées de `CLAUDE.md`.

## 0.13.1 — 2026-09-29

**La barre de progression de la fenêtre se voit, et dit le temps
restant.** Elle avançait bien, mais sous Linux le thème de la fenêtre la
dessinait en gris clair sur fond gris, et elle se vidait dès la lecture
finie : on la prenait pour une barre cassée. Elle est maintenant bleue,
reste pleine une fois la lecture ou le rapport terminés, et suit la
position réelle dans le fichier plutôt qu'une estimation par ligne. En
dessous, la ligne d'état donne le pourcentage et le temps restant :
« Lecture… 36 %, 401 409 lignes lues, encore environ 30 s ». Sur votre
journal de 364 Mo, l'estimation annonçait 45 s au bout de 4 secondes
pour 46 s réelles, et n'a jamais été à plus de 3 s de la vérité. Le
rapport, lui, s'écrit en une ou deux secondes : il n'a pas de compte à
rebours.

## 0.13.0 — 2026-09-29

L'audit complet de la 0.12.1, vérifié sur votre journal de 364 Mo du
29 septembre.

**Correction : les pauses d'un joueur qui a un familier étaient
cachées.** Chaque sort lancé par un familier, une invocation ou un totem
mettait fin à la pause de son maître : un chasseur resté quarante
secondes sans rien lancer, pendant que son familier mordait chaque
seconde, affichait zéro seconde sans action. Seuls les sorts du joueur
lui-même comptent maintenant pour le « Temps sans action » et les plus
longues pauses ; ceux de ses invocations restent comptés, à part, dans
les sorts lancés. Sur votre journal, 14 joueurs sur 25 changent ; le
plus concerné passe de 283 s à 458 s sans action sur une clé.

**Correction : en JcJ, l'adversaire était compté dans le groupe.** Dans
une arène ou un champ de bataille, le journal écrit les joueurs d'en face
hors du groupe et hostiles ; ils étaient traités en coéquipiers :
l'adversaire figurait dans le classement, chaque coup échangé comptait
comme un coup reçu d'un allié, et les dégâts infligés restaient à zéro.
Ce sont maintenant des ennemis, avec leurs familiers, leurs incantations
(qu'une interruption peut couper) et leurs morts. Un membre du groupe
sous contrôle mental, ou qui en sort un instant, reste du groupe. Les
matchs ne sont pas encore découpés. Sur votre journal de donjon, aucun
chiffre ne bouge.

**Des mots restaient en français dans les rapports en anglais, allemand
et espagnol** : « et 3 autre(s) » dans le tableau des pulls, « autres »
dans la répartition par école et parmi les cibles d'un soigneur,
« aucun » et « absent » en bas de page et dans `diagnose`, « Mo » dans
`where`. Tout est traduit.

**Une taille de fichier s'écrit partout de la même façon.** La fenêtre
comptait un mégaoctet pour un million d'octets ; la page, `diagnose` et
`where` pour 1 048 576 : le même journal y faisait 364,4 Mo et 347,5 Mo.
C'est partout un million d'octets, comme le disent les unités et comme
l'affiche un gestionnaire de fichiers sous Linux. `diagnose` écrit aussi
ses nombres à la française (« 1 121 188 lignes »).

**Moins de mémoire pour écrire le rapport.** La page était assemblée
entière en mémoire, plusieurs fois, avant d'être écrite ; elle part
maintenant sur le disque combat par combat. Sur votre journal : 252 Mo
→ 89 Mo au plus fort pour la présentation en onglets, 149 Mo → 88 Mo
pour la page longue. La page produite est identique à l'octet près.

Plus petit : `-q` a sa ligne d'aide ; « 1 écarté, trop petit » s'accorde
au singulier ; les tests passent aussi sous Python 3.14.

## 0.12.1 — 2026-09-29

**Correction : le seuil « dans les temps » était trop exigeant de +2 à
+11.** La règle de la 0.12.0, 15 × niveau + 185, tombait juste à partir
de +12 mais demandait 15 à 30 points de trop en dessous : un +10 dans les
temps à 330 points aurait été affiché « hors des temps ». Le seuil est
maintenant le score de base que Raider.IO publie pour chaque niveau, de
+2 à +30 : 125 + 15 × niveau, plus 15 à chaque palier d'affixe (+4, +7,
+10 et +12), soit 320 pour un +10 et 335 pour un +11 (les +12 et plus ne
changent pas). Aucune de vos clés ne change de verdict, mais votre
Allée du meurtre +10 en 19:16, à 335 points pile, ne passait que par
égalité. Les chronomètres de la saison, tels que les donne l'API de
Raider.IO, confirment les 14 verdicts de vos journaux.

## 0.12.0 — 2026-09-29

**Correction : « dans les temps » était faux pour une clé finie en
retard.** Votre Val Aveuglant +13 terminé en 30:23 était affiché « dans
les temps ». Le journal écrit, en fin de clé, un indicateur qui veut dire
« terminée », pas « chronométrée », et il n'écrit nulle part le temps
limite du donjon. Ce qui les distingue, c'est le score que le jeu donne à
la clé : au moins 15 × niveau + 185 dans les temps (380 pour un +13),
moins en retard. Vos deux Val Aveuglant +13 : 383,2 en 27:26 (dans les
temps), 319,5 en 30:23 (hors des temps). Sur 15 clés terminées, les 14
dans les temps sont toutes au-dessus du seuil ; si un verdict vous
semble faux, dites quelle clé. Une clé d'un journal ancien, sans score,
est seulement « terminée ».

**Les pulls dans la liste de gauche.** Chaque clé y est maintenant
repliée derrière un petit « + ». Dépliée, elle montre ses pulls et ses
boss dans l'ordre où ils ont été joués (« Pull 1 », « Pull 2 », le boss,
« Pull 4 »…), avec la même numérotation que le tableau des pulls. Chaque
pull de trash s'ouvre comme un boss, avec son propre détail : dégâts,
soins, morts, joueurs, ennemis (l'ordre des sorts reste dans la vue de la
clé, pull par pull). Cliquer sur le nom de la clé la sélectionne, le
« + » la déplie. La présentation en dossier de pages a aussi une page
par pull ; la page longue ne change pas.

Ces vues ont un coût, mesuré sur votre journal de 364 Mo : 35 s → 45 s,
13 → 20 Mo de page, 163 → 249 Mo de mémoire au plus fort. Tous les
chiffres des combats sont identiques à la 0.11.0, et chaque pull compte
exactement les mêmes dégâts que sa ligne dans le tableau de la clé
(vérifié sur 143 pulls de cinq journaux).

## 0.11.0 — 2026-09-29

**Le premier coup reçu par chaque ennemi**, pull par pull et boss
compris : pour chaque monstre, le joueur qui l'a touché en premier (un
coup manqué compte aussi, il attire le monstre tout autant), avec quel
sort et à quel moment du pull. Le sort d'un familier, d'une invocation
ou d'un totem compte pour son maître. C'est écrit tel quel dans le
journal : c'est sûr. La liste se déplie sous chaque ligne du tableau des
pulls, et sous l'en-tête d'un combat de boss seul.

**Qui a ouvert chaque pull.** Sous chaque ligne du tableau des pulls, le
premier acte qui lie le groupe à un ennemi depuis la fin du pull
précédent : « Ouvert par Tisane (tank) : Caresse de la mort, 0,4 s avant
le premier coup ». Le sort d'un familier, d'une invocation ou d'un totem
compte pour son maître, et le rôle du joueur est écrit à côté de son
nom. Le journal n'a aucune ligne de menace : un ennemi pris par
proximité (un body pull) ne s'y voit qu'à ce qu'il fait ensuite, et la
ligne dit alors « Golem a agi en premier, sur Braise », marquée **bêta**
en attendant vos retours. Comme un soin, un renfort ou une dissipation
donné en combat attire l'ennemi vers celui qui l'a donné, elle ajoute,
quand c'est le cas, que cette cible venait d'aider un autre joueur, et
lequel : c'est souvent lui qui a tiré. Des faits, pas de verdict : une
zone au sol laissée par le pack précédent peut aussi faire agir un
ennemi en premier.

Mesuré sur trois de vos journaux de donjon (159 pulls) : le tank ouvre
la plupart des pulls, typiquement 0,3 à 0,6 s avant le premier coup ;
l'ennemi agit en premier dans environ un pull sur six.

**Un pull se termine après 3 secondes sans dégâts**, au lieu de 6 : c'est
plus proche de ce que fait un groupe en jeu. `--pull-gap` et le réglage
de la fenêtre permettent toujours d'en choisir un autre. Les totaux ne
changent pas ; seul le découpage en pulls est plus fin.

## 0.10.0 — 2026-09-28

**LogsWoW parle aussi allemand et espagnol.** La fenêtre, les commandes,
`diagnose` et le rapport existent maintenant en quatre langues. Le choix
reste automatique (la langue de votre machine, l'anglais pour une langue
sans traduction) ; `--langue de` ou `--langue es` en impose une. Chaque
langue écrit ses nombres à sa façon : « 25,4 Mio. » et « 25.361.906 » en
allemand, « 25,4 M » et « 45,6 mil » en espagnol. Les traductions ont été
écrites avec soin mais n'ont pas encore été relues par des joueurs dont
c'est la langue : un terme qui sonne faux peut être signalé, il se
corrige en une ligne.

**La virgule décimale en français.** « 25,4 M » et « 180,6 Mo » au lieu
de « 25.4 M » et « 180.6 Mo », partout.

**Les clés abandonnées sont reconnues.** Une clé relancée, ou laissée
pour une autre, était comptée « hors des temps » ; elle est désormais
« abandonnée ». Le jeu écrit en effet, avant chaque nouvelle clé, une fin
vide (ni niveau, ni temps) qui ferme celle qui restait ouverte. Une
nouvelle tuile en haut du rapport, **Clés non terminées**, compte ces
clés et celle que le journal laisse ouverte (« interrompu »).

**La colonne « Réattribué »**, dans le classement des dégâts, dès qu'un
combat contient les lignes de soutien d'un Évocateur : les dégâts de
chacun, moins la part que le jeu crédite aux renforts d'un Évocateur
(Puissance d'ébène, Prescience, Bombardements…), plus ce qu'il lui
crédite. C'est la réattribution de Warcraft Logs, et la seule forme
d'« aDPS » que le journal permet : il n'écrit nulle part ce qu'une Furie
sanguinaire ou une Infusion de puissance a ajouté aux coups des autres.
La colonne s'ajoute au total, elle ne le remplace pas, et le total du
groupe ne change pas.

**Correction.** En anglais, la taille du fichier s'affichait en « Mo » ;
c'est « MB ».

Rien d'autre ne change : sur cinq journaux (dont trois vrais), pas un
chiffre ne bouge hors des deux clés abandonnées, et les quatre langues
donnent exactement les mêmes nombres. La vitesse est la même.

## 0.9.0 — 2026-09-28

**LogsWoW parle aussi anglais.** La fenêtre, les commandes, `diagnose` et
le rapport existent désormais en français et en anglais. La langue est
choisie toute seule : celle de votre machine, et l'anglais pour toute
langue qui n'a pas encore de traduction. Pour en imposer une :

- `--langue fr` ou `--langue en`, avant ou après la commande ;
- ou la variable d'environnement `LOGSWOW_LANGUE`, pour un choix
  permanent.

Chaque langue écrit ses nombres à sa façon (« 25 361 906 » et « 46 % »,
« 25,361,906 » et « 46% »), et ses dates aussi. Les noms de sorts, de
boss et de joueurs restent ceux du journal, dans la langue de votre
client de jeu.

Le README et le guide d'installation ont leur version anglaise
(`README.en.md`, `INSTALL.en.md`), comme ce journal des versions
(`CHANGELOG.en.md`).

Rien d'autre ne change. En français, les pages sont identiques à celles
de la 0.8.1, caractère pour caractère. En anglais, les chiffres sont
exactement les mêmes : vérifié sur cinq journaux, dont trois vrais, soit
plus d'un million de nombres. La vitesse est la même aussi.

## 0.8.1 — 2026-09-28

**Le rapport parle un français accentué.** « Dégâts infligés », « Durée »,
« réussite », « échec », « Clés mythiques », « mort instantanée »… : le
rapport, la ligne de commande et `diagnose` écrivaient jusqu'ici une bonne
partie de leurs textes sans accents, à côté d'autres qui en avaient.
Tout est accentué désormais, noms de spécialisations compris
(« Chasseur de démons », « Maîtrise des bêtes », « Évocateur »).

Rien d'autre ne change : pas un chiffre, pas une ligne de tableau. Sur
cinq journaux, dont trois vrais, les pages d'avant et d'après sont
identiques caractère pour caractère une fois les accents retirés. Les
commandes se tapent comme avant : `fenetre`, `--sans-sequence`,
`--format onglets`.

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

*Jamais publiée seule : son contenu est arrivé avec la 0.5.0.*

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
