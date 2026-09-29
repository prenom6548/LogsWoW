# SPDX-License-Identifier: AGPL-3.0-or-later
"""Three ways to lay the same report out: one long page, tabs, or pages.

Asked for by the owner on 2026-09-28: the single page is long, could it
be tabs or pages -- and then, could the reader choose. It can, and none
of the three needs a script: the rule that the report runs nothing and
fetches nothing holds for all of them.

- **longue**: the page as it always was, byte for byte.
- **onglets**: one file. A list of the fights on the left, and inside a
  fight six tabs. Both are radio buttons a label points at, and CSS
  shows the pane whose button is checked -- the technique the cast-order
  filter already uses. Everything is in the file; only what is shown
  changes, so searching the page (Ctrl+F) finds only the visible part.
- **pages**: a folder, `index.html` and one `combat-NN.html` per fight,
  linked by plain relative links. Lighter to open on a big night, but a
  folder to share rather than a file.
"""

import os
import shutil

from . import fmt
from .i18n import N_, _

LAYOUTS = ("onglets", "pages", "longue")

# The tabs of a fight: (key, title, parts of `ReportWriter._sections`).
CATEGORIES = (
    ("resume", N_("Résumé"), ("orphans", "composition", "timeline", "pulls")),
    ("degats", N_("Dégâts et soins"), ("rankings", "taken")),
    ("ecoles", N_("Physique ou magique"), ("schools",)),
    ("morts", N_("Morts"), ("deaths",)),
    ("joueurs", N_("Joueurs"), ("players",)),
    ("ennemis", N_("Ennemis"), ("enemy_casts", "enemies")),
)

TABS_CSS = """
.wrap.tabs{max-width:1320px}
.fsel,.tab{position:absolute;opacity:0;width:1px;height:1px;pointer-events:none}
.layout{display:grid;grid-template-columns:240px minmax(0,1fr);gap:24px;align-items:start}
.side{position:sticky;top:12px;max-height:calc(100vh - 24px);overflow:auto;
display:flex;flex-direction:column;gap:2px;padding-right:4px}
.nv{display:block;padding:6px 10px;border-radius:6px;cursor:pointer;font-size:13.5px;
line-height:1.3}
.nv:hover{background:var(--panel)}
.nv small{display:block;color:var(--muted);font-size:11.5px}
.nv.in{margin-left:14px}
.grp>summary{list-style:none;display:flex;align-items:stretch}
.grp>summary::-webkit-details-marker{display:none}
.grp>summary::before{content:"+";flex:none;width:18px;padding-top:6px;text-align:center;
color:var(--muted);font-weight:700;cursor:pointer}
.grp[open]>summary::before{content:"\u2212"}
.grp>summary>.nv{flex:1}
.grp>.nv.in{margin-left:18px}
.fight{display:none}
.tabbar{display:flex;flex-wrap:wrap;gap:4px;border-bottom:1px solid var(--line);margin:10px 0 16px}
.lb{padding:7px 12px;cursor:pointer;border:1px solid transparent;border-bottom:none;
border-radius:6px 6px 0 0;font-size:13.5px;color:var(--muted);margin-bottom:-1px}
.lb:hover{color:var(--ink)}
.pane{display:none}
.pnav{display:flex;flex-wrap:wrap;gap:8px 18px;font-size:13.5px;margin:6px 0 10px}
@media(max-width:860px){.layout{grid-template-columns:1fr}
.side{position:static;max-height:none;flex-direction:row;flex-wrap:wrap}.nv.in{margin-left:0}}
"""


def tab_rules():
    """The CSS that shows the checked tab's pane and marks its label."""
    rules = []
    for key, _title, _parts in CATEGORIES:
        rules.append(".tb-%s:checked~.panes .pn-%s{display:block}" % (key, key))
        rules.append(".tb-%s:checked~.tabbar .lb-%s{background:var(--panel);"
                     "border-color:var(--line);color:var(--ink);font-weight:600}" % (key, key))
        rules.append(".tb-%s:focus-visible~.tabbar .lb-%s{outline:2px solid var(--accent)}"
                     % (key, key))
    return "\n".join(rules)


def fight_rules(indexes):
    """One rule per fight: its button shows its section and marks its label."""
    rules = []
    for index in indexes:
        rules.append("#f%d:checked~.layout .v%d{display:block}" % (index, index))
        rules.append("#f%d:checked~.layout .n%d{background:var(--panel);font-weight:600;"
                     "box-shadow:inset 3px 0 var(--accent)}" % (index, index))
        rules.append("#f%d:focus-visible~.layout .n%d{outline:2px solid var(--accent)}"
                     % (index, index))
    return "\n".join(rules)


