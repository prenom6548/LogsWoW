# SPDX-License-Identifier: AGPL-3.0-or-later
"""The order a player cast their spells in, pull by pull, as coloured chips.

Asked for by the owner on 2026-09-27, from a screenshot of an online
site's "cast order by pull". Three things differ from it, each for a
reason this project already had:

- **No icons.** They live on the game's and Wowhead's servers, and a page
  that fetched them would break the rule that the report loads nothing.
  Each spell gets a fixed colour (from its id) and a two-letter
  abbreviation; hovering says its name and when it was cast, and a click
  opens Wowhead the way every other spell name on the page does.
- **Triggered casts are a reading, not a list.** See castorder.py for
  the measured rule. They are grouped apart and hidden by default, and
  the page says why.
- **The filter is CSS, not script.** One hidden checkbox per spell, and a
  rule per spell that hides its chips while the box is ticked
  (`.h123:checked ~ .pulls .c123`). The page stays free of any script;
  a test makes sure of it.
"""

import re

from . import fmt
from .castorder import (TRIGGER_FASTER_THAN_MS, TRIGGER_MAX_MEDIAN_GAP_MS, TRIGGER_MIN_CASTS,
                        TRIGGER_SHARE, split_by_pull)
from .timestamps import format_duration
from .wowhead import spell_url

# Short words a two-letter abbreviation skips: "Lame du Vide" -> "Lv".
_SMALL_WORDS = frozenset(
    "a au aux d de des du en et l la le les of on sur the to un une".split())

CHIP_CSS = """
.co summary{font-weight:600}
.cobody{padding:6px 0 0}
.hf{position:absolute;opacity:0;width:1px;height:1px;pointer-events:none}
.legend{margin:4px 0 12px;font-size:12.5px}
.legend .grp{margin:6px 0}
.legend .grp b{display:block;font-size:11px;text-transform:uppercase;letter-spacing:.05em;
color:var(--muted);margin:0 0 4px}
.lg{display:inline-flex;align-items:center;gap:4px;margin:2px 8px 2px 0;cursor:pointer;
white-space:nowrap}
.pull h4{margin:14px 0 6px;font-size:12px;letter-spacing:.05em;text-transform:uppercase;
color:var(--muted);display:flex;justify-content:space-between;gap:12px;font-weight:600}
.pull h4 span{font-weight:400;text-transform:none;letter-spacing:0}
.seq{line-height:0}
.k{display:inline-block;min-width:24px;height:24px;margin:1px;padding:0 3px;border-radius:4px;
color:#fff;font:600 11px/24px -apple-system,"Segoe UI",Roboto,Arial,sans-serif;text-align:center;
text-decoration:none;vertical-align:top}
.k.t{outline:2px dashed var(--warn);outline-offset:-2px}
.k.p{border-radius:12px;font-style:italic}
"""


def abbreviate(name):
    """'Frappe d'essai' -> 'Fe', 'Estropier' -> 'Es': two letters that stay put."""
    words = [word for word in re.findall(r"[^\W\d_]+", name or "")
             if word.lower() not in _SMALL_WORDS]
    if not words:
        return (name or "?")[:2] or "?"
    if len(words) == 1:
        return words[0][:2].capitalize()
    return words[0][0].upper() + words[1][0].lower()


def spell_colour(spell_id):
    """A fixed colour per spell id, dark enough for white letters on it.

    At 32% lightness the worst hue (yellow) keeps white text at 4.58:1,
    above the 4.5:1 a small label needs; at 38% it fell to about 3.4:1.
    """
    hue = int((spell_id * 0.6180339887) % 1 * 360)
    return "hsl(%d,48%%,32%%)" % hue


def chip_rules(spell_ids):
    """The CSS for every spell that appears on the page: colour and filter."""
    rules = [CHIP_CSS]
    for spell_id in sorted(spell_ids):
        rules.append(".c%d{background:%s}" % (spell_id, spell_colour(spell_id)))
        rules.append(".h%d:checked~.pulls .c%d{display:none}" % (spell_id, spell_id))
        rules.append(".h%d:checked~.legend .l%d{opacity:.4;text-decoration:line-through}"
                     % (spell_id, spell_id))
    return "\n".join(rules)


