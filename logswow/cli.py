# SPDX-License-Identifier: AGPL-3.0-or-later
"""`python3 -m logswow` -- the whole tool, from one command.

Deliberately dependency-free and deliberately offline: nothing here
opens a socket, and there is no configuration file, no cache directory
and no account. Point it at a log, get an HTML page next to it.
"""

import argparse
import glob
import math
import os
import sys
import time

from . import __version__
from .analysis import SegmentAnalysis
from .diagnose import run as run_diagnose
from .i18n import LANGUAGES, _, language, set_language
from .parse import LogFile
from .report import ReportWriter
from .report_layouts import LAYOUTS, is_our_report
from .segment import Splitter
from .timestamps import format_duration


# Where another disk is mounted: Linux (/mnt by hand, /media and
# /run/media by the desktop) and macOS (/Volumes). A game library on a
# second disk is common -- the owner's is /mnt/<disk>/World of Warcraft,
# which `where` missed on the first try.
MOUNT_ROOTS = ("/mnt/*", "/media/*", "/media/*/*", "/run/media/*/*", "/Volumes/*")


def _on_other_disks(retail, mount_roots):
    """Logs folders at the top of a mounted disk, or one or two folders down."""
    logs = os.path.join("World of Warcraft", "_retail_", "Logs")
    found = []
    for root in mount_roots:
        for pattern in (logs, os.path.join("*", logs),       # <disk>/[Jeux/]World of Warcraft
                        os.path.join("*", retail),           # <disk>/<prefix>/drive_c/...
                        os.path.join("*", "*", retail)):     # <disk>/Games/battlenet/drive_c/...
            found += sorted(glob.glob(os.path.join(root, pattern)))
    return found


def default_log_locations(mount_roots=MOUNT_ROOTS):
    """Where the client usually writes, on each system it runs on.

    On Windows, Battle.net installs on whichever drive was chosen, so the
    usual folders are tried on C: to H:. On macOS the game is native and
    lives in /Applications. On Linux the game runs through a Windows
    compatibility layer, and each launcher keeps its own copy of drive C:
    Lutris under ~/Games, Steam (Battle.net added as a non-Steam game)
    under a numbered compatdata prefix, Bottles under its own data
    folder. The numbered ones are found by pattern rather than guessed.
    Outside Windows, other mounted disks are looked at too.
    """
    retail = os.path.join("drive_c", "Program Files (x86)", "World of Warcraft",
                          "_retail_", "Logs")
    home = os.path.expanduser("~")
    candidates = []
    if os.name == "nt":
        # Battle.net lets the game live on any drive, not only C:.
        for drive in "CDEFGH":
            candidates += [
                drive + r":\Program Files (x86)\World of Warcraft\_retail_\Logs",
                drive + r":\Program Files\World of Warcraft\_retail_\Logs",
                drive + r":\World of Warcraft\_retail_\Logs",
                drive + r":\Games\World of Warcraft\_retail_\Logs",
            ]
    candidates += [
        # macOS: the game is native there, and installs in /Applications.
        os.path.join(os.sep, "Applications", "World of Warcraft", "_retail_", "Logs"),
        os.path.join(home, "Games", "world-of-warcraft", retail),
        os.path.join(home, "Games", "battlenet", retail),
        os.path.join(home, ".wine", retail),
        os.path.join(home, "Applications", "World of Warcraft", "_retail_", "Logs"),
    ]
    for steam in (os.path.join(home, ".steam", "steam"),
                  os.path.join(home, ".local", "share", "Steam"),
                  os.path.join(home, ".var", "app", "com.valvesoftware.Steam",
                               ".local", "share", "Steam")):
        candidates += sorted(glob.glob(os.path.join(
            glob.escape(steam), "steamapps", "compatdata", "*", "pfx", retail)))
    candidates += sorted(glob.glob(os.path.join(
        glob.escape(home), ".var", "app", "com.usebottles.bottles", "data", "bottles",
        "bottles", "*", retail)))
    if os.name != "nt":
        candidates += _on_other_disks(retail, mount_roots)
    found = []
    for path in candidates:
        real = os.path.realpath(path)
        if os.path.isdir(path) and real not in (os.path.realpath(p) for p in found):
            found.append(path)
    return found


class Cancelled(Exception):
    """The reader asked to stop reading (the window's "Annuler")."""


