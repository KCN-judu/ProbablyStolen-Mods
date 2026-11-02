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

## Checks

- Thumbnail test: each cover is also written at 25 % (`*_thumb.png`). The title must still read there.
- No text is closer than 16 px to an edge.
