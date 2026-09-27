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
import re
import sys
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
sys.path.insert(0, ROOT)

from logswow.analysis import SegmentAnalysis  # noqa: E402
from logswow.events import Advanced, Layout, build_event, decompose  # noqa: E402
from logswow.parse import LogFile, detect_layout  # noqa: E402
from logswow.fmt import plural  # noqa: E402
from logswow.report import ReportWriter  # noqa: E402
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
        self.assertEqual(event.base_amount, 7000)
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
            for name, _source, milliseconds, _spell_id in self.first.player_uptimes(
                ardoise.guid
            )
        )
        self.assertEqual(uptimes["Peau de pierre"], 10000)

    def test_an_aura_says_who_applied_it(self):
        ardoise = self._player(self.first, "Ardoise")
        rows = self.first.player_uptimes(ardoise.guid)
        sources = {name: source for name, source, _ms, _id in rows}
        self.assertEqual(sources["Peau de pierre"], "Ardoise")

    def test_no_aura_outlasts_the_pull_it_was_in(self):
        """Routing pets' auras to their owner pushed one real player past
        300% of the fight: several pets can hold one aura at once."""
        for segment in self.segments:
            analysis = segment.analysis
            duration = max(1, analysis.duration_ms)
            for player in analysis.players.values():
                for milliseconds in player.auras_gained.values():
                    self.assertLessEqual(milliseconds, duration + 1000)

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


class TestComposition(unittest.TestCase):
    """Who was in the group, from the spec the client writes."""

    def setUp(self):
        self.log, self.segments = run_fixture()
        self.first = self.segments[0].analysis

    def test_roles_come_from_the_specialization_id(self):
        groups = dict(self.first.composition())
        self.assertEqual([p.short_name for p in groups["Tanks"]], ["Ardoise"])
        self.assertEqual([p.short_name for p in groups["Soigneurs"]], ["Tisane"])
        self.assertIn("Braise", [p.short_name for p in groups["DPS"]])

    def test_an_unknown_specialization_keeps_its_number(self):
        from logswow.specs import SPECS, label_of

        self.assertNotIn(99999, SPECS)
        self.assertEqual(label_of(99999), "spe 99999")

    def test_the_spec_read_from_the_log_is_the_one_at_index_25(self):
        """Three stat values in real logs happen to equal a spec id, so
        this reads one fixed field rather than scanning for a plausible
        number."""
        from logswow.specs import SPEC_ID_INDEX, label_of

        self.assertEqual(SPEC_ID_INDEX, 25)
        tank = [p for p in self.first.players.values() if p.short_name == "Ardoise"][0]
        self.assertEqual(tank.spec_id, 73)
        self.assertEqual(label_of(73), "Guerrier Protection")


class TestEnemies(unittest.TestCase):
    """The same drill-down, for the other side."""

    def setUp(self):
        self.log, self.segments = run_fixture()
        self.first = self.segments[0].analysis
        self.key = self.segments[2].analysis

    def test_units_sharing_a_name_are_one_panel(self):
        sbires = self.key.enemies["Sbire d'essai"]
        self.assertEqual(sbires.count, 2)

    def test_an_enemy_records_what_it_dealt_and_what_it_took(self):
        golem = self.first.enemies["Golem d'essai"]
        self.assertGreater(golem.damage_done, 0)
        self.assertGreater(golem.damage_taken, 0)
        self.assertEqual(golem.deaths, 1)

    def test_an_enemy_ability_names_who_it_hit(self):
        golem = self.first.enemies["Golem d'essai"]
        ability = next(
            a for a in golem.damage_by_ability.values() if a.name == "Balayage"
        )
        self.assertIn("Ardoise", ability.targets)

    def test_enemy_casts_are_listed_by_spell(self):
        golem = self.first.enemies["Golem d'essai"]
        self.assertEqual(golem.casts_by_spell.get("Long sort"), 1)


class TestAbilityDetail(unittest.TestCase):
    """The columns the owner asked for, next to a log site's own."""

    def setUp(self):
        self.log, self.segments = run_fixture()
        self.first = self.segments[0].analysis

    def _ability(self, player_name, spell_name):
        for player in self.first.players.values():
            if player.short_name != player_name:
                continue
            for ability in player.damage_by_ability.values():
                if ability.name == spell_name:
                    return player, ability
        self.fail("capacite absente : %s / %s" % (player_name, spell_name))

    def test_an_ability_knows_its_hits_average_and_biggest(self):
        _player, ability = self._ability("Braise", "Frappe d'essai")
        self.assertEqual(ability.hits, 7)
        self.assertEqual(ability.average, ability.total / ability.hits)
        self.assertEqual(ability.biggest, 9000)

    def test_an_ability_knows_who_it_hit_and_for_how_much(self):
        _player, ability = self._ability("Braise", "Frappe d'essai")
        self.assertEqual(ability.ranked_targets(1)[0][0], "Golem d'essai")
        self.assertEqual(sum(ability.targets.values()), ability.total)

    def test_casts_are_counted_per_spell(self):
        player = [
            p for p in self.segments[2].analysis.players.values()
            if p.short_name == "Braise"
        ][0]
        self.assertEqual(sum(player.casts_by_spell.values()), player.casts)


class TestAuditFindings(unittest.TestCase):
    """Each of these is a bug or an edge the 2026-09-18 audit found or
    checked. They are kept as tests so the next audit starts further on."""

    def _analyse(self, payloads):
        splitter = Splitter(analysis_factory=SegmentAnalysis)
        for payload in payloads:
            _ts, fields = split_line("9/18/2026 20:15:31.123-4  " + payload)
            splitter.feed(build_event(0, fields, 1))
        return splitter.finish()

    def test_windows_line_endings_read_the_same(self):
        """The client writes CRLF whatever the system; a reader on Linux
        or Windows must get identical numbers from the same bytes."""
        import tempfile

        with open(FIXTURE, encoding="utf-8") as handle:
            text = handle.read()
        with tempfile.TemporaryDirectory() as directory:
            crlf = os.path.join(directory, "crlf.txt")
            with open(crlf, "w", encoding="utf-8", newline="") as handle:
                handle.write(text.replace("\n", "\r\n"))
            log = LogFile(crlf)
            splitter = Splitter(analysis_factory=SegmentAnalysis)
            for event in log.events():
                splitter.feed(event)
            segments = splitter.finish()
        reference_log, reference = run_fixture()
        self.assertEqual(
            [s.analysis.total_damage for s in segments],
            [s.analysis.total_damage for s in reference],
        )
        # Problems are counted while reading, so compare against a log
        # that has actually been read -- a fresh LogFile always says zero.
        self.assertEqual(log.problems.total, reference_log.problems.total)

    def test_an_empty_file_produces_no_segments_and_no_crash(self):
        import tempfile

        with tempfile.TemporaryDirectory() as directory:
            empty = os.path.join(directory, "vide.txt")
            open(empty, "w").close()
            log = LogFile(empty)
            splitter = Splitter(analysis_factory=SegmentAnalysis)
            for event in log.events():
                splitter.feed(event)
            self.assertEqual(splitter.finish(), [])
            self.assertEqual(log.duration_ms, 0)
            target = os.path.join(directory, "vide.html")
            ReportWriter(log, [], target).write()
            self.assertTrue(os.path.getsize(target) > 0)

    def test_a_hostile_name_cannot_inject_markup(self):
        """Names come from the file, and the file comes from a stranger's
        group. A unit called <script> must render as text."""
        import tempfile

        payloads = (
            'ENCOUNTER_START,1,"<script>alert(1)</script>",16,5,2000',
            'SPELL_DAMAGE,Player-1,"A&B",0x511,0x0,Creature-1,"<b>x</b>",0xa48,0x0,'
            '1,"<i>Sort</i>",0x1,5000,7000,-1,1,0,0,0,nil,nil,nil,ST',
            'ENCOUNTER_END,1,"<script>alert(1)</script>",16,5,1,1000',
        )
        segments = self._analyse(payloads)
        log = LogFile(FIXTURE)
        with tempfile.TemporaryDirectory() as directory:
            target = os.path.join(directory, "r.html")
            ReportWriter(log, segments, target, wowhead="off").write()
            with open(target, encoding="utf-8") as handle:
                page = handle.read()
        self.assertNotIn("<script>alert", page)
        self.assertNotIn("<b>x</b>", page)
        self.assertNotIn("<i>Sort</i>", page)
        self.assertIn("&lt;script&gt;", page)

    def test_a_cast_restarted_before_it_resolved_is_still_counted(self):
        """Overwriting a pending cast lost two of twenty-five on a real
        boss; the invariant is that outcomes sum to starts."""
        payloads = (
            'ENCOUNTER_START,1,"Boss",16,5,2000',
            'SPELL_CAST_START,Creature-1,"B",0xa48,0x0,Player-1,"A",0x511,0x0,5,"Sort",0x1',
            'SPELL_CAST_START,Creature-1,"B",0xa48,0x0,Player-1,"A",0x511,0x0,5,"Sort",0x1',
            'SPELL_CAST_SUCCESS,Creature-1,"B",0xa48,0x0,Player-1,"A",0x511,0x0,5,"Sort",0x1',
            'ENCOUNTER_END,1,"Boss",16,5,1,1000',
        )
        casts = self._analyse(payloads)[0].analysis.enemy_casts
        self.assertEqual(casts["commences"], 2)
        self.assertEqual(
            casts["aboutis"] + casts["coupes"] + casts["cible morte"] + casts["autre"],
            casts["commences"],
        )

    def test_boss_names_match_across_both_apostrophes(self):
        """ENCOUNTER_START writes a curly apostrophe, the unit's events a
        straight one, in the same file."""
        from logswow.analysis import canon

        self.assertEqual(canon("Xathuux l\u2019Annihilateur"), canon("Xathuux l'Annihilateur"))
        payloads = (
            'CHALLENGE_MODE_START,"Donjon",2000,500,7,[165]',
            'ENCOUNTER_START,1,"Xathuux l\u2019Annihilateur",8,5,2000',
            'SPELL_DAMAGE,Player-1,"A",0x511,0x0,Creature-1,"Xathuux l\'Annihilateur",0xa48,0x0,'
            '1,"Sort",0x1,5000,7000,-1,1,0,0,0,nil,nil,nil,ST',
            'ENCOUNTER_END,1,"Xathuux l\u2019Annihilateur",8,5,1,1000',
            "CHALLENGE_MODE_END,2000,1,7,600000",
        )
        key = self._analyse(payloads)[0].analysis
        self.assertEqual(key.blocks[0].damage_boss, 5000)
        self.assertTrue(key.blocks[0].label(boss_names=key.boss_names).startswith("Xathuux"))

    def test_a_trash_pull_that_funnels_into_a_boss_names_the_boss_first(self):
        _log, segments = run_fixture()
        key = segments[2].analysis
        block = key.blocks[0]
        # The fixture's key has no boss, so the split is all trash...
        self.assertEqual(block.damage_boss, 0)
        self.assertEqual(block.damage_trash, block.damage_done)
        # ...and a boss encounter is all boss.
        boss = segments[0].analysis
        self.assertEqual(boss.blocks[0].damage_boss, boss.blocks[0].damage_done)
        self.assertGreater(boss.blocks[0].damage_boss, 0)

    def test_the_pooled_health_curve_stays_within_bounds(self):
        _log, segments = run_fixture()
        for segment in segments:
            series, _bucket = segment.analysis.timeline_series()
            for row in series:
                self.assertTrue(row[4] is None or 0.0 <= row[4] <= 1.0)
        key = segments[2].analysis
        self.assertTrue(key.has_pool_curve)

    def test_a_pull_gap_under_a_second_is_clamped(self):
        from logswow.segment import Segment

        analysis = SegmentAnalysis(Segment("encounter", "x", 0, 1), pull_gap_ms=0)
        self.assertEqual(analysis.pull_gap_ms, 1000)

    def test_a_missing_output_directory_is_an_error_message_not_a_traceback(self):
        from logswow.cli import main

        code = main(["report", FIXTURE, "-q", "-o", "/nonexistent-dir/x/y/rapport.html"])
        self.assertEqual(code, 2)


