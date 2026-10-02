# SPDX-License-Identifier: AGPL-3.0-or-later
"""The rows, columns and notes of the history's three views, as plain data.

One place for what the history window (`gui_evolution`, `gui_specs`, `gui_records`) and the
history page (`report_history`) both show, so that a figure on one is the figure on the
other: they call the same functions on the same `history_views` objects, the way the window's
preview and the report's comparison share `preview`. No widget and no markup here.

A column is `(key, title, width, numeric)`: the window uses the width, the page the
alignment; a title is marked `N_` and translated where it is shown (`header`).
"""

from . import fmt, history_views
from .i18n import N_, _
from .preview import change_text, ilvl_text, metric_label
from .specs import DPS, HEAL, TANK, label_of
from .timestamps import format_duration

ROLES = (DPS, HEAL, TANK)          # the order the roles are offered in

ILVL = "ilvl"                      # the same in every language: never translated
ALL_CHARACTERS = N_("Tous les personnages suivis")

EVOLUTION_NOTE = N_(
    "Écart : la dernière sortie par rapport à la première, dans un même contenu et un "
    "même niveau (ou une même difficulté). Il dépend aussi du niveau d'objet, du groupe "
    "et des affixes, affichés à côté : ce n'est pas une note. Groupe : tanks / "
    "soigneurs / dps.")
SPEC_NOTE = N_(
    "Médiane des sorties comptées (clés terminées, boss tués) d'un même contenu et d'un "
    "même niveau, pour un rôle à la fois. L'écart est celui de chaque spécialisation par "
    "rapport à la première ligne, la plus jouée : ce n'est pas un classement. Il dépend "
    "aussi du niveau d'objet, des joueurs et du groupe ; avec plusieurs personnages, il "
    "mêle leurs joueurs.")
RECORD_NOTE = N_(
    "Meilleure clé : la plus haute clé terminée dans les temps ; à niveau égal, le "
    "meilleur score, puis le temps le plus court. Une clé terminée hors des temps ne "
    "passe devant que si la spécialisation n'en a aucune dans les temps. Meilleur kill : "
    "le plus rapide d'un même boss de raid à la même difficulté. Ce sont les records de "
    "chaque spécialisation, rangés par rôle : pas un classement, et pas un parse. Ils "
    "dépendent du groupe, du niveau d'objet et des affixes, affichés à côté. Groupe : "
    "tanks / soigneurs / dps ; Clés : dans les temps / terminées.")
NO_FOLLOWED = N_(
    "Aucun personnage suivi dans ce dossier : suivez-en un dans l'onglet « Soirées », "
    "puis ajoutez des soirées.")
NO_RUNS = N_("Aucune sortie de ce personnage dans ce dossier.")
NO_SPEC_GROUPS = N_(
    "Aucun contenu n'a été joué avec au moins deux spécialisations de ce rôle dans ce dossier.")
NO_RECORDS = N_("Aucune clé terminée ni aucun kill de raid dans ce dossier pour l'instant.")

EVOLUTION_GROUPS = (
    ("name", N_("Contenu"), 200, False), ("level", N_("Niveau"), 88, False),
    ("runs", N_("Sorties"), 62, True), ("first", N_("Première"), 80, True),
    ("last", N_("Dernière"), 80, True), ("change", N_("Écart"), 64, True),
    ("ilvl", ILVL, 104, True))
EVOLUTION_RUNS = (
    ("date", N_("Date"), 88, False), ("name", N_("Contenu"), 170, False),
    ("level", N_("Niveau"), 84, False), ("outcome", N_("Issue"), 106, False),
    ("time", N_("Durée"), 52, True), ("spec", N_("Spécialisation"), 196, False),
    ("ilvl", ILVL, 52, True), ("dps", N_("Dégâts/s"), 74, True),
    ("hps", N_("Soins/s"), 68, True), ("taken", N_("Subis/s"), 68, True),
    ("deaths", N_("Morts"), 50, True), ("group", N_("Groupe"), 62, False),
    ("game", N_("Jeu"), 54, False))
SPEC_CONTENTS = (
    ("name", N_("Contenu"), 200, False), ("level", N_("Niveau"), 88, False),
    ("specs", N_("Spés"), 52, True), ("runs", N_("Sorties"), 62, True))
SPEC_ROWS = (
    ("spec", N_("Spécialisation"), 250, False), ("runs", N_("Sorties"), 66, True),
    ("chars", N_("Persos"), 62, True), ("median", N_("Médiane"), 84, True),
    ("range", N_("Min – max"), 170, True), ("ilvl", ILVL, 70, True),
    ("gap", N_("Écart / 1re"), 90, True))
