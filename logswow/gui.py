"""A window, for whoever would rather click than type.

Asked for by the owner on 2026-09-27, after a first try in a terminal:
"une interface graphique plutot que des lignes dans un terminal serait
plus user friendly". It does nothing the command line does not; it puts
the same three steps -- pick a log, pick the fights, write the page -- in
one window, and opens the page in the browser when it is written.

Tkinter, because it is the one toolkit in Python's standard library, and
this project installs nothing. Two consequences, both handled rather
than hidden:

- Some Linux distributions ship it as a separate package (Linux Mint,
  Ubuntu and Debian: python3-tk). Without it, launching the window says
  which command installs it, and the terminal commands keep working.
- It needs a display. On a machine without one, `python3 -m logswow`
  prints the help, as it always did.

Nothing here opens a socket either: `webbrowser` hands a *local file* to
the system's browser, and the page it opens fetches nothing.

The logic (what to list, how to read, where to write) is in plain
functions at the top, so it is tested without a screen; the `App` class
below only arranges widgets around them. Tkinter is not thread-safe:
the long work runs in a thread that talks to the window through a queue,
and only the window's own loop touches a widget.
"""

import os
import pathlib
import queue
import subprocess
import sys
import threading
import time
import traceback
import webbrowser

from . import __version__
from .analysis import PULL_GAP_MS
from .cli import (Cancelled, _build, _refuse_folder, _refuse_to_overwrite,
                  default_log_locations)
from .report import ReportWriter
from .timestamps import format_duration

# Measured on the owner's sixteen logs (2026-09-27): 305 to 322 bytes a
# line, median 310. The reader counts lines, not bytes, so this turns a
# line count into a share of the file -- close enough for a bar, and the
# bar never claims to be done before the read is.
BYTES_PER_LINE = 310

# What to type when the toolkit itself is missing, by system. The
# message names the command rather than a web page to read.
TK_MISSING = (
    "La fenetre de LogsWoW a besoin de Tkinter, qui fait partie de Python mais\n"
    "que certaines distributions Linux livrent a part. Pour l'installer :\n"
    "  Linux Mint, Ubuntu, Debian : sudo apt install python3-tk\n"
    "  Fedora                     : sudo dnf install python3-tkinter\n"
    "  Arch, Manjaro              : sudo pacman -S tk\n"
    "  openSUSE                   : sudo zypper install python3-tk\n"
    "  macOS (Homebrew)           : brew install python-tk\n"
    "Sous Windows, et sous macOS avec l'installateur de python.org, il est deja la.\n"
    "Les commandes du terminal fonctionnent sans lui (voir ci-dessous).\n"
)


# -- the logic, testable without a screen ------------------------------------

def recent_logs(locations=None, limit=40):
    """[(path, size, mtime)] of the combat logs found, newest first."""
    if locations is None:
        locations = default_log_locations()
    found = []
    for directory in locations:
        try:
            names = os.listdir(directory)
        except OSError:
            continue
        for name in names:
            if not (name.startswith("WoWCombatLog") and name.lower().endswith(".txt")):
                continue
            path = os.path.join(directory, name)
            try:
                stat = os.stat(path)
            except OSError:
                continue
            found.append((path, stat.st_size, stat.st_mtime))
    found.sort(key=lambda entry: -entry[2])
    return found[:limit]


def file_size(size):
    """1234567 -> '1,2 Mo', in the units a French reader expects."""
    for unit, scale in (("Go", 1e9), ("Mo", 1e6), ("Ko", 1e3)):
        if size >= scale:
            return ("%.1f %s" % (size / scale, unit)).replace(".", ",")
    return "%d o" % size


def read_share(lines, size):
    """How far through the file `lines` lines probably are, from 0 to 0.99."""
    if size <= 0:
        return 0.0
    return min(0.99, lines * BYTES_PER_LINE / size)


# `Segment.outcome` is written without accents, for the terminal; a
# window can print them.
_OUTCOMES = {"reussite": "réussite", "echec": "échec"}


def fight_rows(segments):
    """One tuple per fight, as the list of fights shows it."""
    return [
        (segment.index, segment.label,
         format_duration(segment.analysis.duration_ms),
         "{:,}".format(segment.analysis.total_damage).replace(",", " "),
         len(segment.analysis.deaths), _OUTCOMES.get(segment.outcome, segment.outcome))
        for segment in segments
    ]