class TestSecondAuditFindings(unittest.TestCase):
    """The 2026-09-19 audit. Same rule as the class above: every bug it
    found keeps a test here, so the third pass starts where this one
    stopped rather than re-finding the same things."""

    def _read(self, text, name="journal.txt", encoding="utf-8"):
        import tempfile

        directory = tempfile.mkdtemp()
        path = os.path.join(directory, name)
        with open(path, "w", encoding=encoding, newline="") as handle:
            handle.write(text)
        log = LogFile(path)
        splitter = Splitter(analysis_factory=SegmentAnalysis)
        for event in log.events():
            splitter.feed(event)
        return log, splitter.finish(), path

    # -- crashes ---------------------------------------------------------

    def test_an_impossible_timestamp_is_skipped_not_raised(self):
        """A line can match a shape and still be impossible. The one that
        needs no corruption at all is 29 February in a year-less log read
        during a non-leap year."""
        reader = TimestampReader(2026)
        for text in ("2/30/2026 10:00:00.000", "13/45 10:00:00.000",
                     "9/18/2026 99:00:00.000", "2/29 10:00:00.000",
                     "9/18/2026 10:00:00.000-99"):
            self.assertIsNone(reader.read(text), text)
        self.assertEqual(reader.unparsed, 5)
        self.assertIsNotNone(reader.read("9/18/2026 20:15:31.123-4"))

    def test_an_infinite_number_does_not_raise(self):
        """int(float("inf")) raises OverflowError, not ValueError."""
        from logswow.tokenize import as_int

        for text in ("inf", "-inf", "Infinity", "1e400"):
            self.assertEqual(as_int(text), 0, text)
        self.assertEqual(as_int("42"), 42)

    def test_a_directory_is_an_error_message_not_a_traceback(self):
        import tempfile

        from logswow.cli import main

        with tempfile.TemporaryDirectory() as directory:
            for command in ("report", "list", "diagnose"):
                # diagnose prints nothing else, so it takes no -q.
                quiet = [] if command == "diagnose" else ["-q"]
                self.assertEqual(main([command, directory] + quiet), 2, command)

    # -- numbers ---------------------------------------------------------

    def test_one_unreadable_line_counts_as_one_problem(self):
        """`unsplittable` used to be incremented beside `by_reason`, so
        the fixture's two bad lines were reported as three -- in
        `diagnose`, in the report's footer and in its own tile."""
        log, _segments = run_fixture()
        self.assertEqual(log.problems.total, 2)
        self.assertEqual(log.problems.total, sum(log.problems.by_reason.values()))

    def test_a_reported_problem_says_which_line_it_was_on(self):
        log, _segments = run_fixture()
        self.assertTrue(log.problems.samples)
        for line_number, _reason, _text in log.problems.samples:
            self.assertIsInstance(line_number, int)

    def test_a_byte_order_mark_does_not_cost_the_first_line(self):
        with open(FIXTURE, encoding="utf-8") as handle:
            text = handle.read()
        plain, _segments, _path = self._read(text)
        marked, _segments, _path = self._read("\ufeff" + text, name="bom.txt")
        self.assertEqual(marked.problems.total, plain.problems.total)
        self.assertEqual(marked.event_count, plain.event_count)

    def test_an_absorb_is_counted_once_not_twice(self):
        """The client writes the same absorption in the hit's `absorbed`
        field *and* as its own SPELL_ABSORBED line."""
        boss = 'Creature-0-1-1-1-70000-0000000001,"Golem",0xa48,0x0'
        tank = 'Player-1-00000001,"Ardoise-Dalaran-EU",0x511,0x0'
        block = ",".join(advanced_block(19, info="Player-1-00000001"))
        segments = self._analyse([
            'ENCOUNTER_START,1,"Golem",16,5,2000',
            'SPELL_DAMAGE,%s,%s,444,"Balayage",0x4,%s,1000,1500,-1,4,0,0,500,nil,nil,nil,ST'
            % (boss, tank, block),
            'SPELL_ABSORBED,%s,%s,%s,%s,1002,"Bouclier",0x2,500,1500,nil'
            % (boss, tank, tank, tank),
            'ENCOUNTER_END,1,"Golem",16,5,1,1000',
        ])
        players = segments[0].analysis.players.values()
        self.assertEqual(sum(p.absorbed_taken for p in players), 500)

    def test_damage_from_a_pet_nobody_owns_is_named_not_dropped(self):
        """A pet summoned before the pull, on lines with no ownerGUID,
        belongs to no ledger. Leaving it out is right; leaving it out
        silently makes the group's total quietly short."""
        pet = 'Pet-0-1-1-1-00099,"Cendre",0x1114,0x0'
        mob = 'Creature-0-1-1-1-70000-0000000001,"Sbire",0xa48,0x0'
        block = ",".join(advanced_block(19, info="Creature-0-1-1-1-70000-0000000001"))
        segments = self._analyse([
            'ENCOUNTER_START,1,"Sbire",16,5,2000',
            'SPELL_DAMAGE,%s,%s,777,"Morsure",0x1,%s,700,700,-1,1,0,0,0,nil,nil,nil,ST'
            % (pet, mob, block),
            'ENCOUNTER_END,1,"Sbire",16,5,1,1000',
        ])
        analysis = segments[0].analysis
        self.assertEqual(analysis.total_damage, 0)
        self.assertEqual(analysis.orphan_damage, 700)
        self.assertEqual(analysis.orphan_sources, {"Cendre": 700})

    def test_a_truncated_pull_keeps_the_time_it_was_recorded_for(self):
        """A log cut mid-fight used to end the pull on its own start."""
        mob = 'Creature-0-1-1-1-70000-0000000001,"Sbire",0xa48,0x0'
        player = 'Player-1-00000001,"Ardoise-Dalaran-EU",0x511,0x0'
        block = ",".join(advanced_block(19, info="Creature-0-1-1-1-70000-0000000001"))
        splitter = Splitter(analysis_factory=SegmentAnalysis)
        payloads = [
            'ENCOUNTER_START,1,"Sbire",16,5,2000',
            'SPELL_DAMAGE,%s,%s,222,"Frappe",0x1,%s,100,100,-1,1,0,0,0,nil,nil,nil,ST'
            % (player, mob, block),
        ]
        for index, payload in enumerate(payloads):
            _ts, fields = split_line("9/18/2026 20:15:31.123-4  " + payload)
            splitter.feed(build_event(index * 30000, fields, index + 1))
        segments = splitter.finish()
        self.assertTrue(segments[0].truncated)
        self.assertEqual(segments[0].duration_ms, 30000)

    def test_lines_between_two_pulls_are_not_analysed_for_nothing(self):
        """Once the file is known to carry markers, the fallback segment
        is discarded by `finish`, so feeding it is work nobody sees --
        and on a night that is mostly corridor it was most of the work."""
        mob = 'Creature-0-1-1-1-70000-0000000001,"Sbire",0xa48,0x0'
        player = 'Player-1-00000001,"Ardoise-Dalaran-EU",0x511,0x0'
        block = ",".join(advanced_block(19, info="Creature-0-1-1-1-70000-0000000001"))
        splitter = Splitter(analysis_factory=SegmentAnalysis)
        for index, payload in enumerate([
            'ENCOUNTER_START,1,"Sbire",16,5,2000',
            'ENCOUNTER_END,1,"Sbire",16,5,1,1000',
            'SPELL_DAMAGE,%s,%s,222,"Frappe",0x1,%s,100,100,-1,1,0,0,0,nil,nil,nil,ST'
            % (player, mob, block),
        ]):
            _ts, fields = split_line("9/18/2026 20:15:31.123-4  " + payload)
            splitter.feed(build_event(index * 1000, fields, index + 1))
        segments = splitter.finish()
        self.assertEqual([segment.kind for segment in segments], ["encounter"])
        self.assertIsNone(splitter._fallback)

    # -- what the reader is told ------------------------------------------

    def test_a_file_with_no_fight_says_so_instead_of_blaming_only(self):
        """An empty file used to be reported as `--only None`, which the
        reader never typed."""
        import io
        import tempfile
        from contextlib import redirect_stderr

        from logswow.cli import main

        with tempfile.TemporaryDirectory() as directory:
            empty = os.path.join(directory, "vide.txt")
            open(empty, "w").close()
            errors = io.StringIO()
            with redirect_stderr(errors):
                code = main(["report", empty, "-q"])
        self.assertEqual(code, 2)
        self.assertIn("Aucun combat", errors.getvalue())
        self.assertNotIn("--only", errors.getvalue())

    def test_the_overview_table_spans_its_own_columns(self):
        page = self._page([])
        heads = page.count("<th", page.find("<h2>Combats</h2>"),
                           page.find("</table>", page.find("<h2>Combats</h2>")))
        self.assertIn("colspan=%d" % heads, page)

    def test_the_report_says_when_damage_belongs_to_nobody(self):
        pet = 'Pet-0-1-1-1-00099,"Cendre",0x1114,0x0'
        mob = 'Creature-0-1-1-1-70000-0000000001,"Sbire",0xa48,0x0'
        block = ",".join(advanced_block(19, info="Creature-0-1-1-1-70000-0000000001"))
        page = self._page([
            'ENCOUNTER_START,1,"Sbire",16,5,2000',
            'SPELL_DAMAGE,%s,%s,777,"Morsure",0x1,%s,700,700,-1,1,0,0,0,nil,nil,nil,ST'
            % (pet, mob, block),
            'ENCOUNTER_END,1,"Sbire",16,5,1,1000',
        ])
        self.assertIn("ne sont comptes pour personne", page)
        self.assertIn("Cendre", page)

    # -- the invariant checker itself --------------------------------------

    def test_the_invariant_checker_reports_instead_of_crashing(self):
        """It raised outside its own guard, so a log with one stray line
        came out as a traceback and no invariant was ever checked."""
        import subprocess

        result = subprocess.run(
            [sys.executable, os.path.join(ROOT, "tools", "check-invariants.py"), FIXTURE],
            cwd=ROOT, capture_output=True, text=True, timeout=120,
        )
        self.assertNotIn("Traceback", result.stderr)
        self.assertIn("All invariants hold", result.stdout)
        # ...and the unreadable lines are still reported, as their own
        # verdict rather than as a reason to check nothing.
        self.assertEqual(result.returncode, 1)
        self.assertIn("could not be read", result.stdout)

    # -- helpers -----------------------------------------------------------

    def _analyse(self, payloads):
        splitter = Splitter(analysis_factory=SegmentAnalysis)
        for index, payload in enumerate(payloads):
            _ts, fields = split_line("9/18/2026 20:15:31.123-4  " + payload)
            splitter.feed(build_event(index * 1000, fields, index + 1))
        return splitter.finish()

    def _page(self, payloads):
        import tempfile

        segments = self._analyse(payloads) if payloads else []
        log, _segments = run_fixture()
        with tempfile.TemporaryDirectory() as directory:
            target = os.path.join(directory, "rapport.html")
            ReportWriter(log, segments, target).write()
            with open(target, encoding="utf-8") as handle:
                return handle.read()


