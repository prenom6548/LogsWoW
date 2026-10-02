# SPDX-License-Identifier: AGPL-3.0-or-later
"""The history: one small file per night, kept in folders the reader names.

Asked for by the owner on 2026-10-02 (see `CLAUDE.md`, "The history"): to see,
over several nights, how a character does, how a specialization compares with
another, and which is the best key or boss kill of each. This module is the
foundation only -- no window and no page -- so that its rules can be checked on
real logs before anything is drawn on top of it.

What it keeps, and why
----------------------
* **Results, not events.** The numbers the analysis has already computed, a few
  tens of kilobytes a night; never the event stream (a database of events was
  tried in a sibling project and weighed 40 to 60 MB for a 100 to 400 MB log).
  So the history carries exactly the figures LogsWoW's own invariants vouch for.
* **Only the characters the reader chose** (`suivi.json`). A pick-up group's
  players are never written. The group's *totals* are kept, anonymous.
* **Dungeons whole, with their pulls and bosses; raid bosses alone.** A raid's
  trash has no segment and so no record. A boss that was not killed keeps its
  remaining health when the file gave one; a trash pull keeps the average health
  of the enemies engaged during it.
* **Raw components, not rates.** `rates()` turns them into damage, healing and
  damage taken per second with the same formulas the window and the page use, so a
  definition that changes later changes it in one place.

Files and versions
------------------
Every file carries two numbers: `format`, the layout of the file, and `analysis`,
the revision of the counting rules (`ANALYSIS_REVISION`: raise it whenever damage,
healing, absorbs or deaths are counted differently). A newer LogsWoW reads every
older format and never rewrites an old file on its own; a file written by a newer
LogsWoW than this one is read as far as it is understood and reported as such,
never modified. A test keeps one real-shaped file per published format.

Layout on disk, under the root (`default_root()`, or `LOGSWOW_HISTORIQUE`)::

    config.json            marks the root as ours; the active folder, the automatic flag
    suivi.json             the characters followed, by GUID
    <folder>/dossier.json  its name as the reader typed it (accents allowed)
    <folder>/<night>.json  one night

Nothing here opens a socket, and nothing is deleted that this module did not write.
"""

import json
import os
import re
import sys
import unicodedata
from datetime import datetime

from . import __version__
from .i18n import _
from .report_layouts import contents, nested
from .specs import DPS, HEAL, TANK, role_of

FORMAT_VERSION = 1
ANALYSIS_REVISION = 1

NIGHT_MARK = "logswow-historique"
ROOT_MARK = "logswow-historique-racine"
FOLDER_MARK = "logswow-historique-dossier"

CONFIG_FILE = "config.json"
TRACKED_FILE = "suivi.json"
FOLDER_FILE = "dossier.json"

# Files an operating system leaves in a folder the reader opened (the Finder's .DS_Store,
# Windows' Thumbs.db and desktop.ini, a Mac's "._" twins), and what a write of ours cut
# short leaves (`_write_json`'s ".tmp-"): none of them is the reader's, and none may stop a
# folder from being deleted. Found by the 2026-10-02 audit: one .DS_Store, and "Supprimer
# ce dossier" refused for good.
SYSTEM_FILES = (".ds_store", "thumbs.db", "desktop.ini")


def _left_behind(name):
    """True for a file the system or an interrupted write of ours left in a folder."""
    folded = name.lower()
    return folded in SYSTEM_FILES or name.startswith("._") or name.startswith(".tmp-")


# A folder's directory name: what `slugify` makes of the name the reader typed.
_SLUG = re.compile(r"^[a-z0-9][a-z0-9-]{0,63}$")

# Older layouts of the file, oldest first: {format: function(record) -> record one
# format newer}. Empty while there is one format; every format ever published
# keeps its entry here and its golden file in the tests.
UPGRADES = {}


class HistoryError(Exception):
    """A refusal or a failure the reader should be told, already in their language."""


# -- where it lives ----------------------------------------------------------------

