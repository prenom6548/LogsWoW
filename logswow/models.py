"""The ledgers one segment keeps: what the analysis adds up *into*.

Split out of analysis.py, which had grown to hold both the data and
every rule for filling it. These classes know how to store and read
back a number; `SegmentAnalysis` alone decides which event feeds which
ledger. Nothing here reads a line of the log.
"""

from collections import deque

# How many hits and heals a death chain keeps, per player.
DEATH_CHAIN_LENGTH = 12

# How many enemy units a single pull bothers to name.
PULL_LABEL_UNITS = 3

# One pull naming the same unit more than this many times is a memory
# guard, not a real pack: the count beside a name stops being exact
# above it. No real pull comes close.
MAX_UNITS_PER_NAME = 1000


class Ability:
    """One spell's contribution, on one side of one ledger."""

    __slots__ = (
        "spell_id", "name", "total", "hits", "crits", "targets", "overkill",
        "overheal", "biggest",
    )

    def __init__(self, spell_id, name):
        self.spell_id = spell_id
        self.name = name or "Attaque"
        self.total = 0
        self.hits = 0
        self.crits = 0
        # Who was on the other end, and for how much. A set only answered
        # "how many"; the report wants "on whom", which is the same data
        # for one more integer per name.
        self.targets = {}
        self.overkill = 0
        self.overheal = 0
        self.biggest = 0

    def add(self, amount, critical=False, target=None, overkill=0, overheal=0):
        """Bank one hit or heal: its amount, and on whom."""
        self.total += amount
        self.hits += 1
        if critical:
            self.crits += 1
        if amount > self.biggest:
            self.biggest = amount
        if target:
            # Bounded: a 20-minute key meets a lot of trash, and one
            # ability's list of victims is not worth unbounded memory.
            if target in self.targets or len(self.targets) < 80:
                self.targets[target] = self.targets.get(target, 0) + amount
        if overkill > 0:
            self.overkill += overkill
        if overheal > 0:
            self.overheal += overheal

    @property
    def overheal_rate(self):
        total = self.total + self.overheal
        return (self.overheal / total) if total else 0.0

    @property
    def crit_rate(self):
        return (self.crits / self.hits) if self.hits else 0.0

    @property
    def average(self):
        return (self.total / self.hits) if self.hits else 0

    def ranked_targets(self, limit=10):
        """[(name, amount)] of whom this ability landed on, largest first."""
        return sorted(self.targets.items(), key=lambda item: -item[1])[:limit]


class Enemy:
    """Every unit sharing a name, added together.

    Aggregating by name rather than by GUID is what makes this readable:
    a key meets thirty-two units called "Diablotin sauvage" and nobody
    wants thirty-two panels. A boss has one unit and one name, so the
    same treatment gives exactly what is wanted there too.
    """

    __slots__ = (
        "name", "units", "damage_done", "damage_taken", "deaths", "casts",
        "damage_by_ability", "taken_by_ability", "casts_by_spell",
    )

    def __init__(self, name):
        self.name = name
        self.units = set()
        self.damage_done = 0
        self.damage_taken = 0
        self.deaths = 0
        self.casts = 0
        self.damage_by_ability = {}
        self.taken_by_ability = {}
        self.casts_by_spell = {}

    @property
    def count(self):
        return len(self.units)


class CombatBlock:
    """One pull: a stretch of fighting with no long silence inside it.

    A boss encounter is one of these. A Mythic+ key is a few dozen, which
    is the whole reason this exists -- "what did we actually pull" is a
    question the file can answer and a single 20-minute total cannot.
    """

    __slots__ = (
        "start_ts", "end_ts", "damage_done", "damage_boss", "damage_taken",
        "deaths", "enemies", "encounters",
    )

    def __init__(self, start_ts):
        self.start_ts = start_ts
        self.end_ts = start_ts
        self.damage_done = 0
        self.damage_boss = 0        # the part of damage_done that hit a boss
        self.damage_taken = 0
        self.deaths = 0
        self.enemies = {}
        # (encounter name, success) for each boss encounter this pull
        # overlapped, as the segment's own markers bound it.
        self.encounters = []

    @property
    def damage_trash(self):
        return self.damage_done - self.damage_boss

    def has_boss(self, boss_names):
        """True when this pull overlapped a boss encounter or hit a unit named as one."""
        return bool(self.encounters) or any(
            canon(name) in boss_names for name in self.enemies)

    @property
    def outcome(self):
        """True if a boss was killed in this pull, False if every boss
        encounter in it was lost, None when the file does not say."""
        results = [success for _name, success in self.encounters]
        if any(results):
            return True
        if results and all(success is False for success in results):
            return False
        return None

    def _unnamed_encounters(self, bosses):
        """Encounters no unit in this pull is named after (a council)."""
        named = {canon(name) for name, _guids in bosses}
        seen = []
        for name, _success in self.encounters:
            if canon(name) not in named and name not in seen:
                seen.append(name)
        return seen

    def note_enemy(self, guid, name):
        """Remember one unit met in this pull, grouped by name, within bounds."""
        # "nil" is what the client writes for a unit with no name, which
        # is not an enemy worth listing in a pull.
        if not name or name == "nil":
            return
        seen = self.enemies.get(name)
        if seen is None:
            if len(self.enemies) >= 24:
                return
            seen = set()
            self.enemies[name] = seen
        if len(seen) < MAX_UNITS_PER_NAME:
            seen.add(guid)

    @property
    def duration_ms(self):
        return max(0, self.end_ts - self.start_ts)

    def label(self, limit=PULL_LABEL_UNITS, boss_names=frozenset()):
        """'Voyou de l'allee x4, Chaman ensorcele x2', bosses first.

        Trash is often dragged onto a boss and killed there, so a pull
        that contains a boss is named after it before anything else,
        however many trash units came along.
        """
        ranked = sorted(self.enemies.items(), key=lambda item: -len(item[1]))
        bosses = [item for item in ranked if canon(item[0]) in boss_names]
        others = [item for item in ranked if canon(item[0]) not in boss_names]
        pieces = list(self._unnamed_encounters(bosses))
        for name, guids in bosses:
            pieces.append("%s x%d" % (name, len(guids)) if len(guids) > 1 else name)
        room = max(0, limit - len(bosses))
        for name, guids in others[:room]:
            pieces.append("%s x%d" % (name, len(guids)) if len(guids) > 1 else name)
        if len(others) > room:
            pieces.append("et %d autre(s)" % (len(others) - room))
        return ", ".join(pieces)

    def boss_label(self, boss_names):
        """Only the bosses in this pull, or ''."""
        names = [name for name in self.enemies if canon(name) in boss_names]
        extra = self._unnamed_encounters([(name, None) for name in names])
        return ", ".join(extra + sorted(names))


