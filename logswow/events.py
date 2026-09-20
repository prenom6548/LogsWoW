"""Turning a field list into a typed event.

The log's own scheme is prefix + suffix: SPELL_DAMAGE is the SPELL
prefix (spellId, spellName, spellSchool) and the _DAMAGE suffix, around
eight base fields naming the source and the destination. With Advanced
Combat Logging on, a block of extra fields describing the unit sits
between the two.

**Nothing about the widths is hardcoded, because every guess was wrong.**
The documentation this package was first written from says the advanced
block holds seventeen fields and that the damage suffix starts with
amount, overkill. Two real logs from a 12.1.0 client say otherwise, and
say it identically across 37,240 samples:

    advanced block          19 fields, not 17
    damage suffix           amount, baseAmount, overkill, school, ...
    SWING_DAMAGE            10 suffix fields
    SPELL_DAMAGE            11, the last one a string tag: ST or AOE
    heal suffix             amount, baseAmount, overhealing, absorbed, critical

So `Layout` is *measured* from the file being read (see parse.py), and
the readers below take their offsets from it. A file written by an older
client, without the baseAmount field, shifts every offset by one and is
read correctly without changing a line of this module.
"""

from .tokenize import as_bool, as_int, looks_like_guid

# What the documentation describes, used only until the file says better.
DEFAULT_ADVANCED_WIDTH = 19

# Why a line could not be placed. These are shown to the reader by
# `diagnose`, so they are in French like the rest of the interface;
# UNKNOWN_SUBEVENT is also a sentinel the reader compares against, so it
# is a constant rather than a repeated literal.
UNKNOWN_SUBEVENT = "evenement inconnu"
MISSING_BASE_FIELDS = "champs de base manquants"

_PREFIXES = (
    ("SPELL_PERIODIC", 3),
    ("SPELL_BUILDING", 3),
    ("SPELL_EMPOWER", 3),
    ("SPELL", 3),
    ("RANGE", 3),
    ("SWING", 0),
    ("ENVIRONMENTAL", 1),
)

# Suffix name -> the field counts it has been seen in. A count is only
# used to decide where the advanced block ends, never to name a field.
_SUFFIXES = {
    "_DAMAGE": (9, 10, 11, 12),
    "_DAMAGE_LANDED": (9, 10, 11, 12),
    "_DAMAGE_SUPPORT": (10, 11, 12, 13),
    "_DAMAGE_LANDED_SUPPORT": (10, 11, 12, 13),
    "_MISSED": (1, 2, 3, 4, 5, 6),
    "_HEAL": (4, 5, 6),
    "_HEAL_SUPPORT": (5, 6, 7),
    "_HEAL_ABSORBED": (5, 6, 9, 10),
    "_ENERGIZE": (2, 3, 4),
    "_DRAIN": (3, 4, 5),
    "_LEECH": (3, 4, 5),
    "_INTERRUPT": (3,),
    "_DISPEL_FAILED": (3,),
    "_DISPEL": (4,),
    "_STOLEN": (4,),
    "_EXTRA_ATTACKS": (1,),
    "_AURA_APPLIED_DOSE": (2, 3),
    "_AURA_REMOVED_DOSE": (2, 3),
    "_AURA_APPLIED": (1, 2, 3),
    "_AURA_REMOVED": (1, 2, 3),
    "_AURA_REFRESH": (1, 2, 3),
    "_AURA_BROKEN_SPELL": (4,),
    "_AURA_BROKEN": (1,),
    "_CAST_START": (0,),
    "_CAST_SUCCESS": (0,),
    "_CAST_FAILED": (1,),
    "_INSTAKILL": (0, 1),
    "_DURABILITY_DAMAGE_ALL": (0,),
    "_DURABILITY_DAMAGE": (0,),
    "_CREATE": (0,),
    "_SUMMON": (0,),
    "_RESURRECT": (0,),
    "_EMPOWER_START": (0,),
    "_EMPOWER_END": (1,),
    "_EMPOWER_INTERRUPT": (1,),
    "_SHIELD": (9, 10, 11, 12),
    "_SHIELD_MISSED": (1, 2, 3),
    "_SPLIT": (9, 10, 11, 12),
}

