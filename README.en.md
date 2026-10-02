# LogsWoW

*Version française : [README.md](README.md) · Deutsche Fassung: [README.de.md](README.de.md) · Versión en español: [README.es.md](README.es.md)*

Read your own World of Warcraft combat logs **on your own machine**: no
account, no upload, no connection.

The game itself writes a file, `WoWCombatLog.txt`, holding everything
that happened during a fight. Online analysis sites read that file once
you have sent it to them. LogsWoW reads it where it is.

Started with nothing else — a double-click on the file, or
`python3 logswow-<version>.pyz` — it opens **a window**: you pick a log
from the list of those it found, tick the fights, and the report opens
in your browser. The same steps exist as commands, for those who prefer
the terminal:

```
python3 -m logswow report "/path/to/WoWCombatLog.txt"
```

An HTML page appears next to the file. It opens offline, loads nothing
from anywhere, and contains no script.

Three layouts to choose from, in the window or with `--format`:
**onglets** (the default: one file, the list of fights on the left and
tabs by section), **pages** (a folder, one page per fight) or **longue**
(everything on one page). The option values stay in French, as they
always were. In the list on the left, each key is folded behind a small
"+": unfolded, it shows its pulls and bosses in the order they were
played, and each trash pull opens like a boss, with its own detail
(everything but the cast order, which the key already shows pull by
pull). The long page does not have them.

The window uses Tkinter, the graphical toolkit that comes with Python.
On Windows and with the python.org installer for macOS it is already
there; on Linux Mint, Ubuntu and Debian it is installed once with
`sudo apt install python3-tk` (the window says so itself when it is
missing). The commands do not need it.

**English, French, German or Spanish.** The window, the commands and the
report speak your machine's language when LogsWoW knows it, English
otherwise. `--langue en`, `fr`, `de` or `es` forces one of them, and the
`LOGSWOW_LANGUE` environment variable sets a choice once and for all.
This README, the installation guide and the changelog exist in English,
French, German and Spanish.
Spell, boss and player names stay as the log wrote them, in your game
client's language.

## What you need first

**Step-by-step instructions for Windows, Linux (Linux Mint included) and
macOS are in [`INSTALL.en.md`](INSTALL.en.md).** Every published version
ships one single file, `logswow-<version>.pyz`, which runs as it is:
`python3 logswow-0.10.0.pyz report WoWCombatLog.txt`.

Nothing to install. Python 3.8 or newer, and that is all: no
`pip install`, no dependency, no network. The package is copied or
cloned, not installed; it deliberately has neither `pyproject.toml` nor
`setup.py`. The tests pass on Python 3.8 to 3.14; prefer a version that is
still maintained (3.10 or newer in 2026), older ones no longer receive
security fixes.

In the game, two settings, done once:

1. **Advanced combat logging** — System → Network → "Advanced Combat
   Logging". It stays on from one session to the next. It is what adds
   positions, health and resources to the file.
2. **`/combatlog`** in the chat to start recording. This one does not
   persist: type it again every session, or install a small addon that
   does it when you enter an instance.