class CastOrderMixin:
    """The cast-order section of each player's panel."""

    def _cast_order(self, analysis, player):
        if not player.cast_log or not self.cast_order:
            return ""
        self._cast_panels += 1
        uid = "o%d" % self._cast_panels
        start = analysis.first_ts or 0
        spells = {}                          # id -> [name, count, pet]
        for _ts, spell_id, name, _paid, from_pet in player.cast_log:
            row = spells.setdefault(spell_id, [name, 0, from_pet])
            row[1] += 1
        self._spell_ids.update(spells)

        boxes = "".join(
            "<input type=checkbox class='hf h%d' id='%s-%d'%s>"
            % (spell_id, uid, spell_id, " checked" if spell_id in player.triggered else "")
            for spell_id in sorted(spells))
        pulls = "".join(
            self._cast_pull(position, block, casts, player, start, analysis)
            for position, (block, casts) in enumerate(
                split_by_pull(player.cast_log, analysis.blocks, analysis.pull_gap_ms), start=1))
        cut = ("<p class=dim style='font-size:12px'>Séquence coupée après %s sorts.</p>"
               % fmt.number(len(player.cast_log))) if player.cast_log_full else ""
        return (
            "<details class=co><summary>Ordre des sorts, pull par pull "
            "<span class=dim>&middot; %s</span></summary><div class=cobody>%s%s"
            "<div class=pulls>%s%s</div></div></details>"
            % (fmt.plural(len(player.cast_log), "sort"), boxes,
               self._cast_legend(uid, spells, player), pulls, cut)
        )

    def _cast_legend(self, uid, spells, player):
        """The filter: every spell of this player, in three groups."""
        groups = {"lances": [], "declenches": [], "invocations": []}
        for spell_id, (name, count, from_pet) in sorted(
                spells.items(), key=lambda item: -item[1][1]):
            key = ("invocations" if from_pet
                   else "declenches" if spell_id in player.triggered else "lances")
            groups[key].append(
                "<label for='%s-%d' class='lg l%d'>%s %s <span class=dim>x%d</span></label>"
                % (uid, spell_id, spell_id, self._chip(spell_id, name, None, key, False),
                   fmt.esc(name), count))
        titles = (
            ("lances", "Lancés"),
            ("declenches", "Probablement déclenchés automatiquement (masqués)"),
            ("invocations", "Lancés par ses invocations"),
        )
        body = "".join(
            "<div class=grp><b>%s</b>%s</div>" % (title, "".join(groups[key]))
            for key, title in titles if groups[key])
        note = ""
        if groups["declenches"]:
            note = ("<p class=dim style='font-size:12px;margin:4px 0 0'>Le journal écrit "
                    "de la même façon un sort appuyé et un sort que le jeu déclenche seul. "
                    "Sont lus comme déclenchés, parmi les sorts lancés au moins %d fois dans "
                    "ce combat sans jamais coûter de ressource%s: ceux qui, à %d%s%% au moins, "
                    "partent en même temps qu'un sort payé, avec un écart médian de %d "
                    "secondes au plus entre deux lancers%s; ceux dont l'écart médian est sous "
                    "%s%ss, plus vite qu'aucun bouton%s; et la seconde copie d'un "
                    "sort que le journal écrit deux fois, sous le "
                    "même nom, au même instant. C'est une lecture du fichier%s: cliquez pour "
                    "les afficher.</p>"
                    % (TRIGGER_MIN_CASTS, fmt.NBSP, round(TRIGGER_SHARE * 100), fmt.NBSP,
                       TRIGGER_MAX_MEDIAN_GAP_MS // 1000, fmt.NBSP,
                       ("%g" % (TRIGGER_FASTER_THAN_MS / 1000.0)).replace(".", ","),
                       fmt.NBSP, fmt.NBSP, fmt.NBSP))
        return ("<div class=legend><p class=dim style='font-size:12px;margin:0'>Cliquez sur "
                "un sort pour le masquer ou l'afficher.</p>%s%s</div>" % (body, note))

    def _cast_pull(self, position, block, casts, player, start, analysis):
        if block is None:
            if not casts:
                return ""
            title = "Entre les pulls"
            span = fmt.plural(len(casts), "sort")
        else:
            title = "Pull %02d &mdash; %s" % (position, self._pull_what(block, analysis))
            span = "%s&ndash;%s &middot; %s" % (
                format_duration(block.start_ts - start), format_duration(block.end_ts - start),
                fmt.plural(len(casts), "sort"))
        chips = "".join(
            self._chip(spell_id, name, ts - start,
                       "invocations" if from_pet
                       else "declenches" if spell_id in player.triggered else "lances",
                       True)
            for ts, spell_id, name, _paid, from_pet in casts)
        return ("<div class=pull><h4>%s <span>%s</span></h4><div class=seq>%s</div></div>"
                % (title, span, chips or "<p class=dim style='line-height:1.5;margin:0'>"
                   "Aucun sort pendant ce pull.</p>"))

    @staticmethod
    def _pull_what(block, analysis):
        """'Mchimba l'Embaumeur, échec' or 'trash (33 ennemis)'."""
        if block.has_boss(analysis.boss_names):
            outcome = block.outcome
            word = ", réussite" if outcome else (", échec" if outcome is False else "")
            return fmt.esc(block.boss_label(analysis.boss_names) or "boss") + word
        count = sum(len(guids) for guids in block.enemies.values())
        return "trash (%s)" % fmt.plural(count, "ennemi")

    def _chip(self, spell_id, name, at_ms, group, linked):
        """One coloured chip; a link to Wowhead when the page has links."""
        css = "k c%d%s" % (spell_id, {"declenches": " t", "invocations": " p"}.get(group, ""))
        title = fmt.esc(name)
        if at_ms is not None:
            title = "%s %s" % (format_duration(at_ms), title)
        text = fmt.esc(abbreviate(name))
        if linked and spell_id and self.wowhead_prefix is not None:
            return "<a class='%s' href='%s' title='%s'>%s</a>" % (
                css, fmt.esc(spell_url(spell_id, self.wowhead_prefix)), title, text)
        return "<span class='%s' title='%s'>%s</span>" % (css, title, text)
