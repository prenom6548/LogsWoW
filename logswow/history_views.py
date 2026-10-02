# SPDX-License-Identifier: AGPL-3.0-or-later
"""What the history shows: the views, as data, with no screen and no markup.

Three views are here, all asked for by the owner on 2026-10-02: **the evolution of a
character** (`trend_groups`), **one specialization against another** (`spec_comparison`) and
**the best key and the best kill of each specialization** (`key_records`, `kill_groups`).
The windows (`gui_evolution.py`, `gui_specs.py`, `gui_records.py`) draw what these functions
return, and a page can later draw the same.

A *run* is one appearance of a followed character in a key or in a boss fight, with the
figures the night kept and the context beside them: the dungeon and its level (or the boss
and its difficulty), the outcome, the specialization, the item level, the group's
composition, the game's version. Runs are only compared with runs of the same *content*
(same dungeon and level, same boss and difficulty): a +12 beside a +13, or a kill beside a
wipe, would make a figure say what it does not. Nothing here is a verdict; the change is
"the last run against the first", with what else changed shown next to it.
"""

from statistics import median

from . import history
from .preview import COMPARABLE, ROLE_ORDER, change
from .segment import difficulty_name
from .specs import DPS, HEAL, TANK, label_of, role_of

METRICS = ("dps", "hps", "taken")
# What each role is judged by here: a tank's damage taken per second was the owner's own
# request, a healer's is healing, a damage dealer's is damage. Any of the three can be chosen.
ROLE_METRIC = {TANK: "taken", HEAL: "hps", DPS: "dps"}

# Kinds of content; also what the window offers to show.
KEY, BOSS = "key", "boss"

SPARK = "▁▂▃▄▅▆▇█"
SPARK_LENGTH = 24           # a run of more than this shows its last ones


class Run:
    """One appearance of a followed character in a key or a boss fight."""

    __slots__ = ("kind", "start", "date", "night", "build", "old_analysis", "name",
                 "content_id", "level", "difficulty_id", "outcome", "duration_ms",
                 "spec_id", "role", "ilvl", "row", "composition", "score", "key_time_ms",
                 "boss_health_end", "inside_key")

    def __init__(self, **fields):
        for name in self.__slots__:
            setattr(self, name, fields.get(name))

    @property
    def content(self):
        """What it can be compared with: ('key', instance, level) or ('boss', id, difficulty)."""
        if self.kind == KEY:
            return (KEY, self.content_id, self.level)
        return (BOSS, self.content_id, self.difficulty_id)

    @property
    def counts(self):
        """Whether it enters a trend: a finished key (timed or not), a boss that was killed.

        An abandoned or interrupted key and a wipe stay listed, but a wipe's short length and
        a key left halfway would make every rate say something else.
        """
        if self.kind == KEY:
            return self.outcome in COMPARABLE
        return self.outcome == "réussite"

    def level_text(self):
        """'+12' for a key, the difficulty's name for a boss."""
        if self.kind == KEY:
            return "+%d" % self.level if self.level else ""
        return difficulty_name(self.difficulty_id)

    def value(self, metric):
        """dps, hps or taken per second, or None (damage taken is only given to a tank)."""
        if metric == "taken" and self.role != TANK:
            return None
        return history.rates(self.row, self.duration_ms)[metric]


# -- reading the runs ---------------------------------------------------------------------

def followed_in_folder(root, slug):
    """[(guid, name, runs seen)] of the followed characters in a folder, most runs first."""
    seen = {}
    for run_guid, run in _runs_of_folder(root, slug):
        entry = seen.setdefault(run_guid, [0, run.row.get("name", "")])
        entry[0] += 1
        entry[1] = run.row.get("name", "") or entry[1]
    ordered = sorted(seen.items(), key=lambda item: (-item[1][0], item[1][1].lower()))
    return [(guid, entry[1], entry[0]) for guid, entry in ordered]


def runs_in_folder(root, slug):
    """Every run of every followed character in a folder, oldest first."""
    runs = [run for _guid, run in _runs_of_folder(root, slug)]
    runs.sort(key=lambda run: (run.start or run.date or ""))
    return runs


def runs_of(root, slug, guid):
    """Every run of one character in a folder, oldest first (ties keep file order)."""
    runs = [run for run_guid, run in _runs_of_folder(root, slug) if run_guid == guid]
    runs.sort(key=lambda run: (run.start or run.date or ""))
    return runs