def default_root():
    """The history's root on this machine: the user's data folder, never the logs'."""
    override = os.environ.get("LOGSWOW_HISTORIQUE")
    if override:
        return override
    if sys.platform.startswith("win"):
        base = (os.environ.get("APPDATA")
                or os.path.join(os.path.expanduser("~"), "AppData", "Roaming"))
        return os.path.join(base, "LogsWoW", "historique")
    if sys.platform == "darwin":
        return os.path.join(os.path.expanduser("~"), "Library", "Application Support",
                            "LogsWoW", "historique")
    base = (os.environ.get("XDG_DATA_HOME")
            or os.path.join(os.path.expanduser("~"), ".local", "share"))
    return os.path.join(base, "logswow", "historique")


def _read_json(path):
    with open(path, encoding="utf-8") as handle:
        return json.load(handle)


def _write_json(path, data):
    """Write whole or not at all: beside the target, then moved into place."""
    folder = os.path.dirname(path)
    os.makedirs(folder, exist_ok=True)
    temporary = os.path.join(folder, ".tmp-%d-%s" % (os.getpid(), os.path.basename(path)))
    try:
        with open(temporary, "w", encoding="utf-8") as handle:
            json.dump(data, handle, ensure_ascii=False, indent=1)
            handle.write("\n")
        os.replace(temporary, path)
    finally:
        if os.path.exists(temporary):
            os.remove(temporary)


def is_root(root):
    """True when `root` holds our marker."""
    path = os.path.join(root, CONFIG_FILE)
    try:
        return os.path.isfile(path) and _read_json(path).get("marque") == ROOT_MARK
    except (OSError, ValueError, AttributeError):
        return False


def ensure_root(root):
    """Create the root if it is not there. Refuses a folder that is not ours and not empty."""
    if os.path.isdir(root) and not is_root(root):
        if os.listdir(root):
            raise HistoryError(_("%s n'est pas un dossier d'historique LogsWoW : refus d'y "
                                 "écrire.") % root)
    if not is_root(root):
        _write_json(os.path.join(root, CONFIG_FILE),
                    {"marque": ROOT_MARK, "format": FORMAT_VERSION, "dossier_actif": "",
                     "automatique": False})
    return root


def config(root):
    """{'dossier_actif': slug or '', 'automatique': bool}: defaults when there is no root yet."""
    settings = {"dossier_actif": "", "automatique": False}
    if is_root(root):
        stored = _read_json(os.path.join(root, CONFIG_FILE))
        settings["dossier_actif"] = str(stored.get("dossier_actif") or "")
        settings["automatique"] = bool(stored.get("automatique"))
    return settings


def set_config(root, **changes):
    """Change `dossier_actif` and/or `automatique`; anything else is refused."""
    ensure_root(root)
    stored = _read_json(os.path.join(root, CONFIG_FILE))
    for name, value in changes.items():
        if name not in ("dossier_actif", "automatique"):
            raise HistoryError(_("Réglage inconnu : %s") % name)
        stored[name] = value
    _write_json(os.path.join(root, CONFIG_FILE), stored)


def needs_setup(root):
    """True until the first folder exists: the moment to explain the history and ask for one."""
    return not (is_root(root) and list_folders(root))


# -- folders --------------------------------------------------------------------------

def slugify(name):
    """'Saison 1 Midnight' -> 'saison-1-midnight'; '' when nothing usable is left."""
    folded = unicodedata.normalize("NFKD", name).encode("ascii", "ignore").decode("ascii")
    return re.sub(r"[^a-z0-9]+", "-", folded.lower()).strip("-")[:64].strip("-")


class Folder:
    """One folder, as `list_folders` reports it."""

    __slots__ = ("slug", "name", "created", "nights", "size_bytes")

    def __init__(self, slug, name, created, nights, size_bytes):
        self.slug, self.name, self.created = slug, name, created
        self.nights, self.size_bytes = nights, size_bytes


def _folder_path(root, slug):
    if not _SLUG.match(slug or ""):
        raise HistoryError(_("Nom de dossier invalide : %s") % slug)
    return os.path.join(root, slug)


