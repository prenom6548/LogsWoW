#!/usr/bin/env python3
# SPDX-License-Identifier: AGPL-3.0-or-later
"""Check, on a real log, that the history keeps exactly what the analysis computed.

    python3 tools/check-history.py WoWCombatLog.txt

Reads the log, builds the night with *every* player followed (the strictest case),
writes it to a throw-away history, reads it back, and compares every figure of every
fight with the analysis object it came from, to the unit. Then it builds the night
again following nobody and checks that no player's name or GUID is anywhere in it.

What it proves is that nothing was lost or altered between the analysis and the file,
and that a pick-up group leaves no trace -- not that the analysis is right (that is
`check-invariants.py` and the outside comparisons). No network, nothing is kept: the
throw-away history is deleted when the tool ends, and it never prints a realm.

Exits 0 when everything holds, 1 on the first disagreement, 2 on a bad call.
"""

import json
import os
import sys
import tempfile
import time

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.dirname(HERE))

from logswow import history, preview  # noqa: E402
from logswow.analysis import SegmentAnalysis  # noqa: E402
from logswow.parse import LogFile  # noqa: E402
from logswow.report_layouts import contents, nested  # noqa: E402
from logswow.segment import Splitter  # noqa: E402


class Failure(Exception):
    pass


def check(condition, label, detail=""):
    if not condition:
        raise Failure("%s %s" % (label, detail))


def compare_fight(record, segment, everyone):
    analysis = segment.analysis
    label = "%s #%d" % (record["name"], segment.index)
    check(record["duration_ms"] == analysis.duration_ms, label + ": duration")
    check(record["outcome"] == segment.outcome, label + ": outcome")
    group = record["group"]
    check(group["damage"] == analysis.total_damage, label + ": group damage")
    check(group["healing"] == analysis.total_healing, label + ": group healing")
    check(group["deaths"] == len(analysis.deaths), label + ": deaths")
    check(group["absorb_done"] == sum(p.absorb_done for p in analysis.players.values()),
          label + ": shields cast")
    check(group["taken"] == sum(p.damage_taken for p in analysis.players.values()),
          label + ": damage taken")
    check(sum(group["composition"].values()) == len(analysis.participants()),
          label + ": composition adds up to the participants")
    mine = preview.group_rates(analysis)
    theirs = history.rates(group, record["duration_ms"])
    for name in ("dps", "hps", "taken"):
        check(abs(mine[name] - theirs[name]) < 1e-6 * max(1.0, abs(mine[name])),
              label + ": group " + name)
    rows = {row["guid"]: row for row in record["players"]}
    check(set(rows) == {p.guid for p in analysis.participants()}, label + ": followed rows")
    for guid, row in rows.items():
        player = analysis.players[guid]
        check(row["damage"] == player.damage_done and row["healing"] == player.healing_done
              and row["absorb_done"] == player.absorb_done
              and row["taken"] == player.damage_taken
              and row["absorbed"] == player.absorbed_taken
              and row["deaths"] == player.deaths, label + ": a player's totals")
        mine = preview.rates(analysis, player)
        theirs = history.rates(row, record["duration_ms"])
        for name in ("dps", "hps", "taken"):
            check(abs(mine[name] - theirs[name]) < 1e-6 * max(1.0, abs(mine[name])),
                  label + ": player " + name)
        if player.gear is not None:
            check(abs(row["ilvl"] - player.gear.average) < 0.01, label + ": item level")
    everyone.update(rows)
    if record["type"] == "encounter":
        health = record["boss_health_end"]
        check(health is None or 0.0 <= health <= 1.0, label + ": boss health in 0..1",
              "(%r)" % health)
        check((health is None) == (not analysis.boss_hp), label + ": boss health presence")


