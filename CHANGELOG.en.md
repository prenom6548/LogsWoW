# Changelog

What each published version changed, for those who use it. This English
changelog starts with 0.9.0, the first version to speak English; earlier
versions are described in French in [`CHANGELOG.md`](CHANGELOG.md), and
the technical detail, dated and measured, is in the dated sections of
`CLAUDE.md`.

## 0.15.0 — 2026-10-02

**A preview in the window, before the page is written.** Under the list
of fights, three tabs follow what you tick: *Overview* (length, damage,
healing, deaths, and a line per player), *Keys* (the comparison, below)
and *Gear*. You see what the report would say, and only write the page
if you want to go further.

**Compare two keys of the same dungeon and level**, in the window and on
the page ("Comparison of keys", under the list of fights), with, for the
group and for each player: **damage per second**, **healing per second**
(shields included, as the online sites do), deaths, and for the **tank**
**damage taken per second** (what shields absorbed counts). The change is
the last key against the first. Only finished keys are compared; an
abandoned key or one of another level stays apart.

**The players' gear, in each fight's summary.** The group's average item
level and, folded under the composition, everyone's gear: slot, level,
enchantments, gems. The log gives each item's number and level, never
its name, icon or stats: those come from the game's item database, which
LogsWoW does not have (it connects to nothing). Each item is therefore a
number with a Wowhead link, followed only if you click it. The average
follows the game's formula (sixteen slots, shirt and tabard left out, a
two-handed weapon counted twice). Read on 420 lines of five logs:
eighteen slots every time. No other figure changes.

## 0.14.0 — 2026-09-29

**Melee swings taken, for the tank above all.** The panel of every
player the enemy swung at ten times or more has a new section: how many
swings hit (critical ones among them), how many were fully absorbed,
parried, dodged, missed or blocked, and the share avoided. All of that
the log writes.

It also gives the share of the swings that landed which **came from
behind**. There the log says nothing: LogsWoW infers it from the
attacker's position and the player's facing, which the log gives line
by line. It is a reliable estimate, not something the log writes, and
limited to melee; the page says so, with a check on the fight itself:
the game allows no parry or dodge of a swing from behind, and on the
owner's four keys of 29 September, 97 to 98% of the tank's parries and
dodges do fall in front. The same tank took 24 to 34% of their hits
from behind, depending on the key. No other figure changes.

## 0.13.1 — 2026-09-29

**The window's progress bar can be seen, and says the time left.** It
did move, but on Linux the window's theme drew it light grey on a grey
background, and it emptied the moment the read ended: it looked broken.
It is blue now, stays full once the read or the report is done, and
follows the actual position in the file rather than an estimate per
line. Below it, the status line gives the percentage and the time left:
"Reading… 36%, 401,409 lines read, about 30 s left". On the owner's
364 MB log the estimate said 45 s four seconds in, for 46 s real, and was
never more than 3 s off. The report itself is written in a second or
two, so it has no countdown.

## 0.13.0 — 2026-09-29

The full audit of 0.12.1, checked on your 364 MB log of 29 September.

**Fix: the pauses of a player with a pet were hidden.** Every spell a
pet, a summon or a totem cast ended its owner's pause: a hunter who cast
nothing for forty seconds while the pet bit every second showed zero
seconds without action. Only the player's own spells now count for
"Time without action" and the longest pauses; their summons' spells are
still counted, apart, among the spells cast. On your log, 14 players of
25 change; the most affected goes from 283 s to 458 s without action on
one key.

**Fix: in PvP, the opponent was counted in the group.** In an arena or a
battleground, the log writes the players of the other side outside the
group and hostile; they were treated as teammates: the opponent stood in
the ranking, every blow exchanged counted as one taken from an ally, and
the damage dealt stayed at zero. They are now enemies, with their pets,
their casts (which an interrupt can cut) and their deaths. A group
member under a mind control, or who steps out of the group for a moment,
stays in the group. Matches are not cut out yet. On your dungeon log, no
figure moves.

**Some words stayed French in the English, German and Spanish reports**:
"et 3 autre(s)" in the table of pulls, "autres" in the breakdown by
school and among a healer's targets, "aucun" and "absent" at the foot of
the page and in `diagnose`, "Mo" in `where`. All are translated.

**A file size is written the same way everywhere.** The window counted a
megabyte as a million bytes; the page, `diagnose` and `where` as
1,048,576: the same log read 364.4 MB in one and 347.5 MB in the others.
It is a million bytes everywhere now, as the unit's name says and as a
Linux file manager shows it. `diagnose` also writes its numbers in your
language's style ("1,121,188 lines").

**Less memory to write the report.** The page was assembled whole in
memory, several times over, before being written; it now goes to disk
one fight at a time. On your log: 252 MB → 89 MB at the peak for the
tabbed layout, 149 MB → 88 MB for the long page. The page written is the
same to the byte.

Smaller: `-q` has its help line; the tests also pass on Python 3.14.

## 0.12.1 — 2026-09-29

**Fix: the "in time" threshold was too strict from +2 to +11.** The
0.12.0 rule, 15 × level + 185, was right from +12 up but asked 15 to 30
points too many below: a timed +10 scoring 330 would have read "over
time". The threshold is now the base score Raider.IO publishes for every
level from +2 to +30: 125 + 15 × level, plus 15 at each affix step (+4,
+7, +10 and +12), so 320 for a +10 and 335 for a +11 (+12 and above do
not change). No key in the owner's logs changes verdict, but a Murder
Row +10 in 19:16, at exactly 335 points, passed only by a tie. The
season's timers, as Raider.IO's API gives them, confirm all 14 verdicts
of those logs.