def _night_files(folder_path):
    """The `.json` files of a folder that are nights (never its own descriptor)."""
    try:
        names = sorted(os.listdir(folder_path))
    except OSError:
        return []
    return [os.path.join(folder_path, name) for name in names
            if name.endswith(".json") and name != FOLDER_FILE and not name.startswith(".")]


def list_folders(root):
    """[Folder] in creation order; an unreadable folder descriptor is skipped, not fatal."""
    if not is_root(root):
        return []
    folders = []
    for entry in sorted(os.listdir(root)):
        path = os.path.join(root, entry)
        descriptor = os.path.join(path, FOLDER_FILE)
        if not (os.path.isdir(path) and not os.path.islink(path) and _SLUG.match(entry)
                and os.path.isfile(descriptor)):
            continue
        try:
            info = _read_json(descriptor)
        except (OSError, ValueError):
            continue
        if not isinstance(info, dict) or info.get("marque") != FOLDER_MARK:
            continue
        files = _night_files(path)
        folders.append(Folder(entry, str(info.get("nom") or entry), str(info.get("cree") or ""),
                              len(files), sum(os.path.getsize(item) for item in files)))
    folders.sort(key=lambda folder: (folder.created, folder.slug))
    return folders


def create_folder(root, name):
    """Make a folder called `name` (free text) and make it the active one if none is."""
    name = (name or "").strip()
    base = slugify(name)
    if not base:
        raise HistoryError(_("Nom de dossier invalide : donnez un nom avec au moins une lettre "
                             "ou un chiffre."))
    ensure_root(root)
    taken = {folder.slug for folder in list_folders(root)}
    if any(folder.name.casefold() == name.casefold() for folder in list_folders(root)):
        raise HistoryError(_("Un dossier de ce nom existe déjà : %s") % name)
    slug, count = base, 1
    while slug in taken or os.path.exists(os.path.join(root, slug)):
        count += 1
        slug = "%s-%d" % (base[:60].rstrip("-"), count)
    _write_json(os.path.join(root, slug, FOLDER_FILE),
                {"marque": FOLDER_MARK, "format": FORMAT_VERSION, "nom": name,
                 "cree": datetime.now().isoformat()})   # microseconds: order is creation order
    if not config(root)["dossier_actif"]:
        set_config(root, dossier_actif=slug)
    return slug


def rename_folder(root, slug, name):
    """Change the name shown; the directory keeps its name, so nothing moves."""
    name = (name or "").strip()
    if not slugify(name):
        raise HistoryError(_("Nom de dossier invalide : donnez un nom avec au moins une lettre "
                             "ou un chiffre."))
    descriptor = os.path.join(_folder_path(root, slug), FOLDER_FILE)
    if not os.path.isfile(descriptor):
        raise HistoryError(_("Dossier d'historique introuvable : %s") % slug)
    info = _read_json(descriptor)
    info["nom"] = name
    _write_json(descriptor, info)


def delete_folder(root, slug):
    """Delete a folder and the nights in it; returns how many nights went.

    Refuses, before deleting anything, a folder that holds a file this module did not
    write: it is the reader's, whatever it is.
    """
    path = _folder_path(root, slug)
    if not is_root(root) or not os.path.isdir(path) or os.path.islink(path):
        raise HistoryError(_("Dossier d'historique introuvable : %s") % slug)
    nights = _night_files(path)
    leftovers = []
    for item in os.listdir(path):
        full = os.path.join(path, item)
        if full in nights or item == FOLDER_FILE:
            continue
        if _left_behind(item) and os.path.isfile(full) and not os.path.islink(full):
            leftovers.append(full)
            continue
        raise HistoryError(_("Le dossier %s contient un fichier qui ne vient pas de LogsWoW "
                             "(%s) : refus de le supprimer.") % (slug, item))
    for item in nights:
        if not _is_night_file(item):
            raise HistoryError(_("Le dossier %s contient un fichier qui ne vient pas de LogsWoW "
                                 "(%s) : refus de le supprimer.") % (slug, os.path.basename(item)))
    for item in nights + leftovers:
        os.remove(item)
    descriptor = os.path.join(path, FOLDER_FILE)
    if os.path.exists(descriptor):
        os.remove(descriptor)
    os.rmdir(path)
    if config(root)["dossier_actif"] == slug:
        remaining = list_folders(root)
        set_config(root, dossier_actif=remaining[0].slug if remaining else "")
    return len(nights)


