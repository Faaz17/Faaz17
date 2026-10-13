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

# Green boards and phosphor, gold metal, steel and tan parts, amber for the second channel.
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
    "tin": "#BCCDC2",         # silver: crystal cans, connector shells
    "pour": "#134832",        # copper pour under the mask, a shade lighter than the board
    "amber": "#FFB547",       # second scope channel, TX/RX activity LEDs
    "ceramic": "#C4AA7A",     # ceramic capacitor bodies
    "housing": "#0D1511",     # black plastic: headers, switch, resistor bodies
    "jst": "#E4DCC6",         # cream plastic of the power connector
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
# Exposed metal is ENIG gold, as on a good board; component bodies are steel.
GOLD = ('<linearGradient id="gold" x1="0" y1="0" x2="0" y2="1">'
        '<stop offset="0" stop-color="#F4D57E"/><stop offset="0.5" stop-color="#D4A64A"/>'
        '<stop offset="1" stop-color="#9C7426"/></linearGradient>')
STEEL = ('<linearGradient id="steel" x1="0" y1="0" x2="1" y2="1">'
         '<stop offset="0" stop-color="#E3E9EB"/><stop offset="0.5" stop-color="#AAB5BA"/>'
         '<stop offset="1" stop-color="#66737A"/></linearGradient>')
