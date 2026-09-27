"""The damage-taken timeline: an inline SVG, drawn from the analysis.

Split out of report.py. Formatters are called through `fmt` so that
replacing `logswow.fmt.compact` changes every number on the page at once,
which is how the page is checked against the analysis with no rounding.
"""

from . import fmt
from .timeline import POOL_STALE_MS
from .fmt import NBSP
from .timestamps import format_duration


class _Frame:
    """The timeline's geometry, shared by the pieces that draw it."""

    width, height = 1060, 190
    left, right = 62, 1016          # the plot area, leaving room for both axes
    top, bottom = 14, 158

    def __init__(self, series):
        self.series = series
        self.plot_width = self.right - self.left
        self.plot_height = self.bottom - self.top
        self.peak = max(max(row[1] for row in series), 1)
        self.step = self.plot_width / float(len(series))


class TimelineMixin:
    """The timeline half of `ReportWriter`."""

    def _timeline(self, analysis):
        """Damage taken per interval, with a real scale on both sides.

        Left axis: how much the group took in one interval. Right axis:
        the main target's health, so the two can be read against each
        other -- a spike of damage taken against a flat health bar is a
        different story from one during a burn phase.
        """
        series, bucket_ms = analysis.timeline_series()
        if len(series) < 3:
            return ""
        frame = _Frame(series)

        # A run is many fights, so one unit's health is the wrong curve for
        # it: the pooled health of everything engaged is drawn instead --
        # sum of current over sum of maximum, so a fresh pack lifts it back
        # to 100% and it falls as the pack dies. A boss pull keeps the
        # boss's own curve, which is what its reader expects.
        use_pool = analysis.has_several_pulls and analysis.has_pool_curve
        has_curve = use_pool or len(analysis.boss_hp) > 3

        pieces = self._timeline_axes(frame, has_curve)
        pieces += self._timeline_bars(frame)
        pieces += self._timeline_curve(frame, analysis, use_pool)
        pieces += self._timeline_time_axis(frame)
        return (
            "<h3>Degats subis par le groupe, seconde par seconde</h3>"
            "<div class=card><svg viewBox='0 0 %d %d' role=img "
            "aria-label='Degats subis au fil du combat'>%s</svg>"
            "<p class=dim style='margin:6px 0 0;font-size:12px'>Barres et echelle de "
            "gauche%s: degats subis par intervalle de %s. Traits rouges%s: morts.%s</p></div>"
            % (frame.width, frame.height, "".join(pieces), NBSP,
               "%.0f%ss" % (bucket_ms / 1000.0, NBSP), NBSP,
               self._timeline_caption(analysis, use_pool))
        )

    @staticmethod
    def _timeline_axes(frame, has_curve):
        """Left: four gridlines and their values. Right: enemy health."""
        pieces = []
        for fraction in (0.0, 0.25, 0.5, 0.75, 1.0):
            y = frame.bottom - fraction * frame.plot_height
            pieces.append(
                "<line x1='%d' y1='%.1f' x2='%d' y2='%.1f' stroke='var(--line)' "
                "stroke-width='1' />" % (frame.left, y, frame.right, y)
            )
            pieces.append(
                "<text x='%d' y='%.1f' font-size='11' fill='var(--muted)' "
                "text-anchor='end'>%s</text>"
                % (frame.left - 8, y + 3.5, fmt.compact(frame.peak * fraction))
            )
        if has_curve:
            for fraction in (0.0, 0.5, 1.0):
                y = frame.bottom - fraction * frame.plot_height
                pieces.append(
                    "<text x='%d' y='%.1f' font-size='11' fill='var(--accent)' "
                    "text-anchor='start'>%s</text>"
                    % (frame.right + 8, y + 3.5, fmt.percent(fraction))
                )
        return pieces

    @staticmethod
    def _timeline_bars(frame):
        """One bar per interval, and a red band where somebody died."""
        pieces = []
        for index, (_seconds, taken, _healing, deaths, _pool) in enumerate(frame.series):
            x = frame.left + index * frame.step
            if taken:
                bar_height = max(1.0, taken / frame.peak * frame.plot_height)
                pieces.append(
                    "<rect x='%.2f' y='%.2f' width='%.2f' height='%.2f' fill='var(--bar)' />"
                    % (x, frame.bottom - bar_height, max(1.0, frame.step - 0.5), bar_height)
                )
            if deaths:
                pieces.append(
                    "<rect x='%.2f' y='%d' width='%.2f' height='%d' fill='var(--bad)' "
                    "opacity='.55' />" % (x, frame.top, max(1.5, frame.step), frame.plot_height)
                )
        return pieces

    @staticmethod
    def _timeline_curve(frame, analysis, use_pool):
        """The enemy health curve: pooled for a run, the target's otherwise."""
        pieces = []
        if use_pool:
            # Drawn as separate strokes: a gap in readings is a gap in the
            # line, not a straight edge joining two unrelated pulls.
            run = []
            strokes = []
            for index, row in enumerate(frame.series):
                pool = row[4]
                if pool is None:
                    if len(run) > 1:
                        strokes.append(run)
                    run = []
                    continue
                run.append("%.1f,%.1f" % (frame.left + (index + 0.5) * frame.step,
                                          frame.bottom - pool * frame.plot_height))
            if len(run) > 1:
                strokes.append(run)
            for stroke in strokes:
                pieces.append(
                    "<polyline points='%s' fill='none' stroke='var(--accent)' "
                    "stroke-width='1.8' opacity='.95' />" % " ".join(stroke)
                )
        elif len(analysis.boss_hp) > 3 and analysis.first_ts is not None:
            span = max(1, (analysis.last_ts or 0) - analysis.first_ts)
            points = " ".join(
                "%.1f,%.1f"
                % (
                    frame.left + (ts - analysis.first_ts) / span * frame.plot_width,
                    frame.bottom - fraction * frame.plot_height,
                )
                for ts, fraction in analysis.boss_hp
            )
            pieces.append(
                "<polyline points='%s' fill='none' stroke='var(--accent)' "
                "stroke-width='1.8' opacity='.95' />" % points
            )
        return pieces

    @staticmethod
    def _timeline_time_axis(frame):
        pieces = [
            "<line x1='%d' y1='%d' x2='%d' y2='%d' stroke='var(--line)' />"
            % (frame.left, frame.bottom, frame.right, frame.bottom)
        ]
        series = frame.series
        for index in range(0, len(series), max(1, len(series) // 8)):
            pieces.append(
                "<text x='%.1f' y='%d' font-size='11' fill='var(--muted)'>%s</text>"
                % (frame.left + index * frame.step, frame.bottom + 18,
                   format_duration(series[index][0] * 1000))
            )
        return pieces

    @staticmethod
    def _timeline_caption(analysis, use_pool):
        """What the right-hand curve is, said precisely."""
        if use_pool:
            return (" Courbe et echelle de droite%s: <b>vie cumulee des ennemis engages</b>, "
                    "somme de leurs points de vie courants sur la somme de leurs maximums. "
                    "Elle remonte a chaque nouveau pack et retombe quand il meurt%s; un "
                    "ennemi que le groupe n'a plus touche depuis %d%ss en sort."
                    % (NBSP, NBSP, POOL_STALE_MS // 1000, NBSP))
        if analysis.boss_name and len(analysis.boss_hp) > 3:
            # Deliberately precise: on one real encounter the boss itself
            # never had its health written to the file, and the curve is
            # an add's. Naming it beats implying it is always the boss.
            return (" Courbe et echelle de droite%s: vie de <b>%s</b>, la cible la plus "
                    "frappee parmi celles dont le journal donne les points de vie."
                    % (NBSP, fmt.esc(analysis.boss_name)))
        return ""
