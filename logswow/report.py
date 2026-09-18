"""One self-contained HTML file, written next to the log it describes.

No CDN, no web font, no script fetched from anywhere: the whole report
is one file that opens from a USB stick on a machine with no network.
That is the point of the exercise, so it is a hard rule rather than a
preference -- if this file ever needs a URL to render, something has
gone wrong.

The interface is in French because the person it is written for reads
French; the code and its comments stay in English.
"""

import html
import os
from datetime import datetime

from . import __version__
from .timestamps import format_duration

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
details[open] summary{border-radius:8px 8px 0 0;border-bottom:none}
.body{border:1px solid var(--line);border-top:none;border-radius:0 0 8px 8px;
padding:4px 16px 16px;background:var(--panel)}
.pill{display:inline-block;font-size:11.5px;padding:2px 8px;border-radius:99px;
border:1px solid var(--line);color:var(--muted);margin-left:6px;vertical-align:1px}
.ok{color:var(--good);border-color:var(--good)}
.ko{color:var(--bad);border-color:var(--bad)}
.grid{display:grid;grid-template-columns:repeat(auto-fit,minmax(150px,1fr));gap:10px;margin:12px 0}
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


def esc(value):
    return html.escape(str(value), quote=True)


def number(value):
    """25361906 -> '25 361 906', with the non-breaking space French uses."""
    return "{:,}".format(int(value)).replace(",", " ")


def compact(value):
    value = float(value)
    for limit, suffix in ((1e9, " Md"), (1e6, " M"), (1e3, " k")):
        if abs(value) >= limit:
            return ("%.1f%s" % (value / limit, suffix)).replace(".0", "")
    return str(int(value))


def percent(value):
    return "%.0f %%" % (value * 100)


# The narrow no-break space French puts before ; : ! ? and inside numbers.
NBSP = "\u202f"


def plural(count, singular, many=None):
    """French agreement: 1 joueur, 2 joueurs, 0 joueur."""
    word = singular if abs(count) < 2 else (many or singular + "s")
    return "%d %s" % (count, word)


def _bar_row(cells, fraction):
    width = max(0.0, min(1.0, fraction)) * 100
    return '<td class="bar" style="--w:%.1f%%">%s</td>' % (width, cells)


