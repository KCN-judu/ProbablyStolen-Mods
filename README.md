# Probably Stolen Mods

Mods for *Probably Stolen* that keep the game's rules and take away what gets in the way: waiting, guessing and stutters. Each one does one thing, works on its own, and needs no special permissions.

**Documentation:** <https://kcn-judu.github.io/ProbablyStolen-Mods/> (English, 简体中文)

| Mod | What it does | Repository |
| --- | --- | --- |
| [Demand Highlight](https://kcn-judu.github.io/ProbablyStolen-Mods/en/demand-highlight/) | Outlines what the customer at the counter wants, and marks your stock by type with the Item Filter. | [ProbablyStolen-DemandHighlight](https://github.com/KCN-judu/ProbablyStolen-DemandHighlight) |
| [Quick Call](https://kcn-judu.github.io/ProbablyStolen-Mods/en/quick-call/) | Calls to Wild and your other contacts go straight to the choices. | [ProbablyStolen-QuickCall](https://github.com/KCN-judu/ProbablyStolen-QuickCall) |
| [Save Language Converter](https://kcn-judu.github.io/ProbablyStolen-Mods/en/save-language-converter/) | Converts a copy of a save started in another language to the language you play in. | [ProbablyStolen-SaveLanguageConverter](https://github.com/KCN-judu/ProbablyStolen-SaveLanguageConverter) |
| [Performance Fixes](https://kcn-judu.github.io/ProbablyStolen-Mods/en/performance-fixes/) | Removes stutters with large, packed storage, without changing how the game plays. | [ProbablyStolen-PerformanceFixes](https://github.com/KCN-judu/ProbablyStolen-PerformanceFixes) |

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
| `tools/lunadoc/` | The gettext documentation tool, from the [Luna Flow documentation site](https://github.com/Luna-Flow/Luna-Flow.github.io) |
| `tools/prepare-site.mjs` | Renders every page in every locale from the English source and the catalogs |
| `tools/i18n/` | Helpers for filling catalogs from a translation table |
| `tools/modding/` | The game's mod scanner harness and the Mono.Cecil game-inspection tools |
| `design/` | The cover design system and the cover renderer |
| `scripts/` | Build every mod, package releases, scan a built mod |

## Commands

| Command | What it does |
| --- | --- |
| `npm run update-po` | Regenerate the catalogs of the site and of every mod after editing English pages |
| `npm run status` | Translation coverage |
| `npm run check` | Validate layout, catalogs and links (what CI runs) |
| `npm run build` | Build the site into `dist/` |
| `scripts/build-all.sh [--install]` | Build every mod, and optionally install it into the game |
| `scripts/package.sh` | Collect built mods into `dist/packages/` with a zip of each |
| `scripts/scan.sh <folder>` | Run the game's mod scanner on a built mod |
| `python design/covers.py design/out` | Render the covers |

See [Contributing](https://kcn-judu.github.io/ProbablyStolen-Mods/en/contribute/) for the documentation standard and the translation workflow.

## License

[Apache License 2.0](LICENSE). *Probably Stolen* and its assets belong to their owners; no game files are distributed here.
