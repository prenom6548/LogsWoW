#!/usr/bin/env python3
"""Cross-check a real log's analysis against itself.

The unit tests run on a fabricated fixture and prove the logic; this
runs on a *real* file and proves the arithmetic holds together at scale,
where the fixture cannot. Every check below is a relation that must be
true by construction -- two ledgers that count the same events from
different sides -- so a violation is a bug in the accounting, never a
property of the fight.

    python3 tools/check-invariants.py WoWCombatLog.txt

Exits non-zero on the first failing invariant. No network, no
dependencies, and it never prints a player's realm.

Read problems are reported too, but *after* the arithmetic and as their
own verdict: a file with one stray line is still a file whose ledgers
must add up, and stopping before the first invariant ran told the reader
nothing about the thing this tool exists to check.
"""

import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.dirname(HERE))

from logswow.analysis import SegmentAnalysis  # noqa: E402
from logswow.parse import LogFile  # noqa: E402
from logswow.segment import Splitter  # noqa: E402


class Failure(Exception):
    pass


def check(condition, label, detail=""):
    if condition:
        print("  ok   %s" % label)
        return
    raise Failure("%s%s" % (label, (" -- " + detail) if detail else ""))


def audit_segment(segment):
    a = segment.analysis
    players = list(a.players.values())
    print("\n[%d] %s" % (segment.index, segment.label))

    # 1. The segment's damage total is the sum of its players' totals.
    check(a.total_damage == sum(p.damage_done for p in players),
          "total damage == sum of players", "%d vs %d" % (
              a.total_damage, sum(p.damage_done for p in players)))

    # 2. Each player's damage is the sum of their abilities.
    for p in players:
        by_ability = sum(x.total for x in p.damage_by_ability.values())
        check(p.damage_done == by_ability,
              "%s: damage == sum of abilities" % p.short_name,
              "%d vs %d" % (p.damage_done, by_ability))

    # 3. Each ability's total is the sum of what it did to each target.
    #    (Targets are capped at 80 names, so only check uncapped ones.)
    for p in players:
        for x in p.damage_by_ability.values():
            if len(x.targets) < 80:
                check(x.total == sum(x.targets.values()),
                      "%s / %s: ability == sum of targets" % (p.short_name, x.name),
                      "%d vs %d" % (x.total, sum(x.targets.values())))

    # 4. Healing: effective == sum of abilities == sum over targets.
    for p in players:
        if not (p.healing_done or p.overhealing):
            continue
        by_ability = sum(x.total for x in p.healing_by_ability.values())
        check(p.healing_done == by_ability,
              "%s: healing == sum of abilities" % p.short_name,
              "%d vs %d" % (p.healing_done, by_ability))
        if "autres" not in p.healing_to:
            check(p.healing_done == sum(p.healing_to.values()),
                  "%s: healing == sum over targets" % p.short_name,
                  "%d vs %d" % (p.healing_done, sum(p.healing_to.values())))
        by_ability_over = sum(x.overheal for x in p.healing_by_ability.values())
        check(p.overhealing == by_ability_over,
              "%s: overheal == sum of abilities' overheal" % p.short_name)

    # 5. What the group took equals what enemies (and friendly fire) dealt.
    taken = sum(p.damage_taken for p in players)
    for p in players:
        by_ability = sum(x.total for x in p.taken_by_ability.values())
        check(p.damage_taken == by_ability,
              "%s: taken == sum of abilities" % p.short_name)
    timeline_taken = sum(row[1] for row in a.timeline_series()[0])
    check(taken == timeline_taken, "taken == timeline total",
          "%d vs %d" % (taken, timeline_taken))

    # 6. Enemies: what they dealt to us is what we took from non-friends.
    dealt = sum(e.damage_done for e in a.enemies.values())
    check(dealt <= taken, "enemy damage dealt <= group damage taken",
          "%d vs %d" % (dealt, taken))
    # ...and what they took from us is what we dealt (both capped at 150
    # enemy names, so compare only when nothing was dropped).
    if len(a.enemies) < 150:
        received = sum(e.damage_taken for e in a.enemies.values())
        check(received == a.total_damage, "enemy damage taken == group damage done",
              "%d vs %d" % (received, a.total_damage))

    # 7. Pulls add up to the run (after crumbs were dropped, <= total).
    pulls = sum(b.damage_done for b in a.blocks)
    check(pulls <= a.total_damage and pulls >= a.total_damage * 0.99,
          "pulls sum to the run (within the dropped crumbs)",
          "%d vs %d" % (pulls, a.total_damage))
    for b in a.blocks:
        check(0 <= b.damage_boss <= b.damage_done, "pull boss share within total")
        check(b.end_ts >= b.start_ts, "pull ends after it starts")
    for earlier, later in zip(a.blocks, a.blocks[1:]):
        check(later.start_ts >= earlier.end_ts, "pulls do not overlap")

    # 8. Deaths: segment list, player counters and timeline agree.
    check(len(a.deaths) == sum(p.deaths for p in players),
          "deaths list == sum of player death counters")
    timeline_deaths = sum(row[3] for row in a.timeline_series()[0])
    check(len(a.deaths) == timeline_deaths, "deaths == timeline deaths")
    check(sum(b.deaths for b in a.blocks) <= len(a.deaths),
          "pull deaths <= deaths (a death outside any pull is possible)")
    for d in a.deaths:
        check(d["ts"] >= (a.first_ts or 0), "death is inside the segment")

    # 9. Bounded quantities stay bounded.
    duration = max(1, a.duration_ms)
    for p in players:
        for ms in p.auras_gained.values():
            check(ms <= duration + 1000, "%s: aura uptime <= fight" % p.short_name,
                  "%d ms vs %d ms" % (ms, duration))
        check(p.downtime_ms <= duration + 1000, "%s: downtime <= fight" % p.short_name)
        check(p.min_hp_fraction is None or 0 <= p.min_hp_fraction <= 1,
              "%s: health fraction in [0,1]" % p.short_name)
        check(sum(p.casts_by_spell.values()) == p.casts,
              "%s: casts by spell == casts" % p.short_name)
        check(p.damage_to_bosses <= p.damage_done, "%s: boss share <= damage" % p.short_name)
    series, _bucket = a.timeline_series()
    for row in series:
        check(row[4] is None or 0 <= row[4] <= 1, "pool ratio in [0,1]")
    casts = a.enemy_casts
    check(casts["commences"] == casts["aboutis"] + casts["coupes"]
          + casts["cible morte"] + casts["autre"],
          "enemy casts: outcomes sum to starts", str(casts))

    # 10. Interrupts: the player counters and the segment's list agree.
    check(sum(p.interrupts for p in players) == sum(a.interrupted_spells.values()),
          "interrupts: player counters == segment list")
    for p in players:
        check(sum(p.interrupted_spells.values()) == p.interrupts,
              "%s: interrupted spells == interrupts" % p.short_name)
        check(sum(p.dispelled_spells.values()) == p.dispels,
              "%s: dispelled spells == dispels" % p.short_name)


