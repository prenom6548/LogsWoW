# SPDX-License-Identifier: AGPL-3.0-or-later
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
from .i18n import _
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
        _("Fichier    : %s") % path,
        _("Taille     : %.1f Mo, %d lignes, %d événements") % (
            log.size_bytes / 1048576.0, log.line_count, log.event_count),
        _("Durée      : %s") % format_duration(log.duration_ms),
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
    lines = [_("DISPOSITION MESURÉE DANS CE FICHIER")]
    lines.append(_("  bloc avancé         : %d champs  (votes: %s)") % (
        layout.advanced_width, evidence.get("advanced_width", {})))
    if evidence.get("advanced_width_tiebreak"):
        lines.append(_("    votes à égalité, départage par : %s")
                     % evidence["advanced_width_tiebreak"])
    lines.append(_("  champ baseAmount    : %s  (position du -1: %s)") % (
        _("présent") if layout.has_base_amount else "absent",
        evidence.get("overkill_position", {})))
    lines.append(_("  champ hideCaster    : %s  (%s)") % (
        _("présent") if layout.hide_caster else "absent", evidence.get("hide_caster", {})))
    lines.append(_("  journalisation avancée : %s") % (
        _("oui") if evidence.get("advanced_logging")
        else _("non -- positions et points de vie absents")))
    lines.append(_("  événements avec bloc avancé : %d sur %d") % (
        reading.advanced_seen.get(True, 0), sum(reading.advanced_seen.values()) or 1))
    # A unit written with more health than its own maximum: the file
    # contradicts itself, and the enemy health curves leave it out.
    lines.append(_("  points de vie incohérents   : %d (courants > maximum ; ignorés "
                   "pour les courbes de vie ennemies)") % reading.inconsistent_health)
    lines.append("")
    return lines


def _segments_section(reading):
    lines = [_("COMBATS DÉLIMITÉS : %d") % len(reading.segments)]
    for segment in reading.segments:
        lines.append("  [%2d] %-46s %8s  %s" % (
            segment.index, segment.label[:46], format_duration(segment.duration_ms),
            _(segment.outcome or "")))
    lines += ["", _("JOUEURS VUS : %d") % len(reading.players), ""]
    return lines


def _events_section(reading):
    lines = [_("ÉVÉNEMENTS (%d types)") % len(reading.subevents)]
    for subevent, count in reading.subevents.most_common():
        known = (
            subevent in SPECIAL_EVENTS
            or subevent in BARE_EVENTS
            or decompose(subevent) is not None
        )
        widths = dict(reading.shapes.get(subevent, {}))
        lines.append("  %-34s %8d  %s%s" % (
            subevent, count, "" if known else _("[SCHÉMA INCONNU] "),
            widths if len(widths) > 1 else ""))
    lines.append("")
    if reading.unresolved:
        lines.append(_("LIGNES NON RÉSOLUES"))
        for (subevent, reason), count in reading.unresolved.most_common(20):
            lines.append("  %-34s %6d  %s" % (subevent, count, _(reason)))
    else:
        lines.append(_("LIGNES NON RÉSOLUES : aucune"))
    lines.append("")
    return lines


def _problems_section(reading):
    problems = reading.log.problems
    # One line, one reason: the breakdown below is the whole ledger. The
    # two commonest reasons used to be printed again above it, which read
    # as two separate problems for one bad line.
    lines = [_("PROBLÈMES DE LECTURE : %d") % problems.total]
    for reason, count in sorted(problems.by_reason.items(), key=lambda item: -item[1])[:10]:
        lines.append("  %-50s %d" % (_(reason), count))
    for line_number, reason, text in problems.samples[:8]:
        lines.append(_("    ligne %s : %s | %s") % (line_number, _(reason), text[:90]))
    return lines
