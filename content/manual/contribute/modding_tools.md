# Modding tools

The collection repository keeps the tools shared by every mod.

## Building

Each mod builds with its own `build.sh` against the game's assemblies; see the mod's Building page. From the collection, `scripts/build-all.sh` builds every mod, and `scripts/package.sh` collects the built folders into `dist/packages/` with a zip of each.

## The scanner check

The game scans every mod DLL before enabling it and asks the player for permission when a mod uses files, the network, reflection over unknown types or similar capabilities. Every mod here declares none.

`tools/modding/ScanTest.cs` runs the game's own scanner, `ModScanner.Scan`, on a built mod outside the game:

```sh
scripts/scan.sh mods/quick-call/out/quick_call
```

It prints the capabilities found and any hard flags, such as an attempt to patch the game's mod loader. A mod is ready when it prints `capabilities: none` and no `HARD` line.

## Inspecting the game

Small Mono.Cecil programs in `tools/modding/` read the game's `Assembly-CSharp.dll`:

| Tool | Use |
| --- | --- |
| `Inspect.cs` | Types, fields and methods matching a pattern, with the IL of chosen methods |
| `Find.cs` | Every method whose IL matches an instruction pattern, such as all callers of a method |
| `Ctx.cs` | Like Find, with the instructions that follow each match |
| `Consts.cs` | The values of constant fields |
| `StaticHolders.cs` | The static fields of the game or of a mod that can keep the store in memory, and whether anything clears them |
| `Singletons.cs` | The game's managers that point at themselves from a static field, which a mod that releases the store clears |
| `LocaleTraps.cs` | Which of the methods a mod patches would freeze localized text when patched before the player's language is applied |

They compile with the C# compiler that ships with Windows against the `Unity.Burst.Cecil.dll` the game provides. Usage is at the top of each file.

For reading a lot of the game's code, `Inspect.exe Assembly-CSharp.dll all.txt "." "."` writes every type with the IL of every method to one file, and `tools/modding/il-method.sh all.txt PixelWindow Show` prints one method from it.

## Leak Probe

`tools/modding/LeakProbe.cs` is a development mod that checks the rule in [Code standard](code_standard.md): nothing may keep the store after the player leaves it. It is never released.

After a scene other than the store replaces the store, it forces a full collection and writes to `Player.log` the managed memory and one `[LeakProbe]` line per field that still holds objects of the store just left, largest first. It looks at the static fields of the game and of every mod, at the objects that survive scene changes, and one level into the plain objects they point to.

1. Build it with the commands at the top of `LeakProbe.cs` and copy `LeakProbe.dll` with the manifest given there into the game's `Mods/leak_probe` folder.
2. Enable Leak Probe (development) in the Mods menu, approve its capability (reflection over the game's types) and restart the game.
3. Load a save, then go back to the main menu.
4. Read the `[LeakProbe]` lines in `Player.log`. A mod passes when none of them names one of its fields.

Disable the probe again before playing: it is meant for checks only.

## Load Breakdown

`tools/modding/LoadBreakdown.cs` is a development mod that shows where loading a save spends its time. When Continue or a save is chosen, it times the startup methods of the game's MonoBehaviours and a checked list of the steps of the load, and when the first frame is drawn it writes to `Player.log` the phases, the methods by their own time with call counts, and which game methods move UI nodes. Build and install it as described at the top of the file.

Use it only on a copy of a save: timing can break a game method, and a broken load must not be saved over a real slot. Timing adds its own cost, so compare totals only with it off; Performance Fixes writes a load timeline on every load for that.

## Releasing

`scripts/release-check.sh <mod folder>` runs every check before a release and lists what is not ready: the changelog entry for the version, the tests and the build, the scanner (no capability, no `HARD` line), the documentation check and translation, the Workshop text (under Steam's limit of 8,000 bytes and starting with What's new for this version), the cover of this version in `preview.png` and the documentation, and a clean working copy without a tag of this version yet.

`python design/covers.py design/out --checkouts <folder> --sync --only <id>` renders the covers and writes only that mod's into its working copy.

After publishing, `python scripts/workshop-status.py` checks every Workshop item against its latest release: updated after the version was set, and showing the cover of that version. It saves the previews to `dist/workshop-status/`.

## Comparison videos

`scripts/media.py` prepares recordings for release pages. `cut` keeps time ranges of a video, to shorten a cover or a title card. `gif` makes a GIF under a size budget (10 MB for Discord without Nitro) while keeping the frame rate, so the stutters a comparison shows stay visible: it lowers the colours first and the width last. The title slides, the OFF and ON labels and the pixel font of such videos come from `design/` (see `design/DESIGN.md`).

## Publishing to the Workshop

`scripts/package.sh` collects the built mods into `dist/packages/`, each with its cover rendered fresh from `design/covers.py`. A cover shows the version in the mod's `manifest.xml`, and every Workshop upload replaces the preview image, so the Workshop page always shows the version it ships. `python design/covers.py design/out --checkouts <folder> --sync` renders the covers from working copies in that folder, for versions not yet published, and writes each one into the mod's `preview.png` and `doc/attachments/cover.png`. `scripts/workshop.py` then writes a SteamCMD upload file for each of them to `dist/workshop/`, using the item ids and titles in `config/workshop.json`; `--only <slug>` writes only the named mods. It stops when a description is over Steam's limit of 8,000 bytes, which SteamCMD would otherwise reject only after uploading the content. Upload files leave the visibility alone, so an update never hides or publishes an item.

SteamCMD cannot set tags. `scripts/workshop-tags.sh` sets the tags listed in `config/workshop.json` through the game's own Steamworks library. It needs the Steam client running and logged in as the owner of the items.

The mods are also gathered in one Workshop collection, Quality of Life. `scripts/workshop-collection.sh` creates or updates it through the same Steamworks library: its title, tags and mods in the order of the `collection` entry of `config/workshop.json`, its text from `config/collection-description.txt` and its cover from `design/collection_cover.py`. A new mod is added by listing it there and running the script again. The visibility changes only when one is given (`public`, `friends` or `private`).
