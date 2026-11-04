"""Renders the mod covers described in DESIGN.md, each with its mod's version from manifest.xml.

    python design/covers.py design/out
    python design/covers.py design/out --checkouts ~/Desktop --sync   # also into each mod's preview.png

Everything is drawn on a 320x180 logical canvas and scaled x4 with nearest-neighbour.
"""
import os
import shutil
import sys
from collections.abc import Callable, Mapping, Sequence
from dataclasses import dataclass
from types import MappingProxyType
from typing import Final, Literal, NamedTuple, TypeAlias

from PIL import Image

from typed import as_dict, load_json, member, split_ids, str_map, take_flag, take_option
from version import read_version, version_label

Color: TypeAlias = tuple[int, int, int]
Rgba: TypeAlias = tuple[int, int, int, int]
Bitmap: TypeAlias = Sequence[str]

W: Final = 320
H: Final = 180
SCALE: Final = 4
MARGIN: Final = 16
TEXT_X0: Final = 16
TEXT_X1: Final = 144
IMG_X0: Final = 160
IMG_X1: Final = 304

# Palette (DESIGN.md, Colour)
BG0: Final[Color] = (0x17, 0x15, 0x1F)
BG1: Final[Color] = (0x1F, 0x1C, 0x2B)
BG2: Final[Color] = (0x25, 0x22, 0x33)
PANEL: Final[Color] = (0x2E, 0x2B, 0x40)
PANEL_HI: Final[Color] = (0x48, 0x42, 0x60)
PANEL_LO: Final[Color] = (0x12, 0x10, 0x18)
SLOT: Final[Color] = (0x23, 0x21, 0x31)
SLOT_HI: Final[Color] = (0x33, 0x30, 0x46)
CREAM: Final[Color] = (0xF3, 0xE6, 0xC8)
CREAM_DIM: Final[Color] = (0xC9, 0xBB, 0x9C)
MUTED: Final[Color] = (0xA7, 0x9F, 0xBF)
FAINT: Final[Color] = (0x5E, 0x57, 0x75)
TEAL: Final[Color] = (0x4C, 0xC3, 0xB5)
ORANGE: Final[Color] = (0xF0, 0x8A, 0x3C)
GREEN: Final[Color] = (0x5C, 0xEB, 0x6B)
AMBER: Final[Color] = (0xFF, 0xB8, 0x29)
RED: Final[Color] = (0xE2, 0x50, 0x4A)
CYAN: Final[Color] = (0x59, 0xD1, 0xFF)
RUST: Final[Color] = (0x9A, 0x5A, 0x3C)
STEEL: Final[Color] = (0x7C, 0x86, 0x9A)
STEEL_LO: Final[Color] = (0x4E, 0x55, 0x66)
LILAC: Final[Color] = (0xC3, 0xA6, 0xEA)
LILAC_DIM: Final[Color] = (0x6E, 0x5E, 0x8C)
PINK: Final[Color] = (0xE8, 0x6A, 0x92)
PINK_HI: Final[Color] = (0xF6, 0xB0, 0xC6)
PINK_LO: Final[Color] = (0x8C, 0x3E, 0x5C)
WOOD_LO: Final[Color] = (0x6A, 0x3A, 0x28)

