# Découpage en pulls : ce que d'autres font, et ce qui reste à vérifier ici

Recherche du 2026-09-26/27, à la demande du propriétaire : *« regarde comment
ils font pour récupérer les pulls (chaque pull), pour peut-être affiner le
nôtre »*. Aucune modification n'a été faite à `logswow/` pendant cette
recherche -- ce document existe pour que l'audit annoncé par le propriétaire
n'ait pas à refaire le travail, et pour lister, honnêtement, ce qui a été
regardé, ce qui en est sorti, et ce qui reste une question ouverte plutôt
qu'une réponse.

## 0. Ce qui a été consulté

- **wowumbra.gg/methodology** et **wowumbra.gg/about** -- pages publiques,
  lues via récupération web, pas de compte créé.
- **github.com/WoWAnalyzer/WoWAnalyzer** -- dépôt public, AGPL-3.0, cloné
  en lecture seule dans un répertoire temporaire de session et **supprimé
  aussitôt la lecture terminée** (rien n'a été copié dans ce dépôt-ci, la
  même règle que `LOGS-SITES-RESEARCH.md` suit déjà pour la même source).

Aucun compte, aucun appel d'API, aucun fichier de log réel impliqué.

## 1. wowumbra.gg ne documente pas de découpage -- parce qu'il n'en a pas

La page `/methodology` explique uniquement le système de notation (grade
Umbra : dégâts, soins, utilité, survie, usage des cooldowns, casts par
minute, pondérés par rôle et par niveau de clé). Rien sur des seuils de
temps, rien sur `ENCOUNTER_START`, rien sur wipe vs kill.

La page `/about` dit pourquoi : le site ne lit aucun fichier de log.
Citation exacte :

> "Run a key, upload via Archon (the official WCL uploader; the addon
> handles combat logging), and look yourself up on the site."
>
> "We can't scrape WCL for everyone, and we don't want to."

