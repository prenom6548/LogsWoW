# SPDX-License-Identifier: AGPL-3.0-or-later
"""Boss encounters inside a segment, bounded by the file's own markers.

A key contains its bosses, and the pull table has to know which of its
pulls were boss fights and how each ended. Matching a unit's name to the
encounter's answered that for most bosses and not at all for a council,
a duo or an altar, which no unit is named after; the window between
ENCOUNTER_START and ENCOUNTER_END answers it for all of them.
`SegmentAnalysis` inherits this and owns the state it uses.
"""

from .models import canon
from .tokenize import as_int


class EncounterLedger:
    """The boss-encounter half of `SegmentAnalysis`."""

    def _feed_encounter_start(self, event):
        """A boss encounter opens: its name, and the window it lasts.

        The name is what lets a trash pull that funnels into a boss be
        told apart. The window is what the file actually says about which
        stretch of a key was a boss fight -- and it is the only thing that
        works for a council, whose units are all named something other
        than the encounter: "Le conseil des tribus" had no unit of that
        name, and a real key showed 0% of damage on the boss for all five
        players. Matching names alone also coloured a wipe like a kill.
        """
        fields = event.fields
        name = fields[2] if len(fields) > 2 and isinstance(fields[2], str) else ""
        if name:
            self.boss_names.add(canon(name))
        if self._encounter is not None:
            # A start with the previous one still open: its END never came.
            self._close_encounter(self.last_ts or event.ts, None)
        self._encounter = {
            "label": name or "Rencontre", "name": canon(name), "start": event.ts,
            "named": 0, "window": 0, "players": {}, "blocks": {},
        }

    def _feed_encounter_end(self, event):
        if self._encounter is None:
            return
        fields = event.fields
        success = bool(as_int(fields[5], 0)) if len(fields) > 5 else None
        self._close_encounter(event.ts, success)

    def _note_window_damage(self, player, block, amount):
        """Damage dealt during an open encounter, to no unit named as a boss."""
        encounter = self._encounter
        encounter["window"] += amount
        players = encounter["players"]
        players[player.guid] = players.get(player.guid, 0) + amount
        held = encounter["blocks"].get(id(block))
        encounter["blocks"][id(block)] = (block, (held[1] if held else 0) + amount)

    def _close_encounter(self, end, success):
        """Tag the pulls the encounter overlapped, and settle a council.

        An encounter whose own name was never on a unit it fought is a
        council, or anything else the client names as a whole: its whole
        window counts as boss damage, and the page says so rather than
        showing a boss fight with no damage on the boss.
        """
        encounter, self._encounter = self._encounter, None
        # (label, start, end, success, fought): what the page's counters
        # read, so a key selected alone still says how many bosses it held.
        fought = bool(encounter["named"] or encounter["window"])
        self.encounters.append((encounter["label"], encounter["start"], end, success, fought))
        for block in reversed(self.blocks):
            if block.end_ts < encounter["start"]:
                break
            if block.start_ts <= end:
                block.encounters.append((encounter["label"], success))
        if encounter["named"] or not encounter["window"]:
            return
        self.window_encounters.append(encounter["label"])
        for block, amount in encounter["blocks"].values():
            block.damage_boss += amount
        for guid, amount in encounter["players"].items():
            player = self.players.get(guid)
            if player is not None:
                player.damage_to_bosses += amount
