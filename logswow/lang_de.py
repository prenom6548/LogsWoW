# SPDX-License-Identifier: AGPL-3.0-or-later
"""German: every French text of the interface, and its translation.

The keys are the French texts exactly as the code writes them; a test
fails when one is missing here, or when a translation does not keep
the original's %-placeholders and HTML tags in the same order.
`%.0s` swallows an argument: French passes a narrow no-break space
before a colon, which German does not want.
"""

TEXTS = {
    # analysis
    'source non nommée par le journal':
        'Quelle, die das Protokoll nicht nennt',
    'Tanks':
        'Tanks',
    'Soigneurs':
        'Heiler',
    'Rôle non indiqué':
        'Rolle nicht angegeben',
    # cli
    '\r  %s lignes lues...':
        '\r  %s Zeilen gelesen...',
    'Fichier introuvable : %s\n':
        'Datei nicht gefunden: %s\n',
    '%s est un dossier, pas un fichier de journal. Cherchez-y WoWCombatLog.txt.\n':
        '%s ist ein Ordner, keine Protokolldatei. Suchen Sie darin nach WoWCombatLog.txt.\n',
    'Impossible de lire %s : %s\n':
        '%s kann nicht gelesen werden: %s\n',
    "Aucun combat n'a été trouvé dans %s. Le fichier est peut-être vide, ou écrit par une version du client que ce lecteur ne comprend pas : `diagnose` dit ce qui a été lu.\n":
        'In %s wurde kein Kampf gefunden. Die Datei ist vielleicht leer oder von einer Client-Version geschrieben, die dieses Programm nicht versteht: `diagnose` zeigt, was gelesen wurde.\n',
    "Refus d'écrire le rapport par-dessus le journal lui-même (%s). Choisissez un autre nom avec -o.\n":
        'Der Bericht wird nicht über das Protokoll selbst geschrieben (%s). Wählen Sie mit -o einen anderen Namen.\n',
    '%s est un dossier : donnez un nom de fichier avec -o.\n':
        '%s ist ein Ordner: Geben Sie mit -o einen Dateinamen an.\n',
    "%s existe et n'est pas un rapport LogsWoW : refus de l'écraser. Choisissez un autre nom, ou ajoutez --force si c'est voulu.\n":
        '%s existiert und ist kein LogsWoW-Bericht: Die Datei wird nicht überschrieben. Wählen Sie einen anderen Namen oder fügen Sie --force hinzu, wenn das gewollt ist.\n',
    "%s existe et n'est pas un dossier : donnez un autre nom avec -o.\n":
        '%s existiert und ist kein Ordner: Geben Sie mit -o einen anderen Namen an.\n',
    "Refus d'écrire les pages dans le dossier du journal lui-même (%s). Donnez un autre dossier avec -o.\n":
        'Die Seiten werden nicht in den Ordner des Protokolls selbst geschrieben (%s). Geben Sie mit -o einen anderen Ordner an.\n',
    "%s contient déjà autre chose qu'un rapport LogsWoW : refus d'y écrire. Choisissez un autre dossier, ou ajoutez --force si c'est voulu.\n":
        '%s enthält bereits etwas anderes als einen LogsWoW-Bericht: Dort wird nicht geschrieben. Wählen Sie einen anderen Ordner oder fügen Sie --force hinzu, wenn das gewollt ist.\n',
    'Aucun combat ne correspond à --only %r. Utilisez `list` pour les voir.\n':
        'Kein Kampf passt zu --only %r. Mit `list` werden alle angezeigt.\n',
    "Impossible d'écrire %s : %s\n":
        '%s kann nicht geschrieben werden: %s\n',
    '%d combat(s) retenu(s) sur %d, %s lignes lues en %.1f s':
        '%d von %d Kämpfen übernommen, %s Zeilen in %.1f s gelesen',
    '%d lignes non comprises -- lancez `diagnose` pour voir lesquelles':
        '%d Zeilen nicht verstanden -- `diagnose` zeigt, welche',
    'Rapport écrit : %s':
        'Bericht geschrieben: %s',
    'Combat':
        'Kampf',
    'Durée':
        'Dauer',
    'Dégâts':
        'Schaden',
    'Morts':
        'Tode',
    'Aucun dossier Logs trouvé aux emplacements habituels.':
        'Kein Logs-Ordner an den üblichen Orten gefunden.',
    'Cherchez WoWCombatLog.txt sous _retail_/Logs dans votre installation,':
        'Suchen Sie WoWCombatLog.txt unter _retail_/Logs in Ihrer Installation',
    "puis donnez son chemin complet, entre guillemets s'il contient des espaces :":
        'und geben Sie den vollständigen Pfad an, in Anführungszeichen, wenn er Leerzeichen enthält:',
    '  report "/chemin/vers/World of Warcraft/_retail_/Logs/WoWCombatLog-....txt"':
        '  report "/Pfad/zu/World of Warcraft/_retail_/Logs/WoWCombatLog-....txt"',
    "Pas d'écran disponible pour ouvrir la fenêtre : utilisez les commandes (voir --help).\n":
        'Kein Bildschirm verfügbar, um das Fenster zu öffnen: Verwenden Sie die Befehle (siehe --help).\n',
    "%r n'est pas un nombre de secondes":
        '%r ist keine Anzahl von Sekunden',
    '%r : il faut un nombre de secondes entre 0 et 86400':
        '%r: Es wird eine Anzahl von Sekunden zwischen 0 und 86400 benötigt',
    "%r n'est pas un nombre entier":
        '%r ist keine ganze Zahl',
    '%r : il faut un nombre supérieur à zéro':
        '%r: Es wird eine Zahl größer als null benötigt',
    "langue de l'interface et du rapport : auto (celle du système, l'anglais pour une langue sans traduction), fr, en, de ou es":
        'Sprache der Oberfläche und des Berichts: auto (die des Systems, Englisch für eine Sprache ohne Übersetzung), fr, en, de oder es',
    'Lit un journal de combat de World of Warcraft, en local, sans rien envoyer nulle part.':
        'Liest ein Kampfprotokoll von World of Warcraft, lokal, ohne irgendetwas irgendwohin zu senden.',
    'sans la progression ni le résumé : seulement les erreurs':
        'ohne Fortschritt und Zusammenfassung: nur Fehler',
    'chemin du fichier WoWCombatLog.txt':
        'Pfad zur Datei WoWCombatLog.txt',
    "année, pour les journaux dont l'horodatage n'en porte pas":
        'Jahr, für Protokolle, deren Zeitstempel keines enthalten',
    'SECONDES':
        'SEKUNDEN',
    'silence nécessaire pour séparer deux pulls (défaut %d s) ; baissez-le si vos packs sont regroupés, montez-le si un pull unique est coupé en deux':
        'Pause, die zwei Pulls trennt (Standard %d s); senken Sie sie, wenn Ihre Packs zusammengezogen werden, erhöhen Sie sie, wenn ein einzelner Pull in zwei geteilt wird',
    'produit le rapport HTML':
        'erstellt den HTML-Bericht',
    'fichier de sortie (.html)':
        'Ausgabedatei (.html)',
    "ne pas mettre l'ordre des sorts de chaque joueur : la page est environ deux fois plus légère":
        'die Zauberreihenfolge jedes Spielers weglassen: Die Seite wird etwa halb so groß',
    'présentation du rapport : onglets (un fichier, un combat et une catégorie à la fois, par défaut), pages (un dossier, une page par combat) ou longue (tout sur une seule page)':
        'Aufbau des Berichts: onglets (eine Datei, ein Kampf und ein Bereich auf einmal, Standard), pages (ein Ordner, eine Seite pro Kampf) oder longue (alles auf einer Seite)',
    "écraser le fichier de sortie même s'il n'est pas un rapport LogsWoW (jamais le journal lu)":
        'die Ausgabedatei überschreiben, auch wenn sie kein LogsWoW-Bericht ist (niemals das gelesene Protokoll)',
    'NUMÉRO|NOM':
        'NUMMER|NAME',
    "n'inclure qu'un combat : son numéro dans `list`, ou un bout de son nom":
        'nur einen Kampf aufnehmen: seine Nummer in `list` oder einen Teil seines Namens',
    'LANGUE':
        'SPRACHE',
    'langue des liens Wowhead : auto (celle du système), fr, en, de, es, it, pt, ru, ko, zh, ou off pour ne mettre aucun lien':
        'Sprache der Wowhead-Links: auto (die des Systems), fr, en, de, es, it, pt, ru, ko, zh oder off für keine Links',
    'liste les combats du fichier':
        'listet die Kämpfe der Datei auf',
    'montre ce que le lecteur a compris du fichier':
        'zeigt, was das Programm von der Datei verstanden hat',
    "s'arrêter après N événements":
        'nach N Ereignissen anhalten',
    'cherche le dossier Logs du jeu':
        'sucht den Logs-Ordner des Spiels',
    "ouvre la fenêtre (c'est aussi ce que fait la commande sans rien)":
        'öffnet das Fenster (das tut auch der Befehl ohne Angaben)',
    '\nInterrompu.\n':
        '\nUnterbrochen.\n',
    # diagnose
    'Fichier    : %s':
        'Datei      : %s',
    'Taille     : %s, %s lignes, %s événements':
        'Größe      : %s, %s Zeilen, %s Ereignisse',
    'Durée      : %s':
        'Dauer      : %s',
    'DISPOSITION MESURÉE DANS CE FICHIER':
        'IN DIESER DATEI GEMESSENER AUFBAU',
    '  bloc avancé         : %d champs  (votes: %s)':
        '  erweiterter Block   : %d Felder  (Stimmen: %s)',
    '    votes à égalité, départage par : %s':
        '    Stimmengleichheit, entschieden durch: %s',
    '  champ baseAmount    : %s  (position du -1: %s)':
        '  Feld baseAmount     : %s  (Position der -1: %s)',
    'présent':
        'vorhanden',
    'absent':
        'nicht vorhanden',
    '  champ hideCaster    : %s  (%s)':
        '  Feld hideCaster     : %s  (%s)',
    '  journalisation avancée : %s':
        '  erweiterte Protokollierung : %s',
    'oui':
        'ja',
    'non -- positions et points de vie absents':
        'nein -- Positionen und Lebenspunkte fehlen',
    '  événements avec bloc avancé : %d sur %d':
        '  Ereignisse mit erweitertem Block : %d von %d',
    '  points de vie incohérents   : %d (courants > maximum ; ignorés pour les courbes de vie ennemies)':
        '  widersprüchliche Lebenspunkte : %d (aktuell > Maximum; bei den Lebenskurven der Gegner ignoriert)',
    'COMBATS DÉLIMITÉS : %d':
        'ABGEGRENZTE KÄMPFE: %d',
    'JOUEURS VUS : %d':
        'GESEHENE SPIELER: %d',
    'ÉVÉNEMENTS (%d types)':
        'EREIGNISSE (%d Arten)',
    '[SCHÉMA INCONNU] ':
        '[UNBEKANNTES SCHEMA] ',
    'LIGNES NON RÉSOLUES':
        'NICHT AUFGELÖSTE ZEILEN',
    'LIGNES NON RÉSOLUES : aucune':
        'NICHT AUFGELÖSTE ZEILEN: keine',
    'PROBLÈMES DE LECTURE : %d':
        'LESEPROBLEME: %d',
    '    ligne %s : %s | %s':
        '    Zeile %s: %s | %s',
    # encounters
    'Rencontre':
        'Begegnung',
    # events
    'événement inconnu':
        'unbekanntes Ereignis',
    'champs de base manquants':
        'Grundfelder fehlen',
    'ligne trop courte : %d champs pour un préfixe de %d':
        'Zeile zu kurz: %d Felder für ein Präfix von %d',
    'nombre de champs inattendu : %d après le préfixe, attendu %s, ou cela +%d':
        'unerwartete Anzahl von Feldern: %d nach dem Präfix, erwartet %s oder das +%d',
    # gui
    "La fenêtre de LogsWoW a besoin de Tkinter, qui fait partie de Python mais\nque certaines distributions Linux livrent à part. Pour l'installer :\n  Linux Mint, Ubuntu, Debian : sudo apt install python3-tk\n  Fedora                     : sudo dnf install python3-tkinter\n  Arch, Manjaro              : sudo pacman -S tk\n  openSUSE                   : sudo zypper install python3-tk\n  macOS (Homebrew)           : brew install python-tk\nSous Windows, et sous macOS avec l'installateur de python.org, il est déjà là.\nLes commandes du terminal fonctionnent sans lui (voir ci-dessous).\n":
        'Das Fenster von LogsWoW benötigt Tkinter, das zu Python gehört, aber\nvon manchen Linux-Distributionen getrennt ausgeliefert wird. So wird es installiert:\n  Linux Mint, Ubuntu, Debian : sudo apt install python3-tk\n  Fedora                     : sudo dnf install python3-tkinter\n  Arch, Manjaro              : sudo pacman -S tk\n  openSUSE                   : sudo zypper install python3-tk\n  macOS (Homebrew)           : brew install python-tk\nUnter Windows und unter macOS mit dem Installer von python.org ist es schon vorhanden.\nDie Befehle im Terminal funktionieren auch ohne (siehe unten).\n',
    'Go':
        'GB',
    'Mo':
        'MB',
    'Ko':
        'KB',
    '%d o':
        '%d B',
    'Onglets (un fichier)':
        'Registerkarten (eine Datei)',
    'Pages (un dossier)':
        'Seiten (ein Ordner)',
    'Une seule longue page':
        'Eine einzige lange Seite',
    "Impossible d'écrire %s : %s":
        '%s kann nicht geschrieben werden: %s',
    'Choisissez un journal, puis « Lire ce journal ».':
        'Wählen Sie ein Protokoll, dann „Dieses Protokoll lesen“.',
    "Tout se passe sur cet ordinateur : aucune donnée n'est envoyée.":
        'Alles geschieht auf diesem Computer: Es werden keine Daten gesendet.',
    ' 1. Le journal ':
        ' 1. Das Protokoll ',
    'Fichier':
        'Datei',
    'Date':
        'Datum',
    'Taille':
        'Größe',
    'Dossier':
        'Ordner',
    'Choisir un autre fichier…':
        'Andere Datei wählen…',
    'Actualiser la liste':
        'Liste aktualisieren',
    'Lire ce journal':
        'Dieses Protokoll lesen',
    'Silence entre deux pulls : ':
        'Pause zwischen zwei Pulls: ',
    'Annuler':
        'Abbrechen',
    ' 2. Les combats ':
        ' 2. Die Kämpfe ',
    'Issue':
        'Ergebnis',
    'Tout sélectionner':
        'Alle auswählen',
    ' 3. Le rapport ':
        ' 3. Der Bericht ',
    'Ordre des sorts de chaque joueur (la page est environ deux fois plus lourde)':
        'Zauberreihenfolge jedes Spielers (die Seite wird etwa doppelt so groß)',
    'Présentation :':
        'Aufbau:',
    "Créer le rapport et l'ouvrir":
        'Bericht erstellen und öffnen',
    'Ouvrir le dossier du rapport':
        'Ordner des Berichts öffnen',
    '%d/%m/%Y %H:%M':
        '%d.%m.%Y %H:%M',
    "Aucun journal trouvé aux emplacements habituels : « Choisir un autre fichier… » pour l'indiquer.":
        'Kein Protokoll an den üblichen Orten gefunden: „Andere Datei wählen…“, um eines anzugeben.',
    'Choisir un journal de combat':
        'Ein Kampfprotokoll wählen',
    'Journaux de combat':
        'Kampfprotokolle',
    'Fichiers texte':
        'Textdateien',
    'Tous les fichiers':
        'Alle Dateien',
    'Lecture de %s…':
        '%s wird gelesen…',
    'Impossible de lire %s : %s':
        '%s kann nicht gelesen werden: %s',
    'Erreur inattendue en lisant le journal :\n\n':
        'Unerwarteter Fehler beim Lesen des Protokolls:\n\n',
    'Dans quel dossier écrire les pages ?':
        'In welchen Ordner sollen die Seiten geschrieben werden?',
    'Où écrire le rapport ?':
        'Wohin soll der Bericht geschrieben werden?',
    'Page web':
        'Webseite',
    'Écriture du rapport (%s)…':
        'Bericht wird geschrieben (%s)…',
    'Erreur inattendue en écrivant le rapport :\n\n':
        'Unerwarteter Fehler beim Schreiben des Berichts:\n\n',
    'Lecture… %s, %s lignes lues':
        'Lesen… %s, %s Zeilen gelesen',
    ', encore environ %s':
        ', noch etwa %s',
    '%d s':
        '%d s',
    '%d min %02d s':
        '%d Min. %02d s',
    "Aucun combat trouvé dans ce fichier : il est peut-être vide, ou /combatlog n'était pas lancé.":
        'Kein Kampf in dieser Datei gefunden: Sie ist vielleicht leer, oder /combatlog war nicht aktiv.',
    '%s, %s lignes lues en %.0f s%s.':
        '%s, %s Zeilen in %.0f s gelesen%s.',
    ', %d non comprises':
        ', %d nicht verstanden',
    'Lecture annulée.':
        'Lesen abgebrochen.',
    'La lecture a échoué.':
        'Das Lesen ist fehlgeschlagen.',
    "Le rapport n'a pas été écrit.":
        'Der Bericht wurde nicht geschrieben.',
    '%s sur %d dans le rapport':
        '%s von %d im Bericht',
    # i18n
    'Attaque':
        'Nahkampf',
    # parse
    'marqueur -1 : %s':
        'Marke -1: %s',
    'puis proximité avec %d':
        'dann Nähe zu %d',
    '%d votes / %d événements':
        '%d Stimmen / %d Ereignisse',
    'ligne sans le séparateur de deux espaces':
        'Zeile ohne das Trennzeichen aus zwei Leerzeichen',
    'horodatage illisible':
        'unlesbarer Zeitstempel',
    "nom d'événement illisible":
        'unlesbarer Ereignisname',
    # report
    'aucun':
        'keine',
    "<span class='pill ok'>boss &middot; réussite</span>":
        "<span class='pill ok'>Boss &middot; Kill</span>",
    "<span class='pill ko'>boss &middot; échec</span>":
        "<span class='pill ko'>Boss &middot; Wipe</span>",
    'tank':
        'Tank',
    'soigneur':
        'Heiler',
    'DPS':
        'DPS',
    ', par une invocation':
        ', über eine Beschwörung',
    'Ouvert par %s%s: %s':
        'Eröffnet von %s%.0s: %s',
    'bêta':
        'Beta',
    '<b>%s</b> a agi en premier, sur %s%s: %s':
        '<b>%s</b> handelte zuerst, gegen %s%.0s: %s',
    ', %s%ss avant le premier coup':
        ', %s%ss vor dem ersten Treffer',
    '%s; %s%ss plus tôt, %s avait aidé <b>%s</b> (%s)':
        '%.0s; %s%ss vorher hatte %s <b>%s</b> geholfen (%s)',
    'Premier coup reçu par chaque ennemi (%s)':
        'Erster Treffer, den jeder Gegner erhielt (%s)',
    ' %s%s: aucune unité ne porte le nom de la rencontre (un conseil, par exemple), donc tous les dégâts infligés pendant sa durée sont comptés sur le boss.':
        ' %s%.0s: Keine Einheit trägt den Namen der Begegnung (zum Beispiel ein Rat), daher wird der gesamte Schaden während ihrer Dauer dem Boss zugerechnet.',
    '<tr><td colspan=7 class=dim>Aucun combat délimité dans ce fichier.</td></tr>':
        '<tr><td colspan=7 class=dim>In dieser Datei wurde kein Kampf abgegrenzt.</td></tr>',
    "<h1>Rapport de combat</h1><p class=sub>%s &middot; %s lignes, %s événements &middot; généré le %s par LogsWoW %s</p><div class=note><b>Tout est resté sur cette machine.</b> Ce rapport a été produit en lisant le fichier de journal directement&nbsp;: aucun envoi, aucun compte, aucune connexion. La page est autonome, elle s'ouvre hors ligne.</div><div class=grid>%s</div><h2>Combats</h2><div class=card><table><tr><th>Combat</th><th class=n>Durée</th><th class=n>Dégâts</th><th class=n>Soins</th><th class=n>Pulls</th><th class=n>Joueurs</th><th class=n>Morts</th></tr>%s</table></div>":
        '<h1>Kampfbericht</h1><p class=sub>%s &middot; %s Zeilen, %s Ereignisse &middot; erstellt am %s von LogsWoW %s</p><div class=note><b>Alles ist auf diesem Rechner geblieben.</b> Dieser Bericht wurde durch direktes Lesen der Protokolldatei erstellt: nichts gesendet, kein Konto, keine Verbindung. Die Seite ist eigenständig und öffnet sich offline.</div><div class=grid>%s</div><h2>Kämpfe</h2><div class=card><table><tr><th>Kampf</th><th class=n>Dauer</th><th class=n>Schaden</th><th class=n>Heilung</th><th class=n>Pulls</th><th class=n>Spieler</th><th class=n>Tode</th></tr>%s</table></div>',
    'Taille du fichier':
        'Dateigröße',
    'Durée couverte':
        'Erfasste Dauer',
    'Pulls de boss':
        'Boss-Pulls',
    'Wipes de boss':
        'Boss-Wipes',
    'Clés mythiques':
        'Mythische Schlüssel',
    'Clés hors des temps':
        'Schlüssel über der Zeit',
    'Clés non terminées':
        'Nicht beendete Schlüssel',
    'Lignes incomprises':
        'Nicht verstandene Zeilen',
    "<h2 id='s%d'>%s%s</h2><p class=sub>%s &middot; %s &middot; %s de dégâts, %s de soins &middot; %s%s</p>":
        "<h2 id='s%d'>%s%s</h2><p class=sub>%s &middot; %s &middot; %s Schaden, %s Heilung &middot; %s%s</p>",
    ' &middot; journal interrompu':
        ' &middot; Protokoll unterbrochen',
    'Dégâts infligés':
        'Verursachter Schaden',
    'Soins effectifs':
        'Effektive Heilung',
    "<div class=note><b>%s de dégâts ne sont comptés pour personne.</b> Ils viennent d'unités alliées qui n'appartiennent à aucun joueur nommé par le journal%s: %s. Faute de savoir à qui les attribuer, ils ne sont ni dans le total ci-dessus ni dans la ligne d'un joueur.</div>":
        '<div class=note><b>%s Schaden wird niemandem zugerechnet.</b> Er stammt von verbündeten Einheiten, die keinem vom Protokoll genannten Spieler gehören%.0s: %s. Da unbekannt ist, wem er gutzuschreiben ist, steht er weder in der Summe oben noch in der Zeile eines Spielers.</div>',
    '<th class=n>sur le boss</th><th class=n>sur les trash</th>':
        '<th class=n>auf den Boss</th><th class=n>auf Trash</th>',
    "<h3>%s</h3><div class=card><table><tr><th class=n>#</th><th class=n>Début</th><th class=n>Durée</th><th>Ce qui a été engagé</th><th class=n>Dégâts</th>%s<th class=n>Subis</th><th class=n>Morts</th></tr>%s</table><p class=dim style='margin:10px 0 0;font-size:12px'>Un pull se termine quand le groupe passe plus de %s sans infliger ni subir de dégâts. Un groupe qui enchaîne les packs sans pause les verra donc regroupés%s: <code>--pull-gap</code> change ce seuil, sauf à l'intérieur d'une rencontre de boss, qui reste toujours un seul pull.%s%s</p></div>":
        "<h3>%s</h3><div class=card><table><tr><th class=n>#</th><th class=n>Beginn</th><th class=n>Dauer</th><th>Was angegriffen wurde</th><th class=n>Schaden</th>%s<th class=n>Erlitten</th><th class=n>Tode</th></tr>%s</table><p class=dim style='margin:10px 0 0;font-size:12px'>Ein Pull endet, wenn die Gruppe länger als %s weder Schaden verursacht noch erleidet. Eine Gruppe, die Packs ohne Pause aneinanderreiht, sieht sie daher zusammengefasst%.0s: <code>--pull-gap</code> ändert diese Schwelle, außer innerhalb einer Bossbegegnung, die immer ein einziger Pull bleibt.%s%s</p></div>",
    " %s écarté%s, trop petit%s pour compter (moins d'un millième des dégâts de la course).":
        ' %s verworfen%.0s, zu klein%.0s, um zu zählen (weniger als ein Tausendstel des Schadens des Durchgangs).',
    " Sous chaque pull, le premier acte qui lie le groupe à un ennemi depuis la fin du pull précédent%s: le journal n'a aucune ligne de menace, donc un ennemi pris par proximité ne s'y voit qu'à ce qu'il fait ensuite. Quand c'est l'ennemi qui agit en premier, sa première cible est un fort indice de qui l'a attiré, pas une preuve (une zone au sol laissée par le pack précédent, par exemple)%s; et un soin, un renfort ou une dissipation donné en combat attire l'ennemi vers celui qui l'a donné, si bien que la ligne dit aussi quand cette cible venait d'en donner un. Cette lecture est en bêta. Le premier coup reçu par chaque ennemi, lui, est écrit tel quel dans le journal.":
        ' Unter jedem Pull steht die erste Handlung, die die Gruppe seit dem Ende des vorigen Pulls mit einem Gegner verbindet%.0s: Das Protokoll hat keine Bedrohungszeile, daher ist ein Gegner, der durch Nähe angelockt wurde, nur an dem zu erkennen, was er danach tut. Handelt der Gegner zuerst, ist sein erstes Ziel ein starker Hinweis darauf, wer ihn angelockt hat, kein Beweis (etwa ein Bodeneffekt, den das vorige Pack hinterlassen hat)%.0s; und eine Heilung, Stärkung oder Bannung im Kampf lenkt den Gegner auf den, der sie gegeben hat, daher sagt die Zeile auch, wenn dieses Ziel gerade eine gegeben hatte. Diese Lesart ist in der Beta. Der erste Treffer, den jeder Gegner erhielt, steht dagegen genau so im Protokoll.',
    ' <span class=dim>(%s de surguérison)</span>':
        ' <span class=dim>(%s Überheilung)</span>',
    '<th>Joueur</th><th class=n>Total</th>':
        '<th>Spieler</th><th class=n>Gesamt</th>',
    '<th class=n>Absorbé</th><th class=n>Somme</th>':
        '<th class=n>Absorbiert</th><th class=n>Summe</th>',
    '<th class=n>Réattribué</th>':
        '<th class=n>Neu zugeordnet</th>',
    "<p class=dim style='margin:10px 0 0;font-size:12px'><b>Réattribué</b>%s: les dégâts de chacun, moins la part que le jeu crédite aux renforts d'un évocateur (Puissance d'ébène, Prescience, Bombardements...), plus ce qu'il crédite au joueur lui-même. C'est la réattribution de Warcraft Logs, et la seule que le journal permet%s: aucune ligne ne dit ce qu'une Furie sanguinaire, une Infusion de puissance ou un buff de raid a ajouté aux coups des autres. Le total du groupe ne change pas.</p>":
        "<p class=dim style='margin:10px 0 0;font-size:12px'><b>Neu zugeordnet</b>%.0s: der Schaden jedes Spielers, abzüglich des Anteils, den das Spiel den Stärkungen eines Rufers gutschreibt (Ebenholzmacht, Voraussicht, Bombardements...), zuzüglich dessen, was es dem Spieler selbst gutschreibt. Das ist die Neuzuordnung von Warcraft Logs und die einzige, die das Protokoll erlaubt%.0s: Keine Zeile sagt, was Kampfrausch, Seele der Macht oder eine Schlachtzugsstärkung zu den Treffern der anderen beigetragen hat. Die Summe der Gruppe ändert sich nicht.</p>",
    "<p class=dim style='margin:10px 0 0;font-size:12px'>Un bouclier n'est pas un soin dans le journal%s: il empêche des dégâts au lieu d'en rendre. Les deux sont donc comptés à part, et additionnés dans la colonne <b>Somme</b> — c'est ce total-là que les sites en ligne appellent « soins ».</p>":
        "<p class=dim style='margin:10px 0 0;font-size:12px'>Ein Schild ist im Protokoll keine Heilung%.0s: Er verhindert Schaden, statt Leben zurückzugeben. Beides wird daher getrennt gezählt und in der Spalte <b>Summe</b> addiert — diese Summe nennen die Online-Seiten „Heilung“.</p>",
    "<p class=dim style='margin:6px 0 0;font-size:12px'>Le Lien d'esprit ne soigne pas%s: il prend de la santé aux joueurs les plus hauts pour la donner aux plus bas. Les %s qu'il a pris sont déduits des soins de son poseur, comme sur Warcraft Logs, et ne comptent dans les dégâts subis de personne.</p>":
        "<p class=dim style='margin:6px 0 0;font-size:12px'>Die Geistverbindung heilt nicht%.0s: Sie nimmt den Spielern mit dem meisten Leben Gesundheit und gibt sie denen mit dem wenigsten. Die %s, die sie genommen hat, werden wie bei Warcraft Logs von der Heilung ihres Wirkers abgezogen und zählen bei niemandem als erlittener Schaden.</p>",
    "<h3>Ce qui a fait mal au groupe</h3><div class=card><table><tr><th>Capacité</th><th class=n>Dégâts</th><th class=n>Coups</th><th class=n>Joueurs touchés</th></tr>%s</table>%s<p class=dim style='margin:10px 0 0;font-size:12px'>Le fichier dit qui a été touché et combien. Il ne dit pas si le coup était évitable&nbsp;: cela demande de connaître le boss, ce que cet outil ne prétend pas savoir.</p></div>":
        "<h3>Was der Gruppe geschadet hat</h3><div class=card><table><tr><th>Fähigkeit</th><th class=n>Schaden</th><th class=n>Treffer</th><th class=n>Getroffene Spieler</th></tr>%s</table>%s<p class=dim style='margin:10px 0 0;font-size:12px'>Die Datei sagt, wer getroffen wurde und wie stark. Sie sagt nicht, ob der Treffer vermeidbar war: Dafür muss man den Boss kennen, und das behauptet dieses Werkzeug nicht.</p></div>",
    "<p class=dim style='margin:8px 0 0;font-size:12.5px'>Et %s de plus, %s de dégâts en tout.</p>":
        "<p class=dim style='margin:8px 0 0;font-size:12.5px'>Und weitere %s, insgesamt %s Schaden.</p>",
    ' <b>coup fatal</b>':
        ' <b>Todesstoß</b>',
    'mort instantanée':
        'sofortiger Tod',
    'cause non écrite dans le journal':
        'Ursache nicht im Protokoll',
    '<li class=dim>Rien avant la mort dans le journal.</li>':
        '<li class=dim>Nichts vor dem Tod im Protokoll.</li>',
    "<h3>Composition du groupe</h3><div class=card><table>%s</table>%s<p class=dim style='margin:10px 0 0;font-size:12px'>Le rôle vient de la spécialisation que le client écrit au début du combat. Une spécialisation que cet outil ne connaît pas est affichée par son numéro.</p></div>":
        "<h3>Zusammensetzung der Gruppe</h3><div class=card><table>%s</table>%s<p class=dim style='margin:10px 0 0;font-size:12px'>Die Rolle ergibt sich aus der Spezialisierung, die der Client zu Beginn des Kampfes schreibt. Eine Spezialisierung, die dieses Werkzeug nicht kennt, wird mit ihrer Nummer angezeigt.</p></div>",
    "<p style='margin:10px 0 0;font-size:12.5px'>Aussi présents dans le journal, sans prendre part au combat (ni dégâts, ni soins, ni coups reçus)%s: %s.</p>":
        "<p style='margin:10px 0 0;font-size:12.5px'>Ebenfalls im Protokoll, ohne am Kampf teilzunehmen (weder Schaden noch Heilung noch erlittene Treffer)%.0s: %s.</p>",
    '<footer>LogsWoW %s &middot; lecture locale de <code>%s</code><br>Disposition détectée dans ce fichier&nbsp;: bloc avancé de %d champs, champ de dégâts bruts %s, champ hideCaster %s. Lignes non comprises&nbsp;: %s. Événements inconnus&nbsp;: %s.<br>Licence AGPL-3.0 ou ultérieure&nbsp;; code source&nbsp;: github.com/prenom6548/LogsWoW. Aucune donnée ne quitte cette machine.</footer></div></body></html>':
        '<footer>LogsWoW %s &middot; lokales Lesen von <code>%s</code><br>In dieser Datei erkannter Aufbau: erweiterter Block mit %d Feldern, Feld für Rohschaden %s, Feld hideCaster %s. Nicht verstandene Zeilen: %s. Unbekannte Ereignisse: %s.<br>Lizenz AGPL-3.0 oder später; Quellcode: github.com/prenom6548/LogsWoW. Keine Daten verlassen diesen Rechner.</footer></div></body></html>',
    # report_casts
    "<p class=dim style='font-size:12px'>Séquence coupée après %s sorts.</p>":
        "<p class=dim style='font-size:12px'>Abfolge nach %s Zaubern abgeschnitten.</p>",
    '<details class=co><summary>Ordre des sorts, pull par pull <span class=dim>&middot; %s</span></summary><div class=cobody>%s%s<div class=pulls>%s%s</div></div></details>':
        '<details class=co><summary>Zauberreihenfolge, Pull für Pull <span class=dim>&middot; %s</span></summary><div class=cobody>%s%s<div class=pulls>%s%s</div></div></details>',
    'Lancés':
        'Gewirkt',
    'Probablement déclenchés automatiquement (masqués)':
        'Wahrscheinlich vom Spiel ausgelöst (ausgeblendet)',
    'Lancés par ses invocations':
        'Von seinen Beschwörungen gewirkt',
    "<p class=dim style='font-size:12px;margin:4px 0 0'>Le journal écrit de la même façon un sort appuyé et un sort que le jeu déclenche seul. Sont lus comme déclenchés, parmi les sorts lancés au moins %d fois dans ce combat sans jamais coûter de ressource%s: ceux qui, à %d%s%% au moins, partent en même temps qu'un sort payé, avec un écart médian de %d secondes au plus entre deux lancers%s; ceux dont l'écart médian est sous %s%ss, plus vite qu'aucun bouton%s; et la seconde copie d'un sort que le journal écrit deux fois, sous le même nom, au même instant. C'est une lecture du fichier%s: cliquez pour les afficher.</p>":
        "<p class=dim style='font-size:12px;margin:4px 0 0'>Das Protokoll schreibt einen gedrückten Zauber genauso wie einen, den das Spiel von selbst auslöst. Als ausgelöst gelten, unter den Zaubern, die in diesem Kampf mindestens %d-mal gewirkt wurden, ohne je eine Ressource zu kosten%.0s: jene, die zu mindestens %d%s%% zusammen mit einem bezahlten Zauber losgehen, mit einem mittleren Abstand von höchstens %d Sekunden zwischen zwei Wirkungen%.0s; jene, deren mittlerer Abstand unter %s%ss liegt, schneller als jede Taste%.0s; und die zweite Kopie eines Zaubers, den das Protokoll zweimal unter demselben Namen im selben Augenblick schreibt. Das ist eine Lesart der Datei%.0s: Klicken Sie, um sie anzuzeigen.</p>",
    "<div class=legend><p class=dim style='font-size:12px;margin:0'>Cliquez sur un sort pour le masquer ou l'afficher.</p>%s%s</div>":
        "<div class=legend><p class=dim style='font-size:12px;margin:0'>Klicken Sie auf einen Zauber, um ihn aus- oder einzublenden.</p>%s%s</div>",
    'Entre les pulls':
        'Zwischen den Pulls',
    'Pull %02d &mdash; %s':
        'Pull %02d &mdash; %s',
    "<p class=dim style='line-height:1.5;margin:0'>Aucun sort pendant ce pull.</p>":
        "<p class=dim style='line-height:1.5;margin:0'>Kein Zauber während dieses Pulls.</p>",
    ', réussite':
        ', Kill',
    ', échec':
        ', Wipe',
    'trash (%s)':
        'Trash (%s)',
    # report_layouts
    'Résumé':
        'Übersicht',
    'Dégâts et soins':
        'Schaden und Heilung',
    'Physique ou magique':
        'Physisch oder magisch',
    'Joueurs':
        'Spieler',
    'Ennemis':
        'Gegner',
    "<input type=radio name=f id=f0 class=fsel checked aria-label='Vue d&#39;ensemble'>":
        "<input type=radio name=f id=f0 class=fsel checked aria-label='Gesamtübersicht'>",
    "<label for=f0 class='nv n0'>Vue d'ensemble</label>":
        "<label for=f0 class='nv n0'>Gesamtübersicht</label>",
    "%s<div class=layout><nav class=side aria-label='Combats'>%s</nav><main>%s</main></div>%s":
        "%s<div class=layout><nav class=side aria-label='Kämpfe'>%s</nav><main>%s</main></div>%s",
    "<a href='index.html'>&larr; Tous les combats</a>":
        "<a href='index.html'>&larr; Alle Kämpfe</a>",
    # report_panels
    ' et %s':
        ' und %s',
    '<p class=dim>Rien.</p>':
        '<p class=dim>Nichts.</p>',
    '<details class=more><summary>%s de plus &middot; %s (%s)</summary>%s</details>':
        '<details class=more><summary>weitere %s &middot; %s (%s)</summary>%s</details>',
    'Sort':
        'Zauber',
    'Total':
        'Gesamt',
    'Part':
        'Anteil',
    'Surguérison':
        'Überheilung',
    'Casts':
        'Wirkungen',
    'Coups':
        'Treffer',
    'Moyenne':
        'Mittel',
    'Crit':
        'Krit',
    'Par sec.':
        'Pro Sek.',
    'Principale cible':
        'Hauptziel',
    'Principale source':
        'Hauptquelle',
    '<table><tr><th>Effet</th><th>%s</th><th class=n>Durée</th></tr>%s</table>':
        '<table><tr><th>Effekt</th><th>%s</th><th class=n>Dauer</th></tr>%s</table>',
    '<h3>Détail par joueur</h3>%s':
        '<h3>Details pro Spieler</h3>%s',
    ' (dont %d de ses invocations)':
        ' (davon %d von seinen Beschwörungen)',
    "<details><summary>%s <span class=dim>&middot; %s &middot; %s dégâts &middot; %s soins &middot; %s</span></summary><div class=body><div class='grid tiles'>%s</div>%s%s</div></details>":
        "<details><summary>%s <span class=dim>&middot; %s &middot; %s Schaden &middot; %s Heilung &middot; %s</span></summary><div class=body><div class='grid tiles'>%s</div>%s%s</div></details>",
    'rôle inconnu':
        'unbekannte Rolle',
    'Part sur les boss':
        'Anteil auf Bosse',
    'Subis par ses invocations':
        'Von seinen Beschwörungen erlitten',
    'Dégâts subis':
        'Erlittener Schaden',
    'Absorbé sur lui':
        'Auf ihm absorbiert',
    'Absorbé par ses boucliers':
        'Von seinen Schilden absorbiert',
    'Soutien crédité par le jeu':
        'Vom Spiel gutgeschriebene Unterstützung',
    'Sorts par minute':
        'Zauber pro Minute',
    'Temps sans action':
        'Zeit ohne Aktion',
    'Interruptions':
        'Unterbrechungen',
    'Dissipations':
        'Bannungen',
    'Vie la plus basse':
        'Niedrigstes Leben',
    'Ce que ses boucliers ont absorbé':
        'Was seine Schilde absorbiert haben',
    'Ses dégâts':
        'Sein Schaden',
    'Ses soins':
        'Seine Heilung',
    'Qui il a soigné':
        'Wen er geheilt hat',
    "Ce qu'il a pris":
        'Was er abbekommen hat',
    'Soutien que le jeu lui crédite':
        'Unterstützung, die das Spiel ihm gutschreibt',
    'Plus longues pauses':
        'Längste Pausen',
    'Gains reçus':
        'Erhaltene Stärkungen',
    'De qui':
        'Von wem',
    'Affaiblissements subis':
        'Erlittene Schwächungen',
    "Ce qu'il a appliqué":
        'Was er angewendet hat',
    'Sur qui':
        'Auf wen',
    "<p class=dim style='font-size:12px;margin:0'>Un effet déjà actif quand le combat commence n'a pas de ligne d'application dans le journal%s: sa durée est comptée depuis le premier événement du combat, ce qui est la seule borne que le fichier donne.</p>":
        "<p class=dim style='font-size:12px;margin:0'>Ein Effekt, der zu Kampfbeginn schon aktiv ist, hat keine Anwendungszeile im Protokoll%.0s: Seine Dauer wird ab dem ersten Ereignis des Kampfes gezählt, der einzigen Grenze, die die Datei angibt.</p>",
    '<li><span class=dim>%s</span> sans lancer de sort, à %s</li>':
        '<li><span class=dim>%s</span> ohne Zauber, bei %s</li>',
    '<li class=dim>Aucune pause notable.</li>':
        '<li class=dim>Keine nennenswerte Pause.</li>',
    "<p class=dim style='font-size:12.5px;margin:8px 0 0'><b>Sorts ennemis coupés</b>%s %s</p>":
        "<p class=dim style='font-size:12.5px;margin:8px 0 0'><b>Unterbrochene gegnerische Zauber</b>%.0s: %s</p>",
    "<p class=dim style='font-size:12.5px;margin:4px 0 0'><b>Effets dissipés</b>%s %s</p>":
        "<p class=dim style='font-size:12.5px;margin:4px 0 0'><b>Gebannte Effekte</b>%.0s: %s</p>",
    "%s<p class=dim style='font-size:12px;margin:4px 0 0'>Le journal crédite cet évocateur de %s de dégâts et %s de soins portés par d'autres joueurs%s: la part que ses renforts (Puissance d'ébène, Prescience...) ont ajoutée à leurs coups, et ses Bombardements, que le journal écrit au nom de l'allié qui les a déclenchés. Ces montants sont <b>déjà comptés</b> chez ceux qui ont porté les coups et ne sont pas ajoutés aux siens%s; Warcraft Logs, lui, les retire aux autres pour les lui donner, d'où l'écart entre les deux.</p>":
        "%s<p class=dim style='font-size:12px;margin:4px 0 0'>Das Protokoll schreibt diesem Rufer %s Schaden und %s Heilung gut, die von anderen Spielern verursacht wurden%.0s: der Anteil, den seine Stärkungen (Ebenholzmacht, Voraussicht...) zu deren Treffern beigetragen haben, und seine Bombardements, die das Protokoll unter dem Namen des Verbündeten schreibt, der sie ausgelöst hat. Diese Beträge sind <b>bereits gezählt</b> bei denen, die die Treffer verursacht haben, und werden seinen eigenen nicht hinzugefügt%.0s; Warcraft Logs nimmt sie dagegen den anderen weg und gibt sie ihm, daher der Unterschied zwischen beiden.</p>",
    '<table><tr><th>Cible</th><th class=n>Total</th><th class=n>Part</th></tr>%s</table>':
        '<table><tr><th>Ziel</th><th class=n>Gesamt</th><th class=n>Anteil</th></tr>%s</table>',
    "Ce qu'il inflige":
        'Was er verursacht',
    "Ce qu'il a subi":
        'Was er erlitten hat',
    'Ses sorts':
        'Seine Zauber',
    '<table><tr><th>Sort</th><th class=n>Lancés</th></tr>%s</table>':
        '<table><tr><th>Zauber</th><th class=n>Gewirkt</th></tr>%s</table>',
    'Unités':
        'Einheiten',
    'Sorts lancés':
        'Gewirkte Zauber',
    'Tués':
        'Getötet',
    "<details><summary>%s <span class=dim>&middot; %s &middot; %s infligé &middot; %s subi</span></summary><div class=body><div class='grid tiles'>%s</div>%s</div></details>":
        "<details><summary>%s <span class=dim>&middot; %s &middot; %s verursacht &middot; %s erlitten</span></summary><div class=body><div class='grid tiles'>%s</div>%s</div></details>",
    '<h3>Détail par ennemi</h3>%s':
        '<h3>Details pro Gegner</h3>%s',
    'Aboutis':
        'Abgeschlossen',
    'Coupés par une interruption':
        'Durch Unterbrechung abgebrochen',
    "Lanceur tué pendant l'incantation":
        'Wirker während des Zauberns getötet',
    'Non aboutis, cause non dite par le journal':
        'Nicht abgeschlossen, Ursache nicht im Protokoll',
    "<p class=dim style='margin:10px 0 0;font-size:12px'>Les plus coupés%s: %s.</p>":
        "<p class=dim style='margin:10px 0 0;font-size:12px'>Am häufigsten unterbrochen%.0s: %s.</p>",
    "<h3>Ce que le groupe a empêché</h3><div class=card><p class=dim style='margin:0 0 10px;font-size:12.5px'>%s sorts commencés par l'ennemi%s:</p><table><tr><th>Issue</th><th class=n>Nombre</th><th class=n>Part</th></tr>%s</table>%s<p class=dim style='margin:10px 0 0;font-size:12px'>Un sort instantané n'apparaît pas ici%s: seuls ceux qui ont un temps d'incantation laissent une trace. La dernière ligne regroupe tout le reste, contrôle compris%s: le journal ne dit nulle part qu'un sort est un étourdissement, donc rien ici ne prétend le savoir.</p></div>":
        "<h3>Was die Gruppe verhindert hat</h3><div class=card><p class=dim style='margin:0 0 10px;font-size:12.5px'>%s vom Gegner begonnene Zauber%.0s:</p><table><tr><th>Ergebnis</th><th class=n>Anzahl</th><th class=n>Anteil</th></tr>%s</table>%s<p class=dim style='margin:10px 0 0;font-size:12px'>Ein Spontanzauber erscheint hier nicht%.0s: Nur Zauber mit Zauberzeit hinterlassen eine Spur. Die letzte Zeile fasst alles Übrige zusammen, Kontrolleffekte eingeschlossen%.0s: Das Protokoll sagt nirgends, dass ein Zauber eine Betäubung ist, also behauptet hier nichts, es zu wissen.</p></div>",
    # report_schools
    'autres %s':
        'andere %s',
    'Physique':
        'Physisch',
    'Magique':
        'Magisch',
    'Mixte':
        'Gemischt',
    'Phys.':
        'Phys.',
    'Mag.':
        'Mag.',
    'Subis':
        'Erlitten',
    'Infligés':
        'Verursacht',
    "<p class=dim style='font-size:12.5px;margin:6px 0 0'><b>%s par école</b>%s: %s</p>":
        "<p class=dim style='font-size:12.5px;margin:6px 0 0'><b>%s nach Schule</b>%.0s: %s</p>",
    "<h3>Physique ou magique</h3><div class='card schools'><p style='margin:0 0 8px;font-size:12.5px'>%s</p><table><tr><th></th><th>Répartition</th>%s</tr>%s</table>%s%s<p class=dim style='margin:10px 0 0;font-size:12px'>L'école de chaque coup est celle que le journal écrit sur la ligne. « Mixte »%s: physique et magique à la fois (Ombre-frappe, Chaos...). Comme dans le reste du rapport, un coup qu'un bouclier ennemi a mangé compte dans les dégâts infligés, et la part qu'un bouclier du groupe a mangée ne compte pas dans les dégâts subis.</p></div>":
        "<h3>Physisch oder magisch</h3><div class='card schools'><p style='margin:0 0 8px;font-size:12.5px'>%s</p><table><tr><th></th><th>Verteilung</th>%s</tr>%s</table>%s%s<p class=dim style='margin:10px 0 0;font-size:12px'>Die Schule jedes Treffers ist die, die das Protokoll in die Zeile schreibt. „Gemischt“%.0s: physisch und magisch zugleich (Schattenschlag, Chaos...). Wie im Rest des Berichts zählt ein Treffer, den ein gegnerischer Schild geschluckt hat, zum verursachten Schaden, und der Teil, den ein Schild der Gruppe geschluckt hat, zählt nicht zum erlittenen Schaden.</p></div>",
    "<h3 style='margin-top:18px'>Pull par pull</h3><table><tr><th class=n>#</th><th>Ce qui a été engagé</th><th>Subis</th>%s<th>Infligés</th>%s</tr>%s</table>":
        "<h3 style='margin-top:18px'>Pull für Pull</h3><table><tr><th class=n>#</th><th>Was angegriffen wurde</th><th>Erlitten</th>%s<th>Verursacht</th>%s</tr>%s</table>",
    # report_timeline
    "<h3>Dégâts subis par le groupe, seconde par seconde</h3><div class=card><svg viewBox='0 0 %d %d' role=img aria-label='Dégâts subis au fil du combat'>%s</svg><p class=dim style='margin:6px 0 0;font-size:12px'>Barres et échelle de gauche%s: dégâts subis par intervalle de %s. Traits rouges%s: morts.%s</p></div>":
        "<h3>Von der Gruppe erlittener Schaden, Sekunde für Sekunde</h3><div class=card><svg viewBox='0 0 %d %d' role=img aria-label='Erlittener Schaden im Verlauf des Kampfes'>%s</svg><p class=dim style='margin:6px 0 0;font-size:12px'>Balken und linke Skala%.0s: erlittener Schaden pro Intervall von %s. Rote Striche%.0s: Tode.%s</p></div>",
    " Courbe et échelle de droite%s: <b>vie cumulée des ennemis engagés</b>, somme de leurs points de vie courants sur la somme de leurs maximums. Elle remonte à chaque nouveau pack et retombe quand il meurt%s; un ennemi que le groupe n'a plus touché depuis %d%ss en sort.":
        ' Kurve und rechte Skala%.0s: <b>gemeinsames Leben der angegriffenen Gegner</b>, die Summe ihrer aktuellen Lebenspunkte geteilt durch die Summe ihrer Maxima. Sie steigt mit jedem neuen Pack und fällt, wenn es stirbt%.0s; ein Gegner, den die Gruppe seit %d%ss nicht mehr getroffen hat, fällt heraus.',
    ' Courbe et échelle de droite%s: vie de <b>%s</b>, la cible la plus frappée parmi celles dont le journal donne les points de vie.':
        ' Kurve und rechte Skala%.0s: Leben von <b>%s</b>, dem am häufigsten getroffenen Ziel unter denen, deren Lebenspunkte das Protokoll angibt.',
    # schools
    'Sacré':
        'Heilig',
    'Feu':
        'Feuer',
    'Nature':
        'Natur',
    'Givre':
        'Frost',
    'Ombre':
        'Schatten',
    'Arcane':
        'Arkan',
    'école inconnue':
        'unbekannte Schule',
    # models
    'et %d autre(s)':
        'und %d weitere',
    'autres':
        'andere',
    # segment
    'Normal':
        'Normal',
    'Héroïque':
        'Heroisch',
    '10 joueurs':
        '10 Spieler',
    '25 joueurs':
        '25 Spieler',
    '10 héroïque':
        '10 Spieler (heroisch)',
    '25 héroïque':
        '25 Spieler (heroisch)',
    'Raid Recherche':
        'Schlachtzugsbrowser',
    'Mythique+':
        'Mythisch+',
    '40 joueurs':
        '40 Spieler',
    'Héroïque scénario':
        'Heroisches Szenario',
    'Normal scénario':
        'Normales Szenario',
    'Mythique':
        'Mythisch',
    'Marche du temps':
        'Zeitwanderung',
    'Torghast':
        'Torghast',
    'difficulté %d':
        'Schwierigkeit %d',
    'sans combat':
        'kein Kampf',
    'abandonnée':
        'abgebrochen',
    'terminée':
        'abgeschlossen',
    'interrompu':
        'unterbrochen',
    'dans les temps':
        'in der Zeit',
    'hors des temps':
        'über der Zeit',
    'réussite':
        'Kill',
    'échec':
        'Wipe',
    'Pull %d':
        'Pull %d',
    'Donjon':
        'Dungeon',
    'Session complète':
        'Ganze Sitzung',
    # specs
    'spe %d':
        'Spez. %d',
    'Touché':
        'Getroffen',
    'Absorbé entièrement':
        'Vollständig absorbiert',
    'Paré':
        'Pariert',
    'Esquivé':
        'Ausgewichen',
    'Raté':
        'Verfehlt',
    'Bloqué entièrement':
        'Vollständig geblockt',
    'Dévié':
        'Abgelenkt',
    'Insensible':
        'Immun',
    'Résisté':
        'Widerstanden',
    'Renvoyé':
        'Reflektiert',
    "Hors d'atteinte":
        'Außer Reichweite',
    'Les coups de mêlée reçus':
        'Erhaltene Nahkampfschläge',
    'dont critiques':
        'davon kritisch',
    'dont bloqués en partie':
        'davon teilweise geblockt',
    '<table><tr><th>Issue</th><th class=n>Coups</th><th class=n>Part</th></tr>%s</table>':
        '<table><tr><th>Ausgang</th><th class=n>Schläge</th><th class=n>Anteil</th></tr>%s</table>',
    '<p><b>%s</b> des coups évités (parés, esquivés ou ratés).</p>':
        '<p><b>%s</b> der Schläge vermieden (pariert, ausgewichen oder verfehlt).</p>',
    '<p><b>%s</b> des coups qui ont touché venaient de derrière (%s sur %s dont la position est connue).</p>':
        '<p><b>%s</b> der Schläge, die trafen, kamen von hinten (%s von %s mit bekannter Position).</p>',
    ' Contrôle sur ce combat%s: le jeu ne laisse ni parer ni esquiver un coup venu de derrière, et %s des %s parades et esquives placées tombent bien devant.':
        ' Kontrolle in diesem Kampf%.0s: Das Spiel erlaubt kein Parieren oder Ausweichen bei einem Schlag von hinten, und %s der %s verorteten Paraden und Ausweichmanöver liegen tatsächlich vorn.',
    "<p class=dim style='font-size:12px;margin:0'>Estimation fiable, mais pas une donnée écrite, et limitée à la mêlée%s: le journal ne dit pas d'où vient un coup. LogsWoW le déduit de la position de l'attaquant et de l'orientation du joueur, que le journal donne ligne par ligne.%s</p>":
        "<p class=dim style='font-size:12px;margin:0'>Eine verlässliche Schätzung, aber keine Angabe des Protokolls, und auf den Nahkampf beschränkt%.0s: Das Protokoll sagt nicht, woher ein Schlag kam. LogsWoW leitet es aus der Position des Angreifers und der Blickrichtung des Spielers ab, die das Protokoll Zeile für Zeile angibt.%s</p>",
    # equipment, comparison of keys, preview (0.15.0)
    'Tête':
        'Kopf',
    'Cou':
        'Hals',
    'Épaules':
        'Schultern',
    'Chemise':
        'Hemd',
    'Torse':
        'Brust',
    'Jambes':
        'Beine',
    'Pieds':
        'Füße',
    'Poignets':
        'Handgelenke',
    'Mains':
        'Hände',
    'Anneau 1':
        'Ring 1',
    'Anneau 2':
        'Ring 2',
    'Bijou 1':
        'Schmuckstück 1',
    'Bijou 2':
        'Schmuckstück 2',
    'Dos':
        'Rücken',
    'Main droite':
        'Waffenhand',
    'Main gauche':
        'Schildhand',
    'Tabard':
        'Wappenrock',
    'Aperçu':
        'Übersicht',
    'Clés':
        'Schlüssel',
    'Équipement':
        'Ausrüstung',
    'Cochez un ou plusieurs combats pour voir ce que le rapport en dirait.':
        'Wählen Sie einen oder mehrere Kämpfe, um zu sehen, was der Bericht dazu sagen würde.',
    'Aucune clé terminée à comparer : il faut au moins une clé, et deux du même niveau pour les mettre côte à côte.':
        'Kein beendeter Schlüssel zum Vergleichen: Es braucht mindestens einen Schlüssel, und zwei der gleichen Stufe, um sie nebeneinanderzustellen.',
    "Écart : la dernière clé par rapport à la première. Soins/s compte les boucliers ; Subis/s compte ce que les boucliers ont absorbé, et n'est donné qu'aux tanks.":
        'Abweichung: der letzte Schlüssel im Vergleich zum ersten. Heilung/s zählt Schilde mit; Erlitten/s zählt, was Schilde absorbiert haben, und wird nur für Tanks angegeben.',
    '%s — %s (%s)':
        '%s — %s (%s)',
    'Dégâts %s (%s/s) · Soins %s (%s/s, boucliers compris) · Subis %s · %s':
        'Schaden %s (%s/s) · Heilung %s (%s/s, Schilde eingeschlossen) · Erlitten %s · %s',
    'Morts :':
        'Tode:',
    '%s dégâts/s':
        '%s Schaden/s',
    '%s soins/s':
        '%s Heilung/s',
    'Dégâts/s':
        'Schaden/s',
    'Soins/s':
        'Heilung/s',
    'Subis/s':
        'Erlitten/s',
    "Niveau d'objet moyen du groupe : %s":
        'Durchschnittliche Gegenstandsstufe der Gruppe: %s',
    'Boss : %s':
        'Boss: %s',
    '%s subis/s':
        '%s erlitten/s',
    'ilvl %s':
        'ilvl %s',
    '%s : %s':
        '%s: %s',
    '  %s à %s : %s':
        '  %s bei %s: %s',
    'Écart':
        'Abweichung',
    'Clé %d':
        'Schlüssel %d',
    'Groupe : ':
        'Gruppe: ',
    'sans résultat':
        'ohne Ergebnis',
    "<p style='margin:10px 0 0;font-size:12.5px'>Niveau d'objet moyen du groupe%s: <b>%s</b> (de %s à %s).</p>":
        "<p style='margin:10px 0 0;font-size:12.5px'>Durchschnittliche Gegenstandsstufe der Gruppe%s: <b>%s</b> (von %s bis %s).</p>",
    'Comparaison des clés':
        'Vergleich der Schlüssel',
    "<p class=dim style='font-size:12.5px'>Écart%s: la dernière clé par rapport à la première. <b>Soins/s</b> compte les boucliers (le journal ne les range pas parmi les soins, les sites en ligne si). <b>Subis/s</b> compte ce que les boucliers ont absorbé : c'est ce qui arrive au tank avant ses protections, et il n'est donné qu'aux tanks. Seules des clés terminées du même niveau sont comparées.</p>":
        "<p class=dim style='font-size:12.5px'>Abweichung%s: der letzte Schlüssel im Vergleich zum ersten. <b>Heilung/s</b> zählt Schilde mit (das Protokoll ordnet sie nicht unter Heilung ein, die Online-Seiten schon). <b>Erlitten/s</b> zählt, was Schilde absorbiert haben: Es ist das, was den Tank vor seinen Schutzeffekten erreicht, und es wird nur für Tanks angegeben. Verglichen werden nur beendete Schlüssel der gleichen Stufe.</p>",
    "Le journal donne le numéro et le niveau de chaque objet, jamais son nom ni son icône : ils viennent de la base d'objets du jeu, que ce rapport n'a pas (il ne se connecte à rien). Le lien ouvre Wowhead si vous cliquez dessus. Le niveau moyen suit la formule du jeu : seize emplacements, chemise et tabard exclus, une arme à deux mains comptée deux fois, un emplacement vide pour zéro.":
        'Das Protokoll nennt Nummer und Stufe jedes Gegenstands, nie seinen Namen oder sein Symbol: Diese stammen aus der Gegenstandsdatenbank des Spiels, die dieser Bericht nicht hat (er verbindet sich mit nichts). Der Link öffnet Wowhead, wenn Sie darauf klicken. Die durchschnittliche Stufe folgt der Formel des Spiels: sechzehn Plätze, Hemd und Wappenrock ausgenommen, eine Zweihandwaffe doppelt gezählt, ein leerer Platz als null.',
    'Joueur':
        'Spieler',
    'objet %d':
        'Gegenstand %d',
    'Emplacement':
        'Platz',
    'Objet':
        'Gegenstand',
    'Niveau':
        'Stufe',
    "<p class=dim style='margin:6px 0 0'>Emplacement vide%s: %s.</p>":
        "<p class=dim style='margin:6px 0 0'>Leerer Platz%s: %s.</p>",
    ' (non compté)':
        ' (nicht gezählt)',
    # history (foundation)
    "%s n'est pas un dossier d'historique LogsWoW : refus d'y écrire.":
        '%s ist kein LogsWoW-Verlaufsordner: Schreiben dort verweigert.',
    'Réglage inconnu : %s':
        'Unbekannte Einstellung: %s',
    'Nom de dossier invalide : %s':
        'Ungültiger Ordnername: %s',
    'Nom de dossier invalide : donnez un nom avec au moins une lettre ou un chiffre.':
        'Ungültiger Ordnername: Geben Sie einen Namen mit mindestens einem Buchstaben oder einer Ziffer an.',
    'Un dossier de ce nom existe déjà : %s':
        'Ein Ordner mit diesem Namen existiert bereits: %s',
    "Dossier d'historique introuvable : %s":
        'Verlaufsordner nicht gefunden: %s',
    'Le dossier %s contient un fichier qui ne vient pas de LogsWoW (%s) : refus de le supprimer.':
        'Der Ordner %s enthält eine Datei, die nicht von LogsWoW stammt (%s): Löschen verweigert.',
    "Fichier de l'historique illisible (%s) : %s":
        'Verlaufsdatei nicht lesbar (%s): %s',
    "Ce fichier n'est pas une soirée de l'historique LogsWoW : %s":
        'Diese Datei ist kein Abend des LogsWoW-Verlaufs: %s',
    'Une soirée de même nom existe déjà dans ce dossier : %s':
        'Ein Abend mit demselben Namen existiert bereits in diesem Ordner: %s',
    # history window (0.15.2)
    'Historique…':
        'Verlauf…',
    "La version du jeu a changé : ouvrez l'Historique pour créer un nouveau dossier.":
        'Die Spielversion hat sich geändert: Öffnen Sie den Verlauf, um einen neuen Ordner zu erstellen.',
    'Historique indisponible : %s':
        'Verlauf nicht verfügbar: %s',
    "Soirée déjà dans l'historique : mise à jour (dossier « %s »).":
        'Abend bereits im Verlauf: aktualisiert (Ordner „%s“).',
    "Soirée ajoutée à l'historique (dossier « %s »).":
        'Abend zum Verlauf hinzugefügt (Ordner „%s“).',
    "L'historique garde, soirée après soirée, les chiffres de vos personnages pour voir comment vous évoluez : un petit fichier par soirée (environ 30 Ko), rangé dans le dossier de votre choix, sur cet ordinateur uniquement. Rien n'est enregistré sans votre accord, et seuls les personnages que vous suivez y laissent leur nom ; les autres joueurs n'apparaissent que dans les totaux du groupe. Commencez par créer un dossier (par exemple une saison, ou « avec mes amis »).":
        'Der Verlauf bewahrt Abend für Abend die Zahlen Ihrer Charaktere auf, damit Sie sehen, wie Sie sich entwickeln: eine kleine Datei pro Abend (etwa 30 KB), im Ordner Ihrer Wahl, nur auf diesem Computer. Ohne Ihre Zustimmung wird nichts gespeichert, und nur die Charaktere, denen Sie folgen, hinterlassen darin ihren Namen; andere Spieler erscheinen nur in den Gruppensummen. Beginnen Sie mit einem Ordner (zum Beispiel eine Saison oder „mit meinen Freunden“).',
    "Rien n'est enregistré sans votre accord. Seuls les personnages suivis y laissent leur nom ; les autres joueurs n'apparaissent que dans les totaux du groupe.":
        'Ohne Ihre Zustimmung wird nichts gespeichert. Nur gefolgte Charaktere hinterlassen darin ihren Namen; andere Spieler erscheinen nur in den Gruppensummen.',
    'Tank':
        'Tank',
    'Soigneur':
        'Heiler',
    "La version du jeu est passée de %s à %s : un nouveau patch. Les chiffres des soirées suivantes ne sont pas forcément comparables à ceux d'avant. Commencer un nouveau dossier ?":
        'Die Spielversion ist von %s auf %s gewechselt: ein neuer Patch. Die Zahlen der folgenden Abende sind nicht unbedingt mit den früheren vergleichbar. Einen neuen Ordner beginnen?',
    "La version du jeu est passée de %s à %s : une nouvelle extension. Les chiffres des soirées suivantes ne sont pas comparables à ceux d'avant. Commencer un nouveau dossier ?":
        'Die Spielversion ist von %s auf %s gewechselt: eine neue Erweiterung. Die Zahlen der folgenden Abende sind nicht mit den früheren vergleichbar. Einen neuen Ordner beginnen?',
    "Choisissez d'abord un dossier.":
        'Wählen Sie zuerst einen Ordner.',
    'Aucun combat à enregistrer dans ce journal.':
        'Kein Kampf zum Speichern in diesem Protokoll.',
    'Historique':
        'Verlauf',
    'Créez un dossier pour commencer.':
        'Erstellen Sie zuerst einen Ordner.',
    'Aucun journal lu : lisez un journal dans la fenêtre principale pour pouvoir ajouter une soirée.':
        'Kein Protokoll gelesen: Lesen Sie im Hauptfenster ein Protokoll, um einen Abend hinzufügen zu können.',
    'Nouveau dossier':
        'Neuer Ordner',
    'Nom du dossier (par exemple « Saison 1 », « Avec mes amis ») :':
        'Ordnername (zum Beispiel „Saison 1“, „Mit meinen Freunden“):',
    'Renommer le dossier':
        'Ordner umbenennen',
    'Nouveau nom du dossier :':
        'Neuer Ordnername:',
    'Déplacer la soirée':
        'Abend verschieben',
    'Dossier de destination :':
        'Zielordner:',
    'Nouveau dossier…':
        'Neuer Ordner…',
    'Renommer…':
        'Umbenennen…',
    'Supprimer ce dossier…':
        'Diesen Ordner löschen…',
    ' Personnages de ce journal ':
        ' Charaktere in diesem Protokoll ',
    'Suivre la sélection':
        'Auswahl folgen',
    'Ne plus suivre':
        'Nicht mehr folgen',
    "Ajouter cette soirée à l'historique":
        'Diesen Abend zum Verlauf hinzufügen',
    'Enregistrer automatiquement chaque journal lu (seulement si un personnage suivi y a joué)':
        'Jedes gelesene Protokoll automatisch speichern (nur wenn ein gefolgter Charakter mitgespielt hat)',
    ' Soirées de ce dossier ':
        ' Abende in diesem Ordner ',
    'Supprimer la soirée':
        'Abend löschen',
    'Déplacer vers un autre dossier…':
        'In einen anderen Ordner verschieben…',
    'Fermer':
        'Schließen',
    'Dossier créé : %s':
        'Ordner erstellt: %s',
    'Supprimer le dossier':
        'Ordner löschen',
    'Dossier supprimé : %s (%s).':
        'Ordner gelöscht: %s (%s).',
    'Suivi':
        'Gefolgt',
    'Spécialisation':
        'Spezialisierung',
    'Rôle':
        'Rolle',
    'Combats':
        'Kämpfe',
    'Journal':
        'Protokoll',
    'Jeu':
        'Spiel',
    'Aucun personnage suivi.':
        'Kein Charakter gefolgt.',
    'Supprimer le dossier « %s » et ses %s ? Cela ne touche pas à vos journaux de combat.':
        'Den Ordner „%s“ und seine %s löschen? Ihre Kampfprotokolle bleiben unberührt.',
    "Ajouter à l'historique":
        'Zum Verlauf hinzufügen',
    "Aucun personnage suivi dans ce journal : la soirée ne gardera que les totaux du groupe. L'enregistrer quand même ?":
        'Kein gefolgter Charakter in diesem Protokoll: Der Abend behält nur die Gruppensummen. Trotzdem speichern?',
    "Supprimer %s de l'historique ? Vos journaux de combat ne sont pas touchés.":
        '%s aus dem Verlauf löschen? Ihre Kampfprotokolle bleiben unberührt.',
    'Créer un nouveau dossier…':
        'Neuen Ordner erstellen…',
    'Ignorer':
        'Ignorieren',
    'Dossier :':
        'Ordner:',
    'Personnages suivis au total : %d':
        'Gefolgte Charaktere insgesamt: %d',
    # history: evolution of a character
    'Clés et boss':
        'Schlüssel und Bosse',
    'Clés seulement':
        'Nur Schlüssel',
    'Boss seulement':
        'Nur Bosse',
    'Certaines sorties ont été comptées avec une ancienne version des règles de calcul : leurs chiffres ne sont pas forcément comparables.':
        'Einige Durchgänge wurden mit einer älteren Version der Zählregeln erfasst: Ihre Zahlen sind nicht unbedingt vergleichbar.',
    '† Hors tendance : clé abandonnée ou interrompue, boss non tué.':
        '† Nicht im Trend: abgebrochener oder unterbrochener Schlüssel, nicht besiegter Boss.',
    ' Par contenu ':
        ' Nach Inhalt ',
    ' Toutes les sorties ':
        ' Alle Durchgänge ',
    "Écart : la dernière sortie par rapport à la première, dans un même contenu et un même niveau (ou une même difficulté). Il dépend aussi du niveau d'objet, du groupe et des affixes, affichés à côté : ce n'est pas une note. Groupe : tanks / soigneurs / dps.":
        'Abweichung: der letzte Durchgang im Vergleich zum ersten, im gleichen Inhalt und auf der gleichen Stufe (oder Schwierigkeit). Sie hängt auch von Gegenstandsstufe, Gruppe und Affixen ab, die daneben angezeigt werden: Es ist keine Note. Gruppe: Tanks / Heiler / DPS.',
    'Spécialisations différentes dans « %s » : %s.':
        'Verschiedene Spezialisierungen in „%s“: %s.',
    'Contenu':
        'Inhalt',
    'Sorties':
        'Durchgänge',
    'Première':
        'Erster',
    'Dernière':
        'Letzter',
    ' Tendance ':
        ' Trend ',
    'Groupe':
        'Gruppe',
    "Aucun personnage suivi dans ce dossier : suivez-en un dans l'onglet « Soirées », puis ajoutez des soirées.":
        'Kein Charakter in diesem Ordner gefolgt: Folgen Sie im Reiter „Abende“ einem und fügen Sie dann Abende hinzu.',
    'Aucune sortie de ce personnage dans ce dossier.':
        'Kein Durchgang dieses Charakters in diesem Ordner.',
    'Personnage :':
        'Charakter:',
    'Mesure :':
        'Messwert:',
    'Afficher :':
        'Anzeigen:',
    'Soirées':
        'Abende',
    'Évolution':
        'Entwicklung',
    # history: one specialization against another
    ' Contenus comparables ':
        ' Vergleichbare Inhalte ',
    ' Médiane par spécialisation ':
        ' Median pro Spezialisierung ',
    ' Spécialisations du contenu choisi ':
        ' Spezialisierungen des gewählten Inhalts ',
    "Aucun contenu n'a été joué avec au moins deux spécialisations de ce rôle dans ce dossier.":
        'In diesem Ordner wurde kein Inhalt mit mindestens zwei Spezialisierungen dieser Rolle gespielt.',
    'Contenus joués avec une seule spécialisation, non comparés : %d.':
        'Mit nur einer Spezialisierung gespielte Inhalte, nicht verglichen: %d.',
    'Min – max':
        'Min – Max',
    'Médiane':
        'Median',
    "Médiane des sorties comptées (clés terminées, boss tués) d'un même contenu et d'un même niveau, pour un rôle à la fois. L'écart est celui de chaque spécialisation par rapport à la première ligne, la plus jouée : ce n'est pas un classement. Il dépend aussi du niveau d'objet, des joueurs et du groupe ; avec plusieurs personnages, il mêle leurs joueurs.":
        'Median der gezählten Durchgänge (beendete Schlüssel, besiegte Bosse) desselben Inhalts und derselben Stufe, jeweils für eine Rolle. Die Abweichung ist die jeder Spezialisierung gegenüber der ersten Zeile, der meistgespielten: Es ist keine Rangliste. Sie hängt auch von Gegenstandsstufe, Spielern und Gruppe ab; bei mehreren Charakteren mischt sie deren Spieler.',
    'Persos':
        'Chars',
    "Sorties dont la spécialisation n'est pas écrite dans le journal ou que LogsWoW ne connaît pas, non comparées : %d.":
        'Durchgänge, deren Spezialisierung im Protokoll nicht steht oder LogsWoW unbekannt ist, nicht verglichen: %d.',
    'Spécialisations':
        'Spezialisierungen',
    'Spés':
        'Spez.',
    'Tous les personnages suivis':
        'Alle gefolgten Charaktere',
    'Écart / 1re':
        'Abw. / 1.',
    '‡ Moins de %d sorties : une médiane sur si peu de sorties dit peu de chose.':
        '‡ Weniger als %d Durchgänge: Ein Median über so wenige Durchgänge sagt wenig aus.',
    '… et %d autres dans le tableau':
        '… und %d weitere in der Tabelle',
    'Rôle :':
        'Rolle:',
    # history: the best key and the best kill
    ' Meilleur kill par spécialisation ':
        ' Bester Kill pro Spezialisierung ',
    ' Meilleure clé par spécialisation ':
        ' Bester Schlüssel pro Spezialisierung ',
    "Aucune clé terminée ni aucun kill de raid dans ce dossier pour l'instant.":
        'Noch kein beendeter Schlüssel und kein Raid-Kill in diesem Ordner.',
    'Boss':
        'Boss',
    'Chiffre':
        'Zahl',
    'Difficulté':
        'Schwierigkeit',
    'Kills':
        'Kills',
    "Meilleure clé : la plus haute clé terminée dans les temps ; à niveau égal, le meilleur score, puis le temps le plus court. Une clé terminée hors des temps ne passe devant que si la spécialisation n'en a aucune dans les temps. Meilleur kill : le plus rapide d'un même boss de raid à la même difficulté. Ce sont les records de chaque spécialisation, rangés par rôle : pas un classement, et pas un parse. Ils dépendent du groupe, du niveau d'objet et des affixes, affichés à côté. Groupe : tanks / soigneurs / dps ; Clés : dans les temps / terminées.":
        'Bester Schlüssel: der höchste rechtzeitig beendete Schlüssel; bei gleicher Stufe die beste Wertung, dann die kürzeste Zeit. Ein außerhalb der Zeit beendeter Schlüssel liegt nur vorn, wenn die Spezialisierung keinen rechtzeitigen hat. Bester Kill: der schnellste eines Raid-Bosses auf gleicher Schwierigkeit. Es sind die Rekorde jeder Spezialisierung, nach Rolle geordnet: keine Rangliste und kein Parse. Sie hängen von Gruppe, Gegenstandsstufe und Affixen ab, die daneben stehen. Gruppe: Tanks / Heiler / DPS; Schlüssel: rechtzeitig / beendet.',
    'Personnage':
        'Charakter',
    'Records':
        'Rekorde',
    'Score':
        'Wertung',
    "Sorties dont la spécialisation n'est pas écrite dans le journal, non comparées : %d.":
        'Durchgänge, deren Spezialisierung im Protokoll nicht steht, nicht verglichen: %d.',
    'Temps':
        'Zeit',
    'En temps':
        'Rechtzeitig',
}

