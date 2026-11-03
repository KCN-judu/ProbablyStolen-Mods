# Cover design system

One system for every mod cover, so the three read as a series in the Workshop grid and the in-game mod list.

## Format

- 320 × 180 logical pixels, scaled ×4 with nearest-neighbour to **1280 × 720** (16:9). The in-game mod list fits `preview.png` to the panel width, and Steam keeps any aspect. 16:9 fills the in-game panel without leaving it tall and empty.
- Every shape sits on whole logical pixels. Nothing is anti-aliased. The game is pixel art, so the cover is too.
- The PNG uses a palette of about 20 colours, which keeps each file far below Steam's 1 MB preview limit.

## Grid (after Müller-Brockmann, *Grid Systems in Graphic Design*)

- 8 px module. Margins are 16 px on the sides and 16 px top and bottom: two modules, about 1/20 of the width, enough to survive thumbnail cropping.
- Two fields: a **text column** of 16–144 px (5/12 of the width) and an **image field** of 160–304 px. The 16 px gutter between them is also two modules.
- Text baselines snap to the 8 px grid. The title block starts on the top margin, and the author line sits on the bottom margin.

## Hierarchy and type (after Bringhurst, *The Elements of Typographic Style*)

- One typeface: a hand-built 5 × 7 pixel capital alphabet, in the spirit of the game's own UI lettering. Capitals only, because pixel lowercase is illegible at thumbnail size.
- The scale has two steps, in a 2 : 1 ratio, because integer scaling is the only kind that stays crisp. The title is ×2 (14 px capitals), and the series tag, tagline and author line are ×1 (7 px).
- Letter spacing is 1 px at ×1 and 2 px at ×2. Line spacing is 1.6× the cap height for the tagline, and the title has 4 px leading.
- The title is at most two words per line and three lines in all. The tagline is at most three short lines. The measure stays under about 20 characters, so it reads at a glance.
- Reading order follows a Z: series tag → title → tagline (left column) → illustration (right field) → author line. The illustration is the single focal point and sits on the right-hand third line.

## Colour (after Itten and Albers)

- **60 / 30 / 10**: dark, desaturated violet backgrounds (60), panel mid-tones (30), one accent per mod (10).
- The base hues come from the game's key art: dusk violet walls, warm orange shop light, teal signage. The accents form the game's own complementary pairs, warm against the cool ground:
  - Save Language Converter: teal `#4CC3B5`
  - Quick Call: shop-light orange `#F08A3C`
  - Demand Highlight: the in-mod green `#5CEB6B`, with the mod's amber, red and cyan outline colours used only inside the illustration
  - Performance Fixes: cyan `#59D1FF`
  - Window Workspaces: lilac `#C3A6EA`
  - Better Key Bindings: amber `#FFB829`, the colour of a lit keycap
- Contrast: cream `#F3E6C8` on the background `#17151F` is about 15 : 1, and the muted tagline `#A79FBF` is about 7 : 1. Both pass WCAG AAA for their size.
- Depth comes from value, not hue: panels get a 1 px highlight on the top and left edges and a 1 px shadow on the bottom and right, like the game's machinery plates.

## Gestalt

- **Similarity**: same grid, same type, same panel frame and rivets on every cover. Only the accent and the illustration change, so the series is recognisable.
- **Proximity**: the series tag, title and accent rule form one group. The tagline is a second group, separated by one module.
- **Figure / ground**: the illustration panel is the brightest, most saturated area, and the background is ordered-dithered toward the corners (a vignette) to push it back.

## Illustrations

Each one shows the mod working, using the game's own visual language: inventory grids, machine panels, item silhouettes.

- **Save Language Converter**: two save cartridges, 文 → A, with an arrow carrying lines of text from one to the other.
- **Quick Call**: a phone keypad, a fast-forward chevron, and a dialog panel opened straight onto its choices with the first one selected.
- **Demand Highlight**: an inventory grid showing the four outline styles, plus a small Item Filter window with ticked boxes.
- **Better Key Bindings**: lit Ctrl + E keycaps, a mouse with its middle and side buttons lit, and a key bindings list where Ctrl + E and E sit on separate rows.