WoWUmbra.gg est une couche de notation au-dessus des données déjà
traitées par Warcraft Logs (uploadées via l'app Archon). Le découpage en
pulls qu'il affiche ("pull-by-pull recap... the pulls you died in") est
entièrement hérité de WCL -- il n'a pas d'algorithme propre à en tirer.

## 2. WoWAnalyzer confirme un fait qui n'était pas documenté ailleurs : WCL découpe le trash intra-clé lui-même, côté serveur

C'était la vraie question ouverte laissée par `LOGS-SITES-RESEARCH.md`
(section 3.3) : ce document savait déjà que WCL borne les combats de boss
par `ENCOUNTER_START`/`ENCOUNTER_END` et une clé Mythic+ par
`CHALLENGE_MODE_START`/`CHALLENGE_MODE_END`, mais pas comment le trash
*entre* deux boss, à l'intérieur d'une même clé, était traité.

Le code source de WoWAnalyzer répond, dans `src/parser/core/Fight.ts` --
c'est la définition du format exact renvoyé par l'API de Warcraft Logs
pour une clé Mythic+ :

```ts
interface WCLDungeonPull {
  id: number;
  boss: number;      // 0 pour un pull de trash, l'id de l'encounter sinon
  start_time: number;
  end_time: number;
  name: string;
  kill?: boolean;
  enemies?: number[][];
}

export interface WCLFight {
  ...
  dungeonPulls?: WCLDungeonPull[];
  ...
}
```

Et l'usage, dans `src/interface/report/Results/Header/FilterButton.tsx`,
confirme la lecture : chaque entrée de `dungeonPulls` est étiquetée
`Boss N` si `boss > 0`, `Pull N` sinon, avec son propre nom, son propre
intervalle de temps, et un `kill` optionnel.

**Ce que ça établit :** Warcraft Logs ne traite pas le trash d'une clé
comme un intervalle continu fondu dans le pull du boss suivant. Il le
découpe en pulls à part entière, chacun avec ses propres bornes -- ce qui
est la même famille d'approche que le silence de groupe que LogsWoW
utilise déjà (section 3), pas une manière fondamentalement différente de
poser la question.

**Ce que ça n'établit pas, et qui reste fermé :** WoWAnalyzer ne calcule
rien de tout ça lui-même -- aucune trace, dans tout le dépôt, d'un
algorithme de segmentation côté client (pas de seuil de temps, pas de
détection de silence). `dungeonPulls` est consommé tel quel, uniquement
pour peupler un menu et pour une vérification de mécanique dans un seul
module de classe. Le calcul se fait sur le serveur de Warcraft Logs, qui
est fermé (aucun dépôt public sur son organisation GitHub, déjà noté par
`LOGS-SITES-RESEARCH.md` section 3.3). **Le seuil exact, ou l'algorithme
exact, que WCL emploie pour couper un pull de trash reste inconnu.** Rien
trouvé dans cette recherche ne le révèle.

## 3. Ce que LogsWoW fait aujourd'hui (l'état des lieux, pour l'audit)

Résumé de ce qui existe déjà dans `logswow/segment.py` et
`logswow/analysis.py`, sans rien y toucher pendant cette recherche :

- **Bornes de haut niveau, mesurées et non supposées** (`CLAUDE.md`) :
  un combat de boss est borné par `ENCOUNTER_START`/`ENCOUNTER_END`, une
  clé Mythic+ par `CHALLENGE_MODE_START`/`CHALLENGE_MODE_END`. Un pull
  tronqué par une coupure du fichier se termine sur le dernier événement
  réellement présent plutôt que sur une durée de zéro.
- **Découpage intra-clé par silence** : `PULL_GAP_MS = 6000` -- un pull
  se termine après 6 secondes sans que le groupe n'infocte ni ne subisse
  de dégâts. Réglable par `--pull-gap` en ligne de commande, avec un
  plancher d'une seconde.
- **Les miettes sont jetées, pas cachées** : `MIN_PULL_SHARE = 0.001`
  (un millième des dégâts totaux de la course) -- un "pull" plus petit
  que ça est écarté. Mesuré sur une vraie clé : deux pulls de 7,9k et
  14,1k dégâts sur un total de 531M ont été identifiés comme des dots
  finissant sur quelque chose déjà mort ; le plus petit pull réel de
  cette même course faisait 20M, deux ordres de grandeur au-dessus. Le
  nombre de pulls écartés est affiché, jamais masqué.
- **Trash vs boss, à l'intérieur d'un pull** : le nom du boss vient des
  lignes `ENCOUNTER_START` de la clé ; les unités portant exactement ce
  nom (images, adds qui partagent le nom) comptent comme boss -- limite
  connue et documentée comme telle, pas un bug. Le tableau des pulls
  sépare "sur le boss" et "sur les trash".
- **Regroupement des ennemis par nom, pas par GUID** : une clé rencontre
  parfois trente unités appelées "Diablotin sauvage" ; `Enemy.units`
  garde les GUID distincts pour dire combien il y en avait, mais le
  panneau reste un par nom.
- **Le trash hors pull n'est pas analysé pour rien** : le segment de
  repli ("session") entre deux pulls réels est jeté par `finish()`
  plutôt qu'alimenté en événements -- correction de performance mesurée
  (10,7 s / 67 Mo avant, 8,4 s / 25 Mo après sur un fichier de 200 000
  lignes majoritairement hors pull).
- **Confirmé sur cinq vrais logs** (31 à 231 Mo) et un export Warcraft
  Logs de la même clé Nalorakk : durée du combat exacte à la dixième de
  seconde, les neuf morts dans le même ordre, le classement de chaque
  tableau identique. 146 tests passent, `tools/check-invariants.py`
  confirme les identités arithmétiques sur les cinq logs.

## 4. Pistes ouvertes -- des questions pour l'audit, pas des décisions

Rien ci-dessous n'a été tranché ni implémenté. Ce sont des points que
cette recherche a fait remonter et qui méritent d'être posés pendant
l'audit annoncé, avec leur statut de preuve actuel :

1. **Un pull de trash n'a pas de verdict kill/wipe explicite ici.**
   `WCLDungeonPull.kill` existe côté Warcraft Logs même pour un pull de
   trash. LogsWoW a un `success` pour un combat de boss (depuis
   `ENCOUNTER_END`), mais rien d'équivalent, actuellement, pour dire si
   un pull de trash a été terminé ou abandonné (un wipe sur du trash
   pendant une clé chronométrée est un événement réel). À vérifier si
   c'est un manque ou un renoncement déjà voulu ailleurs dans le projet.
2. **Le seuil `PULL_GAP_MS = 6000` n'a été mesuré que sur les clés de ce
   groupe**, qui chain-pull. Aucune contre-preuve externe (WCL ne publie
   pas le sien, voir section 2) ne dit si 6 s est trop court pour un
   groupe qui joue plus lentement, ou trop long pour un qui enchaîne
   encore plus vite. Rien à changer sans données -- juste à savoir que
   ce nombre n'a qu'une seule source.
3. **Deux boss identiques par nom, consécutifs dans la même clé**, sont
   une limite déjà documentée comme telle dans `CLAUDE.md` ("known limit
   rather than a bug") plutôt que vérifiée sur un vrai log qui contient
   ce cas précis -- à confirmer si l'occasion se présente.
4. **`enemies` par pull (la liste des unités engagées) existe côté WCL**
   et n'a pas d'équivalent direct ici groupé par pull plutôt que par nom
   sur toute la clé. Pas nécessairement utile -- à juger pendant l'audit
   si un besoin réel s'en dégage, pas à ajouter par anticipation.
5. **La documentation publique de l'API GraphQL de Warcraft Logs**
   (schema public, pas le serveur lui-même) n'a pas été consultée cette
   session, faute de portée -- ce serait la prochaine piste logique si
   quelqu'un veut aller plus loin que ce que le code de WoWAnalyzer
   laisse voir, sans que ça change quoi que ce soit à la règle "aucun
   réseau" du paquet lui-même : ce serait toujours de la recherche, jamais
   un appel fait par `logswow/` en fonctionnement.

## 5. Ce que ce document n'est pas

Une recherche, pas un plan de travail approuvé. Personne n'a demandé de
changer `PULL_GAP_MS`, d'ajouter un verdict par pull de trash, ou quoi
que ce soit d'autre listé en section 4 -- ce sont des questions à poser,
pas des tâches actées. Le propriétaire a explicitement demandé de ne rien
modifier à la version actuelle pendant cette recherche, et rien ne l'a
été.

## 6. Suite donnée par l'audit du 2026-09-27

L'audit annoncé a eu lieu, sur deux vrais journaux fournis pendant sa
réalisation (une soirée de raid héroïque, une session Mythique+). Ce qu'il
a fait des questions de la section 4 :

1. **Verdict d'un pull de boss : corrigé.** Le badge « boss » de la table
   des pulls était vert quelle que soit l'issue ; sur une vraie clé, le
   wipe et le kill sur Mchimba portaient le même. Il dit maintenant
   « réussite » (vert) ou « échec » (rouge), d'après l'`ENCOUNTER_END` de
   la rencontre que le pull recouvre. La même correction a révélé un
   défaut plus large : une rencontre dont aucune unité ne porte le nom
   (« Le conseil des tribus », « Viperis et Aspis », « Autel Annelé »)
   avait 0 dégât « sur le boss ». Ses bornes `ENCOUNTER_START`/`END`
   servent désormais à la reconnaître. Un pull de **trash** n'a toujours
   pas de verdict : le fichier n'en donne pas, et rien n'est affiché.
2. **`PULL_GAP_MS` : une seconde source, et une règle ajoutée.** Sur les
   quatre clés d'un autre soir, 6 s donne 11, 8, 2 et 12 pulls, dans la
   plage déjà mesurée. Mais une rencontre de boss était coupée en deux
   par une accalmie de plus de 6 s : un pull contenu dans une rencontre
   ne se coupe plus.
3. **Deux boss homonymes consécutifs** : toujours pas observés.
4. **`enemies` par pull** : inchangé, aucun besoin ne s'en est dégagé.
5. **API GraphQL de Warcraft Logs** : non consultée ; ce n'était pas
   l'objet d'un audit de code.