# The French nouns `fmt.plural` agrees, and their German forms.
PLURALS = {
    'autre': ('weiterer', 'weitere'),
    'capacité': ('Fähigkeit', 'Fähigkeiten'),
    'cible': ('Ziel', 'Ziele'),
    'clé': ('Schlüssel', 'Schlüssel'),
    'combat': ('Kampf', 'Kämpfe'),
    'ennemi': ('Gegner', 'Gegner'),
    'joueur': ('Spieler', 'Spieler'),
    'mort': ('Tod', 'Tode'),
    'pull': ('Pull', 'Pulls'),
    'soirée': ('Abend', 'Abende'),
    'sortie': ('Durchgang', 'Durchgänge'),
    'sort': ('Zauber', 'Zauber'),
    'unité': ('Einheit', 'Einheiten'),
}

# Class and specialization by id: French names two different ones
# "Dévastation" (Demon Hunter Havoc, Evoker Devastation).
SPECS = {
    250: ('Todesritter', 'Blut'),
    251: ('Todesritter', 'Frost'),
    252: ('Todesritter', 'Unheilig'),
    577: ('Dämonenjäger', 'Verwüstung'),
    581: ('Dämonenjäger', 'Rachsucht'),
    1480: ('Dämonenjäger', 'Verschlinger'),
    102: ('Druide', 'Gleichgewicht'),
    103: ('Druide', 'Wildheit'),
    104: ('Druide', 'Wächter'),
    105: ('Druide', 'Wiederherstellung'),
    1467: ('Rufer', 'Verheerung'),
    1468: ('Rufer', 'Bewahrung'),
    1473: ('Rufer', 'Verstärkung'),
    253: ('Jäger', 'Tierherrschaft'),
    254: ('Jäger', 'Treffsicherheit'),
    255: ('Jäger', 'Überleben'),
    62: ('Magier', 'Arkan'),
    63: ('Magier', 'Feuer'),
    64: ('Magier', 'Frost'),
    268: ('Mönch', 'Braumeister'),
    269: ('Mönch', 'Windläufer'),
    270: ('Mönch', 'Nebelwirker'),
    65: ('Paladin', 'Heilig'),
    66: ('Paladin', 'Schutz'),
    70: ('Paladin', 'Vergeltung'),
    256: ('Priester', 'Disziplin'),
    257: ('Priester', 'Heilig'),
    258: ('Priester', 'Schatten'),
    259: ('Schurke', 'Meucheln'),
    260: ('Schurke', 'Gesetzlosigkeit'),
    261: ('Schurke', 'Täuschung'),
    262: ('Schamane', 'Elementar'),
    263: ('Schamane', 'Verstärkung'),
    264: ('Schamane', 'Wiederherstellung'),
    265: ('Hexenmeister', 'Gebrechen'),
    266: ('Hexenmeister', 'Dämonologie'),
    267: ('Hexenmeister', 'Zerstörung'),
    71: ('Krieger', 'Waffen'),
    72: ('Krieger', 'Furor'),
    73: ('Krieger', 'Schutz'),
}
