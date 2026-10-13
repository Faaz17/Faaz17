"""Activity: a two-channel oscilloscope on the bench.

CH1 (green) is contributions per week, drawn as a smooth analog trace. CH2
(amber) is how many days of that week had any contribution, drawn as a
stepped digital trace: volume and consistency on one screen. The trigger level
is CH1's weekly average and a cursor marks the busiest week, as a scope would
show them. The measure panel sits beside the screen on desktop and below it on
a phone.
"""
from __future__ import annotations

import math

from ghdata import MONTHS, Activity
from parts import P, SHEEN, STEEL, document, instrument, knob, mix, monotone_path, num, rect, screw
from typeset import Ink

COLS, ROWS = 13, 6   # 13 divisions of 4 weeks across, 6 divisions up
CH2_STEP = 2         # CH2 is drawn at 2 days per division, so a full week sits at 3.5 divisions
AMBER_TEXT = mix(P["amber"], "#FFFFFF", 0.45)

DEFS = (
    SHEEN, STEEL,
    '<radialGradient id="crt" cx="0.5" cy="0.45" r="0.75">'
    f'<stop offset="0" stop-color="#072318"/><stop offset="1" stop-color="{P["glass"]}"/></radialGradient>'
    '<filter id="bloom" x="-0.2" y="-0.5" width="1.4" height="2"><feGaussianBlur stdDeviation="3"/></filter>',
)
CSS = (
    ".draw{stroke-dasharray:100 100;animation:draw 2.4s cubic-bezier(.3,0,.2,1) .2s backwards}"
    "@keyframes draw{from{stroke-dashoffset:100}to{stroke-dashoffset:0}}"
    "@media (prefers-reduced-motion:reduce){.draw{animation:none}.beam{display:none}}"
)


def nice_step(peak: int, divisions: int) -> int:
    for step in (1, 2, 3, 4, 5, 6, 8, 10, 12, 15, 20, 25, 30, 40, 50, 60, 80, 100):
        if step * divisions >= peak:
            return step
    return math.ceil(peak / divisions / 50) * 50


