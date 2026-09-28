# SPDX-License-Identifier: AGPL-3.0-or-later
"""Reading a combat log file as a stream of events.

Streaming matters here rather than being a style choice: a raid night
writes a file of several hundred megabytes, and the point of this
package is that it runs on the machine that has it, not on a server
farm. Nothing ever holds the whole file, or even a whole fight, in
memory -- the analysis accumulates as the lines go past.
"""

import io
import os

from .events import (
    DEFAULT_ADVANCED_WIDTH,
    SPECIAL_EVENTS,
    UNKNOWN_SUBEVENT,
    Layout,
    build_event,
    decompose,
    resolve_layout,
)
from .timestamps import TimestampReader
from .tokenize import looks_like_guid, split_line

# Big enough that the layout vote sees thousands of damage lines, small
# enough that holding it costs about a megabyte.
WARMUP_LINES = 5000


def _overkill_evidence(samples, offset, advanced_width):
    """Count the damage lines whose overkill marker lands where expected.

    A hit that killed nothing writes -1 as its overkill, and almost no hit
    kills anything, so on the *right* width nearly every damage line shows
    a -1 at suffix index 1 (no baseAmount) or 2 (with one). On a wrong
    width it shows up at neither -- which makes this a test of the width
    as well as of the field.
    """
    at_one = at_two = 0
    for fields in samples:
        if not fields or not fields[0].endswith(("_DAMAGE", "_DAMAGE_LANDED")):
            continue
        scheme = decompose(fields[0])
        if scheme is None:
            continue
        _, prefix_n, _, suffix_counts = scheme
        remainder = fields[offset + 8 :]
        _, _, suffix, note = resolve_layout(
            remainder, prefix_n, suffix_counts, advanced_width
        )
        if note or len(suffix) < 3:
            continue
        if suffix[1] == "-1":
            at_one += 1
        elif suffix[2] == "-1":
            at_two += 1
    return at_one, at_two


def _measure_hide_caster(samples, evidence):
    """Question 1 of `detect_layout`: is the addon-only field there?"""
    # 1 -- hideCaster.
    with_field = without = 0
    for fields in samples:
        if not fields or fields[0] in SPECIAL_EVENTS or len(fields) < 3:
            continue
        if looks_like_guid(fields[1]):
            without += 1
        elif looks_like_guid(fields[2]):
            with_field += 1
    hide_caster = with_field > without
    evidence["hide_caster"] = {"absent": without, "present": with_field}
    return hide_caster


def _break_width_tie(tied, samples, offset):
    """Several widths are backed equally: returns (width, how it was settled)."""
    tiebreak = ""
    # Every candidate is backed by the same events -- which is
    # what a file with a single kind of damage line looks like.
    # Ask the file a *different* question: where does the overkill
    # -1 land? A log of nothing but SPELL_DAMAGE used to answer
    # this with "the widest candidate" and read every amount off
    # the overkill field: 30 hits of 5,000 came out as -30.
    scores = {
        width: sum(_overkill_evidence(samples, offset, width))
        for width in tied
    }
    if max(scores.values()) > 0:
        tiebreak = "marqueur -1 : %s" % scores
        tied = [
            width for width in tied
            if scores[width] == max(scores.values())
        ]
    # Still undecided: the file cannot tell these apart, so the
    # width this client is known to use beats the largest number.
    if len(tied) > 1:
        tiebreak = ((tiebreak + ", ") if tiebreak else "") + (
            "puis proximite avec %d" % DEFAULT_ADVANCED_WIDTH)
    width = min(
        tied, key=lambda width: (abs(width - DEFAULT_ADVANCED_WIDTH), -width)
    )
    return width, tiebreak


