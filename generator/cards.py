"""The cards, drawn as the parts of one circuit board.

The hero is the main board, activity is an oscilloscope on the bench, the
languages are LED bar graphs, the toolchain is a tray of chips, and each
project is a plug-in module. Every colour comes from P and every typeface from
the `F` dict that build.py passes in, so a restyle is a change in one place.

Motion rules: anything animated must leave a complete card when animation is
off (reduced motion, or a viewer that ignores CSS/SMIL in images). So the
scope trace is visible by default and only *animates in*, the signal pulses are
invisible by default, and the scope beam starts hidden.
"""
from __future__ import annotations

import math
from datetime import date
from html import escape

from ghdata import MONTHS, Activity, month_label
from typeset import Ink

# One green family, from the board itself to the phosphor of the scope.
P = {
    "mask": "#0F3D29",        # solder mask: the surface of every board
    "mask_lo": "#0A2E1F",     # recessed areas, unlit LED segments
    "edge": "#2A7350",        # board edge highlight
    "trace": "#1E6844",       # copper traces under the mask
    "trace_lit": "#2E9163",   # tented vias, active traces
    "silk": "#E3F2E7",        # silkscreen: primary text
    "silk_body": "#C3E2CF",   # running text
    "silk_dim": "#9DC8AF",    # secondary text
    "silk_faint": "#5F957A",  # labels and fine print
    "tin": "#BCCDC2",         # exposed pads and pins
    "epoxy": "#0B1D15",       # chip packages
    "epoxy_edge": "#1C3B2D",
    "body": "#0A2219",        # the oscilloscope's case
    "glass": "#03130B",       # the oscilloscope's screen
    "grid": "#174C33",        # graticule
    "phosphor": "#5EF29C",    # scope trace, lit LEDs, signal pulses
    "phosphor_dim": "#2F9A62",
    "bloom": "#CFFFE3",       # hottest highlight
}

# LED bar segments run from a deep green to a pale mint, like a real bar graph
# running from its first segment to its last (but green the whole way).
LED_FROM, LED_TO = "#2DB872", "#B2FFD4"


# --- small helpers -----------------------------------------------------------

def num(v: float) -> str:
    s = f"{v:.2f}".rstrip("0").rstrip(".")
    return "0" if s == "-0" else s


def esc(s: str) -> str:
    return escape(str(s), quote=True)


def mix(a: str, b: str, t: float) -> str:
    ca = [int(a[i:i + 2], 16) for i in (1, 3, 5)]
    cb = [int(b[i:i + 2], 16) for i in (1, 3, 5)]
    return "#" + "".join(f"{round(x + (y - x) * t):02X}" for x, y in zip(ca, cb))


def document(w: int, h: int, ink: Ink, body: str, *, title: str, desc: str,
             defs: str = "", style: str = "") -> str:
    return (
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{w}" height="{h}" viewBox="0 0 {w} {h}" '
        f'role="img" aria-labelledby="title desc">'
        f'<title id="title">{esc(title)}</title><desc id="desc">{esc(desc)}</desc>'
        + (f"<style>{style}</style>" if style else "")
        + f"<defs>{defs}{ink.defs()}</defs>{body}</svg>\n"
    )


def rounded_rect_d(x: float, y: float, w: float, h: float, r: float) -> str:
    return (f"M{num(x + r)} {num(y)}H{num(x + w - r)}A{r} {r} 0 0 1 {num(x + w)} {num(y + r)}"
            f"V{num(y + h - r)}A{r} {r} 0 0 1 {num(x + w - r)} {num(y + h)}H{num(x + r)}"
            f"A{r} {r} 0 0 1 {num(x)} {num(y + h - r)}V{num(y + r)}A{r} {r} 0 0 1 {num(x + r)} {num(y)}Z")


def circle_d(cx: float, cy: float, r: float) -> str:
    return f"M{num(cx - r)} {num(cy)}a{r} {r} 0 1 0 {num(2 * r)} 0a{r} {r} 0 1 0 {num(-2 * r)} 0Z"


def corners(w: float, h: float, m: float) -> list[tuple[float, float]]:
    return [(m, m), (w - m, m), (m, h - m), (w - m, h - m)]


SHEEN = ('<linearGradient id="sheen" x1="0" y1="0" x2="0" y2="1">'
         '<stop offset="0" stop-color="#fff" stop-opacity="0.045"/>'
         '<stop offset="1" stop-color="#000" stop-opacity="0.14"/></linearGradient>')