# -- followed characters ------------------------------------------------------------------

def tracked(root):
    """{guid: {'name', 'added'}} of the characters followed."""
    path = os.path.join(root, TRACKED_FILE)
    if not is_root(root) or not os.path.isfile(path):
        return {}
    try:
        stored = _read_json(path).get("personnages", {})
    except (OSError, ValueError, AttributeError):
        return {}
    if not isinstance(stored, dict):
        return {}
    return {guid: info for guid, info in stored.items()
            if isinstance(guid, str) and guid and isinstance(info, dict)}


def _save_tracked(root, characters):
    _write_json(os.path.join(root, TRACKED_FILE),
                {"format": FORMAT_VERSION, "personnages": characters})


def track(root, guid, name):
    """Follow a character, or refresh the name it is shown under."""
    if not guid:
        return
    ensure_root(root)
    characters = tracked(root)
    added = characters.get(guid, {}).get("added") or datetime.now().strftime("%Y-%m-%d")
    characters[guid] = {"name": str(name), "added": added}
    _save_tracked(root, characters)


def untrack(root, guid):
    """Stop following a character; what was already kept stays where it is."""
    characters = tracked(root)
    if guid in characters:
        del characters[guid]
        _save_tracked(root, characters)


def players_seen(segments):
    """[(guid, name, spec id, role, fights)] of everyone who took part, to tick who to follow.

    `role` is '' for a specialization the table does not know; `fights` counts the
    top-level fights the player took part in.
    """
    seen, order = {}, []
    for segment in segments:
        if segment.kind not in ("keystone", "encounter") or segment.analysis is None:
            continue
        for player in segment.analysis.participants():
            row = seen.get(player.guid)
            if row is None:
                row = seen[player.guid] = [player.guid, player.short_name, player.spec_id,
                                           role_of(player.spec_id), 0]
                order.append(player.guid)
            elif player.spec_id and not row[2]:
                row[2], row[3] = player.spec_id, role_of(player.spec_id)
            row[4] += 1
    return [tuple(seen[guid]) for guid in order]


# -- one night, built from the analysis ------------------------------------------------------

def _iso(ts):
    """'2026-10-02T19:23:11' in this machine's time, '' when there is no timestamp."""
    if ts is None:
        return ""
    try:
        return datetime.fromtimestamp(ts / 1000.0).strftime("%Y-%m-%dT%H:%M:%S")
    except (OverflowError, OSError, ValueError):
        return ""


def _round(value, digits=4):
    return None if value is None else round(float(value), digits)


def _composition(analysis):
    counts = {"tank": 0, "healer": 0, "dps": 0, "unknown": 0}
    for player in analysis.participants():
        role = role_of(player.spec_id)
        counts[{TANK: "tank", HEAL: "healer", DPS: "dps"}.get(role, "unknown")] += 1
    return counts


def _group(analysis):
    """The group's totals, raw: players of a pick-up group included, anonymously."""
    players = analysis.players.values()
    return {
        "damage": analysis.total_damage,
        "healing": analysis.total_healing,
        "absorb_done": sum(player.absorb_done for player in players),
        "taken": sum(player.damage_taken for player in players),
        "absorbed": sum(player.absorbed_taken for player in players),
        "deaths": len(analysis.deaths),
        "composition": _composition(analysis),
    }


def _player_row(player):
    gear = player.gear
    return {
        "guid": player.guid, "name": player.short_name, "spec_id": player.spec_id,
        "role": role_of(player.spec_id),
        "damage": player.damage_done, "healing": player.healing_done,
        "absorb_done": player.absorb_done, "taken": player.damage_taken,
        "absorbed": player.absorbed_taken, "deaths": player.deaths,
        "ilvl": _round(gear.average, 2) if gear is not None else None,
    }


