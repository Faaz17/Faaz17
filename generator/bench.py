"""The bench: two boards side by side (stacked on a phone).

Languages are LED bar graphs, one segment per 5% of public code, fed by an
LED-driver chip through a bus up the left of the bars. The toolchain is a tray
of DIP chips, each marked with what it is and what it is for, wired to power
rails between the rows with a decoupling capacitor beside each one. They share
one image so a phone can stack them at full width.
"""
from __future__ import annotations

from parts import (BOARD_DEFS, EPOXY, GLOW, LED_FROM, LED_TO, P, Copper, board, cap, corners, designator,
                   dip, document, jst, mix, rect, resistor, soic)
from typeset import Ink

SEGMENTS = 20


def _languages(ink: Ink, F, langs, x: float, y: float, w: float, h: float, *, phone: bool) -> str:
    m = 16 if phone else 18
    cu = Copper()
    out: list[str] = []
    title_x = x + (36 if phone else 40)
    out.append(ink.text(F["display"], "LANGUAGES", title_x, y + 48 + (0 if phone else 2), 13 if phone else 12,
                        P["silk"], track=0.16))
    if phone:
        out.append(ink.text(F["mono"], "share of code in public repos", title_x, y + 68, 11.5, P["silk_faint"]))
        name_x, name_size, bar_x, bar_w, pct_size, row0, pitch = 24, 15, 112, 168, 13.5, 106, 31
        chip_x, chip_w = 30, 78  # clear of the corner hole; the bus still lands left of the bars
    else:
        out.append(ink.text(F["mono"], "share of code, public repos", x + w - 40, y + 50, 10.5, P["silk_faint"],
                            anchor="end"))
        name_x, name_size, bar_x, bar_w, pct_size, row0, pitch = 40, 14, 132, 202, 12.5, 90, 33
        chip_x, chip_w = 36, 88

    slot = (bar_w - 8) / SEGMENTS
    lit, glow, rows = [], [], []
    for i, (name, share) in enumerate(langs):
        ry = y + row0 + pitch * i
        rows.append(ry)
        out.append(ink.text(F["sans_md"], name, x + name_x, ry, name_size, P["silk"]))
        out.append(rect(x + bar_x, ry - 15, bar_w, 20, f' rx="3" fill="url(#epoxy)" stroke="{P["epoxy_edge"]}"'))
        count = max(1, round(share * SEGMENTS)) if share > 0 else 0
        for s in range(SEGMENTS):
            sx, sy = x + bar_x + 4 + s * slot, ry - 11
            if s < count:
                colour = mix(LED_FROM, LED_TO, s / (SEGMENTS - 1))
                lit.append(rect(sx, sy, slot - 3, 12, f' rx="1.2" fill="{colour}"'))
                glow.append(rect(sx, sy, slot - 3, 12, f' fill="{colour}"'))
            else:
                out.append(rect(sx, sy, slot - 3, 12, f' rx="1.2" fill="{P["mask_lo"]}" stroke="#123B29" stroke-width="0.8"'))
        out.append(ink.text(F["mono_md"], f"{share * 100:.1f}%", x + w - (24 if phone else 40), ry, pct_size,
                            P["silk"], anchor="end"))
    out.append(f'<g opacity="0.6" filter="url(#glow)">{"".join(glow)}</g>{"".join(lit)}')

    # The driver that lights them, a bus up the left of the bars, and the power in.
    chip_y = y + h - (44 if phone else 46)
    driver, top_pins, _ = soic(x + chip_x, chip_y, chip_w, 16, ink, F, "IS31FL3731", pins=9)
    bus_x = top_pins[-1][0]
    if rows:
        cu.trace([top_pins[-1], (bus_x, rows[0] - 5)], width=2)
        for ry in rows:
            cu.trace([(bus_x, ry - 5), (x + bar_x, ry - 5)], width=2)
    parts = [driver, designator(ink, F, "U2", x + chip_x + chip_w + 6, chip_y + 11)]
    for k in range(3):
        parts.append(resistor(x + chip_x + chip_w + 30 + 14 * k, chip_y + 8, vertical=True))
    parts.append(cap(x + chip_x + chip_w + 78, chip_y + 8, vertical=True))
    parts.append(designator(ink, F, "R1-3", x + chip_x + chip_w + 24, chip_y + 25))
    jx = x + w - (96 if phone else 100)
    parts.append(jst(jx, chip_y + 1))
    parts.append(designator(ink, F, "J3 5V", jx + 32, chip_y + 11))

    body = board(w, h, x=x, y=y, holes=corners(w, h, m, x, y), hole_r=3.6 if phone else 4.2, under=cu.gaps())
    return body + cu.top() + "".join(out) + "".join(parts)