EPOXY = ('<linearGradient id="epoxy" x1="0" y1="0" x2="0" y2="1">'
         '<stop offset="0" stop-color="#12291F"/><stop offset="1" stop-color="#08150F"/></linearGradient>')
GLOW = '<filter id="glow" x="-1" y="-1" width="3" height="3"><feGaussianBlur stdDeviation="3"/></filter>'


def board(w: float, h: float, *, r: float = 16, holes=(), hole_r: float = 4.2) -> tuple[str, str]:
    """A board with real drill holes: the page behind shows through them."""
    d = rounded_rect_d(0, 0, w, h, r) + "".join(circle_d(x, y, hole_r) for x, y in holes)
    defs = (
        '<pattern id="drill" width="14" height="14" patternUnits="userSpaceOnUse">'
        f'<circle cx="7" cy="7" r="0.75" fill="{P["silk"]}" fill-opacity="0.07"/></pattern>' + SHEEN
    )
    body = (
        f'<path d="{d}" fill="{P["mask"]}" fill-rule="evenodd"/>'
        f'<path d="{d}" fill="url(#drill)" fill-rule="evenodd"/>'
        f'<path d="{d}" fill="url(#sheen)" fill-rule="evenodd"/>'
        f'<path d="{rounded_rect_d(0.75, 0.75, w - 1.5, h - 1.5, r - 0.75)}" fill="none" '
        f'stroke="{P["edge"]}" stroke-width="1.5"/>'
        + "".join(
            f'<circle cx="{num(x)}" cy="{num(y)}" r="{num(hole_r + 1.6)}" fill="none" stroke="{P["tin"]}" stroke-width="3.2"/>'
            f'<circle cx="{num(x)}" cy="{num(y)}" r="{num(hole_r + 5.5)}" fill="none" stroke="{P["silk"]}" '
            f'stroke-opacity="0.22" stroke-width="0.8"/>'
            for x, y in holes)
    )
    return defs, body


def path_d(points) -> str:
    (x0, y0), *rest = points
    return f"M{num(x0)} {num(y0)}" + "".join(f"L{num(x)} {num(y)}" for x, y in rest)


def trace(points, *, width: float = 2.6, color: str | None = None, extra: str = "") -> str:
    return (f'<path d="{path_d(points)}" fill="none" stroke="{color or P["trace"]}" stroke-width="{width}" '
            f'stroke-linecap="round" stroke-linejoin="round"{extra}/>')


def via(x: float, y: float, r: float = 3.4) -> str:
    return (f'<circle cx="{num(x)}" cy="{num(y)}" r="{r}" fill="{P["trace_lit"]}"/>'
            f'<circle cx="{num(x)}" cy="{num(y)}" r="{num(r * 0.42)}" fill="{P["mask_lo"]}"/>')


def jog_h(x0, y0, x1, y1, turn_x):
    """Horizontal to turn_x, 45 degrees across to y1, horizontal to x1."""
    step = abs(y1 - y0) * (1 if x1 >= x0 else -1)
    return [(x0, y0), (turn_x, y0), (turn_x + step, y1), (x1, y1)]


def jog_v(x0, y0, x1, y1, turn_y):
    """Vertical to turn_y, 45 degrees across to x1, vertical to y1."""
    step = abs(x1 - x0) * (1 if y1 >= y0 else -1)
    return [(x0, y0), (x0, turn_y), (x1, turn_y + step), (x1, y1)]


def rect(x, y, w, h, extra: str = "") -> str:
    return f'<rect x="{num(x)}" y="{num(y)}" width="{num(w)}" height="{num(h)}"{extra}/>'


# --- hero: the main board ----------------------------------------------------