def _followed(analysis, guids):
    return [_player_row(player) for player in analysis.participants() if player.guid in guids]


def health_average(analysis):
    """The average of the engaged enemies' pooled health over a pull, or None.

    The curve the page draws (`TimelineLedger.timeline_series`): one reading per bucket
    while something engaged is alive; a pull with no reading has no average.
    """
    series, _bucket = analysis.timeline_series()
    values = [point[4] for point in series if point[4] is not None]
    return _round(sum(values) / len(values)) if values else None


def boss_health_end(analysis):
    """(remaining fraction, unit name) from the last reading of the most-hit unit, or (None, '').

    That unit is the boss on a boss pull; the reading is the file's own last, so it is
    only worth looking at for a boss that was not killed.
    """
    if analysis.boss_hp:
        return _round(analysis.boss_hp[-1][1]), analysis.boss_name
    return None, ""


def _fight(segment, guids):
    analysis = segment.analysis
    if segment.kind == "keystone":
        record = {
            "type": "key", "name": segment.name, "instance_id": segment.instance_id,
            "level": segment.key_level, "affixes": list(segment.affixes),
            "start": _iso(segment.start_ts), "outcome": segment.outcome,
            "score": segment.score, "key_time_ms": segment.reported_duration_ms,
        }
    else:
        health, unit = boss_health_end(analysis)
        record = {
            "type": "encounter", "name": segment.name, "encounter_id": segment.encounter_id,
            "difficulty_id": segment.difficulty_id,
            "start": _iso(segment.start_ts), "outcome": segment.outcome,
            "boss_health_end": health, "boss_unit": unit,
        }
    record["duration_ms"] = analysis.duration_ms
    record["group"] = _group(analysis)
    record["players"] = _followed(analysis, guids)
    return record


def _pull(segment, key):
    analysis = segment.analysis
    return {
        "offset_ms": max(0, segment.start_ts - key.start_ts),
        "duration_ms": analysis.duration_ms,
        "damage": analysis.total_damage,
        "taken": sum(player.damage_taken for player in analysis.players.values()),
        "deaths": len(analysis.deaths),
        "health_average": health_average(analysis),
    }


def build_night(log, segments, guids=()):
    """The record of a night: every key (with its pulls and bosses) and every raid boss.

    `guids` are the characters to keep a row for; everyone else only counts in the
    group's totals. A segment with no analysis, a session with no markers and a boss
    pull nobody fought leave nothing.
    """
    guids = set(guids)
    held, inside = contents(segments), nested(segments)
    fights = []
    for segment in segments:
        if segment.analysis is None or segment.index in inside:
            continue
        if segment.kind == "keystone":
            record = _fight(segment, guids)
            children = held.get(segment.index, [])
            record["pulls"] = [_pull(child, segment) for child in children
                               if child.kind == "pull" and child.analysis is not None]
            record["bosses"] = [_fight(child, guids) for child in children
                                if child.kind == "encounter" and child.analysis is not None
                                and not child.never_fought]
            fights.append(record)
        elif segment.kind == "encounter" and not segment.never_fought:
            fights.append(_fight(segment, guids))
    size = log.size_bytes or 0
    name = os.path.basename(log.path)
    return {
        "marque": NIGHT_MARK, "format": FORMAT_VERSION, "logswow": __version__,
        "analysis": ANALYSIS_REVISION,
        "identity": "%s|%d|%s" % (name, size, log.first_ts),
        "source": name,
        "date": _iso(log.first_ts)[:10],
        "game": {"build": log.build_version, "project": log.project_id},
        "fights": fights,
    }