# The three presentations of report_layouts.py, as the window names them.
LAYOUT_CHOICES = (
    ("onglets", "Onglets (un fichier)"),
    ("pages", "Pages (un dossier)"),
    ("longue", "Une seule longue page"),
)


def default_report_path(log_path, chosen, segments, layout="onglets"):
    """Next to the log, under its name; one fight gets its number in the name.

    A page for "onglets" and "longue", a folder for "pages".
    """
    stem = os.path.splitext(log_path)[0]
    if len(chosen) == 1 and len(segments) > 1:
        stem = "%s-combat-%d" % (stem, chosen[0].index)
    return stem if layout == "pages" else stem + ".html"


def report_entry(out, layout):
    """The file to open: the page itself, or the folder's index.html."""
    return os.path.join(out, "index.html") if layout == "pages" else out


def _refusal(out, log_path, layout):
    if layout == "pages":
        return _refuse_folder(out, log_path, force=False)
    return _refuse_to_overwrite(out, log_path, force=False)


def write_report(log, chosen, out, log_path, cast_order=True, layout="onglets"):
    """Write the report, or say in French why not. Returns None or the reason."""
    refusal = _refusal(out, log_path, layout)
    if refusal:
        return refusal.strip()
    try:
        ReportWriter(log, chosen, out, cast_order=cast_order, layout=layout).write()
    except OSError as error:
        return "Impossible d'ecrire %s : %s" % (out, error.strerror or error)
    return None


def page_address(path):
    """The file:// address of a local page, spaces and accents encoded.

    The owner's logs live in ".../World of Warcraft/_retail_/Logs": a
    hand-made "file://" + path would hand the browser a broken address.
    """
    return pathlib.Path(os.path.abspath(path)).as_uri()


def open_in_browser(path):
    """Hand a local page to the system's browser. Nothing is downloaded."""
    return webbrowser.open(page_address(path))


def open_folder(path):
    """Show the folder that holds `path` in the system's file manager."""
    folder = os.path.dirname(os.path.abspath(path))
    if os.name == "nt":
        os.startfile(folder)  # nosec B606 -- a folder the reader chose, opened locally
    elif sys.platform == "darwin":
        subprocess.Popen(["open", folder])  # nosec B603 B607
    else:
        subprocess.Popen(["xdg-open", folder])  # nosec B603 B607


# -- the window -----------------------------------------------------------------

def run():
    """Open the window. Returns an exit code, or None when there is no screen."""
    try:
        import tkinter
    except ImportError:
        if sys.stderr is not None:          # None when started by pythonw (a .pyzw)
            sys.stderr.write(TK_MISSING + "\n")
        return 3
    try:
        root = tkinter.Tk()
    except tkinter.TclError:
        return None                 # no display: the caller prints the help
    App(root)
    root.mainloop()
    return 0


