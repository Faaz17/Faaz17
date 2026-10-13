"""The hero: the main board.

Name, current role and focus areas. Each focus area is a net label with a pad,
routed back to a chip that carries the handle as its part number and, on the
desktop board, the week it was drawn as its date code, the way real chips are
marked. The status LED blinks beside the role because that is what is live now.
"""
from __future__ import annotations

from datetime import date

from parts import (BOARD_DEFS, EPOXY, GLOW, P, PULSE_CSS, board, corners, document, jog_h, jog_v,
                   led, path_d, qfp, rect, trace, via)
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
    out = [board(W, H, r=18, holes=corners(W, H, 20))]

    left = 52
    eyebrow = cfg["eyebrow"].upper()
    if ink.width(F["mono_md"], eyebrow, 11, 0.16) > 580:
        raise ValueError("hero eyebrow is too long: it would run into the chip")
    out.append(ink.text(F["mono_md"], eyebrow, left, 62, 11, P["silk_dim"], track=0.16))

    name = cfg["name"].upper()
    size = 40.0
    while ink.width(F["display"], name, size, 0.03) > 530:
        size -= 0.5
    out.append(ink.text(F["display"], name, left, 114, size, P["silk"], track=0.03))

    out.append(led(left + 5, 140))
    role_x = left + 20
    term_x = role_x + ink.width(F["sans_md"], cfg["role"], 15) + 8
    if term_x + ink.width(F["sans_md"], f"· {cfg['term']}", 15) > 600:
        raise ValueError("hero role is too long: it would run into the chip")
    out.append(ink.text(F["sans_md"], cfg["role"], role_x, 145, 15, P["silk"]))
    out.append(ink.text(F["sans_md"], f"· {cfg['term']}", term_x, 145, 15, P["silk_dim"]))

    cx, cy, cs = 676, 84, 132
    chip, tips = qfp(cx, cy, cs, ink, F, cfg["chip"], f"DXB {today:%y}{today.isocalendar().week:02d}")

    nets = cfg["nets"]
    label_w = max(ink.width(F["mono_sb"], n["net"], 13, 0.06) for n in nets)
    detail_x = left + label_w + 18
    pad_x = max(detail_x + ink.width(F["mono"], n["detail"], 13) for n in nets) + 22
    rows = [192 + 28 * i for i in range(len(nets))]
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
        copper += [trace(points), via(*end)]
    for i in (0, 2, 4, 6):  # these leave the board on the right edge
        copper.append(trace([R[i], (W, R[i][1])]))
    out.insert(1, "".join(copper))

    for y in rows:
        out.append(rect(pad_x, y - 8, 8, 8, f' fill="{P["tin"]}"'))
    for i, p in enumerate(net_paths):  # signal pulses run out from the chip along each net
        out.append(f'<path class="pulse p{i}" d="{path_d(p)}" pathLength="100"/>')
    out.append(chip)
    out.append(ink.text(F["mono"], "U1", cx - 21, cy - 18, 10, P["silk_faint"], track=0.1))
    out.append(ink.text(F["mono"], f"{cfg['chip']} · REV {today:%Y.%m}", 836, 283, 10, P["silk_faint"],
                        track=0.12, anchor="end"))

    title, desc = _about(cfg)
    return document(W, H, ink, "".join(out), title=title, desc=desc,
                    defs=(BOARD_DEFS, EPOXY, GLOW), style=PULSE_CSS)


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
    H = net_y[-1] + 18 + 36

    out = [board(W, H, r=16, holes=corners(W, H, 16), hole_r=3.6)]
    copper = []

    cx, cy, cs = 258, 40, 62
    chip, tips = qfp(cx, cy, cs, ink, F, cfg["chip"], None, pins=5, pitch=10, length=6, width=3.4,
                     marking_size=8.5, courtyard=4)
    L, R, T, B = tips["left"], tips["right"], tips["top"], tips["bottom"]
    for i in (0, 2, 4):
        copper.append(trace([R[i], (W, R[i][1])], width=2))
    for i in (1, 3):
        copper += [trace([R[i], (R[i][0] + 10, R[i][1])], width=2), via(R[i][0] + 10, R[i][1], 2.6)]
        copper += [trace([T[i], (T[i][0], 22)], width=2), via(T[i][0], 22, 2.6)]
        copper += [trace([L[i], (L[i][0] - 10, L[i][1])], width=2), via(L[i][0] - 10, L[i][1], 2.6)]
    for i in (0, 2, 4):
        copper += [trace([B[i], (B[i][0], B[i][1] + 8)], width=2), via(B[i][0], B[i][1] + 8, 2.6)]

    for i, line in enumerate(cfg.get("eyebrow_mobile", [cfg["eyebrow"]])):
        out.append(ink.text(F["mono_md"], line.upper(), left, 56 + 17 * i, 11, P["silk_dim"], track=0.14))
    for line, y in zip(name_lines, name_y):
        out.append(ink.text(F["display"], line, left, y, size, P["silk"], track=0.03))
    out.append(led(left + 5, role_y[0] - 5))
    for i, (line, y) in enumerate(zip(role_lines, role_y)):
        if i == len(role_lines) - 1 and f"· {cfg['term']}" in line:
            head = line[: line.rindex("·")].rstrip()
            out.append(ink.text(F["sans_md"], head, left + 20, y, 15, P["silk"]))
            tail_x = left + 20 + ink.width(F["sans_md"], head, 15) + 8
            out.append(ink.text(F["sans_md"], f"· {cfg['term']}", tail_x, y, 15, P["silk_dim"]))
        else:
            out.append(ink.text(F["sans_md"], line, left + 20, y, 15, P["silk"]))

    pulses = []
    for i, (n, y) in enumerate(zip(cfg["nets"], net_y)):
        label_w = ink.width(F["mono_sb"], n["net"], 13, 0.06)
        out.append(ink.text(F["mono_sb"], n["net"], left, y, 13, P["silk"], track=0.06))
        out.append(ink.text(F["sans"], n["detail"], left, y + 19, 15, P["silk_dim"]))
        pad_x = left + label_w + 12
        out.append(rect(pad_x, y - 8.5, 8, 8, f' fill="{P["tin"]}"'))
        route = [(W, y - 4.5), (pad_x + 8, y - 4.5)]  # signals arrive from off the board
        copper.append(trace(route, width=2.4))
        pulses.append(f'<path class="pulse p{i}" d="{path_d(route)}" pathLength="100"/>')
    out.insert(1, "".join(copper))
    out += pulses
    out.append(chip)

    title, desc = _about(cfg)
    return document(W, H, ink, "".join(out), title=title, desc=desc,
                    defs=(BOARD_DEFS, EPOXY, GLOW), style=PULSE_CSS)
