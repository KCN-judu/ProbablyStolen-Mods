// Load Breakdown: a development mod that shows where loading a save spends its time. Not for release.
//   Build like tools/modding/LeakProbe.cs (see its header), with 0Harmony added to the references:
//     refs=(); for r in mscorlib netstandard System System.Core Assembly-CSharp UnityEngine UnityEngine.CoreModule 0Harmony; do refs+=("-r:$M/$r.dll"); done
//     "$CSC" -nologo -nostdlib -noconfig -target:library -optimize+ -langversion:latest "${refs[@]}" -out:LoadBreakdown.dll LoadBreakdown.cs
//   Install as "$GAME/Mods/load_breakdown" with a manifest like Leak Probe's (ID load_breakdown, assembly LoadBreakdown.dll,
//   capability reflection-external). Turn off Performance Fixes' "Profile long frames" while measuring.
//   Use only on a copy of a save: timing can break a game method, and a broken load must not be saved over a real slot.
//   Press Continue or load a save. When the button is pressed it attaches timers (this takes a moment, before the load is
//   timed) to the startup methods of the game's MonoBehaviours (Awake, OnEnable, Start; each timed as a whole, not what
//   it calls) and to a checked list of the steps of PlayerStore.LoadGame. Three startup methods are left alone, because
//   timing them broke item registration once. When the first frame after the save load is drawn, Player.log gets
//   "[LoadBreakdown]" lines: the phases, then the methods by their own time (without the timed methods they call), with
//   call counts. Time no timed method accounts for is Unity's own work (reading the scene, layout, drawing). If a timed
//   method threw, the first line says so: that load is not valid and must not be saved.
using System;
using System.Collections.Generic;
using System.Diagnostics;
using System.Reflection;
using System.Reflection.Emit;
using System.Threading;
using HarmonyLib;
using UnityEngine;
using UnityEngine.SceneManagement;
using Debug = UnityEngine.Debug;

namespace LoadBreakdown
{
    public sealed class LoadBreakdownMod : IMod
    {
        static GameObject host;
        internal static Harmony Harmony;

        public void Init(ModManifest manifest) { }

        public void OnEnable()
        {
            if (Harmony != null) return;
            Harmony = new Harmony("dev.load_breakdown");
            Harmony.Patch(typeof(MainMenuUIController).GetMethod("StartNewGameClick", BindingFlags.Instance | BindingFlags.Public | BindingFlags.NonPublic),
                new HarmonyMethod(typeof(Timers).GetMethod("Arm", BindingFlags.Static | BindingFlags.NonPublic)));
            host = new GameObject("LoadBreakdown");
            UnityEngine.Object.DontDestroyOnLoad(host);
            host.hideFlags = HideFlags.HideAndDontSave;
            host.AddComponent<Watcher>();
        }

        public void OnDisable()
        {
            if (Harmony != null) Harmony.UnpatchAll("dev.load_breakdown");
            Harmony = null;
            if (host != null) UnityEngine.Object.Destroy(host);
        }
    }

    public sealed class Watcher : MonoBehaviour
    {
        void Awake() { SceneManager.sceneLoaded += (s, m) => Timers.SceneLoaded(s.name); }
        void Update() { Timers.OnFrame(); }
    }

    static class Timers
    {
        const string Tag = "[LoadBreakdown] ";
        const int MinIlBytes = 24;

        // Timing these broke the game's item registration (ArrayTypeMismatchException in the timed copy), so they stay as
        // they are.
        static readonly string[] leftAlone = { "ItemBehaviourManager.Awake", "EventTriggerManager.Awake", "PriorityTrigger.InitBehaviours" };

