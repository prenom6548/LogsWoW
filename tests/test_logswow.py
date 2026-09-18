"""Tests for LogsWoW. Standard library only: `python3 tests/run-tests.py`.

Two kinds of test live here and they are worth telling apart.

The *layout* tests assert that a field is read from the right place even
when Blizzard moves it. They are written against both the layout two
real 12.1.0 logs were measured to use and the older one the published
documentation describes, because the whole parser was built on the
second and the first proved it wrong. A test that only covers today's
client would have passed on the day the reader was broken.

The *behaviour* tests run the fabricated fixture end to end. They assert
on which functions did what, not only on the numbers that came out --
a filter can be entirely absent and still produce a plausible total.
"""

import os
import sys
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
sys.path.insert(0, ROOT)

from logswow.analysis import SegmentAnalysis  # noqa: E402
from logswow.events import Advanced, Layout, build_event, decompose  # noqa: E402
from logswow.parse import LogFile, detect_layout  # noqa: E402
from logswow.report import ReportWriter, plural  # noqa: E402
from logswow.segment import Splitter, difficulty_name  # noqa: E402
from logswow.timestamps import TimestampReader, format_duration  # noqa: E402
from logswow.tokenize import looks_like_guid, split_fields, split_line  # noqa: E402

FIXTURE = os.path.join(ROOT, "examples", "exemple-combat.txt")

MODERN = Layout(advanced_width=19, has_base_amount=True)
DOCUMENTED = Layout(advanced_width=17, has_base_amount=False)


def advanced_block(width, info="Player-1", hp=500, maxhp=1000):
    """A block of `width` fields whose two ends carry the known values."""
    head = [info, "0000000000000000", str(hp), str(maxhp), "10", "20", "30", "40"]
    tail = ["1", "111", "222", "0", "12.5", "-34.5", "2393", "3.14", "80"]
    middle = ["0"] * (width - len(head) - len(tail))
    return head + middle + tail


def event_from(payload, layout=MODERN):
    _ts, fields = split_line("9/18/2026 20:15:31.123-4  " + payload)
    return build_event(0, fields, 1, layout)


class TestTokenize(unittest.TestCase):
    def test_commas_inside_quotes_stay_together(self):
        fields = split_fields('SPELL_DAMAGE,P,"Garde, le Brise-Fer",0x1')
        self.assertEqual(fields[2], "Garde, le Brise-Fer")

    def test_nested_groups_become_lists(self):
        fields = split_fields("COMBATANT_INFO,P,0,[(1,2),(3,4)],5")
        self.assertEqual(fields[3], [["1", "2"], ["3", "4"]])
        self.assertEqual(fields[4], "5")

    def test_genuinely_empty_fields_survive(self):
        self.assertEqual(split_fields("A,,B"), ["A", "", "B"])

    def test_unterminated_quote_does_not_raise(self):
        self.assertEqual(split_fields('X,"never closed'), ["X", "never closed"])

    def test_line_without_separator_is_rejected(self):
        self.assertEqual(split_line("pas une ligne"), (None, None))

    def test_guid_detection(self):
        self.assertTrue(looks_like_guid("Player-9999-0A1B2C3D"))
        self.assertTrue(looks_like_guid("0000000000000000"))
        self.assertFalse(looks_like_guid("1"))
        self.assertFalse(looks_like_guid(""))


