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

# Bounds on the per-enemy health sampling, so a 20-minute key cannot grow
# without limit while it works out which unit was the main target.
MAX_TRACKED_ENEMIES = 40
KEEP_TRACKED_ENEMIES = 20
MAX_HP_SAMPLES = 400


class Ability:
    """One spell's contribution, on one side of one ledger."""

    __slots__ = (
        "spell_id", "name", "total", "hits", "crits", "targets", "overkill", "overheal",
    )

    def __init__(self, spell_id, name):
        self.spell_id = spell_id
        self.name = name or "Attaque"
        self.total = 0
        self.hits = 0
        self.crits = 0
        self.targets = set()
        self.overkill = 0
        self.overheal = 0

    def add(self, amount, critical=False, target=None, overkill=0, overheal=0):
        self.total += amount
        self.hits += 1
        if critical:
            self.crits += 1
        if target:
            self.targets.add(target)
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


class CombatBlock:
    """One pull: a stretch of fighting with no long silence inside it.

    A boss encounter is one of these. A Mythic+ key is a few dozen, which
    is the whole reason this exists -- "what did we actually pull" is a
    question the file can answer and a single 20-minute total cannot.
    """

    __slots__ = ("start_ts", "end_ts", "damage_done", "damage_taken", "deaths", "enemies")

    def __init__(self, start_ts):
        self.start_ts = start_ts
        self.end_ts = start_ts
        self.damage_done = 0
        self.damage_taken = 0
        self.deaths = 0
        self.enemies = {}

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

    def label(self, limit=PULL_LABEL_UNITS):
        """'Voyou de l'allee x4, Chaman ensorcele x2'."""
        ranked = sorted(self.enemies.items(), key=lambda item: -len(item[1]))
        pieces = []
        for name, guids in ranked[:limit]:
            pieces.append("%s x%d" % (name, len(guids)) if len(guids) > 1 else name)
        if len(ranked) > limit:
            pieces.append("et %d autre(s)" % (len(ranked) - limit))
        return ", ".join(pieces)


class Player:
    """One friendly actor's whole ledger for one segment."""

    __slots__ = (
        "guid", "name", "damage_done", "healing_done", "overhealing",
        "damage_taken", "absorbed_taken", "deaths", "interrupts", "dispels",
        "casts", "damage_by_ability", "healing_by_ability", "taken_by_ability",
        "casts_by_ability", "healing_to", "interrupted_spells", "dispelled_spells",
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
        self.pull_gap_ms = pull_gap_ms
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
        self._pending_casts = {}
        self._block = None
        self._enemy_damage = {}
        self._enemy_names = {}
        self._hp_samples = {}
        self._timeline = {}
        self._bucket_ms = 1000
        self.events_seen = 0
        self.landed_seen = 0

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
            self.players[guid] = player
        return player

    def _is_ours(self, actor):
        """A player, or something a player owns."""
        if actor.is_player:
            return True
        if actor.guid in self.pet_owner:
            return True
        return False

    def _timeline_add(self, ts, key, value):
        if self.first_ts is None:
            return
        index = (ts - self.first_ts) // self._bucket_ms
        bucket = self._timeline.get(index)
        if bucket is None:
            bucket = {"damage_taken": 0, "healing": 0, "deaths": 0}
            self._timeline[index] = bucket
        bucket[key] = bucket.get(key, 0) + value

    # -- the stream -------------------------------------------------------

    def feed(self, event):
        self.events_seen += 1
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
        absorbed = event.absorbed
        source_ours = self._is_ours(event.source)
        dest_ours = self._is_ours(event.dest)

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
            if not event.dest.is_pet:
                block.note_enemy(event.dest.guid, event.dest.name)

        if dest_ours:
            player = self._player(event.dest)
            player.damage_taken += amount
            player.absorbed_taken += max(0, absorbed)
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
            if event.source.is_hostile and not event.source.is_pet:
                block.note_enemy(event.source.guid, event.source.name)

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
        self._pending_casts[(event.source.guid, event.spell_id)] = event.ts

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
        if not event.dest.is_player:
            return
        key = (event.dest.guid, event.spell_id, event.spell_name)
        if key not in self.aura_open:
            self.aura_open[key] = event.ts

    def _aura_close(self, event):
        if not event.dest.is_player:
            return
        key = (event.dest.guid, event.spell_id, event.spell_name)
        opened = self.aura_open.pop(key, None)
        if opened is None:
            return
        self.aura_uptime[key] = self.aura_uptime.get(key, 0) + max(0, event.ts - opened)

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
        for key, opened in list(self.aura_open.items()):
            self.aura_uptime[key] = self.aura_uptime.get(key, 0) + max(0, end - opened)
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
                for index, bucket in self._timeline.items():
                    target = collapsed.setdefault(
                        index // factor, {"damage_taken": 0, "healing": 0, "deaths": 0}
                    )
                    for name, value in bucket.items():
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
        """[(second, damage_taken, healing, deaths)], evenly spaced."""
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
                )
            )
        return series, self._bucket_ms

    @property
    def has_several_pulls(self):
        """True when a pull table would say something a total cannot."""
        return len(self.blocks) > 1

    def player_uptimes(self, guid, limit=14):
        rows = []
        for (owner, spell_id, name), milliseconds in self.aura_uptime.items():
            if owner == guid and milliseconds > 0:
                rows.append((name, spell_id, milliseconds))
        rows.sort(key=lambda row: row[2], reverse=True)
        return rows[:limit]
