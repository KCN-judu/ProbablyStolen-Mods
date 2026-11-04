"""Renders the logo of the Quality of Life collection: a drafting compass that reads as a lambda (DESIGN.md, Logo).

    python design/collection_logo.py design/out/logo

The logo is drawn on a 128x128 grid with the instrument's parts drawn out, on a sheet of drafting paper; sizes
of 64 px and below use a plain version on a 64x64 grid. Both scale with nearest-neighbour, like the covers.
Every bar runs at 1:2; the two legs are equal and their points sit on one row.
"""
import math
import os
import sys
from collections.abc import Callable, Sequence
from typing import Final, TypeAlias

from PIL import Image

import covers as C

Point: TypeAlias = tuple[float, float]
Poly: TypeAlias = Sequence[Point]
Region: TypeAlias = Callable[[float, float], bool]
CLEAR: Final[C.Rgba] = (0, 0, 0, 0)

N: Final = 64
TEAL_LO: Final[C.Color] = (0x2E, 0x86, 0x7E)
HINGE: Final = (32, 24)            # on the centre line
# Every edge runs along (1, 2) or (2, -1), with its corners on whole pixels, so each edge is an even stair step.
ALONG: Final = (1, 2)
ACROSS: Final = (2, -1)


def at(p: Point, t: float, s: float) -> Point:
    # The point t steps down the right leg's axis and s steps across it from p.
    return (p[0] + t * ALONG[0] + s * ACROSS[0], p[1] + t * ALONG[1] + s * ACROSS[1])


def mirror(poly: Poly) -> Poly:
    return [(N - x, y) for x, y in poly]


def right_leg(top_t: float) -> Poly:
    # From top_t down to the tip row (y 57). The outer edge runs to the point; the inner edge stops short of it,
    # a short chamfer like a sharpened lead.
    return [at(HINGE, top_t, 1), at(HINGE, 17, 1), at(HINGE, 14.5, -1), at(HINGE, top_t, -1)]


def block(centre: Point, half_along: float, half_across: float) -> Poly:
    return [at(centre, sa * half_along, sc * half_across) for sa, sc in ((-1, -1), (1, -1), (1, 1), (-1, 1))]


def inside(poly: Poly, x: float, y: float) -> bool:
    # Convex polygon, either winding.
    sign: float = 0
    for (x0, y0), (x1, y1) in zip(poly, (*poly[1:], *poly[:1])):
        c = (x1 - x0) * (y - y0) - (y1 - y0) * (x - x0)
        if c != 0:
            if sign and (c > 0) != (sign > 0):
                return False
            sign = c
    return True


def everywhere(x: float, y: float) -> bool:
    return True


def fill(cv: C.Canvas, poly: Poly, colour: C.Color, where: Region = everywhere) -> None:
    # Pixel centres, nudged off the edges so a centre on an edge always falls the same way.
    # The polygon is convex, so only the pixels of its bounding box can be inside it.
    x0, x1 = max(0, int(min(p[0] for p in poly)) - 1), min(N, int(max(p[0] for p in poly)) + 2)
    y0, y1 = max(0, int(min(p[1] for p in poly)) - 1), min(N, int(max(p[1] for p in poly)) + 2)
    for y in range(y0, y1):
        for x in range(x0, x1):
            px, py = x + 0.5 + 1e-3, y + 0.5 + 2e-3
            if inside(poly, px, py) and where(px, py):
                cv.put(x, y, colour)


def bevel(cv: C.Canvas, light: C.Color, dark: C.Color) -> None:
    # Depth by value (DESIGN.md, Colour): each shape's right and bottom edge pixels take its darker tone.
    for y in range(N):
        for x in range(N):
            if cv.get(x, y)[:3] != light:
                continue
            for dx, dy in ((1, 0), (0, 1)):
                if x + dx >= N or y + dy >= N or cv.get(x + dx, y + dy)[:3] != light:
                    cv.put(x, y, dark)
                    break


