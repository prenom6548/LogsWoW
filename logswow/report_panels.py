# SPDX-License-Identifier: AGPL-3.0-or-later
"""The unfolding panels: one per player, one per enemy, and their tables.

Split out of report.py, with the same rule as the timeline: formatters
are called through `fmt`, so one replacement reaches every table.
"""

from . import fmt
from .fmt import NBSP
from .fmt import bar_row as _bar_row
from .i18n import N_, _, spell_label
from .models import OTHER_TARGETS
from .specs import label_of
from .timestamps import format_duration
from .wowhead import spell_url

# How an enemy's melee swing at a player ended, in the order the table
# lists them: "hit" is the analysis's own key, the rest are the file's
# miss types. A type not listed here is shown under its own name.
MELEE_OUTCOMES = (
    ("hit", N_("Touché")),
    ("ABSORB", N_("Absorbé entièrement")),
    ("PARRY", N_("Paré")),
    ("DODGE", N_("Esquivé")),
    ("MISS", N_("Raté")),
    ("BLOCK", N_("Bloqué entièrement")),
    ("DEFLECT", N_("Dévié")),
    ("IMMUNE", N_("Insensible")),
    ("RESIST", N_("Résisté")),
    ("REFLECT", N_("Renvoyé")),
    ("EVADE", N_("Hors d'atteinte")),
)
# The keys of `Player.melee_taken` that describe hits rather than count swings.
MELEE_DETAILS = frozenset({"crit", "partial_block", "front", "behind", "unplaced",
                           "avoided_front", "avoided_behind"})
# A player the enemy swung at fewer times than this gets no melee table:
# a healer clipped by three swings learns nothing from percentages.
MELEE_SECTION_MIN = 10
# Fewer placed swings than this and no share of "from behind" is given.
MELEE_SIDE_MIN = 10


