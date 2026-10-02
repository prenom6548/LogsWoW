# SPDX-License-Identifier: AGPL-3.0-or-later
"""The history window's "Records" tab: the best key and the best kill of each specialization.

It draws what `history_views.key_records` and `kill_groups` compute. Above, one row per
specialization with its best finished key (the highest one in time, then the score, then the
shortest time); below, a boss and a difficulty chosen from the list, and for each
specialization its fastest kill of that boss.

A board of records, not a ranking: rows are in a neutral order (role, then name), and the
context sits beside every record -- the item level, the group, the character, the date --
because a record says as much about the group and the gear as about the specialization.
"""

from . import fmt, history_views
from .gui_evolution import value_text
from .gui_specs import FolderCharacters
from .i18n import _
from .preview import ilvl_text, metric_label
from .specs import label_of
from .timestamps import format_duration


# -- rows, testable without a screen -----------------------------------------------------------

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


def notes_for(key_unknown, kill_unknown, records, groups):
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


# -- the tab ---------------------------------------------------------------------------------------

class RecordsTab(FolderCharacters):
    """The tab, built into `parent` (a frame of the history window's notebook)."""

    def __init__(self, window, parent):
        self.window = window
        self.parent = parent
        self.guids = []
        self.records = []
        self.groups = []
        self._build()

    def _build(self):
        app = self.window.app
        tk, ttk = app.tk, app.ttk
        frame = self.parent
        frame.columnconfigure(0, weight=1)
        frame.rowconfigure(2, weight=2)
        frame.rowconfigure(3, weight=3)

        choose = ttk.Frame(frame)
        choose.grid(row=0, column=0, sticky="ew")
        ttk.Label(choose, text=_("Personnage :")).pack(side="left")
        self.who = tk.StringVar()
        self.who_box = ttk.Combobox(choose, textvariable=self.who, state="readonly", width=30)
        self.who_box.pack(side="left", padx=(6, 0))
        self.who_box.bind("<<ComboboxSelected>>", lambda _event: self.redraw())

        self.message = ttk.Label(frame, text="", justify="left", wraplength=1000)
        self.message.grid(row=1, column=0, sticky="ew", pady=(8, 0))

        keys = ttk.LabelFrame(frame, text=_(" Meilleure clé par spécialisation "), padding=6)
        keys.grid(row=2, column=0, sticky="nsew", pady=(8, 0))
        keys.columnconfigure(0, weight=1)
        keys.rowconfigure(0, weight=1)
        self.key_table = app._table(keys, (
            ("spec", _("Spécialisation"), 215), ("dungeon", _("Donjon"), 185),
            ("level", _("Niveau"), 68), ("timely", _("En temps"), 78), ("time", _("Temps"), 58),
            ("score", _("Score"), 56), ("ilvl", "ilvl", 56), ("date", _("Date"), 88),
            ("who", _("Personnage"), 104), ("group", _("Groupe"), 68), ("timed", _("Clés"), 54),
            ("figure", _("Chiffre"), 126)), height=7, select="browse")
        self.key_table.master.grid(row=0, column=0, sticky="nsew")

        kills = ttk.LabelFrame(frame, text=_(" Meilleur kill par spécialisation "), padding=6)
        kills.grid(row=3, column=0, sticky="nsew", pady=(8, 0))
        kills.columnconfigure(1, weight=1)
        kills.rowconfigure(0, weight=1)
        self.boss_table = app._table(kills, (
            ("boss", _("Boss"), 170), ("level", _("Difficulté"), 84), ("kills", _("Kills"), 48),
            ("specs", _("Spés"), 44)), height=6, select="browse")
        self.boss_table.master.grid(row=0, column=0, sticky="nsew", padx=(0, 8))
        self.boss_table.bind("<<TreeviewSelect>>", lambda _event: self._fill_kills())
        self.kill_table = app._table(kills, (
            ("spec", _("Spécialisation"), 215), ("time", _("Durée"), 62), ("ilvl", "ilvl", 56),
            ("date", _("Date"), 88), ("who", _("Personnage"), 104), ("group", _("Groupe"), 68),
            ("kills", _("Kills"), 48), ("figure", _("Chiffre"), 126)), height=6, select="browse")
        self.kill_table.master.grid(row=0, column=1, sticky="nsew")

        self.note = ttk.Label(frame, justify="left", wraplength=1000, foreground="#555", text=_(
            "Meilleure clé : la plus haute clé terminée dans les temps ; à niveau égal, le "
            "meilleur score, puis le temps le plus court. Une clé terminée hors des temps ne "
            "passe devant que si la spécialisation n'en a aucune dans les temps. Meilleur kill : "
            "le plus rapide d'un même boss de raid à la même difficulté. Ce sont les records de "
            "chaque spécialisation, rangés par rôle : pas un classement, et pas un parse. Ils "
            "dépendent du groupe, du niveau d'objet et des affixes, affichés à côté. Groupe : "
            "tanks / soigneurs / dps ; Clés : dans les temps / terminées."))
        self.note.grid(row=4, column=0, sticky="ew", pady=(8, 0))
        self.warnings = ttk.Label(frame, justify="left", wraplength=1000, foreground="#8a4b00",
                                  text="")
        self.warnings.grid(row=5, column=0, sticky="ew", pady=(4, 0))

    # -- showing -------------------------------------------------------------------------------

    def refresh(self):
        self._load_characters()
        self.redraw()

    def redraw(self):
        """Recompute both boards for the characters chosen."""
        self.records, self.groups = [], []
        if not self.guids:
            self.message.configure(text=_(
                "Aucun personnage suivi dans ce dossier : suivez-en un dans l'onglet « Soirées », "
                "puis ajoutez des soirées."))
            self._clear()
            return
        runs = self._runs()
        self.records, key_unknown = history_views.key_records(runs)
        self.groups, kill_unknown = history_views.kill_groups(runs)
        self.message.configure(text="" if self.records or self.groups else _(
            "Aucune clé terminée ni aucun kill de raid dans ce dossier pour l'instant."))
        self.key_table.delete(*self.key_table.get_children())
        for number, row in enumerate(key_rows(self.records)):
            self.key_table.insert("", "end", iid=str(number), values=row)
        self.boss_table.delete(*self.boss_table.get_children())
        for number, row in enumerate(boss_rows(self.groups)):
            self.boss_table.insert("", "end", iid=str(number), values=row)
        self.warnings.configure(text="\n".join(
            notes_for(key_unknown, kill_unknown, self.records, self.groups)))
        if self.groups:
            self.boss_table.selection_set("0")
        self._fill_kills()

    def _clear(self):
        for table in (self.key_table, self.boss_table, self.kill_table):
            table.delete(*table.get_children())
        self.warnings.configure(text="")

    def _fill_kills(self):
        self.kill_table.delete(*self.kill_table.get_children())
        selected = self.boss_table.selection()
        if selected:
            group = self.groups[int(selected[0])]
        elif self.groups:
            group = self.groups[0]
        else:
            return
        for number, row in enumerate(kill_rows(group)):
            self.kill_table.insert("", "end", iid=str(number), values=row)
