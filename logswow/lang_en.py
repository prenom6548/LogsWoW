# SPDX-License-Identifier: AGPL-3.0-or-later
"""English: every French text of the interface, and its translation.

The keys are the French texts exactly as the code writes them; a test
fails when one is missing here, or when a translation does not keep
the original's %-placeholders and HTML tags in the same order.
`%.0s` swallows an argument: French passes a narrow no-break space
before a colon, which English does not want.
"""

TEXTS = {
    # analysis.py
    'source non nommée par le journal':
        'source the log does not name',
    # analysis.py
    'Tanks':
        'Tanks',
    # analysis.py
    'Soigneurs':
        'Healers',
    # analysis.py
    'Rôle non indiqué':
        'Role not given',
    # cli.py
    '\r  %s lignes lues...':
        '\r  %s lines read...',
    # cli.py
    'Fichier introuvable : %s\n':
        'File not found: %s\n',
    # cli.py
    '%s est un dossier, pas un fichier de journal. Cherchez-y WoWCombatLog.txt.\n':
        '%s is a folder, not a log file. Look for WoWCombatLog.txt inside it.\n',
    # cli.py
    'Impossible de lire %s : %s\n':
        'Cannot read %s: %s\n',
    # cli.py
    "Aucun combat n'a été trouvé dans %s. Le fichier est peut-être vide, ou écrit par une version du client que ce lecteur ne comprend pas : `diagnose` dit ce qui a été lu.\n":
        'No fight was found in %s. The file may be empty, or written by a client version this reader does not understand: `diagnose` says what was read.\n',
    # cli.py
    "Refus d'écrire le rapport par-dessus le journal lui-même (%s). Choisissez un autre nom avec -o.\n":
        'Refusing to write the report over the log itself (%s). Choose another name with -o.\n',
    # cli.py
    '%s est un dossier : donnez un nom de fichier avec -o.\n':
        '%s is a folder: give a file name with -o.\n',
    # cli.py
    "%s existe et n'est pas un rapport LogsWoW : refus de l'écraser. Choisissez un autre nom, ou ajoutez --force si c'est voulu.\n":
        '%s exists and is not a LogsWoW report: refusing to overwrite it. Choose another name, or add --force if that is intended.\n',
    # cli.py
    "%s existe et n'est pas un dossier : donnez un autre nom avec -o.\n":
        '%s exists and is not a folder: give another name with -o.\n',
    # cli.py
    "Refus d'écrire les pages dans le dossier du journal lui-même (%s). Donnez un autre dossier avec -o.\n":
        "Refusing to write the pages into the log's own folder (%s). Give another folder with -o.\n",
    # cli.py
    "%s contient déjà autre chose qu'un rapport LogsWoW : refus d'y écrire. Choisissez un autre dossier, ou ajoutez --force si c'est voulu.\n":
        '%s already holds something other than a LogsWoW report: refusing to write there. Choose another folder, or add --force if that is intended.\n',
    # cli.py
    'Aucun combat ne correspond à --only %r. Utilisez `list` pour les voir.\n':
        'No fight matches --only %r. Use `list` to see them.\n',
    # cli.py
    "Impossible d'écrire %s : %s\n":
        'Cannot write %s: %s\n',
    # cli.py
    '%d combat(s) retenu(s) sur %d, %s lignes lues en %.1f s':
        '%d fight(s) kept of %d, %s lines read in %.1f s',
    # cli.py
    '%d lignes non comprises -- lancez `diagnose` pour voir lesquelles':
        '%d lines not understood -- run `diagnose` to see which',
    # cli.py
    'Rapport écrit : %s':
        'Report written: %s',
    # cli.py
    'Combat':
        'Fight',
    # cli.py
    'Durée':
        'Duration',
    # cli.py
    'Dégâts':
        'Damage',
    # cli.py
    'Morts':
        'Deaths',
    # cli.py
    'Aucun dossier Logs trouvé aux emplacements habituels.':
        'No Logs folder found in the usual places.',
    # cli.py
    'Cherchez WoWCombatLog.txt sous _retail_/Logs dans votre installation,':
        'Look for WoWCombatLog.txt under _retail_/Logs in your installation,',
    # cli.py
    "puis donnez son chemin complet, entre guillemets s'il contient des espaces :":
        'then give its full path, in quotes if it contains spaces:',
    # cli.py
    '  report "/chemin/vers/World of Warcraft/_retail_/Logs/WoWCombatLog-....txt"':
        '  report "/path/to/World of Warcraft/_retail_/Logs/WoWCombatLog-....txt"',
    # cli.py
    "Pas d'écran disponible pour ouvrir la fenêtre : utilisez les commandes (voir --help).\n":
        'No screen available to open the window: use the commands (see --help).\n',
    # cli.py
    "%r n'est pas un nombre de secondes":
        '%r is not a number of seconds',
    # cli.py
    '%r : il faut un nombre de secondes entre 0 et 86400':
        '%r: a number of seconds between 0 and 86400 is needed',
    # cli.py
    "%r n'est pas un nombre entier":
        '%r is not a whole number',
    # cli.py
    '%r : il faut un nombre supérieur à zéro':
        '%r: a number above zero is needed',
    # cli.py
    "langue de l'interface et du rapport : auto (celle du système, l'anglais pour une langue sans traduction), fr ou en":
        "language of the interface and the report: auto (the system's, English for a language with no translation), fr or en",
    # cli.py
    'Lit un journal de combat de World of Warcraft, en local, sans rien envoyer nulle part.':
        'Reads a World of Warcraft combat log, locally, without sending anything anywhere.',
    # cli.py
    'chemin du fichier WoWCombatLog.txt':
        'path to the WoWCombatLog.txt file',
    # cli.py
    "année, pour les journaux dont l'horodatage n'en porte pas":
        'year, for logs whose timestamps carry none',
    # cli.py
    'SECONDES':
        'SECONDS',
    # cli.py
    'silence nécessaire pour séparer deux pulls (défaut 6 s) ; baissez-le si vos packs sont regroupés, montez-le si un pull unique est coupé en deux':
        'silence needed to separate two pulls (default 6 s); lower it if your packs are grouped together, raise it if a single pull is cut in two',
    # cli.py
    'produit le rapport HTML':
        'writes the HTML report',
    # cli.py
    'fichier de sortie (.html)':
        'output file (.html)',
    # cli.py
    "ne pas mettre l'ordre des sorts de chaque joueur : la page est environ deux fois plus légère":
        "leave out each player's cast order: the page is about half the size",
    # cli.py
    'présentation du rapport : onglets (un fichier, un combat et une catégorie à la fois, par défaut), pages (un dossier, une page par combat) ou longue (tout sur une seule page)':
        'report layout: onglets (one file, one fight and one section at a time, the default), pages (a folder, one page per fight) or longue (everything on one page)',
    # cli.py
    "écraser le fichier de sortie même s'il n'est pas un rapport LogsWoW (jamais le journal lu)":
        'overwrite the output file even if it is not a LogsWoW report (never the log being read)',
    # cli.py
    'NUMÉRO|NOM':
        'NUMBER|NAME',
    # cli.py
    "n'inclure qu'un combat : son numéro dans `list`, ou un bout de son nom":
        'include only one fight: its number in `list`, or part of its name',
    # cli.py
    'LANGUE':
        'LANGUAGE',
    # cli.py
    'langue des liens Wowhead : auto (celle du système), fr, en, de, es, it, pt, ru, ko, zh, ou off pour ne mettre aucun lien':
        "language of the Wowhead links: auto (the system's), fr, en, de, es, it, pt, ru, ko, zh, or off for no links",
    # cli.py
    'liste les combats du fichier':
        'lists the fights in the file',
    # cli.py
    'montre ce que le lecteur a compris du fichier':
        'shows what the reader understood of the file',
    # cli.py
    "s'arrêter après N événements":
        'stop after N events',
    # cli.py
    'cherche le dossier Logs du jeu':
        "looks for the game's Logs folder",
    # cli.py
    "ouvre la fenêtre (c'est aussi ce que fait la commande sans rien)":
        'opens the window (which is also what the command does with nothing typed)',
    # cli.py
    '\nInterrompu.\n':
        '\nInterrupted.\n',
    # diagnose.py
    'Fichier    : %s':
        'File       : %s',
    # diagnose.py
    'Taille     : %.1f Mo, %d lignes, %d événements':
        'Size       : %.1f MB, %d lines, %d events',
    # diagnose.py
    'Durée      : %s':
        'Duration   : %s',
    # diagnose.py
    'DISPOSITION MESURÉE DANS CE FICHIER':
        'LAYOUT MEASURED IN THIS FILE',
    # diagnose.py
    '  bloc avancé         : %d champs  (votes: %s)':
        '  advanced block      : %d fields  (votes: %s)',
    # diagnose.py
    '    votes à égalité, départage par : %s':
        '    tied vote, settled by: %s',
    # diagnose.py
    '  champ baseAmount    : %s  (position du -1: %s)':
        '  baseAmount field    : %s  (position of the -1: %s)',
    # diagnose.py
    'présent':
        'present',
    # diagnose.py
    '  champ hideCaster    : %s  (%s)':
        '  hideCaster field    : %s  (%s)',
    # diagnose.py
    '  journalisation avancée : %s':
        '  advanced logging    : %s',
    # diagnose.py
    'oui':
        'yes',
    # diagnose.py
    'non -- positions et points de vie absents':
        'no -- positions and health missing',
    # diagnose.py
    '  événements avec bloc avancé : %d sur %d':
        '  events with an advanced block : %d of %d',
    # diagnose.py
    '  points de vie incohérents   : %d (courants > maximum ; ignorés pour les courbes de vie ennemies)':
        '  inconsistent health : %d (current > maximum; left out of the enemy health curves)',
    # diagnose.py
    'COMBATS DÉLIMITÉS : %d':
        'FIGHTS FOUND: %d',
    # diagnose.py
    'JOUEURS VUS : %d':
        'PLAYERS SEEN: %d',
    # diagnose.py
    'ÉVÉNEMENTS (%d types)':
        'EVENTS (%d types)',
    # diagnose.py
    '[SCHÉMA INCONNU] ':
        '[UNKNOWN SCHEME] ',
    # diagnose.py
    'LIGNES NON RÉSOLUES':
        'UNRESOLVED LINES',
    # diagnose.py
    'LIGNES NON RÉSOLUES : aucune':
        'UNRESOLVED LINES: none',
    # diagnose.py
    'PROBLÈMES DE LECTURE : %d':
        'READ PROBLEMS: %d',
    # diagnose.py
    '    ligne %s : %s | %s':
        '    line %s: %s | %s',
    # encounters.py
    'Rencontre':
        'Encounter',
    # events.py
    'événement inconnu':
        'unknown event',
    # events.py
    'champs de base manquants':
        'base fields missing',
    # events.py
    'ligne trop courte : %d champs pour un préfixe de %d':
        'line too short: %d fields for a prefix of %d',
    # events.py
    'nombre de champs inattendu : %d après le préfixe, attendu %s, ou cela +%d':
        'unexpected number of fields: %d after the prefix, expected %s, or that +%d',
    # gui.py
    "La fenêtre de LogsWoW a besoin de Tkinter, qui fait partie de Python mais\nque certaines distributions Linux livrent à part. Pour l'installer :\n  Linux Mint, Ubuntu, Debian : sudo apt install python3-tk\n  Fedora                     : sudo dnf install python3-tkinter\n  Arch, Manjaro              : sudo pacman -S tk\n  openSUSE                   : sudo zypper install python3-tk\n  macOS (Homebrew)           : brew install python-tk\nSous Windows, et sous macOS avec l'installateur de python.org, il est déjà là.\nLes commandes du terminal fonctionnent sans lui (voir ci-dessous).\n":
        'The LogsWoW window needs Tkinter, which is part of Python but\nwhich some Linux distributions ship separately. To install it:\n  Linux Mint, Ubuntu, Debian : sudo apt install python3-tk\n  Fedora                     : sudo dnf install python3-tkinter\n  Arch, Manjaro              : sudo pacman -S tk\n  openSUSE                   : sudo zypper install python3-tk\n  macOS (Homebrew)           : brew install python-tk\nOn Windows, and on macOS with the python.org installer, it is already there.\nThe terminal commands work without it (see below).\n',
    # gui.py
    'Onglets (un fichier)':
        'Tabs (one file)',
    # gui.py
    'Pages (un dossier)':
        'Pages (a folder)',
    # gui.py
    'Une seule longue page':
        'One long page',
    # gui.py
    "Impossible d'écrire %s : %s":
        'Cannot write %s: %s',
    # gui.py
    'Choisissez un journal, puis « Lire ce journal ».':
        'Choose a log, then “Read this log”.',
    # gui.py
    "Tout se passe sur cet ordinateur : aucune donnée n'est envoyée.":
        'Everything happens on this computer: no data is sent.',
    # gui.py
    ' 1. Le journal ':
        ' 1. The log ',
    # gui.py
    'Fichier':
        'File',
    # gui.py
    'Date':
        'Date',
    # gui.py
    'Taille':
        'Size',
    # gui.py
    'Dossier':
        'Folder',
    # gui.py
    'Choisir un autre fichier…':
        'Choose another file…',
    # gui.py
    'Actualiser la liste':
        'Refresh the list',
    # gui.py
    'Lire ce journal':
        'Read this log',
    # gui.py
    'Silence entre deux pulls : ':
        'Silence between two pulls: ',
    # gui.py
    'Annuler':
        'Cancel',
    # gui.py
    ' 2. Les combats ':
        ' 2. The fights ',
    # gui.py
    'Issue':
        'Outcome',
    # gui.py
    'Tout sélectionner':
        'Select all',
    # gui.py
    ' 3. Le rapport ':
        ' 3. The report ',
    # gui.py
    'Ordre des sorts de chaque joueur (la page est environ deux fois plus lourde)':
        "Each player's cast order (the page is about twice as large)",
    # gui.py
    'Présentation :':
        'Layout:',
    # gui.py
    "Créer le rapport et l'ouvrir":
        'Create the report and open it',
    # gui.py
    'Ouvrir le dossier du rapport':
        "Open the report's folder",
    # gui.py
    "Aucun journal trouvé aux emplacements habituels : « Choisir un autre fichier… » pour l'indiquer.":
        'No log found in the usual places: “Choose another file…” to point to one.',
    # gui.py
    'Choisir un journal de combat':
        'Choose a combat log',
    # gui.py
    'Journaux de combat':
        'Combat logs',
    # gui.py
    'Fichiers texte':
        'Text files',
    # gui.py
    'Tous les fichiers':
        'All files',
    # gui.py
    'Lecture de %s…':
        'Reading %s…',
    # gui.py
    'Impossible de lire %s : %s':
        'Cannot read %s: %s',
    # gui.py
    'Erreur inattendue en lisant le journal :\n\n':
        'Unexpected error while reading the log:\n\n',
    # gui.py
    'Dans quel dossier écrire les pages ?':
        'Which folder should the pages go in?',
    # gui.py
    'Où écrire le rapport ?':
        'Where should the report go?',
    # gui.py
    'Page web':
        'Web page',
    # gui.py
    'Écriture du rapport (%s)…':
        'Writing the report (%s)…',
    # gui.py
    'Erreur inattendue en écrivant le rapport :\n\n':
        'Unexpected error while writing the report:\n\n',
    # gui.py
    'Lecture… %s lignes lues':
        'Reading… %s lines read',
    # gui.py
    "Aucun combat trouvé dans ce fichier : il est peut-être vide, ou /combatlog n'était pas lancé.":
        'No fight found in this file: it may be empty, or /combatlog was not running.',
    # gui.py
    '%s, %s lignes lues en %.0f s%s.':
        '%s, %s lines read in %.0f s%s.',
    # gui.py
    ', %d non comprises':
        ', %d not understood',
    # gui.py
    'Lecture annulée.':
        'Reading cancelled.',
    # gui.py
    'La lecture a échoué.':
        'Reading failed.',
    # gui.py
    "Le rapport n'a pas été écrit.":
        'The report was not written.',
    # gui.py
    '%s sur %d dans le rapport':
        '%s of %d in the report',
    # i18n.py
    'Attaque':
        'Melee',
    # parse.py
    'marqueur -1 : %s':
        '-1 marker: %s',
    # parse.py
    'puis proximité avec %d':
        'then closeness to %d',
    # parse.py
    '%d votes / %d événements':
        '%d votes / %d events',
    # parse.py
    'ligne sans le séparateur de deux espaces':
        'line without the two-space separator',
    # parse.py
    'horodatage illisible':
        'unreadable timestamp',
    # parse.py
    "nom d'événement illisible":
        'unreadable event name',
    # report.py
    "<span class='pill ok'>boss &middot; réussite</span>":
        "<span class='pill ok'>boss &middot; kill</span>",
    # report.py
    "<span class='pill ko'>boss &middot; échec</span>":
        "<span class='pill ko'>boss &middot; wipe</span>",
    # report.py
    ' %s%s: aucune unité ne porte le nom de la rencontre (un conseil, par exemple), donc tous les dégâts infligés pendant sa durée sont comptés sur le boss.':
        " %s%.0s: no unit bears the encounter's name (a council, for instance), so all the damage dealt while it lasted counts as on the boss.",
    # report.py
    '<tr><td colspan=7 class=dim>Aucun combat délimité dans ce fichier.</td></tr>':
        '<tr><td colspan=7 class=dim>No fight found in this file.</td></tr>',
    # report.py
    '%d/%m/%Y %H:%M':
        '%Y-%m-%d %H:%M',
    # report.py
    "<h1>Rapport de combat</h1><p class=sub>%s &middot; %s lignes, %s événements &middot; généré le %s par LogsWoW %s</p><div class=note><b>Tout est resté sur cette machine.</b> Ce rapport a été produit en lisant le fichier de journal directement&nbsp;: aucun envoi, aucun compte, aucune connexion. La page est autonome, elle s'ouvre hors ligne.</div><div class=grid>%s</div><h2>Combats</h2><div class=card><table><tr><th>Combat</th><th class=n>Durée</th><th class=n>Dégâts</th><th class=n>Soins</th><th class=n>Pulls</th><th class=n>Joueurs</th><th class=n>Morts</th></tr>%s</table></div>":
        '<h1>Combat report</h1><p class=sub>%s &middot; %s lines, %s events &middot; generated on %s by LogsWoW %s</p><div class=note><b>Everything stayed on this machine.</b> This report was produced by reading the log file directly: nothing sent, no account, no connection. The page stands alone and opens offline.</div><div class=grid>%s</div><h2>Fights</h2><div class=card><table><tr><th>Fight</th><th class=n>Duration</th><th class=n>Damage</th><th class=n>Healing</th><th class=n>Pulls</th><th class=n>Players</th><th class=n>Deaths</th></tr>%s</table></div>',
    # report.py
    'Taille du fichier':
        'File size',
    # report.py
    'Durée couverte':
        'Time covered',
    # report.py
    'Pulls de boss':
        'Boss pulls',
    # report.py
    'Wipes de boss':
        'Boss wipes',
    # report.py
    'Clés mythiques':
        'Mythic keys',
    # report.py
    'Clés hors des temps':
        'Keys over time',
    # report.py
    'Lignes incomprises':
        'Lines not understood',
    # report.py
    "<h2 id='s%d'>%s%s</h2><p class=sub>%s &middot; %s &middot; %s de dégâts, %s de soins &middot; %s%s</p>":
        "<h2 id='s%d'>%s%s</h2><p class=sub>%s &middot; %s &middot; %s damage, %s healing &middot; %s%s</p>",
    # report.py
    ' &middot; journal interrompu':
        ' &middot; log cut short',
    # report.py
    'Dégâts infligés':
        'Damage done',
    # report.py
    'Soins effectifs':
        'Effective healing',
    # report.py
    "<div class=note><b>%s de dégâts ne sont comptés pour personne.</b> Ils viennent d'unités alliées qui n'appartiennent à aucun joueur nommé par le journal%s: %s. Faute de savoir à qui les attribuer, ils ne sont ni dans le total ci-dessus ni dans la ligne d'un joueur.</div>":
        "<div class=note><b>%s of damage is counted for nobody.</b> It comes from friendly units that belong to no player the log names%.0s: %s. With no way of knowing whom to credit, it is neither in the total above nor in any player's row.</div>",
    # report.py
    '<th class=n>sur le boss</th><th class=n>sur les trash</th>':
        '<th class=n>on the boss</th><th class=n>on trash</th>',
    # report.py
    "<h3>%s</h3><div class=card><table><tr><th class=n>#</th><th class=n>Début</th><th class=n>Durée</th><th>Ce qui a été engagé</th><th class=n>Dégâts</th>%s<th class=n>Subis</th><th class=n>Morts</th></tr>%s</table><p class=dim style='margin:10px 0 0;font-size:12px'>Un pull se termine quand le groupe passe plus de %s sans infliger ni subir de dégâts. Un groupe qui enchaîne les packs sans pause les verra donc regroupés%s: <code>--pull-gap</code> change ce seuil, sauf à l'intérieur d'une rencontre de boss, qui reste toujours un seul pull.%s%s</p></div>":
        "<h3>%s</h3><div class=card><table><tr><th class=n>#</th><th class=n>Start</th><th class=n>Duration</th><th>What was engaged</th><th class=n>Damage</th>%s<th class=n>Taken</th><th class=n>Deaths</th></tr>%s</table><p class=dim style='margin:10px 0 0;font-size:12px'>A pull ends when the group goes more than %s without dealing or taking damage. A group that chains packs without a pause will therefore see them grouped%.0s: <code>--pull-gap</code> changes that threshold, except inside a boss encounter, which always stays one pull.%s%s</p></div>",
    # report.py
    " %s écarté%s, trop petits pour compter (moins d'un millième des dégâts de la course).":
        " %s dropped%.0s, too small to count (less than a thousandth of the run's damage).",
    # report.py
    ' <span class=dim>(%s de surguérison)</span>':
        ' <span class=dim>(%s overhealing)</span>',
    # report.py
    '<th>Joueur</th><th class=n>Total</th>':
        '<th>Player</th><th class=n>Total</th>',
    # report.py
    '<th class=n>Absorbé</th><th class=n>Somme</th>':
        '<th class=n>Absorbed</th><th class=n>Sum</th>',
    # report.py
    "<p class=dim style='margin:10px 0 0;font-size:12px'>Un bouclier n'est pas un soin dans le journal%s: il empêche des dégâts au lieu d'en rendre. Les deux sont donc comptés à part, et additionnés dans la colonne <b>Somme</b> — c'est ce total-là que les sites en ligne appellent « soins ».</p>":
        "<p class=dim style='margin:10px 0 0;font-size:12px'>A shield is not a heal in the log%.0s: it prevents damage instead of restoring health. The two are therefore counted apart, and added up in the <b>Sum</b> column — that total is what the online sites call “healing”.</p>",
    # report.py
    "<p class=dim style='margin:6px 0 0;font-size:12px'>Le Lien d'esprit ne soigne pas%s: il prend de la santé aux joueurs les plus hauts pour la donner aux plus bas. Les %s qu'il a pris sont déduits des soins de son poseur, comme sur Warcraft Logs, et ne comptent dans les dégâts subis de personne.</p>":
        "<p class=dim style='margin:6px 0 0;font-size:12px'>Spirit Link does not heal%.0s: it takes health from the highest players to give it to the lowest. The %s it took are taken off its caster's healing, as on Warcraft Logs, and count in nobody's damage taken.</p>",
    # report.py
    "<h3>Ce qui a fait mal au groupe</h3><div class=card><table><tr><th>Capacité</th><th class=n>Dégâts</th><th class=n>Coups</th><th class=n>Joueurs touchés</th></tr>%s</table>%s<p class=dim style='margin:10px 0 0;font-size:12px'>Le fichier dit qui a été touché et combien. Il ne dit pas si le coup était évitable&nbsp;: cela demande de connaître le boss, ce que cet outil ne prétend pas savoir.</p></div>":
        "<h3>What hurt the group</h3><div class=card><table><tr><th>Ability</th><th class=n>Damage</th><th class=n>Hits</th><th class=n>Players hit</th></tr>%s</table>%s<p class=dim style='margin:10px 0 0;font-size:12px'>The file says who was hit and how hard. It does not say whether the hit was avoidable: that takes knowing the boss, which this tool does not claim to.</p></div>",
    # report.py
    "<p class=dim style='margin:8px 0 0;font-size:12.5px'>Et %s de plus, %s de dégâts en tout.</p>":
        "<p class=dim style='margin:8px 0 0;font-size:12.5px'>And %s more, %s of damage in all.</p>",
    # report.py
    ' <b>coup fatal</b>':
        ' <b>killing blow</b>',
    # report.py
    'mort instantanée':
        'instant death',
    # report.py
    'cause non écrite dans le journal':
        'cause not written in the log',
    # report.py
    '<li class=dim>Rien avant la mort dans le journal.</li>':
        '<li class=dim>Nothing before the death in the log.</li>',
    # report.py
    "<h3>Composition du groupe</h3><div class=card><table>%s</table>%s<p class=dim style='margin:10px 0 0;font-size:12px'>Le rôle vient de la spécialisation que le client écrit au début du combat. Une spécialisation que cet outil ne connaît pas est affichée par son numéro.</p></div>":
        "<h3>Group composition</h3><div class=card><table>%s</table>%s<p class=dim style='margin:10px 0 0;font-size:12px'>The role comes from the specialization the client writes at the start of the fight. A specialization this tool does not know is shown by its number.</p></div>",
    # report.py
    "<p style='margin:10px 0 0;font-size:12.5px'>Aussi présents dans le journal, sans prendre part au combat (ni dégâts, ni soins, ni coups reçus)%s: %s.</p>":
        "<p style='margin:10px 0 0;font-size:12.5px'>Also present in the log, without taking part in the fight (no damage, no healing, no hits taken)%.0s: %s.</p>",
    # report.py
    '<footer>LogsWoW %s &middot; lecture locale de <code>%s</code><br>Disposition détectée dans ce fichier&nbsp;: bloc avancé de %d champs, champ de dégâts bruts %s, champ hideCaster %s. Lignes non comprises&nbsp;: %s. Événements inconnus&nbsp;: %s.<br>Licence AGPL-3.0 ou ultérieure&nbsp;; code source&nbsp;: github.com/prenom6548/LogsWoW. Aucune donnée ne quitte cette machine.</footer></div></body></html>':
        '<footer>LogsWoW %s &middot; local reading of <code>%s</code><br>Layout detected in this file: advanced block of %d fields, raw damage field %s, hideCaster field %s. Lines not understood: %s. Unknown events: %s.<br>Licence AGPL-3.0 or later; source code: github.com/prenom6548/LogsWoW. No data leaves this machine.</footer></div></body></html>',
    # report_casts.py
    "<p class=dim style='font-size:12px'>Séquence coupée après %s sorts.</p>":
        "<p class=dim style='font-size:12px'>Sequence cut after %s casts.</p>",
    # report_casts.py
    '<details class=co><summary>Ordre des sorts, pull par pull <span class=dim>&middot; %s</span></summary><div class=cobody>%s%s<div class=pulls>%s%s</div></div></details>':
        '<details class=co><summary>Cast order, pull by pull <span class=dim>&middot; %s</span></summary><div class=cobody>%s%s<div class=pulls>%s%s</div></div></details>',
    # report_casts.py
    'Lancés':
        'Cast',
    # report_casts.py
    'Probablement déclenchés automatiquement (masqués)':
        'Probably triggered by the game (hidden)',
    # report_casts.py
    'Lancés par ses invocations':
        'Cast by their summons',
    # report_casts.py
    "<p class=dim style='font-size:12px;margin:4px 0 0'>Le journal écrit de la même façon un sort appuyé et un sort que le jeu déclenche seul. Sont lus comme déclenchés, parmi les sorts lancés au moins %d fois dans ce combat sans jamais coûter de ressource%s: ceux qui, à %d%s%% au moins, partent en même temps qu'un sort payé, avec un écart médian de %d secondes au plus entre deux lancers%s; ceux dont l'écart médian est sous %s%ss, plus vite qu'aucun bouton%s; et la seconde copie d'un sort que le journal écrit deux fois, sous le même nom, au même instant. C'est une lecture du fichier%s: cliquez pour les afficher.</p>":
        "<p class=dim style='font-size:12px;margin:4px 0 0'>The log writes a spell pressed and a spell the game fires on its own the same way. Read as triggered, among the spells cast at least %d times in this fight without ever costing a resource%.0s: those that, %d%.0s%% of the time or more, go off together with a paid spell, with a median gap of %d seconds at most between two casts%.0s; those whose median gap is under %s%.0ss, faster than any button%.0s; and the second copy of a spell the log writes twice, under the same name, at the same instant. This is a reading of the file%.0s: click to show them.</p>",
    # report_casts.py
    "<div class=legend><p class=dim style='font-size:12px;margin:0'>Cliquez sur un sort pour le masquer ou l'afficher.</p>%s%s</div>":
        "<div class=legend><p class=dim style='font-size:12px;margin:0'>Click a spell to hide or show it.</p>%s%s</div>",
    # report_casts.py
    'Entre les pulls':
        'Between pulls',
    # report_casts.py
    'Pull %02d &mdash; %s':
        'Pull %02d &mdash; %s',
    # report_casts.py
    "<p class=dim style='line-height:1.5;margin:0'>Aucun sort pendant ce pull.</p>":
        "<p class=dim style='line-height:1.5;margin:0'>No cast during this pull.</p>",
    # report_casts.py
    ', réussite':
        ', kill',
    # report_casts.py
    ', échec':
        ', wipe',
    # report_casts.py
    'trash (%s)':
        'trash (%s)',
    # report_layouts.py
    'Résumé':
        'Summary',
    # report_layouts.py
    'Dégâts et soins':
        'Damage and healing',
    # report_layouts.py
    'Physique ou magique':
        'Physical or magic',
    # report_layouts.py
    'Joueurs':
        'Players',
    # report_layouts.py
    'Ennemis':
        'Enemies',
    # report_layouts.py
    "<input type=radio name=f id=f0 class=fsel checked aria-label='Vue d&#39;ensemble'>":
        "<input type=radio name=f id=f0 class=fsel checked aria-label='Overview'>",
    # report_layouts.py
    "<label for=f0 class='nv n0'>Vue d'ensemble</label>":
        "<label for=f0 class='nv n0'>Overview</label>",
    # report_layouts.py
    "%s<div class=layout><nav class=side aria-label='Combats'>%s</nav><main>%s</main></div>%s":
        "%s<div class=layout><nav class=side aria-label='Fights'>%s</nav><main>%s</main></div>%s",
    # report_layouts.py
    "<a href='index.html'>&larr; Tous les combats</a>":
        "<a href='index.html'>&larr; All fights</a>",
    # report_panels.py
    ' et %s':
        ' and %s',
    # report_panels.py
    '<p class=dim>Rien.</p>':
        '<p class=dim>Nothing.</p>',
    # report_panels.py
    '<details class=more><summary>%s de plus &middot; %s (%s)</summary>%s</details>':
        '<details class=more><summary>%s more &middot; %s (%s)</summary>%s</details>',
    # report_panels.py
    'Sort':
        'Spell',
    # report_panels.py
    'Total':
        'Total',
    # report_panels.py
    'Part':
        'Share',
    # report_panels.py
    'Surguérison':
        'Overhealing',
    # report_panels.py
    'Casts':
        'Casts',
    # report_panels.py
    'Coups':
        'Hits',
    # report_panels.py
    'Moyenne':
        'Average',
    # report_panels.py
    'Crit':
        'Crit',
    # report_panels.py
    'Par sec.':
        'Per sec.',
    # report_panels.py
    'Principale cible':
        'Main target',
    # report_panels.py
    'Principale source':
        'Main source',
    # report_panels.py
    '<table><tr><th>Effet</th><th>%s</th><th class=n>Durée</th></tr>%s</table>':
        '<table><tr><th>Effect</th><th>%s</th><th class=n>Uptime</th></tr>%s</table>',
    # report_panels.py
    '<h3>Détail par joueur</h3>%s':
        '<h3>Player details</h3>%s',
    # report_panels.py
    ' (dont %d de ses invocations)':
        ' (%d of them by their summons)',
    # report_panels.py
    "<details><summary>%s <span class=dim>&middot; %s &middot; %s dégâts &middot; %s soins &middot; %s</span></summary><div class=body><div class='grid tiles'>%s</div>%s%s</div></details>":
        "<details><summary>%s <span class=dim>&middot; %s &middot; %s damage &middot; %s healing &middot; %s</span></summary><div class=body><div class='grid tiles'>%s</div>%s%s</div></details>",
    # report_panels.py
    'rôle inconnu':
        'unknown role',
    # report_panels.py
    'Part sur les boss':
        'Share on bosses',
    # report_panels.py
    'Subis par ses invocations':
        'Taken by their summons',
    # report_panels.py
    'Dégâts subis':
        'Damage taken',
    # report_panels.py
    'Absorbé sur lui':
        'Absorbed on them',
    # report_panels.py
    'Absorbé par ses boucliers':
        'Absorbed by their shields',
    # report_panels.py
    'Soutien crédité par le jeu':
        'Support credited by the game',
    # report_panels.py
    'Sorts par minute':
        'Casts per minute',
    # report_panels.py
    'Temps sans action':
        'Time idle',
    # report_panels.py
    'Interruptions':
        'Interrupts',
    # report_panels.py
    'Dissipations':
        'Dispels',
    # report_panels.py
    'Vie la plus basse':
        'Lowest health',
    # report_panels.py
    'Ce que ses boucliers ont absorbé':
        'What their shields absorbed',
    # report_panels.py
    'Ses dégâts':
        'Their damage',
    # report_panels.py
    'Ses soins':
        'Their healing',
    # report_panels.py
    'Qui il a soigné':
        'Whom they healed',
    # report_panels.py
    "Ce qu'il a pris":
        'What they took',
    # report_panels.py
    'Soutien que le jeu lui crédite':
        'Support the game credits them with',
    # report_panels.py
    'Plus longues pauses':
        'Longest pauses',
    # report_panels.py
    'Gains reçus':
        'Buffs received',
    # report_panels.py
    'De qui':
        'From whom',
    # report_panels.py
    'Affaiblissements subis':
        'Debuffs suffered',
    # report_panels.py
    "Ce qu'il a appliqué":
        'What they applied',
    # report_panels.py
    'Sur qui':
        'On whom',
    # report_panels.py
    "<p class=dim style='font-size:12px;margin:0'>Un effet déjà actif quand le combat commence n'a pas de ligne d'application dans le journal%s: sa durée est comptée depuis le premier événement du combat, ce qui est la seule borne que le fichier donne.</p>":
        "<p class=dim style='font-size:12px;margin:0'>An effect already up when the fight starts has no application line in the log%.0s: its uptime is counted from the fight's first event, the only bound the file gives.</p>",
    # report_panels.py
    '<li><span class=dim>%s</span> sans lancer de sort, à %s</li>':
        '<li><span class=dim>%s</span> without casting, at %s</li>',
    # report_panels.py
    '<li class=dim>Aucune pause notable.</li>':
        '<li class=dim>No notable pause.</li>',
    # report_panels.py
    "<p class=dim style='font-size:12.5px;margin:8px 0 0'><b>Sorts ennemis coupés</b>%s %s</p>":
        "<p class=dim style='font-size:12.5px;margin:8px 0 0'><b>Enemy spells interrupted</b>%.0s: %s</p>",
    # report_panels.py
    "<p class=dim style='font-size:12.5px;margin:4px 0 0'><b>Effets dissipés</b>%s %s</p>":
        "<p class=dim style='font-size:12.5px;margin:4px 0 0'><b>Effects dispelled</b>%.0s: %s</p>",
    # report_panels.py
    "%s<p class=dim style='font-size:12px;margin:4px 0 0'>Le journal crédite cet évocateur de %s de dégâts et %s de soins portés par d'autres joueurs%s: la part que ses renforts (Puissance d'ébène, Prescience...) ont ajoutée à leurs coups, et ses Bombardements, que le journal écrit au nom de l'allié qui les a déclenchés. Ces montants sont <b>déjà comptés</b> chez ceux qui ont porté les coups et ne sont pas ajoutés aux siens%s; Warcraft Logs, lui, les retire aux autres pour les lui donner, d'où l'écart entre les deux.</p>":
        "%s<p class=dim style='font-size:12px;margin:4px 0 0'>The log credits this Evoker with %s of damage and %s of healing dealt by other players%.0s: the part their buffs (Ebon Might, Prescience...) added to those hits, and their Bombardments, which the log writes under the name of the ally who set them off. These amounts are <b>already counted</b> for the players who dealt the hits and are not added to the Evoker's own%.0s; Warcraft Logs moves them from the others to the Evoker instead, hence the gap between the two.</p>",
    # report_panels.py
    '<table><tr><th>Cible</th><th class=n>Total</th><th class=n>Part</th></tr>%s</table>':
        '<table><tr><th>Target</th><th class=n>Total</th><th class=n>Share</th></tr>%s</table>',
    # report_panels.py
    "Ce qu'il inflige":
        'What it deals',
    # report_panels.py
    "Ce qu'il a subi":
        'What it took',
    # report_panels.py
    'Ses sorts':
        'Its spells',
    # report_panels.py
    '<table><tr><th>Sort</th><th class=n>Lancés</th></tr>%s</table>':
        '<table><tr><th>Spell</th><th class=n>Cast</th></tr>%s</table>',
    # report_panels.py
    'Unités':
        'Units',
    # report_panels.py
    'Sorts lancés':
        'Spells cast',
    # report_panels.py
    'Tués':
        'Killed',
    # report_panels.py
    "<details><summary>%s <span class=dim>&middot; %s &middot; %s infligé &middot; %s subi</span></summary><div class=body><div class='grid tiles'>%s</div>%s</div></details>":
        "<details><summary>%s <span class=dim>&middot; %s &middot; %s dealt &middot; %s taken</span></summary><div class=body><div class='grid tiles'>%s</div>%s</div></details>",
    # report_panels.py
    '<h3>Détail par ennemi</h3>%s':
        '<h3>Enemy details</h3>%s',
    # report_panels.py
    'Aboutis':
        'Completed',
    # report_panels.py
    'Coupés par une interruption':
        'Cut by an interrupt',
    # report_panels.py
    "Lanceur tué pendant l'incantation":
        'Caster killed mid-cast',
    # report_panels.py
    'Non aboutis, cause non dite par le journal':
        'Not completed, cause not given by the log',
    # report_panels.py
    "<p class=dim style='margin:10px 0 0;font-size:12px'>Les plus coupés%s: %s.</p>":
        "<p class=dim style='margin:10px 0 0;font-size:12px'>Most interrupted%.0s: %s.</p>",
    # report_panels.py
    "<h3>Ce que le groupe a empêché</h3><div class=card><p class=dim style='margin:0 0 10px;font-size:12.5px'>%s sorts commencés par l'ennemi%s:</p><table><tr><th>Issue</th><th class=n>Nombre</th><th class=n>Part</th></tr>%s</table>%s<p class=dim style='margin:10px 0 0;font-size:12px'>Un sort instantané n'apparaît pas ici%s: seuls ceux qui ont un temps d'incantation laissent une trace. La dernière ligne regroupe tout le reste, contrôle compris%s: le journal ne dit nulle part qu'un sort est un étourdissement, donc rien ici ne prétend le savoir.</p></div>":
        "<h3>What the group prevented</h3><div class=card><p class=dim style='margin:0 0 10px;font-size:12.5px'>%s spells begun by the enemy%.0s:</p><table><tr><th>Outcome</th><th class=n>Count</th><th class=n>Share</th></tr>%s</table>%s<p class=dim style='margin:10px 0 0;font-size:12px'>An instant spell does not appear here%.0s: only those with a cast time leave a trace. The last row gathers all the rest, crowd control included%.0s: the log never says a spell is a stun, so nothing here claims to know.</p></div>",
    # report_schools.py
    'Physique':
        'Physical',
    # report_schools.py
    'Magique':
        'Magic',
    # report_schools.py
    'Mixte':
        'Mixed',
    # report_schools.py
    'Phys.':
        'Phys.',
    # report_schools.py
    'Mag.':
        'Mag.',
    # report_schools.py
    'Subis':
        'Taken',
    # report_schools.py
    'Infligés':
        'Dealt',
    # report_schools.py
    "<p class=dim style='font-size:12.5px;margin:6px 0 0'><b>%s par école</b>%s: %s</p>":
        "<p class=dim style='font-size:12.5px;margin:6px 0 0'><b>%s by school</b>%.0s: %s</p>",
    # report_schools.py
    "<h3>Physique ou magique</h3><div class='card schools'><p style='margin:0 0 8px;font-size:12.5px'>%s</p><table><tr><th></th><th>Répartition</th>%s</tr>%s</table>%s%s<p class=dim style='margin:10px 0 0;font-size:12px'>L'école de chaque coup est celle que le journal écrit sur la ligne. « Mixte »%s: physique et magique à la fois (Ombre-frappe, Chaos...). Comme dans le reste du rapport, un coup qu'un bouclier ennemi a mangé compte dans les dégâts infligés, et la part qu'un bouclier du groupe a mangée ne compte pas dans les dégâts subis.</p></div>":
        "<h3>Physical or magic</h3><div class='card schools'><p style='margin:0 0 8px;font-size:12.5px'>%s</p><table><tr><th></th><th>Split</th>%s</tr>%s</table>%s%s<p class=dim style='margin:10px 0 0;font-size:12px'>Each hit's school is the one the log writes on its line. “Mixed”%.0s: physical and magic at once (Shadowstrike, Chaos...). As in the rest of the report, a hit an enemy shield ate counts in damage dealt, and the part a group shield ate does not count in damage taken.</p></div>",
    # report_schools.py
    "<h3 style='margin-top:18px'>Pull par pull</h3><table><tr><th class=n>#</th><th>Ce qui a été engagé</th><th>Subis</th>%s<th>Infligés</th>%s</tr>%s</table>":
        "<h3 style='margin-top:18px'>Pull by pull</h3><table><tr><th class=n>#</th><th>What was engaged</th><th>Taken</th>%s<th>Dealt</th>%s</tr>%s</table>",
    # report_timeline.py
    "<h3>Dégâts subis par le groupe, seconde par seconde</h3><div class=card><svg viewBox='0 0 %d %d' role=img aria-label='Dégâts subis au fil du combat'>%s</svg><p class=dim style='margin:6px 0 0;font-size:12px'>Barres et échelle de gauche%s: dégâts subis par intervalle de %s. Traits rouges%s: morts.%s</p></div>":
        "<h3>Damage taken by the group, second by second</h3><div class=card><svg viewBox='0 0 %d %d' role=img aria-label='Damage taken over the fight'>%s</svg><p class=dim style='margin:6px 0 0;font-size:12px'>Bars and left-hand scale%.0s: damage taken per interval of %s. Red lines%.0s: deaths.%s</p></div>",
    # report_timeline.py
    " Courbe et échelle de droite%s: <b>vie cumulée des ennemis engagés</b>, somme de leurs points de vie courants sur la somme de leurs maximums. Elle remonte à chaque nouveau pack et retombe quand il meurt%s; un ennemi que le groupe n'a plus touché depuis %d%ss en sort.":
        ' Curve and right-hand scale%.0s: <b>pooled health of the engaged enemies</b>, the sum of their current health over the sum of their maximums. It rises with each new pack and falls as it dies%.0s; an enemy the group has not hit for %d%ss drops out of it.',
    # report_timeline.py
    ' Courbe et échelle de droite%s: vie de <b>%s</b>, la cible la plus frappée parmi celles dont le journal donne les points de vie.':
        ' Curve and right-hand scale%.0s: health of <b>%s</b>, the most-hit target among those whose health the log gives.',
    # schools.py
    'Sacré':
        'Holy',
    # schools.py
    'Feu':
        'Fire',
    # schools.py
    'Nature':
        'Nature',
    # schools.py
    'Givre':
        'Frost',
    # schools.py
    'Ombre':
        'Shadow',
    # schools.py
    'Arcane':
        'Arcane',
    # schools.py
    'école inconnue':
        'unknown school',
    # segment.py
    'Normal':
        'Normal',
    # segment.py
    'Héroïque':
        'Heroic',
    # segment.py
    '10 joueurs':
        '10 Player',
    # segment.py
    '25 joueurs':
        '25 Player',
    # segment.py
    '10 héroïque':
        '10 Player Heroic',
    # segment.py
    '25 héroïque':
        '25 Player Heroic',
    # segment.py
    'Raid Recherche':
        'Raid Finder',
    # segment.py
    'Mythique+':
        'Mythic+',
    # segment.py
    '40 joueurs':
        '40 Player',
    # segment.py
    'Héroïque scénario':
        'Heroic Scenario',
    # segment.py
    'Normal scénario':
        'Normal Scenario',
    # segment.py
    'Mythique':
        'Mythic',
    # segment.py
    'Marche du temps':
        'Timewalking',
    # segment.py
    'Torghast':
        'Torghast',
    # segment.py
    'difficulté %d':
        'difficulty %d',
    # segment.py
    'sans combat':
        'no fight',
    # segment.py
    'interrompu':
        'cut short',
    # segment.py
    'dans les temps':
        'in time',
    # segment.py
    'hors des temps':
        'over time',
    # segment.py
    'réussite':
        'kill',
    # segment.py
    'échec':
        'wipe',
    # segment.py
    'Donjon':
        'Dungeon',
    # segment.py
    'Session complète':
        'Whole session',
    # specs.py
    'spe %d':
        'spec %d',
}

# The French nouns `fmt.plural` agrees, and their English forms.
PLURALS = {
    'autre': ('other', 'others'),
    'capacité': ('ability', 'abilities'),
    'cible': ('target', 'targets'),
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
