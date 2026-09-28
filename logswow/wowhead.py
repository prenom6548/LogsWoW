# SPDX-License-Identifier: AGPL-3.0-or-later
"""Spell links, in the reader's own language.

The report stays a single file that loads nothing: a link is followed
only if someone clicks it, which is their choice and not the page
reaching out on its own.

**The prefixes below were measured, not looked up.** Each was requested
once against a real spell id: `fr`, `de`, `es`, `it`, `pt`, `ru`, `ko`
and `cn` answer 200, no prefix answers 200 for English, and `zh` and
`ja` answer 404. So Chinese maps to `cn`, and a language the site does
not serve falls back to English rather than producing a dead link.
"""

import locale
import os

BASE = "https://www.wowhead.com"

# Language -> the path segment the site serves it under. English has none.
PREFIXES = {
    "en": "",
    "fr": "fr",
    "de": "de",
    "es": "es",
    "it": "it",
    "pt": "pt",
    "ru": "ru",
    "ko": "ko",
    "zh": "cn",
}


def normalise(tag):
    """'fr_FR.UTF-8', 'pt-BR', 'zh_TW' -> 'fr', 'pt', 'zh'."""
    if not tag:
        return ""
    tag = str(tag).strip().replace("-", "_")
    for separator in (".", "@"):
        tag = tag.split(separator, 1)[0]
    return tag.split("_", 1)[0].lower()


def system_language():
    """The machine's language, from the environment then from locale.

    Checked in the order the C library does, so a session that overrides
    LC_ALL for one command still gets the right answer.
    """
    for name in ("LC_ALL", "LC_MESSAGES", "LANG", "LANGUAGE"):
        value = os.environ.get(name)
        if value:
            language = normalise(value.split(":", 1)[0])
            if language and language != "c":
                return language
    language = normalise(_platform_language())
    return "" if language in ("c", "posix") else language


def _platform_language():
    """The machine's language when no environment variable says it.

    `locale.getdefaultlocale()` answered this until Python 3.15 removes
    it; on Windows, where the variables above are usually unset, the
    links would then have fallen back to English without a word. Windows
    is asked directly for its interface language instead, and every other
    system for the locale Python itself started with.
    """
    if os.name == "nt":
        try:
            import ctypes

            code = ctypes.windll.kernel32.GetUserDefaultUILanguage()
            return locale.windows_locale.get(code, "")
        except (AttributeError, OSError, ValueError):
            return ""
    try:
        return locale.getlocale()[0] or ""
    except (TypeError, ValueError):
        return ""


def resolve(choice=None):
    """A language tag -> the prefix to use. 'auto' reads the machine."""
    if choice in ("off", "none"):
        return None
    language = normalise(choice) if choice and choice != "auto" else system_language()
    return PREFIXES.get(language, "")


def spell_url(spell_id, prefix=""):
    """https://www.wowhead.com/fr/spell=1239608"""
    if not spell_id:
        return ""
    if prefix:
        return "%s/%s/spell=%d" % (BASE, prefix, spell_id)
    return "%s/spell=%d" % (BASE, spell_id)