class TestTimestamps(unittest.TestCase):
    def test_four_shapes_parse(self):
        for text in (
            "9/18/2026 20:15:31.123-4",
            "9/18/2026 20:15:31.1230000-7",
            "9/18 20:15:31.123",
            "2026-09-18T20:15:31.123-04:00",
        ):
            self.assertIsNotNone(TimestampReader(2026).read(text), text)

    def test_junk_returns_none_and_is_counted(self):
        reader = TimestampReader(2026)
        self.assertIsNone(reader.read("pas une date"))
        self.assertEqual(reader.unparsed, 1)

    def test_midnight_needs_no_special_case(self):
        """Every shape carries the date, so the client rolls it itself."""
        reader = TimestampReader(2026)
        before = reader.read("9/18 23:59:59.500")
        after = reader.read("9/19 00:00:01.500")
        self.assertEqual(after - before, 2000)

    def test_new_year_rolls_the_year_forward(self):
        """The one case a year-less timestamp cannot express on its own."""
        reader = TimestampReader(2026)
        before = reader.read("12/31 23:59:59.000")
        after = reader.read("1/1 00:00:01.000")
        self.assertEqual(after - before, 2000)

    def test_an_out_of_order_line_near_midnight_shifts_nothing(self):
        """This broke: one line out of order rolled every later timestamp
        a whole day forward, and only a fixture caught it."""
        reader = TimestampReader(2026)
        reader.read("9/18 23:59:51.000")
        reader.read("9/19 00:00:01.000")
        stray = reader.read("9/18 23:59:52.000")  # out of order, as real logs are
        after = reader.read("9/19 00:00:30.000")
        self.assertEqual(after - stray, 38000)

    def test_out_of_order_line_does_not_trigger_a_rollover(self):
        reader = TimestampReader(2026)
        first = reader.read("9/18 20:00:10.000")
        second = reader.read("9/18 20:00:09.000")
        self.assertEqual(second - first, -1000)

    def test_format_duration(self):
        self.assertEqual(format_duration(0), "0:00")
        self.assertEqual(format_duration(125000), "2:05")
        self.assertEqual(format_duration(3725000), "1:02:05")
        self.assertEqual(format_duration(None), "?")


class TestDamageLayouts(unittest.TestCase):
    """The same hit, written three ways, must read the same."""

    def _spell_damage(self, layout, suffix):
        block = ",".join(advanced_block(layout.advanced_width, "Creature-1"))
        return event_from(
            'SPELL_DAMAGE,Player-1,"A",0x511,0x0,Creature-1,"B",0xa48,0x0,'
            '1,"Frappe",0x1,%s,%s' % (block, suffix),
            layout,
        )

    def test_modern_layout(self):
        event = self._spell_damage(MODERN, "5000,7000,-1,1,0,0,300,1,nil,nil,ST")
        self.assertEqual(event.amount, 5000)
        self.assertEqual(event.unmitigated, 7000)
        self.assertEqual(event.overkill, -1)
        self.assertEqual(event.absorbed, 300)
        self.assertTrue(event.is_critical)
        self.assertEqual(event.damage_tag, "ST")
        self.assertIsNone(event.mismatch)

    def test_documented_layout_reads_the_same_hit(self):
        event = self._spell_damage(DOCUMENTED, "5000,-1,1,0,0,300,1,nil,nil,nil")
        self.assertEqual(event.amount, 5000)
        self.assertEqual(event.overkill, -1)
        self.assertEqual(event.absorbed, 300)
        self.assertTrue(event.is_critical)
        self.assertIsNone(event.mismatch)

    def test_swing_has_no_trailing_tag(self):
        block = ",".join(advanced_block(19, "Creature-1"))
        event = event_from(
            'SWING_DAMAGE,Player-1,"A",0x511,0x0,Creature-1,"B",0xa48,0x0,%s,'
            "900,1200,-1,1,0,0,0,nil,nil,nil" % block,
            MODERN,
        )
        self.assertEqual(event.amount, 900)
        self.assertEqual(event.overkill, -1)
        self.assertEqual(event.damage_tag, "")
        self.assertIsNone(event.mismatch)

    def test_killing_blow_reports_overkill(self):
        event = self._spell_damage(MODERN, "9000,9000,3000,1,0,0,0,1,nil,nil,ST")
        self.assertEqual(event.overkill, 3000)

    def test_no_advanced_block_at_all(self):
        event = event_from(
            'SPELL_DAMAGE,Player-1,"A",0x511,0x0,Creature-1,"B",0xa48,0x0,'
            '1,"Frappe",0x1,5000,7000,-1,1,0,0,0,nil,nil,nil,ST',
            MODERN,
        )
        self.assertIsNone(event.advanced)
        self.assertEqual(event.amount, 5000)
        self.assertIsNone(event.mismatch)

    def test_a_shape_nobody_knows_is_reported_not_guessed(self):
        event = event_from(
            'SPELL_DAMAGE,Player-1,"A",0x511,0x0,Creature-1,"B",0xa48,0x0,1,"F",0x1,1,2,3',
            MODERN,
        )
        self.assertIsNotNone(event.mismatch)


