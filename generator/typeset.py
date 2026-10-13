"""Text drawn as glyph outlines.

An SVG <text> element renders in whatever fonts the viewer happens to have, so
the same card looks different on every machine and its layout cannot be
measured ahead of time. Here every string is shaped with HarfBuzz (so kerning
is right) and emitted as <use> references to outlines taken from the fonts in
assets/fonts. Each SVG defines every glyph it needs exactly once.
"""
from __future__ import annotations

from pathlib import Path

import uharfbuzz as hb
from fontTools.pens.svgPathPen import SVGPathPen
from fontTools.ttLib import TTFont


class Face:
    """One font file: shaped by HarfBuzz, drawn by fontTools."""

    def __init__(self, key: str, path: Path):
        self.key = key  # prefix for glyph ids, unique per face
        self._hb = hb.Font(hb.Face(path.read_bytes()))
        tt = TTFont(path)
        self.upm = tt["head"].unitsPerEm
        self.cap = tt["OS/2"].sCapHeight / self.upm  # cap height in em
        self._glyphset = tt.getGlyphSet()
        self._names = tt.getGlyphOrder()
        self._outlines: dict[int, str] = {}

    def shape(self, text: str) -> list[tuple[int, int, int, int]]:
        """(glyph id, x advance, x offset, y offset) per glyph, in font units."""
        buf = hb.Buffer()
        buf.add_str(text)
        buf.guess_segment_properties()
        hb.shape(self._hb, buf, {"kern": True})
        glyphs = []
        for info, pos in zip(buf.glyph_infos, buf.glyph_positions):
            if info.codepoint == 0:
                raise ValueError(f"font {self.key!r} has no glyph for a character in {text!r}")
            glyphs.append((info.codepoint, pos.x_advance, pos.x_offset, pos.y_offset))
        return glyphs

    def outline(self, gid: int) -> str:
        if gid not in self._outlines:
            pen = SVGPathPen(self._glyphset)
            self._glyphset[self._names[gid]].draw(pen)
            self._outlines[gid] = pen.getCommands()
        return self._outlines[gid]


class Ink:
    """The glyph outlines one SVG document uses."""

    def __init__(self):
        self._defs: dict[str, str] = {}

    def width(self, face: Face, text: str, size: float, track: float = 0.0) -> float:
        """Rendered width in px. `track` is extra letter spacing in em."""
        glyphs = face.shape(text)
        units = sum(g[1] for g in glyphs) + track * face.upm * max(len(glyphs) - 1, 0)
        return units * size / face.upm

    def text(self, face: Face, text: str, x: float, y: float, size: float, fill: str, *,
             track: float = 0.0, anchor: str = "start", extra: str = "") -> str:
        """A run of text with its baseline at y. `anchor` is start, middle or end."""
        if anchor != "start":
            w = self.width(face, text, size, track)
            x -= w / 2 if anchor == "middle" else w
        k = size / face.upm
        gap = track * face.upm
        uses, pen = [], 0.0
        for gid, advance, dx, dy in face.shape(text):
            if face.outline(gid):  # spaces have no outline
                ref = f"{face.key}{gid}"
                self._defs.setdefault(ref, face.outline(gid))
                uses.append(f'<use href="#{ref}" x="{pen + dx:.0f}"' + (f' y="{dy}"' if dy else "") + "/>")
            pen += advance + gap
        # Glyphs are drawn in font units (y up), so the run is scaled and flipped once here.
        return (f'<g transform="translate({x:.1f} {y:.1f}) scale({k:.5f} {-k:.5f})" '
                f'fill="{fill}"{extra}>{"".join(uses)}</g>')

    def wrap(self, face: Face, text: str, size: float, max_width: float, track: float = 0.0) -> list[str]:
        """Greedy line breaks at spaces."""
        lines, line = [], ""
        for word in text.split():
            trial = f"{line} {word}".strip()
            if line and self.width(face, trial, size, track) > max_width:
                lines.append(line)
                line = word
            else:
                line = trial
        if line:
            lines.append(line)
        return lines

    def defs(self) -> str:
        return "".join(f'<path id="{ref}" d="{d}"/>' for ref, d in self._defs.items())