def _toolchain(ink: Ink, F, parts, x: float, y: float, w: float, h: float, *, phone: bool) -> str:
    m = 16 if phone else 18
    cu = Copper()
    out: list[str] = []
    title_x = x + (36 if phone else 40)
    out.append(ink.text(F["display"], "TOOLCHAIN", title_x, y + 48 + (0 if phone else 2), 13 if phone else 12,
                        P["silk"], track=0.16))
    if phone:
        out.append(ink.text(F["mono"], "what I build with", title_x, y + 68, 11.5, P["silk_faint"]))
        cols, cw, ch, row0, pitch, inset = 2, 140, 38, 94, 58, 20
        name_size, role_size = 13, 10
    else:
        out.append(ink.text(F["mono"], "what I build with", x + w - 40, y + 50, 10.5, P["silk_faint"], anchor="end"))
        cols, cw, ch, row0, pitch, inset = 3, 108, 36, 70, 58, 28
        name_size, role_size = 11.5, 9
    col_w = (w - 2 * inset) / cols
    rows = -(-len(parts) // cols)
    gap = col_w - cw

    # Power rails run between the rows; each chip takes its outer pins to the rail below
    # and its inner pins to the rail above, with a decoupling capacitor at its side.
    rail_y = [y + row0 + pitch * r + ch + 5 + (pitch - ch - 10) / 2 for r in range(rows)]
    rail_x0, rail_x1 = x + inset + 2, x + w - inset - 2
    for ry in rail_y:
        cu.trace([(rail_x0, ry), (rail_x1, ry)], width=2)
        cu.via(rail_x0, ry, 2.6)
        cu.via(rail_x1, ry, 2.6)
    chips = []
    for i, part in enumerate(parts):
        r, c = divmod(i, cols)
        cx = x + inset + col_w * c + (col_w - cw) / 2
        cy = y + row0 + pitch * r
        xs = [cx + 16 + k * (cw - 32) / 3 for k in range(4)]
        for k in (0, 3):
            cu.trace([(xs[k], cy + ch + 5), (xs[k], rail_y[r])], width=1.6)
        if r:
            for k in (1, 2):
                cu.trace([(xs[k], cy - 5), (xs[k], rail_y[r - 1])], width=1.6)
        chips.append(dip(cx, cy, cw, ch, ink, F, part["part"], part["role"],
                         name_size=name_size, role_size=role_size, role_track=0.06))
        chips.append(cap(cx + cw + gap / 2, cy + ch / 2, vertical=True))

    body = board(w, h, x=x, y=y, holes=corners(w, h, m, x, y), hole_r=3.6 if phone else 4.2, under=cu.gaps())
    return body + cu.top() + "".join(out) + "".join(chips)


def _about(langs, parts) -> tuple[str, str]:
    return ("Languages and toolchain",
            "Languages by share of code in public repositories: "
            + ", ".join(f"{name} {share * 100:.1f}%" for name, share in langs)
            + ". Toolchain: " + ", ".join(f"{p['part']} ({p['role'].lower()})" for p in parts) + ".")


def bench_desktop(F, langs, parts) -> str:
    if len(parts) > 12:
        raise ValueError("the toolchain has room for twelve chips")
    W, H = 880, 320
    ink = Ink()
    body = _languages(ink, F, langs, 0, 0, 430, H, phone=False) + _toolchain(ink, F, parts, 450, 0, 430, H, phone=False)
    title, desc = _about(langs, parts)
    return document(W, H, ink, body, title=title, desc=desc, defs=(BOARD_DEFS, EPOXY, GLOW))


def bench_mobile(F, langs, parts) -> str:
    rows = -(-len(parts) // 2)
    lang_h = 106 + 31 * (len(langs) - 1) + 40 + 52
    tool_h = 94 + 58 * (rows - 1) + 38 + 5 + 26 + 18
    W, gap = 360, 16
    H = lang_h + gap + tool_h
    ink = Ink()
    body = (_languages(ink, F, langs, 0, 0, W, lang_h, phone=True)
            + _toolchain(ink, F, parts, 0, lang_h + gap, W, tool_h, phone=True))
    title, desc = _about(langs, parts)
    return document(W, H, ink, body, title=title, desc=desc, defs=(BOARD_DEFS, EPOXY, GLOW))