class TestHealLayouts(unittest.TestCase):
    def _heal(self, layout, suffix):
        block = ",".join(advanced_block(layout.advanced_width, "Player-2"))
        return event_from(
            'SPELL_HEAL,Player-1,"A",0x511,0x0,Player-2,"B",0x512,0x0,'
            '9,"Soin",0x2,%s,%s' % (block, suffix),
            layout,
        )

    def test_modern_heal(self):
        event = self._heal(MODERN, "1000,1200,300,50,1")
        self.assertEqual(event.amount, 1000)
        self.assertEqual(event.overhealing, 300)
        self.assertEqual(event.healing_absorbed, 50)
        self.assertEqual(event.effective_healing, 650)
        self.assertTrue(event.is_critical)

    def test_documented_heal_reads_the_same(self):
        event = self._heal(DOCUMENTED, "1000,300,50,1")
        self.assertEqual(event.effective_healing, 650)
        self.assertTrue(event.is_critical)

    def test_a_full_overheal_is_not_negative(self):
        event = self._heal(MODERN, "749,749,749,0,nil")
        self.assertEqual(event.effective_healing, 0)


class TestNonDamageEventsStayClean(unittest.TestCase):
    """An aura must not answer questions only damage can answer."""

    def setUp(self):
        self.aura = event_from(
            'SPELL_AURA_APPLIED,Player-1,"A",0x511,0x0,Player-1,"A",0x511,0x0,'
            '77,"Bouclier",0x2,BUFF'
        )

    def test_aura_type(self):
        self.assertEqual(self.aura.aura_type, "BUFF")

    def test_aura_has_no_overkill_or_crit(self):
        self.assertEqual(self.aura.overkill, 0)
        self.assertEqual(self.aura.absorbed, 0)
        self.assertFalse(self.aura.is_critical)
        self.assertEqual(self.aura.overhealing, 0)

    def test_interrupt_names_the_interrupted_spell(self):
        event = event_from(
            'SPELL_INTERRUPT,Player-1,"A",0x511,0x0,Creature-1,"B",0xa48,0x0,'
            '10,"Coup",0x1,555,"Incantation",0x20'
        )
        self.assertEqual(event.extra_spell_id, 555)
        self.assertEqual(event.extra_spell_name, "Incantation")

    def test_stagger_events_are_recognised_not_broken(self):
        event = event_from("STAGGER_CLEAR,Player-1,1199.5")
        self.assertIsNone(event.mismatch)


class TestAdvancedBlock(unittest.TestCase):
    def test_both_ends_are_read_at_either_width(self):
        for width in (17, 19, 21):
            block = Advanced(advanced_block(width, "Player-9", hp=250, maxhp=1000))
            self.assertEqual(block.info_guid, "Player-9", width)
            self.assertEqual(block.current_hp, 250, width)
            self.assertEqual(block.max_hp, 1000, width)
            self.assertEqual(block.health_fraction, 0.25, width)
            self.assertEqual(block.ui_map_id, 2393, width)
            self.assertEqual(block.level, 80, width)
            self.assertEqual(block.position_x, "12.5", width)

    def test_missing_max_hp_gives_no_fraction(self):
        self.assertIsNone(Advanced(advanced_block(19, "P", hp=5, maxhp=0)).health_fraction)


class TestDecompose(unittest.TestCase):
    def test_longest_suffix_wins(self):
        self.assertEqual(decompose("SPELL_AURA_APPLIED_DOSE")[2], "_AURA_APPLIED_DOSE")
        self.assertEqual(decompose("SPELL_PERIODIC_DAMAGE")[0], "SPELL_PERIODIC")
        self.assertEqual(decompose("SWING_DAMAGE")[1], 0)

    def test_unknown_name_returns_none(self):
        self.assertIsNone(decompose("SPELL_BANANE"))


