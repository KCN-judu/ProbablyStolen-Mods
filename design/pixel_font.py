"""Builds a TrueType font from the cover alphabet (covers.FONT), for video titles, timers and labels.

    python design/pixel_font.py design/out/ProbablyStolenPixel.ttf

Capitals only, as on the covers (DESIGN.md, Hierarchy and type): lowercase letters map to the same glyphs.
One font pixel is 128 units and the em is the 7 px cap height, so at a font size of 7 x n px each pixel is
n x n screen pixels and stays crisp: 21 px at 1080p, 42 px at 2160p.
"""
import os
import sys
from collections.abc import Sequence
from typing import Final

from fontTools.fontBuilder import FontBuilder
from fontTools.pens.ttGlyphPen import TTGlyphPen
from fontTools.ttLib.tables._g_l_y_f import Glyph

import covers as C

PX: Final = 128
EM: Final = 7 * PX
ADVANCE: Final = 6 * PX            # 5 px glyph and 1 px letter spacing, as covers.text at x1
ASCENT: Final = 8 * PX
DESCENT: Final = 2 * PX
FAMILY: Final = "Probably Stolen Pixel"
NOTDEF: Final[C.Bitmap] = ("11111", "10001", "10001", "10001", "10001", "10001", "11111")


# Glyph names follow the AGL: `space` and uniXXXX.
def glyph_name(ch: str) -> str:
    return "space" if ch == " " else "uni%04X" % ord(ch)


def outline(rows: C.Bitmap) -> Glyph:
    # One rectangle per run of lit pixels in a row, drawn clockwise, the TrueType outer direction.
    pen = TTGlyphPen(None)
    for j, row in enumerate(rows):
        top = (7 - j) * PX
        i = 0
        while i < len(row):
            if row[i] != "1":
                i += 1
                continue
            start = i
            while i < len(row) and row[i] == "1":
                i += 1
            x0, x1 = start * PX, i * PX
            pen.moveTo((x0, top - PX))
            pen.lineTo((x0, top))
            pen.lineTo((x1, top))
            pen.lineTo((x1, top - PX))
            pen.closePath()
    return pen.glyph()


# Writes the font; glyph set and shapes come from covers.FONT, so a new cover letter appears here without changes.
def build(path: str) -> None:
    chars: Sequence[str] = sorted(C.FONT, key=ord)
    order = [".notdef"] + [glyph_name(ch) for ch in chars]
    glyphs: dict[str, Glyph] = {".notdef": outline(NOTDEF)} | {glyph_name(ch): outline(C.FONT[ch]) for ch in chars}
    # Lowercase letters map to the capitals' glyphs.
    cmap = {ord(ch): glyph_name(ch) for ch in chars} | {ord(ch.lower()): glyph_name(ch) for ch in chars if ch.isalpha()}

    fb = FontBuilder(EM, isTTF=True)
    fb.setupGlyphOrder(order)
    fb.setupCharacterMap(cmap)
    fb.setupGlyf(glyphs)
    # The left side bearing must be each glyph's own left edge, or rasterizers shift narrow glyphs like '.'.
    glyf = fb.font["glyf"]
    fb.setupHorizontalMetrics({name: (ADVANCE, getattr(glyf[name], "xMin", 0)) for name in order})
    fb.setupHorizontalHeader(ascent=ASCENT, descent=-DESCENT)
    fb.setupNameTable({
        "familyName": FAMILY,
        "styleName": "Regular",
        "uniqueFontIdentifier": FAMILY + " Regular",
        "fullName": FAMILY,
        "psName": FAMILY.replace(" ", "") + "-Regular",
        "version": "Version 1.000",
        "designer": "KCN-judu",
        "licenseDescription": "Apache License 2.0",
    })
    fb.setupOS2(sTypoAscender=ASCENT, sTypoDescender=-DESCENT, sTypoLineGap=0,
                usWinAscent=ASCENT, usWinDescent=DESCENT, sCapHeight=EM, sxHeight=EM,
                achVendID="KCNJ", fsType=0)
    fb.setupPost(isFixedPitch=1)
    os.makedirs(os.path.dirname(os.path.abspath(path)), exist_ok=True)
    fb.save(path)
    print(path, len(chars), "glyphs", os.path.getsize(path), "bytes")


if __name__ == "__main__":
    build(sys.argv[1] if len(sys.argv) > 1 else "out/ProbablyStolenPixel.ttf")