        // The steps of PlayerStore.LoadGame, checked by hand.
        static readonly KeyValuePair<Type, string[]>[] steps =
        {
            Pair(typeof(EmporiumEntry), "GetAllItems", "HandleLocale", "LoadDisplayCaseUpgrade", "LoadFixtureUpgrades", "LoadFaucetUpdate"),
            Pair(typeof(EmporiumOption), "ApplySetting"),
            Pair(typeof(KeyBindHelper), "Save"),
            Pair(typeof(LetterboxManager), "Refresh"),
            Pair(typeof(StartOfDayUIManager), "ShowMorningReport"),
            Pair(typeof(PlayerStore), "LoadGame", "DecodeSaveItem", "LoadPower", "AlwayCall", "PreLoadStore"),
            Pair(typeof(SaveFiles), "WithIORetry", "ResolveLoadFile"),
            Pair(typeof(ModHook), "FireOnGameLoadedInit", "FireOnGameLoadedEarly", "FireOnGameLoadedNormal", "FireOnGameLoadedLate"),
            Pair(typeof(StoreService), "HealIntroducedAfterLoad"),
            Pair(typeof(StoreClientData), "HealButcherArrestAfterLoad"),
            Pair(typeof(NetworkUpgrade), "AddMissingAfterLoad"),
            Pair(typeof(StoreReputation), "AddMissingPerksAfterLoad"),
            Pair(typeof(StorePoster), "LoadStorePoster"),
            Pair(typeof(Shotgun), "LoadShotgun"),
            Pair(typeof(StorePC), "RefreshState"),
            Pair(typeof(SaveManager), "DecodeNodes", "DecodeNodesInternal"),
            Pair(typeof(MachineHelper), "LoadUpgrade", "OnLoad"),
            Pair(typeof(SpriteHelper), "UpdateWaterContainerSprite"),
            Pair(typeof(GeneralHelper), "LoadLockItem", "LoadNonOwnedToolTag", "LoadImportantStoryItemTag", "LoadHazardousWasteTag", "SetItemOwned"),
            Pair(typeof(PlantTraitList), "LoadEdibleProduce", "LoadTasteFeature"),
            Pair(typeof(ScavHelper), "LoadScavTokenTag"),
            Pair(typeof(LockHelper), "LoadLockedContainer"),
            Pair(typeof(MachineBrokenHelper), "LoadBrokenMachine"),
            Pair(typeof(MachineTurboBoosterAdv), "LoadTurboBoostEligibleTag"),
            Pair(typeof(CurrentConverterHelper), "OnLoad"),
            Pair(typeof(GraphUtils), "DestroyIfUnplaced"),
            Pair(typeof(GameItem), "ValidateShapeState", "ModifyTag", "EnableTag", "DisableTag", "ComputeModifiedShapeState", "Destroy", "RemoveAllFeature", "SetSprite", "SetSpriteAndShape"),
            Pair(typeof(GameItemElement), "Validate", "ToggleFakeBackground", "ToggleBackground"),
            Pair(typeof(GameGridInventory), "Validate", "UncheckedAccept", "Expel"),
            Pair(typeof(GameSlotInventory), "Validate", "UncheckedAccept", "Expel"),
            Pair(typeof(PermitHelper), "ReapplyPermits", "OnNewItemCreated"),
            Pair(typeof(EmporiumAnalytics), "TrackLoadGame"),
            Pair(typeof(DirectoryMaster), "Item", "CharacterItem"),
            Pair(typeof(ItemDirectory), "CreateEmptyItem"),
            Pair(typeof(CharacterItemDirectory), "CreateEmptyCharacterItem"),
            Pair(typeof(TagSystem), "Clone"),
            Pair(typeof(TreeNodeRender), "InstantiateAsRoot", "SetParent", "ApplyLocaleFont", "InitEventHandler"),
            Pair(typeof(RenderHandler), "LoadFromAtlas"),
            Pair(typeof(PixelWindow), "Validate", "AddParent"),
            Pair(typeof(StorageExpansionHelper), "RestoreTabs"),
            Pair(typeof(MachineryPanel), "Validate"),
            Pair(typeof(MachineryPanelRow), "Validate"),
            Pair(typeof(MachineryIntake), "Validate"),
            Pair(typeof(MachineryStack), "Validate"),
        };

        static KeyValuePair<Type, string[]> Pair(Type t, params string[] methods) { return new KeyValuePair<Type, string[]>(t, methods); }

        static int failures;
        static string firstFailure;
        const BindingFlags All = BindingFlags.Instance | BindingFlags.Static | BindingFlags.Public | BindingFlags.NonPublic | BindingFlags.DeclaredOnly;

        static bool patched, armed;
        static readonly Dictionary<MethodBase, int> index = new Dictionary<MethodBase, int>();
        static readonly List<string> names = new List<string>();
        static long[] own = new long[0], total = new long[0], calls = new long[0];
        struct Frame { public int Id; public long Start, Children; }
        static readonly Stack<Frame> stack = new Stack<Frame>();
        static Thread main;
        static long clickAt, sceneAt, loadStartAt, loadEndAt, topLevel;
        static int loadEndFrame = -1;

        // The start button was pressed: attach the timers once, then time this trip into the store.
        static void Arm()
        {
            try
            {
                if (!patched) Attach();
                patched = true;
            }
            catch (Exception e) { Debug.LogWarning(Tag + "could not attach: " + e); return; }
            Array.Clear(own, 0, own.Length); Array.Clear(total, 0, total.Length); Array.Clear(calls, 0, calls.Length);
            movers.Clear();
            moves = movesFromTemp = 0;
            failures = 0;
            firstFailure = null;
            stack.Clear();
            topLevel = 0;
            sceneAt = loadStartAt = loadEndAt = 0;
            loadEndFrame = -1;
            main = Thread.CurrentThread;
            clickAt = Stopwatch.GetTimestamp();
            armed = true;
        }

