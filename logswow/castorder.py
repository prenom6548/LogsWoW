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

So a spell is called **probably triggered** when, within one fight, it
was cast at least `TRIGGER_MIN_CASTS` times, at least `TRIGGER_SHARE` of
them within `TRIGGER_WINDOW_MS` of another spell of the same player,
none of them costing anything, and the median gap between two of them
is at most `TRIGGER_MAX_MEDIAN_GAP_MS`. It is a reading of the file,
stated on the page, and the reader can overrule it with one click.
"""

TRIGGER_WINDOW_MS = 20
TRIGGER_SHARE = 0.8
TRIGGER_MIN_CASTS = 8
TRIGGER_MAX_MEDIAN_GAP_MS = 30000

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
    own = sorted((entry for entry in cast_log if not entry[4]), key=lambda e: e[0])
    stats = {}                      # spell id -> [casts, beside another, paid, times]
    start = 0
    for index, (ts, spell_id, _name, paid, _pet) in enumerate(own):
        while own[start][0] < ts - TRIGGER_WINDOW_MS:
            start += 1
        beside = False
        probe = start
        while probe < len(own) and own[probe][0] <= ts + TRIGGER_WINDOW_MS:
            if probe != index and own[probe][1] != spell_id:
                beside = True
                break
            probe += 1
        row = stats.setdefault(spell_id, [0, 0, 0, []])
        row[0] += 1
        row[1] += beside
        row[2] += bool(paid)
        row[3].append(ts)
    return frozenset(
        spell_id for spell_id, (casts, beside, paid, times) in stats.items()
        if casts >= TRIGGER_MIN_CASTS and not paid and beside >= TRIGGER_SHARE * casts
        and _median_gap(times) <= TRIGGER_MAX_MEDIAN_GAP_MS
    )


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
