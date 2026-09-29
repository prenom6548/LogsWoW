# SPDX-License-Identifier: AGPL-3.0-or-later
"""Cutting a log into the things a player actually thinks in: pulls.

Three markers do the work, and all three are written by the client
itself into the file, which is why none of this depends on an addon:

    ENCOUNTER_START / ENCOUNTER_END        a boss attempt
    CHALLENGE_MODE_START / CHALLENGE_MODE_END   a Mythic+ key
    (neither)                               one open session

A key contains boss pulls, so segments nest: an event inside a key that
is also inside a boss encounter is fed to both. That is deliberate and
matches how anyone reads a dungeon run -- the whole key, and each boss
within it.
"""

from .i18n import N_, _
from .tokenize import as_int

# Lines that mean somebody fought: a hit, or a swing that missed. An
# encounter with none of them was never fought -- a real raid opened on
# one that lasted 8 ms, 18 lines and not one of these, and it was counted
# as a wipe. The shortest real encounter in two logs had 7,867.
FIGHT_KINDS = frozenset({"_DAMAGE", "_DAMAGE_LANDED", "_MISSED", "_SHIELD", "_SPLIT"})

# A key's success flag says it was *completed*, not that it was timed: the
# owner's late Val Aveuglant +13 (30:23) carries a 1 like every timed key.
# What tells them apart is the run's score, the next field: a timed key
# scores at least its level's base score, a late one less. The base is
# Raider.IO's published table (+2 to +30): 125 + 15 per level, plus 15 at
# each affix step, levels 4, 7, 10 and 12 -- the formula gives all 29 rows.
# On 14 completed keys of real logs (levels 10 to 14), the 13 timed ones
# scored from 3 to 15 points above it -- 15 is the most speed adds, and a
# +10 in 19:16 scored exactly 335.0 -- and the late one 60 below; the
# season's timers, as Raider.IO's API gives them, agree on every one.
KEY_SCORE_START = 125
KEY_SCORE_PER_LEVEL = 15
KEY_SCORE_STEPS = (4, 7, 10, 12)


def key_base_score(level):
    """The score a key of this level is worth when timed, before the
    bonus for speed: what a completed key must reach to be in time."""
    steps = sum(1 for step in KEY_SCORE_STEPS if level >= step)
    return KEY_SCORE_START + KEY_SCORE_PER_LEVEL * (level + steps)


# Difficulty ids, as the client writes them. Anything unlisted is shown
# by number rather than guessed at.
DIFFICULTY_NAMES = {
    1: N_("Normal"),
    2: N_("Héroïque"),
    3: N_("10 joueurs"),
    4: N_("25 joueurs"),
    5: N_("10 héroïque"),
    6: N_("25 héroïque"),
    7: N_("Raid Recherche"),
    8: N_("Mythique+"),
    9: N_("40 joueurs"),
    11: N_("Héroïque scénario"),
    12: N_("Normal scénario"),
    14: N_("Normal"),
    15: N_("Héroïque"),
    16: N_("Mythique"),
    17: N_("Raid Recherche"),
    23: N_("Mythique"),
    24: N_("Marche du temps"),
    33: N_("Marche du temps"),
    151: N_("Raid Recherche"),
    167: N_("Torghast"),
}


def _text(fields, index, default):
    """A field that must be a name: text, or the default.

    A damaged line can carry a bracket where a name should be, and the
    field then arrives as a list. Found by fuzzing on 2026-09-27: the
    encounter was named with a list, and the whole report stopped on it.
    """
    value = fields[index] if len(fields) > index else ""
    return value if isinstance(value, str) and value else default


def _number(text):
    """'383.191437' -> 383.191437; None for anything that is not a finite number."""
    try:
        value = float(text)
    except (TypeError, ValueError):
        return None
    return value if value == value and abs(value) != float("inf") else None


def difficulty_name(difficulty_id):
    """A difficulty id as the reader says it, or its number when unknown."""
    if not difficulty_id:
        return ""
    if difficulty_id in DIFFICULTY_NAMES:
        return _(DIFFICULTY_NAMES[difficulty_id])
    return _("difficulté %d") % difficulty_id


