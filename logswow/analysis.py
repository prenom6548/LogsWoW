"""What the events add up to, accumulated as they stream past.

Nothing here keeps the events themselves. Each segment holds counters,
a handful of bounded ring buffers for the death chains, and one bucket
array for the timeline, so the memory a 240 MB file needs is set by how
many players and spells appear in a fight, not by how long the fight was.

What this can and cannot answer is worth being plain about:

  * "what happened, and who did what"  -- yes, this is arithmetic on the
    file, and it is what the tables below are.
  * "why did we wipe"  -- partly. Damage taken per ability, who was hit,
    who died to what, and the chain of the last hits before each death
    are all in the file. Which of those were *avoidable* is boss
    knowledge this package does not have and does not pretend to.
  * "how do I compare to other players"  -- no, and not by accident: it
    would need everyone else's logs, which is the one thing a local tool
    on your own machine does not have.
"""

from collections import deque

from .specs import SPEC_ID_INDEX
from .tokenize import as_int

DOWNTIME_THRESHOLD_MS = 2000
DEATH_CHAIN_LENGTH = 12
MAX_TIMELINE_BUCKETS = 400

# How long the group has to stop dealing and taking damage before what
# follows counts as a new pull. Six seconds is long enough to survive a
# ranged gap-close or a cast finishing after the last mob dies, and short
# enough to separate two trash packs in a Mythic+ key.
PULL_GAP_MS = 6000

# A "pull" worth a line has to be a meaningful share of the run. A real
# key produced two blocks of 7.9k and 14.1k damage against a 531M total:
# a dot finishing on something already dead, or a critter. One part in a
# thousand cuts those and leaves the smallest genuine pull (20M) two
# orders of magnitude clear.
MIN_PULL_SHARE = 0.001

# How many enemy units a single pull bothers to name.
PULL_LABEL_UNITS = 3

# An enemy the group has not touched for this long is no longer "engaged":
# it walked off, reset, or despawned without a UNIT_DIED, and it must stop
# weighing on the pooled health curve.
POOL_STALE_MS = 30000

# Bounds on the per-enemy health sampling, so a 20-minute key cannot grow
# without limit while it works out which unit was the main target.
MAX_TRACKED_ENEMIES = 40
KEEP_TRACKED_ENEMIES = 20
MAX_HP_SAMPLES = 400


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
        "taken_from_boss", "deaths", "enemies",
    )

    def __init__(self, start_ts):
        self.start_ts = start_ts
        self.end_ts = start_ts
        self.damage_done = 0
        self.damage_boss = 0        # the part of damage_done that hit a boss
        self.damage_taken = 0
        self.taken_from_boss = 0    # the part of damage_taken a boss dealt
        self.deaths = 0
        self.enemies = {}

    @property
    def damage_trash(self):
        return self.damage_done - self.damage_boss

    def has_boss(self, boss_names):
        return any(canon(name) in boss_names for name in self.enemies)

    def note_enemy(self, guid, name):
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
        pieces = []
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
        return ", ".join(sorted(names))


