# Probably Stolen Mods

Small mods for *Probably Stolen*. Each one changes one thing, such as the stutters with packed storage, the waits on phone calls or the keys you can bind, and keeps the game's rules. Each works on its own and needs no special permissions.

**Documentation:** <https://kcn-judu.github.io/ProbablyStolen-Mods/> (English, 简体中文)

**Steam Workshop:** all of them in one collection, [Quality of Life](https://steamcommunity.com/sharedfiles/filedetails/?id=3832619146).

| Mod | What it does | Repository |
| --- | --- | --- |
| [Demand Highlight](https://kcn-judu.github.io/ProbablyStolen-Mods/en/demand-highlight/) | Outlines what the customer at the counter wants, and marks your stock by type with the Item Filter. | [ProbablyStolen-DemandHighlight](https://github.com/KCN-judu/ProbablyStolen-DemandHighlight) |
| [Quick Call](https://kcn-judu.github.io/ProbablyStolen-Mods/en/quick-call/) | Calls to Wild and your other contacts go straight to the choices. | [ProbablyStolen-QuickCall](https://github.com/KCN-judu/ProbablyStolen-QuickCall) |
| [Save Language Converter](https://kcn-judu.github.io/ProbablyStolen-Mods/en/save-language-converter/) | Converts a copy of a save started in another language to the language you play in. | [ProbablyStolen-SaveLanguageConverter](https://github.com/KCN-judu/ProbablyStolen-SaveLanguageConverter) |
| [Performance Fixes](https://kcn-judu.github.io/ProbablyStolen-Mods/en/performance-fixes/) | Removes stutters with large, packed storage, without changing how the game plays. | [ProbablyStolen-PerformanceFixes](https://github.com/KCN-judu/ProbablyStolen-PerformanceFixes) |
| [Window Workspaces](https://kcn-judu.github.io/ProbablyStolen-Mods/en/window-workspaces/) | Windows snap to each other while you drag them, and workspaces switch whole sets of open containers with one key. | [ProbablyStolen-WindowWorkspaces](https://github.com/KCN-judu/ProbablyStolen-WindowWorkspaces) |
| [Better Key Bindings](https://kcn-judu.github.io/ProbablyStolen-Mods/en/better-key-bindings/) | Key combinations, the middle mouse button and mouse buttons 4 and 5 for every key binding, without double triggers. | [ProbablyStolen-BetterKeyBindings](https://github.com/KCN-judu/ProbablyStolen-BetterKeyBindings) |
| [Texture Packs (early access)](https://kcn-judu.github.io/ProbablyStolen-Mods/en/texture-packs/) | Lets mods replace the game's pictures: items, windows, the shop and its people, and the pictures other mods add. | [ProbablyStolen-TexturePacks](https://github.com/KCN-judu/ProbablyStolen-TexturePacks) |

## This repository

Each mod lives in its own repository and is included here as a Git submodule under `mods/`. This repository builds the documentation site from them and keeps the tools they share.

```sh
git clone --recurse-submodules https://github.com/KCN-judu/ProbablyStolen-Mods.git
cd ProbablyStolen-Mods
npm ci
npm run build && npm run preview   # the site at http://localhost:4321/ProbablyStolen-Mods/
```

| Path | Contents |
| --- | --- |
| `mods/` | The mods, as submodules |
| `content/` | The site's own pages (home, about, contributing) and interface strings, in the same layout as a mod's `doc/` |
| `config/` | Locales, the site's base path and the mods with their repositories and groups |
| `src/` | Astro pages, layouts, components and the pixel theme |
| `tools/lunadoc/` | The gettext documentation tool |
| `tools/prepare-site.mjs` | Renders every page in every locale from the English source and the catalogs |
| `tools/i18n/` | Helpers for filling catalogs from a translation table |
| `tools/modding/` | The game's mod scanner harness, the Mono.Cecil game-inspection tools and the development mods Leak Probe and Load Breakdown |
| `design/` | The cover design system and its renderers: covers, the collection and guide covers, the logo, video slides, comparison labels, documentation diagrams and the pixel font |
| `scripts/` | Build every mod, package releases, scan a built mod, upload to the Workshop, prepare comparison videos |

## Commands

| Command | What it does |
| --- | --- |
| `npm run update-po` | Regenerate the catalogs of the site and of every mod after editing English pages |
| `npm run status` | Translation coverage |
| `npm run check` | Validate layout, catalogs and links (what CI runs) |
| `npm run build` | Build the site into `dist/` |
| `scripts/build-all.sh [--install]` | Build every mod, and optionally install it into the game |
| `scripts/package.sh` | Collect built mods into `dist/packages/` with a zip of each |
| `scripts/release-check.sh <mod folder>` | Check a mod before a release: changelog, tests, build, scanner, docs, Workshop text, cover, git |
| `scripts/workshop.py` | Write a SteamCMD upload file per mod to `dist/workshop/`, using the item ids in `config/workshop.json` (`--only <slug>` for one) |
| `scripts/workshop-status.py` | Check that every Workshop item has its latest release and the cover of that version |
| `scripts/media.py` | Cut parts out of a comparison video, and make a GIF of it under a size budget |
| `scripts/workshop-tags.sh` | Set the Workshop tags in `config/workshop.json` (Steam client must be running) |
| `scripts/scan.sh <folder>` | Run the game's mod scanner on a built mod |
| `python design/covers.py design/out` | Render the covers (`--checkouts <folder> --sync --only <id>` writes one mod's) |
| `python design/collection_cover.py design/out` | Render the cover of the Workshop collection |
| `python design/guide_cover.py design/out` | Render the covers of the Steam guides in `workshop/` |

See [Contributing](https://kcn-judu.github.io/ProbablyStolen-Mods/en/contribute/) for the documentation standard and the translation workflow.

## License

[Apache License 2.0](LICENSE). *Probably Stolen* and its assets belong to their owners; no game files are distributed here.