KEY_RECORDS = (
    ("spec", N_("Spécialisation"), 215, False), ("dungeon", N_("Donjon"), 185, False),
    ("level", N_("Niveau"), 68, False), ("timely", N_("En temps"), 78, False),
    ("time", N_("Temps"), 58, True), ("score", N_("Score"), 56, True),
    ("ilvl", ILVL, 56, True), ("date", N_("Date"), 88, False),
    ("who", N_("Personnage"), 104, False), ("group", N_("Groupe"), 68, False),
    ("timed", N_("Clés"), 54, True), ("figure", N_("Chiffre"), 126, True))
BOSSES = (
    ("boss", N_("Boss"), 170, False), ("level", N_("Difficulté"), 84, False),
    ("kills", N_("Kills"), 48, True), ("specs", N_("Spés"), 44, True))
KILL_RECORDS = (
    ("spec", N_("Spécialisation"), 215, False), ("time", N_("Durée"), 62, True),
    ("ilvl", ILVL, 56, True), ("date", N_("Date"), 88, False),
    ("who", N_("Personnage"), 104, False), ("group", N_("Groupe"), 68, False),
    ("kills", N_("Kills"), 48, True), ("figure", N_("Chiffre"), 126, True))


def header(title):
    """A column's title as it is shown, in the language chosen."""
    return title if title == ILVL else _(title)


def window_columns(columns):
    """The `(key, title, width)` the window's tables take."""
    return tuple((key, header(title), width) for key, title, width, _numeric in columns)


# -- rows ----------------------------------------------------------------------------------------

def value_text(value):
    return "—" if value is None else fmt.compact(value)


def group_rows(groups):
    """[(content, level, runs, first, last, change, item level)] for the first table."""
    rows = []
    for group in groups:
        if group.ilvl_first is None:
            ilvl = ""
        elif group.ilvl_first == group.ilvl_last:
            ilvl = ilvl_text(group.ilvl_last)
        else:
            ilvl = "%s → %s" % (ilvl_text(group.ilvl_first), ilvl_text(group.ilvl_last))
        count = ("%d" % len(group.runs) if len(group.runs) == len(group.listed)
                 else "%d/%d" % (len(group.runs), len(group.listed)))
        rows.append((group.name, group.level_text, count,
                     value_text(group.first), value_text(group.last),
                     change_text(group.change), ilvl))
    return rows


def run_rows(runs):
    """One row per run for the second table: the three figures, with the context beside."""
    rows = []
    for run in runs:
        mark = "" if run.counts else "†"            # listed, left out of the trend
        health = run.boss_health_end
        outcome = _(run.outcome)
        if health is not None and run.kind == history_views.BOSS and run.outcome != "réussite":
            outcome = "%s (%s)" % (outcome, fmt.percent(health))
        rows.append((
            run.date, run.name + mark, run.level_text(), outcome,
            format_duration(run.duration_ms), label_of(run.spec_id) or "?",
            ilvl_text(run.ilvl) if run.ilvl is not None else "",
            value_text(run.value("dps")), value_text(run.value("hps")),
            value_text(run.value("taken")), run.row.get("deaths", 0),
            "%d/%d/%d" % run.composition, run.build or "?"))
    return rows


def evolution_notes(groups):
    """The warnings that apply to what is listed: a mixed specialization, an older count."""
    notes = []
    for group in groups:
        if group.mixed_specs:
            notes.append(_("Spécialisations différentes dans « %s » : %s.") % (
                group.name, ", ".join(label_of(spec) or "?" for spec in group.specs)))
    if any(group.old_analysis for group in groups):
        notes.append(_("Certaines sorties ont été comptées avec une ancienne version des règles "
                       "de calcul : leurs chiffres ne sont pas forcément comparables."))
    if any(len(group.listed) != len(group.runs) for group in groups):
        notes.append(_("† Hors tendance : clé abandonnée ou interrompue, boss non tué."))
    return notes


def chart_points(values, width, height, left=46, right=12, top=12, bottom=26):
    """([(x, y) or None per value], (low, high)): the values placed in a plot area.

    The lowest value sits at the bottom and the highest at the top, so the line shows the
    shape and the labels say the scale; equal values give a flat line in the middle, never a
    slope. The runs are spaced evenly (a run is a run, whatever the days between). A gap
    (None) stays a gap.
    """
    present = [value for value in values if value is not None]
    if not present:
        return [None] * len(values), (None, None)
    low, high = min(present), max(present)
    plot_w, plot_h = width - left - right, height - top - bottom
    points = []
    for index, value in enumerate(values):
        if value is None:
            points.append(None)
            continue
        x = left + (plot_w / 2.0 if len(values) == 1 else plot_w * index / (len(values) - 1))
        flat = high - low < 1e-9
        y = top + (plot_h / 2.0 if flat else plot_h * (1 - (value - low) / (high - low)))
        points.append((x, y))
    return points, (low, high)