class Player:
    """One friendly actor's whole ledger for one segment."""

    __slots__ = (
        "guid", "name", "damage_done", "healing_done", "overhealing",
        "damage_taken", "absorbed_taken", "deaths", "interrupts", "dispels",
        "casts", "damage_by_ability", "healing_by_ability", "taken_by_ability",
        "casts_by_ability", "healing_to", "interrupted_spells", "dispelled_spells",
        "spec_id", "auras_gained", "auras_applied", "casts_by_spell",
        "_gained_until", "_applied_until", "absorb_done", "pet_casts",
        "absorb_by_ability", "pet_damage_taken",
        "damage_to_bosses",
        "first_cast_ts", "last_cast_ts", "downtime_ms",
        "longest_gaps", "recent", "hp_fraction", "min_hp_fraction", "max_hp",
        "active_ms", "died_at", "label", "cast_log", "cast_log_full", "triggered",
    )

    def __init__(self, guid, name):
        self.guid = guid
        self.name = name
        self.damage_done = 0
        self.healing_done = 0
        self.overhealing = 0
        self.damage_taken = 0
        self.absorbed_taken = 0
        self.deaths = 0
        self.interrupts = 0
        self.dispels = 0
        self.casts = 0
        # Casts by this player's own summons, included in `casts` above.
        self.pet_casts = 0
        # Damage this player's shields prevented on somebody. Warcraft
        # Logs adds this into "healing"; it is kept apart here, because
        # the file reports them as two different things and a shield that
        # ate 90M is worth seeing as itself.
        self.absorb_done = 0
        self.absorb_by_ability = {}
        # What this player's summons took, kept out of `damage_taken`.
        # A mage whose elemental is being chewed on has not taken that
        # damage: nobody healed them for it, their health never moved,
        # and on one real key it was 12% of what the report showed them
        # as having survived.
        self.pet_damage_taken = 0
        self.damage_by_ability = {}
        self.healing_by_ability = {}
        self.taken_by_ability = {}
        self.casts_by_ability = {}
        self.healing_to = {}
        self.interrupted_spells = {}
        self.dispelled_spells = {}
        self.spec_id = 0
        self.damage_to_bosses = 0
        # (spell, who put it there, BUFF/DEBUFF) -> milliseconds
        self.auras_gained = {}
        # (spell, on whom) -> milliseconds
        self.auras_applied = {}
        # The far end of what each of those has already counted, so two
        # instances of one aura running at the same time are counted once.
        self._gained_until = {}
        self._applied_until = {}
        self.casts_by_spell = {}
        self.first_cast_ts = None
        self.last_cast_ts = None
        self.downtime_ms = 0
        self.longest_gaps = []
        self.recent = deque(maxlen=DEATH_CHAIN_LENGTH)
        self.hp_fraction = None
        self.min_hp_fraction = None
        self.max_hp = 0
        self.active_ms = 0
        self.died_at = []
        # The name the page shows: the realm-less name, made unique
        # within the segment ("Tisane", "Tisane (2)") by SegmentAnalysis.
        self.label = ""
        # Every cast in order: (ts, spell id, name, paid, from a summon).
        # Bounded by castorder.MAX_CAST_LOG; `cast_log_full` says it was.
        self.cast_log = []
        self.cast_log_full = False
        # Spell ids castorder.classify_triggered reads as not pressed.
        self.triggered = frozenset()

    @property
    def short_name(self):
        if self.label:
            return self.label
        return self.name.split("-", 1)[0] if self.name else self.guid

    @property
    def overheal_rate(self):
        total = self.healing_done + self.overhealing
        return (self.overhealing / total) if total else 0.0


def canon(name):
    """A name as the log writes it on a unit, whichever apostrophe it used.

    ENCOUNTER_START writes "Xathuux l\u2019Annihilateur" with a curly
    apostrophe and the unit's own events write "Xathuux l'Annihilateur"
    with a straight one, on the same client in the same file. Matching
    the two is what tells a boss pull from the trash funnelled into it,
    so every comparison of names goes through here.
    """
    if not name:
        return ""
    return name.replace("\u2019", "'").replace("\u2018", "'").strip()


def _bucket(store, spell_id, name):
    key = (spell_id, name or "Attaque")
    ability = store.get(key)
    if ability is None:
        ability = Ability(spell_id, name)
        store[key] = ability
    return ability
