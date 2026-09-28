# SPDX-License-Identifier: AGPL-3.0-or-later
"""Aura uptime: who held what, put there by whom, and for how long.

The one part of the analysis that has to pair two lines -- an APPLIED
with its REMOVED -- and so the part with the most ways to go wrong:
two casters of one spell, several units sharing a name, overlapping
copies, an aura already up when the pull began. Each of those is a
dated lesson in the docstrings below. `SegmentAnalysis` inherits this
and owns the state it uses (`aura_open`, `players`, `first_ts`...).
"""


class AuraLedger:
    """The aura half of `SegmentAnalysis`."""

    def _aura_key(self, event):
        """What identifies one aura: the unit, the spell, **and the caster**.

        Two casters can hold the same spell on the same target at the
        same time, and real logs do it constantly: two players casting
        "Clairvoyance de tisse-arcane" on one of them, and -- the case
        that needs the GUID rather than the name -- **several creatures
        sharing a name**, each stacking its own "Celerite du Neant" on
        the same player. Keyed by unit and spell alone, the second
        application found the slot taken and was dropped, then its
        removal closed the *first* one's interval: a silent under-count
        present since the first commit. It stopped being silent when an
        unmatched removal started being read as "up since the pull
        began" -- one such removal credited 122 seconds of a 154-second
        fight -- and the bounded-uptime invariant said so on two of the
        owner's five real logs. The caster's *name* is still what the
        report groups by; only the slot is per unit.
        """
        return (event.dest.guid, event.spell_id,
                event.source.guid or event.source.short_name or "?")

    def _aura_open(self, event):
        """Remember when an aura landed, and who put it there.

        Both ends matter and the file has both: a player wants to know
        which of their buffs came from whom, and which of their debuffs
        they kept up on what.
        """
        key = self._aura_key(event)
        if key not in self.aura_open:
            if len(self.aura_open) >= 4000:
                # Remember that one was dropped: `_aura_close` must not
                # then read an unmatched removal as "it was up from the
                # start", because here it demonstrably was not.
                self._aura_overflowed = True
                return
            self.aura_open[key] = (
                event.ts,
                self._name_of(event.source) or "?",
                event.spell_name,
                event.aura_type or "BUFF",
                self._name_of(event.dest) or "?",
                event.dest.is_player,
                event.source.guid,
            )

    def _aura_close(self, event):
        """An aura ended. If it began before the segment did, say so.

        A buff cast before the pull has no APPLIED line inside the
        segment, so its removal used to match nothing and the whole
        uptime was lost -- a shield taken before the pull read as 0%.
        The file does say it was there: it was removed at this moment and
        never applied within the segment, so it was up from the segment's
        first event until now. That is the same reading the online sites
        use, and it stays inside the bound the invariants check.

        Two cases where that reasoning fails, and both are refused: a
        removal whose APPLIED was dropped by the cap in `_aura_open`, and
        a *second* unmatched removal of the same aura on the same unit.
        The client writes an APPLIED before every REMOVED, so one
        unmatched removal means the aura predates the segment -- but two
        mean lines are missing, and inferring from the segment's start
        each time credits the whole run again and again. A run of a
        synthetic log did exactly that and came out at twenty-four times
        the length of the fight, which is what the bounded-uptime
        invariant is there to catch.
        """
        key = self._aura_key(event)
        opened = self.aura_open.pop(key, None)
        if opened is None:
            if self._aura_overflowed or self.first_ts is None:
                return
            if event.ts <= self.first_ts or key in self._inferred_auras:
                return
            if len(self._inferred_auras) >= 4000:
                return
            self._inferred_auras.add(key)
            opened = (
                self.first_ts,
                self._name_of(event.source) or "?",
                event.spell_name,
                event.aura_type or "BUFF",
                self._name_of(event.dest) or "?",
                event.dest.is_player,
                event.source.guid,
            )
            self.auras_before_the_pull += 1
        self._bank_aura(event.dest.guid, event.spell_id, opened, event.ts)

    @staticmethod
    def _merge_uptime(totals, horizons, key, start, ended, room):
        """Add [start, ended] to a row's uptime, counting overlap once.

        **Uptime is the time the aura was up, not the sum of the times it
        was applied**, and on a real fight those differ by a lot: six
        "Tortionnaire infidele" each held their own Fixation on one
        player at the same moment, and adding the six durations gave 249
        seconds of a 181-second fight. What a reader means by "68% of the
        fight" is the union of the intervals.

        Banks arrive in order of when each aura *ended*, so the union can
        be kept without storing any interval: everything up to `horizon`
        is already counted, and only what lies beyond it is new.
        """
        if key not in totals and len(totals) >= room:
            return
        horizon = horizons.get(key)
        if horizon is not None and start < horizon:
            start = horizon
        if ended <= start:
            return
        totals[key] = totals.get(key, 0) + (ended - start)
        if horizon is None or ended > horizon:
            horizons[key] = ended

    def _bank_aura(self, guid, spell_id, opened, ended):
        (start, source_name, spell_name, aura_type, dest_name, dest_is_player,
         source_guid) = opened
        if ended <= start:
            return
        # Only a player's *own* buffs count as that player's uptime. Routing
        # a pet's auras to its owner, the way damage is routed, pushed one
        # warlock's totals past 300% of the fight: several pets can hold
        # the same aura at the same time, and a person cannot.
        if dest_is_player:
            player = self.players.get(guid)
            if player is not None:
                self._merge_uptime(
                    player.auras_gained, player._gained_until,
                    (spell_id, spell_name, source_name, aura_type),
                    start, ended, 400,
                )
        # By GUID: two players sharing a name on two realms used to have
        # the second one's auras credited to the first.
        caster = self.players.get(source_guid)
        if caster is not None:
            self._merge_uptime(
                caster.auras_applied, caster._applied_until,
                (spell_id, spell_name, dest_name), start, ended, 400,
            )

    # -- readers the report uses ------------------------------------------

    def player_uptimes(self, guid, limit=14, kind=None):
        """[(spell, who applied it, milliseconds)] for one player.

        `kind` filters to "BUFF" or "DEBUFF"; None merges both.
        """
        player = self.players.get(guid)
        if player is None:
            return []
        merged = {}
        for (spell_id, name, source, aura_type), milliseconds in player.auras_gained.items():
            if kind and aura_type != kind:
                continue
            key = (spell_id, name, source)
            merged[key] = merged.get(key, 0) + milliseconds
        rows = [
            (name, source, ms, spell_id)
            for (spell_id, name, source), ms in merged.items()
            if ms > 0
        ]
        rows.sort(key=lambda row: row[2], reverse=True)
        return rows[:limit]

    def player_applied(self, guid, limit=14):
        """[(spell, on whom, milliseconds)] -- a player's own auras."""
        player = self.players.get(guid)
        if player is None:
            return []
        rows = [
            (name, target, milliseconds, spell_id)
            for (spell_id, name, target), milliseconds in player.auras_applied.items()
            if milliseconds > 0
        ]
        rows.sort(key=lambda row: row[2], reverse=True)
        return rows[:limit]
