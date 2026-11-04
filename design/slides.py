"""Renders the title slides inserted into videos, from slides.json, in the mod cover style (DESIGN.md, Video slides).

    python design/slides.py design/out/slides                    # every slide, English and Chinese, 1080p
    python design/slides.py design/out/slides performance_fixes_stutter --height 2160

Each slide is one statement, centred: the mod's name in its accent, a two-line headline whose last line takes
the accent, and one muted line under it. English is set in the cover alphabet, Chinese in Cubic 11
(fonts/Cubic_11.ttf, OFL). Both are drawn on the 320x180 cover canvas and scaled with nearest-neighbour.
"""
import os
import sys
from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from functools import cache
from types import MappingProxyType
from typing import Final, Literal, TypeAlias, get_args

from PIL import Image, ImageDraw, ImageFont

import covers as C
from compare_labels import MODS
from typed import as_dict, as_list, as_str, load_json, member, take_option

Lang: TypeAlias = Literal["en", "zh"]
LANGS: Final[tuple[Lang, ...]] = get_args(Lang)

HERE: Final = os.path.dirname(os.path.abspath(__file__))
# Cubic 11 sits on a 100-unit pixel grid with a 1200-unit em: at 12 px each of its pixels is one canvas pixel.
CUBIC: Final = ImageFont.truetype(os.path.join(HERE, "fonts", "Cubic_11.ttf"), 12)
CUBIC_ASCENT: Final = 9     # CJK glyphs reach 9 px above the baseline and 2 below: an 11 px line


@dataclass(frozen=True)
class TypeSpec:
    """Headline and sub scale, line height of one line at x1, and leading between headline lines."""
    headline: int
    sub: int
    height: int
    leading: int


TYPE: Final[Mapping[Lang, TypeSpec]] = MappingProxyType({
    "en": TypeSpec(headline=4, sub=1, height=7, leading=8),
    "zh": TypeSpec(headline=3, sub=1, height=11, leading=6),
})


@dataclass(frozen=True)
class SlideText:
    headline: Sequence[str]
    sub: str


@dataclass(frozen=True)
class Slide:
    id: str
    mod: str
    text: Mapping[Lang, SlideText]


# A slide has the same text in every language in LANGS; a missing key stops the render rather than leaving a gap.
def parse_slide(raw: object) -> Slide:
    slide = as_dict(raw, "slides.json slide")
    sid = as_str(member(slide, "id", "slides.json slide"), "id")

    def text(lang: Lang) -> SlideText:
        t = as_dict(member(slide, lang, sid), f"{sid}.{lang}")
        return SlideText(
            tuple(as_str(line, f"{sid}.{lang}.headline") for line in as_list(member(t, "headline", sid), "headline")),
            as_str(member(t, "sub", sid), f"{sid}.{lang}.sub"))

    return Slide(sid, as_str(member(slide, "mod", sid), f"{sid}.mod"), {lang: text(lang) for lang in LANGS})


def load_slides(path: str) -> Sequence[Slide]:
    return tuple(parse_slide(s) for s in as_list(member(as_dict(load_json(path), path), "slides", path), "slides"))


# The 1-bit mask of a Chinese string in Cubic 11 (no anti-aliasing), cropped to its ink on the right so centring is exact.
@cache
def cubic_mask(s: str) -> Image.Image:
    w = int(CUBIC.getlength(s)) + 1
    mask = Image.new("1", (w, 11), 0)
    d = ImageDraw.Draw(mask)
    d.fontmode = "1"
    d.text((0, CUBIC_ASCENT), s, font=CUBIC, fill=1, anchor="ls")
    box = mask.getbbox()
    return mask.crop((0, 0, box[2] if box else 1, 11))


# Width of a string in px at the given scale: the 5x7 alphabet for English, Cubic 11 for Chinese.
def width(lang: Lang, s: str, scale: int) -> int:
    if lang == "en":
        return C.text_width(s, scale, scale)
    return cubic_mask(s).width * scale


# Draws at integer scale; Chinese goes through the mask so its pixels stay square like the cover alphabet's.
def draw_text(cv: C.Canvas, lang: Lang, x: int, y: int, s: str, color: C.Color, scale: int) -> None:
    if lang == "en":
        cv.text(x, y, s, color, scale=scale, spacing=scale)
        return
    mask = cubic_mask(s)
    px = mask.load()
    if px is None:
        raise RuntimeError("the mask has no pixel access")
    for j in range(mask.height):
        for i in range(mask.width):
            if px[i, j]:
                cv.rect(x + i * scale, y + j * scale, scale, scale, color)


def background(cv: C.Canvas) -> None:
    # Ordered-dither vignette centred on the statement, darker toward the corners.
    cv.paint(lambda x, y: C.vignette(x, y, C.W / 2, C.H / 2, 190.0, 110.0))


# Refuses a line wider than the slide's text area instead of clipping it; shorten the wording in slides.json.
def centred(cv: C.Canvas, lang: Lang, y: int, s: str, color: C.Color, scale: int) -> None:
    w = width(lang, s, scale)
    if w > C.W - 2 * C.MARGIN:
        raise SystemExit(f"'{s}' is {w} px wide; the slide takes {C.W - 2 * C.MARGIN}")
    draw_text(cv, lang, (C.W - w) // 2, y, s, color, scale)


def draw(cv: C.Canvas, slide: Slide, lang: Lang) -> None:
    name, accent = MODS[slide.mod]
    text, t = slide.text[lang], TYPE[lang]
    lines = text.headline
    line_h = t.height * t.headline
    head_h = len(lines) * line_h + (len(lines) - 1) * t.leading
    sub_h = t.height * t.sub
    # Kicker, one module, headline, two modules, sub: centred as one block on the optical centre, 4 px above.
    block = 7 + 8 + head_h + 16 + sub_h
    y = (C.H - block) // 2 - 4
    background(cv)
    centred(cv, "en", y, name, accent, 1)
    y += 7 + 8
    for i, line in enumerate(lines):
        centred(cv, lang, y, line, accent if i == len(lines) - 1 else C.CREAM, t.headline)
        y += line_h + t.leading
    y += 16 - t.leading
    centred(cv, lang, y, text.sub, C.MUTED, t.sub)


@dataclass(frozen=True)
class Options:
    out: str
    wanted: Sequence[str]
    height: int


def parse_options(argv: Sequence[str]) -> Options:
    height_arg, rest = take_option(argv, "--height")
    return Options(rest[0] if rest else "out/slides", rest[1:], 1080 if height_arg is None else int(height_arg))


def main(argv: Sequence[str]) -> None:
    """python design/slides.py [out] [slide id ...] [--height PX]"""
    opts = parse_options(argv)
    slides = load_slides(os.path.join(HERE, "slides.json"))
    unknown = set(opts.wanted) - {s.id for s in slides}
    if unknown:
        raise SystemExit(f"not in slides.json: {', '.join(sorted(unknown))}")
    os.makedirs(opts.out, exist_ok=True)
    s = opts.height // C.H
    for slide in slides:
        if opts.wanted and slide.id not in opts.wanted:
            continue
        for lang in LANGS:
            cv = C.Canvas()
            draw(cv, slide, lang)
            img = cv.img.resize((C.W * s, C.H * s), Image.Resampling.NEAREST)
            path = os.path.join(opts.out, "%s_%s_%dp.png" % (slide.id, lang, opts.height))
            img.save(path, optimize=True)
            print(path, "%dx%d" % img.size)


if __name__ == "__main__":
    main(sys.argv[1:])
