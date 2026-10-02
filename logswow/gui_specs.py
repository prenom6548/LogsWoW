# SPDX-License-Identifier: AGPL-3.0-or-later
"""The history window's "Spécialisations" tab: one specialization against another.

It draws what `history_views.spec_comparison` computes. On the left, the contents (a dungeon
and a level, a boss and a difficulty) that were played with at least two specializations;
selecting one gives, for each specialization, the number of runs, the *median* figure, its
range, the item level and the gap to the first row, with a bar chart of the medians.

Nothing here ranks anything. The first row is the most played, not the best; the gap is a
number with the item level and the group beside it, and a row backed by fewer than three
runs is marked, because a median of two runs says little. Several characters mix their
players, which the tab says.
"""

from . import fmt, history, history_views
from .gui_evolution import KINDS, SHOW_CHOICES, value_text
from .i18n import N_, _
from .preview import change_text, ilvl_text, metric_label, role_label
from .specs import DPS, HEAL, TANK, label_of

ALL_CHARACTERS = N_("Tous les personnages suivis")
ROLES = (DPS, HEAL, TANK)          # the order of the role box
CHART_WIDTH, CHART_HEIGHT = 470, 204
MAX_BARS = 8
BAR_HEIGHT, LABEL_WIDTH, VALUE_WIDTH = 16, 180, 56
BAR, TEXT, REFERENCE = "#4a6984", "#444444", "#2f4f6b"


# -- rows, testable without a screen -----------------------------------------------------------

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


def notes_for(groups, single, unknown):
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


# -- the tab ---------------------------------------------------------------------------------------