def _measure_advanced_width(samples, offset, evidence):
    """Question 2 of `detect_layout`: how wide is the advanced block?"""
    # 2 -- the advanced block's width. A line only votes when it cannot
    # be read without an advanced block at all; otherwise events that
    # never carry one (SPELL_CAST_START, the aura events) would vote for
    # a width of zero and drown the ones that do.
    width_votes = {}
    width_backers = {}
    for fields in samples:
        if not fields or fields[0] in SPECIAL_EVENTS:
            continue
        scheme = decompose(fields[0])
        if scheme is None:
            continue
        _, prefix_n, _, suffix_counts = scheme
        available = len(fields) - offset - 8 - prefix_n
        if available < 0 or available in suffix_counts:
            continue
        # An unambiguous suffix (one known width) is worth more than one
        # that could be read several ways.
        weight = 3 if len(suffix_counts) == 1 else 1
        for count in suffix_counts:
            width = available - count
            if width > 0:
                width_votes[width] = width_votes.get(width, 0) + weight
                width_backers.setdefault(width, set()).add(fields[0])
    tiebreak = ""
    if width_votes:
        # The real width is the one every advanced-carrying event agrees
        # on, so the count of distinct subevents backing a width decides
        # first and the raw vote count only breaks ties. On a real 240 MB
        # log the raw counts alone were 19:3585 against 20:2985 -- true,
        # but far too close to rest a whole report on.
        ranked = sorted(
            width_votes,
            key=lambda key: (len(width_backers[key]), width_votes[key]),
            reverse=True,
        )
        best = (len(width_backers[ranked[0]]), width_votes[ranked[0]])
        tied = [
            width for width in ranked
            if (len(width_backers[width]), width_votes[width]) == best
        ]
        if len(tied) == 1:
            advanced_width = tied[0]
        else:
            advanced_width, tiebreak = _break_width_tie(tied, samples, offset)
    else:
        advanced_width = DEFAULT_ADVANCED_WIDTH
    evidence["advanced_width"] = {
        width: "%d votes / %d evenements" % (width_votes[width], len(width_backers[width]))
        for width in sorted(width_votes, key=lambda key: -len(width_backers[key]))[:5]
    }
    evidence["advanced_width_chosen"] = advanced_width
    evidence["advanced_width_tiebreak"] = tiebreak
    evidence["advanced_logging"] = bool(width_votes)
    return advanced_width


def detect_layout(samples):
    """Work out how this file lays its fields out, by counting.

    `samples` is a list of already-split field lists. Three questions get
    answered, in order, each from the file's own lines:

    1. Is the addon-only `hideCaster` field present? (It should not be.)
    2. How wide is the Advanced Combat Logging block? Documented as 17,
       measured as 19 on a 12.1.0 client.
    3. Does the damage suffix carry a baseAmount before overkill? Found
       by looking for where the -1 lives: a hit that killed nothing
       writes -1 as its overkill, and almost no hit kills anything.

    Returns a Layout carrying the answers and the evidence for each, so
    `diagnose` can show its work instead of asking to be believed.
    """
    evidence = {}

    hide_caster = _measure_hide_caster(samples, evidence)
    offset = 2 if hide_caster else 1
    advanced_width = _measure_advanced_width(samples, offset, evidence)

    # 3 -- the baseAmount field, found by where the -1 sits.
    at_one, at_two = _overkill_evidence(samples, offset, advanced_width)
    has_base_amount = at_two >= at_one
    evidence["overkill_position"] = {
        "index 1 (no baseAmount)": at_one,
        "index 2 (baseAmount)": at_two,
    }
    evidence["has_base_amount"] = has_base_amount

    return Layout(
        advanced_width=advanced_width,
        has_base_amount=has_base_amount,
        hide_caster=hide_caster,
        evidence=evidence,
    )


# The two reasons that stop a line before it is even an event. Named
# because `diagnose` breaks them out, and because counting them twice is
# exactly the bug this class used to have.
NO_SEPARATOR = "ligne sans le separateur de deux espaces"
BAD_TIMESTAMP = "horodatage illisible"
# A line whose first field is not a name: a damaged line starting with a
# bracket, found by fuzzing on 2026-09-27 -- the layout vote stopped on it.
NO_EVENT_NAME = "nom d'evenement illisible"


