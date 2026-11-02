# Translation

English pages are the only source of the documentation. Every other language is a gettext catalog of translated messages, and a page in Chinese is generated from the English page and the catalog when the site is built.

This has three consequences:

- A language can never fall out of structure with English. Pages, headings, code and links come from one source.
- An untranslated or outdated passage is shown in English instead of disappearing or being wrong. The page says how much of it is translated.
- The site knows the coverage of every page and every mod, and shows it in the library.

## Messages

`lunadoc` splits every page into messages: headings, paragraphs, list items, table cells, and the `title` and `description` front matter keys. Code blocks and raw HTML are never messages; they appear in every language exactly as written in English.

A paragraph that wraps over several lines is one message. Re-wrapping English text does not change its message, so it does not invalidate translations.

## The workflow

1. Edit the English pages in `doc/manual`.
2. Run `npm run update-po` in the collection. It regenerates `doc/locale/manual.pot` of every mod and merges it into every `manual.po`.
3. Commit the pages and the catalogs together.

`update` behaves like GNU `msgmerge`:

- A message whose English text is unchanged keeps its translation.
- A message whose English text changed takes the translation of the most similar old message and is marked `fuzzy`. The previous English text is kept in a `#| msgid` comment so a translator can see what changed.
- A translation whose message disappeared is kept as an obsolete entry (`#~`) at the end of the catalog, where `update` can recover it later.

Fuzzy translations are not shown on the site. They count as untranslated until a translator reviews them and removes the `fuzzy` flag.

## Translating

Open `doc/locale/<locale>/LC_MESSAGES/manual.po` in a text editor or a gettext editor such as Poedit, and fill in `msgstr` for each `msgid`:

```po
#: manual/index.md:12
msgid "The first window opens or closes at once, so the key answers immediately."
msgstr "第一个窗口立即打开或关闭，按键马上有反应。"
```

When translating:

- Keep inline code and link destinations exactly as in English. Translate link text.
- Keep Markdown markup: emphasis, inline code and links must still be balanced.
- Keep a GitHub alert marker such as `[!NOTE]` at the start of the message.
- Do not translate identifiers, even in prose. Use the game's own Chinese names for items, places and people.
- Leave `msgstr` empty rather than guessing. An empty message falls back to English.

Check the result with `npm run status` and preview it with the site.

## Locales

Locale names follow gettext: `zh_CN` for Simplified Chinese. They appear in `conf.json`, in the catalog paths and in `config/locales.json` of the site, which also gives each locale its URL segment and display name. Adding a language to the site means adding it there; adding it to a repository means listing it in `conf.json` and running `update`.