# 5x7 capitals, digits and the few signs the covers use.
FONT: Final[Mapping[str, Bitmap]] = MappingProxyType({
    'A': ["01110", "10001", "10001", "11111", "10001", "10001", "10001"],
    'B': ["11110", "10001", "10001", "11110", "10001", "10001", "11110"],
    'C': ["01110", "10001", "10000", "10000", "10000", "10001", "01110"],
    'D': ["11110", "10001", "10001", "10001", "10001", "10001", "11110"],
    'E': ["11111", "10000", "10000", "11110", "10000", "10000", "11111"],
    'F': ["11111", "10000", "10000", "11110", "10000", "10000", "10000"],
    'G': ["01110", "10001", "10000", "10111", "10001", "10001", "01111"],
    'H': ["10001", "10001", "10001", "11111", "10001", "10001", "10001"],
    'I': ["11111", "00100", "00100", "00100", "00100", "00100", "11111"],
    'J': ["00111", "00010", "00010", "00010", "00010", "10010", "01100"],
    'K': ["10001", "10010", "10100", "11000", "10100", "10010", "10001"],
    'L': ["10000", "10000", "10000", "10000", "10000", "10000", "11111"],
    'M': ["10001", "11011", "10101", "10101", "10001", "10001", "10001"],
    'N': ["10001", "11001", "10101", "10011", "10001", "10001", "10001"],
    'O': ["01110", "10001", "10001", "10001", "10001", "10001", "01110"],
    'P': ["11110", "10001", "10001", "11110", "10000", "10000", "10000"],
    'Q': ["01110", "10001", "10001", "10001", "10101", "10010", "01101"],
    'R': ["11110", "10001", "10001", "11110", "10100", "10010", "10001"],
    'S': ["01111", "10000", "10000", "01110", "00001", "00001", "11110"],
    'T': ["11111", "00100", "00100", "00100", "00100", "00100", "00100"],
    'U': ["10001", "10001", "10001", "10001", "10001", "10001", "01110"],
    'V': ["10001", "10001", "10001", "10001", "10001", "01010", "00100"],
    'W': ["10001", "10001", "10001", "10101", "10101", "10101", "01010"],
    'X': ["10001", "10001", "01010", "00100", "01010", "10001", "10001"],
    'Y': ["10001", "10001", "01010", "00100", "00100", "00100", "00100"],
    'Z': ["11111", "00001", "00010", "00100", "01000", "10000", "11111"],
    '0': ["01110", "10011", "10101", "10101", "11001", "10001", "01110"],
    '1': ["00100", "01100", "00100", "00100", "00100", "00100", "01110"],
    '2': ["01110", "10001", "00001", "00010", "00100", "01000", "11111"],
    '3': ["11110", "00001", "00001", "01110", "00001", "00001", "11110"],
    '4': ["00010", "00110", "01010", "10010", "11111", "00010", "00010"],
    '5': ["11111", "10000", "11110", "00001", "00001", "10001", "01110"],
    '6': ["00110", "01000", "10000", "11110", "10001", "10001", "01110"],
    '7': ["11111", "00001", "00010", "00100", "01000", "01000", "01000"],
    '8': ["01110", "10001", "10001", "01110", "10001", "10001", "01110"],
    '9': ["01110", "10001", "10001", "01111", "00001", "00010", "01100"],
    '.': ["00000", "00000", "00000", "00000", "00000", "01100", "01100"],
    ',': ["00000", "00000", "00000", "00000", "01100", "00100", "01000"],
    ':': ["00000", "01100", "01100", "00000", "01100", "01100", "00000"],
    '-': ["00000", "00000", "00000", "01110", "00000", "00000", "00000"],
    '/': ["00001", "00010", "00010", "00100", "01000", "01000", "10000"],
    "'": ["00100", "00100", "01000", "00000", "00000", "00000", "00000"],
    '>': ["01000", "00100", "00010", "00001", "00010", "00100", "01000"],
    '+': ["00000", "00100", "00100", "11111", "00100", "00100", "00000"],
    ' ': ["00000"] * 7,
    # The rest of printable ASCII, so the font built from this table (pixel_font.py) sets any English text.
    '!': ["00100", "00100", "00100", "00100", "00100", "00000", "00100"],
    '"': ["01010", "01010", "01010", "00000", "00000", "00000", "00000"],
    '#': ["01010", "01010", "11111", "01010", "11111", "01010", "01010"],
    '$': ["00100", "01111", "10100", "01110", "00101", "11110", "00100"],
    '%': ["11000", "11001", "00010", "00100", "01000", "10011", "00011"],
    '&': ["01100", "10010", "10100", "01000", "10101", "10010", "01101"],
    '(': ["00010", "00100", "01000", "01000", "01000", "00100", "00010"],
    ')': ["01000", "00100", "00010", "00010", "00010", "00100", "01000"],
    '*': ["00000", "00100", "10101", "01110", "10101", "00100", "00000"],
    ';': ["00000", "01100", "01100", "00000", "01100", "00100", "01000"],
    '<': ["00010", "00100", "01000", "10000", "01000", "00100", "00010"],
    '=': ["00000", "00000", "11111", "00000", "11111", "00000", "00000"],
    '?': ["01110", "10001", "00001", "00010", "00100", "00000", "00100"],
    '@': ["01110", "10001", "10111", "10101", "10111", "10000", "01110"],
    '[': ["01110", "01000", "01000", "01000", "01000", "01000", "01110"],
    '\\': ["10000", "01000", "01000", "00100", "00010", "00010", "00001"],
    ']': ["01110", "00010", "00010", "00010", "00010", "00010", "01110"],
    '^': ["00100", "01010", "10001", "00000", "00000", "00000", "00000"],
    '_': ["00000", "00000", "00000", "00000", "00000", "00000", "11111"],
    '`': ["01000", "00100", "00010", "00000", "00000", "00000", "00000"],
    '{': ["00010", "00100", "00100", "01000", "00100", "00100", "00010"],
    '|': ["00100", "00100", "00100", "00100", "00100", "00100", "00100"],
    '}': ["01000", "00100", "00100", "00010", "00100", "00100", "01000"],
    '~': ["00000", "00000", "01000", "10101", "00010", "00000", "00000"],
})

# 7x7 hand-drawn 文 for the language cover.
WEN: Final[Bitmap] = ("0001000", "1111111", "0100010", "0010100", "0001000", "0110110", "1000001")

# Ordered dither (Bayer 4x4) for the vignette.
BAYER: Final[Sequence[Sequence[int]]] = ((0, 8, 2, 10), (12, 4, 14, 6), (3, 11, 1, 9), (15, 7, 13, 5))


def vignette(x: int, y: int, cx: float, cy: float, rx: float, ry: float) -> Color:
    """The ordered-dither background colour at (x, y): lighter toward (cx, cy), darker toward the corners."""
    d = (((x - cx) / rx) ** 2 + ((y - cy) / ry) ** 2) ** 0.5
    level = int(max(0.0, min(1.0, 1.0 - d)) * 2.2 * 16)
    th = BAYER[y % 4][x % 4]
    return BG2 if level > 16 + th else BG1 if level > th else BG0