def _runs_of_folder(root, slug):
    for night in history.list_nights(root, slug):
        try:
            record, notes = history.read_night(night.path)
        except history.HistoryError:
            continue
        for fight in record.get("fights") or []:
            yield from _runs_of_fight(record, fight, notes, inside_key=False)


def _runs_of_fight(record, fight, notes, inside_key):
    """The runs of one fight record and of the bosses it holds; what is odd is skipped."""
    if not isinstance(fight, dict):
        return
    kind = {"key": KEY, "encounter": BOSS}.get(fight.get("type"))
    if kind is not None:
        group = _dict(fight.get("group"))
        composition = _dict(group.get("composition"))
        for row in _list(fight.get("players")):
            if not isinstance(row, dict) or not row.get("guid"):
                continue
            row = _complete(row)
            yield row["guid"], Run(
                kind=kind, start=str(fight.get("start", "")), date=str(record.get("date", "")),
                night=record.get("source", ""),
                build=_dict(record.get("game")).get("build", ""),
                old_analysis="older_analysis" in notes, name=str(fight.get("name", "")),
                content_id=_whole(fight.get("instance_id" if kind == KEY else "encounter_id")),
                level=_whole(fight.get("level")), difficulty_id=_whole(fight.get("difficulty_id")),
                outcome=str(fight.get("outcome", "")), duration_ms=_whole(fight.get("duration_ms")),
                spec_id=_whole(row.get("spec_id")),
                role=role_of(_whole(row.get("spec_id"))) or row.get("role") or "",
                ilvl=row.get("ilvl") if isinstance(row.get("ilvl"), (int, float)) else None,
                row=row, composition=(_whole(composition.get("tank")),
                                      _whole(composition.get("healer")),
                                      _whole(composition.get("dps"))),
                score=fight.get("score"), key_time_ms=fight.get("key_time_ms"),
                boss_health_end=fight.get("boss_health_end") if isinstance(
                    fight.get("boss_health_end"), (int, float)) else None,
                inside_key=inside_key)
    for boss in _list(fight.get("bosses")):
        yield from _runs_of_fight(record, boss, notes, inside_key=True)


def _dict(value):
    return value if isinstance(value, dict) else {}


def _list(value):
    return value if isinstance(value, list) else []


def _whole(value):
    """A number as the file gave it, or 0: a figure that is not one must not stop a view."""
    return value if isinstance(value, (int, float)) and not isinstance(value, bool) else 0


def _complete(row):
    """The row with every figure `history.rates` reads: a missing or odd one counts as zero."""
    out = dict(row)
    for name in ("damage", "healing", "absorb_done", "taken", "absorbed", "deaths"):
        out[name] = _whole(row.get(name))
    return out


# -- the trend ----------------------------------------------------------------------------------

def default_metric(runs):
    """The measure to open on: what the character's latest role is judged by here.

    See `ROLE_METRIC`.
    """
    return ROLE_METRIC.get(runs[-1].role if runs else "", "dps")


def sparkline(values):
    """'▂▃▅█': the values as bars scaled between their lowest and highest, '' for none.

    Equal values give a flat middle line rather than a made-up slope; a gap (None) is skipped.
    """
    present = [value for value in values if value is not None][-SPARK_LENGTH:]
    if not present:
        return ""
    low, high = min(present), max(present)
    if high - low < 1e-9:
        return SPARK[3] * len(present)
    return "".join(SPARK[min(len(SPARK) - 1, int((value - low) / (high - low) * len(SPARK)))]
                   for value in present)


