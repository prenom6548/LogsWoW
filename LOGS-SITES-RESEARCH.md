# Warcraft Logs, WoWAnalyzer, Wipefest, Archon : ce qu'ils font, comment, et pourquoi

Recherche du 2026-09-16, à la demande du propriétaire (« renseigne-toi
entièrement sur ces quatre sites : ce qu'ils font, comment, pourquoi »).
C'est un document de lecture, écrit deux jours avant que LogsWoW existe ;
la section 8 dit ce qui en a été retenu pour le construire.

## 0. Comment lire ce document, et ce qu'il ne couvre pas

- **Les pages vivantes de warcraftlogs.com et d'archon.gg refusent toute
  lecture automatisée** (HTTP 403, protection anti-robot, quel que soit
  l'agent utilisateur). Tout ce qui vient de ces deux sites a été lu dans
  des instantanés 2026 de web.archive.org, ou dans des reprises
  intégrales publiées par Wowhead. La date « dernière mise à jour »
  affichée par chaque article est citée quand elle compte.
- wipefest.gg ne renvoie qu'une coquille d'application (Angular) ; son
  fonctionnement est décrit d'après les articles d'aide qu'Archon publie
  pour lui, et d'après le code historique de son moteur.
- **WoWAnalyzer est en source ouverte** : le dépôt a été cloné et lu
  (dernier commit le 14 septembre 2026). C'est la seule des quatre
  briques dont le « comment » est vérifié dans le code plutôt que dans
  la communication.
- **Aucun compte n'a été créé, aucun fichier de log réel n'a été lu,
  aucune API n'a été appelée.** Ce qui suit est donc ce que ces
  services *disent* faire, recoupé avec du code ou des tiers quand
  c'était possible, jamais ce qui a été *observé* en les utilisant.
  Les tarifs et limites cités sont ceux affichés dans les sources à
  leur date ; ils peuvent avoir bougé.
- Les sources sont numérotées [S1]... et listées en section 9.

## 1. Vue d'ensemble

Quatre noms, mais deux réalités.

**Une seule entreprise.** Archon est le nom-ombrelle, adopté en octobre
2023, de RPG Logs LLC, société établie à Houston (Texas, États-Unis)
[S13][S22]. Elle a été fondée par un développeur connu sous le pseudonyme
Kihra, qui a créé Warcraft Logs seul en 2013 [S5][S6]. Elle possède
aujourd'hui Warcraft Logs, Wipefest (racheté fin 2020 [S9]), WoWAnalyzer
(racheté en octobre 2021 [S10]), Mythic Trap (des guides de boss
illustrés, nés dans une guilde européenne, Raid Trap sur Kirin Tor, et
traduits en plusieurs langues dont le français [S39]), et les
sites jumeaux FF Logs, ESO Logs, SWTOR Logs, plus le support du jeu
Fellowship [S5][S13]. En mars 2023 elle comptait 14 salariés de 8 pays,
le premier embauché en janvier 2018 [S5].

**Une seule matière première.** Tout repose sur le fichier
`WoWCombatLog.txt` que le client du jeu écrit lui-même sur le disque du
joueur quand la journalisation est activée. Aucun de ces sites ne lit le
jeu en direct : ils lisent ce fichier, après coup.

La chaîne complète, en une image :

```
client WoW  --/combatlog-->  _retail_\Logs\WoWCombatLog.txt
    --Archon App (ex « Warcraft Logs Uploader »)-->  serveurs Warcraft Logs (AWS)
    -->  un « rapport » : combats, événements, tableaux, replay 2D
    -->  classements (parses, percentiles, All Stars), statistiques agrégées
    -->  API GraphQL v2 (OAuth2) / API v1 héritée
          -->  WoWAnalyzer  : analyse d'UN joueur sur UN combat, dans le navigateur
          -->  Wipefest     : analyse mécanique d'UN raid, notée contre les autres guildes
          -->  Archon Builds & Tier Lists : agrégats de popularité sur des millions de parses
```

Chaque étage vit de l'étage du dessous. Warcraft Logs sans le fichier
n'existe pas ; WoWAnalyzer et Wipefest sans l'API de Warcraft Logs
n'existent pas ; les guides d'Archon sans la masse des rapports publics
n'existent pas.

## 2. Le socle : le fichier de journal de combat

### 2.1 Activation et emplacement

- La commande `/combatlog` (ou l'appel `LoggingCombat(true)`) fait écrire
  tous les événements de combat dans `Logs\WoWCombatLog.txt` sous le
  dossier du jeu [S1][S2]. Elle ne persiste pas d'une session à l'autre ;
  des addons minuscules (AutoCombatLogger, SimpleCombatLogger)
  l'activent en entrant en instance [S2][S20].
- **L'option « Advanced Combat Logging »** (Système > Réseau, ou
  `/console advancedCombatLogging 1`) persiste, et elle est **obligatoire
  pour que Warcraft Logs accepte un fichier** : c'est elle qui ajoute les
  positions, les points de vie, les ressources [S1][S2].
- Ordre de grandeur des fichiers cités : plusieurs centaines de Mo pour
  une soirée de raid, 100 à 200 Mo pour une session de donjons [S2].

### 2.2 Format

Une ligne par événement : un horodatage, puis le nom de l'événement et
ses champs séparés par des virgules. La structure est celle de
l'événement `COMBAT_LOG_EVENT` documentée sur le wiki [S3] :

- **11 champs de base** : timestamp, sous-événement (`SPELL_DAMAGE`,
  `SPELL_AURA_APPLIED`, `UNIT_DIED`...), hideCaster, puis GUID / nom /
  flags / raid-flags de la source, et les quatre mêmes pour la cible.
- **Préfixe** selon la nature : `SPELL_` ajoute spellId, spellName,
  spellSchool ; `ENVIRONMENTAL_` ajoute le type.
- **Suffixe** selon le résultat : `_DAMAGE` ajoute montant, overkill,
  école, résisté, bloqué, absorbé, critique... ; `_HEAL` ajoute montant,
  surguérison, absorbé, critique ; `_MISSED` le type d'esquive, etc.
- **17 champs « avancés », propres au fichier** (jamais fournis aux
  addons) : GUID de l'unité et de son propriétaire, PV courants et max,
  puissance d'attaque et des sorts, armure, absorption, type / valeur /
  max / coût de ressource, **position X, Y, uiMapID, orientation**, et
  niveau ou niveau d'objet [S3].
- **Lignes qui n'existent que dans le fichier** : `COMBAT_LOG_VERSION`
  (en-tête de session), `ENCOUNTER_START` / `ENCOUNTER_END` (bornes d'un
  boss), `COMBATANT_INFO` (instantané des stats, talents et équipement
  de chaque joueur au pull), `ZONE_CHANGE`, `MAP_CHANGE`,
  `CHALLENGE_MODE_START` / `_END` (une clé), `WORLD_MARKER_PLACED`,
  `EMOTE` [S3].

C'est cette richesse-là, positions comprises, qui rend possible le replay
2D de Warcraft Logs, les « insights » de position de Wipefest, et la
« stat priority » d'Archon (lue dans `COMBATANT_INFO`).

### 2.3 Midnight : ce qui a changé, et ce qui n'a pas changé

C'est le point sur lequel tout repose, et il vaut d'être dit précisément.

- **Pour les addons**, le journal de combat est fermé depuis le patch
  12.0.0 : enregistrer `COMBAT_LOG_EVENT` ou
  `COMBAT_LOG_EVENT_UNFILTERED` déclenche `ADDON_ACTION_FORBIDDEN` [S3].
  Les valeurs « secrètes » ont tué WeakAuras (Retail), les rotations
  assistées, les compteurs de menace.
- **Pour le fichier**, rien n'a changé. Le wiki le dit explicitement :
  la journalisation vers `WoWCombatLog.txt` via `LoggingCombat()` /
  `/combatlog` est distincte de l'accès addon et n'est pas touchée [S3].
  Les deux billets officiels de Blizzard sur les addons de combat ne
  mentionnent ni le fichier, ni les sites d'analyse [S16][S17] ; ils
  visent « l'automatisation des décisions de combat » et « l'avantage
  compétitif en combat ». Un outil qui lit le fichier *après* le combat
  n'est ni l'un ni l'autre. Les sites tiers et la presse spécialisée le
  confirment depuis l'automne 2025 : « Warcraft Logs et tout outil qui
  lit WoWCombatLog.txt fonctionnent exactement comme avant » [S2][S18].
- Blizzard a d'ailleurs assoupli sa première version (annonce du 3
  octobre 2025) : les restrictions de communication d'addons en instance
  ne s'appliquent plus que **pendant** un combat de boss ou une clé en
  cours, pour ne pas casser les timers de pause, les conseils de loot,
  les notes de raid [S18][S19].
- Blizzard a en parallèle livré son propre **compteur de dégâts intégré,
  « avec validation côté serveur »** [S17]. Ce n'est pas un concurrent de
  Warcraft Logs (pas d'historique, pas de comparaison entre guildes),
  mais c'est la première fois que Blizzard prend en charge lui-même une
  fonction que l'écosystème assurait.

En résumé : **le combat log n'est pas mort, il a changé de porte.** Il
n'entre plus dans le jeu par les addons ; il sort du jeu par le fichier.
Toute la chaîne de la section 1 tient debout sur cette porte-là.

### 2.4 Un bug ouvert : des soins qui manquent dans le fichier

Depuis le lancement de Midnight, plusieurs joueurs constatent que le
fichier avancé enregistre **moins de soins** que ce que l'interface et le
compteur intégré affichent, pour certaines spécialisations (Moine
Tisse-brume et Paladin Sacré sont les plus cités ; les dégâts et les
tanks sont corrects). Fil ouvert sur le forum européen le 23 mars 2026,
dernier message de fond le 5 avril, fermé automatiquement le 5 mai,
**sans réponse de Blizzard** [S4]. Aucune note de correctif trouvée
jusqu'aux hotfixes du 10 septembre 2026 [S4b]. Conséquence pratique : pour
un soigneur, le chiffre du site et le chiffre du jeu peuvent diverger de
plusieurs millions sur un combat, et le site n'y peut rien : il ne voit
que ce que le client a bien voulu écrire.

## 3. Warcraft Logs

### 3.1 Ce que c'est

Un site qui reçoit des fichiers de journal, les découpe en combats, et
les rend lisibles et comparables :

- **Un rapport** par fichier envoyé : liste des combats (boss, essais,
  clés), et pour chacun des tableaux dégâts / soins / dégâts subis /
  morts / buffs et debuffs / casts / ressources / interruptions /
  dispels / invocations, un graphe de temps zoomable, des **requêtes**
  libres qui filtrent les événements bruts, et un **replay 2D** qui
  rejoue les positions de tous les joueurs et ennemis [S6][S14].
- **Des classements** : dès qu'un boss meurt dans un rapport public,
  chaque joueur est classé contre tous les joueurs de sa spécialisation
  (section 3.4). C'est de là que vient la culture du « parse ».
- Autour : pages de personnage et de guilde, progression, recrutement,
  classements de vitesse, analyse multi-rapports, guides de boss (Mythic
  Trap) intégrés dans l'en-tête, et un « Time Machine » de widgets pour
  les diffusions de course au premier kill mondial [S5].

Visibilité d'un rapport : public (classé), non listé (« unlisted »,
visible par lien, non classé), privé. Ce point compte pour les outils
tiers : Wipefest ne peut lire que les publics et non listés [S12].

### 3.2 Histoire

- **2013.** Kihra, joueur sur le serveur Windrunner (US), commence le
  site « par intérêt pour le problème » alors que World of Logs, la
  référence d'alors, cesse d'être mis à jour pendant Siege of Orgrimmar.
  Le boss Dark Animus (Trône du Tonnerre) est le déclencheur : il
  fallait pouvoir savoir *qui* frappait *quel* golem, donc distinguer
  les instances de monstres, ce que World of Logs ne faisait pas. Dès
  l'interview de décembre 2013 les choix structurants sont posés :
  rapports **stockés par segments** (un segment = un combat de boss)
  pour ne charger que le combat demandé ; le replay comme fonction
  phare ; et « le plus dur, c'est la montée en charge quand toutes les
  guildes journalisent en même temps » [S6].
- **Avril 2015.** Ouverture d'un Patreon pour payer les serveurs, le site
  restant gratuit pour tous [S7].
- **Ensuite**, les jumeaux : FF Logs, ESO Logs, Rift Logs, WildStar Logs,
  puis SWTOR Logs, sur la même base de code [S5][S14].
- **Janvier 2018.** Premier employé. **Automne 2020** : rachat de Wipefest
  [S9]. **Octobre 2021** : rachat de WoWAnalyzer [S10]. Mythic Trap
  rejoint aussi le groupe [S5].
- **Octobre 2023.** RPG Logs LLC devient **Archon** (section 6).
- **Mars 2026.** L'**Archon App** sort de bêta avec l'enregistrement
  vidéo ; le créateur de Warcraft Recorder rejoint l'équipe [S23][S24].
  **29 juin 2026** : l'ancien « Warcraft Logs Uploader » est retiré au
  profit de l'Archon App (version complète) ou d'**Archon Lite**
  (envoi seul, sans publicité ni bibliothèques tierces) [S25].

### 3.3 Comment ça marche, techniquement

Ce qui est public ou déductible ; le serveur lui-même est fermé (aucun
dépôt public sur l'organisation GitHub de Warcraft Logs [S26]).

1. **Côté joueur**, un client de bureau (Electron) surveille le dossier
   `Logs`, découpe le fichier, et l'envoie soit en fin de session, soit
   **en direct** (« live logging ») pour que la guilde relise un essai
   entre deux pulls [S1][S2]. Le client détecte le jeu et son dossier.
2. **Côté serveur**, le fichier est analysé, les combats sont bornés par
   `ENCOUNTER_START/END` et `CHALLENGE_MODE_START/END`, les acteurs
   identifiés par GUID, les événements indexés par segment.
3. **Les données d'un combat sont tenues en mémoire rapide**, pas
   seulement sur disque : c'est ce qui permet les graphes zoomables, les
   requêtes libres et le replay en temps réel, et c'est la raison
   avancée pour le coût élevé de l'infrastructure (AWS, instances
   réservées à l'année, montée en charge aux heures de raid) [S14].
4. **Le stockage ne supprime jamais** : plus de 400 To en 2024. Depuis
   2024 (article mis à jour en novembre 2024), les rapports de plus de
   deux ans sont **archivés** sur un
   stockage moins cher et ne sont plus accessibles qu'aux abonnés Gold
   et Platinum [S14].
5. **Les classements** sont recalculés par lots : file de traitement
   (prioritaire pour les abonnés), verrouillage « historique » par
   fenêtres de 24 h à midi UTC, All Stars une fois par jour vers 7 h UTC
   [S15]. Les kills sont **dédoublonnés** (deux joueurs de la même
   guilde qui envoient le même kill ne comptent qu'une fois) ; les wipes
   ne le sont pas, trop coûteux [S27].
6. **La triche** est traitée par signalement (Discord, e-mail), par
   marquage automatique d'exploits connus, et par mise sur liste noire
   d'un rapport (horloge système fausse, journal corrompu) ou, en
   dernier recours, d'un personnage [S15].

### 3.4 Classements : le vocabulaire exact

Tout est dans l'article d'aide « Rankings and Parses » (mis à jour le
11 février 2026) [S15].

- **Parse** : le score (DPS, HPS...) d'un joueur sur un kill. **Ranking** :
  son *meilleur* parse. Tout ranking est un parse, seul le meilleur parse
  est un ranking.
- **Percentile** : la part des scores comparables sous le vôtre. Codé par
  couleur : 100 tan, 99+ rose, 95+ orange, etc.
- **Bracket** : une tranche de niveau d'objet (raid) ou de niveau de clé
  (Mythique+). On peut être classé dans sa tranche, ou toutes tranches
  confondues.
- **Partition** : une remise à zéro des classements, à chaque tier de
  contenu et parfois en cours de tier après un gros équilibrage, pour
  qu'une classe nerfée puisse encore se classer. Les anciennes
  partitions sont gelées.
- **All Stars** : un score par zone entière. Formule publiée pour les
  dégâts / soins : `max(100 x (votre DPS / DPS du rang 1), percentile) +
  20 x (votre DPS / DPS du rang 1)`. Variantes pour la vitesse et
  l'exécution ; en Mythique+ c'est la cote de donjon de Blizzard.
- **Huit chiffres possibles** pour un même score, d'où les écarts qu'on
  voit d'une page à l'autre : ranking ou parse, historique ou
  aujourd'hui, sa tranche ou toutes. Le percentile *historique* compare
  au jour du kill (sur des valeurs cachées à 100 %, 99 %, 95 %...,
  interpolées) ; le percentile *du jour* compare à l'état actuel, qui
  baisse à mesure que le tier vieillit.

### 3.5 Modèle économique

Gratuit pour l'essentiel, financé par la publicité pour les non-abonnés
(régies Playwire et Nitro [S28]) et par un abonnement Patreon commun à
tous les sites du groupe [S14] :

| Palier | Prix cité | Ce qu'il apporte |
|---|---|---|
| Silver | 2 $/mois | Sans publicité (sites et client), file de traitement prioritaire |
| Gold | 5 $/mois | + archives de plus de 2 ans, bannières de personnage, quota API 9 000 points/h |
| Platinum | 10 $/mois | + bannières de guilde, traitement prioritaire pour toute la guilde, analyse multi-rapports, quota API 18 000 points/h |

Le quota API de base est de 3 600 points par heure [S14][S21]. Un palier
« Alchemical Society » à 25 $/mois (accès anticipé, canal Discord) est
mentionné par la page Patreon d'après les résultats de recherche ; non
vérifié directement. Les fonctions lourdes (requêtes, replay) restent
volontairement gratuites : « les données sont à vous à filtrer et
manipuler, mais cela a un coût » [S14].

### 3.6 L'API, et ce qu'on a le droit d'en faire

- **v2, GraphQL**, authentifiée par OAuth 2.0 : flux *client
  credentials* pour les données publiques (`/api/v2/client`), flux
  *authorization code* ou *PKCE* pour lire les rapports privés d'un
  utilisateur avec son accord (`/api/v2/user`). Le schéma GraphQL est
  auto-documenté ; l'aide recommande le client Altair [S21].
- **Quota en points par heure**, remis à zéro chaque heure ; la requête
  `rateLimitData` renvoie la limite, les points dépensés et le délai. La
  doc donne une politique de cache : données de jeu à vie, métadonnées
  d'un rapport récent 5 à 10 min, événements d'un combat terminé à vie
  [S21].
- **v1**, l'API REST historique (`/v1/report/events/...`), existe
  toujours : c'est celle que WoWAnalyzer appelle encore aujourd'hui
  (section 4.3), et celle sur laquelle Wipefest a été construit.
- **Conditions d'utilisation** (RPGLogs API Terms, droit du Texas,
  tribunaux de Harris County) [S22] : usage commercial soumis à accord
  préalable (« gagner de l'argent, y compris par la publicité, les
  abonnements, ou apprendre des données pour les revendre ») ;
  interdiction de **constituer des bases permanentes** ou des copies
  au-delà des en-têtes de cache ; interdiction de **représenter le
  contenu tel quel via un autre canal** (site concurrent, addon, overlay,
  mobile) ; interdiction de scraper hors API ; les identifiants ne
  doivent pas être embarqués dans un projet open source. Le contenu
  non public d'un utilisateur ne peut être montré à d'autres sans son
  accord explicite.

### 3.7 Pourquoi ça existe, et pourquoi ça a gagné

- **Le besoin** : un combat de raid de 6 minutes à 20 joueurs produit des
  centaines de milliers d'événements ; personne ne peut les lire à la
  main. World of Logs le faisait, puis a cessé d'évoluer. Kihra a repris
  le flambeau avec les fonctions que la communauté réclamait (instances
  de monstres, animaux et absorptions dans le total, multi-guildes)
  [S6].
- **La comparaison** : classer chaque joueur contre tous les autres de
  sa spécialisation a fait du « parse » un langage commun (recrutement,
  fierté, pression sociale aussi). C'est l'effet de réseau : la valeur
  du classement vient du nombre de rapports, et le nombre de rapports
  vient de la valeur du classement.
- **L'échelle comme produit** : comme pour Raidbots, dont le moteur est
  SimulationCraft, un logiciel libre, le moteur n'est pas le secret. Le format du fichier est
  public, les analyseurs existent en source ouverte. Ce qui ne se copie
  pas, c'est dix ans de rapports, 400 To, et la comparaison contre tout
  le monde.

## 4. WoWAnalyzer

### 4.1 Ce que c'est

Un site qui prend **un rapport Warcraft Logs, un combat, un joueur**, et
rend un verdict pédagogique propre à sa spécialisation : une **checklist**
(uptime des buffs, efficacité des temps de recharge, gaspillage de
ressources, temps mort), des **suggestions** classées par importance,
une **timeline** cast par cast avec les erreurs surlignées, des
**statistiques** (gain estimé de chaque talent, bijou, effet), et pour
les spécialisations les mieux tenues un **« Guide »** rédigé [S10][S11].
Là où Warcraft Logs dit *ce qui s'est passé*, WoWAnalyzer dit *ce que
vous auriez dû faire*, avec les règles de votre spé encodées par des
joueurs qui la connaissent.

### 4.2 Histoire

- **29 mai 2017.** Annoncé par Zerotorescue (Martijn Hols, développeur
  React indépendant installé aux Pays-Bas d'après son profil GitHub
  [S30]) : d'abord un « Holy Paladin Analyzer », fusionné avec des
  clones pour d'autres soigneurs, puis généralisé. Dès le départ : source
  ouverte, contributions par pull request, Discord [S29].
- **Octobre 2021.** Racheté par Warcraft Logs ; **emallson**, l'un des
  principaux contributeurs, est embauché pour le maintenir ; la vue
  Timeline, passée payante, redevient gratuite ; le projet « conserve sa
  nature open source » [S10]. Un Patreon propre subsiste (1 $/mois cité
  par un tiers [S11]).

### 4.3 Comment ça marche, lu dans le code

Dépôt `WoWAnalyzer/WoWAnalyzer`, cloné le 2026-09-16 [S31].

- **Une application entièrement dans le navigateur** : React, Redux,
  TypeScript, Vite, pnpm ; graphiques Vega ; internationalisation
  Lingui. Pas de base de données côté WoWAnalyzer : chaque analyse est
  recalculée à la volée à partir des événements du combat.
- **L'entrée** est une URL de rapport (`warcraftlogs.com/reports/<code>`),
  ou un personnage, ou une guilde ; le site liste alors les combats et
  les joueurs.
- **La lecture des données** passe par un petit serveur intermédiaire de
  WoWAnalyzer (`VITE_SERVER_BASE` + `VITE_API_BASE`) qui appelle l'API
  **v1** de Warcraft Logs : `report/events/<code>` avec `start`, `end`,
  `actorid`, `translate=true`, paginée par `nextPageTimestamp` jusqu'à la
  fin du combat (`src/interface/report/hooks/useEvents.ts`). Le serveur
  intermédiaire porte la clé d'API, ce qui est cohérent avec les
  conditions d'utilisation (pas d'identifiants dans un projet open
  source). Le code contient encore des rustines pour des réponses JSON
  mal échappées (« WCL n'échappe pas les noms de sorts avec
  translate=true ») : un rappel que l'API amont reste une dépendance
  vivante.
- **Le moteur** (`src/parser/core/`) : un `CombatLogParser` reçoit la
  liste d'événements, la passe d'abord par des **normaliseurs**
  (réordonnancement d'événements, liaison cast-dégâts, rafraîchissement
  de buffs) puis par des **modules `Analyzer`** qui s'abonnent à des
  événements typés et accumulent des métriques. `Combatant`, `Enemy`,
  `Pet`, `StateHistory`, `DotSnapshots` modélisent l'état du combat ;
  `ISSUE_IMPORTANCE` grade les suggestions.
- **Une spécialisation = un dossier** sous `src/analysis/retail/<classe>/<spé>/`
  avec un `CONFIG.tsx` (contributeurs, `patchCompatibility`,
  `supportLevel`, rapport d'exemple, changelog) et son propre
  `CombatLogParser` qui assemble les modules. Au 14 septembre 2026 : 40
  configurations Retail, version courante du jeu déclarée `12.1.0` ;
  compatibilité déclarée 12.1.0 pour 13 spés, 12.0.7 pour 12, 12.1 pour
  5, 12.0.1 pour 5, 12.0.0 pour 3, 12.0 pour 1, et une spé encore à
  11.0.5 ; niveau de maintenance : 16 « MaintainedFull », 17
  « MaintainedPartial », 6 « Foundation », 1 « Unmaintained ». Autrement
  dit, **la qualité dépend de la spé** : c'est le point que même les
  concurrents relèvent [S11], et que le site affiche honnêtement.
- **Ajouter un patch ou un raid** est documenté (`docs/Patches-and-raids.md`) :
  déclarer la version dans `parser/Config.ts`, `game/VERSIONS.ts`,
  `interface/report/PATCHES.ts` ; un raid est un dossier sous
  `src/game/raids/` avec les identifiants de rencontre et de zone de
  Warcraft Logs.

### 4.4 Licence et politique de contribution

- **AGPL-3.0** [S31]. C'est une licence compatible avec la GPLv3 (la
  GPLv3, section 13, autorise expressément la combinaison) : du code
  WoWAnalyzer peut entrer dans un projet GPLv3 du propriétaire, avec
  attribution, la partie AGPL restant AGPL. La contrainte propre à
  l'AGPL : si le programme est **offert en service réseau**, le code
  source doit être proposé aux utilisateurs distants. Pour un outil
  local, cette clause ne joue pas.
- **Politique IA stricte** (`AI_POLICY.md`) : tout usage d'IA doit être
  déclaré (outil et étendue) ; l'auteur doit comprendre tout ce qu'il
  soumet ; les issues et discussions ne doivent pas être générées ; les
  images générées sont interdites ; « les PR de nouveaux contributeurs
  largement ou entièrement générées par des LLM ne seront pas
  acceptées ». Le `AGENTS.md` du dépôt va jusqu'à interdire aux agents
  de créer issues ou PR. À respecter à la lettre si l'on devait un jour
  y contribuer ; à retenir aussi comme signe de ce que ce projet a subi.

### 4.5 Limites, et pourquoi il existe quand même

- **Dépend entièrement de Warcraft Logs** : pas de rapport, pas
  d'analyse ; rapport privé, pas d'analyse [S11].
- **Analyse de rotation, pas de situation** : un temps de recharge gardé
  pour une mécanique est compté comme gaspillé ; les règles ignorent le
  contexte du combat [S11].
- Pourquoi il existe : les tableaux de Warcraft Logs sont bruts, et lire
  « ce qu'il aurait fallu faire » demande de connaître la spé. WoWAnalyzer
  met cette connaissance dans du code, une fois, pour tout le monde. Son
  intérêt pour ce dépôt-ci : c'est **le seul endroit public où les
  règles « bonne rotation » de chaque spé sont écrites en code lisible
  et sous une licence compatible**.

## 5. Wipefest

### 5.1 Ce que c'est

Un site qui prend **un combat de raid** (par lien Warcraft Logs, par
personnage ou par guilde) et le lit sous l'angle des **mécaniques**, pas
du DPS : dégâts évitables, durées de debuffs, timing des dispels,
soins ennemis, changements de tank, soaks, interruptions, potions,
morts. Trois vues [S12] :

- **Mechanics** : une ligne par mécanique du boss, avec une **note de 0 à
  100** (le raid a fait mieux que N % des kills de la semaine sur cette
  mécanique), un graphe des dégâts pris, une mini-timeline, une astuce
  et un court extrait vidéo tiré de Mythic Trap. Les mécaniques sont
  ordonnées par importance, calculée chaque jour : plus une mécanique
  est réussie sur les kills les plus propres, plus elle pèse.
- **Players** : la même chose joueur par joueur, avec un **Player Score**
  qui répond à « quelle serait la note du raid si tout le monde avait
  fait comme ce joueur sur cette mécanique ? », pondéré par l'importance,
  réduit en cas de mort précoce, et complété d'un score bonus pour ce
  que tout le monde n'a pas l'occasion de faire (interruptions, dispels,
  soaks). L'aide elle-même dit de le prendre « avec une pincée de sel ».
- **Timeline** : casts de boss importants, debuffs, temps de recharge de
  raid, morts, Bloodlust.

Plus un onglet **Guide** (les guides Mythic Trap), une **analyse
multi-pulls** (réservée aux abonnés : 50 pulls pour « Rare », 150 pour
« Legendary », partageable à la guilde), et un **bot Discord** qui
écoute un rapport et poste un résumé après chaque essai [S12].

### 5.2 Histoire

- **1er septembre 2017.** Annoncé sur MMO-Champion par **Yax** (Josh
  Yaxley), qui l'a écrit sur son temps libre pour aider sa propre guilde
  à affiner ses tactiques de progression. Dès le lancement : timelines,
  « insights », astuces, et les **configurations d'événements par boss
  ouvertes sur GitHub avec un guide de pull request** pour que la
  communauté contribue. Il dit limiter volontairement ce qu'il demande à
  l'API « pour garder une empreinte légère sur leurs serveurs » [S8].
- **Automne 2020.** Racheté par Warcraft Logs, « première addition à la
  famille ». Yax passe à plein temps sur les deux produits. Le gain qu'il
  met en avant : ne plus être limité par l'API et **avoir accès à chaque
  événement du log, positions comprises**, pour des insights « comme
  savoir qui est trop loin du Brutal Enforcer sur Vexiona » [S9]. On le
  retrouve en 2023 comme ingénieur de l'équipe, parlant priorisation et
  dette de maintenance [S5].

### 5.3 Comment ça marche

- **Avant le rachat** : un front Angular (c'est encore la coquille servie
  aujourd'hui [S32]) et un moteur TypeScript publié en paquet npm,
  `@wipefest/core`, sous **AGPL-3.0** : services de lecture de l'API v1
  de Warcraft Logs (rapport, combats, événements), `EventConfigService`
  qui charge la configuration du boss (quels sorts suivre, comment les
  afficher) depuis un dépôt séparé `Wipefest.EventConfigs`,
  `InsightService` qui produit les constats, `FightService` qui
  orchestre ; axios et RxJS [S33]. Le dépôt d'origine n'est plus en ligne
  (404) ; des forks subsistent.
- **Après le rachat** : accès direct aux données de Warcraft Logs, sans
  passer par l'API publique ni ses quotas, et scoring statistique contre
  un échantillon de kills des sept ou quatorze derniers jours, recalculé
  quotidiennement [S12]. Les scores joueurs « ont besoin de beaucoup de
  données réelles » : les premiers jours d'un tier ils peuvent manquer
  [S12].
- **Dépendances déclarées** : l'API Battle.net (personnages, guildes) et
  l'API Warcraft Logs. Pas d'API Wipefest pour les tiers : « utilisez
  l'API Warcraft Logs, toutes nos données en viennent » [S12].
- **Ne charge pas** : les rapports privés (mettre en « non listé »), le
  mode Raid Recherché, les rapports archivés de plus de deux ans [S12].

### 5.4 Modèle

Gratuit pour les kills ; les essais non aboutis (les wipes, donc
l'essentiel de la progression) et l'analyse multi-pulls sont réservés aux
abonnés Patreon (paliers « Rare » et « Legendary » ; un tiers citait
3 $/mois pour l'accès aux wipes, prix ancien et non vérifié pour 2026)
[S12][S34].

### 5.5 Pourquoi

Warcraft Logs répond à « combien » ; Wipefest répond à « **pourquoi on a
wipe** », ce qu'un chef de raid veut savoir entre deux essais, sans
ouvrir dix tableaux. Sa niche, dite par son auteur : « l'analyse
mécanique, qui n'avait pas autant d'attention à l'époque » [S9]. Sa
force vient de la note *contre les autres* : « 3 morts sur ce boss,
c'est en fait au-dessus de la moyenne des kills » est une information
qu'un log isolé ne peut pas donner.

## 6. Archon

### 6.1 Trois choses sous un nom

1. **L'entreprise** : le nom-ombrelle pris par RPG Logs LLC le 3 octobre
   2023, « pour regrouper nos produits sous une seule marque et lancer
   facilement de nouveaux outils qui ne trouvaient pas leur place sur
   nos anciens sites ». L'annonce dit elle-même « pas grand-chose de
   neuf... pour l'instant » [S13].
2. **Le site archon.gg** : d'abord un portail, puis depuis le 14 décembre
   2023 les **Build Guides et Tier Lists** (section 6.2), et l'hébergement
   de tous les articles d'aide et d'actualité du groupe (ce qui explique
   que l'aide de Warcraft Logs se lise aujourd'hui sur archon.gg).
3. **L'Archon App** (section 6.3), qui a remplacé tous les clients
   d'envoi du groupe en 2026.

### 6.2 Builds et Tier Lists : la méthode, telle qu'ils la publient

Article « Disclaimers & FAQ », mis à jour le 20 octobre 2025 [S35].

- **Ce qu'ils montrent** : par classe et spé, les talents, l'équipement,
  les enchantements, les gemmes, les consommables et les bijoux **les
  plus populaires** parmi les meilleurs parses, filtrables par boss, par
  difficulté, par donjon et niveau de clé ; une **priorité de stats** ;
  et quatre tier lists : débit (DPS/HPS en raid), cote en Mythique+,
  popularité (nombre de parses sur deux semaines), et survivabilité
  (l'inverse de la statistique de morts).
- **La métrique est la popularité, pas la puissance**, et ils le disent :
  « la plupart du temps le choix le plus populaire est le meilleur »,
  mais « un bijou de Mythique+ un peu moins bon sera plus populaire en
  début de saison parce qu'il est plus facile à obtenir ». D'où le
  premier avertissement de la page : « un ensemble agrégé ne s'applique
  pas forcément à votre situation ; **simulez-vous toujours** (Raidbots
  en Retail) ».
- **Échantillonnage** : par boss, les 50 % meilleurs classements (ou les
  1 000 meilleurs si c'est plus), après dédoublonnage ; ces jeux par
  boss sont ensuite fusionnés en « All Bosses ». Pour les « High Keys » :
  les 5 % meilleures clés par donjon et par spé, au moins 25 clés, jamais
  sous le niveau 20.
- **Débit** : le 95e percentile, corrigé de la variance par la **borne
  basse de l'intervalle de confiance à 95 %**. Idem pour la cote
  Mythique+.
- **Priorité de stats** : les stats lues au début du combat
  (`COMBATANT_INFO`), regroupées en tranches de 250 points de score ;
  deux stats dont les intervalles de confiance se recouvrent sont
  affichées côte à côte, sinon séparées par « > ».
- **Ce qu'ils ne voient pas** : les stats choisies sur les objets
  fabriqués (non journalisées par Blizzard), et les nouvelles stratégies
  tant qu'elles n'ont pas assez de volume, le temps que la popularité
  suive [S36].

C'est l'exact complément de Raidbots : Raidbots
**simule** un personnage précis avec SimulationCraft, de manière
déterministe ; Archon **observe** ce que des dizaines de milliers de
joueurs ont réellement porté et réussi. L'un ne remplace pas l'autre, et
Archon lui-même renvoie vers la simulation.

### 6.3 L'Archon App

Lancée hors bêta le 10 mars 2026 (Windows, Linux, macOS) [S23][S24] ;
remplace l'ancien uploader depuis le 29 juin 2026 [S25].

- Envoi de logs pour tous les jeux du groupe, détection automatique du
  jeu lancé, **auto-logging** sur contenu prédéfini (boss Mythique, clé
  au-dessus d'un niveau).
- **Enregistrement vidéo synchronisé avec le log** : on choisit le
  contenu à enregistrer, l'application filme, et la vidéo se relit à
  côté de la timeline et du replay 2D. La technique vient de **Warcraft
  Recorder**, un outil libre (Electron/React empaquetant OBS, qui
  détecte les rencontres en surveillant le fichier de log [S37]) dont
  le créateur, Alex, a rejoint l'équipe ; Warcraft Recorder reste libre
  et gratuit, et ses abonnés Pro obtiennent la navigation sans publicité
  sur les sites Archon [S23]. Stockage cloud « pour les points de vue de
  tout le groupe » annoncé comme à venir.
- Vue de rapport refaite dans l'application, filtres prédéfinis, pages
  de personnage, **group finder** et « alliés récents », un **addon
  d'infobulles** en jeu, et pour FFXIV et SWTOR un compteur de dégâts en
  overlay (proposé pour ces deux jeux seulement, pas pour WoW) [S24].
- L'application « n'est pas open source » [S23].

### 6.4 Partenaires, publicité, données

La page « Archon & External Partners » est franche [S28] :

- Régies publicitaires **Playwire** et **Nitro** ; plateformes d'analyse
  d'audience « anonymes et agrégées ».
- L'application embarque les bibliothèques **Overwolf** (`ow-electron`)
  pour la détection de jeu, les overlays en jeu, les raccourcis, la vidéo
  **et la publicité dans le client** : « nous ne pourrions
  (malheureusement) pas exister sans servir de publicité ». On peut
  désactiver presque tout par les réglages, et **Archon Lite** existe
  précisément pour ceux qui ne veulent aucune bibliothèque tierce : envoi
  de logs seulement, sans vidéo ni analyse post-pull.
- S'abonner désactive le suivi publicitaire.

Pour un utilisateur européen, les faits à connaître : société de droit
texan, hébergement AWS, conditions d'API sous juridiction du Texas, et
un journal de combat qui contient **les noms et les performances de tous
les membres du groupe**, pas seulement ceux de la personne qui l'envoie.
Un rapport public les publie tous. Les modes « non listé » et « privé »
existent pour cela.

### 6.5 Pourquoi Archon

Trois raisons lisibles dans leurs propres textes :

1. **Monétiser la donnée autrement que par le classement.** Les guides
   de builds occupent le terrain de Wowhead, d'Icy Veins et, en partie,
   de Raidbots, avec un argument que ceux-ci n'ont pas : « des millions
   de parses réels, pas de la théorie » [S36].
2. **Une marque pour six jeux.** Les joueurs ne savaient pas que FF Logs
   et Warcraft Logs étaient la même équipe [S13] ; un seul client pour
   tous les jeux « évite à l'équipe de maintenir une douzaine de
   programmes » [S25].
3. **Occuper tout l'entonnoir** : le fichier (App), l'envoi (App), la
   lecture (Warcraft Logs), le diagnostic (Wipefest, WoWAnalyzer), la
   vidéo (Warcraft Recorder), les guides (Mythic Trap), les
   recommandations (Builds). Chaque rachat a bouché un trou entre deux
   étages de la section 1.

## 7. Les quatre en un tableau

| | Warcraft Logs | WoWAnalyzer | Wipefest | Archon (Builds) |
|---|---|---|---|---|
| Question à laquelle il répond | Que s'est-il passé, et où est-ce que je me situe ? | Qu'aurais-je dû faire, moi, sur ma spé ? | Pourquoi le raid a-t-il wipe ? | Que portent et jouent ceux qui réussissent ? |
| Unité d'analyse | Un rapport, un combat, tout le monde | Un joueur, un combat | Un raid, un combat (ou N pulls) | Une spé, des milliers de kills |
| Entrée | `WoWCombatLog.txt` via l'App | Un lien de rapport Warcraft Logs | Un lien, un personnage, une guilde | Rien (interne) |
| Source des données | Le fichier envoyé | API v1 de Warcraft Logs | Données internes de Warcraft Logs (API v1 à l'origine) | Toute la base de Warcraft Logs |
| Méthode | Parsing, indexation par segment, classements par percentile | Modules de règles par spé, exécutés dans le navigateur | Configs d'événements par boss + scoring contre les kills récents | Popularité sur échantillons top 50 %, IC 95 % |
| Code | Fermé | **Ouvert, AGPL-3.0** | Moteur historique AGPL-3.0 ; site actuel fermé | Fermé |
| Prix | Gratuit + pub ; 2 / 5 / 10 $ | Gratuit ; Patreon | Kills gratuits ; wipes et multi-pulls par abonnement | Gratuit + pub |
| Origine | Kihra, 2013, États-Unis | Martijn Hols, 2017, Pays-Bas | Josh Yaxley, 2017 | RPG Logs LLC, 2023, Houston |
| Propriétaire en 2026 | Archon | Archon (2021) | Archon (2020) | Archon |

## 8. Ce qui en a été retenu pour LogsWoW

Ce document a été écrit avant l'outil. Voici ce qu'il a décidé.

- **Le fichier est libre, l'échelle ne l'est pas.** Le format est public,
  des analyseurs ouverts existent (WoWAnalyzer, le moteur historique de
  Wipefest, des parseurs communautaires du fichier vers JSON ou DuckDB
  [S38]), et **rien de tout cela ne dépend d'un site**. Ce qu'un outil
  personnel ne peut pas reproduire, c'est la comparaison contre tout le
  monde (percentiles, scores Wipefest, builds populaires). LogsWoW ne
  le prétend pas et le dit dans son README.
- **Un outil local sur son propre fichier n'a besoin d'aucune API**, donc
  d'aucune permission commerciale, d'aucun quota, et n'entre pas dans
  les interdictions des conditions d'utilisation (bases permanentes,
  canaux concurrents). Il garde aussi le fichier, et les noms des
  coéquipiers, sur la machine. C'est la règle numéro un du projet :
  aucune connexion réseau, jamais.
- **Le bug des soins manquants (2.4) est une limite du fichier, pas des
  sites.** LogsWoW le subit exactement comme eux, tant que Blizzard ne
  l'a pas corrigé.
- **Archon confirme de sa propre voix que la popularité n'est pas la
  puissance** et renvoie vers la simulation. Un outil qui lit un seul
  journal n'a de toute façon pas la masse de données pour faire ce
  qu'Archon fait ; il n'essaie pas.
- **Ce que la documentation publique disait du format s'est révélé
  faux sur trois points** dès le premier vrai fichier lu : la largeur du
  bloc de journalisation avancée, un champ de dégâts bruts avant le
  surplus, et un coup de mêlée écrit deux fois. Le détail est dans le
  `CLAUDE.md` du dépôt. La leçon vaut pour quiconque écrit un lecteur :
  mesurer dans le fichier, ne pas croire la page.
- **L'API a servi une fois, comme étalon, jamais comme dépendance.** Le
  2026-09-28, le propriétaire a créé un client API Warcraft Logs à son
  nom pour comparer cinq de ses clés, table par table puis coup par coup,
  aux chiffres de LogsWoW. Le script de récupération vivait hors du
  dépôt ; les données et les identifiants ont été supprimés après, et le
  client révoqué. Chaque écart expliqué a été remesuré dans le fichier
  lui-même avant que le code ne change : c'est le fichier qui fait foi,
  l'API a seulement dit où regarder. Le détail est dans `CLAUDE.md`.

## 9. Sources

Lues directement sauf mention. « archive » = instantané 2026 de
web.archive.org, les pages vivantes renvoyant 403.

- [S1] warcraft.wiki.gg, *COMBAT_LOG_EVENT* ; wowcoach.gg, *How to Enable
  Combat Logging in WoW Midnight* (2026).
- [S2] wowcoach.gg, même article (emplacement, tailles, addons,
  « le fichier n'est pas affecté par les valeurs secrètes »).
- [S3] warcraft.wiki.gg, *COMBAT_LOG_EVENT* (charge utile, paramètres
  avancés, lignes propres au fichier, note « plus accessible aux addons
  depuis 12.0.0, ADDON_ACTION_FORBIDDEN »).
- [S4] eu.forums.blizzard.com, *Healing data mismatch: In-game UI/Addons
  vs. Advanced Combat Log in Midnight* (23 mars - 5 mai 2026).
- [S4b] Recherche des hotfixes Midnight jusqu'au 10 septembre 2026 : aucune
  mention d'un correctif.
- [S5] archon.gg, *Reflecting on a Decade of Warcraft Logs* (5 mars 2023,
  archive) ; repris par Wowhead (article 331676).
- [S6] blizzpro.com, *Interview with Kihra from Warcraft Logs* (30
  décembre 2013).
- [S7] blizzardwatch.com, *Warcraft Logs looking for funding from Patreon*
  (22 avril 2015).
- [S8] mmo-champion.com, fil *Wipefest - a new web tool...* (1er septembre
  2017, par Yax).
- [S9] wowhead.com, *Warcraft Logs Acquires Wipefest* (article 318375,
  avec le message de Yax sur r/CompetitiveWoW).
- [S10] wowhead.com, *WoWAnalyzer Acquired by Warcraft Logs* (article
  324677, 29-30 octobre 2021).
- [S11] wowcoach.gg, *WarcraftLogs vs WoWAnalyzer vs WowCoach* (source
  concurrente, autopromotionnelle ; utilisée seulement pour les limites
  qu'elle décrit et que le code confirme).
- [S12] archon.gg, *How to Improve Your Raid With Wipefest* (24 juillet
  2025, archive) et *Wipefest: Frequently Asked Questions* (archive).
- [S13] archon.gg, *Introducing Archon* / *Announcement* (archive) ;
  wowhead.com, *Introducing Archon - Warcraft Logs Parent Company
  Rebranded* (3 octobre 2023).
- [S14] archon.gg, *Subscriber Benefits* (18 novembre 2024, archive).
- [S15] archon.gg, *Rankings and Parses* (11 février 2026, archive).
- [S16] news.blizzard.com, *How Midnight's Upcoming Game Changes Will
  Impact Combat Addons*.
- [S17] news.blizzard.com, *Combat Philosophy and Addon Disarmament in
  Midnight*.
- [S18] icy-veins.com, *Combat Addon Restrictions Eased in Midnight* ;
  us.forums.blizzard.com, *Is Warcraft logs going to die in Midnight?*
  (16 octobre 2025).
- [S19] warcrafttavern.com, *Blizzard Walks Back Some API Changes for
  Addons in Midnight* (3 octobre 2025).
- [S20] github.com/aza547/wow-recorder (README : addons de
  journalisation recommandés).
- [S21] archon.gg, *API Documentation* (2 décembre 2025, archive) ;
  forums.combatlogforums.com, *[API v2] requests limit* (2024).
- [S22] archon.gg, *RPGLogs' API Terms of Service* (archive).
- [S23] warcrafttavern.com, *Warcraftlogs Launches New App Including
  Video Recording* (10 mars 2026) ; archon.gg, *Introducing: Archon App*
  (archive).
- [S24] wowhead.com, *Record and Review Your Gameplay With the Archon
  App* (article 380702).
- [S25] wowhead.com, *WarcraftLogs Uploader Transitioning to Archon App
  on June 29th* (article 381785).
- [S26] github.com/WarcraftLogs (organisation sans dépôt public).
- [S27] archon.gg, *Death Statistics* (13 décembre 2023, archive).
- [S28] archon.gg, *Archon & External Partners* (archive).
- [S29] mmo-champion.com, *Announcing WoWAnalyzer* (29 mai 2017, par
  Zerotorescue).
- [S30] github.com/MartijnHols (profil : Pays-Bas ; WoWAnalyzer épinglé).
- [S31] github.com/WoWAnalyzer/WoWAnalyzer, cloné le 2026-09-16 (commit
  32a9285, 14 septembre 2026) : `LICENSE`, `README.md`, `AI_POLICY.md`,
  `AGENTS.md`, `docs/Patches-and-raids.md`, `src/common/fetchWclApi.ts`,
  `src/common/makeWclApiUrl.ts`, `src/interface/report/hooks/useEvents.ts`,
  `src/game/VERSIONS.ts`, `src/interface/report/PATCHES.ts`,
  `src/analysis/retail/*/*/CONFIG.tsx`.
- [S32] wipefest.gg, page d'accueil (coquille Angular ; description
  « Raid summaries based on Warcraft Logs »).
- [S33] github.com/yajinni/Wipefest.Core (fork du dépôt d'origine
  JoshYaxley/Wipefest.Core, aujourd'hui en 404) ; npm `@wipefest/core`,
  `@wipefest/cli`.
- [S34] hrothmar.com, *Become a better raider with Wipefest.gg* (prix de
  3 $/mois, date ancienne).
- [S35] archon.gg, *Archon: Disclaimers & FAQ* (20 octobre 2025, archive).
- [S36] wowcarry.com, *Archon Builds and Tier Lists: Launch and 2026
  State* (14 décembre 2023 pour le lancement).
- [S37] github.com/aza547/wow-recorder (README).
- [S38] github.com/rp4rk/WoWP (parseur du fichier vers JSON) ;
  github.com/xiaosongz/sd_wcl (fichier vers DuckDB) : cités comme
  existants, non lus en détail.
- [S39] mythictrap.com (page d'accueil et « Useful Websites ») ;
  archon.gg, *Aberrus Guides on Warcraft Logs*.
