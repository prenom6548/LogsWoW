"""What the reader did and did not understand, before you trust a number.

This exists because of a rule this project's sibling repository paid for
several times over: a fix that cannot be seen working is not finished,
and a tool that reports a confident number from a file it misread is
worse than one that refuses. So `diagnose` shows its work -- the layout
it measured, the evidence behind each choice, every subevent it met, and
every line it could not place.

Run it first on any log from a client version this package has not seen.
"""

from collections import Counter

from .events import BARE_EVENTS, SPECIAL_EVENTS, decompose
from .parse import LogFile
from .segment import Splitter
from .timestamps import format_duration


def run(path, default_year=None, limit=None):
    log = LogFile(path, default_year=default_year)
    splitter = Splitter()
    subevents = Counter()
    unresolved = Counter()
    shapes = {}
    advanced_seen = Counter()
    players = set()

    for index, event in enumerate(log.events()):
        if limit and index >= limit:
            break
        subevents[event.subevent] += 1
        splitter.feed(event)
        if event.source.is_player:
            players.add(event.source.name)
        if event.subevent not in SPECIAL_EVENTS:
            shapes.setdefault(event.subevent, Counter())[len(event.fields)] += 1
            advanced_seen[bool(event.advanced)] += 1
        if event.mismatch:
            unresolved[(event.subevent, event.mismatch)] += 1
    segments = splitter.finish()

    lines = []
    add = lines.append
    add("Fichier    : %s" % path)
    add("Taille     : %.1f Mo, %d lignes, %d evenements" % (
        log.size_bytes / 1048576.0, log.line_count, log.event_count))
    add("Duree      : %s" % format_duration(log.duration_ms))
    add("")
    add("DISPOSITION MESUREE DANS CE FICHIER")
    layout = log.layout
    evidence = layout.evidence
    add("  bloc avance         : %d champs  (votes: %s)" % (
        layout.advanced_width, evidence.get("advanced_width", {})))
    add("  degats bruts        : %s  (position du -1: %s)" % (
        "present" if layout.has_base_amount else "absent",
        evidence.get("overkill_position", {})))
    add("  champ hideCaster    : %s  (%s)" % (
        "present" if layout.hide_caster else "absent", evidence.get("hide_caster", {})))
    add("  journalisation avancee : %s" % (
        "oui" if evidence.get("advanced_logging") else "non -- positions et points de vie absents"))
    add("  evenements avec bloc avance : %d sur %d" % (
        advanced_seen.get(True, 0), sum(advanced_seen.values()) or 1))
    add("")
    add("COMBATS DELIMITES : %d" % len(segments))
    for segment in segments:
        add("  [%2d] %-46s %8s  %s" % (
            segment.index, segment.label[:46], format_duration(segment.duration_ms),
            segment.outcome or ""))
    add("")
    add("JOUEURS VUS : %d" % len(players))
    add("")
    add("EVENEMENTS (%d types)" % len(subevents))
    for subevent, count in subevents.most_common():
        known = (
            subevent in SPECIAL_EVENTS
            or subevent in BARE_EVENTS
            or decompose(subevent) is not None
        )
        widths = dict(shapes.get(subevent, {}))
        add("  %-34s %8d  %s%s" % (
            subevent, count, "" if known else "[SCHEMA INCONNU] ",
            widths if len(widths) > 1 else ""))
    add("")
    if unresolved:
        add("LIGNES NON RESOLUES")
        for (subevent, reason), count in unresolved.most_common(20):
            add("  %-34s %6d  %s" % (subevent, count, reason))
    else:
        add("LIGNES NON RESOLUES : aucune")
    add("")
    problems = log.problems
    add("PROBLEMES DE LECTURE : %d" % problems.total)
    if problems.unsplittable:
        add("  lignes sans separateur : %d" % problems.unsplittable)
    if problems.bad_timestamp:
        add("  horodatages illisibles : %d" % problems.bad_timestamp)
    for reason, count in sorted(problems.by_reason.items(), key=lambda item: -item[1])[:10]:
        add("  %-50s %d" % (reason, count))
    for line_number, reason, text in problems.samples[:8]:
        add("    ligne %s : %s | %s" % (line_number, reason, text[:90]))
    return "\n".join(lines)
