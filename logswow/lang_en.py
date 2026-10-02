# SPDX-License-Identifier: AGPL-3.0-or-later
"""English: every French text of the interface, and its translation.

The keys are the French texts exactly as the code writes them; a test
fails when one is missing here, or when a translation does not keep
the original's %-placeholders and HTML tags in the same order.
`%.0s` swallows an argument: French passes a narrow no-break space
before a colon, which English does not want.
"""

TEXTS = {
    # analysis
    'source non nommée par le journal':
        'source the log does not name',
    'Tanks':
        'Tanks',
    'Soigneurs':
        'Healers',
    'Rôle non indiqué':
        'Role not given',
    # cli
    '\r  %s lignes lues...':
        '\r  %s lines read...',
    'Fichier introuvable : %s\n':
        'File not found: %s\n',
    '%s est un dossier, pas un fichier de journal. Cherchez-y WoWCombatLog.txt.\n':
        '%s is a folder, not a log file. Look for WoWCombatLog.txt inside it.\n',
    'Impossible de lire %s : %s\n':
        'Cannot read %s: %s\n',
    "Aucun combat n'a été trouvé dans %s. Le fichier est peut-être vide, ou écrit par une version du client que ce lecteur ne comprend pas : `diagnose` dit ce qui a été lu.\n":
        'No fight was found in %s. The file may be empty, or written by a client version this reader does not understand: `diagnose` says what was read.\n',
    "Refus d'écrire le rapport par-dessus le journal lui-même (%s). Choisissez un autre nom avec -o.\n":
        'Refusing to write the report over the log itself (%s). Choose another name with -o.\n',
    '%s est un dossier : donnez un nom de fichier avec -o.\n':
        '%s is a folder: give a file name with -o.\n',
    "%s existe et n'est pas un rapport LogsWoW : refus de l'écraser. Choisissez un autre nom, ou ajoutez --force si c'est voulu.\n":
        '%s exists and is not a LogsWoW report: refusing to overwrite it. Choose another name, or add --force if that is intended.\n',
    "%s existe et n'est pas un dossier : donnez un autre nom avec -o.\n":
        '%s exists and is not a folder: give another name with -o.\n',
    "Refus d'écrire les pages dans le dossier du journal lui-même (%s). Donnez un autre dossier avec -o.\n":
        "Refusing to write the pages into the log's own folder (%s). Give another folder with -o.\n",
    "%s contient déjà autre chose qu'un rapport LogsWoW : refus d'y écrire. Choisissez un autre dossier, ou ajoutez --force si c'est voulu.\n":
        '%s already holds something other than a LogsWoW report: refusing to write there. Choose another folder, or add --force if that is intended.\n',
    'Aucun combat ne correspond à --only %r. Utilisez `list` pour les voir.\n':
        'No fight matches --only %r. Use `list` to see them.\n',
    "Impossible d'écrire %s : %s\n":
        'Cannot write %s: %s\n',
    '%d combat(s) retenu(s) sur %d, %s lignes lues en %.1f s':
        '%d fight(s) kept of %d, %s lines read in %.1f s',
    '%d lignes non comprises -- lancez `diagnose` pour voir lesquelles':
        '%d lines not understood -- run `diagnose` to see which',
    'Rapport écrit : %s':
        'Report written: %s',
    'Combat':
        'Fight',
    'Durée':
        'Duration',
    'Dégâts':
        'Damage',
    'Morts':
        'Deaths',
    'Aucun dossier Logs trouvé aux emplacements habituels.':
        'No Logs folder found in the usual places.',
    'Cherchez WoWCombatLog.txt sous _retail_/Logs dans votre installation,':
        'Look for WoWCombatLog.txt under _retail_/Logs in your installation,',
    "puis donnez son chemin complet, entre guillemets s'il contient des espaces :":
        'then give its full path, in quotes if it contains spaces:',
    '  report "/chemin/vers/World of Warcraft/_retail_/Logs/WoWCombatLog-....txt"':
        '  report "/path/to/World of Warcraft/_retail_/Logs/WoWCombatLog-....txt"',
    "Pas d'écran disponible pour ouvrir la fenêtre : utilisez les commandes (voir --help).\n":
        'No screen available to open the window: use the commands (see --help).\n',
    "%r n'est pas un nombre de secondes":
        '%r is not a number of seconds',
    '%r : il faut un nombre de secondes entre 0 et 86400':
        '%r: a number of seconds between 0 and 86400 is needed',
    "%r n'est pas un nombre entier":
        '%r is not a whole number',
    '%r : il faut un nombre supérieur à zéro':
        '%r: a number above zero is needed',
    "langue de l'interface et du rapport : auto (celle du système, l'anglais pour une langue sans traduction), fr, en, de ou es":
        "language of the interface and the report: auto (the system's, English for a language with no translation), fr, en, de or es",
    'Lit un journal de combat de World of Warcraft, en local, sans rien envoyer nulle part.':
        'Reads a World of Warcraft combat log, locally, without sending anything anywhere.',
    'sans la progression ni le résumé : seulement les erreurs':
        'no progress or summary: errors only',
    'chemin du fichier WoWCombatLog.txt':
        'path to the WoWCombatLog.txt file',
    "année, pour les journaux dont l'horodatage n'en porte pas":
        'year, for logs whose timestamps carry none',
    'SECONDES':
        'SECONDS',
    'silence nécessaire pour séparer deux pulls (défaut %d s) ; baissez-le si vos packs sont regroupés, montez-le si un pull unique est coupé en deux':
        'silence needed to separate two pulls (default %d s); lower it if your packs are grouped together, raise it if a single pull is cut in two',
    'produit le rapport HTML':
        'writes the HTML report',
    'fichier de sortie (.html)':
        'output file (.html)',
    "ne pas mettre l'ordre des sorts de chaque joueur : la page est environ deux fois plus légère":
        "leave out each player's cast order: the page is about half the size",
    'présentation du rapport : onglets (un fichier, un combat et une catégorie à la fois, par défaut), pages (un dossier, une page par combat) ou longue (tout sur une seule page)':
        'report layout: onglets (one file, one fight and one section at a time, the default), pages (a folder, one page per fight) or longue (everything on one page)',
    "écraser le fichier de sortie même s'il n'est pas un rapport LogsWoW (jamais le journal lu)":
        'overwrite the output file even if it is not a LogsWoW report (never the log being read)',
    'NUMÉRO|NOM':
        'NUMBER|NAME',
    "n'inclure qu'un combat : son numéro dans `list`, ou un bout de son nom":
        'include only one fight: its number in `list`, or part of its name',
    'LANGUE':
        'LANGUAGE',
    'langue des liens Wowhead : auto (celle du système), fr, en, de, es, it, pt, ru, ko, zh, ou off pour ne mettre aucun lien':
        "language of the Wowhead links: auto (the system's), fr, en, de, es, it, pt, ru, ko, zh, or off for no links",
    'liste les combats du fichier':
        'lists the fights in the file',
    'montre ce que le lecteur a compris du fichier':
        'shows what the reader understood of the file',
    "s'arrêter après N événements":
        'stop after N events',
    'cherche le dossier Logs du jeu':
        "looks for the game's Logs folder",
    "ouvre la fenêtre (c'est aussi ce que fait la commande sans rien)":
        'opens the window (which is also what the command does with nothing typed)',
    '\nInterrompu.\n':
        '\nInterrupted.\n',
    # diagnose
    'Fichier    : %s':
        'File       : %s',
    'Taille     : %s, %s lignes, %s événements':
        'Size       : %s, %s lines, %s events',
    'Durée      : %s':
        'Duration   : %s',
    'DISPOSITION MESURÉE DANS CE FICHIER':
        'LAYOUT MEASURED IN THIS FILE',
    '  bloc avancé         : %d champs  (votes: %s)':
        '  advanced block      : %d fields  (votes: %s)',
    '    votes à égalité, départage par : %s':
        '    tied vote, settled by: %s',
    '  champ baseAmount    : %s  (position du -1: %s)':
        '  baseAmount field    : %s  (position of the -1: %s)',
    'présent':
        'present',
    'absent':
        'absent',
    '  champ hideCaster    : %s  (%s)':
        '  hideCaster field    : %s  (%s)',
    '  journalisation avancée : %s':
        '  advanced logging    : %s',
    'oui':
        'yes',
    'non -- positions et points de vie absents':
        'no -- positions and health missing',
    '  événements avec bloc avancé : %d sur %d':
        '  events with an advanced block : %d of %d',
    '  points de vie incohérents   : %d (courants > maximum ; ignorés pour les courbes de vie ennemies)':
        '  inconsistent health : %d (current > maximum; left out of the enemy health curves)',
    'COMBATS DÉLIMITÉS : %d':
        'FIGHTS FOUND: %d',
    'JOUEURS VUS : %d':
        'PLAYERS SEEN: %d',
    'ÉVÉNEMENTS (%d types)':
        'EVENTS (%d types)',
    '[SCHÉMA INCONNU] ':
        '[UNKNOWN SCHEME] ',
    'LIGNES NON RÉSOLUES':
        'UNRESOLVED LINES',
    'LIGNES NON RÉSOLUES : aucune':
        'UNRESOLVED LINES: none',
    'PROBLÈMES DE LECTURE : %d':
        'READ PROBLEMS: %d',
    '    ligne %s : %s | %s':
        '    line %s: %s | %s',
    # encounters
    'Rencontre':
        'Encounter',
    # events
    'événement inconnu':
        'unknown event',
    'champs de base manquants':
        'base fields missing',
    'ligne trop courte : %d champs pour un préfixe de %d':
        'line too short: %d fields for a prefix of %d',
    'nombre de champs inattendu : %d après le préfixe, attendu %s, ou cela +%d':
        'unexpected number of fields: %d after the prefix, expected %s, or that +%d',
    # gui
    "La fenêtre de LogsWoW a besoin de Tkinter, qui fait partie de Python mais\nque certaines distributions Linux livrent à part. Pour l'installer :\n  Linux Mint, Ubuntu, Debian : sudo apt install python3-tk\n  Fedora                     : sudo dnf install python3-tkinter\n  Arch, Manjaro              : sudo pacman -S tk\n  openSUSE                   : sudo zypper install python3-tk\n  macOS (Homebrew)           : brew install python-tk\nSous Windows, et sous macOS avec l'installateur de python.org, il est déjà là.\nLes commandes du terminal fonctionnent sans lui (voir ci-dessous).\n":
        'The LogsWoW window needs Tkinter, which is part of Python but\nwhich some Linux distributions ship separately. To install it:\n  Linux Mint, Ubuntu, Debian : sudo apt install python3-tk\n  Fedora                     : sudo dnf install python3-tkinter\n  Arch, Manjaro              : sudo pacman -S tk\n  openSUSE                   : sudo zypper install python3-tk\n  macOS (Homebrew)           : brew install python-tk\nOn Windows, and on macOS with the python.org installer, it is already there.\nThe terminal commands work without it (see below).\n',
    'Go':
        'GB',
    'Mo':
        'MB',
    'Ko':
        'KB',
    '%d o':
        '%d B',
    'Onglets (un fichier)':
        'Tabs (one file)',
    'Pages (un dossier)':
        'Pages (a folder)',
    'Une seule longue page':
        'One long page',
    "Impossible d'écrire %s : %s":
        'Cannot write %s: %s',
    'Choisissez un journal, puis « Lire ce journal ».':
        'Choose a log, then “Read this log”.',
    "Tout se passe sur cet ordinateur : aucune donnée n'est envoyée.":
        'Everything happens on this computer: no data is sent.',
    ' 1. Le journal ':
        ' 1. The log ',
    'Fichier':
        'File',
    'Date':
        'Date',
    'Taille':
        'Size',
    'Dossier':
        'Folder',
    'Choisir un autre fichier…':
        'Choose another file…',
    'Actualiser la liste':
        'Refresh the list',
    'Lire ce journal':
        'Read this log',
    'Silence entre deux pulls : ':
        'Silence between two pulls: ',
    'Annuler':
        'Cancel',
    ' 2. Les combats ':
        ' 2. The fights ',
    'Issue':
        'Outcome',
    'Tout sélectionner':
        'Select all',
    ' 3. Le rapport ':
        ' 3. The report ',
    'Ordre des sorts de chaque joueur (la page est environ deux fois plus lourde)':
        "Each player's cast order (the page is about twice as large)",
    'Présentation :':
        'Layout:',
    "Créer le rapport et l'ouvrir":
        'Create the report and open it',
    'Ouvrir le dossier du rapport':
        "Open the report's folder",
    '%d/%m/%Y %H:%M':
        '%Y-%m-%d %H:%M',
    "Aucun journal trouvé aux emplacements habituels : « Choisir un autre fichier… » pour l'indiquer.":
        'No log found in the usual places: “Choose another file…” to point to one.',
    'Choisir un journal de combat':
        'Choose a combat log',
    'Journaux de combat':
        'Combat logs',
    'Fichiers texte':
        'Text files',
    'Tous les fichiers':
        'All files',
    'Lecture de %s…':
        'Reading %s…',
    'Impossible de lire %s : %s':
        'Cannot read %s: %s',
    'Erreur inattendue en lisant le journal :\n\n':
        'Unexpected error while reading the log:\n\n',
    'Dans quel dossier écrire les pages ?':
        'Which folder should the pages go in?',
    'Où écrire le rapport ?':
        'Where should the report go?',
    'Page web':
        'Web page',
    'Écriture du rapport (%s)…':
        'Writing the report (%s)…',
    'Erreur inattendue en écrivant le rapport :\n\n':
        'Unexpected error while writing the report:\n\n',
    'Lecture… %s, %s lignes lues':
        'Reading… %s, %s lines read',
    ', encore environ %s':
        ', about %s left',
    '%d s':
        '%d s',
    '%d min %02d s':
        '%d min %02d s',
    "Aucun combat trouvé dans ce fichier : il est peut-être vide, ou /combatlog n'était pas lancé.":
        'No fight found in this file: it may be empty, or /combatlog was not running.',
    '%s, %s lignes lues en %.0f s%s.':
        '%s, %s lines read in %.0f s%s.',
    ', %d non comprises':
        ', %d not understood',
    'Lecture annulée.':
        'Reading cancelled.',
    'La lecture a échoué.':
        'Reading failed.',
    "Le rapport n'a pas été écrit.":
        'The report was not written.',
    '%s sur %d dans le rapport':
        '%s of %d in the report',
    # i18n
    'Attaque':
        'Melee',
    # parse
    'marqueur -1 : %s':
        '-1 marker: %s',
    'puis proximité avec %d':
        'then closeness to %d',
    '%d votes / %d événements':
        '%d votes / %d events',
    'ligne sans le séparateur de deux espaces':
        'line without the two-space separator',
    'horodatage illisible':
        'unreadable timestamp',
    "nom d'événement illisible":
        'unreadable event name',
    # report
    'aucun':
        'none',
    "<span class='pill ok'>boss &middot; réussite</span>":
        "<span class='pill ok'>boss &middot; kill</span>",
    "<span class='pill ko'>boss &middot; échec</span>":
        "<span class='pill ko'>boss &middot; wipe</span>",
    'tank':
        'tank',
    'soigneur':
        'healer',
    'DPS':
        'DPS',
    ', par une invocation':
        ', through a summon',
    'Ouvert par %s%s: %s':
        'Opened by %s%.0s: %s',
    'bêta':
        'beta',
    '<b>%s</b> a agi en premier, sur %s%s: %s':
        '<b>%s</b> acted first, on %s%.0s: %s',
    ', %s%ss avant le premier coup':
        ', %s%ss before the first hit',
    '%s; %s%ss plus tôt, %s avait aidé <b>%s</b> (%s)':
        '%.0s; %s%ss earlier, %s had helped <b>%s</b> (%s)',
    'Premier coup reçu par chaque ennemi (%s)':
        'First hit each enemy took (%s)',
    ' %s%s: aucune unité ne porte le nom de la rencontre (un conseil, par exemple), donc tous les dégâts infligés pendant sa durée sont comptés sur le boss.':
        " %s%.0s: no unit bears the encounter's name (a council, for instance), so all the damage dealt while it lasted counts as on the boss.",
    '<tr><td colspan=7 class=dim>Aucun combat délimité dans ce fichier.</td></tr>':
        '<tr><td colspan=7 class=dim>No fight found in this file.</td></tr>',
    "<h1>Rapport de combat</h1><p class=sub>%s &middot; %s lignes, %s événements &middot; généré le %s par LogsWoW %s</p><div class=note><b>Tout est resté sur cette machine.</b> Ce rapport a été produit en lisant le fichier de journal directement&nbsp;: aucun envoi, aucun compte, aucune connexion. La page est autonome, elle s'ouvre hors ligne.</div><div class=grid>%s</div><h2>Combats</h2><div class=card><table><tr><th>Combat</th><th class=n>Durée</th><th class=n>Dégâts</th><th class=n>Soins</th><th class=n>Pulls</th><th class=n>Joueurs</th><th class=n>Morts</th></tr>%s</table></div>":
        '<h1>Combat report</h1><p class=sub>%s &middot; %s lines, %s events &middot; generated on %s by LogsWoW %s</p><div class=note><b>Everything stayed on this machine.</b> This report was produced by reading the log file directly: nothing sent, no account, no connection. The page stands alone and opens offline.</div><div class=grid>%s</div><h2>Fights</h2><div class=card><table><tr><th>Fight</th><th class=n>Duration</th><th class=n>Damage</th><th class=n>Healing</th><th class=n>Pulls</th><th class=n>Players</th><th class=n>Deaths</th></tr>%s</table></div>',
    'Taille du fichier':
        'File size',
    'Durée couverte':
        'Time covered',
    'Pulls de boss':
        'Boss pulls',
    'Wipes de boss':
        'Boss wipes',
    'Clés mythiques':
        'Mythic keys',
    'Clés hors des temps':
        'Keys over time',
    'Clés non terminées':
        'Unfinished keys',
    'Lignes incomprises':
        'Lines not understood',
    "<h2 id='s%d'>%s%s</h2><p class=sub>%s &middot; %s &middot; %s de dégâts, %s de soins &middot; %s%s</p>":
        "<h2 id='s%d'>%s%s</h2><p class=sub>%s &middot; %s &middot; %s damage, %s healing &middot; %s%s</p>",
    ' &middot; journal interrompu':
        ' &middot; log cut short',
    'Dégâts infligés':
        'Damage done',
    'Soins effectifs':
        'Effective healing',
    "<div class=note><b>%s de dégâts ne sont comptés pour personne.</b> Ils viennent d'unités alliées qui n'appartiennent à aucun joueur nommé par le journal%s: %s. Faute de savoir à qui les attribuer, ils ne sont ni dans le total ci-dessus ni dans la ligne d'un joueur.</div>":
        "<div class=note><b>%s of damage is counted for nobody.</b> It comes from friendly units that belong to no player the log names%.0s: %s. With no way of knowing whom to credit, it is neither in the total above nor in any player's row.</div>",
    '<th class=n>sur le boss</th><th class=n>sur les trash</th>':
        '<th class=n>on the boss</th><th class=n>on trash</th>',
    "<h3>%s</h3><div class=card><table><tr><th class=n>#</th><th class=n>Début</th><th class=n>Durée</th><th>Ce qui a été engagé</th><th class=n>Dégâts</th>%s<th class=n>Subis</th><th class=n>Morts</th></tr>%s</table><p class=dim style='margin:10px 0 0;font-size:12px'>Un pull se termine quand le groupe passe plus de %s sans infliger ni subir de dégâts. Un groupe qui enchaîne les packs sans pause les verra donc regroupés%s: <code>--pull-gap</code> change ce seuil, sauf à l'intérieur d'une rencontre de boss, qui reste toujours un seul pull.%s%s</p></div>":
        "<h3>%s</h3><div class=card><table><tr><th class=n>#</th><th class=n>Start</th><th class=n>Duration</th><th>What was engaged</th><th class=n>Damage</th>%s<th class=n>Taken</th><th class=n>Deaths</th></tr>%s</table><p class=dim style='margin:10px 0 0;font-size:12px'>A pull ends when the group goes more than %s without dealing or taking damage. A group that chains packs without a pause will therefore see them grouped%.0s: <code>--pull-gap</code> changes that threshold, except inside a boss encounter, which always stays one pull.%s%s</p></div>",
    " %s écarté%s, trop petit%s pour compter (moins d'un millième des dégâts de la course).":
        " %s dropped%.0s, too small%.0s to count (less than a thousandth of the run's damage).",
    " Sous chaque pull, le premier acte qui lie le groupe à un ennemi depuis la fin du pull précédent%s: le journal n'a aucune ligne de menace, donc un ennemi pris par proximité ne s'y voit qu'à ce qu'il fait ensuite. Quand c'est l'ennemi qui agit en premier, sa première cible est un fort indice de qui l'a attiré, pas une preuve (une zone au sol laissée par le pack précédent, par exemple)%s; et un soin, un renfort ou une dissipation donné en combat attire l'ennemi vers celui qui l'a donné, si bien que la ligne dit aussi quand cette cible venait d'en donner un. Cette lecture est en bêta. Le premier coup reçu par chaque ennemi, lui, est écrit tel quel dans le journal.":
        ' Under each pull, the first act linking the group and an enemy since the previous pull ended%.0s: the log has no threat line, so an enemy drawn by proximity only shows in what it does next. When the enemy acts first, its first target is a strong hint of who drew it, not a proof (a ground effect left by the previous pack, for instance)%.0s; and a heal, a buff or a dispel given in combat draws the enemy towards whoever gave it, so the line also says when that target had just given one. This reading is in beta. The first hit each enemy took, on the other hand, is written as such in the log.',
    ' <span class=dim>(%s de surguérison)</span>':
        ' <span class=dim>(%s overhealing)</span>',
    '<th>Joueur</th><th class=n>Total</th>':
        '<th>Player</th><th class=n>Total</th>',
    '<th class=n>Absorbé</th><th class=n>Somme</th>':
        '<th class=n>Absorbed</th><th class=n>Sum</th>',
    '<th class=n>Réattribué</th>':
        '<th class=n>Reattributed</th>',
    "<p class=dim style='margin:10px 0 0;font-size:12px'><b>Réattribué</b>%s: les dégâts de chacun, moins la part que le jeu crédite aux renforts d'un évocateur (Puissance d'ébène, Prescience, Bombardements...), plus ce qu'il crédite au joueur lui-même. C'est la réattribution de Warcraft Logs, et la seule que le journal permet%s: aucune ligne ne dit ce qu'une Furie sanguinaire, une Infusion de puissance ou un buff de raid a ajouté aux coups des autres. Le total du groupe ne change pas.</p>":
        "<p class=dim style='margin:10px 0 0;font-size:12px'><b>Reattributed</b>%.0s: each player's damage, minus the part the game credits to an Evoker's buffs (Ebon Might, Prescience, Bombardments...), plus what it credits to the player themselves. This is Warcraft Logs' reattribution, and the only one the log allows%.0s: no line says what a Bloodlust, a Power Infusion or a raid buff added to other players' hits. The group's total does not change.</p>",
    "<p class=dim style='margin:10px 0 0;font-size:12px'>Un bouclier n'est pas un soin dans le journal%s: il empêche des dégâts au lieu d'en rendre. Les deux sont donc comptés à part, et additionnés dans la colonne <b>Somme</b> — c'est ce total-là que les sites en ligne appellent « soins ».</p>":
        "<p class=dim style='margin:10px 0 0;font-size:12px'>A shield is not a heal in the log%.0s: it prevents damage instead of restoring health. The two are therefore counted apart, and added up in the <b>Sum</b> column — that total is what the online sites call “healing”.</p>",
    "<p class=dim style='margin:6px 0 0;font-size:12px'>Le Lien d'esprit ne soigne pas%s: il prend de la santé aux joueurs les plus hauts pour la donner aux plus bas. Les %s qu'il a pris sont déduits des soins de son poseur, comme sur Warcraft Logs, et ne comptent dans les dégâts subis de personne.</p>":
        "<p class=dim style='margin:6px 0 0;font-size:12px'>Spirit Link does not heal%.0s: it takes health from the highest players to give it to the lowest. The %s it took are taken off its caster's healing, as on Warcraft Logs, and count in nobody's damage taken.</p>",
    "<h3>Ce qui a fait mal au groupe</h3><div class=card><table><tr><th>Capacité</th><th class=n>Dégâts</th><th class=n>Coups</th><th class=n>Joueurs touchés</th></tr>%s</table>%s<p class=dim style='margin:10px 0 0;font-size:12px'>Le fichier dit qui a été touché et combien. Il ne dit pas si le coup était évitable&nbsp;: cela demande de connaître le boss, ce que cet outil ne prétend pas savoir.</p></div>":
        "<h3>What hurt the group</h3><div class=card><table><tr><th>Ability</th><th class=n>Damage</th><th class=n>Hits</th><th class=n>Players hit</th></tr>%s</table>%s<p class=dim style='margin:10px 0 0;font-size:12px'>The file says who was hit and how hard. It does not say whether the hit was avoidable: that takes knowing the boss, which this tool does not claim to.</p></div>",
    "<p class=dim style='margin:8px 0 0;font-size:12.5px'>Et %s de plus, %s de dégâts en tout.</p>":
        "<p class=dim style='margin:8px 0 0;font-size:12.5px'>And %s more, %s of damage in all.</p>",
    ' <b>coup fatal</b>':
        ' <b>killing blow</b>',
    'mort instantanée':
        'instant death',
    'cause non écrite dans le journal':
        'cause not written in the log',
    '<li class=dim>Rien avant la mort dans le journal.</li>':
        '<li class=dim>Nothing before the death in the log.</li>',
    "<h3>Composition du groupe</h3><div class=card><table>%s</table>%s<p class=dim style='margin:10px 0 0;font-size:12px'>Le rôle vient de la spécialisation que le client écrit au début du combat. Une spécialisation que cet outil ne connaît pas est affichée par son numéro.</p></div>":
        "<h3>Group composition</h3><div class=card><table>%s</table>%s<p class=dim style='margin:10px 0 0;font-size:12px'>The role comes from the specialization the client writes at the start of the fight. A specialization this tool does not know is shown by its number.</p></div>",
    "<p style='margin:10px 0 0;font-size:12.5px'>Aussi présents dans le journal, sans prendre part au combat (ni dégâts, ni soins, ni coups reçus)%s: %s.</p>":
        "<p style='margin:10px 0 0;font-size:12.5px'>Also present in the log, without taking part in the fight (no damage, no healing, no hits taken)%.0s: %s.</p>",
    '<footer>LogsWoW %s &middot; lecture locale de <code>%s</code><br>Disposition détectée dans ce fichier&nbsp;: bloc avancé de %d champs, champ de dégâts bruts %s, champ hideCaster %s. Lignes non comprises&nbsp;: %s. Événements inconnus&nbsp;: %s.<br>Licence AGPL-3.0 ou ultérieure&nbsp;; code source&nbsp;: github.com/prenom6548/LogsWoW. Aucune donnée ne quitte cette machine.</footer></div></body></html>':
        '<footer>LogsWoW %s &middot; local reading of <code>%s</code><br>Layout detected in this file: advanced block of %d fields, raw damage field %s, hideCaster field %s. Lines not understood: %s. Unknown events: %s.<br>Licence AGPL-3.0 or later; source code: github.com/prenom6548/LogsWoW. No data leaves this machine.</footer></div></body></html>',
    # report_casts
    "<p class=dim style='font-size:12px'>Séquence coupée après %s sorts.</p>":
        "<p class=dim style='font-size:12px'>Sequence cut after %s casts.</p>",
    '<details class=co><summary>Ordre des sorts, pull par pull <span class=dim>&middot; %s</span></summary><div class=cobody>%s%s<div class=pulls>%s%s</div></div></details>':
        '<details class=co><summary>Cast order, pull by pull <span class=dim>&middot; %s</span></summary><div class=cobody>%s%s<div class=pulls>%s%s</div></div></details>',
    'Lancés':
        'Cast',
    'Probablement déclenchés automatiquement (masqués)':
        'Probably triggered by the game (hidden)',
    'Lancés par ses invocations':
        'Cast by their summons',
    "<p class=dim style='font-size:12px;margin:4px 0 0'>Le journal écrit de la même façon un sort appuyé et un sort que le jeu déclenche seul. Sont lus comme déclenchés, parmi les sorts lancés au moins %d fois dans ce combat sans jamais coûter de ressource%s: ceux qui, à %d%s%% au moins, partent en même temps qu'un sort payé, avec un écart médian de %d secondes au plus entre deux lancers%s; ceux dont l'écart médian est sous %s%ss, plus vite qu'aucun bouton%s; et la seconde copie d'un sort que le journal écrit deux fois, sous le même nom, au même instant. C'est une lecture du fichier%s: cliquez pour les afficher.</p>":
        "<p class=dim style='font-size:12px;margin:4px 0 0'>The log writes a spell pressed and a spell the game fires on its own the same way. Read as triggered, among the spells cast at least %d times in this fight without ever costing a resource%.0s: those that, %d%.0s%% of the time or more, go off together with a paid spell, with a median gap of %d seconds at most between two casts%.0s; those whose median gap is under %s%.0ss, faster than any button%.0s; and the second copy of a spell the log writes twice, under the same name, at the same instant. This is a reading of the file%.0s: click to show them.</p>",
    "<div class=legend><p class=dim style='font-size:12px;margin:0'>Cliquez sur un sort pour le masquer ou l'afficher.</p>%s%s</div>":
        "<div class=legend><p class=dim style='font-size:12px;margin:0'>Click a spell to hide or show it.</p>%s%s</div>",
    'Entre les pulls':
        'Between pulls',
    'Pull %02d &mdash; %s':
        'Pull %02d &mdash; %s',
    "<p class=dim style='line-height:1.5;margin:0'>Aucun sort pendant ce pull.</p>":
        "<p class=dim style='line-height:1.5;margin:0'>No cast during this pull.</p>",
    ', réussite':
        ', kill',
    ', échec':
        ', wipe',
    'trash (%s)':
        'trash (%s)',
    # report_layouts
    'Résumé':
        'Summary',
    'Dégâts et soins':
        'Damage and healing',
    'Physique ou magique':
        'Physical or magic',
    'Joueurs':
        'Players',
    'Ennemis':
        'Enemies',
    "<input type=radio name=f id=f0 class=fsel checked aria-label='Vue d&#39;ensemble'>":
        "<input type=radio name=f id=f0 class=fsel checked aria-label='Overview'>",
    "<label for=f0 class='nv n0'>Vue d'ensemble</label>":
        "<label for=f0 class='nv n0'>Overview</label>",
    "%s<div class=layout><nav class=side aria-label='Combats'>%s</nav><main>%s</main></div>%s":
        "%s<div class=layout><nav class=side aria-label='Fights'>%s</nav><main>%s</main></div>%s",
    "<a href='index.html'>&larr; Tous les combats</a>":
        "<a href='index.html'>&larr; All fights</a>",
    # report_panels
    ' et %s':
        ' and %s',
    '<p class=dim>Rien.</p>':
        '<p class=dim>Nothing.</p>',
    '<details class=more><summary>%s de plus &middot; %s (%s)</summary>%s</details>':
        '<details class=more><summary>%s more &middot; %s (%s)</summary>%s</details>',
    'Sort':
        'Spell',
    'Total':
        'Total',
    'Part':
        'Share',
    'Surguérison':
        'Overhealing',
    'Casts':
        'Casts',
    'Coups':
        'Hits',
    'Moyenne':
        'Average',
    'Crit':
        'Crit',
    'Par sec.':
        'Per sec.',
    'Principale cible':
        'Main target',
    'Principale source':
        'Main source',
    '<table><tr><th>Effet</th><th>%s</th><th class=n>Durée</th></tr>%s</table>':
        '<table><tr><th>Effect</th><th>%s</th><th class=n>Uptime</th></tr>%s</table>',
    '<h3>Détail par joueur</h3>%s':
        '<h3>Player details</h3>%s',
    ' (dont %d de ses invocations)':
        ' (%d of them by their summons)',
    "<details><summary>%s <span class=dim>&middot; %s &middot; %s dégâts &middot; %s soins &middot; %s</span></summary><div class=body><div class='grid tiles'>%s</div>%s%s</div></details>":
        "<details><summary>%s <span class=dim>&middot; %s &middot; %s damage &middot; %s healing &middot; %s</span></summary><div class=body><div class='grid tiles'>%s</div>%s%s</div></details>",
    'rôle inconnu':
        'unknown role',
    'Part sur les boss':
        'Share on bosses',
    'Subis par ses invocations':
        'Taken by their summons',
    'Dégâts subis':
        'Damage taken',
    'Absorbé sur lui':
        'Absorbed on them',
    'Absorbé par ses boucliers':
        'Absorbed by their shields',
    'Soutien crédité par le jeu':
        'Support credited by the game',
    'Sorts par minute':
        'Casts per minute',
    'Temps sans action':
        'Time idle',
    'Interruptions':
        'Interrupts',
    'Dissipations':
        'Dispels',
    'Vie la plus basse':
        'Lowest health',
    'Ce que ses boucliers ont absorbé':
        'What their shields absorbed',
    'Ses dégâts':
        'Their damage',
    'Ses soins':
        'Their healing',
    'Qui il a soigné':
        'Whom they healed',
    "Ce qu'il a pris":
        'What they took',
    'Soutien que le jeu lui crédite':
        'Support the game credits them with',
    'Plus longues pauses':
        'Longest pauses',
    'Gains reçus':
        'Buffs received',
    'De qui':
        'From whom',
    'Affaiblissements subis':
        'Debuffs suffered',
    "Ce qu'il a appliqué":
        'What they applied',
    'Sur qui':
        'On whom',
    "<p class=dim style='font-size:12px;margin:0'>Un effet déjà actif quand le combat commence n'a pas de ligne d'application dans le journal%s: sa durée est comptée depuis le premier événement du combat, ce qui est la seule borne que le fichier donne.</p>":
        "<p class=dim style='font-size:12px;margin:0'>An effect already up when the fight starts has no application line in the log%.0s: its uptime is counted from the fight's first event, the only bound the file gives.</p>",
    '<li><span class=dim>%s</span> sans lancer de sort, à %s</li>':
        '<li><span class=dim>%s</span> without casting, at %s</li>',
    '<li class=dim>Aucune pause notable.</li>':
        '<li class=dim>No notable pause.</li>',
    "<p class=dim style='font-size:12.5px;margin:8px 0 0'><b>Sorts ennemis coupés</b>%s %s</p>":
        "<p class=dim style='font-size:12.5px;margin:8px 0 0'><b>Enemy spells interrupted</b>%.0s: %s</p>",
    "<p class=dim style='font-size:12.5px;margin:4px 0 0'><b>Effets dissipés</b>%s %s</p>":
        "<p class=dim style='font-size:12.5px;margin:4px 0 0'><b>Effects dispelled</b>%.0s: %s</p>",
    "%s<p class=dim style='font-size:12px;margin:4px 0 0'>Le journal crédite cet évocateur de %s de dégâts et %s de soins portés par d'autres joueurs%s: la part que ses renforts (Puissance d'ébène, Prescience...) ont ajoutée à leurs coups, et ses Bombardements, que le journal écrit au nom de l'allié qui les a déclenchés. Ces montants sont <b>déjà comptés</b> chez ceux qui ont porté les coups et ne sont pas ajoutés aux siens%s; Warcraft Logs, lui, les retire aux autres pour les lui donner, d'où l'écart entre les deux.</p>":
        "%s<p class=dim style='font-size:12px;margin:4px 0 0'>The log credits this Evoker with %s of damage and %s of healing dealt by other players%.0s: the part their buffs (Ebon Might, Prescience...) added to those hits, and their Bombardments, which the log writes under the name of the ally who set them off. These amounts are <b>already counted</b> for the players who dealt the hits and are not added to the Evoker's own%.0s; Warcraft Logs moves them from the others to the Evoker instead, hence the gap between the two.</p>",
    '<table><tr><th>Cible</th><th class=n>Total</th><th class=n>Part</th></tr>%s</table>':
        '<table><tr><th>Target</th><th class=n>Total</th><th class=n>Share</th></tr>%s</table>',
    "Ce qu'il inflige":
        'What it deals',
    "Ce qu'il a subi":
        'What it took',
    'Ses sorts':
        'Its spells',
    '<table><tr><th>Sort</th><th class=n>Lancés</th></tr>%s</table>':
        '<table><tr><th>Spell</th><th class=n>Cast</th></tr>%s</table>',
    'Unités':
        'Units',
    'Sorts lancés':
        'Spells cast',
    'Tués':
        'Killed',
    "<details><summary>%s <span class=dim>&middot; %s &middot; %s infligé &middot; %s subi</span></summary><div class=body><div class='grid tiles'>%s</div>%s</div></details>":
        "<details><summary>%s <span class=dim>&middot; %s &middot; %s dealt &middot; %s taken</span></summary><div class=body><div class='grid tiles'>%s</div>%s</div></details>",
    '<h3>Détail par ennemi</h3>%s':
        '<h3>Enemy details</h3>%s',
    'Aboutis':
        'Completed',
    'Coupés par une interruption':
        'Cut by an interrupt',
    "Lanceur tué pendant l'incantation":
        'Caster killed mid-cast',
    'Non aboutis, cause non dite par le journal':
        'Not completed, cause not given by the log',
    "<p class=dim style='margin:10px 0 0;font-size:12px'>Les plus coupés%s: %s.</p>":
        "<p class=dim style='margin:10px 0 0;font-size:12px'>Most interrupted%.0s: %s.</p>",
    "<h3>Ce que le groupe a empêché</h3><div class=card><p class=dim style='margin:0 0 10px;font-size:12.5px'>%s sorts commencés par l'ennemi%s:</p><table><tr><th>Issue</th><th class=n>Nombre</th><th class=n>Part</th></tr>%s</table>%s<p class=dim style='margin:10px 0 0;font-size:12px'>Un sort instantané n'apparaît pas ici%s: seuls ceux qui ont un temps d'incantation laissent une trace. La dernière ligne regroupe tout le reste, contrôle compris%s: le journal ne dit nulle part qu'un sort est un étourdissement, donc rien ici ne prétend le savoir.</p></div>":
        "<h3>What the group prevented</h3><div class=card><p class=dim style='margin:0 0 10px;font-size:12.5px'>%s spells begun by the enemy%.0s:</p><table><tr><th>Outcome</th><th class=n>Count</th><th class=n>Share</th></tr>%s</table>%s<p class=dim style='margin:10px 0 0;font-size:12px'>An instant spell does not appear here%.0s: only those with a cast time leave a trace. The last row gathers all the rest, crowd control included%.0s: the log never says a spell is a stun, so nothing here claims to know.</p></div>",
    # report_schools
    'autres %s':
        'other %s',
    'Physique':
        'Physical',
    'Magique':
        'Magic',
    'Mixte':
        'Mixed',
    'Phys.':
        'Phys.',
    'Mag.':
        'Mag.',
    'Subis':
        'Taken',
    'Infligés':
        'Dealt',
    "<p class=dim style='font-size:12.5px;margin:6px 0 0'><b>%s par école</b>%s: %s</p>":
        "<p class=dim style='font-size:12.5px;margin:6px 0 0'><b>%s by school</b>%.0s: %s</p>",
    "<h3>Physique ou magique</h3><div class='card schools'><p style='margin:0 0 8px;font-size:12.5px'>%s</p><table><tr><th></th><th>Répartition</th>%s</tr>%s</table>%s%s<p class=dim style='margin:10px 0 0;font-size:12px'>L'école de chaque coup est celle que le journal écrit sur la ligne. « Mixte »%s: physique et magique à la fois (Ombre-frappe, Chaos...). Comme dans le reste du rapport, un coup qu'un bouclier ennemi a mangé compte dans les dégâts infligés, et la part qu'un bouclier du groupe a mangée ne compte pas dans les dégâts subis.</p></div>":
        "<h3>Physical or magic</h3><div class='card schools'><p style='margin:0 0 8px;font-size:12.5px'>%s</p><table><tr><th></th><th>Split</th>%s</tr>%s</table>%s%s<p class=dim style='margin:10px 0 0;font-size:12px'>Each hit's school is the one the log writes on its line. “Mixed”%.0s: physical and magic at once (Shadowstrike, Chaos...). As in the rest of the report, a hit an enemy shield ate counts in damage dealt, and the part a group shield ate does not count in damage taken.</p></div>",
    "<h3 style='margin-top:18px'>Pull par pull</h3><table><tr><th class=n>#</th><th>Ce qui a été engagé</th><th>Subis</th>%s<th>Infligés</th>%s</tr>%s</table>":
        "<h3 style='margin-top:18px'>Pull by pull</h3><table><tr><th class=n>#</th><th>What was engaged</th><th>Taken</th>%s<th>Dealt</th>%s</tr>%s</table>",
    # report_timeline
    "<h3>Dégâts subis par le groupe, seconde par seconde</h3><div class=card><svg viewBox='0 0 %d %d' role=img aria-label='Dégâts subis au fil du combat'>%s</svg><p class=dim style='margin:6px 0 0;font-size:12px'>Barres et échelle de gauche%s: dégâts subis par intervalle de %s. Traits rouges%s: morts.%s</p></div>":
        "<h3>Damage taken by the group, second by second</h3><div class=card><svg viewBox='0 0 %d %d' role=img aria-label='Damage taken over the fight'>%s</svg><p class=dim style='margin:6px 0 0;font-size:12px'>Bars and left-hand scale%.0s: damage taken per interval of %s. Red lines%.0s: deaths.%s</p></div>",
    " Courbe et échelle de droite%s: <b>vie cumulée des ennemis engagés</b>, somme de leurs points de vie courants sur la somme de leurs maximums. Elle remonte à chaque nouveau pack et retombe quand il meurt%s; un ennemi que le groupe n'a plus touché depuis %d%ss en sort.":
        ' Curve and right-hand scale%.0s: <b>pooled health of the engaged enemies</b>, the sum of their current health over the sum of their maximums. It rises with each new pack and falls as it dies%.0s; an enemy the group has not hit for %d%ss drops out of it.',
    ' Courbe et échelle de droite%s: vie de <b>%s</b>, la cible la plus frappée parmi celles dont le journal donne les points de vie.':
        ' Curve and right-hand scale%.0s: health of <b>%s</b>, the most-hit target among those whose health the log gives.',
    # schools
    'Sacré':
        'Holy',
    'Feu':
        'Fire',
    'Nature':
        'Nature',
    'Givre':
        'Frost',
    'Ombre':
        'Shadow',
    'Arcane':
        'Arcane',
    'école inconnue':
        'unknown school',
    # models
    'et %d autre(s)':
        'and %d more',
    'autres':
        'others',
    # segment
    'Normal':
        'Normal',
    'Héroïque':
        'Heroic',
    '10 joueurs':
        '10 Player',
    '25 joueurs':
        '25 Player',
    '10 héroïque':
        '10 Player Heroic',
    '25 héroïque':
        '25 Player Heroic',
    'Raid Recherche':
        'Raid Finder',
    'Mythique+':
        'Mythic+',
    '40 joueurs':
        '40 Player',
    'Héroïque scénario':
        'Heroic Scenario',
    'Normal scénario':
        'Normal Scenario',
    'Mythique':
        'Mythic',
    'Marche du temps':
        'Timewalking',
    'Torghast':
        'Torghast',
    'difficulté %d':
        'difficulty %d',
    'sans combat':
        'no fight',
    'abandonnée':
        'abandoned',
    'terminée':
        'completed',
    'interrompu':
        'cut short',
    'dans les temps':
        'in time',
    'hors des temps':
        'over time',
    'réussite':
        'kill',
    'échec':
        'wipe',
    'Pull %d':
        'Pull %d',
    'Donjon':
        'Dungeon',
    'Session complète':
        'Whole session',
    # specs
    'spe %d':
        'spec %d',
    'Touché':
        'Hit',
    'Absorbé entièrement':
        'Fully absorbed',
    'Paré':
        'Parried',
    'Esquivé':
        'Dodged',
    'Raté':
        'Missed',
    'Bloqué entièrement':
        'Fully blocked',
    'Dévié':
        'Deflected',
    'Insensible':
        'Immune',
    'Résisté':
        'Resisted',
    'Renvoyé':
        'Reflected',
    "Hors d'atteinte":
        'Evaded',
    'Les coups de mêlée reçus':
        'Melee swings taken',
    'dont critiques':
        'of which critical',
    'dont bloqués en partie':
        'of which partly blocked',
    '<table><tr><th>Issue</th><th class=n>Coups</th><th class=n>Part</th></tr>%s</table>':
        '<table><tr><th>Outcome</th><th class=n>Swings</th><th class=n>Share</th></tr>%s</table>',
    '<p><b>%s</b> des coups évités (parés, esquivés ou ratés).</p>':
        '<p><b>%s</b> of the swings avoided (parried, dodged or missed).</p>',
    '<p><b>%s</b> des coups qui ont touché venaient de derrière (%s sur %s dont la position est connue).</p>':
        '<p><b>%s</b> of the swings that landed came from behind (%s of %s whose position is known).</p>',
    ' Contrôle sur ce combat%s: le jeu ne laisse ni parer ni esquiver un coup venu de derrière, et %s des %s parades et esquives placées tombent bien devant.':
        ' Check on this fight%.0s: the game allows no parry or dodge of a swing from behind, and %s of the %s placed parries and dodges do fall in front.',
    "<p class=dim style='font-size:12px;margin:0'>Estimation fiable, mais pas une donnée écrite, et limitée à la mêlée%s: le journal ne dit pas d'où vient un coup. LogsWoW le déduit de la position de l'attaquant et de l'orientation du joueur, que le journal donne ligne par ligne.%s</p>":
        "<p class=dim style='font-size:12px;margin:0'>A reliable estimate, but not something the log writes, and limited to melee%.0s: the log does not say where a swing came from. LogsWoW infers it from the attacker's position and the player's facing, which the log gives line by line.%s</p>",
    # equipment, comparison of keys, preview (0.15.0)
    'Tête':
        'Head',
    'Cou':
        'Neck',
    'Épaules':
        'Shoulders',
    'Chemise':
        'Shirt',
    'Torse':
        'Chest',
    'Jambes':
        'Legs',
    'Pieds':
        'Feet',
    'Poignets':
        'Wrists',
    'Mains':
        'Hands',
    'Anneau 1':
        'Ring 1',
    'Anneau 2':
        'Ring 2',
    'Bijou 1':
        'Trinket 1',
    'Bijou 2':
        'Trinket 2',
    'Dos':
        'Back',
    'Main droite':
        'Main hand',
    'Main gauche':
        'Off hand',
    'Tabard':
        'Tabard',
    'Aperçu':
        'Overview',
    'Clés':
        'Keys',
    'Équipement':
        'Gear',
    'Cochez un ou plusieurs combats pour voir ce que le rapport en dirait.':
        'Tick one or more fights to see what the report would say about them.',
    "Équipement tel qu'il était à « %s »%s.\n\n":
        'Gear as it was at "%s"%s.\n\n',
    ' (le dernier combat choisi)':
        ' (the last fight chosen)',
    ' Aperçu des combats choisis ':
        ' Preview of the fights chosen ',
    'Aucune clé terminée à comparer : il faut au moins une clé, et deux du même niveau pour les mettre côte à côte.':
        'No finished key to compare: it takes at least one key, and two of the same level to set them side by side.',
    "Écart : la dernière clé par rapport à la première. Soins/s compte les boucliers ; Subis/s compte ce que les boucliers ont absorbé, et n'est donné qu'aux tanks.":
        'Change: the last key against the first. Healing/s counts shields; Taken/s counts what shields absorbed, and is given to tanks only.',
    'Aucun joueur dans ce combat.':
        'No player in this fight.',
    "Le journal donne le numéro et le niveau de chaque objet, jamais son nom ni son icône : ils viennent de la base d'objets du jeu. Le rapport les relie à Wowhead.":
        "The log gives each item's number and level, never its name or icon: those come from the game's item database. The report links them to Wowhead.",
    '%s — %s (%s)':
        '%s — %s (%s)',
    'Dégâts %s (%s/s) · Soins %s (%s/s, boucliers compris) · Subis %s · %s':
        'Damage %s (%s/s) · Healing %s (%s/s, shields included) · Taken %s · %s',
    'Morts :':
        'Deaths:',
    '%s dégâts/s':
        '%s damage/s',
    '%s soins/s':
        '%s healing/s',
    'Dégâts/s':
        'Damage/s',
    'Soins/s':
        'Healing/s',
    'Subis/s':
        'Taken/s',
    "Niveau d'objet moyen du groupe : %s":
        'Average item level of the group: %s',
    'Boss : %s':
        'Boss: %s',
    '%s subis/s':
        '%s taken/s',
    'ilvl %s':
        'ilvl %s',
    '%s : %s':
        '%s: %s',
    '  %s à %s : %s':
        '  %s at %s: %s',
    'Écart':
        'Change',
    '%s : ilvl %s (de %d à %d)':
        '%s: ilvl %s (from %d to %d)',
    'Clé %d':
        'Key %d',
    'Groupe : ':
        'Group: ',
    '%s : équipement non écrit dans le journal':
        '%s: gear not written in the log',
    '  %-12s ilvl %d  objet %d%s%s':
        '  %-12s ilvl %d  item %d%s%s',
    '  Emplacement vide : %s.':
        '  Empty slot: %s.',
    '  enchantement %s':
        '  enchant %s',
    '  gemmes %d':
        '  gems %d',
    'sans résultat':
        'no result',
    "<p style='margin:10px 0 0;font-size:12.5px'>Niveau d'objet moyen du groupe%s: <b>%s</b> (de %s à %s).</p>":
        "<p style='margin:10px 0 0;font-size:12.5px'>Average item level of the group%s: <b>%s</b> (from %s to %s).</p>",
    '<h2>Comparaison des clés</h2>':
        '<h2>Comparison of keys</h2>',
    "<p class=dim style='font-size:12.5px'>Écart%s: la dernière clé par rapport à la première. <b>Soins/s</b> compte les boucliers (le journal ne les range pas parmi les soins, les sites en ligne si). <b>Subis/s</b> compte ce que les boucliers ont absorbé : c'est ce qui arrive au tank avant ses protections, et il n'est donné qu'aux tanks. Seules des clés terminées du même niveau sont comparées.</p>":
        "<p class=dim style='font-size:12.5px'>Change%s: the last key against the first. <b>Healing/s</b> counts shields (the log does not file them under healing, the online sites do). <b>Taken/s</b> counts what shields absorbed: it is what reaches the tank before their protections, and it is given to tanks only. Only finished keys of the same level are compared.</p>",
    "Le journal donne le numéro et le niveau de chaque objet, jamais son nom ni son icône : ils viennent de la base d'objets du jeu, que ce rapport n'a pas (il ne se connecte à rien). Le lien ouvre Wowhead si vous cliquez dessus. Le niveau moyen suit la formule du jeu : seize emplacements, chemise et tabard exclus, une arme à deux mains comptée deux fois, un emplacement vide pour zéro.":
        "The log gives each item's number and level, never its name or icon: those come from the game's item database, which this report does not have (it connects to nothing). The link opens Wowhead if you click it. The average level follows the game's formula: sixteen slots, shirt and tabard excluded, a two-handed weapon counted twice, an empty slot counted as zero.",
    'Joueur':
        'Player',
    'objet %d':
        'item %d',
    'Emplacement':
        'Slot',
    'Objet':
        'Item',
    'Niveau':
        'Level',
    'Enchantements':
        'Enchantments',
    'Gemmes':
        'Gems',
    "<p class=dim style='margin:6px 0 0'>Emplacement vide%s: %s.</p>":
        "<p class=dim style='margin:6px 0 0'>Empty slot%s: %s.</p>",
    ' (non compté)':
        ' (not counted)',
}