def hero(F, cfg: dict, today: date) -> str:
    W, H = 880, 300
    ink = Ink()
    board_defs, body = board(W, H, r=18, holes=corners(W, H, 20))
    out = [body]

    # Who: status LED, eyebrow, name.
    left = 52
    out.append(led(left + 5, 65))
    eyebrow = cfg["eyebrow"].upper()
    if ink.width(F["mono_md"], eyebrow, 11, 0.16) > 560:
        raise ValueError("hero eyebrow is too long: it would run into the chip")
    out.append(ink.text(F["mono_md"], eyebrow, left + 20, 69, 11, P["silk_dim"], track=0.16))
    name = cfg["name"].upper()
    size = 40.0
    while ink.width(F["display"], name, size, 0.03) > 530:
        size -= 0.5
    out.append(ink.text(F["display"], name, left, 124, size, P["silk"], track=0.03))

    # The chip that drives everything: part number is the handle, the date code
    # is the ISO year and week this card was drawn (as real chips print it).
    cx, cy, cs = 676, 84, 132
    chip, tips = qfp(cx, cy, cs, ink, F, cfg["chip"], f"DXB {today:%y}{today.isocalendar().week:02d}")

    # Nets: each focus area is a net label with a pad, routed back to the chip.
    nets = cfg["nets"]
    if not 1 <= len(nets) <= 3:
        raise ValueError("the hero has room for one to three nets")
    label_w = max(ink.width(F["mono_sb"], n["net"], 13, 0.06) for n in nets)
    detail_x = left + label_w + 18
    pad_x = max(detail_x + ink.width(F["mono"], n["detail"], 13) for n in nets) + 22
    rows = [176 + 28 * i for i in range(len(nets))]
    net_paths = []
    for i, (n, y) in enumerate(zip(nets, rows)):
        out.append(ink.text(F["mono_sb"], n["net"], left, y, 13, P["silk"], track=0.06))
        out.append(ink.text(F["mono"], n["detail"], detail_x, y, 13, P["silk_dim"]))
        px, py = tips["left"][4 + i]
        route = jog_h(px, py, pad_x + 4, y - 4, px - 16)
        if route[2][0] < pad_x + 16:
            raise ValueError("hero net details are too long to route back to the chip; shorten them")
        net_paths.append(route)

    copper = [trace(p) for p in net_paths]
    # Decorative fan-out from the other pins, routed at 45 degrees like a real layout.
    L, R, T, B = tips["left"], tips["right"], tips["top"], tips["bottom"]
    stubs = [
        ([L[0], (646, L[0][1])], (646, L[0][1])),
        ([L[2], (640, L[2][1])], (640, L[2][1])),
        (jog_v(*T[1], 687, 40, 60), (687, 40)),
        ([T[3], (T[3][0], 44)], (T[3][0], 44)),
        (jog_v(*T[5], 783, 38, 58), (783, 38)),
        (jog_v(*T[7], 821, 34, 64), (821, 34)),
        ([R[1], (846, R[1][1])], (846, R[1][1])),
        ([R[5], (846, R[5][1])], (846, R[5][1])),
        (jog_v(*B[0], 673, 262, 242), (673, 262)),
        ([B[2], (B[2][0], 258)], (B[2][0], 258)),
        (jog_v(*B[4], 769, 262, 242), (769, 262)),
        (jog_v(*B[6], 805, 254, 226), (805, 254)),
    ]
    for points, end in stubs:
        copper.append(trace(points))
        copper.append(via(*end))
    for i in (0, 2, 4, 6):  # these leave the board on the right edge
        copper.append(trace([R[i], (W, R[i][1])]))
    out.insert(1, "".join(copper))

    for y in rows:
        out.append(rect(pad_x, y - 8, 8, 8, f' fill="{P["tin"]}"'))
    # Signal pulses travel out from the chip along each net.
    for i, p in enumerate(net_paths):
        out.append(f'<path class="pulse n{i}" d="{path_d(p)}" pathLength="100"/>')

    out.append(chip)
    out.append(ink.text(F["mono"], "U1", cx - 21, cy - 18, 10, P["silk_faint"], track=0.1))
    out.append(ink.text(F["mono"], f"{cfg['chip']} · REV {today:%Y.%m}", 836, 283, 10, P["silk_faint"],
                        track=0.12, anchor="end"))

    style = (
        f".pulse{{fill:none;stroke:{P['bloom']};stroke-width:3;stroke-linecap:round;"
        "stroke-dasharray:6 140;stroke-dashoffset:6;"
        f"filter:drop-shadow(0 0 3px {P['phosphor']});"
        "animation:pulse 4.2s cubic-bezier(.45,0,.25,1) infinite}"
        ".n1{animation-delay:.35s}.n2{animation-delay:.7s}"
        "@keyframes pulse{0%{stroke-dashoffset:6}55%,100%{stroke-dashoffset:-100}}"
        ".led{animation:blink 2.6s ease-in-out infinite}"
        "@keyframes blink{0%,58%,100%{opacity:1}74%{opacity:.25}}"
        "@media (prefers-reduced-motion:reduce){.pulse{display:none}.led{animation:none}}"
    )
    title = f"{cfg['name']}: {cfg['eyebrow']}"
    desc = "; ".join(f"{n['net'].replace('_', ' ').title()}: {n['detail']}" for n in nets)
    return document(W, H, ink, "".join(out), title=title, desc=desc,
                    defs=board_defs + EPOXY + GLOW, style=style)


