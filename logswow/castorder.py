# SPDX-License-Identifier: AGPL-3.0-or-later
"""The order a player cast their spells in, and which of them nobody pressed.

The file writes a cast the game triggered on its own -- a talent firing
beside a button, a trinket, a second copy of a heal -- exactly like a
cast a player pressed. Telling them apart for certain needs a maintained
list of spells, which is the structural cost this project refuses (see
CLAUDE.md, "What this deliberately does not do"). What the file *does*
give is two measurable signs, and this module uses both, together:

- **When.** A pressed spell is spaced from the player's other casts by
  the global cooldown. A triggered one is written in the same instant as
  the cast that set it off.
- **What it cost.** The caster's advanced block carries the power the
  cast spent. A triggered cast spends nothing.
- **How often.** A triggered spell rides on something the player does
  all the time; a spell fired alongside another by a *macro* is a long
  cooldown.

Measured 2026-09-27 on two real logs (a raid night and a Mythic+
session, 272 player spells with 30 casts or more): timing alone is not
enough -- "Totem guerisseur" lands beside another cast 98% of the time
and "Toucher des magi" 89%, both pressed, both always paid for. One press
of "Estropier" writes two lines under two spell ids at the same moment,
277 times each: one paid for every time, the other never. The spells
that are simultaneous at least 80% of the time *and* never cost anything
-- the unpaid "Estropier", "Nova de chi", "Bete feroce", "Piece
predestinee (pile)", "Recuperation (Germination)" -- are the ones a
player does not press, and the distribution has a clear hole between
40% and 80%.

Those two signs, per fight, still took pressed spells for triggered
ones: a healthstone, "Invisibilite superieure", "Fureur sanguinaire",
"Zenith" and two trinkets, all fired by a macro beside another spell,
all free, each only a few times. The third sign separates them cleanly:
the median gap between two casts of the genuine ones is 0.0 to 21.1 s,
and of the macro'd ones 35.9 to 186.7 s. With at least 8 casts and a
median gap of 30 s at most, exactly the five genuine spells are left.

Recalibrated the same day on sixteen real logs (32.7 million lines,
all 40 specializations, 2,386 player-fights), where that rule showed
three faults:

- **It hid both copies of one press.** Fracture writes two unpaid casts
  under two ids for every press (3,061 pairs of 3,062), and so do
  Felblade, Throw Glaive and Skull Bash: each copy stands beside the
  other, both were "triggered", and the press vanished. One spell
  written twice under one name in the same instant is now shown once:
  the paid copy, else the most cast, else the higher id.
- **It hid the pressed spell of a free pair.** Mind Flay: Insanity lands
  with a Shadowy Apparition 417 times of 417 and neither costs anything.
  The spell at a trigger's side must now be one that is **paid for** --
  at least once in the fight, because a proc can make the button free
  (Spinning Crane Kick under Dance of Chi-Ji, Disintegrate under Essence
  Burst) and Chi Burst, Twin Flame still ride on it.
- **Two copies at one instant timed a cooldown at 0.0 s.** Power
  Infusion is written twice when a talent copies it to the priest, and
  a two-minute cooldown macro'd with a trinket passed the gap test. The
  paid-neighbour rule already excludes it (the trinket is free); the
  new "faster than any button" test counts copies within the window as
  one moment, so that it does not bring it back.

And one family it could not see at all: procs that fire *alone*, faster
than any button. Soul Fragment is cast every 0.2 s (48,517 times in one
spec's fights), Empyrean Hammer and Reclamation likewise; Warcraft Logs
removes the first from its cast count. A never-paid spell whose median
gap is under `TRIGGER_FASTER_THAN_MS` is read as triggered.

Still out of reach, and stated rather than guessed: a proc that fires
alone at a button's pace (Shadowy Apparition, 1.1 s) and a pressed spell
that always lands with a paid one (Windstrike beside Lightning Bolt, if
it is pressed at all -- the file cannot say which of the two set the
other off).

So a spell is called **probably triggered** when, within one fight, it
was cast at least `TRIGGER_MIN_CASTS` times, never costing anything, and
either at least `TRIGGER_SHARE` of its casts landed within
`TRIGGER_WINDOW_MS` of a paid spell with a median gap of at most
`TRIGGER_MAX_MEDIAN_GAP_MS`, or the median gap between the moments it
was cast is under `TRIGGER_FASTER_THAN_MS`, or it is the second copy of a spell written
twice under one name. It is a reading of the file, stated on the page,
and the reader can overrule it with one click.
"""

TRIGGER_WINDOW_MS = 20
TRIGGER_SHARE = 0.8
TRIGGER_MIN_CASTS = 8
TRIGGER_MAX_MEDIAN_GAP_MS = 30000
TRIGGER_FASTER_THAN_MS = 500

# The casts one player's sequence keeps per segment. A Mythic+ key is
# about 3,700 per player, so this only guards against a file nobody has
# seen yet; past it, `Player.cast_log_full` says the sequence is cut.
MAX_CAST_LOG = 20000


def classify_triggered(cast_log):
    """The spell ids of `cast_log` that were probably not pressed.

    `cast_log` is [(ts, spell_id, name, paid, from_pet)]. Casts by the
    player's summons are left out: they are shown as their own group,
    and a pet's attacks follow rules of their own.
    """
    stats = spell_stats(cast_log)
    chosen = set()
    for spell_id, row in stats.items():
        if row["casts"] < TRIGGER_MIN_CASTS or row["paid"]:
            continue
        rides = (row["beside_paid"] >= TRIGGER_SHARE * row["casts"]
                 and row["median_gap"] <= TRIGGER_MAX_MEDIAN_GAP_MS)
        if rides or row["moment_gap"] < TRIGGER_FASTER_THAN_MS:
            chosen.add(spell_id)
    return frozenset(chosen | _echoes(stats))


