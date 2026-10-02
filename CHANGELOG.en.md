# Changelog

What each published version changed, for those who use it. This English
changelog starts with 0.9.0, the first version to speak English; earlier
versions are described in French in [`CHANGELOG.md`](CHANGELOG.md), and
the technical detail, dated and measured, is in the dated sections of
`CLAUDE.md`.

## 0.20.1 — 2026-10-02

A version that comes from a full audit of everything added since 0.12.1
(progress bar, melee swings, gear, preview, the history and its views, the
history page).

**A log read twice counted twice.** During an evening, the game writes into
the same file: read at 9 pm and again at 11 pm, the log has grown, and the
history kept two nights instead of one (automatically, with the automatic
saving switched on). On one of the owner's logs read that way, 15 runs out of
25 were counted twice in the progress view, the specializations' medians and
the records. Reading a log again now **updates** its night. Duplicates
already saved by versions 0.16.0 to 0.20.0 count once in the views, and the
most complete read wins (a key cut short by the first read gives way to the
same key finished). The same goes for a split file ("Split") of a night
already kept whole. You can delete the duplicate nights from the list if you
wish; they no longer skew anything.

**Other fixes:**

- A system file left in a history folder (the Mac Finder's `.DS_Store`,
  Windows' `Thumbs.db` or `desktop.ini`) prevented deleting that folder. It
  is now deleted with it; a file of yours still blocks the deletion.
- A damaged list of followed characters (`suivi.json`) crashed the history
  window. It is now read as empty, and written again.
- Updating a night kept in a folder other than the active one named the
  wrong folder.
- Two followed characters with the same name (on two realms) had the same
  label in the lists and on the page: the second is now "Name (2)".
- A role saved with an unexpected type no longer stops a view.

No figure of a report changes.

## 0.20.0 — 2026-10-02

**The history as a web page.** The three views of the "History" window
(a character's progress, specializations against each other, records) can
also be written as an HTML page: the **"Write the page…"** button of the
window, or the command `logswow historique` (`--dossier` to choose the
folder, `-o` for the file). The page opens in the browser.

It follows the rules of every report: **no script, nothing fetched**, one
file. Three tabs (Progress, Specializations, Records) and a choice of
character ("all followed characters" or one of them) work without a script,
like the tabs of the reports. The progress view shows one character content
by content, with its curve and its runs; specializations are compared role by
role, with bars starting at zero; the records give each specialization's best
key and best kill. **The figures are not recomputed for the page**: they are
the same rows as in the window, with the same notes under the tables (median,
‡, "not a ranking"). It exists in French, English, German and Spanish, and
follows the dark theme like the reports.

It is a page of its own, not a part of a log's report: a report is made from
that one log and is meant to be shared, while the history spans several nights
and carries the names of your followed characters. The page never overwrites a
file that is not a LogsWoW page (unless `--force`), nor anything inside the
history folder itself.

Fixed along the way, found by fuzzing the history's files: a damaged night
file (an infinite number, a date as a list, a field of another type) could stop
a list or a view. It no longer stops anything. No existing figure changes.

### Also in this release

These versions never had a release of their own: their notes are gathered here, so that nothing that changed is missing.

#### 0.18.0

**One specialization against another, in the "History" window.** A new tab,
*Specializations*, answers "how does this specialization do against that
one?" with the runs of the history. It works on one followed character, or on
all those of the folder, **one role at a time**: a tank's damage beside a mage's
is not a comparison of specializations.

As with the progress view, **only the same content is compared**: the same
dungeon at the same key level, the same boss at the same difficulty, and only
the runs that count (finished keys, killed bosses). The list on the left keeps
only the content played with at least two specializations; choosing one gives,
for each specialization, the number of runs, the **median** (one extreme run
does not skew it), the range from minimum to maximum, the item level and the
gap to the first row, with a bar chart of the medians (starting at zero, so a
small difference is not magnified). The measure opens on the role played most
(damage taken/s for tanks, healing/s, damage/s); damage taken is given to
tanks only, so two tank specializations are needed to compare it.

It is not a ranking: the first row is the most played, not the best, and the
gap depends on item level, players and group, which the tab says. A row backed
by fewer than three runs is marked ‡. Nothing disappears quietly: content
played with a single specialization, and runs whose specialization the log does
not write, are counted under the table. The role is now read from the
specialization first, which fixes runs whose id was not known when they were
saved. No existing figure changes.

#### 0.16.0

**The history: keeping your nights to compare yourself.** A "History…" button
opens a window to build, night after night, the history of your characters. On
first use it explains the idea and has you create a first folder, named however
you like (a season, "with my friends"…); a menu lets you create, rename or
delete others at any time, and move a night from one to another.

**Nothing is saved without your consent.** You tick the characters to follow:
only they leave their name in the history; other players (a pick-up group, for
example) appear only in the group totals. "Add this night to the history" saves
it on request; a checkbox, off by default, saves every log read, but only if a
followed character played in it. Each night is a small readable file (about 30 KB:
the figures LogsWoW computed, never the log's events), kept on this computer only.
Deleting a night or a whole folder is one click, and never touches your combat logs.

A key is kept whole, with each of its pulls (length, damage, deaths and the
average health of the enemies engaged) and its bosses; a raid boss is kept with
its difficulty and, if it did not fall, its remaining health. Raid trash is not
kept.

When the game version changes between two logs (a new patch, a new expansion),
the window offers to start a new folder: the log does not say the season, only
the client's version, and you decide. No existing figure changes.

#### 0.4.0

**The window, so that the terminal is no longer needed.** Launched with nothing else (a double-click on the file on Windows), LogsWoW opens a window in three steps: the log, the fights, the report ("Create the report and open it" shows it in the browser). A large log is followed on a progress bar and can be cancelled; if the log's folder refuses writing, or a file of the same name that is not a report exists, the window asks where to write rather than overwrite anything. The terminal commands do not change; `fenetre` opens the window from the terminal. On Linux Mint, Ubuntu and Debian the window asks once for `sudo apt install python3-tk`, and says so itself if it is missing.

## 0.19.0 — 2026-10-02

**The best of each specialization, in the "History" window.** A new tab,
*Records*, gives for each specialization its **best key** and its **best
kill**, for one followed character or for all those of the folder.

*Best key*: the highest key finished **in time**; at equal level, the best
score, then the shortest time. A key finished out of time only comes first if
the specialization has none in time (the "In time" column says so, and "Keys"
counts the keys in time out of the keys finished). *Best kill*: the fastest of
one raid boss at the same difficulty, boss by boss (a three-minute fight and an
eight-minute one do not belong in the same table); bosses met inside a key
belong to the key.

Each record keeps its context beside it: the dungeon or boss, the date, the
character, the item level, the group (tanks / healers / dps) and the figure of
the role (damage/s, healing/s, or damage taken/s for a tank). Rows are ordered
by role, then by name, never "best first": these are each specialization's
records, not a ranking of the specializations, and not a parse (a kill's time
depends on the group as much as on the specialization). Runs whose
specialization the log does not write are counted under the tables. No existing
figure changes.

## 0.18.0 — 2026-10-02

*Never published on its own: its notes are gathered in those of 0.20.0.*

**One specialization against another, in the "History" window.** A new tab,
*Specializations*, answers "how does this specialization do against that
one?" with the runs of the history. It works on one followed character, or on
all those of the folder, **one role at a time**: a tank's damage beside a mage's
is not a comparison of specializations.

As with the progress view, **only the same content is compared**: the same
dungeon at the same key level, the same boss at the same difficulty, and only
the runs that count (finished keys, killed bosses). The list on the left keeps
only the content played with at least two specializations; choosing one gives,
for each specialization, the number of runs, the **median** (one extreme run
does not skew it), the range from minimum to maximum, the item level and the
gap to the first row, with a bar chart of the medians (starting at zero, so a
small difference is not magnified). The measure opens on the role played most
(damage taken/s for tanks, healing/s, damage/s); damage taken is given to
tanks only, so two tank specializations are needed to compare it.

It is not a ranking: the first row is the most played, not the best, and the
gap depends on item level, players and group, which the tab says. A row backed
by fewer than three runs is marked ‡. Nothing disappears quietly: content
played with a single specialization, and runs whose specialization the log does
not write, are counted under the table. The role is now read from the
specialization first, which fixes runs whose id was not known when they were
saved. No existing figure changes.

## 0.17.0 — 2026-10-02

**The evolution of a character, in the "History" window.** A new tab,
*Progress*, shows one of the characters you follow, run after run. The
results are grouped **by content**: a dungeon and a key level, or a boss and
a difficulty. A +12 is never compared with a +13, nor a kill with a wipe: that
would make the figures say what they do not.

For each content: the number of runs, the first and the last value, the change
(the last run against the first), the item level at the start and at the end,
and a curve. The measure opens on what matters for the character's role
(**damage taken/s** for a tank, **healing/s** for a healer, **damage/s** for a
dps) and changes in one click; you can also show only keys or only bosses. A
table lists every run with its context: date, level, outcome (with the
remaining health of a boss that was not killed), length, specialization, item
level, damage/s, healing/s, taken/s, deaths, the group's composition (tanks /
healers / dps) and the game's version.

It is never a grade. An abandoned or interrupted key and a boss that was not
killed stay listed (marked †) but do not enter the trend; the tab says when a
content mixes several specializations, or when runs come from a file computed
by an older version of LogsWoW. The other views (one specialization against
another, best key and best kill) will follow. No existing figure changes.

## 0.16.0 — 2026-10-02

*Never published on its own: its notes are gathered in those of 0.20.0.*

**The history: keeping your nights to compare yourself.** A "History…" button
opens a window to build, night after night, the history of your characters. On
first use it explains the idea and has you create a first folder, named however
you like (a season, "with my friends"…); a menu lets you create, rename or
delete others at any time, and move a night from one to another.

**Nothing is saved without your consent.** You tick the characters to follow:
only they leave their name in the history; other players (a pick-up group, for
example) appear only in the group totals. "Add this night to the history" saves
it on request; a checkbox, off by default, saves every log read, but only if a
followed character played in it. Each night is a small readable file (about 30 KB:
the figures LogsWoW computed, never the log's events), kept on this computer only.
Deleting a night or a whole folder is one click, and never touches your combat logs.

A key is kept whole, with each of its pulls (length, damage, deaths and the
average health of the enemies engaged) and its bosses; a raid boss is kept with
its difficulty and, if it did not fall, its remaining health. Raid trash is not
kept.

When the game version changes between two logs (a new patch, a new expansion),
the window offers to start a new folder: the log does not say the season, only
the client's version, and you decide. **The comparisons themselves (a
character's progress, one specialization against another, best key and best
kill) will come in a later version**: this one starts keeping the data. No
existing figure changes.

## 0.15.1 — 2026-10-02

**The window reads side by side, and the gear is simpler.** The fights are
on the left, and on the right the preview and the comparison of keys
(two tabs): you see what the report says without leaving the list. The
*Gear* tab is gone from the window: an item number tells a player
nothing. The item level stays, per player in the preview, and on the
page next to each name in the group's composition, with the group's
average. On the page, the gear detail keeps the slot, the item (a
Wowhead link) and the level; the enchantments and gems columns, which
only showed numbers, are removed.

**On the page, the comparison of keys becomes a tab** next to "Fights",
instead of being added below: the overview no longer grows. With no key
to compare, the page stays as it was. No figure changes.

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
