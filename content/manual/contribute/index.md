# Contributing

Each mod keeps its documentation next to its code. Its repository has a `doc/` folder with English pages and translations as gettext catalogs beside them. This site collects every mod on each build, so a change merged into a mod's `main` branch appears here once the collection points at it.

The same rules apply to every mod:

- [Documentation standard](documentation_standard.md): where files go and what each page contains.
- [Writing and markup](writing.md): headings, code, notes and images.
- [Translation](translation.md): how the gettext workflow keeps every language in step with English.
- [Code standard](code_standard.md): rules for the mods' code, such as keeping nothing of the store after leaving it.
- [Modding tools](modding_tools.md): building mods, the scanner check, the game-inspection tools, the Leak Probe and Load Breakdown development mods, releasing and publishing to the Workshop.

## Getting the collection

```sh
git clone --recurse-submodules https://github.com/KCN-judu/ProbablyStolen-Mods.git
cd ProbablyStolen-Mods
npm ci
```

## Commands

Run these from the collection repository. Each one covers the site's own pages and every mod in `mods/`:

```sh
npm run update-po   # refresh catalogs after editing English pages
npm run status      # translation coverage
npm run check       # what continuous integration runs
```

A change to a mod's `doc/manual` must also contain the updated catalogs produced by `update-po`.

## Previewing the site

```sh
npm run build
npm run preview
```

The build reads the mods from `mods/`, so a local preview shows unpublished changes in any of them.
