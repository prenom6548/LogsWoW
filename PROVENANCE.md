# Provenance

Where everything in this repository comes from, to preempt any copyright
question. The git history, with its `Co-Authored-By` trailers and session
links, is the primary record; this file is the human-readable summary. It
is documentation, not legal advice. That history was rewritten once, on
2026-09-28, by the owner, to remove a real player's identifier and
character name from its first commits: every commit hash from before
that date changed, and nothing about authorship did (messages, trailers,
authors and dates were kept). GitHub still served the old commits by
their hash (found by the 2026-09-29 audit), so the same day the owner
recreated the repository: the old one was renamed `LogsWoW1`, to be
deleted, and this one received only the rewritten history, which is
the whole history of this repository. Releases were published again
from the same tags.

## Authorship

All content here -- the `logswow/` package, the tests, the fixture
generator, and this documentation -- was written from scratch by Claude,
an AI assistant made by Anthropic, working in Claude Code sessions at the
direction of the repository owner (GitHub: prenom6548). No code was
copied from any third-party project.

In particular, nothing was taken from Warcraft Logs, WoWAnalyzer,
Wipefest or Archon. WoWAnalyzer's source (AGPL-3.0) was read while
researching what those sites do, and that research is
`LOGS-SITES-RESEARCH.md` in this repository; it informed *what a reader
of combat logs is for*, which is a fact about a problem, not an
expression of a solution. No file, function, identifier or structure
from it appears here. This package's architecture -- a streaming reader
with a measured field layout, feeding accumulators per segment -- was
designed for this repository and looks nothing like it.

The legal status of AI-generated works varies by jurisdiction; to the
extent any rights exist in this content, they are held by the repository
owner and licensed under the GNU Affero General Public License, version 3
or (at the licensee's option) any later version (AGPL-3.0-or-later).

The licence history, since each step was the owner's decision: "GPLv3"
until 2026-09-27; GPL-3.0-or-later from then, made explicit before the
repository went public, for versions 0.3.2 to 0.7.0; AGPL-3.0-or-later
from 0.8.0 (2026-09-28), chosen by the owner so that anyone running a
modified version as an online service must offer its source to its users
as well. The owner could make that change alone because no third-party
code is in the repository (see below).

On 2026-09-28 the owner also placed the **earlier versions** (0.1.0 to
0.7.0) under AGPL-3.0-or-later: from that date, the owner distributes
every version of LogsWoW, old and new, under that licence only. What
this cannot do is take back a licence already given. GPLv3 says so in
its own text: its section 2 declares the rights it grants "irrevocable
provided the stated conditions are met", section 10 gives every
recipient a licence directly from the licensor, and section 8 ends
those rights only for someone who breaks the licence. Anyone who
obtained a copy of 0.1.0 to 0.7.0 before 2026-09-28 therefore keeps,
for that copy, the GPL rights it came with. Nobody else's
agreement was needed: the repository has no contributor other than the
owner's own sessions.

## Third-party material

**None is vendored.** The package imports only the Python standard
library, by design: no dependency means nothing to audit, nothing to
install, and nothing that can phone home.

`LICENSE` is the verbatim GNU AGPLv3, fetched from gnu.org on
2026-09-28 (SHA-256 0d96a4ff68ad6d4b6f1f30f713b18d5184912ba8dd389f86aa7710db079abcb0,
the FSF's own file). The FSF permits and requires verbatim copying of the
license document itself.

## The research document

`LOGS-SITES-RESEARCH.md` is original text, written in French for the
owner on 2026-09-16, two days before this package. It describes four
public web services from their own published help pages, press coverage
and forum threads, all listed by number at its end; short phrases are
quoted with attribution and the rest is paraphrase. It was copied here
unchanged in substance on 2026-09-18, with a few internal cross-references
to the author's private working notes rewritten so the document stands
on its own.

## The combat log format

The field layouts this package reads were **measured from two real logs
supplied by the owner** (a 12.1.0 client, 2026-09-12 and 2026-09-14),
not copied from anyone's parser. Where published documentation and those
files disagreed, the files won and the difference is recorded in
`CLAUDE.md`. A file format is a fact about a program's output, not a
creative work, and no text from any documentation source was reproduced.

## A second research document

`PULL-DETECTION-RESEARCH.md` is original text, written in French for the
owner on 2026-09-26/27, after they asked whether wowumbra.gg's published
methodology could refine this package's pull segmentation. It quotes two
short, clearly-attributed sentences from wowumbra.gg's own public pages
(fair use of a factual claim about their own data source). It also
quotes two short code excerpts from WoWAnalyzer's `src/parser/core/Fight.ts`
and `FilterButton.tsx` (github.com/WoWAnalyzer/WoWAnalyzer, AGPL-3.0):
the repository was cloned read-only into a session's temporary directory
to answer one factual question -- how does Warcraft Logs' API describe a
Mythic+ dungeon's pulls -- and deleted immediately after. Nothing from it
was adapted or reused as logic; the quotes exist only to show, verbatim,
what a public API's data shape is, which is a fact rather than an
expression of one. No file in `logswow/` was changed as a result of this
research, and the document says so.

## The owner's own logs are not in this repository, and must not be

The files used to develop and check this package were read in session
containers and never committed: the two 12.1.0 logs above, five more
supplied on 2026-09-20 (three Mythic+ keys and the first two again), a
Warcraft Logs export of one of those keys, and two supplied during the
2026-09-27 audit (a raid night and a Mythic+ session), then sixteen
the same day (those two among them), which the owner put on a Swiss
file-transfer service because they were too large to attach. Those
were downloaded one at a time into the session's scratch directory,
read, and deleted after the read; only counts per specialization and
per spell were kept. On 2026-09-28 the owner sent one more night (five
keys, with a Warcraft Logs events export and a report of their own to
compare), read the same way. For that night the owner also created a
Warcraft Logs API client of their own and gave the session its
credentials, so the session could fetch the site's tables and events
for the same five keys (their public report) and compare them with this
package's numbers. The fetching script lived in the session's scratch
directory only; the package still opens no socket, and the fetched data
was deleted after the comparison, as were the credentials. Only facts
about the file format came out of it -- which lines the site counts --
and they were each re-measured on the logs themselves before any code
changed. On 2026-09-29 the owner attached one more, a Mythic+ night of
that day, to the audit of 0.12.1; it was read the same way, in the
scratch directory only, and deleted after. What they taught is recorded here as
counts and totals, in `CLAUDE.md` and in commit messages. A combat log
carries the character names, realms and performance of **everyone in
the group**, who did not agree to anything. `examples/exemple-
combat.txt` is generated by `tests/make_fixture.py` and is entirely
fabricated: invented names, invented numbers, real shapes. Keep it
that way.