def _build(path, year=None, verbose=True, pull_gap_ms=None, progress=None, cancelled=None):
    """Read and analyse a whole log: (log, segments, seconds).

    `progress(lines_read)` is called about four times a second and
    `cancelled()` as often; when it answers True the read stops with
    `Cancelled`. The terminal passes neither, the window both.
    """
    log = LogFile(path, default_year=year)
    if pull_gap_ms is None:
        factory = SegmentAnalysis
    else:
        def factory(segment):
            return SegmentAnalysis(segment, pull_gap_ms=pull_gap_ms)

    splitter = Splitter(analysis_factory=factory)
    started = time.time()
    last_report = last_tick = started
    for count, event in enumerate(log.events()):
        splitter.feed(event)
        if count % 4096:
            continue
        now = time.time()
        if now - last_tick > 0.25:
            last_tick = now
            if cancelled is not None and cancelled():
                raise Cancelled()
            if progress is not None:
                progress(log.line_count)
        if verbose and now - last_report > 3.0:
            last_report = now
            sys.stderr.write(
                _("\r  %s lignes lues...") % _count(log.line_count)
            )
            sys.stderr.flush()
    segments = splitter.finish()
    if verbose:
        sys.stderr.write("\r" + " " * 60 + "\r")
        sys.stderr.flush()
    return log, segments, time.time() - started


def read_log(args, verbose=True):
    """Read the log, or say in French why it could not be read.

    Returns (log, segments, elapsed) or None. Every failure a path can
    produce ends up here: a name that does not exist, a directory, a file
    the account cannot open, a disk error halfway through. They used to
    arrive as a Python traceback, which tells the reader nothing they can
    act on.
    """
    if not os.path.exists(args.log):
        sys.stderr.write(_("Fichier introuvable : %s\n") % args.log)
        return None
    if os.path.isdir(args.log):
        sys.stderr.write(
            _("%s est un dossier, pas un fichier de journal. "
              "Cherchez-y WoWCombatLog.txt.\n") % args.log
        )
        return None
    try:
        return _build(args.log, args.year, verbose, _pull_gap_ms(args))
    except OSError as error:
        sys.stderr.write(
            _("Impossible de lire %s : %s\n") % (args.log, error.strerror or error)
        )
        return None


def no_fight_message(path):
    """Why nothing was reported, without blaming an option nobody typed."""
    return (
        _("Aucun combat n'a été trouvé dans %s. Le fichier est peut-être vide, "
          "ou écrit par une version du client que ce lecteur ne comprend pas : "
          "`diagnose` dit ce qui a été lu.\n") % path
    )


def select_segments(segments, only):
    """Narrow a report to one fight, by number or by name.

    A raid night's full report is several megabytes; most of the time the
    question is about one pull.
    """
    if not only:
        return segments
    if only.isdigit():
        wanted = int(only)
        chosen = [segment for segment in segments if segment.index == wanted]
    else:
        needle = only.lower()
        chosen = [segment for segment in segments if needle in segment.label.lower()]
    return chosen


def _refuse_to_overwrite(out, log, force):
    """Why the report must not be written at `out`, or None.

    `report journal.txt -o journal.txt` wrote the report over the log it
    was made from, and that refusal can never be forced: a combat log
    cannot be recovered. The 2026-09-27 audit then found the same thing
    one step away -- `-o autre-journal.txt` turned *another* log into a
    web page and said "Rapport ecrit". Any existing file that is not a
    report of ours is now refused too, unless --force says it is meant.
    """
    if not os.path.exists(out):
        return None
    if os.path.samefile(out, log):
        return (_("Refus d'écrire le rapport par-dessus le journal lui-même (%s). "
                  "Choisissez un autre nom avec -o.\n") % out)
    if os.path.isdir(out):
        return _("%s est un dossier : donnez un nom de fichier avec -o.\n") % out
    if not force and not is_our_report(out):
        return (_("%s existe et n'est pas un rapport LogsWoW : refus de l'écraser. "
                  "Choisissez un autre nom, ou ajoutez --force si c'est voulu.\n") % out)
    return None