# No source/dest pair in the usual place, or no scheme at all.
SPECIAL_EVENTS = frozenset(
    {
        "COMBAT_LOG_VERSION",
        "ENCOUNTER_START",
        "ENCOUNTER_END",
        "ZONE_CHANGE",
        "MAP_CHANGE",
        "CHALLENGE_MODE_START",
        "CHALLENGE_MODE_END",
        "COMBATANT_INFO",
        "WORLD_MARKER_PLACED",
        "WORLD_MARKER_REMOVED",
        "EMOTE",
        "ARENA_MATCH_START",
        "ARENA_MATCH_END",
        # A Brewmaster's staggered damage. Real logs carry these, and they
        # have no source/dest pair at all:
        #   STAGGER_CLEAR,<playerGUID>,<amount>
        #   STAGGER_PREVENTED,<playerGUID>,<spellId>,<amount>
        "STAGGER_CLEAR",
        "STAGGER_PREVENTED",
    }
)

# Base source/dest pair, then fields that follow no prefix/suffix scheme.
BARE_EVENTS = frozenset(
    {
        "UNIT_DIED",
        "UNIT_DESTROYED",
        "UNIT_DISSIPATES",
        "PARTY_KILL",
        "ENCHANT_APPLIED",
        "ENCHANT_REMOVED",
        "SPELL_ABSORBED",
    }
)

FLAG_REACTION_FRIENDLY = 0x00000010
FLAG_REACTION_HOSTILE = 0x00000040
FLAG_TYPE_PLAYER = 0x00000400
FLAG_TYPE_PET = 0x00001000
FLAG_TYPE_GUARDIAN = 0x00002000


def _hex(value):
    if isinstance(value, str) and value.startswith("0x"):
        try:
            return int(value, 16)
        except ValueError:
            return 0
    return as_int(value, 0)


class Layout:
    """How this particular file lays its fields out.

    `advanced_width` and `has_base_amount` are measured from the file's
    own lines rather than assumed; `diagnose` prints both, with the
    evidence behind them, so a future client change shows up as a
    number instead of as quietly wrong damage.
    """

    __slots__ = ("advanced_width", "has_base_amount", "hide_caster", "evidence")

    def __init__(self, advanced_width=DEFAULT_ADVANCED_WIDTH, has_base_amount=True,
                 hide_caster=False, evidence=None):
        self.advanced_width = advanced_width
        self.has_base_amount = has_base_amount
        self.hide_caster = hide_caster
        self.evidence = evidence or {}

    @property
    def shift(self):
        """0 or 1: how far the baseAmount field pushes everything along."""
        return 1 if self.has_base_amount else 0


DEFAULT_LAYOUT = Layout()


class Actor:
    """One side of an event."""

    __slots__ = ("guid", "name", "flags", "raid_flags")

    def __init__(self, guid, name, flags, raid_flags):
        self.guid = guid if isinstance(guid, str) else ""
        self.name = name if isinstance(name, str) else ""
        self.flags = flags
        self.raid_flags = raid_flags

    @property
    def is_player(self):
        return self.guid.startswith("Player-") or bool(self.flags & FLAG_TYPE_PLAYER)

    @property
    def is_pet(self):
        return self.guid.startswith(("Pet-", "Vehicle-")) or bool(
            self.flags & (FLAG_TYPE_PET | FLAG_TYPE_GUARDIAN)
        )

    @property
    def is_friendly(self):
        return bool(self.flags & FLAG_REACTION_FRIENDLY)

    @property
    def is_hostile(self):
        return bool(self.flags & FLAG_REACTION_HOSTILE)

    @property
    def short_name(self):
        """'Ardoise-Dalaran-EU' -> 'Ardoise'."""
        return self.name.split("-", 1)[0] if self.name else ""

    @property
    def display_name(self):
        """The name to *write down*: a player without their realm.

        Only a player's name carries a realm, and only a player's name
        may be split on a dash -- a creature called "Garde-fou" would
        lose half of itself. Every name the analysis stores for the
        report goes through here, so a realm cannot reach the page from
        a death chain, a healing target or a PvP opponent's panel.
        """
        return self.short_name if self.is_player else self.name

    def __repr__(self):
        return "Actor(%r)" % (self.name,)


