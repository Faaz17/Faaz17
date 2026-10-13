"""The hero: the main board.

Name, current role and focus areas. Each focus area is a net label with a pad,
routed back to a chip that carries the handle as its part number and, on the
desktop board, the week it was drawn as its date code, the way real chips are
marked. The status LED blinks beside the role because that is what is live now.

The desktop board is populated the way a real one is: decoupling capacitors
under the chip, a crystal with its load capacitors, USB-C on a length-matched
differential pair, TX/RX LEDs that flicker like serial traffic, a UART header,
a reset switch, an antenna and fiducials, with the chip on a copper pour.
"""
from __future__ import annotations

from datetime import date

from parts import (BOARD_DEFS, EPOXY, GLOW, P, PULSE_CSS, STEEL, Copper, antenna, board, cap, corners,
                   crystal, designator, document, fiducial, header, jog_h, jog_v, led, path_d, qfp, rect,
                   rounded_rect_d, serpentine, tact_switch, usb_c)
from typeset import Ink


def _check(cfg: dict) -> None:
    if not 1 <= len(cfg["nets"]) <= 3:
        raise ValueError("the hero has room for one to three nets")


def _about(cfg: dict) -> tuple[str, str]:
    title = f"{cfg['name']}: {cfg['eyebrow']}"
    desc = f"{cfg['role']}, {cfg['term']}. " + "; ".join(
        f"{n['net'].replace('_', ' ').title()}: {n['detail']}" for n in cfg["nets"])
    return title, desc


