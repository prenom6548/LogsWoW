# Changelog

What each published version changed, for those who use it. This English
changelog starts with 0.9.0, the first version to speak English; earlier
versions are described in French in [`CHANGELOG.md`](CHANGELOG.md), and
the technical detail, dated and measured, is in the dated sections of
`CLAUDE.md`.

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