def rates(row, duration_ms):
    """{'dps', 'hps', 'taken'} per second from a group or player row.

    The same formulas as the preview and the page (`preview.rates`): healing includes the
    shields a player cast, damage taken includes what shields absorbed. A second counted
    at least, so a fight of no length does not divide by zero.
    """
    seconds = max(1.0, duration_ms / 1000.0)
    return {
        "dps": row["damage"] / seconds,
        "hps": (row["healing"] + row["absorb_done"]) / seconds,
        "taken": (row["taken"] + row["absorbed"]) / seconds,
    }


# -- nights on disk ----------------------------------------------------------------------------

class Night:
    """One night's file, as `list_nights` reports it (the figures are read on demand)."""

    __slots__ = ("path", "folder", "identity", "date", "source", "build", "analysis",
                 "fights", "size_bytes")

    def __init__(self, path, folder, record):
        self.path, self.folder = path, folder
        self.identity = str(record.get("identity", ""))
        self.date = str(record.get("date", ""))
        self.source = str(record.get("source", ""))
        game = record.get("game")
        self.build = str(game.get("build", "")) if isinstance(game, dict) else ""
        self.analysis = record.get("analysis", 0)
        fights = record.get("fights")
        self.fights = len(fights) if isinstance(fights, list) else 0
        self.size_bytes = os.path.getsize(path)


def _is_night_file(path):
    try:
        record = _read_json(path)
    except (OSError, ValueError):
        return False
    return isinstance(record, dict) and record.get("marque") == NIGHT_MARK


def read_night(path):
    """(record, notes): the file's content, brought to the layout this version reads.

    `notes` may hold 'newer_format' (written by a newer LogsWoW: read as far as it is
    understood, never modify it), 'older_analysis' (counted by an older revision of the
    rules: figures not necessarily comparable) and 'upgraded' (an older layout, brought
    up to date in memory only: the file is left as it was).
    """
    try:
        record = _read_json(path)
    except OSError as error:
        raise HistoryError(_("Fichier de l'historique illisible (%s) : %s")
                           % (os.path.basename(path), error.strerror or error))
    except ValueError as error:
        raise HistoryError(_("Fichier de l'historique illisible (%s) : %s")
                           % (os.path.basename(path), error))
    if (not isinstance(record, dict) or record.get("marque") != NIGHT_MARK
            or not isinstance(record.get("format"), int)):
        raise HistoryError(_("Ce fichier n'est pas une soirée de l'historique LogsWoW : %s")
                           % os.path.basename(path))
    notes = []
    layout = record["format"]
    if layout > FORMAT_VERSION:
        notes.append("newer_format")
    while layout < FORMAT_VERSION and layout in UPGRADES:
        record = UPGRADES[layout](record)
        layout += 1
        notes.append("upgraded")
    if isinstance(record.get("analysis"), int) and record["analysis"] < ANALYSIS_REVISION:
        notes.append("older_analysis")
    return record, notes


def _night_paths(root):
    for folder in list_folders(root):
        for path in _night_files(os.path.join(root, folder.slug)):
            yield folder.slug, path


def list_nights(root, slug=None):
    """[Night], oldest first; a file that is not a readable night is left out, not fatal."""
    nights = []
    for folder, path in _night_paths(root):
        if slug is not None and folder != slug:
            continue
        try:
            nights.append(Night(path, folder, _read_json(path)))
        except (OSError, ValueError, AttributeError):
            continue
    nights.sort(key=lambda night: (night.date, night.path))
    return nights


def _night_name(record):
    stem = slugify(os.path.splitext(record.get("source", ""))[0]) or "journal"
    first = (record.get("fights") or [{}])[0].get("start", "") or record.get("date", "")
    stamp = re.sub(r"[^0-9]", "", first)[:14] or "inconnu"
    return "%s_%s.json" % (stamp, stem[:40].strip("-"))


def log_of(identity):
    """(source name, first moment) of a night's identity: which log it was read from.

    The identity also carries the file's size, and the size is not the log: the game keeps
    writing the same file all evening, so a log read at 21:00 and again at 23:00 is the same
    log, bigger. Found by the 2026-10-02 audit: the two reads made two nights, and every run
    of the first part of the evening counted twice in every view.
    """
    parts = str(identity).rsplit("|", 2)
    return (parts[0], parts[2]) if len(parts) == 3 else (str(identity), "")