NO_ONE = Actor("", "", 0, 0)


class Advanced:
    """The extra fields Advanced Combat Logging writes about a unit.

    Read from both ends, because that is where the stability is: the
    first eight fields and the last nine have never moved, and every
    field Blizzard has added went in between them. A 17-field block and
    a 19-field block both come out right.
    """

    __slots__ = (
        "info_guid", "owner_guid", "current_hp", "max_hp", "attack_power",
        "spell_power", "armor", "absorb", "power_type", "current_power",
        "max_power", "power_cost", "position_x", "position_y", "ui_map_id",
        "facing", "level",
    )

    def __init__(self, fields):
        count = len(fields)

        def head(index, default=""):
            return fields[index] if 0 <= index < count else default

        def tail(offset, default=""):
            index = count + offset
            return fields[index] if 0 <= index < count else default

        self.info_guid = head(0) if isinstance(head(0), str) else ""
        self.owner_guid = head(1) if isinstance(head(1), str) else ""
        self.current_hp = as_int(head(2), 0)
        self.max_hp = as_int(head(3), 0)
        self.attack_power = as_int(head(4), 0)
        self.spell_power = as_int(head(5), 0)
        self.armor = as_int(head(6), 0)
        self.absorb = as_int(head(7), 0)
        self.power_type = tail(-9)
        self.current_power = tail(-8)
        self.max_power = tail(-7)
        self.power_cost = tail(-6)
        self.position_x = tail(-5)
        self.position_y = tail(-4)
        self.ui_map_id = as_int(tail(-3), 0)
        self.facing = tail(-2)
        self.level = as_int(tail(-1), 0)

    @property
    def health_fraction(self):
        if self.max_hp > 0:
            return max(0.0, min(1.0, self.current_hp / self.max_hp))
        return None