def _refuse_folder(folder, log, force):
    """Why a folder of pages must not be written at `folder`, or None.

    The same care as `_refuse_to_overwrite`, for the "pages" layout: a
    folder that exists must be empty, or hold a LogsWoW report already
    (its index.html says so); anything else is refused unless --force.
    The log being read is never touched either way.
    """
    if not os.path.exists(folder):
        return None
    if not os.path.isdir(folder):
        return (_("%s existe et n'est pas un dossier : donnez un autre nom avec -o.\n") % folder)
    if os.path.dirname(os.path.abspath(log)) == os.path.abspath(folder):
        return (_("Refus d'écrire les pages dans le dossier du journal lui-même (%s). "
                  "Donnez un autre dossier avec -o.\n") % folder)
    if force or not os.listdir(folder):
        return None
    if is_our_report(os.path.join(folder, "index.html")):
        return None
    return (_("%s contient déjà autre chose qu'un rapport LogsWoW : refus d'y écrire. "
              "Choisissez un autre dossier, ou ajoutez --force si c'est voulu.\n") % folder)


def default_output(log, layout):
    """Next to the log: a page under its name, or a folder under its name."""
    stem = os.path.splitext(log)[0]
    return stem if layout == "pages" else stem + ".html"


def _pull_gap_ms(args):
    seconds = getattr(args, "pull_gap", None)
    return None if seconds is None else int(seconds * 1000)


def command_report(args):
    """`report`: read, select, refuse a dangerous output, write the page."""
    read = read_log(args, not args.quiet)
    if read is None:
        return 2
    log, segments, elapsed = read
    if not segments:
        # Not the same thing as "--only matched nothing", and saying so
        # mattered: an empty file used to be reported as `--only None`.
        sys.stderr.write(no_fight_message(args.log))
        return 2
    chosen = select_segments(segments, args.only)
    if not chosen:
        sys.stderr.write(
            _("Aucun combat ne correspond à --only %r. Utilisez `list` pour les voir.\n")
            % args.only
        )
        return 2
    out = args.out or default_output(args.log, args.layout)
    if args.layout == "pages":
        refusal = _refuse_folder(out, args.log, args.force)
    else:
        refusal = _refuse_to_overwrite(out, args.log, args.force)
    if refusal:
        sys.stderr.write(refusal)
        return 2
    try:
        out = ReportWriter(log, chosen, out, wowhead=args.wowhead,
                           cast_order=not args.no_cast_order, layout=args.layout).write()
    except OSError as error:
        sys.stderr.write(_("Impossible d'écrire %s : %s\n") % (out, error.strerror or error))
        return 2
    if not args.quiet:
        print(_("%d combat(s) retenu(s) sur %d, %s lignes lues en %.1f s") % (
            len(chosen), len(segments),
            _count(log.line_count), elapsed))
        if log.problems.total:
            print(_("%d lignes non comprises -- lancez `diagnose` pour voir lesquelles")
                  % log.problems.total)
        print(_("Rapport écrit : %s") % out)
    return 0


def command_list(args):
    """`list`: one line per fight, numbered as `--only` expects."""
    read = read_log(args, not args.quiet)
    if read is None:
        return 2
    _log, segments, _elapsed = read
    if not segments:
        sys.stderr.write(no_fight_message(args.log))
        return 2
    print("%-4s %-46s %9s %10s %7s" % ("#", _("Combat"), _("Durée"), _("Dégâts"), _("Morts")))
    for segment in segments:
        analysis = segment.analysis
        print("%-4d %-46s %9s %10s %7d  %s" % (
            segment.index,
            segment.label[:46],
            format_duration(analysis.duration_ms),
            _count(analysis.total_damage),
            len(analysis.deaths),
            _(segment.outcome),
        ))
    return 0


def command_diagnose(args):
    """`diagnose`: what the reader understood of the file, and what it did not."""
    if not os.path.exists(args.log):
        sys.stderr.write(_("Fichier introuvable : %s\n") % args.log)
        return 2
    if os.path.isdir(args.log):
        sys.stderr.write(
            _("%s est un dossier, pas un fichier de journal. "
              "Cherchez-y WoWCombatLog.txt.\n") % args.log
        )
        return 2
    try:
        print(run_diagnose(args.log, default_year=args.year, limit=args.limit))
    except OSError as error:
        sys.stderr.write(
            _("Impossible de lire %s : %s\n") % (args.log, error.strerror or error)
        )
        return 2
    return 0