        static bool Allowed(Type t)
        {
            if (t == null || t.Assembly.GetName().Name != "Assembly-CSharp") return false;
            for (var x = t; x != null; x = x.DeclaringType)
            {
                var n = x.Name;
                if (n.StartsWith("Mod") || n.StartsWith("Steam") || n.StartsWith("Workshop") || n.Contains("Trust")) return false;
            }
            return true;
        }

        static bool Worth(MethodBase m)
        {
            if (m == null || m.IsAbstract || m.ContainsGenericParameters || !Allowed(m.DeclaringType)) return false;
            MethodBody body;
            try { body = m.GetMethodBody(); } catch { return false; }
            return body != null && body.GetILAsByteArray().Length >= MinIlBytes;
        }

        static void Attach()
        {
            var clock = Stopwatch.StartNew();
            var game = typeof(PlayerStore).Assembly;
            Type[] types;
            try { types = game.GetTypes(); } catch (ReflectionTypeLoadException e) { types = e.Types; }

            var chosen = new HashSet<MethodBase>();
            Action<MethodBase> add = m =>
            {
                if (!Worth(m)) return;
                if (Array.IndexOf(leftAlone, m.DeclaringType.Name + "." + m.Name) >= 0) return;
                chosen.Add(m);
            };
            foreach (var t in types)
            {
                if (t == null || !Allowed(t) || !typeof(MonoBehaviour).IsAssignableFrom(t)) continue;
                foreach (var m in t.GetMethods(All))
                    if (m.Name == "Awake" || m.Name == "OnEnable" || m.Name == "Start") add(m);
            }
            foreach (var step in steps)
            {
                foreach (var m in step.Key.GetMethods(All))
                    if (Array.IndexOf(step.Value, m.Name) >= 0 && !m.IsGenericMethodDefinition) add(m);
                foreach (var c in step.Key.GetConstructors(BindingFlags.Instance | BindingFlags.Public | BindingFlags.NonPublic))
                    if (step.Key == typeof(GameItemElement) || step.Key == typeof(TagSystem)) add(c);
            }

            var pre = new HarmonyMethod(typeof(Timers).GetMethod("Pre", BindingFlags.Static | BindingFlags.NonPublic));
            var post = new HarmonyMethod(typeof(Timers).GetMethod("Post", BindingFlags.Static | BindingFlags.NonPublic));
            int failed = 0;
            foreach (var m in chosen)
            {
                try
                {
                    index[m] = names.Count;
                    names.Add(m.DeclaringType.FullName + "." + m.Name);
                    LoadBreakdownMod.Harmony.Patch(m, pre, null, null, post);
                }
                catch { failed++; }
            }
            own = new long[names.Count]; total = new long[names.Count]; calls = new long[names.Count];
            LoadBreakdownMod.Harmony.Patch(typeof(TreeNodeRender).GetMethod("SetParent", BindingFlags.Instance | BindingFlags.Public, null, new[] { typeof(TreeNodeRender), typeof(bool) }, null),
                new HarmonyMethod(typeof(Timers).GetMethod("MovePre", BindingFlags.Static | BindingFlags.NonPublic)));
            Debug.Log(Tag + "timing " + (chosen.Count - failed) + " methods (" + failed + " could not be timed); attaching took " +
                clock.ElapsedMilliseconds + " ms, before the load is timed");
        }

        static void Pre(MethodBase __originalMethod)
        {
            if (!armed || Thread.CurrentThread != main) return;
            int id;
            if (!index.TryGetValue(__originalMethod, out id)) return;
            if (__originalMethod.Name == "LoadGame" && loadStartAt == 0) loadStartAt = Stopwatch.GetTimestamp();
            stack.Push(new Frame { Id = id, Start = Stopwatch.GetTimestamp() });
        }

        // A finalizer, so a method that throws still closes its timer.
        static Exception Post(MethodBase __originalMethod, Exception __exception)
        {
            if (!armed || Thread.CurrentThread != main) return __exception;
            int id;
            if (__exception != null && index.ContainsKey(__originalMethod))
            {
                if (failures++ == 0) firstFailure = __originalMethod.DeclaringType.Name + "." + __originalMethod.Name + ": " + __exception.GetType().Name;
            }
            if (!index.TryGetValue(__originalMethod, out id) || stack.Count == 0 || stack.Peek().Id != id) return __exception;
            var f = stack.Pop();
            long t = Stopwatch.GetTimestamp() - f.Start;
            total[id] += t; own[id] += t - f.Children; calls[id]++;
            if (stack.Count > 0) { var p = stack.Pop(); p.Children += t; stack.Push(p); }
            else topLevel += t;
            if (__originalMethod.Name == "LoadGame" && loadEndAt == 0) { loadEndAt = Stopwatch.GetTimestamp(); loadEndFrame = Time.frameCount; }
            return __exception;
        }

