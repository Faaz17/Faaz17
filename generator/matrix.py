"""The contribution calendar as an LED dot-matrix display.

One LED per day, in the same columns and rows as the GitHub profile graph
(a column is a week, Sunday at the top), lit at GitHub's own four levels, so
it lights the same cells as the graph below the README. A chain of MAX7219
matrix drivers runs along the board under it, and a faint scan line sweeps the
display the way a multiplexed matrix refreshes.

Desktop shows the year in one panel. A phone gets two half-year panels, so
each LED stays big enough to see.
"""
from __future__ import annotations

from ghdata import MONTHS, Activity
from parts import (BOARD_DEFS, EPOXY, GLOW, P, Copper, board, corners, designator, document, header, num, rect,
                   soic)
from typeset import Ink

# Off, then GitHub's four quartiles, in the LED bar graph's ramp.
LEVEL_FILL = ["#0D2A1D", "#1E7A4E", "#2DB872", "#5EF29C", "#C6FFE0"]
# The scan runs on SMIL; with motion reduced (or no SMIL) it stays parked outside the panel.
SCAN_CSS = "@media (prefers-reduced-motion:reduce){.scan{display:none}}"


def _panel(ink: Ink, F, weeks: list, x: float, y: float, pitch: float, led: float, *, labels: str) -> tuple[str, float]:
    """One LED matrix module with its month labels above. Returns (svg, panel width)."""
    pad = (pitch - led) / 2 + 3
    w = len(weeks) * pitch + 2 * pad
    h = 7 * pitch + 2 * pad
    out = [rect(x, y, w, h, f' rx="4" fill="url(#epoxy)" stroke="{P["epoxy_edge"]}"')]
    lit, glow = [], []
    last_month = None
    for c, week in enumerate(weeks):
        first = week[0][0]
        if first.month != last_month:
            if last_month is not None or first.day <= 7:
                out.append(ink.text(F["mono"], MONTHS[first.month - 1].upper(), x + pad + c * pitch, y - 7,
                                    9.5 if labels == "full" else 9, P["silk_faint"], track=0.06))
            last_month = first.month
        for day, count, level in week:
            r = (day.weekday() + 1) % 7  # Sunday first, as GitHub draws it
            lx, ly = x + pad + c * pitch, y + pad + r * pitch
            cell = rect(lx, ly, led, led, f' rx="{num(led * 0.22)}" fill="{LEVEL_FILL[level]}"')
            (lit if level else out).append(cell)
            if level >= 3:
                glow.append(rect(lx, ly, led, led, f' fill="{LEVEL_FILL[level]}"'))
    out.append(f'<g opacity="0.55" filter="url(#glow)">{"".join(glow)}</g>{"".join(lit)}')
    # The refresh scan: a soft bright column sweeping the module.
    out.append(f'<g clip-path="url(#clip{int(x)}_{int(y)})"><rect class="scan" x="{num(x - 24)}" y="{num(y)}" '
               f'width="24" height="{num(h)}" fill="url(#scanfade)">'
               f'<animateTransform attributeName="transform" type="translate" from="0 0" to="{num(w + 24)} 0" '
               'dur="6s" repeatCount="indefinite"/></rect></g>')
    clip_rect = rect(x, y, w, h, ' rx="4"')
    clip = f'<clipPath id="clip{int(x)}_{int(y)}">{clip_rect}</clipPath>'
    return clip + "".join(out), w


def _legend(ink: Ink, F, right: float, y: float, led: float) -> str:
    out = [ink.text(F["mono_md"], "MORE", right, y, 9.5, P["silk_faint"], anchor="end", track=0.1)]
    x = right - ink.width(F["mono_md"], "MORE", 9.5, 0.1) - 8 - led
    for level in (4, 3, 2, 1, 0):
        out.append(rect(x, y - led + 1, led, led, f' rx="{num(led * 0.22)}" fill="{LEVEL_FILL[level]}"'))
        x -= led + 4
    out.append(ink.text(F["mono_md"], "LESS", x + led - 4, y, 9.5, P["silk_faint"], anchor="end", track=0.1))
    return "".join(out)