class ReportWriter:
    def __init__(self, log, segments, out_path):
        self.log = log
        self.segments = segments
        self.out_path = out_path

    def write(self):
        parts = [self._head(), self._overview()]
        for segment in self.segments:
            parts.append(self._segment(segment))
        parts.append(self._footer())
        with open(self.out_path, "w", encoding="utf-8") as handle:
            handle.write("".join(parts))
        return self.out_path

    # -- page ------------------------------------------------------------

    def _head(self):
        return (
            "<!doctype html><html lang=fr><head><meta charset=utf-8>"
            '<meta name=viewport content="width=device-width,initial-scale=1">'
            "<title>LogsWoW — %s</title><style>%s</style></head><body><div class=wrap>"
            % (esc(os.path.basename(self.log.path)), CSS)
        )

    def _overview(self):
        layout = self.log.layout
        rows = []
        for segment in self.segments:
            analysis = segment.analysis
            outcome = segment.outcome
            css = "ok" if segment.success else ("ko" if segment.success is False else "")
            rows.append(
                "<tr><td><a href='#s%d' class=name>%s</a>%s</td>"
                "<td class=n>%s</td><td class=n>%s</td><td class=n>%s</td>"
                "<td class=n>%s</td><td class=n>%s</td><td class=n>%d</td></tr>"
                % (
                    segment.index,
                    esc(segment.label),
                    "<span class='pill %s'>%s</span>" % (css, esc(outcome)) if outcome else "",
                    format_duration(analysis.duration_ms),
                    compact(analysis.total_damage),
                    compact(analysis.total_healing),
                    len(analysis.blocks) if analysis.has_several_pulls else "1",
                    len(analysis.players),
                    len(analysis.deaths),
                )
            )
        if not rows:
            rows.append(
                "<tr><td colspan=8 class=dim>Aucun combat delimite dans ce fichier.</td></tr>"
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
                esc(os.path.basename(self.log.path)),
                number(self.log.line_count),
                number(self.log.event_count),
                generated,
                __version__,
                self._stats(layout),
                "".join(rows),
            )
        )

    def _stats(self, layout):
        pulls = sum(1 for segment in self.segments if segment.kind == "encounter")
        keys = sum(1 for segment in self.segments if segment.kind == "keystone")
        wipes = sum(1 for segment in self.segments if segment.success is False)
        cells = [
            ("Taille du fichier", "%s Mo" % round(self.log.size_bytes / 1048576.0, 1)),
            ("Duree couverte", format_duration(self.log.duration_ms)),
            ("Pulls de boss", str(pulls)),
            ("Cles mythiques", str(keys)),
            ("Echecs", str(wipes)),
            ("Lignes incomprises", number(self.log.problems.total)),
        ]
        return "".join(
            "<div class=stat><b>%s</b><span>%s</span></div>" % (esc(value), esc(label))
            for label, value in cells
        )

    # -- one pull ---------------------------------------------------------

    def _segment(self, segment):
        analysis = segment.analysis
        seconds = max(1.0, analysis.duration_ms / 1000.0)
        outcome = segment.outcome
        css = "ok" if segment.success else ("ko" if segment.success is False else "")
        head = (
            "<h2 id='s%d'>%s%s</h2><p class=sub>%s &middot; %s &middot; "
            "%s de degats, %s de soins &middot; %s%s</p>"
            % (
                segment.index,
                esc(segment.label),
                "<span class='pill %s'>%s</span>" % (css, esc(outcome)) if outcome else "",
                format_duration(analysis.duration_ms),
                plural(len(analysis.players), "joueur"),
                compact(analysis.total_damage),
                compact(analysis.total_healing),
                plural(len(analysis.deaths), "mort"),
                " &middot; journal interrompu" if segment.truncated else "",
            )
        )
        body = [
            head,
            self._timeline(analysis),
            self._pulls(analysis),
            "<div class=cols>",
            self._ranking(analysis, "damage_done", "Degats infliges", "DPS", seconds),
            self._ranking(analysis, "healing_done", "Soins effectifs", "HPS", seconds),
            "</div>",
            self._taken(analysis),
            self._deaths(analysis),
            self._players(analysis, seconds),
        ]
        return "".join(body)

    def _timeline(self, analysis):
        """Damage taken per interval, with a real scale on both sides.

        Left axis: how much the group took in one interval. Right axis:
        the main target's health, so the two can be read against each
        other -- a spike of damage taken against a flat health bar is a
        different story from one during a burn phase.
        """
        series, bucket_ms = analysis.timeline_series()
        if len(series) < 3:
            return ""

        width, height = 1060, 190
        left, right = 62, 1016          # the plot area, leaving room for both axes
        top, bottom = 14, 158
        plot_width = right - left
        plot_height = bottom - top
        peak = max(max(row[1] for row in series), 1)
        step = plot_width / float(len(series))

        pieces = []

        # -- left axis: four gridlines and their values -------------------
        for fraction in (0.0, 0.25, 0.5, 0.75, 1.0):
            y = bottom - fraction * plot_height
            pieces.append(
                "<line x1='%d' y1='%.1f' x2='%d' y2='%.1f' stroke='var(--line)' "
                "stroke-width='1' />" % (left, y, right, y)
            )
            pieces.append(
                "<text x='%d' y='%.1f' font-size='11' fill='var(--muted)' "
                "text-anchor='end'>%s</text>" % (left - 8, y + 3.5, compact(peak * fraction))
            )

        # -- right axis: the main target's health -------------------------
        if len(analysis.boss_hp) > 3:
            for fraction in (0.0, 0.5, 1.0):
                y = bottom - fraction * plot_height
                pieces.append(
                    "<text x='%d' y='%.1f' font-size='11' fill='var(--accent)' "
                    "text-anchor='start'>%s</text>"
                    % (right + 8, y + 3.5, percent(fraction))
                )

        # -- the bars, and a marker per death -----------------------------
        for index, (_seconds, taken, _healing, deaths) in enumerate(series):
            x = left + index * step
            if taken:
                bar_height = max(1.0, taken / peak * plot_height)
                pieces.append(
                    "<rect x='%.2f' y='%.2f' width='%.2f' height='%.2f' fill='var(--bar)' />"
                    % (x, bottom - bar_height, max(1.0, step - 0.5), bar_height)
                )
            if deaths:
                pieces.append(
                    "<rect x='%.2f' y='%d' width='%.2f' height='%d' fill='var(--bad)' "
                    "opacity='.55' />" % (x, top, max(1.5, step), plot_height)
                )

        # -- the main target's health curve -------------------------------
        if len(analysis.boss_hp) > 3 and analysis.first_ts is not None:
            span = max(1, (analysis.last_ts or 0) - analysis.first_ts)
            points = " ".join(
                "%.1f,%.1f"
                % (
                    left + (ts - analysis.first_ts) / span * plot_width,
                    bottom - fraction * plot_height,
                )
                for ts, fraction in analysis.boss_hp
            )
            pieces.append(
                "<polyline points='%s' fill='none' stroke='var(--accent)' "
                "stroke-width='1.8' opacity='.95' />" % points
            )

        # -- the time axis -------------------------------------------------
        pieces.append(
            "<line x1='%d' y1='%d' x2='%d' y2='%d' stroke='var(--line)' />"
            % (left, bottom, right, bottom)
        )
        for index in range(0, len(series), max(1, len(series) // 8)):
            pieces.append(
                "<text x='%.1f' y='%d' font-size='11' fill='var(--muted)'>%s</text>"
                % (left + index * step, bottom + 18,
                   format_duration(series[index][0] * 1000))
            )

        target = ""
        if analysis.boss_name and len(analysis.boss_hp) > 3:
            # Deliberately precise: on one real encounter the boss itself
            # never had its health written to the file, and the curve is
            # an add's. Naming it beats implying it is always the boss.
            target = (" Courbe et echelle de droite%s: vie de <b>%s</b>, la cible la plus "
                      "frappee parmi celles dont le journal donne les points de vie."
                      % (NBSP, esc(analysis.boss_name)))
        return (
            "<h3>Degats subis par le groupe, seconde par seconde</h3>"
            "<div class=card><svg viewBox='0 0 %d %d' role=img "
            "aria-label='Degats subis au fil du combat'>%s</svg>"
            "<p class=dim style='margin:6px 0 0;font-size:12px'>Barres et echelle de "
            "gauche%s: degats subis par intervalle de %s. Traits rouges%s: morts.%s</p></div>"
            % (width, height, "".join(pieces), NBSP,
               "%.0f%ss" % (bucket_ms / 1000.0, NBSP), NBSP, target)
        )

    def _pulls(self, analysis):
        """The pulls inside a run. Only worth showing when there are several."""
        if not analysis.has_several_pulls:
            return ""
        start = analysis.first_ts or 0
        rows = []
        peak = max(block.damage_done for block in analysis.blocks) or 1
        for index, block in enumerate(analysis.blocks, start=1):
            rows.append(
                "<tr><td class=n>%d</td><td class=n>%s</td><td class=n>%s</td>"
                "%s<td class=n>%s</td><td class=n>%s</td><td class=n>%s</td></tr>"
                % (
                    index,
                    format_duration(block.start_ts - start),
                    format_duration(block.duration_ms),
                    _bar_row(esc(block.label()) or "<span class=dim>?</span>",
                             block.damage_done / peak),
                    compact(block.damage_done),
                    compact(block.damage_taken),
                    ("<span class=dim>0</span>" if not block.deaths else str(block.deaths)),
                )
            )
        return (
            "<h3>%s</h3><div class=card><table>"
            "<tr><th class=n>#</th><th class=n>Debut</th><th class=n>Duree</th>"
            "<th>Ce qui a ete engage</th><th class=n>Degats</th>"
            "<th class=n>Subis</th><th class=n>Morts</th></tr>%s</table>"
            "<p class=dim style='margin:10px 0 0;font-size:12px'>Un pull se termine "
            "quand le groupe passe plus de %s sans infliger ni subir de degats. "
            "Un groupe qui encha%sne les packs sans pause les verra donc regroupes%s: "
            "<code>--pull-gap</code> change ce seuil.%s</p></div>"
            % (
                plural(len(analysis.blocks), "pull"),
                "".join(rows),
                "%d%ss" % (analysis.pull_gap_ms / 1000, NBSP),
                "î",
                NBSP,
                (" %s ecarte%s, trop petits pour compter (moins d'un milli%sme "
                 "des degats de la course)."
                 % (analysis.dropped_pulls,
                    "s" if analysis.dropped_pulls > 1 else "",
                    "è"))
                if analysis.dropped_pulls else "",
            )
        )


    def _ranking(self, analysis, key, title, rate_label, seconds):
        rows = analysis.ranked_players(key)
        if not rows:
            return ""
        peak = rows[0][1]
        lines = []
        for player, value, rate in rows[:20]:
            extra = ""
            if key == "healing_done" and player.overheal_rate:
                extra = " <span class=dim>(%s perdu)</span>" % percent(player.overheal_rate)
            lines.append(
                "<tr>%s<td class=n>%s</td><td class=n>%s</td></tr>"
                % (
                    _bar_row(
                        "<span class=name>%s</span>%s" % (esc(player.short_name), extra),
                        value / peak if peak else 0,
                    ),
                    compact(value),
                    compact(rate),
                )
            )
        return (
            "<div><h3>%s</h3><div class=card><table>"
            "<tr><th>Joueur</th><th class=n>Total</th><th class=n>%s</th></tr>%s"
            "</table></div></div>" % (esc(title), esc(rate_label), "".join(lines))
        )

    def _taken(self, analysis):
        # Abilities that dealt nothing (a link, a shield that ate it all)
        # are real events but noise in a table about what hurt.
        abilities = [
            ability
            for ability in analysis.top_abilities(analysis.enemy_damage_by_ability, 18)
            if ability.total > 0
        ][:14]
        if not abilities:
            return ""
        peak = abilities[0].total
        lines = []
        for ability in abilities:
            lines.append(
                "<tr>%s<td class=n>%s</td><td class=n>%d</td><td class=n>%d</td></tr>"
                % (
                    _bar_row(esc(ability.name), ability.total / peak if peak else 0),
                    compact(ability.total),
                    ability.hits,
                    len(ability.targets),
                )
            )
        return (
            "<h3>Ce qui a fait mal au groupe</h3><div class=card><table>"
            "<tr><th>Capacite</th><th class=n>Degats</th><th class=n>Coups</th>"
            "<th class=n>Joueurs touches</th></tr>%s</table>"
            "<p class=dim style='margin:10px 0 0;font-size:12px'>Le fichier dit qui a ete "
            "touche et combien. Il ne dit pas si le coup etait evitable&nbsp;: cela demande "
            "de connaitre le boss, ce que cet outil ne pretend pas savoir.</p></div>"
            % "".join(lines)
        )

    def _deaths(self, analysis):
        if not analysis.deaths:
            return ""
        blocks = []
        start = analysis.first_ts or 0
        for death in analysis.deaths[:24]:
            chain = []
            for moment in death["chain"]:
                ts, source, spell, delta, fraction = moment[:5]
                overkill = moment[5] if len(moment) > 5 else 0
                css = "hit" if delta < 0 else "heal"
                hp = (" → %s" % percent(fraction)) if fraction is not None else ""
                # The log marks the hit that killed with a positive
                # overkill; every other hit writes -1.
                mark = " <b>coup fatal</b>" if overkill > 0 else ""
                chain.append(
                    "<li><span class=dim>%s</span> <span class=%s>%s%s</span> "
                    "%s <span class=dim>%s</span>%s%s</li>"
                    % (
                        format_duration(ts - start),
                        css,
                        "+" if delta > 0 else "",
                        number(abs(delta)),
                        esc(spell or "Attaque"),
                        esc(source or ""),
                        hp,
                        mark,
                    )
                )
            blocks.append(
                "<details><summary>%s &middot; %s <span class=dim>%s</span></summary>"
                "<div class=body><ul class=chain>%s</ul></div></details>"
                % (
                    esc(death["player"]),
                    format_duration(death["ts"] - start),
                    esc(death["killing_blow"]),
                    "".join(chain) or "<li class=dim>Rien avant la mort dans le journal.</li>",
                )
            )
        return "<h3>%s</h3>%s" % (plural(len(analysis.deaths), "mort"), "".join(blocks))

    def _players(self, analysis, seconds):
        rows = sorted(
            analysis.players.values(),
            key=lambda player: player.damage_done + player.healing_done,
            reverse=True,
        )
        blocks = []
        for player in rows[:30]:
            if not (player.damage_done or player.healing_done or player.casts):
                continue
            uptimes = analysis.player_uptimes(player.guid)
            duration = max(1, analysis.duration_ms)
            gaps = "".join(
                "<li><span class=dim>%s</span> sans lancer de sort, a %s</li>"
                % (format_duration(gap), format_duration(at - (analysis.first_ts or 0)))
                for gap, at in player.longest_gaps[:5]
            )
            top_damage = "".join(
                "<tr><td>%s</td><td class=n>%s</td><td class=n>%s</td></tr>"
                % (esc(ability.name), compact(ability.total), percent(ability.crit_rate))
                for ability in analysis.top_abilities(player.damage_by_ability, 8)
            )
            top_taken = "".join(
                "<tr><td>%s</td><td class=n>%s</td><td class=n>%d</td></tr>"
                % (esc(ability.name), compact(ability.total), ability.hits)
                for ability in analysis.top_abilities(player.taken_by_ability, 8)
            )
            top_uptime = "".join(
                "<tr><td>%s</td><td class=n>%s</td></tr>"
                % (esc(name), percent(min(1.0, milliseconds / duration)))
                for name, _spell_id, milliseconds in uptimes
            )
            blocks.append(
                "<details><summary>%s <span class=dim>&middot; %s degats &middot; %s soins "
                "&middot; %s</span></summary><div class=body>"
                "<div class=grid>"
                "<div class=stat><b>%s</b><span>DPS</span></div>"
                "<div class=stat><b>%s</b><span>HPS</span></div>"
                "<div class=stat><b>%s</b><span>Degats subis</span></div>"
                "<div class=stat><b>%s</b><span>Temps sans action</span></div>"
                "<div class=stat><b>%d</b><span>Interruptions</span></div>"
                "<div class=stat><b>%s</b><span>Vie la plus basse</span></div>"
                "</div>"
                "<div class=cols>"
                "<div><h3>Ses degats</h3><table><tr><th>Capacite</th><th class=n>Total</th>"
                "<th class=n>Crit</th></tr>%s</table></div>"
                "<div><h3>Ce qu'il a pris</h3><table><tr><th>Capacite</th><th class=n>Total</th>"
                "<th class=n>Coups</th></tr>%s</table></div>"
                "</div>"
                "<div class=cols><div><h3>Effets actifs</h3><table>"
                "<tr><th>Effet</th><th class=n>Duree</th></tr>%s</table></div>"
                "<div><h3>Plus longues pauses</h3><ul class=chain>%s</ul></div></div>"
                "</div></details>"
                % (
                    esc(player.short_name),
                    compact(player.damage_done),
                    compact(player.healing_done),
                    plural(player.casts, "sort"),
                    compact(player.damage_done / seconds),
                    compact(player.healing_done / seconds),
                    compact(player.damage_taken),
                    format_duration(player.downtime_ms),
                    player.interrupts,
                    percent(player.min_hp_fraction) if player.min_hp_fraction is not None else "?",
                    top_damage or "<tr><td class=dim colspan=3>Rien</td></tr>",
                    top_taken or "<tr><td class=dim colspan=3>Rien</td></tr>",
                    top_uptime or "<tr><td class=dim colspan=2>Rien</td></tr>",
                    gaps or "<li class=dim>Aucune pause notable.</li>",
                )
            )
        return "<h3>Detail par joueur</h3>%s" % "".join(blocks)

    def _footer(self):
        problems = self.log.problems
        unknown = ", ".join(sorted(problems.unknown_subevents)) or "aucun"
        return (
            "<footer>LogsWoW %s &middot; lecture locale de <code>%s</code><br>"
            "Disposition detectee dans ce fichier&nbsp;: bloc avance de %d champs, "
            "champ de degats bruts %s, champ hideCaster %s. "
            "Lignes non comprises&nbsp;: %s. Evenements inconnus&nbsp;: %s.<br>"
            "GPLv3. Aucune donnee ne quitte cette machine.</footer></div></body></html>"
            % (
                __version__,
                esc(os.path.basename(self.log.path)),
                self.log.layout.advanced_width,
                "present" if self.log.layout.has_base_amount else "absent",
                "present" if self.log.layout.hide_caster else "absent",
                number(problems.total),
                esc(unknown),
            )
        )