class Event:
    """One parsed line."""

    __slots__ = (
        "ts", "subevent", "source", "dest", "spell_id", "spell_name",
        "spell_school", "advanced", "suffix", "suffix_kind", "support_guid",
        "shift", "fields", "line_number", "mismatch",
    )

    def __init__(self, ts, subevent, line_number):
        self.ts = ts
        self.subevent = subevent
        self.line_number = line_number
        self.source = NO_ONE
        self.dest = NO_ONE
        self.spell_id = 0
        self.spell_name = ""
        self.spell_school = 0
        self.advanced = None
        self.suffix = []
        self.suffix_kind = ""
        self.support_guid = ""
        self.shift = 1
        self.fields = []
        self.mismatch = None

    DAMAGE_KINDS = frozenset({"_DAMAGE", "_DAMAGE_LANDED", "_SHIELD", "_SPLIT"})
    HEAL_KINDS = frozenset({"_HEAL"})

    # -- suffix readers ---------------------------------------------------
    # Offsets are counted from the front and shifted by the measured
    # baseAmount field. Every reader returns a harmless zero when the
    # suffix is missing or a size nobody has seen: one odd line out of ten
    # million must not stop a report from being produced.

    def _at(self, index, default=""):
        if 0 <= index < len(self.suffix):
            return self.suffix[index]
        return default

    @property
    def amount(self):
        return as_int(self._at(0), 0)

    @property
    def base_amount(self):
        """The second number on a damage or heal, when the client writes one.

        **It is not "the hit before mitigation", whatever it gets called.**
        Measured across a real key: on non-critical hits `amount` is 1.03
        times this field, and on critical ones 2.59 times it -- so it is
        the amount before the critical multiplier and before some
        damage bonuses, and a hit that *landed* is routinely larger than
        it. Dividing one by the other gives a number that looks like a
        mitigation percentage and is not one: on the same key it said a
        tank mitigated 71.6% where an outside reference said 68.3%, and
        the agreement is a coincidence of two unrelated quantities.

        Nothing in this package computes with it. It is read because its
        *position* is what tells `detect_layout` where the overkill
        marker sits.
        """
        return as_int(self._at(1), 0) if self.shift else 0

    @property
    def overkill(self):
        """Wasted damage on a killing blow. -1 when the hit did not kill."""
        if self.suffix_kind not in self.DAMAGE_KINDS:
            return 0
        return as_int(self._at(1 + self.shift), 0)

    @property
    def absorbed(self):
        if self.suffix_kind not in self.DAMAGE_KINDS:
            return 0
        return as_int(self._at(5 + self.shift), 0)

    @property
    def is_critical(self):
        if self.suffix_kind in self.DAMAGE_KINDS:
            return as_bool(self._at(6 + self.shift))
        if self.suffix_kind in self.HEAL_KINDS:
            return as_bool(self._at(3 + self.shift))
        return False

    @property
    def damage_tag(self):
        """'ST' or 'AOE' -- a Midnight-era marker on spell damage."""
        if self.suffix_kind not in self.DAMAGE_KINDS or not self.suffix:
            return ""
        last = self.suffix[-1]
        return last if isinstance(last, str) and last in ("ST", "AOE") else ""

    @property
    def overhealing(self):
        if self.suffix_kind not in self.HEAL_KINDS:
            return 0
        return as_int(self._at(1 + self.shift), 0)

    @property
    def healing_absorbed(self):
        if self.suffix_kind not in self.HEAL_KINDS:
            return 0
        return as_int(self._at(2 + self.shift), 0)

    @property
    def effective_healing(self):
        return max(0, self.amount - self.overhealing - self.healing_absorbed)

    @property
    def miss_type(self):
        value = self._at(0)
        return value if isinstance(value, str) else ""

    @property
    def extra_spell_id(self):
        """The interrupted / dispelled / stolen spell."""
        return as_int(self._at(0), 0)

    @property
    def extra_spell_name(self):
        value = self._at(1)
        return value if isinstance(value, str) else ""

    @property
    def aura_type(self):
        value = self._at(0)
        return value if isinstance(value, str) else ""

    @property
    def absorb_caster(self):
        """SPELL_ABSORBED: (guid, name) of whoever's shield ate the hit.

        Measured on a real 12.1.0 log, in both widths the event comes in:
        the caster sits ten and nine fields from the end, whether or not
        the attacker's own spell is named. That is the same tail anchor
        `absorbed_amount` uses, for the same reason.
        """
        if self.subevent != "SPELL_ABSORBED":
            return "", ""
        guid = self._at(len(self.suffix) - 10)
        name = self._at(len(self.suffix) - 9)
        return (guid if isinstance(guid, str) else "",
                name if isinstance(name, str) else "")

    @property
    def absorb_spell(self):
        """SPELL_ABSORBED: (id, name) of the shield, not of the hit.

        The event carries two spells -- the attacker's, when the wide
        form names it, and the shield's -- and the ordinary `spell_id`
        is neither: SPELL_ABSORBED has no prefix at all, so it reads 0.
        Banking a shield under that id put every shield in one row
        called "Attaque". Tail-anchored like the rest of this event.
        """
        if self.subevent != "SPELL_ABSORBED":
            return 0, ""
        name = self._at(len(self.suffix) - 5)
        return (as_int(self._at(len(self.suffix) - 6), 0),
                name if isinstance(name, str) else "")

    @property
    def absorbed_amount(self):
        """SPELL_ABSORBED: how much a shield ate. Tail-anchored.

        Two layouts exist, with and without the attacker's spell, and
        both end on absorbedAmount, totalAmount, critical.
        """
        if self.subevent != "SPELL_ABSORBED":
            return 0
        return as_int(self._at(len(self.suffix) - 3), 0)

    def __repr__(self):
        return "Event(%s %s -> %s)" % (self.subevent, self.source.name, self.dest.name)