def hero_desktop(F, cfg: dict, today: date) -> str:
    W, H = 880, 300
    ink = Ink()
    _check(cfg)
    cu = Copper()
    parts: list[str] = []   # components, drawn over the copper
    text: list[str] = []    # silkscreen
    pulses: list[str] = []

    # Who: eyebrow, name, and the current role beside the status LED.
    left = 52
    eyebrow = cfg["eyebrow"].upper()
    if ink.width(F["mono_md"], eyebrow, 11, 0.16) > 500:
        raise ValueError("hero eyebrow is too long: it would run into the crystal")
    text.append(ink.text(F["mono_md"], eyebrow, left, 62, 11, P["silk_dim"], track=0.16))
    name = cfg["name"].upper()
    size = 40.0
    while ink.width(F["display"], name, size, 0.03) > 520:
        size -= 0.5
    text.append(ink.text(F["display"], name, left, 114, size, P["silk"], track=0.03))
    parts.append(led(left + 5, 140))
    role_x = left + 20
    term_x = role_x + ink.width(F["sans_md"], cfg["role"], 15) + 8
    if term_x + ink.width(F["sans_md"], f"· {cfg['term']}", 15) > 600:
        raise ValueError("hero role is too long: it would run into the chip")
    text.append(ink.text(F["sans_md"], cfg["role"], role_x, 145, 15, P["silk"]))
    text.append(ink.text(F["sans_md"], f"· {cfg['term']}", term_x, 145, 15, P["silk_dim"]))

    # U1, the chip everything is wired to.
    cx, cy, cs = 676, 84, 132
    chip, tips = qfp(cx, cy, cs, ink, F, cfg["chip"], f"DXB {today:%y}{today.isocalendar().week:02d}")
    L, R, T, B = tips["left"], tips["right"], tips["top"], tips["bottom"]
    text.append(ink.text(F["mono"], "U1", cx - 21, cy - 18, 10, P["silk_faint"], track=0.1))

    # Nets: each focus area routed back to the chip, with a pulse running out along it.
    nets = cfg["nets"]
    label_w = max(ink.width(F["mono_sb"], n["net"], 13, 0.06) for n in nets)
    detail_x = left + label_w + 18
    pad_x = max(detail_x + ink.width(F["mono"], n["detail"], 13) for n in nets) + 22
    for i, (n, y) in enumerate(zip(nets, [192 + 28 * k for k in range(len(nets))])):
        text.append(ink.text(F["mono_sb"], n["net"], left, y, 13, P["silk"], track=0.06))
        text.append(ink.text(F["mono"], n["detail"], detail_x, y, 13, P["silk_dim"]))
        px, py = L[4 + i]
        route = jog_h(px, py, pad_x + 4, y - 4, px - 16)
        if route[2][0] < pad_x + 16:
            raise ValueError("hero net details are too long to route back to the chip; shorten them")
        cu.trace(route)
        parts.append(rect(pad_x, y - 8, 8, 8, ' fill="url(#gold)"'))
        pulses.append(f'<path class="pulse p{i}" d="{path_d(route)}" pathLength="100"/>')

    # Y1, a 16 MHz crystal on the oscillator pin, with its two load capacitors.
    parts.append(crystal(566, 27, 46, 16, ink, F, "16.000"))
    cu.trace(jog_v(*T[0], 660, 35, 68) + [(612, 35)])
    cu.trace([(566, 35), (548, 35)])
    cu.via(548, 35)
    for x, ref, anchor, lx in ((567, "C5", "end", 561), (611, "C6", "start", 617)):
        cu.trace([(x, 38.5), (x, 47.5)])
        cu.trace([(x, 56.5), (x, 64)])
        cu.via(x, 64, 2.6)
        parts.append(cap(x, 52, vertical=True))
        text.append(designator(ink, F, ref, lx, 55, anchor))
    text.append(designator(ink, F, "Y1", 589, 20, "middle"))

    # Decoupling capacitors under the chip, one per supply pin, and their ground vias.
    for i, ref in zip((1, 3, 5, 7), ("C1", "C2", "C3", "C4")):
        cu.trace([B[i], (B[i][0], 245.5)])
        parts.append(cap(B[i][0], 250, vertical=True))
        text.append(designator(ink, F, ref, B[i][0], 266, "middle"))
    for i in (2, 6):
        cu.trace([B[i], (B[i][0], 252)])
        cu.via(B[i][0], 252)
    cu.trace(jog_v(*B[0], 673, 262, 242))
    cu.via(673, 262)
    cu.trace([B[4], (B[4][0], 262)])
    cu.via(B[4][0], 262)

    # The rest of the fan-out, routed at 45 degrees like a real layout.
    for points, end in ((jog_v(*T[1], 687, 40, 60), (687, 40)), ([T[3], (T[3][0], 44)], (T[3][0], 44)),
                        (jog_v(*T[5], 783, 38, 58), (783, 38)), (jog_v(*T[7], 821, 34, 64), (821, 34)),
                        ([L[0], (646, L[0][1])], (646, L[0][1])), ([L[2], (640, L[2][1])], (640, L[2][1])),
                        ([R[1], (846, R[1][1])], (846, R[1][1])), ([R[5], (846, R[5][1])], (846, R[5][1]))):
        cu.trace(points)
        cu.via(*end)
    for i in (0, 2, 6):  # these leave the board on the right edge
        cu.trace([R[i], (W, R[i][1])])

    # J1, USB-C on a differential pair: D- carries a serpentine to match D+ in length.
    cu.trace([R[3], (858, R[3][1])], width=2.2)
    cu.trace([R[4]] + serpentine(826, 848, R[4][1], 5, 2) + [(858, R[4][1])], width=2.2)
    parts.append(usb_c(858, 134, 20, 34))

    # TX/RX activity LEDs, flickering like serial traffic.
    cu.trace(jog_h(*R[7], 835, 212, 822))
    cu.trace([(834, 228), (824, 228)])
    cu.via(824, 228, 2.6)
    parts.append(led(842, 212, P["amber"], "tx"))
    parts.append(led(842, 228, P["amber"], "rx"))
    text.append(designator(ink, F, "TX", 853, 214.5))
    text.append(designator(ink, F, "RX", 853, 230.5))

    # Along the bottom: the UART header, the reset switch, a fiducial and the antenna.
    hdr, pins = header(52, 262, 4, pitch=14)
    parts.append(hdr)
    for (px, _), pin in zip(pins, ("GND", "TX", "RX", "3V3")):
        text.append(ink.text(F["mono"], pin, px, 287, 7, P["silk_faint"], anchor="middle"))
    text.append(designator(ink, F, "J2 UART", 114, 271))
    parts.append(tact_switch(166, 258))
    text.append(designator(ink, F, "SW1", 192, 266))
    text.append(designator(ink, F, "RESET", 192, 276))
    parts.append(fiducial(248, 272))
    parts.append(fiducial(56, 30))
    ant = antenna(296, 264, 120, 14, 5)
    cu.trace(ant, width=2.2)
    cu.trace([ant[0], (282, ant[0][1])])
    cu.via(282, ant[0][1])
    text.append(designator(ink, F, "ANT1 · 2.4 GHz", 426, 275))
    text.append(ink.text(F["mono"], f"{cfg['chip']} · REV {today:%Y.%m}", 836, 283, 10, P["silk_faint"],
                         track=0.12, anchor="end"))

    # The chip sits on a copper pour; every trace and via through it keeps its clearance.
    pour = f'<path d="{rounded_rect_d(630, 48, 240, 208, 10)}" fill="{P["pour"]}"/>'
    body = (board(W, H, r=18, holes=corners(W, H, 20), under=pour + cu.gaps())
            + cu.top() + "".join(parts) + chip + "".join(text) + "".join(pulses))
    title, desc = _about(cfg)
    return document(W, H, ink, body, title=title, desc=desc, defs=(BOARD_DEFS, EPOXY, GLOW, STEEL),
                    style=PULSE_CSS)


