"""Projects as plug-in modules, and the connector badges.

Each project card shows how its system works as a signal-flow diagram, taken
from `flow` (and an optional `tap` branch) in profile.toml. On desktop the
diagram runs left to right and a pulse is handed from block to block; on a
phone it runs top to bottom without the pulse, since the arrows are too short
to carry one.
"""
from __future__ import annotations

import math
from datetime import date

from ghdata import month_label
from parts import (BOARD_DEFS, EPOXY, METAL, P, PULSE_CSS, board, document, fingers, num, path_d, rect,
                   star_d, tag_pill, trace)
from typeset import Ink

SHADES = [P["phosphor"], "#3CC27D", "#2A8B5B"]  # language dots, largest first


def _arrow(x: float, y: float, direction: str) -> str:
    """An arrowhead whose tip is at (x, y)."""
    if direction == "right":
        pts = [(x - 7, y - 4.5), (x, y), (x - 7, y + 4.5)]
    else:  # down
        pts = [(x - 4.5, y - 7), (x, y), (x + 4.5, y - 7)]
    return f'<path d="{path_d(pts)}Z" fill="{P["trace_lit"]}"/>'


def _pad(x: float, y: float, w: float, h: float) -> str:
    """A gold contact where a trace meets a block."""
    return rect(x, y, w, h, f' fill="{METAL}"')


def _frame(ink: Ink, F, x: float, y: float, w: float, h: float, size: float) -> str:
    """A silkscreen frame titled SIGNAL FLOW, the title breaking its top edge."""
    tw = ink.width(F["mono_md"], "SIGNAL FLOW", size, 0.14)
    return (rect(x, y, w, h, f' rx="4" fill="none" stroke="{P["silk"]}" stroke-opacity="0.22" stroke-width="0.8"')
            + rect(x + 8, y - size * 0.7, tw + 12, size * 1.4, f' fill="{P["mask"]}"')
            + ink.text(F["mono_md"], "SIGNAL FLOW", x + 14, y + size * 0.36, size, P["silk_faint"], track=0.14))


def _block(ink: Ink, F, x, y, w, h, part: dict, *, two_lines: bool, label: float, note: float) -> str:
    """One stage of the diagram, drawn as a module package with its name and a note,
    either centred on two lines or side by side on one."""
    lw = ink.width(F["mono_sb"], part["part"], label, 0.05)
    nw = ink.width(F["sans"], part["note"], note)
    fits = max(lw, nw) <= w - 12 if two_lines else lw + nw + 30 <= w
    if not fits:
        raise ValueError(f"block {part['part']!r} / {part['note']!r} does not fit; shorten it")
    out = [rect(x, y, w, h, f' rx="3" fill="url(#epoxy)" stroke="{P["epoxy_edge"]}"')]
    if two_lines:
        out.append(ink.text(F["mono_sb"], part["part"], x + w / 2, y + h * 0.43, label, P["silk"],
                            anchor="middle", track=0.05))
        out.append(ink.text(F["sans"], part["note"], x + w / 2, y + h * 0.43 + note * 1.25, note, P["silk_dim"],
                            anchor="middle"))
    else:
        base = y + h / 2 + label * 0.36
        out.append(ink.text(F["mono_sb"], part["part"], x + 12, base, label, P["silk"], track=0.05))
        out.append(ink.text(F["sans"], part["note"], x + w - 12, base, note, P["silk_dim"], anchor="end"))
    return "".join(out)


def _diagram_across(ink: Ink, F, flow: list, tap: dict | None, x0: float, x1: float, y: float) -> tuple[str, str]:
    """Blocks left to right, the tap branching down. Returns (svg, pulses)."""
    n, gap, bh = len(flow), 30, 42
    bw = (x1 - x0 - gap * (n - 1)) / n
    cy = y + bh / 2
    copper, parts, pulses, contacts = [], [], [], []
    for i, part in enumerate(flow):
        bx = x0 + i * (bw + gap)
        parts.append(_block(ink, F, bx, y, bw, bh, part, two_lines=True, label=10.5, note=11.5))
        if i < n - 1:
            route = [(bx + bw + 1, cy), (bx + bw + gap - 1, cy)]
            copper.append(trace(route, width=2.2, color=P["trace_lit"]) + _arrow(route[1][0], cy, "right"))
            pulses.append(f'<path class="flow s{i}" d="{path_d(route)}" pathLength="100"/>')
            contacts.append(_pad(bx + bw - 2, cy - 4, 4, 8) + _pad(bx + bw + gap - 2, cy - 4, 4, 8))
    if tap:
        src = tap["from"]
        bx = x0 + src * (bw + gap)
        ty = y + bh + 26
        parts.append(_block(ink, F, bx, ty, bw, bh, tap, two_lines=True, label=10.5, note=11.5))
        route = [(bx + bw / 2, y + bh + 1), (bx + bw / 2, ty - 1)]
        copper.append(trace(route, width=2.2, color=P["trace_lit"]) + _arrow(bx + bw / 2, ty - 1, "down"))
        pulses.append(f'<path class="flow s{src}" d="{path_d(route)}" pathLength="100"/>')
        contacts.append(_pad(bx + bw / 2 - 4, y + bh - 2, 8, 4) + _pad(bx + bw / 2 - 4, ty - 2, 8, 4))
    return "".join(copper + parts + contacts), "".join(pulses)