class Canvas:
    """A pixel canvas of its own size; every drawing call clips to it. `RGBA` canvases start transparent."""

    def __init__(self, w: int = W, h: int = H, mode: Literal["RGB", "RGBA"] = "RGB") -> None:
        self.w: int = w
        self.h: int = h
        self.alpha: bool = mode == "RGBA"
        self.img: Image.Image = Image.new("RGBA", (w, h), (0, 0, 0, 0)) if self.alpha else Image.new("RGB", (w, h), BG0)
        self.version: str = "V1.0"   # set from the mod's manifest before drawing
        px = self.img.load()
        if px is None:
            raise RuntimeError("the image has no pixel access")
        self._px = px

    def put(self, x: int, y: int, c: Color | Rgba) -> None:
        if 0 <= x < self.w and 0 <= y < self.h:
            self._px[x, y] = (*c, 255) if self.alpha and len(c) == 3 else c

    def get(self, x: int, y: int) -> tuple[int, ...]:
        v = self._px[x, y]
        return v if isinstance(v, tuple) else (int(v),)

    def lit(self, x: int, y: int) -> bool:
        """Whether (x, y) is on the canvas and not transparent."""
        return 0 <= x < self.w and 0 <= y < self.h and self.get(x, y)[3] != 0

    def rect(self, x: int, y: int, w: int, h: int, c: Color | Rgba) -> None:
        # Clipped to the canvas once and filled in one call, instead of one bounds check per pixel.
        x0, y0, x1, y1 = max(x, 0), max(y, 0), min(x + w, self.w), min(y + h, self.h)
        if x0 < x1 and y0 < y1:
            self.img.paste((*c, 255) if self.alpha and len(c) == 3 else c, (x0, y0, x1, y1))

    def paint(self, colour_at: Callable[[int, int], Color]) -> None:
        """Sets every pixel of an opaque canvas from its position, in one pass."""
        self.img.putdata([colour_at(x, y) for y in range(self.h) for x in range(self.w)])

    def frame(self, x: int, y: int, w: int, h: int, c: Color) -> None:
        self.rect(x, y, w, 1, c)
        self.rect(x, y + h - 1, w, 1, c)
        self.rect(x, y, 1, h, c)
        self.rect(x + w - 1, y, 1, h, c)

    def hline(self, x: int, y: int, w: int, c: Color) -> None:
        self.rect(x, y, w, 1, c)

    def vline(self, x: int, y: int, h: int, c: Color) -> None:
        self.rect(x, y, 1, h, c)

    def bitmap(self, x: int, y: int, rows: Bitmap, c: Color, scale: int = 1) -> None:
        for j, row in enumerate(rows):
            for i, bit in enumerate(row):
                if bit == '1':
                    self.rect(x + i * scale, y + j * scale, scale, scale, c)

    def text(self, x: int, y: int, s: str, c: Color, scale: int = 1, spacing: int | None = None) -> int:
        spacing = scale if spacing is None else spacing
        for ch in s.upper():
            self.bitmap(x, y, FONT[ch], c, scale)
            x += 5 * scale + spacing
        return x

    # A machinery plate: body, 1 px bevel, rivets (DESIGN.md, Colour: depth by value).
    def plate(self, x: int, y: int, w: int, h: int, body: Color = PANEL, rivets: bool = True) -> None:
        self.rect(x, y, w, h, body)
        self.hline(x, y, w, PANEL_HI)
        self.vline(x, y, h, PANEL_HI)
        self.hline(x, y + h - 1, w, PANEL_LO)
        self.vline(x + w - 1, y, h, PANEL_LO)
        if rivets:
            for rx, ry in ((x + 2, y + 2), (x + w - 4, y + 2), (x + 2, y + h - 4), (x + w - 4, y + h - 4)):
                self.put(rx, ry, PANEL_HI)
                self.put(rx + 1, ry, STEEL_LO)
                self.put(rx, ry + 1, STEEL_LO)
                self.put(rx + 1, ry + 1, PANEL_LO)

    def slot(self, x: int, y: int, w: int, h: int) -> None:
        self.rect(x, y, w, h, SLOT)
        self.hline(x, y, w, PANEL_LO)
        self.vline(x, y, h, PANEL_LO)
        self.hline(x, y + h - 1, w, SLOT_HI)
        self.vline(x + w - 1, y, h, SLOT_HI)


Drawer: TypeAlias = Callable[[Canvas], None]


# Width in px of a line of text; the text column is TEXT_X1 - TEXT_X0 wide, so a line must stay within it.
def text_width(s: str, scale: int = 1, spacing: int | None = None) -> int:
    spacing = scale if spacing is None else spacing
    return len(s) * (5 * scale + spacing) - spacing


def background(cv: Canvas) -> None:
    # Ordered-dither vignette: lighter toward the image field, darker toward the corners.
    cv.paint(lambda x, y: vignette(x, y, 232, 84, 200.0, 120.0))
    # Faint shelf lines, like the shop wall in the key art.
    for y in (40, 104, 168):
        for x in range(0, W, 2):
            cv.put(x, y, BG2)


# The left half shared by every mod cover: title lines at scale 2, accent rule, up to three tagline lines at 11 px steps,
# author and version on the bottom margin. The covers below draw the right half themselves.
def layout(cv: Canvas, accent: Color, title_lines: Sequence[str], tagline_lines: Sequence[str]) -> None:
    background(cv)
    y = MARGIN
    cv.text(TEXT_X0, y, "PROBABLY STOLEN MOD", MUTED)
    y += 7 + 9
    for line in title_lines:
        # A word too long for the text column closes up to 1 px spacing rather than leaving the grid.
        spacing = 2 if text_width(line, 2, 2) <= TEXT_X1 - TEXT_X0 else 1
        cv.text(TEXT_X0, y, line, CREAM, scale=2, spacing=spacing)
        y += 14 + 4
    y += 2
    cv.rect(TEXT_X0, y, 24, 2, accent)
    y += 2 + 10
    for line in tagline_lines:
        cv.text(TEXT_X0, y, line, MUTED)
        y += 11
    # Author line on the bottom margin.
    cv.text(TEXT_X0, H - MARGIN - 7, "BY KCN-JUDU", FAINT)
    cv.text(TEXT_X0 + text_width("BY KCN-JUDU") + 8, H - MARGIN - 7, cv.version, accent)