- **The Quality of Life collection** (`collection_cover.py`): one tile per mod in its own accent, in the order the collection lists them, with what each mod takes away. The series tag reads PROBABLY STOLEN MODS and the author line gives the number of mods instead of a version.

## Logo

The collection's logo (`collection_logo.py`) is a drafting compass that reads as a λ: a long stroke with a branch.

- Two legs of equal length on mirrored 1:2 slopes, points on one row; the stalk continues the right leg up to the knob.
- **Detailed** (128 × 128 grid; 128, 256, 512 and 1024 px): cream legs lit on one side and shaded on the other with a darker rim; a knurled knob; a teal hinge plate with four rivets and a slotted steel screw; steel collars with their screw heads; a pencil leg ending in a sharpened cone and a teal lead, and a needle leg. A one-pixel dark outline holds it on any ground. On the icon it lies on drafting paper (an inset sheet with a dotted 8 px grid) casting a shadow, inside a machinery plate with rivets and cut corners. Teal is the collection's accent.
- **Small** (64 × 64 grid; 32 and 64 px): the same compass without the parts, cream with a teal hinge and lead on the plate, because detail turns to noise at that size.
- `collection_logo_*.png` is the icon, `collection_mark_*.png` the detailed compass alone on transparency, `collection_logo_small_*.png` the small icon.

```
python design/collection_logo.py design/out/logo
```

## Comparison labels

Comparison videos (before / after one mod) carry a corner label on each half, rendered by `compare_labels.py`.

- One line on a machinery plate without rivets: the mod's name in cream, then a switch. **OFF** is an unlit slot with muted text and a faint bar; **ON** is lit in the mod's accent with dark text, and the bar on the left edge takes the accent too.
- The switch is sized for OFF, so the OFF and ON labels are exactly the same size and line up across the two halves.
- Transparent PNG, scaled with nearest-neighbour by half the cover's video scale: ×3 for 1080p, ×6 for 2160p (`--height`).
- Placement: top-left of each half, inset by the cover margin at the same scale (48 px at 1080p, 96 px at 2160p). OFF on the left, ON on the right.
- A new mod gets a line in `compare_labels.MODS` with its name and the accent from Colour above.

```
python design/compare_labels.py design/out/labels performance_fixes            # 1080p
python design/compare_labels.py design/out/labels performance_fixes --height 2160
```

## Video font

`pixel_font.py` builds **Probably Stolen Pixel** (`ProbablyStolenPixel.ttf`) from the same alphabet as the covers, for timers, titles and captions in videos. It has every printable ASCII character; lowercase sets as capitals, as on the covers.

- Font size a multiple of 7 px (21 px at 1080p, 42 px at 2160p) and anti-aliasing off, so each font pixel stays a whole block.
- Colours from the palette above: cream for text, the mod's accent for values such as a timer.

```
python design/pixel_font.py design/out/ProbablyStolenPixel.ttf
```

## Video slides

Statement slides cut into videos, rendered by `slides.py` from `slides.json`, in English and Chinese. A new slide is a new entry in `slides.json`; the code stays as it is.

- One statement per slide, centred as a block a little above the middle: the mod's name in its accent (×1), a two-line headline whose last line takes the accent, and one muted line under it.
- English is set in the cover alphabet with a ×4 headline. Chinese is set in Cubic 11 (`fonts/Cubic_11.ttf`, SIL Open Font License, licence beside it) with a ×3 headline; the mod's name stays in English. At 12 px each Cubic pixel is one canvas pixel, so both scripts scale with nearest-neighbour and stay crisp.
- Same 320 × 180 canvas, ×6 for 1080p and ×12 for 2160p (`--height`); the vignette is centred on the statement.
- Each line must fit between the margins; the script stops with the line's width if it does not.

```
python design/slides.py design/out/slides
python design/slides.py design/out/slides performance_fixes_stutter --height 2160
```

## Checks

- Thumbnail test: each cover is also written at 25 % (`*_thumb.png`). The title must still read there.
- No text is closer than 16 px to an edge.

## Version

The version next to the author line comes from the mod's `manifest.xml`; it is always shown in full as x.y.z (V1.1.0, V1.0.1), except a new major version x.0.0, which shows as Vx.0 (V1.0, V2.0). `scripts/package.sh` renders the covers again for every package, and `covers.py --sync` writes them into the mods, so a cover never shows an old version.