def _diagram_down(ink: Ink, F, flow: list, tap: dict | None, x0: float, x1: float, y: float) -> tuple[str, float]:
    """Blocks top to bottom, the tap indented below them. Returns (svg, bottom edge)."""
    bh, gap = 32, 14
    copper, parts, contacts = [], [], []
    tops = []
    for i, part in enumerate(flow):
        by = y + i * (bh + gap)
        tops.append(by)
        parts.append(_block(ink, F, x0, by, x1 - x0, bh, part, two_lines=False, label=12.5, note=13))
        if i < len(flow) - 1:
            ax = x0 + 26
            copper.append(trace([(ax, by + bh + 1), (ax, by + bh + gap - 1)], width=2.2, color=P["trace_lit"])
                          + _arrow(ax, by + bh + gap - 1, "down"))
            contacts.append(_pad(ax - 4, by + bh - 2, 8, 4) + _pad(ax - 4, by + bh + gap - 2, 8, 4))
    bottom = tops[-1] + bh
    if tap:
        ty = bottom + gap
        indent = x0 + 24
        parts.append(_block(ink, F, indent, ty, x1 - indent, bh, tap, two_lines=False, label=12.5, note=13))
        sy, gutter = tops[tap["from"]] + bh / 2, x0 - 12
        route = [(x0 - 1, sy), (gutter, sy), (gutter, ty + bh / 2), (indent - 1, ty + bh / 2)]
        copper.append(trace(route, width=2.2, color=P["trace_lit"]) + _arrow(indent - 1, ty + bh / 2, "right"))
        contacts.append(_pad(x0 - 2, sy - 4, 4, 8) + _pad(indent - 2, ty + bh / 2 - 4, 4, 8))
        bottom = ty + bh
    return "".join(copper + parts + contacts), bottom


def _meta(ink: Ink, F, repo: dict, hide: list[str], x: float, y: float, right: float, *, size: float,
          langs_max: int) -> str:
    out = []
    langs = [e["node"]["name"] for e in repo["languages"]["edges"] if e["node"]["name"] not in hide][:langs_max]
    for shade, lang in zip(SHADES, langs):
        out.append(f'<circle cx="{num(x + 3.5)}" cy="{num(y - size * 0.33)}" r="3.5" fill="{shade}"/>')
        out.append(ink.text(F["mono"], lang, x + 11, y, size, P["silk_dim"]))
        x += 11 + ink.width(F["mono"], lang, size) + 14
    if repo["stargazerCount"]:
        out.append(f'<path d="{star_d(x + 5, y - size * 0.36, 5.5)}" fill="{P["silk_dim"]}"/>')
        out.append(ink.text(F["mono"], str(repo["stargazerCount"]), x + 14, y, size, P["silk_dim"]))
    pushed = date.fromisoformat(repo["pushedAt"][:10])
    out.append(ink.text(F["mono"], f"updated {month_label(pushed)}", right, y, size, P["silk_faint"], anchor="end"))
    return "".join(out)


def _about(proj: dict, blurb: str) -> tuple[str, str]:
    steps = " to ".join(p["part"].title() for p in proj["flow"])
    return f"{proj['title']}: {proj['tag']}", f"{blurb} Signal flow: {steps}."


