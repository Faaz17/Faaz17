"""Shared parts for every card: the palette, boards, copper, chips, and the
SVG document wrapper.

Every colour comes from P and every typeface from the `F` dict that build.py
passes around, so a restyle is a change in one place.

Motion rule: anything animated must leave a complete card when animation is
off (reduced motion, or a viewer that ignores CSS/SMIL in images). Signal
pulses are therefore invisible by default, the scope trace is visible by
default and only animates in, and the scope beam starts hidden.
"""
from __future__ import annotations

import math
from html import escape

# One green family, from the board itself to the phosphor of the scope.
P = {
    "mask": "#0F3D29",        # solder mask: the surface of every board
    "mask_lo": "#0A2E1F",     # recessed areas, unlit LED segments
    "edge": "#2A7350",        # board edge highlight
    "trace": "#1E6844",       # copper traces under the mask
    "trace_lit": "#2E9163",   # tented vias, signal arrows
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


def num(v: float) -> str:
    s = f"{v:.2f}".rstrip("0").rstrip(".")
    return "0" if s == "-0" else s


def esc(s: str) -> str:
    return escape(str(s), quote=True)


def mix(a: str, b: str, t: float) -> str:
    ca = [int(a[i:i + 2], 16) for i in (1, 3, 5)]
    cb = [int(b[i:i + 2], 16) for i in (1, 3, 5)]
    return "#" + "".join(f"{round(x + (y - x) * t):02X}" for x, y in zip(ca, cb))


# --- <defs> snippets. document() includes each one once. ---------------------

SHEEN = ('<linearGradient id="sheen" x1="0" y1="0" x2="0" y2="1">'
         '<stop offset="0" stop-color="#fff" stop-opacity="0.045"/>'
         '<stop offset="1" stop-color="#000" stop-opacity="0.14"/></linearGradient>')
BOARD_DEFS = ('<pattern id="drill" width="14" height="14" patternUnits="userSpaceOnUse">'
              f'<circle cx="7" cy="7" r="0.75" fill="{P["silk"]}" fill-opacity="0.07"/></pattern>' + SHEEN)
EPOXY = ('<linearGradient id="epoxy" x1="0" y1="0" x2="0" y2="1">'
         '<stop offset="0" stop-color="#12291F"/><stop offset="1" stop-color="#08150F"/></linearGradient>')
GLOW = '<filter id="glow" x="-1" y="-1" width="3" height="3"><feGaussianBlur stdDeviation="3"/></filter>'

# Signal pulses. `.pulse` runs the hero's nets out of step with each other;
# `.flow` hands one pulse along a diagram, edge after edge (.s1 starts as .s0 lands).
PULSE_CSS = (
    f".pulse,.flow{{fill:none;stroke:{P['bloom']};stroke-width:3;stroke-linecap:round;"
    "stroke-dasharray:6 140;stroke-dashoffset:6;"
    f"filter:drop-shadow(0 0 3px {P['phosphor']})}}"
    ".pulse{animation:pulse 4.2s cubic-bezier(.45,0,.25,1) infinite}"
    ".p1{animation-delay:.35s}.p2{animation-delay:.7s}"
    "@keyframes pulse{0%{stroke-dashoffset:6}55%,100%{stroke-dashoffset:-100}}"
    ".flow{animation:flow 5.5s linear infinite}"
    ".s1{animation-delay:1.1s}.s2{animation-delay:2.2s}.s3{animation-delay:3.3s}.s4{animation-delay:4.4s}"
    "@keyframes flow{0%{stroke-dashoffset:6}20%,100%{stroke-dashoffset:-100}}"
    ".led{animation:blink 2.6s ease-in-out infinite}"
    "@keyframes blink{0%,58%,100%{opacity:1}74%{opacity:.25}}"
    "@media (prefers-reduced-motion:reduce){.pulse,.flow{display:none}.led{animation:none}}"
)


def document(w: float, h: float, ink, body: str, *, title: str, desc: str,
             defs=(), style: str = "") -> str:
    unique = list(dict.fromkeys(defs))
    return (
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{num(w)}" height="{num(h)}" '
        f'viewBox="0 0 {num(w)} {num(h)}" role="img" aria-labelledby="title desc">'
        f'<title id="title">{esc(title)}</title><desc id="desc">{esc(desc)}</desc>'
        + (f"<style>{style}</style>" if style else "")
        + f"<defs>{''.join(unique)}{ink.defs()}</defs>{body}</svg>\n"
    )


# --- geometry ----------------------------------------------------------------

def rounded_rect_d(x: float, y: float, w: float, h: float, r: float) -> str:
    return (f"M{num(x + r)} {num(y)}H{num(x + w - r)}A{r} {r} 0 0 1 {num(x + w)} {num(y + r)}"
            f"V{num(y + h - r)}A{r} {r} 0 0 1 {num(x + w - r)} {num(y + h)}H{num(x + r)}"
            f"A{r} {r} 0 0 1 {num(x)} {num(y + h - r)}V{num(y + r)}A{r} {r} 0 0 1 {num(x + r)} {num(y)}Z")


def circle_d(cx: float, cy: float, r: float) -> str:
    return f"M{num(cx - r)} {num(cy)}a{r} {r} 0 1 0 {num(2 * r)} 0a{r} {r} 0 1 0 {num(-2 * r)} 0Z"


def corners(w: float, h: float, m: float, x: float = 0, y: float = 0) -> list[tuple[float, float]]:
    return [(x + m, y + m), (x + w - m, y + m), (x + m, y + h - m), (x + w - m, y + h - m)]


def rect(x, y, w, h, extra: str = "") -> str:
    return f'<rect x="{num(x)}" y="{num(y)}" width="{num(w)}" height="{num(h)}"{extra}/>'


def path_d(points) -> str:
    (x0, y0), *rest = points
    return f"M{num(x0)} {num(y0)}" + "".join(f"L{num(x)} {num(y)}" for x, y in rest)


def jog_h(x0, y0, x1, y1, turn_x):
    """Horizontal to turn_x, 45 degrees across to y1, horizontal to x1."""
    step = abs(y1 - y0) * (1 if x1 >= x0 else -1)
    return [(x0, y0), (turn_x, y0), (turn_x + step, y1), (x1, y1)]


def jog_v(x0, y0, x1, y1, turn_y):
    """Vertical to turn_y, 45 degrees across to x1, vertical to y1."""
    step = abs(x1 - x0) * (1 if y1 >= y0 else -1)
    return [(x0, y0), (x0, turn_y), (x1, turn_y + step), (x1, y1)]


def star_d(cx: float, cy: float, r: float) -> str:
    points = []
    for k in range(10):
        a = -math.pi / 2 + k * math.pi / 5
        rr = r if k % 2 == 0 else r * 0.45
        points.append((cx + rr * math.cos(a), cy + rr * math.sin(a)))
    return path_d(points) + "Z"


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


# --- parts -------------------------------------------------------------------

def board(w: float, h: float, *, x: float = 0, y: float = 0, r: float = 16,
          holes=(), hole_r: float = 4.2) -> str:
    """A board with real drill holes, so the page shows through them. Needs BOARD_DEFS."""
    d = rounded_rect_d(x, y, w, h, r) + "".join(circle_d(hx, hy, hole_r) for hx, hy in holes)
    return (
        f'<path d="{d}" fill="{P["mask"]}" fill-rule="evenodd"/>'
        f'<path d="{d}" fill="url(#drill)" fill-rule="evenodd"/>'
        f'<path d="{d}" fill="url(#sheen)" fill-rule="evenodd"/>'
        f'<path d="{rounded_rect_d(x + 0.75, y + 0.75, w - 1.5, h - 1.5, r - 0.75)}" fill="none" '
        f'stroke="{P["edge"]}" stroke-width="1.5"/>'
        + "".join(
            f'<circle cx="{num(hx)}" cy="{num(hy)}" r="{num(hole_r + 1.6)}" fill="none" stroke="{P["tin"]}" stroke-width="3.2"/>'
            f'<circle cx="{num(hx)}" cy="{num(hy)}" r="{num(hole_r + 5.5)}" fill="none" stroke="{P["silk"]}" '
            f'stroke-opacity="0.22" stroke-width="0.8"/>'
            for hx, hy in holes)
    )


def trace(points, *, width: float = 2.6, color: str | None = None, extra: str = "") -> str:
    return (f'<path d="{path_d(points)}" fill="none" stroke="{color or P["trace"]}" stroke-width="{width}" '
            f'stroke-linecap="round" stroke-linejoin="round"{extra}/>')


def via(x: float, y: float, r: float = 3.4) -> str:
    return (f'<circle cx="{num(x)}" cy="{num(y)}" r="{r}" fill="{P["trace_lit"]}"/>'
            f'<circle cx="{num(x)}" cy="{num(y)}" r="{num(r * 0.42)}" fill="{P["mask_lo"]}"/>')


def led(x: float, y: float) -> str:
    """A 0603 LED: two tin pads either side of a glowing lens. Needs GLOW."""
    return (f'<rect x="{num(x - 8)}" y="{num(y - 3)}" width="3" height="6" fill="{P["tin"]}"/>'
            f'<rect x="{num(x + 5)}" y="{num(y - 3)}" width="3" height="6" fill="{P["tin"]}"/>'
            f'<g class="led"><circle cx="{num(x)}" cy="{num(y)}" r="9" fill="{P["phosphor"]}" '
            f'opacity="0.3" filter="url(#glow)"/>'
            f'<rect x="{num(x - 5)}" y="{num(y - 3)}" width="10" height="6" rx="1.5" fill="{P["phosphor"]}"/>'
            f'<rect x="{num(x - 1.5)}" y="{num(y - 2)}" width="3" height="4" rx="1" fill="{P["bloom"]}"/></g>')


def qfp(x, y, size, ink, F, marking, code=None, *, pins=8, pitch=14.0, length=9.0, width=5.0,
        marking_size=15.0, code_size=10.0, courtyard=6.0):
    """A square flat-pack chip. Returns (svg, tips) where tips[side][i] is pin i's outer end.
    Needs EPOXY."""
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
    m = length + courtyard  # silkscreen courtyard around the pins
    mark_y = y + size / 2 + (2 if code else marking_size * 0.36)
    svg = (
        rect(x - m, y - m, size + 2 * m, size + 2 * m,
             f' rx="3" fill="none" stroke="{P["silk"]}" stroke-opacity="0.25" stroke-width="0.8"')
        + f'<g fill="{P["tin"]}">{"".join(metal)}</g>'
        + rect(x, y, size, size, f' rx="{num(size * 0.03)}" fill="url(#epoxy)" stroke="{P["epoxy_edge"]}"')
        + f'<circle cx="{num(x + size * 0.1)}" cy="{num(y + size * 0.1)}" r="{num(max(2.0, size * 0.03))}" '
          f'fill="#06110C" stroke="{P["epoxy_edge"]}"/>'
        + ink.text(F["display"], marking, x + size / 2, mark_y, marking_size, P["silk"], anchor="middle", track=0.04)
        + (ink.text(F["mono"], code, x + size / 2, y + size / 2 + 22, code_size, P["silk_faint"],
                    anchor="middle", track=0.12) if code else "")
    )
    return svg, tips


def dip(x, y, w, h, ink, F, name, role, *, name_size, role_size, role_track=0.08, pin_w=6.0, pin_h=5.0) -> str:
    """A DIP-8 package: four pins along each long edge, notch at the left end. Needs EPOXY."""
    pins = "".join(rect(x + 16 + k * (w - 32) / 3 - pin_w / 2, py, pin_w, pin_h)
                   for k in range(4) for py in (y - pin_h, y + h))
    mid = y + h / 2
    for label, face, size, track in ((name, F["mono_sb"], name_size, 0.04), (role, F["mono_md"], role_size, role_track)):
        if ink.width(face, label, size, track) > w - 12:
            raise ValueError(f"{label!r} is too wide for its chip")
    # Centre the two lines as one block of cap heights plus the gap between them.
    cap = F["mono_sb"].cap
    gap = 0.6 * role_size
    top = mid - (cap * name_size + gap + cap * role_size) / 2
    name_y = top + cap * name_size
    return (
        f'<g fill="{P["tin"]}">{pins}</g>'
        + rect(x, y, w, h, f' rx="3" fill="url(#epoxy)" stroke="{P["epoxy_edge"]}"')
        + f'<path d="M{num(x)} {num(mid - 4.5)}A4.5 4.5 0 0 1 {num(x)} {num(mid + 4.5)}Z" fill="#06110C"/>'
        + ink.text(F["mono_sb"], name, x + w / 2 + 2, name_y, name_size, P["silk"], anchor="middle", track=0.04)
        + ink.text(F["mono_md"], role, x + w / 2 + 2, name_y + gap + cap * role_size, role_size, P["silk_dim"],
                   anchor="middle", track=role_track)
    )


def fingers(x0: float, x1: float, y: float, h: float = 12, *, pitch: float = 12, w: float = 6) -> str:
    """Card-edge connector pads, with a key gap a third of the way along."""
    count = int((x1 - x0) // pitch)
    key = count // 3
    pads = "".join(rect(x0 + k * pitch, y, w, h) for k in range(count) if k != key)
    return f'<g fill="{mix(P["tin"], P["mask"], 0.35)}">{pads}</g>'


def tag_pill(ink, F, text: str, x: float, y: float, size: float) -> tuple[str, float]:
    """A silkscreen-outlined tag with its baseline at y. Returns (svg, right edge)."""
    w = ink.width(F["mono_md"], text, size, 0.14)
    h = size * 1.8
    svg = (rect(x - 7, y - size * 1.25, w + 14, h, f' rx="3" fill="none" stroke="{P["silk_faint"]}"')
           + ink.text(F["mono_md"], text, x, y, size, P["silk_dim"], track=0.14))
    return svg, x + w + 7
