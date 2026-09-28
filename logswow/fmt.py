# SPDX-License-Identifier: AGPL-3.0-or-later
"""Small formatters the report is written with, French typography included.

Kept apart from report.py so the page builder reads as layout rather
than as number formatting. Nothing here knows what a fight is.
"""

import html

from .i18n import language, plural_forms

_UNITS = ((1e9, " Md"), (1e6, " M"), (1e3, " k"))
_UNITS_EN = ((1e9, "B"), (1e6, "M"), (1e3, "k"))


def esc(value):
    """Any value as HTML text, quotes included: every name from a log goes through here."""
    return html.escape(str(value), quote=True)


def number(value):
    """25361906 -> '25 361 906', with the non-breaking space French uses; '25,361,906'."""
    if language() != "fr":
        return "{:,}".format(int(value))
    return "{:,}".format(int(value)).replace(",", " ")


def compact(value):
    """25361906 -> '25.4 M'. One decimal, French units.

    The threshold carries the rounding with it: 999,999 is a thousand
    thousands once rounded to one decimal, and printing it as "1000 k"
    instead of "1 M" is the kind of small wrongness a reader notices
    before they notice anything else.
    """
    value = float(value)
    units = _UNITS if language() == "fr" else _UNITS_EN
    for limit, suffix in units:
        if abs(value) >= limit * 0.9995:
            return ("%.1f%s" % (value / limit, suffix)).replace(".0", "")
    return str(int(value))


def percent(value):
    """0.456 -> '46 %', with the narrow no-break space French puts before the sign; '46%'."""
    if language() != "fr":
        return "%.0f%%" % (value * 100)
    return "%.0f %%" % (value * 100)


def decimal(value):
    """0.5 -> '0,5', or '0.5' in English: the shortest form, the reader's comma."""
    text = "%g" % value
    return text.replace(".", ",") if language() == "fr" else text


# The narrow no-break space French puts before ; : ! ? and inside numbers.
NBSP = "\u202f"


def plural(count, singular, many=None):
    """A count and its noun, agreed: 1 joueur, 2 joueurs, 0 joueur; 0 players.

    `singular` is the French noun; another language takes its forms from
    its table. French keeps a zero singular, English makes it plural.
    """
    one, several = plural_forms(singular, many)
    single = abs(count) < 2 if language() == "fr" else abs(count) == 1
    return "%d %s" % (count, one if single else several)


def bar_row(cells, fraction):
    """A table cell whose background is a bar `fraction` of its width."""
    width = max(0.0, min(1.0, fraction)) * 100
    return '<td class="bar" style="--w:%.1f%%">%s</td>' % (width, cells)
