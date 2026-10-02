# SPDX-License-Identifier: AGPL-3.0-or-later
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

import math

from .auras import AuraLedger
from .castorder import MAX_CAST_LOG, classify_triggered
from .encounters import EncounterLedger
from .events import FLAGS_IN_GROUP, FLAGS_OPPONENT, Actor, Event
from .gear import parse as parse_gear
from .i18n import _, spell_label
from .models import (
    OTHER_TARGETS,
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
# follows counts as a new pull. Six seconds until 0.11.0; the owner, who
# plays these keys, found three closer to what the group actually does
# (2026-09-29), and `--pull-gap` still lets a reader choose.
PULL_GAP_MS = 3000

# Who opened a pull: the first act linking the group and an enemy after
# the previous pull's last damage. Measured on 150 pulls of three real
# dungeon logs: a tank's opener comes a median 0.35 s before the first
# damage, and 13 s at the most; nothing earlier than this is taken. When
# nothing came before, the first act within this long after it is.
OPENING_LOOKBACK_MS = 15000
OPENING_WAIT_MS = 2000
# Healing and buffing a player in combat draws the enemy's attention to the
# healer (the owner, 2026-09-29): an enemy's first target may have inherited
# the aggro of the player it had just helped. On 27 pulls of three real
# logs where the enemy acted first, one heal came 0.2 s before; the next
# nearest help was a paladin aura reapplying itself at 2.8 s. So: two.
OPENING_HELP_MS = 2000
# The first hit each enemy unit took from the group, per pull. A hit that
# missed draws the enemy all the same, so it counts; a pull keeps at most
# this many units (a real key's largest pull had far fewer).
FIRST_HIT_KINDS = frozenset({"_DAMAGE", "_MISSED"})
MAX_FIRST_HITS = 300
# Where a melee swing came from. The file never says it; each advanced
# block gives the position and the facing of the unit it describes, so a
# swing is placed from the victim's facing and the attacker's position,
# each from that unit's latest line. A swing that missed carries no block
# at all, so both ends are always a unit's last known place, and no older
# than this: on the owner's 364 MB night, 97% of parries and 96% of dodges
# came out in front -- the game allows neither from behind -- and 29% of
# the swings that landed from behind (2026-09-29).
POSITION_STALE_MS = 1500
# Units whose last position is kept at once; past it, the stale ones go.
MAX_POSITIONS = 4000
# Keys a player's `melee_taken` may grow to: a damaged line cannot open
# one key per garbage miss type.
MAX_MELEE_KEYS = 30
# The acts that can open a pull. An aura *ending* cannot: on those logs the
# first "link" before a pull was, 23 times in 68, a debuff falling off the
# last pack's corpses.
OPENING_KINDS = frozenset({
    "_DAMAGE", "_DAMAGE_LANDED", "_MISSED", "_CAST_SUCCESS", "_AURA_APPLIED",
    "_AURA_APPLIED_DOSE", "_INSTAKILL", "_INTERRUPT", "_DRAIN", "_LEECH",
})

# Summons an encounter makes players cast (see SegmentAnalysis._note_summon).
SUMMON_INSTANT_MS = 20
MECHANIC_MIN_SUMMONS = 3
MECHANIC_SHARE = 0.8
MAX_SUMMONS = 50000

# A "pull" worth a line has to be a meaningful share of the run. A real
# key produced two blocks of 7.9k and 14.1k damage against a 531M total:
# a dot finishing on something already dead, or a critter. One part in a
# thousand cuts those and leaves the smallest genuine pull (20M) two
# orders of magnitude clear.
MIN_PULL_SHARE = 0.001


class SegmentAnalysis(AuraLedger, EncounterLedger, TimelineLedger):
    """Accumulates one segment. `feed` per event, `finish` once."""

    def __init__(self, segment, pull_gap_ms=PULL_GAP_MS):
        self.segment = segment
        # Under a second, every dot tick would be its own pull.
        self.pull_gap_ms = max(1000, int(pull_gap_ms))
        self.players = {}
        self.pet_owner = {}
        # Players by the side the file has shown them on, by GUID: in the
        # group at least once, or outside it and hostile. See `_is_opponent`.
        self._members = set()
        self._opponents = set()
        # Summons, to tell a player's own from an encounter's: see
        # `_note_summon` and `_disown_mechanics`.
        self._recent_summons = []
        self._summoned_by = {}          # unit GUID -> (summoning spell id, unit name)
        self._shared_summons = set()    # units summoned in the same instant as another player's
        self.enemy_damage_by_ability = {}  # what hit the group, raid-wide
        self.deaths = []
        self.first_ts = None
        self.last_ts = None
        self.total_damage = 0
        self.total_healing = 0
        self.aura_open = {}
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
        self._gear = {}
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
        # (name, start, end, success, fought). A key sees every boss it contains;
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
        # The first act linking the group and an enemy since the last
        # damage, and a pull still waiting for its opener (_note_opening).
        self._opening_pending = None
        self._opening_wait = None
        # {player guid: (ts, helped player's ledger, spell)}: the last heal
        # or buff each player gave another, for the opener's context.
        self._last_help = {}
        # {enemy guid: first hit} noted after the last damage, for the pull
        # the next damage opens (_note_first_hit).
        self._first_hits_pending = {}
        self._enemy_damage = {}
        self._enemy_names = {}
        self._hp_samples = {}
        self._timeline = {}
        self._bucket_ms = 1000
        self.landed_seen = 0
        # Units a player "summoned" that turned out to be the encounter's.
        self.disowned_units = 0
        # Health a summon of ours moved from one player to another (Spirit
        # Link Totem): see `_feed_moved_health`. The pairs (unit, spell)
        # seen healing the group, and the hits held until their instant
        # ends, when the lines written after them say how to read them.
        self.moved_health = 0
        self._moving_units = set()
        self._held = []
        # Each unit's latest (time, advanced block), and the melee swings
        # at players counted while reading, by GUID: they reach the players'
        # ledgers at the end, so that no ledger is opened while reading.
        self._where = {}
        self._melee_taken = {}
        # What the group dealt into its enemies' shields: in damage done,
        # counted apart here too so the page and the checks can name it.
        self.shield_damage = 0
        # Players the file wrote as dead who only fell unconscious.
        self.unconscious_seen = 0
        # True once a SWING_DAMAGE_LANDED on the group was seen: see
        # `_feed_damage`.
        self._melee_taken_landed = False
        # {school mask: amount} over the whole segment, crumbs included:
        # what the group took (players and their summons) and dealt.
        self.taken_by_school = {}
        self.done_by_school = {}
        # *_SUPPORT lines read and kept out of every total (see _feed_support).
        self.support_seen = 0
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
            player = self._player_by_guid(guid, actor.name if owner is None else None)
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
            return not self._is_opponent(actor)
        if actor.guid in self.pet_owner:
            return True
        return False

    def _is_opponent(self, actor):
        """A player of the other side: outside the group, hostile, and never in it here.

        Counted as the group until 2026-09-29: in an arena the opponent sat
        in the ranking, every blow between the two teams was friendly fire,
        and the damage dealt read zero. The flags say it -- outsider and
        hostile together; a raid member under a mind control is hostile but
        still in the raid -- on the line being read. A player the segment
        has already shown in the group stays in it: on the owner's night a
        cross-faction member who stepped out of the group at the end of a
        key was written outside and hostile, and came back. An actor
        rebuilt from a GUID alone (a shield's caster) carries no flags, and
        is judged by what the file last said about that player.
        """
        guid = actor.guid
        if guid in self._members or not actor.is_player:
            return False
        if actor.flags:
            return actor.flags & FLAGS_OPPONENT == FLAGS_OPPONENT
        return guid in self._opponents

    def _note_sides(self, event):
        """Remember which players the file shows in the group, and which against it."""
        for actor in (event.source, event.dest):
            flags = actor.flags
            if flags & FLAGS_IN_GROUP:
                if actor.guid.startswith("Player-") and len(self._members) < 5000:
                    self._members.add(actor.guid)
            elif (flags & FLAGS_OPPONENT == FLAGS_OPPONENT and actor.guid.startswith("Player-")
                  and len(self._opponents) < 5000):
                self._opponents.add(actor.guid)

    # -- the stream -------------------------------------------------------

    def feed(self, event):
        """Route one event to the ledgers it concerns.

        Every event of the segment passes through here once, in file
        order. The two that carry no unit pair are handled first; every
        other one goes to the reader for its suffix (`_BY_SUFFIX`, at the
        end of the class) and then, if it describes a hostile unit's
        health, to the sampling that picks the main target's curve.
        """
        if self._held and event.ts != self._held[0].ts:
            self._settle_moves()
        subevent = event.subevent
        if subevent == "COMBATANT_INFO":
            self._feed_combatant_info(event)
            return
        if subevent == "ENCOUNTER_START":
            self._feed_encounter_start(event)
            return
        if event.advanced is not None:
            self._feed_pool(event)
            self._note_position(event)
        self._sample_pool(event.ts)
        if self.first_ts is None:
            self.first_ts = event.ts
        self.last_ts = event.ts
        self._learn_owner(event)
        self._remember_player(event.source)
        self._remember_player(event.dest)

        kind = event.suffix_kind
        handler = self._BY_SUFFIX.get(kind)
        if event.support_guid:
            self._feed_support(event)
            return
        if handler is not None:
            handler(self, event)
        elif subevent == "UNIT_DIED":
            self._feed_unit_died(event)
        elif subevent == "SPELL_ABSORBED":
            self._feed_absorbed(event)
        elif subevent == "ENCOUNTER_END":
            self._feed_encounter_end(event)
        if kind in OPENING_KINDS:
            self._note_opening(event)
        if kind in ("_HEAL", "_AURA_APPLIED", "_DISPEL"):
            self._note_help(event)
        if kind in FIRST_HIT_KINDS:
            self._note_first_hit(event)

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

    def _learn_owner(self, event):
        """Pets: SPELL_SUMMON names the owner directly, and the advanced
        block carries an ownerGUID on everything a pet does. Both are
        used, because a pet summoned before the pull has no summon line
        inside the segment. An opposing player's summons are never ours."""
        self._note_sides(event)
        if (event.subevent == "SPELL_SUMMON" and event.source.is_player
                and self._is_ours(event.source) and event.dest.guid):
            self.pet_owner[event.dest.guid] = event.source.guid
            self._note_summon(event)
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
                and (owner not in self._opponents or owner in self._members)
            ):
                self.pet_owner[info] = owner

    def _note_summon(self, event):
        """Remember a player's summon, and whether another player's came with it.

        An encounter can make players "summon" its own units: the log
        writes SPELL_SUMMON with the player as the source, and Nalorakk's
        echoes then cast in that player's name. Nothing in the flags tells
        them apart from a real summon (measured 2026-09-28 on three logs:
        type, reaction and affiliation all overlap). What does is the
        instant: Echo de Nalorakk came to three players in the same
        millisecond, 24 summons of 24, and "Orbes gravitationnels" 9 of 9,
        where two warlocks' imps met by chance at most 1.4% of the time.
        """
        if len(self._summoned_by) >= MAX_SUMMONS:
            return
        ts, spell_id = event.ts, event.spell_id
        self._recent_summons = [entry for entry in self._recent_summons
                                if ts - entry[0] <= SUMMON_INSTANT_MS]
        for _ts, other_spell, other_player, other_unit in self._recent_summons:
            if other_spell == spell_id and other_player != event.source.guid:
                self._shared_summons.update((other_unit, event.dest.guid))
        self._recent_summons.append((ts, spell_id, event.source.guid, event.dest.guid))
        self._summoned_by[event.dest.guid] = (spell_id, event.dest.name)

    def _disown_mechanics(self):
        """Hand back to the encounter the units it made players summon.

        A summoning spell is the encounter's when, in this segment, it
        brought units at least MECHANIC_MIN_SUMMONS times and at least
        MECHANIC_SHARE of them in the same instant as another player's.
        Their casts leave the players' sequences and counts and become the
        enemy's; their hits on the group already went to the enemy (see
        `_feed_damage`).
        """
        units = {}
        for unit, (spell_id, _name) in self._summoned_by.items():
            units.setdefault(spell_id, []).append(unit)
        disowned = {}
        for spell_id, members in units.items():
            shared = sum(1 for unit in members if unit in self._shared_summons)
            if len(members) >= MECHANIC_MIN_SUMMONS and shared >= MECHANIC_SHARE * len(members):
                for unit in members:
                    disowned[unit] = self._summoned_by[unit][1]
        if not disowned:
            return
        self.disowned_units = len(disowned)
        for player in self.players.values():
            kept = []
            for entry in player.cast_log:
                unit = entry[4]
                if unit not in disowned:
                    kept.append(entry)
                    continue
                player.casts -= 1
                player.pet_casts -= 1
                spell_id, name = entry[1], entry[2]
                ability = player.casts_by_ability.get((spell_id, name))
                if ability is not None:
                    ability.hits -= 1
                    if ability.hits <= 0:
                        del player.casts_by_ability[(spell_id, name)]
                left = player.casts_by_spell.get(spell_id, 0) - 1
                if left > 0:
                    player.casts_by_spell[spell_id] = left
                else:
                    player.casts_by_spell.pop(spell_id, None)
                enemy = self._enemy(Actor(unit, disowned[unit], 0, 0))
                if enemy is not None:
                    enemy.casts += 1
                    if name in enemy.casts_by_spell or len(enemy.casts_by_spell) < 60:
                        enemy.casts_by_spell[name] = enemy.casts_by_spell.get(name, 0) + 1
            player.cast_log = kept

    def _feed_cast_success(self, event):
        """A cast that completed: an enemy's resolves its pending start."""
        if event.source.is_hostile and (not event.source.is_player
                                        or self._is_opponent(event.source)):
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
        if event.dest.is_player and event.unconscious:
            # Not a death: the player got up and acted again (see
            # `Event.unconscious`).
            self.unconscious_seen += 1
            return
        self._pool.pop(event.dest.guid, None)
        opponent = self._is_opponent(event.dest)
        if (not event.dest.is_player or opponent) and event.dest.is_hostile:
            enemy = self._enemy(event.dest)
            if enemy is not None:
                enemy.deaths += 1
        if not event.dest.is_player or opponent:
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
        # ...and, when the shield was an enemy's, on the attacker: a hit a
        # shield ate is damage dealt to the unit behind it. Left out until
        # 2026-09-28, the group's damage read 0.5% to 1.6% short of
        # Warcraft Logs on five real keys, and the gap matched what their
        # enemies' shields ate to the unit.
        if amount > 0 and self._is_ours(event.source) and not self._target_is_ours(event):
            spell_id, spell_name, school = event.absorbed_attack
            self.shield_damage += amount
            self._feed_damage_dealt(event, amount, spell=(spell_id, spell_name or "Attaque"),
                                    school=school, critical=event.absorbed_critical)
        elif (amount > 0 and not self._is_ours(event.source) and not self._is_ours(event.dest)
              and event.source.is_friendly and not event.source.is_hostile):
            # The same hit, from a friendly unit nobody owns: unattributed,
            # like the rest of what it dealt (see `_bank_orphan`).
            self._bank_orphan(event, amount)

    def _target_is_ours(self, event):
        """Whether the unit hit is the group's, for a hit that one of us dealt.

        A player, yes. A player's summon, unless the line flags it hostile:
        the encounter can put a unit there under a player's name for the
        group to break -- "Tombe glaciale", the ice a player is locked in,
        10.9M on one night, until 2026-09-28 counted as the group's own
        damage taken instead of damage dealt. Measured on three real logs,
        every such unit carries hostile flags (0xa48), while every genuine
        summon the group's lines touch -- a demon taking its share of Soul
        Link, a raid boss turning a pet against the group -- is friendly.
        """
        if event.dest.is_player:
            return self._is_ours(event.dest)
        return self._is_ours(event.dest) and not event.dest.is_hostile

    def _feed_damage(self, event, settled=False):
        """One hit: whose ledger it belongs to depends on both ends."""
        source_ours, dest_ours = self._damage_sides(event)
        if event.subevent.startswith("SWING_DAMAGE") and not self._melee_counts(
                event, source_ours, dest_ours, settled):
            return
        if (source_ours and dest_ours and event.dest.is_player
                and not event.source.is_player and not settled):
            # A summon of ours hitting a player of ours: Spirit Link Totem
            # moving health, unless the instant says otherwise.
            if (event.source.guid, event.spell_id) in self._moving_units:
                self._feed_moved_health(event)
            else:
                self._held.append(event)
            return
        self._bank_damage(event, source_ours, dest_ours)

    def _damage_sides(self, event):
        """(source is the group's, target is the group's), for one hit."""
        source_ours = self._is_ours(event.source)
        dest_ours = self._is_ours(event.dest)
        if source_ours and dest_ours and event.source.guid in self._shared_summons:
            # A unit the encounter made several players summon at once (see
            # `_note_summon`) hitting the group: the enemy's damage, not a
            # player's friendly fire. Only those: a first version took every
            # summon hitting an ally for the enemy's, and the snapshot showed
            # Spirit Link Totem, a Rune Weapon and an Arcane Phoenix among
            # the enemies of a real key.
            source_ours = False
        if source_ours and dest_ours:
            dest_ours = self._target_is_ours(event)
        return source_ours, dest_ours

    def _melee_counts(self, event, source_ours, dest_ours, settled):
        """Whether this melee line is the one of its pair that counts, now.

        False also when the line is held back to the end of its instant
        (`_held`), to be decided by `_settle_moves`.
        """
        landed = event.suffix_kind == "_DAMAGE_LANDED"
        if not dest_ours or source_ours:
            return not landed       # the SWING_DAMAGE line of the same hit counts
        # Melee the group took is counted from _LANDED: the client
        # writes many such hits *only* as _LANDED (5,720 lines against
        # 3,870 SWING_DAMAGE on a real night, 4,691 against 2,815 on
        # another), and on a tank SWING_DAMAGE came to 12.6% less than
        # the hits that landed. Warcraft Logs counts _LANDED; five keys
        # agree with it to the unit once this does. SWING_DAMAGE comes
        # first in a pair (2,056 times of 2,058), so until the segment
        # has shown a _LANDED one is held to the end of its instant; a
        # file that writes no _LANDED at all keeps SWING_DAMAGE.
        if landed:
            self._melee_taken_landed = True
            return True
        if self._melee_taken_landed:
            return False
        if not settled:
            self._held.append(event)
            return False
        return True

    def _bank_damage(self, event, source_ours, dest_ours):
        """A hit that counts: into the ledgers of whoever was on each end."""
        amount = event.amount
        # Damage past the last point of health went nowhere, as healing
        # past full health does: it is the overkill, counted apart.
        # Warcraft Logs leaves it out too; five real keys agree with it to
        # the unit once it is, and once shields and mechanics are counted.
        overkill = min(max(0, event.overkill), max(0, amount))
        if (
            not source_ours
            and not dest_ours
            and amount
            and event.source.is_friendly
            and not event.source.is_hostile
        ):
            self._bank_orphan(event, amount - overkill)
        if source_ours and not dest_ours:
            self._feed_damage_dealt(event, amount - overkill, overkill=overkill)
        if dest_ours and not event.dest.is_player:
            self._feed_summon_hit(event, amount, source_ours)
        elif dest_ours:
            self._feed_player_hit(event, amount, source_ours)

    def _feed_support(self, event):
        """The part of a hit the game credits to an Evoker who did not deal it.

        **Never added to a total.** The line repeats part or all of a hit
        its *source* already dealt, measured two ways on real logs:

        - An Augmentation buff (Ebon Might, Prescience, Shifting Sands)
          raises a stat, so it makes the ally's own hit bigger and creates
          no hit of its own. The line says how much of that hit was the
          buff: 0.4% to 13.1% of each supported player's damage.
        - Bombardments explodes when an ally attacks, and the client
          writes the explosion as the *ally's* SPELL_DAMAGE, then again,
          same amount, as a _SUPPORT line naming the Evoker.

        Read as ordinary damage, as it was until 2026-09-27, both counted
        twice: 3.15% of the group's damage over the fights of a log with
        three Augmentation Evokers, 14.3% of one player's on the owner's
        own raid night, which had no Augmentation at all -- a Devastation
        Evoker's Bombardments was enough, and no read problem showed it.

        It is banked on the Evoker instead, as a figure of its own: what
        the game says their buffs added to other players' numbers.
        Warcraft Logs moves it from the ally to the Evoker; this report
        leaves every hit with whoever dealt it and shows the credit apart.
        """
        self.support_seen += 1
        if not (event.support_guid.startswith("Player-") and self._is_ours(event.source)):
            return
        if event.suffix_kind in Event.HEAL_KINDS:
            amount, attr = event.effective_healing, "support_healing"
        # A melee's share comes only as SWING_DAMAGE_LANDED_SUPPORT: the
        # real log with 9,772 of them has no SWING_DAMAGE_SUPPORT at all.
        elif (event.suffix_kind in ("_DAMAGE", "_DAMAGE_LANDED")
              and not self._is_ours(event.dest)):
            amount, attr = event.amount, "support_damage"
        else:
            return
        if amount <= 0:
            return
        evoker = self._player_by_guid(event.support_guid)
        setattr(evoker, attr, getattr(evoker, attr) + amount)
        if attr == "support_damage":
            _bucket(evoker.support_by_ability, event.spell_id, event.spell_name).add(
                amount, False, self._name_of(event.source))
            self._player(event.source).support_received += amount

    def _player_by_guid(self, guid, name=None):
        """A player's ledger by GUID, opened under `name` or what the file has said."""
        player = self.players.get(guid)
        if player is None:
            if name is None:
                name = self._player_names.get(guid, "")
            player = Player(guid, name)
            player.label = self._labels.get(guid, "")
            player.spec_id = self._specs.get(guid, 0)
            player.gear = self._gear.get(guid)
            self.players[guid] = player
        return player

    def _bank_orphan(self, event, amount):
        """Friendly damage that belongs to no player the file names."""
        self.orphan_damage += amount
        name = self._name_of(event.source) or event.source.guid
        if not name or name == "nil":
            name = _("source non nommée par le journal")
        if name in self.orphan_sources or len(self.orphan_sources) < 30:
            self.orphan_sources[name] = self.orphan_sources.get(name, 0) + amount

    def _feed_damage_dealt(self, event, amount, overkill=0, spell=None, school=None,
                           critical=None):
        """The group hit something that is not the group.

        `amount` is what the hit took off the unit: its overkill already
        removed. A hit an enemy's shield ate comes from SPELL_ABSORBED,
        which names its spell, school and critical flag elsewhere on the
        line, so the caller passes them.
        """
        spell_id, spell_name = spell or (event.spell_id, event.spell_name)
        if critical is None:
            critical = event.is_critical
        player = self._player(event.source)
        player.damage_done += amount
        ability = _bucket(player.damage_by_ability, spell_id, spell_name)
        ability.add(amount, critical, self._name_of(event.dest), overkill)
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
        _bank_mask(event.damage_school if school is None else school, amount,
                   block.done_by_school, self.done_by_school)
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
            _bucket(enemy.taken_by_ability, spell_id, spell_name).add(
                amount, critical, player.short_name
            )

    def _settle_moves(self):
        """Decide the hits held back by `_feed_damage`, now their instant is over.

        An enemy's SWING_DAMAGE on the group is dropped if a _LANDED line
        has shown up since, and counted otherwise.

        Spirit Link Totem writes, in one millisecond, a damage line on each
        player above the group's average health and a heal line on each
        one below, with the same spell. Which comes first varies (of 14
        totems on a real night, 13 wrote both in their first instant, 7
        heal first and 6 damage first), so a summon's hit on a player waits for
        its instant to end: if the same unit healed the group with the
        same spell by then, it was moving health; otherwise it was an
        ordinary hit and is read as one.
        """
        pending, self._held = self._held, []
        for event in pending:
            if (not event.source.is_player and event.dest.is_player
                    and (event.source.guid, event.spell_id) in self._moving_units):
                self._feed_moved_health(event)
            else:
                self._feed_damage(event, settled=True)

    def _feed_moved_health(self, event):
        """Health a summon took from one player to give another: not damage.

        Spirit Link Totem, the one case in three real logs (23.5M on one
        night). Read as damage, it was the group's damage taken -- listed
        among what hurt the group -- while the heal half was the shaman's
        healing, so the totem looked like it both hurt and healed. It is
        neither: the shaman's healing is net of it, as on Warcraft Logs
        (their "Spirit Link (Damage)" row, negative), and nobody's damage
        taken counts it. The victim's own health and death recap still see
        the hit, because it did lower their health.
        """
        amount = event.amount
        # The part a shield ate is moved health too; the shield's caster
        # was credited for it by SPELL_ABSORBED.
        moved = amount + max(0, event.absorbed)
        self.moved_health += moved
        owner = self._player(event.source)
        owner.healing_done -= moved
        owner.moved_health += moved
        _bucket(owner.healing_by_ability, event.spell_id, event.spell_name).total -= moved
        self.total_healing -= moved
        self._timeline_add(event.ts, "healing", -moved)
        victim = self._player(event.dest)
        victim.recent.append((event.ts, self._name_of(event.source), event.spell_name,
                              -amount, self._hp_of(event), event.overkill))
        self._track_hp(event, victim)

    def _feed_summon_hit(self, event, amount, source_ours):
        # A summon's damage is the group's, not the owner's. It stays
        # in the timeline and in the pull, because the graph is about
        # what the group took, and out of the player's own row.
        owner = self._player(event.dest)
        owner.pet_damage_taken += amount
        self._timeline_add(event.ts, "damage_taken", amount)
        block = self._touch_block(event)
        block.damage_taken += amount
        _bank_school(event, amount, block.taken_by_school, self.taken_by_school)
        if not source_ours:
            enemy = self._enemy(event.source)
            if enemy is not None:
                enemy.damage_done += amount

    def _feed_player_hit(self, event, amount, source_ours):
        player = self._player(event.dest)
        player.damage_taken += amount
        if not source_ours and event.subevent.startswith("SWING_DAMAGE"):
            self._note_melee_taken(event, "hit")
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
        _bank_school(event, amount, block.taken_by_school, self.taken_by_school)
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
        """Who each player was: the specialization id, at one fixed field, and what they wore.

        The latest line wins: a player who changed a piece between two bosses of a key is
        shown with what they had on at the end.
        """
        fields = event.fields
        if len(fields) < 2 or not isinstance(fields[1], str):
            return
        guid = fields[1]
        gear = parse_gear(fields)
        if gear is not None and len(self._gear) < 5000:
            self._gear[guid] = gear
            player = self.players.get(guid)
            if player is not None:
                player.gear = gear
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
        if not event.source.is_hostile or (event.source.is_player
                                           and not self._is_opponent(event.source)):
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
            self._open_with(block)
        else:
            # Still the same pull: whatever was noted since its last damage
            # was part of it, not the opening of the next.
            self._opening_pending = None
            if self._first_hits_pending:
                for guid, hit in self._first_hits_pending.items():
                    block.first_hits.setdefault(guid, hit)
                self._first_hits_pending = {}
        block.end_ts = max(block.end_ts, event.ts)
        return block

    # -- who opened each pull ----------------------------------------------

    def _open_with(self, block):
        """Give a new pull the act noted before its first damage, or wait for one."""
        early, self._first_hits_pending = self._first_hits_pending, {}
        for guid, hit in early.items():
            if block.start_ts - hit[0] <= OPENING_LOOKBACK_MS:
                block.first_hits[guid] = hit
        pending, self._opening_pending = self._opening_pending, None
        self._opening_wait = None
        if pending is not None and block.start_ts - pending[0] <= OPENING_LOOKBACK_MS:
            block.opening = (block.start_ts - pending[0],) + pending[1:]
        else:
            self._opening_wait = block

    def _note_opening(self, event):
        """The first act linking the group and an enemy, in either direction.

        The file has no threat line: an enemy that aggroes a player who
        merely came close is visible only by what it does next -- its first
        swing, cast or debuff on that player, before anyone touched it. The
        report says which side acted first and leaves the verdict to the
        reader: the enemy's first target is a strong hint of who drew it,
        never a proof.
        """
        if event.ts is None:
            return
        link = self._link_of(event)
        if link is None:
            return
        wait = self._opening_wait
        if wait is not None:
            self._opening_wait = None
            if event.ts - wait.start_ts <= OPENING_WAIT_MS:
                wait.opening = (0,) + link
                return
        block = self._block
        if self._opening_pending is None and (block is None or event.ts > block.end_ts):
            self._opening_pending = (event.ts,) + link

    def _link_of(self, event):
        """(side, player, spell, enemy, by a summon, help) or None.

        `side` is "groupe" when the group acted on the enemy, "ennemi" when
        the enemy acted on the group; `player` is the player's ledger, a
        summon's owner when a summon acted or was hit. `help`, only when the
        enemy acted first: (ms before, helped player, spell) if its target
        had just healed or buffed another player -- the aggro it may have
        inherited.
        """
        # GUIDs only while reading, turned into ledgers by
        # `_resolve_openings`: opening a ledger here would change what the
        # aura code banks (it banks only for players already known), and
        # the first version of this did, by a few hundred milliseconds.
        source, dest = event.source, event.dest
        if dest.is_hostile and not source.is_hostile and self._is_ours(source):
            return ("groupe", self.pet_owner.get(source.guid, source.guid), event.spell_name,
                    self._name_of(dest), not source.is_player, None)
        if source.is_hostile and not dest.is_hostile and self._is_ours(dest):
            target = self.pet_owner.get(dest.guid, dest.guid)
            helped = self._last_help.get(target)
            if helped is not None and 0 <= event.ts - helped[0] <= OPENING_HELP_MS:
                helped = (event.ts - helped[0],) + helped[1:]
            else:
                helped = None
            return ("ennemi", target, event.spell_name, self._name_of(source),
                    not dest.is_player, helped)
        return None

    def _note_help(self, event):
        """A heal that healed, a buff or a dispel, from one player to another.

        What draws an enemy's attention to the helper, in the owner's words
        (2026-09-29): a heal received, a buff (damage, defence, speed), a
        debuff removed.
        """
        source, dest = event.source, event.dest
        if (event.ts is None or not source.is_player or not dest.is_player
                or source.guid == dest.guid or source.is_hostile or dest.is_hostile):
            return
        if event.suffix_kind == "_HEAL":
            if event.effective_healing <= 0:
                return     # a full-health player: no healing, no threat
        elif event.suffix_kind == "_AURA_APPLIED" and (event.aura_type or "BUFF") != "BUFF":
            return
        self._last_help[source.guid] = (event.ts, dest.guid, event.spell_name)

    def _note_first_hit(self, event):
        """The first hit, landed or missed, each enemy unit takes in a pull.

        Unlike the opener, this is certain: the line says who hit whom. A
        summon's hit is its owner's. GUIDs only, resolved at the end.
        """
        source, dest = event.source, event.dest
        if (event.ts is None or not dest.is_hostile or source.is_hostile
                or not self._is_ours(source) or not dest.guid):
            return
        hit = (event.ts, self.pet_owner.get(source.guid, source.guid), event.spell_name,
               not source.is_player, self._name_of(dest))
        block = self._block
        if block is not None and event.ts <= block.end_ts:
            hits = block.first_hits
        else:
            hits = self._first_hits_pending
        if dest.guid not in hits and len(hits) < MAX_FIRST_HITS:
            hits[dest.guid] = hit

    def _resolve_openings(self):
        """The GUIDs noted by `_note_opening`, as ledgers; None if nobody is known."""
        for block in self.blocks:
            if block.opening is None or not isinstance(block.opening[2], str):
                continue
            lead, side, guid, spell, enemy, by_summon, helped = block.opening
            player = self.players.get(guid)
            if player is None:
                block.opening = None
                continue
            if helped is not None:
                other = self.players.get(helped[1])
                helped = (helped[0], other, helped[2]) if other is not None else None
            block.opening = (lead, side, player, spell, enemy, by_summon, helped)
        for block in self.blocks:
            if isinstance(block.first_hits, list):
                continue      # already resolved: finish() may run twice
            resolved = []
            hits = sorted(block.first_hits.values(), key=lambda hit: hit[0])
            for ts, guid, spell, by_summon, enemy in hits:
                player = self.players.get(guid)
                if player is not None:
                    resolved.append((ts, enemy, player, spell, by_summon))
            block.first_hits = resolved

    def _feed_instakill(self, event):
        """A player killed outright: the cause of death, with no amount at all.

        SPELL_INSTAKILL carries no damage and no overkill, so the chain
        before such a death held only heals and the page named no killing
        blow: 3 of the 5 deaths without one on a real raid night, 11 such
        lines on a Mythic+ night. It goes into the chain marked as the
        fatal moment, with nothing to add to any total.
        """
        if event.dest.is_player and self._is_ours(event.dest):
            self._player(event.dest).recent.append(
                (event.ts, self._name_of(event.source), event.spell_name, 0, None, 1))

    def _feed_missed(self, event):
        """An enemy's melee swing at a player that did not land: how it failed."""
        if event.subevent != "SWING_MISSED" or not event.dest.is_player:
            return
        source_ours, dest_ours = self._damage_sides(event)
        if dest_ours and not source_ours:
            self._note_melee_taken(event, event.miss_type or "?")

    def _note_melee_taken(self, event, outcome):
        """One enemy swing at a player: how it ended, and from which side."""
        taken = self._melee_taken.get(event.dest.guid)
        if taken is None:
            if len(self._melee_taken) >= 5000:
                return
            taken = self._melee_taken[event.dest.guid] = {}
        if outcome not in taken and len(taken) >= MAX_MELEE_KEYS:
            outcome = "?"
        taken[outcome] = taken.get(outcome, 0) + 1
        if outcome == "hit":
            if event.is_critical:
                taken["crit"] = taken.get("crit", 0) + 1
            if event.blocked > 0:
                taken["partial_block"] = taken.get("partial_block", 0) + 1
            side = self._melee_side(event) or "unplaced"
            taken[side] = taken.get(side, 0) + 1
        elif outcome in ("PARRY", "DODGE"):
            side = self._melee_side(event)
            if side is not None:
                key = "avoided_" + side
                taken[key] = taken.get(key, 0) + 1

    def _note_position(self, event):
        """Remember where the unit an advanced block describes stood, and faced."""
        guid = event.advanced.info_guid
        if not guid:
            return
        where = self._where
        if guid not in where and len(where) >= MAX_POSITIONS:
            cutoff = event.ts - POSITION_STALE_MS
            for stale in [key for key, (ts, _adv) in where.items() if ts < cutoff]:
                del where[stale]
            if len(where) >= MAX_POSITIONS:
                return
        where[guid] = (event.ts, event.advanced)

    def _melee_side(self, event):
        """"front" or "behind": where the attacker stood as the victim faced, or None.

        An estimate, never a fact of the file: see `POSITION_STALE_MS`.
        None when either end has no recent position, or when both stand
        on the same spot, where no side can be told.
        """
        victim = self._where.get(event.dest.guid)
        attacker = self._where.get(event.source.guid)
        if (victim is None or attacker is None or event.ts - victim[0] > POSITION_STALE_MS
                or event.ts - attacker[0] > POSITION_STALE_MS):
            return None
        try:
            facing = float(victim[1].facing)
            dx = float(attacker[1].position_x) - float(victim[1].position_x)
            dy = float(attacker[1].position_y) - float(victim[1].position_y)
        except (TypeError, ValueError):
            return None
        if not (math.isfinite(facing) and math.isfinite(dx) and math.isfinite(dy)):
            return None
        if abs(dx) + abs(dy) < 0.05:
            return None
        # The facing is an angle from the x axis, towards y: the reading
        # that put 97% of parries in front, where the three others tried
        # put 47% to 57% -- a coin toss.
        return "front" if dx * math.cos(facing) + dy * math.sin(facing) > 0 else "behind"

    def _feed_landed(self, event):
        """A resolved melee hit: the group's health, and the melee it took.

        Never a total for melee the group *dealt*: there it is the same hit
        as SWING_DAMAGE, written twice. For melee the group *took* it is the
        one line counted (see `_feed_damage`).
        """
        self.landed_seen += 1
        if event.dest.is_player and self._is_ours(event.dest):
            self._track_hp(event, self._player(event.dest))
        if self._is_ours(event.dest):
            self._feed_damage(event)

    def _feed_heal(self, event):
        effective = event.effective_healing
        if (not event.source.is_player and event.dest.is_player
                and self._is_ours(event.source) and self._is_ours(event.dest)
                and len(self._moving_units) < 1000):
            self._moving_units.add((event.source.guid, event.spell_id))
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
                    target = OTHER_TARGETS
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
        if len(player.cast_log) < MAX_CAST_LOG:
            advanced = event.advanced
            paid = (advanced is not None and advanced.info_guid == event.source.guid
                    and advanced.paid_power)
            # The last field is "" for the player's own casts and the
            # summon's GUID for a summon's: still false and true where it
            # is read as a flag, and what `_disown_mechanics` looks for.
            player.cast_log.append((event.ts, event.spell_id, event.spell_name or "?",
                                    bool(paid), "" if event.source.is_player
                                    else event.source.guid))
        else:
            player.cast_log_full = True
        if not event.source.is_player:
            # A pet or a guardian casting is not the player pressing a
            # button: counted in `casts` above, but never an end to the
            # player's own pause. A hunter's pet biting every second hid
            # forty seconds without a single cast (audit of 2026-09-29).
            return
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
                killing_blow = "%s (%s)" % (spell_label(moment[2]), moment[1] or "?")
                break
        if not killing_blow:
            for moment in reversed(chain):
                if moment[3] < 0:
                    killing_blow = "%s (%s)" % (spell_label(moment[2]), moment[1] or "?")
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
        self._settle_moves()
        if self._encounter is not None:
            self._close_encounter(end, None)
        self._pick_main_target()
        # Whatever is still pending never completed and nothing here can
        # say why: a stun, a fear, a knockback, the caster walking out of
        # range. The file does not label a spell as crowd control, so this
        # bucket is named for what is known rather than guessed at.
        self.enemy_casts["autre"] += len(self._pending_casts)
        self._pending_casts = {}
        self._resolve_openings()

        self._drop_crumbs()
        # An aura still up when the pull ended counts to the end of it,
        # not to the last event that happened to mention it.
        for (guid, spell_id, _source), opened in list(self.aura_open.items()):
            self._bank_aura(guid, spell_id, opened, end)
        self.aura_open = {}

        self._disown_mechanics()
        self._settle_melee_taken()
        self._close_downtime(end)
        self._collapse_timeline()
        for player in self.players.values():
            player.triggered = classify_triggered(player.cast_log)

    def _settle_melee_taken(self):
        """The swings counted while reading, into the ledgers of the players who took them.

        Only a ledger that exists: a player whom the enemy only ever swung
        at and missed, and who did nothing else, has no row to carry them.
        """
        for guid, taken in self._melee_taken.items():
            player = self.players.get(guid)
            if player is not None:
                player.melee_taken = taken
        self._melee_taken = {}

    def _drop_crumbs(self):
        # Drop the stray ticks, but never drop the only pull there is.
        if len(self.blocks) > 1 and self.total_damage > 0:
            floor = self.total_damage * MIN_PULL_SHARE
            kept = [block for block in self.blocks if block.damage_done >= floor]
            self.dropped_pulls = len(self.blocks) - len(kept)
            if kept:
                self.blocks = kept

    def _close_downtime(self, end):
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

    # -- readers the report uses ------------------------------------------

    @property
    def duration_ms(self):
        if self.segment.duration_ms:
            return self.segment.duration_ms
        if self.first_ts is not None and self.last_ts is not None:
            return max(0, self.last_ts - self.first_ts)
        return 0

    def ranked_players(self, key):
        """[(player, value, per second)] for one ledger, largest first."""
        seconds = max(1.0, self.duration_ms / 1000.0)
        rows = []
        for player in self.players.values():
            value = getattr(player, key)
            if value:
                rows.append((player, value, value / seconds))
        rows.sort(key=lambda row: row[1], reverse=True)
        return rows

    def top_abilities(self, store, limit=12):
        """The `limit` abilities of one store with the largest totals."""
        return sorted(store.values(), key=lambda ability: ability.total, reverse=True)[:limit]

    @property
    def has_several_pulls(self):
        """True when a pull table would say something a total cannot."""
        return len(self.blocks) > 1

    def ranked_enemies(self, key="damage_done", limit=20):
        """Enemies (grouped by name) by one ledger, largest first."""
        rows = [
            enemy
            for enemy in self.enemies.values()
            if getattr(enemy, key) or enemy.casts or enemy.deaths
        ]
        rows.sort(key=lambda enemy: -getattr(enemy, key))
        return rows[:limit]

    @staticmethod
    def took_part(player):
        """True when a player did or suffered something in the fight itself.

        Casting is not enough: on the owner's failed +14, two players who
        had joined the group for the next key cast a buff in the last
        seconds before CHALLENGE_MODE_END, and a five-player dungeon was
        listed with seven. They are named apart (`bystanders`), not hidden.
        """
        return bool(player.damage_done or player.healing_done or player.damage_taken
                    or player.absorb_done or player.absorbed_taken or player.pet_damage_taken
                    or player.deaths or player.support_damage or player.support_healing)

    def participants(self):
        """The players who took part, in no particular order."""
        return [player for player in self.players.values() if self.took_part(player)]

    def bystanders(self):
        """Players the file shows only casting: present, but not in the fight."""
        return sorted((player for player in self.players.values()
                       if player.casts and not self.took_part(player)),
                      key=lambda player: player.short_name.lower())

    def composition(self):
        """[(label, [players])] -- tanks, healers, then everyone else."""
        from .specs import DPS, HEAL, TANK, role_of

        groups = {TANK: [], HEAL: [], DPS: [], "": []}
        for player in self.participants():
            groups.setdefault(role_of(player.spec_id), []).append(player)
        for players in groups.values():
            players.sort(key=lambda player: player.short_name.lower())
        return [
            (label, groups[role])
            for role, label in ((TANK, _("Tanks")), (HEAL, _("Soigneurs")), (DPS, "DPS"),
                                ("", _("Rôle non indiqué")))
            if groups[role]
        ]

    # Which reader each suffix goes to. SWING_DAMAGE and SWING_DAMAGE_LANDED
    # describe the same hits, and adding both doubled every melee total (on
    # a real 12.1.0 log, 5,943 of 6,135 pairs sharing a timestamp, a source
    # and a target carried identical amounts). Which one counts depends on
    # the side: SWING_DAMAGE for melee the group dealt, where the two agree
    # to the unit; _LANDED for melee it took, which the client writes more
    # completely (see `_feed_damage`). _LANDED's advanced block describes
    # the *target* (7,561 of 7,561), SWING_DAMAGE's the attacker.
    _BY_SUFFIX = {
        "_DAMAGE_LANDED": _feed_landed,
        "_DAMAGE": _feed_damage,
        "_MISSED": _feed_missed,
        "_SHIELD": _feed_damage,
        "_SPLIT": _feed_damage,
        "_HEAL": _feed_heal,
        "_CAST_SUCCESS": _feed_cast_success,
        "_INTERRUPT": _feed_interrupt,
        "_DISPEL": _feed_dispel,
        "_STOLEN": _feed_dispel,
        "_CAST_START": _feed_enemy_cast_start,
        "_INSTAKILL": _feed_instakill,
        "_AURA_APPLIED": AuraLedger._aura_open,
        "_AURA_REFRESH": AuraLedger._aura_open,
        "_AURA_REMOVED": AuraLedger._aura_close,
    }


def _bank_school(event, amount, *ledgers):
    """Add one hit to each {school mask: amount} ledger."""
    _bank_mask(event.damage_school, amount, *ledgers)


def _bank_mask(school, amount, *ledgers):
    """Add an amount of one school mask to each {school mask: amount} ledger."""
    if not 0 < school <= 127:       # a damaged line: one "unknown" key, not one per value
        school = 0
    for ledger in ledgers:
        ledger[school] = ledger.get(school, 0) + amount