def stud(cv: C.Canvas, x: int, y: int, size: int, body: C.Color, dark: C.Color) -> None:
    # A square block: highlight on the top and left edges, shadow on the bottom and right.
    cv.rect(x, y, size, size, body)
    cv.hline(x, y, size, C.CREAM if body != C.CREAM else body)
    cv.vline(x, y, size, C.CREAM if body != C.CREAM else body)
    cv.hline(x, y + size - 1, size, dark)
    cv.vline(x + size - 1, y, size, dark)


def compass(cv: C.Canvas) -> None:
    # The stalk continues the right leg up to the knob; the left leg is its mirror, hung from the hinge.
    right = right_leg(-7)
    fill(cv, right, C.CREAM)
    # The lead: the last stretch of the right leg, past a line square to it.
    lead = 13 * (ALONG[0] ** 2 + ALONG[1] ** 2)
    fill(cv, right, C.TEAL, lambda x, y: (x - HINGE[0]) * ALONG[0] + (y - HINGE[1]) * ALONG[1] > lead)
    fill(cv, mirror(right_leg(0)), C.CREAM)
    # The knob: a wider stretch at the top of the stalk, on the stalk's own slope.
    fill(cv, block(at(HINGE, -8, 0), 1.5, 1.5), C.CREAM)
    # A corner on the knob lands as a lone pixel; the tips below the hinge keep theirs, they are the points.
    for y in range(HINGE[1]):
        for x in range(N):
            if cv.get(x, y)[:3] == C.CREAM and sum(
                    0 <= x + dx < N and 0 <= y + dy < N and cv.get(x + dx, y + dy)[:3] == C.CREAM
                    for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1))) <= 1:
                cv.put(x, y, CLEAR)
    bevel(cv, C.CREAM, C.CREAM_DIM)
    # The hinge is a square block lit like the game's plates; turned to the stalk it would lose its corners at
    # this size.
    stud(cv, HINGE[0] - 5, HINGE[1] - 5, 10, C.TEAL, TEAL_LO)
    cv.rect(HINGE[0] - 1, HINGE[1] - 1, 2, 2, C.PANEL_LO)


def tile(cv: C.Canvas) -> None:
    # A machinery plate, as on the covers, with its corners cut to round it off.
    cv.plate(0, 0, N, N)
    for x, y in ((0, 0), (1, 0), (0, 1), (N - 1, 0), (N - 2, 0), (N - 1, 1),
                 (0, N - 1), (1, N - 1), (0, N - 2), (N - 1, N - 1), (N - 2, N - 1), (N - 1, N - 2)):
        cv.put(x, y, CLEAR)
    for x, y in ((2, 1), (1, 2), (N - 3, 1), (N - 2, 2)):
        cv.put(x, y, C.PANEL_HI)
    for x, y in ((1, N - 3), (2, N - 2), (N - 2, N - 3), (N - 3, N - 2)):
        cv.put(x, y, C.PANEL_LO)


# The detailed logo, on a 128x128 grid: the same compass with its parts drawn out, on a sheet of drafting paper.
# Shapes are described in steps down (t) and across (s) the right leg, from the hinge; the left leg is the mirror.
BIG: Final = 128
BIG_HINGE: Final = (64, 50)
TIP_T: Final = 31                  # both points sit on row 112
CREAM_LO: Final[C.Color] = (0xA0, 0x92, 0x76)
TEAL_HI: Final[C.Color] = (0x8F, 0xE3, 0xD7)
SHADOW: Final[C.Color] = (0x1A, 0x18, 0x24)


# Inverse of at(): (t, s) of a pixel centre, in units of 5 (the length of the axis vector (1, 2) is sqrt 5; the divisor
# # keeps the sqrt 5 out of the shapes). The same coordinates serve the left leg by mirroring x.
def steps(x: int, y: int) -> tuple[float, float]:
    dx, dy = x + 0.5 - BIG_HINGE[0], y + 0.5 - BIG_HINGE[1]
    return (dx * ALONG[0] + dy * ALONG[1]) / 5.0, (dx * ACROSS[0] + dy * ACROSS[1]) / 5.0


