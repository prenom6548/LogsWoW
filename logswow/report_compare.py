# SPDX-License-Identifier: AGPL-3.0-or-later
"""The report's two additions of 0.15.0: keys side by side, and what each player wore.

Both read `preview.py`, which the window reads too: the page and the window cannot disagree.
"""

from . import fmt
from .gear import SLOT_NAMES, slot_label
from .i18n import _
from .preview import (average_ilvl, change, change_text, comparison, ilvl_text, metric_label,
                      metric_text, role_groups)
from .specs import label_of
from .timestamps import format_duration
from .wowhead import item_url

NBSP = fmt.NBSP


class CompareMixin:
    """Methods of `ReportWriter`: the comparison card and the equipment of a group."""

    def _comparison(self):
        """The 'Comparaison des clés' card of the overview, or '' when no key finished."""
        groups = comparison(self.segments)
        if not groups:
            return ""
        blocks = []
        for group in groups:
            runs = group["runs"]
            head = "".join("<th class=n>%s</th>" % fmt.esc(_("Clé %d") % run["index"])
                           for run in runs)
            rows = [
                self._cmp_row(_("Durée"), [format_duration(r["duration"]) for r in runs],
                              change([r["duration"] for r in runs])),
                self._cmp_row(_("Issue"), [_(r["outcome"]) for r in runs], None),
                self._cmp_row(_("Morts"), [str(r["deaths"]) for r in runs], None),
            ]
            for key in ("dps", "hps", "taken"):
                rows.append(self._cmp_row(_("Groupe : ") + metric_label(key),
                                          [fmt.compact(r[key]) for r in runs],
                                          change([r[key] for r in runs])))
            table = ("<table><tr><th></th>%s%s</tr>%s</table>" % (
                head, "<th class=n>%s</th>" % fmt.esc(_("Écart")) if len(runs) > 1 else "",
                "".join(rows)))
            blocks.append("<h3>%s <span class=dim>&middot; %s</span></h3><div class=card>%s%s</div>"
                          % (fmt.esc(group["title"]), fmt.plural(len(runs), "clé"), table,
                             self._cmp_players(group)))
        return (_("<h2>Comparaison des clés</h2>") + "".join(blocks)
                + _("<p class=dim style='font-size:12.5px'>Écart%s: la dernière clé par rapport "
                    "à la première. <b>Soins/s</b> compte les boucliers (le journal ne les range "
                    "pas parmi les soins, les sites en ligne si). <b>Subis/s</b> compte ce que les "
                    "boucliers ont absorbé : c'est ce qui arrive au tank avant ses protections, "
                    "et il n'est donné qu'aux tanks. Seules des clés terminées du même niveau "
                    "sont comparées.</p>") % NBSP)

    @staticmethod
    def _cmp_row(label, cells, delta, indent=False):
        return "<tr><td%s>%s</td>%s%s</tr>" % (
            " class=dim" if indent else "", fmt.esc(label),
            "".join("<td class=n>%s</td>" % fmt.esc(cell) for cell in cells),
            ("<td class=n>%s</td>" % fmt.esc(change_text(delta))) if delta is not None
            or len(cells) > 1 else "")

    def _cmp_players(self, group):
        if not group["players"]:
            return ""
        runs = group["runs"]
        rows = []
        for player in group["players"]:
            first = True
            for key, values, delta in player["rows"]:
                name = ("<span class=name>%s</span> <span class=dim>%s</span>"
                        % (fmt.esc(player["name"]), fmt.esc(player["spec"]))) if first else ""
                first = False
                rows.append("<tr><td>%s</td><td class=dim>%s</td>%s<td class=n>%s</td></tr>" % (
                    name, fmt.esc(metric_label(key)),
                    "".join("<td class=n>%s</td>" % fmt.esc(metric_text(key, v)) for v in values),
                    fmt.esc(change_text(delta))))
        head = "".join("<th class=n>%s</th>" % fmt.esc(_("Clé %d") % run["index"]) for run in runs)
        table = ("<div style='margin-top:12px'><table><tr><th>%s</th><th></th>%s<th class=n>%s</th>"
                 "</tr>%s</table></div>")
        return table % (fmt.esc(_("Joueur")), head, fmt.esc(_("Écart")), "".join(rows))

    # -- equipment ------------------------------------------------------------

    def _group_ilvl(self, analysis):
        """'Niveau d'objet moyen du groupe : 320,8' as a paragraph, or ''."""
        players = [p for _role, group in role_groups(analysis) for p in group]
        value = average_ilvl(players)
        if value is None:
            return ""
        known = [p.gear.average for p in players if p.gear is not None]
        return (_("<p style='margin:10px 0 0;font-size:12.5px'>Niveau d'objet moyen du groupe%s: "
                  "<b>%s</b> (de %s à %s).</p>")
                % (NBSP, ilvl_text(value), ilvl_text(min(known)), ilvl_text(max(known))))

    def _equipment(self, analysis):
        """One folded table per player: each slot's item (a Wowhead link), level, enchants, gems."""
        blocks = []
        for _role, players in role_groups(analysis):
            for player in players:
                gear = player.gear
                if gear is None:
                    continue
                rows = []
                for index, item in gear.worn():
                    link = _("objet %d") % item.item_id
                    if self.wowhead_prefix is not None:
                        link = "<a href='%s'>%s</a>" % (
                            fmt.esc(item_url(item.item_id, self.wowhead_prefix)), fmt.esc(link))
                    rows.append(
                        "<tr><td class=dim>%s</td><td>%s</td><td class=n>%d</td><td>%s</td>"
                        "<td class=n>%s</td></tr>" % (
                            fmt.esc(slot_label(index)), link, item.ilvl,
                            fmt.esc(", ".join(str(e) for e in item.enchants)) or "-",
                            len(item.gems) or "-"))
                empty = [_(SLOT_NAMES[i]) for i in gear.empty_slots()]
                blocks.append(
                    "<details><summary><span class=name>%s</span> <span class=dim>%s</span> "
                    "&middot; ilvl <b>%s</b></summary><div class=body><table>"
                    "<tr><th>%s</th><th>%s</th><th class=n>%s</th><th>%s</th><th class=n>%s</th>"
                    "</tr>%s</table>%s</div></details>" % (
                        fmt.esc(player.short_name), fmt.esc(label_of(player.spec_id) or "?"),
                        ilvl_text(gear.average), fmt.esc(_("Emplacement")), fmt.esc(_("Objet")),
                        fmt.esc(_("Niveau")), fmt.esc(_("Enchantements")), fmt.esc(_("Gemmes")),
                        "".join(rows),
                        (_("<p class=dim style='margin:6px 0 0'>Emplacement vide%s: %s.</p>")
                         % (NBSP, fmt.esc(", ".join(empty)))) if empty else ""))
        if not blocks:
            return ""
        return ("<details class=more><summary>%s</summary>%s"
                "<p class=dim style='margin:10px 0 0;font-size:12px'>%s</p></details>" % (
                    fmt.esc(_("Équipement")), "".join(blocks),
                    _("Le journal donne le numéro et le niveau de chaque objet, jamais son nom ni "
                      "son icône : ils viennent de la base d'objets du jeu, que ce rapport n'a pas "
                      "(il ne se connecte à rien). Le lien ouvre Wowhead si vous cliquez dessus. "
                      "Le niveau moyen suit la formule du jeu : seize emplacements, chemise et "
                      "tabard exclus, une arme à deux mains comptée deux fois, un emplacement vide "
                      "pour zéro.")))