def command_where(_args):
    """`where`: the usual log folders on this machine, newest files first."""
    found = default_log_locations()
    if not found:
        print(_("Aucun dossier Logs trouvé aux emplacements habituels."))
        print(_("Cherchez WoWCombatLog.txt sous _retail_/Logs dans votre installation,"))
        print(_("puis donnez son chemin complet, entre guillemets s'il contient des espaces :"))
        print(_('  report "/chemin/vers/World of Warcraft/_retail_/Logs/WoWCombatLog-....txt"'))
        return 1
    for directory in found:
        print(directory)
        entries = []
        try:
            for name in os.listdir(directory):
                if not name.lower().endswith(".txt"):
                    continue
                full = os.path.join(directory, name)
                try:
                    entries.append((os.path.getmtime(full), os.path.getsize(full), name))
                except OSError:
                    continue
        except OSError:
            continue
        for _mtime, size, name in sorted(entries, reverse=True)[:10]:
            print("   %-44s %6.1f Mo" % (name, size / 1048576.0))
    return 0


def command_window(_args):
    """`fenetre`: the same three steps, in a window."""
    from . import gui

    code = gui.run()
    if code is None:
        sys.stderr.write(_("Pas d'écran disponible pour ouvrir la fenêtre : "
                           "utilisez les commandes (voir --help).\n"))
        return 2
    return code


def _seconds(text):
    """--pull-gap: a finite, non-negative number of seconds.

    `nan`, `inf` or `1e308` used to reach int() and come out as a Python
    traceback; argparse now says what is wrong, in French.
    """
    try:
        value = float(text)
    except ValueError:
        raise argparse.ArgumentTypeError(_("%r n'est pas un nombre de secondes") % text) from None
    if not math.isfinite(value) or value < 0 or value > 86400:
        raise argparse.ArgumentTypeError(
            _("%r : il faut un nombre de secondes entre 0 et 86400") % text)
    return value


def _positive(text):
    """--limit: a whole number above zero (-1 used to stop after one event)."""
    try:
        value = int(text)
    except ValueError:
        raise argparse.ArgumentTypeError(_("%r n'est pas un nombre entier") % text) from None
    if value < 1:
        raise argparse.ArgumentTypeError(_("%r : il faut un nombre supérieur à zéro") % text)
    return value


def language_option(parser):
    """--langue, accepted before the command and after it alike.

    It is read from the raw arguments before the parser exists
    (`requested_language`), so that the help itself comes out in the
    chosen language; declaring it here is what makes argparse accept it.
    """
    parser.add_argument(
        "--langue", "--lang", choices=("auto",) + LANGUAGES, default=argparse.SUPPRESS,
        help=_("langue de l'interface et du rapport : auto (celle du système, "
               "l'anglais pour une langue sans traduction), fr ou en"))


def requested_language(argv):
    """The value of --langue / --lang anywhere in `argv`, or 'auto'."""
    for index, token in enumerate(argv):
        for name in ("--langue", "--lang"):
            if token == name and index + 1 < len(argv):
                return argv[index + 1]
            if token.startswith(name + "="):
                return token.split("=", 1)[1]
    return "auto"


def _count(value):
    """25 361 906 in a French terminal, 25,361,906 in an English one."""
    text = "{:,}".format(value)
    return text.replace(",", " ") if language() == "fr" else text


