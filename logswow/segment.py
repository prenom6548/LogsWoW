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

from .tokenize import as_int

# Lines that mean somebody fought: a hit, or a swing that missed. An
# encounter with none of them was never fought -- a real raid opened on
# one that lasted 8 ms, 18 lines and not one of these, and it was counted
# as a wipe. The shortest real encounter in two logs had 7,867.
FIGHT_KINDS = frozenset({"_DAMAGE", "_DAMAGE_LANDED", "_MISSED", "_SHIELD", "_SPLIT"})

# Difficulty ids, as the client writes them. Anything unlisted is shown
# by number rather than guessed at.
DIFFICULTY_NAMES = {
    1: "Normal",
    2: "Heroique",
    3: "10 joueurs",
    4: "25 joueurs",
    5: "10 heroique",
    6: "25 heroique",
    7: "Raid Recherche",
    8: "Mythique+",
    9: "40 joueurs",
    11: "Heroique scenario",
    12: "Normal scenario",
    14: "Normal",
    15: "Heroique",
    16: "Mythique",
    17: "Raid Recherche",
    23: "Mythique",
    24: "Marche du temps",
    33: "Marche du temps",
    151: "Raid Recherche",
    167: "Torghast",
}


def difficulty_name(difficulty_id):
    if not difficulty_id:
        return ""
    return DIFFICULTY_NAMES.get(difficulty_id, "difficulte %d" % difficulty_id)


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
        self.fought = False
        self.analysis = None

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
        if self.kind == "session":
            return ""
        if self.never_fought and not self.truncated:
            return "sans combat"
        if self.success is None:
            return "interrompu"
        if self.kind == "keystone":
            return "dans les temps" if self.success else "hors des temps"
        return "reussite" if self.success else "echec"

    @property
    def label(self):
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

        if subevent == "ENCOUNTER_END":
            self._close_encounter(event)
        elif subevent == "CHALLENGE_MODE_END":
            self._close_keystone(event)

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
        name = fields[2] if len(fields) > 2 else "Rencontre"
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
        name = fields[1] if len(fields) > 1 else "Donjon"
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
                if segment.analysis is not None:
                    segment.analysis.finish(segment)
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
        if len(fields) > 2:
            segment.success = bool(as_int(fields[2], 0))
        if len(fields) > 4:
            segment.reported_duration_ms = as_int(fields[4], 0) or None

    def _abandon(self, kinds, end_ts):
        """Close, as truncated, the open segments of these kinds."""
        for segment in [s for s in self._active if s.kind in kinds]:
            self._active.remove(segment)
            segment.truncated = True
            segment.end_ts = max(segment.start_ts, end_ts or segment.start_ts)
            if segment.analysis is not None:
                segment.analysis.finish(segment)

    # -- the no-marker case -----------------------------------------------

    def _feed_fallback(self, event):
        """Everything outside a pull.

        Only kept when the file has no markers at all -- somebody logging
        in the open world, or a file cut mid-session. Otherwise it would
        be one huge segment of corridor trash that nobody asked about.
        """
        if self._fallback is None:
            self._fallback = self._new("session", "Session complete", event.ts)
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
            if segment.analysis is not None:
                segment.analysis.finish(segment)
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
        return self.segments
