"""Renders the cover of the Steam Workshop collection, in the mod cover style (DESIGN.md).

    python design/collection_cover.py design/out

Same canvas, grid, type and palette as covers.py. The illustration is one tile per mod in its own accent,
in the order the collection lists them, so the cover reads as the series it gathers.
"""
import os
import sys
from PIL import Image

import covers as C

# One tile per mod: accent, what it takes away, where.
MODS = [
    (C.CYAN, "NO LAG", "STORAGE"),          # Performance Fixes
    (C.GREEN, "FIND IT", "DEMAND"),         # Demand Highlight
    (C.ORANGE, "NO WAIT", "PHONE"),         # Quick Call
    (C.LILAC, "WINDOWS", "WORKSPACE"),      # Window Workspaces
    (C.AMBER, "KEYS", "CTRL + E"),          # Better Key Bindings
    (C.TEAL, "LANGUAGE", "SAVES"),          # Save Language Converter
]


def tile(cv, x, y, w, h, accent, label, sub):
    cv.plate(x, y, w, h, rivets=False)
    cv.rect(x + 1, y + 1, 3, h - 2, accent)
    cv.text(x + 8, y + 9, label, accent)
    cv.text(x + 8, y + 23, sub, C.CREAM_DIM)


def draw(cv):
    C.background(cv)
    y = C.MARGIN
    cv.text(C.TEXT_X0, y, "PROBABLY STOLEN MODS", C.MUTED)
    y += 7 + 9
    for line in ("QUALITY", "OF LIFE"):
        cv.text(C.TEXT_X0, y, line, C.CREAM, scale=2, spacing=2)
        y += 14 + 4
    y += 2
    cv.rect(C.TEXT_X0, y, 24, 2, C.TEAL)
    y += 2 + 10
    for line in ("KEEP THE RULES.", "LOSE THE WAITING,", "GUESSING, STUTTERS."):
        cv.text(C.TEXT_X0, y, line, C.MUTED)
        y += 11
    cv.text(C.TEXT_X0, C.H - C.MARGIN - 7, "BY KCN-JUDU", C.FAINT)
    cv.text(C.TEXT_X0 + C.text_width("BY KCN-JUDU") + 8, C.H - C.MARGIN - 7, "%d MODS" % len(MODS), C.TEAL)

    w, h, gap = 68, 40, 8
    for i, (accent, label, sub) in enumerate(MODS):
        col, row = i % 2, i // 2
        tile(cv, C.IMG_X0 + col * (w + gap), 24 + row * (h + 6), w, h, accent, label, sub)


def main(out):
    os.makedirs(out, exist_ok=True)
    cv = C.Canvas()
    draw(cv)
    big = cv.img.resize((C.W * C.SCALE, C.H * C.SCALE), Image.NEAREST)
    big = big.convert("P", palette=Image.ADAPTIVE, colors=64)
    path = os.path.join(out, "collection.png")
    big.save(path, optimize=True)
    cv.img.resize((C.W, C.H), Image.NEAREST).save(os.path.join(out, "collection_thumb.png"))
    print(path, os.path.getsize(path), "bytes")


if __name__ == "__main__":
    main(sys.argv[1] if len(sys.argv) > 1 else "out")
