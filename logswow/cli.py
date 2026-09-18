"""`python3 -m logswow` -- the whole tool, from one command.

Deliberately dependency-free and deliberately offline: nothing here
opens a socket, and there is no configuration file, no cache directory
and no account. Point it at a log, get an HTML page next to it.
"""

import argparse
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
    """Where the client usually writes, on each system it runs on."""
    candidates = [
        r"C:\Program Files (x86)\World of Warcraft\_retail_\Logs",
        r"C:\Program Files\World of Warcraft\_retail_\Logs",
        os.path.expanduser("~/Games/world-of-warcraft/drive_c/Program Files (x86)"
                           "/World of Warcraft/_retail_/Logs"),
        os.path.expanduser("~/.wine/drive_c/Program Files (x86)/World of Warcraft"
                           "/_retail_/Logs"),
        os.path.expanduser("~/Applications/World of Warcraft/_retail_/Logs"),
    ]
    return [path for path in candidates if os.path.isdir(path)]


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


def _pull_gap_ms(args):
    seconds = getattr(args, "pull_gap", None)
    return None if seconds is None else int(seconds * 1000)


def command_report(args):
    if not os.path.exists(args.log):
        sys.stderr.write("Fichier introuvable : %s\n" % args.log)
        return 2
    log, segments, elapsed = _build(
        args.log, args.year, not args.quiet, _pull_gap_ms(args)
    )
    chosen = select_segments(segments, args.only)
    if not chosen:
        sys.stderr.write(
            "Aucun combat ne correspond a --only %r. Utilisez `list` pour les voir.\n"
            % args.only
        )
        return 2
    out = args.out or os.path.splitext(args.log)[0] + ".html"
    ReportWriter(log, chosen, out, wowhead=args.wowhead).write()
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
    if not os.path.exists(args.log):
        sys.stderr.write("Fichier introuvable : %s\n" % args.log)
        return 2
    log, segments, _elapsed = _build(
        args.log, args.year, not args.quiet, _pull_gap_ms(args)
    )
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
    print(run_diagnose(args.log, default_year=args.year, limit=args.limit))
    return 0


def command_where(_args):
    found = default_log_locations()
    if not found:
        print("Aucun dossier Logs trouve aux emplacements habituels.")
        print("Cherchez WoWCombatLog.txt sous _retail_/Logs dans votre installation.")
        return 1
    for directory in found:
        print(directory)
        try:
            names = sorted(
                (name for name in os.listdir(directory) if name.lower().endswith(".txt")),
                key=lambda name: os.path.getmtime(os.path.join(directory, name)),
                reverse=True,
            )
        except OSError:
            continue
        for name in names[:10]:
            full = os.path.join(directory, name)
            print("   %-44s %6.1f Mo" % (name, os.path.getsize(full) / 1048576.0))
    return 0


def build_parser():
    parser = argparse.ArgumentParser(
        prog="logswow",
        description="Lit un journal de combat de World of Warcraft, en local, "
                    "sans rien envoyer nulle part.",
    )
    parser.add_argument("--version", action="version", version="LogsWoW " + __version__)
    subparsers = parser.add_subparsers(dest="command")

    def common(subparser):
        subparser.add_argument("log", help="chemin du fichier WoWCombatLog.txt")
        subparser.add_argument("--year", type=int, default=None,
                               help="annee, pour les journaux dont l'horodatage n'en porte pas")
        subparser.add_argument("-q", "--quiet", action="store_true")
        subparser.add_argument(
            "--pull-gap",
            type=float,
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
        "diagnose", help="montre ce que le lecteur a compris du fichier"))
    diagnose.add_argument("--limit", type=int, default=None,
                          help="s'arreter apres N evenements")
    diagnose.set_defaults(func=command_diagnose)

    where = subparsers.add_parser("where", help="cherche le dossier Logs du jeu")
    where.set_defaults(func=command_where)
    return parser


def main(argv=None):
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