class TestLayoutDetection(unittest.TestCase):
    def test_measured_from_the_fixture(self):
        log = LogFile(FIXTURE)
        list(log.events())
        self.assertEqual(log.layout.advanced_width, 19)
        self.assertTrue(log.layout.has_base_amount)
        self.assertFalse(log.layout.hide_caster)

    def test_the_old_layout_is_detected_too(self):
        """A file whose -1 sits one field earlier must be read that way."""
        samples = []
        for _ in range(40):
            _ts, fields = split_line(
                "9/18/2026 20:15:31.123-4  "
                'SPELL_DAMAGE,Player-1,"A",0x511,0x0,Creature-1,"B",0xa48,0x0,'
                '1,"F",0x1,%s,5000,-1,1,0,0,0,nil,nil,nil'
                % ",".join(advanced_block(17, "Creature-1"))
            )
            samples.append(fields)
        layout = detect_layout(samples)
        self.assertEqual(layout.advanced_width, 17)
        self.assertFalse(layout.has_base_amount)

    def test_hide_caster_is_detected_when_present(self):
        samples = []
        for _ in range(40):
            _ts, fields = split_line(
                "9/18/2026 20:15:31.123-4  "
                'SPELL_AURA_APPLIED,nil,Player-1,"A",0x511,0x0,Player-1,"A",0x511,0x0,'
                '77,"B",0x2,BUFF'
            )
            samples.append(fields)
        self.assertTrue(detect_layout(samples).hide_caster)


def run_fixture():
    log = LogFile(FIXTURE)
    splitter = Splitter(analysis_factory=SegmentAnalysis)
    for event in log.events():
        splitter.feed(event)
    return log, splitter.finish()


class TestSegments(unittest.TestCase):
    def setUp(self):
        self.log, self.segments = run_fixture()

    def test_every_marked_fight_is_found(self):
        self.assertEqual(len(self.segments), 3)
        self.assertEqual(
            [s.kind for s in self.segments], ["encounter", "encounter", "keystone"]
        )

    def test_outcomes_are_read_from_the_end_marker(self):
        self.assertTrue(self.segments[0].success)
        self.assertFalse(self.segments[1].success)
        self.assertEqual(self.segments[0].outcome, "reussite")
        self.assertEqual(self.segments[1].outcome, "echec")

    def test_pull_crossing_midnight_has_a_positive_duration(self):
        self.assertGreater(self.segments[1].duration_ms, 0)

    def test_indices_are_contiguous_from_one(self):
        self.assertEqual([s.index for s in self.segments], [1, 2, 3])

    def test_difficulty_is_named_or_numbered_never_guessed(self):
        self.assertEqual(difficulty_name(16), "Mythique")
        self.assertEqual(difficulty_name(999), "difficulte 999")

    def test_a_keystone_contains_its_boss_pulls(self):
        splitter = Splitter()
        for payload in (
            'CHALLENGE_MODE_START,"Donjon d\'essai",2000,500,7,[165]',
            'ENCOUNTER_START,1,"Boss",8,5,2000',
            'ENCOUNTER_END,1,"Boss",8,5,1,1000',
            "CHALLENGE_MODE_END,2000,1,7,600000",
        ):
            _ts, fields = split_line("9/18/2026 20:15:31.123-4  " + payload)
            splitter.feed(build_event(0, fields, 1))
        segments = splitter.finish()
        self.assertEqual([s.kind for s in segments], ["keystone", "encounter"])
        self.assertEqual(segments[0].key_level, 7)
        self.assertEqual(segments[0].affixes, [165])

    def test_an_unfinished_pull_is_marked_truncated(self):
        splitter = Splitter()
        _ts, fields = split_line(
            '9/18/2026 20:15:31.123-4  ENCOUNTER_START,1,"Boss",16,20,2000'
        )
        splitter.feed(build_event(0, fields, 1))
        segments = splitter.finish()
        self.assertTrue(segments[0].truncated)
        self.assertEqual(segments[0].outcome, "interrompu")


