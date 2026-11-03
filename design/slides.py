"""Renders the title slides inserted into videos, from slides.json, in the mod cover style (DESIGN.md, Video slides).

    python design/slides.py design/out/slides                    # every slide, English and Chinese, 1080p
    python design/slides.py design/out/slides performance_fixes_stutter --height 2160

Each slide is one statement, centred: the mod's name in its accent, a two-line headline whose last line takes
the accent, and one muted line under it. English is set in the cover alphabet, Chinese in Cubic 11
(fonts/Cubic_11.ttf, OFL). Both are drawn on the 320x180 cover canvas and scaled with nearest-neighbour.
"""
import json
import os
import sys
from PIL import Image, ImageDraw, ImageFont

import covers as C
from compare_labels import MODS

HERE = os.path.dirname(os.path.abspath(__file__))
# Cubic 11 sits on a 100-unit pixel grid with a 1200-unit em: at 12 px each of its pixels is one canvas pixel.
CUBIC = ImageFont.truetype(os.path.join(HERE, "fonts", "Cubic_11.ttf"), 12)
CUBIC_ASCENT = 9            # CJK glyphs reach 9 px above the baseline and 2 below: an 11 px line

# Type per language: headline and sub scale, line height of one line at x1, and leading between headline lines.
TYPE = {
    "en": {"headline": 4, "sub": 1, "height": 7, "leading": 8},
    "zh": {"headline": 3, "sub": 1, "height": 11, "leading": 6},
}


def cubic_mask(s):
    w = int(CUBIC.getlength(s)) + 1
    mask = Image.new("1", (w, 11), 0)
    d = ImageDraw.Draw(mask)
    d.fontmode = "1"
    d.text((0, CUBIC_ASCENT), s, font=CUBIC, fill=1, anchor="ls")
    box = mask.getbbox()
    return mask.crop((0, 0, box[2] if box else 1, 11))


def width(lang, s, scale):
    if lang == "en":
        return C.text_width(s, scale, scale)
    return cubic_mask(s).width * scale


def draw_text(cv, lang, x, y, s, color, scale):
    if lang == "en":
        cv.text(x, y, s, color, scale=scale, spacing=scale)
        return
    mask = cubic_mask(s)
    px = mask.load()
    for j in range(mask.height):
        for i in range(mask.width):
            if px[i, j]:
                cv.rect(x + i * scale, y + j * scale, scale, scale, color)


def background(cv):
    # Ordered-dither vignette centred on the statement, darker toward the corners.
    for y in range(C.H):
        for x in range(C.W):
            d = (((x - C.W / 2) / 190.0) ** 2 + ((y - C.H / 2) / 110.0) ** 2) ** 0.5
            level = int(max(0.0, min(1.0, 1.0 - d)) * 2.2 * 16)
            th = C.BAYER[y % 4][x % 4]
            cv.put(x, y, C.BG2 if level > 16 + th else C.BG1 if level > th else C.BG0)


def centred(cv, lang, y, s, color, scale):
    w = width(lang, s, scale)
    if w > C.W - 2 * C.MARGIN:
        sys.exit(f"'{s}' is {w} px wide; the slide takes {C.W - 2 * C.MARGIN}")
    draw_text(cv, lang, (C.W - w) // 2, y, s, color, scale)


def draw(cv, slide, lang):
    name, accent = MODS[slide["mod"]]
    text, t = slide[lang], TYPE[lang]
    lines = text["headline"]
    line_h = t["height"] * t["headline"]
    head_h = len(lines) * line_h + (len(lines) - 1) * t["leading"]
    sub_h = t["height"] * t["sub"]
    # Kicker, one module, headline, two modules, sub: centred as one block on the optical centre, 4 px above.
    block = 7 + 8 + head_h + 16 + sub_h
    y = (C.H - block) // 2 - 4
    background(cv)
    centred(cv, "en", y, name, accent, 1)
    y += 7 + 8
    for i, line in enumerate(lines):
        centred(cv, lang, y, line, accent if i == len(lines) - 1 else C.CREAM, t["headline"])
        y += line_h + t["leading"]
    y += 16 - t["leading"]
    centred(cv, lang, y, text["sub"], C.MUTED, t["sub"])


def main(argv):
    """python design/slides.py [out] [slide id ...] [--height PX]"""
    args = list(argv)
    height = 1080
    if "--height" in args:
        i = args.index("--height")
        height = int(args[i + 1])
        del args[i:i + 2]
    out = args[0] if args else "out/slides"
    slides = json.load(open(os.path.join(HERE, "slides.json"), encoding="utf-8"))["slides"]
    wanted = args[1:]
    unknown = set(wanted) - {s["id"] for s in slides}
    if unknown:
        sys.exit(f"not in slides.json: {', '.join(sorted(unknown))}")
    os.makedirs(out, exist_ok=True)
    s = height // C.H
    for slide in slides:
        if wanted and slide["id"] not in wanted:
            continue
        for lang in ("en", "zh"):
            cv = C.Canvas()
            draw(cv, slide, lang)
            img = cv.img.resize((C.W * s, C.H * s), Image.NEAREST)
            path = os.path.join(out, "%s_%s_%dp.png" % (slide["id"], lang, height))
            img.save(path, optimize=True)
            print(path, "%dx%d" % img.size)


if __name__ == "__main__":
    main(sys.argv[1:])
