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

    def test_midnight_rolls_forward_instead_of_backwards(self):
        reader = TimestampReader(2026)
        before = reader.read("9/18 23:59:59.500")
        after = reader.read("9/18 00:00:01.500")
        self.assertEqual(after - before, 2000)

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

    def test_two_pulls_found(self):
        self.assertEqual(len(self.segments), 2)
        self.assertEqual([s.kind for s in self.segments], ["encounter", "encounter"])

    def test_outcomes_are_read_from_the_end_marker(self):
        self.assertTrue(self.segments[0].success)
        self.assertFalse(self.segments[1].success)
        self.assertEqual(self.segments[0].outcome, "reussite")
        self.assertEqual(self.segments[1].outcome, "echec")

    def test_pull_crossing_midnight_has_a_positive_duration(self):
        self.assertGreater(self.segments[1].duration_ms, 0)

    def test_indices_are_contiguous_from_one(self):
        self.assertEqual([s.index for s in self.segments], [1, 2])

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
        tisane = self._player(self.first, "Tisane")
        self.assertEqual(tisane.healing_done, 25000 - 5000)
        self.assertEqual(tisane.overhealing, 5000)

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


class TestProblemsAreCountedNotSwallowed(unittest.TestCase):
    def test_the_fixtures_deliberate_bad_lines_are_reported(self):
        log, _segments = run_fixture()
        self.assertEqual(log.problems.unsplittable, 1)
        self.assertIn("EVENEMENT_INCONNU", str(log.problems.by_reason) + str(log.problems.samples))

    def test_a_broken_line_does_not_stop_the_read(self):
        log, segments = run_fixture()
        self.assertEqual(len(segments), 2)
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

    def test_french_agreement(self):
        self.assertEqual(plural(0, "mort"), "0 mort")
        self.assertEqual(plural(1, "joueur"), "1 joueur")
        self.assertEqual(plural(3, "joueur"), "3 joueurs")


if __name__ == "__main__":
    unittest.main(verbosity=2)
