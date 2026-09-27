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
from .parse import LogFile
from .report import ReportWriter
from .segment import Splitter
from .timestamps import format_duration


def default_log_locations():
    """Where the client usually writes, on each system it runs on.

    On Linux the game runs through a Windows compatibility layer, and each
    launcher keeps its own copy of drive C: Lutris under ~/Games, Steam
    (Battle.net added as a non-Steam game) under a numbered compatdata
    prefix, Bottles under its own data folder. The numbered ones are
    found by pattern rather than guessed.
    """
    retail = os.path.join("drive_c", "Program Files (x86)", "World of Warcraft",
                          "_retail_", "Logs")
    home = os.path.expanduser("~")
    candidates = [
        r"C:\Program Files (x86)\World of Warcraft\_retail_\Logs",
        r"C:\Program Files\World of Warcraft\_retail_\Logs",
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
    found = []
    for path in candidates:
        real = os.path.realpath(path)
        if os.path.isdir(path) and real not in (os.path.realpath(p) for p in found):
            found.append(path)
    return found


def _build(path, year=None, verbose=True, pull_gap_ms=None):
    log = LogFile(path, default_year=year)
    if pull_gap_ms is None:
        factory = SegmentAnalysis
    else:
        def factory(segment):
            return SegmentAnalysis(segment, pull_gap_ms=pull_gap_ms)

    splitter = Splitter(analysis_factory=factory)
    started = time.time()
    last_report = started
    for event in log.events():
        splitter.feed(event)
        if verbose and time.time() - last_report > 3.0:
            last_report = time.time()
            sys.stderr.write(
                "\r  %s lignes lues..." % "{:,}".format(log.line_count).replace(",", " ")
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
        sys.stderr.write("Fichier introuvable : %s\n" % args.log)
        return None
    if os.path.isdir(args.log):
        sys.stderr.write(
            "%s est un dossier, pas un fichier de journal. "
            "Cherchez-y WoWCombatLog.txt.\n" % args.log
        )
        return None
    try:
        return _build(args.log, args.year, verbose, _pull_gap_ms(args))
    except OSError as error:
        sys.stderr.write(
            "Impossible de lire %s : %s\n" % (args.log, error.strerror or error)
        )
        return None


def no_fight_message(path):
    return (
        "Aucun combat n'a ete trouve dans %s. Le fichier est peut-etre vide, "
        "ou ecrit par une version du client que ce lecteur ne comprend pas : "
        "`diagnose` dit ce qui a ete lu.\n" % path
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


def _is_our_report(path):
    """True when the file at `path` is a page this program wrote."""
    try:
        with open(path, "rb") as handle:
            head = handle.read(512)
    except OSError:
        return False
    return head.startswith(b"<!doctype html>") and b"<title>LogsWoW" in head


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
        return ("Refus d'ecrire le rapport par-dessus le journal lui-meme (%s). "
                "Choisissez un autre nom avec -o.\n" % out)
    if os.path.isdir(out):
        return "%s est un dossier : donnez un nom de fichier avec -o.\n" % out
    if not force and not _is_our_report(out):
        return ("%s existe et n'est pas un rapport LogsWoW : refus de l'ecraser. "
                "Choisissez un autre nom, ou ajoutez --force si c'est voulu.\n" % out)
    return None


def _pull_gap_ms(args):
    seconds = getattr(args, "pull_gap", None)
    return None if seconds is None else int(seconds * 1000)


def command_report(args):
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
            "Aucun combat ne correspond a --only %r. Utilisez `list` pour les voir.\n"
            % args.only
        )
        return 2
    out = args.out or os.path.splitext(args.log)[0] + ".html"
    refusal = _refuse_to_overwrite(out, args.log, args.force)
    if refusal:
        sys.stderr.write(refusal)
        return 2
    try:
        ReportWriter(log, chosen, out, wowhead=args.wowhead).write()
    except OSError as error:
        sys.stderr.write("Impossible d'ecrire %s : %s\n" % (out, error.strerror or error))
        return 2
    if not args.quiet:
        print("%d combat(s) retenu(s) sur %d, %s lignes lues en %.1f s" % (
            len(chosen), len(segments),
            "{:,}".format(log.line_count).replace(",", " "), elapsed))
        if log.problems.total:
            print("%d lignes non comprises -- lancez `diagnose` pour voir lesquelles"
                  % log.problems.total)
        print("Rapport ecrit : %s" % out)
    return 0


def command_list(args):
    read = read_log(args, not args.quiet)
    if read is None:
        return 2
    _log, segments, _elapsed = read
    if not segments:
        sys.stderr.write(no_fight_message(args.log))
        return 2
    print("%-4s %-46s %9s %10s %7s" % ("#", "Combat", "Duree", "Degats", "Morts"))
    for segment in segments:
        analysis = segment.analysis
        print("%-4d %-46s %9s %10s %7d  %s" % (
            segment.index,
            segment.label[:46],
            format_duration(analysis.duration_ms),
            "{:,}".format(analysis.total_damage).replace(",", " "),
            len(analysis.deaths),
            segment.outcome,
        ))
    return 0


def command_diagnose(args):
    if not os.path.exists(args.log):
        sys.stderr.write("Fichier introuvable : %s\n" % args.log)
        return 2
    if os.path.isdir(args.log):
        sys.stderr.write(
            "%s est un dossier, pas un fichier de journal. "
            "Cherchez-y WoWCombatLog.txt.\n" % args.log
        )
        return 2
    try:
        print(run_diagnose(args.log, default_year=args.year, limit=args.limit))
    except OSError as error:
        sys.stderr.write(
            "Impossible de lire %s : %s\n" % (args.log, error.strerror or error)
        )
        return 2
    return 0


def command_where(_args):
    found = default_log_locations()
    if not found:
        print("Aucun dossier Logs trouve aux emplacements habituels.")
        print("Cherchez WoWCombatLog.txt sous _retail_/Logs dans votre installation.")
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


def _seconds(text):
    """--pull-gap: a finite, non-negative number of seconds.

    `nan`, `inf` or `1e308` used to reach int() and come out as a Python
    traceback; argparse now says what is wrong, in French.
    """
    try:
        value = float(text)
    except ValueError:
        raise argparse.ArgumentTypeError("%r n'est pas un nombre de secondes" % text)
    if not math.isfinite(value) or value < 0 or value > 86400:
        raise argparse.ArgumentTypeError(
            "%r : il faut un nombre de secondes entre 0 et 86400" % text)
    return value


def _positive(text):
    """--limit: a whole number above zero (-1 used to stop after one event)."""
    try:
        value = int(text)
    except ValueError:
        raise argparse.ArgumentTypeError("%r n'est pas un nombre entier" % text)
    if value < 1:
        raise argparse.ArgumentTypeError("%r : il faut un nombre superieur a zero" % text)
    return value


def build_parser():
    parser = argparse.ArgumentParser(
        prog="logswow",
        description="Lit un journal de combat de World of Warcraft, en local, "
                    "sans rien envoyer nulle part.",
    )
    parser.add_argument("--version", action="version", version="LogsWoW " + __version__)
    subparsers = parser.add_subparsers(dest="command")

    def common(subparser, analyses=True):
        """The options every command that reads a log shares.

        `diagnose` runs no analysis and prints nothing else, so it takes
        neither --pull-gap nor -q: it used to accept both and ignore them.
        """
        subparser.add_argument("log", help="chemin du fichier WoWCombatLog.txt")
        subparser.add_argument("--year", type=int, default=None,
                               help="annee, pour les journaux dont l'horodatage n'en porte pas")
        if not analyses:
            return subparser
        subparser.add_argument("-q", "--quiet", action="store_true")
        subparser.add_argument(
            "--pull-gap",
            type=_seconds,
            default=None,
            metavar="SECONDES",
            help="silence necessaire pour separer deux pulls (defaut 6 s) ; "
                 "baissez-le si vos packs sont regroupes, montez-le si un pull "
                 "unique est coupe en deux",
        )
        return subparser

    report = common(subparsers.add_parser("report", help="produit le rapport HTML"))
    report.add_argument("-o", "--out", default=None, help="fichier de sortie (.html)")
    report.add_argument(
        "--force", action="store_true",
        help="ecraser le fichier de sortie meme s'il n'est pas un rapport LogsWoW "
             "(jamais le journal lu)")
    report.add_argument(
        "--only",
        default=None,
        metavar="NUMERO|NOM",
        help="n'inclure qu'un combat : son numero dans `list`, ou un bout de son nom",
    )
    report.add_argument(
        "--wowhead",
        default="auto",
        metavar="LANGUE",
        help="langue des liens Wowhead : auto (celle du systeme), fr, en, de, es, "
             "it, pt, ru, ko, zh, ou off pour ne mettre aucun lien",
    )
    report.set_defaults(func=command_report)

    listing = common(subparsers.add_parser("list", help="liste les combats du fichier"))
    listing.set_defaults(func=command_list)

    diagnose = common(subparsers.add_parser(
        "diagnose", help="montre ce que le lecteur a compris du fichier"), analyses=False)
    diagnose.add_argument("--limit", type=_positive, default=None,
                          help="s'arreter apres N evenements")
    diagnose.set_defaults(func=command_diagnose)

    where = subparsers.add_parser("where", help="cherche le dossier Logs du jeu")
    where.set_defaults(func=command_where)
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
    _prepare_console()
    parser = build_parser()
    args = parser.parse_args(argv)
    if not getattr(args, "command", None):
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
        sys.stderr.write("\nInterrompu.\n")
        return 130