def _plot(ink: Ink, F, act: Activity, x0: float, x1: float, y0: float, y1: float, *,
          label: float, small: float, month_every: int = 1) -> tuple[str, int]:
    """Graticule, both channels, trigger level, busiest-week cursor and beam.
    Returns (svg, CH1 contributions per division)."""
    out = []
    div_w, div_h = (x1 - x0) / COLS, (y1 - y0) / ROWS
    step = nice_step(act.peak, ROWS)
    top = step * ROWS

    grid = []
    for i in range(COLS + 1):
        x = x0 + i * div_w
        dash = "" if i in (0, COLS) else ' stroke-dasharray="1 3"'
        grid.append(f'<line x1="{num(x)}" y1="{num(y0)}" x2="{num(x)}" y2="{num(y1)}"{dash}/>')
    for j in range(ROWS + 1):
        y = y0 + j * div_h
        dash = "" if j in (0, ROWS) else ' stroke-dasharray="1 3"'
        grid.append(f'<line x1="{num(x0)}" y1="{num(y)}" x2="{num(x1)}" y2="{num(y)}"{dash}/>')
    yc = y0 + ROWS / 2 * div_h
    for k in range(COLS * 5 + 1):  # minor ticks on the centre line, as on a real graticule
        x = x0 + k * div_w / 5
        grid.append(f'<line x1="{num(x)}" y1="{num(yc - 2.5)}" x2="{num(x)}" y2="{num(yc + 2.5)}"/>')
    out.append(f'<g stroke="{P["grid"]}" stroke-width="1">{"".join(grid)}</g>')

    slot = (x1 - x0) / len(act.weeks)
    xs = [x0 + (i + 0.5) * slot for i in range(len(act.weeks))]
    ys = [y1 - v / top * (y1 - y0) for v in act.weeks]
    d = monotone_path(xs, ys)

    # CH2: a stepped trace, one level per week, drawn under CH1.
    levels = [y1 - v / (CH2_STEP * ROWS) * (y1 - y0) for v in act.week_active]
    d2 = f"M{num(x0)} {num(levels[0])}"
    for i, ly in enumerate(levels):
        if i:
            d2 += f"V{num(ly)}"
        d2 += f"H{num(x0 + (i + 1) * slot)}"
    out.append(f'<path class="draw" d="{d2}" pathLength="100" fill="none" stroke="{P["amber"]}" '
               f'stroke-width="5" stroke-opacity="0.3" filter="url(#bloom)"/>')
    out.append(f'<path class="draw" d="{d2}" pathLength="100" fill="none" stroke="{P["amber"]}" '
               f'stroke-width="1.5" stroke-opacity="0.9"/>')

    # CH1's weekly average as the trigger level, marked on the right edge as a scope does.
    avg = sum(act.weeks) / len(act.weeks)
    ay = y1 - avg / top * (y1 - y0)
    out.append(f'<line x1="{num(x0)}" y1="{num(ay)}" x2="{num(x1)}" y2="{num(ay)}" stroke="{P["phosphor"]}" '
               f'stroke-opacity="0.45" stroke-dasharray="4 4"/>')
    out.append(f'<path d="M{num(x1 + 11)} {num(ay - 4.5)}L{num(x1 + 3)} {num(ay)}L{num(x1 + 11)} {num(ay + 4.5)}Z" '
               f'fill="{P["phosphor"]}"/>')
    # Its label sits on the line wherever CH1 leaves the most room, and is drawn
    # after the traces so it stays legible if no spot is fully clear.
    avg_text = f"AVG {avg:.0f} / WK"
    aw = ink.width(F["mono_md"], avg_text, label, 0.06)
    top_edge, bottom_edge = ay - label * 1.8, ay - 2

    def clearance(xa: float) -> float:
        near = [y for x, y in zip(xs, ys) if xa - 16 <= x <= xa + aw + 16]
        return min((0.0 if top_edge <= y <= bottom_edge else min(abs(y - top_edge), abs(y - bottom_edge)))
                   for y in near) if near else 99.0

    ax = max(range(int(x0 + 6), int(x1 - 6 - aw) + 1, 4), key=lambda xa: (min(clearance(xa), 12), xa))
    avg_label = (rect(ax - 4, top_edge, aw + 8, label * 1.45, f' rx="2" fill="{P["glass"]}" fill-opacity="0.85"')
                 + ink.text(F["mono_md"], avg_text, ax, ay - 6.5, label, P["phosphor"], track=0.06))

    # Cursor on the busiest week.
    pi = max(range(len(act.weeks)), key=lambda i: (act.weeks[i], i))
    px = xs[pi]
    out.append(f'<line x1="{num(px)}" y1="{num(y0)}" x2="{num(px)}" y2="{num(y1)}" stroke="{P["bloom"]}" '
               f'stroke-opacity="0.5" stroke-dasharray="2 3"/>')
    peak_text = f"PEAK {act.peak} · {act.peak_start.day} {MONTHS[act.peak_start.month - 1].upper()}"
    pw = ink.width(F["mono_md"], peak_text, label, 0.06)
    lx = px + 7 if px + 7 + pw < x1 - 4 else px - 7 - pw
    out.append(rect(lx - 4, y0 + 5, pw + 8, label * 1.55, f' rx="2" fill="{P["glass"]}" fill-opacity="0.9"'))
    out.append(ink.text(F["mono_md"], peak_text, lx, y0 + 5 + label * 1.15, label, P["bloom"], track=0.06))

    # CH1: a wide blurred pass for the phosphor bloom, then the line, then its hot core.
    out.append(f'<path class="draw" d="{d}" pathLength="100" fill="none" stroke="{P["phosphor"]}" '
               f'stroke-width="6" stroke-opacity="0.4" filter="url(#bloom)"/>')
    out.append(f'<path class="draw" d="{d}" pathLength="100" fill="none" stroke="{P["phosphor"]}" stroke-width="2"/>')
    out.append(f'<path class="draw" id="beam-path" d="{d}" pathLength="100" fill="none" stroke="{P["bloom"]}" '
               f'stroke-width="0.8" stroke-opacity="0.9"/>')
    # The beam: hidden unless SMIL runs, then sweeps the year and rests on this week.
    out.append(
        f'<g class="beam" visibility="hidden"><set attributeName="visibility" to="visible" begin="2.6s"/>'
        f'<circle r="6" fill="{P["phosphor"]}" opacity="0.45" filter="url(#bloom)"/>'
        f'<circle r="2.2" fill="{P["bloom"]}"/>'
        '<animateMotion dur="7s" begin="2.6s" repeatCount="indefinite" calcMode="linear" '
        'keyPoints="0;1;1" keyTimes="0;0.62;1"><mpath href="#beam-path"/></animateMotion></g>'
    )
    out.append(avg_label)

    # Scale at the corners, months along the bottom.
    out.append(ink.text(F["mono"], str(top), x0 - 8, y0 + small * 0.35, small, P["phosphor_dim"], anchor="end"))
    out.append(ink.text(F["mono"], "0", x0 - 8, y1 + small * 0.35, small, P["phosphor_dim"], anchor="end"))
    firsts = [(i, day) for i, day in enumerate(act.days) if day and day.day == 1]
    for k, (idx, day) in enumerate(firsts):
        x = x0 + (idx + 0.5) * (x1 - x0) / len(act.days)
        out.append(f'<line x1="{num(x)}" y1="{num(y1)}" x2="{num(x)}" y2="{num(y1 + 4)}" stroke="{P["phosphor_dim"]}"/>')
        if (len(firsts) - 1 - k) % month_every == 0:  # always label the newest month
            out.append(ink.text(F["mono"], MONTHS[day.month - 1].upper(), x, y1 + small * 1.9, small,
                                P["phosphor_dim"], anchor="middle", track=0.08))
    return "".join(out), step