def project_desktop(F, proj: dict, repo: dict, hide: list[str]) -> str:
    W, H = 880, 206
    ink = Ink()
    out = [board(W, H, r=14, holes=[(18, 18), (W - 18, 18)])]

    pill, right = tag_pill(ink, F, proj["tag"].upper(), 43, 22.5, 10)
    out.append(pill)
    out.append(ink.text(F["mono"], proj["context"], right + 14, 22.5, 10.5, P["silk_dim"], track=0.02))
    out.append(ink.text(F["mono_md"], "OPEN REPO ↗", W - 38, 22.5, 10, P["silk_faint"], anchor="end", track=0.08))

    size = 18.0
    while ink.width(F["display"], proj["title"], size, 0.02) > 360:  # the text column is 360 wide
        size -= 0.5
    out.append(ink.text(F["display"], proj["title"], 24, 66, size, P["silk"], track=0.02))
    blurb = proj.get("blurb") or repo["description"] or ""
    lines = ink.wrap(F["sans"], blurb, 13.5, 352)
    if len(lines) > 4:
        raise ValueError(f"blurb for {repo['name']} needs {len(lines)} lines on its card; keep it to 4")
    for i, line in enumerate(lines):
        out.append(ink.text(F["sans"], line, 24, 92 + 18.5 * i, 13.5, P["silk_body"]))

    tap = proj.get("tap")
    out.append(_frame(ink, F, 398, 36, W - 24 - 398 + 10, 126, 8.5))  # ends 10px above the meta row
    diagram, pulses = _diagram_across(ink, F, proj["flow"], tap, 412, W - 28, 48 if tap else 78)
    out.append(diagram)
    out.append(pulses)
    out.append(_meta(ink, F, repo, hide, 24, 180, W - 24, size=11, langs_max=3))
    out.append(fingers(40, W - 40, H - 12))

    title, desc = _about(proj, blurb)
    return document(W, H, ink, "".join(out), title=title, desc=desc, defs=(BOARD_DEFS, EPOXY), style=PULSE_CSS)


def project_mobile(F, proj: dict, repo: dict, hide: list[str]) -> str:
    W, left = 360, 24
    ink = Ink()
    blurb = proj.get("blurb") or repo["description"] or ""
    context = ink.wrap(F["mono"], proj["context"], 11.5, W - 2 * left)
    lines = ink.wrap(F["sans"], blurb, 15, W - 2 * left)
    titles = ink.wrap(F["display"], proj["title"], 21, W - 2 * left, 0.02)
    title_y = [56 + 17 * len(context) + 24 + 26 * i for i in range(len(titles))]
    blurb_y = [title_y[-1] + 30 + 21 * i for i in range(len(lines))]
    diagram_y = blurb_y[-1] + 38
    diagram, bottom = _diagram_down(ink, F, proj["flow"], proj.get("tap"), 44, W - left - 8, diagram_y)
    frame = _frame(ink, F, 22, diagram_y - 16, W - 44, bottom - diagram_y + 30, 9)
    meta_y = bottom + 46
    H = meta_y + 34

    out = [board(W, H, r=14, holes=[(16, 16), (W - 16, 16)], hole_r=3.6)]
    pill, _ = tag_pill(ink, F, proj["tag"].upper(), 38, 22.5, 10.5)
    out.append(pill)
    out.append(ink.text(F["mono_md"], "OPEN ↗", W - 36, 22.5, 10.5, P["silk_faint"], anchor="end", track=0.08))
    for i, line in enumerate(context):
        out.append(ink.text(F["mono"], line, left, 56 + 17 * i, 11.5, P["silk_dim"]))
    for line, y in zip(titles, title_y):
        out.append(ink.text(F["display"], line, left, y, 21, P["silk"], track=0.02))
    for line, y in zip(lines, blurb_y):
        out.append(ink.text(F["sans"], line, left, y, 15, P["silk_body"]))
    out.append(frame)
    out.append(diagram)
    out.append(_meta(ink, F, repo, hide, left, meta_y, W - left, size=12, langs_max=2))
    out.append(fingers(40, W - 40, H - 12))

    title, desc = _about(proj, blurb)
    return document(W, H, ink, "".join(out), title=title, desc=desc, defs=(BOARD_DEFS, EPOXY))


def link_badge(F, label: str, handle: str) -> str:
    """A connector: a 2x3 pin header beside who and where."""
    H = 44
    ink = Ink()
    w1 = ink.width(F["display"], label.upper(), 10.5, 0.16)
    w2 = ink.width(F["mono"], handle, 10)
    W = math.ceil(48 + max(w1, w2) + 18)
    pins = "".join(rect(14 + 9 * c, 9 + 9 * r, 6, 6) for r in range(3) for c in range(2))
    out = [board(W, H, r=10),
           rect(10, 5, 23, 34, f' rx="2" fill="none" stroke="{P["silk"]}" stroke-opacity="0.3" stroke-width="0.8"'),
           f'<g fill="{METAL}">{pins}</g>',
           ink.text(F["display"], label.upper(), 46, 20, 10.5, P["silk"], track=0.16),
           ink.text(F["mono"], handle, 46, 34, 10, P["silk_dim"])]
    return document(W, H, ink, "".join(out), title=f"{label}: {handle}", desc=f"{label}: {handle}",
                    defs=(BOARD_DEFS,))