class SpecsTab:
    """The tab, built into `parent` (a frame of the history window's notebook)."""

    def __init__(self, window, parent):
        self.window = window
        self.parent = parent
        self.guids = []             # the characters offered after "all", in the box's order
        self.groups = []
        self._build()

    def _build(self):
        app = self.window.app
        tk, ttk = app.tk, app.ttk
        frame = self.parent
        frame.columnconfigure(0, weight=1)
        frame.rowconfigure(2, weight=1)
        frame.rowconfigure(3, weight=2)

        choose = ttk.Frame(frame)
        choose.grid(row=0, column=0, columnspan=2, sticky="ew")
        ttk.Label(choose, text=_("Personnage :")).pack(side="left")
        self.who = tk.StringVar()
        self.who_box = ttk.Combobox(choose, textvariable=self.who, state="readonly", width=30)
        self.who_box.pack(side="left", padx=(6, 14))
        self.who_box.bind("<<ComboboxSelected>>", lambda _event: self.redraw(reset=True))
        ttk.Label(choose, text=_("Rôle :")).pack(side="left")
        self.role = tk.StringVar()
        self.role_box = ttk.Combobox(choose, textvariable=self.role, state="readonly", width=11,
                                     values=[role_label(role) for role in ROLES])
        self.role_box.pack(side="left", padx=(6, 14))
        self.role_box.bind("<<ComboboxSelected>>", lambda _event: self.redraw(role_changed=True))
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

        contents = ttk.LabelFrame(frame, text=_(" Contenus comparables "), padding=6)
        contents.grid(row=2, column=0, sticky="nsew", pady=(8, 0), padx=(0, 8))
        contents.columnconfigure(0, weight=1)
        contents.rowconfigure(0, weight=1)
        self.content_table = app._table(contents, (
            ("name", _("Contenu"), 200), ("level", _("Niveau"), 88),
            ("specs", _("Spés"), 52), ("runs", _("Sorties"), 62)), height=6, select="browse")
        self.content_table.master.grid(row=0, column=0, sticky="nsew")
        self.content_table.bind("<<TreeviewSelect>>", lambda _event: self._fill_specs())

        chart = ttk.LabelFrame(frame, text=_(" Médiane par spécialisation "), padding=6)
        chart.grid(row=2, column=1, sticky="nsew", pady=(8, 0))
        self.canvas = tk.Canvas(chart, width=CHART_WIDTH, height=CHART_HEIGHT,
                                background="white", highlightthickness=0)
        self.canvas.pack()

        specs = ttk.LabelFrame(frame, text=_(" Spécialisations du contenu choisi "), padding=6)
        specs.grid(row=3, column=0, columnspan=2, sticky="nsew", pady=(8, 0))
        specs.columnconfigure(0, weight=1)
        specs.rowconfigure(0, weight=1)
        self.spec_table = app._table(specs, (
            ("spec", _("Spécialisation"), 250), ("runs", _("Sorties"), 66),
            ("chars", _("Persos"), 62), ("median", _("Médiane"), 84),
            ("range", _("Min – max"), 170), ("ilvl", "ilvl", 70),
            ("gap", _("Écart / 1re"), 90)), height=6, select="browse")
        self.spec_table.master.grid(row=0, column=0, sticky="nsew")

        self.note = ttk.Label(frame, justify="left", wraplength=800, foreground="#555", text=_(
            "Médiane des sorties comptées (clés terminées, boss tués) d'un même contenu et d'un "
            "même niveau, pour un rôle à la fois. L'écart est celui de chaque spécialisation par "
            "rapport à la première ligne, la plus jouée : ce n'est pas un classement. Il dépend "
            "aussi du niveau d'objet, des joueurs et du groupe ; avec plusieurs personnages, il "
            "mêle leurs joueurs."))
        self.note.grid(row=4, column=0, columnspan=2, sticky="ew", pady=(8, 0))
        self.warnings = ttk.Label(frame, justify="left", wraplength=800, foreground="#8a4b00",
                                  text="")
        self.warnings.grid(row=5, column=0, columnspan=2, sticky="ew", pady=(4, 0))

    # -- showing -------------------------------------------------------------------------------

    @property
    def root(self):
        return self.window.root

    def _slug(self):
        return history.config(self.root)["dossier_actif"]

    def refresh(self):
        """Reload the characters of the active folder, keeping the choice if still valid."""
        slug = self._slug()
        found = history_views.followed_in_folder(self.root, slug) if slug else []
        index = self.who_box.current()
        keep = self.guids[index - 1] if 1 <= index <= len(self.guids) else None
        self.guids = [guid for guid, _name, _count in found]
        self.who_box.configure(values=([_(ALL_CHARACTERS)] if found else []) + [
            "%s (%s)" % (name, fmt.plural(count, "sortie")) for _guid, name, count in found])
        if found:
            self.who_box.current(self.guids.index(keep) + 1 if keep in self.guids else 0)
        else:
            self.who.set("")
        self.redraw(reset=True)

    def _runs(self):
        index = self.who_box.current()
        if index < 0:
            return []
        if index == 0:
            return history_views.runs_in_folder(self.root, self._slug())
        return history_views.runs_of(self.root, self._slug(), self.guids[index - 1])

    def redraw(self, reset=False, role_changed=False):
        """Recompute the comparison for the characters, the role, the measure and the kinds."""
        self.groups = []
        if not self.guids:
            self.message.configure(text=_(
                "Aucun personnage suivi dans ce dossier : suivez-en un dans l'onglet « Soirées », "
                "puis ajoutez des soirées."))
            self._clear()
            return
        runs = self._runs()
        if reset or not self.role.get():
            self.role_box.current(ROLES.index(history_views.majority_role(runs)))
        role = ROLES[max(0, self.role_box.current())]
        if reset or role_changed or not self.metric.get():
            self.metric_box.current(history_views.METRICS.index(history_views.ROLE_METRIC[role]))
        metric = history_views.METRICS[max(0, self.metric_box.current())]
        kinds = KINDS[SHOW_CHOICES[max(0, self.show_box.current())][0]]
        self.groups, single, unknown = history_views.spec_comparison(runs, role, metric, kinds)
        self.message.configure(text="" if self.groups else _(
            "Aucun contenu n'a été joué avec au moins deux spécialisations de ce rôle dans ce "
            "dossier."))
        self.content_table.delete(*self.content_table.get_children())
        for number, row in enumerate(content_rows(self.groups)):
            self.content_table.insert("", "end", iid=str(number), values=row)
        self.warnings.configure(text="\n".join(notes_for(self.groups, single, unknown)))
        if self.groups:
            self.content_table.selection_set("0")
        self._fill_specs()

    def _clear(self):
        self.content_table.delete(*self.content_table.get_children())
        self.spec_table.delete(*self.spec_table.get_children())
        self.warnings.configure(text="")
        self.canvas.delete("all")

    def _selected(self):
        selected = self.content_table.selection()
        if selected:
            return self.groups[int(selected[0])]
        return self.groups[0] if self.groups else None

    def _fill_specs(self):
        group = self._selected()
        self.spec_table.delete(*self.spec_table.get_children())
        self.canvas.delete("all")
        if group is None:
            return
        for number, row in enumerate(spec_rows(group)):
            self.spec_table.insert("", "end", iid=str(number), values=row)
        self._draw(group)

    def _draw(self, group):
        """The medians as horizontal bars from zero, the most played specialization first."""
        canvas = self.canvas
        rows = group.rows[:MAX_BARS]
        plot = CHART_WIDTH - LABEL_WIDTH - VALUE_WIDTH - 12
        for index, (row, length) in enumerate(zip(rows, bar_lengths(
                [row.median for row in rows], plot))):
            top = 10 + index * (BAR_HEIGHT + 6)
            colour = REFERENCE if index == 0 else BAR
            canvas.create_text(LABEL_WIDTH - 6, top + BAR_HEIGHT / 2.0, anchor="e", fill=TEXT,
                               text=_clip(label_of(row.spec_id) or "?", 22))
            canvas.create_rectangle(LABEL_WIDTH, top, LABEL_WIDTH + max(length, 1),
                                    top + BAR_HEIGHT, fill=colour, outline=colour)
            canvas.create_text(LABEL_WIDTH + length + 6, top + BAR_HEIGHT / 2.0, anchor="w",
                               fill=TEXT, text=value_text(row.median))
        if len(group.rows) > MAX_BARS:
            canvas.create_text(8, CHART_HEIGHT - 10, anchor="w", fill=TEXT, text=_(
                "… et %d autres dans le tableau") % (len(group.rows) - MAX_BARS))


def _clip(text, length):
    return text if len(text) <= length else text[:length - 1] + "…"
