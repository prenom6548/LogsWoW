#!/usr/bin/env python3
# SPDX-License-Identifier: AGPL-3.0-or-later
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
from logswow.castorder import split_by_pull  # noqa: E402
from logswow.parse import LogFile  # noqa: E402
from logswow.segment import Splitter  # noqa: E402


class Failure(Exception):
    pass


def check(condition, label, detail=""):
    if condition:
        print("  ok   %s" % label)
        return
    raise Failure("%s%s" % (label, (" -- " + detail) if detail else ""))


def _damage(a, players):
    """Damage: the segment, each player, each ability, each target."""
    # 1. The segment's damage total is the sum of its players' totals.
    check(a.total_damage == sum(p.damage_done for p in players),
          "total damage == sum of players", "%d vs %d" % (
              a.total_damage, sum(p.damage_done for p in players)))

    # 1b. What enemies' shields ate is inside that total, never beside it.
    check(0 <= a.shield_damage <= a.total_damage, "damage into shields within the total",
          "%d of %d" % (a.shield_damage, a.total_damage))

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


def _support(a, players):
    """An Evoker's credit is somebody's damage: both ends of the same lines."""
    given = sum(p.support_damage for p in players)
    received = sum(p.support_received for p in players)
    check(given == received, "support credited == support received",
          "%d vs %d" % (given, received))


def _healing(a, players):
    """Healing: effective, per ability, per target, and overheal."""
    # 4. Healing: effective == sum of abilities == sum over targets.
    for p in players:
        if not (p.healing_done or p.overhealing):
            continue
        by_ability = sum(x.total for x in p.healing_by_ability.values())
        check(p.healing_done == by_ability,
              "%s: healing == sum of abilities" % p.short_name,
              "%d vs %d" % (p.healing_done, by_ability))
        # The targets are what was healed; health a totem moved away from
        # a player is taken out of the total but belongs to no target.
        if "autres" not in p.healing_to:
            check(p.healing_done == sum(p.healing_to.values()) - p.moved_health,
                  "%s: healing == sum over targets - moved health" % p.short_name,
                  "%d vs %d" % (p.healing_done, sum(p.healing_to.values()) - p.moved_health))
        by_ability_over = sum(x.overheal for x in p.healing_by_ability.values())
        check(p.overhealing == by_ability_over,
              "%s: overheal == sum of abilities' overheal" % p.short_name)
    check(a.moved_health == sum(p.moved_health for p in players),
          "moved health == sum of players'")
    check(a.total_healing == sum(p.healing_done for p in players),
          "total healing == sum of players", "%d vs %d" % (
              a.total_healing, sum(p.healing_done for p in players)))


def _taken(a, players):
    """Damage taken, on the group's side and the enemies'."""
    # 5. What the group took equals what enemies (and friendly fire) dealt.
    taken = sum(p.damage_taken for p in players)
    for p in players:
        by_ability = sum(x.total for x in p.taken_by_ability.values())
        check(p.damage_taken == by_ability,
              "%s: taken == sum of abilities" % p.short_name)
    timeline_taken = sum(row[1] for row in a.timeline_series()[0])
    # The timeline is what the *group* took, summons included; a player's
    # own row is not.
    pets = sum(p.pet_damage_taken for p in players)
    check(taken + pets == timeline_taken, "taken (+ pets) == timeline total",
          "%d + %d vs %d" % (taken, pets, timeline_taken))

    # 6. Enemies: what they dealt to us is what we took from non-friends.
    dealt = sum(e.damage_done for e in a.enemies.values())
    check(dealt <= taken + pets, "enemy damage dealt <= group damage taken",
          "%d vs %d" % (dealt, taken + pets))
    # ...and what they took from us is what we dealt (both capped at 150
    # enemy names, so compare only when nothing was dropped).
    if len(a.enemies) < 150:
        received = sum(e.damage_taken for e in a.enemies.values())
        check(received == a.total_damage, "enemy damage taken == group damage done",
              "%d vs %d" % (received, a.total_damage))


def _pulls(a, players):
    """Pulls: they add up to the run and never overlap."""
    # 7. Pulls add up to the run (after crumbs were dropped, <= total).
    pulls = sum(b.damage_done for b in a.blocks)
    check(pulls <= a.total_damage and pulls >= a.total_damage * 0.99,
          "pulls sum to the run (within the dropped crumbs)",
          "%d vs %d" % (pulls, a.total_damage))
    # 7b. Physical / magic: each pull's schools add up to its own totals,
    # and the run's to the group's (crumbs included on both sides).
    check(sum(a.done_by_school.values()) == a.total_damage,
          "damage done by school == group damage done")
    taken = sum(p.damage_taken + p.pet_damage_taken for p in players)
    check(sum(a.taken_by_school.values()) == taken,
          "damage taken by school == players' and summons' damage taken",
          "%d vs %d" % (sum(a.taken_by_school.values()), taken))
    for b in a.blocks:
        check(sum(b.done_by_school.values()) == b.damage_done, "pull schools == pull damage")
        check(sum(b.taken_by_school.values()) == b.damage_taken, "pull schools == pull taken")
        check(0 <= b.damage_boss <= b.damage_done, "pull boss share within total")
        check(b.end_ts >= b.start_ts, "pull ends after it starts")
    for earlier, later in zip(a.blocks, a.blocks[1:]):
        check(later.start_ts >= earlier.end_ts, "pulls do not overlap")


