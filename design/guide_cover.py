"""Renders the square covers of the Steam guides (workshop/guide-*.txt), in the mod cover style.

    python design/guide_cover.py design/out

A 180x180 logical canvas scaled x4 to 720x720. Same palette, panels, dither and 5x7 capitals as
covers.py; the Chinese cover sets its lettering in SimSun's 12 px bitmap strike, which is pixel
art in its own right, so both covers stay crisp at whole-pixel scales.
"""
import os
import sys
from collections.abc import Sequence
from functools import cache
from typing import Final, Literal, TypeAlias

from PIL import Image, ImageDraw, ImageFont
from PIL.ImageFont import FreeTypeFont

import covers as C

S: Final = 180
M: Final = 16
CJK_FONT: Final = 'C:/Windows/Fonts/simsun.ttc'

IconKind: TypeAlias = Literal['performance', 'demand', 'call', 'language']
Lang: TypeAlias = Literal['en', 'zh']

# The four mods in guide order, each in its cover accent.
MODS: Final[Sequence[tuple[IconKind, C.Color, str, str]]] = (
    ('performance', C.CYAN, "STUTTERS", "卡顿"),
    ('demand', C.GREEN, "DEMAND", "需求"),
    ('call', C.ORANGE, "CALLS", "电话"),
    ('language', C.TEAL, "LANGUAGE", "存档语言"),
)


# Opened once: loading the .ttc per call would dominate the render. SimSun has bitmap strikes at 12 px, which is why that size.
@cache
def cjk_font() -> FreeTypeFont:
    return ImageFont.truetype(CJK_FONT, 12)


# The cover background on the guide's square canvas: same vignette and shelf lines as covers.background, centred differently.
def background(cv: C.Canvas) -> None:
    cv.paint(lambda x, y: C.vignette(x, y, 120, 110, 150.0, 130.0))
    for y in (40, 104, 168):
        for x in range(0, S, 2):
            cv.put(x, y, C.BG2)


def cjk(cv: C.Canvas, x: int, y: int, s: str, color: C.Color, scale: int = 1) -> int:
    # SimSun's embedded 12 px bitmaps, drawn without anti-aliasing and scaled by whole pixels.
    font = cjk_font()
    w = int(font.getlength(s)) + 2
    mask = Image.new('L', (w, 14), 0)
    d = ImageDraw.Draw(mask)
    d.fontmode = '1'
    d.text((0, 0), s, font=font, fill=255)
    px = mask.load()
    if px is None:
        raise RuntimeError("the mask has no pixel access")
    for j in range(14):
        for i in range(w):
            if px[i, j]:
                cv.rect(x + i * scale, y + j * scale, scale, scale, color)
    return w * scale


# Advance width of a Chinese string at the given scale, for centring.
def cjk_width(s: str, scale: int = 1) -> int:
    return int(cjk_font().getlength(s)) * scale


# The small picture of each mod above its tile label: performance bars, demand outline, phone with chevrons, WEN to A/Z.
def icon(cv: C.Canvas, kind: IconKind, x: int, y: int, accent: C.Color) -> None:
    # Each icon fits a 30x16 box whose top-left is (x, y).
    if kind == 'performance':
        for i in range(7):
            cv.rect(x + 1 + i * 4, y + 11 - (i % 2), 3, 4 + (i % 2), accent)
        cv.hline(x, y + 15, 30, C.MUTED)
        for k in range(0, 30, 3):
            cv.put(x + k, y + 4, C.FAINT)
    elif kind == 'demand':
        cv.slot(x + 1, y, 16, 16)
        C.item(cv, 'box', x + 2, y + 1, 14, 14)
        C.outline(cv, x + 2, y + 1, 14, 14, 'solid', accent)
        cv.slot(x + 17, y + 3, 12, 12)
        C.item(cv, 'can', x + 17, y + 3, 12, 12)
    elif kind == 'call':
        cv.rect(x + 2, y + 2, 10, 12, C.PANEL_HI)
        cv.rect(x + 3, y + 3, 8, 3, C.PANEL_LO)
        for r in range(2):
            for c in range(3):
                cv.rect(x + 3 + c * 3, y + 7 + r * 3, 2, 2, C.CREAM_DIM)
        for k in range(2):
            for i in range(5):
                cv.vline(x + 15 + k * 6 + i, y + 3 + i, 11 - 2 * i, accent if k else C.RUST)
    elif kind == 'language':
        cv.bitmap(x + 1, y + 1, C.WEN, C.CREAM_DIM, 2)
        cv.rect(x + 16, y + 7, 4, 2, accent)
        for k in range(3):
            cv.vline(x + 20 + k, y + 5 + k, 6 - 2 * k, accent)
        cv.bitmap(x + 24, y + 1, C.FONT['A'], accent, 1)
        cv.bitmap(x + 24, y + 9, C.FONT['Z'], accent, 1)


# English letters use the shared 5x7 capitals; Chinese uses cjk(). Both versions have the same layout: heading, accent rule
# in the four mod colours, four tiles, author line.
def draw(lang: Lang) -> C.Canvas:
    cv = C.Canvas(S, S)
    background(cv)
    if lang == 'en':
        cv.text(M, M, "PROBABLY STOLEN MODS", C.MUTED)
        cv.text(M, 32, "FOUR SMALL", C.CREAM, scale=2, spacing=2)
        cv.text(M, 50, "MODS", C.CREAM, scale=2, spacing=2)
        tag = "GUIDE"
    else:
        cjk(cv, M, M - 2, "深空当铺 体验优化模组", C.MUTED)
        cjk(cv, M, 36, "四个小模组", C.CREAM, scale=2)
        tag = "GUIDE"
    # Accent rule in the four mod colours: the series in one stroke.
    for i, (_, accent, _, _) in enumerate(MODS):
        cv.rect(M + i * 8, 68, 8, 2, accent)
    # Four tiles, one per mod, in guide order.
    tw, th, gap = 70, 36, 8
    for i, (kind, accent, en, zh) in enumerate(MODS):
        x = M + (i % 2) * (tw + gap)
        y = 74 + (i // 2) * (th + 4)
        cv.plate(x, y, tw, th, rivets=False)
        cv.rect(x + 1, y + 1, 2, th - 2, accent)
        icon(cv, kind, x + (tw - 30) // 2, y + 4, accent)
        if lang == 'en':
            cv.text(x + (tw - C.text_width(en)) // 2, y + 24, en, C.CREAM_DIM)
        else:
            cjk(cv, x + (tw - cjk_width(zh)) // 2, y + 20, zh, C.CREAM_DIM)
    # Author line on the bottom margin.
    by = S - M - 7
    cv.text(M, by, tag, C.TEAL)
    cv.text(M + C.text_width(tag) + 6, by, "BY KCN-JUDU", C.FAINT)
    return cv


def main(out: str) -> None:
    os.makedirs(out, exist_ok=True)
    langs: tuple[Lang, ...] = ('en', 'zh')
    for lang in langs:
        cv = draw(lang)
        big = cv.img.resize((S * 4, S * 4), Image.Resampling.NEAREST).convert("P", palette=Image.Palette.ADAPTIVE, colors=64)
        path = os.path.join(out, f"guide-cover-{lang}.png")
        big.save(path, optimize=True)
        print(path, os.path.getsize(path), "bytes")


if __name__ == "__main__":
    main(sys.argv[1] if len(sys.argv) > 1 else "out")