class Segment:
    """One pull, one key, or one whole session."""

    def __init__(self, kind, name, start_ts, index):
        self.kind = kind  # "encounter" | "keystone" | "session"
        self.name = name
        self.start_ts = start_ts
        self.end_ts = None
        self.index = index
        self.success = None
        self.difficulty_id = 0
        self.group_size = 0
        self.instance_id = 0
        self.encounter_id = 0
        self.key_level = 0
        self.affixes = []
        self.reported_duration_ms = None
        self.truncated = False
        self.abandoned = False
        # Completed, whatever the timer said; the score the game gave it.
        self.completed = False
        self.score = None
        self.fought = False
        self.analysis = None
        # A key's trash pulls, each a segment of its own ("pull") with its
        # own analysis, so a reader can open one like a boss (the owner,
        # 2026-09-29). Not in the Splitter's list: `list`, `--only` and
        # every count keep the fights they always had.
        self.pulls = []
        self.parent = None
        self.block = None
        self.number = 0
        self._open_pull = None
        self._pull_block = None

    @property
    def duration_ms(self):
        if self.end_ts is None or self.start_ts is None:
            return 0
        return max(0, self.end_ts - self.start_ts)

    @property
    def difficulty(self):
        return difficulty_name(self.difficulty_id)

    @property
    def never_fought(self):
        """An encounter the client opened and closed with no fighting in it."""
        return self.kind == "encounter" and not self.fought

    @property
    def is_wipe(self):
        """A lost fight -- not one that never took place."""
        return self.success is False and not self.never_fought

    @property
    def outcome(self):
        """The result, in French: réussite, échec, sans combat, interrompu... (see `_()`)."""
        if self.kind in ("session", "pull"):
            return ""
        if self.never_fought and not self.truncated:
            return N_("sans combat")
        if self.abandoned:
            return N_("abandonnée")
        if self.kind == "keystone" and self.completed and self.success is None:
            return N_("terminée")     # completed; no score to say whether in time
        if self.success is None:
            return N_("interrompu")
        if self.kind == "keystone":
            return N_("dans les temps") if self.success else N_("hors des temps")
        return N_("réussite") if self.success else N_("échec")

    @property
    def label(self):
        """'Allee du meurtre +14', 'Golem Mythique': the name a fight is listed under."""
        if self.kind == "pull":
            return "%s \u2014 %s" % (self.parent.label, self.name)
        pieces = [self.name]
        if self.kind == "keystone" and self.key_level:
            pieces.append("+%d" % self.key_level)
        elif self.difficulty:
            pieces.append(self.difficulty)
        return " ".join(piece for piece in pieces if piece)

    def __repr__(self):
        return "Segment(%s %r)" % (self.kind, self.label)


