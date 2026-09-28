# SPDX-License-Identifier: AGPL-3.0-or-later
"""One self-contained HTML file, written next to the log it describes.

No CDN, no web font, no script fetched from anywhere: the whole report
is one file that opens from a USB stick on a machine with no network.
That is the point of the exercise, so it is a hard rule rather than a
preference -- if this file ever needs a URL to render, something has
gone wrong.

The interface is in French because the person it is written for reads
French; the code and its comments stay in English.
"""

import os
from datetime import datetime

from . import __version__
from . import fmt
from .fmt import NBSP
from .fmt import bar_row as _bar_row
from .specs import label_of
from .timestamps import format_duration
from .report_casts import CastOrderMixin, chip_rules
from .report_panels import PanelsMixin
from .report_layouts import LayoutsMixin, write_atomic
from .report_schools import SCHOOL_CSS, SchoolsMixin
from .report_timeline import TimelineMixin
from .wowhead import resolve

CSS = """
:root{--bg:#f6f5f2;--panel:#fff;--ink:#1a1a1a;--muted:#5d5d5d;--line:#dcd9d2;
--accent:#7a5c2e;--bar:#b99354;--bad:#9c3b2e;--good:#39683f;--warn:#8a6d1f}
@media (prefers-color-scheme:dark){:root:not([data-theme=light]){--bg:#15161a;
--panel:#1d1f24;--ink:#e9e7e2;--muted:#a09c94;--line:#31343c;--accent:#d8b678;
--bar:#8a6d3c;--bad:#d4796a;--good:#7fb487;--warn:#d8b678}}
*{box-sizing:border-box}
body{margin:0;background:var(--bg);color:var(--ink);
font:15px/1.55 -apple-system,BlinkMacSystemFont,"Segoe UI",Roboto,Helvetica,Arial,sans-serif}
.wrap{max-width:1080px;margin:0 auto;padding:28px 16px 80px}
h1{font-size:25px;margin:0 0 4px;letter-spacing:-.01em}
h2{font-size:19px;margin:34px 0 10px;padding-bottom:6px;border-bottom:1px solid var(--line)}
h3{font-size:15px;margin:20px 0 8px;color:var(--muted);text-transform:uppercase;
letter-spacing:.06em;font-weight:600}
a{color:var(--accent)}
.sub{color:var(--muted);font-size:13.5px;margin:0 0 18px}
.card{background:var(--panel);border:1px solid var(--line);border-radius:10px;
padding:16px 18px;margin:14px 0}
.note{background:var(--panel);border-left:3px solid var(--accent);border-radius:0 8px 8px 0;
padding:12px 16px;margin:16px 0;font-size:13.5px;color:var(--muted)}
table{width:100%;border-collapse:collapse;font-size:13.5px}
th{text-align:left;color:var(--muted);font-weight:600;font-size:11.5px;
text-transform:uppercase;letter-spacing:.05em;padding:6px 8px;border-bottom:1px solid var(--line)}
td{padding:6px 8px;border-bottom:1px solid var(--line);vertical-align:middle}
tr:last-child td{border-bottom:none}
td.n,th.n{text-align:right;font-variant-numeric:tabular-nums;white-space:nowrap}
.bar{position:relative;background:linear-gradient(90deg,var(--bar) var(--w),transparent var(--w));
border-radius:3px;padding-left:6px}
.name{font-weight:600}
.dim{color:var(--muted)}
details{margin:8px 0}
summary{cursor:pointer;padding:8px 10px;background:var(--panel);border:1px solid var(--line);
border-radius:8px;font-weight:600;font-size:14px}
summary:hover{border-color:var(--accent)}
details.more{margin:4px 0 0}
details.more>summary{font-weight:400;font-size:12.5px;padding:4px 8px;background:none;
border:1px dashed var(--line);color:var(--muted)}
details[open] summary{border-radius:8px 8px 0 0;border-bottom:none}
.body{border:1px solid var(--line);border-top:none;border-radius:0 0 8px 8px;
padding:4px 16px 16px;background:var(--panel)}
.pill{display:inline-block;font-size:11.5px;padding:2px 8px;border-radius:99px;
border:1px solid var(--line);color:var(--muted);margin-left:6px;vertical-align:1px}
.ok{color:var(--good);border-color:var(--good)}
.ko{color:var(--bad);border-color:var(--bad)}
.grid{display:grid;grid-template-columns:repeat(auto-fit,minmax(150px,1fr));gap:10px;margin:12px 0}
.grid.tiles{grid-template-columns:repeat(auto-fit,minmax(104px,1fr))}
.grid.tiles .stat b{font-size:17px}
.grid.tiles .stat span{font-size:10.5px}
.stat{background:var(--panel);border:1px solid var(--line);border-radius:8px;padding:10px 12px}
.stat b{display:block;font-size:19px;font-variant-numeric:tabular-nums;letter-spacing:-.02em}
.stat span{font-size:11.5px;color:var(--muted);text-transform:uppercase;letter-spacing:.05em}
.chain{font-size:12.5px;margin:6px 0 0;padding:0;list-style:none}
.chain li{padding:2px 0;border-bottom:1px dotted var(--line)}
.chain .hit{color:var(--bad)}
.chain .heal{color:var(--good)}
svg{display:block;width:100%;height:auto}
.cols{display:grid;grid-template-columns:1fr 1fr;gap:20px}
@media(max-width:720px){.cols{grid-template-columns:1fr}.wrap{padding:18px 12px 60px}}
footer{margin-top:44px;padding-top:14px;border-top:1px solid var(--line);
color:var(--muted);font-size:12.5px}
"""