def decompose(subevent):
    """'SPELL_PERIODIC_DAMAGE' -> ('SPELL_PERIODIC', 3, '_DAMAGE', counts)."""
    for prefix, prefix_n in _PREFIXES:
        if not subevent.startswith(prefix):
            continue
        remainder = subevent[len(prefix) :]
        if not remainder:
            continue
        best = None
        for suffix, counts in _SUFFIXES.items():
            if remainder == suffix and (best is None or len(suffix) > len(best[0])):
                best = (suffix, counts)
        if best:
            return prefix, prefix_n, best[0], best[1]
    for suffix in ("_SHIELD_MISSED", "_SHIELD", "_SPLIT"):
        if subevent == "DAMAGE" + suffix:
            return "SPELL", 3, suffix, _SUFFIXES[suffix]
    return None


def resolve_layout(remainder, prefix_n, suffix_counts, advanced_width):
    """Split what follows the base fields into (prefix, advanced, suffix).

    Returns a fourth value: why the split is uncertain, or None when the
    arithmetic came out exact.
    """
    available = len(remainder) - prefix_n
    if available < 0:
        return (
            remainder,
            None,
            [],
            "ligne trop courte : %d champs pour un prefixe de %d"
            % (len(remainder), prefix_n),
        )
    prefix = remainder[:prefix_n]
    rest = remainder[prefix_n:]

    for count in suffix_counts:
        if available == count + advanced_width:
            return prefix, rest[:advanced_width], rest[advanced_width:], None
    for count in suffix_counts:
        if available == count:
            return prefix, None, rest, None

    note = ("nombre de champs inattendu : %d apres le prefixe, attendu %s, "
            "ou cela +%d") % (
        available,
        " / ".join(str(count) for count in suffix_counts) or "0",
        advanced_width,
    )
    smallest = min(suffix_counts) if suffix_counts else 0
    if available >= smallest + advanced_width:
        return prefix, rest[:advanced_width], rest[advanced_width:], note
    return prefix, None, rest, note


def build_event(ts, fields, line_number, layout=DEFAULT_LAYOUT):
    """Fields (already split) -> Event. Never raises."""
    subevent = fields[0] if fields else ""
    event = Event(ts, subevent, line_number)
    event.fields = fields
    event.shift = layout.shift

    if subevent in SPECIAL_EVENTS:
        return event

    offset = 2 if layout.hide_caster else 1
    base = fields[offset : offset + 8]
    if len(base) < 8:
        event.mismatch = MISSING_BASE_FIELDS
        return event
    event.source = Actor(base[0], base[1], _hex(base[2]), _hex(base[3]))
    event.dest = Actor(base[4], base[5], _hex(base[6]), _hex(base[7]))
    remainder = fields[offset + 8 :]

    if subevent in BARE_EVENTS:
        event.suffix = remainder
        return event

    scheme = decompose(subevent)
    if scheme is None:
        event.mismatch = UNKNOWN_SUBEVENT
        event.suffix = remainder
        return event

    _, prefix_n, suffix_name, suffix_counts = scheme
    prefix, advanced, suffix, note = resolve_layout(
        remainder, prefix_n, suffix_counts, layout.advanced_width
    )
    if prefix_n == 3 and len(prefix) == 3:
        event.spell_id = as_int(prefix[0], 0)
        event.spell_name = prefix[1] if isinstance(prefix[1], str) else ""
        event.spell_school = _hex(prefix[2])
    elif prefix_n == 1 and len(prefix) == 1:
        event.spell_name = prefix[0] if isinstance(prefix[0], str) else ""
    elif prefix_n == 0:
        event.spell_name = "Attaque"  # SWING_*, which carries no spell
    if advanced is not None:
        event.advanced = Advanced(advanced)

    # The *_SUPPORT variants append the supporting player's GUID. Checked
    # rather than assumed: neither real log read so far contains one.
    if suffix_name.endswith("_SUPPORT") and suffix and looks_like_guid(suffix[-1]):
        event.support_guid = suffix[-1]
        suffix = suffix[:-1]
        suffix_name = suffix_name[: -len("_SUPPORT")]

    event.suffix = suffix
    event.suffix_kind = suffix_name
    event.mismatch = note
    return event