class TestThirdAuditFindings(unittest.TestCase):
    """The second pass of the 2026-09-19 audit: whole-file shapes the unit
    tests covered field by field but had never read end to end."""

    PLAYER = 'Player-9-00000001,"Ardoise-Dalaran-EU",0x511,0x0'
    HEALER = 'Player-9-00000002,"Tisane-Dalaran-EU",0x512,0x0'
    MOB = 'Creature-0-9-2-1-70000-0000000001,"Golem",0xa48,0x0'
    MOB_GUID = "Creature-0-9-2-1-70000-0000000001"
    MODERN = ("{i},0000000000000000,{hp},100000,1500,420,830,240,0,0,1,1100,"
              "1300,0,1.0,2.0,2393,3.14,80")
    OLD = ("{i},0000000000000000,{hp},100000,1500,420,830,240,1,1100,1300,0,"
           "1.0,2.0,2393,3.14,80")

    def _run(self, lines):
        import tempfile

        directory = tempfile.mkdtemp()
        path = os.path.join(directory, "journal.txt")
        with open(path, "w", encoding="utf-8") as handle:
            handle.write("\n".join(lines) + "\n")
        log = LogFile(path)
        splitter = Splitter(analysis_factory=SegmentAnalysis)
        for event in log.events():
            splitter.feed(event)
        return log, splitter.finish(), path

    def test_a_log_of_one_event_kind_still_measures_its_width(self):
        """Every candidate width is backed by the same single subevent, so
        the vote ties. It used to be broken by "take the widest", which
        read every amount off the overkill field: thirty hits of 5,000
        were reported as -30 damage."""
        lines = ['9/18/2026 20:00:00.000  ENCOUNTER_START,1,"Golem",16,1,2000']
        for index in range(30):
            lines.append(
                '9/18/2026 20:00:%02d.000  SPELL_DAMAGE,%s,%s,222,"Frappe",0x1,'
                '%s,5000,6000,-1,1,0,0,0,nil,nil,nil,ST'
                % (index + 1, self.PLAYER, self.MOB,
                   self.MODERN.format(i=self.MOB_GUID, hp=100000 - index * 1000))
            )
        lines.append('9/18/2026 20:01:00.000  ENCOUNTER_END,1,"Golem",16,1,1,60000')
        log, segments, _path = self._run(lines)
        self.assertEqual(log.layout.advanced_width, 19)
        self.assertEqual(segments[0].analysis.total_damage, 150000)

    def test_the_documented_older_layout_reads_end_to_end(self):
        """17 fields and no baseAmount: the layout the published
        documentation describes, checked as a whole file rather than one
        field at a time."""
        lines = ['12/31 23:59:00.000  ENCOUNTER_START,1,"Golem",16,5,2000']
        for index in range(12):
            lines.append(
                '12/31 23:59:%02d.000  SPELL_DAMAGE,%s,%s,222,"Frappe",0x1,'
                '%s,5000,-1,1,0,0,0,nil,nil,nil'
                % (index + 2, self.PLAYER, self.MOB,
                   self.OLD.format(i=self.MOB_GUID, hp=100000 - index * 8000))
            )
            lines.append(
                '12/31 23:59:%02d.600  SPELL_HEAL,%s,%s,555,"Soin",0x2,%s,3000,500,0,nil'
                % (index + 2, self.HEALER, self.PLAYER,
                   self.OLD.format(i="Player-9-00000001", hp=90000))
            )
        lines.append('1/1 00:00:21.000  ENCOUNTER_END,1,"Golem",16,5,1,80000')
        log, segments, _path = self._run(lines)
        self.assertEqual(log.layout.advanced_width, 17)
        self.assertFalse(log.layout.has_base_amount)
        analysis = segments[0].analysis
        self.assertEqual(analysis.total_damage, 12 * 5000)
        self.assertEqual(analysis.total_healing, 12 * 2500)
        # ...and the year-less shape crossed New Year without a jump.
        self.assertGreater(analysis.duration_ms, 0)
        self.assertLess(analysis.duration_ms, 2 * 60 * 1000)

    def test_a_log_without_advanced_logging_still_adds_up(self):
        """Somebody forgets the setting every day. No positions, no health,
        but the totals must be exact."""
        lines = ['9/18/2026 20:00:00.000  ENCOUNTER_START,1,"Golem",16,5,2000']
        for index in range(20):
            lines.append(
                '9/18/2026 20:00:%02d.000  SPELL_DAMAGE,%s,%s,222,"Frappe",0x1,'
                '5000,6000,-1,1,0,0,0,nil,nil,nil,ST' % (index + 1, self.PLAYER, self.MOB))
            lines.append(
                '9/18/2026 20:00:%02d.700  SPELL_HEAL,%s,%s,555,"Soin",0x2,3000,3000,500,0,nil'
                % (index + 1, self.HEALER, self.PLAYER))
        lines.append('9/18/2026 20:01:00.000  ENCOUNTER_END,1,"Golem",16,5,1,60000')
        log, segments, _path = self._run(lines)
        self.assertFalse(log.layout.evidence.get("advanced_logging"))
        self.assertEqual(segments[0].analysis.total_damage, 20 * 5000)
        self.assertEqual(segments[0].analysis.total_healing, 20 * 2500)
        self.assertEqual(log.problems.total, 0)

    def test_a_line_earlier_than_the_fight_stays_on_the_graph(self):
        """A log is not perfectly ordered. A timestamp before the first
        event gave a negative bucket, which the series never walks, and
        the damage vanished from the graph while staying in the table."""
        lines = ['9/18/2026 20:00:10.000  ENCOUNTER_START,1,"Golem",16,5,2000']
        for moment in ("20:00:11.000", "20:00:05.000", "20:00:13.000"):
            lines.append(
                '9/18/2026 %s  SPELL_DAMAGE,%s,%s,444,"Balayage",0x4,%s,'
                '1000,1000,-1,4,0,0,0,nil,nil,nil,AOE'
                % (moment, self.MOB, self.PLAYER,
                   self.MODERN.format(i="Player-9-00000001", hp=50000)))
        lines.append('9/18/2026 20:00:20.000  ENCOUNTER_END,1,"Golem",16,5,1,10000')
        _log, segments, _path = self._run(lines)
        analysis = segments[0].analysis
        taken = sum(p.damage_taken for p in analysis.players.values())
        drawn = sum(row[1] for row in analysis.timeline_series()[0])
        self.assertEqual(taken, 3000)
        self.assertEqual(drawn, taken)

    def test_an_aura_up_before_the_pull_is_counted_from_the_start(self):
        lines = [
            '9/18/2026 20:00:00.000  SPELL_AURA_APPLIED,%s,%s,111,"Potion",0x1,BUFF'
            % (self.PLAYER, self.PLAYER),
            '9/18/2026 20:00:10.000  ENCOUNTER_START,1,"Golem",16,5,2000',
            '9/18/2026 20:00:11.000  SPELL_DAMAGE,%s,%s,222,"Frappe",0x1,%s,'
            '2000,2000,-1,1,0,0,0,nil,nil,nil,ST'
            % (self.PLAYER, self.MOB, self.MODERN.format(i=self.MOB_GUID, hp=90000)),
            '9/18/2026 20:00:40.000  SPELL_AURA_REMOVED,%s,%s,111,"Potion",0x1,BUFF'
            % (self.PLAYER, self.PLAYER),
            '9/18/2026 20:01:10.000  ENCOUNTER_END,1,"Golem",16,5,1,60000',
        ]
        _log, segments, _path = self._run(lines)
        analysis = segments[0].analysis
        self.assertEqual(analysis.auras_before_the_pull, 1)
        uptimes = analysis.player_uptimes("Player-9-00000001", kind="BUFF")
        self.assertEqual(len(uptimes), 1)
        self.assertEqual(uptimes[0][0], "Potion")
        self.assertEqual(uptimes[0][2], 29000)
        # It can never be inferred twice for the same aura on the same
        # unit: a file missing lines would otherwise credit the whole run
        # again at every removal.
        self.assertLessEqual(uptimes[0][2], analysis.duration_ms)

    def test_a_second_unmatched_removal_infers_nothing(self):
        lines = ['9/18/2026 20:00:00.000  ENCOUNTER_START,1,"Golem",16,5,2000',
                 '9/18/2026 20:00:01.000  SPELL_DAMAGE,%s,%s,222,"Frappe",0x1,%s,'
                 '2000,2000,-1,1,0,0,0,nil,nil,nil,ST'
                 % (self.PLAYER, self.MOB, self.MODERN.format(i=self.MOB_GUID, hp=90000))]
        for moment in ("20:00:20.000", "20:00:40.000"):
            lines.append('9/18/2026 %s  SPELL_AURA_REMOVED,%s,%s,111,"Potion",0x1,BUFF'
                         % (moment, self.PLAYER, self.PLAYER))
        lines.append('9/18/2026 20:01:00.000  ENCOUNTER_END,1,"Golem",16,5,1,60000')
        _log, segments, _path = self._run(lines)
        analysis = segments[0].analysis
        self.assertEqual(analysis.auras_before_the_pull, 1)
        total = sum(analysis.players["Player-9-00000001"].auras_gained.values())
        self.assertLessEqual(total, analysis.duration_ms)

    def test_the_report_refuses_to_overwrite_the_log_it_read(self):
        """`report journal.txt -o journal.txt` wrote the page over the
        log. A combat log cannot be recovered."""
        import shutil
        import tempfile

        from logswow.cli import main

        with tempfile.TemporaryDirectory() as directory:
            copy = os.path.join(directory, "journal.txt")
            shutil.copy(FIXTURE, copy)
            before = os.path.getsize(copy)
            self.assertEqual(main(["report", copy, "-o", copy, "-q"]), 2)
            self.assertEqual(os.path.getsize(copy), before)

    def test_reading_the_same_file_twice_gives_the_same_numbers(self):
        log, _segments, _path = self._run([
            '9/18/2026 20:00:00.000  ENCOUNTER_START,1,"Golem",16,5,2000',
            '9/18/2026 20:00:10.000  ENCOUNTER_END,1,"Golem",16,5,1,10000',
        ])
        first = (log.line_count, log.event_count, log.problems.total)
        for _event in log.events():
            pass
        self.assertEqual((log.line_count, log.event_count, log.problems.total), first)

    def test_a_million_is_not_printed_as_a_thousand_thousands(self):
        from logswow.fmt import compact

        self.assertTrue(compact(999999).endswith("M"))
        self.assertEqual(compact(999), "999")

    def test_finishing_a_splitter_twice_does_not_duplicate_a_session(self):
        splitter = Splitter(analysis_factory=SegmentAnalysis)
        _ts, fields = split_line(
            '9/18/2026 20:00:00.000  SPELL_CAST_SUCCESS,%s,%s,222,"Frappe",0x1'
            % (self.PLAYER, self.MOB))
        splitter.feed(build_event(0, fields, 1))
        self.assertEqual(len(splitter.finish()), 1)
        self.assertEqual(len(splitter.finish()), 1)


class TestFourthAuditFindings(unittest.TestCase):
    """The third pass of the 2026-09-19 audit: what reaches the page."""

    def test_a_report_never_carries_a_realm(self):
        """The log names everyone in the group, realm included. The page
        is the thing a reader shares, and it had realms in it: the death
        chains named "Tisane-Dalaran-EU", and so did a healer's main
        target."""
        import tempfile

        log, segments = run_fixture()
        with tempfile.TemporaryDirectory() as directory:
            target = os.path.join(directory, "rapport.html")
            ReportWriter(log, segments, target).write()
            with open(target, encoding="utf-8") as handle:
                page = handle.read()
        self.assertIn("Tisane", page)
        self.assertNotIn("Dalaran", page)
        self.assertNotIn("-EU", page)

    def test_only_a_player_loses_the_part_after_its_dash(self):
        """A creature called "Garde-fou" must keep all of itself."""
        from logswow.events import Actor

        player = Actor("Player-9-1", "Ardoise-Dalaran-EU", 0x511, 0)
        creature = Actor("Creature-0-9-2-1-70000-1", "Garde-fou", 0xA48, 0)
        self.assertEqual(player.display_name, "Ardoise")
        self.assertEqual(creature.display_name, "Garde-fou")

    def test_meeting_many_units_does_not_grow_without_limit(self):
        """Damage was banked per enemy GUID with nothing dropping the
        tail: 150,000 units on a 48 MB file took peak memory to 56 MB on
        their own. Only the leaders can win the main-target ranking, so
        the rest goes -- and the total must not move."""
        from logswow.analysis import MAX_DAMAGED_UNITS

        player = 'Player-9-00000001,"Ardoise-Dalaran-EU",0x511,0x0'
        block = ",".join(advanced_block(19, info="Creature-0-9-2-1-70000-1"))
        splitter = Splitter(analysis_factory=SegmentAnalysis)
        payloads = ['ENCOUNTER_START,1,"Foule",16,5,2000']
        units = MAX_DAMAGED_UNITS * 3
        for index in range(units):
            payloads.append(
                'SPELL_DAMAGE,%s,Creature-0-9-2-1-70000-%d,"Sbire",0xa48,0x0,'
                '222,"Frappe",0x1,%s,100,100,-1,1,0,0,0,nil,nil,nil,ST'
                % (player, index, block))
        for index, payload in enumerate(payloads):
            _ts, fields = split_line("9/18/2026 20:15:31.123-4  " + payload)
            splitter.feed(build_event(index * 10, fields, index + 1))
        analysis = splitter.finish()[0].analysis
        self.assertEqual(analysis.total_damage, units * 100)
        self.assertLessEqual(len(analysis._enemy_damage), MAX_DAMAGED_UNITS + 1)
        self.assertLessEqual(len(analysis._enemy_names), MAX_DAMAGED_UNITS + 1)

    def test_the_page_shows_the_numbers_the_analysis_holds(self):
        """The report has its own arithmetic -- shares, sums, rankings --
        and nothing checked it against the analysis it renders. With the
        rounding removed, every table must add up to its own total."""
        import html as html_module
        import tempfile

        from logswow import fmt as fmt_module

        log, segments = run_fixture()
        # One replacement reaches every table: the page calls fmt.compact.
        original = fmt_module.compact
        fmt_module.compact = lambda value: str(int(value))
        try:
            with tempfile.TemporaryDirectory() as directory:
                target = os.path.join(directory, "rapport.html")
                ReportWriter(log, segments, target).write()
                with open(target, encoding="utf-8") as handle:
                    page = handle.read()
        finally:
            fmt_module.compact = original

        def cells(fragment):
            return [
                html_module.unescape(
                    re.sub(r"<[^>]+>", "", cell)
                ).strip().replace("\u202f", "")
                for cell in re.findall(r"<td[^>]*>(.*?)</td>", fragment, re.S)
            ]

        checked = 0
        for segment in segments:
            analysis = segment.analysis
            body = page.split("<h2 id='s%d'>" % segment.index, 1)[1]
            body = body.split("<h2 id='s", 1)[0]
            if "<h3>Degats infliges</h3>" not in body:
                continue
            table = body.split("<h3>Degats infliges</h3>", 1)[1].split("</table>", 1)[0]
            rows = re.findall(r"<tr>(.*?)</tr>", table, re.S)[1:]
            self.assertEqual(
                sum(int(cells(row)[1]) for row in rows),
                analysis.total_damage,
                "segment %d" % segment.index,
            )
            checked += 1
        self.assertGreater(checked, 0)