def _deaths(a, players):
    """Deaths, counted three ways."""
    # 8. Deaths: segment list, player counters and timeline agree.
    check(len(a.deaths) == sum(p.deaths for p in players),
          "deaths list == sum of player death counters")
    timeline_deaths = sum(row[3] for row in a.timeline_series()[0])
    check(len(a.deaths) == timeline_deaths, "deaths == timeline deaths")
    check(sum(b.deaths for b in a.blocks) <= len(a.deaths),
          "pull deaths <= deaths (a death outside any pull is possible)")
    for d in a.deaths:
        check(d["ts"] >= (a.first_ts or 0), "death is inside the segment")


def _bounds(a, players):
    """Quantities that have a bound by construction."""
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


def _shields(a, players):
    """Shields: what each one ate sums to the player's total."""
    # 9b. Shields: what each one ate sums to the player's total.
    for p in players:
        if not p.absorb_by_ability:
            continue
        by_ability = sum(x.total for x in p.absorb_by_ability.values())
        check(p.absorb_done == by_ability,
              "%s: absorbed == sum of shields" % p.short_name,
              "%d vs %d" % (p.absorb_done, by_ability))


def _interrupts(a, players):
    """Interrupts and dispels: counters and lists agree."""
    # 10. Interrupts: the player counters and the segment's list agree.
    check(sum(p.interrupts for p in players) == sum(a.interrupted_spells.values()),
          "interrupts: player counters == segment list")
    for p in players:
        check(sum(p.interrupted_spells.values()) == p.interrupts,
              "%s: interrupted spells == interrupts" % p.short_name)
        check(sum(p.dispelled_spells.values()) == p.dispels,
              "%s: dispelled spells == dispels" % p.short_name)


def _casts(a, players):
    """The cast order: every cast exactly once, and triggered spells among them."""
    for p in players:
        if not p.cast_log_full:
            check(len(p.cast_log) == p.casts, "%s: cast order == casts" % p.short_name,
                  "%d vs %d" % (len(p.cast_log), p.casts))
        logged = {entry[1] for entry in p.cast_log}
        check(p.triggered <= logged, "%s: triggered spells were cast" % p.short_name)
        placed = sum(len(casts) for _block, casts in
                     split_by_pull(p.cast_log, a.blocks, a.pull_gap_ms))
        check(placed == len(p.cast_log), "%s: every cast in one pull or between" % p.short_name,
              "%d vs %d" % (placed, len(p.cast_log)))


def _melee(a, players):
    """The enemy's swings at players: every landed one placed once, and inside damage taken."""
    for p in players:
        m = p.melee_taken
        hits = m.get("hit", 0)
        check(hits == m.get("front", 0) + m.get("behind", 0) + m.get("unplaced", 0),
              "%s: every landed swing placed once" % p.short_name)
        check(m.get("crit", 0) <= hits and m.get("partial_block", 0) <= hits,
              "%s: crits and partial blocks among the hits" % p.short_name)
        check(m.get("avoided_front", 0) + m.get("avoided_behind", 0)
              <= m.get("PARRY", 0) + m.get("DODGE", 0),
              "%s: placed parries and dodges among the parries and dodges" % p.short_name)
        melee = p.taken_by_ability.get((0, "Attaque"))
        check(hits <= (melee.hits if melee else 0),
              "%s: landed swings are in the melee taken" % p.short_name,
              "%d vs %d" % (hits, melee.hits if melee else 0))


FAMILIES = (_damage, _support, _healing, _taken, _pulls, _deaths, _bounds, _shields, _interrupts,
            _casts, _melee)


def audit_segment(segment):
    """Every family of invariants on one segment; returns what failed.

    One failure no longer stops the run: a family that fails is reported
    and the next one still runs, and so does the next segment. A real
    dungeon log failed the pooled-health bound on one key and, because
    the tool stopped there, nothing after that key was ever checked.
    """
    a = segment.analysis
    players = list(a.players.values())
    print("\n[%d] %s" % (segment.index, segment.label))
    failures = []
    for family in FAMILIES:
        try:
            family(a, players)
        except Failure as failure:
            print("  FAIL %s" % failure)
            failures.append("[%d] %s" % (segment.index, failure))
    return failures


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
    failures = []
    try:
        check(len(segments) > 0, "at least one segment")
        for earlier, later in zip(segments, segments[1:]):
            check(later.start_ts >= earlier.start_ts, "segments are in file order")
    except Failure as failure:
        failures.append(str(failure))
    for segment in segments:
        failures.extend(audit_segment(segment))
        # A key's trash pulls have analyses of their own (0.12.0): every
        # family holds on each, and each must count what the key counted
        # for that pull -- a pull that sees more or less than its key is a
        # pull fed the wrong events.
        for pull in segment.pulls:
            failures.extend(audit_segment(pull))
            try:
                check(pull.analysis.total_damage == pull.block.damage_done,
                      "%s: damage == the key's for that pull" % pull.label,
                      "%d vs %d" % (pull.analysis.total_damage, pull.block.damage_done))
            except Failure as failure:
                failures.append(str(failure))
    if failures:
        print("\n%d INVARIANT(S) VIOLATED:" % len(failures))
        for failure in failures:
            print("  %s" % failure)
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