The file is under `_retail_\Logs\`. On Linux it is inside the copy of
drive C that your launcher keeps (Lutris, Steam with Proton, Bottles,
Wine). To find it:

```
python3 -m logswow where
```

## The commands

| Command | What it does |
|---|---|
| *(none)* or `fenetre` | opens the window |
| `report FILE` | writes the full HTML page |
| | `--format onglets\|pages\|longue` the layout, `-o` the file name (the folder for `pages`), `--only` a single fight, `--pull-gap` how pulls are cut, `--wowhead` the language of the links, `--sans-sequence` without the cast order, `--force` to overwrite a file that is not a report |
| `list FILE` | lists the fights in the file, one line each |
| `diagnose FILE` | shows what the reader understood, and what it did not |
| `where` | looks for the game's `Logs` folder |
| *(all)* | `--langue en\|fr\|de\|es\|auto` the language of the interface and the report |

**Run `diagnose` first** after every game patch. It shows the field
layout as it was *measured in your file*, the list of events it met, and
every line it could not place. A confident combat report drawn from a
misread file would be worse than no report at all.

## What the report contains

- **The fights**: every boss pull and every Mythic+ key, with its
  duration, its outcome and its number of deaths. A key and the bosses
  inside it both appear. An encounter the game opens and closes without a
  single hit landing is called "no fight" and is not counted as a wipe.
- **The group's composition**, tanks, healers and DPS, with each one's
  class and specialization. They come from what the client writes at the
  start of the fight; a specialization the tool does not know is shown by
  its number rather than guessed.
- **A timeline** of the damage the group took, second by second, with a
  labelled scale on the left and deaths in red. As a curve, on a boss
  pull, the boss's health (named under the chart); in a key, **the pooled
  health of everything engaged**, the sum of current health over the sum
  of maximums, which rises with every pack and falls as it dies.
- **The list of pulls** as soon as a fight holds several, which every
  Mythic+ key does: start time, duration, what was engaged and how many,
  damage dealt, damage taken, deaths. A pull that holds a boss names it
  first, wears a badge with the encounter's outcome (kill in green, wipe
  in red), and splits **damage on the boss from damage on the trash**
  dragged along with it. An encounter's bounds come from the log itself:
  an encounter no unit is named after (a council, a duo) counts on the
  boss all the damage dealt while it lasted, and the page says so. A pull
  ends after three seconds without damage either way, except inside a boss
  encounter, which always stays one pull; `--pull-gap` changes that
  threshold if your group chains packs.
- **Who opened each pull**, under its row: the first act linking the
  group and an enemy since the previous pull ended, with the player,
  their role, the spell (a summon's counts for its master) and how long
  before the first hit. The log has no threat line: an enemy drawn by
  proximity only shows in what it does next, and the line then says
  "Golem acted first, on Tisane", marked **beta**. Since a heal, a buff or
  a dispel given in combat draws the enemy towards whoever gave it, it
  also says when that target had just given one, and to whom: that
  player is often the real puller. Facts, no verdict.
- **The first hit each enemy took** in each pull, bosses included, to
  unfold under its row: who touched it first (a missed hit counts), with
  which spell, at what moment. That one is certain: the log writes it as
  such.
- **Damage and healing** per player, with DPS, HPS and the share of
  healing lost to overhealing. **Shields** have their own column: what
  they absorbed is not a heal in the log, since they prevent damage
  instead of restoring health. The "Sum" column adds the two — that total
  is what the online sites call "healing". Damage counts what each hit
  really took off: not the excess of a killing blow, but indeed what an
  enemy's shield ate. Healing counts what a healing-absorb debuff ate,
  and Spirit Link, which moves health from one player to another, is
  neither healing nor damage taken.
- **Compared with Warcraft Logs** on five keys, player by player: the
  same deaths for all, the same damage within 0.1% (to the unit for half
  the players), the same healing to the unit for 17 players of 25. The
  remaining gaps have a known cause, written in `CHANGELOG.md`.
- **Spells cast** include those of summons, shown apart. The file writes
  a spell the game fires by itself exactly like one pressed by hand, so
  the count is higher than an online site's, which removes procs from a
  maintained list.
- **Damage the file credits to nobody**, when there is some: a friendly
  creature whose master the log never names cannot be tied to any
  player. It is left out of the total, and a box says so, with names and
  amounts — a silently short total would be worse.
- **An Augmentation Evoker's share**: the log credits their buffs (Ebon
  Might, Prescience…) with part of other players' hits, and them with the
  Bombardments an ally sets off. Those amounts are already in the damage
  of whoever dealt the hits: they are shown apart on the Evoker's panel,
  never added a second time. Warcraft Logs moves them to the Evoker
  instead: the **Reattributed** column of the damage ranking makes that
  same move, beside the total rather than in place of it, whenever a
  fight contains such lines.
- **Abandoned keys**: a key restarted or left for another is
  "abandoned", not "over time", and the **Unfinished keys** tile also
  counts the one the log leaves open.
- **In time or over time**: the log says a key was completed, never
  whether in time, and does not write the dungeon's timer. The verdict
  comes from the score the game writes when the key ends: a timed key
  earns at least its level's base score, from the table Raider.IO
  publishes (125 + 15 × level, plus 15 at each affix step: +4, +7, +10
  and +12; 320 for a +10, 380 for a +13), a late one less. Measured on
  14 completed keys: the 13 timed ones 3 to 15 points above, the only
  late one 60 points below, and the season's timers as Raider.IO gives
  them confirm every one of these verdicts. With no score (older format),
  the key is only "completed".
- **The history** ("History…" button of the window): keep, night after night,
  the figures of your characters, in folders you name (a season, "with my
  friends"). Off by default: nothing is saved without your consent, only the
  characters you tick leave their name, a night weighs about 30 KB, and you
  delete a night or a folder in one click. Whole keys (with their pulls and
  bosses) and raid bosses; no raid trash. The **Progress** tab shows one
  character run after run, content by content (same dungeon and level,
  same boss and difficulty), with the item level, the specialization, the
  group and the game's version beside it; it is never a grade. The
  **Specializations** tab sets side by side, in one content, the
  specializations played (median, range, item level), with no ranking.
  Best key and best kill will follow.
- **Preview and comparison of keys in the window.** To the right of the
  list of fights, two tabs follow what you tick: the overview (length,
  damage, healing, deaths, a line per player with their item level) and
  the keys. Two finished keys of the same dungeon and level are compared:
  damage/s, healing/s (shields included) and, for the tank, damage
  taken/s, for the group and for each player. The page carries the same
  comparison.
- **The players' item level**, in the overview and on the page: next to
  each name in the group's composition, with the group's average. On the
  page, a folded detail gives every piece (slot, item, level). The log
  gives only an item's number and level: the name and icon come from the
  game's item database, which LogsWoW does not have; each item is
  therefore a number with a Wowhead link, followed only if you click.
- **Melee swings taken**, in the panel of every player the enemy
  swung at ten times or more (the tank above all): hit, critical, fully
  absorbed, parried, dodged, missed, blocked, as the log writes them.
  And the share of the swings that landed which **came from behind**:
  the log does not write it, LogsWoW infers it from the attacker's
  position and the player's facing. It is a reliable estimate, not
  something the log writes, and limited to melee; the page says so,
  with a check: the game allows no parry or dodge from behind, and 97
  to 98% of parries and dodges do fall in front on the keys measured.
- **Physical or magic**: the share of damage taken and dealt that was
  physical, magic or both, as percentages, over the whole fight then pull
  by pull, with the detail by school (Shadow, Fire, Nature…).
- **What hurt the group**: every enemy ability, how much it cost, how
  many players it hit.
- **Deaths**, each with the chain of the last hits and heals received
  before the end, and the health left at each step.
- **What the group prevented**: how many spells the enemy began, how many
  completed, how many were cut by an interrupt, and how many ended
  because the caster died.
- **Per player**, by unfolding their name: for each spell, the total,
  the share, the number of casts, of hits, the average, the crit rate,
  the rate per second and the main target. Then their healing with its
  overhealing and whom it went to, what they took and from whom, the
  buffs received **with who gave them**, the debuffs suffered, what they
  applied themselves and on whom, their interrupts and dispels with the
  name of what was cut, and their longest pauses without a cast.
- **The cast order, pull by pull**, at the bottom of each player's panel:
  every spell cast, in order, as a chip of a fixed colour carrying its
  first two letters. Hovering gives its name and the moment it was cast,
  a click opens Wowhead. The legend is a filter: a click on a spell hides
  or shows all its chips, with no script in the page. Their summons'
  spells are apart, as round chips. Those the game fires by itself are
  written in the log exactly like a press; the ones that bear the marks
  (never paid for, and cast together with a paid spell, or faster than
  any button, or the second copy of a spell the log writes twice under
  the same name) are grouped apart and hidden at first, and one click
  shows them. `--sans-sequence` leaves the section out, for a page about
  half the size.
- **Per enemy**, the same way: units sharing a name are grouped, with
  what they dealt and to whom, what they took and from whom, the spells
  they cast, and how many were killed.
- **PvP, in part**: in an arena or a battleground, the players of the
  other side (outside the group and hostile, as the log writes them) are
  enemies, never the group; a group member under a mind control stays in
  the group. Matches are not cut out yet: with no encounter and no key in
  the file, the whole log is one "session".
- **Spell names are links to Wowhead**, in your machine's language.
  `--wowhead en` forces a language, `--wowhead off` removes the links.
  Nothing is loaded when the page opens: a link is followed only if you
  click it.

A whole evening makes a page of several megabytes. To look at only part
of it:

```
python3 -m logswow list WoWCombatLog.txt          # see the fights
python3 -m logswow report WoWCombatLog.txt --only 5
python3 -m logswow report WoWCombatLog.txt --only "Murder Row"
```

## What it does not do, and why

- **It compares you to nobody.** A percentile needs every other player's
  logs. That is exactly what a local tool on your machine does not have,
  and it is the one real service a central site provides.
- **It does not say whether a hit was avoidable.** The file says who was
  hit and how hard; knowing that a given damage came from a ground effect
  takes knowing the boss. This tool does not claim to.
- **It does not know what crowd control is.** The log never writes that a
  spell is a stun or a fear. An enemy spell that stops without an
  interrupt and without its caster dying is therefore filed under "cause
  not given by the log". Telling control apart from an ordinary debuff
  would take a maintained spell list.
- **It computes no mitigation percentage.** The log never writes what a
  hit would have done *before* armour and damage reductions. The second
  number on each hit looks like that and is not: measured on a real key,
  it is 1.03 times the damage taken on a normal hit and 2.59 times on a
  crit — it is the amount before the critical multiplier. Dividing one by
  the other gives a believable, wrong percentage. What really is in the
  file, and is shown, is the **damage absorbed** by shields.
- **It does not compute an FF Logs-style aDPS.** FF Logs does not read a
  buff's share in the log: it computes it, from a maintained table of
  each buff's multiplier and, for a critical-strike buff, from the
  likelihood that the crit came from it. WoW's log writes that share
  itself only for an Evoker's buffs, and that is exactly what the
  **Reattributed** column shows: the rDPS formula (damage − the share
  from others' buffs + the share given to others), limited to those
  buffs. The others would need the same maintained table; and a haste
  buff (Bloodlust, Power Infusion) changes how many hits there are, which
  none of those formulas handles.
- **It does not judge your rotation.** It shows your pauses, your
  abilities and your active effects. Saying "you should have pressed
  this" takes your specialization's rules, written and maintained by
  someone who plays it.

These limits are structural, not missing features.

## Where your data is

On your disk, and nowhere else. The program opens a file, writes a
file, and exits. It opens no network connection, reads no configuration,
writes no cache and knows no account. The page it produces loads nothing
when it opens: the test `test_writes_a_self_contained_page` fails if a
`<script>`, a stylesheet, a `src=`, an `@import` or a `url(` slips in, and
if any address other than Wowhead appears. Wowhead links are followed
only if you click them.

The report never writes a player's **realm**: names appear in their
short form, in the tables as in the death chains. A screenshot of the
report therefore identifies less than a screenshot of the log.

A useful reminder: a combat log holds the names and performance of **the
whole group**, not only yours. **So does the HTML report**: without the
realms, but with each one's short name, damage, healing and deaths.
Share it only with the agreement of those it names, as you would the log
itself.

`report` refuses to write over an existing file that is not a LogsWoW
report (another log, for instance), unless `--force`, and never writes
over the log it reads, even with `--force`.

## Tests, and checking on a real log

```
python3 tests/run-tests.py
python3 tools/check-invariants.py WoWCombatLog.txt
ln -s ../../tools/pre-push .git/hooks/pre-push     # once, for contributors
```

The tests run with no dependency and no network on
`examples/exemple-combat.txt`, a log **made up** for this repository: no
real log is ever committed, precisely because of the reminder above. The
tests read French whatever the machine's language; the English ones ask
for English.

The second script takes a **real** log and checks that the accounts
hold together: the group's damage is the sum of the players', a player's
the sum of their spells, a spell's the sum over its targets; the same for
healing; deaths counted three ways give the same number; no effect's
duration exceeds the fight; enemy casts begun equal the sum of their
outcomes; the share the game credits to an Evoker equals the share taken
from the players. It found a bug the first time it ran. It does not say whether a
number is true, only whether the numbers agree with each other. It checks
the whole file even after a first failure, and gives the tally at the
end.

Nothing runs online on a push: the `tools/pre-push` hook replays these
checks on your machine before each push. Only **publishing a version**
goes through a GitHub action (`.github/workflows/release.yml`), started
either by the "Run workflow" button in the Actions tab (on `main`) or by
a `v0.2.0` tag pushed from a copy of the repository: it runs the tests
again, checks that the tag is the package's version and sits on `main`,
builds the `.pyz` and its `SHA256SUMS` fingerprint, and publishes them
with the version's notes. It uses only what GitHub's machine already
has, with no third-party action.

What changes from one version to the next is in
[`CHANGELOG.en.md`](CHANGELOG.en.md) (in French: [`CHANGELOG.md`](CHANGELOG.md), in German: [`CHANGELOG.de.md`](CHANGELOG.de.md), in Spanish: [`CHANGELOG.es.md`](CHANGELOG.es.md));
the technical detail, dated and measured, in the dated sections of
`CLAUDE.md`.

The log is read as the game writes it, with its Windows line endings, on
Linux as on Windows.

## Licence

GNU Affero General Public License, **version 3 or (at your option) any
later version** (AGPL-3.0-or-later), since version 0.8.0. Anyone may use,
modify and redistribute it; whoever distributes a version, modified or
not, must provide its source code under the same licence. The AGPL adds
one point to the GPL: **whoever runs a modified version as an online
service** (a site that would read your logs, for instance) must also
offer its source code to the people using it. For you, using it on your
machine, nothing changes. Since 28 September 2026 the earlier versions
(0.1.0 to 0.7.0) are also distributed under AGPL-3.0-or-later; whoever
already had a copy keeps, for that copy, the rights of the GPL it was
received under, which the GPL declares irrevocable. See `LICENSE` and
`PROVENANCE.md`.