        // Real moves (the parent changes), counted by the game method that asked for them. Reading the call stack costs
        // time, so the timings of a run with this are higher; the counts are what matter.
        static readonly Dictionary<string, int> movers = new Dictionary<string, int>();
        static int moves, movesFromTemp;

        static void MovePre(TreeNodeRender __instance, TreeNodeRender parent)
        {
            if (!armed || Thread.CurrentThread != main || parent == null || __instance == null) return;
            var from = __instance.rectTransform != null ? __instance.rectTransform.parent : null;
            if (from == parent.rectTransform) return;
            moves++;
            var temp = RenderHandler.current != null ? RenderHandler.current.tempRoot : null;
            if (temp != null && from == temp.rectTransform) movesFromTemp++;
            string caller = "?";
            var trace = new StackTrace(1, false);
            for (int i = 0; i < trace.FrameCount; i++)
            {
                var m = trace.GetFrame(i).GetMethod();
                if (m == null || m.DeclaringType == null || m.DeclaringType == typeof(TreeNodeRender) || m.DeclaringType == typeof(Timers)) continue;
                string name = m.DeclaringType.FullName + "." + m.Name;
                // A timed (patched) game method shows as MonoMod.Utils.DynamicMethodDefinition.<Type>.<Method>_PatchN.
                if (name.StartsWith("MonoMod."))
                {
                    name = m.Name;
                    int cut = name.LastIndexOf("_Patch");
                    if (cut > 0) name = name.Substring(0, cut);
                }
                if (name.StartsWith("TreeNodeRender.")) continue;
                caller = name;
                break;
            }
            int n;
            movers.TryGetValue(caller, out n);
            movers[caller] = n + 1;
        }

        public static void SceneLoaded(string scene)
        {
            if (armed && scene == "InventoryScene" && sceneAt == 0) sceneAt = Stopwatch.GetTimestamp();
        }

        public static void OnFrame()
        {
            if (!armed || loadEndFrame < 0 || Time.frameCount <= loadEndFrame) return;
            armed = false;
            Report(Stopwatch.GetTimestamp());
        }

        static double Ms(long ticks) { return ticks * 1000.0 / Stopwatch.Frequency; }

        static void Report(long end)
        {
            if (failures > 0)
                Debug.LogWarning(Tag + "WARNING: " + failures + " timed call(s) threw (first: " + firstFailure + "). This load is not valid: do not save it.");
            Debug.Log(Tag + "click to first frame " + Ms(end - clickAt).ToString("0") + " ms: to scene set up " + Ms(sceneAt - clickAt).ToString("0") +
                " ms, then to save load start " + Ms(loadStartAt - sceneAt).ToString("0") + " ms, save load " + Ms(loadEndAt - loadStartAt).ToString("0") +
                " ms, then to first frame " + Ms(end - loadEndAt).ToString("0") + " ms. Timed methods account for " + Ms(topLevel).ToString("0") +
                " ms; the other " + Ms(end - clickAt - topLevel).ToString("0") + " ms is Unity's own work and the fade.");
            var order = new List<int>();
            for (int i = 0; i < names.Count; i++) if (calls[i] > 0) order.Add(i);
            order.Sort((a, b) => own[b].CompareTo(own[a]));
            long totalCalls = 0;
            foreach (var i in order) totalCalls += calls[i];
            Debug.Log(Tag + order.Count + " methods ran, " + totalCalls + " timed calls (timing adds roughly " +
                (totalCalls * 0.6 / 1000.0).ToString("0") + " ms of its own). Slowest by own time:");
            var byMover = new List<KeyValuePair<string, int>>(movers);
            byMover.Sort((x, y) => y.Value.CompareTo(x.Value));
            Debug.Log(Tag + moves + " real node moves (" + movesFromTemp + " out of the shared temporary root), by the game method that asked:");
            for (int k = 0; k < byMover.Count && k < 25; k++) Debug.Log(Tag + "  " + byMover[k].Value + "  " + byMover[k].Key);
            for (int k = 0; k < order.Count && k < 60; k++)
            {
                int i = order[k];
                Debug.Log(Tag + "  " + Ms(own[i]).ToString("0.0") + " ms own, " + Ms(total[i]).ToString("0.0") + " ms total, x" + calls[i] + "  " + names[i]);
            }
        }
    }
}