def bar(s: float, half: float, light: C.Color, mid: C.Color, dark: C.Color) -> C.Color:
    # Lit on the upper side, shaded on the lower, with a darker rim on the shaded edge.
    if s < -half + 0.5:
        return dark
    return mid if s < -0.6 else light


def clamp(t: float, s: float, at_t: float) -> C.Color | None:
    # A steel collar, with its screw head standing out on the outer side.
    if at_t - 2 <= t <= at_t + 2 and abs(s) <= 2.6:
        return bar(s, 2.6, C.CREAM_DIM, C.STEEL, C.STEEL_LO)
    if abs(t - at_t) <= 0.7 and 2.6 < s <= 3.5:
        return C.STEEL_LO
    return None


# Colour of the pixel at (t, s) of the right leg, or None outside it: knob, bar, clamp, pencil. The left leg has its own below.
def right_leg_colour(t: float, s: float) -> C.Color | None:
    if -16.5 <= t <= -11 and abs(s) <= 3:
        # The knob, knurled across its grip.
        if t < -16 or s < -2.4:
            return CREAM_LO
        return C.CREAM if math.floor(t) % 2 == 0 else C.CREAM_DIM
    if -11 < t < 19 and abs(s) <= 2:
        return bar(s, 2, C.CREAM, C.CREAM_DIM, CREAM_LO)
    c = clamp(t, s, 21)
    if c:
        return c
    if 23 < t <= TIP_T and abs(s) <= 2 * (TIP_T - t) / 8:
        # The pencil: a sharpened wooden cone ending in the lead.
        if t > TIP_T - 4:
            return C.TEAL if s >= 0 else TEAL_LO
        return C.CREAM_DIM if s >= 0 else CREAM_LO
    return None


# As right_leg_colour for the left leg: plain bar, the same clamp, and a needle point instead of the pencil.
def left_leg_colour(t: float, s: float) -> C.Color | None:
    if 0 <= t < 19 and abs(s) <= 2:
        return bar(s, 2, C.CREAM, C.CREAM_DIM, CREAM_LO)
    c = clamp(t, s, 21)
    if c:
        return c
    half = 0.8 if t < TIP_T - 2 else 0.8 * (TIP_T - t) / 2
    if 23 < t <= TIP_T and abs(s) <= half:
        # The needle.
        return C.CREAM_DIM if s >= 0 else C.STEEL
    return None


def hinge(cv: C.Canvas) -> None:
    # A riveted teal plate holding a slotted screw.
    x0, y0, size = BIG_HINGE[0] - 11, BIG_HINGE[1] - 11, 22
    cv.rect(x0, y0, size, size, C.TEAL)
    cv.hline(x0, y0, size, TEAL_HI)
    cv.vline(x0, y0, size, TEAL_HI)
    cv.hline(x0, y0 + size - 1, size, TEAL_LO)
    cv.vline(x0 + size - 1, y0, size, TEAL_LO)
    for rx, ry in ((x0 + 3, y0 + 3), (x0 + size - 5, y0 + 3), (x0 + 3, y0 + size - 5), (x0 + size - 5, y0 + size - 5)):
        cv.put(rx, ry, TEAL_HI)
        cv.put(rx + 1, ry, TEAL_LO)
        cv.put(rx, ry + 1, TEAL_LO)
        cv.put(rx + 1, ry + 1, C.PANEL_LO)
    cx, cy = BIG_HINGE
    for y in range(cy - 6, cy + 6):
        for x in range(cx - 6, cx + 6):
            dx, dy = x + 0.5 - cx, y + 0.5 - cy
            r = math.hypot(dx, dy)
            if r > 5.6:
                continue
            c: C.Color
            if abs(dx * ALONG[0] + dy * ALONG[1]) / math.sqrt(5) < 0.9 and r < 4.6:
                c = C.PANEL_LO                      # the slot, square to the stalk
            elif r > 4.6:
                c = C.STEEL_LO
            elif dx + dy < -2.5:
                c = C.CREAM_DIM
            else:
                c = C.STEEL
            cv.put(x, y, c)


