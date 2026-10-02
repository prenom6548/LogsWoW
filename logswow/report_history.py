# SPDX-License-Identifier: AGPL-3.0-or-later
"""The history as one page: evolution, specializations against each other, records.

Asked for by the owner on 2026-10-02, once the three views existed in the window: show them in
the HTML page too. It is a page of its own, written from the history of a folder, and not a
part of a log's report: the report is the artefact a reader shares and is made from one log,
while the history spans many nights and carries the followed characters' names.

It follows the rules every page of this project follows. It runs nothing and fetches nothing:
the tabs and the choice of character are radio buttons a label points at, CSS shows the pane
whose button is checked (the technique of the report's tabs), the charts are inline SVG, and
there is no script, no font, no image and no link outside the file. The figures are not
computed here: the rows, columns and notes come from `history_tables`, the same functions the
window calls on the same `history_views` objects, so a number on the page is the number in the
window.
"""

import os

from . import __version__, fmt, history, history_views
from .history_tables import (ALL_CHARACTERS, EVOLUTION_GROUPS, EVOLUTION_NOTE, EVOLUTION_RUNS,
                             KEY_RECORDS, KILL_RECORDS, NO_RECORDS, NO_RUNS, NO_SPEC_GROUPS,
                             RECORD_NOTE, ROLES, SPEC_NOTE, SPEC_ROWS, bar_lengths, boss_rows,
                             chart_points, evolution_notes, group_rows, header, key_rows,
                             kill_rows, record_notes, run_rows, spec_notes, spec_rows,
                             value_text)
from .i18n import N_, _, language
from .preview import metric_label, role_label
from .report import CSS
from .report_layouts import write_atomic
from .specs import label_of

TABS = (("evo", N_("Évolution")), ("spec", N_("Spécialisations")), ("rec", N_("Records")))
CHART_WIDTH, CHART_HEIGHT = 440, 176
BARS_WIDTH, BAR_ROW, BARS_LABEL, BARS_VALUE, MAX_BARS = 560, 24, 210, 70, 12

HISTORY_CSS = """
.hx,.hw{position:absolute;opacity:0;width:1px;height:1px;pointer-events:none}
.hbar{display:flex;flex-wrap:wrap;gap:4px}
.hbar.tabs{border-bottom:1px solid var(--line);margin:22px 0 10px}
.hbar.who{margin:0 0 6px;gap:6px}
.hl{cursor:pointer;color:var(--muted)}
.tabs .hl{padding:7px 14px;border:1px solid transparent;border-bottom:none;font-weight:600;
border-radius:6px 6px 0 0;font-size:17px;margin-bottom:-1px}
.who .hl{padding:4px 10px;border:1px solid var(--line);border-radius:99px;font-size:13px}
.hl:hover{color:var(--ink)}
.hv,.hs{display:none}
.scroll{overflow-x:auto}
.chart{max-width:480px;margin:8px 0 4px}
.chart svg text{fill:var(--muted);font-size:12px}
td.nw{white-space:nowrap}
.chart svg .ref{fill:var(--accent)}
.chart svg .bar{fill:var(--bar)}
.chart svg .ax{stroke:var(--line);fill:none}
.chart svg .ln{stroke:var(--accent);fill:none;stroke-width:2}
.chart svg .pt{fill:var(--accent)}
.hg>summary .dim{font-weight:400}
.hnote{font-size:13px;color:var(--muted);margin:8px 0}
.hwarn{font-size:13px;color:var(--warn);margin:4px 0}
"""


def rules(characters):
    """One rule per tab and per character: the checked button shows its panes."""
    out = []
    for key, _title in TABS:
        out.append("#hx-%s:checked~.hv-%s{display:block}" % (key, key))
        out.append("#hx-%s:checked~.tabs .hlt-%s{background:var(--panel);"
                   "border-color:var(--line);color:var(--ink)}" % (key, key))
        out.append("#hx-%s:focus-visible~.tabs .hlt-%s{outline:2px solid var(--accent)}"
                   % (key, key))
    for index in range(characters + 1):
        out.append("#hw-%d:checked~.hv .hs-%d{display:block}" % (index, index))
        out.append("#hw-%d:checked~.who .hlw-%d{background:var(--panel);color:var(--ink);"
                   "border-color:var(--accent);font-weight:600}" % (index, index))
        out.append("#hw-%d:focus-visible~.who .hlw-%d{outline:2px solid var(--accent)}"
                   % (index, index))
    return "\n".join(out)


