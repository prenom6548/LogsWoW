# SPDX-License-Identifier: AGPL-3.0-or-later
"""The language the interface speaks.

French is the reference: every text is written in French in the code,
and `_()` returns it unchanged. Another language is one module,
`lang_<code>.py`, holding a table from each French text to its
translation; `_()` looks the text up there. A text the table lacks comes
out in French, and a test fails the build before that can ship.

The language is chosen once, before anything is read: `--langue` on the
command line, or the machine's own (the way Wowhead links already were),
with English for any language that has no table. Everything the package
prints goes through here, and nothing that is *data* does: spell, boss
and player names come from the log, in the language of the game client
that wrote it.

A lookup is one dictionary access per text drawn, not per log line, so
it costs nothing a stopwatch can see (measured on a real raid night).
"""

import importlib
import os

from .wowhead import normalise, system_language

# The languages with a table, French first because it needs none.
LANGUAGES = ("fr", "en")
# What a machine speaking anything else gets.
FALLBACK = "en"

_current = "fr"
_texts = {}
_plurals = {}
_specs = {}


def choose(choice="auto"):
    """'auto', 'fr', 'en', 'fr_FR.UTF-8'... -> a language this package speaks.

    'auto' is LOGSWOW_LANGUE when set -- a reader's standing choice, and
    what the tests use to stay in French on any machine -- and otherwise
    the machine's own language.
    """
    if choice in (None, "", "auto"):
        language = normalise(os.environ.get("LOGSWOW_LANGUE", "")) or system_language()
    else:
        language = normalise(choice)
    return language if language in LANGUAGES else FALLBACK


def set_language(choice="auto"):
    """Speak `choice` from now on; returns the language actually chosen."""
    global _current, _texts, _plurals, _specs
    language = choose(choice)
    if language == "fr":
        texts, plurals, specs = {}, {}, {}
    else:
        table = importlib.import_module(".lang_%s" % language, __package__)
        texts, plurals, specs = table.TEXTS, table.PLURALS, table.SPECS
    _current, _texts, _plurals, _specs = language, texts, plurals, specs
    return language


def language():
    """The language texts come out in now: 'fr' or 'en'."""
    return _current


def _(text):
    """A French text of the interface, in the current language."""
    return _texts.get(text, text)


def N_(text):
    """Marks a French text defined at import time, translated where it is shown.

    `_()` there would run before the language is chosen. The mark is what
    lets the test on translations find the text.
    """
    return text


def plural_forms(singular, many=None):
    """(one, several) for a French noun, in the current language."""
    if _current == "fr":
        return singular, many or singular + "s"
    return _plurals.get(singular, (singular, many or singular + "s"))


def spec_names(spec_id, french):
    """(class, specialization) of a spec id in the current language."""
    return _specs.get(spec_id, french)


# The name this package gives a melee swing, which carries no spell.
MELEE = N_("Attaque")


def spell_label(name):
    """A spell name from the log, or the melee's own label when it is ours."""
    return _(MELEE) if not name or name == MELEE else name