def hero_mobile(F, cfg: dict, today: date) -> str:
    """The same board for a phone: everything stacked, type sized for a 300px column."""
    W = 360
    ink = Ink()
    _check(cfg)
    left = 24

    # Lay the text out first, because the board's height depends on it.
    name_words = cfg["name"].upper().split()
    name_lines = [" ".join(name_words[:-1]), name_words[-1]] if len(name_words) > 1 else name_words
    size = 36.0
    while max(ink.width(F["display"], line, size, 0.03) for line in name_lines) > W - 2 * left:
        size -= 0.5
    name_y = [160 + i * size * 1.12 for i in range(len(name_lines))]
    role_lines = ink.wrap(F["sans_md"], f"{cfg['role']} · {cfg['term']}", 15, W - left - 44)
    role_y = [name_y[-1] + 44 + 20 * i for i in range(len(role_lines))]
    net_y = [role_y[-1] + 50 + 46 * i for i in range(len(cfg["nets"]))]
    band_y = net_y[-1] + 40  # the UART header and the activity LEDs along the bottom
    H = band_y + 42

    cu = Copper()
    parts: list[str] = []
    text: list[str] = []
    pulses: list[str] = []

    cx, cy, cs = 258, 40, 62
    chip, tips = qfp(cx, cy, cs, ink, F, cfg["chip"], None, pins=5, pitch=10, length=6, width=3.4,
                     marking_size=8.5, courtyard=4)
    L, R, T, B = tips["left"], tips["right"], tips["top"], tips["bottom"]
    for i in (0, 2, 4):
        cu.trace([R[i], (W, R[i][1])], width=2)
    for i in (1, 3):
        cu.trace([R[i], (R[i][0] + 10, R[i][1])], width=2)
        cu.via(R[i][0] + 10, R[i][1], 2.6)
        cu.trace([T[i], (T[i][0], 22)], width=2)
        cu.via(T[i][0], 22, 2.6)
        cu.trace([L[i], (L[i][0] - 10, L[i][1])], width=2)
        cu.via(L[i][0] - 10, L[i][1], 2.6)
        cu.trace([B[i], (B[i][0], B[i][1] + 7)], width=2)  # decoupling capacitors under the chip
        parts.append(cap(B[i][0], B[i][1] + 11, vertical=True))
    for i in (0, 4):
        cu.trace([B[i], (B[i][0], B[i][1] + 8)], width=2)
        cu.via(B[i][0], B[i][1] + 8, 2.6)
    parts.append(fiducial(226, 30))

    for i, line in enumerate(cfg.get("eyebrow_mobile", [cfg["eyebrow"]])):
        text.append(ink.text(F["mono_md"], line.upper(), left, 56 + 17 * i, 11, P["silk_dim"], track=0.14))
    for line, y in zip(name_lines, name_y):
        text.append(ink.text(F["display"], line, left, y, size, P["silk"], track=0.03))
    parts.append(led(left + 5, role_y[0] - 5))
    for i, (line, y) in enumerate(zip(role_lines, role_y)):
        if i == len(role_lines) - 1 and f"· {cfg['term']}" in line:
            head = line[: line.rindex("·")].rstrip()
            text.append(ink.text(F["sans_md"], head, left + 20, y, 15, P["silk"]))
            tail_x = left + 20 + ink.width(F["sans_md"], head, 15) + 8
            text.append(ink.text(F["sans_md"], f"· {cfg['term']}", tail_x, y, 15, P["silk_dim"]))
        else:
            text.append(ink.text(F["sans_md"], line, left + 20, y, 15, P["silk"]))

    for i, (n, y) in enumerate(zip(cfg["nets"], net_y)):
        label_w = ink.width(F["mono_sb"], n["net"], 13, 0.06)
        text.append(ink.text(F["mono_sb"], n["net"], left, y, 13, P["silk"], track=0.06))
        text.append(ink.text(F["sans"], n["detail"], left, y + 19, 15, P["silk_dim"]))
        pad_x = left + label_w + 12
        parts.append(rect(pad_x, y - 8.5, 8, 8, ' fill="url(#gold)"'))
        route = [(W, y - 4.5), (pad_x + 8, y - 4.5)]  # signals arrive from off the board
        cu.trace(route, width=2.4)
        pulses.append(f'<path class="pulse p{i}" d="{path_d(route)}" pathLength="100"/>')

    hdr, _ = header(left, band_y, 4, pitch=13)
    parts.append(hdr)
    text.append(designator(ink, F, "J2 UART", left + 60, band_y + 9))
    parts.append(led(292, band_y + 6, P["amber"], "tx"))
    parts.append(led(322, band_y + 6, P["amber"], "rx"))
    text.append(designator(ink, F, "TX", 292, band_y + 22, "middle"))
    text.append(designator(ink, F, "RX", 322, band_y + 22, "middle"))

    pour = f'<path d="{rounded_rect_d(236, 14, 112, 116, 8)}" fill="{P["pour"]}"/>'
    body = (board(W, H, r=16, holes=corners(W, H, 16), hole_r=3.6, under=pour + cu.gaps())
            + cu.top() + "".join(parts) + chip + "".join(text) + "".join(pulses))
    title, desc = _about(cfg)
    return document(W, H, ink, body, title=title, desc=desc, defs=(BOARD_DEFS, EPOXY, GLOW), style=PULSE_CSS)