# -- small pieces ------------------------------------------------------------------------------

def table(columns, rows):
    """A table of `rows` under the columns' titles; numeric columns are right-aligned."""
    heads = "".join("<th%s>%s</th>" % (" class=n" if numeric else "", fmt.esc(header(title)))
                    for _key, title, _width, numeric in columns)

    def cell(column, value):
        key, _title, _width, numeric = column
        css = " class=n" if numeric else (" class=nw" if key == "date" else "")
        return "<td%s>%s</td>" % (css, fmt.esc(value))

    body = "".join(
        "<tr>%s</tr>" % "".join(cell(column, value) for column, value in zip(columns, row))
        for row in rows)
    return "<div class=scroll><table><tr>%s</tr>%s</table></div>" % (heads, body)


def notes(lines, css="hwarn"):
    return "".join("<p class=%s>%s</p>" % (css, fmt.esc(line)) for line in lines)


def details(summary, body):
    return ("<details class=hg><summary>%s</summary><div class=body>%s</div></details>"
            % (summary, body))


def trend_chart(values, dates):
    """The figure over the runs as a line, lowest at the bottom, scale in the labels."""
    points, (low, high) = chart_points(values, CHART_WIDTH, CHART_HEIGHT, left=58)
    if low is None:
        return ""
    left, bottom = 58, CHART_HEIGHT - 26
    drawn = [point for point in points if point is not None]
    parts = ["<line class=ax x1=%d y1=12 x2=%d y2=%d />" % (left, left, bottom),
             "<line class=ax x1=%d y1=%d x2=%d y2=%d />" % (
                 left, bottom, CHART_WIDTH - 12, bottom),
             "<text x=%d y=16 text-anchor=end>%s</text>" % (left - 6, fmt.esc(value_text(high))),
             "<text x=%d y=%d text-anchor=end>%s</text>" % (
                 left - 6, bottom, fmt.esc(value_text(low)))]
    if len(drawn) > 1:
        parts.append("<polyline class=ln points='%s' />" % " ".join("%.1f,%.1f" % point
                                                                    for point in drawn))
    parts.extend("<circle class=pt cx=%.1f cy=%.1f r=3 />" % point for point in drawn)
    shown = [date for date, point in zip(dates, points) if point is not None]
    parts.append("<text x=%d y=%d>%s</text>" % (left, CHART_HEIGHT - 8, fmt.esc(shown[0])))
    if len(shown) > 1:
        parts.append("<text x=%d y=%d text-anchor=end>%s</text>"
                     % (CHART_WIDTH - 12, CHART_HEIGHT - 8, fmt.esc(shown[-1])))
    return "<div class=chart><svg viewBox='0 0 %d %d' role=img>%s</svg></div>" % (
        CHART_WIDTH, CHART_HEIGHT, "".join(parts))


def bars_chart(group):
    """The medians of a content as horizontal bars from zero, the reference row darker."""
    rows = group.rows[:MAX_BARS]
    plot = BARS_WIDTH - BARS_LABEL - BARS_VALUE
    lengths = bar_lengths([row.median for row in rows], plot)
    parts = []
    for index, (row, length) in enumerate(zip(rows, lengths)):
        top = index * BAR_ROW + 4
        parts.append("<text x=%d y=%d text-anchor=end>%s</text>" % (
            BARS_LABEL - 8, top + 13, fmt.esc(label_of(row.spec_id) or "?")))
        parts.append("<rect class='%s' x=%d y=%d width=%.1f height=16 rx=2 />" % (
            "ref" if index == 0 else "bar", BARS_LABEL, top, max(length, 1.0)))
        parts.append("<text x=%.1f y=%d>%s</text>" % (
            BARS_LABEL + length + 6, top + 13, fmt.esc(value_text(row.median))))
    height = len(rows) * BAR_ROW + 8
    return "<div class=chart><svg viewBox='0 0 %d %d' role=img>%s</svg></div>" % (
        BARS_WIDTH, height, "".join(parts))


# -- the three views, for one choice of characters ----------------------------------------------