class TestAnalysis(unittest.TestCase):
    def setUp(self):
        self.log, self.segments = run_fixture()
        self.first = self.segments[0].analysis
        self.second = self.segments[1].analysis

    def _player(self, analysis, name):
        for player in analysis.players.values():
            if player.short_name == name:
                return player
        self.fail("joueur absent : %s" % name)

    def test_damage_is_attributed_to_the_right_player(self):
        braise = self._player(self.first, "Braise")
        self.assertEqual(braise.damage_done, 6 * 5000 + 9000 + 6 * 700)

    def test_a_pet_is_not_a_separate_player(self):
        names = {player.short_name for player in self.first.players.values()}
        self.assertNotIn("Cendre", names)

    def test_pet_damage_lands_on_its_owner_by_ability(self):
        braise = self._player(self.first, "Braise")
        abilities = {ability.name for ability in braise.damage_by_ability.values()}
        self.assertIn("Morsure", abilities)

    def test_a_swing_written_twice_is_counted_once(self):
        """SWING_DAMAGE and SWING_DAMAGE_LANDED are one hit, not two."""
        ardoise = self._player(self.first, "Ardoise")
        self.assertEqual(ardoise.damage_done, 6 * 900)
        self.assertEqual(self.first.landed_seen, 6)

    def test_damage_taken_is_recorded_for_the_target(self):
        ardoise = self._player(self.first, "Ardoise")
        self.assertEqual(ardoise.damage_taken, 30000)

    def test_effective_healing_excludes_overheal(self):
        """Two heals in the fixture: 25000 with 5000 wasted on the tank,
        then 4000 with 1000 wasted on the damage dealer."""
        tisane = self._player(self.first, "Tisane")
        self.assertEqual(tisane.healing_done, (25000 - 5000) + (4000 - 1000))
        self.assertEqual(tisane.overhealing, 5000 + 1000)

    def test_interrupts_are_counted(self):
        self.assertEqual(self._player(self.first, "Ardoise").interrupts, 1)

    def test_aura_uptime_is_measured_between_apply_and_remove(self):
        ardoise = self._player(self.first, "Ardoise")
        uptimes = dict(
            (name, milliseconds)
            for name, _id, milliseconds in self.first.player_uptimes(ardoise.guid)
        )
        self.assertEqual(uptimes["Peau de pierre"], 10000)

    def test_a_death_is_recorded_with_its_killing_blow(self):
        self.assertEqual(len(self.second.deaths), 1)
        death = self.second.deaths[0]
        self.assertEqual(death["player"], "Tisane")
        self.assertIn("Balayage", death["killing_blow"])

    def test_the_death_chain_holds_the_hits_before_it(self):
        chain = self.second.deaths[0]["chain"]
        self.assertGreaterEqual(len(chain), 2)
        self.assertTrue(all(len(moment) == 6 for moment in chain))
        self.assertTrue(any(moment[3] < 0 for moment in chain))

    def test_the_killing_blow_is_the_hit_the_log_marks_with_an_overkill(self):
        """Not simply the last damaging event. On a real log that named a
        post-death redistribution from a Spirit Link Totem instead of the
        hit that actually killed."""
        chain = self.second.deaths[0]["chain"]
        marked = [moment for moment in chain if moment[5] > 0]
        self.assertEqual(len(marked), 1)
        self.assertIn(marked[0][2], self.second.deaths[0]["killing_blow"])

    def test_health_fraction_is_taken_from_the_advanced_block(self):
        tisane = self._player(self.second, "Tisane")
        self.assertEqual(tisane.min_hp_fraction, 0.0)

    def test_downtime_counts_the_tail_of_the_pull_not_only_the_gaps(self):
        braise = self._player(self.second, "Braise")
        self.assertGreater(braise.downtime_ms, 0)

    def test_the_timeline_is_bounded_and_evenly_spaced(self):
        series, bucket_ms = self.first.timeline_series()
        self.assertGreater(bucket_ms, 0)
        self.assertLessEqual(len(series), 401)
        if len(series) > 1:
            step = series[1][0] - series[0][0]
            self.assertAlmostEqual(series[-1][0] - series[-2][0], step, places=6)

    def test_a_boss_health_curve_is_built_without_a_boss_database(self):
        self.assertGreaterEqual(len(self.first.boss_hp), 2)
        self.assertLessEqual(self.first.boss_hp[-1][1], self.first.boss_hp[0][1])


