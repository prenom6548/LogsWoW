"""The timeline, the pooled enemy health, and the main target's curve.

Everything the analysis keeps *in time* rather than in totals: damage
taken per bucket, the engaged enemies' pooled health read once per
bucket, and the per-unit health samples from which the curve of the
unit the group spent the fight killing is chosen at the end. Every
structure here is bounded; the constants below say by how much.
`SegmentAnalysis` inherits this and owns the state it uses.
"""

# However long the fight, the drawn timeline has at most this many
# buckets: longer fights are collapsed at the end by `_collapse_timeline`.
MAX_TIMELINE_BUCKETS = 400

# An enemy the group has not touched for this long is no longer "engaged":
# it walked off, reset, or despawned without a UNIT_DIED, and it must stop
# weighing on the pooled health curve.
POOL_STALE_MS = 30000

# Bounds on the per-enemy health sampling, so a 20-minute key cannot grow
# without limit while it works out which unit was the main target.
MAX_TRACKED_ENEMIES = 40
KEEP_TRACKED_ENEMIES = 20
MAX_HP_SAMPLES = 400

# Damage is banked per enemy GUID while the analysis works out which
# single unit the group spent the fight killing. That is one entry per
# distinct unit met, and a long run meets a great many: 150,000 of them
# on a 48 MB test file, which took peak memory to 56 MB on their own.
# Only the leaders can ever win that ranking, so the tail is dropped.
MAX_DAMAGED_UNITS = 5000
KEEP_DAMAGED_UNITS = 500


class TimelineLedger:
    """The time-series half of `SegmentAnalysis`."""

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
        if advanced.current_hp > advanced.max_hp:
            # A reading that contradicts itself does not vote. A real key
            # wrote one unit at 3,814,068 health out of a maximum of 24,
            # and the pooled curve went to 8,724,400%: which of the two
            # fields is wrong the file does not say, so neither is used.
            self.inconsistent_health += 1
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

    def _sample_enemy_health(self, event):
        guid = event.dest.guid
        fraction = event.advanced.health_fraction
        if fraction is None:
            return
        if event.advanced.current_hp > event.advanced.max_hp:
            # Same rule as the pool: clamped to 100%, this would draw a
            # health the file never actually gave.
            self.inconsistent_health += 1
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

    def _prune_damaged_units(self):
        """Keep only the units that could still be the main target.

        The ranking in `finish` reads the top of this table and nothing
        else, so a unit sitting far below the leaders cannot change the
        answer. Whatever is still being sampled for its health is kept
        too, so the two tables cannot disagree about who exists.
        """
        ranked = sorted(
            self._enemy_damage, key=lambda guid: -self._enemy_damage[guid]
        )
        keep = set(ranked[:KEEP_DAMAGED_UNITS])
        keep.update(self._hp_samples)
        self._enemy_damage = {
            guid: amount for guid, amount in self._enemy_damage.items()
            if guid in keep
        }
        self._enemy_names = {
            guid: name for guid, name in self._enemy_names.items()
            if guid in keep
        }

    def _prune_tracked_enemies(self):
        """Keep sampling only the units worth being the main target."""
        ranked = sorted(
            self._hp_samples,
            key=lambda guid: -self._enemy_damage.get(guid, 0),
        )
        for guid in ranked[KEEP_TRACKED_ENEMIES:]:
            self._hp_samples.pop(guid, None)

    def _pick_main_target(self):
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

    def _collapse_timeline(self):
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