def _about(act: Activity) -> tuple[str, str]:
    active = sum(1 for w in act.calendar for _, c, _ in w if c)
    return (f"{act.total:,} contributions in the last year",
            f"Contribution calendar as an LED matrix: one LED per day over the last year, "
            f"lit on {active} days, brighter for busier days.")


DEFS = (BOARD_DEFS, EPOXY, GLOW,
        '<linearGradient id="scanfade" x1="0" y1="0" x2="1" y2="0">'
        '<stop offset="0" stop-color="#CFFFE3" stop-opacity="0"/>'
        '<stop offset="0.7" stop-color="#CFFFE3" stop-opacity="0.10"/>'
        '<stop offset="1" stop-color="#CFFFE3" stop-opacity="0"/></linearGradient>')


def matrix_desktop(F, act: Activity) -> str:
    W, H = 880, 268
    ink = Ink()
    pitch, led = 14, 10
    cu = Copper()
    panel, pw = _panel(ink, F, act.calendar, 86, 80, pitch, led, labels="full")
    out = [ink.text(F["display"], "CONTRIBUTIONS", 40, 50, 12, P["silk"], track=0.16),
           ink.text(F["mono"], f"{act.total:,} in the last year, one LED per day", W - 40, 50, 10.5,
                    P["silk_faint"], anchor="end")]
    for label, r in (("MON", 1), ("WED", 3), ("FRI", 5)):
        out.append(ink.text(F["mono"], label, 78, 80 + 3 + (pitch - led) / 2 + r * pitch + led * 0.8, 9,
                            P["silk_faint"], anchor="end", track=0.04))
    out.append(panel)
    out.append(_legend(ink, F, 86 + pw, 210, led))

    # Six MAX7219 drivers in a daisy chain, fed from a header: DOUT of each to DIN of the next.
    chips, y_chip = [], 222
    hdr, pins = header(40, y_chip - 2, 3, pitch=12)
    xs = [92 + 92 * k for k in range(6)]
    for k, cx in enumerate(xs):
        svg, top, bottom = soic(cx, y_chip, 70, 14, ink, F, "MAX7219", pins=8)
        chips.append(svg)
        if k:
            cu.trace([(xs[k - 1] + 70, y_chip + 7), (cx, y_chip + 7)], width=1.8)
        cu.trace([top[3], (top[3][0], 80 + 7 * pitch + 2 * ((pitch - led) / 2 + 3))], width=1.4)
    cu.trace([(pins[0][0], y_chip + 4), (pins[0][0], y_chip + 22), (xs[0] - 6, y_chip + 22), (xs[0] - 6, y_chip + 7),
              (xs[0], y_chip + 7)], width=1.8)
    body = (board(W, H, holes=corners(W, H, 18), under=cu.gaps()) + cu.top() + hdr + "".join(chips)
            + designator(ink, F, "J5 DIN", 40, y_chip + 26) + "".join(out))
    title, desc = _about(act)
    return document(W, H, ink, body, title=title, desc=desc, defs=DEFS, style=SCAN_CSS)


def matrix_mobile(F, act: Activity) -> str:
    W = 360
    ink = Ink()
    pitch, led = 11, 8
    half = (len(act.calendar) + 1) // 2
    out = [ink.text(F["display"], "CONTRIBUTIONS", 36, 46, 13, P["silk"], track=0.16),
           ink.text(F["mono"], f"{act.total:,} in the last year, one LED per day", 36, 66, 11, P["silk_faint"])]
    y = 100
    for part in (act.calendar[:half], act.calendar[half:]):
        panel, pw = _panel(ink, F, part, 44, y, pitch, led, labels="short")
        out.append(panel)
        for label, r in (("M", 1), ("W", 3), ("F", 5)):
            out.append(ink.text(F["mono"], label, 36, y + 3 + (pitch - led) / 2 + r * pitch + led * 0.8, 9,
                                P["silk_faint"], anchor="end"))
        y += 7 * pitch + 2 * ((pitch - led) / 2 + 3) + 30
    out.append(_legend(ink, F, 44 + pw, y - 6, led))
    H = y + 22
    body = board(W, H, holes=corners(W, H, 16), hole_r=3.6) + "".join(out)
    title, desc = _about(act)
    return document(W, H, ink, body, title=title, desc=desc, defs=DEFS, style=SCAN_CSS)
