# SPDX-License-Identifier: AGPL-3.0-or-later
"""What the window shows before a page is written, and the numbers the report's comparison uses.

No widget and no HTML here: plain data, then plain text. The window and the page read the
same functions, so a figure on one is the figure on the other.

Three rates, kept apart on purpose:

- **dégâts/s**: the player's damage dealt over the fight's length.
- **soins/s**: effective healing *plus* the damage their shields absorbed, over the same
  length. The sites call that sum "healing", and the report already shows it (column
  "Somme"); a shield is not a heal in the file, so the two are added here and said so.
- **subis/s**: damage taken *plus* the part a shield absorbed, over the same length: what
  came in, before the shields. It is the figure that matters for a tank, so it is only
  given to tanks.
"""

from .i18n import _
from . import fmt
from .specs import DPS, HEAL, TANK, label_of, role_of
from .timestamps import format_duration

ROLE_ORDER = (TANK, HEAL, DPS, "")
# A key the comparison may line up: completed, whatever the verdict on its timer.
COMPARABLE = ("dans les temps", "hors des temps", "terminée")


def seconds_of(analysis):
    return max(1.0, analysis.duration_ms / 1000.0)


def rates(analysis, player):
    """{'dps', 'hps', 'taken'}: per second, over the fight's length (see the module note)."""
    seconds = seconds_of(analysis)
    return {
        "dps": player.damage_done / seconds,
        "hps": (player.healing_done + player.absorb_done) / seconds,
        "taken": (player.damage_taken + player.absorbed_taken) / seconds,
    }


def group_rates(analysis):
    seconds = seconds_of(analysis)
    shields = sum(player.absorb_done for player in analysis.players.values())
    return {
        "dps": analysis.total_damage / seconds,
        "hps": (analysis.total_healing + shields) / seconds,
        "taken": sum(player.damage_taken + player.absorbed_taken
                     for player in analysis.players.values()) / seconds,
    }


def role_groups(analysis):
    """[(role, [players])] of the people who took part, tanks first, each group by name."""
    groups = {role: [] for role in ROLE_ORDER}
    for player in analysis.participants():
        groups.setdefault(role_of(player.spec_id), []).append(player)
    for players in groups.values():
        players.sort(key=lambda player: player.short_name.lower())
    return [(role, groups[role]) for role in ROLE_ORDER if groups[role]]


def role_label(role):
    return {TANK: _("Tanks"), HEAL: _("Soigneurs"), DPS: "DPS", "": _("Rôle non indiqué")}[role]


def average_ilvl(players):
    """The mean of the players' equipped item levels, or None when nobody's is known."""
    levels = [player.gear.average for player in players if player.gear is not None]
    return sum(levels) / len(levels) if levels else None


def ilvl_text(value):
    return fmt.decimal(round(value, 1)) if value is not None else "?"


# -- one fight -------------------------------------------------------------------

def fight_preview(segment):
    """The words for one fight: totals, deaths, and a line per player."""
    analysis = segment.analysis
    seconds = seconds_of(analysis)
    outcome = _(segment.outcome) if segment.outcome else ""
    group = group_rates(analysis)
    lines = [
        _("%s — %s (%s)") % (segment.label, outcome or "?", format_duration(analysis.duration_ms)),
        _("Dégâts %s (%s/s) · Soins %s (%s/s, boucliers compris) · Subis %s · %s") % (
            fmt.compact(analysis.total_damage), fmt.compact(group["dps"]),
            fmt.compact(group["hps"] * seconds), fmt.compact(group["hps"]),
            fmt.compact(group["taken"] * seconds), fmt.plural(len(analysis.deaths), "mort"))]
    groups = role_groups(analysis)
    ilvl = average_ilvl([player for _role, players in groups for player in players])
    if ilvl is not None:
        lines.append(_("Niveau d'objet moyen du groupe : %s") % ilvl_text(ilvl))
    fought = [(label, success) for label, _start, _end, success, fought in analysis.encounters
              if fought]
    if fought:
        lines.append(_("Boss : %s") % ", ".join(
            "%s (%s)" % (label, _("réussite") if success else
                         _("échec") if success is False else _("sans résultat"))
            for label, success in fought))
    if analysis.deaths:
        lines.append("")
        lines.append(_("Morts :"))
        start = analysis.first_ts or 0
        for death in analysis.deaths:
            lines.append(_("  %s à %s : %s") % (
                death["player"], format_duration(death["ts"] - start),
                death["killing_blow"] or _("cause non écrite dans le journal")))
    for role, players in groups:
        lines.append("")
        lines.append(role_label(role))
        for player in players:
            lines.append(player_line(analysis, player, role))
    return "\n".join(lines)


