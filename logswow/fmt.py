# SPDX-License-Identifier: AGPL-3.0-or-later
"""Small formatters the report is written with, French typography included.

Kept apart from report.py so the page builder reads as layout rather
than as number formatting. Nothing here knows what a fight is.
"""

import html

from .i18n import language, plural_forms

# The narrow no-break space French puts before ; : ! ? and inside numbers.
NBSP = "\u202f"


class Style:
    """How one language writes a number: separators, units, percent, plural."""

    def __init__(self, thousands, decimal, units, percent, zero_is_singular=False):
        self.thousands = thousands
        self.decimal = decimal
        self.units = units
        self.percent = percent
        self.zero_is_singular = zero_is_singular


STYLES = {
    # 25 361 906 · 25,4 M · 46 % · 0 joueur
    "fr": Style(NBSP, ",", ((1e9, NBSP + "Md"), (1e6, NBSP + "M"), (1e3, NBSP + "k")),
                "%.0f" + NBSP + "%%", zero_is_singular=True),
    # 25,361,906 · 25.4M · 46% · 0 players
    "en": Style(",", ".", ((1e9, "B"), (1e6, "M"), (1e3, "k")), "%.0f%%"),
    # 25.361.906 · 25,4 Mio. · 46 % · 0 Spieler
    "de": Style(".", ",", ((1e9, NBSP + "Mrd."), (1e6, NBSP + "Mio."), (1e3, NBSP + "Tsd.")),
                "%.0f" + NBSP + "%%"),
    # 25.361.906 · 25,4 M · 46 % · 0 jugadores
    "es": Style(".", ",", ((1e9, NBSP + "mil" + NBSP + "M"), (1e6, NBSP + "M"),
                           (1e3, NBSP + "mil")), "%.0f" + NBSP + "%%"),
}


def style():
    """The current language's way with numbers; English for one with none."""
    return STYLES.get(language(), STYLES["en"])


def esc(value):
    """Any value as HTML text, quotes included: every name from a log goes through here."""
    return html.escape(str(value), quote=True)


def number(value):
    """25361906 -> '25 361 906', with the non-breaking space French uses; '25,361,906'."""
    return "{:,}".format(int(value)).replace(",", style().thousands)


def compact(value):
    """25361906 -> '25,4 M'. One decimal, the language's units and comma.

    The threshold carries the rounding with it: 999,999 is a thousand
    thousands once rounded to one decimal, and printing it as "1000 k"
    instead of "1 M" is the kind of small wrongness a reader notices
    before they notice anything else.
    """
    value = float(value)
    current = style()
    for limit, suffix in current.units:
        if abs(value) >= limit * 0.9995:
            text = ("%.1f" % (value / limit))
            if text.endswith(".0"):
                text = text[:-2]
            return text.replace(".", current.decimal) + suffix
    return str(int(value))


def percent(value):
    """0.456 -> '46 %', with the narrow no-break space French puts before the sign; '46%'."""
    return style().percent % (value * 100)


def decimal(value):
    """0.5 -> '0,5', or '0.5' in English: the shortest form, the reader's comma."""
    return ("%g" % value).replace(".", style().decimal)


def one_decimal(value):
    """180.64 -> '180,6', or '180.6' in English."""
    return ("%.1f" % value).replace(".", style().decimal)


def plural(count, singular, many=None):
    """A count and its noun, agreed: 1 joueur, 2 joueurs, 0 joueur; 0 players.

    `singular` is the French noun; another language takes its forms from
    its table. French keeps a zero singular, English makes it plural.
    """
    one, several = plural_forms(singular, many)
    single = abs(count) < 2 if style().zero_is_singular else abs(count) == 1
    return "%d %s" % (count, one if single else several)


def bar_row(cells, fraction):
    """A table cell whose background is a bar `fraction` of its width."""
    width = max(0.0, min(1.0, fraction)) * 100
    return '<td class="bar" style="--w:%.1f%%">%s</td>' % (width, cells)