## 0.12.0 — 2026-09-29

**Fix: "in time" was wrong for a key finished late.** A Val Aveuglant +13
completed in 30:23 read "in time". The log writes, when a key ends, a
flag that means "completed", not "timed", and it never writes the
dungeon's time limit. What tells them apart is the score the game gives
the key: at least 15 × level + 185 in time (380 for a +13), less when
late. The owner's two Val Aveuglant +13: 383.2 in 27:26 (in time), 319.5
in 30:23 (over time). Of 15 completed keys, the 14 timed ones are all
above the threshold; if a verdict looks wrong, say which key. A key from
an older log, with no score, is only "completed".

**Pulls in the list on the left.** Each key is now folded there behind a
small "+". Unfolded, it shows its pulls and bosses in the order they
were played ("Pull 1", "Pull 2", the boss, "Pull 4"…), numbered as in
the pull table. Each trash pull opens like a boss, with its own detail:
damage, healing, deaths, players, enemies (the cast order stays in the
key's view, pull by pull). Clicking the key's name selects it, the "+"
unfolds it. The folder of pages has a page per pull too; the long page
does not change.

These views have a cost, measured on a 364 MB log: 35 s → 45 s, 13 → 20
MB of page, 163 → 249 MB of peak memory. Every figure of the fights is
identical to 0.11.0, and each pull counts exactly the same damage as its
row in the key's table (checked on 143 pulls of five logs).

## 0.11.0 — 2026-09-29

**The first hit each enemy took**, pull by pull, bosses included: for
each monster, the player who touched it first (a missed hit counts too,
it draws the monster just the same), with which spell and when in the
pull. A pet's, a summon's or a totem's spell counts for its master. The
log writes this as such: it is certain. The list unfolds under each row
of the pull table, and under the heading of a boss fight on its own.

**Who opened each pull.** Under each row of the pull table, the first
act linking the group and an enemy since the previous pull ended:
"Opened by Tisane (tank): Death Grip, 0.4 s before the first hit". A
pet's, a summon's or a totem's spell counts for its master, and the
player's role is written beside their name. The log has no threat line:
an enemy drawn by proximity (a body pull) only shows in what it does
next, and the line then says "Golem acted first, on Braise", marked
**beta** until players have said how it reads. Since a heal, a buff or
a dispel given in combat draws the enemy towards whoever gave it, it
adds, when that is the case, that this target had just helped another
player, and which one: that player is often the puller.
Facts, no verdict: a ground effect left by the previous pack can also
make an enemy act first.

Measured on three real dungeon logs (159 pulls): the tank opens most
pulls, typically 0.3 to 0.6 s before the first hit; the enemy acts
first in about one pull in six.

**A pull ends after 3 seconds without damage**, instead of 6: closer to
what a group does in the game. `--pull-gap` and the window's setting
still let you choose another. Totals do not change; only the cutting
into pulls is finer.

## 0.10.0 — 2026-09-28

**LogsWoW speaks German and Spanish too.** The window, the commands,
`diagnose` and the report now exist in four languages. The choice is
still automatic (your machine's language, English for one with no
translation); `--langue de` or `--langue es` forces one. Each language
writes its numbers its own way: "25,4 Mio." and "25.361.906" in German,
"25,4 M" and "45,6 mil" in Spanish. The translations were written with
care but have not yet been reviewed by native-speaking players: a term
that sounds wrong can be reported, and it is a one-line fix.

**The decimal comma in French.** "25,4 M" and "180,6 Mo" instead of
"25.4 M" and "180.6 Mo", everywhere.

**Abandoned keys are recognised.** A key restarted, or left for another,
was counted "over time"; it is now "abandoned". Before every new key the
game writes an empty end (no level, no time) that closes the one still
open. A new tile at the top of the report, **Unfinished keys**, counts
those keys and the one the log leaves open ("cut short").

**The "Reattributed" column**, in the damage ranking, whenever a fight
contains an Evoker's support lines: each player's damage, minus the part
the game credits to an Evoker's buffs (Ebon Might, Prescience,
Bombardments…), plus what it credits to them. This is Warcraft Logs'
reattribution, and the only kind of "aDPS" the log allows: it never
writes what a Bloodlust or a Power Infusion added to other players'
hits. The column sits beside the total rather than replacing it, and the
group's total does not change.

**Fix.** In English, the file size read "Mo"; it is "MB".

Nothing else changes: on five logs (three of them real), not one number
moves apart from the two abandoned keys, and the four languages give
exactly the same numbers. The speed is the same.

## 0.9.0 — 2026-09-28

**LogsWoW speaks English too.** The window, the commands, `diagnose` and
the report now exist in French and in English. The language chooses
itself: your machine's, and English for any language that has no
translation yet. To force one:

- `--langue en` or `--langue fr`, before or after the command;
- or the `LOGSWOW_LANGUE` environment variable, for a standing choice.

Each language writes its numbers its own way ("25,361,906" and "46%",
"25 361 906" and "46 %"), and its dates too. Spell, boss and player names
stay as the log wrote them, in your game client's language.

The README and the installation guide have their English versions
(`README.en.md`, `INSTALL.en.md`), and so does this changelog.

Nothing else changes. In French, the pages are identical to those of
0.8.1, character for character. In English, the numbers are exactly the
same: checked on five logs, three of them real, more than a million
numbers in all. The speed is the same too.
