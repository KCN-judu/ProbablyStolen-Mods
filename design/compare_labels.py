"""Renders the OFF / ON labels for comparison videos, in the mod cover style (DESIGN.md, Comparison labels).

    python design/compare_labels.py design/out/labels                      # every mod, for 1080p video
    python design/compare_labels.py design/out/labels performance_fixes --height 2160

Same type, palette and plates as covers.py. Each label is a transparent PNG: the mod's name, then a switch
that reads OFF (unlit slot) or ON (lit in the mod's accent). OFF and ON are the same size, so the two halves
of a comparison line up.
"""
import os
import sys
from PIL import Image

import covers as C

# Each mod's name on the label and its accent (DESIGN.md, Colour), keyed like covers.COVERS.
MODS = {
    "performance_fixes": ("PERFORMANCE FIXES", C.CYAN),
    "demand_highlight": ("DEMAND HIGHLIGHT", C.GREEN),
    "quick_call": ("QUICK CALL", C.ORANGE),
    "window_workspaces": ("WINDOW WORKSPACES", C.LILAC),
    "better_key_bindings": ("BETTER KEY BINDINGS", C.AMBER),
    "save_language_converter": ("SAVE LANGUAGE CONVERTER", C.TEAL),
}

PAD = 8                                   # bevel, accent bar and gap before the name
CHIP_W = C.text_width("OFF") + 8          # the switch fits the longer state, so OFF and ON match
H = 17


class LabelCanvas(C.Canvas):
    # A transparent canvas of its own size; drawing works as on the cover canvas.
    def __init__(self, w, h):
        self.w, self.h = w, h
        self.img = Image.new("RGBA", (w, h), (0, 0, 0, 0))
        self.px = self.img.load()

    def put(self, x, y, c):
        if 0 <= x < self.w and 0 <= y < self.h:
            self.px[x, y] = c + (255,) if len(c) == 3 else c


def draw(name, accent, on):
    chip_x = PAD + C.text_width(name) + 6
    cv = LabelCanvas(chip_x + CHIP_W + 4, H)
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


def scale_for(height):
    # The cover grid is 180 logical px tall, so 1080p is x6. The label takes half of that, x3, so it sits in
    # a corner of each half of a side-by-side without covering the game.
    return max(1, height // C.H // 2)


def main(argv):
    """python design/compare_labels.py [out] [mod ...] [--height PX]"""
    args = list(argv)
    height = 1080
    if "--height" in args:
        i = args.index("--height")
        height = int(args[i + 1])
        del args[i:i + 2]
    out = args[0] if args else "out/labels"
    names = args[1:] or list(MODS)
    for name in names:
        if name not in MODS:
            sys.exit(f"{name}: not one of {', '.join(MODS)}")
    os.makedirs(out, exist_ok=True)
    s = scale_for(height)
    for name in names:
        title, accent = MODS[name]
        for on in (False, True):
            img = draw(title, accent, on)
            img = img.resize((img.width * s, img.height * s), Image.NEAREST)
            path = os.path.join(out, "%s_%s_%dp.png" % (name, "on" if on else "off", height))
            img.save(path, optimize=True)
            print(path, "%dx%d" % img.size)


if __name__ == "__main__":
    main(sys.argv[1:])
