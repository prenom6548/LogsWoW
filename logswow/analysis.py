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

from .auras import AuraLedger
from .events import Actor
from .models import (
    CombatBlock,
    Enemy,
    Player,
    _bucket,
    canon,
)
from .specs import SPEC_ID_INDEX
from .timeline import MAX_DAMAGED_UNITS, TimelineLedger
from .tokenize import as_int

# The client writes this GUID when it has no unit to name. It carries
# player flags on a few lines per log -- "Zone anti-magie" ticks, for
# instance -- and it used to open a ledger of its own: a player row
# called "nil". It belongs to nobody, and what it does is counted as
# unattributed rather than dropped.
NULL_GUID = "0000000000000000"

DOWNTIME_THRESHOLD_MS = 2000

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


class SegmentAnalysis(AuraLedger, TimelineLedger):
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
        # Players by GUID: the full name the file gives them, and the
        # unique realm-less label the page uses. Two players can share a
        # name on two realms, and the realm is never shown, so the second
        # becomes "Tisane (2)" rather than merging into the first.
        self._player_names = {}
        self._labels = {}
        self._label_owner = {}
        # The pooled enemy health: guid -> (current, max, last seen). Read
        # once per timeline bucket into the "pool" series.
        self._pool = {}
        # The boss encounters inside this segment, from its own markers:
        # (name, start, end, success). A key sees every boss it contains;
        # a boss segment sees itself.
        self.encounters = []
        # Encounters no unit is named after -- a council of several
        # bosses -- whose damage was counted on the boss over their window.
        self.window_encounters = []
        self._encounter = None
        # Hostile health readings whose current exceeds their maximum,
        # left out of the pooled curve and the main target's curve.
        self.inconsistent_health = 0
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
        # Damage dealt by a friendly unit that belongs to no player the
        # file names -- usually a pet summoned before the segment began,
        # on lines whose advanced block carries no ownerGUID, sometimes a
        # friendly NPC fighting alongside the group. Either way it is in
        # nobody's ledger and is deliberately left out of the group's
        # total, but leaving it out *silently* is how a total goes quietly
        # wrong: the report says so, so the reader can see the size of
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
            # Never the pet's own name: a hunter whose pet struck first
            # used to get a row called after the pet, in the rankings,
            # the composition and the deaths alike. The owner's name is
            # whatever the file has said about that GUID; if it has said
            # nothing yet, `_remember_player` fills it in when it does.
            if owner is None:
                name = actor.name
            else:
                name = self._player_names.get(guid, "")
            player = Player(guid, name)
            player.label = self._labels.get(guid, "")
            player.spec_id = self._specs.get(guid, 0)
            self.players[guid] = player
        return player

    def _remember_player(self, actor):
        """Learn a player's name and label the first time the file names them."""
        guid = actor.guid
        if not guid.startswith("Player-") or guid in self._labels:
            return
        name = actor.name
        if not name or name == "nil" or len(self._labels) >= 5000:
            return
        base = name.split("-", 1)[0]
        label, number = base, 1
        while label in self._label_owner:
            number += 1
            label = "%s (%d)" % (base, number)
        self._labels[guid] = label
        self._label_owner[label] = guid
        self._player_names[guid] = name
        player = self.players.get(guid)
        if player is not None:
            if not player.name:
                player.name = name
            player.label = label

    def _name_of(self, actor):
        """The one way a unit's name is written down for the page.

        A player: the unique realm-less label. Anything else: its whole
        name -- "Chauve-souris" split at its dash came out as "Chauve",
        and on the owner's raid a creature appeared as "Jeune" in 21
        cells. Only a player's name carries a realm to strip.
        """
        if actor.guid.startswith("Player-"):
            label = self._labels.get(actor.guid)
            if label:
                return label
        return actor.display_name

    def _enemy(self, actor):
        """The aggregate for everything sharing this unit's name."""
        name = actor.display_name or "?"
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
        """A player, or something a player owns.

        The null GUID is never ours however it is flagged: it names no
        unit, so it can hold no ledger.
        """
        if not actor.guid or actor.guid == NULL_GUID:
            return False
        if actor.is_player:
            return True
        if actor.guid in self.pet_owner:
            return True
        return False

    # -- the stream -------------------------------------------------------

    def feed(self, event):
        """Route one event to the ledgers it concerns.

        Every event of the segment passes through here once, in file
        order. The two that carry no unit pair are handled first; every
        other one goes to the reader for its suffix (`_BY_SUFFIX`, at the
        end of the class) and then, if it describes a hostile unit's
        health, to the sampling that picks the main target's curve.
        """
        self.events_seen += 1
        subevent = event.subevent
        if subevent == "COMBATANT_INFO":
            self._feed_combatant_info(event)
            return
        if subevent == "ENCOUNTER_START":
            self._feed_encounter_start(event)
            return
        if event.advanced is not None:
            self._feed_pool(event)
        self._sample_pool(event.ts)
        if self.first_ts is None:
            self.first_ts = event.ts
        self.last_ts = event.ts
        self._learn_owner(event)
        self._remember_player(event.source)
        self._remember_player(event.dest)

        kind = event.suffix_kind
        handler = self._BY_SUFFIX.get(kind)
        if handler is not None:
            handler(self, event)
        elif subevent == "UNIT_DIED":
            self._feed_unit_died(event)
        elif subevent == "SPELL_ABSORBED":
            self._feed_absorbed(event)
        elif subevent == "ENCOUNTER_END":
            self._feed_encounter_end(event)

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
        self.encounters.append((encounter["label"], encounter["start"], end, success))
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

    def _learn_owner(self, event):
        """Pets: SPELL_SUMMON names the owner directly, and the advanced
        block carries an ownerGUID on everything a pet does. Both are
        used, because a pet summoned before the pull has no summon line
        inside the segment."""
        if (event.subevent == "SPELL_SUMMON" and event.source.is_player
                and event.dest.guid):
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

    def _feed_cast_success(self, event):
        """A cast that completed: an enemy's resolves its pending start."""
        if event.source.is_hostile and not event.source.is_player:
            self._resolve_enemy_cast(event.source.guid, event.spell_id, "aboutis")
            enemy = self._enemy(event.source)
            if enemy is not None:
                enemy.casts += 1
                name = event.spell_name or "?"
                if name in enemy.casts_by_spell or len(enemy.casts_by_spell) < 60:
                    enemy.casts_by_spell[name] = enemy.casts_by_spell.get(name, 0) + 1
        self._feed_cast(event)

    def _feed_dispel(self, event):
        if self._is_ours(event.source):
            player = self._player(event.source)
            player.dispels += 1
            name = event.extra_spell_name or "?"
            player.dispelled_spells[name] = player.dispelled_spells.get(name, 0) + 1

    def _feed_unit_died(self, event):
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

    def _feed_absorbed(self, event):
        """A shield ate a hit: bank it on the victim and on the caster."""
        amount = event.absorbed_amount
        if event.dest.is_player and self._is_ours(event.dest):
            self._player(event.dest).absorbed_taken += amount
        # ...and credit whoever's shield ate it. For a discipline
        # priest or a blood death knight this is most of their
        # output, and it was in no ledger at all until a Warcraft
        # Logs export of the same key showed 53.8M of it on one
        # player and this reader showed none.
        caster_guid, caster_name = event.absorb_caster
        if amount and caster_guid:
            shield = Actor(caster_guid, caster_name, 0, 0)
            if self._is_ours(shield):
                spell_id, spell_name = event.absorb_spell
                player = self._player(shield)
                player.absorb_done += amount
                _bucket(player.absorb_by_ability, spell_id, spell_name).add(
                    amount, False, self._name_of(event.dest))

    def _feed_damage(self, event):
        """One hit: whose ledger it belongs to depends on both ends."""
        amount = event.amount
        source_ours = self._is_ours(event.source)
        dest_ours = self._is_ours(event.dest)
        if (
            not source_ours
            and not dest_ours
            and amount
            and event.source.is_friendly
            and not event.source.is_hostile
        ):
            self._bank_orphan(event, amount)
        if source_ours and not dest_ours:
            self._feed_damage_dealt(event, amount)
        if dest_ours and not event.dest.is_player:
            self._feed_summon_hit(event, amount, source_ours)
        elif dest_ours:
            self._feed_player_hit(event, amount, source_ours)

    def _bank_orphan(self, event, amount):
        """Friendly damage that belongs to no player the file names."""
        self.orphan_damage += amount
        name = self._name_of(event.source) or event.source.guid
        if not name or name == "nil":
            name = "source non nommee par le journal"
        if name in self.orphan_sources or len(self.orphan_sources) < 30:
            self.orphan_sources[name] = self.orphan_sources.get(name, 0) + amount

    def _feed_damage_dealt(self, event, amount):
        """The group hit something that is not the group."""
        player = self._player(event.source)
        player.damage_done += amount
        ability = _bucket(player.damage_by_ability, event.spell_id, event.spell_name)
        ability.add(amount, event.is_critical, self._name_of(event.dest),
                    max(0, event.overkill))
        self.total_damage += amount
        self._enemy_damage[event.dest.guid] = (
            self._enemy_damage.get(event.dest.guid, 0) + amount
        )
        if len(self._enemy_damage) > MAX_DAMAGED_UNITS:
            self._prune_damaged_units()
        # Record the name here rather than only where health is
        # sampled: a unit can take damage for a whole fight without a
        # single event carrying its advanced block, and it was then
        # the top target with no name at all.
        if event.dest.name and event.dest.guid not in self._enemy_names:
            self._enemy_names[event.dest.guid] = event.dest.display_name
        block = self._touch_block(event)
        block.damage_done += amount
        dest_name = canon(event.dest.name)
        if dest_name in self.boss_names:
            block.damage_boss += amount
            player.damage_to_bosses += amount
        elif self._encounter is not None:
            self._note_window_damage(player, block, amount)
        if self._encounter is not None and dest_name == self._encounter["name"]:
            self._encounter["named"] += amount
        if not event.dest.is_pet:
            block.note_enemy(event.dest.guid, event.dest.display_name)
        enemy = self._enemy(event.dest)
        if enemy is not None:
            enemy.damage_taken += amount
            _bucket(enemy.taken_by_ability, event.spell_id, event.spell_name).add(
                amount, event.is_critical, player.short_name
            )

    def _feed_summon_hit(self, event, amount, source_ours):
        # A summon's damage is the group's, not the owner's. It stays
        # in the timeline and in the pull, because the graph is about
        # what the group took, and out of the player's own row.
        owner = self._player(event.dest)
        owner.pet_damage_taken += amount
        self._timeline_add(event.ts, "damage_taken", amount)
        block = self._touch_block(event)
        block.damage_taken += amount
        if not source_ours:
            enemy = self._enemy(event.source)
            if enemy is not None:
                enemy.damage_done += amount

    def _feed_player_hit(self, event, amount, source_ours):
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
        ability.add(amount, False, self._name_of(event.source))
        raid_ability = _bucket(self.enemy_damage_by_ability, event.spell_id, event.spell_name)
        # Count the owner, not the pet: "2 players hit" when only one
        # player is present is a pet being counted as a person.
        raid_ability.add(amount, False, player.short_name)
        player.recent.append(
            (
                event.ts,
                self._name_of(event.source),
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
            block.note_enemy(event.source.guid, event.source.display_name)
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

    def _touch_block(self, event):
        """Open, extend or restart the current pull."""
        block = self._block
        # A lull inside a boss encounter is not the end of a pull: a real
        # council fight came out as two pulls, split by an intermission.
        inside = (self._encounter is not None and block is not None
                  and block.end_ts >= self._encounter["start"])
        if block is None or (event.ts - block.end_ts > self.pull_gap_ms and not inside):
            block = CombatBlock(event.ts)
            self._block = block
            self.blocks.append(block)
        block.end_ts = max(block.end_ts, event.ts)
        return block

    def _feed_landed(self, event):
        """A resolved melee hit: health and position only, never a total."""
        self.landed_seen += 1
        if event.dest.is_player and self._is_ours(event.dest):
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
                self._name_of(event.dest),
                overheal=event.overhealing,
            )
            self.total_healing += effective
            # Who the healing actually went to. For a healer this is most
            # of the story, and the file has it on every line.
            target = self._name_of(event.dest) or "?"
            if effective or event.overhealing:
                current = player.healing_to.get(target)
                if current is None and len(player.healing_to) >= 60:
                    target = "autres"
                    current = player.healing_to.get(target)
                player.healing_to[target] = (current or 0) + effective
        if event.dest.is_player and self._is_ours(event.dest):
            # A player's own health and death chain only: a heal landing
            # on their summon is not a heal on them.
            target = self._player(event.dest)
            if effective:
                target.recent.append(
                    (
                        event.ts,
                        self._name_of(event.source),
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
        """The player's own health, never a summon's.

        `_hp_of` reads the advanced block when it describes the event's
        destination -- and that destination can be somebody's pet, whose
        health then became the owner's. Every player in a real key showed
        "lowest health 0%" for pets that had died while they had not.
        """
        if not event.dest.is_player:
            return
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
        if not event.source.is_player:
            player.pet_casts += 1
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
        if not event.dest.is_player or not self._is_ours(event.dest):
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

    # -- closing ----------------------------------------------------------

    def finish(self, segment):
        """Close the segment: everything that can only be known at its end."""
        end = segment.end_ts or self.last_ts or self.first_ts or 0
        if self._encounter is not None:
            self._close_encounter(end, None)
        self._pick_main_target()
        # Whatever is still pending never completed and nothing here can
        # say why: a stun, a fear, a knockback, the caster walking out of
        # range. The file does not label a spell as crowd control, so this
        # bucket is named for what is known rather than guessed at.
        self.enemy_casts["autre"] += len(self._pending_casts)
        self._pending_casts = {}

        self._drop_crumbs()
        # An aura still up when the pull ended counts to the end of it,
        # not to the last event that happened to mention it.
        for (guid, spell_id, _source), opened in list(self.aura_open.items()):
            self._bank_aura(guid, spell_id, opened, end)
        self.aura_open = {}

        self._close_downtime(segment, end)
        self._collapse_timeline()

    def _drop_crumbs(self):
        # Drop the stray ticks, but never drop the only pull there is.
        if len(self.blocks) > 1 and self.total_damage > 0:
            floor = self.total_damage * MIN_PULL_SHARE
            kept = [block for block in self.blocks if block.damage_done >= floor]
            self.dropped_pulls = len(self.blocks) - len(kept)
            if kept:
                self.blocks = kept

    def _close_downtime(self, segment, end):
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

    @property
    def has_several_pulls(self):
        """True when a pull table would say something a total cannot."""
        return len(self.blocks) > 1

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

    # Which reader each suffix goes to. SWING_DAMAGE and SWING_DAMAGE_LANDED
    # are the same hit written twice: on a real 12.1.0 log, 5,943 of 6,135
    # pairs sharing a timestamp, a source and a target carried identical
    # amounts, so adding both doubled every melee total. _LANDED is kept for
    # what only it has -- its advanced block describes the *target* (7,561
    # of 7,561), where SWING_DAMAGE's describes the attacker -- and it is
    # never added to a total.
    _BY_SUFFIX = {
        "_DAMAGE_LANDED": _feed_landed,
        "_DAMAGE": _feed_damage,
        "_SHIELD": _feed_damage,
        "_SPLIT": _feed_damage,
        "_HEAL": _feed_heal,
        "_CAST_SUCCESS": _feed_cast_success,
        "_INTERRUPT": _feed_interrupt,
        "_DISPEL": _feed_dispel,
        "_STOLEN": _feed_dispel,
        "_CAST_START": _feed_enemy_cast_start,
        "_AURA_APPLIED": AuraLedger._aura_open,
        "_AURA_REFRESH": AuraLedger._aura_open,
        "_AURA_REMOVED": AuraLedger._aura_close,
    }