def _channel(ink: Ink, F, name: str, title: str, x: float, y: float, size: float, colour: str,
             text_colour: str) -> tuple[str, float]:
    """A channel badge and its title, as the scope prints them. Returns (svg, right edge)."""
    svg = (rect(x, y - 12, 30, 16, f' rx="3" fill="none" stroke="{colour}"')
           + ink.text(F["mono_sb"], name, x + 15, y, 9.5, colour, anchor="middle")
           + ink.text(F["sans_md"], title, x + 40, y + 1, size, text_colour))
    return svg, x + 40 + ink.width(F["sans_md"], title, size)


def _about(act: Activity) -> tuple[str, str]:
    title = f"{act.total:,} contributions in the last 12 months"
    desc = (f"Oscilloscope-style chart. Channel 1: contributions per week; channel 2: active days per week. "
            f"Busiest week: {act.peak}, starting {act.peak_start.day} {MONTHS[act.peak_start.month - 1]} "
            f"{act.peak_start.year}. Active on {act.active_days} of the last 365 days. "
            f"Longest streak: {act.longest_streak} days.")
    return title, desc


def _readouts(act: Activity) -> list[tuple[str, str, int]]:
    week = f"{act.peak_start.day} {MONTHS[act.peak_start.month - 1]}"
    return [
        ("BUSIEST WEEK", f"week of {week}", act.peak),
        ("ACTIVE DAYS", "of the last 365", act.active_days),
        ("LONGEST STREAK", "days in a row", act.longest_streak),
    ]


def _stamp(act: Activity) -> str:
    return f"{act.today.day} {MONTHS[act.today.month - 1].upper()} {act.today.year}"


