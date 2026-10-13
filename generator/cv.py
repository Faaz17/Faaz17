"""Two cards from the CV, both filled from profile.toml.

Career is a logic analyser: one channel per role, the trace high while the
role ran and coloured by kind (amber for work, green for leadership, mint for
study). A role still running stays high up to the NOW cursor and carries on
dashed. Record is a board of published papers and the awards, each award with
a gold medal.
"""
from __future__ import annotations

from datetime import date

from ghdata import MONTHS
from parts import (BOARD_DEFS, P, SHEEN, STEEL, board, corners, document, instrument, mix, num, path_d, rect,
                   screw, star_d)
from typeset import Ink

KIND = {"work": P["amber"], "lead": P["phosphor"], "study": P["bloom"]}
KIND_NAME = {"work": "WORK", "lead": "LEADERSHIP", "study": "STUDY"}
CRT = ('<radialGradient id="crt" cx="0.5" cy="0.45" r="0.75">'
       f'<stop offset="0" stop-color="#072318"/><stop offset="1" stop-color="{P["glass"]}"/></radialGradient>')


def _month(text: str) -> int:
    """'2025-07' as a count of months, so ranges are subtraction."""
    year, month = text.split("-")
    return int(year) * 12 + int(month) - 1


def _label(m: int) -> str:
    return f"{MONTHS[m % 12].upper()} {m // 12}"


def _span_text(ch: dict) -> str:
    start = _month(ch["from"])
    if not ch.get("to"):
        return f"SINCE {_label(start)}"
    end = _month(ch["to"])
    if start // 12 == end // 12:
        return f"{MONTHS[start % 12].upper()}-{MONTHS[end % 12].upper()} {end // 12}"
    return f"{_label(start)}-{_label(end)}"


class _Axis:
    """Maps months (and today) to x across a chart."""

    def __init__(self, cfg: dict, x0: float, x1: float, today: date):
        self.m0 = _month(cfg["start"])
        self.m1 = _month(cfg["end"]) + 1  # the chart runs to the end of its last month
        self.x0, self.x1 = x0, x1
        self.now = self.x(today.year * 12 + today.month - 1 + (today.day - 1) / 31)

    def x(self, m: float) -> float:
        return self.x0 + (m - self.m0) / (self.m1 - self.m0) * (self.x1 - self.x0)


def _wave(ink: Ink, F, ch: dict, axis: _Axis, high: float, low: float, size: float, *, dates: bool = True) -> str:
    """One channel: low, high while the role ran, low again (or dashed on past NOW).
    With `dates`, the span is printed on the trace."""
    colour = KIND[ch["kind"]]
    start = axis.x(_month(ch["from"]))
    ongoing = not ch.get("to")
    end = axis.now if ongoing else axis.x(_month(ch["to"]) + 1)
    out = [rect(start, high, end - start, low - high, f' fill="{colour}" fill-opacity="0.14"')]
    if ongoing:
        out.append(rect(end, high, axis.x1 - end, low - high, f' fill="{colour}" fill-opacity="0.05"'))
        out.append(f'<path d="M{num(end)} {num(high)}H{num(axis.x1)}" stroke="{colour}" stroke-opacity="0.6" '
                   'stroke-width="1.6" stroke-dasharray="4 3" fill="none"/>')
    lows = [(axis.x0, start)] + ([] if ongoing else [(end, axis.x1)])
    for a, b in lows:
        if b > a:
            out.append(f'<path d="M{num(a)} {num(low)}H{num(b)}" stroke="{colour}" stroke-opacity="0.35" '
                       'stroke-width="1.2" fill="none"/>')
    edge = [(start, low), (start, high), (end, high)] + ([] if ongoing else [(end, low)])
    out.append(f'<path d="{path_d(edge)}" stroke="{colour}" stroke-width="1.8" fill="none" '
               'stroke-linejoin="round" filter="url(#glow2)"/>')
    out.append(f'<path d="{path_d(edge)}" stroke="{colour}" stroke-width="1.8" fill="none" stroke-linejoin="round"/>')

    if not dates:
        return "".join(out)
    # Dates go inside the pulse when it is wide enough, else beside it.
    text = _span_text(ch)
    w = ink.width(F["mono_md"], text, size, 0.04)
    tint = mix(colour, P["glass"], 0.2)
    if end - start >= w + 12:
        tx = start + 6
    elif end + 6 + w <= axis.x1 - 4 and not ongoing:
        tx = end + 6
    else:
        tx = start - 6 - w
    out.append(ink.text(F["mono_md"], text, tx, low - 4, size, tint, track=0.04))
    return "".join(out)