def player_line(analysis, player, role):
    """One player: spec, the rates (subis/s for a tank only), deaths, item level."""
    rate = rates(analysis, player)
    pieces = [_("%s dégâts/s") % fmt.compact(rate["dps"]),
              _("%s soins/s") % fmt.compact(rate["hps"])]
    if role == TANK:
        pieces.append(_("%s subis/s") % fmt.compact(rate["taken"]))
    pieces.append(fmt.plural(player.deaths, "mort"))
    if player.gear is not None:
        pieces.append(_("ilvl %s") % ilvl_text(player.gear.average))
    spec = label_of(player.spec_id) or "?"
    return "  %s (%s) : %s" % (player.short_name, spec, " · ".join(pieces))


# -- keys side by side -------------------------------------------------------------

def comparable_keys(segments):
    return [segment for segment in segments
            if segment.kind == "keystone" and segment.outcome in COMPARABLE]


def comparison(segments):
    """The keys of `segments` lined up: [{'title', 'runs', 'players'}], per dungeon and level.

    Every finished key appears in a group of its own level; a group with two keys or more also
    carries a table per player (`players`), with a change from the first run to the last. A key
    that was abandoned or is still open is not comparable and is left out, and so is a +13 beside
    a +12: they would make the columns say something they do not.
    """
    groups = {}
    for segment in comparable_keys(segments):
        groups.setdefault(segment.label, []).append(segment)
    out = []
    for title, runs in groups.items():
        entry = {"title": title, "runs": [_run(segment) for segment in runs], "players": []}
        if len(runs) > 1:
            entry["players"] = _player_rows(runs)
        out.append(entry)
    return out


def _run(segment):
    analysis = segment.analysis
    rate = group_rates(analysis)
    return {"index": segment.index, "duration": analysis.duration_ms,
            "outcome": segment.outcome, "deaths": len(analysis.deaths),
            "dps": rate["dps"], "hps": rate["hps"], "taken": rate["taken"],
            "ilvl": average_ilvl(analysis.participants())}


def _player_rows(runs):
    """[{'name', 'spec', 'role', 'rows': [(metric key, [value or None per run], change)]}]."""
    by_guid, order = {}, []
    for position, segment in enumerate(runs):
        analysis = segment.analysis
        for role, players in role_groups(analysis):
            for player in players:
                entry = by_guid.get(player.guid)
                if entry is None:
                    entry = by_guid[player.guid] = {
                        "name": player.short_name, "spec": label_of(player.spec_id) or "?",
                        "role": role, "per_run": [None] * len(runs)}
                    order.append(player.guid)
                entry["per_run"][position] = (rates(analysis, player), player.deaths, player.gear)
                if role == TANK:
                    entry["role"] = TANK        # a tank in any run gets the tank's figures
    rows = []
    for guid in sorted(order, key=lambda g: (ROLE_ORDER.index(by_guid[g]["role"]),
                                             by_guid[g]["name"].lower())):
        entry = by_guid[guid]
        metrics = ["dps", "hps"] + (["taken"] if entry["role"] == TANK else [])
        lines = []
        for key in metrics:
            values = [cell[0][key] if cell else None for cell in entry["per_run"]]
            lines.append((key, values, change(values)))
        deaths = [cell[1] if cell else None for cell in entry["per_run"]]
        lines.append(("deaths", deaths, None))
        ilvl = [cell[2].average if cell and cell[2] is not None else None
                for cell in entry["per_run"]]
        if any(value is not None for value in ilvl):
            lines.append(("ilvl", ilvl, None))
        rows.append({"name": entry["name"], "spec": entry["spec"], "role": entry["role"],
                     "rows": lines})
    return rows