# The French nouns `fmt.plural` agrees, and their English forms.
PLURALS = {
    'autre': ('other', 'others'),
    'capacité': ('ability', 'abilities'),
    'cible': ('target', 'targets'),
    'clé': ('key', 'keys'),
    'combat': ('fight', 'fights'),
    'ennemi': ('enemy', 'enemies'),
    'joueur': ('player', 'players'),
    'mort': ('death', 'deaths'),
    'pull': ('pull', 'pulls'),
    'sort': ('spell', 'spells'),
    'unité': ('unit', 'units'),
}

# Class and specialization by id: French names two different ones
# "Dévastation" (Demon Hunter Havoc, Evoker Devastation).
SPECS = {
    250: ('Death Knight', 'Blood'),
    251: ('Death Knight', 'Frost'),
    252: ('Death Knight', 'Unholy'),
    577: ('Demon Hunter', 'Havoc'),
    581: ('Demon Hunter', 'Vengeance'),
    1480: ('Demon Hunter', 'Devourer'),
    102: ('Druid', 'Balance'),
    103: ('Druid', 'Feral'),
    104: ('Druid', 'Guardian'),
    105: ('Druid', 'Restoration'),
    1467: ('Evoker', 'Devastation'),
    1468: ('Evoker', 'Preservation'),
    1473: ('Evoker', 'Augmentation'),
    253: ('Hunter', 'Beast Mastery'),
    254: ('Hunter', 'Marksmanship'),
    255: ('Hunter', 'Survival'),
    62: ('Mage', 'Arcane'),
    63: ('Mage', 'Fire'),
    64: ('Mage', 'Frost'),
    268: ('Monk', 'Brewmaster'),
    269: ('Monk', 'Windwalker'),
    270: ('Monk', 'Mistweaver'),
    65: ('Paladin', 'Holy'),
    66: ('Paladin', 'Protection'),
    70: ('Paladin', 'Retribution'),
    256: ('Priest', 'Discipline'),
    257: ('Priest', 'Holy'),
    258: ('Priest', 'Shadow'),
    259: ('Rogue', 'Assassination'),
    260: ('Rogue', 'Outlaw'),
    261: ('Rogue', 'Subtlety'),
    262: ('Shaman', 'Elemental'),
    263: ('Shaman', 'Enhancement'),
    264: ('Shaman', 'Restoration'),
    265: ('Warlock', 'Affliction'),
    266: ('Warlock', 'Demonology'),
    267: ('Warlock', 'Destruction'),
    71: ('Warrior', 'Arms'),
    72: ('Warrior', 'Fury'),
    73: ('Warrior', 'Protection'),
}