def led(x: float, y: float) -> str:
    """A 0603 LED: two tin pads either side of a glowing lens."""
    return (f'<rect x="{num(x - 8)}" y="{num(y - 3)}" width="3" height="6" fill="{P["tin"]}"/>'
            f'<rect x="{num(x + 5)}" y="{num(y - 3)}" width="3" height="6" fill="{P["tin"]}"/>'
            f'<g class="led"><circle cx="{num(x)}" cy="{num(y)}" r="9" fill="{P["phosphor"]}" '
            f'opacity="0.3" filter="url(#glow)"/>'
            f'<rect x="{num(x - 5)}" y="{num(y - 3)}" width="10" height="6" rx="1.5" fill="{P["phosphor"]}"/>'
            f'<rect x="{num(x - 1.5)}" y="{num(y - 2)}" width="3" height="4" rx="1" fill="{P["bloom"]}"/></g>')


def qfp(x, y, size, ink, F, marking, code, *, pins=8, pitch=14, length=9, width=5):
    """A square flat-pack chip. Returns (svg, tips) where tips[side][i] is pin i's outer end."""
    first = (size - pitch * (pins - 1)) / 2
    tips = {side: [] for side in ("left", "right", "top", "bottom")}
    metal = []
    for i in range(pins):
        o = first + pitch * i
        metal += [rect(x - length, y + o - width / 2, length, width),
                  rect(x + size, y + o - width / 2, length, width),
                  rect(x + o - width / 2, y - length, width, length),
                  rect(x + o - width / 2, y + size, width, length)]
        tips["left"].append((x - length, y + o))
        tips["right"].append((x + size + length, y + o))
        tips["top"].append((x + o, y - length))
        tips["bottom"].append((x + o, y + size + length))
    m = length + 6  # silkscreen courtyard around the pins
    svg = (
        rect(x - m, y - m, size + 2 * m, size + 2 * m,
             f' rx="3" fill="none" stroke="{P["silk"]}" stroke-opacity="0.25" stroke-width="0.8"')
        + f'<g fill="{P["tin"]}">{"".join(metal)}</g>'
        + rect(x, y, size, size, f' rx="4" fill="url(#epoxy)" stroke="{P["epoxy_edge"]}"')
        + f'<circle cx="{x + 13}" cy="{y + 13}" r="4" fill="#06110C" stroke="{P["epoxy_edge"]}"/>'
        + ink.text(F["display"], marking, x + size / 2, y + size / 2 + 2, 15, P["silk"], anchor="middle", track=0.04)
        + ink.text(F["mono"], code, x + size / 2, y + size / 2 + 22, 10, P["silk_faint"], anchor="middle", track=0.12)
    )
    return svg, tips


# --- activity: the oscilloscope ---------------------------------------------

def nice_step(peak: int, divisions: int) -> int:
    for step in (1, 2, 3, 4, 5, 6, 8, 10, 12, 15, 20, 25, 30, 40, 50, 60, 80, 100):
        if step * divisions >= peak:
            return step
    return math.ceil(peak / divisions / 50) * 50


def monotone_path(xs: list[float], ys: list[float]) -> str:
    """A smooth curve through the points that never overshoots them (Fritsch-Carlson),
    so a quiet week never dips below zero on screen."""
    count = len(xs)
    dx = [xs[i + 1] - xs[i] for i in range(count - 1)]
    slope = [(ys[i + 1] - ys[i]) / dx[i] for i in range(count - 1)]
    m = [slope[0]] + [0.0 if slope[i - 1] * slope[i] <= 0 else (slope[i - 1] + slope[i]) / 2
                      for i in range(1, count - 1)] + [slope[-1]]
    for i in range(count - 1):
        if slope[i] == 0:
            m[i] = m[i + 1] = 0.0
            continue
        a, b = m[i] / slope[i], m[i + 1] / slope[i]
        if a * a + b * b > 9:
            t = 3 / math.sqrt(a * a + b * b)
            m[i], m[i + 1] = t * a * slope[i], t * b * slope[i]
    d = f"M{num(xs[0])} {num(ys[0])}"
    for i in range(count - 1):
        h = dx[i]
        d += (f"C{num(xs[i] + h / 3)} {num(ys[i] + m[i] * h / 3)} "
              f"{num(xs[i + 1] - h / 3)} {num(ys[i + 1] - m[i + 1] * h / 3)} {num(xs[i + 1])} {num(ys[i + 1])}")
    return d