class PanelsMixin:
    """The per-player and per-enemy half of `ReportWriter`."""

    def spell_link(self, spell_id, name):
        """The spell's name, linking to Wowhead in the reader's language.

        Nothing is fetched to render this: it is an anchor, followed only
        if someone clicks it.
        """
        label = fmt.esc(spell_label(name))
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
        tail = (_(" et %s") % fmt.plural(others, "autre")) if others else ""
        return "%s <span class=dim>%s%s</span>" % (fmt.esc(name), fmt.percent(share), tail)

    def _ability_table(self, abilities, casts_by_spell, seconds, mode, total=None, limit=None):
        """One ability table. `mode` is damage, healing or taken.

        Past `limit` rows the rest is not dropped: it folds into a line
        that opens on the others. A rogue's Mutilate, split by the client
        into a main-hand and an off-hand row, fell below a hard cut of
        sixteen on a real key and vanished from the page without a word.
        """
        if not abilities:
            return _("<p class=dim>Rien.</p>")
        grand = total if total is not None else sum(a.total for a in abilities)
        shown, rest = (abilities[:limit], abilities[limit:]) if limit else (abilities, [])
        table = self._ability_rows(shown, casts_by_spell, seconds, mode, grand)
        if not rest:
            return table
        hidden = sum(a.total for a in rest)
        return table + (
            _("<details class=more><summary>%s de plus &middot; %s (%s)</summary>%s</details>")
            % (fmt.plural(len(rest), "sort"), fmt.compact(hidden),
               fmt.percent(hidden / grand) if grand else fmt.percent(0),
               self._ability_rows(rest, casts_by_spell, seconds, mode, grand)))

    def _ability_rows(self, abilities, casts_by_spell, seconds, mode, grand):
        """The table itself, header included."""
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

        heads = [_("Sort"), _("Total"), _("Part")]
        if mode == "healing":
            heads.append(_("Surguérison"))
        heads += [_("Casts"), _("Coups"), _("Moyenne")]
        if mode != "taken":
            heads.append(_("Crit"))
        heads += [_("Par sec."),
                  _("Principale cible") if mode != "taken" else _("Principale source")]
        header = "".join(
            "<th%s>%s</th>" % ("" if index == 0 else " class=n", fmt.esc(name))
            for index, name in enumerate(heads)
        )
        return "<table><tr>%s</tr>%s</table>" % (header, "".join(rows))

    def _aura_table(self, rows, duration, other_label):
        if not rows:
            return _("<p class=dim>Rien.</p>")
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
            _("<table><tr><th>Effet</th><th>%s</th><th class=n>Durée</th></tr>%s</table>")
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
        # Every player who took part: a heroic raid is up to thirty, and a
        # cap here would drop a panel without a word.
        for player in rows:
            if not analysis.took_part(player):
                continue
            blocks.append(self._one_player(analysis, player, seconds))
        return _("<h3>Détail par joueur</h3>%s") % "".join(blocks)

    def _one_player(self, analysis, player, seconds):
        tiles_html = self._player_tiles(analysis, player, seconds)
        sections = self._player_sections(analysis, player, seconds)
        sections.append(("", self._cast_order(analysis, player)))
        body = "".join(
            ("<h3>%s</h3>%s" % (fmt.esc(title), content)) if title else content
            for title, content in sections
        )
        summary_casts = fmt.plural(player.casts, "sort")
        if player.pet_casts:
            summary_casts += _(" (dont %d de ses invocations)") % player.pet_casts
        return (
            _("<details><summary>%s <span class=dim>&middot; %s &middot; %s dégâts "
              "&middot; %s soins &middot; %s</span></summary><div class=body>"
              "<div class='grid tiles'>%s</div>%s%s</div></details>")
            % (
                fmt.esc(player.short_name),
                fmt.esc(label_of(player.spec_id) or _("rôle inconnu")),
                fmt.compact(player.damage_done),
                fmt.compact(player.healing_done),
                summary_casts,
                tiles_html,
                body,
                self._player_notes(player),
            )
        )

    def _player_tiles(self, analysis, player, seconds):
        """The figures at the top of a player's panel; role-specific ones only when they apply."""
        tiles = [
            ("DPS", fmt.compact(player.damage_done / seconds)),
            ("HPS", fmt.compact(player.healing_done / seconds)),
        ]
        if analysis.boss_names and analysis.has_several_pulls and player.damage_done:
            tiles.append((_("Part sur les boss"),
                          fmt.percent(player.damage_to_bosses / player.damage_done)))
        if player.pet_damage_taken:
            tiles.append((_("Subis par ses invocations"),
                          fmt.compact(player.pet_damage_taken)))
        tiles += [
            (_("Dégâts subis"), fmt.compact(player.damage_taken)),
            (_("Absorbé sur lui"), fmt.compact(player.absorbed_taken)),
            (_("Absorbé par ses boucliers"), fmt.compact(player.absorb_done)),
        ]
        if player.support_damage or player.support_healing:
            tiles.append((_("Soutien crédité par le jeu"),
                          fmt.compact(player.support_damage + player.support_healing)))
        tiles += [
            (_("Sorts par minute"), "%.1f" % (player.casts / max(1.0, seconds / 60.0))),
            (_("Temps sans action"), format_duration(player.downtime_ms)),
            (_("Interruptions"), str(player.interrupts)),
            (_("Dissipations"), str(player.dispels)),
            (_("Morts"), str(player.deaths)),
            (_("Vie la plus basse"),
             fmt.percent(player.min_hp_fraction) if player.min_hp_fraction is not None else "?"),
        ]
        return "".join(
            "<div class=stat><b>%s</b><span>%s</span></div>" % (fmt.esc(value), fmt.esc(label))
            for label, value in tiles
        )

    def _player_sections(self, analysis, player, seconds):
        """[(title, html)] of a player's tables, in the order the panel shows them."""
        if player.absorb_by_ability:
            sections_absorb = [(_("Ce que ses boucliers ont absorbé"), self._ability_table(
                analysis.top_abilities(player.absorb_by_ability, None),
                None, seconds, "taken", player.absorb_done, limit=12))]
        else:
            sections_absorb = []
        sections = [
            (_("Ses dégâts"), self._ability_table(
                analysis.top_abilities(player.damage_by_ability, None),
                player.casts_by_spell, seconds, "damage", player.damage_done, limit=16)),
        ]
        if player.healing_done or player.overhealing:
            sections.append((_("Ses soins"), self._ability_table(
                analysis.top_abilities(player.healing_by_ability, None),
                player.casts_by_spell, seconds, "healing", player.healing_done, limit=16)))
            sections.append((_("Qui il a soigné"), self._targets_table(player.healing_to)))
        sections.append((_("Ce qu'il a pris"), self._ability_table(
            analysis.top_abilities(player.taken_by_ability, None),
            None, seconds, "taken", player.damage_taken, limit=16)))
        melee = self._melee_taken(player.melee_taken)
        if melee:
            sections.append((_("Les coups de mêlée reçus"), melee))
        sections.extend(sections_absorb)
        if player.support_damage or player.support_healing:
            sections.append((_("Soutien que le jeu lui crédite"), self._support(
                analysis, player, seconds)))
        sections += self._player_auras(analysis, player)
        sections.append((_("Plus longues pauses"), self._player_gaps(analysis, player)))
        return sections

    def _player_auras(self, analysis, player):
        """The three aura tables of a player's panel, and the note on auras up before the pull."""
        duration = max(1, analysis.duration_ms)
        sections = [
            (_("Gains reçus"), self._aura_table(
                analysis.player_uptimes(player.guid, 18, kind="BUFF"), duration, _("De qui"))),
            (_("Affaiblissements subis"), self._aura_table(
                analysis.player_uptimes(player.guid, 18, kind="DEBUFF"), duration, _("De qui"))),
            (_("Ce qu'il a appliqué"), self._aura_table(
                analysis.player_applied(player.guid, 18), duration, _("Sur qui"))),
        ]
        if analysis.auras_before_the_pull:
            sections.append(("", (
                _("<p class=dim style='font-size:12px;margin:0'>Un effet déjà "
                  "actif quand le combat commence n'a pas de ligne d'application "
                  "dans le journal%s: sa durée est comptée depuis le premier "
                  "événement du combat, ce qui est la seule borne que le fichier "
                  "donne.</p>") % NBSP)))
        return sections

    @staticmethod
    def _melee_taken(taken):
        """How the enemy's melee swings at a player ended, and from which side they landed.

        "" below `MELEE_SECTION_MIN` swings. The side is an estimate from
        positions (`SegmentAnalysis._melee_side`), and the page says so in
        the words the owner asked for, with the check that backs it.
        """
        swings = sum(count for key, count in taken.items() if key not in MELEE_DETAILS)
        if swings < MELEE_SECTION_MIN:
            return ""
        labels = dict(MELEE_OUTCOMES)
        order = [key for key, _label in MELEE_OUTCOMES if taken.get(key)]
        order += sorted(key for key in taken if key not in labels and key not in MELEE_DETAILS)

        def row(label, count, dim=False):
            # A detail of the hits (critical, partly blocked) is a share of
            # the hits; every other row a share of all the swings.
            whole = taken.get("hit", 0) if dim else swings
            cell = "<td class=dim>%s</td>" % label if dim else _bar_row(label, count / swings)
            return "<tr>%s<td class=n>%s</td><td class=n>%s</td></tr>" % (
                cell, fmt.number(count), fmt.percent(count / max(1, whole)))

        rows = []
        for key in order:
            rows.append(row(fmt.esc(_(labels[key]) if key in labels else key), taken[key]))
            if key == "hit":
                for detail, label in (("crit", _("dont critiques")),
                                      ("partial_block", _("dont bloqués en partie"))):
                    if taken.get(detail):
                        rows.append(row("&nbsp;&nbsp;" + label, taken[detail], dim=True))
        html = (_("<table><tr><th>Issue</th><th class=n>Coups</th><th class=n>Part</th></tr>"
                  "%s</table>") % "".join(rows))
        avoided = sum(taken.get(key, 0) for key in ("PARRY", "DODGE", "MISS"))
        html += (_("<p><b>%s</b> des coups évités (parés, esquivés ou ratés).</p>")
                 % fmt.percent(avoided / swings))
        front, behind = taken.get("front", 0), taken.get("behind", 0)
        if front + behind < MELEE_SIDE_MIN:
            return html
        html += (_("<p><b>%s</b> des coups qui ont touché venaient de derrière "
                   "(%s sur %s dont la position est connue).</p>")
                 % (fmt.percent(behind / (front + behind)), fmt.number(behind),
                    fmt.number(front + behind)))
        checked = taken.get("avoided_front", 0) + taken.get("avoided_behind", 0)
        control = ""
        if checked >= MELEE_SIDE_MIN:
            control = (_(" Contrôle sur ce combat%s: le jeu ne laisse ni parer ni esquiver "
                         "un coup venu de derrière, et %s des %s parades et esquives "
                         "placées tombent bien devant.")
                       % (NBSP, fmt.percent(taken.get("avoided_front", 0) / checked),
                          fmt.number(checked)))
        return html + (_("<p class=dim style='font-size:12px;margin:0'>Estimation fiable, "
                         "mais pas une donnée écrite, et limitée à la mêlée%s: le journal "
                         "ne dit pas d'où vient un coup. LogsWoW le déduit de la position "
                         "de l'attaquant et de l'orientation du joueur, que le journal "
                         "donne ligne par ligne.%s</p>") % (NBSP, control))

    @staticmethod
    def _player_gaps(analysis, player):
        """The player's five longest stretches without a cast."""
        gaps = "".join(
            _("<li><span class=dim>%s</span> sans lancer de sort, à %s</li>")
            % (format_duration(gap), format_duration(at - (analysis.first_ts or 0)))
            for gap, at in player.longest_gaps[:5]
        )
        return "<ul class=chain>%s</ul>" % (gaps or _("<li class=dim>Aucune pause notable.</li>"))

    def _player_notes(self, player):
        """The enemy spells the player cut and the effects they dispelled, named."""
        notes = []
        if player.interrupted_spells:
            notes.append(_("<p class=dim style='font-size:12.5px;margin:8px 0 0'>"
                           "<b>Sorts ennemis coupés</b>%s %s</p>")
                         % (NBSP + ":", self._counted_list(player.interrupted_spells)))
        if player.dispelled_spells:
            notes.append(_("<p class=dim style='font-size:12.5px;margin:4px 0 0'>"
                           "<b>Effets dissipés</b>%s %s</p>")
                         % (NBSP + ":", self._counted_list(player.dispelled_spells)))
        return "".join(notes)

    def _support(self, analysis, player, seconds):
        """An Augmentation Evoker's share of other players' numbers, and what it is not."""
        table = ""
        if player.support_by_ability:
            table = self._ability_table(
                analysis.top_abilities(player.support_by_ability, None),
                None, seconds, "damage", player.support_damage, limit=10)
        return (
            _("%s<p class=dim style='font-size:12px;margin:4px 0 0'>Le journal crédite "
              "cet évocateur de %s de dégâts et %s de soins portés par d'autres joueurs"
              "%s: la part que ses renforts (Puissance d'ébène, Prescience...) ont ajoutée "
              "à leurs coups, et ses Bombardements, que le journal écrit au nom de l'allié "
              "qui les a déclenchés. Ces montants sont <b>déjà comptés</b> chez ceux qui ont "
              "porté les coups et ne sont pas ajoutés aux siens%s; Warcraft Logs, lui, les "
              "retire aux autres pour les lui donner, d'où l'écart entre les deux.</p>")
            % (table, fmt.compact(player.support_damage), fmt.compact(player.support_healing),
               NBSP, NBSP)
        )

    def _targets_table(self, targets, limit=20):
        """Who a healer healed. Past `limit`, the rest folds open below.

        A raid healer reached 36 targets on a real night, and the sixteen
        after the twentieth were dropped without a word.
        """
        if not targets:
            return _("<p class=dim>Rien.</p>")
        ranked = sorted(targets.items(), key=lambda item: -item[1])
        grand = sum(targets.values()) or 1

        def table(rows):
            return (_("<table><tr><th>Cible</th><th class=n>Total</th><th class=n>Part</th></tr>"
                      "%s</table>") % "".join(
                        "<tr>%s<td class=n>%s</td><td class=n>%s</td></tr>"
                        % (_bar_row(fmt.esc(_(name) if name == OTHER_TARGETS else name),
                                    value / grand), fmt.compact(value),
                           fmt.percent(value / grand))
                        for name, value in rows))

        shown, rest = ranked[:limit], ranked[limit:]
        if not rest:
            return table(shown)
        hidden = sum(value for _name, value in rest)
        return table(shown) + (
            _("<details class=more><summary>%s de plus &middot; %s (%s)</summary>%s</details>")
            % (fmt.plural(len(rest), "cible"), fmt.compact(hidden),
               fmt.percent(hidden / grand), table(rest)))

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
                sections.append((_("Ce qu'il inflige"), self._ability_table(
                    analysis.top_abilities(enemy.damage_by_ability, None),
                    None, seconds, "damage", enemy.damage_done, limit=10)))
            if enemy.taken_by_ability:
                sections.append((_("Ce qu'il a subi"), self._ability_table(
                    analysis.top_abilities(enemy.taken_by_ability, None),
                    None, seconds, "taken", enemy.damage_taken, limit=10)))
            if enemy.casts_by_spell:
                ranked = sorted(enemy.casts_by_spell.items(), key=lambda item: -item[1])[:16]
                peak = ranked[0][1] or 1
                sections.append((_("Ses sorts"), _("<table><tr><th>Sort</th>"
                                                   "<th class=n>Lancés</th></tr>%s</table>")
                                 % "".join(
                                     "<tr>%s<td class=n>%d</td></tr>"
                                     % (_bar_row(fmt.esc(name), count / peak), count)
                                     for name, count in ranked)))
            tiles = "".join(
                "<div class=stat><b>%s</b><span>%s</span></div>" % (fmt.esc(value), fmt.esc(label))
                for label, value in (
                    (_("Unités"), str(enemy.count)),
                    (_("Dégâts infligés"), fmt.compact(enemy.damage_done)),
                    (_("Dégâts subis"), fmt.compact(enemy.damage_taken)),
                    (_("Sorts lancés"), str(enemy.casts)),
                    (_("Tués"), str(enemy.deaths)),
                )
            )
            blocks.append(
                _("<details><summary>%s <span class=dim>&middot; %s &middot; "
                  "%s infligé &middot; %s subi</span></summary><div class=body>"
                  "<div class='grid tiles'>%s</div>%s</div></details>")
                % (
                    fmt.esc(enemy.name),
                    fmt.plural(enemy.count, "unité"),
                    fmt.compact(enemy.damage_done),
                    fmt.compact(enemy.damage_taken),
                    tiles,
                    "".join("<h3>%s</h3>%s" % (fmt.esc(title), content)
                            for title, content in sections),
                )
            )
        return _("<h3>Détail par ennemi</h3>%s") % "".join(blocks)

    def _enemy_casts(self, analysis):
        """What became of the spells the enemy tried to cast."""
        casts = analysis.enemy_casts
        if not casts.get("commences"):
            return ""
        started = casts["commences"]
        order = ("aboutis", "coupes", "cible morte", "autre")
        titles = {
            "aboutis": _("Aboutis"),
            "coupes": _("Coupés par une interruption"),
            "cible morte": _("Lanceur tué pendant l'incantation"),
            "autre": _("Non aboutis, cause non dite par le journal"),
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
            top = (_("<p class=dim style='margin:10px 0 0;font-size:12px'>Les plus "
                     "coupés%s: %s.</p>")
                   % (NBSP, self._counted_list(analysis.interrupted_spells, 8)))
        return (
            _("<h3>Ce que le groupe a empêché</h3><div class=card>"
              "<p class=dim style='margin:0 0 10px;font-size:12.5px'>%s sorts commencés "
              "par l'ennemi%s:</p><table><tr><th>Issue</th><th class=n>Nombre</th>"
              "<th class=n>Part</th></tr>%s</table>%s"
              "<p class=dim style='margin:10px 0 0;font-size:12px'>Un sort instantané "
              "n'apparaît pas ici%s: seuls ceux qui ont un temps d'incantation laissent "
              "une trace. La dernière ligne regroupe tout le reste, contrôle compris%s: "
              "le journal ne dit nulle part qu'un sort est un étourdissement, donc rien "
              "ici ne prétend le savoir.</p></div>")
            % (started, NBSP, rows, top, NBSP, NBSP)
        )