class Player:
    """One friendly actor's whole ledger for one segment."""

    __slots__ = (
        "guid", "name", "damage_done", "healing_done", "overhealing",
        "damage_taken", "absorbed_taken", "deaths", "interrupts", "dispels",
        "casts", "damage_by_ability", "healing_by_ability", "taken_by_ability",
        "casts_by_ability", "healing_to", "interrupted_spells", "dispelled_spells",
        "spec_id", "auras_gained", "auras_applied", "casts_by_spell",
        "damage_to_bosses",
        "first_cast_ts", "last_cast_ts", "downtime_ms",
        "longest_gaps", "recent", "hp_fraction", "min_hp_fraction", "max_hp",
        "active_ms", "died_at",
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

    @property
    def short_name(self):
        return self.name.split("-", 1)[0] if self.name else self.guid

    @property
    def realm(self):
        parts = self.name.split("-", 1)
        return parts[1] if len(parts) > 1 else ""

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


class SegmentAnalysis:
    """Accumulates one segment. `feed` per event, `finish` once."""

    def __init__(self, segment, pull_gap_ms=PULL_GAP_MS):
        self.segment = segment
        # Under a second, every dot tick would be its own pull.
        self.pull_gap_ms = max(1000, int(pull_gap_ms))
        self.players = {}
        self.pet_owner = {}
        self.enemy_damage_by_ability = {}  # what hit the group, raid-wide
        self.deaths = []
        self.first_ts = None
        self.last_ts = None
        self.total_damage = 0
        self.total_healing = 0
        self.aura_open = {}
        self.aura_uptime = {}
        # True once an aura could not be tracked for want of room; see
        # `_aura_close`, which stops inferring anything after that.
        self._aura_overflowed = False
        # Auras that were already up when the segment began, counted from
        # its first event because the file gives no earlier bound.
        self.auras_before_the_pull = 0
        self._inferred_auras = set()
        self.boss_hp = []
        self.boss_name = ""
        self.blocks = []
        self.dropped_pulls = 0
        # What became of the spells the enemy tried to cast. The file
        # answers this without any boss knowledge: a cast either reaches
        # its SPELL_CAST_SUCCESS or it does not, and an interrupt or a
        # death in between says why.
        self.enemy_casts = {
            "commences": 0,
            "aboutis": 0,
            "coupes": 0,
            "cible morte": 0,
            "autre": 0,
        }
        self.interrupted_spells = {}
        self.enemies = {}
        # Canonical spellings (see `canon`): the encounter's own name is
        # written with a different apostrophe than the unit's.
        self.boss_names = set()
        if segment.kind == "encounter" and segment.name:
            self.boss_names.add(canon(segment.name))
        self._specs = {}
        self._by_short_name = {}
        # The pooled enemy health: guid -> (current, max, last seen). Read
        # once per timeline bucket into the "pool" series.
        self._pool = {}
        self._pool_last_index = None
        self._pending_casts = {}
        self._block = None
        self._enemy_damage = {}
        self._enemy_names = {}
        self._hp_samples = {}
        self._timeline = {}
        self._bucket_ms = 1000
        self.events_seen = 0
        self.landed_seen = 0
        # Damage dealt by a friendly non-player unit whose owner the file
        # never names -- a pet summoned before the segment began, on a
        # line whose advanced block carries no ownerGUID. It belongs to
        # nobody's ledger and is deliberately left out of the group's
        # total, but leaving it out *silently* is how a total goes quietly
        # wrong: `diagnose` prints this, so the reader can see the size of
        # what was dropped instead of trusting that it was nothing.
        self.orphan_damage = 0
        self.orphan_sources = {}

    # -- helpers ----------------------------------------------------------

    def _player(self, actor):
        """The ledger an actor's numbers belong to, following pets home."""
        guid = actor.guid
        owner = self.pet_owner.get(guid)
        if owner is not None:
            guid = owner
        player = self.players.get(guid)
        if player is None:
            name = actor.name
            if owner is not None:
                owner_player = self.players.get(owner)
                name = owner_player.name if owner_player else name
            player = Player(guid, name)
            player.spec_id = self._specs.get(guid, 0)
            self.players[guid] = player
            # An index rather than a scan: _bank_aura asks this once per
            # aura, and a raid night has millions of auras.
            self._by_short_name.setdefault(player.short_name, player)
        return player

    def _enemy(self, actor):
        """The aggregate for everything sharing this unit's name."""
        name = actor.name or "?"
        enemy = self.enemies.get(name)
        if enemy is None:
            if len(self.enemies) >= 150:
                return None
            enemy = Enemy(name)
            self.enemies[name] = enemy
        if len(enemy.units) < 500:
            enemy.units.add(actor.guid)
        return enemy

    def _is_ours(self, actor):
        """A player, or something a player owns."""
        if actor.is_player:
            return True
        if actor.guid in self.pet_owner:
            return True
        return False

    def _bucket_index(self, ts):
        """Which timeline bucket a moment falls in, never a negative one.

        A log is not perfectly ordered -- a line can carry a timestamp
        earlier than the first event of its own segment. That gave a
        negative index, `timeline_series` only walks from zero, and the
        damage on that line vanished from the graph while staying in the
        player's row: 4,000 taken, 3,000 drawn. It is counted in the
        first bucket instead, which is where it happened to within one
        bucket's width.
        """
        return max(0, (ts - self.first_ts) // self._bucket_ms)

    def _timeline_add(self, ts, key, value):
        if self.first_ts is None:
            return
        index = self._bucket_index(ts)
        bucket = self._timeline.get(index)
        if bucket is None:
            bucket = {"damage_taken": 0, "healing": 0, "deaths": 0}
            self._timeline[index] = bucket
        bucket[key] = bucket.get(key, 0) + value

    # -- the stream -------------------------------------------------------

    def feed(self, event):
        self.events_seen += 1
        subevent = event.subevent
        if subevent == "COMBATANT_INFO":
            self._feed_combatant_info(event)
            return
        if subevent == "ENCOUNTER_START":
            # A key sees the boss pulls it contains; their names are what
            # lets a trash pull that funnels into a boss be told apart.
            fields = event.fields
            if len(fields) > 2 and isinstance(fields[2], str) and fields[2]:
                self.boss_names.add(canon(fields[2]))
            return
        if event.advanced is not None:
            self._feed_pool(event)
        self._sample_pool(event.ts)
        if self.first_ts is None:
            self.first_ts = event.ts
        self.last_ts = event.ts
        subevent = event.subevent

        # Pets: SPELL_SUMMON names the owner directly, and the advanced
        # block carries an ownerGUID on everything a pet does. Both are
        # used, because a pet summoned before the pull has no summon line
        # inside the segment.
        if subevent == "SPELL_SUMMON" and event.source.is_player and event.dest.guid:
            self.pet_owner[event.dest.guid] = event.source.guid
        if event.advanced is not None:
            owner = event.advanced.owner_guid
            info = event.advanced.info_guid
            # Only a player can own a pet, and only a pet or a guardian can
            # be owned. Without both checks a stray ownerGUID turns a boss
            # into somebody's minion and its damage into theirs.
            if (
                owner.startswith("Player-")
                and info.startswith(("Pet-", "Vehicle-", "Creature-"))
                and info not in self.pet_owner
            ):
                self.pet_owner[info] = owner

        kind = event.suffix_kind

        # SWING_DAMAGE and SWING_DAMAGE_LANDED are the same hit written
        # twice: on a real 12.1.0 log, 5,943 of 6,135 pairs sharing a
        # timestamp, a source and a target carried identical amounts, so
        # adding both doubled every melee total. _LANDED is kept for what
        # only it has -- its advanced block describes the *target* (7,561
        # of 7,561), where SWING_DAMAGE's describes the attacker -- and it
        # is never added to a total.
        if kind == "_DAMAGE_LANDED":
            self._feed_landed(event)
        elif kind in ("_DAMAGE", "_SHIELD", "_SPLIT"):
            self._feed_damage(event)
        elif kind == "_HEAL":
            self._feed_heal(event)
        elif kind == "_CAST_SUCCESS":
            if event.source.is_hostile and not event.source.is_player:
                self._resolve_enemy_cast(event.source.guid, event.spell_id, "aboutis")
                enemy = self._enemy(event.source)
                if enemy is not None:
                    enemy.casts += 1
                    name = event.spell_name or "?"
                    if name in enemy.casts_by_spell or len(enemy.casts_by_spell) < 60:
                        enemy.casts_by_spell[name] = enemy.casts_by_spell.get(name, 0) + 1
            self._feed_cast(event)
        elif kind == "_INTERRUPT":
            self._feed_interrupt(event)
        elif kind in ("_DISPEL", "_STOLEN"):
            if self._is_ours(event.source):
                player = self._player(event.source)
                player.dispels += 1
                name = event.extra_spell_name or "?"
                player.dispelled_spells[name] = player.dispelled_spells.get(name, 0) + 1
        elif kind == "_CAST_START":
            self._feed_enemy_cast_start(event)
        elif kind in ("_AURA_APPLIED", "_AURA_REFRESH"):
            self._aura_open(event)
        elif kind == "_AURA_REMOVED":
            self._aura_close(event)
        elif subevent == "UNIT_DIED":
            self._pool.pop(event.dest.guid, None)
            if not event.dest.is_player and event.dest.is_hostile:
                enemy = self._enemy(event.dest)
                if enemy is not None:
                    enemy.deaths += 1
            if not event.dest.is_player:
                for key in [
                    k for k in self._pending_casts if k[0] == event.dest.guid
                ]:
                    del self._pending_casts[key]
                    self.enemy_casts["cible morte"] += 1
            self._feed_death(event)
        elif subevent == "SPELL_ABSORBED":
            if event.dest.is_player:
                self._player(event.dest).absorbed_taken += event.absorbed_amount

        # The health curve of whatever the group actually spent the fight
        # killing. Picking the unit with the biggest health pool was a
        # guess, and on a dungeon key it was often the wrong one; this
        # ranks by damage received and the answer is only known at the
        # end, so several candidates are sampled and pruned as it goes.
        if (
            event.advanced is not None
            and kind in ("_DAMAGE", "_DAMAGE_LANDED")  # health only, not a total
            and event.dest.is_hostile
            and not event.dest.is_pet
            and event.advanced.max_hp > 0
            and event.advanced.info_guid == event.dest.guid
        ):
            self._sample_enemy_health(event)

    def _feed_damage(self, event):
        amount = event.amount
        source_ours = self._is_ours(event.source)
        dest_ours = self._is_ours(event.dest)

        if (
            not source_ours
            and not dest_ours
            and amount
            and event.source.is_friendly
            and not event.source.is_hostile
            and not event.source.is_player
            and event.source.guid
        ):
            self.orphan_damage += amount
            name = event.source.short_name or event.source.guid
            if name in self.orphan_sources or len(self.orphan_sources) < 30:
                self.orphan_sources[name] = self.orphan_sources.get(name, 0) + amount

        if source_ours and not dest_ours:
            player = self._player(event.source)
            player.damage_done += amount
            ability = _bucket(player.damage_by_ability, event.spell_id, event.spell_name)
            ability.add(amount, event.is_critical, event.dest.name, max(0, event.overkill))
            self.total_damage += amount
            self._enemy_damage[event.dest.guid] = (
                self._enemy_damage.get(event.dest.guid, 0) + amount
            )
            # Record the name here rather than only where health is
            # sampled: a unit can take damage for a whole fight without a
            # single event carrying its advanced block, and it was then
            # the top target with no name at all.
            if event.dest.name and event.dest.guid not in self._enemy_names:
                self._enemy_names[event.dest.guid] = event.dest.name
            block = self._touch_block(event)
            block.damage_done += amount
            if canon(event.dest.name) in self.boss_names:
                block.damage_boss += amount
                player.damage_to_bosses += amount
            if not event.dest.is_pet:
                block.note_enemy(event.dest.guid, event.dest.name)
            enemy = self._enemy(event.dest)
            if enemy is not None:
                enemy.damage_taken += amount
                _bucket(enemy.taken_by_ability, event.spell_id, event.spell_name).add(
                    amount, event.is_critical, player.short_name
                )

        if dest_ours:
            player = self._player(event.dest)
            player.damage_taken += amount
            # The absorbed part is NOT banked here. The client writes the
            # same absorption twice -- once in this hit's `absorbed`
            # field, once as its own SPELL_ABSORBED line -- and adding
            # both doubled every shield in the ledger (proved on a
            # synthetic log: 504,000 absorbed, 1,008,000 counted).
            # SPELL_ABSORBED is the one kept, because it is also written
            # for a hit absorbed *entirely*, which the client records as
            # a MISSED with no damage event to carry an absorbed field.
            ability = _bucket(player.taken_by_ability, event.spell_id, event.spell_name)
            ability.add(amount, False, event.source.name)
            raid_ability = _bucket(self.enemy_damage_by_ability, event.spell_id, event.spell_name)
            # Count the owner, not the pet: "2 players hit" when only one
            # player is present is a pet being counted as a person.
            raid_ability.add(amount, False, player.short_name)
            player.recent.append(
                (
                    event.ts,
                    event.source.name,
                    event.spell_name,
                    -amount,
                    self._hp_of(event),
                    event.overkill,
                )
            )
            self._track_hp(event, player)
            self._timeline_add(event.ts, "damage_taken", amount)
            block = self._touch_block(event)
            block.damage_taken += amount
            if canon(event.source.name) in self.boss_names:
                block.taken_from_boss += amount
            if event.source.is_hostile and not event.source.is_pet:
                block.note_enemy(event.source.guid, event.source.name)
            if not source_ours:
                enemy = self._enemy(event.source)
                if enemy is not None:
                    enemy.damage_done += amount
                    _bucket(
                        enemy.damage_by_ability, event.spell_id, event.spell_name
                    ).add(amount, event.is_critical, player.short_name)

    def _feed_combatant_info(self, event):
        """Who each player was: the specialization id, at one fixed field."""
        fields = event.fields
        if len(fields) < 2 or not isinstance(fields[1], str):
            return
        guid = fields[1]
        spec_id = 0
        if len(fields) > SPEC_ID_INDEX and isinstance(fields[SPEC_ID_INDEX], str):
            spec_id = as_int(fields[SPEC_ID_INDEX], 0)
        if spec_id:
            self._specs[guid] = spec_id
            player = self.players.get(guid)
            if player is not None:
                player.spec_id = spec_id

    def _feed_pool(self, event):
        """Keep the last known health of every hostile unit the log shows.

        The advanced block describes the attacker on SWING_DAMAGE and the
        target on SPELL_DAMAGE, so the unit is found by matching its GUID
        against both ends rather than assuming either.
        """
        advanced = event.advanced
        info = advanced.info_guid
        if not info or advanced.max_hp <= 0:
            return
        if info == event.dest.guid:
            actor = event.dest
        elif info == event.source.guid:
            actor = event.source
        else:
            return
        if actor.is_player or actor.is_pet or not actor.is_hostile:
            return
        if info in self._pool or len(self._pool) < 400:
            self._pool[info] = (advanced.current_hp, advanced.max_hp, event.ts)

    def _sample_pool(self, ts):
        """Once per timeline bucket, write the pooled health ratio."""
        if self.first_ts is None:
            return
        index = self._bucket_index(ts)
        if index == self._pool_last_index:
            return
        self._pool_last_index = index
        if not self._pool:
            return
        cutoff = ts - POOL_STALE_MS
        current = maximum = 0
        for guid, (hp, max_hp, seen) in list(self._pool.items()):
            if seen < cutoff or hp <= 0:
                del self._pool[guid]
                continue
            current += hp
            maximum += max_hp
        if maximum <= 0:
            return
        bucket = self._timeline.get(index)
        if bucket is None:
            bucket = {"damage_taken": 0, "healing": 0, "deaths": 0}
            self._timeline[index] = bucket
        bucket["pool"] = current / maximum
        bucket["engaged"] = len(self._pool)

    def _feed_enemy_cast_start(self, event):
        """An enemy started casting. Remember it until something ends it."""
        if event.source.is_player or not event.source.is_hostile:
            return
        self.enemy_casts["commences"] += 1
        if len(self._pending_casts) >= 400:
            # Bounded: a cast nobody ever resolved is stale after a while.
            cutoff = event.ts - 60000
            for key in [k for k, ts in self._pending_casts.items() if ts < cutoff]:
                del self._pending_casts[key]
                self.enemy_casts["autre"] += 1
        key = (event.source.guid, event.spell_id)
        if key in self._pending_casts:
            # The same unit started the same spell again before the first
            # resolved: the first never completed. Overwriting it silently
            # lost two casts in twenty-five on a real boss, found by the
            # invariant that outcomes must sum to starts.
            self.enemy_casts["autre"] += 1
        self._pending_casts[key] = event.ts

    def _resolve_enemy_cast(self, guid, spell_id, outcome):
        if self._pending_casts.pop((guid, spell_id), None) is not None:
            self.enemy_casts[outcome] += 1
            return True
        return False

    def _feed_interrupt(self, event):
        """A player cut an enemy cast. Records which spell, not just how many."""
        if not self._is_ours(event.source):
            return
        player = self._player(event.source)
        player.interrupts += 1
        stopped = event.extra_spell_name or "?"
        player.interrupted_spells[stopped] = player.interrupted_spells.get(stopped, 0) + 1
        self.interrupted_spells[stopped] = self.interrupted_spells.get(stopped, 0) + 1
        self._resolve_enemy_cast(event.dest.guid, event.extra_spell_id, "coupes")

    def _sample_enemy_health(self, event):
        guid = event.dest.guid
        fraction = event.advanced.health_fraction
        if fraction is None:
            return
        self._enemy_names.setdefault(guid, event.dest.name)
        samples = self._hp_samples.get(guid)
        if samples is None:
            if len(self._hp_samples) >= MAX_TRACKED_ENEMIES:
                self._prune_tracked_enemies()
            samples = []
            self._hp_samples[guid] = samples
        if not samples or event.ts - samples[-1][0] >= 1000:
            if len(samples) < MAX_HP_SAMPLES:
                samples.append((event.ts, fraction))

    def _prune_tracked_enemies(self):
        """Keep sampling only the units worth being the main target."""
        ranked = sorted(
            self._hp_samples,
            key=lambda guid: -self._enemy_damage.get(guid, 0),
        )
        for guid in ranked[KEEP_TRACKED_ENEMIES:]:
            self._hp_samples.pop(guid, None)

    def _touch_block(self, event):
        """Open, extend or restart the current pull."""
        block = self._block
        if block is None or event.ts - block.end_ts > self.pull_gap_ms:
            block = CombatBlock(event.ts)
            self._block = block
            self.blocks.append(block)
        block.end_ts = max(block.end_ts, event.ts)
        return block

    def _feed_landed(self, event):
        """A resolved melee hit: health and position only, never a total."""
        self.landed_seen += 1
        if self._is_ours(event.dest):
            self._track_hp(event, self._player(event.dest))

    def _feed_heal(self, event):
        effective = event.effective_healing
        if self._is_ours(event.source):
            player = self._player(event.source)
            player.healing_done += effective
            player.overhealing += event.overhealing
            ability = _bucket(player.healing_by_ability, event.spell_id, event.spell_name)
            ability.add(
                effective,
                event.is_critical,
                event.dest.name,
                overheal=event.overhealing,
            )
            self.total_healing += effective
            # Who the healing actually went to. For a healer this is most
            # of the story, and the file has it on every line.
            target = event.dest.name.split("-", 1)[0] if event.dest.name else "?"
            if effective or event.overhealing:
                current = player.healing_to.get(target)
                if current is None and len(player.healing_to) >= 60:
                    target = "autres"
                    current = player.healing_to.get(target)
                player.healing_to[target] = (current or 0) + effective
        if self._is_ours(event.dest):
            target = self._player(event.dest)
            if effective:
                target.recent.append(
                    (
                        event.ts,
                        event.source.name,
                        event.spell_name,
                        effective,
                        self._hp_of(event),
                        0,
                    )
                )
            self._track_hp(event, target)
            self._timeline_add(event.ts, "healing", effective)

    def _hp_of(self, event):
        if event.advanced is not None and event.advanced.info_guid == event.dest.guid:
            return event.advanced.health_fraction
        return None

    def _track_hp(self, event, player):
        fraction = self._hp_of(event)
        if fraction is None:
            return
        player.hp_fraction = fraction
        if player.min_hp_fraction is None or fraction < player.min_hp_fraction:
            player.min_hp_fraction = fraction
        if event.advanced.max_hp > player.max_hp:
            player.max_hp = event.advanced.max_hp

    def _feed_cast(self, event):
        if not self._is_ours(event.source):
            return
        player = self._player(event.source)
        player.casts += 1
        _bucket(player.casts_by_ability, event.spell_id, event.spell_name).add(0)
        # Keyed by spell id so a damage or healing row can find its own
        # cast count without a second pass.
        player.casts_by_spell[event.spell_id] = (
            player.casts_by_spell.get(event.spell_id, 0) + 1
        )
        if player.last_cast_ts is not None:
            gap = event.ts - player.last_cast_ts
            if gap > DOWNTIME_THRESHOLD_MS:
                player.downtime_ms += gap - DOWNTIME_THRESHOLD_MS
                player.longest_gaps.append((gap, player.last_cast_ts))
                player.longest_gaps.sort(reverse=True)
                del player.longest_gaps[5:]
        if player.first_cast_ts is None:
            player.first_cast_ts = event.ts
        player.last_cast_ts = event.ts

    def _feed_death(self, event):
        if not event.dest.is_player:
            return
        player = self._player(event.dest)
        player.deaths += 1
        player.died_at.append(event.ts)
        chain = list(player.recent)
        # The killing blow is the hit the log itself marks as one: a hit
        # that killed something writes a positive overkill, where every
        # other hit writes -1. Taking "the last damaging event" instead
        # named a 0%-to-97% redistribution from a Spirit Link Totem on a
        # real log, which is the last event but plainly not the cause.
        killing_blow = ""
        for moment in reversed(chain):
            if len(moment) > 5 and moment[5] > 0:
                killing_blow = "%s (%s)" % (moment[2] or "Attaque", moment[1] or "?")
                break
        if not killing_blow:
            for moment in reversed(chain):
                if moment[3] < 0:
                    killing_blow = "%s (%s)" % (moment[2] or "Attaque", moment[1] or "?")
                    break
        if self._block is not None:
            self._block.deaths += 1
        self.deaths.append(
            {
                "ts": event.ts,
                "player": player.short_name,
                "guid": player.guid,
                "killing_blow": killing_blow,
                "chain": chain,
            }
        )
        self._timeline_add(event.ts, "deaths", 1)

    # -- auras ------------------------------------------------------------

    def _aura_open(self, event):
        """Remember when an aura landed, and who put it there.

        Both ends matter and the file has both: a player wants to know
        which of their buffs came from whom, and which of their debuffs
        they kept up on what.
        """
        key = (event.dest.guid, event.spell_id)
        if key not in self.aura_open:
            if len(self.aura_open) >= 4000:
                # Remember that one was dropped: `_aura_close` must not
                # then read an unmatched removal as "it was up from the
                # start", because here it demonstrably was not.
                self._aura_overflowed = True
                return
            self.aura_open[key] = (
                event.ts,
                event.source.short_name or "?",
                event.spell_name,
                event.aura_type or "BUFF",
                event.dest.short_name or "?",
                event.dest.is_player,
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
        key = (event.dest.guid, event.spell_id)
        opened = self.aura_open.pop(key, None)
        if opened is None:
            if self._aura_overflowed or self.first_ts is None:
                return
            if event.ts <= self.first_ts or key in self._inferred_auras:
                return
            self._inferred_auras.add(key)
            opened = (
                self.first_ts,
                event.source.short_name or "?",
                event.spell_name,
                event.aura_type or "BUFF",
                event.dest.short_name or "?",
                event.dest.is_player,
            )
            self.auras_before_the_pull += 1
        self._bank_aura(event.dest.guid, event.spell_id, opened, event.ts)

    def _bank_aura(self, guid, spell_id, opened, ended):
        start, source_name, spell_name, aura_type, dest_name, dest_is_player = opened
        duration = max(0, ended - start)
        if not duration:
            return
        # Only a player's *own* buffs count as that player's uptime. Routing
        # a pet's auras to its owner, the way damage is routed, pushed one
        # warlock's totals past 300% of the fight: several pets can hold
        # the same aura at the same time, and a person cannot.
        if dest_is_player:
            player = self.players.get(guid)
            if player is not None:
                gained = (spell_id, spell_name, source_name, aura_type)
                if gained in player.auras_gained or len(player.auras_gained) < 400:
                    player.auras_gained[gained] = (
                        player.auras_gained.get(gained, 0) + duration
                    )
        caster = self._by_short_name.get(source_name)
        if caster is not None:
            applied = (spell_id, spell_name, dest_name)
            if applied in caster.auras_applied or len(caster.auras_applied) < 400:
                caster.auras_applied[applied] = (
                    caster.auras_applied.get(applied, 0) + duration
                )

    # -- closing ----------------------------------------------------------

    def finish(self, segment):
        end = segment.end_ts or self.last_ts or self.first_ts or 0

        # Which unit the group actually spent the fight killing, known only
        # now. On a boss pull this is the boss; in a key it is whichever
        # single unit soaked the most damage, and the report names it
        # rather than leaving the reader to guess what the curve shows.
        if self._enemy_damage:
            ranked = sorted(
                self._enemy_damage, key=lambda guid: -self._enemy_damage[guid]
            )
            # The unit that took the most damage, among those with enough
            # health samples to draw an honest line. Some units take
            # damage for a whole fight without one event carrying their
            # advanced block, and a curve cannot be invented for them.
            for guid in ranked:
                samples = self._hp_samples.get(guid) or []
                if len(samples) >= 3:
                    self.boss_name = self._enemy_names.get(guid, "")
                    self.boss_hp = samples
                    break
        self._hp_samples = {}

        # Whatever is still pending never completed and nothing here can
        # say why: a stun, a fear, a knockback, the caster walking out of
        # range. The file does not label a spell as crowd control, so this
        # bucket is named for what is known rather than guessed at.
        self.enemy_casts["autre"] += len(self._pending_casts)
        self._pending_casts = {}

        # Drop the stray ticks, but never drop the only pull there is.
        if len(self.blocks) > 1 and self.total_damage > 0:
            floor = self.total_damage * MIN_PULL_SHARE
            kept = [block for block in self.blocks if block.damage_done >= floor]
            self.dropped_pulls = len(self.blocks) - len(kept)
            if kept:
                self.blocks = kept
        # An aura still up when the pull ended counts to the end of it,
        # not to the last event that happened to mention it.
        for (guid, spell_id), opened in list(self.aura_open.items()):
            self._bank_aura(guid, spell_id, opened, end)
        self.aura_open = {}

        # A player's own downtime runs to the end of the pull, not to
        # their last cast: a rotation that stops thirty seconds early is
        # exactly the thing worth seeing.
        for player in self.players.values():
            if player.last_cast_ts is not None and end > player.last_cast_ts:
                trailing = end - player.last_cast_ts
                if trailing > DOWNTIME_THRESHOLD_MS:
                    player.downtime_ms += trailing - DOWNTIME_THRESHOLD_MS
                    player.longest_gaps.append((trailing, player.last_cast_ts))
                    player.longest_gaps.sort(reverse=True)
                    del player.longest_gaps[5:]
            player.active_ms = segment.duration_ms or (
                (self.last_ts or 0) - (self.first_ts or 0)
            )

        # Collapse the timeline into a bounded, evenly-spaced series.
        if self._timeline:
            highest = max(self._timeline)
            if highest >= MAX_TIMELINE_BUCKETS:
                factor = highest // MAX_TIMELINE_BUCKETS + 1
                collapsed = {}
                for index in sorted(self._timeline):
                    bucket = self._timeline[index]
                    target = collapsed.setdefault(
                        index // factor, {"damage_taken": 0, "healing": 0, "deaths": 0}
                    )
                    for name, value in bucket.items():
                        if name in ("pool", "engaged"):
                            # A ratio is not a sum: the last one in the
                            # merged bucket is the one that stands.
                            target[name] = value
                        else:
                            target[name] = target.get(name, 0) + value
                self._timeline = collapsed
                self._bucket_ms *= factor

    # -- readers the report uses ------------------------------------------

    @property
    def duration_ms(self):
        if self.segment.duration_ms:
            return self.segment.duration_ms
        if self.first_ts is not None and self.last_ts is not None:
            return max(0, self.last_ts - self.first_ts)
        return 0

    def ranked_players(self, key):
        seconds = max(1.0, self.duration_ms / 1000.0)
        rows = []
        for player in self.players.values():
            value = getattr(player, key)
            if value:
                rows.append((player, value, value / seconds))
        rows.sort(key=lambda row: row[1], reverse=True)
        return rows

    def top_abilities(self, store, limit=12):
        return sorted(store.values(), key=lambda ability: ability.total, reverse=True)[:limit]

    def timeline_series(self):
        """[(second, damage_taken, healing, deaths, pool)], evenly spaced.

        `pool` is the engaged enemies' pooled health as a fraction, or
        None for a bucket with no reading.
        """
        if not self._timeline:
            return [], self._bucket_ms
        highest = max(self._timeline)
        series = []
        for index in range(highest + 1):
            bucket = self._timeline.get(index) or {}
            series.append(
                (
                    index * self._bucket_ms / 1000.0,
                    bucket.get("damage_taken", 0),
                    bucket.get("healing", 0),
                    bucket.get("deaths", 0),
                    bucket.get("pool"),
                )
            )
        return series, self._bucket_ms

    @property
    def has_pool_curve(self):
        return any("pool" in bucket for bucket in self._timeline.values())

    @property
    def has_several_pulls(self):
        """True when a pull table would say something a total cannot."""
        return len(self.blocks) > 1

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

    def ranked_enemies(self, key="damage_done", limit=20):
        rows = [
            enemy
            for enemy in self.enemies.values()
            if getattr(enemy, key) or enemy.casts or enemy.deaths
        ]
        rows.sort(key=lambda enemy: -getattr(enemy, key))
        return rows[:limit]

    def composition(self):
        """[(label, [players])] -- tanks, healers, then everyone else."""
        from .specs import DPS, HEAL, TANK, role_of

        groups = {TANK: [], HEAL: [], DPS: [], "": []}
        for player in self.players.values():
            if not (player.damage_done or player.healing_done or player.casts):
                continue
            groups.setdefault(role_of(player.spec_id), []).append(player)
        for players in groups.values():
            players.sort(key=lambda player: player.short_name.lower())
        return [
            (label, groups[role])
            for role, label in ((TANK, "Tanks"), (HEAL, "Soigneurs"), (DPS, "DPS"),
                                ("", "Role non indique"))
            if groups[role]
        ]