def _grid(axis: _Axis, top: float, bottom: float) -> str:
    lines = []
    for m in range(axis.m0, axis.m1 + 1):
        x = axis.x(m)
        if m % 12 == 0 or m in (axis.m0, axis.m1):
            lines.append(f'<line x1="{num(x)}" y1="{num(top)}" x2="{num(x)}" y2="{num(bottom)}" stroke-opacity="0.9"/>')
        else:
            lines.append(f'<line x1="{num(x)}" y1="{num(top)}" x2="{num(x)}" y2="{num(bottom)}" stroke-dasharray="1 4"/>')
    return f'<g stroke="{P["grid"]}" stroke-width="1">{"".join(lines)}</g>'


def _years(ink: Ink, F, axis: _Axis, y: float, size: float) -> str:
    out = []
    first_year = next((m for m in range(axis.m0 + 1, axis.m1) if m % 12 == 0), axis.m1)
    start_w = ink.width(F["mono"], _label(axis.m0), size, 0.06)
    if axis.x(axis.m0) + 3 + start_w + 6 < axis.x(first_year):  # a narrow chart has no room for both
        out.append(ink.text(F["mono"], _label(axis.m0), axis.x(axis.m0) + 3, y, size, P["phosphor_dim"], track=0.06))
    for m in range(axis.m0 + 1, axis.m1):
        if m % 12 == 0:
            out.append(ink.text(F["mono"], str(m // 12), axis.x(m) + 3, y, size, P["phosphor_dim"], track=0.06))
    return "".join(out)


def _now(ink: Ink, F, axis: _Axis, top: float, bottom: float, label_y: float, size: float) -> str:
    return (f'<line x1="{num(axis.now)}" y1="{num(top)}" x2="{num(axis.now)}" y2="{num(bottom)}" '
            f'stroke="{P["bloom"]}" stroke-opacity="0.55" stroke-dasharray="2 3"/>'
            + ink.text(F["mono_sb"], "NOW", axis.now, label_y, size, P["bloom"], anchor="middle", track=0.08))


def _legend(ink: Ink, F, kinds: list[str], right: float, y: float, size: float) -> str:
    out, x = [], right
    for kind in reversed(kinds):
        name = KIND_NAME[kind]
        w = ink.width(F["mono_md"], name, size, 0.08)
        out.append(ink.text(F["mono_md"], name, x, y, size, mix(KIND[kind], P["glass"], 0.15), anchor="end", track=0.08))
        x -= w + 8
        out.append(rect(x - 14, y - size * 0.45, 14, 3, f' rx="1.5" fill="{KIND[kind]}"'))
        x -= 14 + 16
    return "".join(out)


def _career_about(channels: list[dict]) -> tuple[str, str]:
    return ("Career", "Roles over time: " + "; ".join(
        f"{c['role']}, {c['org']} ({_span_text(c).lower()})" for c in channels) + ".")


GLOW2 = '<filter id="glow2" x="-0.1" y="-1" width="1.2" height="3"><feGaussianBlur stdDeviation="2.2"/></filter>'


def career_desktop(F, cfg: dict, today: date) -> str:
    channels = cfg["channels"]
    W, pitch, top0 = 880, 34, 70
    H = top0 + pitch * len(channels) + 52
    ink = Ink()
    axis = _Axis(cfg, 380, 836, today)
    out = [instrument(W, H, 18)]
    out += [screw(x, y) for x, y in ((12, 12), (W - 12, 12), (12, H - 12), (W - 12, H - 12))]
    out += [rect(20, 20, 840, H - 40, ' rx="14" fill="#061A11" stroke="#173F2D"'),
            rect(28, 28, 824, H - 56, ' rx="10" fill="url(#crt)"')]

    out.append(rect(40, 39, 44, 16, f' rx="3" fill="none" stroke="{P["phosphor"]}"'))
    out.append(ink.text(F["mono_sb"], f"D0-{len(channels) - 1}", 62, 51, 9.5, P["phosphor"], anchor="middle"))
    out.append(ink.text(F["sans_md"], "Roles over time", 94, 52, 13.5, P["bloom"]))
    out.append(_legend(ink, F, ["work", "lead", "study"], 836, 51, 10))

    bottom = top0 + pitch * len(channels)
    out.append(_grid(axis, top0 - 4, bottom))
    for i, ch in enumerate(channels):
        top = top0 + pitch * i
        colour = KIND[ch["kind"]]
        if i:
            out.append(f'<line x1="40" y1="{num(top - 2)}" x2="{num(axis.x1)}" y2="{num(top - 2)}" '
                       f'stroke="{P["grid"]}" stroke-opacity="0.6"/>')
        out.append(rect(40, top + 5, 24, 14, f' rx="2" fill="none" stroke="{colour}" stroke-opacity="0.8"'))
        out.append(ink.text(F["mono_sb"], f"D{i}", 52, top + 15.5, 9, colour, anchor="middle"))
        for text, face, size, colour_, y in ((ch["org"], F["mono_sb"], 11.5, P["silk"], top + 15),
                                             (ch["role"], F["sans"], 12.5, P["silk_dim"], top + 29)):
            if ink.width(face, text, size) > axis.x0 - 74 - 12:
                raise ValueError(f"career entry {text!r} is too wide for its label column; shorten it")
            out.append(ink.text(face, text, 74, y, size, colour_))
        out.append(_wave(ink, F, ch, axis, top + 8, top + 26, 9.5))
    out.append(_now(ink, F, axis, top0 - 4, bottom, bottom + 18, 9.5))
    out.append(_years(ink, F, axis, bottom + 18, 10))

    title, desc = _career_about(channels)
    return document(W, H, ink, "".join(out), title=title, desc=desc, defs=(SHEEN, STEEL, CRT, GLOW2))


def career_mobile(F, cfg: dict, today: date) -> str:
    channels = cfg["channels"]
    W, pitch, top0 = 360, 66, 82
    H = top0 + pitch * len(channels) + 44
    ink = Ink()
    axis = _Axis(cfg, 24, 336, today)
    out = [instrument(W, H, 16)]
    out += [rect(8, 8, 344, H - 16, ' rx="12" fill="#061A11" stroke="#173F2D"'),
            rect(14, 14, 332, H - 28, ' rx="9" fill="url(#crt)"')]
    out.append(rect(24, 26, 44, 16, f' rx="3" fill="none" stroke="{P["phosphor"]}"'))
    out.append(ink.text(F["mono_sb"], f"D0-{len(channels) - 1}", 46, 38, 9.5, P["phosphor"], anchor="middle"))
    out.append(ink.text(F["sans_md"], "Roles over time", 78, 39, 14.5, P["bloom"]))
    out.append(_legend(ink, F, ["work", "lead", "study"], 336, 62, 10))

    for i, ch in enumerate(channels):
        top = top0 + pitch * i
        out.append(_grid(axis, top + 34, top + 54))
        dates = _span_text(ch)
        dw = ink.width(F["mono_md"], dates, 10.5, 0.04)
        if ink.width(F["mono_sb"], ch["org"], 12.5) + dw + 12 > axis.x1 - axis.x0:
            raise ValueError(f"career entry {ch['org']!r} and its dates do not fit a phone row; shorten it")
        out.append(ink.text(F["mono_sb"], ch["org"], 24, top + 12, 12.5, P["silk"]))
        out.append(ink.text(F["mono_md"], dates, 336, top + 12, 10.5, mix(KIND[ch["kind"]], P["glass"], 0.15),
                            anchor="end", track=0.04))
        role = ch["role"]
        if ink.width(F["sans"], role, 13.5) > axis.x1 - axis.x0:
            raise ValueError(f"career role {role!r} is too wide for a phone row; shorten it")
        out.append(ink.text(F["sans"], role, 24, top + 29, 13.5, P["silk_dim"]))
        out.append(_wave(ink, F, ch, axis, top + 38, top + 52, 10, dates=False))  # dates sit on the org line
        out.append(f'<line x1="{num(axis.now)}" y1="{num(top + 34)}" x2="{num(axis.now)}" y2="{num(top + 56)}" '
                   f'stroke="{P["bloom"]}" stroke-opacity="0.5" stroke-dasharray="2 3"/>')
    bottom = top0 + pitch * len(channels)
    out.append(_years(ink, F, axis, bottom + 8, 10.5))
    out.append(ink.text(F["mono_sb"], "NOW", axis.now, bottom + 24, 9.5, P["bloom"], anchor="middle", track=0.08))

    title, desc = _career_about(channels)
    return document(W, H, ink, "".join(out), title=title, desc=desc, defs=(SHEEN, STEEL, CRT, GLOW2))


# --- the record: papers and awards -------------------------------------------

def medal(x: float, y: float, r: float = 11) -> str:
    """A gold medal on two ribbons, amber and green. Needs the gold gradient (BOARD_DEFS)."""
    ribbons = (f'<path d="M{num(x - 3)} {num(y + 2)}L{num(x - 9)} {num(y + r + 10)}L{num(x - 4)} {num(y + r + 7)}'
               f'L{num(x - 1)} {num(y + r + 11)}L{num(x + 1)} {num(y + 3)}Z" fill="{P["amber"]}"/>'
               f'<path d="M{num(x + 3)} {num(y + 2)}L{num(x + 9)} {num(y + r + 10)}L{num(x + 4)} {num(y + r + 7)}'
               f'L{num(x + 1)} {num(y + r + 11)}L{num(x - 1)} {num(y + 3)}Z" fill="{P["phosphor"]}"/>')
    return (ribbons
            + f'<circle cx="{num(x)}" cy="{num(y)}" r="{r}" fill="url(#gold)"/>'
            + f'<circle cx="{num(x)}" cy="{num(y)}" r="{num(r * 0.74)}" fill="none" stroke="#9C7426" stroke-width="1"/>'
            + f'<path d="{star_d(x, y, r * 0.5)}" fill="#8A6620"/>')


def _record_items(ink: Ink, F, rec: dict, x: float, y: float, width: float, *, phone: bool) -> tuple[list[str], float]:
    """Papers: a gold pad, the venue, the title, a note. Returns (svg parts, bottom)."""
    title_size, venue_size, note_size, line = (15, 11.5, 11, 20) if phone else (14, 11, 10.5, 18.5)
    out = []
    for paper in rec["papers"]:
        out.append(rect(x, y - 9, 9, 9, ' fill="url(#gold)"'))
        out.append(ink.text(F["mono_sb"], paper["venue"], x + 18, y, venue_size, P["amber"], track=0.06))
        lines = ink.wrap(F["sans_md"], paper["title"], title_size, width - 18)
        for k, text in enumerate(lines):
            out.append(ink.text(F["sans_md"], text, x + 18, y + 20 + line * k, title_size, P["silk"]))
        y_note = y + 20 + line * (len(lines) - 1) + 17
        out.append(ink.text(F["mono"], paper["note"], x + 18, y_note, note_size, P["silk_faint"]))
        y = y_note + (36 if phone else 32)
    return out, y


def _awards(ink: Ink, F, rec: dict, x: float, y: float, width: float, *, phone: bool) -> tuple[list[str], float]:
    title_size, detail_size, pitch = (15, 11.5, 56) if phone else (14, 10.5, 50)
    out = []
    for award in rec["awards"]:
        if ink.width(F["sans_md"], award["title"], title_size) > width - 34:
            raise ValueError(f"award {award['title']!r} is too wide; shorten it")
        out.append(medal(x + 11, y - 6))
        out.append(ink.text(F["sans_md"], award["title"], x + 34, y - 2, title_size, P["silk"]))
        out.append(ink.text(F["mono"], award["detail"], x + 34, y + 15, detail_size, P["silk_dim"]))
        y += pitch
    return out, y


def _record_about(rec: dict) -> tuple[str, str]:
    papers = "; ".join(f"{p['title']} ({p['venue']})" for p in rec["papers"])
    awards = "; ".join(f"{a['title']}, {a['detail']}" for a in rec["awards"])
    return "Published and awarded", f"Papers: {papers}. Awards for {rec['awards_for']}: {awards}."


def record_desktop(F, rec: dict) -> str:
    W = 880
    ink = Ink()
    papers, p_bottom = _record_items(ink, F, rec, 40, 92, 470, phone=False)
    awards, a_bottom = _awards(ink, F, rec, 566, 102, 290, phone=False)
    H = max(p_bottom, a_bottom) + 6
    out = [board(W, H, holes=corners(W, H, 18))]
    out.append(ink.text(F["display"], "PUBLISHED", 40, 52, 12, P["silk"], track=0.16))
    out.append(ink.text(F["mono"], "conference papers, 2026", 182, 52, 10.5, P["silk_faint"]))
    out.append(ink.text(F["display"], "AWARDED", 566, 52, 12, P["silk"], track=0.16))
    out.append(ink.text(F["mono"], f"for {rec['awards_for']}", 680, 52, 10.5, P["silk_faint"]))
    out.append(f'<line x1="538" y1="34" x2="538" y2="{num(H - 34)}" stroke="{P["silk"]}" stroke-opacity="0.22" '
               'stroke-dasharray="3 4"/>')
    out += papers + awards
    title, desc = _record_about(rec)
    return document(W, H, ink, "".join(out), title=title, desc=desc, defs=(BOARD_DEFS,))


def record_mobile(F, rec: dict) -> str:
    W = 360
    ink = Ink()
    papers, p_bottom = _record_items(ink, F, rec, 24, 100, 312, phone=True)
    awards_top = p_bottom + 46
    awards, a_bottom = _awards(ink, F, rec, 24, awards_top + 52, 312, phone=True)
    H = a_bottom + 4
    out = [board(W, H, holes=corners(W, H, 16), hole_r=3.6)]
    out.append(ink.text(F["display"], "PUBLISHED", 36, 50, 13, P["silk"], track=0.16))
    out.append(ink.text(F["mono"], "conference papers, 2026", 36, 70, 11.5, P["silk_faint"]))
    out.append(f'<line x1="24" y1="{num(p_bottom - 6)}" x2="336" y2="{num(p_bottom - 6)}" stroke="{P["silk"]}" '
               'stroke-opacity="0.22" stroke-dasharray="3 4"/>')
    out.append(ink.text(F["display"], "AWARDED", 36, awards_top, 13, P["silk"], track=0.16))
    out.append(ink.text(F["mono"], f"for {rec['awards_for']}", 36, awards_top + 20, 11.5, P["silk_faint"]))
    out += papers + awards
    title, desc = _record_about(rec)
    return document(W, H, ink, "".join(out), title=title, desc=desc, defs=(BOARD_DEFS,))