def activity_card(F, act: Activity) -> str:
    W, H = 880, 300
    ink = Ink()
    out = [
        f'<rect width="{W}" height="{H}" rx="18" fill="{P["body"]}"/>',
        f'<rect width="{W}" height="{H}" rx="18" fill="url(#sheen)"/>',
        f'<path d="{rounded_rect_d(0.75, 0.75, W - 1.5, H - 1.5, 17.25)}" fill="none" stroke="{P["edge"]}" stroke-width="1.5"/>',
        f'<rect x="20" y="20" width="600" height="260" rx="14" fill="#061A11" stroke="#173F2D"/>',
        f'<rect x="28" y="28" width="584" height="244" rx="10" fill="url(#crt)"/>',
    ]

    # 13 divisions of 4 weeks across, 6 divisions up.
    x0, x1, y0, y1 = 72, 592, 66, 234
    cols, rows = 13, 6
    div_w, div_h = (x1 - x0) / cols, (y1 - y0) / rows
    step = nice_step(act.peak, rows)
    top = step * rows

    grid = []
    for i in range(cols + 1):
        x = x0 + i * div_w
        dash = "" if i in (0, cols) else ' stroke-dasharray="1 3"'
        grid.append(f'<line x1="{num(x)}" y1="{y0}" x2="{num(x)}" y2="{y1}"{dash}/>')
    for j in range(rows + 1):
        y = y0 + j * div_h
        dash = "" if j in (0, rows) else ' stroke-dasharray="1 3"'
        grid.append(f'<line x1="{x0}" y1="{num(y)}" x2="{x1}" y2="{num(y)}"{dash}/>')
    yc = y0 + rows / 2 * div_h
    for k in range(cols * 5 + 1):  # minor ticks on the centre line, as on a real graticule
        x = x0 + k * div_w / 5
        grid.append(f'<line x1="{num(x)}" y1="{num(yc - 2.5)}" x2="{num(x)}" y2="{num(yc + 2.5)}"/>')
    out.append(f'<g stroke="{P["grid"]}" stroke-width="1">{"".join(grid)}</g>')

    slot = (x1 - x0) / len(act.weeks)
    xs = [x0 + (i + 0.5) * slot for i in range(len(act.weeks))]
    ys = [y1 - v / top * (y1 - y0) for v in act.weeks]
    d = monotone_path(xs, ys)

    # Weekly average as the trigger level, marked on the right edge as a scope does.
    avg = sum(act.weeks) / len(act.weeks)
    ay = y1 - avg / top * (y1 - y0)
    out.append(f'<line x1="{x0}" y1="{num(ay)}" x2="{x1}" y2="{num(ay)}" stroke="{P["phosphor"]}" '
               f'stroke-opacity="0.45" stroke-dasharray="4 4"/>')
    out.append(f'<path d="M{x1 + 11} {num(ay - 4.5)}L{x1 + 3} {num(ay)}L{x1 + 11} {num(ay + 4.5)}Z" fill="{P["phosphor"]}"/>')
    # Its label sits on the line wherever the trace leaves the most room, and
    # is drawn after the trace so it stays legible if no spot is fully clear.
    avg_text = f"AVG {avg:.0f} / WK"
    aw = ink.width(F["mono_md"], avg_text, 10.5, 0.06)
    top_edge, bottom_edge = ay - 19, ay - 2

    def clearance(xa: float) -> float:
        near = [y for x, y in zip(xs, ys) if xa - 16 <= x <= xa + aw + 16]
        return min((0.0 if top_edge <= y <= bottom_edge else min(abs(y - top_edge), abs(y - bottom_edge)))
                   for y in near) if near else 99.0

    ax = max(range(x0 + 6, int(x1 - 6 - aw) + 1, 4), key=lambda xa: (min(clearance(xa), 12), xa))
    avg_label = (rect(ax - 4, top_edge, aw + 8, 15, f' rx="2" fill="{P["glass"]}" fill-opacity="0.85"')
                 + ink.text(F["mono_md"], avg_text, ax, ay - 6.5, 10.5, P["phosphor"], track=0.06))

    # Cursor on the busiest week.
    pi = max(range(len(act.weeks)), key=lambda i: (act.weeks[i], i))
    px = xs[pi]
    out.append(f'<line x1="{num(px)}" y1="{y0}" x2="{num(px)}" y2="{y1}" stroke="{P["bloom"]}" '
               f'stroke-opacity="0.5" stroke-dasharray="2 3"/>')
    peak_text = f"PEAK {act.peak} · {act.peak_start.day} {MONTHS[act.peak_start.month - 1].upper()}"
    pw = ink.width(F["mono_md"], peak_text, 10.5, 0.06)
    lx = px + 7 if px + 7 + pw < x1 - 4 else px - 7 - pw
    out.append(rect(lx - 4, y0 + 5, pw + 8, 16, f' rx="2" fill="{P["glass"]}" fill-opacity="0.9"'))
    out.append(ink.text(F["mono_md"], peak_text, lx, y0 + 17, 10.5, P["bloom"], track=0.06))

    # The trace: a wide blurred pass for the phosphor bloom, then the line, then its hot core.
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

    # Axes text: scale at the corners, months along the bottom.
    out.append(ink.text(F["mono"], str(top), x0 - 8, y0 + 3.5, 10, P["phosphor_dim"], anchor="end"))
    out.append(ink.text(F["mono"], "0", x0 - 8, y1 + 3.5, 10, P["phosphor_dim"], anchor="end"))
    for idx, day in enumerate(act.days):
        if day and day.day == 1:
            x = x0 + (idx + 0.5) * (x1 - x0) / len(act.days)
            out.append(f'<line x1="{num(x)}" y1="{y1}" x2="{num(x)}" y2="{y1 + 4}" stroke="{P["phosphor_dim"]}"/>')
            out.append(ink.text(F["mono"], MONTHS[day.month - 1].upper(), x, y1 + 19, 10, P["phosphor_dim"],
                                anchor="middle", track=0.08))

    # Top bar: channel and scale, as the scope prints them.
    out.append(rect(40, 39, 30, 16, f' rx="3" fill="none" stroke="{P["phosphor"]}"'))
    out.append(ink.text(F["mono_sb"], "CH1", 55, 51, 9.5, P["phosphor"], anchor="middle"))
    out.append(ink.text(F["sans_md"], "Contributions per week", 80, 52, 13.5, P["bloom"]))
    out.append(ink.text(F["mono"], f"{step} / div    4 wk / div", 600, 51, 11, P["phosphor_dim"], anchor="end"))

    # Measure panel.
    mx, mr = 644, 856
    out.append(ink.text(F["display"], "MEASURE", mx, 47, 10.5, P["silk_faint"], track=0.24))
    out.append(ink.text(F["display"], f"{act.total:,}", mx - 2, 100, 38, P["silk"]))
    out.append(ink.text(F["mono"], "contributions, last 12 months", mx, 120, 11, P["silk_dim"]))
    out.append(f'<line x1="{mx}" y1="140" x2="{mr}" y2="140" stroke="{P["silk_faint"]}" stroke-opacity="0.4"/>')
    readouts = [
        ("BUSIEST WEEK", f"week of {act.peak_start.day} {MONTHS[act.peak_start.month - 1]}", act.peak),
        ("ACTIVE DAYS", "of the last 365", act.active_days),
        ("LONGEST STREAK", "days in a row", act.longest_streak),
    ]
    for i, (label, sub, value) in enumerate(readouts):
        y = 172 + 40 * i
        out.append(ink.text(F["mono_md"], label, mx, y, 11, P["silk_dim"], track=0.1))
        out.append(ink.text(F["mono"], sub, mx, y + 16, 10.5, P["silk_faint"]))
        out.append(ink.text(F["mono_sb"], f"{value:,}", mr, y + 9, 21, P["silk"], anchor="end"))

    defs = (
        SHEEN
        + '<radialGradient id="crt" cx="0.5" cy="0.45" r="0.75">'
        f'<stop offset="0" stop-color="#072318"/><stop offset="1" stop-color="{P["glass"]}"/></radialGradient>'
        '<filter id="bloom" x="-0.2" y="-0.5" width="1.4" height="2"><feGaussianBlur stdDeviation="3"/></filter>'
    )
    style = (
        ".draw{stroke-dasharray:100 100;animation:draw 2.4s cubic-bezier(.3,0,.2,1) .2s backwards}"
        "@keyframes draw{from{stroke-dashoffset:100}to{stroke-dashoffset:0}}"
        "@media (prefers-reduced-motion:reduce){.draw{animation:none}.beam{display:none}}"
    )
    title = f"{act.total:,} contributions in the last 12 months"
    desc = (f"Oscilloscope-style chart of contributions per week. Busiest week: {act.peak}, "
            f"starting {act.peak_start:%d %b %Y}. Active on {act.active_days} of the last 365 days. "
            f"Longest streak: {act.longest_streak} days.")
    return document(W, H, ink, "".join(out), title=title, desc=desc, defs=defs, style=style)