class TestPulls(unittest.TestCase):
    """A run is several fights, and the file can say which."""

    def setUp(self):
        self.log, self.segments = run_fixture()
        self.boss = self.segments[0].analysis
        self.key = self.segments[2].analysis

    def test_a_boss_pull_is_one_pull(self):
        self.assertEqual(len(self.boss.blocks), 1)
        self.assertFalse(self.boss.has_several_pulls)

    def test_a_key_is_split_where_the_fighting_stopped(self):
        self.assertEqual(len(self.key.blocks), 2)
        self.assertTrue(self.key.has_several_pulls)

    def test_each_pull_names_what_was_engaged_and_how_many(self):
        labels = [block.label() for block in self.key.blocks]
        self.assertIn("Sbire d'essai x2", labels[0])
        self.assertIn("Brute d'essai", labels[1])

    def test_pull_totals_add_up_to_the_run(self):
        self.assertEqual(
            sum(block.damage_done for block in self.key.blocks),
            sum(player.damage_done for player in self.key.players.values()),
        )

    def test_a_longer_gap_merges_the_two_pulls(self):
        """The threshold is a judgement call, so it is tunable and tested."""
        from logswow.parse import LogFile as _LogFile

        log = _LogFile(FIXTURE)
        splitter = Splitter(
            analysis_factory=lambda segment: SegmentAnalysis(segment, pull_gap_ms=120000)
        )
        for event in log.events():
            splitter.feed(event)
        key = splitter.finish()[2].analysis
        self.assertEqual(len(key.blocks), 1)

    def test_a_negligible_pull_is_dropped_and_counted(self):
        """A real key produced two 'pulls' of 7.9k damage against 531M."""
        from logswow.analysis import CombatBlock, MIN_PULL_SHARE

        self.assertLess(MIN_PULL_SHARE, 0.01)
        crumb = CombatBlock(self.key.first_ts)
        crumb.damage_done = 1
        self.key.blocks.append(crumb)
        self.key.finish(self.segments[2])
        self.assertNotIn(crumb, self.key.blocks)
        self.assertGreaterEqual(self.key.dropped_pulls, 1)

    def test_the_only_pull_is_never_dropped(self):
        self.assertEqual(len(self.boss.blocks), 1)

    def test_a_death_is_counted_against_the_pull_it_happened_in(self):
        second = self.segments[1].analysis
        self.assertEqual(sum(block.deaths for block in second.blocks), 1)


class TestMainTarget(unittest.TestCase):
    """The health curve has to say whose health it is."""

    def setUp(self):
        self.log, self.segments = run_fixture()

    def test_it_is_named_not_left_to_the_reader_to_guess(self):
        analysis = self.segments[0].analysis
        self.assertEqual(analysis.boss_name, "Golem d'essai")

    def test_a_unit_with_no_health_in_the_log_cannot_be_the_curve(self):
        """One real encounter never wrote the boss's health at all, so the
        curve falls back to the most-damaged unit that does have it, and
        says which one that is rather than implying it is the boss."""
        for segment in self.segments:
            analysis = segment.analysis
            if analysis.boss_name:
                self.assertGreaterEqual(len(analysis.boss_hp), 3)

    def test_it_is_the_unit_that_took_the_most_damage(self):
        """Not the one with the biggest health pool, which was the old
        guess and picked the wrong unit in a dungeon."""
        analysis = self.segments[2].analysis
        totals = {}
        for block in analysis.blocks:
            for name in block.enemies:
                totals[name] = totals.get(name, 0) + block.damage_done
        if analysis.boss_name:
            self.assertEqual(analysis.boss_name, max(totals, key=lambda key: totals[key]))

    def test_no_curve_is_drawn_from_too_few_samples(self):
        for segment in self.segments:
            analysis = segment.analysis
            if analysis.boss_hp:
                self.assertGreaterEqual(len(analysis.boss_hp), 3)
            else:
                self.assertEqual(analysis.boss_name, "")