def activity_desktop(F, act: Activity) -> str:
    W, H = 880, 300
    ink = Ink()
    out = [instrument(W, H, 18)]
    out += [screw(x, y) for x, y in ((12, 12), (W - 12, 12), (12, H - 12), (W - 12, H - 12))]
    out += [rect(20, 20, 600, 260, ' rx="14" fill="#061A11" stroke="#173F2D"'),
            rect(28, 28, 584, 244, ' rx="10" fill="url(#crt)"')]
    plot, step = _plot(ink, F, act, 72, 592, 62, 226, label=10.5, small=10)
    out.append(plot)

    # Top bar: both channels, and the RUN light.
    ch1, right = _channel(ink, F, "CH1", "Contributions per week", 40, 51, 13.5, P["phosphor"], P["bloom"])
    ch2, _ = _channel(ink, F, "CH2", "Active days per week", right + 18, 51, 13.5, P["amber"], AMBER_TEXT)
    out += [ch1, ch2]
    out.append(rect(566, 39, 34, 16, f' rx="3" fill="{P["phosphor"]}" fill-opacity="0.9"'))
    out.append(ink.text(F["mono_sb"], "RUN", 583, 51, 9.5, P["glass"], anchor="middle", track=0.08))

    # Status bar along the bottom of the screen: scales, timebase, date.
    out.append(ink.text(F["mono"], f"CH1 {step}/div", 40, 264, 10, P["phosphor_dim"]))
    out.append(ink.text(F["mono"], f"CH2 {CH2_STEP} d/div", 140, 264, 10, mix(P["amber"], P["glass"], 0.35)))
    out.append(ink.text(F["mono"], "TIME 4 wk/div", 250, 264, 10, P["phosphor_dim"]))
    out.append(ink.text(F["mono"], _stamp(act), 600, 264, 10, P["phosphor_dim"], anchor="end", track=0.06))

    # Measure panel, with the front-panel knobs above it.
    mx, mr = 644, 856
    out.append(knob(806, 44, 11, -40))
    out.append(knob(838, 44, 11, 35))
    out.append(ink.text(F["display"], "MEASURE", mx, 47, 10.5, P["silk_faint"], track=0.24))
    out.append(ink.text(F["display"], f"{act.total:,}", mx - 2, 100, 38, P["silk"]))
    out.append(ink.text(F["mono"], "contributions, last 12 months", mx, 120, 11, P["silk_dim"]))
    out.append(f'<line x1="{mx}" y1="140" x2="{mr}" y2="140" stroke="{P["silk_faint"]}" stroke-opacity="0.4"/>')
    for i, (label, sub, value) in enumerate(_readouts(act)):
        y = 172 + 40 * i
        out.append(ink.text(F["mono_md"], label, mx, y, 11, P["silk_dim"], track=0.1))
        out.append(ink.text(F["mono"], sub, mx, y + 16, 10.5, P["silk_faint"]))
        out.append(ink.text(F["mono_sb"], f"{value:,}", mr, y + 9, 21, P["silk"], anchor="end"))

    title, desc = _about(act)
    return document(W, H, ink, "".join(out), title=title, desc=desc, defs=DEFS, style=CSS)


def activity_mobile(F, act: Activity) -> str:
    W, H = 360, 474
    ink = Ink()
    out = [instrument(W, H, 16)]
    out += [screw(x, y, 4) for x, y in ((12, H - 12), (W - 12, H - 12))]
    out += [rect(8, 8, 344, 258, ' rx="12" fill="#061A11" stroke="#173F2D"'),
            rect(14, 14, 332, 246, ' rx="9" fill="url(#crt)"')]
    plot, step = _plot(ink, F, act, 44, 332, 56, 204, label=11, small=10.5, month_every=2)
    out.append(plot)

    ch1, right = _channel(ink, F, "CH1", "Contributions", 24, 39, 14, P["phosphor"], P["bloom"])
    ch2, _ = _channel(ink, F, "CH2", "Active days", right + 14, 39, 14, P["amber"], AMBER_TEXT)
    out += [ch1, ch2]

    out.append(ink.text(F["mono"], f"CH1 {step}/div", 24, 248, 10.5, P["phosphor_dim"]))
    out.append(ink.text(F["mono"], f"CH2 {CH2_STEP} d/div", 118, 248, 10.5, mix(P["amber"], P["glass"], 0.35)))
    out.append(ink.text(F["mono"], _stamp(act), 334, 248, 10.5, P["phosphor_dim"], anchor="end"))

    out.append(knob(300, 292, 10, -40))
    out.append(knob(330, 292, 10, 35))
    out.append(ink.text(F["display"], "MEASURE", 22, 296, 11, P["silk_faint"], track=0.24))
    out.append(ink.text(F["display"], f"{act.total:,}", 20, 344, 40, P["silk"]))
    out.append(ink.text(F["mono"], "contributions, last 12 months", 22, 366, 12, P["silk_dim"]))
    out.append(f'<line x1="22" y1="384" x2="338" y2="384" stroke="{P["silk_faint"]}" stroke-opacity="0.4"/>')
    for i, (label, sub, value) in enumerate(_readouts(act)):
        x = 22 + 110 * i
        first, _, rest = label.partition(" ")  # three columns: each label takes two short lines
        out.append(ink.text(F["mono_md"], first, x, 408, 10.5, P["silk_dim"], track=0.06))
        out.append(ink.text(F["mono_md"], rest, x, 422, 10.5, P["silk_dim"], track=0.06))
        out.append(ink.text(F["mono_sb"], f"{value:,}", x, 450, 24, P["silk"]))
        out.append(ink.text(F["mono"], sub, x, 466, 10.5, P["silk_faint"]))

    title, desc = _about(act)
    return document(W, H, ink, "".join(out), title=title, desc=desc, defs=DEFS, style=CSS)
