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

from . import history_views
from .gui_specs import FolderCharacters
from .history_tables import (BOSSES, KEY_RECORDS, KILL_RECORDS, NO_FOLLOWED, NO_RECORDS,
                             RECORD_NOTE, boss_rows, key_rows, kill_rows, record_notes,
                             window_columns)
from .i18n import _


notes_for = record_notes             # the name the tests and this tab have always used


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
        self.key_table = app._table(keys, window_columns(KEY_RECORDS), height=7,
                                    select="browse")
        self.key_table.master.grid(row=0, column=0, sticky="nsew")

        kills = ttk.LabelFrame(frame, text=_(" Meilleur kill par spécialisation "), padding=6)
        kills.grid(row=3, column=0, sticky="nsew", pady=(8, 0))
        kills.columnconfigure(1, weight=1)
        kills.rowconfigure(0, weight=1)
        self.boss_table = app._table(kills, window_columns(BOSSES), height=6, select="browse")
        self.boss_table.master.grid(row=0, column=0, sticky="nsew", padx=(0, 8))
        self.boss_table.bind("<<TreeviewSelect>>", lambda _event: self._fill_kills())
        self.kill_table = app._table(kills, window_columns(KILL_RECORDS), height=6,
                                     select="browse")
        self.kill_table.master.grid(row=0, column=1, sticky="nsew")

        self.note = ttk.Label(frame, justify="left", wraplength=1000, foreground="#555",
                              text=_(RECORD_NOTE))
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
            self.message.configure(text=_(NO_FOLLOWED))
            self._clear()
            return
        runs = self._runs()
        self.records, key_unknown = history_views.key_records(runs)
        self.groups, kill_unknown = history_views.kill_groups(runs)
        self.message.configure(text="" if self.records or self.groups else _(NO_RECORDS))
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
