"""Combat log timestamps -> milliseconds.

The client has written several shapes over the years, and a log can be
read on a machine in a different timezone than the one that wrote it, so
this module never trusts a single layout:

    9/18/2026 20:15:31.123-4        month/day/year, 3-digit ms, tz hours
    9/18/2026 20:15:31.1230000-7    same, 7-digit fraction
    9/18 20:15:31.123               no year (older clients)
    2026-09-18T20:15:31.123-04:00   ISO, in case a tool rewrote the file

Only *relative* time matters for every number this package reports (a
fight's duration, DPS, the gap between two casts), so the absolute epoch
is a convenience, not a dependency. When the year is missing we anchor
to a caller-supplied year and roll the day forward when the clock goes
backwards, which is what a raid crossing midnight looks like.
"""

import re
from datetime import datetime, timedelta, timezone

_PATTERNS = (
    # 9/18/2026 20:15:31.1230000-7  (tz may be -7, +2, -04:00, or absent)
    re.compile(
        r"^(?P<month>\d{1,2})/(?P<day>\d{1,2})/(?P<year>\d{2,4})\s+"
        r"(?P<hour>\d{1,2}):(?P<minute>\d{2}):(?P<second>\d{2})\.(?P<frac>\d+)"
        r"(?P<tz>[+-]\d{1,2}(?::?\d{2})?)?$"
    ),
    # 9/18 20:15:31.123
    re.compile(
        r"^(?P<month>\d{1,2})/(?P<day>\d{1,2})\s+"
        r"(?P<hour>\d{1,2}):(?P<minute>\d{2}):(?P<second>\d{2})\.(?P<frac>\d+)"
        r"(?P<tz>[+-]\d{1,2}(?::?\d{2})?)?$"
    ),
    # 2026-09-18T20:15:31.123-04:00
    re.compile(
        r"^(?P<year>\d{4})-(?P<month>\d{2})-(?P<day>\d{2})[T ]"
        r"(?P<hour>\d{1,2}):(?P<minute>\d{2}):(?P<second>\d{2})\.(?P<frac>\d+)"
        r"(?P<tz>Z|[+-]\d{1,2}(?::?\d{2})?)?$"
    ),
)


def _fraction_to_ms(frac: str) -> int:
    """'123' -> 123, '1230000' -> 123, '1' -> 100. Never raises."""
    frac = (frac + "000")[:3]
    return int(frac)


def _tz_to_offset(tz):
    """'-7' / '+02' / '-04:00' / 'Z' / None -> timedelta or None."""
    if not tz:
        return None
    if tz == "Z":
        return timedelta(0)
    sign = -1 if tz[0] == "-" else 1
    body = tz[1:].replace(":", "")
    if len(body) <= 2:
        hours, minutes = int(body), 0
    else:
        hours, minutes = int(body[:-2]), int(body[-2:])
    return sign * timedelta(hours=hours, minutes=minutes)


class TimestampReader:
    """Stateful reader, because a year-less timestamp needs the previous one.

    Feed it timestamps in file order. `default_year` is only consulted for
    the shapes that carry no year at all.
    """

    def __init__(self, default_year=None):
        self.default_year = default_year or datetime.now().year
        self._last_ms = None
        self._day_rollovers = 0
        self.unparsed = 0

    def read(self, text):
        """Return milliseconds, or None when the shape is not recognised."""
        text = text.strip()
        for pattern in _PATTERNS:
            match = pattern.match(text)
            if match:
                return self._build(match)
        self.unparsed += 1
        return None

    def _build(self, match):
        parts = match.groupdict()
        year = parts.get("year")
        if year is None:
            year = self.default_year
        else:
            year = int(year)
            if year < 100:  # two-digit year, seen in some old files
                year += 2000
        offset = _tz_to_offset(parts.get("tz"))
        moment = datetime(
            year,
            int(parts["month"]),
            int(parts["day"]),
            int(parts["hour"]),
            int(parts["minute"]),
            int(parts["second"]),
            _fraction_to_ms(parts["frac"]) * 1000,
            tzinfo=timezone(offset) if offset is not None else timezone.utc,
        )
        moment = moment + timedelta(days=self._day_rollovers)
        milliseconds = int(moment.timestamp() * 1000)
        # A raid that crosses midnight, in a file whose timestamps carry no
        # year: the clock jumps backwards by nearly a day. Anything smaller
        # than that is an out-of-order line, which happens, and must not
        # shift every timestamp after it.
        if self._last_ms is not None and milliseconds < self._last_ms - 20 * 3600 * 1000:
            self._day_rollovers += 1
            milliseconds += 86400 * 1000
        if self._last_ms is None or milliseconds > self._last_ms:
            self._last_ms = milliseconds
        return milliseconds


def format_duration(milliseconds):
    """1234567 -> '20:34'. Used in the report, so it stays human-sized."""
    if milliseconds is None:
        return "?"
    total_seconds = max(0, int(round(milliseconds / 1000)))
    minutes, seconds = divmod(total_seconds, 60)
    hours, minutes = divmod(minutes, 60)
    if hours:
        return "%d:%02d:%02d" % (hours, minutes, seconds)
    return "%d:%02d" % (minutes, seconds)