def tabbed_fight(index, parts):
    """The tabs of one fight; a tab with nothing in it is left out."""
    present = [(key, _(title), "".join(parts[name] for name in names))
               for key, title, names in CATEGORIES]
    present = [(key, title, html) for key, title, html in present if html]
    if not present:
        return ""
    radios = "".join(
        "<input type=radio name=t%d id=t%d-%s class='tab tb-%s'%s aria-label='%s'>"
        % (index, index, key, key, " checked" if position == 0 else "", fmt.esc(title))
        for position, (key, title, _html) in enumerate(present))
    labels = "".join("<label for=t%d-%s class='lb lb-%s'>%s</label>" % (index, key, key, title)
                     for key, title, _html in present)
    panes = "".join("<div class='pane pn-%s'>%s</div>" % (key, html)
                    for key, _title, html in present)
    return "%s<div class=tabbar>%s</div><div class=panes>%s</div>" % (radios, labels, panes)


def nested(segments):
    """Indexes of the fights that sit inside a key listed before them."""
    return {segment.index for children in contents(segments).values() for segment in children}


def contents(segments):
    """{key index: [what the key holds, in order]}: its bosses and its trash pulls.

    What the owner asked for on 2026-09-29: a key folded under a "+", and
    once unfolded, every pull in the order it was fought, each one a view
    of its own.
    """
    held, key = {}, None
    for segment in segments:
        if segment.kind == "keystone":
            key = segment
            held[key.index] = list(key.pulls)
        elif (key is not None and segment.kind == "encounter"
              and key.start_ts <= segment.start_ts <= (key.end_ts or segment.start_ts)):
            held[key.index].append(segment)
    for children in held.values():
        children.sort(key=lambda segment: (segment.start_ts, segment.kind != "pull"))
    return held


def nav_label(segment, inside=False):
    """One entry of the list on the left: a fight, a boss in a key, or a pull."""
    if segment.kind == "pull":
        what = segment.block.label() if segment.block is not None else ""
        if len(what) > 38:
            what = what[:37].rstrip() + "\u2026"
        title, small = segment.name, what
    else:
        title, small = segment.label, _(segment.outcome)
    return "<label for=f%d class='nv n%d%s'>%s<small>%s</small></label>" % (
        segment.index, segment.index, " in" if inside else "", fmt.esc(title),
        fmt.esc(small) or "&nbsp;")


def views(segments):
    """Every view of the report: the fights, and after each key its pulls."""
    return [view for segment in segments for view in [segment] + list(segment.pulls)]


def write_atomic(path, text):
    """Write beside the target and move into place: never a half page."""
    partial = path + ".partiel"
    try:
        with open(partial, "w", encoding="utf-8") as handle:
            handle.write(text)
        os.replace(partial, path)
    finally:
        if os.path.exists(partial):
            os.remove(partial)


def write_streamed(path, body, head):
    """Write `head()` and then every piece of `body`, never the page at once.

    The head is known last -- it carries a CSS rule for every spell a
    cast-order chip shows -- yet it opens the file. Assembling the whole
    page to put it first meant holding it several times over: the sections,
    their join, the frame around them, the head in front, each a copy of a
    page of tens of megabytes. On the owner's 364 MB night the tabbed
    report peaked at 252 MB for a 20 MB page, the reading itself at 70 MB;
    written this way, at 89 MB.
    The pieces now go to a spool beside the target as they are made, and
    the page is the head followed by the spool: the same bytes, written in
    the same two steps -- beside the target, then moved into place -- so a
    full disk or an interrupt halfway still leaves the previous report whole.
    """
    partial = path + ".partiel"
    spool = path + ".partiel-corps"
    try:
        # newline="" both ways: the spool keeps the text as it was made,
        # and only the page itself translates line ends, as it always did.
        with open(spool, "w+", encoding="utf-8", newline="") as spooled:
            for piece in body:
                spooled.write(piece)
            spooled.seek(0)
            with open(partial, "w", encoding="utf-8") as handle:
                handle.write(head())
                shutil.copyfileobj(spooled, handle, 1 << 20)
        os.replace(partial, path)
    finally:
        for leftover in (partial, spool):
            if os.path.exists(leftover):
                os.remove(leftover)


def page_name(segment):
    if segment.kind == "pull":
        return "combat-%02d-pull-%02d.html" % (segment.parent.index, segment.number)
    return "combat-%02d.html" % segment.index


