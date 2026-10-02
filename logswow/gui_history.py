# SPDX-License-Identifier: AGPL-3.0-or-later
"""The history's window: folders, who to follow, the nights kept.

The rules are in `history.py`; this is how the reader reaches them. Asked for by
the owner on 2026-10-02: off by default with a simple way to purge, an explanation
on first use and a first folder created then, a menu to make another folder at any
time, the characters to follow ticked by the reader, and nothing written without
their word -- except through one setting they switch on themselves.

The logic that needs no screen is at the top (`player_rows`, `night_rows`,
`pending_suggestion`, `save_current`, `autosave`) and is tested without one; the
window is `HistoryWindow`, tested when a display exists.
"""

import os

from . import fmt, history, report_history
from .gui_evolution import EvolutionTab
from .gui_records import RecordsTab
from .gui_specs import SpecsTab
from .i18n import N_, _
from .preview import role_word
from .specs import label_of

INTRO_FIRST = N_(
    "L'historique garde, soirée après soirée, les chiffres de vos personnages pour voir "
    "comment vous évoluez : un petit fichier par soirée (environ 30 Ko), rangé dans le "
    "dossier de votre choix, sur cet ordinateur uniquement. Rien n'est enregistré sans votre "
    "accord, et seuls les personnages que vous suivez y laissent leur nom ; les autres "
    "joueurs n'apparaissent que dans les totaux du groupe. Commencez par créer un dossier "
    "(par exemple une saison, ou « avec mes amis »).")
INTRO_SHORT = N_(
    "Rien n'est enregistré sans votre accord. Seuls les personnages suivis y laissent leur "
    "nom ; les autres joueurs n'apparaissent que dans les totaux du groupe.")


# -- logic, testable without a screen ---------------------------------------------------

def player_rows(segments, followed):
    """[(guid, '✓' or '', name, specialization, role, fights)] of the log's players.

    `followed` is a collection of GUIDs; the followed ones come first, then by name.
    """
    rows = []
    for guid, name, spec_id, role, fights in history.players_seen(segments):
        rows.append((guid, "✓" if guid in followed else "", name,
                     label_of(spec_id) or "?", role_word(role), fights))
    rows.sort(key=lambda row: (row[1] == "", row[2].lower()))
    return rows


def night_rows(nights):
    """[(path, date, source, game version, fights, size)] of the nights, oldest first."""
    return [(night.path, night.date, night.source, night.build or "?", night.fights,
             fmt.size(night.size_bytes)) for night in nights]


def folder_label(folder):
    """'Saison 1 (3 soirées)': what the folder list shows."""
    return "%s (%s)" % (folder.name, fmt.plural(folder.nights, "soirée"))


def pending_suggestion(root, log):
    """('patch' | 'extension', previous build, new build) when this log asks for a new folder.

    Compared with the newest night of the active folder; a log older than what the folder
    holds, or without a version, suggests nothing.
    """
    slug = history.config(root)["dossier_actif"]
    builds = [night.build for night in history.list_nights(root, slug) if night.build] if slug \
        else []
    if not builds or not getattr(log, "build_version", ""):
        return None
    kind = history.suggest_new_folder(builds[-1], log.build_version)
    return (kind, builds[-1], log.build_version) if kind else None


def suggestion_text(suggestion):
    kind, before, after = suggestion
    if kind == "extension":
        return _("La version du jeu est passée de %s à %s : une nouvelle extension. Les chiffres "
                 "des soirées suivantes ne sont pas comparables à ceux d'avant. Commencer un "
                 "nouveau dossier ?") % (before, after)
    return _("La version du jeu est passée de %s à %s : un nouveau patch. Les chiffres des "
             "soirées suivantes ne sont pas forcément comparables à ceux d'avant. Commencer un "
             "nouveau dossier ?") % (before, after)


def followed_present(root, segments):
    """The GUIDs of the followed characters who took part in this log."""
    followed = history.tracked(root)
    return [row[0] for row in history.players_seen(segments) if row[0] in followed]


def save_current(root, log, segments, slug=None):
    """Write this log's night into a folder (the active one by default).

    Every followed character is kept; the others only count in the group's totals.
    Returns (path, replaced, folder name). Raises `HistoryError` with a message ready to show.
    """
    folders = {folder.slug: folder for folder in history.list_folders(root)}
    slug = slug or history.config(root)["dossier_actif"]
    if slug not in folders:
        raise history.HistoryError(_("Choisissez d'abord un dossier."))
    record = history.build_night(log, segments, list(history.tracked(root)))
    if not record["fights"]:
        raise history.HistoryError(_("Aucun combat à enregistrer dans ce journal."))
    path, replaced = history.save_night(root, slug, record)
    return path, replaced, folders[slug].name


