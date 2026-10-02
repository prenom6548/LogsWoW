# Suivre une soirée en direct : ce que fait Archon, et ce qui serait possible ici

Recherche du 2026-10-02, à la demande du propriétaire : *« peux tu regarder
Archon, leurs client peut faire "live" est ce que c'est possible avec le
notre ? »*. Il a ensuite demandé de **garder les résultats, les recherches et
les idées pour plus tard**, le temps de faire ses retours sur la 0.20.1.
Aucune modification n'a été faite à `logswow/` pour cette recherche : ce
document existe pour que la session qui reprendra le sujet n'ait pas à refaire
le travail, et pour séparer ce qui est établi de ce qui reste à mesurer.

## 0. Ce qui a été consulté

- **La page d'aide de l'Archon App** (archon.gg, « Archon App: Help & FAQ »).
  Une récupération directe a reçu un refus HTTP 403, comme lors de l'étude de
  septembre ; son contenu sur le *live logging* a été lu à travers un moteur
  de recherche. Aucun compte créé, aucun logiciel installé.
- **Un fil du forum de Blizzard** (août 2025) sur le délai d'écriture du
  journal de combat.
- **`LOGS-SITES-RESEARCH.md`**, sections 3.3 (comment fonctionne le client)
  et 6.3 (l'Archon App).
- **Le code de LogsWoW** : `parse.py` (`LogFile.events`) et `segment.py`
  (`Splitter._close`, `Splitter.finish`).

Aucun journal réel n'a été lu pour cette recherche, et aucun n'est nécessaire
avant la mesure de la section 4.

## 1. Ce que fait Archon

- Leur client (l'Archon App, qui remplace l'ancien « Warcraft Logs Uploader »
  depuis le 29 juin 2026) **surveille le fichier `WoWCombatLog.txt` pendant
  que le joueur joue** : dès que le jeu ajoute des événements à la fin du
  fichier, le client les envoie au site, et le rapport se construit pendant
  la soirée.
- Il faut avoir activé la **journalisation de combat avancée** (réglages
  réseau du jeu) et lancé `/combatlog`, comme pour LogsWoW.
- Une option envoie **tout le fichier en cours**, pour qui a oublié de lancer
  le direct avant de commencer.
- Le but affiché est de **relire un essai entre deux pulls**, en guilde
  (`LOGS-SITES-RESEARCH.md`, 3.3).
- L'Archon App propose un **compteur de dégâts superposé au jeu pour FFXIV et
  SWTOR, mais pas pour WoW** (`LOGS-SITES-RESEARCH.md`, 6.3).
- Différence de fond avec LogsWoW : Archon **envoie tout à ses serveurs** ;
  ici, tout resterait sur la machine du joueur, sans aucune connexion.

## 2. Ce que dit le code de LogsWoW

Établi en lisant le code le 2026-10-02 :

- **Le lecteur est un flux** : `LogFile.events()` lit le fichier ligne à
  ligne et produit les événements au fur et à mesure ; rien ne charge le
  fichier entier. Mais il **s'arrête à la fin du fichier** : il n'attend pas
  les lignes que le jeu écrira ensuite.
- **La disposition des champs est mesurée sur les 5 000 premières lignes**
  (`WARMUP_LINES`, `detect_layout`) avant de produire le premier événement.
  En direct, en début de session, ces 5 000 lignes peuvent tarder à venir
  (rapide en clé ou en raid, lent en ville).
- **Un combat est bouclé dès sa ligne de fin** : `Splitter._close` appelle
  `analysis.finish` quand arrive `ENCOUNTER_END` (un boss, réussi ou non) ou
  `CHALLENGE_MODE_END` (une clé), et règle les pulls de la clé à ce moment.
  Un mode direct pourrait donc afficher chaque essai de boss et chaque clé
  **dès que le jeu a écrit leur fin**, avec les mêmes chiffres qu'à la
  lecture complète du fichier.
- **La numérotation des combats n'est faite que dans `finish()`** : en
  direct, il faudrait une numérotation provisoire, ou numéroter dans l'ordre
  d'arrivée.
- **Les pulls de trash d'une clé ne sont réglés qu'à la fin de la clé** :
  en direct, une clé en cours ne montrerait pas encore ses pulls (amélioration
  possible plus tard, à part).
- **La fenêtre a déjà ce qu'il faut pour un travail long** : un fil de lecture,
  une file de messages vers la boucle de la fenêtre, l'annulation, la barre
  de progression.

## 3. Deux réserves

1. **Le jeu écrit le fichier avec retard.** WoW garde les événements en
   mémoire avant de les écrire sur le disque. En clé et en raid, le flux est
   dense et les écritures sont fréquentes ; hors groupe, un développeur
   rapporte sur le forum de Blizzard des délais « de plusieurs minutes »
   (août 2025), sans réponse de Blizzard sur le mécanisme. **Rien de cela n'a
   été mesuré** : il faut le mesurer sur la machine du propriétaire avant de
   construire quoi que ce soit (section 4).
2. **Pas de compteur de dégâts pendant le combat.** Il serait peu fiable à
   cause du retard ci-dessus, et surtout la 12.0 a précisément retiré aux
   addons l'accès aux données de combat en direct : un outil externe qui le
   rendrait irait contre l'esprit de cette décision. Archon lui-même ne
   propose pas de compteur superposé pour WoW. **Le direct visé ici est la
   relecture entre deux pulls**, pas un compteur en jeu.

## 4. Ce qui est proposé, en deux temps

### 4.1 D'abord mesurer le délai, chez le propriétaire

Un petit script en lecture seule (bibliothèque standard, aucune connexion),
lancé pendant une clé ou un raid, puis quelques minutes en ville :

- toutes les deux secondes, il affiche la **taille du fichier** le plus récent
  du dossier `Logs`, et l'**écart entre l'heure réelle et l'horodatage de la
  dernière ligne complète** écrite ;
- il note à part l'instant où une ligne `ENCOUNTER_END` ou
  `CHALLENGE_MODE_END` apparaît sur le disque, comparé à l'heure de cette
  ligne : c'est le délai qui compte pour relire un essai.

Ce qu'il faut en tirer : si, en groupe, la fin d'un combat arrive sur le
disque en **quelques secondes** (ordre de grandeur à confirmer : moins d'une
dizaine), le mode direct vaut la peine ; si elle arrive en minutes, il n'apporte
presque rien par rapport à « lire le journal » après le combat.

### 4.2 Ensuite, si la mesure le justifie : « Suivre en direct »

- **Un lecteur qui suit le fichier** (`tail -f`) : le fichier reste ouvert ;
  à la fin du fichier, il attend (une seconde, par exemple) et relit ; une
  **ligne incomplète** en fin de fichier est gardée jusqu'à ce que le jeu
  l'ait finie ; si un **fichier plus récent** apparaît dans le dossier (un
  `/combatlog` relancé, le jeu redémarré), il passe à celui-là.
