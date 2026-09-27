"""What the reader did and did not understand, before you trust a number.

This exists because of a rule this project has paid for twice already,
both times in the same way: a wrong field position does not raise, it
prints a confident wrong number. A fix that cannot be seen working is
not finished, and a tool that reports a total from a file it misread is
worse than one that refuses to report at all. So `diagnose` shows its work -- the layout
it measured, the evidence behind each choice, every subevent it met, and
every line it could not place.

Run it first on any log from a client version this package has not seen.
"""

from collections import Counter

from .events import BARE_EVENTS, SPECIAL_EVENTS, decompose
from .parse import LogFile
from .segment import Splitter
from .timestamps import format_duration


def _contradicts_itself(event):
    """A hostile unit written with more health than its own maximum.

    The same test the analysis applies before an enemy's health may vote
    for a curve, so the count printed here is what the curves left out.
    A player's reading is not counted: a player's health is only ever
    clamped, never left out.
    """
    advanced = event.advanced
    if advanced is None or not 0 < advanced.max_hp < advanced.current_hp:
        return False
    info = advanced.info_guid
    actor = event.dest if info == event.dest.guid else (
        event.source if info == event.source.guid else None)
    return (actor is not None and actor.is_hostile
            and not actor.is_player and not actor.is_pet)


class _Reading:
    """What one pass over the file collected, for the sections below."""

    def __init__(self, path, default_year, limit):
        self.log = LogFile(path, default_year=default_year)
        splitter = Splitter()
        self.subevents = Counter()
        self.unresolved = Counter()
        self.shapes = {}
        self.advanced_seen = Counter()
        self.players = set()
        self.inconsistent_health = 0
        for index, event in enumerate(self.log.events()):
            if limit and index >= limit:
                break
            self.subevents[event.subevent] += 1
            splitter.feed(event)
            if event.source.is_player:
                self.players.add(event.source.name)
            if event.subevent not in SPECIAL_EVENTS:
                self.shapes.setdefault(event.subevent, Counter())[len(event.fields)] += 1
                self.advanced_seen[bool(event.advanced)] += 1
            if _contradicts_itself(event):
                self.inconsistent_health += 1
            if event.mismatch:
                self.unresolved[(event.subevent, event.mismatch)] += 1
        self.segments = splitter.finish()


def run(path, default_year=None, limit=None):
    """The whole diagnosis of one file, as the text `diagnose` prints."""
    reading = _Reading(path, default_year, limit)
    log = reading.log
    lines = [
        "Fichier    : %s" % path,
        "Taille     : %.1f Mo, %d lignes, %d evenements" % (
            log.size_bytes / 1048576.0, log.line_count, log.event_count),
        "Duree      : %s" % format_duration(log.duration_ms),
        "",
    ]
    lines += _layout_section(reading)
    lines += _segments_section(reading)
    lines += _events_section(reading)
    lines += _problems_section(reading)
    return "\n".join(lines)


def _layout_section(reading):
    layout = reading.log.layout
    evidence = layout.evidence
    lines = ["DISPOSITION MESUREE DANS CE FICHIER"]
    lines.append("  bloc avance         : %d champs  (votes: %s)" % (
        layout.advanced_width, evidence.get("advanced_width", {})))
    if evidence.get("advanced_width_tiebreak"):
        lines.append("    votes a egalite, departage par : %s"
                     % evidence["advanced_width_tiebreak"])
    lines.append("  champ baseAmount    : %s  (position du -1: %s)" % (
        "present" if layout.has_base_amount else "absent",
        evidence.get("overkill_position", {})))
    lines.append("  champ hideCaster    : %s  (%s)" % (
        "present" if layout.hide_caster else "absent", evidence.get("hide_caster", {})))
    lines.append("  journalisation avancee : %s" % (
        "oui" if evidence.get("advanced_logging")
        else "non -- positions et points de vie absents"))
    lines.append("  evenements avec bloc avance : %d sur %d" % (
        reading.advanced_seen.get(True, 0), sum(reading.advanced_seen.values()) or 1))
    # A unit written with more health than its own maximum: the file
    # contradicts itself, and the enemy health curves leave it out.
    lines.append("  points de vie incoherents   : %d (courants > maximum ; ignores "
                 "pour les courbes de vie ennemies)" % reading.inconsistent_health)
    lines.append("")
    return lines


def _segments_section(reading):
    lines = ["COMBATS DELIMITES : %d" % len(reading.segments)]
    for segment in reading.segments:
        lines.append("  [%2d] %-46s %8s  %s" % (
            segment.index, segment.label[:46], format_duration(segment.duration_ms),
            segment.outcome or ""))
    lines += ["", "JOUEURS VUS : %d" % len(reading.players), ""]
    return lines


def _events_section(reading):
    lines = ["EVENEMENTS (%d types)" % len(reading.subevents)]
    for subevent, count in reading.subevents.most_common():
        known = (
            subevent in SPECIAL_EVENTS
            or subevent in BARE_EVENTS
            or decompose(subevent) is not None
        )
        widths = dict(reading.shapes.get(subevent, {}))
        lines.append("  %-34s %8d  %s%s" % (
            subevent, count, "" if known else "[SCHEMA INCONNU] ",
            widths if len(widths) > 1 else ""))
    lines.append("")
    if reading.unresolved:
        lines.append("LIGNES NON RESOLUES")
        for (subevent, reason), count in reading.unresolved.most_common(20):
            lines.append("  %-34s %6d  %s" % (subevent, count, reason))
    else:
        lines.append("LIGNES NON RESOLUES : aucune")
    lines.append("")
    return lines


def _problems_section(reading):
    problems = reading.log.problems
    # One line, one reason: the breakdown below is the whole ledger. The
    # two commonest reasons used to be printed again above it, which read
    # as two separate problems for one bad line.
    lines = ["PROBLEMES DE LECTURE : %d" % problems.total]
    for reason, count in sorted(problems.by_reason.items(), key=lambda item: -item[1])[:10]:
        lines.append("  %-50s %d" % (reason, count))
    for line_number, reason, text in problems.samples[:8]:
        lines.append("    ligne %s : %s | %s" % (line_number, reason, text[:90]))
    return lines