def log_size(identity):
    """The size a night's identity records, or 0."""
    parts = str(identity).rsplit("|", 2)
    try:
        return int(parts[1]) if len(parts) == 3 else 0
    except ValueError:
        return 0


def save_night(root, slug, record):
    """Write a night into a folder; returns (path, replaced).

    A log read twice is one night: when a file read from the same log (`log_of`: the source's
    name and its first moment, whatever its size by then) exists in any folder, it is replaced
    where it is, whatever `slug` says; `move_night` is how a night changes folder.
    """
    if not isinstance(record, dict) or record.get("marque") != NIGHT_MARK:
        label = record.get("source", "?") if isinstance(record, dict) else "?"
        raise HistoryError(_("Ce fichier n'est pas une soirée de l'historique LogsWoW : %s")
                           % label)
    ensure_root(root)
    wanted = log_of(record.get("identity", ""))
    for folder, path in _night_paths(root):
        try:
            same = log_of(_read_json(path).get("identity", "")) == wanted
        except (OSError, ValueError, AttributeError):
            same = False
        if same:
            _write_json(path, record)
            return path, True
    folder_path = _folder_path(root, slug)
    if not os.path.isfile(os.path.join(folder_path, FOLDER_FILE)):
        raise HistoryError(_("Dossier d'historique introuvable : %s") % slug)
    name, count = _night_name(record), 1
    path = os.path.join(folder_path, name)
    while os.path.exists(path):
        count += 1
        path = os.path.join(folder_path, "%s-%d.json" % (name[:-5], count))
    _write_json(path, record)
    return path, False


def _inside(root, path):
    """True when `path` is a file of a folder of the root, symbolic links left out."""
    real_root = os.path.normcase(os.path.realpath(root))
    real = os.path.normcase(os.path.realpath(path))
    try:
        common = os.path.commonpath([real_root, real])
    except ValueError:          # two drives on Windows: certainly not inside
        return False
    return (common == real_root and os.path.dirname(os.path.dirname(real)) == real_root
            and not os.path.islink(path))


def delete_night(root, path):
    """Delete one night's file; only a night of this history, nothing else."""
    if not is_root(root) or not _inside(root, path) or not _is_night_file(path):
        raise HistoryError(_("Ce fichier n'est pas une soirée de l'historique LogsWoW : %s")
                           % os.path.basename(path))
    os.remove(path)


def move_night(root, path, slug):
    """Move a night to another folder; returns its new path."""
    if not is_root(root) or not _inside(root, path) or not _is_night_file(path):
        raise HistoryError(_("Ce fichier n'est pas une soirée de l'historique LogsWoW : %s")
                           % os.path.basename(path))
    target = _folder_path(root, slug)
    if not os.path.isfile(os.path.join(target, FOLDER_FILE)):
        raise HistoryError(_("Dossier d'historique introuvable : %s") % slug)
    destination = os.path.join(target, os.path.basename(path))
    if os.path.exists(destination):
        raise HistoryError(_("Une soirée de même nom existe déjà dans ce dossier : %s")
                           % os.path.basename(path))
    os.replace(path, destination)
    return destination


# -- when to suggest a new folder -----------------------------------------------------------------

def _version(text):
    parts = re.match(r"^(\d+)\.(\d+)(?:\.(\d+))?", text or "")
    return tuple(int(part or 0) for part in parts.groups()) if parts else None


def suggest_new_folder(previous_build, new_build):
    """'extension', 'patch' or None, from two game versions such as '12.1.0' and '12.2.0'.

    The log never says which season it is, only the client's version: a new first number is
    a new expansion, a new second number a new patch (a season often starts with one, not
    always), and anything else -- a hotfix, an unreadable version -- is no reason to ask.
    """
    before, after = _version(previous_build), _version(new_build)
    if before is None or after is None or after <= before:
        return None
    if after[0] != before[0]:
        return "extension"
    if after[1] != before[1]:
        return "patch"
    return None