def main(argv):
    if len(argv) != 2:
        print(__doc__)
        return 2
    path = argv[1]
    if not os.path.isfile(path):
        print("Not a readable file: %s" % path)
        return 2
    try:
        log = LogFile(path)
        splitter = Splitter(analysis_factory=SegmentAnalysis)
        for event in log.events():
            splitter.feed(event)
        segments = splitter.finish()
    except OSError as error:
        print("Could not read %s: %s" % (path, error.strerror or error))
        return 2
    print("%s : %d segments, %d problemes de lecture" % (
        os.path.basename(path), len(segments), log.problems.total))

    # Every check runs inside the guard: one raised outside it used to
    # come out as a traceback, which is the opposite of what a tool that
    # exists to report cleanly should do.
    try:
        check(len(segments) > 0, "at least one segment")
        for earlier, later in zip(segments, segments[1:]):
            check(later.start_ts >= earlier.start_ts, "segments are in file order")
        for segment in segments:
            audit_segment(segment)
    except Failure as failure:
        print("\nINVARIANT VIOLATED: %s" % failure)
        return 1

    name = os.path.basename(path)
    if log.problems.total:
        print("\nAll invariants hold on %s, but %d line(s) could not be read:"
              % (name, log.problems.total))
        for reason, count in sorted(
            log.problems.by_reason.items(), key=lambda item: -item[1]
        )[:5]:
            print("  %6d  %s" % (count, reason))
        print("Run `python3 -m logswow diagnose %s` to see them." % name)
        return 1
    print("\nAll invariants hold on %s." % name)
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