def evolution_view(runs):
    """One character, content by content: a table, then each content's chart and runs."""
    if not runs:
        return notes([_(NO_RUNS)], "hnote")
    metric = history_views.default_metric(runs)
    groups = history_views.trend_groups(runs, metric)
    out = ["<p class=hnote>%s %s</p>" % (fmt.esc(_("Mesure :")), fmt.esc(metric_label(metric)))]
    out.append(table(EVOLUTION_GROUPS, group_rows(groups)))
    out.append(notes(evolution_notes(groups)))
    for group in groups:
        listed = group.listed
        title = "%s <span class=dim>%s</span>" % (fmt.esc(group.name), fmt.esc(group.level_text))
        body = (trend_chart(group.values, [run.date for run in group.runs])
                + table(EVOLUTION_RUNS, run_rows(listed)))
        out.append(details(title, body))
    out.append("<p class=hnote>%s</p>" % fmt.esc(_(EVOLUTION_NOTE)))
    return "".join(out)


def specs_view(runs):
    """For each role, the contents played with two specializations or more."""
    out, shown = [], False
    for role in ROLES:
        metric = history_views.ROLE_METRIC[role]
        groups, single, unknown = history_views.spec_comparison(runs, role, metric)
        if not groups and not single:
            continue
        shown = True
        out.append("<h3>%s <span class=dim>· %s</span></h3>" % (
            fmt.esc(role_label(role)), fmt.esc(metric_label(metric))))
        if not groups:
            out.append(notes([_(NO_SPEC_GROUPS)], "hnote"))
        for group in groups:
            title = "%s <span class=dim>%s · %d / %d</span>" % (
                fmt.esc(group.name), fmt.esc(group.level_text), len(group.rows), group.total)
            out.append(details(title, bars_chart(group) + table(SPEC_ROWS, spec_rows(group))))
        out.append(notes(spec_notes(groups, single, unknown)))
    if not shown:
        return notes([_(NO_SPEC_GROUPS)], "hnote")
    out.append("<p class=hnote>%s</p>" % fmt.esc(_(SPEC_NOTE)))
    return "".join(out)


def records_view(runs):
    """The best key of each specialization, then its fastest kill of each raid boss."""
    records, key_unknown = history_views.key_records(runs)
    groups, kill_unknown = history_views.kill_groups(runs)
    if not records and not groups:
        return notes([_(NO_RECORDS)], "hnote")
    out = []
    if records:
        out.append("<h3>%s</h3>" % fmt.esc(_("Meilleure clé par spécialisation")))
        out.append(table(KEY_RECORDS, key_rows(records)))
    if groups:
        out.append("<h3>%s</h3>" % fmt.esc(_("Meilleur kill par spécialisation")))
        for group, row in zip(groups, boss_rows(groups)):
            title = "%s <span class=dim>%s · %s</span>" % (
                fmt.esc(row[0]), fmt.esc(row[1]),
                fmt.esc(_("%d kills · %d spés") % (row[2], row[3])))
            out.append(details(title, table(KILL_RECORDS, kill_rows(group))))
    out.append(notes(record_notes(key_unknown, kill_unknown, records, groups)))
    out.append("<p class=hnote>%s</p>" % fmt.esc(_(RECORD_NOTE)))
    return "".join(out)


# -- the page ------------------------------------------------------------------------------------

def controls(labels):
    """The buttons, before everything they show: one per tab, one per choice of characters
    (`labels[0]` is "all"), then the two rows of labels that point at them."""
    radios = "".join(
        "<input type=radio name=hx id=hx-%s class=hx%s aria-label='%s'>"
        % (key, " checked" if position == 0 else "", fmt.esc(_(title)))
        for position, (key, title) in enumerate(TABS))
    radios += "".join(
        "<input type=radio name=hw id=hw-%d class=hw%s aria-label='%s'>"
        % (index, " checked" if index == 0 else "", fmt.esc(label))
        for index, label in enumerate(labels))
    tabs = "<div class='hbar tabs'>%s</div>" % "".join(
        "<label for=hx-%s class='hl hlt-%s'>%s</label>" % (key, key, fmt.esc(_(title)))
        for key, title in TABS)
    who = "<div class='hbar who'>%s</div>" % "".join(
        "<label for=hw-%d class='hl hlw-%d'>%s</label>" % (index, index, fmt.esc(label))
        for index, label in enumerate(labels))
    return radios + tabs + who