def cartridge(cv: Canvas, x: int, y: int, label_color: Color, glyph: str, glyph_color: Color) -> None:
    # A save cartridge: steel shell, label, notch.
    cv.rect(x, y, 40, 48, STEEL_LO)
    cv.rect(x + 1, y + 1, 38, 46, STEEL)
    cv.hline(x + 1, y + 1, 38, CREAM_DIM)
    cv.rect(x + 30, y, 10, 6, BG1)
    cv.rect(x + 4, y + 8, 32, 26, label_color)
    cv.rect(x + 4, y + 8, 32, 3, PANEL)
    cv.rect(x + 8, y + 38, 24, 6, STEEL_LO)
    for i in range(4):
        cv.rect(x + 10 + i * 6, y + 39, 3, 4, PANEL_LO)
    if glyph == 'WEN':
        cv.bitmap(x + 13, y + 15, WEN, glyph_color, 2)
    else:
        cv.bitmap(x + 15, y + 15, FONT[glyph], glyph_color, 2)


# Save Language Converter: two save cartridges, the original and the converted copy, with an arrow and their line items.
def cover_language(cv: Canvas) -> None:
    layout(cv, TEAL, ["SAVE", "LANGUAGE", "CONVERTER"], ["COPIES A SAVE AND", "CONVERTS ITS TEXT TO", "YOUR LANGUAGE."])
    cv.plate(IMG_X0, 24, IMG_X1 - IMG_X0, 132)
    cv.rect(IMG_X0 + 1, 25, IMG_X1 - IMG_X0 - 2, 9, PANEL_LO)
    cv.text(IMG_X0 + 6, 26, "CONVERT A COPY", TEAL)
    cartridge(cv, IMG_X0 + 12, 46, CREAM_DIM, 'WEN', PANEL_LO)
    cartridge(cv, IMG_X1 - 52, 46, CREAM, 'A', PANEL_LO)
    # Arrow carrying text lines from one save to the other.
    ax = IMG_X0 + 58
    for i, w in enumerate((10, 16, 12)):
        cv.rect(ax, 58 + i * 8, w, 2, FAINT)
        cv.rect(ax + 22, 58 + i * 8, w + 2, 2, TEAL)
    cv.rect(ax + 2, 84, 24, 2, TEAL)
    for k in range(5):
        cv.vline(ax + 26 + k, 80 + k, 10 - 2 * k, TEAL)
    # Line items under each save.
    for i, w in enumerate((30, 22, 26)):
        cv.slot(IMG_X0 + 12, 104 + i * 12, 40, 9)
        cv.rect(IMG_X0 + 15, 107 + i * 12, w - 6, 3, FAINT)
        cv.slot(IMG_X1 - 52, 104 + i * 12, 40, 9)
        cv.rect(IMG_X1 - 49, 107 + i * 12, w, 3, CREAM_DIM)
    cv.text(IMG_X0 + 62, 116, "OK", TEAL)


# Quick Call: the phone and its number pad with fast-forward chevrons, and the dialog opened straight on its choices.
def cover_call(cv: Canvas) -> None:
    layout(cv, ORANGE, ["QUICK", "CALL"], ["CALLS OPEN ON THEIR", "CHOICES: NO RINGING,", "NO GREETING LINES."])
    # Phone on the left of the image field.
    px, py = IMG_X0 + 2, 34
    cv.plate(px, py, 58, 112)
    cv.rect(px + 6, py + 6, 46, 14, PANEL_LO)
    cv.text(px + 9, py + 10, "4471", ORANGE)
    for r in range(4):
        for c in range(3):
            kx, ky = px + 7 + c * 15, py + 26 + r * 20
            cv.rect(kx, ky, 13, 16, PANEL_HI)
            cv.rect(kx, ky + 14, 13, 2, PANEL_LO)
            label = "123456789+0-"[r * 3 + c]
            cv.bitmap(kx + 4, ky + 4, FONT[label], CREAM_DIM)
    cv.rect(px + 22, py + 46, 13, 16, ORANGE)
    cv.rect(px + 22, py + 60, 13, 2, RUST)
    cv.bitmap(px + 26, py + 50, FONT['5'], PANEL_LO)
    # Fast-forward chevrons.
    fx = px + 61
    for k in range(2):
        for i in range(6):
            cv.vline(fx + k * 7 + i, 82 + i, 13 - 2 * i, ORANGE if k else RUST)
    # Dialog panel opened straight on its choices.
    dx, dy = IMG_X0 + 78, 40
    cv.plate(dx, dy, IMG_X1 - dx, 100)
    cv.rect(dx + 1, dy + 1, IMG_X1 - dx - 2, 9, PANEL_LO)
    cv.text(dx + 5, dy + 2, "WILD", ORANGE)
    rows = ["BROWSE", "ORDER", "HANG UP"]
    for i, s in enumerate(rows):
        ry = dy + 18 + i * 24
        if i == 0:
            cv.rect(dx + 6, ry, IMG_X1 - dx - 12, 17, ORANGE)
            cv.text(dx + 8, ry + 5, ">", PANEL_LO)
            cv.text(dx + 15, ry + 5, s, PANEL_LO)
        else:
            cv.slot(dx + 6, ry, IMG_X1 - dx - 12, 17)
            cv.text(dx + 15, ry + 5, s, CREAM_DIM)


OutlineStyle: TypeAlias = Literal['solid', 'tape', 'double', 'brackets']
ItemKind: TypeAlias = Literal['bottle', 'pistol', 'box', 'pills', 'gem', 'can']