class TestWhatTheRealLogsFound(unittest.TestCase):
    """Five real logs, read on 2026-09-20. The invariant checker refused
    two of them, and both refusals were about the same thing: an aura is
    identified by its caster as well as by its spell, and uptime is a
    union of intervals rather than a sum of them."""

    MOB_A = 'Creature-0-9-2-1-70000-0000000001,"Ombre",0xa48,0x0'
    MOB_B = 'Creature-0-9-2-1-70000-0000000002,"Ombre",0xa48,0x0'
    HEALER = 'Player-9-00000002,"Tisane-Dalaran-EU",0x512,0x0'
    MAGE = 'Player-9-00000003,"Braise-Dalaran-EU",0x512,0x0'
    VICTIM = 'Player-9-00000001,"Ardoise-Dalaran-EU",0x511,0x0'
    VICTIM_GUID = "Player-9-00000001"

    def _analyse(self, payloads):
        """A player exists in the analysis once they have done or taken
        something, so the victim takes one hit before anything else --
        an aura alone never creates a row, by design."""
        block = ",".join(advanced_block(19, info=self.VICTIM_GUID))
        opening = (500, 'SPELL_DAMAGE,%s,%s,999,"Coup",0x1,%s,'
                        '100,100,-1,1,0,0,0,nil,nil,nil,ST'
                        % (self.MOB_A, self.VICTIM, block))
        splitter = Splitter(analysis_factory=SegmentAnalysis)
        for ts, payload in [payloads[0], opening] + payloads[1:]:
            _stamp, fields = split_line("9/18/2026 20:15:31.123-4  " + payload)
            splitter.feed(build_event(ts, fields, 1))
        return splitter.finish()[0].analysis

    def test_two_casters_of_one_spell_are_two_auras(self):
        """Keyed by target and spell alone, the second application found
        the slot taken and was dropped, and its removal closed the first
        one's interval. Two players casting the same buff on one target
        is not rare -- the owner's logs do it constantly."""
        segments = self._analyse([
            (0, 'ENCOUNTER_START,1,"Golem",16,5,2000'),
            (1000, 'SPELL_AURA_APPLIED,%s,%s,111,"Clairvoyance",0x1,BUFF'
                   % (self.HEALER, self.VICTIM)),
            (2000, 'SPELL_AURA_APPLIED,%s,%s,111,"Clairvoyance",0x1,BUFF'
                   % (self.MAGE, self.VICTIM)),
            (5000, 'SPELL_AURA_REMOVED,%s,%s,111,"Clairvoyance",0x1,BUFF'
                   % (self.HEALER, self.VICTIM)),
            (9000, 'SPELL_AURA_REMOVED,%s,%s,111,"Clairvoyance",0x1,BUFF'
                   % (self.MAGE, self.VICTIM)),
            (20000, 'ENCOUNTER_END,1,"Golem",16,5,1,20000'),
        ])
        rows = {(name, source): ms for name, source, ms, _id
                in segments.player_uptimes(self.VICTIM_GUID, kind="BUFF")}
        self.assertEqual(rows, {("Clairvoyance", "Tisane"): 4000,
                                ("Clairvoyance", "Braise"): 7000})

    def test_two_units_sharing_a_name_are_two_auras(self):
        """The caster is told apart by GUID, not by name: several
        creatures called "Ombre etherienne" stack their own copy of one
        debuff on the same player, and the name cannot separate them."""
        segments = self._analyse([
            (0, 'ENCOUNTER_START,1,"Golem",16,5,2000'),
            (1000, 'SPELL_AURA_APPLIED,%s,%s,222,"Celerite",0x20,DEBUFF'
                   % (self.MOB_A, self.VICTIM)),
            (2000, 'SPELL_AURA_APPLIED,%s,%s,222,"Celerite",0x20,DEBUFF'
                   % (self.MOB_B, self.VICTIM)),
            (4000, 'SPELL_AURA_REMOVED,%s,%s,222,"Celerite",0x20,DEBUFF'
                   % (self.MOB_A, self.VICTIM)),
            (6000, 'SPELL_AURA_REMOVED,%s,%s,222,"Celerite",0x20,DEBUFF'
                   % (self.MOB_B, self.VICTIM)),
            (20000, 'ENCOUNTER_END,1,"Golem",16,5,1,20000'),
        ])
        # One row, because the report groups by the caster's *name* -- and
        # 1000..6000 held by one or the other, counted once.
        rows = segments.player_uptimes(self.VICTIM_GUID, kind="DEBUFF")
        self.assertEqual([(name, source, ms) for name, source, ms, _id in rows],
                         [("Celerite", "Ombre", 5000)])

    def test_overlapping_copies_of_one_aura_count_once(self):
        """Six "Tortionnaire infidele" each held their own Fixation on one
        player at the same moment. Summing the six gave 249 seconds of a
        181-second fight; what a reader means by a percentage of the
        fight is the union of the intervals."""
        payloads = [(0, 'ENCOUNTER_START,1,"Golem",16,5,2000')]
        for index in range(6):
            mob = ('Creature-0-9-2-1-70000-000000000%d,"Tortionnaire",0xa48,0x0'
                   % (index + 1))
            payloads.append((1000 + index * 100,
                             'SPELL_AURA_APPLIED,%s,%s,333,"Fixation",0x20,DEBUFF'
                             % (mob, self.VICTIM)))
        for index in range(6):
            mob = ('Creature-0-9-2-1-70000-000000000%d,"Tortionnaire",0xa48,0x0'
                   % (index + 1))
            payloads.append((8000 + index * 100,
                             'SPELL_AURA_REMOVED,%s,%s,333,"Fixation",0x20,DEBUFF'
                             % (mob, self.VICTIM)))
        payloads.append((20000, 'ENCOUNTER_END,1,"Golem",16,5,1,20000'))
        analysis = self._analyse(payloads)
        rows = analysis.player_uptimes(self.VICTIM_GUID, kind="DEBUFF")
        self.assertEqual(len(rows), 1)
        # 1000 to 8500, counted once, not six times over.
        self.assertEqual(rows[0][2], 7500)
        for milliseconds in analysis.players[self.VICTIM_GUID].auras_gained.values():
            self.assertLessEqual(milliseconds, analysis.duration_ms)


