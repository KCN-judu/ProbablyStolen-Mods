# Documentation standard

This standard applies to every mod in the collection. It fixes where documentation lives, how it is divided into pages, and which source is authoritative.

## Principles

**Describe what exists.** Pages document the mod as it is on the current branch: what it does, its options, and the decisions behind them. Plans belong in issues.

**English is the source.** Pages are written once, in English. Translations are made from that text through [gettext catalogs](translation.md) and are never edited as copies of a page.

**Players first, then modders.** The overview page tells a player what the mod does and how to use it. How it works, measurements and build instructions follow on their own pages.

## Repository layout

```text
doc/
├── conf.json                      title, summary, locales and page order
├── manual/                        English source pages
│   ├── index.md                   what the mod does and how to use it
│   ├── <guide>.md                 how it works, options, performance, ...
│   └── building.md                requirements and build steps
├── attachments/                   images shared by all locales
│   └── cover.png                  the mod's cover, shown in the library
└── locale/
    ├── manual.pot                 generated template, never edited
    └── zh_CN/LC_MESSAGES/manual.po
```

Nothing else belongs in `doc/`.

### `conf.json`

```json
{
  "title": "Quick Call",
  "summary": "Calls to Wild and your other contacts go straight to the choices.",
  "locales": ["zh_CN"],
  "order": ["index.md", "how-it-works.md", "building.md"]
}
```

`title` is the mod's name as shown in the library. `summary` is one sentence for the library and the home page; it is translated like any page text. `locales` lists the translations the mod maintains. `order` is the order of the pages in the sidebar.

## Pages

- Each page starts with one `# Title`, which becomes its title in the sidebar and in search results.
- One page, one purpose: an overview, a guide to one part, or the build instructions.
- Name a game type or method in code formatting, as in `PhoneUIManager.PressNumber`, so a reader can find it in the game.
- Numbers that motivate a change, such as a measured stutter, come with how they were measured.