def _echoes(stats):
    """One press written twice under one name: every copy but one."""
    by_name = {}
    for spell_id, row in stats.items():
        by_name.setdefault(row["name"], []).append(spell_id)
    hidden = set()
    for ids in by_name.values():
        if len(ids) < 2:
            continue
        kept = max(ids, key=lambda i: (stats[i]["paid"] > 0, stats[i]["casts"], i))
        hidden.update(
            i for i in ids
            if i != kept and not stats[i]["paid"] and stats[i]["casts"] >= TRIGGER_MIN_CASTS
            and stats[i]["same_name"] >= TRIGGER_SHARE * stats[i]["casts"])
    return hidden


def spell_stats(cast_log):
    """Per spell id of the player's own casts, what the rule reads.

    casts, paid (how many spent power), beside (landed within the window
    of another spell), beside_paid (of a spell that spent power at least
    once in this fight), same_name (of another id with the same name),
    median_gap (between two casts, as the rule was calibrated), and
    moment_gap (between two *moments*: copies within the window are one).

    Two gaps, because each question needs its own. Dire Beast summons
    two beasts at one instant: between casts its median is 7 s, between
    moments 40 to 56 s, which is where macro'd cooldowns sit (36 to
    187 s, measured between casts). And Power Infusion written twice at
    once has a median of 0.0 s between casts, which the "faster than any
    button" test must not read as a spell fired twice a second.
    """
    own = sorted((entry for entry in cast_log if not entry[4]), key=lambda e: e[0])
    # A spell that is paid for is a button, even on the casts a proc made
    # free: a Spinning Crane Kick under Dance of Chi-Ji, a Disintegrate
    # under Essence Burst still set off what rides on them.
    paying = {entry[1] for entry in own if entry[3]}
    stats = {}
    start = 0
    for index, (ts, spell_id, name, paid, _pet) in enumerate(own):
        while own[start][0] < ts - TRIGGER_WINDOW_MS:
            start += 1
        beside = beside_paid = same_name = False
        probe = start
        while probe < len(own) and own[probe][0] <= ts + TRIGGER_WINDOW_MS:
            other = own[probe]
            if probe != index and other[1] != spell_id:
                beside = True
                beside_paid = beside_paid or other[1] in paying
                same_name = same_name or other[2] == name
            probe += 1
        row = stats.get(spell_id)
        if row is None:
            row = stats[spell_id] = {"name": name, "casts": 0, "paid": 0, "beside": 0,
                                     "beside_paid": 0, "same_name": 0, "times": [],
                                     "moments": []}
        row["casts"] += 1
        row["paid"] += bool(paid)
        row["beside"] += beside
        row["beside_paid"] += beside_paid
        row["same_name"] += same_name
        row["times"].append(ts)
        if not row["moments"] or ts - row["moments"][-1] > TRIGGER_WINDOW_MS:
            row["moments"].append(ts)
    for row in stats.values():
        row["median_gap"] = _median_gap(row.pop("times"))
        row["moment_gap"] = _median_gap(row.pop("moments"))
    return stats


def _median_gap(times):
    """The median time between two consecutive casts, in milliseconds."""
    gaps = sorted(later - earlier for earlier, later in zip(times, times[1:]))
    if not gaps:
        return 0
    middle = len(gaps) // 2
    return gaps[middle] if len(gaps) % 2 else (gaps[middle - 1] + gaps[middle]) / 2


def split_by_pull(cast_log, blocks, lead_ms):
    """[(block or None, [casts])]: each cast in the pull it belongs to.

    A pull is bounded by its first and last *hit*, and a player casts on
    both sides of those: the opener before anything is hit, a last spell
    after the last mob died. So a cast belongs to a pull from `lead_ms`
    before its first hit to `lead_ms` after its last. Two pulls are more
    than the pull gap apart, so the two windows can meet only in that
    gap; a cast there goes to the nearer pull. Whatever falls in no
    window (buffs in the corridor) is returned last, under None.

    The first version stopped each window at the last hit, and on a real
    key 57 casts landed "between the pulls", most of them a second after
    one had ended.
    """
    ordered = sorted(cast_log, key=lambda entry: entry[0])
    groups = [(block, []) for block in blocks]
    outside = []
    index = 0
    for entry in ordered:
        ts = entry[0]
        # Skip the pulls this cast is already too late for.
        while index < len(blocks) and ts > blocks[index].end_ts + lead_ms:
            index += 1
        candidates = [
            position for position in (index, index + 1)
            if position < len(blocks)
            and blocks[position].start_ts - lead_ms <= ts <= blocks[position].end_ts + lead_ms
        ]
        if not candidates:
            outside.append(entry)
            continue
        nearest = min(candidates, key=lambda position: _distance(blocks[position], ts))
        groups[nearest][1].append(entry)
    return groups + [(None, outside)]


def _distance(block, ts):
    """How far a moment is from a pull: 0 inside it."""
    if ts < block.start_ts:
        return block.start_ts - ts
    if ts > block.end_ts:
        return ts - block.end_ts
    return 0