def autosave(root, log, segments):
    """What the 'save every log' setting does after a read; (path, replaced, folder) or None.

    Off unless the reader switched it on, and even then only when a followed character
    took part (a pick-up night is not worth a file), and never while a new folder is being
    suggested: the night would land in the folder the game's version has just left.
    """
    settings = history.config(root)
    if not settings["automatique"] or not settings["dossier_actif"]:
        return None
    if not followed_present(root, segments) or pending_suggestion(root, log) is not None:
        return None
    try:
        return save_current(root, log, segments)
    except history.HistoryError:
        return None


# -- the window ---------------------------------------------------------------------------------

class HistoryWindow:
    """The history's window, opened from the main window and kept in step with it."""

    def __init__(self, app):
        self.app = app
        self.top = None
        self._slugs = []        # the folders, in the order the list shows them

    # Dialogs go through these, so a test can answer them without a screen to click.

    def _ask_name(self, title, prompt, initial=""):
        from tkinter import simpledialog

        return simpledialog.askstring(title, prompt, initialvalue=initial, parent=self.top)

    def _confirm(self, title, text):
        from tkinter import messagebox

        return messagebox.askyesno(title, text, parent=self.top)

    def _error(self, text):
        from tkinter import messagebox

        messagebox.showerror("LogsWoW", text, parent=self.top)

    def _inform(self, text):
        from tkinter import messagebox

        messagebox.showinfo("LogsWoW", text, parent=self.top)

    def _ask_page_path(self, initial):
        """Where to write the history's page: a path, or "" when the reader gives up."""
        from tkinter import filedialog

        return filedialog.asksaveasfilename(
            parent=self.top, title=_("Où écrire la page de l'historique ?"),
            initialdir=os.path.expanduser("~"), initialfile=initial, defaultextension=".html",
            filetypes=((_("Page web"), "*.html"),))

    def _open_page(self, path):
        from . import gui

        gui.open_in_browser(path)

    def write_page(self):
        """Write the active folder's page (evolution, specializations, records) and open it."""
        slug = history.config(self.root)["dossier_actif"]
        if not slug:
            self._error(_("Choisissez d'abord un dossier."))
            return
        out = self._ask_page_path("historique-%s.html" % slug)
        if not out:
            return
        reason = report_history.write_page(self.root, slug, out)
        if reason:
            self._error(reason)
            return
        self._open_page(out)
        self.refresh(_("Page écrite : %s") % out)

    def _pick_folder(self, title, prompt, choices):
        """A folder among `choices` ([(slug, label)]), or None: a small modal list."""
        ttk, tk = self.app.ttk, self.app.tk
        dialog = tk.Toplevel(self.top)
        dialog.title(title)
        dialog.transient(self.top)
        ttk.Label(dialog, text=prompt, padding=(12, 12, 12, 6)).pack(anchor="w")
        value = tk.StringVar(value=choices[0][1])
        box = ttk.Combobox(dialog, textvariable=value, values=[label for _s, label in choices],
                           state="readonly", width=40)
        box.pack(padx=12)
        chosen = []

        def accept():
            chosen.append(choices[box.current()][0])
            dialog.destroy()

        line = ttk.Frame(dialog, padding=12)
        line.pack(fill="x")
        ttk.Button(line, text=_("Annuler"), command=dialog.destroy).pack(side="right")
        ttk.Button(line, text="OK", command=accept).pack(side="right", padx=(0, 6))
        dialog.grab_set()
        dialog.wait_window()
        return chosen[0] if chosen else None

    # -- building ------------------------------------------------------------------

    def show(self):
        """Open the window, or bring the open one forward."""
        if self.top is not None:
            self.top.deiconify()
            self.top.lift()
            self.refresh()
            return
        self._build()
        self.refresh()

    def close(self):
        if self.top is not None:
            self.top.destroy()
            self.top = None

    def _build(self):
        tk, ttk = self.app.tk, self.app.ttk
        top = self.top = tk.Toplevel(self.app.root)
        top.title(_("Historique"))
        top.minsize(1000, 720)
        top.geometry("1260x880")
        top.protocol("WM_DELETE_WINDOW", self.close)
        buttons = ttk.Frame(top)
        buttons.pack(side="bottom", fill="x", padx=12, pady=(0, 12))
        ttk.Button(buttons, text=_("Fermer"), command=self.close).pack(side="right")
        ttk.Button(buttons, text=_("Écrire la page…"), command=self.write_page).pack(side="left")
        book = ttk.Notebook(top)
        book.pack(fill="both", expand=True, padx=6, pady=(6, 6))
        outer = ttk.Frame(book, padding=12)
        book.add(outer, text=_("Soirées"))
        evolution = ttk.Frame(book, padding=12)
        book.add(evolution, text=_("Évolution"))
        self.book = book
        self.evolution = EvolutionTab(self, evolution)
        specs = ttk.Frame(book, padding=12)
        book.add(specs, text=_("Spécialisations"))
        self.specs = SpecsTab(self, specs)
        records = ttk.Frame(book, padding=12)
        book.add(records, text=_("Records"))
        self.records = RecordsTab(self, records)
        outer.columnconfigure(0, weight=1)
        outer.rowconfigure(3, weight=1)
        outer.rowconfigure(6, weight=1)

        self.intro = ttk.Label(outer, justify="left", wraplength=780)
        self.intro.grid(row=0, column=0, sticky="ew")

        self.suggestion_box = ttk.Frame(outer)
        self.suggestion_box.columnconfigure(0, weight=1)
        self.suggestion_label = ttk.Label(self.suggestion_box, justify="left", wraplength=640,
                                          foreground="#8a4b00")
        self.suggestion_label.grid(row=0, column=0, sticky="w")
        ttk.Button(self.suggestion_box, text=_("Créer un nouveau dossier…"),
                   command=self.new_folder).grid(row=0, column=1, padx=(8, 0))
        ttk.Button(self.suggestion_box, text=_("Ignorer"),
                   command=self.dismiss_suggestion).grid(row=0, column=2, padx=(6, 0))
        self.suggestion_box.grid(row=1, column=0, sticky="ew", pady=(8, 0))

        folders = ttk.Frame(outer)
        folders.grid(row=2, column=0, sticky="ew", pady=(10, 0))
        ttk.Label(folders, text=_("Dossier :")).pack(side="left")
        self.folder_choice = tk.StringVar()
        self.folder_box = ttk.Combobox(folders, textvariable=self.folder_choice,
                                       state="readonly", width=34)
        self.folder_box.pack(side="left", padx=(6, 12))
        self.folder_box.bind("<<ComboboxSelected>>", lambda _event: self.choose_folder())
        self.new_button = ttk.Button(folders, text=_("Nouveau dossier…"), command=self.new_folder)
        self.new_button.pack(side="left")
        self.rename_button = ttk.Button(folders, text=_("Renommer…"), command=self.rename_folder)
        self.rename_button.pack(side="left", padx=(6, 0))
        self.delete_folder_button = ttk.Button(folders, text=_("Supprimer ce dossier…"),
                                               command=self.delete_folder)
        self.delete_folder_button.pack(side="left", padx=(6, 0))

        self.who = ttk.LabelFrame(outer, text=_(" Personnages de ce journal "), padding=8)
        self.who.grid(row=3, column=0, sticky="nsew", pady=(10, 0))
        self.who.columnconfigure(0, weight=1)
        self.who.rowconfigure(0, weight=1)
        self.players = self.app._table(self.who, (
            ("mark", _("Suivi"), 50), ("name", _("Joueur"), 190),
            ("spec", _("Spécialisation"), 210), ("role", _("Rôle"), 100),
            ("fights", _("Combats"), 84)), height=6, select="extended")
        self.players.master.grid(row=0, column=0, sticky="nsew")
        self.players.bind("<<TreeviewSelect>>", lambda _event: self._buttons())
        line = ttk.Frame(self.who)
        line.grid(row=1, column=0, sticky="ew", pady=(8, 0))
        self.follow_button = ttk.Button(line, text=_("Suivre la sélection"), command=self.follow)
        self.follow_button.pack(side="left")
        self.unfollow_button = ttk.Button(line, text=_("Ne plus suivre"), command=self.unfollow)
        self.unfollow_button.pack(side="left", padx=(6, 0))
        self.followed_label = ttk.Label(line, text="")
        self.followed_label.pack(side="left", padx=(12, 0))

        add = ttk.Frame(outer)
        add.grid(row=5, column=0, sticky="ew", pady=(10, 0))
        self.add_button = ttk.Button(add, text=_("Ajouter cette soirée à l'historique"),
                                     style="Accent.TButton", command=self.add_night)
        self.add_button.grid(row=0, column=0, sticky="w")
        self.automatic = tk.BooleanVar(value=False)
        self.automatic_box = ttk.Checkbutton(
            add, variable=self.automatic, command=self.toggle_automatic,
            text=_("Enregistrer automatiquement chaque journal lu (seulement si un personnage "
                   "suivi y a joué)"))
        self.automatic_box.grid(row=1, column=0, sticky="w", pady=(6, 0))

        self.kept = ttk.LabelFrame(outer, text=_(" Soirées de ce dossier "), padding=8)
        self.kept.grid(row=6, column=0, sticky="nsew", pady=(10, 0))
        self.kept.columnconfigure(0, weight=1)
        self.kept.rowconfigure(0, weight=1)
        self.nights = self.app._table(self.kept, (
            ("date", _("Date"), 100), ("source", _("Journal"), 280), ("game", _("Jeu"), 70),
            ("fights", _("Combats"), 84), ("size", _("Taille"), 80)), height=6, select="extended")
        self.nights.master.grid(row=0, column=0, sticky="nsew")
        self.nights.bind("<<TreeviewSelect>>", lambda _event: self._buttons())
        line = ttk.Frame(self.kept)
        line.grid(row=1, column=0, sticky="ew", pady=(8, 0))
        self.delete_night_button = ttk.Button(line, text=_("Supprimer la soirée"),
                                              command=self.delete_nights)
        self.delete_night_button.pack(side="left")
        self.move_button = ttk.Button(line, text=_("Déplacer vers un autre dossier…"),
                                      command=self.move_nights)
        self.move_button.pack(side="left", padx=(6, 0))

        self.status = tk.StringVar(value="")
        ttk.Label(outer, textvariable=self.status, anchor="w", wraplength=780,
                  justify="left").grid(row=7, column=0, sticky="ew", pady=(10, 0))

    # -- showing the state ---------------------------------------------------------

    @property
    def root(self):
        return self.app.history_root

    def refresh(self, message=""):
        """Redraw everything from the files and from the log last read.

        `message` is what the line at the bottom says afterwards; without one it says what
        is missing to go on, if anything is.
        """
        if self.top is None:
            return
        folders = history.list_folders(self.root)
        self._slugs = [folder.slug for folder in folders]
        settings = history.config(self.root)
        active = settings["dossier_actif"] if settings["dossier_actif"] in self._slugs else (
            self._slugs[0] if self._slugs else "")
        self.folder_box.configure(values=[folder_label(folder) for folder in folders])
        if active:
            self.folder_box.current(self._slugs.index(active))
        else:
            self.folder_choice.set("")
        self.intro.configure(text=_(INTRO_SHORT if folders else INTRO_FIRST))
        self.automatic.set(settings["automatique"])
        self._fill_players()
        self._fill_nights(active)
        suggestion = self.app.history_suggestion
        if suggestion is not None and folders:
            self.suggestion_label.configure(text=suggestion_text(suggestion))
            self.suggestion_box.grid()
        else:
            self.suggestion_box.grid_remove()
        self._buttons()
        self.status.set(message or self._hint())
        self.evolution.refresh()
        self.specs.refresh()
        self.records.refresh()

    def _fill_players(self):
        self.players.delete(*self.players.get_children())
        segments = self.app.segments or []
        rows = player_rows(segments, history.tracked(self.root)) if segments else []
        for row in rows:
            self.players.insert("", "end", iid=row[0], values=row[1:])
        count = len(history.tracked(self.root))
        self.followed_label.configure(
            text=_("Personnages suivis au total : %d") % count if count
            else _("Aucun personnage suivi."))

    def _fill_nights(self, slug):
        self.nights.delete(*self.nights.get_children())
        for row in night_rows(history.list_nights(self.root, slug) if slug else []):
            self.nights.insert("", "end", iid=row[0], values=row[1:])

    def _buttons(self):
        def state(widget, on):
            widget.state(["!disabled"] if on else ["disabled"])

        have_folder = bool(self._slugs)
        have_log = bool(self.app.segments)
        state(self.rename_button, have_folder)
        state(self.delete_folder_button, have_folder)
        state(self.follow_button, have_log and bool(self.players.selection()))
        state(self.unfollow_button, have_log and bool(self.players.selection()))
        state(self.add_button, have_folder and have_log and not self.app.busy)
        state(self.automatic_box, have_folder)
        state(self.delete_night_button, bool(self.nights.selection()))
        state(self.move_button, len(self._slugs) > 1 and bool(self.nights.selection()))

    def _hint(self):
        """What is missing before a night can be added, or ''."""
        if not self._slugs:
            return _("Créez un dossier pour commencer.")
        if not self.app.segments:
            return _("Aucun journal lu : lisez un journal dans la fenêtre principale pour "
                     "pouvoir ajouter une soirée.")
        return ""

    # -- the folders ---------------------------------------------------------------

    def choose_folder(self):
        index = self.folder_box.current()
        if 0 <= index < len(self._slugs):
            history.set_config(self.root, dossier_actif=self._slugs[index])
            self.app.history_suggestion = (pending_suggestion(self.root, self.app.log)
                                           if self.app.log is not None else None)
            self.refresh()

    def new_folder(self):
        name = self._ask_name(_("Nouveau dossier"),
                              _("Nom du dossier (par exemple « Saison 1 », « Avec mes amis ») :"))
        if name is None:
            return
        try:
            slug = history.create_folder(self.root, name)
            history.set_config(self.root, dossier_actif=slug)
        except history.HistoryError as error:
            self._error(str(error))
            return
        self.app.history_suggestion = None       # the night goes to the new folder: no more to ask
        self.refresh(_("Dossier créé : %s") % name.strip())

    def rename_folder(self):
        if not self._slugs:
            return
        slug = self._slugs[max(0, self.folder_box.current())]
        current = [folder.name for folder in history.list_folders(self.root)
                   if folder.slug == slug][0]
        name = self._ask_name(_("Renommer le dossier"), _("Nouveau nom du dossier :"), current)
        if name is None:
            return
        try:
            history.rename_folder(self.root, slug, name)
        except history.HistoryError as error:
            self._error(str(error))
            return
        self.refresh()

    def delete_folder(self):
        if not self._slugs:
            return
        slug = self._slugs[max(0, self.folder_box.current())]
        folder = [item for item in history.list_folders(self.root) if item.slug == slug][0]
        if not self._confirm(_("Supprimer le dossier"), _(
                "Supprimer le dossier « %s » et ses %s ? Cela ne touche pas à vos journaux de "
                "combat.") % (folder.name, fmt.plural(folder.nights, "soirée"))):
            return
        try:
            removed = history.delete_folder(self.root, slug)
        except history.HistoryError as error:
            self._error(str(error))
            return
        self.refresh(_("Dossier supprimé : %s (%s).")
                     % (folder.name, fmt.plural(removed, "soirée")))

    # -- who to follow -------------------------------------------------------------

    def _selected_players(self):
        wanted = set(self.players.selection())
        return [(row[0], row[2]) for row in history.players_seen(self.app.segments or [])
                if row[0] in wanted]

    def follow(self):
        for guid, name in self._selected_players():
            history.track(self.root, guid, name)
        self.refresh()

    def unfollow(self):
        for guid, _name in self._selected_players():
            history.untrack(self.root, guid)
        self.refresh()

    # -- the nights ----------------------------------------------------------------

    def add_night(self):
        """The button: this log's night into the active folder, after one question if needed."""
        app = self.app
        if not app.segments or app.log is None:
            return
        if not followed_present(self.root, app.segments):
            if not self._confirm(_("Ajouter à l'historique"), _(
                    "Aucun personnage suivi dans ce journal : la soirée ne gardera que les "
                    "totaux du groupe. L'enregistrer quand même ?")):
                return
        try:
            _path, replaced, name = save_current(self.root, app.log, app.segments)
        except history.HistoryError as error:
            self._error(str(error))
            return
        self.refresh((_("Soirée déjà dans l'historique : mise à jour (dossier « %s »).")
                      if replaced else _("Soirée ajoutée à l'historique (dossier « %s »).")) % name)

    def toggle_automatic(self):
        history.set_config(self.root, automatique=bool(self.automatic.get()))

    def dismiss_suggestion(self):
        self.app.history_suggestion = None
        self.refresh()

    def _selected_nights(self):
        return list(self.nights.selection())

    def delete_nights(self):
        paths = self._selected_nights()
        if not paths:
            return
        if not self._confirm(_("Supprimer la soirée"), _(
                "Supprimer %s de l'historique ? Vos journaux de combat ne sont pas touchés.")
                % fmt.plural(len(paths), "soirée")):
            return
        try:
            for path in paths:
                history.delete_night(self.root, path)
        except history.HistoryError as error:
            self._error(str(error))
        self.refresh()

    def move_nights(self):
        paths = self._selected_nights()
        current = self._slugs[max(0, self.folder_box.current())] if self._slugs else ""
        choices = [(folder.slug, folder_label(folder)) for folder in history.list_folders(self.root)
                   if folder.slug != current]
        if not paths or not choices:
            return
        target = self._pick_folder(_("Déplacer la soirée"), _("Dossier de destination :"), choices)
        if target is None:
            return
        try:
            for path in paths:
                history.move_night(self.root, path, target)
        except history.HistoryError as error:
            self._error(str(error))
        self.refresh()