def is_our_report(path):
    """True when the file at `path` is a page this program wrote.

    The one test both the command line and the folder layout use before
    replacing a file: a LogsWoW page starts with the doctype and names
    itself in its title, and nothing else is ever overwritten.
    """
    try:
        with open(path, "rb") as handle:
            head = handle.read(512)
    except OSError:
        return False
    return head.startswith(b"<!doctype html>") and b"<title>LogsWoW" in head


class LayoutsMixin:
    """The tabbed page and the folder of pages; the long page is `write` itself."""

    def _write_tabbed(self):
        overview = self._overview(link=lambda segment: "<label for=f%d class=name>%s</label>"
                                  % (segment.index, fmt.esc(segment.label)))
        every = views(self.segments)
        held = contents(self.segments)
        inside = nested(self.segments)
        radios = _("<input type=radio name=f id=f0 class=fsel checked "
                   "aria-label='Vue d&#39;ensemble'>")
        radios += "".join("<input type=radio name=f id=f%d class=fsel aria-label='%s'>"
                          % (segment.index, fmt.esc(segment.label)) for segment in every)
        entries = []
        for segment in self.segments:
            if segment.index in inside:
                continue        # drawn inside its key
            children = held.get(segment.index)
            if children:
                entries.append("<details class=grp><summary>%s</summary>%s</details>" % (
                    nav_label(segment), "".join(nav_label(child, True) for child in children)))
            else:
                entries.append(nav_label(segment))
        nav = _("<label for=f0 class='nv n0'>Vue d'ensemble</label>") + "".join(entries)
        # The translated frame around the radios, the list, the fights and
        # the footer, cut at markers so that each fight is written as soon
        # as it is drawn (`write_streamed`) rather than all held at once.
        mark = "\x00"
        frame = (_("%s<div class=layout><nav class=side aria-label='Combats'>%s</nav>"
                   "<main>%s</main></div>%s") % (mark, mark, mark, mark)).split(mark)

        def body():
            yield frame[0] + radios + frame[1] + nav + frame[2]
            yield "<section class='fight v0'>%s</section>" % overview
            for segment in every:
                head, parts = self._view(segment)
                yield ("<section class='fight v%d'>%s%s</section>"
                       % (segment.index, head, tabbed_fight(segment.index, parts)))
            yield frame[3] + self._footer() + frame[4]

        css = TABS_CSS + tab_rules() + "\n" + fight_rules([0] + [s.index for s in every])
        write_streamed(self.out_path, body(),
                       lambda: self._head(extra_css=css, wrap_class="wrap tabs"))
        return self.out_path

    def _view(self, segment):
        """A fight's head and parts; a pull's leave out the cast order, which
        its key already draws pull by pull."""
        if segment.kind != "pull":
            return self._segment(segment)
        cast_order, self.cast_order = self.cast_order, False
        try:
            return self._segment(segment)
        finally:
            self.cast_order = cast_order

    def _write_pages(self):
        folder = self.out_path
        os.makedirs(folder, exist_ok=True)
        written = set()
        segments = views(self.segments)
        for position, segment in enumerate(segments):
            self._spell_ids = set()
            head, parts = self._view(segment)
            links = [_("<a href='index.html'>&larr; Tous les combats</a>")]
            if position > 0:
                links.append("<a href='%s'>&lsaquo; %s</a>" % (
                    page_name(segments[position - 1]), fmt.esc(segments[position - 1].label)))
            if position + 1 < len(segments):
                links.append("<a href='%s'>%s &rsaquo;</a>" % (
                    page_name(segments[position + 1]), fmt.esc(segments[position + 1].label)))
            nav = "<nav class=pnav>%s</nav>" % "".join(links)
            body = nav + head + "".join(parts.values()) + nav + self._footer()
            name = page_name(segment)
            write_atomic(os.path.join(folder, name), self._head(extra_css=TABS_CSS) + body)
            written.add(name)
        self._spell_ids = set()
        overview = self._overview(link=lambda segment: "<a href='%s' class=name>%s</a>"
                                  % (page_name(segment), fmt.esc(segment.label)))
        index = os.path.join(folder, "index.html")
        write_atomic(index, self._head() + overview + self._footer())
        # Pages of an earlier report of ours that this one no longer has.
        for name in os.listdir(folder):
            if (name.startswith("combat-") and name.endswith(".html") and name not in written
                    and is_our_report(os.path.join(folder, name))):
                os.remove(os.path.join(folder, name))
        return index
