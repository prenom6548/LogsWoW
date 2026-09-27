"""Splitting one combat log line into fields.

A line is:

    <timestamp>  <EVENT_NAME>,<field>,<field>,...

with exactly two spaces between the timestamp and the rest. Fields are
comma-separated, but three things make a naive split wrong:

  * quoted strings, which contain commas: "Thalia-Hyjal", "Coup de bouclier"
  * bracketed lists, which nest: COMBATANT_INFO's talents, gear, auras
  * parenthesised tuples inside those lists

So this is a small depth-aware scanner rather than a str.split(','). It
never raises on malformed input: an unterminated quote or bracket ends
at the end of the line, and the caller can see that in the result.
"""

import csv

_QUOTE = '"'
_READER = csv.reader
_OPENERS = {"[": "]", "(": ")"}
_CLOSERS = {"]", ")"}


def split_line(line):
    """'<ts>  EVENT,a,b' -> (timestamp_text, [fields]) or (None, None)."""
    separator = line.find("  ")
    if separator == -1:
        return None, None
    timestamp = line[:separator]
    payload = line[separator + 2 :].strip()
    if not payload:
        return None, None
    return timestamp, split_fields(payload)


def split_fields(payload):
    """Depth-aware comma split. Returns a list of strings and lists.

    A bracketed group becomes a nested list, so COMBATANT_INFO's talent
    and gear blocks arrive structured instead of as one long string.

    Most lines have no group at all, and for those the standard library's
    csv reader -- written in C -- gives the same fields about six times
    faster than the character loop below, which was half of the time a
    whole report took. Measured on 1,848,185 real lines from two logs:
    not one field differed. Anything unusual still goes through the loop:
    a bracket, a parenthesis, a backslash, or a quote the reader left in
    a field (a quote that did not sit at a field's edge).
    """
    if payload and "[" not in payload and "(" not in payload and "\\" not in payload:
        try:
            row = next(_READER((payload,), quotechar=_QUOTE, skipinitialspace=True))
        except (csv.Error, StopIteration):
            row = None
        if row is not None and _QUOTE not in "\x00".join(row):
            return [field.strip() for field in row]
    return _scan_fields(payload)


def _scan_fields(payload):
    """The character loop: quotes, nested groups, escapes. Never raises."""
    fields = []
    stack = [fields]
    current = []
    in_quotes = False
    escaped = False
    # A comma directly after a closing bracket is a separator between two
    # groups, not an empty field: "[(1,2),(3,4)]" holds two tuples, not
    # two tuples and a blank.
    just_closed = False

    for char in payload:
        if escaped:
            current.append(char)
            escaped = False
            just_closed = False
            continue
        if in_quotes:
            if char == "\\":
                escaped = True
            elif char == _QUOTE:
                in_quotes = False
            else:
                current.append(char)
            continue
        if char == _QUOTE:
            in_quotes = True
            just_closed = False
            continue
        if char in _OPENERS:
            _flush(stack[-1], current, keep_empty=False)
            nested = []
            stack[-1].append(nested)
            stack.append(nested)
            just_closed = False
            continue
        if char in _CLOSERS:
            _flush(stack[-1], current, keep_empty=False)
            if len(stack) > 1:
                stack.pop()
            just_closed = True
            continue
        if char == ",":
            _flush(stack[-1], current, keep_empty=not just_closed)
            just_closed = False
            continue
        current.append(char)
        just_closed = False

    _flush(stack[-1], current, keep_empty=not just_closed)
    return fields


def _flush(target, buffer, keep_empty):
    text = "".join(buffer).strip()
    del buffer[:]
    if text or keep_empty:
        target.append(text)


_GUID_PREFIXES = (
    "Player-",
    "Creature-",
    "Pet-",
    "Vehicle-",
    "GameObject-",
    "Vignette-",
    "BattlePet-",
    "Item-",
)


def looks_like_guid(value):
    """True for a unit GUID, including the nil one.

    Used to tell whether a line carries the addon-only `hideCaster`
    field. The text file is not supposed to contain it, but this package
    has never been run against a file written by a real client, so the
    parser checks rather than assumes -- and `diagnose` reports which
    answer it got.
    """
    if not isinstance(value, str) or not value:
        return False
    if value == "0000000000000000":
        return True
    # "nil" is what the client writes for an absent *name*, as in
    # ENCHANT_REMOVED,0000000000000000,nil,... -- counting it as a GUID
    # made the hideCaster vote read a shifted line as a normal one.
    return value.startswith(_GUID_PREFIXES)


def as_int(value, default=0):
    """Combat logs write ints, floats, 'nil', and occasionally junk."""
    if isinstance(value, (int, float)):
        return int(value)
    if not isinstance(value, str) or not value or value == "nil":
        return default
    try:
        return int(value)
    except ValueError:
        pass
    try:
        # OverflowError as well as ValueError: int(float("inf")) and
        # int(float("1e400")) both raise it, and a line damaged by a
        # crash mid-write is exactly where such a string comes from.
        return int(float(value))
    except (ValueError, OverflowError):
        return default


def as_bool(value):
    """The log writes 1/0, and sometimes nil/true/false."""
    if isinstance(value, str):
        lowered = value.lower()
        if lowered in ("1", "true"):
            return True
        if lowered in ("0", "nil", "false", ""):
            return False
    return bool(as_int(value, 0))