def content_rows(groups):
    """[(content, level, specializations, runs)] for the list of comparable contents."""
    return [(group.name, group.level_text, len(group.rows), group.total) for group in groups]


def spec_rows(group):
    """One row per specialization of a content: runs, median, range, item level, gap."""
    rows = []
    for row in group.rows:
        gap = "" if row is group.rows[0] else change_text(group.gap(row))
        spread = "—" if row.low is None else (
            value_text(row.low) if row.low == row.high
            else "%s – %s" % (value_text(row.low), value_text(row.high)))
        rows.append((
            label_of(row.spec_id) or "?",
            "%d%s" % (len(row.runs), "‡" if row.thin else ""), row.characters,
            value_text(row.median), spread,
            ilvl_text(row.ilvl) if row.ilvl is not None else "", gap or "—"))
    return rows


def spec_notes(groups, single, unknown):
    """What was left out or needs care: said, never hidden."""
    notes = []
    if single:
        notes.append(_("Contenus joués avec une seule spécialisation, non comparés : %d.") % single)
    if unknown:
        notes.append(_("Sorties dont la spécialisation n'est pas écrite dans le journal ou que "
                       "LogsWoW ne connaît pas, non comparées : %d.") % unknown)
    if any(row.thin for group in groups for row in group.rows):
        notes.append(_("‡ Moins de %d sorties : une médiane sur si peu de sorties dit peu de "
                       "chose.") % history_views.LOW_SAMPLE)
    if any(row.old_analysis for group in groups for row in group.rows):
        notes.append(_("Certaines sorties ont été comptées avec une ancienne version des règles "
                       "de calcul : leurs chiffres ne sont pas forcément comparables."))
    return notes


def bar_lengths(values, plot_width):
    """The bar of each value, in pixels, from zero: the longest fills `plot_width`.

    A bar starts at zero because a length stands for a quantity; cutting the axis would make a
    small difference look large. None (no figure) and zero give no bar.
    """
    present = [value for value in values if value is not None and value > 0]
    if not present:
        return [0.0] * len(values)
    top = max(present)
    return [0.0 if value is None or value <= 0 else plot_width * value / top for value in values]


def _figure(run):
    """The run's figure in the measure its role is judged by, with the measure's name."""
    metric = history_views.ROLE_METRIC.get(run.role, "dps")
    value = run.value(metric)
    return "—" if value is None else "%s %s" % (value_text(value), metric_label(metric))


def _who(run):
    return run.row.get("name") or "?"


def _time_text(milliseconds):
    return (format_duration(milliseconds)
            if isinstance(milliseconds, (int, float)) and milliseconds > 0 else "")


def _score_text(score):
    return fmt.decimal(round(score, 1)) if isinstance(score, (int, float)) and score else ""


TIMELY = {"dans les temps": "✓", "hors des temps": "✗"}      # a key finished with no score: "?"


def key_rows(records):
    """One row per specialization: its best key, the context beside it, and how many it made."""
    rows = []
    for record in records:
        run = record.best
        rows.append((
            label_of(record.spec_id) or "?", run.name, run.level_text(),
            TIMELY.get(run.outcome, "?"), _time_text(run.key_time_ms), _score_text(run.score),
            ilvl_text(run.ilvl) if run.ilvl is not None else "", run.date, _who(run),
            "%d/%d/%d" % run.composition, "%d/%d" % (record.timed, record.total),
            _figure(run)))
    return rows


def boss_rows(groups):
    """[(boss, difficulty, kills, specializations)] for the list of raid bosses."""
    return [(group.name, group.level_text, group.kills, len(group.rows)) for group in groups]


def kill_rows(group):
    """One row per specialization that killed the boss: its fastest kill and the context."""
    rows = []
    for record in group.rows:
        run = record.best
        rows.append((
            label_of(record.spec_id) or "?", format_duration(run.duration_ms),
            ilvl_text(run.ilvl) if run.ilvl is not None else "", run.date, _who(run),
            "%d/%d/%d" % run.composition, record.total, _figure(run)))
    return rows


def record_notes(key_unknown, kill_unknown, records, groups):
    """What was left out or needs care: said, never hidden."""
    notes = []
    unknown = key_unknown + kill_unknown
    if unknown:
        notes.append(_("Sorties dont la spécialisation n'est pas écrite dans le journal, non "
                       "comparées : %d.") % unknown)
    runs = [record.best for record in records] + [
        row.best for group in groups for row in group.rows]
    if any(run.old_analysis for run in runs):
        notes.append(_("Certaines sorties ont été comptées avec une ancienne version des règles "
                       "de calcul : leurs chiffres ne sont pas forcément comparables."))
    return notes
