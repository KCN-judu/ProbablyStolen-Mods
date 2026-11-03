// Leak Probe: a development mod that lists what still holds the store after leaving it. Not for release.
//   Build (Git Bash; GAME and CSC as in each mod's build.sh), from the collection root:
//     M="$GAME/Probably Stolen_Data/Managed"; W="${TEMP:-/tmp}/lp_build"; mkdir -p "$W/leak_probe"
//     cp tools/modding/LeakProbe.cs "$W/"; cd "$W"
//     refs=(); for r in mscorlib netstandard System System.Core Assembly-CSharp UnityEngine UnityEngine.CoreModule; do refs+=("-r:$M/$r.dll"); done
//     "$CSC" -nologo -nostdlib -noconfig -target:library -optimize+ -langversion:latest "${refs[@]}" -out:LeakProbe.dll LeakProbe.cs
//   (Already installed on this computer as "$GAME/Mods/leak_probe".)
//   Install: copy LeakProbe.dll and the manifest below into "$GAME/Mods/leak_probe", enable "Leak Probe
//   (development)" in the Mods menu and approve its capability (reflection-external), restart.
//   Use: load a save, go back to the main menu. Player.log gets "[LeakProbe] left the store ..." with the managed
//   memory and one line per field still holding destroyed store objects, largest first. A mod is clean when none of
//   its fields is listed.
//   manifest.xml:
//     <Manifest><ID>leak_probe</ID><Name>Leak Probe (development)</Name><Author>KCN-judu</Author>
//       <ModVersion>0.1.0</ModVersion><Description>Development tool. Not meant for play.</Description>
//       <GameVersions><Version>0.46D</Version></GameVersions><Prerequisites /><Assemblies>
//       <Assembly>LeakProbe.dll</Assembly></Assemblies><Capabilities><Capability>reflection-external</Capability>
//       </Capabilities></Manifest>
using System;
using System.Collections;
using System.Collections.Generic;
using System.Reflection;
using UnityEngine;
using UnityEngine.SceneManagement;

namespace LeakProbe
{
    // Development tool: after leaving the store for another scene, forces a full collection and lists what still
    // holds objects of the store that was left: static fields of the game and of every mod, the instance fields of
    // objects that survive scene changes, and one level further into plain objects those point to. An object counts
    // as left behind when it is a destroyed Unity object, an item whose UI is destroyed, or an inventory or window
    // whose node is destroyed.
    public sealed class LeakProbeMod : IMod
    {
        static GameObject host;

        public void Init(ModManifest manifest) { }

        public void OnEnable()
        {
            if (host != null) return;
            host = new GameObject("LeakProbe");
            UnityEngine.Object.DontDestroyOnLoad(host);
            host.hideFlags = HideFlags.HideAndDontSave;
            host.AddComponent<Runner>();
        }

        public void OnDisable()
        {
            if (host != null) UnityEngine.Object.Destroy(host);
            host = null;
        }
    }

    public sealed class Runner : MonoBehaviour
    {
        const string Store = "InventoryScene";
        const BindingFlags Statics = BindingFlags.Static | BindingFlags.Public | BindingFlags.NonPublic | BindingFlags.DeclaredOnly;
        const BindingFlags Instances = BindingFlags.Instance | BindingFlags.Public | BindingFlags.NonPublic;
        const int MaxElements = 200000;

        bool wasInStore;
        long storeMemory;

        int visits;

        void Awake() { SceneManager.sceneLoaded += OnLoaded; }

        // The scene the game starts in is already loaded when mods start, so measure it here.
        void Start() { StartCoroutine(Baseline(SceneManager.GetActiveScene().name)); }
        void OnDestroy() { SceneManager.sceneLoaded -= OnLoaded; }

        void OnLoaded(Scene scene, LoadSceneMode mode)
        {
            if (mode != LoadSceneMode.Single) return;
            if (scene.name == Store)
            {
                wasInStore = true;
                StartCoroutine(NoteStoreMemory());
                return;
            }
            if (!wasInStore) return;
            wasInStore = false;
            StartCoroutine(Check(scene.name));
        }

        // The same measurement before the store was ever entered, to compare with.
        IEnumerator Baseline(string sceneName)
        {
            for (int i = 0; i < 30; i++) yield return null;
            GC.Collect();
            GC.WaitForPendingFinalizers();
            GC.Collect();
            Debug.Log("[LeakProbe] '" + sceneName + "' before entering the store: managed memory " + Mb(GC.GetTotalMemory(true)) +
                " after a full collection");
        }

        // In the store, after a full collection: on a second visit, what the first store still takes shows as growth.
        IEnumerator NoteStoreMemory()
        {
            for (int i = 0; i < 30; i++) yield return null;
            storeMemory = GC.GetTotalMemory(false);
            GC.Collect();
            GC.WaitForPendingFinalizers();
            GC.Collect();
            visits++;
            Debug.Log("[LeakProbe] in the store, visit " + visits + ": managed memory " + Mb(GC.GetTotalMemory(true)) + " after a full collection");
        }

