# SPDX-License-Identifier: AGPL-3.0-or-later
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

import contextlib
import io
import itertools
import os
import re
import sys
import time
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
sys.path.insert(0, ROOT)
# Every test reads French, on any machine: "auto" would otherwise follow
# the machine's language, and the release runner's is English. The tests
# of other languages ask for theirs and put French back.
os.environ["LOGSWOW_LANGUE"] = "fr"

from logswow.analysis import SegmentAnalysis  # noqa: E402
from logswow.cli import main as cli_main  # noqa: E402
from logswow.events import Advanced, Layout, build_event, decompose  # noqa: E402
from logswow.parse import LogFile, detect_layout  # noqa: E402
from logswow.fmt import plural  # noqa: E402
from logswow.report import ReportWriter  # noqa: E402
from logswow.segment import Splitter, difficulty_name, key_base_score  # noqa: E402
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
        # What a healing-absorb debuff ate is not inside the amount, and is
        # healing done (see effective_healing): 1000 - 300 + 50.
        self.assertEqual(event.effective_healing, 750)
        self.assertTrue(event.is_critical)

    def test_documented_heal_reads_the_same(self):
        event = self._heal(DOCUMENTED, "1000,300,50,1")
        self.assertEqual(event.effective_healing, 750)
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
        self.assertEqual(self.segments[0].outcome, "réussite")
        self.assertEqual(self.segments[1].outcome, "échec")

    def test_pull_crossing_midnight_has_a_positive_duration(self):
        self.assertGreater(self.segments[1].duration_ms, 0)

    def test_indices_are_contiguous_from_one(self):
        self.assertEqual([s.index for s in self.segments], [1, 2, 3])

    def test_difficulty_is_named_or_numbered_never_guessed(self):
        self.assertEqual(difficulty_name(16), "Mythique")
        self.assertEqual(difficulty_name(999), "difficulté 999")

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

    def _keys(self, payloads):
        splitter = Splitter()
        for second, payload in payloads:
            _ts, fields = split_line("9/18/2026 20:%02d:%02d.123-4  %s"
                                     % (second // 60, second % 60, payload))
            splitter.feed(build_event(0, fields, 1))
        return [s for s in splitter.finish() if s.kind == "keystone"]

    def test_a_key_restarted_is_abandoned_not_late(self):
        """Two real logs restarted a dungeon: the client writes, before every
        CHALLENGE_MODE_START, an END with nothing in it -- success, level and
        time all zero. With a key still open, that is the end of a key nobody
        finished, and it was being counted as a key over time."""
        keys = self._keys([
            (0, "CHALLENGE_MODE_END,2813,0,0,0,0.000000,0.000000"),
            (1, 'CHALLENGE_MODE_START,"Allee",2813,587,14,[9,10,147]'),
            (500, "CHALLENGE_MODE_END,2813,0,0,0,0.000000,0.000000"),
            (501, 'CHALLENGE_MODE_START,"Allee",2813,587,12,[9,10,147]'),
            (2000, "CHALLENGE_MODE_END,2813,1,12,1724985,370.790710,3161.141357"),
            (2100, "CHALLENGE_MODE_END,1762,0,0,0,0.000000,0.000000"),
            (2101, 'CHALLENGE_MODE_START,"Repos",1762,249,12,[9,10,147]'),
            (2400, "CHALLENGE_MODE_END,1762,0,12,2900000,0.000000,0.000000"),
        ])
        self.assertEqual([(k.key_level, k.outcome) for k in keys],
                         [(14, "abandonnée"), (12, "dans les temps"), (12, "hors des temps")])
        self.assertEqual(keys[0].success, None)
        self.assertFalse(keys[0].truncated)
        self.assertFalse(keys[0].is_wipe)

    def test_a_completed_key_is_in_time_only_when_its_score_says_so(self):
        """The success flag says completed, not timed: the owner's late Val
        Aveuglant +13 (30:23) carries a 1 like their timed one (27:26). Only
        the score tells them apart: 383.2 against 319.5, where a timed +13
        scores at least 380 (2026-09-29)."""
        keys = self._keys([
            (1, 'CHALLENGE_MODE_START,"Le val",2859,584,13,[9,10,147]'),
            (100, "CHALLENGE_MODE_END,2859,1,13,1646811,383.191437,3170.274658"),
            (200, 'CHALLENGE_MODE_START,"Le val",2859,584,13,[9,10,147]'),
            (300, "CHALLENGE_MODE_END,2859,1,13,1823476,319.510925,3170.274658"),
            # An older log with no score: completed, and nothing more is said.
            (400, 'CHALLENGE_MODE_START,"Allee",2000,500,7,[9]'),
            (500, "CHALLENGE_MODE_END,2000,1,7,90000"),
        ])
        self.assertEqual([k.outcome for k in keys],
                         ["dans les temps", "hors des temps", "terminée"])
        self.assertEqual([k.completed for k in keys], [True, True, True])
        self.assertAlmostEqual(keys[1].score, 319.510925)

    def test_the_base_score_is_raider_io_s_table(self):
        """Raider.IO's published base score for every level from +2 to +30.
        The first rule, 15 x level + 185, was right from +12 up and asked
        15 to 30 points too many below: a timed +10 scoring 330 read late."""
        table = [155, 170, 200, 215, 230, 260, 275, 290, 320, 335, 365, 380,
                 395, 410, 425, 440, 455, 470, 485, 500, 515, 530, 545, 560,
                 575, 590, 605, 620, 635]
        self.assertEqual([key_base_score(level) for level in range(2, 31)], table)
        keys = self._keys([
            (1, 'CHALLENGE_MODE_START,"Allee",2813,587,10,[9,10,147]'),
            (100, "CHALLENGE_MODE_END,2813,1,10,1156000,330.000000,3000.000000"),
            (200, 'CHALLENGE_MODE_START,"Allee",2813,587,11,[9,10,147]'),
            (300, "CHALLENGE_MODE_END,2813,1,11,1156000,334.900000,3000.000000"),
        ])
        self.assertEqual([k.outcome for k in keys], ["dans les temps", "hors des temps"])

    def test_a_key_the_file_ends_in_is_cut_short_and_a_new_one_abandons_it(self):
        keys = self._keys([
            (1, 'CHALLENGE_MODE_START,"Allee",2813,587,14,[9]'),
            # A START with no empty END before it: the key is abandoned all the same.
            (300, 'CHALLENGE_MODE_START,"Repos",1762,249,12,[9]'),
        ])
        self.assertEqual([k.outcome for k in keys], ["abandonnée", "interrompu"])
        self.assertTrue(keys[1].truncated)


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
        # The 9,000 hit killed with 3,000 to spare: 6,000 of it was dealt.
        self.assertEqual(braise.damage_done, 6 * 5000 + (9000 - 3000) + 6 * 700)

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
        self.fail("capacité absente : %s / %s" % (player_name, spell_name))

    def test_an_ability_knows_its_hits_average_and_biggest(self):
        _player, ability = self._ability("Braise", "Frappe d'essai")
        self.assertEqual(ability.hits, 7)
        self.assertEqual(ability.average, ability.total / ability.hits)
        self.assertEqual(ability.biggest, 6000)     # 9,000 with 3,000 overkill
        self.assertEqual(ability.overkill, 3000)

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
        self.assertIn("ne sont comptés pour personne", page)
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
            if "<h3>Dégâts infligés</h3>" not in body:
                continue
            table = body.split("<h3>Dégâts infligés</h3>", 1)[1].split("</table>", 1)[0]
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
        self.assertIn("source non nommée par le journal", analysis.orphan_sources)

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
        self.assertIn("Courbe et échelle de droite", page)
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
        self.assertIn("Qui il a soigné", page)
        self.assertIn("Surguérison", page)
        self.assertIn("Dissipations", page)
        self.assertIn("Sorts ennemis coupés", page)
        self.assertIn("Ce que le groupe a empêché", page)

    def test_the_report_carries_the_group_and_the_enemies(self):
        import tempfile

        with tempfile.TemporaryDirectory() as directory:
            target = os.path.join(directory, "rapport.html")
            ReportWriter(self.log, self.segments, target).write()
            with open(target, encoding="utf-8") as handle:
                page = handle.read()
        self.assertIn("Composition du groupe", page)
        self.assertIn("Guerrier Protection", page)
        self.assertIn("Détail par ennemi", page)
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
        # The pull table's own heading; the physical/magic section has a
        # column of the same name, per pull too.
        heading = "<th>Ce qui a été engagé</th><th class=n>Dégâts</th>"
        self.assertIn(heading, page)
        self.assertEqual(page.count(heading), 1)

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
        self.assertIn("aucune unité ne porte le nom de la rencontre", self._page(segments))

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
        self.assertIn("boss &middot; échec", page)
        self.assertIn("boss &middot; réussite", page)
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
            self.assertIn("journal lui-même", said.getvalue())
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
        self.assertEqual([s.outcome for s in segments], ["sans combat", "échec"])
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
        for section in ("DISPOSITION MESURÉE DANS CE FICHIER", "bloc avancé         : 19",
                        "champ baseAmount    : présent", "points de vie incohérents   : 0",
                        "COMBATS DÉLIMITÉS : 3", "ÉVÉNEMENTS (",
                        "[SCHÉMA INCONNU] ", "PROBLÈMES DE LECTURE : 2"):
            self.assertIn(section, out)
        code, out, _err = self._main(["diagnose", FIXTURE, "--limit", "5"])
        self.assertEqual(code, 0)
        self.assertIn("ÉVÉNEMENTS (", out)

    def test_list_prints_one_line_per_fight(self):
        code, out, _err = self._main(["list", FIXTURE, "-q"])
        self.assertEqual(code, 0)
        lines = out.strip().splitlines()
        self.assertEqual(len(lines), 4)
        self.assertIn("réussite", lines[1])
        self.assertIn("échec", lines[2])
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
            self.assertTrue("secondes" in err or "supérieur à zéro" in err
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
            # The machine's own mounted disks are left out: on a player's
            # computer with the game on a second disk, `where` rightly
            # finds it, and this test is about the launchers only.
            with mock.patch.dict(os.environ, {"HOME": home}), \
                    mock.patch("logswow.cli._on_other_disks", return_value=[]):
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
        self.assertEqual([bool(entry[4]) for entry in player.cast_log],
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
        # One hit, so the player took part in the fight and gets a panel.
        payloads.append((26000, 'SPELL_DAMAGE,%s,%s,100,"Frappe",0x1,500,500,-1,1,0,0,0,'
                                'nil,nil,nil,ST' % (self.PLAYER, self.MOB)))
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
            self.assertEqual(log.problems.by_reason.get("nom d'événement illisible"), 1)

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

    def test_the_reattributed_column_moves_the_evokers_share_and_keeps_the_total(self):
        """What the file allows of an "aDPS" (0.10.0): Warcraft Logs' move of
        the *_SUPPORT share from the ally to the Evoker, beside the damage."""
        import tempfile
        from unittest import mock

        from logswow import fmt

        segments = self._run(self._lines())
        analysis = segments[0].analysis
        ally = analysis.players[self.ALLY_GUID]
        self.assertEqual(ally.support_received, 950)
        self.assertEqual(ally.damage_done, 12000)
        log, _fixture = run_fixture()
        with tempfile.TemporaryDirectory() as folder:
            target = os.path.join(folder, "r.html")
            with mock.patch.object(fmt, "compact", lambda value: "=%d" % value):
                ReportWriter(log, segments, target, wowhead="off", cast_order=False,
                             layout="longue").write()
            with open(target, encoding="utf-8") as handle:
                page = handle.read()
        self.assertIn("<th class=n>Réattribué</th>", page)
        # The ally keeps 12,000 and is reattributed 11,050; the Evoker, who
        # dealt nothing, gets a row and the 950.
        self.assertIn("<td class=n>=12000</td><td class=n>=11050</td>", page)
        self.assertIn("<td class=n>=0</td><td class=n>=950</td>", page)
        self.assertIn("Infusion de puissance", page)

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
        self.assertIn("Soutien crédité par le jeu", page)
        self.assertIn("déjà comptés", page)


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


class TestWindow(unittest.TestCase):
    """The window (2026-09-27): its logic without a screen, the widgets with one."""

    def test_logs_are_listed_newest_first_and_nothing_else(self):
        import tempfile
        from logswow import gui

        with tempfile.TemporaryDirectory() as folder:
            for name, age in (("WoWCombatLog-091826_203000.txt", 300),
                              ("WoWCombatLog-092026_203000.txt", 100),
                              ("notes.txt", 0), ("WoWCombatLog-092026_203000.html", 0)):
                path = os.path.join(folder, name)
                with open(path, "w") as handle:
                    handle.write("x" * 10)
                os.utime(path, (time.time() - age, time.time() - age))
            names = [os.path.basename(path) for path, _size, _mtime
                     in gui.recent_logs([folder, os.path.join(folder, "absent")])]
        self.assertEqual(names, ["WoWCombatLog-092026_203000.txt",
                                 "WoWCombatLog-091826_203000.txt"])

    def test_the_small_things_the_window_prints(self):
        from logswow import gui

        self.assertEqual(gui.file_size(709329406), "709,3 Mo")
        self.assertEqual(gui.file_size(9532819484), "9,5 Go")
        self.assertEqual(gui.file_size(12), "12 o")
        self.assertEqual(gui.read_share(0, 1000), 0.0)
        self.assertEqual(gui.read_share(500, 1000), 0.5)
        self.assertEqual(gui.read_share(10 ** 9, 1000), 0.99)   # never "done" early
        self.assertEqual(gui.read_share(5, 0), 0.0)

    def test_the_bar_follows_the_file_s_own_position(self):
        """The bar turned lines into bytes at 310 a line, an average of sixteen
        logs; it now reads how far into the file the read is (2026-09-29)."""
        import tempfile
        from unittest import mock
        from logswow import cli, parse

        with open(FIXTURE, "rb") as source:
            lines = source.read().splitlines(keepends=True)
        # Past the warm-up: its lines are all read before the first is used.
        ROUNDS = 200
        self.assertGreater(len(lines) * ROUNDS // 2, parse.WARMUP_LINES)
        with tempfile.TemporaryDirectory() as folder:
            path = os.path.join(folder, "WoWCombatLog-long.txt")
            with open(path, "wb") as copy:
                for _round in range(ROUNDS):
                    copy.writelines(lines)
            size = os.path.getsize(path)
            log = LogFile(path)
            offsets = [0]
            for line in lines * ROUNDS:
                offsets.append(offsets[-1] + len(line))
            seen = []
            for event in log.events():
                if log.line_count > len(lines) * ROUNDS // 2 and not seen:
                    seen.append((log.line_count, log.bytes_read))
            line_count, done = seen[0]
            # The text layer reads ahead by a chunk: a few kilobytes, never more.
            self.assertLessEqual(offsets[line_count], done)
            self.assertLess(done - offsets[line_count], 64 * 1024)
            self.assertLess(done, size)
            self.assertEqual(log.bytes_read, 0)           # the read is over
            # `_build` hands both counts to the window.
            calls = []
            with mock.patch.object(cli.time, "time", side_effect=itertools.count(0, 1.0)):
                cli._build(path, verbose=False,
                           progress=lambda lines, done: calls.append((lines, done)))
            self.assertTrue(calls)
            self.assertTrue(all(0 < done <= size for _lines, done in calls))

    def test_the_window_says_how_long_the_read_still_needs(self):
        from logswow import gui

        self.assertIsNone(gui.time_left(0.5, 1.0))           # the first second: too early
        self.assertIsNone(gui.time_left(0.01, 10.0))         # 1 % of the file: too early
        self.assertEqual(gui.time_left(0.5, 10.0), 10.0)
        self.assertEqual(gui.time_left(0.25, 12.0), 36.0)
        self.assertEqual(gui.left_text(0.2), "1 s")
        self.assertEqual(gui.left_text(8.4), "8 s")
        self.assertEqual(gui.left_text(23), "25 s")          # by 5 s past 20: no flicker
        self.assertEqual(gui.left_text(65), "1 min 05 s")
        self.assertEqual(gui.left_text(122), "2 min 00 s")

    def test_a_path_with_spaces_becomes_a_valid_address(self):
        """The owner's logs are under ".../World of Warcraft/_retail_/Logs"."""
        from logswow import gui

        path = os.path.join(os.sep, "mnt", "Jeux SSD", "World of Warcraft", "rapport é.html")
        address = gui.page_address(path)
        self.assertTrue(address.startswith("file:///"))
        self.assertNotIn(" ", address)
        self.assertIn("World%20of%20Warcraft", address)

    def test_the_fights_are_listed_with_their_outcome_in_french(self):
        from logswow import gui

        _log, segments = run_fixture()
        rows = gui.fight_rows(segments)
        self.assertEqual([row[0] for row in rows], [segment.index for segment in segments])
        self.assertTrue(all("reussite" != row[5] and "echec" != row[5] for row in rows))

    def test_the_report_goes_next_to_the_log_and_never_over_it(self):
        import tempfile
        from logswow import gui

        log, segments = run_fixture()
        with tempfile.TemporaryDirectory() as folder:
            log_path = os.path.join(folder, "WoWCombatLog-x.txt")
            with open(FIXTURE, "rb") as source, open(log_path, "wb") as copy:
                copy.write(source.read())
            self.assertEqual(gui.default_report_path(log_path, segments, segments),
                             os.path.join(folder, "WoWCombatLog-x.html"))
            if len(segments) > 1:
                self.assertTrue(gui.default_report_path(log_path, segments[1:2], segments)
                                .endswith("-combat-%d.html" % segments[1].index))
            out = os.path.join(folder, "WoWCombatLog-x.html")
            self.assertIsNone(gui.write_report(log, segments, out, log_path))
            self.assertIsNone(gui.write_report(log, segments, out, log_path))  # ours: redone
            self.assertIn("journal", gui.write_report(log, segments, log_path, log_path))
            other = os.path.join(folder, "autre.txt")
            with open(other, "w") as handle:
                handle.write("pas un rapport")
            self.assertIsNotNone(gui.write_report(log, segments, other, log_path))
            with open(other) as handle:
                self.assertEqual(handle.read(), "pas un rapport")

    def test_without_the_toolkit_the_window_says_what_to_install(self):
        from logswow import gui

        saved = sys.modules.get("tkinter")
        sys.modules["tkinter"] = None                    # makes `import tkinter` fail
        try:
            with contextlib.redirect_stderr(io.StringIO()) as err:
                code = gui.run()
        finally:
            if saved is None:
                del sys.modules["tkinter"]
            else:
                sys.modules["tkinter"] = saved
        self.assertEqual(code, 3)
        self.assertIn("sudo apt install python3-tk", err.getvalue())

    def test_the_commands_still_print_the_help_when_called_with_nothing(self):
        with contextlib.redirect_stdout(io.StringIO()) as out:
            self.assertEqual(cli_main([]), 0)
        self.assertIn("fenetre", out.getvalue())

    def test_the_window_opens_no_connection(self):
        import subprocess

        code = ("import sys, logswow.gui, logswow.cli; "
                "print(sorted(m for m in ('socket', 'ssl', 'http.client', 'urllib.request')"
                " if m in sys.modules))")
        result = subprocess.run([sys.executable, "-c", code], cwd=ROOT,
                                stdout=subprocess.PIPE, universal_newlines=True)
        self.assertEqual(result.stdout.strip(), "[]")

    def test_the_window_reads_a_log_and_writes_its_report(self):
        """Needs Tkinter and a display; skipped wherever either is missing."""
        import tempfile
        from logswow import gui

        try:
            import tkinter
            root = tkinter.Tk()
        except (ImportError, Exception) as error:        # noqa: BLE001 -- no screen here
            self.skipTest("pas de fenetre possible ici : %s" % str(error).splitlines()[0])
        opened = []
        saved = gui.open_in_browser
        gui.open_in_browser = opened.append
        try:
            with tempfile.TemporaryDirectory() as folder:
                log_path = os.path.join(folder, "WoWCombatLog-092726_200000.txt")
                with open(FIXTURE, "rb") as source, open(log_path, "wb") as copy:
                    copy.write(source.read())
                app = gui.App(root, locations=[folder])
                self.assertEqual(app.logs.get_children(), (log_path,))
                app.read_selected()
                deadline = time.time() + 30
                while app.segments is None and time.time() < deadline:
                    root.update()
                    time.sleep(0.02)
                self.assertTrue(app.segments)
                self.assertEqual(len(app.fights.selection()), len(app.segments))
                # A read that ended leaves the bar full, not empty (2026-09-29).
                self.assertEqual(app.bar["value"], 1000)
                app.write_selected()
                while app.busy and time.time() < deadline:
                    root.update()
                    time.sleep(0.02)
                self.assertEqual(opened, [os.path.join(folder, "WoWCombatLog-092726_200000.html")])
                self.assertEqual(app.bar["value"], 1000)
                # Halfway through a file, ten seconds in: ten seconds left.
                app._handle(("progress", 5000, 500, 1000, 10.0))
                self.assertEqual(app.bar["value"], 500)
                self.assertIn("encore environ 10 s", app.status.get())
                self.assertTrue(os.path.getsize(opened[0]) > 1000)
        finally:
            gui.open_in_browser = saved
            root.destroy()


class TestMeleeTaken(unittest.TestCase):
    """How the enemy's swings at a player ended, and from which side (2026-09-29).

    Asked for by the owner, a tank: parried, dodged, missed, blocked,
    critical -- all written by the file -- and hits from behind, which it
    does not write and which are placed from positions instead.
    """

    TANK = 'Player-9999-00000001,"Ardoise-Dalaran-EU",0x511,0x0'
    FRONT = 'Creature-0-9999-2222-1111-70000-0000000001,"Golem d\'essai",0xa48,0x0'
    BEHIND = 'Creature-0-9999-2222-1111-70000-0000000002,"Golem d\'essai",0xa48,0x0'
    STALE = 'Creature-0-9999-2222-1111-70000-0000000003,"Golem d\'essai",0xa48,0x0'

    @staticmethod
    def _at(info, x, y, facing="0.0000"):
        """An advanced block for `info` standing at (x, y), facing `facing`."""
        head = [info, "0000000000000000", "500", "1000", "10", "20", "30", "40", "0", "0"]
        return ",".join(head + ["1", "111", "222", "0", x, y, "2393", facing, "80"])

    def _hit(self, ms, mob, crit="nil"):
        guid = mob.split(",")[0]
        x = {"1": "2.00", "2": "-2.00", "3": "0.00"}[guid[-1]]
        y = "3.00" if guid.endswith("3") else "0.00"
        return [
            (ms, 'SWING_DAMAGE,%s,%s,%s,900,900,-1,1,0,0,0,%s,nil,nil'
             % (mob, self.TANK, self._at(guid, x, y), crit)),
            (ms, 'SWING_DAMAGE_LANDED,%s,%s,%s,900,900,-1,1,0,0,0,%s,nil,nil'
             % (mob, self.TANK, self._at("Player-9999-00000001", "0.00", "0.00"), crit)),
        ]

    def _analysis(self):
        lines = []
        # The third golem's only position is five seconds old when it hits.
        stale = self._at(self.STALE.split(",")[0], "0.00", "3.00")
        lines += [(0, 'SPELL_CAST_SUCCESS,%s,0000000000000000,nil,0x80000000,0x80000000,'
                      '1,"Coup",0x1,%s' % (self.STALE, stale))]
        for n in range(12):
            lines += self._hit(5000 + 100 * n, self.FRONT, "1" if n == 0 else "nil")
        for n in range(4):
            lines += self._hit(6500 + 100 * n, self.BEHIND)
        lines += [(7000, 'SWING_DAMAGE_LANDED,%s,%s,%s,900,900,-1,1,0,0,0,nil,nil,nil'
                   % (self.STALE, self.TANK, self._at("Player-9999-00000001", "0.00", "0.00")))]
        for n, kind in enumerate(["PARRY"] * 8 + ["DODGE"] * 2 + ["MISS", "ABSORB"]):
            lines.append((5050 + 100 * n, "SWING_MISSED,%s,%s,%s,nil"
                          % (self.FRONT, self.TANK, kind)))
        lines.sort(key=lambda line: line[0])
        splitter = Splitter(analysis_factory=SegmentAnalysis)
        for index, (ms, payload) in enumerate(lines):
            _ts, fields = split_line("9/18/2026 20:15:31.123-4  " + payload)
            splitter.feed(build_event(ms, fields, index + 1))
        return splitter.finish()[0].analysis

    def test_each_swing_is_counted_by_how_it_ended_and_where_it_came_from(self):
        taken = self._analysis().players["Player-9999-00000001"].melee_taken
        self.assertEqual(taken, {
            "hit": 17, "crit": 1, "front": 12, "behind": 4, "unplaced": 1,
            "PARRY": 8, "DODGE": 2, "MISS": 1, "ABSORB": 1, "avoided_front": 10})

    def test_the_panel_says_it_is_an_estimate_and_checks_it(self):
        from logswow.report import ReportWriter

        taken = self._analysis().players["Player-9999-00000001"].melee_taken
        html = ReportWriter._melee_taken(taken)
        self.assertIn("Paré", html)
        self.assertIn("dont critiques", html)
        self.assertIn("venaient de derrière", html)
        self.assertIn("Estimation fiable, mais pas une donnée écrite, et limitée à la mêlée", html)
        # Every placed parry and dodge in front: the check says so.
        self.assertIn("et 100\u202f% des 10 parades", html)
        # A critical hit is a share of the hits, not of every swing: 1 of 17.
        self.assertIn("dont critiques</td><td class=n>1</td><td class=n>6\u202f%", html)
        # Too few swings for percentages to mean anything: no table at all.
        self.assertEqual(ReportWriter._melee_taken({"hit": 3, "PARRY": 2}), "")


class TestPhysicalOrMagic(unittest.TestCase):
    """Damage by school, taken and dealt, per run and per pull (2026-09-27)."""

    TANK = 'Player-9999-00000001,"Ardoise-Dalaran-EU",0x511,0x0'
    MOB = 'Creature-0-9999-2222-1111-70000-0000111111,"Golem d\'essai",0xa48,0x0'

    def _adv(self, info):
        return ",".join(advanced_block(19, info=info))

    def test_the_school_is_read_from_the_line(self):
        swing = event_from('SWING_DAMAGE,%s,%s,%s,900,900,-1,1,0,0,0,nil,nil,nil'
                           % (self.MOB, self.TANK, self._adv("Creature-0-1")))
        spell = event_from('SPELL_DAMAGE,%s,%s,444,"Balayage",0x20,%s,3000,2900,-1,48,0,0,0,'
                           'nil,nil,nil,AOE' % (self.MOB, self.TANK, self._adv("Player-9999-1")))
        self.assertEqual((swing.damage_school, spell.damage_school), (1, 48))
        old = event_from('SPELL_DAMAGE,%s,%s,444,"Balayage",0x20,3000,-1,32,0,0,0,nil,nil,nil'
                         % (self.MOB, self.TANK), DOCUMENTED)
        self.assertEqual(old.damage_school, 32)

    def test_schools_are_physical_magic_or_both(self):
        from logswow import schools

        self.assertEqual([schools.kind(m) for m in (1, 32, 106, 33, 127, 0, 999)],
                         ["physique", "magique", "magique", "mixte", "mixte", "", ""])
        self.assertEqual(schools.name(36), "Feu + Ombre")
        self.assertEqual(schools.name(0), "école inconnue")

    def test_the_shares_always_add_up_to_a_hundred(self):
        from logswow.report_schools import shares

        self.assertEqual(shares({"a": 1, "b": 1, "c": 1}), {"a": 34, "b": 33, "c": 33})
        self.assertEqual(sum(shares({"a": 2, "b": 997, "c": 1}).values()), 100)
        self.assertEqual(shares({"a": 0}), {"a": 0})
        # Only a damaged line writes a negative amount; fuzzing found one.
        self.assertEqual(shares({"a": -5, "b": 0}), {"a": 0, "b": 0})
        self.assertEqual(shares({"a": -5, "b": 10}), {"a": 0, "b": 100})

    def test_a_fall_is_named_a_fall_not_the_victims_guid(self):
        """ENVIRONMENTAL_DAMAGE writes its advanced block before the type,
        65 lines of 65 in two real logs. Read in the usual order, the page
        named what hit a player after that player's own GUID."""
        line = ('ENVIRONMENTAL_DAMAGE,0000000000000000,nil,0x80000000,0x80000000,%s,%s,'
                'Falling,52487,52487,0,1,0,0,0,nil,nil,nil'
                % (self.TANK, self._adv("Player-9999-00000001")))
        event = event_from(line)
        self.assertIsNone(event.mismatch)
        self.assertEqual(event.spell_name, "Falling")
        self.assertEqual((event.amount, event.damage_school), (52487, 1))
        self.assertEqual(event.advanced.info_guid, "Player-9999-00000001")
        bare = event_from('ENVIRONMENTAL_DAMAGE,0000000000000000,nil,0x80000000,0x80000000,%s,'
                          'Lava,8000,-1,4,0,0,0,nil,nil,nil' % self.TANK, DOCUMENTED)
        self.assertEqual((bare.spell_name, bare.amount, bare.damage_school), ("Lava", 8000, 4))

    def test_a_run_and_its_pulls_are_split_by_school(self):
        splitter = Splitter(analysis_factory=SegmentAnalysis)
        lines = [
            (0, 'SWING_DAMAGE,%s,%s,%s,1000,1000,-1,1,0,0,0,nil,nil,nil'
             % (self.MOB, self.TANK, self._adv("Creature-0-1"))),
            (500, 'SPELL_DAMAGE,%s,%s,444,"Balayage",0x20,%s,3000,3000,-1,32,0,0,0,nil,nil,nil,'
             'AOE' % (self.MOB, self.TANK, self._adv("Player-9999-00000001"))),
            (900, 'SPELL_DAMAGE,%s,%s,222,"Frappe",0x1,%s,4000,4000,-1,1,0,0,0,nil,nil,nil,ST'
             % (self.TANK, self.MOB, self._adv("Creature-0-9999-2222-1111-70000-0000111111"))),
        ]
        for index, (ms, payload) in enumerate(lines):
            _ts, fields = split_line("9/18/2026 20:15:31.123-4  " + payload)
            splitter.feed(build_event(ms, fields, index + 1))
        analysis = splitter.finish()[0].analysis
        self.assertEqual(analysis.taken_by_school, {1: 1000, 32: 3000})
        self.assertEqual(analysis.done_by_school, {1: 4000})
        block = analysis.blocks[0]
        self.assertEqual(sum(block.taken_by_school.values()), block.damage_taken)

    def test_the_page_says_it_in_percentages(self):
        import tempfile

        log, segments = run_fixture()
        with tempfile.TemporaryDirectory() as directory:
            target = os.path.join(directory, "rapport.html")
            ReportWriter(log, segments, target).write()
            with open(target, encoding="utf-8") as handle:
                page = handle.read()
        self.assertIn("Physique ou magique", page)
        self.assertIn("Subis par école", page)
        self.assertRegex(page, r"\d+ %")


class TestOwnerFeedback(unittest.TestCase):
    """What the owner found reading their own reports (2026-09-28)."""

    A = 'Player-9999-00000001,"Ardoise-Dalaran-EU",0x512,0x0'
    B = 'Player-9999-00000002,"Tisane-Dalaran-EU",0x512,0x0'
    C = 'Player-9999-00000003,"Braise-Dalaran-EU",0x512,0x0'
    MOB = 'Creature-0-9999-2222-1111-70000-0000111111,"Golem",0xa48,0x0'

    @staticmethod
    def _echo(n):
        return 'Creature-0-9999-2222-1111-247301-00000000%02d,"Echo",0xa28,0x0' % n

    def _run(self, timed_payloads):
        splitter = Splitter(analysis_factory=SegmentAnalysis)
        for index, (ms, payload) in enumerate(timed_payloads):
            _ts, fields = split_line("9/18/2026 20:15:31.123-4  " + payload)
            splitter.feed(build_event(ms, fields, index + 1))
        return splitter.finish()

    def _hit(self, ms, source, dest, amount=1000):
        return (ms, 'SPELL_DAMAGE,%s,%s,100,"Frappe",0x1,%d,%d,-1,1,0,0,0,nil,nil,nil,ST'
                % (source, dest, amount, amount))

    def _summon(self, ms, player, unit, spell=1242953, name="Echo de Nalorakk"):
        return (ms, 'SPELL_SUMMON,%s,%s,%d,"%s",0x20' % (player, unit, spell, name))

    def _echo_fight(self):
        lines = [(0, 'ENCOUNTER_START,1,"Nalorakk",8,5,2000')]
        for i, player in enumerate((self.A, self.B, self.C)):
            lines.append(self._hit(10 + i, player, self.MOB))
        for wave in range(2):
            for i, player in enumerate((self.A, self.B, self.C)):
                lines.append(self._summon(1000 + wave * 5000, player, self._echo(wave * 3 + i)))
            for i in range(3):
                lines.append((1100 + wave * 5000,
                              'SPELL_CAST_SUCCESS,%s,0000000000000000,nil,0x80000000,0x80000000,'
                              '1242976,"Mutilation des echos",0x1' % self._echo(wave * 3 + i)))
        lines.append(self._hit(1200, self._echo(0), self.A, 5000))
        lines.append(self._hit(7000, self.A, self.MOB))
        lines.append((8000, 'ENCOUNTER_END,1,"Nalorakk",8,5,1,8000'))
        return self._run(lines)[0].analysis

    def test_an_encounter_that_summons_through_players_owns_its_units(self):
        """Echo de Nalorakk came to three players in the same millisecond,
        24 times of 24; its casts were in a player's sequence."""
        analysis = self._echo_fight()
        self.assertEqual(analysis.disowned_units, 6)
        for player in analysis.players.values():
            self.assertFalse([e for e in player.cast_log if "echos" in e[2]])
            self.assertEqual(player.pet_casts, 0)
            self.assertEqual(player.casts, len(player.cast_log))
        echo = analysis.enemies["Echo"]
        self.assertEqual(echo.casts, 6)
        self.assertEqual(echo.damage_done, 5000)          # its hit is the enemy's
        self.assertEqual(analysis.players["Player-9999-00000001"].damage_taken, 5000)

    def test_a_players_own_summons_stay_theirs(self):
        """Two warlocks' imps met by chance at most 1.4% of the time."""
        lines = [(0, 'ENCOUNTER_START,1,"Golem",8,5,2000')]
        for i in range(10):
            imp = 'Creature-0-9999-2222-1111-55659-00000001%02d,"Diablotin",0xa28,0x0' % i
            player = self.A if i % 2 else self.B
            ms = 100 + i * 700 + (0 if i != 3 else -690)     # one pair lands together
            lines.append(self._summon(ms, player, imp, 104317, "Diablotin sauvage"))
            lines.append(self._hit(ms + 50, imp, self.MOB))
        lines.append((9000, 'ENCOUNTER_END,1,"Golem",8,5,1,9000'))
        analysis = self._run(lines)[0].analysis
        self.assertEqual(analysis.disowned_units, 0)
        self.assertEqual(analysis.total_damage, 10000)

    def test_a_player_who_only_cast_a_buff_is_not_in_the_group(self):
        """Two players joining for the next key cast a buff in the last
        seconds of a failed +14: seven listed in a five-player dungeon."""
        lines = [(0, 'CHALLENGE_MODE_START,"Allee",2000,500,14,[9]'),
                 self._hit(100, self.A, self.MOB),
                 (200, 'SPELL_CAST_SUCCESS,%s,%s,1459,"Intelligence",0x40' % (self.B, self.B)),
                 (300, 'CHALLENGE_MODE_END,2000,0,14,300')]
        analysis = self._run(lines)[0].analysis
        self.assertEqual([p.short_name for p in analysis.participants()], ["Ardoise"])
        self.assertEqual([p.short_name for p in analysis.bystanders()], ["Tisane"])
        self.assertEqual([name for _label, players in analysis.composition()
                          for name in (p.short_name for p in players)], ["Ardoise"])

    def test_no_spell_is_cut_from_a_table_without_a_word(self):
        """Mutilate, split in two rows, fell under a hard cut of sixteen."""
        import tempfile

        lines = [(0, 'ENCOUNTER_START,1,"Golem",8,5,2000')]
        for spell in range(20):
            lines.append((10 + spell, 'SPELL_DAMAGE,%s,%s,%d,"Sort %d",0x1,%d,%d,-1,1,0,0,0,'
                          'nil,nil,nil,ST' % (self.A, self.MOB, 500 + spell, spell,
                                              10000 - spell, 10000 - spell)))
        lines.append((100, 'ENCOUNTER_END,1,"Golem",8,5,1,100'))
        segments = self._run(lines)
        log, _fixture = run_fixture()
        with tempfile.TemporaryDirectory() as directory:
            target = os.path.join(directory, "r.html")
            ReportWriter(log, segments, target, wowhead="off", cast_order=False).write()
            with open(target, encoding="utf-8") as handle:
                page = handle.read()
        self.assertIn("4 sorts de plus", page)
        self.assertIn("Sort 19", page)

    def test_the_counters_see_the_bosses_inside_a_key_and_tell_failures_apart(self):
        """A key chosen alone showed '0 pulls de boss'; a depleted key with a
        boss wipe inside read as one dungeon failed twice."""
        import tempfile

        lines = [(0, 'CHALLENGE_MODE_START,"Allee",2000,500,14,[9]')]
        for n, (start, success) in enumerate(((1000, 0), (5000, 1), (9000, 1))):
            lines += [(start, 'ENCOUNTER_START,%d,"Boss %d",8,5,2000' % (n, n)),
                      self._hit(start + 10, self.A, self.MOB),
                      (start + 900, 'ENCOUNTER_END,%d,"Boss %d",8,5,%d,900' % (n, n, success))]
        lines.append((12000, 'CHALLENGE_MODE_END,2000,0,14,12000'))
        segments = self._run(lines)
        key = [segment for segment in segments if segment.kind == "keystone"]
        log, _fixture = run_fixture()
        with tempfile.TemporaryDirectory() as directory:
            target = os.path.join(directory, "r.html")
            for chosen, bosses in ((key, "3"), (segments, "3")):
                ReportWriter(log, chosen, target, wowhead="off", cast_order=False).write()
                with open(target, encoding="utf-8") as handle:
                    page = handle.read()
                self.assertIn("<b>%s</b><span>Pulls de boss" % bosses, page)
                self.assertIn("<b>1</b><span>Wipes de boss", page)
                self.assertIn("<b>1</b><span>Clés hors des temps", page)
                self.assertIn("<b>0</b><span>Clés non terminées", page)


class TestWhoOpenedThePull(unittest.TestCase):
    """The first act of each pull, and the three-second gap (2026-09-29)."""

    A = 'Player-9999-00000001,"Ardoise-Dalaran-EU",0x512,0x0'
    B = 'Player-9999-00000002,"Tisane-Dalaran-EU",0x512,0x0'
    C = 'Player-9999-00000003,"Braise-Dalaran-EU",0x512,0x0'
    PET = 'Pet-0-9999-2222-1111-165189-0000000001,"Loup",0x1112,0x0'

    @staticmethod
    def _mob(n):
        return 'Creature-0-9999-2222-1111-70000-00001111%02d,"Golem",0xa48,0x0' % n

    def _hit(self, ms, source, dest):
        return (ms, 'SPELL_DAMAGE,%s,%s,100,"Frappe",0x1,1000,1000,-1,1,0,0,0,nil,nil,nil,ST'
                % (source, dest))

    def _key(self):
        lines = [
            (0, 'CHALLENGE_MODE_START,"Allee",2000,500,14,[9]'),
            (500, 'SPELL_SUMMON,%s,%s,883,"Appel du familier",0x1' % (self.A, self.PET)),
            self._hit(1000, self.A, self._mob(1)),
            self._hit(2000, self._mob(1), self.A),
            # The last pack's debuff falling off its corpse opens nothing.
            (3000, 'SPELL_AURA_REMOVED,%s,%s,55078,"Peste de sang",0x20,DEBUFF'
             % (self.A, self._mob(1))),
            (9000, 'SPELL_CAST_SUCCESS,%s,%s,49576,"Caresse de la mort",0x1'
             % (self.B, self._mob(2))),
            # A miss draws the enemy as surely as a hit: it is the first one.
            (9200, 'SWING_MISSED,%s,%s,MISS,nil' % (self.A, self._mob(2))),
            self._hit(9400, self.B, self._mob(2)),
            # 4.6 s after the last hit: a new pull at three seconds, the same
            # pull at the six that were the default until 0.11.0.
            # The healer who is hit first had just healed Ardoise: the aggro
            # a heal draws. A heal that healed nothing draws none.
            (13800, 'SPELL_HEAL,%s,%s,2061,"Soins rapides",0x2,800,800,0,0,nil'
             % (self.C, self.A)),
            (13900, 'SPELL_HEAL,%s,%s,2061,"Soins rapides",0x2,500,500,500,0,nil'
             % (self.C, self.B)),
            self._hit(14000, self._mob(3), self.C),
            self._hit(14100, self.C, self._mob(3)),
            self._hit(20000, self.PET, self._mob(4)),
            self._hit(20100, self.C, self._mob(5)),
            (30000, "CHALLENGE_MODE_END,2000,1,14,30000"),
        ]
        splitter = Splitter(analysis_factory=SegmentAnalysis)
        for index, (ms, payload) in enumerate(lines):
            _ts, fields = split_line("9/18/2026 20:15:31.123-4  " + payload)
            splitter.feed(build_event(ms, fields, index + 1))
        return splitter.finish()

    def test_each_pull_says_who_acted_first_and_how_early(self):
        analysis = self._key()[0].analysis
        self.assertEqual(len(analysis.blocks), 4)
        openings = [(o[0], o[1], o[2].short_name, o[3], o[5])
                    for o in (block.opening for block in analysis.blocks)]
        self.assertEqual(openings, [
            (0, "groupe", "Ardoise", "Frappe", False),
            (400, "groupe", "Tisane", "Caresse de la mort", False),
            (0, "ennemi", "Braise", "Frappe", False),
            (0, "groupe", "Ardoise", "Frappe", True),
        ])
        self.assertEqual(analysis.blocks[2].opening[4], "Golem")
        before, helped, spell = analysis.blocks[2].opening[6]
        self.assertEqual((before, helped.short_name, spell), (200, "Ardoise", "Soins rapides"))
        self.assertIsNone(analysis.blocks[1].opening[6])
        firsts = [[(ts, enemy, player.short_name, spell, summon)
                   for ts, enemy, player, spell, summon in block.first_hits]
                  for block in analysis.blocks]
        self.assertEqual(firsts, [
            [(1000, "Golem", "Ardoise", "Frappe", False)],
            [(9200, "Golem", "Ardoise", "Attaque", False)],
            [(14100, "Golem", "Braise", "Frappe", False)],
            [(20000, "Golem", "Ardoise", "Frappe", True),
             (20100, "Golem", "Braise", "Frappe", False)],
        ])

    def test_the_pull_gap_is_three_seconds_unless_asked_otherwise(self):
        from logswow.analysis import PULL_GAP_MS

        self.assertEqual(PULL_GAP_MS, 3000)
        splitter = Splitter(analysis_factory=lambda segment: SegmentAnalysis(
            segment, pull_gap_ms=6000))
        self.assertEqual(SegmentAnalysis(Splitter()._new("keystone", "x", 0)).pull_gap_ms,
                         3000)
        del splitter

    def test_the_pull_table_writes_it_under_each_pull(self):
        import tempfile

        segments = self._key()
        log, _fixture = run_fixture()
        with tempfile.TemporaryDirectory() as folder:
            target = os.path.join(folder, "r.html")
            ReportWriter(log, segments, target, wowhead="off", cast_order=False,
                         layout="longue").write()
            with open(target, encoding="utf-8") as handle:
                page = handle.read()
        self.assertIn("Ouvert par <b>Tisane</b>\u202f: Caresse de la mort, "
                      "0,4\u202fs avant le premier coup", page)
        self.assertIn("<span class=pill>bêta</span> <b>Golem</b> a agi en premier, "
                      "sur <b>Braise</b>", page)
        self.assertIn("Premier coup reçu par chaque ennemi (2 ennemis)", page)
        self.assertIn("<li>Golem (2) &mdash; <b>Braise</b>\u202f: Frappe, +0,1\u202fs</li>",
                      page)
        self.assertIn("<li>Golem &mdash; <b>Ardoise</b>\u202f: Attaque, &minus;0,2\u202fs</li>",
                      page)
        self.assertIn("<b>Ardoise</b>, par une invocation", page)
        self.assertIn("\u202f; 0,2\u202fs plus tôt, Braise avait aidé "
                      "<b>Ardoise</b> (Soins rapides)", page)
        self.assertIn("aucune ligne de menace", page)


class TestLayouts(unittest.TestCase):
    """Tabs, a folder of pages, or the long page (2026-09-28)."""

    def _write(self, directory, layout, name="r.html"):
        log, segments = run_fixture()
        target = os.path.join(directory, name)
        return ReportWriter(log, segments, target, wowhead="off", layout=layout).write(), segments

    def test_a_key_folds_its_pulls_and_bosses_under_a_plus(self):
        """The owner, 2026-09-29: the key closed under a "+", and inside it
        every pull in the order it was fought, each a view of its own."""
        import tempfile

        with tempfile.TemporaryDirectory() as directory:
            path, segments = self._write(directory, "onglets")
            with open(path, encoding="utf-8") as handle:
                page = handle.read()
        key = [segment for segment in segments if segment.kind == "keystone"][0]
        self.assertEqual([pull.name for pull in key.pulls], ["Pull 1", "Pull 2"])
        # The fights keep their numbers: pulls are numbered after them.
        self.assertEqual([segment.index for segment in segments], [1, 2, 3])
        self.assertEqual([pull.index for pull in key.pulls], [4, 5])
        self.assertIn("<details class=grp><summary><label for=f3 class='nv n3'>", page)
        self.assertIn("<label for=f4 class='nv n4 in'>Pull 1<small>", page)
        self.assertIn("#f5:checked~.layout .v5{display:block}", page)
        # The sign of an open key: once an octal escape that drew a box.
        self.assertIn('.grp[open]>summary::before{content:"\u2212"}', page)
        pull_view = page[page.index("<section class='fight v4'>"):]
        pull_view = pull_view[:pull_view.index("</section>")]
        self.assertIn("Donjon d&#x27;essai +7 \u2014 Pull 1", pull_view)
        # Its key already draws the cast order pull by pull.
        self.assertNotIn("class=co>", pull_view)
        self.assertEqual(key.pulls[0].analysis.total_damage, key.pulls[0].block.damage_done)

    def test_tabs_are_one_file_with_no_script(self):
        import tempfile

        with tempfile.TemporaryDirectory() as directory:
            path, segments = self._write(directory, "onglets")
            with open(path, encoding="utf-8") as handle:
                page = handle.read()
        self.assertNotIn("<script", page)
        self.assertIn("<input type=radio name=f id=f0 class=fsel checked", page)
        for segment in segments:
            self.assertIn("#f%d:checked~.layout .v%d{display:block}"
                          % (segment.index, segment.index), page)
            self.assertIn("<section class='fight v%d'>" % segment.index, page)
        self.assertIn(".tb-resume:checked~.panes .pn-resume{display:block}", page)
        self.assertIn("<label for=f%d class=name>" % segments[0].index, page)

    def test_pages_are_a_folder_linked_together(self):
        import tempfile

        with tempfile.TemporaryDirectory() as directory:
            folder = os.path.join(directory, "rapport")
            path, segments = self._write(directory, "pages", "rapport")
            self.assertEqual(path, os.path.join(folder, "index.html"))
            names = sorted(os.listdir(folder))
            # One page per fight, and one per trash pull of a key (0.12.0).
            from logswow.report_layouts import page_name, views

            self.assertEqual(names, sorted(["index.html"] + [page_name(view)
                                                             for view in views(segments)]))
            self.assertIn("combat-03-pull-01.html", names)
            with open(path, encoding="utf-8") as handle:
                index = handle.read()
            self.assertIn("href='combat-%02d.html'" % segments[0].index, index)
            with open(os.path.join(folder, "combat-%02d.html" % segments[0].index),
                      encoding="utf-8") as handle:
                self.assertIn("href='index.html'", handle.read())
            # A page left by an earlier report of ours goes; a stranger's stays.
            for name, text in (("combat-99.html", "<!doctype html><title>LogsWoW x"),
                               ("notes.txt", "a moi")):
                with open(os.path.join(folder, name), "w") as handle:
                    handle.write(text)
            self._write(directory, "pages", "rapport")
            self.assertNotIn("combat-99.html", os.listdir(folder))
            self.assertIn("notes.txt", os.listdir(folder))

    def test_a_folder_that_is_not_ours_is_refused(self):
        import tempfile
        from logswow.cli import _refuse_folder

        with tempfile.TemporaryDirectory() as directory:
            log = os.path.join(directory, "WoWCombatLog.txt")
            with open(log, "w") as handle:
                handle.write("x")
            mine = os.path.join(directory, "photos")
            os.makedirs(mine)
            with open(os.path.join(mine, "vacances.jpg"), "w") as handle:
                handle.write("x")
            self.assertIsNotNone(_refuse_folder(mine, log, force=False))
            self.assertIsNone(_refuse_folder(os.path.join(directory, "neuf"), log, False))
            self.assertIsNotNone(_refuse_folder(directory, log, force=True))  # the log's own
            self.assertIsNotNone(_refuse_folder(log, log, force=False))       # a file

    def test_the_command_line_chooses_and_tabs_are_the_default(self):
        import tempfile

        with tempfile.TemporaryDirectory() as directory:
            page = os.path.join(directory, "a.html")
            folder = os.path.join(directory, "b")
            with contextlib.redirect_stdout(io.StringIO()), \
                    contextlib.redirect_stderr(io.StringIO()):
                self.assertEqual(cli_main(["report", FIXTURE, "-q", "-o", page]), 0)
                self.assertEqual(cli_main(["report", FIXTURE, "-q", "-o", folder,
                                           "--format", "pages"]), 0)
            with open(page, encoding="utf-8") as handle:
                self.assertIn("class=layout", handle.read())
            self.assertTrue(os.path.isfile(os.path.join(folder, "index.html")))

    def test_the_window_writes_each_layout_where_it_should(self):
        from logswow import gui

        _log, segments = run_fixture()
        self.assertEqual(gui.default_report_path("/j/Log.txt", segments, segments, "pages"),
                         "/j/Log")
        self.assertEqual(gui.default_report_path("/j/Log.txt", segments, segments), "/j/Log.html")
        self.assertEqual(gui.report_entry("/j/Log", "pages"), os.path.join("/j/Log", "index.html"))
        self.assertEqual(gui.report_entry("/j/Log.html", "longue"), "/j/Log.html")


class TestWhatWarcraftLogsShowed(unittest.TestCase):
    """Five real keys read side by side with Warcraft Logs (2026-09-28).

    Each gap was traced line by line against the site's own events; every
    test here fails without the change it names.
    """

    A = 'Player-9999-00000001,"Ardoise-Dalaran-EU",0x512,0x0'
    B = 'Player-9999-00000002,"Tisane-Dalaran-EU",0x512,0x0'
    MOB = 'Creature-0-9999-2222-1111-70000-0000111111,"Golem",0xa48,0x0'
    NOBODY = '0000000000000000,nil,0x80000000,0x80000000'

    def _run(self, timed_payloads):
        splitter = Splitter(analysis_factory=SegmentAnalysis)
        for index, (ms, payload) in enumerate(timed_payloads):
            _ts, fields = split_line("9/18/2026 20:15:31.123-4  " + payload)
            splitter.feed(build_event(ms, fields, index + 1))
        return splitter.finish()[0].analysis

    def _player(self, analysis, guid_end):
        return analysis.players["Player-9999-0000000%d" % guid_end]

    def _hit(self, ms, source, dest, amount, overkill=-1, spell=100, name="Frappe", school=1):
        return (ms, 'SPELL_DAMAGE,%s,%s,%d,"%s",0x%x,%d,%d,%d,%d,0,0,0,nil,nil,nil,ST'
                % (source, dest, spell, name, school, amount, amount, overkill, school))

    def _heal(self, ms, source, dest, amount, over=0, eaten=0, spell=2061, name="Soin"):
        return (ms, 'SPELL_HEAL,%s,%s,%d,"%s",0x2,%d,%d,%d,%d,nil'
                % (source, dest, spell, name, amount, amount + eaten, over, eaten))

    def test_damage_past_the_last_point_of_health_is_not_dealt(self):
        """Warcraft Logs leaves the overkill out, as healing leaves overhealing."""
        analysis = self._run([self._hit(0, self.A, self.MOB, 5000),
                              self._hit(100, self.A, self.MOB, 9000, overkill=3000)])
        player = self._player(analysis, 1)
        self.assertEqual(player.damage_done, 5000 + 6000)
        ability = next(iter(player.damage_by_ability.values()))
        self.assertEqual((ability.total, ability.overkill), (11000, 3000))
        self.assertEqual(analysis.enemies["Golem"].damage_taken, 11000)

    def test_a_hit_an_enemy_shield_ate_is_damage_dealt(self):
        """0.5% to 1.6% of a key's damage was missing: what enemies' shields ate."""
        caster = self.MOB.rsplit(",", 2)[0]
        wide = ('SPELL_ABSORBED,%s,%s,300,"Eclair",0x4,%s,0xa48,0x0,999,"Barriere",0x20,'
                '4000,9000,1' % (self.A, self.MOB, caster))
        narrow = ('SPELL_ABSORBED,%s,%s,%s,0xa48,0x0,999,"Barriere",0x20,500,700,nil'
                  % (self.A, self.MOB, caster))
        analysis = self._run([self._hit(0, self.A, self.MOB, 1000), (50, wide), (60, narrow)])
        player = self._player(analysis, 1)
        self.assertEqual(player.damage_done, 1000 + 4000 + 500)
        self.assertEqual(analysis.shield_damage, 4500)
        names = {a.name: (a.total, a.crits) for a in player.damage_by_ability.values()}
        self.assertEqual(names["Eclair"], (4000, 1))
        self.assertEqual(names["Attaque"], (500, 0))
        self.assertEqual(analysis.done_by_school, {1: 1500, 4: 4000})
        # A shield on the group is the victim's, never damage dealt.
        on_us = ('SPELL_ABSORBED,%s,%s,300,"Eclair",0x4,%s,999,"Barriere",0x20,800,900,nil'
                 % (self.MOB, self.A, self.A))
        analysis = self._run([(0, on_us)])
        self.assertEqual((analysis.total_damage, self._player(analysis, 1).absorbed_taken),
                         (0, 800))

    def test_a_unit_the_encounter_puts_under_a_players_name_is_a_target(self):
        """'Tombe glaciale': summoned by the player it holds, flagged hostile,
        broken by the group -- 10.9M counted as the group's own damage taken."""
        tomb = 'Creature-0-9999-2222-1111-248000-0000000001,"Tombe glaciale",0xa48,0x0'
        demon = 'Creature-0-9999-2222-1111-17252-0000000002,"Gangregarde",0x1112,0x0'
        lines = [(0, 'SPELL_SUMMON,%s,%s,1240000,"Tombe glaciale",0x10' % (self.A, tomb)),
                 (10, 'SPELL_SUMMON,%s,%s,30146,"Gangregarde",0x20' % (self.B, demon)),
                 self._hit(100, self.B, tomb, 7000),
                 self._hit(200, self.B, demon, 300)]           # the owner's own demon
        analysis = self._run(lines)
        self.assertEqual(self._player(analysis, 2).damage_done, 7000)
        holder = analysis.players.get("Player-9999-00000001")
        self.assertEqual(holder.pet_damage_taken if holder else 0, 0)
        self.assertEqual(self._player(analysis, 2).pet_damage_taken, 300)
        self.assertIn("Tombe glaciale", analysis.enemies)

    def test_spirit_link_moves_health_it_does_not_deal_damage(self):
        """Damage and heal lines in one instant, in either order: nobody's
        damage taken, and the shaman's healing is net of it."""
        totem = 'Creature-0-9999-2222-1111-53006-0000000003,"Totem de lien d\'esprit",0x2111,0x0'
        link = dict(spell=98021, name="Lien d'esprit")
        lines = [(0, 'SPELL_SUMMON,%s,%s,98008,"Totem de lien d\'esprit",0x8' % (self.A, totem)),
                 self._heal(10, self.A, self.B, 10000),
                 self._hit(1000, totem, self.B, 3000, school=8, **link),     # damage first
                 self._heal(1000, totem, self.A, 2500, **link),
                 self._heal(2000, totem, self.B, 1000, **link),              # heal first
                 self._hit(2000, totem, self.A, 1200, school=8, **link),
                 self._hit(3000, self.MOB, self.B, 400)]
        analysis = self._run(lines)
        shaman, other = self._player(analysis, 1), self._player(analysis, 2)
        self.assertEqual(other.damage_taken, 400)
        self.assertEqual(shaman.damage_taken, 0)
        self.assertEqual(shaman.moved_health, 4200)
        self.assertEqual(shaman.healing_done, 10000 + 2500 + 1000 - 4200)
        self.assertEqual(analysis.total_healing, shaman.healing_done)
        self.assertEqual(analysis.moved_health, 4200)
        # The hit still lowered their health: it stays in their recap.
        self.assertIn("Lien d'esprit", [moment[2] for moment in other.recent])

    def test_a_summon_that_never_heals_hits_like_anything_else(self):
        imp = 'Creature-0-9999-2222-1111-55659-0000000004,"Diablotin",0x1112,0x0'
        lines = [(0, 'SPELL_SUMMON,%s,%s,104317,"Diablotin",0x20' % (self.A, imp)),
                 self._hit(100, imp, self.B, 600, spell=555, name="Boule de feu")]
        analysis = self._run(lines)
        self.assertEqual(self._player(analysis, 2).damage_taken, 600)
        self.assertEqual(analysis.moved_health, 0)

    def test_what_a_healing_absorb_ate_is_healing_and_not_taken_off_the_rest(self):
        """The eaten part is beside `amount`, not inside it: the heal of
        74,143 with 141,613 eaten used to count 0."""
        analysis = self._run([self._heal(0, self.A, self.B, 74143, eaten=141613),
                              self._heal(10, self.A, self.B, 0, eaten=8203),
                              self._heal(20, self.A, self.B, 1000, over=400)])
        self.assertEqual(self._player(analysis, 1).healing_done, 215756 + 8203 + 600)

    def test_a_player_who_fell_unconscious_did_not_die(self):
        """A hunter written dead, casting again 217 ms later: not a death."""
        lines = [self._hit(0, self.MOB, self.A, 500),
                 (100, 'UNIT_DIED,%s,%s,1' % (self.NOBODY, self.A)),
                 (200, 'UNIT_DIED,%s,%s,0' % (self.NOBODY, self.B))]
        analysis = self._run(lines)
        self.assertEqual((self._player(analysis, 1).deaths, self._player(analysis, 2).deaths),
                         (0, 1))
        self.assertEqual(analysis.unconscious_seen, 1)
        self.assertEqual(len(analysis.deaths), 1)

    def test_melee_the_group_took_is_read_from_the_line_that_landed(self):
        """SWING_DAMAGE comes first, then its _LANDED twin -- or _LANDED alone."""
        adv = ",".join(advanced_block(19, info="Player-9999-00000001"))

        def swing(ms, kind, source, dest, amount):
            return (ms, '%s,%s,%s,%s,%d,%d,-1,1,0,0,0,nil,nil,nil'
                    % (kind, source, dest, adv, amount, amount))

        lines = [swing(0, "SWING_DAMAGE", self.MOB, self.A, 1000),
                 swing(0, "SWING_DAMAGE_LANDED", self.MOB, self.A, 1100),
                 swing(500, "SWING_DAMAGE_LANDED", self.MOB, self.A, 900),     # alone
                 swing(900, "SWING_DAMAGE", self.MOB, self.A, 700),            # twin below
                 swing(900, "SWING_DAMAGE_LANDED", self.MOB, self.A, 800),
                 swing(1000, "SWING_DAMAGE", self.A, self.MOB, 400),           # dealt
                 swing(1000, "SWING_DAMAGE_LANDED", self.A, self.MOB, 400)]
        analysis = self._run(lines)
        player = self._player(analysis, 1)
        self.assertEqual(player.damage_taken, 1100 + 900 + 800)
        self.assertEqual(player.damage_done, 400)
        # A file that writes no _LANDED at all keeps SWING_DAMAGE.
        analysis = self._run([swing(0, "SWING_DAMAGE", self.MOB, self.A, 1000),
                              swing(10, "SWING_DAMAGE", self.MOB, self.A, 500)])
        self.assertEqual(self._player(analysis, 1).damage_taken, 1500)


class TestSixthAuditFindings(unittest.TestCase):
    """The 2026-09-28 audit of 0.7.0: what three real logs and a full read
    of every file found. Each test fails without the change it names."""

    MOB = 'Creature-0-9999-2222-1111-70000-0000111111,"Golem",0xa48,0x0'
    NOBODY = '0000000000000000,nil,0x80000000,0x80000000'

    @staticmethod
    def _player(n):
        return 'Player-9999-%08d,"Joueur%d-Dalaran-EU",0x512,0x0' % (n, n)

    def _run(self, timed_payloads):
        splitter = Splitter(analysis_factory=SegmentAnalysis)
        for index, (ms, payload) in enumerate(timed_payloads):
            _ts, fields = split_line("9/18/2026 20:15:31.123-4  " + payload)
            splitter.feed(build_event(ms, fields, index + 1))
        return splitter.finish()

    def _page(self, segments):
        import tempfile

        log, _fixture = run_fixture()
        with tempfile.TemporaryDirectory() as directory:
            target = os.path.join(directory, "r.html")
            ReportWriter(log, segments, target, wowhead="off", cast_order=False,
                         layout="longue").write()
            with open(target, encoding="utf-8") as handle:
                return handle.read()

    def test_a_raid_of_more_than_twenty_is_ranked_whole(self):
        """A real heroic encounter had 21 players; the ranking stopped at
        twenty and the last one vanished from it. Deaths stopped at 24."""
        lines = [(0, 'ENCOUNTER_START,1,"Golem",15,30,2000')]
        for n in range(1, 31):
            lines.append((n, 'SPELL_DAMAGE,%s,%s,1,"Frappe",0x1,%d,%d,-1,1,0,0,0,nil,nil,nil,ST'
                          % (self._player(n), self.MOB, 1000 + n, 1000 + n)))
            lines.append((100 + n, 'UNIT_DIED,%s,%s,0' % (self.NOBODY, self._player(n))))
        lines.append((500, 'ENCOUNTER_END,1,"Golem",15,30,0,500'))
        page = self._page(self._run(lines))
        ranking = page.split("<h3>Dégâts infligés</h3>", 1)[1].split("</table>", 1)[0]
        self.assertEqual(ranking.count("<tr>") - 1, 30)
        self.assertEqual(page.count("<details><summary>Joueur"), 30 + 30)   # deaths + panels

    def test_a_healer_with_many_targets_shows_them_all(self):
        """A raid healer reached 36 targets; the list stopped at twenty."""
        healer = self._player(99)
        lines = [(0, 'ENCOUNTER_START,1,"Golem",15,30,2000'),
                 (1, 'SPELL_DAMAGE,%s,%s,1,"Frappe",0x1,10,10,-1,1,0,0,0,nil,nil,nil,ST'
                  % (healer, self.MOB))]
        for n in range(1, 26):
            lines.append((10 + n, 'SPELL_HEAL,%s,%s,2,"Soin",0x2,%d,%d,0,0,nil'
                          % (healer, self._player(n), 500 - n, 500 - n)))
        lines.append((100, 'ENCOUNTER_END,1,"Golem",15,30,1,100'))
        page = self._page(self._run(lines))
        self.assertIn("5 cibles de plus", page)
        self.assertIn(">Joueur25<", page.replace("<span class=name>", ">"))

    def test_an_instant_kill_is_the_cause_of_death(self):
        """SPELL_INSTAKILL carries no amount: three of five unexplained
        deaths on a real raid night, eleven such lines on a Mythic+ one."""
        victim = self._player(1)
        segments = self._run([
            (0, 'ENCOUNTER_START,1,"Golem",15,30,2000'),
            (10, 'SPELL_HEAL,%s,%s,2,"Soin",0x2,500,500,0,0,nil' % (victim, victim)),
            (20, 'SPELL_INSTAKILL,%s,%s,777,"Aneantissement",0x20,0' % (self.MOB, victim)),
            (21, 'UNIT_DIED,%s,%s,0' % (self.NOBODY, victim)),
            (30, 'ENCOUNTER_END,1,"Golem",15,30,0,30'),
        ])
        death = segments[0].analysis.deaths[0]
        self.assertEqual(death["killing_blow"], "Aneantissement (Golem)")
        self.assertIn("mort instantanée", self._page(segments))

    def test_a_death_the_file_explains_nowhere_says_so(self):
        victim = self._player(1)
        segments = self._run([
            (0, 'ENCOUNTER_START,1,"Golem",15,30,2000'),
            (10, 'SPELL_HEAL,%s,%s,2,"Soin",0x2,500,500,0,0,nil' % (victim, victim)),
            (21, 'UNIT_DIED,%s,%s,0' % (self.NOBODY, victim)),
            (30, 'ENCOUNTER_END,1,"Golem",15,30,0,30'),
        ])
        self.assertIn("cause non écrite dans le journal", self._page(segments))

    def test_a_shield_hit_from_a_pet_nobody_owns_is_unattributed_not_lost(self):
        pet = 'Pet-0-9999-1-1-00099,"Cendre",0x1114,0x0'
        caster = self.MOB.rsplit(",", 2)[0]
        analysis = self._run([
            (0, 'SPELL_ABSORBED,%s,%s,300,"Morsure",0x1,%s,0xa48,0x0,999,"Barriere",0x20,'
                '700,900,nil' % (pet, self.MOB, caster)),
        ])[0].analysis
        self.assertEqual(analysis.total_damage, 0)
        self.assertEqual(analysis.orphan_damage, 700)

    def test_the_window_refuses_a_second_read_while_one_runs(self):
        """'Choisir un autre fichier...' stayed clickable during a read and
        started a second one; the first file's fights then came back under
        the second file's name."""
        from types import SimpleNamespace

        from logswow import gui

        app = SimpleNamespace(busy=True, read=lambda path: self.fail("a second read"))
        self.assertIsNone(gui.App.choose_file(app))

    def test_every_published_minor_version_keeps_its_changelog_section(self):
        """Writing each new section *over* the previous heading lost 0.5.0
        and 0.5.1: their notes were published inside 0.5.1's and 0.6.0's."""
        from logswow import __version__

        with open(os.path.join(ROOT, "CHANGELOG.md"), encoding="utf-8") as handle:
            versions = [tuple(int(p) for p in line.split()[1].split("."))
                        for line in handle if line.startswith("## ")]
        self.assertEqual(versions[0], tuple(int(p) for p in __version__.split(".")))
        self.assertEqual(versions, sorted(set(versions), reverse=True))
        minors = {version[:2] for version in versions}
        self.assertEqual(minors, {(0, minor) for minor in range(1, versions[0][1] + 1)})

    def test_the_licence_is_the_fsf_text_byte_for_byte(self):
        import hashlib

        with open(os.path.join(ROOT, "LICENSE"), "rb") as handle:
            digest = hashlib.sha256(handle.read()).hexdigest()
        self.assertEqual(
            digest, "0d96a4ff68ad6d4b6f1f30f713b18d5184912ba8dd389f86aa7710db079abcb0")
        from logswow import __doc__ as notice

        self.assertIn("GNU Affero General Public License", notice)

    def test_every_source_file_names_its_licence(self):
        # One SPDX line per file, so a file copied out alone still says
        # what it may be used under.
        tag = "# SPDX-License-Identifier: AGPL-3.0-or-later\n"
        paths = []
        for folder in ("logswow", "tests", "tools"):
            for name in sorted(os.listdir(os.path.join(ROOT, folder))):
                path = os.path.join(ROOT, folder, name)
                if os.path.isfile(path) and (name.endswith(".py") or "." not in name):
                    paths.append(path)
        self.assertGreater(len(paths), 30)
        for path in paths:
            with open(path, encoding="utf-8") as handle:
                head = handle.readline() + handle.readline()
            with self.subTest(path=path):
                self.assertIn(tag, head)


class TestLanguages(unittest.TestCase):
    """French, English (0.9.0), German and Spanish (0.10.0): one set of numbers,
    four ways of saying them."""

    TABLES = ("en", "de", "es")

    PACKAGE = os.path.join(ROOT, "logswow")
    SLOT = re.compile(r"%(?:\.0s|[-0-9.]*[sdfr]|%)")
    TAG = re.compile(r"<(/?[a-z0-9]+)")

    def tearDown(self):
        from logswow.i18n import set_language

        set_language("fr")

    def _marked(self):
        """{French text: where} of every _() and N_() in the package, and plural nouns."""
        import ast

        texts, nouns = {}, {}
        for name in sorted(os.listdir(self.PACKAGE)):
            if not name.endswith(".py") or name.startswith("lang_"):
                continue
            with open(os.path.join(self.PACKAGE, name), encoding="utf-8") as handle:
                tree = ast.parse(handle.read())
            for node in ast.walk(tree):
                if not isinstance(node, ast.Call):
                    continue
                called = getattr(node.func, "id", None) or getattr(node.func, "attr", None)
                first = node.args[0] if node.args else None
                if called in ("_", "N_") and isinstance(first, ast.Constant):
                    texts.setdefault(first.value, "%s:%d" % (name, node.lineno))
                if (called == "plural" and len(node.args) > 1
                        and isinstance(node.args[1], ast.Constant)):
                    nouns.setdefault(node.args[1].value, "%s:%d" % (name, node.lineno))
        return texts, nouns

    def test_every_text_has_its_translation_and_keeps_its_placeholders_and_tags(self):
        import importlib

        from logswow.i18n import LANGUAGES

        self.assertEqual(LANGUAGES, ("fr",) + self.TABLES)
        texts, nouns = self._marked()
        self.assertGreater(len(texts), 250)
        for code in self.TABLES:
            table = importlib.import_module("logswow.lang_" + code)
            for french, where in texts.items():
                with self.subTest(language=code, where=where):
                    self.assertIn(french, table.TEXTS)
                    translated = table.TEXTS[french]
                    kinds = [re.sub(r"[-0-9.]", "", slot)[-1]
                             for slot in self.SLOT.findall(french)]
                    self.assertEqual(
                        kinds, [re.sub(r"[-0-9.]", "", slot)[-1]
                                for slot in self.SLOT.findall(translated)])
                    self.assertEqual(self.TAG.findall(french), self.TAG.findall(translated))
            with self.subTest(language=code):
                # Nothing in the table the code no longer says.
                self.assertEqual(sorted(set(table.TEXTS) - set(texts)), [])
                self.assertEqual(sorted(set(nouns) - set(table.PLURALS)), [])

    def test_the_current_version_is_told_in_every_language(self):
        import subprocess

        from logswow import __version__

        for code in self.TABLES:
            with self.subTest(language=code):
                path = os.path.join(ROOT, "CHANGELOG.%s.md" % code)
                with open(path, encoding="utf-8") as handle:
                    headings = [line.split()[1] for line in handle if line.startswith("## ")]
                self.assertEqual(headings[0], __version__)
        result = subprocess.run(
            [sys.executable, os.path.join(ROOT, "tools", "release-notes"), __version__],
            capture_output=True, text=True, timeout=60)
        for title in ("**English**", "**Deutsch**", "**Español**"):
            self.assertIn(title, result.stdout)

    def test_every_readme_and_install_guide_points_to_the_three_others(self):
        for stem in ("README", "INSTALL"):
            names = ["%s.md" % stem] + ["%s.%s.md" % (stem, code) for code in self.TABLES]
            for name in names:
                with open(os.path.join(ROOT, name), encoding="utf-8") as handle:
                    head = handle.read(600)
                with self.subTest(document=name):
                    for other in names:
                        if other != name:
                            self.assertIn("(%s)" % other, head)

    def test_every_specialization_has_its_name_in_every_language(self):
        import importlib

        from logswow.i18n import set_language
        from logswow.specs import SPECS, label_of

        for code in self.TABLES:
            with self.subTest(language=code):
                table = importlib.import_module("logswow.lang_" + code)
                self.assertEqual(set(SPECS), set(table.SPECS))
        # English puts the specialization first; German and Spanish do not.
        labels = []
        for code in ("en", "de", "es"):
            set_language(code)
            labels.append(label_of(268))
        self.assertEqual(labels, ["Brewmaster Monk", "Mönch Braumeister",
                                  "Monje Maestro cervecero"])

    def test_no_function_hides_the_translation_behind_a_variable(self):
        # `for _ in ...` or `a, _ = ...` in a function makes every _() in
        # it call a string: parse.py did it three times, and every test
        # that read a log failed at once.
        import ast

        for name in sorted(os.listdir(self.PACKAGE)):
            if not name.endswith(".py"):
                continue
            with open(os.path.join(self.PACKAGE, name), encoding="utf-8") as handle:
                tree = ast.parse(handle.read())
            for node in ast.walk(tree):
                stored = (isinstance(node, ast.Name) and node.id == "_"
                          and isinstance(node.ctx, ast.Store))
                argument = isinstance(node, ast.arg) and node.arg == "_"
                with self.subTest(module=name, line=getattr(node, "lineno", 0)):
                    self.assertFalse(stored or argument)

    def test_the_language_is_the_one_asked_for_else_the_machines_else_english(self):
        from unittest import mock

        from logswow.i18n import choose

        self.assertEqual(choose("en"), "en")
        self.assertEqual(choose("fr_FR.UTF-8"), "fr")
        self.assertEqual(choose("de_AT.UTF-8"), "de")
        self.assertEqual(choose("es-MX"), "es")
        self.assertEqual(choose("it"), "en")
        with mock.patch.dict(os.environ, {"LOGSWOW_LANGUE": ""}), \
                mock.patch("logswow.i18n.system_language", return_value="fr"):
            self.assertEqual(choose("auto"), "fr")
        with mock.patch.dict(os.environ, {"LOGSWOW_LANGUE": ""}), \
                mock.patch("logswow.i18n.system_language", return_value="de"):
            self.assertEqual(choose("auto"), "de")
        with mock.patch.dict(os.environ, {"LOGSWOW_LANGUE": ""}), \
                mock.patch("logswow.i18n.system_language", return_value="pt"):
            self.assertEqual(choose("auto"), "en")
        with mock.patch.dict(os.environ, {"LOGSWOW_LANGUE": "en"}):
            self.assertEqual(choose("auto"), "en")

    def test_langue_is_read_before_the_command_and_after_it(self):
        from logswow.cli import requested_language

        self.assertEqual(requested_language(["--langue", "en", "list", "x"]), "en")
        self.assertEqual(requested_language(["list", "x", "--lang=fr"]), "fr")
        self.assertEqual(requested_language(["list", "x"]), "auto")

    def test_numbers_are_written_the_way_each_language_writes_them(self):
        from logswow import fmt
        from logswow.i18n import set_language

        french = (fmt.number(25361906), fmt.compact(25361906), fmt.percent(0.456),
                  fmt.plural(0, "joueur"), fmt.decimal(0.5))
        # The decimal comma in the compact form too: "25.4 M" was an
        # English point in a French number until 0.10.0.
        self.assertEqual(french, ("25\u202f361\u202f906", "25,4\u202fM", "46\u202f%",
                                  "0 joueur", "0,5"))
        self.assertEqual((fmt.compact(1e6 - 1), fmt.compact(2e9), fmt.compact(-1500),
                          fmt.compact(20000)),
                         ("1\u202fM", "2\u202fMd", "-1,5\u202fk", "20\u202fk"))
        expected = {
            "en": ("25,361,906", "25.4M", "46%", "0 players", "1 player", "0.5"),
            "de": ("25.361.906", "25,4\u202fMio.", "46\u202f%", "0 Spieler", "1 Spieler",
                   "0,5"),
            "es": ("25.361.906", "25,4\u202fM", "46\u202f%", "0 jugadores", "1 jugador",
                   "0,5"),
        }
        for code, numbers in expected.items():
            set_language(code)
            self.assertEqual((fmt.number(25361906), fmt.compact(25361906), fmt.percent(0.456),
                              fmt.plural(0, "joueur"), fmt.plural(1, "joueur"),
                              fmt.decimal(0.5)), numbers)

    def test_an_english_report_says_everything_in_english_and_the_same_numbers(self):
        import tempfile

        with tempfile.TemporaryDirectory() as folder:
            pages = {}
            for language in ("fr", "en"):
                out = os.path.join(folder, language + ".html")
                with contextlib.redirect_stdout(io.StringIO()), \
                        contextlib.redirect_stderr(io.StringIO()):
                    cli_main(["report", FIXTURE, "--langue", language, "-o", out,
                              "--format", "longue"])
                with open(out, encoding="utf-8") as handle:
                    pages[language] = handle.read()
        english = pages["en"]
        self.assertIn("<html lang=en>", english)
        for words in ("Damage done", "Player details", "What hurt the group", "Damage taken",
                      "kill", "Melee"):
            self.assertIn(words, english)
        text = re.sub(r"<[^>]+>", " ", re.sub(r"<style>.*?</style>", "", english, flags=re.S))
        text = text.replace("exemple-combat.txt", "")
        for french in ("Dégâts", "dégâts", "joueur", "réussite", "échec", "Détail", "journal",
                       "Durée", "Attaque", "sorts"):
            self.assertNotIn(french, text)
        # The same fight, the same totals, each in its own typography.
        self.assertIn("45,6\u202fk", pages["fr"])
        self.assertIn("45.6k", english)

    def test_german_and_spanish_reports_carry_the_same_numbers(self):
        import tempfile

        with tempfile.TemporaryDirectory() as folder:
            for code, words, total in (("de", ("Verursachter Schaden", "Details pro Spieler",
                                               "Nahkampf"), "45,6\u202fTsd."),
                                       ("es", ("Daño infligido", "Detalle por jugador",
                                               "Cuerpo a cuerpo"), "45,6\u202fmil")):
                out = os.path.join(folder, code + ".html")
                with contextlib.redirect_stdout(io.StringIO()), \
                        contextlib.redirect_stderr(io.StringIO()):
                    cli_main(["report", FIXTURE, "--langue", code, "-o", out,
                              "--format", "longue"])
                with open(out, encoding="utf-8") as handle:
                    page = handle.read()
                with self.subTest(language=code):
                    self.assertIn("<html lang=%s>" % code, page)
                    for word in words:
                        self.assertIn(word, page)
                    self.assertIn(total, page)

    def test_the_command_line_speaks_the_language_asked_for(self):
        out = io.StringIO()
        with contextlib.redirect_stdout(out), contextlib.redirect_stderr(io.StringIO()):
            cli_main(["list", FIXTURE, "--langue", "en"])
        self.assertIn("Fight", out.getvalue())
        self.assertIn("kill", out.getvalue())
        out = io.StringIO()
        with contextlib.redirect_stdout(out), contextlib.redirect_stderr(io.StringIO()):
            cli_main(["--langue", "fr", "list", FIXTURE])
        self.assertIn("réussite", out.getvalue())


class TestGearAndComparison(unittest.TestCase):
    """0.15.0: the gear a fight starts with, the keys side by side, the window's preview."""

    @staticmethod
    def _entry(item, ilvl, enchants="()", gems="()"):
        return "(%d,%d,%s,(),%s)" % (item, ilvl, enchants, gems)

    def _gear(self, entries):
        from logswow.gear import parse

        fields = split_fields("COMBATANT_INFO,P,1,%s,73,[],[],[%s],[],0"
                              % (",".join(["0"] * 22), ",".join(entries)))
        return parse(fields)

    def _worn(self, ilvl, off_hand=True, empty=()):
        return [self._entry(0, 0) if index in empty or (index == 16 and not off_hand)
                else self._entry(900000 + index, ilvl + index) for index in range(18)]

    def test_the_equipment_is_the_field_at_index_28_and_its_average_follows_the_game(self):
        gear = self._gear(self._worn(600))
        self.assertEqual(len(gear.items), 18)
        self.assertEqual(gear.items[2].item_id, 900002)
        # Sixteen slots, shirt (3) and tabard (17) left out: 600 + the mean of 0..16 but 3.
        expected = sum(600 + i for i in range(17) if i != 3) / 16.0
        self.assertAlmostEqual(gear.average, expected)
        self.assertFalse(gear.two_handed)

    def test_a_two_handed_weapon_counts_twice_and_an_empty_slot_counts_zero(self):
        two = self._gear(self._worn(600, off_hand=False))
        base = sum(600 + i for i in range(17) if i != 3 and i != 16)
        self.assertTrue(two.two_handed)
        self.assertAlmostEqual(two.average, (base + 615) / 16.0)
        self.assertEqual(two.empty_slots(), [])           # the weapon fills both hands
        hole = self._gear(self._worn(600, empty=(1,)))
        self.assertEqual(hole.empty_slots(), [1])
        self.assertAlmostEqual(hole.average, (sum(600 + i for i in range(17) if i not in (1, 3)))
                               / 16.0)

    def test_enchants_and_gems_are_read_and_a_gem_is_an_id_then_its_level(self):
        entries = self._worn(600)
        entries[4] = self._entry(900004, 604, "(7000,7001)", "(213743,619,213744,619)")
        item = self._gear(entries).items[4]
        self.assertEqual(item.enchants, (7000, 7001))
        self.assertEqual(item.gems, (213743, 213744))

    def test_a_line_without_equipment_gives_none_rather_than_a_guess(self):
        from logswow.gear import parse

        self.assertIsNone(parse(split_fields("COMBATANT_INFO,P,1,0,0")))
        self.assertIsNone(parse(split_fields("COMBATANT_INFO,P,1,%s,73,[],[],[],[],0"
                                             % ",".join(["0"] * 22))))
        self.assertIsNone(self._gear(self._worn(600)[:10]))           # too short: not measured
        self.assertIsNone(self._gear([self._entry(0, 0)] * 18))     # nothing worn at all

    def test_the_fixture_players_carry_their_gear(self):
        _log, segments = run_fixture()
        players = segments[0].analysis.players
        self.assertEqual(len(players), 3)
        averages = sorted(round(player.gear.average, 1) for player in players.values())
        self.assertEqual(averages, [round(x, 1) for x in sorted(averages)])
        self.assertTrue(all(player.gear is not None for player in players.values()))

    def test_rates_are_per_second_and_only_a_tank_gets_damage_taken_per_second(self):
        from types import SimpleNamespace
        from logswow import preview
        from logswow.specs import DPS, TANK

        analysis = SimpleNamespace(duration_ms=100000)
        player = SimpleNamespace(damage_done=5000000, healing_done=800000, absorb_done=200000,
                                 damage_taken=3000000, absorbed_taken=1000000,
                                 short_name="Ardoise", spec_id=73, deaths=1, gear=None)
        rate = preview.rates(analysis, player)
        self.assertEqual((rate["dps"], rate["hps"], rate["taken"]), (50000, 10000, 40000))
        self.assertIn("subis/s", preview.player_line(analysis, player, TANK))
        self.assertNotIn("subis/s", preview.player_line(analysis, player, DPS))

    def test_a_change_is_the_last_run_against_the_first_and_never_says_minus_zero(self):
        from logswow import preview

        self.assertAlmostEqual(preview.change([100.0, 90.0, 110.0]), 0.10)
        self.assertIsNone(preview.change([100.0]))
        self.assertIsNone(preview.change([0.0, 5.0]))
        self.assertIsNone(preview.change([None, 5.0]))
        self.assertEqual(preview.change_text(0.103), "+10\u202f%")
        self.assertEqual(preview.change_text(-0.0001), preview.change_text(0.0))
        self.assertNotIn("\u2212", preview.change_text(-0.0001))

    def _two_keys(self):
        import tempfile

        with open(FIXTURE, encoding="utf-8") as handle:
            text = handle.read()
        with tempfile.TemporaryDirectory() as folder:
            path = os.path.join(folder, "WoWCombatLog-091826_235900.txt")
            with open(path, "w", encoding="utf-8") as handle:
                handle.write(text + text.replace("9/18/2026", "9/19/2026"))
            log = LogFile(path)
            splitter = Splitter(analysis_factory=SegmentAnalysis)
            for event in log.events():
                splitter.feed(event)
            return log, splitter.finish()

    def test_only_finished_keys_of_the_same_level_are_lined_up(self):
        from logswow import preview

        _log, segments = self._two_keys()
        keys = [segment for segment in segments if segment.kind == "keystone"]
        self.assertEqual(len(keys), 2)
        groups = preview.comparison(segments)
        self.assertEqual([len(group["runs"]) for group in groups], [2])
        self.assertTrue(groups[0]["players"])
        self.assertIn("2 clés", preview.comparison_text(groups))
        keys[1].abandoned = True
        self.assertEqual([len(g["runs"]) for g in preview.comparison(segments)], [1])
        self.assertEqual(preview.comparison(segments)[0]["players"], [])
        keys[1].abandoned = False
        keys[1].key_level = 8
        self.assertEqual(sorted(len(g["runs"]) for g in preview.comparison(segments)), [1, 1])
        self.assertIn("Aucune clé terminée", preview.comparison_text(preview.comparison([])))

    def test_the_columns_of_the_text_never_run_into_each_other(self):
        from logswow import preview

        _log, segments = self._two_keys()
        lines = preview.comparison_text(preview.comparison(segments)).splitlines()
        issue = [line for line in lines if line.startswith("Issue")][0]
        self.assertIn("dans les temps  dans les temps", issue)     # two cells, two spaces apart
        head = [line for line in lines if "Clé 3" in line][0]
        self.assertIn("Clé 4", head)
        self.assertTrue(head.rstrip().endswith("Écart"))

    def _page(self, log, segments, layout="longue"):
        import tempfile

        with tempfile.TemporaryDirectory() as folder:
            target = os.path.join(folder, "rapport.html")
            ReportWriter(log, segments, target, layout=layout).write()
            with open(target, encoding="utf-8") as handle:
                return handle.read()

    def test_the_page_carries_the_comparison_the_ilvl_and_the_gear_and_fetches_nothing(self):
        log, segments = self._two_keys()
        for layout in ("longue", "onglets"):
            with self.subTest(layout=layout):
                page = self._page(log, segments, layout)
                # Two tabs of the overview (fights, comparison): the page does not grow.
                self.assertIn("<label for=ov-keys class='olb ol-keys'>Comparaison des clés</label>",
                              page)
                self.assertIn("<label for=ov-fights class='olb ol-fights'>Combats</label>", page)
                self.assertNotIn("<h2>Comparaison des clés</h2>", page)
                self.assertIn("Clé 3", page)
                self.assertIn("Clé 4", page)
                self.assertIn("Niveau d'objet moyen du groupe", page)
                self.assertIn("objet 900000", page)
                self.assertIn("(non compté)", page)
                self.assertIn("Emplacement vide", page)       # the DPS has no neck and no ring
                # Slot, item and level only: an enchant id or a gem count means nothing to a player.
                self.assertNotIn("Enchantements", page)
                self.assertNotIn("Gemmes", page)
                # Item links are anchors Wowhead opens on a click, never something fetched.
                self.assertIn("<a href='https://www.wowhead.com/", page)
                self.assertNotRegex(page, r"(?i)<(img|script|link|iframe)\b")
                self.assertNotRegex(page, r"(?i)\bsrc\s*=|@import|url\(")
        # One key, nothing to line up: no card.
        one = self._page(log, segments[:1])
        self.assertNotIn("Comparaison des clés", one)
        self.assertNotIn("class=otab", one)           # one pane only: no tabs to draw
        # The first cell of the overview carries the number the comparison calls a fight by.
        self.assertRegex(self._page(log, segments), r"<span class=dim>3</span> <a href='#s3'")

    def test_the_window_preview_has_two_tabs_and_an_empty_message(self):
        from logswow import gui

        keys = [key for key, _title in gui.PREVIEW_TABS]
        self.assertEqual(keys, ["overview", "keys"])     # no gear tab: ids mean nothing to a player
        empty = gui.preview_texts([])
        self.assertEqual(set(empty), set(keys))
        self.assertIn("Cochez", empty["overview"])
        _log, segments = self._two_keys()
        texts = gui.preview_texts(segments[:1])
        self.assertIn("Golem d'essai", texts["overview"])
        # The item level stays, per player and for the group; the items themselves do not.
        self.assertIn("ilvl 6", texts["overview"])
        self.assertIn("Niveau d'objet moyen du groupe", texts["overview"])
        self.assertNotRegex(texts["overview"], r"objet \d+")
        self.assertIn("Aucune clé", texts["keys"])
        self.assertIn("2 clés", gui.preview_texts(segments)["keys"])

    def test_each_player_s_item_level_is_in_the_composition_of_the_page(self):
        log, segments = self._two_keys()
        page = self._page(log, segments)
        self.assertRegex(page, r"<span class=dim>[^<]*\u00b7 ilvl 6\d\d,\d</span>")

    def test_the_preview_follows_the_selection_in_the_window(self):
        """Needs Tkinter and a display; skipped wherever either is missing."""
        import tempfile
        from logswow import gui

        try:
            import tkinter
            root = tkinter.Tk()
        except (ImportError, Exception) as error:        # noqa: BLE001 -- no screen here
            self.skipTest("pas de fenetre possible ici : %s" % str(error).splitlines()[0])
        try:
            with tempfile.TemporaryDirectory() as folder:
                log_path = os.path.join(folder, "WoWCombatLog-092726_200000.txt")
                with open(FIXTURE, "rb") as source, open(log_path, "wb") as copy:
                    copy.write(source.read())
                app = gui.App(root, locations=[folder])
                app.read_selected()
                deadline = time.time() + 30
                while app.segments is None and time.time() < deadline:
                    root.update()
                    time.sleep(0.02)
                time.sleep(0.3)
                root.update()
                overview = app.previews["overview"]
                self.assertIn("Golem d'essai", overview.get("1.0", "end"))
                app.fights.selection_set(())
                root.update()
                time.sleep(0.3)
                root.update()
                self.assertIn("Cochez", overview.get("1.0", "end"))
        finally:
            root.destroy()


class TestSeventhAuditFindings(unittest.TestCase):
    """The 2026-09-29 audit of 0.12.1: a full read of every file, the
    tools of the earlier audits again, and one real 364 MB Mythic+ night.
    Each test fails without the change it names, except the mind-control
    and the stepping-out ones, which guard that change from reaching too far."""

    MOB = 'Creature-0-9999-2222-1111-70000-0000111111,"Golem",0xa48,0x0'
    NOBODY = '0000000000000000,nil,0x80000000,0x80000000'
    PLAYER = 'Player-9999-00000003,"Braise-Dalaran-EU",0x514,0x0'
    PET = 'Pet-0-9999-2222-1111-00004,"Cendre",0x1114,0x0'

    def tearDown(self):
        from logswow.i18n import set_language

        set_language("fr")

    def _run(self, timed_payloads):
        splitter = Splitter(analysis_factory=SegmentAnalysis)
        for index, (ms, payload) in enumerate(timed_payloads):
            _ts, fields = split_line("9/18/2026 20:15:31.123-4  " + payload)
            splitter.feed(build_event(ms, fields, index + 1))
        return splitter.finish()

    def _page(self, segments, language="fr"):
        import tempfile

        from logswow.i18n import set_language

        log, _fixture = run_fixture()
        set_language(language)
        with tempfile.TemporaryDirectory() as directory:
            target = os.path.join(directory, "r.html")
            ReportWriter(log, segments, target, wowhead="off", layout="longue").write()
            with open(target, encoding="utf-8") as handle:
                return handle.read()

    def test_a_summons_casts_do_not_hide_the_players_own_pauses(self):
        """A pet's casts ended the owner's pause: a hunter who pressed
        nothing for forty seconds while the pet bit every second read zero
        seconds of downtime and no gap at all."""
        lines = [(0, 'SPELL_SUMMON,%s,%s,883,"Appel",0x1' % (self.PLAYER, self.PET)),
                 (1000, 'SPELL_CAST_SUCCESS,%s,%s,1,"Tir",0x1' % (self.PLAYER, self.MOB)),
                 (1100, 'SPELL_DAMAGE,%s,%s,1,"Tir",0x1,5000,5000,-1,1,0,0,0,nil,nil,nil,ST'
                  % (self.PLAYER, self.MOB))]
        for second in range(2, 41):
            lines.append((second * 1000, 'SPELL_CAST_SUCCESS,%s,%s,2,"Morsure",0x1'
                          % (self.PET, self.MOB)))
            lines.append((second * 1000 + 100,
                          'SPELL_DAMAGE,%s,%s,2,"Morsure",0x1,700,700,-1,1,0,0,0,nil,nil,nil,ST'
                          % (self.PET, self.MOB)))
        lines.append((41000, 'SPELL_CAST_SUCCESS,%s,%s,1,"Tir",0x1' % (self.PLAYER, self.MOB)))
        lines.append((41100, 'SPELL_DAMAGE,%s,%s,1,"Tir",0x1,5000,5000,-1,1,0,0,0,nil,nil,nil,ST'
                      % (self.PLAYER, self.MOB)))
        segment = self._run(lines)[0]
        player = segment.analysis.players["Player-9999-00000003"]
        self.assertEqual(player.casts, 41)          # the pet's casts are still counted...
        self.assertEqual(player.pet_casts, 39)
        self.assertEqual(player.longest_gaps[0][0], 40000)    # ...but end no pause
        self.assertGreaterEqual(player.downtime_ms, 38000)

    def test_an_opposing_player_is_an_enemy_not_the_group(self):
        """In an arena the other side is written outside the group and
        hostile (0x548). It was counted as the group: the opponent sat in
        the ranking, every blow between the teams was friendly fire, and
        the damage dealt read zero."""
        rival = 'Player-9999-00000009,"Rival-Hyjal-EU",0x548,0x0'
        rival_pet = 'Pet-0-9999-2222-1111-00009,"Loup",0x1148,0x0'
        lines = [(0, 'SPELL_SUMMON,%s,%s,883,"Appel",0x1' % (rival, rival_pet)),
                 (10, 'SPELL_CAST_START,%s,%s,5,"Eclair",0x8' % (rival, self.NOBODY))]
        for second in range(1, 11):
            lines.append((second * 1000, 'SPELL_DAMAGE,%s,%s,1,"Frappe",0x1,5000,5000,-1,1,0,0,0,'
                          'nil,nil,nil,ST' % (self.PLAYER, rival)))
            lines.append((second * 1000 + 500, 'SPELL_DAMAGE,%s,%s,4,"Riposte",0x1,3000,3000,-1,1,'
                          '0,0,0,nil,nil,nil,ST' % (rival, self.PLAYER)))
            lines.append((second * 1000 + 700, 'SPELL_DAMAGE,%s,%s,6,"Morsure",0x1,400,400,-1,1,'
                          '0,0,0,nil,nil,nil,ST' % (rival_pet, self.PLAYER)))
        lines.append((10800, 'SPELL_INTERRUPT,%s,%s,7,"Coup",0x1,5,"Eclair",0x8'
                      % (self.PLAYER, rival)))
        lines.append((11000, 'UNIT_DIED,%s,%s,0' % (self.NOBODY, rival)))
        analysis = self._run(lines)[0].analysis
        self.assertEqual(set(analysis.players), {"Player-9999-00000003"})
        ours = analysis.players["Player-9999-00000003"]
        self.assertEqual(ours.damage_done, 50000)
        self.assertEqual(ours.damage_taken, 34000)          # the rival and the rival's pet
        self.assertEqual(analysis.total_damage, 50000)
        self.assertEqual(analysis.enemies["Rival"].deaths, 1)
        self.assertEqual(analysis.enemy_casts["coupes"], 1)
        self.assertEqual(analysis.deaths, [])

    def test_a_raid_member_under_a_mind_control_stays_in_the_group(self):
        """Hostile but still in the raid (0x544): not an opponent."""
        controlled = 'Player-9999-00000005,"Tisane-Dalaran-EU",0x544,0x0'
        lines = [(1000, 'SPELL_DAMAGE,%s,%s,1,"Frappe",0x1,5000,5000,-1,1,0,0,0,nil,nil,nil,ST'
                  % (controlled, self.MOB))]
        analysis = self._run(lines)[0].analysis
        self.assertIn("Player-9999-00000005", analysis.players)
        self.assertEqual(analysis.total_damage, 5000)

    def test_a_group_member_who_steps_out_is_still_the_groups(self):
        """The owner's night: a cross-faction member who left the group at
        the end of a key was written outside and hostile (0x548), then in
        the party again. A first version of the opponent rule then dropped
        every later cast of theirs."""
        member = 'Player-9999-00000006,"Galet-Dalaran-EU",0x512,0x0'
        outside = member.replace("0x512", "0x548")
        lines = [(1000, 'SPELL_DAMAGE,%s,%s,1,"Frappe",0x1,5000,5000,-1,1,0,0,0,nil,nil,nil,ST'
                  % (member, self.MOB)),
                 (2000, 'SPELL_CAST_SUCCESS,%s,%s,2,"Bouclier",0x8' % (outside, self.NOBODY)),
                 (3000, 'SPELL_CAST_SUCCESS,%s,%s,2,"Bouclier",0x8' % (member, self.NOBODY))]
        analysis = self._run(lines)[0].analysis
        self.assertEqual(analysis.players["Player-9999-00000006"].casts, 2)
        self.assertNotIn("Galet", analysis.enemies)

    def test_no_french_is_left_on_a_page_in_another_language(self):
        """Four texts reached the page in French whatever the language: a
        pull's "et 3 autre(s)", a school breakdown's "autres", a healer's
        "autres" targets and the footer's "aucun"/"absent"."""
        healer = 'Player-9999-00000002,"Tisane-Dalaran-EU",0x512,0x0'
        lines = [(0, 'SPELL_DAMAGE,%s,%s,1,"Frappe",0x1,10,10,-1,1,0,0,0,nil,nil,nil,ST'
                  % (healer, self.MOB))]
        schools = (1, 2, 4, 8, 16, 32, 64, 3)
        for index, school in enumerate(schools):     # eight names, eight schools, one pull
            mob = 'Creature-0-9999-2222-1111-7100%d-00000000C%d,"Ennemi%d",0xa48,0x0' % (
                index, index, index)
            lines.append((100 + index, 'SPELL_DAMAGE,%s,%s,1,"Frappe",0x1,5000,5000,-1,%d,'
                          '0,0,0,nil,nil,nil,ST' % (self.PLAYER, mob, school)))
        for index in range(70):           # more targets than a healer's table keeps
            target = 'Player-9999-%08d,"Joueur%d-Dalaran-EU",0x512,0x0' % (100 + index, index)
            lines.append((200 + index, 'SPELL_HEAL,%s,%s,2,"Soin",0x2,100,100,0,0,nil'
                          % (healer, target)))
        # A second pull, so that the page draws its table of pulls.
        lines.append((30000, 'SPELL_DAMAGE,%s,%s,1,"Frappe",0x1,5000,5000,-1,1,0,0,0,'
                      'nil,nil,nil,ST' % (self.PLAYER, self.MOB)))
        segments = self._run(lines)
        self.assertEqual(len(segments[0].analysis.blocks), 2)
        for language, words in (("en", ("autre", "aucun")),
                                ("de", ("autre", "aucun", "absent")),
                                ("es", ("autre", "aucun", "absent"))):
            page = self._page(segments, language)
            text = re.sub(r"<[^>]+>", " ", page)
            for word in words:
                with self.subTest(language=language, word=word):
                    self.assertNotIn(word, text)

    def test_a_file_size_is_written_the_same_way_everywhere(self):
        """The window divided by 1,000,000 and the page, `diagnose` and
        `where` by 1,048,576: one log read 364,4 Mo in one and 347,5 Mo in
        the others."""
        from logswow import fmt
        from logswow.diagnose import run as diagnose

        self.assertEqual(fmt.size(364388746), "364,4 Mo")
        self.assertEqual(fmt.size(364388746, " "), "364,4 Mo")
        log, segments = run_fixture()
        size = os.path.getsize(FIXTURE)
        self.assertIn(fmt.size(size), self._page(segments))
        self.assertIn(fmt.size(size, " "), diagnose(FIXTURE))

    def test_quiet_says_what_it_does(self):
        out = io.StringIO()
        with contextlib.redirect_stdout(out), self.assertRaises(SystemExit):
            cli_main(["report", "--help"])
        self.assertIn("seulement les erreurs", " ".join(out.getvalue().split()))


if __name__ == "__main__":
    unittest.main(verbosity=2)