class Group:
    """The runs of one content, with the trend of one measure over them."""

    __slots__ = ("content", "kind", "name", "level_text", "runs", "listed", "values", "first",
                 "last", "change", "spark", "ilvl_first", "ilvl_last", "specs", "old_analysis",
                 "builds")

    def __init__(self, content, runs, metric):
        self.content = content
        self.listed = runs                              # every run, oldest first
        self.runs = [run for run in runs if run.counts]  # the ones the trend is made of
        self.kind = content[0]
        self.name = runs[-1].name
        self.level_text = runs[-1].level_text()
        self.values = [run.value(metric) for run in self.runs]
        present = [value for value in self.values if value is not None]
        self.first = present[0] if present else None
        self.last = present[-1] if present else None
        self.change = change(self.values)
        self.spark = sparkline(self.values)
        ilvls = [run.ilvl for run in self.runs if run.ilvl is not None]
        self.ilvl_first = ilvls[0] if ilvls else None
        self.ilvl_last = ilvls[-1] if ilvls else None
        self.specs = sorted({run.spec_id for run in self.runs if run.spec_id})
        self.old_analysis = any(run.old_analysis for run in self.runs)
        self.builds = sorted({run.build for run in self.runs if run.build})

    @property
    def mixed_specs(self):
        return len(self.specs) > 1


def trend_groups(runs, metric, kinds=(KEY, BOSS)):
    """[Group] of the runs, one per content, the most recently played first.

    `kinds` keeps keys, bosses or both. A content with no run that counts (only abandoned
    keys, only wipes) is still returned, with an empty trend, so nothing played disappears.
    """
    by_content, order = {}, []
    for run in runs:
        if run.kind not in kinds:
            continue
        if run.content not in by_content:
            by_content[run.content] = []
            order.append(run.content)
        by_content[run.content].append(run)
    groups = [Group(content, by_content[content], metric) for content in order]
    groups.sort(key=lambda group: group.listed[-1].start or group.listed[-1].date or "",
                reverse=True)
    return groups


# -- one specialization against another ---------------------------------------------------------

LOW_SAMPLE = 3          # fewer runs than this and a median says little: the row is marked


def majority_role(runs):
    """The role most of the counted runs played (damage dealer when they tie), or DPS."""
    count = {}
    for run in runs:
        if run.counts and run.role in ROLE_METRIC:
            count[run.role] = count.get(run.role, 0) + 1
    return max(count, key=lambda role: (count[role], role == DPS), default=DPS)


class SpecRow:
    """What one specialization did in one content: its counted runs and the median figure."""

    __slots__ = ("spec_id", "runs", "characters", "values", "median", "low", "high", "ilvl",
                 "old_analysis")

    def __init__(self, spec_id, runs, metric):
        self.spec_id = spec_id
        self.runs = runs
        self.characters = len({run.row.get("guid") for run in runs})
        self.values = [run.value(metric) for run in runs]
        present = [value for value in self.values if value is not None]
        self.median = median(present) if present else None
        self.low = min(present) if present else None
        self.high = max(present) if present else None
        ilvls = [run.ilvl for run in runs if run.ilvl is not None]
        self.ilvl = median(ilvls) if ilvls else None
        self.old_analysis = any(run.old_analysis for run in runs)

    @property
    def thin(self):
        return len(self.runs) < LOW_SAMPLE


class SpecGroup:
    """The specializations that played one content, most played first.

    The first row is the reference the others are set against: the most played, never "the
    best" -- the figures are not ranked, and a lower damage taken is not a verdict.
    """

    __slots__ = ("content", "kind", "name", "level_text", "rows", "total")

    def __init__(self, content, rows, name, level_text):
        self.content = content
        self.kind = content[0]
        self.rows = rows
        self.name = name
        self.level_text = level_text
        self.total = sum(len(row.runs) for row in rows)

    def gap(self, row):
        """Row against the reference as a fraction, None for the reference or no figure."""
        if row is self.rows[0]:
            return None
        return change([self.rows[0].median, row.median])


def spec_comparison(runs, role, metric, kinds=(KEY, BOSS)):
    """([SpecGroup], single, unknown): the contents played with two specializations or more.

    **One role at a time**: a tank's damage beside a mage's is not a comparison of
    specializations. Only runs that count enter (a finished key, a killed boss), only of the
    same content, and a specialization is a row when it has a figure for the measure (damage
    taken is a tank's alone). `single` counts the contents left out because only one
    specialization of the role played them, `unknown` the counted runs whose specialization
    or role the file or the table does not give: both are said on the window, so nothing
    disappears quietly.
    """
    by_content, names, unknown = {}, {}, 0
    for run in runs:
        if run.kind not in kinds or not run.counts:
            continue
        if not run.spec_id or run.role not in ROLE_METRIC:
            unknown += 1
            continue
        if run.role != role:
            continue
        by_content.setdefault(run.content, {}).setdefault(run.spec_id, []).append(run)
        names[run.content] = (run.name, run.level_text())
    groups, single = [], 0
    for content, specs in by_content.items():
        rows = [SpecRow(spec_id, spec_runs, metric) for spec_id, spec_runs in specs.items()]
        rows = [row for row in rows if row.median is not None]
        if len(rows) < 2:
            single += 1
            continue
        rows.sort(key=lambda row: (-len(row.runs), row.spec_id))
        groups.append(SpecGroup(content, rows, *names[content]))
    groups.sort(key=lambda group: (-group.total, group.name, group.level_text))
    return groups, single, unknown