def outline(cv: C.Canvas, colour: C.Color) -> None:
    # A one-pixel dark rim around the whole instrument, so it holds on any ground.
    rim = [(x, y) for y in range(cv.h) for x in range(cv.w)
           if not cv.lit(x, y) and any(cv.lit(x + dx, y + dy) for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1)))]
    for x, y in rim:
        cv.put(x, y, colour)


# The 128 grid compass is shaded per pixel from the leg coordinates; the left leg is the right one read at the mirrored x.
def big_compass(cv: C.Canvas) -> None:
    for y in range(BIG):
        for x in range(BIG):
            colour = right_leg_colour(*steps(x, y)) or left_leg_colour(*steps(BIG - 1 - x, y))
            if colour is not None:
                cv.put(x, y, colour)
    hinge(cv)
    outline(cv, C.PANEL_LO)


# The icon: a plate with cut corners, rivets, the drafting-paper inset, the compass's shadow, then the compass itself.
def big_tile(cv: C.Canvas, mark: C.Canvas) -> None:
    n = BIG
    cv.plate(0, 0, n, n, rivets=False)
    for i in range(3):
        for x, y in ((i, 0), (0, i), (n - 1 - i, 0), (n - 1, i), (i, n - 1), (0, n - 1 - i), (n - 1 - i, n - 1), (n - 1, n - 1 - i)):
            if i < 2 or (x in (0, n - 1) and y in (0, n - 1)):
                cv.put(x, y, CLEAR)
    for x, y in ((1, 1), (n - 2, 1), (1, n - 2), (n - 2, n - 2)):
        cv.put(x, y, CLEAR)
    for rx, ry in ((4, 4), (n - 7, 4), (4, n - 7), (n - 7, n - 7)):
        cv.rect(rx, ry, 3, 3, C.STEEL_LO)
        cv.hline(rx, ry, 2, C.PANEL_HI)
        cv.vline(rx, ry, 2, C.PANEL_HI)
        cv.put(rx + 2, ry + 2, C.PANEL_LO)
    # The drafting paper: an inset sheet with a dotted 8 px grid.
    p0, p1 = 10, n - 10
    cv.slot(p0, p0, p1 - p0, p1 - p0)
    for g in range(p0 + 6, p1 - 1, 8):
        for k in range(p0 + 2, p1 - 2, 2):
            cv.put(g, k, C.SLOT_HI)
            cv.put(k, g, C.SLOT_HI)
    # The instrument's shadow on the paper, down and to the right.
    for y in range(n):
        for x in range(n):
            if mark.lit(x, y) and p0 + 1 <= x + 3 < p1 - 1 and p0 + 1 <= y + 3 < p1 - 1:
                cv.put(x + 3, y + 3, SHADOW)
    cv.img.alpha_composite(mark.img)


def main(out: str) -> None:
    os.makedirs(out, exist_ok=True)
    # Small sizes keep the plain compass on the 64 grid; detail would only turn to noise there.
    small_mark = C.Canvas(N, N, "RGBA")
    compass(small_mark)
    small = C.Canvas(N, N, "RGBA")
    tile(small)
    small.img.alpha_composite(small_mark.img)
    # The compass is drawn on its own transparent canvas, then laid on the paper for the icon.
    mark = C.Canvas(BIG, BIG, "RGBA")
    big_compass(mark)
    icon = C.Canvas(BIG, BIG, "RGBA")
    big_tile(icon, mark)
    outputs: tuple[tuple[str, C.Canvas, tuple[int, ...]], ...] = (
        ("collection_logo", icon, (128, 256, 512, 1024)),
        ("collection_mark", mark, (512, 1024)),
        ("collection_logo_small", small, (32, 64)))
    for name, cv, sizes in outputs:
        for size in sizes:
            path = os.path.join(out, "%s_%d.png" % (name, size))
            cv.img.resize((size, size), Image.Resampling.NEAREST).save(path, optimize=True)
            print(path)


if __name__ == "__main__":
    main(sys.argv[1] if len(sys.argv) > 1 else "out/logo")
