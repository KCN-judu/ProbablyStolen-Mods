# Writing and markup

Pages are GitHub-flavoured Markdown. Everything described here also renders on GitHub, so a page read in the repository and the same page on this site say the same thing.

## Style

- Write for a player first: what happens in the game, in the game's own words (customer, counter, storage bay, Workshop).
- Short sentences, one fact each. Active voice: "the mod skips the ringing", not "the ringing is skipped".
- Say what something does, not that it is easy, simple or powerful.

## Code

Fence shell commands with `sh` or `bash` and C# with `csharp`. Keep examples small and make sure they work.

```bash
./build.sh --install
```

## Tables

Use a table for options and other lists with the same columns. Keep each cell to one sentence; every cell is translated on its own.

## Notes

GitHub alerts render as notes:

```markdown
> [!NOTE]
> Mods load when the game starts, so restart after enabling one.
```

## Images

Put images in `doc/attachments/` and link them relatively, with alt text that says what the image shows:

```markdown
![The four outline styles](../attachments/outline-styles.png)
```

Pixel art is shown with nearest-neighbour scaling, so draw it at a small size and let the site scale it.