# -- the best key and the best kill of each specialization ------------------------------------

TIMED = "dans les temps"


def _number(value, default):
    """A figure as the file gave it, or the default: records never stop on an odd field."""
    return value if isinstance(value, (int, float)) and not isinstance(value, bool) else default


def key_rank(run):
    """How a key is ranked among a specialization's keys, the greatest being the best.

    Timed first (a finished key that missed its timer never passes one that made it), then the
    level, then the score, then the shortest time. The score and the time are the file's own.
    """
    return (run.outcome == TIMED, run.level or 0, _number(run.score, 0.0),
            -_number(run.key_time_ms, float("inf")))


class Record:
    """The best run of one specialization, with how many runs it was picked among."""

    __slots__ = ("spec_id", "role", "best", "total", "timed")

    def __init__(self, spec_id, runs, rank):
        self.spec_id = spec_id
        self.best = max(runs, key=rank)             # the first of equals: runs are oldest first
        self.role = self.best.role
        self.total = len(runs)
        self.timed = sum(1 for run in runs if run.outcome == TIMED)


def _in_order(records):
    """Records in a neutral order -- role, then name -- never best first: this is a board of
    each specialization's own record, not a ranking of the specializations."""
    order = {role: index for index, role in enumerate(ROLE_ORDER)}
    records.sort(key=lambda record: (order.get(record.role, len(order)),
                                     label_of(record.spec_id) or "", record.spec_id))
    return records


def key_records(runs):
    """([Record], unknown): the best finished key of each specialization.

    Only keys that count (finished, timed or not); `unknown` counts those whose specialization
    the file did not write. A key finished late is a record only when the specialization has
    no key in time (`key_rank`), and the row says how many were timed.
    """
    by_spec, unknown = {}, 0
    for run in runs:
        if run.kind != KEY or not run.counts:
            continue
        if not run.spec_id:
            unknown += 1
            continue
        by_spec.setdefault(run.spec_id, []).append(run)
    return _in_order([Record(spec, spec_runs, key_rank)
                      for spec, spec_runs in by_spec.items()]), unknown


def kill_rank(run):
    """The fastest kill is the best: a shorter duration ranks higher."""
    return -_number(run.duration_ms, float("inf"))


class KillGroup:
    """One raid boss at one difficulty: the best kill of each specialization that killed it."""

    __slots__ = ("content", "name", "level_text", "rows", "kills")

    def __init__(self, content, rows, name, level_text):
        self.content = content
        self.rows = rows
        self.name = name
        self.level_text = level_text
        self.kills = sum(row.total for row in rows)


def kill_groups(runs):
    """([KillGroup], unknown): for every raid boss and difficulty, each specialization's best kill.

    **Within one boss at one difficulty only**: a three-minute fight and an eight-minute one
    are not rows of the same table. A boss met inside a key belongs to the key, not here.
    "Best" is the fastest kill, which depends on the group as much as on the specialization:
    the figures and the item level are beside it, and the window says it is not a parse.
    """
    by_content, names, unknown = {}, {}, 0
    for run in runs:
        if run.kind != BOSS or run.inside_key or not run.counts or not _number(run.duration_ms, 0):
            continue
        if not run.spec_id:
            unknown += 1
            continue
        by_content.setdefault(run.content, {}).setdefault(run.spec_id, []).append(run)
        names[run.content] = (run.name, run.level_text())
    groups = [KillGroup(content, _in_order([Record(spec, spec_runs, kill_rank)
                                            for spec, spec_runs in specs.items()]),
                        *names[content]) for content, specs in by_content.items()]
    groups.sort(key=lambda group: (-group.kills, group.name, group.level_text))
    return groups, unknown
