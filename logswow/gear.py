# SPDX-License-Identifier: AGPL-3.0-or-later
"""What a player wore: the equipment `COMBATANT_INFO` writes at the start of a fight.

**Measured 2026-10-02 on the owner's night (110 lines, 12.1.0):** field 28 is the
equipment, 18 entries in inventory-slot order (head, neck, shoulders, shirt, chest,
waist, legs, feet, wrists, hands, ring, ring, trinket, trinket, back, main hand,
off hand, tabard), each `(itemID, itemLevel, (enchants), (bonus ids), (gems))`. An
empty slot is `(0, 0, (), (), ())`; a gem is an id followed by its own level.

The file gives an item's **number and level**, never its name, icon or stats: those
live in the game's item database, which a program that reads only the log does not
have. So the average item level is computed here, offline, and each item is shown as a
number with a link that opens Wowhead if the reader clicks it (the one allowed
exception to "the page fetches nothing": a link is followed only on a click).
"""

from collections import namedtuple

from .i18n import N_, _
from .tokenize import as_int

EQUIPMENT_INDEX = 28

SLOT_NAMES = (
    N_("Tête"), N_("Cou"), N_("Épaules"), N_("Chemise"), N_("Torse"), N_("Taille"),
    N_("Jambes"), N_("Pieds"), N_("Poignets"), N_("Mains"), N_("Anneau 1"), N_("Anneau 2"),
    N_("Bijou 1"), N_("Bijou 2"), N_("Dos"), N_("Main droite"), N_("Main gauche"),
    N_("Tabard"),
)
SHIRT, TABARD = 3, 17
MAIN_HAND, OFF_HAND = 15, 16
COUNTED = 16        # slots the average is taken over: all but the shirt and the tabard

Item = namedtuple("Item", "item_id ilvl enchants gems")


class Gear:
    """One player's equipment as the log wrote it."""

    __slots__ = ("items",)

    def __init__(self, items):
        self.items = tuple(items)

    def counted(self):
        """[(slot index, item)] for the sixteen slots the average covers."""
        return [(index, item) for index, item in enumerate(self.items)
                if index not in (SHIRT, TABARD)]

    @property
    def two_handed(self):
        """A main hand and nothing in the off hand: the game counts that weapon twice."""
        return (len(self.items) > OFF_HAND and self.items[MAIN_HAND].item_id
                and not self.items[OFF_HAND].item_id)

    @property
    def average(self):
        """The equipped item level, as the game computes it: the sixteen slots added up
        (a two-hander counted in both hands) and divided by sixteen. An empty slot counts
        as zero, so a missing piece lowers it, as in the game."""
        total = sum(item.ilvl for _index, item in self.counted())
        if self.two_handed:
            total += self.items[MAIN_HAND].ilvl
        return total / float(COUNTED)

    def empty_slots(self):
        """Slot indexes of the sixteen with nothing in them (the off hand of a two-hander
        is not empty: that weapon fills both)."""
        return [index for index, item in self.counted()
                if not item.item_id and not (index == OFF_HAND and self.two_handed)]

    def worn(self):
        """[(slot index, item)] for what is actually there, shirt and tabard included."""
        return [(index, item) for index, item in enumerate(self.items) if item.item_id]


def _ints(value):
    return [as_int(part, 0) for part in value] if isinstance(value, list) else []


def parse(fields):
    """A `Gear` from a COMBATANT_INFO line's fields, or None when it carries none.

    None for a line too short, an equipment field that is not a list, or fewer than 17
    entries: a layout this reader has not measured is not guessed at.
    """
    if len(fields) <= EQUIPMENT_INDEX or not isinstance(fields[EQUIPMENT_INDEX], list):
        return None
    raw = fields[EQUIPMENT_INDEX]
    if len(raw) < len(SLOT_NAMES) - 1:
        return None
    items = []
    for entry in raw[:len(SLOT_NAMES)]:
        if not isinstance(entry, list) or len(entry) < 2:
            items.append(Item(0, 0, (), ()))
            continue
        enchants = tuple(value for value in _ints(entry[2] if len(entry) > 2 else []) if value)
        gem_fields = _ints(entry[4] if len(entry) > 4 else [])
        gems = tuple(value for value in gem_fields[::2] if value)     # id, level, id, level...
        items.append(Item(as_int(entry[0], 0), as_int(entry[1], 0), enchants, gems))
    while len(items) < len(SLOT_NAMES):
        items.append(Item(0, 0, (), ()))
    if not any(item.item_id for item in items):
        return None
    return Gear(items)


def slot_label(index):
    """The slot's name, with a note on the two the game's average leaves out."""
    name = _(SLOT_NAMES[index])
    return name + _(" (non compté)") if index in (SHIRT, TABARD) else name