class TestHealingDetail(unittest.TestCase):
    """A healer's panel used to show damage tables and nothing else."""

    def setUp(self):
        self.log, self.segments = run_fixture()
        self.first = self.segments[0].analysis

    def _player(self, name):
        for player in self.first.players.values():
            if player.short_name == name:
                return player
        self.fail("joueur absent : %s" % name)

    def test_healing_is_broken_down_by_spell(self):
        healer = self._player("Tisane")
        names = {ability.name for ability in healer.healing_by_ability.values()}
        self.assertIn("Vague apaisante", names)

    def test_each_spell_carries_its_own_overheal(self):
        healer = self._player("Tisane")
        ability = next(iter(healer.healing_by_ability.values()))
        self.assertGreater(ability.overheal, 0)
        self.assertGreater(ability.overheal_rate, 0)
        self.assertLess(ability.overheal_rate, 1)

    def test_who_was_healed_is_recorded(self):
        healer = self._player("Tisane")
        self.assertEqual(set(healer.healing_to), {"Ardoise", "Braise"})
        self.assertEqual(healer.healing_to["Ardoise"], 20000)

    def test_healing_targets_sum_to_the_healing_done(self):
        healer = self._player("Tisane")
        self.assertEqual(sum(healer.healing_to.values()), healer.healing_done)


class TestWhatThePlayersStopped(unittest.TestCase):
    """The owner asked what players did *to* the monsters."""

    def setUp(self):
        self.log, self.segments = run_fixture()
        self.first = self.segments[0].analysis

    def _player(self, name):
        for player in self.first.players.values():
            if player.short_name == name:
                return player
        self.fail("joueur absent : %s" % name)

    def test_an_interrupt_names_the_spell_it_stopped(self):
        tank = self._player("Ardoise")
        self.assertEqual(tank.interrupts, 1)
        self.assertEqual(tank.interrupted_spells, {"Incantation": 1})
        self.assertEqual(self.first.interrupted_spells, {"Incantation": 1})

    def test_a_dispel_names_what_was_removed(self):
        healer = self._player("Tisane")
        self.assertEqual(healer.dispels, 1)
        self.assertEqual(healer.dispelled_spells, {"Marque": 1})

    def test_enemy_casts_are_counted_by_outcome(self):
        casts = self.first.enemy_casts
        self.assertEqual(casts["commences"], 2)
        self.assertEqual(casts["coupes"], 1)
        self.assertEqual(casts["aboutis"], 1)

    def test_the_outcomes_add_up_to_what_was_started(self):
        casts = self.first.enemy_casts
        self.assertEqual(
            casts["aboutis"] + casts["coupes"] + casts["cible morte"] + casts["autre"],
            casts["commences"],
        )

    def test_a_caster_killed_mid_cast_is_not_called_an_interrupt(self):
        """Killing something that is casting is not a kick, and saying so
        would flatter the group."""
        splitter = Splitter(analysis_factory=SegmentAnalysis)
        payloads = (
            'ENCOUNTER_START,1,"Boss",16,5,2000',
            'SPELL_CAST_START,Creature-1,"B",0xa48,0x0,Player-1,"A",0x511,0x0,5,"Sort",0x1',
            "UNIT_DIED,0000000000000000,nil,0x80000000,0x80000000,"
            'Creature-1,"B",0xa48,0x0,0',
            'ENCOUNTER_END,1,"Boss",16,5,1,1000',
        )
        for payload in payloads:
            _ts, fields = split_line("9/18/2026 20:15:31.123-4  " + payload)
            splitter.feed(build_event(0, fields, 1))
        analysis = splitter.finish()[0].analysis
        self.assertEqual(analysis.enemy_casts["cible morte"], 1)
        self.assertEqual(analysis.enemy_casts["coupes"], 0)


