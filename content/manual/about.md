# About

This collection gathers the *Probably Stolen* mods written by KCN-judu. Every mod lives in its own repository, with its own releases and Steam Workshop page; the collection repository ties them together as Git submodules and builds this site from their documentation.

## Principles

**Keep the game's rules.** A mod may remove waiting, guessing or wasted work, but customers accept what they accepted before, locks still lock, and saves load as they did. Where a mod changes how something is computed, it computes the same answer.

**Ask for nothing.** Every mod declares no capabilities, so the game enables it without a permission prompt. Reflection only names game types directly, which the game's mod scanner accepts.

**Fail quietly.** A patch that cannot attach, after a game update for example, turns its own feature off and writes one line to `Player.log`. It never stops the rest of the mod or the game.

**Measure first.** Performance work starts from the game's own log and from a profiler, not from guesses. The numbers behind each fix are in its documentation.

## The mods

| Mod | What it does |
| --- | --- |
| Demand Highlight | Outlines what the customer at the counter wants, and marks your stock by type with the Item Filter. |
| Quick Call | Calls go straight to the choices. |
| Save Language Converter | Converts a copy of a save started in another language. |
| Performance Fixes | Removes stutters with large, packed storage. |

## Look

The site and the mod covers share one design: the game's dusk-violet windows, cream text and teal title bars, square panels with a one-pixel bevel, and pixel lettering for names and labels. The cover system is described in `design/DESIGN.md` of the collection repository. Chinese headings use Cubic 11, an open-source pixel font released under the SIL Open Font License.

## License

Every repository is released under the Apache License 2.0. *Probably Stolen* and its assets belong to their owners; no game files are distributed here.
