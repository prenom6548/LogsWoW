# SPDX-License-Identifier: AGPL-3.0-or-later
"""The history window's "Évolution" tab: how a followed character does, run after run.

It draws what `history_views` computes. Two tables, because two questions: *by content*
(one row per dungeon and level, or boss and difficulty, with the first and last figure, the
change between them, the item level and a small bar chart of the figure over the runs) and
*every run* (one row each, with the context beside the figure). Selecting a content row
narrows the second table to it. The measure is a choice -- damage, healing or, for a tank,
damage taken per second -- and opens on what the character's latest role is judged by.

Nothing here says "better" or "worse": the change is a number with what else changed next to
it, and the tab says so.
"""

from . import fmt, history, history_views
from .i18n import N_, _
from .preview import change_text, ilvl_text, metric_label
from .specs import label_of
from .timestamps import format_duration

SHOW_CHOICES = (("all", N_("Clés et boss")), ("keys", N_("Clés seulement")),
                ("bosses", N_("Boss seulement")))
CHART_WIDTH, CHART_HEIGHT = 340, 170
LINE, AXIS, TEXT = "#4a6984", "#aaaaaa", "#444444"
KINDS = {"all": (history_views.KEY, history_views.BOSS), "keys": (history_views.KEY,),
         "bosses": (history_views.BOSS,)}


# -- rows, testable without a screen -----------------------------------------------------------

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


def notes_for(groups):
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


# -- the tab -------------------------------------------------------------------------------------