        IEnumerator Check(string sceneName)
        {
            yield return null;
            yield return null;
            GC.Collect();
            GC.WaitForPendingFinalizers();
            GC.Collect();
            long after = GC.GetTotalMemory(true);
            var holders = new List<KeyValuePair<string, int>>();
            var seen = new HashSet<object>(new RefEq());
            int fieldsChecked = 0;
            try
            {
                foreach (var asm in AppDomain.CurrentDomain.GetAssemblies())
                {
                    if (!Interesting(asm)) continue;
                    Type[] types;
                    try { types = asm.GetTypes(); } catch (ReflectionTypeLoadException e) { types = e.Types; }
                    foreach (var t in types)
                    {
                        if (t == null || t.ContainsGenericParameters) continue;
                        FieldInfo[] fields;
                        try { fields = t.GetFields(Statics); } catch { continue; }
                        foreach (var f in fields)
                        {
                            if (f.IsLiteral || f.FieldType.IsValueType) continue;
                            object v;
                            try { v = f.GetValue(null); } catch { continue; }
                            if (v == null) continue;
                            fieldsChecked++;
                            Inspect(t.FullName + "." + f.Name, v, 2, holders, seen);
                        }
                    }
                }
                foreach (var b in Resources.FindObjectsOfTypeAll<MonoBehaviour>())
                {
                    if (b == null || b.gameObject.scene.name != "DontDestroyOnLoad") continue;
                    if (!Interesting(b.GetType().Assembly)) continue;
                    foreach (var f in b.GetType().GetFields(Instances))
                    {
                        if (f.FieldType.IsValueType) continue;
                        object v;
                        try { v = f.GetValue(b); } catch { continue; }
                        if (v == null) continue;
                        fieldsChecked++;
                        Inspect("[kept " + b.GetType().FullName + "]." + f.Name, v, 2, holders, seen);
                    }
                }
            }
            catch (Exception e) { Debug.LogWarning("[LeakProbe] scan stopped: " + e); }

            holders.Sort((x, y) => y.Value.CompareTo(x.Value));
            Debug.Log("[LeakProbe] left the store for '" + sceneName + "': managed memory " + Mb(storeMemory) + " in the store, " +
                Mb(after) + " after a full collection; " + fieldsChecked + " fields checked; " + holders.Count + " holder(s) of left-behind objects");
            for (int i = 0; i < holders.Count; i++)
                Debug.Log("[LeakProbe]   " + holders[i].Value + "  " + holders[i].Key);
        }

        static string Mb(long bytes) { return (bytes / (1024.0 * 1024.0)).ToString("0") + " MB"; }

        static bool Interesting(Assembly asm)
        {
            var n = asm.GetName().Name;
            return !(n.StartsWith("System") || n.StartsWith("Unity") || n.StartsWith("mscorlib") || n.StartsWith("Mono") ||
                n.StartsWith("netstandard") || n.StartsWith("0Harmony") || n == "LeakProbe" || n.StartsWith("DOTween") ||
                n.StartsWith("Newtonsoft") || n.StartsWith("TextMeshPro") || n.StartsWith("Febucci") || n.StartsWith("QFSW"));
        }

        // Counts left-behind objects in v (and in its elements, and, depth permitting, in the fields of plain objects
        // from the game or a mod), and records path when there are any.
        static void Inspect(string path, object v, int depth, List<KeyValuePair<string, int>> holders, HashSet<object> seen)
        {
            int direct = Count(v);
            if (direct > 0) { holders.Add(new KeyValuePair<string, int>(path + "  (" + Describe(v) + ")", direct)); return; }
            if (depth <= 0 || v is UnityEngine.Object || v is string || v is Delegate || v is IEnumerable) return;
            if (!Interesting(v.GetType().Assembly) || !seen.Add(v)) return;
            foreach (var f in v.GetType().GetFields(Instances))
            {
                if (f.FieldType.IsValueType) continue;
                object w;
                try { w = f.GetValue(v); } catch { continue; }
                if (w != null) Inspect(path + "." + f.Name, w, depth - 1, holders, seen);
            }
        }

        static int Count(object v)
        {
            if (LeftBehind(v)) return 1;
            var d = v as Delegate;
            if (d != null)
            {
                int n = 0;
                foreach (var part in d.GetInvocationList()) if (part.Target != null && LeftBehind(part.Target)) n++;
                return n;
            }
            if (v is string) return 0;
            var dict = v as IDictionary;
            if (dict != null)
            {
                int n = 0, i = 0;
                foreach (DictionaryEntry e in dict)
                {
                    if (LeftBehind(e.Key) || (e.Value != null && LeftBehind(e.Value))) n++;
                    if (++i > MaxElements) break;
                }
                return n;
            }
            var list = v as IEnumerable;
            if (list != null)
            {
                int n = 0, i = 0;
                try
                {
                    foreach (var e in list)
                    {
                        if (e != null && LeftBehind(e)) n++;
                        if (++i > MaxElements) break;
                    }
                }
                catch { }
                return n;
            }
            return 0;
        }

        static bool LeftBehind(object o)
        {
            var u = o as UnityEngine.Object;
            if (!ReferenceEquals(u, null)) return u == null;
            var element = o as GameItemElement;
            if (element != null) { try { return element.IsDestroyed(); } catch { return false; } }
            var pixel = o as PixelElement;
            if (pixel != null) { try { return pixel.handler == null; } catch { return false; } }
            return false;
        }

        static string Describe(object v)
        {
            var t = v.GetType();
            var c = v as ICollection;
            return t.Name + (c != null ? ", " + c.Count + " entries" : "");
        }

        sealed class RefEq : IEqualityComparer<object>
        {
            public new bool Equals(object a, object b) { return ReferenceEquals(a, b); }
            public int GetHashCode(object o) { return System.Runtime.CompilerServices.RuntimeHelpers.GetHashCode(o); }
        }
    }
}
