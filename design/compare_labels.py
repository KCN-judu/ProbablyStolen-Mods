"""Renders the OFF / ON labels for comparison videos, in the mod cover style (DESIGN.md, Comparison labels).

    python design/compare_labels.py design/out/labels                      # every mod, for 1080p video
    python design/compare_labels.py design/out/labels performance_fixes --height 2160

Same type, palette and plates as covers.py. Each label is a transparent PNG: the mod's name, then a switch
that reads OFF (unlit slot) or ON (lit in the mod's accent). OFF and ON are the same size, so the two halves
of a comparison line up.
"""
import os
import sys
from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from types import MappingProxyType
from typing import Final

from PIL import Image

import covers as C
from typed import take_option

# Each mod's name on the label and its accent (DESIGN.md, Colour), keyed like covers.COVERS.
MODS: Final[Mapping[str, tuple[str, C.Color]]] = MappingProxyType({
    "performance_fixes": ("PERFORMANCE FIXES", C.CYAN),
    "demand_highlight": ("DEMAND HIGHLIGHT", C.GREEN),
    "quick_call": ("QUICK CALL", C.ORANGE),
    "window_workspaces": ("WINDOW WORKSPACES", C.LILAC),
    "better_key_bindings": ("BETTER KEY BINDINGS", C.AMBER),
    "save_language_converter": ("SAVE LANGUAGE CONVERTER", C.TEAL),
})

PAD: Final = 8                                   # bevel, accent bar and gap before the name
CHIP_W: Final = C.text_width("OFF") + 8          # the switch fits the longer state, so OFF and ON match
H: Final = 17


# One label: plate, accent bar (lit only for ON), the mod's name, then the OFF/ON switch chip; returned as a transparent image.
def draw(name: str, accent: C.Color, on: bool) -> Image.Image:
    chip_x = PAD + C.text_width(name) + 6
    cv = C.Canvas(chip_x + CHIP_W + 4, H, "RGBA")   # transparent, so the label lies on any video
    cv.plate(0, 0, cv.w, H, rivets=False)
    # Accent bar on the left edge, lit only when the mod is on.
    cv.rect(1, 1, 3, H - 2, accent if on else C.FAINT)
    cv.text(PAD, 5, name, C.CREAM)
    state = "ON" if on else "OFF"
    if on:
        cv.rect(chip_x, 3, CHIP_W, 11, accent)
        cv.hline(chip_x, 3, CHIP_W, C.CREAM)
        ink = C.BG0
    else:
        cv.slot(chip_x, 3, CHIP_W, 11)
        ink = C.MUTED
    cv.text(chip_x + (CHIP_W - C.text_width(state)) // 2, 5, state, ink)
    return cv.img


def scale_for(height: int) -> int:
    # The cover grid is 180 logical px tall, so 1080p is x6. The label takes half of that, x3, so it sits in
    # a corner of each half of a side-by-side without covering the game.
    return max(1, height // C.H // 2)


@dataclass(frozen=True)
class Options:
    out: str
    names: Sequence[str]
    height: int


def parse_options(argv: Sequence[str]) -> Options:
    height_arg, rest = take_option(argv, "--height")
    names = rest[1:] or tuple(MODS)
    for name in names:
        if name not in MODS:
            raise SystemExit(f"{name}: not one of {', '.join(MODS)}")
    return Options(rest[0] if rest else "out/labels", names, 1080 if height_arg is None else int(height_arg))


def main(argv: Sequence[str]) -> None:
    """python design/compare_labels.py [out] [mod ...] [--height PX]"""
    opts = parse_options(argv)
    os.makedirs(opts.out, exist_ok=True)
    s = scale_for(opts.height)
    for name in opts.names:
        title, accent = MODS[name]
        for on in (False, True):
            img = draw(title, accent, on)
            img = img.resize((img.width * s, img.height * s), Image.Resampling.NEAREST)
            path = os.path.join(opts.out, "%s_%s_%dp.png" % (name, "on" if on else "off", opts.height))
            img.save(path, optimize=True)
            print(path, "%dx%d" % img.size)


if __name__ == "__main__":
    main(sys.argv[1:])