class TestProblemsAreCountedNotSwallowed(unittest.TestCase):
    def test_the_fixtures_deliberate_bad_lines_are_reported(self):
        log, _segments = run_fixture()
        self.assertEqual(log.problems.unsplittable, 1)
        self.assertIn("EVENEMENT_INCONNU", str(log.problems.by_reason) + str(log.problems.samples))

    def test_a_broken_line_does_not_stop_the_read(self):
        log, segments = run_fixture()
        self.assertEqual(len(segments), 3)
        self.assertGreater(log.event_count, 30)


class TestCommandLine(unittest.TestCase):
    def test_a_closed_pipe_is_not_an_error(self):
        """`logswow list big.txt | head` closes stdout early; that is
        ordinary use, not a crash."""
        import subprocess

        listing = subprocess.Popen(
            [sys.executable, "-m", "logswow", "list", FIXTURE, "-q"],
            cwd=ROOT,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
        )
        head = subprocess.Popen(
            ["head", "-1"], stdin=listing.stdout, stdout=subprocess.PIPE
        )
        listing.stdout.close()
        head.communicate()
        listing.wait(timeout=30)
        self.assertNotIn(b"BrokenPipeError", listing.stderr.read())
        self.assertEqual(listing.returncode, 0)

    def test_a_missing_file_is_reported_not_raised(self):
        from logswow.cli import main

        self.assertEqual(main(["report", os.path.join(ROOT, "pas-la.txt")]), 2)


class TestReport(unittest.TestCase):
    def setUp(self):
        self.log, self.segments = run_fixture()

    def test_writes_a_self_contained_page(self):
        import tempfile

        with tempfile.TemporaryDirectory() as directory:
            target = os.path.join(directory, "rapport.html")
            ReportWriter(self.log, self.segments, target).write()
            with open(target, encoding="utf-8") as handle:
                page = handle.read()
        self.assertIn("<!doctype html>", page)
        # The whole point: it must open with no network at all.
        self.assertNotIn("http://", page)
        self.assertNotIn("https://", page)
        self.assertNotIn("<script", page)
        self.assertIn("Golem d&#x27;essai", page)

    def test_the_timeline_carries_a_readable_scale(self):
        """The owner asked for the axis labels a log site shows."""
        import tempfile

        with tempfile.TemporaryDirectory() as directory:
            target = os.path.join(directory, "rapport.html")
            ReportWriter(self.log, self.segments, target).write()
            with open(target, encoding="utf-8") as handle:
                page = handle.read()
        self.assertIn("text-anchor='end'", page)  # the left axis values
        self.assertIn("Courbe et echelle de droite", page)
        self.assertIn("Golem d&#x27;essai", page)  # the curve says whose health it is  # what the curve is

    def test_a_healers_panel_shows_healing_not_only_damage(self):
        import tempfile

        with tempfile.TemporaryDirectory() as directory:
            target = os.path.join(directory, "rapport.html")
            ReportWriter(self.log, self.segments, target).write()
            with open(target, encoding="utf-8") as handle:
                page = handle.read()
        self.assertIn("Ses soins", page)
        self.assertIn("Qui il a soigne", page)
        self.assertIn("Surguerison", page)
        self.assertIn("Dissipations", page)
        self.assertIn("Sorts ennemis coupes", page)
        self.assertIn("Ce que le groupe a empeche", page)

    def test_the_pull_table_appears_only_for_a_run_with_several(self):
        import tempfile

        with tempfile.TemporaryDirectory() as directory:
            target = os.path.join(directory, "rapport.html")
            ReportWriter(self.log, self.segments, target).write()
            with open(target, encoding="utf-8") as handle:
                page = handle.read()
        self.assertIn("Ce qui a ete engage", page)
        self.assertEqual(page.count("Ce qui a ete engage"), 1)

    def test_french_agreement(self):
        self.assertEqual(plural(0, "mort"), "0 mort")
        self.assertEqual(plural(1, "joueur"), "1 joueur")
        self.assertEqual(plural(3, "joueur"), "3 joueurs")


if __name__ == "__main__":
    unittest.main(verbosity=2)
