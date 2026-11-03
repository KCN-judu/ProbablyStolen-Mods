# Code standard

These rules apply to the code of every mod in the collection. How to build a mod and check it with the game's scanner is on the [Modding tools](modding_tools.md) page.

## Nothing kept after leaving the store

A store's items, inventories, windows and managers all point at each other. One reference to any of them that outlives the store keeps the whole store in memory: the next load in the same session starts with the old store still on the managed heap, and every load after it gets slower.

**No mod keeps store objects after the player leaves the store.** Store objects are `GameItem`, `GameItemElement`, `GameInventory`, `PixelWindow`, `TreeNodeRender`, `StoreClient`, the store's managers and any Unity object of the store's scene. A mod must not keep them in:

- static fields, static collections or caches;
- objects that outlive the scene, such as one marked with `DontDestroyOnLoad`;
- event subscriptions, or delegates whose target is a store object.

**Release them when the store is left.** The store is the scene `InventoryScene`. Subscribe to `SceneManager.sceneLoaded` and, when a scene other than `InventoryScene` is loaded in single mode (the main menu is `EmporiumMenu`), clear every such field, cache and subscription. Where that does not fit, key a cache with a `ConditionalWeakTable` or remove its destroyed entries. Nothing may change while the player is in the store. The decision of when to release goes in a `.Pure.cs` file with a headless test, like any other decision.

**Check with the Leak Probe.** Every new or changed mod is checked with the [Leak Probe](modding_tools.md#leak-probe): load a save, go back to the main menu and read the `[LeakProbe]` lines in `Player.log`. None of them may name a field of the mod.