# Below this share of the damage dealt, unattributable damage is a stray
# tick rather than a missing pet, and the note about it would be noise.
ORPHAN_NOTE_SHARE = 0.005


def _boss_pill(outcome):
    """The badge of a pull holding a boss, coloured by what happened.

    It used to be green whatever the outcome, and green is what a kill
    looks like everywhere else on the page: on a real key, the wipe and
    the kill on the same boss wore the same badge.
    """
    if outcome:
        return "<span class='pill ok'>boss &middot; reussite</span>"
    if outcome is False:
        return "<span class='pill ko'>boss &middot; echec</span>"
    return "<span class='pill'>boss</span>"


def _council_note(names):
    if not names:
        return ""
    return (" %s%s: aucune unite ne porte le nom de la rencontre (un conseil, "
            "par exemple), donc tous les degats infliges pendant sa duree sont "
            "comptes sur le boss." % (", ".join(fmt.esc(name) for name in names), NBSP))


class ReportWriter(TimelineMixin, PanelsMixin, CastOrderMixin, SchoolsMixin, LayoutsMixin):
    """Writes the whole page for a list of segments."""

    def __init__(self, log, segments, out_path, wowhead="auto", cast_order=True,
                 layout="longue"):
        self.log = log
        # "longue", "onglets" or "pages" (report_layouts.py). For "pages",
        # out_path is a folder and `write` returns its index.html.
        self.layout = layout
        self.segments = segments
        self.out_path = out_path
        # None disables spell links entirely; "" is English, "fr" French...
        self.wowhead_prefix = resolve(wowhead)
        # Filled while the page is built: every spell a cast-order chip
        # shows, whose colour and filter rule the <head> then carries.
        self._spell_ids = set()
        self._cast_panels = 0
        # The cast order about doubles a page (8.4 MB instead of 4.3 for a
        # real raid night); --sans-sequence leaves it out.
        self.cast_order = cast_order

    def write(self):
        """Assemble the report and put it in place; returns the file to open."""
        if self.layout == "onglets":
            return self._write_tabbed()
        if self.layout == "pages":
            return self._write_pages()
        body = [self._overview()]
        for segment in self.segments:
            head, parts = self._segment(segment)
            body.append(head + "".join(parts.values()))
        body.append(self._footer())
        # The head comes last: it carries one CSS rule per spell that a
        # cast-order chip shows, and those are known only now. Written
        # beside the target and moved into place in one step: a full disk
        # or an interrupt halfway leaves the previous report whole.
        write_atomic(self.out_path, self._head() + "".join(body))
        return self.out_path

    # -- page ------------------------------------------------------------

    def _head(self, extra_css="", wrap_class="wrap"):
        # `class=wrap` stays unquoted: the long page is the same bytes as before.
        wrap = "class=wrap" if wrap_class == "wrap" else "class='%s'" % wrap_class
        return (
            "<!doctype html><html lang=fr><head><meta charset=utf-8>"
            '<meta name=viewport content="width=device-width,initial-scale=1">'
            "<title>LogsWoW — %s</title><style>%s%s%s</style></head><body><div %s>"
            % (fmt.esc(os.path.basename(self.log.path)), CSS + SCHOOL_CSS,
               chip_rules(self._spell_ids) if self._spell_ids else "", extra_css, wrap)
        )

    def _overview(self, link=None):
        rows = []
        for segment in self.segments:
            analysis = segment.analysis
            outcome = segment.outcome
            css = "ok" if segment.success else ("ko" if segment.is_wipe else "")
            name = (link(segment) if link is not None else
                    "<a href='#s%d' class=name>%s</a>" % (segment.index, fmt.esc(segment.label)))
            rows.append(
                "<tr><td>%s%s</td>"
                "<td class=n>%s</td><td class=n>%s</td><td class=n>%s</td>"
                "<td class=n>%s</td><td class=n>%s</td><td class=n>%d</td></tr>"
                % (
                    name,
                    "<span class='pill %s'>%s</span>" % (css, fmt.esc(outcome)) if outcome else "",
                    format_duration(analysis.duration_ms),
                    fmt.compact(analysis.total_damage),
                    fmt.compact(analysis.total_healing),
                    len(analysis.blocks) if analysis.has_several_pulls else "1",
                    len(analysis.participants()),
                    len(analysis.deaths),
                )
            )
        if not rows:
            rows.append(
                "<tr><td colspan=7 class=dim>Aucun combat delimite dans ce fichier.</td></tr>"
            )

        generated = datetime.now().strftime("%d/%m/%Y %H:%M")
        return (
            "<h1>Rapport de combat</h1>"
            "<p class=sub>%s &middot; %s lignes, %s evenements &middot; genere le %s "
            "par LogsWoW %s</p>"
            "<div class=note><b>Tout est reste sur cette machine.</b> Ce rapport a ete "
            "produit en lisant le fichier de journal directement&nbsp;: aucun envoi, "
            "aucun compte, aucune connexion. La page est autonome, elle s'ouvre hors ligne.</div>"
            "<div class=grid>%s</div>"
            "<h2>Combats</h2><div class=card><table>"
            "<tr><th>Combat</th><th class=n>Duree</th><th class=n>Degats</th>"
            "<th class=n>Soins</th><th class=n>Pulls</th><th class=n>Joueurs</th>"
            "<th class=n>Morts</th></tr>"
            "%s</table></div>"
            % (
                fmt.esc(os.path.basename(self.log.path)),
                fmt.number(self.log.line_count),
                fmt.number(self.log.event_count),
                generated,
                __version__,
                self._stats(),
                "".join(rows),
            )
        )

    def _boss_pulls(self):
        """{start: (success, fought)} of every boss encounter the chosen fights hold.

        Counted from each fight's own encounter windows, not from which
        fights were ticked: a key chosen alone showed "0 pulls de boss"
        with three bosses killed inside it. Keyed by the encounter's start,
        so a boss chosen together with its key counts once.
        """
        pulls = {}
        for segment in self.segments:
            for _label, start, _end, success, fought in segment.analysis.encounters:
                pulls.setdefault(start, (success, fought))
        return pulls

    def _stats(self):
        pulls = self._boss_pulls()
        keys = [segment for segment in self.segments if segment.kind == "keystone"]
        # Two counters, not one "Echecs": a depleted key and a boss wipe
        # inside it are two different failures, and a single sum read as
        # the same dungeon counted twice.
        late = sum(1 for segment in keys if segment.success is False)
        wipes = sum(1 for success, fought in pulls.values() if success is False and fought)
        cells = [
            ("Taille du fichier", "%s Mo" % round(self.log.size_bytes / 1048576.0, 1)),
            ("Duree couverte", format_duration(self.log.duration_ms)),
            ("Pulls de boss", str(len(pulls))),
            ("Wipes de boss", str(wipes)),
            ("Cles mythiques", str(len(keys))),
            ("Cles hors des temps", str(late)),
            ("Lignes incomprises", fmt.number(self.log.problems.total)),
        ]
        return "".join(
            "<div class=stat><b>%s</b><span>%s</span></div>" % (fmt.esc(value), fmt.esc(label))
            for label, value in cells
        )

    # -- one pull ---------------------------------------------------------

    def _segment(self, segment):
        analysis = segment.analysis
        seconds = max(1.0, analysis.duration_ms / 1000.0)
        outcome = segment.outcome
        css = "ok" if segment.success else ("ko" if segment.is_wipe else "")
        head = (
            "<h2 id='s%d'>%s%s</h2><p class=sub>%s &middot; %s &middot; "
            "%s de degats, %s de soins &middot; %s%s</p>"
            % (
                segment.index,
                fmt.esc(segment.label),
                "<span class='pill %s'>%s</span>" % (css, fmt.esc(outcome)) if outcome else "",
                format_duration(analysis.duration_ms),
                fmt.plural(len(analysis.participants()), "joueur"),
                fmt.compact(analysis.total_damage),
                fmt.compact(analysis.total_healing),
                fmt.plural(len(analysis.deaths), "mort"),
                " &middot; journal interrompu" if segment.truncated else "",
            )
        )
        return head, self._sections(analysis, seconds)

    def _sections(self, analysis, seconds):
        """{part: html} of one fight, rendered in the order the long page shows them."""
        parts = {}
        parts["orphans"] = self._orphans(analysis)
        parts["composition"] = self._composition(analysis)
        parts["timeline"] = self._timeline(analysis)
        parts["pulls"] = self._pulls(analysis)
        parts["schools"] = self._schools(analysis)
        parts["rankings"] = "<div class=cols>%s%s</div>" % (
            self._ranking(analysis, "damage_done", "Degats infliges", "DPS"),
            self._ranking(analysis, "healing_done", "Soins effectifs", "HPS"))
        parts["taken"] = self._taken(analysis)
        parts["enemy_casts"] = self._enemy_casts(analysis)
        parts["deaths"] = self._deaths(analysis)
        parts["players"] = self._players(analysis, seconds)
        parts["enemies"] = self._enemies(analysis, seconds)
        return parts

    def _orphans(self, analysis):
        """Damage the file gives to nobody, when there is enough to matter.

        A pet summoned before the pull began, on lines whose advanced
        block carries no ownerGUID, cannot be routed to its owner -- nor
        can a friendly NPC that belongs to no player at all. Their damage
        is in no player's row and in no total. That is the honest choice;
        saying nothing about it is not, because the group's total would
        be quietly short.
        """
        dropped = analysis.orphan_damage
        if not dropped:
            return ""
        whole = analysis.total_damage + dropped
        if whole and dropped / whole < ORPHAN_NOTE_SHARE:
            return ""
        ranked = sorted(analysis.orphan_sources.items(), key=lambda item: -item[1])
        names = ", ".join("%s (%s)" % (fmt.esc(name), fmt.compact(value))
                          for name, value in ranked[:4])
        return (
            "<div class=note><b>%s de degats ne sont comptes pour personne.</b> "
            "Ils viennent d'unites alliees qui n'appartiennent a aucun joueur "
            "nomme par le journal%s: %s. Faute de savoir a qui les attribuer, "
            "ils ne sont ni dans le total ci-dessus ni dans la ligne d'un "
            "joueur.</div>"
            % (fmt.compact(dropped), NBSP, names)
        )

    def _pulls(self, analysis):
        """The pulls inside a run. Only worth showing when there are several."""
        if not analysis.has_several_pulls:
            return ""
        start = analysis.first_ts or 0
        bosses = analysis.boss_names
        any_boss = any(block.has_boss(bosses) for block in analysis.blocks)
        rows = []
        peak = max(block.damage_done for block in analysis.blocks) or 1
        for index, block in enumerate(analysis.blocks, start=1):
            label = fmt.esc(block.label(boss_names=bosses)) or "<span class=dim>?</span>"
            if block.has_boss(bosses):
                label = _boss_pill(block.outcome) + " " + label
            boss_cells = ""
            if any_boss:
                # Trash is often funnelled onto a boss and killed there:
                # the two are counted apart so a boss pull is not judged
                # by the trash that came with it, or the reverse.
                if block.damage_boss:
                    boss_cells = "<td class=n>%s</td><td class=n>%s</td>" % (
                        fmt.compact(block.damage_boss), fmt.compact(block.damage_trash))
                else:
                    boss_cells = ("<td class=n><span class=dim>-</span></td>"
                                  "<td class=n>%s</td>" % fmt.compact(block.damage_trash))
            rows.append(
                "<tr><td class=n>%d</td><td class=n>%s</td><td class=n>%s</td>"
                "%s<td class=n>%s</td>%s<td class=n>%s</td><td class=n>%s</td></tr>"
                % (
                    index,
                    format_duration(block.start_ts - start),
                    format_duration(block.duration_ms),
                    _bar_row(label, block.damage_done / peak),
                    fmt.compact(block.damage_done),
                    boss_cells,
                    fmt.compact(block.damage_taken),
                    ("<span class=dim>0</span>" if not block.deaths else str(block.deaths)),
                )
            )
        boss_heads = ("<th class=n>sur le boss</th><th class=n>sur les trash</th>"
                      if any_boss else "")
        return (
            "<h3>%s</h3><div class=card><table>"
            "<tr><th class=n>#</th><th class=n>Debut</th><th class=n>Duree</th>"
            "<th>Ce qui a ete engage</th><th class=n>Degats</th>%s"
            "<th class=n>Subis</th><th class=n>Morts</th></tr>%s</table>"
            "<p class=dim style='margin:10px 0 0;font-size:12px'>Un pull se termine "
            "quand le groupe passe plus de %s sans infliger ni subir de degats. "
            "Un groupe qui enchaîne les packs sans pause les verra donc regroupes%s: "
            "<code>--pull-gap</code> change ce seuil, sauf a l'interieur d'une "
            "rencontre de boss, qui reste toujours un seul pull.%s%s</p></div>"
            % (
                fmt.plural(len(analysis.blocks), "pull"),
                boss_heads,
                "".join(rows),
                "%d%ss" % (analysis.pull_gap_ms / 1000, NBSP),
                NBSP,
                (" %s ecarte%s, trop petits pour compter (moins d'un millième "
                 "des degats de la course)."
                 % (analysis.dropped_pulls,
                    "s" if analysis.dropped_pulls > 1 else ""))
                if analysis.dropped_pulls else "",
                _council_note(analysis.window_encounters),
            )
        )

    def _ranking(self, analysis, key, title, rate_label):
        # Everyone, not the first twenty: a real heroic encounter had 21
        # players, and the twenty-first vanished from the table unannounced.
        rows = analysis.ranked_players(key)
        if not rows:
            return ""
        # A shield that ate a hit never becomes healing in the file, so it
        # is shown beside it rather than inside it. Warcraft Logs adds the
        # two together, which is why a discipline priest reads so
        # differently there; the note under the table says so.
        healing = key == "healing_done"
        absorbs = healing and any(player.absorb_done for player, _v, _r in rows)
        peak = rows[0][1]
        lines = []
        for player, value, rate in rows:
            extra = ""
            if healing and player.overheal_rate:
                extra = (" <span class=dim>(%s de surguerison)</span>"
                         % fmt.percent(player.overheal_rate))
            cells = [
                _bar_row(
                    "<span class=name>%s</span>%s" % (fmt.esc(player.short_name), extra),
                    value / peak if peak else 0,
                ),
                "<td class=n>%s</td>" % fmt.compact(value),
            ]
            if absorbs:
                cells.append("<td class=n>%s</td>" % (
                    fmt.compact(player.absorb_done) if player.absorb_done
                    else "<span class=dim>-</span>"))
                cells.append("<td class=n>%s</td>"
                             % fmt.compact(value + player.absorb_done))
            cells.append("<td class=n>%s</td>" % fmt.compact(rate))
            lines.append("<tr>%s</tr>" % "".join(cells))
        heads = "<th>Joueur</th><th class=n>Total</th>"
        if absorbs:
            heads += "<th class=n>Absorbe</th><th class=n>Somme</th>"
        heads += "<th class=n>%s</th>" % fmt.esc(rate_label)
        note = ""
        if absorbs:
            note = ("<p class=dim style='margin:10px 0 0;font-size:12px'>"
                    "Un bouclier n'est pas un soin dans le journal%s: il "
                    "empeche des degats au lieu d'en rendre. Les deux sont "
                    "donc comptes a part, et additionnes dans la colonne "
                    "<b>Somme</b> — c'est ce total-la que les sites en ligne "
                    "appellent \u00ab soins \u00bb.</p>" % NBSP)
        moved = sum(player.moved_health for player, _v, _r in rows) if healing else 0
        if moved:
            note += ("<p class=dim style='margin:6px 0 0;font-size:12px'>"
                     "Le Lien d'esprit ne soigne pas%s: il prend de la sante aux "
                     "joueurs les plus hauts pour la donner aux plus bas. Les %s "
                     "qu'il a pris sont deduits des soins de son poseur, comme sur "
                     "Warcraft Logs, et ne comptent dans les degats subis de "
                     "personne.</p>" % (NBSP, fmt.compact(moved)))
        return (
            "<div><h3>%s</h3><div class=card><table>"
            "<tr>%s</tr>%s</table>%s</div></div>"
            % (fmt.esc(title), heads, "".join(lines), note)
        )

    def _taken(self, analysis):
        # Abilities that dealt nothing (a link, a shield that ate it all)
        # are real events but noise in a table about what hurt.
        hurting = [
            ability
            for ability in analysis.top_abilities(analysis.enemy_damage_by_ability, None)
            if ability.total > 0
        ]
        abilities, rest = hurting[:14], hurting[14:]
        if not abilities:
            return ""
        peak = abilities[0].total
        lines = []
        for ability in abilities:
            lines.append(
                "<tr>%s<td class=n>%s</td><td class=n>%d</td><td class=n>%d</td></tr>"
                % (
                    _bar_row(fmt.esc(ability.name), ability.total / peak if peak else 0),
                    fmt.compact(ability.total),
                    ability.hits,
                    len(ability.targets),
                )
            )
        return (
            "<h3>Ce qui a fait mal au groupe</h3><div class=card><table>"
            "<tr><th>Capacite</th><th class=n>Degats</th><th class=n>Coups</th>"
            "<th class=n>Joueurs touches</th></tr>%s</table>%s"
            "<p class=dim style='margin:10px 0 0;font-size:12px'>Le fichier dit qui a ete "
            "touche et combien. Il ne dit pas si le coup etait evitable&nbsp;: cela demande "
            "de connaitre le boss, ce que cet outil ne pretend pas savoir.</p></div>"
            % ("".join(lines), (
                "<p class=dim style='margin:8px 0 0;font-size:12.5px'>Et %s de plus, "
                "%s de degats en tout.</p>"
                % (fmt.plural(len(rest), "capacite"), fmt.compact(sum(a.total for a in rest))))
               if rest else "")
        )

    def _deaths(self, analysis):
        if not analysis.deaths:
            return ""
        blocks = []
        start = analysis.first_ts or 0
        # Every death: a raid wipe is twenty of them at once, and the list
        # used to stop at twenty-four without saying so.
        for death in analysis.deaths:
            chain = []
            for moment in death["chain"]:
                ts, source, spell, delta, fraction = moment[:5]
                overkill = moment[5] if len(moment) > 5 else 0
                css = "hit" if delta <= 0 else "heal"
                hp = (" → %s" % fmt.percent(fraction)) if fraction is not None else ""
                # The log marks the hit that killed with a positive
                # overkill; every other hit writes -1. An instant kill
                # carries no amount at all (see `_feed_instakill`).
                mark = " <b>coup fatal</b>" if overkill > 0 else ""
                chain.append(
                    "<li><span class=dim>%s</span> <span class=%s>%s%s</span> "
                    "%s <span class=dim>%s</span>%s%s</li>"
                    % (
                        format_duration(ts - start),
                        css,
                        "+" if delta > 0 else "",
                        fmt.number(abs(delta)) if delta else "mort instantanee",
                        fmt.esc(spell or "Attaque"),
                        fmt.esc(source or ""),
                        hp,
                        mark,
                    )
                )
            blocks.append(
                "<details><summary>%s &middot; %s <span class=dim>%s</span></summary>"
                "<div class=body><ul class=chain>%s</ul></div></details>"
                % (
                    fmt.esc(death["player"]),
                    format_duration(death["ts"] - start),
                    fmt.esc(death["killing_blow"] or "cause non ecrite dans le journal"),
                    "".join(chain) or "<li class=dim>Rien avant la mort dans le journal.</li>",
                )
            )
        return "<h3>%s</h3>%s" % (fmt.plural(len(analysis.deaths), "mort"), "".join(blocks))

    # -- the group ---------------------------------------------------------

    def _composition(self, analysis):
        groups = analysis.composition()
        if not groups:
            return ""
        rows = []
        for label, players in groups:
            names = ", ".join(
                "<span class=name>%s</span> <span class=dim>%s</span>"
                % (fmt.esc(player.short_name), fmt.esc(label_of(player.spec_id) or "?"))
                for player in players
            )
            rows.append(
                "<tr><td class=dim style='white-space:nowrap'>%s</td><td>%s</td></tr>"
                % (fmt.esc(label), names)
            )
        return (
            "<h3>Composition du groupe</h3><div class=card><table>%s</table>%s"
            "<p class=dim style='margin:10px 0 0;font-size:12px'>Le role vient de la "
            "specialisation que le client ecrit au debut du combat. Une specialisation "
            "que cet outil ne connait pas est affichee par son numero.</p></div>"
            % ("".join(rows), self._bystanders(analysis))
        )

    @staticmethod
    def _bystanders(analysis):
        """Players the file shows only casting, named so nothing is silently dropped."""
        present = analysis.bystanders()
        if not present:
            return ""
        return (
            "<p style='margin:10px 0 0;font-size:12.5px'>Aussi presents dans le journal, "
            "sans prendre part au combat (ni degats, ni soins, ni coups recus)%s: %s.</p>"
            % (NBSP, ", ".join(
                "<span class=name>%s</span> <span class=dim>(%s)</span>"
                % (fmt.esc(player.short_name), fmt.plural(player.casts, "sort"))
                for player in present))
        )

    # -- the enemies -------------------------------------------------------

    def _footer(self):
        problems = self.log.problems
        unknown = ", ".join(sorted(problems.unknown_subevents)) or "aucun"
        return (
            "<footer>LogsWoW %s &middot; lecture locale de <code>%s</code><br>"
            "Disposition detectee dans ce fichier&nbsp;: bloc avance de %d champs, "
            "champ de degats bruts %s, champ hideCaster %s. "
            "Lignes non comprises&nbsp;: %s. Evenements inconnus&nbsp;: %s.<br>"
            "Licence AGPL-3.0 ou ulterieure&nbsp;; code source&nbsp;: "
            "github.com/prenom6548/LogsWoW. Aucune donnee ne quitte cette machine."
            "</footer></div></body></html>"
            % (
                __version__,
                fmt.esc(os.path.basename(self.log.path)),
                self.log.layout.advanced_width,
                "present" if self.log.layout.has_base_amount else "absent",
                "present" if self.log.layout.hide_caster else "absent",
                fmt.number(problems.total),
                fmt.esc(unknown),
            )
        )
