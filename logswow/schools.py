# SPDX-License-Identifier: AGPL-3.0-or-later
"""Schools of damage: physical, magic, or both at once.

Every damage line carries the school of what it dealt, as a bit mask:
1 physical, 2 holy, 4 fire, 8 nature, 16 frost, 32 shadow, 64 arcane,
and any sum of them for a blow that is several at once (Shadowflame is
36, Chaos 127). Measured on the owner's logs (2026-09-27): every melee
hit is 1 (33,335 of 33,335), and the line's school equals the spell's
own on 343,013 lines of 343,016 in a dungeon -- where they differ, the
line says what was actually dealt, so the line is what is read.

A mask with the physical bit and another one is neither physical nor
magic, and is counted apart as "mixte" rather than forced into either.
"""

from .i18n import N_, _

PHYSICAL = 1
NAMES = ((1, N_("Physique")), (2, N_("Sacré")), (4, N_("Feu")), (8, N_("Nature")),
         (16, N_("Givre")), (32, N_("Ombre")), (64, N_("Arcane")))
KINDS = ("physique", "magique", "mixte")


def kind(mask):
    """'physique', 'magique', 'mixte', or '' when the file gave no school."""
    if mask <= 0 or mask > 127:
        return ""
    if mask == PHYSICAL:
        return "physique"
    return "mixte" if mask & PHYSICAL else "magique"


def name(mask):
    """'Ombre', 'Ombre + Feu' -- the schools a mask holds, in French."""
    parts = [_(label) for bit, label in NAMES if mask & bit]
    return " + ".join(parts) if parts and 0 < mask <= 127 else _("école inconnue")


def by_kind(by_school):
    """{mask: amount} -> {'physique': .., 'magique': .., 'mixte': .., '': ..}."""
    totals = {}
    for mask, amount in by_school.items():
        key = kind(mask)
        totals[key] = totals.get(key, 0) + amount
    return totals
