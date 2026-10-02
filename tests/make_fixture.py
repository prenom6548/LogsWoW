#!/usr/bin/env python3
# SPDX-License-Identifier: AGPL-3.0-or-later
"""Write examples/exemple-combat.txt: a small, fabricated combat log.

**Nothing here comes from anybody's real log.** The names are invented,
the numbers are made up, and the file exists so the tests have something
to assert against that can live in a public repository. Real logs carry
the names of everyone who was in the group, which is exactly the kind of
thing this project exists to keep on one machine.

The shapes, on the other hand, are real: they follow what two 12.1.0
logs were measured to contain (a 19-field advanced block, a baseAmount
before overkill), plus the awkward cases a reader has to survive --
a line with no advanced block, an unknown event, a malformed line, and
a pull that crosses midnight.
"""

import os

# 19 fields, counted against a real 12.1.0 line:
#   infoGUID, ownerGUID, currentHP, maxHP, attackPower, spellPower, armor,
#   absorb, ?, ?, powerType, currentPower, maxPower, powerCost, posX, posY,
#   uiMapID, facing, level
# The two unnamed fields are the ones Blizzard added after the documented
# seventeen; this package reads the block from both ends so it never has to
# know what they are.
ADVANCED = "{info},{owner},{hp},{maxhp},1500,420,830,240,0,0,1,1100,1300,0,{x},{y},2393,3.14,80"


def equipment(ilvl, off_hand=False, missing=()):
    """The equipment field: 18 slots from `ilvl`, each a little above the last.

    Slot 16 (off hand) stays empty unless `off_hand`; the slots in `missing` are empty.
    Item ids are fabricated (900000 and up).
    """
    slots = []
    for slot in range(18):
        if slot in missing or (slot == 16 and not off_hand):
            slots.append("(0,0,(),(),())")
            continue
        enchants = "(7000)" if slot in (4, 8, 11) else "()"
        gems = "(213743,619)" if slot == 2 else "()"
        slots.append("(%d,%d,%s,(),%s)" % (900000 + slot, ilvl + slot, enchants, gems))
    return "[" + ",".join(slots) + "]"


def advanced(info, hp=100000, maxhp=100000, owner="0000000000000000", x="100.5", y="-200.5"):
    return ADVANCED.format(info=info, owner=owner, hp=hp, maxhp=maxhp, x=x, y=y)


TANK = 'Player-9999-00000001,"Ardoise-Dalaran-EU",0x511,0x0'
HEALER = 'Player-9999-00000002,"Tisane-Dalaran-EU",0x512,0x0'
DPS = 'Player-9999-00000003,"Braise-Dalaran-EU",0x514,0x0'
PET = 'Pet-0-9999-2222-1111-00004,"Cendre",0x1114,0x0'
BOSS = 'Creature-0-9999-2222-1111-70000-0000111111,"Golem d\'essai",0xa48,0x0'
ADD = 'Creature-0-9999-2222-1111-70001-0000222222,"Eclat d\'essai",0xa48,0x0'

TANK_GUID = "Player-9999-00000001"
HEALER_GUID = "Player-9999-00000002"
DPS_GUID = "Player-9999-00000003"
PET_GUID = "Pet-0-9999-2222-1111-00004"
BOSS_GUID = "Creature-0-9999-2222-1111-70000-0000111111"