# --- languages: LED bar graphs ---------------------------------------------

def languages_card(F, langs: list[tuple[str, float]]) -> str:
    W, H = 430, 320
    ink = Ink()
    board_defs, body = board(W, H, holes=corners(W, H, 18))
    out = [body]
    out.append(ink.text(F["display"], "LANGUAGES", 40, 50, 12, P["silk"], track=0.16))
    out.append(ink.text(F["mono"], "share of code, public repos", 390, 50, 10.5, P["silk_faint"], anchor="end"))

    segments, bar_x, bar_w = 20, 132, 202
    slot = (bar_w - 8) / segments
    lit_all, glow = [], []
    for i, (name, share) in enumerate(langs):
        y = 94 + 37 * i
        out.append(ink.text(F["sans_md"], name, 40, y, 14, P["silk"]))
        out.append(rect(bar_x, y - 15, bar_w, 20, f' rx="3" fill="url(#epoxy)" stroke="{P["epoxy_edge"]}"'))
        lit = max(1, round(share * segments)) if share > 0 else 0
        for s in range(segments):
            sx, sy = bar_x + 4 + s * slot, y - 11
            if s < lit:
                colour = mix(LED_FROM, LED_TO, s / (segments - 1))
                lit_all.append(rect(sx, sy, slot - 3, 12, f' rx="1.2" fill="{colour}"'))
                glow.append(rect(sx, sy, slot - 3, 12, f' fill="{colour}"'))
            else:
                out.append(rect(sx, sy, slot - 3, 12, f' rx="1.2" fill="{P["mask_lo"]}" stroke="#123B29" stroke-width="0.8"'))
        out.append(ink.text(F["mono_md"], f"{share * 100:.1f}%", 390, y, 12.5, P["silk"], anchor="end"))
    out.append(f'<g opacity="0.6" filter="url(#glow)">{"".join(glow)}</g>{"".join(lit_all)}')

    title = "Languages by share of code in public repositories"
    desc = ", ".join(f"{name} {share * 100:.1f}%" for name, share in langs)
    return document(W, H, ink, "".join(out), title=title, desc=desc, defs=board_defs + EPOXY + GLOW)