def outline(cv: Canvas, x: int, y: int, w: int, h: int, style: OutlineStyle, color: Color) -> None:
    if style == 'solid':
        cv.frame(x, y, w, h, color)
    elif style == 'tape':
        for i in range(w):
            c = color if ((x + i + y) // 3) % 2 == 0 else RUST
            cv.put(x + i, y, c)
            cv.put(x + i, y + h - 1, c)
        for j in range(h):
            c = color if ((x + y + j) // 3) % 2 == 0 else RUST
            cv.put(x, y + j, c)
            cv.put(x + w - 1, y + j, c)
    elif style == 'double':
        cv.frame(x, y, w, h, color)
        cv.frame(x + 1, y + 1, w - 2, h - 2, color)
        cv.frame(x + 4, y + 4, w - 8, h - 8, color)
    elif style == 'brackets':
        arm = 5
        for (cx, cy, sx, sy) in ((x, y, 1, 1), (x + w - 1, y, -1, 1), (x, y + h - 1, 1, -1), (x + w - 1, y + h - 1, -1, -1)):
            for i in range(arm):
                cv.put(cx + sx * i, cy, color)
                cv.put(cx, cy + sy * i, color)


# Item silhouettes for the demand grid, drawn inside their cell with a margin.
def item(cv: Canvas, kind: ItemKind, x: int, y: int, w: int, h: int) -> None:
    # Simple item silhouettes inside their cells.
    if kind == 'bottle':
        cv.rect(x + w // 2 - 2, y + 3, 4, 4, CREAM_DIM)
        cv.rect(x + w // 2 - 4, y + 7, 8, h - 10, TEAL)
        cv.rect(x + w // 2 - 3, y + 9, 2, h - 14, CREAM)
    elif kind == 'pistol':
        cv.rect(x + 3, y + 4, w - 6, 4, STEEL)
        cv.rect(x + 3, y + 8, 5, h - 11, STEEL_LO)
        cv.rect(x + w - 6, y + 3, 2, 2, STEEL_LO)
    elif kind == 'box':
        cv.rect(x + 3, y + 3, w - 6, h - 6, RUST)
        cv.hline(x + 3, y + 3, w - 6, ORANGE)
        cv.rect(x + w // 2 - 1, y + 3, 2, h - 6, CREAM_DIM)
    elif kind == 'pills':
        cv.rect(x + 4, y + 4, w - 8, h - 8, CREAM)
        cv.rect(x + 4, y + 4, w - 8, 3, RED)
    elif kind == 'gem':
        cx = x + w // 2
        for i in range(5):
            cv.hline(cx - i, y + 4 + i, 2 * i + 1, CYAN)
        for i in range(5):
            cv.hline(cx - 4 + i, y + 9 + i, 9 - 2 * i, TEAL)
    elif kind == 'can':
        cv.rect(x + 4, y + 3, w - 8, h - 6, AMBER)
        cv.hline(x + 4, y + 3, w - 8, CREAM)
        cv.rect(x + 4, y + h // 2 - 1, w - 8, 3, RUST)


class Placed(NamedTuple):
    # An item in the demand grid: its cell, its size in cells, and the outline that marks it.
    kind: ItemKind
    col: int
    row: int
    w: int
    h: int
    style: OutlineStyle | None
    color: Color | None


# Demand Highlight: an inventory grid with outlined items and the Item Filter window over its corner.
def cover_demand(cv: Canvas) -> None:
    layout(cv, GREEN, ["DEMAND", "HIGHLIGHT"], ["OUTLINES ITEMS THE", "CUSTOMER WANTS.", "ITEM FILTER BY TYPE."])
    gx, gy, cell = IMG_X0 + 4, 30, 18
    cols, rows = 7, 6
    cv.plate(gx - 4, gy - 6, cols * cell + 8, rows * cell + 12)
    for r in range(rows):
        for c in range(cols):
            cv.slot(gx + c * cell, gy + r * cell, cell, cell)
    # Items and their outline styles (DESIGN.md, Illustrations).
    placed = (
        Placed('bottle', 0, 0, 1, 2, 'solid', GREEN),
        Placed('pills', 1, 0, 1, 1, 'solid', GREEN),
        Placed('pistol', 2, 1, 2, 1, 'double', RED),
        Placed('can', 1, 1, 1, 1, 'tape', AMBER),
        Placed('box', 0, 3, 2, 2, 'brackets', GREEN),
        Placed('gem', 4, 0, 1, 1, 'tape', AMBER),
        Placed('can', 2, 4, 1, 1, None, None),
        Placed('box', 3, 3, 1, 1, None, None),
    )
    for p in placed:
        x, y = gx + p.col * cell, gy + p.row * cell
        item(cv, p.kind, x + 1, y + 1, p.w * cell - 2, p.h * cell - 2)
        if p.style is not None and p.color is not None:
            outline(cv, x + 1, y + 1, p.w * cell - 2, p.h * cell - 2, p.style, p.color)
    # The Item Filter window, overlapping the grid's corner.
    fx, fy, fw, fh = IMG_X1 - 72, 92, 70, 66
    cv.rect(fx + 2, fy + 2, fw, fh, PANEL_LO)
    cv.plate(fx, fy, fw, fh, rivets=False)
    cv.rect(fx + 1, fy + 1, fw - 2, 9, PANEL_LO)
    cv.text(fx + 4, fy + 2, "FILTER", CYAN)
    for i, (label, on, col) in enumerate((("FOOD", True, CYAN), ("TOOL", False, CYAN), ("STOLEN", True, AMBER), ("ILLEGAL", False, RED))):
        by = fy + 14 + i * 12
        cv.frame(fx + 5, by, 7, 7, MUTED)
        if on:
            cv.rect(fx + 7, by + 2, 3, 3, col)
        cv.text(fx + 15, by, label, CREAM_DIM if on else FAINT)


# Performance Fixes: a frame-time chart, spiky before and flat after, against a 60 fps guide line.
def cover_performance(cv: Canvas) -> None:
    layout(cv, CYAN, ["PERFORMANCE", "FIXES"], ["SAVES LOAD FASTER.", "FULL CONTAINERS OPEN", "WITHOUT STUTTERING."])
    px, py, pw, ph = IMG_X0, 24, IMG_X1 - IMG_X0, 132
    cv.plate(px, py, pw, ph)
    cv.rect(px + 1, py + 1, pw - 2, 9, PANEL_LO)
    cv.text(px + 6, py + 2, "FRAME TIME", CYAN)
    # A frame-time chart: spiky before, flat after, with a 60 fps guide line.
    gx0, gx1, base = px + 10, px + pw - 10, py + ph - 22
    guide = base - 30
    for x in range(gx0, gx1, 3):
        cv.put(x, guide, FAINT)
    cv.text(gx1 - text_width("60FPS"), guide - 9, "60FPS", FAINT)
    before = [8, 10, 9, 52, 12, 9, 70, 11, 10, 46, 9, 12]
    after = [8, 9, 8, 10, 9, 8, 11, 9, 8, 10, 9, 8]
    mid = (gx0 + gx1) // 2
    cv.vline(mid, py + 16, base - py - 14, PANEL_HI)
    for i, h in enumerate(before):
        x = gx0 + 2 + i * 5
        cv.rect(x, base - h, 3, h, RED if h > 30 else STEEL)
    for i, h in enumerate(after):
        x = mid + 4 + i * 5
        cv.rect(x, base - h, 3, h, CYAN)
    cv.hline(gx0, base, gx1 - gx0, MUTED)
    cv.text(gx0 + 2, base + 6, "BEFORE", FAINT)
    cv.text(mid + 4, base + 6, "AFTER", CYAN)


def mini_window(cv: Canvas, x: int, y: int, w: int, h: int, title_color: Color, rows: int) -> None:
    # A container window: plate, title bar, a few item slots.
    cv.plate(x, y, w, h, rivets=False)
    cv.rect(x + 1, y + 1, w - 2, 6, title_color)
    for r in range(rows):
        for c in range((w - 6) // 9):
            cv.slot(x + 3 + c * 9, y + 10 + r * 9, 8, 8)


# Window Workspaces: workspace chips 1-4 above windows snapped edge to edge on a grid.
def cover_workspaces(cv: Canvas) -> None:
    layout(cv, LILAC, ["WINDOW", "WORKSPACES"], ["WINDOWS SNAP TO EDGES", "ONE KEY SWITCHES", "SETS OF WINDOWS."])
    px, py, pw, ph = IMG_X0, 24, IMG_X1 - IMG_X0, 132
    cv.plate(px, py, pw, ph)
    cv.rect(px + 1, py + 1, pw - 2, 9, PANEL_LO)
    cv.text(px + 6, py + 2, "WORKSPACE", LILAC)
    # Workspace chips 1-4, the second one current.
    for i in range(4):
        cx = px + pw - 46 + i * 10
        if i == 1:
            cv.rect(cx, py + 1, 9, 9, LILAC)
            cv.bitmap(cx + 2, py + 2, FONT[str(i + 1)], PANEL_LO)
        else:
            cv.bitmap(cx + 2, py + 2, FONT[str(i + 1)], FAINT)
    # The desk under the windows, with the faint snapping grid.
    gx0, gy0, gx1, gy1 = px + 4, py + 13, px + pw - 4, py + ph - 4
    cv.rect(gx0, gy0, gx1 - gx0, gy1 - gy0, BG1)
    for x in range(gx0, gx1, 8):
        for y in range(gy0, gy1):
            if (y - gy0) % 2 == 0: cv.put(x, y, PANEL)
    for y in range(gy0, gy1, 8):
        for x in range(gx0, gx1):
            if (x - gx0) % 2 == 0: cv.put(x, y, PANEL)
    # Three windows snapped edge to edge; the last one still settling onto the guide.
    mini_window(cv, gx0 + 4, gy0 + 4, 60, 46, LILAC, 4)
    mini_window(cv, gx0 + 64, gy0 + 4, 64, 30, LILAC_DIM, 2)
    mini_window(cv, gx0 + 64, gy0 + 34, 64, 34, LILAC_DIM, 2)
    mini_window(cv, gx0 + 4, gy0 + 60, 42, 38, LILAC_DIM, 3)
    # Snap guides on the shared edges.
    for y in range(gy0 + 1, gy1 - 1):
        if (y // 2) % 2 == 0: cv.put(gx0 + 64, y, LILAC)
    for x in range(gx0 + 60, gx1 - 1):
        if (x // 2) % 2 == 0: cv.put(x, gy0 + 34, LILAC)
    # Drag arrow: the loose window heading right, onto the guide.
    ax, ay = gx0 + 49, gy0 + 78
    cv.rect(ax, ay, 9, 2, CREAM_DIM)
    for k in range(4):
        cv.vline(ax + 9 + k, ay - 3 + k, 8 - 2 * k, CREAM_DIM)


def keycap(cv: Canvas, x: int, y: int, w: int, label: str, lit: bool) -> None:
    # A key: raised top, darker front lip, label centred on the top.
    top, lip, ink = (AMBER, RUST, PANEL_LO) if lit else (PANEL_HI, PANEL_LO, CREAM_DIM)
    cv.rect(x, y, w, 18, lip)
    cv.rect(x, y, w, 15, top)
    cv.hline(x + 1, y + 1, w - 2, CREAM if lit else MUTED)
    cv.text(x + (w - text_width(label)) // 2, y + 5, label, ink)


def mouse(cv: Canvas, x: int, y: int) -> None:
    # A mouse seen from above, with the middle button and the two side buttons lit.
    w, h = 29, 46
    cv.vline(x + w // 2, y - 8, 8, MUTED)
    # Rounded by stepping the outline in: tighter at the top, wider at the palm.
    insets = [6, 4, 3, 2, 1, 1] + [0] * (h - 14) + [1, 1, 2, 3, 4, 6, 8, 10]
    for j, inset in enumerate(insets):
        cv.hline(x + inset, y + j, w - 2 * inset, STEEL_LO)
        if 0 < j < h - 1:
            cv.hline(x + inset + 1, y + j, w - 2 * inset - 2, STEEL)
    cv.hline(x + 6, y + 1, w - 12, CREAM_DIM)
    cv.hline(x + 1, y + 19, w - 2, STEEL_LO)
    cv.vline(x + w // 2, y + 1, 18, STEEL_LO)
    cv.rect(x + w // 2 - 2, y + 5, 5, 9, AMBER)
    cv.vline(x + w // 2, y + 6, 7, RUST)
    cv.rect(x - 2, y + 23, 3, 6, AMBER)
    cv.rect(x - 2, y + 31, 3, 6, AMBER)


# Better Key Bindings: a key combination and the mouse buttons it may use.
def cover_keys(cv: Canvas) -> None:
    layout(cv, AMBER, ["BETTER", "KEY", "BINDINGS"], ["BIND CTRL+E, MOUSE", "4, 5, MIDDLE BUTTON", "AND THE WHEEL."])
    px, py, pw, ph = IMG_X0, 24, IMG_X1 - IMG_X0, 132
    cv.plate(px, py, pw, ph)
    cv.rect(px + 1, py + 1, pw - 2, 9, PANEL_LO)
    cv.text(px + 6, py + 2, "KEY BINDINGS", AMBER)
    # The combination being bound, and the mouse buttons it may use.
    keycap(cv, px + 10, py + 22, 34, "CTRL", True)
    cv.bitmap(px + 49, py + 27, FONT['+'], AMBER)
    keycap(cv, px + 60, py + 22, 20, "E", True)
    mouse(cv, px + pw - 44, py + 16)
    # Two bindings on the same key stay apart: the combination and the key alone.
    rows = [("ROTATE", "CTRL+E", True), ("SORT", "E", False), ("BELL", "MOUSE 4", True)]
    for i, (name, key, lit) in enumerate(rows):
        ry = py + 70 + i * 19
        cv.slot(px + 8, ry, pw - 16, 15)
        cv.text(px + 13, ry + 4, name, CREAM_DIM)
        cv.text(px + pw - 13 - text_width(key), ry + 4, key, AMBER if lit else MUTED)


# A braced crate, 16 x 16: o outline, l lit edge, w body, d shade.
CRATE: Final[Bitmap] = (
    "oooooooooooooooo",
    "ollllllllllllllo",
    "olwwwwwwwwwwwwdo",
    "olwdwwwwwwwwwddo",
    "olwwdwwwwwwwdwdo",
    "olwwwdwwwwwdwwdo",
    "olwwwwdwwwdwwwdo",
    "olwwwwwdwdwwwwdo",
    "olwwwwwwdwwwwwdo",
    "olwwwwwdwdwwwwdo",
    "olwwwwdwwwdwwwdo",
    "olwwwdwwwwwdwwdo",
    "olwwdwwwwwwwdwdo",
    "olwdwwwwwwwwwddo",
    "oddddddddddddddo",
    "oooooooooooooooo",
)


# Draws a character-keyed bitmap; keys missing from the palette are left transparent.
def pixmap(cv: Canvas, x: int, y: int, rows: Bitmap, palette: Mapping[str, Color], scale: int = 1) -> None:
    for j, row in enumerate(rows):
        for i, key in enumerate(row):
            if key in palette:
                cv.rect(x + i * scale, y + j * scale, scale, scale, palette[key])


def triangle(cv: Canvas, x: int, y: int, up: bool, c: Color) -> None:
    # A 5 x 3 arrowhead for the move buttons.
    for k, w in enumerate((1, 3, 5) if up else (5, 3, 1)):
        cv.hline(x + (5 - w) // 2, y + k, w, c)


# Texture Packs: the same crate before and after a pack, and the manager listing packs in priority order.
def cover_packs(cv: Canvas) -> None:
    layout(cv, PINK, ["TEXTURE", "PACKS"], ["RESOURCE PACKS THAT", "REPLACE THE GAME'S", "PICTURES, IN ORDER."])
    px, py, pw, ph = IMG_X0, 24, IMG_X1 - IMG_X0, 132
    cv.plate(px, py, pw, ph)
    cv.rect(px + 1, py + 1, pw - 2, 9, PANEL_LO)
    cv.text(px + 6, py + 2, "PACK ORDER", PINK)
    # The same item before and after: the game's crate, then the pack's.
    before = {'o': PANEL_LO, 'l': CREAM_DIM, 'w': RUST, 'd': WOOD_LO}
    after = {'o': PANEL_LO, 'l': PINK_HI, 'w': PINK, 'd': PINK_LO}
    for sx, pal in ((px + 14, before), (px + pw - 50, after)):
        cv.slot(sx, py + 18, 36, 36)
        pixmap(cv, sx + 2, py + 20, CRATE, pal, 2)
    ax, ay = px + 58, py + 35
    cv.rect(ax, ay, 22, 2, CREAM_DIM)
    for k in range(4):
        cv.vline(ax + 22 + k, ay - 3 + k, 8 - 2 * k, CREAM_DIM)
    # The manager: packs in priority order, each switched on or off, with buttons to move it.
    rows = [("HD ITEMS", True), ("DARK SHOP", True), ("OLD UI", False)]
    for i, (name, on) in enumerate(rows):
        ry = py + 70 + i * 19
        cv.slot(px + 8, ry, pw - 16, 15)
        cv.frame(px + 13, ry + 4, 7, 7, MUTED if on else FAINT)
        if on:
            cv.rect(px + 15, ry + 6, 3, 3, PINK)
        cv.text(px + 25, ry + 4, name, CREAM_DIM if on else FAINT)
        arrows = MUTED if on else FAINT
        triangle(cv, px + pw - 27, ry + 6, True, FAINT if i == 0 else arrows)
        triangle(cv, px + pw - 18, ry + 6, False, FAINT if i == len(rows) - 1 else arrows)


COVERS: Final[Mapping[str, Drawer]] = MappingProxyType({
    "save_language_converter": cover_language,
    "quick_call": cover_call,
    "demand_highlight": cover_demand,
    "performance_fixes": cover_performance,
    "window_workspaces": cover_workspaces,
    "better_key_bindings": cover_keys,
    "texture_packs": cover_packs,
})

# Mods still being made, not yet listed in config/repos.json (which publishes them on the site): their cover is
# drawn only from a working copy (--checkouts), and skipped otherwise.
UNLISTED: Final[Mapping[str, str]] = MappingProxyType({"texture-packs": "ProbablyStolen-TexturePacks"})


def mod_folders(checkouts: str | None) -> Mapping[str, str]:
    # Each cover's mod folder: mods/<slug> in this repository, or with --checkouts the working copy
    # <checkouts>/<repository>/<repository without its ProbablyStolen- prefix>.
    root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    repos_path = os.path.join(root, "config", "repos.json")
    repos = str_map(member(as_dict(load_json(repos_path), repos_path), "repos", repos_path), "repos")

    def folder(name: str) -> str:
        slug = name.replace("_", "-")
        repo = repos.get(slug) or UNLISTED.get(slug)
        if checkouts and repo:
            return os.path.join(checkouts, repo, repo.replace("ProbablyStolen-", "", 1))
        return os.path.join(root, "mods", slug)

    return {name: folder(name) for name in COVERS}


def read_bytes(path: str) -> bytes:
    with open(path, "rb") as f:
        return f.read()


def sync(rendered: str, folder: str) -> None:
    # The cover is the mod's preview.png and its documentation cover; only files that differ are written.
    want = read_bytes(rendered)
    for target in ("preview.png", os.path.join("doc", "attachments", "cover.png")):
        path = os.path.join(folder, target)
        if os.path.isfile(path) and read_bytes(path) != want:
            shutil.copyfile(rendered, path)
            print("   updated", path)


def render(draw: Drawer, version: str) -> Canvas:
    cv = Canvas()
    cv.version = version_label(version)
    draw(cv)
    return cv


def to_png(cv: Canvas) -> Image.Image:
    """The cover as published: scaled by whole pixels, on a 64-colour palette."""
    big = cv.img.resize((W * SCALE, H * SCALE), Image.Resampling.NEAREST)
    return big.convert("P", palette=Image.Palette.ADAPTIVE, colors=64)


@dataclass(frozen=True)
class Options:
    out: str
    checkouts: str | None
    sync: bool
    only: frozenset[str] | None
    help: bool


def parse_options(argv: Sequence[str]) -> Options:
    help_asked = "-h" in argv or "--help" in argv
    only_arg, rest = take_option(argv, "--only")
    only = split_ids(only_arg)
    if only is not None and only - COVERS.keys():
        raise SystemExit("unknown cover id(s): " + ", ".join(sorted(only - COVERS.keys())))
    do_sync, rest = take_flag(rest, "--sync")
    checkouts, rest = take_option(rest, "--checkouts")
    return Options(rest[0] if rest else "out", checkouts, do_sync, only, help_asked)


def main(argv: Sequence[str]) -> None:
    """python design/covers.py [out] [--checkouts DIR] [--sync] [--only ID[,ID...]]

    Each cover shows its mod's version, read from the mod's manifest.xml. --checkouts reads the manifests from
    working copies in DIR instead of the submodules, so a version not yet published gets its cover too. --sync
    writes each cover into the mod's preview.png and doc/attachments/cover.png; with --only, only into the mods
    named (by id, such as performance_fixes), so releasing one mod leaves the others' working copies alone."""
    if "-h" in argv or "--help" in argv:
        print(main.__doc__)
        return
    opts = parse_options(argv)
    os.makedirs(opts.out, exist_ok=True)
    folders = mod_folders(opts.checkouts)
    for name, draw in COVERS.items():
        version = read_version(folders[name])
        if version is None and name.replace("_", "-") in UNLISTED:
            print(name, "skipped: not in the collection yet, give --checkouts to draw it")
            continue
        if version is None:
            raise SystemExit(f"{name}: no manifest.xml with a ModVersion in {folders[name]}")
        cv = render(draw, version)
        rendered = os.path.join(opts.out, name + ".png")
        to_png(cv).save(rendered, optimize=True)
        cv.img.resize((W, H), Image.Resampling.NEAREST).save(os.path.join(opts.out, name + "_thumb.png"))
        print(name, cv.version, os.path.getsize(rendered), "bytes")
        if opts.sync and (opts.only is None or name in opts.only):
            sync(rendered, folders[name])


if __name__ == "__main__":
    main(sys.argv[1:])
