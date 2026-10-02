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
from .history_tables import (EVOLUTION_GROUPS, EVOLUTION_NOTE, EVOLUTION_RUNS, NO_FOLLOWED, NO_RUNS,
                             chart_points, evolution_notes, group_rows, run_rows, value_text,
                             window_columns)
from .i18n import N_, _
from .preview import metric_label

SHOW_CHOICES = (("all", N_("Clés et boss")), ("keys", N_("Clés seulement")),
                ("bosses", N_("Boss seulement")))
CHART_WIDTH, CHART_HEIGHT = 340, 170
LINE, AXIS, TEXT = "#4a6984", "#aaaaaa", "#444444"
notes_for = evolution_notes          # the name the tests and this tab have always used
KINDS = {"all": (history_views.KEY, history_views.BOSS), "keys": (history_views.KEY,),
         "bosses": (history_views.BOSS,)}


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
        self.group_table = app._table(by_content, window_columns(EVOLUTION_GROUPS), height=6,
                                      select="browse")
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
        self.run_table = app._table(every, window_columns(EVOLUTION_RUNS), height=8,
                                    select="browse")
        self.run_table.master.grid(row=0, column=0, sticky="nsew")

        self.note = ttk.Label(frame, justify="left", wraplength=800, foreground="#555",
                              text=_(EVOLUTION_NOTE))
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
            self.message.configure(text=_(NO_FOLLOWED))
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
                               _(NO_RUNS))
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