- **La mesure de la disposition** : attendre les 5 000 lignes comme
  aujourd'hui, ou décider plus tôt sur moins de lignes après un délai ; à
  mesurer sur un début de session réel avant de choisir.
- **Dans la fenêtre** : un bouton « Suivre en direct » ; chaque combat bouclé
  s'ajoute à la liste avec son aperçu, la page s'écrit à la demande comme
  aujourd'hui ; un arrêt propre (le même mécanisme que l'annulation).
- **Historique, en option** : enregistrer la soirée à chaque clé terminée ou
  boss bouclé. Depuis la 0.20.1, une soirée relue est **mise à jour** et non
  doublée, ce qui rend cette option sûre.
- **Toujours aucune connexion**, rien d'écrit dans le dossier du jeu, rien
  d'injecté dans le jeu : un programme qui lit un fichier, comme aujourd'hui.
- **Mémoire sur une longue soirée** : la même que lire le fichier entier
  aujourd'hui (les combats bouclés gardent leur analyse) ; à confirmer sur une
  soirée rejouée.

### 4.3 Comment le tester sans jeu

Rejouer un vrai journal du propriétaire **dans un fichier qui grossit**, à
vitesse accélérée (écrire les lignes par paquets, avec des pauses et des
lignes coupées en deux), dans le répertoire temporaire de la session, puis
vérifier que :

- chaque combat apparaît une fois, dès sa ligne de fin ;
- les chiffres de chaque combat sont **identiques à l'octet près** à ceux d'une
  lecture complète du même fichier (la même preuve par instantané que les
  audits) ;
- une ligne coupée en fin de fichier n'est jamais lue à moitié ;
- le passage à un nouveau fichier ne perd ni ne double rien.

## 5. Questions ouvertes

- Le **délai réel** d'écriture du jeu, en groupe et hors groupe (section 4.1).
- Que fait le jeu quand `/combatlog` est relancé dans la même session :
  nouveau fichier, ou suite du même ? (Les fichiers du propriétaire portent
  l'heure de début dans leur nom, `WoWCombatLog-092926_152403.txt`, ce qui
  laisse penser à un nouveau fichier ; à vérifier.)
- Combien de temps faut-il, en début de session, pour atteindre les 5 000
  lignes de la mesure de disposition ?
- Le propriétaire voudra-t-il voir les **pulls d'une clé en cours**, ou la
  clé une fois finie lui suffit-elle ?

## 6. Sources

- archon.gg, *Archon App: Help & FAQ* —
  https://www.archon.gg/classic-vanilla/articles/help/archon-app-help-and-faq
  (lue via un moteur de recherche ; accès direct refusé, HTTP 403).
- Forum Blizzard, *[wow] WoW Combat Log Delay – seeking API or workaround*,
  28-29 août 2025 —
  https://us.forums.blizzard.com/en/blizzard/t/wow-wow-combat-log-delay-%E2%80%93-seeking-api-or-workaround/55869
- `LOGS-SITES-RESEARCH.md`, sections 3.3 et 6.3, et leurs sources [S1], [S2],
  [S23], [S24], [S25].
