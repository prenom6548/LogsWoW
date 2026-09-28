# Changelog

What each published version changed, for those who use it. This English
changelog starts with 0.9.0, the first version to speak English; earlier
versions are described in French in [`CHANGELOG.md`](CHANGELOG.md), and
the technical detail, dated and measured, is in the dated sections of
`CLAUDE.md`.

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