class TestAgainstWarcraftLogs(unittest.TestCase):
    """The owner exported the same Mythic+ key from Warcraft Logs and
    asked whether the numbers matched. Three gaps were real gaps, and
    each one keeps a test here."""

    TANK = 'Player-9-00000001,"Ardoise-Dalaran-EU",0x511,0x0'
    HEALER = 'Player-9-00000002,"Tisane-Dalaran-EU",0x512,0x0'
    MOB = 'Creature-0-9-2-1-70000-0000000001,"Golem",0xa48,0x0'
    PET = 'Pet-0-9-2-1-00099,"Cendre",0x1114,0x0'

    def _analyse(self, payloads):
        splitter = Splitter(analysis_factory=SegmentAnalysis)
        for index, payload in enumerate(payloads):
            _ts, fields = split_line("9/18/2026 20:15:31.123-4  " + payload)
            splitter.feed(build_event(index * 1000, fields, index + 1))
        return splitter.finish()[0].analysis

    def test_a_shield_is_credited_to_whoever_cast_it(self):
        """A discipline priest's whole output is absorbs, and they were
        in no ledger at all: the export showed 53.8M on one player where
        this reader showed nothing."""
        analysis = self._analyse([
            'ENCOUNTER_START,1,"Golem",16,5,2000',
            # the wide form, with the attacker's own spell named
            'SPELL_ABSORBED,%s,%s,444,"Balayage",0x4,%s,1002,"Bouclier",0x2,900,1500,nil'
            % (self.MOB, self.TANK, self.HEALER),
            # ...and the narrow form, without it
            'SPELL_ABSORBED,%s,%s,%s,1002,"Bouclier",0x2,100,1500,nil'
            % (self.MOB, self.TANK, self.HEALER),
            'ENCOUNTER_END,1,"Golem",16,5,1,3000',
        ])
        healer = analysis.players["Player-9-00000002"]
        tank = analysis.players["Player-9-00000001"]
        self.assertEqual(healer.absorb_done, 1000)
        self.assertEqual(tank.absorbed_taken, 1000)
        self.assertEqual(sum(x.total for x in healer.absorb_by_ability.values()), 1000)

    def test_a_shield_is_named_in_its_own_table(self):
        """SPELL_ABSORBED has no prefix, so `event.spell_id` reads 0 and
        `spell_name` reads empty: banking a shield under those put every
        shield of every player in one row called "Attaque". The shield's
        own id and name sit six and five fields from the end."""
        analysis = self._analyse([
            'ENCOUNTER_START,1,"Golem",16,5,2000',
            'SPELL_ABSORBED,%s,%s,444,"Balayage",0x4,%s,17,"Mot de pouvoir",0x2,900,1500,nil'
            % (self.MOB, self.TANK, self.HEALER),
            'SPELL_ABSORBED,%s,%s,%s,77535,"Bouclier de sang",0x20,100,1500,nil'
            % (self.MOB, self.TANK, self.HEALER),
            'ENCOUNTER_END,1,"Golem",16,5,1,3000',
        ])
        healer = analysis.players["Player-9-00000002"]
        rows = {ability.name: ability.total
                for ability in healer.absorb_by_ability.values()}
        self.assertEqual(rows, {"Mot de pouvoir": 900, "Bouclier de sang": 100})

    def test_a_summons_damage_taken_is_not_its_owners(self):
        """A mage whose elemental is being chewed on has not taken that
        damage: nobody healed them for it and their health never moved.
        On a real key it was 12% of what one player was shown as having
        survived -- and the pet's health became the owner's, so every
        player read "lowest health 0%" for a pet that had died."""
        pet = 'Pet-0-9-2-1-00099,"Cendre",0x1114,0x0'
        block_pet = ",".join(advanced_block(19, info="Pet-0-9-2-1-00099", hp=0, maxhp=1000))
        block_owner = ",".join(advanced_block(19, info="Player-9-00000001",
                                              hp=900, maxhp=1000))
        analysis = self._analyse([
            'ENCOUNTER_START,1,"Golem",16,5,2000',
            'SPELL_SUMMON,%s,%s,777,"Invocation",0x1' % (self.TANK, pet),
            'SPELL_DAMAGE,%s,%s,444,"Balayage",0x4,%s,300,300,-1,4,0,0,0,nil,nil,nil,ST'
            % (self.MOB, self.TANK, block_owner),
            'SPELL_DAMAGE,%s,%s,444,"Balayage",0x4,%s,1000,1000,-1,4,0,0,0,nil,nil,nil,ST'
            % (self.MOB, pet, block_pet),
            'ENCOUNTER_END,1,"Golem",16,5,1,5000',
        ])
        tank = analysis.players["Player-9-00000001"]
        self.assertEqual(tank.damage_taken, 300)
        self.assertEqual(tank.pet_damage_taken, 1000)
        # the pet hit the floor; the player was at 90%
        self.assertEqual(tank.min_hp_fraction, 0.9)
        # ...and the group's graph still shows everything it took
        drawn = sum(row[1] for row in analysis.timeline_series()[0])
        self.assertEqual(drawn, 1300)

    def test_the_null_guid_never_becomes_a_player(self):
        """The client writes 0000000000000000 with player flags on a few
        lines per log -- an "Anti-Magic Zone" tick, for instance. It used
        to open a ledger of its own, and the report grew a player called
        "nil"."""
        nobody = '0000000000000000,nil,0x511,0x0'
        analysis = self._analyse([
            'ENCOUNTER_START,1,"Golem",16,5,2000',
            'SPELL_CAST_SUCCESS,%s,%s,145629,"Zone anti-magie",0x20' % (nobody, self.MOB),
            'SPELL_DAMAGE,%s,%s,145629,"Zone anti-magie",0x20,500,500,-1,1,0,0,0,nil,nil,nil,ST'
            % (nobody, self.MOB),
            'ENCOUNTER_END,1,"Golem",16,5,1,3000',
        ])
        self.assertEqual([p.short_name for p in analysis.players.values()], [])
        # ...and its damage is unattributed rather than silently gone.
        self.assertEqual(analysis.orphan_damage, 500)
        self.assertIn("source non nommee par le journal", analysis.orphan_sources)

    def test_a_pets_casts_are_counted_apart(self):
        """The export counts 880 casts where this reader counted 3,668:
        pets, plus proc-generated casts the file cannot tell from real
        ones. The pets' share is knowable, so it is shown."""
        analysis = self._analyse([
            'ENCOUNTER_START,1,"Golem",16,5,2000',
            'SPELL_SUMMON,%s,%s,777,"Invocation",0x1' % (self.TANK, self.PET),
            'SPELL_CAST_SUCCESS,%s,%s,222,"Frappe",0x1' % (self.TANK, self.MOB),
            'SPELL_CAST_SUCCESS,%s,%s,333,"Morsure",0x1' % (self.PET, self.MOB),
            'SPELL_CAST_SUCCESS,%s,%s,333,"Morsure",0x1' % (self.PET, self.MOB),
            'ENCOUNTER_END,1,"Golem",16,5,1,5000',
        ])
        tank = analysis.players["Player-9-00000001"]
        self.assertEqual(tank.casts, 3)
        self.assertEqual(tank.pet_casts, 2)


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
        # The rule is that the page *fetches* nothing when it opens: no
        # script, no stylesheet, no image, no font, no import. A Wowhead
        # link in an anchor is not a fetch -- it is followed only if the
        # reader clicks it -- so the test names the mechanisms rather than
        # banning the string "https", which it used to do and which would
        # now fail for the wrong reason.
        self.assertNotIn("<script", page)
        self.assertNotIn("<iframe", page)
        self.assertNotIn("@import", page)
        self.assertNotIn("stylesheet", page)
        self.assertNotIn(" src=", page)
        self.assertNotIn("url(", page)
        for fragment in re.findall(r"https?://[^\s\"']+", page):
            self.assertIn("wowhead.com", fragment)
        self.assertIn("Golem d&#x27;essai", page)

    def test_spell_links_follow_the_chosen_language(self):
        import tempfile

        for language, expected in (("fr", "/fr/spell="), ("en", ".com/spell=")):
            with tempfile.TemporaryDirectory() as directory:
                target = os.path.join(directory, "rapport.html")
                ReportWriter(self.log, self.segments, target, wowhead=language).write()
                with open(target, encoding="utf-8") as handle:
                    page = handle.read()
            self.assertIn(expected, page, language)

    def test_links_can_be_turned_off_entirely(self):
        import tempfile

        with tempfile.TemporaryDirectory() as directory:
            target = os.path.join(directory, "rapport.html")
            ReportWriter(self.log, self.segments, target, wowhead="off").write()
            with open(target, encoding="utf-8") as handle:
                page = handle.read()
        self.assertNotIn("wowhead.com", page)
        self.assertIn("Frappe d&#x27;essai", page)

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
        # the curve says whose health it is
        self.assertIn("Golem d&#x27;essai", page)

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

    def test_the_report_carries_the_group_and_the_enemies(self):
        import tempfile

        with tempfile.TemporaryDirectory() as directory:
            target = os.path.join(directory, "rapport.html")
            ReportWriter(self.log, self.segments, target).write()
            with open(target, encoding="utf-8") as handle:
                page = handle.read()
        self.assertIn("Composition du groupe", page)
        self.assertIn("Guerrier Protection", page)
        self.assertIn("Detail par ennemi", page)
        self.assertIn("Ce qu&#x27;il inflige", page)
        self.assertIn("Principale cible", page)

    def test_only_keeps_the_fight_asked_for(self):
        from logswow.cli import select_segments

        self.assertEqual(len(select_segments(self.segments, "2")), 1)
        self.assertEqual(select_segments(self.segments, "2")[0].index, 2)
        self.assertEqual(len(select_segments(self.segments, "donjon")), 1)
        self.assertEqual(select_segments(self.segments, "rien du tout"), [])
        self.assertEqual(len(select_segments(self.segments, None)), 3)

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


class TestFifthAuditFindings(unittest.TestCase):
    """The 2026-09-27 audit, run on two real logs the owner supplied
    during it: a raid night and a Mythic+ session. Each test here is a
    defect one of them showed, rebuilt from fabricated lines."""

    PLAYER = 'Player-9-00000001,"Ardoise-Dalaran-EU",0x511,0x0'
    PLAYER_GUID = "Player-9-00000001"

    @staticmethod
    def _mob(number, name):
        guid = "Creature-0-9-2-1-%d-%010d" % (70000 + number, number)
        return guid, '%s,"%s",0xa48,0x0' % (guid, name)

    def _run(self, timed_payloads):
        """[(milliseconds, payload)] -> segments, finished."""
        splitter = Splitter(analysis_factory=SegmentAnalysis)
        for index, (ms, payload) in enumerate(timed_payloads):
            _ts, fields = split_line("9/18/2026 20:15:31.123-4  " + payload)
            splitter.feed(build_event(ms, fields, index + 1))
        return splitter.finish()

    def _hit(self, mob, amount=5000, hp=500, maxhp=1000):
        guid, actor = mob
        block = ",".join(advanced_block(19, info=guid, hp=hp, maxhp=maxhp))
        return ('SPELL_DAMAGE,%s,%s,222,"Frappe",0x1,%s,%d,%d,-1,1,0,0,0,nil,nil,nil,ST'
                % (self.PLAYER, actor, block, amount, amount))

    def _page(self, segments):
        import tempfile

        log, _fixture_segments = run_fixture()
        with tempfile.TemporaryDirectory() as directory:
            target = os.path.join(directory, "rapport.html")
            ReportWriter(log, segments, target).write()
            with open(target, encoding="utf-8") as handle:
                return handle.read()

    def test_a_self_contradicting_health_reading_does_not_vote(self):
        """A real key wrote one unit at 3,814,068 health out of a maximum
        of 24, and the pooled health of the engaged enemies was drawn at
        8,724,400% -- far outside the graph."""
        sane = self._mob(1, "Sbire")
        broken_guid, broken = self._mob(2, "Seide")
        block = ",".join(advanced_block(19, info=broken_guid, hp=3814068, maxhp=24))
        segments = self._run([
            (0, 'CHALLENGE_MODE_START,"Donjon",2000,500,7,[9]'),
            (1000, self._hit(sane)),
            (1500, 'SPELL_CAST_SUCCESS,%s,%s,9,"Cri",0x1,%s' % (broken, self.PLAYER, block)),
            (2500, self._hit(sane, hp=400)),
            (60000, self._hit(self._mob(3, "Brute"))),
            (61000, "CHALLENGE_MODE_END,2000,1,7,61000"),
        ])
        analysis = segments[0].analysis
        pools = [row[4] for row in analysis.timeline_series()[0] if row[4] is not None]
        self.assertTrue(pools)
        self.assertTrue(all(0 <= value <= 1 for value in pools), pools)
        self.assertEqual(analysis.inconsistent_health, 1)

    def test_a_council_is_counted_on_the_boss(self):
        """No unit of "Le conseil des tribus" bore the encounter's name,
        so a real key counted its 101M of damage as trash and every
        player's "Part sur les boss" read 0%."""
        segments = self._run([
            (0, 'CHALLENGE_MODE_START,"Donjon",2000,500,7,[9]'),
            (1000, self._hit(self._mob(1, "Sbire"), 3000)),
            (60000, 'ENCOUNTER_START,77,"Le conseil",8,5,2000'),
            (61000, self._hit(self._mob(2, "Chef A"), 7000)),
            (62000, self._hit(self._mob(3, "Chef B"), 4000)),
            (90000, 'ENCOUNTER_END,77,"Le conseil",8,5,1,30000'),
            (91000, "CHALLENGE_MODE_END,2000,1,7,91000"),
        ])
        key = next(s for s in segments if s.kind == "keystone").analysis
        council = key.blocks[-1]
        self.assertEqual(council.damage_boss, 11000)
        self.assertEqual(key.blocks[0].damage_boss, 0)
        self.assertEqual(key.players[self.PLAYER_GUID].damage_to_bosses, 11000)
        self.assertEqual(key.window_encounters, ["Le conseil"])
        self.assertTrue(council.label(boss_names=key.boss_names).startswith("Le conseil"))
        # ...and the encounter's own segment says the same.
        boss = next(s for s in segments if s.kind == "encounter").analysis
        self.assertEqual(sum(b.damage_boss for b in boss.blocks), boss.total_damage)
        self.assertIn("aucune unite ne porte le nom de la rencontre", self._page(segments))

    def test_a_wipe_and_a_kill_wear_different_badges(self):
        """On a real key the wipe and the kill on Mchimba wore the same
        green badge, the colour a kill has everywhere else on the page."""
        boss = self._mob(1, "Mchimba")
        segments = self._run([
            (0, 'CHALLENGE_MODE_START,"Donjon",2000,500,7,[9]'),
            (1000, 'ENCOUNTER_START,5,"Mchimba",8,5,2000'),
            (2000, self._hit(boss)),
            (20000, 'ENCOUNTER_END,5,"Mchimba",8,5,0,19000'),
            (80000, 'ENCOUNTER_START,5,"Mchimba",8,5,2000'),
            (81000, self._hit(boss)),
            (99000, 'ENCOUNTER_END,5,"Mchimba",8,5,1,19000'),
            (100000, "CHALLENGE_MODE_END,2000,1,7,100000"),
        ])
        key = next(s for s in segments if s.kind == "keystone").analysis
        self.assertEqual([block.outcome for block in key.blocks], [False, True])
        page = self._page(segments)
        self.assertIn("boss &middot; echec", page)
        self.assertIn("boss &middot; reussite", page)
        self.assertNotIn("<span class='pill ok'>boss</span>", page)

    def test_a_lull_inside_an_encounter_does_not_split_the_pull(self):
        """The council fight was cut in two by an intermission longer
        than the pull gap: one boss, two pulls."""
        boss = self._mob(1, "Golem")
        segments = self._run([
            (0, 'CHALLENGE_MODE_START,"Donjon",2000,500,7,[9]'),
            (1000, 'ENCOUNTER_START,5,"Golem",8,5,2000'),
            (2000, self._hit(boss)),
            (30000, self._hit(boss)),
            (40000, 'ENCOUNTER_END,5,"Golem",8,5,1,39000'),
            (41000, "CHALLENGE_MODE_END,2000,1,7,41000"),
        ])
        for segment in segments:
            self.assertEqual(len(segment.analysis.blocks), 1, segment.kind)

    # -- names ---------------------------------------------------------------

    def test_a_creature_keeps_the_part_after_its_dash_in_every_table(self):
        """"Jeune-ne chancrecaille" was "Jeune" in 21 cells of the owner's
        raid report: auras, healing targets and unattributed sources
        split every name at its first dash, a player's or not."""
        bat = self._mob(1, "Chauve-souris")[1]
        healer = 'Player-9-00000002,"Tisane-Dalaran-EU",0x512,0x0'
        escort = 'Creature-0-9-2-1-70009-0000000009,"Porte-etendard",0xa18,0x0'
        segments = self._run([
            (0, 'ENCOUNTER_START,1,"Golem",16,5,2000'),
            (1000, 'SPELL_AURA_APPLIED,%s,%s,666,"Morsure",0x20,DEBUFF' % (bat, healer)),
            (2000, 'SPELL_HEAL,%s,%s,555,"Vague",0x2,4000,4000,0,0,nil' % (healer, escort)),
            (4000, 'SPELL_AURA_REMOVED,%s,%s,666,"Morsure",0x20,DEBUFF' % (bat, healer)),
            (5000, 'ENCOUNTER_END,1,"Golem",16,5,1,5000'),
        ])
        analysis = segments[0].analysis
        player = analysis.players["Player-9-00000002"]
        self.assertEqual(list(player.healing_to), ["Porte-etendard"])
        sources = [row[1] for row in analysis.player_uptimes(player.guid, kind="DEBUFF")]
        self.assertEqual(sources, ["Chauve-souris"])

    def test_a_player_whose_pet_struck_first_keeps_their_own_name(self):
        """The owner's row was named after whichever unit opened it: a
        hunter whose pet hit first appeared as the pet, in the rankings,
        the composition and the deaths."""
        pet_guid = "Pet-0-9-2-1-00099"
        block = advanced_block(19, info=pet_guid)
        block[1] = self.PLAYER_GUID  # ownerGUID
        golem = self._mob(1, "Golem")
        segments = self._run([
            (0, 'ENCOUNTER_START,1,"Golem",16,5,2000'),
            (1000, 'SWING_DAMAGE,%s,"Crocs",0x1114,0x0,%s,%s,900,1200,-1,1,0,0,0,nil,nil,nil'
             % (pet_guid, golem[1], ",".join(block))),
            (2000, self._hit(golem)),
            (3000, 'ENCOUNTER_END,1,"Golem",16,5,1,3000'),
        ])
        player = segments[0].analysis.players[self.PLAYER_GUID]
        self.assertEqual(player.short_name, "Ardoise")
        self.assertEqual(player.damage_done, 5900)

    def test_two_players_sharing_a_name_stay_two_people(self):
        """Two "Tisane" on two realms: healing went into one row and the
        second one's auras were credited to the first. The realm is never
        shown, so the second becomes "Tisane (2)"."""
        first = 'Player-9-00000002,"Tisane-Dalaran-EU",0x512,0x0'
        second = 'Player-9-00000005,"Tisane-Hyjal-EU",0x514,0x0'
        segments = self._run([
            (0, 'ENCOUNTER_START,1,"Golem",16,5,2000'),
            (1000, 'SPELL_HEAL,%s,%s,555,"Vague",0x2,4000,4000,0,0,nil' % (first, first)),
            (1500, 'SPELL_HEAL,%s,%s,555,"Vague",0x2,1000,1000,0,0,nil' % (first, second)),
            (2000, 'SPELL_CAST_SUCCESS,%s,%s,17,"Mot",0x2' % (second, first)),
            (2000, 'SPELL_AURA_APPLIED,%s,%s,17,"Mot",0x2,BUFF' % (second, first)),
            (3000, 'SPELL_AURA_REMOVED,%s,%s,17,"Mot",0x2,BUFF' % (second, first)),
            (4000, 'ENCOUNTER_END,1,"Golem",16,5,1,4000'),
        ])
        analysis = segments[0].analysis
        healer = analysis.players["Player-9-00000002"]
        other = analysis.players["Player-9-00000005"]
        self.assertEqual(healer.healing_to, {"Tisane": 4000, "Tisane (2)": 1000})
        self.assertEqual(other.short_name, "Tisane (2)")
        self.assertEqual(list(other.auras_applied), [(17, "Mot", "Tisane")])
        self.assertEqual(healer.auras_applied, {})

    # -- segments and output ---------------------------------------------------

    def test_an_encounter_that_never_ended_does_not_swallow_the_file(self):
        """A disconnect leaves an ENCOUNTER_START with no END. Left open,
        it took in every later event: the next boss counted twice, and a
        pull that lasted until the log ended."""
        boss = self._mob(1, "Golem")
        segments = self._run([
            (0, 'ENCOUNTER_START,1,"Golem",16,5,2000'),
            (60000, self._hit(boss)),
            (120000, 'ENCOUNTER_START,1,"Golem",16,5,2000'),
            (180000, self._hit(boss)),
            (240000, 'ENCOUNTER_END,1,"Golem",16,5,1,120000'),
            (300000, 'ENCOUNTER_START,2,"Autre",16,5,2000'),
            (360000, self._hit(boss)),
            (420000, 'ENCOUNTER_END,2,"Autre",16,5,1,120000'),
        ])
        lost = segments[0]
        self.assertTrue(lost.truncated)
        self.assertEqual(lost.duration_ms, 60000)
        self.assertEqual(lost.analysis.total_damage, 5000)
        self.assertEqual([s.analysis.total_damage for s in segments], [5000, 5000, 5000])

    def test_the_report_never_overwrites_a_file_that_is_not_a_report(self):
        """`-o autre-journal.txt` turned another combat log into a web
        page and said "Rapport ecrit". Only the log being read was
        protected."""
        import contextlib
        import io
        import shutil
        import tempfile

        from logswow.cli import main

        with tempfile.TemporaryDirectory() as directory:
            other = os.path.join(directory, "autre-journal.txt")
            shutil.copy(FIXTURE, other)
            with contextlib.redirect_stderr(io.StringIO()) as said:
                code = main(["report", FIXTURE, "-q", "-o", other])
            self.assertEqual(code, 2)
            self.assertIn("--force", said.getvalue())
            with open(other, encoding="utf-8") as handle:
                self.assertTrue(handle.read().startswith("9/18/2026"))
            # A report of ours is simply replaced, and nothing is left behind.
            page = os.path.join(directory, "rapport.html")
            self.assertEqual(main(["report", FIXTURE, "-q", "-o", page]), 0)
            self.assertEqual(main(["report", FIXTURE, "-q", "-o", page]), 0)
            self.assertEqual(sorted(os.listdir(directory)), ["autre-journal.txt", "rapport.html"])
            # --force is for the first case, never for the log itself.
            self.assertEqual(main(["report", FIXTURE, "-q", "-o", other, "--force"]), 0)
            log = os.path.join(directory, "journal.txt")
            shutil.copy(FIXTURE, log)
            with contextlib.redirect_stderr(io.StringIO()) as said:
                self.assertEqual(main(["report", log, "-q", "-o", log, "--force"]), 2)
            self.assertIn("journal lui-meme", said.getvalue())
            with open(log, encoding="utf-8") as handle:
                self.assertTrue(handle.read().startswith("9/18/2026"))


