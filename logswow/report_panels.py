"""The unfolding panels: one per player, one per enemy, and their tables.

Split out of report.py, with the same rule as the timeline: formatters
are called through `fmt`, so one replacement reaches every table.
"""

from . import fmt
from .fmt import NBSP
from .fmt import bar_row as _bar_row
from .specs import label_of
from .timestamps import format_duration
from .wowhead import spell_url


class PanelsMixin:
    """The per-player and per-enemy half of `ReportWriter`."""

    def spell_link(self, spell_id, name):
        """The spell's name, linking to Wowhead in the reader's language.

        Nothing is fetched to render this: it is an anchor, followed only
        if someone clicks it.
        """
        label = fmt.esc(name or "Attaque")
        if not spell_id or self.wowhead_prefix is None:
            return label
        return (
            "<a href='%s' target='_blank' rel='noopener noreferrer'>%s</a>"
            % (fmt.esc(spell_url(spell_id, self.wowhead_prefix)), label)
        )

    def _rate(self, total, seconds):
        return fmt.compact(total / seconds) if seconds else "0"

    def _top_target(self, ability):
        ranked = ability.ranked_targets(1)
        if not ranked:
            return "<span class=dim>-</span>"
        name, amount = ranked[0]
        share = amount / ability.total if ability.total else 0
        others = len(ability.targets) - 1
        # "+1" sitting straight against "72 %" read as one number.
        tail = (" et %s" % fmt.plural(others, "autre")) if others else ""
        return "%s <span class=dim>%s%s</span>" % (fmt.esc(name), fmt.percent(share), tail)

    def _ability_table(self, abilities, casts_by_spell, seconds, mode, total=None):
        """One ability table. `mode` is damage, healing or taken."""
        if not abilities:
            return "<p class=dim>Rien.</p>"
        grand = total if total is not None else sum(a.total for a in abilities)
        rows = []
        for ability in abilities:
            casts = (casts_by_spell or {}).get(ability.spell_id, 0)
            share = (ability.total / grand) if grand else 0
            cells = [
                _bar_row(self.spell_link(ability.spell_id, ability.name), share),
                "<td class=n>%s</td>" % fmt.compact(ability.total),
                "<td class=n>%s</td>" % fmt.percent(share),
            ]
            if mode == "healing":
                cells.append("<td class=n>%s</td>" % fmt.percent(ability.overheal_rate))
            cells.append(
                "<td class=n>%s</td>" % (casts if casts else "<span class=dim>-</span>")
            )
            cells.append("<td class=n>%d</td>" % ability.hits)
            cells.append("<td class=n>%s</td>" % fmt.compact(ability.average))
            if mode != "taken":
                cells.append("<td class=n>%s</td>" % fmt.percent(ability.crit_rate))
            cells.append("<td class=n>%s</td>" % self._rate(ability.total, seconds))
            cells.append("<td>%s</td>" % self._top_target(ability))
            rows.append("<tr>%s</tr>" % "".join(cells))

        heads = ["Sort", "Total", "Part"]
        if mode == "healing":
            heads.append("Surguerison")
        heads += ["Casts", "Coups", "Moyenne"]
        if mode != "taken":
            heads.append("Crit")
        heads += ["Par sec.", "Principale cible" if mode != "taken" else "Principale source"]
        header = "".join(
            "<th%s>%s</th>" % ("" if index == 0 else " class=n", fmt.esc(name))
            for index, name in enumerate(heads)
        )
        return "<table><tr>%s</tr>%s</table>" % (header, "".join(rows))

    def _aura_table(self, rows, duration, other_label):
        if not rows:
            return "<p class=dim>Rien.</p>"
        body = "".join(
            "<tr>%s<td>%s</td><td class=n>%s</td></tr>"
            % (
                _bar_row(self.spell_link(spell_id, name), min(1.0, ms / duration)),
                fmt.esc(other),
                fmt.percent(min(1.0, ms / duration)),
            )
            for name, other, ms, spell_id in rows
        )
        return (
            "<table><tr><th>Effet</th><th>%s</th><th class=n>Duree</th></tr>%s</table>"
            % (fmt.esc(other_label), body)
        )

    def _counted_list(self, counts, limit=8):
        ranked = sorted(counts.items(), key=lambda item: -item[1])[:limit]
        return ", ".join(
            "%s%s" % (fmt.esc(name), (" x%d" % count) if count > 1 else "")
            for name, count in ranked
        )

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
            blocks.append(self._one_player(analysis, player, seconds))
        return "<h3>Detail par joueur</h3>%s" % "".join(blocks)

    def _one_player(self, analysis, player, seconds):
        duration = max(1, analysis.duration_ms)
        tiles = [
            ("DPS", fmt.compact(player.damage_done / seconds)),
            ("HPS", fmt.compact(player.healing_done / seconds)),
        ]
        if analysis.boss_names and analysis.has_several_pulls and player.damage_done:
            tiles.append(("Part sur les boss",
                          fmt.percent(player.damage_to_bosses / player.damage_done)))
        if player.pet_damage_taken:
            tiles.append(("Subis par ses invocations",
                          fmt.compact(player.pet_damage_taken)))
        tiles += [
            ("Degats subis", fmt.compact(player.damage_taken)),
            ("Absorbe sur lui", fmt.compact(player.absorbed_taken)),
            ("Absorbe par ses boucliers", fmt.compact(player.absorb_done)),
            ("Sorts par minute", "%.1f" % (player.casts / max(1.0, seconds / 60.0))),
            ("Temps sans action", format_duration(player.downtime_ms)),
            ("Interruptions", str(player.interrupts)),
            ("Dissipations", str(player.dispels)),
            ("Morts", str(player.deaths)),
            ("Vie la plus basse",
             fmt.percent(player.min_hp_fraction) if player.min_hp_fraction is not None else "?"),
        ]
        tiles_html = "".join(
            "<div class=stat><b>%s</b><span>%s</span></div>" % (fmt.esc(value), fmt.esc(label))
            for label, value in tiles
        )

        if player.absorb_by_ability:
            sections_absorb = [("Ce que ses boucliers ont absorbe", self._ability_table(
                analysis.top_abilities(player.absorb_by_ability, 12),
                None, seconds, "taken", player.absorb_done))]
        else:
            sections_absorb = []
        sections = [
            ("Ses degats", self._ability_table(
                analysis.top_abilities(player.damage_by_ability, 16),
                player.casts_by_spell, seconds, "damage", player.damage_done)),
        ]
        if player.healing_done or player.overhealing:
            sections.append(("Ses soins", self._ability_table(
                analysis.top_abilities(player.healing_by_ability, 16),
                player.casts_by_spell, seconds, "healing", player.healing_done)))
            sections.append(("Qui il a soigne", self._targets_table(player.healing_to)))
        sections.append(("Ce qu'il a pris", self._ability_table(
            analysis.top_abilities(player.taken_by_ability, 16),
            None, seconds, "taken", player.damage_taken)))
        sections.extend(sections_absorb)
        sections.append(("Gains recus", self._aura_table(
            analysis.player_uptimes(player.guid, 18, kind="BUFF"), duration, "De qui")))
        sections.append(("Affaiblissements subis", self._aura_table(
            analysis.player_uptimes(player.guid, 18, kind="DEBUFF"), duration, "De qui")))
        sections.append(("Ce qu'il a applique", self._aura_table(
            analysis.player_applied(player.guid, 18), duration, "Sur qui")))
        if analysis.auras_before_the_pull:
            sections.append(("", (
                "<p class=dim style='font-size:12px;margin:0'>Un effet deja "
                "actif quand le combat commence n'a pas de ligne d'application "
                "dans le journal%s: sa duree est comptee depuis le premier "
                "evenement du combat, ce qui est la seule borne que le fichier "
                "donne.</p>" % NBSP)))

        gaps = "".join(
            "<li><span class=dim>%s</span> sans lancer de sort, a %s</li>"
            % (format_duration(gap), format_duration(at - (analysis.first_ts or 0)))
            for gap, at in player.longest_gaps[:5]
        )
        sections.append((
            "Plus longues pauses",
            "<ul class=chain>%s</ul>" % (gaps or "<li class=dim>Aucune pause notable.</li>"),
        ))
        sections.append(("", self._cast_order(analysis, player)))

        notes = []
        if player.interrupted_spells:
            notes.append("<p class=dim style='font-size:12.5px;margin:8px 0 0'>"
                         "<b>Sorts ennemis coupes</b>%s %s</p>"
                         % (NBSP + ":", self._counted_list(player.interrupted_spells)))
        if player.dispelled_spells:
            notes.append("<p class=dim style='font-size:12.5px;margin:4px 0 0'>"
                         "<b>Effets dissipes</b>%s %s</p>"
                         % (NBSP + ":", self._counted_list(player.dispelled_spells)))

        body = "".join(
            ("<h3>%s</h3>%s" % (fmt.esc(title), content)) if title else content
            for title, content in sections
        )
        summary_casts = fmt.plural(player.casts, "sort")
        if player.pet_casts:
            summary_casts += " (dont %d de ses invocations)" % player.pet_casts
        return (
            "<details><summary>%s <span class=dim>&middot; %s &middot; %s degats "
            "&middot; %s soins &middot; %s</span></summary><div class=body>"
            "<div class='grid tiles'>%s</div>%s%s</div></details>"
            % (
                fmt.esc(player.short_name),
                fmt.esc(label_of(player.spec_id) or "role inconnu"),
                fmt.compact(player.damage_done),
                fmt.compact(player.healing_done),
                summary_casts,
                tiles_html,
                body,
                "".join(notes),
            )
        )

    def _targets_table(self, targets, limit=20):
        if not targets:
            return "<p class=dim>Rien.</p>"
        ranked = sorted(targets.items(), key=lambda item: -item[1])[:limit]
        grand = sum(targets.values()) or 1
        rows = "".join(
            "<tr>%s<td class=n>%s</td><td class=n>%s</td></tr>"
            % (_bar_row(fmt.esc(name), value / grand), fmt.compact(value),
               fmt.percent(value / grand))
            for name, value in ranked
        )
        return (
            "<table><tr><th>Cible</th><th class=n>Total</th><th class=n>Part</th></tr>"
            "%s</table>" % rows
        )

    def _enemies(self, analysis, seconds):
        # Twelve rather than everything: a whole raid night's report was
        # 3.7 MB, and the tail of that list is trash that hit once.
        enemies = analysis.ranked_enemies("damage_done", 12)
        if not enemies:
            return ""
        blocks = []
        for enemy in enemies:
            sections = []
            if enemy.damage_by_ability:
                sections.append(("Ce qu'il inflige", self._ability_table(
                    analysis.top_abilities(enemy.damage_by_ability, 10),
                    None, seconds, "damage", enemy.damage_done)))
            if enemy.taken_by_ability:
                sections.append(("Ce qu'il a subi", self._ability_table(
                    analysis.top_abilities(enemy.taken_by_ability, 10),
                    None, seconds, "taken", enemy.damage_taken)))
            if enemy.casts_by_spell:
                ranked = sorted(enemy.casts_by_spell.items(), key=lambda item: -item[1])[:16]
                peak = ranked[0][1] or 1
                sections.append(("Ses sorts", "<table><tr><th>Sort</th>"
                                 "<th class=n>Lances</th></tr>%s</table>"
                                 % "".join(
                                     "<tr>%s<td class=n>%d</td></tr>"
                                     % (_bar_row(fmt.esc(name), count / peak), count)
                                     for name, count in ranked)))
            tiles = "".join(
                "<div class=stat><b>%s</b><span>%s</span></div>" % (fmt.esc(value), fmt.esc(label))
                for label, value in (
                    ("Unites", str(enemy.count)),
                    ("Degats infliges", fmt.compact(enemy.damage_done)),
                    ("Degats subis", fmt.compact(enemy.damage_taken)),
                    ("Sorts lances", str(enemy.casts)),
                    ("Tues", str(enemy.deaths)),
                )
            )
            blocks.append(
                "<details><summary>%s <span class=dim>&middot; %s &middot; "
                "%s inflige &middot; %s subi</span></summary><div class=body>"
                "<div class='grid tiles'>%s</div>%s</div></details>"
                % (
                    fmt.esc(enemy.name),
                    fmt.plural(enemy.count, "unite"),
                    fmt.compact(enemy.damage_done),
                    fmt.compact(enemy.damage_taken),
                    tiles,
                    "".join("<h3>%s</h3>%s" % (fmt.esc(title), content)
                            for title, content in sections),
                )
            )
        return "<h3>Detail par ennemi</h3>%s" % "".join(blocks)

    def _enemy_casts(self, analysis):
        """What became of the spells the enemy tried to cast."""
        casts = analysis.enemy_casts
        if not casts.get("commences"):
            return ""
        started = casts["commences"]
        order = ("aboutis", "coupes", "cible morte", "autre")
        titles = {
            "aboutis": "Aboutis",
            "coupes": "Coupes par une interruption",
            "cible morte": "Lanceur tue pendant l'incantation",
            "autre": "Non aboutis, cause non dite par le journal",
        }
        rows = "".join(
            "<tr>%s<td class=n>%d</td><td class=n>%s</td></tr>"
            % (
                _bar_row(fmt.esc(titles[key]), casts[key] / started),
                casts[key],
                fmt.percent(casts[key] / started),
            )
            for key in order
            if casts[key]
        )
        top = ""
        if analysis.interrupted_spells:
            top = ("<p class=dim style='margin:10px 0 0;font-size:12px'>Les plus "
                   "coupes%s: %s.</p>"
                   % (NBSP, self._counted_list(analysis.interrupted_spells, 8)))
        return (
            "<h3>Ce que le groupe a empeche</h3><div class=card>"
            "<p class=dim style='margin:0 0 10px;font-size:12.5px'>%s sorts commences "
            "par l'ennemi%s:</p><table><tr><th>Issue</th><th class=n>Nombre</th>"
            "<th class=n>Part</th></tr>%s</table>%s"
            "<p class=dim style='margin:10px 0 0;font-size:12px'>Un sort instantane "
            "n'apparait pas ici%s: seuls ceux qui ont un temps d'incantation laissent "
            "une trace. La derniere ligne regroupe tout le reste, controle compris%s: "
            "le journal ne dit nulle part qu'un sort est un etourdissement, donc rien "
            "ici ne pretend le savoir.</p></div>"
            % (started, NBSP, rows, top, NBSP, NBSP)
        )