# --- toolchain: a tray of chips ---------------------------------------------

def toolchain_card(F, parts: list[dict]) -> str:
    W, H = 430, 320
    ink = Ink()
    board_defs, body = board(W, H, holes=corners(W, H, 18))
    out = [body]
    out.append(ink.text(F["display"], "TOOLCHAIN", 40, 50, 12, P["silk"], track=0.16))
    out.append(ink.text(F["mono"], "what I build with", 390, 50, 10.5, P["silk_faint"], anchor="end"))

    cols, cw, ch = 3, 108, 36
    col_w = (W - 56) / cols
    for i, part in enumerate(parts):
        r, c = divmod(i, cols)
        x = 28 + col_w * c + (col_w - cw) / 2
        y = 70 + 58 * r
        pins = "".join(rect(x + 16 + k * (cw - 32) / 3 - 3, py, 6, 5)
                       for k in range(4) for py in (y - 5, y + ch))
        out.append(f'<g fill="{P["tin"]}">{pins}</g>')
        out.append(rect(x, y, cw, ch, f' rx="3" fill="url(#epoxy)" stroke="{P["epoxy_edge"]}"'))
        out.append(f'<path d="M{num(x)} {num(y + ch / 2 - 4.5)}A4.5 4.5 0 0 1 {num(x)} {num(y + ch / 2 + 4.5)}Z" fill="#06110C"/>')
        out.append(ink.text(F["mono_sb"], part["part"], x + cw / 2 + 2, y + 17, 11.5, P["silk"], anchor="middle", track=0.04))
        out.append(ink.text(F["mono_md"], part["role"], x + cw / 2 + 2, y + 29, 9, P["silk_dim"], anchor="middle", track=0.08))

    title = "Toolchain"
    desc = ", ".join(f"{p['part']} ({p['role'].lower()})" for p in parts)
    return document(W, H, ink, "".join(out), title=title, desc=desc, defs=board_defs + EPOXY)