class TestWhatTheAuditLeftUntested(unittest.TestCase):
    """Paths the 2026-09-27 audit measured at 7% (diagnose), 59% (cli)
    or never executed at all (the timeline's collapse, which runs for
    every fight longer than 6 min 40 -- every Mythic+ key)."""

    PLAYER = 'Player-9-00000001,"Ardoise-Dalaran-EU",0x511,0x0'
    MOB = 'Creature-0-9-2-1-70000-0000000001,"Golem",0xa48,0x0'

    def _run(self, timed_payloads):
        splitter = Splitter(analysis_factory=SegmentAnalysis)
        for index, (ms, payload) in enumerate(timed_payloads):
            _ts, fields = split_line("9/18/2026 20:15:31.123-4  " + payload)
            splitter.feed(build_event(ms, fields, index + 1))
        return splitter.finish()

    def test_a_long_fight_is_collapsed_without_losing_anything(self):
        """Thirty minutes of hits, one every ten seconds, and deaths: the
        drawn series stays bounded and evenly spaced, and every hit and
        every death is still in it."""
        from logswow.timeline import MAX_TIMELINE_BUCKETS

        payloads = [(0, 'ENCOUNTER_START,1,"Golem",16,5,2000')]
        hits = 0
        for second in range(0, 1800, 10):
            payloads.append((second * 1000 + 500,
                             'SPELL_DAMAGE,%s,%s,444,"Balayage",0x4,700,700,-1,4,0,0,0,'
                             'nil,nil,nil,ST' % (self.MOB, self.PLAYER)))
            hits += 700
        for second in (400, 1200):
            payloads.append((second * 1000 + 600,
                             "UNIT_DIED,0000000000000000,nil,0x80000000,0x80000000,%s,0"
                             % self.PLAYER))
        payloads.append((1800000, 'ENCOUNTER_END,1,"Golem",16,5,0,1800000'))
        payloads.sort(key=lambda item: item[0])
        analysis = self._run(payloads)[0].analysis
        series, bucket_ms = analysis.timeline_series()
        self.assertLessEqual(len(series), MAX_TIMELINE_BUCKETS)
        self.assertGreater(bucket_ms, 1000)
        steps = {round(b[0] - a[0], 6) for a, b in zip(series, series[1:])}
        self.assertEqual(steps, {bucket_ms / 1000.0})
        self.assertEqual(sum(row[1] for row in series), hits)
        self.assertEqual(sum(row[3] for row in series), 2)

    def test_an_encounter_nobody_fought_is_not_a_wipe(self):
        """The owner's raid opened on an encounter 8 ms long, with not
        one hit in it, and the page counted it as a wipe."""
        segments = self._run([
            (0, 'ENCOUNTER_START,1,"Golem",16,5,2000'),
            (8, 'ENCOUNTER_END,1,"Golem",16,5,0,8'),
            (60000, 'ENCOUNTER_START,1,"Golem",16,5,2000'),
            (61000, 'SPELL_DAMAGE,%s,%s,1,"Frappe",0x1,500,500,-1,1,0,0,0,nil,nil,nil,ST'
             % (self.PLAYER, self.MOB)),
            (90000, 'ENCOUNTER_END,1,"Golem",16,5,0,30000'),
        ])
        self.assertEqual([s.outcome for s in segments], ["sans combat", "echec"])
        self.assertEqual([s.is_wipe for s in segments], [False, True])

    def test_the_fast_split_gives_exactly_what_the_scanner_gives(self):
        """The csv path must never disagree with the character loop: on
        every line of the fixture, and on lines built to trip it."""
        from logswow.tokenize import _scan_fields

        with open(FIXTURE, encoding="utf-8") as handle:
            payloads = [line.rstrip("\n").split("  ", 1)[1].strip()
                        for line in handle if "  " in line]
        payloads += [
            'a,"b,c",d', 'a,"b""c",d', 'a,ab"c,d"e,f', 'a, "b",c', 'a,"b" ,c',
            'a,"unterminated', 'a,,b,', '"",x', 'a,"x\\"y",z', ' a , b ', 'a,"b"c,d',
            '"', ',', 'a,"b,"', 'x,[1,2],(3)', 'SPELL_DAMAGE,"Eclat d\'essai",0x1',
        ]
        for payload in payloads:
            self.assertEqual(split_fields(payload), _scan_fields(payload), payload)

    def test_the_language_is_read_without_the_call_python_removes(self):
        """locale.getdefaultlocale() is gone in Python 3.15; on Windows,
        where no LANG is set, the links would have silently gone English."""
        import warnings
        from unittest import mock

        from logswow import wowhead

        with mock.patch.dict(os.environ, {"LC_ALL": "", "LC_MESSAGES": "", "LANG": "",
                                          "LANGUAGE": ""}):
            with warnings.catch_warnings():
                warnings.simplefilter("error", DeprecationWarning)
                language = wowhead.system_language()
        self.assertNotIn(language, ("c", "posix"))
        self.assertIn(wowhead.resolve("auto"), wowhead.PREFIXES.values())

    # -- the command line ----------------------------------------------------

    def _main(self, argv):
        import contextlib
        import io

        from logswow.cli import main

        out, err = io.StringIO(), io.StringIO()
        with contextlib.redirect_stdout(out), contextlib.redirect_stderr(err):
            try:
                code = main(argv)
            except SystemExit as leaving:  # argparse refusing an option
                code = leaving.code
        return code, out.getvalue(), err.getvalue()

    def test_diagnose_shows_its_work(self):
        code, out, _err = self._main(["diagnose", FIXTURE])
        self.assertEqual(code, 0)
        for section in ("DISPOSITION MESUREE DANS CE FICHIER", "bloc avance         : 19",
                        "champ baseAmount    : present", "points de vie incoherents   : 0",
                        "COMBATS DELIMITES : 3", "EVENEMENTS (",
                        "[SCHEMA INCONNU] ", "PROBLEMES DE LECTURE : 2"):
            self.assertIn(section, out)
        code, out, _err = self._main(["diagnose", FIXTURE, "--limit", "5"])
        self.assertEqual(code, 0)
        self.assertIn("EVENEMENTS (", out)

    def test_list_prints_one_line_per_fight(self):
        code, out, _err = self._main(["list", FIXTURE, "-q"])
        self.assertEqual(code, 0)
        lines = out.strip().splitlines()
        self.assertEqual(len(lines), 4)
        self.assertIn("reussite", lines[1])
        self.assertIn("echec", lines[2])
        self.assertIn("dans les temps", lines[3])

    def test_numbers_that_make_no_sense_are_refused_in_french(self):
        for argv in (["report", FIXTURE, "--pull-gap", "nan"],
                     ["report", FIXTURE, "--pull-gap", "inf"],
                     ["report", FIXTURE, "--pull-gap", "-5"],
                     ["list", FIXTURE, "--pull-gap", "abc"],
                     ["diagnose", FIXTURE, "--limit", "-1"]):
            code, _out, err = self._main(argv)
            self.assertEqual(code, 2, argv)
            self.assertNotIn("Traceback", err)
            self.assertTrue("secondes" in err or "superieur a zero" in err
                            or "entier" in err, err)

    def test_where_finds_a_log_folder_under_steam_and_lutris(self):
        """The owner runs Linux Mint: the game lives in a launcher's own
        copy of drive C, which `where` did not look in."""
        import tempfile
        from unittest import mock

        from logswow.cli import default_log_locations

        retail = os.path.join("drive_c", "Program Files (x86)", "World of Warcraft",
                              "_retail_", "Logs")
        with tempfile.TemporaryDirectory() as home:
            steam = os.path.join(home, ".steam", "steam", "steamapps", "compatdata",
                                 "3141592", "pfx", retail)
            lutris = os.path.join(home, "Games", "battlenet", retail)
            for folder in (steam, lutris):
                os.makedirs(folder)
            with open(os.path.join(steam, "WoWCombatLog.txt"), "w") as handle:
                handle.write("x")
            with mock.patch.dict(os.environ, {"HOME": home}):
                found = default_log_locations()
                code, out, _err = self._main(["where"])
        self.assertEqual(sorted(found), sorted([lutris, steam]))
        self.assertEqual(code, 0)
        self.assertIn("WoWCombatLog.txt", out)