METAL = "url(#gold)"
BOARD_DEFS = ('<pattern id="drill" width="14" height="14" patternUnits="userSpaceOnUse">'
              f'<circle cx="7" cy="7" r="0.75" fill="{P["silk"]}" fill-opacity="0.07"/></pattern>' + SHEEN + GOLD)
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
    ".tx,.rx{animation:serial 2.8s steps(1,end) infinite}.rx{animation-delay:1.3s}"
    "@keyframes serial{0%{opacity:1}4%{opacity:.2}8%{opacity:1}12%{opacity:.2}16%{opacity:1}22%,100%{opacity:.2}}"
    "@media (prefers-reduced-motion:reduce){.pulse,.flow{display:none}.led,.tx,.rx{animation:none}}"
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
          holes=(), hole_r: float = 4.2, under: str = "") -> str:
    """A board with real drill holes, so the page shows through them. `under` is
    drawn on the bare mask, below the drill pattern and the sheen, which is where
    copper pours and their clearances belong. Needs BOARD_DEFS."""
    d = rounded_rect_d(x, y, w, h, r) + "".join(circle_d(hx, hy, hole_r) for hx, hy in holes)
    return (
        f'<path d="{d}" fill="{P["mask"]}" fill-rule="evenodd"/>'
        + under
        + f'<path d="{d}" fill="url(#drill)" fill-rule="evenodd"/>'
        f'<path d="{d}" fill="url(#sheen)" fill-rule="evenodd"/>'
        f'<path d="{rounded_rect_d(x + 0.75, y + 0.75, w - 1.5, h - 1.5, r - 0.75)}" fill="none" '
        f'stroke="{P["edge"]}" stroke-width="1.5"/>'
        + "".join(
            f'<circle cx="{num(hx)}" cy="{num(hy)}" r="{num(hole_r + 1.6)}" fill="none" stroke="{METAL}" stroke-width="3.2"/>'
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


def led(x: float, y: float, colour: str | None = None, cls: str = "led") -> str:
    """A 0603 LED: two gold pads either side of a glowing lens. Needs GLOW."""
    colour = colour or P["phosphor"]
    return (f'<rect x="{num(x - 8)}" y="{num(y - 3)}" width="3" height="6" fill="{METAL}"/>'
            f'<rect x="{num(x + 5)}" y="{num(y - 3)}" width="3" height="6" fill="{METAL}"/>'
            f'<g class="{cls}"><circle cx="{num(x)}" cy="{num(y)}" r="9" fill="{colour}" '
            f'opacity="0.3" filter="url(#glow)"/>'
            f'<rect x="{num(x - 5)}" y="{num(y - 3)}" width="10" height="6" rx="1.5" fill="{colour}"/>'
            f'<rect x="{num(x - 1.5)}" y="{num(y - 2)}" width="3" height="4" rx="1" fill="{mix(colour, "#FFFFFF", 0.7)}"/></g>')


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
        + f'<g fill="{METAL}">{"".join(metal)}</g>'
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
        f'<g fill="{METAL}">{pins}</g>'
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
    return f'<g fill="{METAL}" opacity="0.92">{pads}</g>'


def tag_pill(ink, F, text: str, x: float, y: float, size: float) -> tuple[str, float]:
    """A silkscreen-outlined tag with its baseline at y. Returns (svg, right edge)."""
    w = ink.width(F["mono_md"], text, size, 0.14)
    h = size * 1.8
    svg = (rect(x - 7, y - size * 1.25, w + 14, h, f' rx="3" fill="none" stroke="{P["silk_faint"]}"')
           + ink.text(F["mono_md"], text, x, y, size, P["silk_dim"], track=0.14))
    return svg, x + w + 7


# --- populated parts: what makes a board look built rather than drawn --------

def designator(ink, F, text: str, x: float, y: float, anchor: str = "start") -> str:
    """A reference designator (C1, J2, SW1...) in fine silkscreen."""
    return ink.text(F["mono"], text, x, y, 7.5, P["silk_faint"], anchor=anchor, track=0.06)


def cap(x: float, y: float, *, vertical: bool = False) -> str:
    """A 0603 ceramic capacitor centred on (x, y): tan body between gold terminals."""
    L, W, e = 9.0, 4.6, 2.2
    if vertical:
        return (rect(x - W / 2, y - L / 2 + e, W, L - 2 * e, f' fill="{P["ceramic"]}"')
                + rect(x - W / 2, y - L / 2, W, e, f' fill="{METAL}"')
                + rect(x - W / 2, y + L / 2 - e, W, e, f' fill="{METAL}"'))
    return (rect(x - L / 2 + e, y - W / 2, L - 2 * e, W, f' fill="{P["ceramic"]}"')
            + rect(x - L / 2, y - W / 2, e, W, f' fill="{METAL}"')
            + rect(x + L / 2 - e, y - W / 2, e, W, f' fill="{METAL}"'))


def resistor(x: float, y: float, *, vertical: bool = False) -> str:
    """A 0603 resistor centred on (x, y): black body, gold ends, a hint of its printed value."""
    L, W, e = 9.0, 4.6, 1.8
    if vertical:
        return (rect(x - W / 2, y - L / 2, W, L, f' fill="{P["housing"]}"')
                + rect(x - W / 2, y - L / 2, W, e, f' fill="{METAL}"')
                + rect(x - W / 2, y + L / 2 - e, W, e, f' fill="{METAL}"')
                + rect(x - 0.4, y - 1.6, 0.8, 3.2, f' fill="{P["silk"]}" opacity="0.6"'))
    return (rect(x - L / 2, y - W / 2, L, W, f' fill="{P["housing"]}"')
            + rect(x - L / 2, y - W / 2, e, W, f' fill="{METAL}"')
            + rect(x + L / 2 - e, y - W / 2, e, W, f' fill="{METAL}"')
            + rect(x - 1.6, y - 0.4, 3.2, 0.8, f' fill="{P["silk"]}" opacity="0.6"'))


def crystal(x: float, y: float, w: float, h: float, ink, F, label: str) -> str:
    """An HC-49 crystal: gold pads at each end under a steel can. Needs STEEL."""
    return (rect(x - 3, y + h / 2 - 3.5, 7, 7, f' fill="{METAL}"')
            + rect(x + w - 4, y + h / 2 - 3.5, 7, 7, f' fill="{METAL}"')
            + rect(x, y, w, h, f' rx="{num(h / 2)}" fill="url(#steel)"')
            + rect(x + 2.5, y + 2.5, w - 5, h - 5, f' rx="{num((h - 5) / 2)}" fill="none" stroke="#FFFFFF" '
                   'stroke-opacity="0.4" stroke-width="0.8"')
            + ink.text(F["mono_md"], label, x + w / 2, y + h / 2 + 2.4, 6.8, "#33403F", anchor="middle", track=0.04))


def usb_c(x: float, y: float, w: float, h: float) -> str:
    """A USB-C receptacle from above, its mouth at the board edge (x + w). Needs STEEL."""
    legs = rect(x - 4, y + 3, 5, 6, f' fill="{METAL}"') + rect(x - 4, y + h - 9, 5, 6, f' fill="{METAL}"')
    return (legs + rect(x, y, w, h, ' rx="3" fill="url(#steel)"')
            + f'<path d="M{num(x + 3)} {num(y + 4)}V{num(y + h - 4)}" stroke="#56636A" stroke-width="1"/>'
            + rect(x + w - 5, y + 3, 3, h - 6, ' rx="1.5" fill="#2A3338"'))


def header(x: float, y: float, n: int, *, pitch: float = 14.0) -> tuple[str, list[tuple[float, float]]]:
    """A 1xN pin header: black housing, square gold pins. Returns (svg, pin centres)."""
    pins = [(x + pitch * (i + 0.5), y + 6) for i in range(n)]
    svg = (rect(x, y, pitch * n, 12, f' rx="1.5" fill="{P["housing"]}" stroke="#25352D" stroke-width="0.8"')
           + "".join(rect(px - 2.6, py - 2.6, 5.2, 5.2, f' fill="{METAL}"') for px, py in pins))
    return svg, pins


def tact_switch(x: float, y: float, s: float = 20) -> str:
    """A 6 mm tactile switch: steel body, black plunger, four gold legs. Needs STEEL."""
    legs = "".join(rect(lx, ly, 4, 3.5, f' fill="{METAL}"')
                   for lx, ly in ((x - 3, y + 2), (x + s - 1, y + 2), (x - 3, y + s - 5.5), (x + s - 1, y + s - 5.5)))
    return (legs + rect(x, y, s, s, ' rx="2" fill="url(#steel)"')
            + f'<circle cx="{num(x + s / 2)}" cy="{num(y + s / 2)}" r="{num(s * 0.31)}" fill="#141A17" stroke="#2C3832"/>')


def fiducial(x: float, y: float) -> str:
    """A pick-and-place fiducial: a gold dot in a ring of bare board."""
    return (f'<circle cx="{num(x)}" cy="{num(y)}" r="5.4" fill="{P["mask_lo"]}"/>'
            f'<circle cx="{num(x)}" cy="{num(y)}" r="2.3" fill="{METAL}"/>')


def antenna(x: float, y: float, w: float, h: float, turns: int) -> list[tuple[float, float]]:
    """Points of a meandered PCB antenna: copper folded into a square wave."""
    p = w / (2 * turns)
    pts = [(x, y + h)]
    for i in range(2 * turns):
        xi = x + i * p
        rail = y if i % 2 == 0 else y + h
        pts += [(xi, rail), (xi + p, rail)]
    return pts


def screw(x: float, y: float, r: float = 4.4) -> str:
    """A Phillips screw head. Needs STEEL."""
    a = r * 0.55
    return (f'<circle cx="{num(x)}" cy="{num(y)}" r="{r}" fill="url(#steel)" stroke="#3E4A4F" stroke-width="0.6"/>'
            f'<path d="M{num(x - a)} {num(y)}H{num(x + a)}M{num(x)} {num(y - a)}V{num(y + a)}" stroke="#4A565B" '
            'stroke-width="1.1" stroke-linecap="round"/>')


def knob(x: float, y: float, r: float, angle: float) -> str:
    """A rotary knob: knurled steel skirt, dark cap, pointer at `angle` degrees (0 is up). Needs STEEL."""
    knurl = "".join(
        f'<line x1="{num(x + math.sin(t) * (r - 1.6))}" y1="{num(y - math.cos(t) * (r - 1.6))}" '
        f'x2="{num(x + math.sin(t) * r)}" y2="{num(y - math.cos(t) * r)}"/>'
        for t in (k * math.pi / 12 for k in range(24)))
    a = math.radians(angle)
    return (f'<circle cx="{num(x)}" cy="{num(y)}" r="{r}" fill="url(#steel)"/>'
            f'<g stroke="#56636A" stroke-width="0.7">{knurl}</g>'
            f'<circle cx="{num(x)}" cy="{num(y)}" r="{num(r * 0.7)}" fill="#151D19" stroke="#2C3A33"/>'
            f'<line x1="{num(x)}" y1="{num(y)}" x2="{num(x + math.sin(a) * r * 0.62)}" '
            f'y2="{num(y - math.cos(a) * r * 0.62)}" stroke="{P["silk"]}" stroke-width="1.6" stroke-linecap="round"/>')


def soic(x: float, y: float, w: float, h: float, ink, F, marking: str, *, pins: int) -> tuple[str, list, list]:
    """A SOIC chip with gull-wing pins on its long edges.
    Returns (svg, top pin tips, bottom pin tips). Needs EPOXY."""
    pitch = (w - 8) / (pins - 1)
    top = [(x + 4 + pitch * i, y - 4) for i in range(pins)]
    bottom = [(x + 4 + pitch * i, y + h + 4) for i in range(pins)]
    metal = ("".join(rect(px - 1.4, y - 4, 2.8, 4) for px, _ in top)
             + "".join(rect(px - 1.4, y + h, 2.8, 4) for px, _ in bottom))
    svg = (f'<g fill="{METAL}">{metal}</g>'
           + rect(x, y, w, h, f' rx="1.5" fill="url(#epoxy)" stroke="{P["epoxy_edge"]}"')
           + f'<circle cx="{num(x + 5)}" cy="{num(y + h - 5)}" r="1.6" fill="#06110C"/>'
           + ink.text(F["mono_md"], marking, x + w / 2, y + h / 2 + 3, 8, P["silk_dim"], anchor="middle", track=0.08))
    return svg, top, bottom


def jst(x: float, y: float, n: int = 2, pitch: float = 10.0) -> str:
    """A JST-XH style connector: cream housing with gold pins showing through."""
    w, h = pitch * n + 6, 14
    pins = "".join(rect(x + 3 + pitch * (i + 0.5) - 2.2, y + 5, 4.4, 4.4, f' fill="{METAL}"') for i in range(n))
    return (rect(x, y, w, h, f' rx="1.5" fill="{P["jst"]}" stroke="#B9AF95" stroke-width="0.8"')
            + rect(x + 2.5, y + 3, w - 5, h - 6, ' rx="1" fill="#CFC5AA"') + pins)


class Copper:
    """Traces and vias, each remembered with the clearance a copper pour keeps
    around it. Draw `gaps()` in a board's `under` layer and `top()` above it."""

    def __init__(self):
        self._top: list[str] = []
        self._gaps: list[str] = []

    def trace(self, points, width: float = 2.6, color: str | None = None) -> None:
        self._top.append(trace(points, width=width, color=color))
        self._gaps.append(trace(points, width=width + 5, color=P["mask"]))

    def via(self, x: float, y: float, r: float = 3.4) -> None:
        self._top.append(via(x, y, r))
        self._gaps.append(f'<circle cx="{num(x)}" cy="{num(y)}" r="{num(r + 2.6)}" fill="{P["mask"]}"/>')

    def top(self) -> str:
        return "".join(self._top)

    def gaps(self) -> str:
        return "".join(self._gaps)


def serpentine(x0: float, x1: float, y: float, amp: float, bumps: int) -> list[tuple[float, float]]:
    """A straight run with `bumps` square detours of height `amp`: how one trace of a
    differential pair is lengthened to match its partner."""
    bw = (x1 - x0) / (2 * bumps)
    pts = [(x0, y)]
    for i in range(bumps):
        xs = x0 + (2 * i + 0.5) * bw
        pts += [(xs, y), (xs, y + amp), (xs + bw, y + amp), (xs + bw, y)]
    return pts + [(x1, y)]


def instrument(W: float, H: float, r: float) -> str:
    """The case of a bench instrument: dark green body, sheen, edge highlight, a screw
    in each corner. Needs SHEEN and STEEL."""
    return (f'<rect width="{num(W)}" height="{num(H)}" rx="{r}" fill="{P["body"]}"/>'
            f'<rect width="{num(W)}" height="{num(H)}" rx="{r}" fill="url(#sheen)"/>'
            f'<path d="{rounded_rect_d(0.75, 0.75, W - 1.5, H - 1.5, r - 0.75)}" fill="none" '
            f'stroke="{P["edge"]}" stroke-width="1.5"/>')