class EvolutionTab:
    """The tab, built into `parent` (a frame of the history window's notebook)."""

    def __init__(self, window, parent):
        self.window = window
        self.parent = parent
        self.guids = []             # the characters the first list shows, in its order
        self.groups = []
        self.runs = []
        self._build()

    # -- building -------------------------------------------------------------------------

    def _build(self):
        app = self.window.app
        tk, ttk = app.tk, app.ttk
        frame = self.parent
        frame.columnconfigure(0, weight=1)
        frame.rowconfigure(2, weight=1)
        frame.rowconfigure(3, weight=2)
        frame.columnconfigure(1, weight=0)

        choose = ttk.Frame(frame)
        choose.grid(row=0, column=0, columnspan=2, sticky="ew")
        ttk.Label(choose, text=_("Personnage :")).pack(side="left")
        self.who = tk.StringVar()
        self.who_box = ttk.Combobox(choose, textvariable=self.who, state="readonly", width=30)
        self.who_box.pack(side="left", padx=(6, 14))
        self.who_box.bind("<<ComboboxSelected>>", lambda _event: self.redraw(reset=True))
        ttk.Label(choose, text=_("Mesure :")).pack(side="left")
        self.metric = tk.StringVar()
        self.metric_box = ttk.Combobox(choose, textvariable=self.metric, state="readonly",
                                       width=12, values=[metric_label(m) for m in
                                                         history_views.METRICS])
        self.metric_box.pack(side="left", padx=(6, 14))
        self.metric_box.bind("<<ComboboxSelected>>", lambda _event: self.redraw())
        ttk.Label(choose, text=_("Afficher :")).pack(side="left")
        self.show = tk.StringVar()
        self.show_box = ttk.Combobox(choose, textvariable=self.show, state="readonly", width=16,
                                     values=[_(label) for _key, label in SHOW_CHOICES])
        self.show_box.current(0)
        self.show_box.pack(side="left", padx=(6, 0))
        self.show_box.bind("<<ComboboxSelected>>", lambda _event: self.redraw())

        self.message = ttk.Label(frame, text="", justify="left", wraplength=800)
        self.message.grid(row=1, column=0, columnspan=2, sticky="ew", pady=(8, 0))

        by_content = ttk.LabelFrame(frame, text=_(" Par contenu "), padding=6)
        by_content.grid(row=2, column=0, sticky="nsew", pady=(8, 0), padx=(0, 8))
        by_content.columnconfigure(0, weight=1)
        by_content.rowconfigure(0, weight=1)
        self.group_table = app._table(by_content, (
            ("name", _("Contenu"), 200), ("level", _("Niveau"), 88), ("runs", _("Sorties"), 62),
            ("first", _("Première"), 80), ("last", _("Dernière"), 80), ("change", _("Écart"), 64),
            ("ilvl", "ilvl", 104)), height=6, select="browse")
        self.group_table.master.grid(row=0, column=0, sticky="nsew")
        self.group_table.bind("<<TreeviewSelect>>", lambda _event: self._fill_runs())

        chart = ttk.LabelFrame(frame, text=_(" Tendance "), padding=6)
        chart.grid(row=2, column=1, sticky="nsew", pady=(8, 0))
        self.canvas = tk.Canvas(chart, width=CHART_WIDTH, height=CHART_HEIGHT,
                                background="white", highlightthickness=0)
        self.canvas.pack()

        every = ttk.LabelFrame(frame, text=_(" Toutes les sorties "), padding=6)
        every.grid(row=3, column=0, columnspan=2, sticky="nsew", pady=(8, 0))
        every.columnconfigure(0, weight=1)
        every.rowconfigure(0, weight=1)
        self.run_table = app._table(every, (
            ("date", _("Date"), 88), ("name", _("Contenu"), 170), ("level", _("Niveau"), 84),
            ("outcome", _("Issue"), 106), ("time", _("Durée"), 52),
            ("spec", _("Spécialisation"), 196), ("ilvl", "ilvl", 52), ("dps", _("Dégâts/s"), 74),
            ("hps", _("Soins/s"), 68), ("taken", _("Subis/s"), 68), ("deaths", _("Morts"), 50),
            ("group", _("Groupe"), 62), ("game", _("Jeu"), 54)), height=8, select="browse")
        self.run_table.master.grid(row=0, column=0, sticky="nsew")

        self.note = ttk.Label(frame, justify="left", wraplength=800, foreground="#555", text=_(
            "Écart : la dernière sortie par rapport à la première, dans un même contenu et un "
            "même niveau (ou une même difficulté). Il dépend aussi du niveau d'objet, du groupe "
            "et des affixes, affichés à côté : ce n'est pas une note. Groupe : tanks / "
            "soigneurs / dps."))
        self.note.grid(row=4, column=0, columnspan=2, sticky="ew", pady=(8, 0))
        self.warnings = ttk.Label(frame, justify="left", wraplength=800, foreground="#8a4b00",
                                  text="")
        self.warnings.grid(row=5, column=0, columnspan=2, sticky="ew", pady=(4, 0))

    # -- showing ---------------------------------------------------------------------------

    @property
    def root(self):
        return self.window.root

    def _slug(self):
        return history.config(self.root)["dossier_actif"]

    def refresh(self):
        """Reload the characters of the active folder, keeping the one chosen if still there."""
        slug = self._slug()
        found = history_views.followed_in_folder(self.root, slug) if slug else []
        keep = self.guids[self.who_box.current()] if (
            self.guids and 0 <= self.who_box.current() < len(self.guids)) else None
        self.guids = [guid for guid, _name, _count in found]
        self.who_box.configure(values=["%s (%s)" % (name, fmt.plural(count, "sortie"))
                                       for _guid, name, count in found])
        if self.guids:
            self.who_box.current(self.guids.index(keep) if keep in self.guids else 0)
        else:
            self.who.set("")
        self.redraw(reset=keep not in self.guids)

    def redraw(self, reset=False):
        """Recompute the two tables for the character, the measure and the kinds chosen."""
        index = self.who_box.current()
        if not self.guids or not 0 <= index < len(self.guids):
            self.runs, self.groups = [], []
            self.message.configure(text=_(
                "Aucun personnage suivi dans ce dossier : suivez-en un dans l'onglet « Soirées », "
                "puis ajoutez des soirées."))
            self._clear()
            return
        self.runs = history_views.runs_of(self.root, self._slug(), self.guids[index])
        if reset or not self.metric.get():
            self.metric_box.current(history_views.METRICS.index(
                history_views.default_metric(self.runs)))
        metric = history_views.METRICS[max(0, self.metric_box.current())]
        kinds = KINDS[SHOW_CHOICES[max(0, self.show_box.current())][0]]
        self.groups = history_views.trend_groups(self.runs, metric, kinds)
        self.message.configure(text="" if self.groups else
                               _("Aucune sortie de ce personnage dans ce dossier."))
        self.group_table.delete(*self.group_table.get_children())
        for number, row in enumerate(group_rows(self.groups)):
            self.group_table.insert("", "end", iid=str(number), values=row)
        self.warnings.configure(text="\n".join(notes_for(self.groups)))
        self._fill_runs()

    def _clear(self):
        self.group_table.delete(*self.group_table.get_children())
        self.run_table.delete(*self.run_table.get_children())
        self.warnings.configure(text="")
        self.canvas.delete("all")

    def _draw(self, groups):
        """The trend of the content selected (the first when none is) as a line over its runs."""
        canvas = self.canvas
        canvas.delete("all")
        group = groups[0] if groups else None
        if group is None or not group.runs:
            return
        values = group.values
        points, (low, high) = chart_points(values, CHART_WIDTH, CHART_HEIGHT)
        if low is None:
            return
        left, bottom = 46, CHART_HEIGHT - 26
        canvas.create_line(left, 12, left, bottom, fill=AXIS)
        canvas.create_line(left, bottom, CHART_WIDTH - 12, bottom, fill=AXIS)
        canvas.create_text(left - 4, 12, text=value_text(high), anchor="e", fill=TEXT)
        canvas.create_text(left - 4, bottom, text=value_text(low), anchor="e", fill=TEXT)
        drawn = [point for point in points if point is not None]
        if len(drawn) > 1:
            canvas.create_line(*[coordinate for point in drawn for coordinate in point],
                               fill=LINE, width=2)
        for x, y in drawn:
            canvas.create_oval(x - 3, y - 3, x + 3, y + 3, fill=LINE, outline=LINE)
        dated = [run for run, point in zip(group.runs, points) if point is not None]
        canvas.create_text(left, bottom + 12, text=dated[0].date, anchor="w", fill=TEXT)
        if len(dated) > 1:
            canvas.create_text(CHART_WIDTH - 12, bottom + 12, text=dated[-1].date, anchor="e",
                               fill=TEXT)

    def _fill_runs(self):
        """The second table: every run, or those of the content selected in the first."""
        selected = self.group_table.selection()
        groups = ([self.groups[int(item)] for item in selected] if selected else self.groups)
        listed = sorted((run for group in groups for run in group.listed),
                        key=lambda run: (run.start or run.date or ""))
        self.run_table.delete(*self.run_table.get_children())
        for number, row in enumerate(run_rows(listed)):
            self.run_table.insert("", "end", iid=str(number), values=row)
        self._draw(groups)