class ParseProblems:
    """What the reader did not understand, kept for `diagnose`.

    Counted rather than raised. One malformed line in ten million must
    not stop a report from being produced, but it must not vanish either.

    **One line is one problem.** `by_reason` is the only ledger;
    `unsplittable` and `total` are views of it. They used to be incremented
    *alongside* it, so every unsplittable line and every unreadable
    timestamp was reported twice -- the example log's two bad lines came
    out as three problems in `diagnose`, in the report's footer and in
    the "lignes incomprises" tile.
    """

    def __init__(self):
        self.by_reason = {}
        self.unknown_subevents = {}
        self.samples = []

    def note(self, reason, line_number=None, text=""):
        """Count one line the reader could not place, keeping a few as samples."""
        self.by_reason[reason] = self.by_reason.get(reason, 0) + 1
        if len(self.samples) < 25:
            self.samples.append((line_number, reason, text[:200]))

    def note_unknown(self, subevent):
        self.unknown_subevents[subevent] = self.unknown_subevents.get(subevent, 0) + 1

    @property
    def unsplittable(self):
        return self.by_reason.get(NO_SEPARATOR, 0)

    @property
    def total(self):
        """Lines not understood, each counted once."""
        return sum(self.by_reason.values())


class LogFile:
    """One combat log on disk."""

    def __init__(self, path, default_year=None):
        self.path = path
        self.default_year = default_year
        self.problems = ParseProblems()
        self.line_count = 0
        self.event_count = 0
        self.layout = Layout()
        self.first_ts = None
        self.last_ts = None
        self.size_bytes = os.path.getsize(path) if os.path.exists(path) else 0

    def _open(self):
        # errors="replace" rather than "strict": a single byte damaged by a
        # crash mid-write should cost one character, not the whole night.
        # utf-8-sig rather than utf-8: the client writes no byte order
        # mark, but a file that has been through a Windows editor can
        # carry one, and it would otherwise make line 1 unreadable.
        return io.open(self.path, "r", encoding="utf-8-sig", errors="replace",
                       newline="")

    def events(self):
        """Yield Event objects in file order.

        The first `WARMUP_LINES` lines are buffered so the layout can be
        measured before a single event is built from them; then they are
        replayed and the rest streams past.
        """
        # Reading the same file twice must give the same numbers, not
        # twice the numbers: the counters below belong to one pass.
        self.problems = ParseProblems()
        self.line_count = 0
        self.event_count = 0
        self.first_ts = None
        self.last_ts = None
        clock = TimestampReader(self.default_year)
        buffered = []
        decided = False

        with self._open() as handle:
            for line in handle:
                self.line_count += 1
                line = line.rstrip("\r\n")
                if not line.strip():
                    continue
                timestamp_text, fields = split_line(line)
                if fields is None:
                    self.problems.note(NO_SEPARATOR, line_number=self.line_count,
                                       text=line)
                    continue
                if not fields or not isinstance(fields[0], str) or not fields[0]:
                    self.problems.note(NO_EVENT_NAME, line_number=self.line_count,
                                       text=line)
                    continue
                ts = clock.read(timestamp_text)
                if ts is None:
                    self.problems.note(BAD_TIMESTAMP, line_number=self.line_count,
                                       text=timestamp_text)
                    continue
                if self.first_ts is None:
                    self.first_ts = ts
                self.last_ts = ts

                if not decided:
                    buffered.append((ts, fields, self.line_count))
                    if len(buffered) >= WARMUP_LINES:
                        decided = True
                        self.layout = detect_layout([item[1] for item in buffered])
                        for item in buffered:
                            yield self._build(*item)
                        buffered = []
                    continue

                yield self._build(ts, fields, self.line_count)

        if not decided:
            # Short file: settle the vote on whatever evidence there is.
            self.layout = detect_layout([item[1] for item in buffered])
            for item in buffered:
                yield self._build(*item)

    def _build(self, ts, fields, line_number):
        event = build_event(ts, fields, line_number, self.layout)
        self.event_count += 1
        if event.mismatch:
            if event.mismatch == UNKNOWN_SUBEVENT:
                self.problems.note_unknown(event.subevent)
            else:
                self.problems.note(event.mismatch, line_number=line_number, text=event.subevent)
        return event

    @property
    def duration_ms(self):
        if self.first_ts is None or self.last_ts is None:
            return 0
        return self.last_ts - self.first_ts
