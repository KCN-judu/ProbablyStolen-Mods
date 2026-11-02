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

They compile with the C# compiler that ships with Windows against the `Unity.Burst.Cecil.dll` the game provides.

## Publishing to the Workshop

`scripts/package.sh` collects the built mods into `dist/packages/`, each with its cover rendered fresh from `design/covers.py`. A cover shows the version in the mod's `manifest.xml`, and every Workshop upload replaces the preview image, so the Workshop page always shows the version it ships. `python design/covers.py design/out --checkouts <folder> --sync` renders the covers from working copies in that folder, for versions not yet published, and writes each one into the mod's `preview.png` and `doc/attachments/cover.png`. `scripts/workshop.py` then writes a SteamCMD upload file for each of them to `dist/workshop/`, using the item ids and titles in `config/workshop.json`. Upload files leave the visibility alone, so an update never hides or publishes an item.

SteamCMD cannot set tags. `scripts/workshop-tags.sh` sets the tags listed in `config/workshop.json` through the game's own Steamworks library. It needs the Steam client running and logged in as the owner of the items.

The mods are also gathered in one Workshop collection, Quality of Life. `scripts/workshop-collection.sh` creates or updates it through the same Steamworks library: its title, tags and mods in the order of the `collection` entry of `config/workshop.json`, its text from `config/collection-description.txt` and its cover from `design/collection_cover.py`. A new mod is added by listing it there and running the script again. The visibility changes only when one is given (`public`, `friends` or `private`).