def build():
    lines = []

    def add(time_text, payload):
        # A real client writes the new date itself once the clock passes
        # midnight, so the fixture does too: the pulls below run from
        # 23:59 on the 18th into the small hours of the 19th.
        day = 19 if time_text.startswith("00:") or time_text.startswith("01:") \
            or time_text.startswith("02:") else 18
        lines.append("9/%d/2026 %s  %s" % (day, time_text, payload))

    add("23:59:00.000",
        "COMBAT_LOG_VERSION,22,ADVANCED_LOG_ENABLED,1,BUILD_VERSION,12.1.0,PROJECT_ID,1")
    add("23:59:00.100", 'ZONE_CHANGE,2000,"Salle d\'essai",23')

    # -- pull 1: a clean kill, with a pet and an interrupt ---------------
    add("23:59:01.000", 'ENCOUNTER_START,9001,"Golem d\'essai",16,3,2000')
    # Specializations, so the report can say who tanked and who healed.
    # Field 25 is the current spec id; the rest is padding of the right
    # shape, not real stats.
    # Field 28 is the equipment: eighteen (item, ilvl, (enchants), (bonus), (gems)) in slot
    # order. The ids are invented. The tank wears a shield (a one-hander and an off hand),
    # the healer a two-handed staff and an empty off hand, the DPS has no neck and no ring.
    for guid, spec, gear in ((TANK_GUID, 73, equipment(600, off_hand=True)),
                             (HEALER_GUID, 257, equipment(610)),
                             (DPS_GUID, 1480, equipment(620, missing=(1, 10)))):
        add("23:59:01.050", "COMBATANT_INFO,%s,1,%s,%d,[],[],%s,[],0"
            % (guid, ",".join(["0"] * 22), spec, gear))
    add("23:59:01.100", "SPELL_SUMMON,%s,%s,777,\"Invocation\",0x1" % (DPS, PET))
    # buff applied on the tank, removed 10 s later: 10 s of uptime
    add("23:59:01.200", 'SPELL_AURA_APPLIED,%s,%s,111,"Peau de pierre",0x1,BUFF' % (TANK, TANK))
    # damage done, both layouts: SPELL (11-field suffix) and SWING (10)
    for offset in range(6):
        add("23:59:%02d.000" % (2 + offset),
            'SPELL_DAMAGE,%s,%s,222,"Frappe d\'essai",0x1,%s,5000,7000,-1,1,0,0,0,nil,nil,nil,ST'
            % (DPS, BOSS, advanced(BOSS_GUID, 100000 - offset * 10000)))
        add("23:59:%02d.500" % (2 + offset),
            'SWING_DAMAGE,%s,%s,%s,900,1200,-1,1,0,0,0,nil,nil,nil'
            % (TANK, BOSS, advanced(BOSS_GUID, 95000 - offset * 10000)))
        # The same swing, written twice, exactly as a real client writes it:
        # the total must count it once.
        add("23:59:%02d.500" % (2 + offset),
            'SWING_DAMAGE_LANDED,%s,%s,%s,900,1200,-1,1,0,0,0,nil,nil,nil'
            % (TANK, BOSS, advanced(BOSS_GUID, 95000 - offset * 10000)))
        add("23:59:%02d.700" % (2 + offset),
            'SPELL_DAMAGE,%s,%s,333,"Morsure",0x1,%s,700,700,-1,1,0,0,0,nil,nil,nil,ST'
            % (PET, BOSS, advanced(BOSS_GUID, 94000 - offset * 10000)))
    # the boss hits the tank, the healer heals it back
    add("23:59:04.000",
        'SPELL_DAMAGE,%s,%s,444,"Balayage",0x4,%s,30000,45000,-1,4,0,0,2000,1,nil,nil,AOE'
        % (BOSS, TANK, advanced(TANK_GUID, 70000, 100000)))
    add("23:59:04.500",
        'SPELL_HEAL,%s,%s,555,"Vague apaisante",0x2,%s,25000,30000,5000,0,1'
        % (HEALER, TANK, advanced(TANK_GUID, 95000, 100000)))
    # an event with no advanced block at all, to prove detection is per line
    add("23:59:05.000", 'SPELL_AURA_APPLIED,%s,%s,666,"Marque",0x20,DEBUFF' % (BOSS, DPS))
    # An enemy cast that gets kicked, and one that lands: the two outcomes
    # the report counts.
    add("23:59:05.200", 'SPELL_CAST_START,%s,%s,999,"Incantation",0x20' % (BOSS, TANK))
    add("23:59:05.500", 'SPELL_INTERRUPT,%s,%s,888,"Coup de bouclier",0x1,999,"Incantation",0x20'
        % (TANK, BOSS))
    add("23:59:06.000", 'SPELL_CAST_START,%s,%s,1001,"Long sort",0x20' % (BOSS, TANK))
    add("23:59:08.000", 'SPELL_CAST_SUCCESS,%s,%s,1001,"Long sort",0x20,%s'
        % (BOSS, TANK, advanced(BOSS_GUID, 60000)))
    # A dispel, so a healer's panel has something beyond healing.
    add("23:59:08.500", 'SPELL_DISPEL,%s,%s,1002,"Purification",0x2,666,"Marque",0x20,DEBUFF'
        % (HEALER, DPS))
    # A second healing target, so "who was healed" has more than one row.
    add("23:59:09.000",
        'SPELL_HEAL,%s,%s,555,"Vague apaisante",0x2,%s,4000,4000,1000,0,nil'
        % (HEALER, DPS, advanced(DPS_GUID, 90000, 100000)))
    add("23:59:11.200", 'SPELL_AURA_REMOVED,%s,%s,111,"Peau de pierre",0x1,BUFF' % (TANK, TANK))
    # a killing blow: overkill positive rather than -1
    add("23:59:12.000",
        'SPELL_DAMAGE,%s,%s,222,"Frappe d\'essai",0x1,%s,9000,9000,3000,1,0,0,0,1,nil,nil,ST'
        % (DPS, BOSS, advanced(BOSS_GUID, 0)))
    add("23:59:12.100", "PARTY_KILL,%s,%s,0" % (DPS, BOSS))
    add("23:59:12.200", "UNIT_DIED,0000000000000000,nil,0x80000000,0x80000000,%s,0" % BOSS)
    add("23:59:13.000", 'ENCOUNTER_END,9001,"Golem d\'essai",16,3,1,12000')

    # -- a line the reader must survive rather than trip on --------------
    lines.append("ceci n'est pas une ligne de journal")
    add("23:59:14.000", "EVENEMENT_INCONNU,quelque,chose,1,2,3")
    add("23:59:14.500", "STAGGER_CLEAR,%s,1234.5" % TANK_GUID)

    # -- pull 2: crosses midnight, and someone dies ----------------------
    add("23:59:50.000", 'ENCOUNTER_START,9002,"Eclat d\'essai",16,3,2000')
    add("23:59:52.000",
        'SPELL_DAMAGE,%s,%s,222,"Frappe d\'essai",0x1,%s,4000,4000,-1,1,0,0,0,nil,nil,nil,ST'
        % (DPS, ADD, advanced("Creature-0-9999-2222-1111-70001-0000222222", 50000, 60000)))
    add("23:59:55.000",
        'SPELL_DAMAGE,%s,%s,444,"Balayage",0x4,%s,40000,40000,-1,4,0,0,0,1,nil,nil,AOE'
        % (ADD, HEALER, advanced(HEALER_GUID, 20000, 60000)))
    add("00:00:01.000",
        'SPELL_DAMAGE,%s,%s,444,"Balayage",0x4,%s,25000,25000,5000,4,0,0,0,1,nil,nil,AOE'
        % (ADD, HEALER, advanced(HEALER_GUID, 0, 60000)))
    add("00:00:01.100", "UNIT_DIED,0000000000000000,nil,0x80000000,0x80000000,%s,0" % HEALER)
    add("23:59:51.000", 'SPELL_CAST_SUCCESS,%s,%s,222,"Frappe d\'essai",0x1,%s'
        % (DPS, ADD, advanced(ADD.split(",")[0])))
    # ...then nothing for forty seconds, which is the whole point of the
    # downtime column.
    add("00:00:30.000", 'SPELL_CAST_SUCCESS,%s,%s,222,"Frappe d\'essai",0x1,%s'
        % (DPS, ADD, advanced(ADD.split(",")[0])))
    add("00:00:31.000", 'ENCOUNTER_END,9002,"Eclat d\'essai",16,3,0,41000')

    # -- a key with two trash packs, separated by a real silence ---------
    # This is what makes the pull table mean anything: one segment that
    # contains several distinct fights rather than one long total.
    add("00:01:00.000", 'CHALLENGE_MODE_START,"Donjon d\'essai",2000,500,7,[165,162]')
    for index, guid_tail in enumerate(("0000AA0001", "0000AA0002")):
        mob = ('Creature-0-9999-2222-1111-70002-%s,"Sbire d\'essai",0xa48,0x0' % guid_tail)
        for tick in range(3):
            add("00:01:%02d.000" % (5 + index * 2 + tick),
                'SPELL_DAMAGE,%s,%s,222,"Frappe d\'essai",0x1,%s,3000,3000,-1,1,0,0,0,'
                "nil,nil,nil,AOE"
                % (DPS, mob, advanced("Creature-0-9999-2222-1111-70002-%s" % guid_tail,
                                      30000 - tick * 10000, 30000)))
    # forty seconds of nothing at all, then a second pack
    for tick in range(2):
        mob = 'Creature-0-9999-2222-1111-70003-0000BB0001,"Brute d\'essai",0xa48,0x0'
        add("00:02:%02d.000" % (5 + tick),
            'SPELL_DAMAGE,%s,%s,222,"Frappe d\'essai",0x1,%s,8000,8000,-1,1,0,0,0,'
            "nil,nil,nil,ST"
            % (DPS, mob, advanced("Creature-0-9999-2222-1111-70003-0000BB0001",
                                  60000 - tick * 30000, 60000)))
    add("00:02:30.000", "CHALLENGE_MODE_END,2000,1,7,90000,300.000000,3000.000000")
    return "\n".join(lines) + "\n"


def main():
    here = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    target = os.path.join(here, "examples", "exemple-combat.txt")
    os.makedirs(os.path.dirname(target), exist_ok=True)
    with open(target, "w", encoding="utf-8") as handle:
        handle.write(build())
    print("ecrit : %s" % target)


if __name__ == "__main__":
    main()
