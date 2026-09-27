"""Small formatters the report is written with, French typography included.

Kept apart from report.py so the page builder reads as layout rather
than as number formatting. Nothing here knows what a fight is.
"""

import html


def esc(value):
    """Any value as HTML text, quotes included: every name from a log goes through here."""
    return html.escape(str(value), quote=True)


def number(value):
    """25361906 -> '25 361 906', with the non-breaking space French uses."""
    return "{:,}".format(int(value)).replace(",", " ")


def compact(value):
    """25361906 -> '25.4 M'. One decimal, French units.

    The threshold carries the rounding with it: 999,999 is a thousand
    thousands once rounded to one decimal, and printing it as "1000 k"
    instead of "1 M" is the kind of small wrongness a reader notices
    before they notice anything else.
    """
    value = float(value)
    for limit, suffix in ((1e9, " Md"), (1e6, " M"), (1e3, " k")):
        if abs(value) >= limit * 0.9995:
            return ("%.1f%s" % (value / limit, suffix)).replace(".0", "")
    return str(int(value))


def percent(value):
    """0.456 -> '46 %', with the narrow no-break space French puts before the sign."""
    return "%.0f %%" % (value * 100)


# The narrow no-break space French puts before ; : ! ? and inside numbers.
NBSP = "\u202f"


def plural(count, singular, many=None):
    """French agreement: 1 joueur, 2 joueurs, 0 joueur."""
    word = singular if abs(count) < 2 else (many or singular + "s")
    return "%d %s" % (count, word)


def bar_row(cells, fraction):
    """A table cell whose background is a bar `fraction` of its width."""
    width = max(0.0, min(1.0, fraction)) * 100
    return '<td class="bar" style="--w:%.1f%%">%s</td>' % (width, cells)