class TestRelease(unittest.TestCase):
    """The one file a release ships must run on its own, from anywhere."""

    def test_the_current_version_says_what_changed(self):
        """The release workflow publishes CHANGELOG.md's section for the
        tagged version, and refuses to publish without one."""
        import subprocess

        from logswow import __version__

        result = subprocess.run(
            [sys.executable, os.path.join(ROOT, "tools", "release-notes"), __version__],
            capture_output=True, text=True, timeout=60)
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertGreater(len(result.stdout.strip()), 100)

    def test_the_single_file_build_runs_and_keeps_its_exit_codes(self):
        import subprocess
        import tempfile

        from logswow import __version__

        with tempfile.TemporaryDirectory() as directory:
            built = subprocess.run(
                [sys.executable, os.path.join(ROOT, "tools", "build-pyz"), directory],
                capture_output=True, text=True, timeout=120)
            self.assertEqual(built.returncode, 0, built.stderr)
            archive = os.path.join(directory, "logswow-%s.pyz" % __version__)
            self.assertTrue(os.path.isfile(archive))

            def run(*argv):
                return subprocess.run([sys.executable, archive] + list(argv), cwd=directory,
                                      capture_output=True, text=True, timeout=120)

            self.assertIn(__version__, run("--version").stdout)
            page = os.path.join(directory, "rapport.html")
            self.assertEqual(run("report", FIXTURE, "-q", "-o", page).returncode, 0)
            self.assertTrue(os.path.isfile(page))
            self.assertEqual(run("report", os.path.join(directory, "absent.txt")).returncode, 2)

            import zipfile

            names = zipfile.ZipFile(archive).namelist()
            self.assertIn("LICENSE", names)
            self.assertFalse([n for n in names if n.startswith(("tests", "examples"))
                              or n.endswith(".txt")])


class TestCastOrder(unittest.TestCase):
    """The order a player cast their spells in, pull by pull (2026-09-27)."""

    PLAYER = 'Player-9-00000001,"Ardoise-Dalaran-EU",0x511,0x0'
    GUID = "Player-9-00000001"
    MOB = 'Creature-0-9-2-1-70000-0000000001,"Golem",0xa48,0x0'
    PET = 'Pet-0-9-2-1-00099,"Cendre",0x1114,0x0'

    def _cast(self, spell_id, name, cost="0", source=None):
        block = advanced_block(19, info=self.GUID)
        block[-6] = cost                      # powerCost, measured in both shapes
        return ('SPELL_CAST_SUCCESS,%s,%s,%d,"%s",0x1,%s'
                % (source or self.PLAYER, self.MOB, spell_id, name, ",".join(block)))

    def _run(self, timed_payloads):
        splitter = Splitter(analysis_factory=SegmentAnalysis)
        for index, (ms, payload) in enumerate(timed_payloads):
            _ts, fields = split_line("9/18/2026 20:15:31.123-4  " + payload)
            splitter.feed(build_event(ms, fields, index + 1))
        return splitter.finish()

    def test_a_triggered_spell_is_told_from_pressed_ones(self):
        """Measured on two real logs: a triggered cast lands in the same
        instant as another, costs nothing, and comes back quickly. A spell
        a macro fires beside another is free and simultaneous too, but it
        is a long cooldown -- that is what tells them apart."""
        from logswow.castorder import classify_triggered

        log = []
        for i in range(12):
            ts = i * 2500
            log.append((ts, 100, "Frappe", True, False))          # pressed, paid
            log.append((ts + 5, 200, "Eclat", False, False))       # rides on it
        for i in range(10):                                       # a macro'd cooldown
            ts = 1000 + i * 120000
            log.append((ts, 300, "Pierre de soins", False, False))
            log.append((ts, 301, "Bouclier", True, False))
        for i in range(5):                                        # too few to judge
            log.append((200 + i * 2500, 400, "Rare", False, False))
        self.assertEqual(classify_triggered(log), frozenset({200}))
        # A pet's casts are their own group, never "triggered".
        pets = [(i * 2500 + 5, 500, "Morsure", False, True) for i in range(12)]
        self.assertEqual(classify_triggered(log + pets), frozenset({200}))

    def test_the_power_cost_is_read_in_every_shape_the_file_uses(self):
        """"0", a whole number, and "3|1500" for a player with two resources."""
        for cost, paid in (("0", False), ("2500", True), ("3|1500", True), ("0|0", False),
                           ("nil", False)):
            block = advanced_block(19)
            block[-6] = cost
            self.assertEqual(Advanced(block).paid_power, paid, cost)

    def test_every_cast_is_kept_in_order_and_in_its_pull(self):
        from logswow.castorder import split_by_pull

        hit = ('SPELL_DAMAGE,%s,%s,1,"Frappe",0x1,500,500,-1,1,0,0,0,nil,nil,nil,ST'
               % (self.PLAYER, self.MOB))
        segments = self._run([
            (0, 'CHALLENGE_MODE_START,"Donjon",2000,500,7,[9]'),
            (500, 'SPELL_SUMMON,%s,%s,777,"Invocation",0x1' % (self.PLAYER, self.PET)),
            (1000, self._cast(10, "Ouverture", "2500")),      # the opener, before any hit
            (3000, hit),
            (4000, self._cast(11, "Frappe", "2500")),
            (4000, self._cast(12, "Morsure", source=self.PET)),
            (20000, self._cast(13, "Buff du couloir")),       # between two pulls
            (40000, hit),
            (41000, self._cast(11, "Frappe", "2500")),
            (60000, "CHALLENGE_MODE_END,2000,1,7,60000"),
        ])
        analysis = segments[0].analysis
        player = analysis.players[self.GUID]
        self.assertEqual(len(player.cast_log), player.casts)
        self.assertEqual([entry[1] for entry in player.cast_log], [10, 11, 12, 13, 11])
        self.assertEqual([entry[4] for entry in player.cast_log],
                         [False, False, True, False, False])
        groups = split_by_pull(player.cast_log, analysis.blocks, analysis.pull_gap_ms)
        self.assertEqual([[entry[1] for entry in casts] for _block, casts in groups],
                         [[10, 11, 12], [11], [13]])
        self.assertIsNone(groups[-1][0])

    def test_the_page_shows_the_order_and_filters_it_without_a_script(self):
        import tempfile

        payloads = [(0, 'ENCOUNTER_START,1,"Golem",16,5,2000')]
        for i in range(10):
            payloads.append((i * 2500, self._cast(100, "Frappe", "2500")))
            payloads.append((i * 2500 + 5, self._cast(200, "Eclat")))
        payloads.append((30000, 'ENCOUNTER_END,1,"Golem",16,5,1,30000'))
        segments = self._run(payloads)
        log, _fixture = run_fixture()
        for links in ("fr", "off"):
            with tempfile.TemporaryDirectory() as directory:
                target = os.path.join(directory, "r.html")
                ReportWriter(log, segments, target, wowhead=links).write()
                with open(target, encoding="utf-8") as handle:
                    page = handle.read()
            self.assertIn("Ordre des sorts, pull par pull", page)
            self.assertNotIn("<script", page)
            self.assertIn(".h200:checked~.pulls .c200{display:none}", page)
            # The triggered one is hidden when the page opens, the other not.
            self.assertRegex(page, r"<input type=checkbox class='hf h200' id='o\d+-200' checked>")
            self.assertRegex(page, r"<input type=checkbox class='hf h100' id='o\d+-100'>")
            self.assertIn("Probablement déclenchés automatiquement", page)
            if links == "fr":
                self.assertIn("href='https://www.wowhead.com/fr/spell=100' title='0:00 Frappe'>Fr<",
                              page)
            else:
                self.assertNotIn("wowhead.com", page)

    def test_the_order_can_be_left_out_for_a_lighter_page(self):
        import tempfile

        from logswow.cli import main

        with tempfile.TemporaryDirectory() as directory:
            full, light = (os.path.join(directory, name) for name in ("a.html", "b.html"))
            self.assertEqual(main(["report", FIXTURE, "-q", "-o", full]), 0)
            self.assertEqual(main(["report", FIXTURE, "-q", "-o", light, "--sans-sequence"]), 0)
            with open(full, encoding="utf-8") as a, open(light, encoding="utf-8") as b:
                self.assertIn("Ordre des sorts", a.read())
                self.assertNotIn("Ordre des sorts", b.read())

    def test_a_damaged_encounter_name_does_not_stop_the_report(self):
        """Found by fuzzing while this section was written: a bracket where
        the encounter's name should be made the name a list, and every
        command stopped on it. The fight is kept, under a plain name."""
        import tempfile

        segments = self._run([
            (0, 'ENCOUNTER_START,1,[Golem,x],16,5,2000'),
            (1000, self._cast(100, "Frappe", "2500")),
            (2000, 'ENCOUNTER_END,1,[Golem,x],16,5,1,2000'),
            (3000, 'CHALLENGE_MODE_START,[Donjon],2000,500,7,[9]'),
            (4000, "CHALLENGE_MODE_END,2000,1,7,1000"),
        ])
        self.assertEqual([s.name for s in segments], ["Rencontre", "Donjon"])
        log, _fixture = run_fixture()
        with tempfile.TemporaryDirectory() as directory:
            target = os.path.join(directory, "r.html")
            ReportWriter(log, segments, target).write()
            self.assertTrue(os.path.getsize(target) > 0)

    def test_a_line_whose_event_name_is_not_a_name_is_one_problem(self):
        """Also found by fuzzing: a damaged line starting with a bracket
        gave an event "name" that was a list, and the layout vote stopped
        the whole read on it."""
        import tempfile

        with tempfile.TemporaryDirectory() as directory:
            path = os.path.join(directory, "journal.txt")
            with open(FIXTURE, encoding="utf-8") as source:
                lines = source.read().splitlines()
            lines.insert(3, "9/18/2026 23:59:00.500  [abime],1,2")
            with open(path, "w", encoding="utf-8") as handle:
                handle.write("\n".join(lines) + "\n")
            log = LogFile(path)
            segments = Splitter(analysis_factory=SegmentAnalysis)
            for event in log.events():
                segments.feed(event)
            self.assertEqual(len(segments.finish()), 3)
            self.assertEqual(log.problems.by_reason.get("nom d'evenement illisible"), 1)

    def test_a_spell_name_becomes_two_letters(self):
        from logswow.report_casts import abbreviate, spell_colour

        self.assertEqual(abbreviate("Estropier"), "Es")
        self.assertEqual(abbreviate("Lame du Vide"), "Lv")
        self.assertEqual(abbreviate("Coup de pied du soleil levant"), "Cp")
        self.assertEqual(abbreviate("Éclair de givre"), "Ég")
        self.assertEqual(abbreviate(""), "?")
        self.assertEqual(spell_colour(100), spell_colour(100))