def build_parser():
    """The command line, in the reader's language: five commands and their options."""
    parser = argparse.ArgumentParser(
        prog="logswow",
        description=_("Lit un journal de combat de World of Warcraft, en local, "
                      "sans rien envoyer nulle part."),
    )
    parser.add_argument("--version", action="version", version="LogsWoW " + __version__)
    language_option(parser)
    subparsers = parser.add_subparsers(dest="command")

    def common(subparser, analyses=True):
        """The options every command that reads a log shares.

        `diagnose` runs no analysis and prints nothing else, so it takes
        neither --pull-gap nor -q: it used to accept both and ignore them.
        """
        language_option(subparser)
        subparser.add_argument("log", help=_("chemin du fichier WoWCombatLog.txt"))
        subparser.add_argument("--year", type=int, default=None,
                               help=_("année, pour les journaux dont l'horodatage n'en porte pas"))
        if not analyses:
            return subparser
        subparser.add_argument("-q", "--quiet", action="store_true")
        subparser.add_argument(
            "--pull-gap",
            type=_seconds,
            default=None,
            metavar=_("SECONDES"),
            help=_("silence nécessaire pour séparer deux pulls (défaut 6 s) ; "
                   "baissez-le si vos packs sont regroupés, montez-le si un pull "
                   "unique est coupé en deux"),
        )
        return subparser

    report = common(subparsers.add_parser("report", help=_("produit le rapport HTML")))
    report.add_argument("-o", "--out", default=None, help=_("fichier de sortie (.html)"))
    report.add_argument(
        "--sans-sequence", dest="no_cast_order", action="store_true",
        help=_("ne pas mettre l'ordre des sorts de chaque joueur : la page est "
               "environ deux fois plus légère"))
    report.add_argument(
        "--format", dest="layout", choices=LAYOUTS, default="onglets",
        help=_("présentation du rapport : onglets (un fichier, un combat et une "
               "catégorie à la fois, par défaut), pages (un dossier, une page par "
               "combat) ou longue (tout sur une seule page)"))
    report.add_argument(
        "--force", action="store_true",
        help=_("écraser le fichier de sortie même s'il n'est pas un rapport LogsWoW "
               "(jamais le journal lu)"))
    report.add_argument(
        "--only",
        default=None,
        metavar=_("NUMÉRO|NOM"),
        help=_("n'inclure qu'un combat : son numéro dans `list`, ou un bout de son nom"),
    )
    report.add_argument(
        "--wowhead",
        default="auto",
        metavar=_("LANGUE"),
        help=_("langue des liens Wowhead : auto (celle du système), fr, en, de, es, "
               "it, pt, ru, ko, zh, ou off pour ne mettre aucun lien"),
    )
    report.set_defaults(func=command_report)

    listing = common(subparsers.add_parser("list", help=_("liste les combats du fichier")))
    listing.set_defaults(func=command_list)

    diagnose = common(subparsers.add_parser(
        "diagnose", help=_("montre ce que le lecteur a compris du fichier")), analyses=False)
    diagnose.add_argument("--limit", type=_positive, default=None,
                          help=_("s'arrêter après N événements"))
    diagnose.set_defaults(func=command_diagnose)

    where = subparsers.add_parser("where", help=_("cherche le dossier Logs du jeu"))
    language_option(where)
    where.set_defaults(func=command_where)

    window = subparsers.add_parser(
        "fenetre", help=_("ouvre la fenêtre (c'est aussi ce que fait la commande sans rien)"))
    language_option(window)
    window.set_defaults(func=command_window)
    return parser


def _prepare_console():
    """Let French names print on a Windows console that cannot encode them.

    A legacy cp1252 console raises UnicodeEncodeError on the first boss
    name with a character it lacks, and `list` would die on line one.
    Replacing the character beats crashing; the report file itself is
    always UTF-8 and unaffected.
    """
    for stream in (sys.stdout, sys.stderr):
        reconfigure = getattr(stream, "reconfigure", None)
        if reconfigure is not None:
            try:
                reconfigure(errors="replace")
            except (ValueError, OSError):
                pass


def main(argv=None):
    """Entry point: parse, run, and turn the ordinary interruptions into exit codes."""
    _prepare_console()
    choice = requested_language(sys.argv[1:] if argv is None else list(argv))
    set_language(choice if choice in ("auto",) + LANGUAGES else "auto")
    parser = build_parser()
    args = parser.parse_args(argv)
    if not getattr(args, "command", None):
        # Nothing typed -- which is also what a double-click on the .pyz
        # does. Open the window when there is a screen; otherwise, or when
        # the toolkit is missing, the help, as before.
        from . import gui

        code = gui.run() if argv is None else None
        if (code is None or code == 3) and sys.stdout is not None:
            parser.print_help()
        return 0
    try:
        return args.func(args)
    except BrokenPipeError:
        # `logswow list gros-journal.txt | head` closes the pipe early, and
        # that is an ordinary thing to do rather than an error. Python
        # flushes stdout again on exit, so it has to be redirected first or
        # the same failure is printed on the way out.
        try:
            os.dup2(os.open(os.devnull, os.O_WRONLY), sys.stdout.fileno())
        except OSError:
            pass
        return 0
    except KeyboardInterrupt:
        sys.stderr.write(_("\nInterrompu.\n"))
        return 130