def compare_night(record, segments):
    held, inside = contents(segments), nested(segments)
    expected = [segment for segment in segments
                if segment.analysis is not None and segment.index not in inside
                and (segment.kind == "keystone"
                     or (segment.kind == "encounter" and not segment.never_fought))]
    check(len(record["fights"]) == len(expected), "one record per top-level fight",
          "(%d against %d)" % (len(record["fights"]), len(expected)))
    everyone, pulls, bosses = set(), 0, 0
    for fight, segment in zip(record["fights"], expected):
        compare_fight(fight, segment, everyone)
        if fight["type"] == "key":
            children = held.get(segment.index, [])
            trash = [child for child in children if child.kind == "pull"]
            fought = [child for child in children
                      if child.kind == "encounter" and not child.never_fought]
            check(len(fight["pulls"]) == len(trash), "the key keeps every trash pull")
            check(len(fight["bosses"]) == len(fought), "the key keeps every boss it holds")
            for entry, child in zip(fight["pulls"], trash):
                check(entry["damage"] == child.analysis.total_damage, "a pull's damage")
                check(entry["deaths"] == len(child.analysis.deaths), "a pull's deaths")
                average = entry["health_average"]
                check(average is None or 0.0 <= average <= 1.0, "a pull's health in 0..1",
                      "(%r)" % average)
                check(entry["offset_ms"] >= 0, "a pull starts inside its key")
            for entry, child in zip(fight["bosses"], fought):
                compare_fight(entry, child, everyone)
            pulls += len(trash)
            bosses += len(fought)
    return len(record["fights"]), pulls, bosses, len(everyone)


def main(argv):
    if len(argv) != 2 or not os.path.isfile(argv[1]):
        print(__doc__)
        return 2
    started = time.time()
    log = LogFile(argv[1])
    splitter = Splitter(analysis_factory=SegmentAnalysis)
    for event in log.events():
        splitter.feed(event)
    segments = splitter.finish()
    print("%s : %d segments, game %s, read in %.0f s" % (
        os.path.basename(argv[1]), len(segments), log.build_version or "?",
        time.time() - started))
    everyone = [row[0] for row in history.players_seen(segments)]
    try:
        with tempfile.TemporaryDirectory() as folder:
            root = os.path.join(folder, "historique")
            slug = history.create_folder(root, "Verification")
            record = history.build_night(log, segments, everyone)
            path, _replaced = history.save_night(root, slug, record)
            stored, notes = history.read_night(path)
            check(notes == [], "a night just written reads with no note", repr(notes))
            check(stored == json.loads(json.dumps(record)), "the file reads back as written")
            fights, pulls, bosses, players = compare_night(stored, segments)
            size = os.path.getsize(path)
            print("  ok: %d fights, %d trash pulls, %d bosses inside keys, %d players, "
                  "%d bytes (%.1f KB)" % (fights, pulls, bosses, players, size, size / 1024.0))
            rows = sum(len(fight["players"]) + sum(len(boss["players"])
                                                   for boss in fight.get("bosses", []))
                       for fight in stored["fights"])
            check(size < 1500 * max(1, fights + bosses) + 300 * rows + 400 * pulls,
                  "the file stays small", "(%d bytes, %d player rows)" % (size, rows))
            # Nobody followed: no player name, no GUID, anywhere in the file.
            anonymous = history.build_night(log, segments, ())
            text = json.dumps(anonymous, ensure_ascii=False)
            names = {player.short_name
                     for segment in segments if segment.analysis is not None
                     for player in segment.analysis.participants()}
            leaked = [name for name in names if name and '"%s"' % name in text]
            check(not leaked, "no followed player, no name in the file",
                  "(%d leaked)" % len(leaked))
            check("Player-" not in text, "no player GUID in the file")
            check(all(fight["players"] == [] for fight in anonymous["fights"]),
                  "no player row for a pick-up group")
            check(len(anonymous["fights"]) == len(stored["fights"]), "same fights either way")
    except Failure as failure:
        print("FAIL: %s" % failure)
        return 1
    print("All history checks hold on %s." % os.path.basename(argv[1]))
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