class TestWhatSixteenLogsFound(unittest.TestCase):
    """Sixteen real logs from the owner, 32.7 million lines (2026-09-27)."""

    ALLY = 'Player-9-00000001,"Ardoise-Dalaran-EU",0x512,0x0'
    ALLY_GUID = "Player-9-00000001"
    EVOKER = 'Player-9-00000002,"Braise-Dalaran-EU",0x512,0x0'
    EVOKER_GUID = "Player-9-00000002"
    MOB = 'Creature-0-9-2-1-70000-0000000001,"Golem",0xa48,0x0'
    NOBODY = '0000000000000000,nil,0x80000000,0x80000000'

    def _adv(self, info):
        return ",".join(advanced_block(19, info=info))

    def _run(self, timed_payloads):
        splitter = Splitter(analysis_factory=SegmentAnalysis)
        for index, (ms, payload) in enumerate(timed_payloads):
            _ts, fields = split_line("9/18/2026 20:15:31.123-4  " + payload)
            event = build_event(ms, fields, index + 1)
            self.assertIsNone(event.mismatch, payload[:40])
            splitter.feed(event)
        return splitter.finish()

    def _lines(self):
        mob = "Creature-0-9-2-1-70000-0000000001"
        return [
            (0, 'SPELL_DAMAGE,%s,%s,100,"Frappe",0x1,%s,10000,9000,-1,1,0,0,0,nil,nil,nil,ST'
             % (self.ALLY, self.MOB, self._adv(mob))),
            # Ebon Might's share of that same hit, credited to the Evoker.
            (0, 'SPELL_DAMAGE_SUPPORT,%s,%s,395152,"Puissance d\'ebene",0xc,%s,'
             '800,700,-1,12,0,0,0,nil,nil,nil,%s'
             % (self.ALLY, self.MOB, self._adv(mob), self.EVOKER_GUID)),
            (100, 'SWING_DAMAGE,%s,%s,%s,2000,1800,-1,1,0,0,0,nil,nil,nil'
             % (self.ALLY, self.MOB, self._adv(self.ALLY_GUID))),
            (100, 'SWING_DAMAGE_LANDED,%s,%s,%s,2000,1800,-1,1,0,0,0,nil,nil,nil'
             % (self.ALLY, self.MOB, self._adv(mob))),
            # A melee support line carries a spell prefix: 42 fields, the
            # width that was 9,772 read problems on one real log.
            (100, 'SWING_DAMAGE_LANDED_SUPPORT,%s,%s,395152,"Puissance d\'ebene",0xc,%s,'
             '150,140,-1,1,0,0,0,nil,nil,nil,%s'
             % (self.ALLY, self.MOB, self._adv(mob), self.EVOKER_GUID)),
            (200, 'SPELL_HEAL,%s,%s,200,"Soin",0x2,%s,3000,2900,0,0,nil'
             % (self.ALLY, self.ALLY, self._adv(self.ALLY_GUID))),
            (200, 'SPELL_HEAL_SUPPORT,%s,%s,410089,"Prescience",0x40,%s,200,190,0,0,nil,%s'
             % (self.ALLY, self.ALLY, self._adv(self.ALLY_GUID), self.EVOKER_GUID)),
            (300, 'SPELL_ABSORBED_SUPPORT,%s,%s,300,"Coup",0x1,%s,413984,"Sables changeants",'
             '0x40,1947,2866,nil,%s' % (self.MOB, self.ALLY, self.ALLY, self.EVOKER_GUID)),
            # An Evoker letting go of an empowered spell, 1 to 47 per log.
            (400, 'SPELL_EMPOWER_INTERRUPT,%s,%s,357208,"Souffle de feu",0x4,1'
             % (self.EVOKER, self.NOBODY)),
            (500, 'SPELL_CAST_SUCCESS,%s,%s,361469,"Frappe vivante",0x4,%s'
             % (self.EVOKER, self.MOB, self._adv(self.EVOKER_GUID))),
        ]

    def test_a_support_line_is_never_counted_twice(self):
        """Every _SUPPORT line repeats part or all of a hit its source
        already dealt. Read as damage, it gave supported players up to
        14.3% of damage they never did, on the owner's own raid night."""
        analysis = self._run(self._lines())[0].analysis
        ally = analysis.players[self.ALLY_GUID]
        self.assertEqual(ally.damage_done, 12000)
        self.assertEqual(analysis.total_damage, 12000)
        self.assertEqual(ally.healing_done, 3000)
        self.assertNotIn((395152, "Puissance d'ebene"), ally.damage_by_ability)
        self.assertEqual(analysis.support_seen, 3)
        self.assertEqual(analysis.landed_seen, 1)

    def test_the_evoker_is_credited_apart(self):
        analysis = self._run(self._lines())[0].analysis
        evoker = analysis.players[self.EVOKER_GUID]
        self.assertEqual(evoker.support_damage, 950)
        self.assertEqual(evoker.support_healing, 200)
        self.assertEqual(evoker.damage_done, 0)
        self.assertEqual(evoker.label, "Braise")
        self.assertEqual(sum(a.total for a in evoker.support_by_ability.values()), 950)

    def test_letting_go_of_an_empowered_spell_is_not_an_interrupt(self):
        """SPELL_EMPOWER_INTERRUPT is SPELL + _EMPOWER_INTERRUPT. Read as
        SPELL_EMPOWER + _INTERRUPT, the Evoker 'interrupted' the null GUID."""
        self.assertEqual(decompose("SPELL_EMPOWER_INTERRUPT")[:3],
                         ("SPELL", 3, "_EMPOWER_INTERRUPT"))
        analysis = self._run(self._lines())[0].analysis
        self.assertEqual(analysis.players[self.EVOKER_GUID].interrupts, 0)

    def test_the_absorbed_support_line_is_a_known_event(self):
        event = event_from(self._lines()[7][1])
        self.assertIsNone(event.mismatch)
        self.assertEqual(event.subevent, "SPELL_ABSORBED_SUPPORT")

    def test_the_page_says_the_credit_is_already_counted(self):
        import tempfile

        segments = self._run(self._lines())
        log, _fixture_segments = run_fixture()
        with tempfile.TemporaryDirectory() as directory:
            target = os.path.join(directory, "rapport.html")
            ReportWriter(log, segments, target).write()
            with open(target, encoding="utf-8") as handle:
                page = handle.read()
        self.assertIn("Soutien credite par le jeu", page)
        self.assertIn("deja comptes", page)


class TestTriggeredAcrossAllClasses(unittest.TestCase):
    """The triggered-spell rule, recalibrated on sixteen logs (2026-09-27)."""

    @staticmethod
    def _classify(log):
        from logswow.castorder import classify_triggered

        return classify_triggered(log)

    def test_a_free_spell_beside_a_free_spell_is_not_called_triggered(self):
        """Mind Flay: Insanity lands with a Shadowy Apparition 417 times of
        417, and neither is ever paid: the rule used to hide the pressed
        one. A trigger now needs a spell that is paid for at its side."""
        log = []
        for i in range(12):
            log.append((i * 5400, 391403, "Fouet mental : insanite", False, False))
            log.append((i * 5400 + 3, 341263, "Apparition tenebreuse", False, False))
            log.append((i * 5400 + 1600, 341263, "Apparition tenebreuse", False, False))
            log.append((i * 5400 + 3000, 8092, "Attaque mentale", True, False))
        self.assertNotIn(391403, self._classify(log))

    def test_a_press_made_free_by_a_proc_still_sets_off_its_trigger(self):
        """Chi Burst rides on Spinning Crane Kick, which Dance of Chi-Ji
        makes free: the button is a paid spell even on its free casts."""
        log = []
        for i in range(12):
            log.append((i * 1500, 101546, "Coup tournoyant", i % 3 == 0, False))
            log.append((i * 1500 + 4, 393056, "Nova de chi", False, False))
        self.assertEqual(self._classify(log), frozenset({393056}))

    def test_one_press_written_twice_under_one_name_shows_once(self):
        """Fracture writes two unpaid casts per press, 3,061 times in a row.
        The rule used to hide both; now it hides exactly one."""
        log = []
        for i in range(20):
            log.append((i * 3700, 263642, "Fracture", False, False))
            log.append((i * 3700 + 1, 225919, "Fracture", False, False))
        log.append((90000, 263642, "Fracture", False, False))
        self.assertEqual(self._classify(log), frozenset({225919}))

    def test_the_paid_copy_of_a_twin_is_the_one_kept(self):
        log = []
        for i in range(12):
            log.append((i * 2100, 1329, "Estropier", True, False))
            log.append((i * 2100 + 2, 27576, "Estropier", False, False))
        self.assertEqual(self._classify(log), frozenset({27576}))

    def test_faster_than_any_button_is_not_pressed(self):
        """Soul fragments: 48,517 casts at a median of 0.2 s, alone."""
        log = [(i * 200, 1223412, "Fragment d'ame", False, False) for i in range(40)]
        log += [(i * 1500 + 90, 100, "Frappe", True, False) for i in range(6)]
        self.assertEqual(self._classify(log), frozenset({1223412}))

    def test_a_spell_written_twice_at_once_is_not_faster_than_a_button(self):
        """Power Infusion on a friend, and on oneself by a talent, is two
        lines at the same instant: 0.0 s between casts. The 'faster than
        any button' test counts moments, so a two-minute cooldown macro'd
        with a free trinket stays visible."""
        log = []
        for i in range(9):
            ts = i * 120000
            log.append((ts, 10060, "Infusion de puissance", False, False))
            log.append((ts, 10060, "Infusion de puissance", False, False))
            log.append((ts + 1, 999, "Bijou", False, False))
        self.assertNotIn(10060, self._classify(log))

    def test_two_summons_at_one_instant_keep_the_gap_it_was_calibrated_on(self):
        """Dire Beast brings two beasts at once, about every 45 s, beside a
        paid Kill Command. Between moments that is a macro's pace; between
        casts, the 0.0 s pairs keep it a proc, as it was calibrated."""
        log = []
        for i in range(10):
            ts = i * 45000
            log.append((ts, 34026, "Ordre de tuer", True, False))
            log.append((ts + 2, 1308188, "Bete feroce", False, False))
            log.append((ts + 3, 1308188, "Bete feroce", False, False))
        self.assertEqual(self._classify(log), frozenset({1308188}))


class TestWhereOnAnotherDisk(unittest.TestCase):
    """The owner's game is on a second disk: /mnt/<disk>/World of Warcraft."""

    def test_a_game_on_a_mounted_disk_is_found(self):
        import tempfile
        from logswow.cli import default_log_locations

        if os.name == "nt":
            self.skipTest("mount points are a Linux and macOS matter")
        with tempfile.TemporaryDirectory() as mnt:
            direct = os.path.join(mnt, "Jeux_SSD", "World of Warcraft", "_retail_", "Logs")
            wine = os.path.join(mnt, "Autre", "Games", "battlenet", "drive_c",
                                "Program Files (x86)", "World of Warcraft", "_retail_", "Logs")
            for path in (direct, wine):
                os.makedirs(path)
            found = default_log_locations(mount_roots=(os.path.join(mnt, "*"),))
        self.assertIn(direct, found)
        self.assertIn(wine, found)


if __name__ == "__main__":
    unittest.main(verbosity=2)