def change(values):
    """Last run against the first, as a fraction (None when either is missing or zero)."""
    present = [value for value in values if value is not None]
    if len(present) < 2 or not present[0]:
        return None
    return (present[-1] - present[0]) / present[0]


def change_text(value):
    if value is None:
        return ""
    text = fmt.percent(abs(value))
    if text == fmt.percent(0):
        return text             # "−0 %" says a direction the rounding has erased
    return ("+" if value > 0 else "−") + text


def metric_label(key):
    return {"dps": _("Dégâts/s"), "hps": _("Soins/s"), "taken": _("Subis/s"),
            "deaths": _("Morts"), "ilvl": "ilvl"}[key]


def metric_text(key, value):
    if value is None:
        return "—"
    if key == "deaths":
        return str(value)
    if key == "ilvl":
        return ilvl_text(value)
    return fmt.compact(value)


def comparison_text(groups):
    """The comparison as lines for the window (a fixed-width font lines the columns up).

    Each group sizes its own columns to its widest cell: "dans les temps" is wider than a
    number, and a fixed width ran two cells into each other.
    """
    if not groups:
        return _("Aucune clé terminée à comparer : il faut au moins une clé, et deux du même "
                 "niveau pour les mettre côte à côte.")
    lines = []
    for group in groups:
        runs = group["runs"]
        table = [("", [_("Clé %d") % run["index"] for run in runs],
                  _("Écart") if len(runs) > 1 else ""),
                 (_("Durée"), [format_duration(run["duration"]) for run in runs],
                  change_text(change([run["duration"] for run in runs]))),
                 (_("Issue"), [_(run["outcome"]) for run in runs], ""),
                 (_("Morts"), [str(run["deaths"]) for run in runs], "")]
        for key in ("dps", "hps", "taken"):
            table.append((_("Groupe : ") + metric_label(key),
                          [fmt.compact(run[key]) for run in runs],
                          change_text(change([run[key] for run in runs]))))
        for player in group["players"]:
            table.append(("", [], ""))
            table.append(("%s (%s)" % (player["name"], player["spec"]), [], ""))
            for key, values, delta in player["rows"]:
                table.append(("  " + metric_label(key), [metric_text(key, v) for v in values],
                              change_text(delta)))
        lines.append(_("%s : %s") % (group["title"], fmt.plural(len(runs), "clé")))
        lines += _aligned(table, len(runs))
        lines.append("")
    lines.append(_("Écart : la dernière clé par rapport à la première. Soins/s compte les "
                   "boucliers ; Subis/s compte ce que les boucliers ont absorbé, et n'est donné "
                   "qu'aux tanks."))
    return "\n".join(lines)


def _aligned(table, columns):
    """Lines for [(label, [cells], change)] with every column as wide as its widest cell."""
    label_width = max([len(label) for label, _cells, _delta in table] + [8]) + 2
    widths = [max([len(cells[c]) for _label, cells, _delta in table if len(cells) > c] + [4]) + 2
              for c in range(columns)]
    delta_width = max([len(delta) for _label, _cells, delta in table] + [0]) + 2
    lines = []
    for label, cells, delta in table:
        line = label.ljust(label_width) + "".join(cell.rjust(widths[c])
                                                  for c, cell in enumerate(cells))
        lines.append((line + delta.rjust(delta_width)).rstrip())
    return lines


def overview_text(segments):
    """What the window's preview says for the chosen fights: one preview each, in order."""
    if not segments:
        return ""
    return "\n\n".join(fight_preview(segment) for segment in segments)
