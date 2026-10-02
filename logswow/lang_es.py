# SPDX-License-Identifier: AGPL-3.0-or-later
"""Spanish (Spain): every French text of the interface, and its translation.

The keys are the French texts exactly as the code writes them; a test
fails when one is missing here, or when a translation does not keep
the original's %-placeholders and HTML tags in the same order.
`%.0s` swallows an argument: French passes a narrow no-break space
before a colon, which Spanish does not want.
"""

TEXTS = {
    # analysis
    'source non nommée par le journal':
        'fuente que el registro no nombra',
    'Tanks':
        'Tanques',
    'Soigneurs':
        'Sanadores',
    'Rôle non indiqué':
        'Rol no indicado',
    # cli
    '\r  %s lignes lues...':
        '\r  %s líneas leídas...',
    'Fichier introuvable : %s\n':
        'Archivo no encontrado: %s\n',
    '%s est un dossier, pas un fichier de journal. Cherchez-y WoWCombatLog.txt.\n':
        '%s es una carpeta, no un archivo de registro. Busque WoWCombatLog.txt dentro.\n',
    'Impossible de lire %s : %s\n':
        'No se puede leer %s: %s\n',
    "Aucun combat n'a été trouvé dans %s. Le fichier est peut-être vide, ou écrit par une version du client que ce lecteur ne comprend pas : `diagnose` dit ce qui a été lu.\n":
        'No se ha encontrado ningún combate en %s. Puede que el archivo esté vacío o que lo haya escrito una versión del cliente que este lector no entiende: `diagnose` muestra lo que se ha leído.\n',
    "Refus d'écrire le rapport par-dessus le journal lui-même (%s). Choisissez un autre nom avec -o.\n":
        'No se escribe el informe encima del propio registro (%s). Elija otro nombre con -o.\n',
    '%s est un dossier : donnez un nom de fichier avec -o.\n':
        '%s es una carpeta: indique un nombre de archivo con -o.\n',
    "%s existe et n'est pas un rapport LogsWoW : refus de l'écraser. Choisissez un autre nom, ou ajoutez --force si c'est voulu.\n":
        '%s existe y no es un informe de LogsWoW: no se sobrescribe. Elija otro nombre, o añada --force si es lo que quiere.\n',
    "%s existe et n'est pas un dossier : donnez un autre nom avec -o.\n":
        '%s existe y no es una carpeta: indique otro nombre con -o.\n',
    "Refus d'écrire les pages dans le dossier du journal lui-même (%s). Donnez un autre dossier avec -o.\n":
        'No se escriben las páginas en la carpeta del propio registro (%s). Indique otra carpeta con -o.\n',
    "%s contient déjà autre chose qu'un rapport LogsWoW : refus d'y écrire. Choisissez un autre dossier, ou ajoutez --force si c'est voulu.\n":
        '%s ya contiene algo distinto de un informe de LogsWoW: no se escribe ahí. Elija otra carpeta, o añada --force si es lo que quiere.\n',
    'Aucun combat ne correspond à --only %r. Utilisez `list` pour les voir.\n':
        'Ningún combate corresponde a --only %r. Use `list` para verlos.\n',
    "Impossible d'écrire %s : %s\n":
        'No se puede escribir %s: %s\n',
    '%d combat(s) retenu(s) sur %d, %s lignes lues en %.1f s':
        '%d de %d combates conservados, %s líneas leídas en %.1f s',
    '%d lignes non comprises -- lancez `diagnose` pour voir lesquelles':
        '%d líneas no comprendidas -- ejecute `diagnose` para ver cuáles',
    'Rapport écrit : %s':
        'Informe escrito: %s',
    'Combat':
        'Combate',
    'Durée':
        'Duración',
    'Dégâts':
        'Daño',
    'Morts':
        'Muertes',
    'Aucun dossier Logs trouvé aux emplacements habituels.':
        'No se ha encontrado ninguna carpeta Logs en los lugares habituales.',
    'Cherchez WoWCombatLog.txt sous _retail_/Logs dans votre installation,':
        'Busque WoWCombatLog.txt en _retail_/Logs dentro de su instalación',
    "puis donnez son chemin complet, entre guillemets s'il contient des espaces :":
        'e indique su ruta completa, entre comillas si contiene espacios:',
    '  report "/chemin/vers/World of Warcraft/_retail_/Logs/WoWCombatLog-....txt"':
        '  report "/ruta/a/World of Warcraft/_retail_/Logs/WoWCombatLog-....txt"',
    "Pas d'écran disponible pour ouvrir la fenêtre : utilisez les commandes (voir --help).\n":
        'No hay pantalla disponible para abrir la ventana: use los comandos (véase --help).\n',
    "%r n'est pas un nombre de secondes":
        '%r no es un número de segundos',
    '%r : il faut un nombre de secondes entre 0 et 86400':
        '%r: se necesita un número de segundos entre 0 y 86400',
    "%r n'est pas un nombre entier":
        '%r no es un número entero',
    '%r : il faut un nombre supérieur à zéro':
        '%r: se necesita un número mayor que cero',
    "langue de l'interface et du rapport : auto (celle du système, l'anglais pour une langue sans traduction), fr, en, de ou es":
        'idioma de la interfaz y del informe: auto (el del sistema, inglés para un idioma sin traducción), fr, en, de o es',
    'Lit un journal de combat de World of Warcraft, en local, sans rien envoyer nulle part.':
        'Lee un registro de combate de World of Warcraft, en local, sin enviar nada a ninguna parte.',
    'sans la progression ni le résumé : seulement les erreurs':
        'sin progreso ni resumen: solo los errores',
    'chemin du fichier WoWCombatLog.txt':
        'ruta del archivo WoWCombatLog.txt',
    "année, pour les journaux dont l'horodatage n'en porte pas":
        'año, para los registros cuya marca de tiempo no lo lleva',
    'SECONDES':
        'SEGUNDOS',
    'silence nécessaire pour séparer deux pulls (défaut %d s) ; baissez-le si vos packs sont regroupés, montez-le si un pull unique est coupé en deux':
        'silencio necesario para separar dos pulls (%d s por defecto); bájelo si sus packs van agrupados, súbalo si un solo pull queda partido en dos',
    'produit le rapport HTML':
        'genera el informe HTML',
    'fichier de sortie (.html)':
        'archivo de salida (.html)',
    "ne pas mettre l'ordre des sorts de chaque joueur : la page est environ deux fois plus légère":
        'no incluir el orden de hechizos de cada jugador: la página pesa aproximadamente la mitad',
    'présentation du rapport : onglets (un fichier, un combat et une catégorie à la fois, par défaut), pages (un dossier, une page par combat) ou longue (tout sur une seule page)':
        'presentación del informe: onglets (un archivo, un combate y una sección a la vez, por defecto), pages (una carpeta, una página por combate) o longue (todo en una sola página)',
    "écraser le fichier de sortie même s'il n'est pas un rapport LogsWoW (jamais le journal lu)":
        'sobrescribir el archivo de salida aunque no sea un informe de LogsWoW (nunca el registro leído)',
    'NUMÉRO|NOM':
        'NÚMERO|NOMBRE',
    "n'inclure qu'un combat : son numéro dans `list`, ou un bout de son nom":
        'incluir un solo combate: su número en `list`, o parte de su nombre',
    'LANGUE':
        'IDIOMA',
    'langue des liens Wowhead : auto (celle du système), fr, en, de, es, it, pt, ru, ko, zh, ou off pour ne mettre aucun lien':
        'idioma de los enlaces de Wowhead: auto (el del sistema), fr, en, de, es, it, pt, ru, ko, zh, u off para no poner ningún enlace',
    'liste les combats du fichier':
        'lista los combates del archivo',
    'montre ce que le lecteur a compris du fichier':
        'muestra lo que el lector ha entendido del archivo',
    "s'arrêter après N événements":
        'detenerse tras N eventos',
    'cherche le dossier Logs du jeu':
        'busca la carpeta Logs del juego',
    "ouvre la fenêtre (c'est aussi ce que fait la commande sans rien)":
        'abre la ventana (es también lo que hace el comando sin nada más)',
    '\nInterrompu.\n':
        '\nInterrumpido.\n',
    # diagnose
    'Fichier    : %s':
        'Archivo    : %s',
    'Taille     : %s, %s lignes, %s événements':
        'Tamaño     : %s, %s líneas, %s eventos',
    'Durée      : %s':
        'Duración   : %s',
    'DISPOSITION MESURÉE DANS CE FICHIER':
        'DISPOSICIÓN MEDIDA EN ESTE ARCHIVO',
    '  bloc avancé         : %d champs  (votes: %s)':
        '  bloque avanzado     : %d campos  (votos: %s)',
    '    votes à égalité, départage par : %s':
        '    empate en la votación, resuelto por: %s',
    '  champ baseAmount    : %s  (position du -1: %s)':
        '  campo baseAmount    : %s  (posición del -1: %s)',
    'présent':
        'presente',
    'absent':
        'ausente',
    '  champ hideCaster    : %s  (%s)':
        '  campo hideCaster    : %s  (%s)',
    '  journalisation avancée : %s':
        '  registro avanzado   : %s',
    'oui':
        'sí',
    'non -- positions et points de vie absents':
        'no -- faltan posiciones y puntos de salud',
    '  événements avec bloc avancé : %d sur %d':
        '  eventos con bloque avanzado : %d de %d',
    '  points de vie incohérents   : %d (courants > maximum ; ignorés pour les courbes de vie ennemies)':
        '  salud incoherente   : %d (actual > máximo; excluida de las curvas de salud enemigas)',
    'COMBATS DÉLIMITÉS : %d':
        'COMBATES DELIMITADOS: %d',
    'JOUEURS VUS : %d':
        'JUGADORES VISTOS: %d',
    'ÉVÉNEMENTS (%d types)':
        'EVENTOS (%d tipos)',
    '[SCHÉMA INCONNU] ':
        '[ESQUEMA DESCONOCIDO] ',
    'LIGNES NON RÉSOLUES':
        'LÍNEAS NO RESUELTAS',
    'LIGNES NON RÉSOLUES : aucune':
        'LÍNEAS NO RESUELTAS: ninguna',
    'PROBLÈMES DE LECTURE : %d':
        'PROBLEMAS DE LECTURA: %d',
    '    ligne %s : %s | %s':
        '    línea %s: %s | %s',
    # encounters
    'Rencontre':
        'Encuentro',
    # events
    'événement inconnu':
        'evento desconocido',
    'champs de base manquants':
        'faltan campos básicos',
    'ligne trop courte : %d champs pour un préfixe de %d':
        'línea demasiado corta: %d campos para un prefijo de %d',
    'nombre de champs inattendu : %d après le préfixe, attendu %s, ou cela +%d':
        'número de campos inesperado: %d tras el prefijo, se esperaba %s, o eso +%d',
    # gui
    "La fenêtre de LogsWoW a besoin de Tkinter, qui fait partie de Python mais\nque certaines distributions Linux livrent à part. Pour l'installer :\n  Linux Mint, Ubuntu, Debian : sudo apt install python3-tk\n  Fedora                     : sudo dnf install python3-tkinter\n  Arch, Manjaro              : sudo pacman -S tk\n  openSUSE                   : sudo zypper install python3-tk\n  macOS (Homebrew)           : brew install python-tk\nSous Windows, et sous macOS avec l'installateur de python.org, il est déjà là.\nLes commandes du terminal fonctionnent sans lui (voir ci-dessous).\n":
        'La ventana de LogsWoW necesita Tkinter, que forma parte de Python pero\nque algunas distribuciones Linux instalan aparte. Para instalarlo:\n  Linux Mint, Ubuntu, Debian : sudo apt install python3-tk\n  Fedora                     : sudo dnf install python3-tkinter\n  Arch, Manjaro              : sudo pacman -S tk\n  openSUSE                   : sudo zypper install python3-tk\n  macOS (Homebrew)           : brew install python-tk\nEn Windows, y en macOS con el instalador de python.org, ya está incluido.\nLos comandos del terminal funcionan sin él (véase más abajo).\n',
    'Go':
        'GB',
    'Mo':
        'MB',
    'Ko':
        'KB',
    '%d o':
        '%d B',
    'Onglets (un fichier)':
        'Pestañas (un archivo)',
    'Pages (un dossier)':
        'Páginas (una carpeta)',
    'Une seule longue page':
        'Una sola página larga',
    "Impossible d'écrire %s : %s":
        'No se puede escribir %s: %s',
    'Choisissez un journal, puis « Lire ce journal ».':
        'Elija un registro y luego «Leer este registro».',
    "Tout se passe sur cet ordinateur : aucune donnée n'est envoyée.":
        'Todo ocurre en este ordenador: no se envía ningún dato.',
    ' 1. Le journal ':
        ' 1. El registro ',
    'Fichier':
        'Archivo',
    'Date':
        'Fecha',
    'Taille':
        'Tamaño',
    'Dossier':
        'Carpeta',
    'Choisir un autre fichier…':
        'Elegir otro archivo…',
    'Actualiser la liste':
        'Actualizar la lista',
    'Lire ce journal':
        'Leer este registro',
    'Silence entre deux pulls : ':
        'Silencio entre dos pulls: ',
    'Annuler':
        'Cancelar',
    ' 2. Les combats ':
        ' 2. Los combates ',
    'Issue':
        'Resultado',
    'Tout sélectionner':
        'Seleccionar todo',
    ' 3. Le rapport ':
        ' 3. El informe ',
    'Ordre des sorts de chaque joueur (la page est environ deux fois plus lourde)':
        'Orden de hechizos de cada jugador (la página pesa aproximadamente el doble)',
    'Présentation :':
        'Presentación:',
    "Créer le rapport et l'ouvrir":
        'Crear el informe y abrirlo',
    'Ouvrir le dossier du rapport':
        'Abrir la carpeta del informe',
    '%d/%m/%Y %H:%M':
        '%d/%m/%Y %H:%M',
    "Aucun journal trouvé aux emplacements habituels : « Choisir un autre fichier… » pour l'indiquer.":
        'No se ha encontrado ningún registro en los lugares habituales: «Elegir otro archivo…» para indicarlo.',
    'Choisir un journal de combat':
        'Elegir un registro de combate',
    'Journaux de combat':
        'Registros de combate',
    'Fichiers texte':
        'Archivos de texto',
    'Tous les fichiers':
        'Todos los archivos',
    'Lecture de %s…':
        'Leyendo %s…',
    'Impossible de lire %s : %s':
        'No se puede leer %s: %s',
    'Erreur inattendue en lisant le journal :\n\n':
        'Error inesperado al leer el registro:\n\n',
    'Dans quel dossier écrire les pages ?':
        '¿En qué carpeta escribir las páginas?',
    'Où écrire le rapport ?':
        '¿Dónde escribir el informe?',
    'Page web':
        'Página web',
    'Écriture du rapport (%s)…':
        'Escribiendo el informe (%s)…',
    'Erreur inattendue en écrivant le rapport :\n\n':
        'Error inesperado al escribir el informe:\n\n',
    'Lecture… %s, %s lignes lues':
        'Leyendo… %s, %s líneas leídas',
    ', encore environ %s':
        ', quedan unos %s',
    '%d s':
        '%d s',
    '%d min %02d s':
        '%d min %02d s',
    "Aucun combat trouvé dans ce fichier : il est peut-être vide, ou /combatlog n'était pas lancé.":
        'No se ha encontrado ningún combate en este archivo: puede que esté vacío, o que /combatlog no estuviera activado.',
    '%s, %s lignes lues en %.0f s%s.':
        '%s, %s líneas leídas en %.0f s%s.',
    ', %d non comprises':
        ', %d no comprendidas',
    'Lecture annulée.':
        'Lectura cancelada.',
    'La lecture a échoué.':
        'La lectura ha fallado.',
    "Le rapport n'a pas été écrit.":
        'El informe no se ha escrito.',
    '%s sur %d dans le rapport':
        '%s de %d en el informe',
    # i18n
    'Attaque':
        'Cuerpo a cuerpo',
    # parse
    'marqueur -1 : %s':
        'marcador -1: %s',
    'puis proximité avec %d':
        'luego proximidad a %d',
    '%d votes / %d événements':
        '%d votos / %d eventos',
    'ligne sans le séparateur de deux espaces':
        'línea sin el separador de dos espacios',
    'horodatage illisible':
        'marca de tiempo ilegible',
    "nom d'événement illisible":
        'nombre de evento ilegible',
    # report
    'aucun':
        'ninguno',
    "<span class='pill ok'>boss &middot; réussite</span>":
        "<span class='pill ok'>jefe &middot; victoria</span>",
    "<span class='pill ko'>boss &middot; échec</span>":
        "<span class='pill ko'>jefe &middot; derrota</span>",
    'tank':
        'tanque',
    'soigneur':
        'sanador',
    'DPS':
        'DPS',
    ', par une invocation':
        ', mediante una invocación',
    'Ouvert par %s%s: %s':
        'Abierto por %s%.0s: %s',
    'bêta':
        'beta',
    '<b>%s</b> a agi en premier, sur %s%s: %s':
        '<b>%s</b> actuó primero, sobre %s%.0s: %s',
    ', %s%ss avant le premier coup':
        ', %s%ss antes del primer golpe',
    '%s; %s%ss plus tôt, %s avait aidé <b>%s</b> (%s)':
        '%.0s; %s%ss antes, %s había ayudado a <b>%s</b> (%s)',
    'Premier coup reçu par chaque ennemi (%s)':
        'Primer golpe recibido por cada enemigo (%s)',
    ' %s%s: aucune unité ne porte le nom de la rencontre (un conseil, par exemple), donc tous les dégâts infligés pendant sa durée sont comptés sur le boss.':
        ' %s%.0s: ninguna unidad lleva el nombre del encuentro (un consejo, por ejemplo), así que todo el daño infligido mientras dura se cuenta sobre el jefe.',
    '<tr><td colspan=7 class=dim>Aucun combat délimité dans ce fichier.</td></tr>':
        '<tr><td colspan=7 class=dim>No se ha delimitado ningún combate en este archivo.</td></tr>',
    "<h1>Rapport de combat</h1><p class=sub>%s &middot; %s lignes, %s événements &middot; généré le %s par LogsWoW %s</p><div class=note><b>Tout est resté sur cette machine.</b> Ce rapport a été produit en lisant le fichier de journal directement&nbsp;: aucun envoi, aucun compte, aucune connexion. La page est autonome, elle s'ouvre hors ligne.</div><div class=grid>%s</div><h2>Combats</h2><div class=card><table><tr><th>Combat</th><th class=n>Durée</th><th class=n>Dégâts</th><th class=n>Soins</th><th class=n>Pulls</th><th class=n>Joueurs</th><th class=n>Morts</th></tr>%s</table></div>":
        '<h1>Informe de combate</h1><p class=sub>%s &middot; %s líneas, %s eventos &middot; generado el %s por LogsWoW %s</p><div class=note><b>Todo se ha quedado en este equipo.</b> Este informe se ha generado leyendo directamente el archivo de registro: ningún envío, ninguna cuenta, ninguna conexión. La página es autónoma y se abre sin conexión.</div><div class=grid>%s</div><h2>Combates</h2><div class=card><table><tr><th>Combate</th><th class=n>Duración</th><th class=n>Daño</th><th class=n>Sanación</th><th class=n>Pulls</th><th class=n>Jugadores</th><th class=n>Muertes</th></tr>%s</table></div>',
    'Taille du fichier':
        'Tamaño del archivo',
    'Durée couverte':
        'Duración cubierta',
    'Pulls de boss':
        'Pulls de jefe',
    'Wipes de boss':
        'Derrotas ante jefes',
    'Clés mythiques':
        'Llaves míticas',
    'Clés hors des temps':
        'Llaves fuera de tiempo',
    'Clés non terminées':
        'Llaves sin terminar',
    'Lignes incomprises':
        'Líneas no comprendidas',
    "<h2 id='s%d'>%s%s</h2><p class=sub>%s &middot; %s &middot; %s de dégâts, %s de soins &middot; %s%s</p>":
        "<h2 id='s%d'>%s%s</h2><p class=sub>%s &middot; %s &middot; %s de daño, %s de sanación &middot; %s%s</p>",
    ' &middot; journal interrompu':
        ' &middot; registro interrumpido',
    'Dégâts infligés':
        'Daño infligido',
    'Soins effectifs':
        'Sanación efectiva',
    "<div class=note><b>%s de dégâts ne sont comptés pour personne.</b> Ils viennent d'unités alliées qui n'appartiennent à aucun joueur nommé par le journal%s: %s. Faute de savoir à qui les attribuer, ils ne sont ni dans le total ci-dessus ni dans la ligne d'un joueur.</div>":
        '<div class=note><b>%s de daño no se cuenta para nadie.</b> Procede de unidades aliadas que no pertenecen a ningún jugador nombrado por el registro%.0s: %s. Sin saber a quién atribuirlo, no está ni en el total de arriba ni en la fila de ningún jugador.</div>',
    '<th class=n>sur le boss</th><th class=n>sur les trash</th>':
        '<th class=n>al jefe</th><th class=n>al trash</th>',
    "<h3>%s</h3><div class=card><table><tr><th class=n>#</th><th class=n>Début</th><th class=n>Durée</th><th>Ce qui a été engagé</th><th class=n>Dégâts</th>%s<th class=n>Subis</th><th class=n>Morts</th></tr>%s</table><p class=dim style='margin:10px 0 0;font-size:12px'>Un pull se termine quand le groupe passe plus de %s sans infliger ni subir de dégâts. Un groupe qui enchaîne les packs sans pause les verra donc regroupés%s: <code>--pull-gap</code> change ce seuil, sauf à l'intérieur d'une rencontre de boss, qui reste toujours un seul pull.%s%s</p></div>":
        "<h3>%s</h3><div class=card><table><tr><th class=n>#</th><th class=n>Inicio</th><th class=n>Duración</th><th>Lo que se ha atacado</th><th class=n>Daño</th>%s<th class=n>Recibido</th><th class=n>Muertes</th></tr>%s</table><p class=dim style='margin:10px 0 0;font-size:12px'>Un pull termina cuando el grupo pasa más de %s sin infligir ni recibir daño. Un grupo que encadena packs sin pausa los verá por tanto agrupados%.0s: <code>--pull-gap</code> cambia ese umbral, salvo dentro de un encuentro con un jefe, que siempre es un solo pull.%s%s</p></div>",
    " %s écarté%s, trop petit%s pour compter (moins d'un millième des dégâts de la course).":
        ' %s descartado%s, demasiado pequeño%s para contar (menos de una milésima del daño de la mazmorra).',
    " Sous chaque pull, le premier acte qui lie le groupe à un ennemi depuis la fin du pull précédent%s: le journal n'a aucune ligne de menace, donc un ennemi pris par proximité ne s'y voit qu'à ce qu'il fait ensuite. Quand c'est l'ennemi qui agit en premier, sa première cible est un fort indice de qui l'a attiré, pas une preuve (une zone au sol laissée par le pack précédent, par exemple)%s; et un soin, un renfort ou une dissipation donné en combat attire l'ennemi vers celui qui l'a donné, si bien que la ligne dit aussi quand cette cible venait d'en donner un. Cette lecture est en bêta. Le premier coup reçu par chaque ennemi, lui, est écrit tel quel dans le journal.":
        ' Bajo cada pull, el primer acto que vincula al grupo con un enemigo desde el final del pull anterior%.0s: el registro no tiene ninguna línea de amenaza, así que un enemigo atraído por proximidad solo se ve por lo que hace después. Cuando el enemigo actúa primero, su primer objetivo es un fuerte indicio de quién lo atrajo, no una prueba (un efecto en el suelo dejado por el pack anterior, por ejemplo)%.0s; y una sanación, un beneficio o una disipación dados en combate atraen al enemigo hacia quien los dio, así que la línea también indica cuándo ese objetivo acababa de dar uno. Esta lectura está en beta. El primer golpe que recibió cada enemigo, en cambio, está escrito tal cual en el registro.',
    ' <span class=dim>(%s de surguérison)</span>':
        ' <span class=dim>(%s de sobresanación)</span>',
    '<th>Joueur</th><th class=n>Total</th>':
        '<th>Jugador</th><th class=n>Total</th>',
    '<th class=n>Absorbé</th><th class=n>Somme</th>':
        '<th class=n>Absorbido</th><th class=n>Suma</th>',
    '<th class=n>Réattribué</th>':
        '<th class=n>Reatribuido</th>',
    "<p class=dim style='margin:10px 0 0;font-size:12px'><b>Réattribué</b>%s: les dégâts de chacun, moins la part que le jeu crédite aux renforts d'un évocateur (Puissance d'ébène, Prescience, Bombardements...), plus ce qu'il crédite au joueur lui-même. C'est la réattribution de Warcraft Logs, et la seule que le journal permet%s: aucune ligne ne dit ce qu'une Furie sanguinaire, une Infusion de puissance ou un buff de raid a ajouté aux coups des autres. Le total du groupe ne change pas.</p>":
        "<p class=dim style='margin:10px 0 0;font-size:12px'><b>Reatribuido</b>%.0s: el daño de cada jugador, menos la parte que el juego acredita a los beneficios de un evocador (Poder de ébano, Presciencia, Bombardeos...), más lo que acredita al propio jugador. Es la reatribución de Warcraft Logs, y la única que permite el registro%.0s: ninguna línea dice lo que un Ansia de sangre, una Infusión de poder o un beneficio de banda añadió a los golpes de los demás. El total del grupo no cambia.</p>",
    "<p class=dim style='margin:10px 0 0;font-size:12px'>Un bouclier n'est pas un soin dans le journal%s: il empêche des dégâts au lieu d'en rendre. Les deux sont donc comptés à part, et additionnés dans la colonne <b>Somme</b> — c'est ce total-là que les sites en ligne appellent « soins ».</p>":
        "<p class=dim style='margin:10px 0 0;font-size:12px'>Un escudo no es una sanación en el registro%.0s: evita daño en lugar de devolver salud. Por eso ambos se cuentan por separado y se suman en la columna <b>Suma</b>; ese total es lo que los sitios en línea llaman «sanación».</p>",
    "<p class=dim style='margin:6px 0 0;font-size:12px'>Le Lien d'esprit ne soigne pas%s: il prend de la santé aux joueurs les plus hauts pour la donner aux plus bas. Les %s qu'il a pris sont déduits des soins de son poseur, comme sur Warcraft Logs, et ne comptent dans les dégâts subis de personne.</p>":
        "<p class=dim style='margin:6px 0 0;font-size:12px'>Enlace de espíritu no sana%.0s: quita salud a los jugadores con más vida para dársela a los que tienen menos. Los %s que ha quitado se restan de la sanación de quien lo lanzó, como en Warcraft Logs, y no cuentan en el daño recibido de nadie.</p>",
    "<h3>Ce qui a fait mal au groupe</h3><div class=card><table><tr><th>Capacité</th><th class=n>Dégâts</th><th class=n>Coups</th><th class=n>Joueurs touchés</th></tr>%s</table>%s<p class=dim style='margin:10px 0 0;font-size:12px'>Le fichier dit qui a été touché et combien. Il ne dit pas si le coup était évitable&nbsp;: cela demande de connaître le boss, ce que cet outil ne prétend pas savoir.</p></div>":
        "<h3>Lo que ha hecho daño al grupo</h3><div class=card><table><tr><th>Habilidad</th><th class=n>Daño</th><th class=n>Golpes</th><th class=n>Jugadores alcanzados</th></tr>%s</table>%s<p class=dim style='margin:10px 0 0;font-size:12px'>El archivo dice quién ha recibido el golpe y cuánto. No dice si el golpe era evitable: para eso hay que conocer al jefe, y esta herramienta no pretende saberlo.</p></div>",
    "<p class=dim style='margin:8px 0 0;font-size:12.5px'>Et %s de plus, %s de dégâts en tout.</p>":
        "<p class=dim style='margin:8px 0 0;font-size:12.5px'>Y %s más, %s de daño en total.</p>",
    ' <b>coup fatal</b>':
        ' <b>golpe mortal</b>',
    'mort instantanée':
        'muerte instantánea',
    'cause non écrite dans le journal':
        'causa no escrita en el registro',
    '<li class=dim>Rien avant la mort dans le journal.</li>':
        '<li class=dim>Nada antes de la muerte en el registro.</li>',
    "<h3>Composition du groupe</h3><div class=card><table>%s</table>%s<p class=dim style='margin:10px 0 0;font-size:12px'>Le rôle vient de la spécialisation que le client écrit au début du combat. Une spécialisation que cet outil ne connaît pas est affichée par son numéro.</p></div>":
        "<h3>Composición del grupo</h3><div class=card><table>%s</table>%s<p class=dim style='margin:10px 0 0;font-size:12px'>El rol procede de la especialización que el cliente escribe al comienzo del combate. Una especialización que esta herramienta no conoce se muestra con su número.</p></div>",
    "<p style='margin:10px 0 0;font-size:12.5px'>Aussi présents dans le journal, sans prendre part au combat (ni dégâts, ni soins, ni coups reçus)%s: %s.</p>":
        "<p style='margin:10px 0 0;font-size:12.5px'>También presentes en el registro, sin participar en el combate (ni daño, ni sanación, ni golpes recibidos)%.0s: %s.</p>",
    '<footer>LogsWoW %s &middot; lecture locale de <code>%s</code><br>Disposition détectée dans ce fichier&nbsp;: bloc avancé de %d champs, champ de dégâts bruts %s, champ hideCaster %s. Lignes non comprises&nbsp;: %s. Événements inconnus&nbsp;: %s.<br>Licence AGPL-3.0 ou ultérieure&nbsp;; code source&nbsp;: github.com/prenom6548/LogsWoW. Aucune donnée ne quitte cette machine.</footer></div></body></html>':
        '<footer>LogsWoW %s &middot; lectura local de <code>%s</code><br>Disposición detectada en este archivo: bloque avanzado de %d campos, campo de daño bruto %s, campo hideCaster %s. Líneas no comprendidas: %s. Eventos desconocidos: %s.<br>Licencia AGPL-3.0 o posterior; código fuente: github.com/prenom6548/LogsWoW. Ningún dato sale de este equipo.</footer></div></body></html>',
    # report_casts
    "<p class=dim style='font-size:12px'>Séquence coupée après %s sorts.</p>":
        "<p class=dim style='font-size:12px'>Secuencia cortada tras %s hechizos.</p>",
    '<details class=co><summary>Ordre des sorts, pull par pull <span class=dim>&middot; %s</span></summary><div class=cobody>%s%s<div class=pulls>%s%s</div></div></details>':
        '<details class=co><summary>Orden de hechizos, pull a pull <span class=dim>&middot; %s</span></summary><div class=cobody>%s%s<div class=pulls>%s%s</div></div></details>',
    'Lancés':
        'Lanzados',
    'Probablement déclenchés automatiquement (masqués)':
        'Probablemente activados por el juego (ocultos)',
    'Lancés par ses invocations':
        'Lanzados por sus invocaciones',
    "<p class=dim style='font-size:12px;margin:4px 0 0'>Le journal écrit de la même façon un sort appuyé et un sort que le jeu déclenche seul. Sont lus comme déclenchés, parmi les sorts lancés au moins %d fois dans ce combat sans jamais coûter de ressource%s: ceux qui, à %d%s%% au moins, partent en même temps qu'un sort payé, avec un écart médian de %d secondes au plus entre deux lancers%s; ceux dont l'écart médian est sous %s%ss, plus vite qu'aucun bouton%s; et la seconde copie d'un sort que le journal écrit deux fois, sous le même nom, au même instant. C'est une lecture du fichier%s: cliquez pour les afficher.</p>":
        "<p class=dim style='font-size:12px;margin:4px 0 0'>El registro escribe igual un hechizo pulsado que uno que el juego activa solo. Se leen como activados, entre los hechizos lanzados al menos %d veces en este combate sin costar nunca un recurso%.0s: los que, al menos el %d%s%% de las veces, salen a la vez que un hechizo pagado, con una separación mediana de %d segundos como máximo entre dos lanzamientos%.0s; los que tienen una separación mediana inferior a %s%ss, más rápido que cualquier botón%.0s; y la segunda copia de un hechizo que el registro escribe dos veces, con el mismo nombre, en el mismo instante. Es una lectura del archivo%.0s: haga clic para mostrarlos.</p>",
    "<div class=legend><p class=dim style='font-size:12px;margin:0'>Cliquez sur un sort pour le masquer ou l'afficher.</p>%s%s</div>":
        "<div class=legend><p class=dim style='font-size:12px;margin:0'>Haga clic en un hechizo para ocultarlo o mostrarlo.</p>%s%s</div>",
    'Entre les pulls':
        'Entre pulls',
    'Pull %02d &mdash; %s':
        'Pull %02d &mdash; %s',
    "<p class=dim style='line-height:1.5;margin:0'>Aucun sort pendant ce pull.</p>":
        "<p class=dim style='line-height:1.5;margin:0'>Ningún hechizo durante este pull.</p>",
    ', réussite':
        ', victoria',
    ', échec':
        ', derrota',
    'trash (%s)':
        'trash (%s)',
    # report_layouts
    'Résumé':
        'Resumen',
    'Dégâts et soins':
        'Daño y sanación',
    'Physique ou magique':
        'Físico o mágico',
    'Joueurs':
        'Jugadores',
    'Ennemis':
        'Enemigos',
    "<input type=radio name=f id=f0 class=fsel checked aria-label='Vue d&#39;ensemble'>":
        "<input type=radio name=f id=f0 class=fsel checked aria-label='Vista general'>",
    "<label for=f0 class='nv n0'>Vue d'ensemble</label>":
        "<label for=f0 class='nv n0'>Vista general</label>",
    "%s<div class=layout><nav class=side aria-label='Combats'>%s</nav><main>%s</main></div>%s":
        "%s<div class=layout><nav class=side aria-label='Combates'>%s</nav><main>%s</main></div>%s",
    "<a href='index.html'>&larr; Tous les combats</a>":
        "<a href='index.html'>&larr; Todos los combates</a>",
    # report_panels
    ' et %s':
        ' y %s',
    '<p class=dim>Rien.</p>':
        '<p class=dim>Nada.</p>',
    '<details class=more><summary>%s de plus &middot; %s (%s)</summary>%s</details>':
        '<details class=more><summary>%s más &middot; %s (%s)</summary>%s</details>',
    'Sort':
        'Hechizo',
    'Total':
        'Total',
    'Part':
        'Parte',
    'Surguérison':
        'Sobresanación',
    'Casts':
        'Lanzamientos',
    'Coups':
        'Golpes',
    'Moyenne':
        'Media',
    'Crit':
        'Crít.',
    'Par sec.':
        'Por seg.',
    'Principale cible':
        'Objetivo principal',
    'Principale source':
        'Fuente principal',
    '<table><tr><th>Effet</th><th>%s</th><th class=n>Durée</th></tr>%s</table>':
        '<table><tr><th>Efecto</th><th>%s</th><th class=n>Duración</th></tr>%s</table>',
    '<h3>Détail par joueur</h3>%s':
        '<h3>Detalle por jugador</h3>%s',
    ' (dont %d de ses invocations)':
        ' (%d de ellos por sus invocaciones)',
    "<details><summary>%s <span class=dim>&middot; %s &middot; %s dégâts &middot; %s soins &middot; %s</span></summary><div class=body><div class='grid tiles'>%s</div>%s%s</div></details>":
        "<details><summary>%s <span class=dim>&middot; %s &middot; %s de daño &middot; %s de sanación &middot; %s</span></summary><div class=body><div class='grid tiles'>%s</div>%s%s</div></details>",
    'rôle inconnu':
        'rol desconocido',
    'Part sur les boss':
        'Parte en jefes',
    'Subis par ses invocations':
        'Recibido por sus invocaciones',
    'Dégâts subis':
        'Daño recibido',
    'Absorbé sur lui':
        'Absorbido en él',
    'Absorbé par ses boucliers':
        'Absorbido por sus escudos',
    'Soutien crédité par le jeu':
        'Apoyo acreditado por el juego',
    'Sorts par minute':
        'Hechizos por minuto',
    'Temps sans action':
        'Tiempo sin acción',
    'Interruptions':
        'Interrupciones',
    'Dissipations':
        'Disipaciones',
    'Vie la plus basse':
        'Salud más baja',
    'Ce que ses boucliers ont absorbé':
        'Lo que absorbieron sus escudos',
    'Ses dégâts':
        'Su daño',
    'Ses soins':
        'Su sanación',
    'Qui il a soigné':
        'A quién sanó',
    "Ce qu'il a pris":
        'Lo que recibió',
    'Soutien que le jeu lui crédite':
        'Apoyo que el juego le acredita',
    'Plus longues pauses':
        'Pausas más largas',
    'Gains reçus':
        'Beneficios recibidos',
    'De qui':
        'De quién',
    'Affaiblissements subis':
        'Perjuicios sufridos',
    "Ce qu'il a appliqué":
        'Lo que aplicó',
    'Sur qui':
        'A quién',
    "<p class=dim style='font-size:12px;margin:0'>Un effet déjà actif quand le combat commence n'a pas de ligne d'application dans le journal%s: sa durée est comptée depuis le premier événement du combat, ce qui est la seule borne que le fichier donne.</p>":
        "<p class=dim style='font-size:12px;margin:0'>Un efecto ya activo cuando empieza el combate no tiene línea de aplicación en el registro%.0s: su duración se cuenta desde el primer evento del combate, que es el único límite que da el archivo.</p>",
    '<li><span class=dim>%s</span> sans lancer de sort, à %s</li>':
        '<li><span class=dim>%s</span> sin lanzar hechizos, a los %s</li>',
    '<li class=dim>Aucune pause notable.</li>':
        '<li class=dim>Ninguna pausa destacable.</li>',
    "<p class=dim style='font-size:12.5px;margin:8px 0 0'><b>Sorts ennemis coupés</b>%s %s</p>":
        "<p class=dim style='font-size:12.5px;margin:8px 0 0'><b>Hechizos enemigos interrumpidos</b>%.0s: %s</p>",
    "<p class=dim style='font-size:12.5px;margin:4px 0 0'><b>Effets dissipés</b>%s %s</p>":
        "<p class=dim style='font-size:12.5px;margin:4px 0 0'><b>Efectos disipados</b>%.0s: %s</p>",
    "%s<p class=dim style='font-size:12px;margin:4px 0 0'>Le journal crédite cet évocateur de %s de dégâts et %s de soins portés par d'autres joueurs%s: la part que ses renforts (Puissance d'ébène, Prescience...) ont ajoutée à leurs coups, et ses Bombardements, que le journal écrit au nom de l'allié qui les a déclenchés. Ces montants sont <b>déjà comptés</b> chez ceux qui ont porté les coups et ne sont pas ajoutés aux siens%s; Warcraft Logs, lui, les retire aux autres pour les lui donner, d'où l'écart entre les deux.</p>":
        "%s<p class=dim style='font-size:12px;margin:4px 0 0'>El registro acredita a este evocador %s de daño y %s de sanación realizados por otros jugadores%.0s: la parte que sus beneficios (Poder de ébano, Presciencia...) añadieron a sus golpes, y sus Bombardeos, que el registro escribe a nombre del aliado que los activó. Estas cantidades ya están <b>contadas</b> para quienes dieron los golpes y no se suman a las suyas%.0s; Warcraft Logs, en cambio, se las quita a los demás para dárselas a él, de ahí la diferencia entre ambos.</p>",
    '<table><tr><th>Cible</th><th class=n>Total</th><th class=n>Part</th></tr>%s</table>':
        '<table><tr><th>Objetivo</th><th class=n>Total</th><th class=n>Parte</th></tr>%s</table>',
    "Ce qu'il inflige":
        'Lo que inflige',
    "Ce qu'il a subi":
        'Lo que recibió',
    'Ses sorts':
        'Sus hechizos',
    '<table><tr><th>Sort</th><th class=n>Lancés</th></tr>%s</table>':
        '<table><tr><th>Hechizo</th><th class=n>Lanzados</th></tr>%s</table>',
    'Unités':
        'Unidades',
    'Sorts lancés':
        'Hechizos lanzados',
    'Tués':
        'Muertos',
    "<details><summary>%s <span class=dim>&middot; %s &middot; %s infligé &middot; %s subi</span></summary><div class=body><div class='grid tiles'>%s</div>%s</div></details>":
        "<details><summary>%s <span class=dim>&middot; %s &middot; %s infligido &middot; %s recibido</span></summary><div class=body><div class='grid tiles'>%s</div>%s</div></details>",
    '<h3>Détail par ennemi</h3>%s':
        '<h3>Detalle por enemigo</h3>%s',
    'Aboutis':
        'Completados',
    'Coupés par une interruption':
        'Cortados por una interrupción',
    "Lanceur tué pendant l'incantation":
        'Lanzador muerto durante el lanzamiento',
    'Non aboutis, cause non dite par le journal':
        'No completados, causa no indicada por el registro',
    "<p class=dim style='margin:10px 0 0;font-size:12px'>Les plus coupés%s: %s.</p>":
        "<p class=dim style='margin:10px 0 0;font-size:12px'>Los más interrumpidos%.0s: %s.</p>",
    "<h3>Ce que le groupe a empêché</h3><div class=card><p class=dim style='margin:0 0 10px;font-size:12.5px'>%s sorts commencés par l'ennemi%s:</p><table><tr><th>Issue</th><th class=n>Nombre</th><th class=n>Part</th></tr>%s</table>%s<p class=dim style='margin:10px 0 0;font-size:12px'>Un sort instantané n'apparaît pas ici%s: seuls ceux qui ont un temps d'incantation laissent une trace. La dernière ligne regroupe tout le reste, contrôle compris%s: le journal ne dit nulle part qu'un sort est un étourdissement, donc rien ici ne prétend le savoir.</p></div>":
        "<h3>Lo que el grupo impidió</h3><div class=card><p class=dim style='margin:0 0 10px;font-size:12.5px'>%s hechizos iniciados por el enemigo%.0s:</p><table><tr><th>Resultado</th><th class=n>Número</th><th class=n>Parte</th></tr>%s</table>%s<p class=dim style='margin:10px 0 0;font-size:12px'>Un hechizo instantáneo no aparece aquí%.0s: solo dejan rastro los que tienen tiempo de lanzamiento. La última fila reúne todo lo demás, control incluido%.0s: el registro nunca dice que un hechizo sea un aturdimiento, así que nada aquí pretende saberlo.</p></div>",
    # report_schools
    'autres %s':
        'otras %s',
    'Physique':
        'Físico',
    'Magique':
        'Mágico',
    'Mixte':
        'Mixto',
    'Phys.':
        'Fís.',
    'Mag.':
        'Mág.',
    'Subis':
        'Recibido',
    'Infligés':
        'Infligido',
    "<p class=dim style='font-size:12.5px;margin:6px 0 0'><b>%s par école</b>%s: %s</p>":
        "<p class=dim style='font-size:12.5px;margin:6px 0 0'><b>%s por escuela</b>%.0s: %s</p>",
    "<h3>Physique ou magique</h3><div class='card schools'><p style='margin:0 0 8px;font-size:12.5px'>%s</p><table><tr><th></th><th>Répartition</th>%s</tr>%s</table>%s%s<p class=dim style='margin:10px 0 0;font-size:12px'>L'école de chaque coup est celle que le journal écrit sur la ligne. « Mixte »%s: physique et magique à la fois (Ombre-frappe, Chaos...). Comme dans le reste du rapport, un coup qu'un bouclier ennemi a mangé compte dans les dégâts infligés, et la part qu'un bouclier du groupe a mangée ne compte pas dans les dégâts subis.</p></div>":
        "<h3>Físico o mágico</h3><div class='card schools'><p style='margin:0 0 8px;font-size:12.5px'>%s</p><table><tr><th></th><th>Reparto</th>%s</tr>%s</table>%s%s<p class=dim style='margin:10px 0 0;font-size:12px'>La escuela de cada golpe es la que el registro escribe en la línea. «Mixto»%.0s: físico y mágico a la vez (Golpe de las Sombras, Caos...). Como en el resto del informe, un golpe que se tragó un escudo enemigo cuenta en el daño infligido, y la parte que se tragó un escudo del grupo no cuenta en el daño recibido.</p></div>",
    "<h3 style='margin-top:18px'>Pull par pull</h3><table><tr><th class=n>#</th><th>Ce qui a été engagé</th><th>Subis</th>%s<th>Infligés</th>%s</tr>%s</table>":
        "<h3 style='margin-top:18px'>Pull a pull</h3><table><tr><th class=n>#</th><th>Lo que se ha atacado</th><th>Recibido</th>%s<th>Infligido</th>%s</tr>%s</table>",
    # report_timeline
    "<h3>Dégâts subis par le groupe, seconde par seconde</h3><div class=card><svg viewBox='0 0 %d %d' role=img aria-label='Dégâts subis au fil du combat'>%s</svg><p class=dim style='margin:6px 0 0;font-size:12px'>Barres et échelle de gauche%s: dégâts subis par intervalle de %s. Traits rouges%s: morts.%s</p></div>":
        "<h3>Daño recibido por el grupo, segundo a segundo</h3><div class=card><svg viewBox='0 0 %d %d' role=img aria-label='Daño recibido a lo largo del combate'>%s</svg><p class=dim style='margin:6px 0 0;font-size:12px'>Barras y escala de la izquierda%.0s: daño recibido por intervalo de %s. Líneas rojas%.0s: muertes.%s</p></div>",
    " Courbe et échelle de droite%s: <b>vie cumulée des ennemis engagés</b>, somme de leurs points de vie courants sur la somme de leurs maximums. Elle remonte à chaque nouveau pack et retombe quand il meurt%s; un ennemi que le groupe n'a plus touché depuis %d%ss en sort.":
        ' Curva y escala de la derecha%.0s: <b>salud conjunta de los enemigos atacados</b>, la suma de su salud actual entre la suma de sus máximos. Sube con cada pack nuevo y baja cuando muere%.0s; un enemigo al que el grupo no ha golpeado desde hace %d%ss sale de ella.',
    ' Courbe et échelle de droite%s: vie de <b>%s</b>, la cible la plus frappée parmi celles dont le journal donne les points de vie.':
        ' Curva y escala de la derecha%.0s: salud de <b>%s</b>, el objetivo más golpeado entre aquellos cuya salud da el registro.',
    # schools
    'Sacré':
        'Sagrado',
    'Feu':
        'Fuego',
    'Nature':
        'Naturaleza',
    'Givre':
        'Escarcha',
    'Ombre':
        'Sombras',
    'Arcane':
        'Arcano',
    'école inconnue':
        'escuela desconocida',
    # models
    'et %d autre(s)':
        'y %d más',
    'autres':
        'otros',
    # segment
    'Normal':
        'Normal',
    'Héroïque':
        'Heroico',
    '10 joueurs':
        '10 jugadores',
    '25 joueurs':
        '25 jugadores',
    '10 héroïque':
        '10 jugadores (heroico)',
    '25 héroïque':
        '25 jugadores (heroico)',
    'Raid Recherche':
        'Buscador de bandas',
    'Mythique+':
        'Mítica+',
    '40 joueurs':
        '40 jugadores',
    'Héroïque scénario':
        'Escenario heroico',
    'Normal scénario':
        'Escenario normal',
    'Mythique':
        'Mítico',
    'Marche du temps':
        'Paseo en el tiempo',
    'Torghast':
        'Torghast',
    'difficulté %d':
        'dificultad %d',
    'sans combat':
        'sin combate',
    'abandonnée':
        'abandonada',
    'terminée':
        'completada',
    'interrompu':
        'interrumpido',
    'dans les temps':
        'a tiempo',
    'hors des temps':
        'fuera de tiempo',
    'réussite':
        'victoria',
    'échec':
        'derrota',
    'Pull %d':
        'Pull %d',
    'Donjon':
        'Mazmorra',
    'Session complète':
        'Sesión completa',
    # specs
    'spe %d':
        'espec. %d',
    'Touché':
        'Impacto',
    'Absorbé entièrement':
        'Absorbido por completo',
    'Paré':
        'Parado',
    'Esquivé':
        'Esquivado',
    'Raté':
        'Fallado',
    'Bloqué entièrement':
        'Bloqueado por completo',
    'Dévié':
        'Desviado',
    'Insensible':
        'Inmune',
    'Résisté':
        'Resistido',
    'Renvoyé':
        'Reflejado',
    "Hors d'atteinte":
        'Fuera de alcance',
    'Les coups de mêlée reçus':
        'Golpes cuerpo a cuerpo recibidos',
    'dont critiques':
        'de ellos críticos',
    'dont bloqués en partie':
        'de ellos bloqueados en parte',
    '<table><tr><th>Issue</th><th class=n>Coups</th><th class=n>Part</th></tr>%s</table>':
        '<table><tr><th>Resultado</th><th class=n>Golpes</th><th class=n>Parte</th></tr>%s</table>',
    '<p><b>%s</b> des coups évités (parés, esquivés ou ratés).</p>':
        '<p><b>%s</b> de los golpes evitados (parados, esquivados o fallados).</p>',
    '<p><b>%s</b> des coups qui ont touché venaient de derrière (%s sur %s dont la position est connue).</p>':
        '<p><b>%s</b> de los golpes que impactaron llegaron por la espalda (%s de %s con posición conocida).</p>',
    ' Contrôle sur ce combat%s: le jeu ne laisse ni parer ni esquiver un coup venu de derrière, et %s des %s parades et esquives placées tombent bien devant.':
        ' Control en este combate%.0s: el juego no permite parar ni esquivar un golpe por la espalda, y el %s de las %s paradas y esquivas situadas cae delante.',
    "<p class=dim style='font-size:12px;margin:0'>Estimation fiable, mais pas une donnée écrite, et limitée à la mêlée%s: le journal ne dit pas d'où vient un coup. LogsWoW le déduit de la position de l'attaquant et de l'orientation du joueur, que le journal donne ligne par ligne.%s</p>":
        "<p class=dim style='font-size:12px;margin:0'>Una estimación fiable, pero no un dato escrito, y limitada al cuerpo a cuerpo%.0s: el registro no dice de dónde viene un golpe. LogsWoW lo deduce de la posición del atacante y de la orientación del jugador, que el registro da línea a línea.%s</p>",
    # equipment, comparison of keys, preview (0.15.0)
    'Tête':
        'Cabeza',
    'Cou':
        'Cuello',
    'Épaules':
        'Hombros',
    'Chemise':
        'Camisa',
    'Torse':
        'Pecho',
    'Jambes':
        'Piernas',
    'Pieds':
        'Pies',
    'Poignets':
        'Muñecas',
    'Mains':
        'Manos',
    'Anneau 1':
        'Anillo 1',
    'Anneau 2':
        'Anillo 2',
    'Bijou 1':
        'Abalorio 1',
    'Bijou 2':
        'Abalorio 2',
    'Dos':
        'Espalda',
    'Main droite':
        'Mano derecha',
    'Main gauche':
        'Mano izquierda',
    'Tabard':
        'Tabardo',
    'Aperçu':
        'Resumen',
    'Clés':
        'Llaves',
    'Équipement':
        'Equipo',
    'Cochez un ou plusieurs combats pour voir ce que le rapport en dirait.':
        'Marque uno o varios combates para ver lo que diría el informe.',
    'Aucune clé terminée à comparer : il faut au moins une clé, et deux du même niveau pour les mettre côte à côte.':
        'No hay ninguna llave terminada que comparar: hace falta al menos una, y dos del mismo nivel para ponerlas una junto a otra.',
    "Écart : la dernière clé par rapport à la première. Soins/s compte les boucliers ; Subis/s compte ce que les boucliers ont absorbé, et n'est donné qu'aux tanks.":
        'Diferencia: la última llave respecto a la primera. Sanación/s cuenta los escudos; Recibido/s cuenta lo que absorbieron los escudos, y solo se da a los tanques.',
    '%s — %s (%s)':
        '%s — %s (%s)',
    'Dégâts %s (%s/s) · Soins %s (%s/s, boucliers compris) · Subis %s · %s':
        'Daño %s (%s/s) · Sanación %s (%s/s, escudos incluidos) · Recibido %s · %s',
    'Morts :':
        'Muertes:',
    '%s dégâts/s':
        '%s de daño/s',
    '%s soins/s':
        '%s de sanación/s',
    'Dégâts/s':
        'Daño/s',
    'Soins/s':
        'Sanación/s',
    'Subis/s':
        'Recibido/s',
    "Niveau d'objet moyen du groupe : %s":
        'Nivel de objeto medio del grupo: %s',
    'Boss : %s':
        'Jefe: %s',
    '%s subis/s':
        '%s recibido/s',
    'ilvl %s':
        'ilvl %s',
    '%s : %s':
        '%s: %s',
    '  %s à %s : %s':
        '  %s a los %s: %s',
    'Écart':
        'Diferencia',
    'Clé %d':
        'Llave %d',
    'Groupe : ':
        'Grupo: ',
    'sans résultat':
        'sin resultado',
    "<p style='margin:10px 0 0;font-size:12.5px'>Niveau d'objet moyen du groupe%s: <b>%s</b> (de %s à %s).</p>":
        "<p style='margin:10px 0 0;font-size:12.5px'>Nivel de objeto medio del grupo%s: <b>%s</b> (de %s a %s).</p>",
    'Comparaison des clés':
        'Comparación de llaves',
    "<p class=dim style='font-size:12.5px'>Écart%s: la dernière clé par rapport à la première. <b>Soins/s</b> compte les boucliers (le journal ne les range pas parmi les soins, les sites en ligne si). <b>Subis/s</b> compte ce que les boucliers ont absorbé : c'est ce qui arrive au tank avant ses protections, et il n'est donné qu'aux tanks. Seules des clés terminées du même niveau sont comparées.</p>":
        "<p class=dim style='font-size:12.5px'>Diferencia%s: la última llave respecto a la primera. <b>Sanación/s</b> cuenta los escudos (el registro no los clasifica como sanación, los sitios en línea sí). <b>Recibido/s</b> cuenta lo que absorbieron los escudos: es lo que llega al tanque antes de sus protecciones, y solo se da a los tanques. Solo se comparan llaves terminadas del mismo nivel.</p>",
    "Le journal donne le numéro et le niveau de chaque objet, jamais son nom ni son icône : ils viennent de la base d'objets du jeu, que ce rapport n'a pas (il ne se connecte à rien). Le lien ouvre Wowhead si vous cliquez dessus. Le niveau moyen suit la formule du jeu : seize emplacements, chemise et tabard exclus, une arme à deux mains comptée deux fois, un emplacement vide pour zéro.":
        'El registro da el número y el nivel de cada objeto, nunca su nombre ni su icono: vienen de la base de objetos del juego, que este informe no tiene (no se conecta a nada). El enlace abre Wowhead si hace clic en él. El nivel medio sigue la fórmula del juego: dieciséis ranuras, sin camisa ni tabardo, un arma a dos manos contada dos veces, una ranura vacía como cero.',
    'Joueur':
        'Jugador',
    'objet %d':
        'objeto %d',
    'Emplacement':
        'Ranura',
    'Objet':
        'Objeto',
    'Niveau':
        'Nivel',
    "<p class=dim style='margin:6px 0 0'>Emplacement vide%s: %s.</p>":
        "<p class=dim style='margin:6px 0 0'>Ranura vacía%s: %s.</p>",
    ' (non compté)':
        ' (no cuenta)',
    # history (foundation)
    "%s n'est pas un dossier d'historique LogsWoW : refus d'y écrire.":
        '%s no es una carpeta de historial de LogsWoW: me niego a escribir en ella.',
    'Réglage inconnu : %s':
        'Ajuste desconocido: %s',
    'Nom de dossier invalide : %s':
        'Nombre de carpeta no válido: %s',
    'Nom de dossier invalide : donnez un nom avec au moins une lettre ou un chiffre.':
        'Nombre de carpeta no válido: escriba un nombre con al menos una letra o un número.',
    'Un dossier de ce nom existe déjà : %s':
        'Ya existe una carpeta con este nombre: %s',
    "Dossier d'historique introuvable : %s":
        'Carpeta de historial no encontrada: %s',
    'Le dossier %s contient un fichier qui ne vient pas de LogsWoW (%s) : refus de le supprimer.':
        'La carpeta %s contiene un archivo que no procede de LogsWoW (%s): me niego a eliminarla.',
    "Fichier de l'historique illisible (%s) : %s":
        'Archivo del historial ilegible (%s): %s',
    "Ce fichier n'est pas une soirée de l'historique LogsWoW : %s":
        'Este archivo no es una noche del historial de LogsWoW: %s',
    'Une soirée de même nom existe déjà dans ce dossier : %s':
        'Ya existe una noche con el mismo nombre en esta carpeta: %s',
    # history window (0.15.2)
    'Historique…':
        'Historial…',
    "La version du jeu a changé : ouvrez l'Historique pour créer un nouveau dossier.":
        'La versión del juego ha cambiado: abra el Historial para crear una carpeta nueva.',
    'Historique indisponible : %s':
        'Historial no disponible: %s',
    "Soirée déjà dans l'historique : mise à jour (dossier « %s »).":
        'Noche ya en el historial: actualizada (carpeta «%s»).',
    "Soirée ajoutée à l'historique (dossier « %s »).":
        'Noche añadida al historial (carpeta «%s»).',
    "L'historique garde, soirée après soirée, les chiffres de vos personnages pour voir comment vous évoluez : un petit fichier par soirée (environ 30 Ko), rangé dans le dossier de votre choix, sur cet ordinateur uniquement. Rien n'est enregistré sans votre accord, et seuls les personnages que vous suivez y laissent leur nom ; les autres joueurs n'apparaissent que dans les totaux du groupe. Commencez par créer un dossier (par exemple une saison, ou « avec mes amis »).":
        'El historial guarda, noche tras noche, las cifras de sus personajes para ver cómo evoluciona: un archivo pequeño por noche (unos 30 KB), en la carpeta que elija, solo en este ordenador. No se guarda nada sin su consentimiento, y solo los personajes que sigue dejan en él su nombre; los demás jugadores solo aparecen en los totales del grupo. Empiece creando una carpeta (por ejemplo una temporada, o «con mis amigos»).',
    "Rien n'est enregistré sans votre accord. Seuls les personnages suivis y laissent leur nom ; les autres joueurs n'apparaissent que dans les totaux du groupe.":
        'No se guarda nada sin su consentimiento. Solo los personajes seguidos dejan en él su nombre; los demás jugadores solo aparecen en los totales del grupo.',
    'Tank':
        'Tanque',
    'Soigneur':
        'Sanador',
    "La version du jeu est passée de %s à %s : un nouveau patch. Les chiffres des soirées suivantes ne sont pas forcément comparables à ceux d'avant. Commencer un nouveau dossier ?":
        'La versión del juego ha pasado de %s a %s: un parche nuevo. Las cifras de las noches siguientes no son necesariamente comparables con las anteriores. ¿Empezar una carpeta nueva?',
    "La version du jeu est passée de %s à %s : une nouvelle extension. Les chiffres des soirées suivantes ne sont pas comparables à ceux d'avant. Commencer un nouveau dossier ?":
        'La versión del juego ha pasado de %s a %s: una expansión nueva. Las cifras de las noches siguientes no son comparables con las anteriores. ¿Empezar una carpeta nueva?',
    "Choisissez d'abord un dossier.":
        'Elija primero una carpeta.',
    'Aucun combat à enregistrer dans ce journal.':
        'Ningún combate que guardar en este registro.',
    'Historique':
        'Historial',
    'Créez un dossier pour commencer.':
        'Cree una carpeta para empezar.',
    'Aucun journal lu : lisez un journal dans la fenêtre principale pour pouvoir ajouter une soirée.':
        'Ningún registro leído: lea un registro en la ventana principal para poder añadir una noche.',
    'Nouveau dossier':
        'Carpeta nueva',
    'Nom du dossier (par exemple « Saison 1 », « Avec mes amis ») :':
        'Nombre de la carpeta (por ejemplo «Temporada 1», «Con mis amigos»):',
    'Renommer le dossier':
        'Renombrar la carpeta',
    'Nouveau nom du dossier :':
        'Nuevo nombre de la carpeta:',
    'Déplacer la soirée':
        'Mover la noche',
    'Dossier de destination :':
        'Carpeta de destino:',
    'Nouveau dossier…':
        'Carpeta nueva…',
    'Renommer…':
        'Renombrar…',
    'Supprimer ce dossier…':
        'Eliminar esta carpeta…',
    ' Personnages de ce journal ':
        ' Personajes de este registro ',
    'Suivre la sélection':
        'Seguir la selección',
    'Ne plus suivre':
        'Dejar de seguir',
    "Ajouter cette soirée à l'historique":
        'Añadir esta noche al historial',
    'Enregistrer automatiquement chaque journal lu (seulement si un personnage suivi y a joué)':
        'Guardar automáticamente cada registro leído (solo si un personaje seguido participó)',
    ' Soirées de ce dossier ':
        ' Noches de esta carpeta ',
    'Supprimer la soirée':
        'Eliminar la noche',
    'Déplacer vers un autre dossier…':
        'Mover a otra carpeta…',
    'Fermer':
        'Cerrar',
    'Dossier créé : %s':
        'Carpeta creada: %s',
    'Supprimer le dossier':
        'Eliminar la carpeta',
    'Dossier supprimé : %s (%s).':
        'Carpeta eliminada: %s (%s).',
    'Suivi':
        'Seguido',
    'Spécialisation':
        'Especialización',
    'Rôle':
        'Rol',
    'Combats':
        'Combates',
    'Journal':
        'Registro',
    'Jeu':
        'Juego',
    'Aucun personnage suivi.':
        'Ningún personaje seguido.',
    'Supprimer le dossier « %s » et ses %s ? Cela ne touche pas à vos journaux de combat.':
        '¿Eliminar la carpeta «%s» y sus %s? No afecta a sus registros de combate.',
    "Ajouter à l'historique":
        'Añadir al historial',
    "Aucun personnage suivi dans ce journal : la soirée ne gardera que les totaux du groupe. L'enregistrer quand même ?":
        'Ningún personaje seguido en este registro: la noche solo conservará los totales del grupo. ¿Guardarla de todos modos?',
    "Supprimer %s de l'historique ? Vos journaux de combat ne sont pas touchés.":
        '¿Eliminar %s del historial? No afecta a sus registros de combate.',
    'Créer un nouveau dossier…':
        'Crear una carpeta nueva…',
    'Ignorer':
        'Ignorar',
    'Dossier :':
        'Carpeta:',
    'Personnages suivis au total : %d':
        'Personajes seguidos en total: %d',
    # history: evolution of a character
    'Clés et boss':
        'Llaves y jefes',
    'Clés seulement':
        'Solo llaves',
    'Boss seulement':
        'Solo jefes',
    'Certaines sorties ont été comptées avec une ancienne version des règles de calcul : leurs chiffres ne sont pas forcément comparables.':
        'Algunas salidas se contaron con una versión anterior de las reglas de cálculo: sus cifras no son necesariamente comparables.',
    '† Hors tendance : clé abandonnée ou interrompue, boss non tué.':
        '† Fuera de la tendencia: llave abandonada o interrumpida, jefe no derrotado.',
    ' Par contenu ':
        ' Por contenido ',
    ' Toutes les sorties ':
        ' Todas las salidas ',
    "Écart : la dernière sortie par rapport à la première, dans un même contenu et un même niveau (ou une même difficulté). Il dépend aussi du niveau d'objet, du groupe et des affixes, affichés à côté : ce n'est pas une note. Groupe : tanks / soigneurs / dps.":
        'Diferencia: la última salida respecto a la primera, en el mismo contenido y el mismo nivel (o dificultad). Depende también del nivel de objeto, del grupo y de los afijos, mostrados al lado: no es una nota. Grupo: tanques / sanadores / dps.',
    'Spécialisations différentes dans « %s » : %s.':
        'Especializaciones distintas en «%s»: %s.',
    'Contenu':
        'Contenido',
    'Sorties':
        'Salidas',
    'Première':
        'Primera',
    'Dernière':
        'Última',
    ' Tendance ':
        ' Tendencia ',
    'Groupe':
        'Grupo',
    "Aucun personnage suivi dans ce dossier : suivez-en un dans l'onglet « Soirées », puis ajoutez des soirées.":
        'Ningún personaje seguido en esta carpeta: siga uno en la pestaña «Noches» y añada después noches.',
    'Aucune sortie de ce personnage dans ce dossier.':
        'Ninguna salida de este personaje en esta carpeta.',
    'Personnage :':
        'Personaje:',
    'Mesure :':
        'Medida:',
    'Afficher :':
        'Mostrar:',
    'Soirées':
        'Noches',
    'Évolution':
        'Evolución',
}

