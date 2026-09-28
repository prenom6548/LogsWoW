# SPDX-License-Identifier: AGPL-3.0-or-later
"""Physical or magic: the share of each in what the group took and dealt.

Asked for by the owner on 2026-09-27 ("un résumé des dégâts physiques /
magiques sur le total du donjon, et par pull (subis, et pourquoi pas
infligés)", then "en pourcentage"). The school comes from each damage
line itself (see schools.py); this module only draws it.

Drawn as a 100% bar per row, the three shares written beside it, since
the colour of a segment must never be the only way to read it. Colours
are the first three slots of a categorical palette validated for colour
blindness in both themes (2026-09-27, OKLab: worst adjacent pair 9.2
light / 9.4 dark); the light green is under 3:1 on white, which is why
every share is also printed as text.
"""

from . import fmt
from .i18n import N_, _
from . import schools

SCHOOL_CSS = """
:root{--phys:#2a78d6;--mag:#eb6834;--mix:#1baf7a}
@media (prefers-color-scheme:dark){:root:not([data-theme=light]){--phys:#3987e5;
--mag:#d95926;--mix:#199e70}}
.sb{display:flex;gap:2px;height:12px;min-width:120px;background:var(--panel)}
.sb span{display:block;height:100%}
.sb span:first-child{border-radius:4px 0 0 4px}
.sb span:last-child{border-radius:0 4px 4px 0}
.sb span:only-child{border-radius:4px}
.sw{display:inline-block;width:10px;height:10px;border-radius:2px;margin:0 5px 0 12px;
vertical-align:-1px}
.sw:first-child{margin-left:0}
.k-physique{background:var(--phys)}.k-magique{background:var(--mag)}
.k-mixte{background:var(--mix)}
td.sbc{width:24%}
.schools td.n{color:var(--ink)}
"""

LABELS = {"physique": N_("Physique"), "magique": N_("Magique"), "mixte": N_("Mixte")}
SHORT = {"physique": N_("Phys."), "magique": N_("Mag."), "mixte": N_("Mixte")}


def shares(parts):
    """Whole percentages that add up to exactly 100 (largest remainder).

    Rounding each share alone gives 99 or 101 on a line of three, which
    a reader rightly takes for an error. Every key gets a value; a part
    below zero -- only a damaged line can write one, and fuzzing did --
    counts as nothing, and when nothing is left every share is 0.
    """
    parts = {key: max(0, value) for key, value in parts.items()}
    total = sum(parts.values())
    if total <= 0:
        return {key: 0 for key in parts}
    exact = {key: 100.0 * value / total for key, value in parts.items()}
    whole = {key: int(value) for key, value in exact.items()}
    missing = 100 - sum(whole.values())
    for key in sorted(exact, key=lambda k: -(exact[k] - whole[k]))[:missing]:
        whole[key] += 1
    return whole


def _cell(percent, amount):
    """'62 %', '<1 %' for a real but tiny share, a dash for none."""
    if not amount:
        return "<span class=dim>&ndash;</span>"
    return ("&lt;1%s%%" % fmt.NBSP) if percent == 0 else ("%d%s%%" % (percent, fmt.NBSP))


class SchoolsMixin:
    """The "Physique ou magique" section of a fight."""

    def _schools(self, analysis):
        taken = schools.by_kind(analysis.taken_by_school)
        done = schools.by_kind(analysis.done_by_school)
        if not (sum(taken.values()) or sum(done.values())):
            return ""
        kinds = [k for k in schools.KINDS
                 if k != "mixte" or taken.get(k) or done.get(k)
                 or any(schools.by_kind(b.taken_by_school).get(k)
                        or schools.by_kind(b.done_by_school).get(k) for b in analysis.blocks)]
        legend = "".join("<span class='sw k-%s'></span>%s" % (k, _(LABELS[k])) for k in kinds)
        heads = "".join("<th class=n>%s</th>" % _(LABELS[k]) for k in kinds)
        rows = "".join(
            "<tr><td class=name>%s</td>%s</tr>" % (title, self._school_cells(parts, kinds))
            for title, parts in ((_("Subis"), taken), (_("Infligés"), done)) if sum(parts.values()))
        detail = "".join(
            _("<p class=dim style='font-size:12.5px;margin:6px 0 0'><b>%s par école</b>%s: %s</p>")
            % (title, fmt.NBSP, _by_school(ledger))
            for title, ledger in ((_("Subis"), analysis.taken_by_school),
                                  (_("Infligés"), analysis.done_by_school)) if ledger)
        return (
            _("<h3>Physique ou magique</h3><div class='card schools'>"
              "<p style='margin:0 0 8px;font-size:12.5px'>%s</p>"
              "<table><tr><th></th><th>Répartition</th>%s</tr>%s</table>%s%s"
              "<p class=dim style='margin:10px 0 0;font-size:12px'>L'école de chaque coup est "
              "celle que le journal écrit sur la ligne. « Mixte »%s: physique et magique à la "
              "fois (Ombre-frappe, Chaos...). Comme dans le reste du rapport, un coup qu'un "
              "bouclier ennemi a mangé compte dans les dégâts infligés, et la part qu'un "
              "bouclier du groupe a mangée ne compte pas dans les dégâts subis.</p></div>")
            % (legend, heads, rows, detail, self._schools_by_pull(analysis, kinds), fmt.NBSP)
        )

    @staticmethod
    def _school_cells(parts, kinds):
        """The bar and the percentages of one row."""
        parts = {k: max(0, parts.get(k, 0)) for k in kinds}
        total = sum(parts.values())
        percent = shares(parts)
        bar = "".join(
            "<span class='k-%s' style='width:%.2f%%' title='%s %s'></span>"
            % (k, 100.0 * parts[k] / total, _(LABELS[k]), _cell(percent[k], parts[k]))
            for k in kinds if parts[k]) if total else ""
        return "<td class=sbc><div class=sb>%s</div></td>%s" % (bar, "".join(
            "<td class=n>%s</td>" % _cell(percent.get(k, 0), parts.get(k, 0)) for k in kinds))

    def _schools_by_pull(self, analysis, kinds):
        if not analysis.has_several_pulls:
            return ""
        rows = []
        for index, block in enumerate(analysis.blocks, start=1):
            label = fmt.esc(block.label(boss_names=analysis.boss_names)) or "?"
            rows.append(
                "<tr><td class=n>%d</td><td>%s</td>%s%s</tr>"
                % (index, label,
                   self._school_cells(schools.by_kind(block.taken_by_school), kinds),
                   self._school_cells(schools.by_kind(block.done_by_school), kinds)))
        heads = "".join("<th class=n>%s</th>" % _(SHORT[k]) for k in kinds)
        return (
            _("<h3 style='margin-top:18px'>Pull par pull</h3><table>"
              "<tr><th class=n>#</th><th>Ce qui a été engagé</th><th>Subis</th>%s"
              "<th>Infligés</th>%s</tr>%s</table>") % (heads, heads, "".join(rows)))


def _by_school(ledger):
    """'Ombre 34 %, Physique 30 %, Feu 12 %...' -- the six largest, the rest together."""
    percent = shares(ledger)
    ranked = sorted(ledger.items(), key=lambda item: -item[1])
    parts = ["%s %s" % (schools.name(mask), _cell(percent[mask], max(0, amount)))
             for mask, amount in ranked[:6]]
    rest = sum(max(0, amount) for _mask, amount in ranked[6:])
    if rest:
        parts.append("autres %s" % _cell(sum(percent[m] for m, _a in ranked[6:]), rest))
    return ", ".join(parts)