# --- projects: plug-in modules ----------------------------------------------

def star_d(cx: float, cy: float, r: float) -> str:
    points = []
    for k in range(10):
        a = -math.pi / 2 + k * math.pi / 5
        rr = r if k % 2 == 0 else r * 0.45
        points.append((cx + rr * math.cos(a), cy + rr * math.sin(a)))
    return path_d(points) + "Z"


def project_card(F, proj: dict, repo: dict, hide_languages: list[str]) -> str:
    W, H = 430, 200
    ink = Ink()
    board_defs, body = board(W, H, r=14, holes=[(18, 18), (W - 18, 18)])
    out = [body]

    tag = proj["tag"].upper()
    tw = ink.width(F["mono_md"], tag, 10, 0.14)
    out.append(rect(36, 9.5, tw + 14, 18, f' rx="3" fill="none" stroke="{P["silk_faint"]}"'))
    out.append(ink.text(F["mono_md"], tag, 43, 22.5, 10, P["silk_dim"], track=0.14))
    out.append(ink.text(F["mono_md"], "OPEN REPO ↗", 392, 22.5, 10, P["silk_faint"], anchor="end", track=0.08))

    out.append(ink.text(F["display"], proj["title"], 24, 64, 17, P["silk"], track=0.02))
    blurb = proj.get("blurb") or repo["description"] or ""
    lines = ink.wrap(F["sans"], blurb, 13.5, W - 48)
    if len(lines) > 3:
        raise ValueError(f"blurb for {repo['name']} needs {len(lines)} lines on its card; keep it to 3")
    for i, line in enumerate(lines):
        out.append(ink.text(F["sans"], line, 24, 90 + 18.5 * i, 13.5, P["silk_body"]))

    # Meta row: languages by size, stars when there are any, last push.
    x, y = 24, 158
    shades = [P["phosphor"], "#3CC27D", "#2A8B5B"]
    langs = [e["node"]["name"] for e in repo["languages"]["edges"] if e["node"]["name"] not in hide_languages][:3]
    for shade, lang in zip(shades, langs):
        out.append(f'<circle cx="{num(x + 3.5)}" cy="{num(y - 3.5)}" r="3.5" fill="{shade}"/>')
        out.append(ink.text(F["mono"], lang, x + 11, y, 11, P["silk_dim"]))
        x += 11 + ink.width(F["mono"], lang, 11) + 14
    if repo["stargazerCount"]:
        out.append(f'<path d="{star_d(x + 5, y - 4, 5.5)}" fill="{P["silk_dim"]}"/>')
        out.append(ink.text(F["mono"], str(repo["stargazerCount"]), x + 14, y, 11, P["silk_dim"]))
    pushed = date.fromisoformat(repo["pushedAt"][:10])
    out.append(ink.text(F["mono"], f"updated {month_label(pushed)}", W - 24, y, 11, P["silk_faint"], anchor="end"))

    # Edge connector along the bottom: this is a module that plugs into the board.
    fingers, key = [], 9
    for k in range(27):
        if k != key:
            fingers.append(rect(53 + k * 12, 188, 6, 12))
    out.append(f'<g fill="{mix(P["tin"], P["mask"], 0.35)}">{"".join(fingers)}</g>')

    title = f"{proj['title']}: {proj['tag']}"
    desc = blurb
    return document(W, H, ink, "".join(out), title=title, desc=desc, defs=board_defs)


# --- links: a connector badge -----------------------------------------------

def link_badge(F, label: str, handle: str) -> str:
    H = 44
    ink = Ink()
    w1 = ink.width(F["display"], label.upper(), 10.5, 0.16)
    w2 = ink.width(F["mono"], handle, 10)
    W = math.ceil(48 + max(w1, w2) + 18)
    board_defs, body = board(W, H, r=10)
    pins = "".join(rect(14 + 9 * c, 9 + 9 * r, 6, 6) for r in range(3) for c in range(2))
    out = [body,
           rect(10, 5, 23, 34, f' rx="2" fill="none" stroke="{P["silk"]}" stroke-opacity="0.3" stroke-width="0.8"'),
           f'<g fill="{P["tin"]}">{pins}</g>',
           ink.text(F["display"], label.upper(), 46, 20, 10.5, P["silk"], track=0.16),
           ink.text(F["mono"], handle, 46, 34, 10, P["silk_dim"])]
    return document(W, H, ink, "".join(out), title=f"{label}: {handle}", desc=f"{label} profile", defs=board_defs)