# The French nouns `fmt.plural` agrees, and their Spanish forms.
PLURALS = {
    'autre': ('otro', 'otros'),
    'capacité': ('habilidad', 'habilidades'),
    'cible': ('objetivo', 'objetivos'),
    'clé': ('llave', 'llaves'),
    'combat': ('combate', 'combates'),
    'ennemi': ('enemigo', 'enemigos'),
    'joueur': ('jugador', 'jugadores'),
    'mort': ('muerte', 'muertes'),
    'pull': ('pull', 'pulls'),
    'soirée': ('noche', 'noches'),
    'sortie': ('salida', 'salidas'),
    'sort': ('hechizo', 'hechizos'),
    'unité': ('unidad', 'unidades'),
}

# Class and specialization by id: French names two different ones
# "Dévastation" (Demon Hunter Havoc, Evoker Devastation).
SPECS = {
    250: ('Caballero de la Muerte', 'Sangre'),
    251: ('Caballero de la Muerte', 'Escarcha'),
    252: ('Caballero de la Muerte', 'Profano'),
    577: ('Cazador de demonios', 'Devastación'),
    581: ('Cazador de demonios', 'Venganza'),
    1480: ('Cazador de demonios', 'Devorador'),
    102: ('Druida', 'Equilibrio'),
    103: ('Druida', 'Feral'),
    104: ('Druida', 'Guardián'),
    105: ('Druida', 'Restauración'),
    1467: ('Evocador', 'Devastación'),
    1468: ('Evocador', 'Preservación'),
    1473: ('Evocador', 'Aumento'),
    253: ('Cazador', 'Bestias'),
    254: ('Cazador', 'Puntería'),
    255: ('Cazador', 'Supervivencia'),
    62: ('Mago', 'Arcano'),
    63: ('Mago', 'Fuego'),
    64: ('Mago', 'Escarcha'),
    268: ('Monje', 'Maestro cervecero'),
    269: ('Monje', 'Viajero del viento'),
    270: ('Monje', 'Tejedor de niebla'),
    65: ('Paladín', 'Sagrado'),
    66: ('Paladín', 'Protección'),
    70: ('Paladín', 'Reprensión'),
    256: ('Sacerdote', 'Disciplina'),
    257: ('Sacerdote', 'Sagrado'),
    258: ('Sacerdote', 'Sombra'),
    259: ('Pícaro', 'Asesinato'),
    260: ('Pícaro', 'Forajido'),
    261: ('Pícaro', 'Sutileza'),
    262: ('Chamán', 'Elemental'),
    263: ('Chamán', 'Mejora'),
    264: ('Chamán', 'Restauración'),
    265: ('Brujo', 'Aflicción'),
    266: ('Brujo', 'Demonología'),
    267: ('Brujo', 'Destrucción'),
    71: ('Guerrero', 'Armas'),
    72: ('Guerrero', 'Furia'),
    73: ('Guerrero', 'Protección'),
}
