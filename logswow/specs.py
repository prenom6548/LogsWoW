# SPDX-License-Identifier: AGPL-3.0-or-later
"""Specialization ids, so the report can say who tanked and who healed.

`COMBATANT_INFO` writes the player's current specialization id as its
26th field. The ids below are the public, stable enumeration the game
has used since Legion; they are facts about the client, in the same way
a field position is, and nothing here is copied from anyone's code.

**An id this table does not know is printed as a number, never guessed.**
That is how 1480 was handled until the owner named it and the log itself
supported the identification; see the comment beside it for which part of
that entry is measured and which part is theirs. The next unknown id gets
the same treatment: "spe 1481", and no invented name.
"""

TANK = "tank"
HEAL = "soigneur"
DPS = "dps"

# id -> (class, specialization, role)
SPECS = {
    250: ("Chevalier de la mort", "Sang", TANK),
    251: ("Chevalier de la mort", "Givre", DPS),
    252: ("Chevalier de la mort", "Impie", DPS),
    577: ("Chasseur de démons", "Dévastation", DPS),
    581: ("Chasseur de démons", "Vengeance", TANK),
    # Added 2026-09-18 from the owner's own log, with each part of it
    # resting on something different:
    #   class  -- measured. The player casts "Planer" (Glide) and
    #             "Ebranlement" (Disrupt), which no other class has, plus
    #             "Fragment d'ame" and "Devorer".
    #   name   -- the owner's identification, offered as "potentiellement"
    #             and kept as theirs rather than presented as verified.
    #   role   -- measured. Top damage in three fights of four, never the
    #             most-hit player, healing negligible.
    1480: ("Chasseur de démons", "Dévoration", DPS),
    102: ("Druide", "Équilibre", DPS),
    103: ("Druide", "Farouche", DPS),
    104: ("Druide", "Gardien", TANK),
    105: ("Druide", "Restauration", HEAL),
    1467: ("Évocateur", "Dévastation", DPS),
    1468: ("Évocateur", "Préservation", HEAL),
    1473: ("Évocateur", "Augmentation", DPS),
    253: ("Chasseur", "Maîtrise des bêtes", DPS),
    254: ("Chasseur", "Précision", DPS),
    255: ("Chasseur", "Survie", DPS),
    62: ("Mage", "Arcanes", DPS),
    63: ("Mage", "Feu", DPS),
    64: ("Mage", "Givre", DPS),
    268: ("Moine", "Maître brasseur", TANK),
    269: ("Moine", "Marche-vent", DPS),
    270: ("Moine", "Tisse-brume", HEAL),
    65: ("Paladin", "Sacré", HEAL),
    66: ("Paladin", "Protection", TANK),
    70: ("Paladin", "Vindicte", DPS),
    256: ("Prêtre", "Discipline", HEAL),
    257: ("Prêtre", "Sacré", HEAL),
    258: ("Prêtre", "Ombre", DPS),
    259: ("Voleur", "Assassinat", DPS),
    260: ("Voleur", "Hors-la-loi", DPS),
    261: ("Voleur", "Finesse", DPS),
    262: ("Chaman", "Élémentaire", DPS),
    263: ("Chaman", "Amélioration", DPS),
    264: ("Chaman", "Restauration", HEAL),
    265: ("Démoniste", "Affliction", DPS),
    266: ("Démoniste", "Démonologie", DPS),
    267: ("Démoniste", "Destruction", DPS),
    71: ("Guerrier", "Armes", DPS),
    72: ("Guerrier", "Fureur", DPS),
    73: ("Guerrier", "Protection", TANK),
}

# Where COMBATANT_INFO keeps it. Measured rather than assumed: across 121
# lines from two real logs the id sits at index 25 in 118 of them, and
# the three that "matched" elsewhere were ordinary stat values that
# happen to equal a spec id -- which is exactly why this reads one fixed
# position instead of scanning for something plausible.
SPEC_ID_INDEX = 25


def describe(spec_id):
    """-> (class, specialization, role). Unknown ids keep their number."""
    if not spec_id:
        return ("", "", "")
    known = SPECS.get(spec_id)
    if known:
        return known
    return ("", "spe %d" % spec_id, "")


def role_of(spec_id):
    """tank, soigneur, dps -- or '' for an id this table does not know."""
    return describe(spec_id)[2]


def label_of(spec_id):
    """'Moine Maître brasseur', or 'spe 1480' for one this table lacks."""
    class_name, spec_name, _role = describe(spec_id)
    return (" ".join(piece for piece in (class_name, spec_name) if piece)).strip()