class App:
    """The three steps, top to bottom, and a line at the bottom saying what happens."""

    def __init__(self, root, locations=None):
        import tkinter as tk
        from tkinter import ttk

        self.tk, self.ttk, self.root = tk, ttk, root
        self.locations = locations
        self.messages = queue.Queue()
        self.cancel = threading.Event()
        self.busy = False
        self.log = self.segments = self.log_path = None
        self.last_report = None

        root.title("LogsWoW %s" % __version__)
        root.minsize(760, 600)
        style = ttk.Style(root)
        if sys.platform.startswith("linux") and "clam" in style.theme_names():
            style.theme_use("clam")
        from tkinter import font

        bold = font.nametofont("TkDefaultFont").copy()
        bold.configure(weight="bold")
        style.configure("Accent.TButton", font=bold)
        self._bold = bold           # a font Tk no longer references is dropped

        outer = ttk.Frame(root, padding=12)
        outer.pack(fill="both", expand=True)
        outer.columnconfigure(0, weight=1)
        outer.rowconfigure(0, weight=1)
        outer.rowconfigure(1, weight=1)
        self._journal_box(outer).grid(row=0, column=0, sticky="nsew")
        self._fights_box(outer).grid(row=1, column=0, sticky="nsew", pady=(10, 0))
        self._report_box(outer).grid(row=2, column=0, sticky="ew", pady=(10, 0))
        self.status = tk.StringVar(value="Choisissez un journal, puis « Lire ce journal ».")
        ttk.Label(outer, textvariable=self.status, anchor="w").grid(
            row=3, column=0, sticky="ew", pady=(10, 0))
        ttk.Label(outer, text="Tout se passe sur cet ordinateur : aucune donnée n'est envoyée.",
                  foreground="#666").grid(row=4, column=0, sticky="w")

        self.refresh_logs()
        self._update_buttons()
        root.after(100, self._drain)

    # -- building -------------------------------------------------------------

    def _journal_box(self, parent):
        tk, ttk = self.tk, self.ttk
        box = ttk.LabelFrame(parent, text=" 1. Le journal ", padding=8)
        box.columnconfigure(0, weight=1)
        box.rowconfigure(0, weight=1)
        self.logs = self._table(box, (("file", "Fichier", 250), ("date", "Date", 130),
                                      ("size", "Taille", 80), ("folder", "Dossier", 260)),
                                height=6, select="browse")
        self.logs.master.grid(row=0, column=0, columnspan=2, sticky="nsew")
        self.logs.bind("<Double-1>", lambda _event: self.read_selected())
        self.logs.bind("<<TreeviewSelect>>", lambda _event: self._update_buttons())

        line = ttk.Frame(box)
        line.grid(row=1, column=0, columnspan=2, sticky="ew", pady=(8, 0))
        ttk.Button(line, text="Choisir un autre fichier…", command=self.choose_file).pack(
            side="left")
        ttk.Button(line, text="Actualiser la liste", command=self.refresh_logs).pack(
            side="left", padx=(6, 0))
        self.read_button = ttk.Button(line, text="Lire ce journal", style="Accent.TButton",
                                      command=self.read_selected)
        self.read_button.pack(side="right")
        self.gap = tk.StringVar(value=str(PULL_GAP_MS // 1000))
        ttk.Label(line, text=" s").pack(side="right", padx=(0, 12))
        ttk.Spinbox(line, from_=1, to=60, width=4, textvariable=self.gap).pack(side="right")
        ttk.Label(line, text="Silence entre deux pulls : ").pack(side="right")

        progress = ttk.Frame(box)
        progress.grid(row=2, column=0, columnspan=2, sticky="ew", pady=(8, 0))
        progress.columnconfigure(0, weight=1)
        self.bar = ttk.Progressbar(progress, maximum=1000)
        self.bar.grid(row=0, column=0, sticky="ew")
        self.cancel_button = ttk.Button(progress, text="Annuler", command=self.cancel.set)
        self.cancel_button.grid(row=0, column=1, padx=(6, 0))
        return box

    def _fights_box(self, parent):
        ttk = self.ttk
        box = ttk.LabelFrame(parent, text=" 2. Les combats ", padding=8)
        box.columnconfigure(0, weight=1)
        box.rowconfigure(0, weight=1)
        self.fights = self._table(box, (("n", "#", 40), ("fight", "Combat", 330),
                                        ("time", "Durée", 70), ("damage", "Dégâts", 120),
                                        ("deaths", "Morts", 60), ("outcome", "Issue", 110)),
                                  height=8, select="extended")
        self.fights.master.grid(row=0, column=0, sticky="nsew")
        self.fights.bind("<<TreeviewSelect>>", lambda _event: self._update_buttons())
        line = ttk.Frame(box)
        line.grid(row=1, column=0, sticky="ew", pady=(8, 0))
        ttk.Button(line, text="Tout sélectionner", command=self.select_all).pack(side="left")
        self.chosen_label = ttk.Label(line, text="")
        self.chosen_label.pack(side="left", padx=(12, 0))
        return box

    def _report_box(self, parent):
        tk, ttk = self.tk, self.ttk
        box = ttk.LabelFrame(parent, text=" 3. Le rapport ", padding=8)
        self.cast_order = tk.BooleanVar(value=True)
        ttk.Checkbutton(box, variable=self.cast_order,
                        text="Ordre des sorts de chaque joueur (la page est environ "
                             "deux fois plus lourde)").pack(anchor="w")
        choice = ttk.Frame(box)
        choice.pack(anchor="w", pady=(6, 0))
        ttk.Label(choice, text="Présentation :").pack(side="left")
        self.layout = tk.StringVar(value="onglets")
        for value, text in LAYOUT_CHOICES:
            ttk.Radiobutton(choice, text=text, value=value,
                            variable=self.layout).pack(side="left", padx=(10, 0))
        line = ttk.Frame(box)
        line.pack(fill="x", pady=(8, 0))
        self.write_button = ttk.Button(line, text="Créer le rapport et l'ouvrir",
                                       style="Accent.TButton", command=self.write_selected)
        self.write_button.pack(side="left")
        self.folder_button = ttk.Button(line, text="Ouvrir le dossier du rapport",
                                        command=lambda: open_folder(self.last_report))
        self.folder_button.pack(side="left", padx=(6, 0))
        return box

    def _table(self, parent, columns, height, select):
        ttk = self.ttk
        frame = ttk.Frame(parent)
        frame.columnconfigure(0, weight=1)
        frame.rowconfigure(0, weight=1)
        table = ttk.Treeview(frame, columns=[key for key, _title, _width in columns],
                             show="headings", height=height, selectmode=select)
        for key, title, width in columns:
            table.heading(key, text=title, anchor="w")
            table.column(key, width=width, anchor="w", stretch=key in ("file", "fight", "folder"))
        scroll = ttk.Scrollbar(frame, orient="vertical", command=table.yview)
        table.configure(yscrollcommand=scroll.set)
        table.grid(row=0, column=0, sticky="nsew")
        scroll.grid(row=0, column=1, sticky="ns")
        return table

    # -- actions ----------------------------------------------------------------

    def refresh_logs(self):
        self.logs.delete(*self.logs.get_children())
        entries = recent_logs(self.locations)
        for path, size, mtime in entries:
            self.logs.insert("", "end", iid=path, values=(
                os.path.basename(path), time.strftime("%d/%m/%Y %H:%M", time.localtime(mtime)),
                file_size(size), os.path.dirname(path)))
        if entries:
            self.logs.selection_set(entries[0][0])
            self.logs.see(entries[0][0])
        else:
            self.status.set("Aucun journal trouvé aux emplacements habituels : "
                            "« Choisir un autre fichier… » pour l'indiquer.")

    def choose_file(self):
        from tkinter import filedialog

        start = next(iter(default_log_locations() if self.locations is None
                          else self.locations), os.path.expanduser("~"))
        path = filedialog.askopenfilename(
            parent=self.root, title="Choisir un journal de combat", initialdir=start,
            filetypes=(("Journaux de combat", "WoWCombatLog*.txt"),
                       ("Fichiers texte", "*.txt"), ("Tous les fichiers", "*")))
        if path:
            if not self.logs.exists(path):
                size = os.path.getsize(path) if os.path.exists(path) else 0
                self.logs.insert("", 0, iid=path, values=(
                    os.path.basename(path), "", file_size(size), os.path.dirname(path)))
            self.logs.selection_set(path)
            self.read(path)

    def read_selected(self):
        selection = self.logs.selection()
        if selection and not self.busy:
            self.read(selection[0])

    def read(self, path):
        """Read and analyse `path` in a thread; the window stays alive meanwhile."""
        try:
            gap = float(self.gap.get().replace(",", "."))
        except ValueError:
            gap = PULL_GAP_MS / 1000
        gap = min(60.0, max(1.0, gap))
        self.fights.delete(*self.fights.get_children())
        self.log = self.segments = None
        self.log_path = path
        self.cancel.clear()
        self._start("Lecture de %s…" % os.path.basename(path))
        size = os.path.getsize(path) if os.path.exists(path) else 0

        def work():
            try:
                log, segments, elapsed = _build(
                    path, verbose=False, pull_gap_ms=int(gap * 1000),
                    progress=lambda lines: self.messages.put(("progress", lines, size)),
                    cancelled=self.cancel.is_set)
                self.messages.put(("read", log, segments, elapsed))
            except Cancelled:
                self.messages.put(("cancelled",))
            except OSError as error:
                self.messages.put(("error", "Impossible de lire %s : %s"
                                   % (path, error.strerror or error)))
            except Exception:       # noqa: BLE001 -- shown to the reader, not swallowed
                self.messages.put(("error", "Erreur inattendue en lisant le journal :\n\n"
                                   + traceback.format_exc()))

        threading.Thread(target=work, daemon=True).start()

    def select_all(self):
        self.fights.selection_set(self.fights.get_children())

    def write_selected(self):
        """Write the page for the chosen fights, then open it."""
        from tkinter import filedialog

        if self.busy or not self.segments:
            return
        wanted = {int(item) for item in self.fights.selection()}
        chosen = [segment for segment in self.segments if segment.index in wanted]
        if not chosen:
            return
        layout = self.layout.get()
        out = default_report_path(self.log_path, chosen, self.segments, layout)
        if _refusal(out, self.log_path, layout) or not _writable(out):
            if layout == "pages":
                parent = filedialog.askdirectory(
                    parent=self.root, title="Dans quel dossier écrire les pages ?",
                    initialdir=os.path.expanduser("~"))
                out = os.path.join(parent, os.path.basename(out)) if parent else ""
            else:
                out = filedialog.asksaveasfilename(
                    parent=self.root, title="Où écrire le rapport ?",
                    initialdir=os.path.expanduser("~"), initialfile=os.path.basename(out),
                    defaultextension=".html", filetypes=(("Page web", "*.html"),))
            if not out:
                return
        log, cast_order = self.log, self.cast_order.get()
        plural = "s" if len(chosen) > 1 else ""
        self._start("Écriture du rapport (%d combat%s)…" % (len(chosen), plural))
        self.bar.configure(mode="indeterminate")
        self.bar.start(12)

        def work():
            try:
                reason = write_report(log, chosen, out, self.log_path, cast_order, layout)
            except Exception:       # noqa: BLE001 -- shown to the reader, not swallowed
                reason = "Erreur inattendue en écrivant le rapport :\n\n" + traceback.format_exc()
            self.messages.put(("written", report_entry(out, layout), reason))

        threading.Thread(target=work, daemon=True).start()

    # -- the loop between the thread and the window ---------------------------

    def _drain(self):
        """Apply what the worker thread said. Only this touches widgets."""
        try:
            while True:
                self._handle(self.messages.get_nowait())
        except queue.Empty:
            pass
        self.root.after(100, self._drain)

    def _handle(self, message):
        from tkinter import messagebox

        kind = message[0]
        if kind == "progress":
            _kind, lines, size = message
            self.bar["value"] = 1000 * read_share(lines, size)
            self.status.set("Lecture… %s lignes lues" % "{:,}".format(lines).replace(",", " "))
        elif kind == "read":
            _kind, log, segments, elapsed = message
            self._stop()
            self.log, self.segments = log, segments
            for row in fight_rows(segments):
                self.fights.insert("", "end", iid=str(row[0]), values=row)
            self.select_all()
            if not segments:
                self.status.set("Aucun combat trouvé dans ce fichier : il est peut-être vide, "
                                "ou /combatlog n'était pas lancé.")
            else:
                problems = log.problems.total
                self.status.set("%d combat%s, %s lignes lues en %.0f s%s." % (
                    len(segments), "s" if len(segments) > 1 else "",
                    "{:,}".format(log.line_count).replace(",", " "), elapsed,
                    ", %d non comprises" % problems if problems else ""))
        elif kind == "cancelled":
            self._stop()
            self.status.set("Lecture annulée.")
        elif kind == "error":
            self._stop()
            self.status.set("La lecture a échoué.")
            messagebox.showerror("LogsWoW", message[1], parent=self.root)
        elif kind == "written":
            _kind, out, reason = message
            self._stop()
            if reason:
                self.status.set("Le rapport n'a pas été écrit.")
                messagebox.showerror("LogsWoW", reason, parent=self.root)
                return
            self.last_report = out
            self.status.set("Rapport écrit : %s" % out)
            open_in_browser(out)
        self._update_buttons()

    def _start(self, text):
        self.busy = True
        self.bar.configure(mode="determinate")
        self.bar["value"] = 0
        self.status.set(text)
        self._update_buttons()

    def _stop(self):
        self.busy = False
        self.bar.stop()
        self.bar.configure(mode="determinate")
        self.bar["value"] = 0

    def _update_buttons(self):
        def state(widget, on):
            widget.state(["!disabled"] if on else ["disabled"])

        state(self.read_button, not self.busy and bool(self.logs.selection()))
        state(self.cancel_button, self.busy)
        state(self.write_button, not self.busy and bool(self.fights.selection()))
        state(self.folder_button, not self.busy and self.last_report is not None)
        count = len(self.fights.selection())
        total = len(self.fights.get_children())
        self.chosen_label.configure(
            text="%d combat%s sur %d dans le rapport" % (count, "s" if count > 1 else "", total)
            if total else "")


def _writable(out):
    """Whether a new file can be created where `out` would go."""
    folder = os.path.dirname(os.path.abspath(out))
    return os.access(folder, os.W_OK)