class Splitter:
    """Feed it every event; it opens, feeds and closes segments.

    `analysis_factory(segment)` is called when a segment opens and must
    return an object with `.feed(event)` and `.finish(segment)`. Keeping
    that injectable is what lets `diagnose` run the same segmentation
    with no analysis attached at all.
    """

    def __init__(self, analysis_factory=None):
        self.analysis_factory = analysis_factory
        self.segments = []
        self._active = []
        self._saw_marker = False
        self._fallback = None
        self._counter = 0
        self._last_ts = None

    def feed(self, event):
        """Open, feed and close whatever this event concerns."""
        subevent = event.subevent
        previous_ts = self._last_ts
        if event.ts is not None:
            self._last_ts = event.ts
        if subevent == "ENCOUNTER_START":
            # A start while an encounter is still open means its END never
            # came -- a disconnect, a crash. Left open, it would swallow
            # the rest of the file: every later boss counted twice, and a
            # pull that lasts until the log ends.
            self._abandon(("encounter",), previous_ts)
            self._open_encounter(event)
        elif subevent == "CHALLENGE_MODE_START":
            # A new key cannot start inside another one.
            self._abandon(("encounter", "keystone"), previous_ts)
            self._open_keystone(event)

        if self._active:
            fought = event.suffix_kind in FIGHT_KINDS
            for segment in self._active:
                if fought:
                    segment.fought = True
                if segment.analysis is not None:
                    segment.analysis.feed(event)
        elif not self._saw_marker:
            # Once the file is known to carry markers, the fallback is
            # thrown away by `finish` -- so analysing the corridor
            # between two pulls is work whose result nobody ever sees. A
            # raid night spends most of its lines there.
            self._feed_fallback(event)

        self._follow_pulls(event)

        if subevent == "ENCOUNTER_END":
            self._close_encounter(event)
        elif subevent == "CHALLENGE_MODE_END":
            self._close_keystone(event)

    # -- a key's trash pulls ------------------------------------------------

    def _follow_pulls(self, event):
        """Open, feed and close the pull the key's own analysis is in.

        The key's analysis already cuts it into pulls (its `blocks`); each
        new one gets a segment and an analysis of its own, fed from the
        event that opened it until the pull can no longer grow. Boss pulls
        are dropped at the end: the encounter is already a segment.
        """
        if self.analysis_factory is None or event.ts is None:
            return
        for key in self._active:
            analysis = key.analysis
            if key.kind != "keystone" or not hasattr(analysis, "blocks"):
                continue
            block = analysis._block
            pull = key._open_pull
            if pull is not None and (block is not pull.block
                                     or event.ts > block.end_ts + analysis.pull_gap_ms):
                self._close_pull(key)
                pull = None
            if pull is None and block is not None and block is not key._pull_block:
                key._pull_block = block
                pull = self._new("pull", "", block.start_ts)
                pull.parent, pull.block = key, block
                # What the key already knows and the pull would not see:
                # who owns which summon, and each player's name and label.
                pull.analysis.pet_owner.update(analysis.pet_owner)
                pull.analysis._player_names.update(analysis._player_names)
                pull.analysis._labels.update(analysis._labels)
                pull.analysis._label_owner.update(analysis._label_owner)
                pull.analysis._members.update(analysis._members)
                pull.analysis._opponents.update(analysis._opponents)
                key._open_pull = pull
                key.pulls.append(pull)
            if pull is not None:
                pull.analysis.feed(event)

    def _close_pull(self, key):
        pull, key._open_pull = key._open_pull, None
        if pull is not None:
            # The last event it was fed, as every fight ends: it was fed
            # until it could no longer grow, a pull gap after its last
            # damage, and an aura ending in that tail must fit inside it.
            last = pull.analysis.last_ts or pull.block.end_ts
            pull.end_ts = max(pull.start_ts, pull.block.end_ts, last)
            pull.analysis.finish(pull)

    def _settle_pulls(self, key):
        """Once the key is finished: keep its trash pulls, numbered as its table."""
        self._close_pull(key)
        analysis = key.analysis
        if not hasattr(analysis, "blocks"):
            return
        numbers = {id(block): position for position, block in enumerate(analysis.blocks, 1)}
        bosses = analysis.boss_names
        kept = []
        for pull in key.pulls:
            number = numbers.get(id(pull.block))
            if number is None or pull.block.has_boss(bosses):
                continue      # a crumb the table dropped, or a boss's pull
            pull.number = number
            pull.name = _("Pull %d") % number
            # The key saw what came before the pull's first damage; the
            # pull's own analysis did not. Its opener and first hits are
            # the key's, and each player keeps the spec the key read.
            own = pull.analysis.blocks
            if own:
                own[0].opening = pull.block.opening
                own[0].first_hits = pull.block.first_hits
            for guid, player in pull.analysis.players.items():
                known = analysis.players.get(guid)
                if known is not None and not player.spec_id:
                    player.spec_id = known.spec_id
            kept.append(pull)
        key.pulls = kept

    # -- opening ----------------------------------------------------------

    def _new(self, kind, name, ts):
        self._counter += 1
        segment = Segment(kind, name, ts, self._counter)
        if self.analysis_factory is not None:
            segment.analysis = self.analysis_factory(segment)
        return segment

    def _open_encounter(self, event):
        # ENCOUNTER_START,encounterID,encounterName,difficultyID,groupSize,instanceID
        fields = event.fields
        name = _text(fields, 2, _("Rencontre"))
        segment = self._new("encounter", name, event.ts)
        segment.encounter_id = as_int(fields[1] if len(fields) > 1 else 0)
        segment.difficulty_id = as_int(fields[3] if len(fields) > 3 else 0)
        segment.group_size = as_int(fields[4] if len(fields) > 4 else 0)
        segment.instance_id = as_int(fields[5] if len(fields) > 5 else 0)
        self._saw_marker = True
        self._active.append(segment)
        self.segments.append(segment)

    def _open_keystone(self, event):
        # CHALLENGE_MODE_START,zoneName,instanceID,challengeModeID,keystoneLevel,[affixes]
        fields = event.fields
        name = _text(fields, 1, _("Donjon"))
        segment = self._new("keystone", name, event.ts)
        segment.instance_id = as_int(fields[2] if len(fields) > 2 else 0)
        segment.key_level = as_int(fields[4] if len(fields) > 4 else 0)
        if len(fields) > 5 and isinstance(fields[5], list):
            segment.affixes = [as_int(value) for value in fields[5]]
        segment.difficulty_id = 8
        self._saw_marker = True
        self._active.append(segment)
        self.segments.append(segment)

    # -- closing ----------------------------------------------------------

    def _close(self, kind, event):
        for position in range(len(self._active) - 1, -1, -1):
            if self._active[position].kind == kind:
                segment = self._active.pop(position)
                segment.end_ts = event.ts
                if segment.kind == "keystone":
                    self._close_pull(segment)
                if segment.analysis is not None:
                    segment.analysis.finish(segment)
                if segment.kind == "keystone":
                    self._settle_pulls(segment)
                return segment
        return None

    def _close_encounter(self, event):
        # ENCOUNTER_END,encounterID,encounterName,difficultyID,groupSize,success[,fightTime]
        fields = event.fields
        segment = self._close("encounter", event)
        if segment is None:
            return
        if len(fields) > 5:
            segment.success = bool(as_int(fields[5], 0))
        if len(fields) > 6:
            segment.reported_duration_ms = as_int(fields[6], 0) or None

    def _close_keystone(self, event):
        # CHALLENGE_MODE_END,instanceID,success,keystoneLevel,totalTime[,...]
        fields = event.fields
        segment = self._close("keystone", event)
        if segment is None:
            return
        if len(fields) > 4 and not any(as_int(fields[i], 0) for i in (2, 3, 4)):
            # "CHALLENGE_MODE_END,2813,0,0,0,0.000000,0.000000": the client
            # writes it just before every CHALLENGE_MODE_START, key open or
            # not, and names the dungeon about to start. With a key still
            # open it is the end of a key nobody finished -- two real logs
            # restarted a dungeon that way. A key completed late writes its
            # level and its time.
            segment.abandoned = True
            return
        if len(fields) > 4:
            segment.reported_duration_ms = as_int(fields[4], 0) or None
        if len(fields) <= 2:
            return
        segment.completed = True
        if not as_int(fields[2], 0):
            segment.success = False
            return
        score = _number(fields[5]) if len(fields) > 5 else None
        segment.score = score
        level = as_int(fields[3], 0) if len(fields) > 3 else 0
        if score is not None and level:
            segment.success = score >= key_base_score(level)

    def _abandon(self, kinds, end_ts):
        """Close the open segments of these kinds: a key abandoned, a pull truncated."""
        for segment in [s for s in self._active if s.kind in kinds]:
            self._active.remove(segment)
            if segment.kind == "keystone":
                segment.abandoned = True
            else:
                segment.truncated = True
            segment.end_ts = max(segment.start_ts, end_ts or segment.start_ts)
            if segment.kind == "keystone":
                self._close_pull(segment)
            if segment.analysis is not None:
                segment.analysis.finish(segment)
            if segment.kind == "keystone":
                self._settle_pulls(segment)

    # -- the no-marker case -----------------------------------------------

    def _feed_fallback(self, event):
        """Everything outside a pull.

        Only kept when the file has no markers at all -- somebody logging
        in the open world, or a file cut mid-session. Otherwise it would
        be one huge segment of corridor trash that nobody asked about.
        """
        if self._fallback is None:
            self._fallback = self._new("session", _("Session complète"), event.ts)
        if self._fallback.analysis is not None:
            self._fallback.analysis.feed(event)
        self._fallback.end_ts = event.ts

    def finish(self):
        """Close anything left open and return the segments, in order."""
        for segment in list(self._active):
            segment.truncated = True
            if segment.end_ts is None:
                # The last event the file actually contains, not the
                # segment's own start: a log cut mid-pull is a pull of
                # the length that was recorded, not a pull of zero.
                segment.end_ts = max(segment.start_ts, self._last_ts or segment.start_ts)
            if segment.kind == "keystone":
                self._close_pull(segment)
            if segment.analysis is not None:
                segment.analysis.finish(segment)
            if segment.kind == "keystone":
                self._settle_pulls(segment)
        self._active = []
        if not self._saw_marker and self._fallback is not None:
            if self._fallback.analysis is not None:
                self._fallback.analysis.finish(self._fallback)
            self.segments.append(self._fallback)
            # Calling finish() twice must not append it twice.
            self._fallback = None
        # Number them contiguously only now: a fallback segment that was
        # opened and then discarded must not leave a hole at the front.
        self.segments.sort(key=lambda segment: (segment.start_ts, segment.index))
        for position, segment in enumerate(self.segments, start=1):
            segment.index = position
        # A key's pulls come after every fight, so no fight's number moves;
        # they only need to be told apart on the page.
        position = len(self.segments)
        for segment in self.segments:
            for pull in segment.pulls:
                position += 1
                pull.index = position
        return self.segments