def views(choices):
    """Each tab's pane, holding one section per choice of characters [(index, runs)]."""
    for key, _title in TABS:
        sections = []
        for index, runs in choices:
            if key == "evo":
                body = (notes([_("Choisissez un personnage ci-dessus pour voir son "
                                 "évolution.")], "hnote") if index == 0
                        else evolution_view(runs))
            elif key == "spec":
                body = specs_view(runs)
            else:
                body = records_view(runs)
            sections.append("<div class='hs hs-%d'>%s</div>" % (index, body))
        yield "<div class='hv hv-%s'>%s</div>" % (key, "".join(sections))


class HistoryPage:
    """The page of one history folder, written to `out_path`."""

    def __init__(self, root, slug, out_path):
        self.root, self.slug, self.out_path = root, slug, out_path

    def html(self):
        folder = next((item for item in history.list_folders(self.root)
                       if item.slug == self.slug), None)
        name = folder.name if folder else self.slug
        nights = history.list_nights(self.root, self.slug)
        everyone, characters = history_views.characters_and_runs(self.root, self.slug)
        labels = [_(ALL_CHARACTERS)] + [item[1] for item in characters]
        choices = [(0, everyone)] + [(index + 1, item[2]) for index, item in enumerate(characters)]
        return (self._head(name, len(characters)) + self._top(name, nights, len(characters))
                + controls(labels) + "".join(views(choices)) + self._foot())

    @staticmethod
    def _head(name, count):
        return ("<!doctype html><html lang=%s><head><meta charset=utf-8>"
                '<meta name=viewport content="width=device-width,initial-scale=1">'
                "<title>LogsWoW — %s — %s</title><style>%s%s%s</style></head><body>"
                "<div class=wrap>"
                % (language(), fmt.esc(_("Historique")), fmt.esc(name), CSS, HISTORY_CSS,
                   rules(count)))

    @staticmethod
    def _top(name, nights, count):
        """The title, what the folder holds, and what the figures are."""
        builds = sorted({night.build for night in nights if night.build})
        sub = [_("%s du %s au %s") % (fmt.plural(len(nights), "soirée"), nights[0].date,
                                      nights[-1].date)
               if nights else _("Aucune soirée dans ce dossier."),
               _("Personnages suivis : %d") % count]
        if builds:
            sub.append(_("jeu %s") % ", ".join(builds))
        return ("<h1>%s — %s</h1><p class=sub>%s</p>"
                "<div class=note>%s</div>" % (
                    fmt.esc(_("Historique")), fmt.esc(name), fmt.esc(" · ".join(sub)),
                    fmt.esc(_("Les chiffres viennent des soirées gardées dans ce dossier de "
                              "l'historique ; seuls les personnages suivis y portent un nom. "
                              "Rien ici n'est un classement des joueurs ni un parse."))))

    @staticmethod
    def _foot():
        return ("<footer>%s</footer></div></body></html>" % fmt.esc(
            _("LogsWoW %s · page écrite à partir de l'historique local. Licence AGPL-3.0 ou "
              "ultérieure ; code source : github.com/prenom6548/LogsWoW. Aucune donnée ne "
              "quitte cette machine.") % __version__))

    def write(self):
        write_atomic(self.out_path, self.html())
        return self.out_path


def write_page(root, slug, out, force=False):
    """Write the page of a folder at `out`, or say in French why not: None or the reason."""
    reason = refusal(out, root, force)
    if reason:
        return reason
    try:
        HistoryPage(root, slug, out).write()
    except OSError as error:
        return _("Impossible d'écrire %s : %s") % (out, error.strerror or error)
    return None


def refusal(out, root, force):
    """Why the page must not be written at `out`, or None.

    The same care as the report's: an existing file that is not a page of ours is refused
    unless `--force` says it is meant, a folder is refused, and the history itself is never
    the target -- a night is a file a page must not replace, forced or not.
    """
    from .report_layouts import is_our_report

    real = os.path.realpath(out)
    base = os.path.realpath(root)
    if real == base or real.startswith(base + os.sep):
        return _("Refus d'écrire la page dans le dossier de l'historique lui-même (%s). "
                 "Choisissez un autre endroit avec -o.") % out
    if not os.path.exists(out):
        return None
    if os.path.isdir(out):
        return _("%s est un dossier : donnez un nom de fichier avec -o.") % out
    if not force and not is_our_report(out):
        return (_("%s existe et n'est pas un rapport LogsWoW : refus de l'écraser. "
                  "Choisissez un autre nom, ou ajoutez --force si c'est voulu.") % out)
    return None
