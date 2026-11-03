// Usage: StaticHolders.exe <Assembly-CSharp.dll> <mod.dll>...  - static fields that can keep the store in memory
//
// For each assembly, lists the static fields whose type can hold the store's objects (items, inventories, windows,
// UI nodes, customers, the store itself, also inside lists, dictionaries and arrays) or a delegate, and how the code
// treats them outside static constructors: plain writes, adds (Add, Push, Enqueue, indexer, Combine...) and clears
// (null, a new collection, Clear, Remove...). A field that is added to and never cleared is marked
// GROWS-NEVER-CLEARED: it keeps everything it was given, including a store that was left. A starting point for the
// rule in the code standard; the Leak Probe confirms in the game what is really kept.
using System;
using System.Collections.Generic;
using System.IO;
using System.Linq;
using Mono.Cecil;
using Mono.Cecil.Cil;

class StaticHolders
{
    static readonly string[] StoreTypes =
    {
        "GameItem", "GameItemElement", "GameInventory", "GameGridInventory", "GameSlotInventory", "GameGridScrollableInventory",
        "PixelWindow", "PixelElement", "GraphNodeStorage", "TreeNodeRender", "StoreClient", "PlayerStore", "GameCharacterItem",
        "SlotMarker", "ItemFeature", "TagSystem",
    };
    static readonly string[] Adds = { "Add", "AddRange", "Push", "Enqueue", "set_Item", "Combine", "Insert" };
    static readonly string[] Clears = { "Clear", "Remove", "RemoveAt", "RemoveAll", "RemoveWhere", "Dequeue", "Pop" };

    static bool Holds(TypeReference t)
    {
        if (t == null) return false;
        if (StoreTypes.Contains(t.Name)) return true;
        var generic = t as GenericInstanceType;
        if (generic != null) return generic.GenericArguments.Any(Holds);
        var array = t as ArrayType;
        return array != null && Holds(array.ElementType);
    }

    static bool IsDelegate(TypeReference t)
    {
        try
        {
            var d = t.Resolve();
            return d != null && d.BaseType != null && d.BaseType.FullName == "System.MulticastDelegate";
        }
        catch { return false; }
    }

    static string Describe(FieldDefinition f)
    {
        var generic = f.FieldType as GenericInstanceType;
        var type = generic != null ? f.FieldType.Name + "<" + string.Join(",", generic.GenericArguments.Select(g => g.Name)) + ">" : f.FieldType.Name;
        return f.DeclaringType.FullName + "::" + f.Name + "  [" + type + "]";
    }

    static void Main(string[] a)
    {
        var res = new DefaultAssemblyResolver();
        res.AddSearchDirectory(Path.GetDirectoryName(Path.GetFullPath(a[0])));
        foreach (var path in a)
        {
            AssemblyDefinition asm;
            try { asm = AssemblyDefinition.ReadAssembly(path, new ReaderParameters { AssemblyResolver = res }); }
            catch (Exception e) { Console.WriteLine("=== " + path + ": cannot read (" + e.Message + ")"); continue; }

            var fields = new Dictionary<string, string>();   // "Type::name" -> description
            // Compiler-generated types (lambda and delegate caches) hold only static methods, never the store.
            foreach (var t in asm.MainModule.GetTypes().Where(x => !x.FullName.Contains("<")))
                foreach (var f in t.Fields.Where(x => x.IsStatic && !x.IsLiteral))
                    if (Holds(f.FieldType) || IsDelegate(f.FieldType)) fields[f.DeclaringType.FullName + "::" + f.Name] = Describe(f);

            var writes = new Dictionary<string, int>();
            var adds = new Dictionary<string, int>();
            var clears = new Dictionary<string, int>();
            Action<Dictionary<string, int>, string> count = (d, k) => d[k] = (d.ContainsKey(k) ? d[k] : 0) + 1;

            foreach (var t in asm.MainModule.GetTypes())
                foreach (var m in t.Methods.Where(x => x.HasBody && x.Name != ".cctor"))
                {
                    var ins = m.Body.Instructions;
                    for (int i = 0; i < ins.Count; i++)
                    {
                        var fr = ins[i].Operand as FieldReference;
                        if (fr == null) continue;
                        var key = fr.DeclaringType.FullName + "::" + fr.Name;
                        if (!fields.ContainsKey(key)) continue;
                        if (ins[i].OpCode.Code == Code.Stsfld)
                        {
                            // Look past dup and the other stores of a chained assignment (a = b = null).
                            int k = i - 1;
                            while (k > 0 && (ins[k].OpCode.Code == Code.Dup || ins[k].OpCode.Code == Code.Stsfld)) k--;
                            var prev = k >= 0 ? ins[k].OpCode.Code : Code.Nop;
                            count(prev == Code.Ldnull || prev == Code.Newobj ? clears : writes, key);
                        }
                        else if (ins[i].OpCode.Code == Code.Ldsfld)
                        {
                            // The first call within a few instructions says what is done with the loaded field.
                            for (int j = i + 1; j < Math.Min(ins.Count, i + 6); j++)
                            {
                                var call = ins[j].Operand as MethodReference;
                                if (call == null) continue;
                                if (Adds.Contains(call.Name)) count(adds, key);
                                else if (Clears.Contains(call.Name)) count(clears, key);
                                break;
                            }
                        }
                    }
                }

            Console.WriteLine("=== " + Path.GetFileName(path) + ": " + fields.Count + " static field(s) that can hold the store");
            foreach (var pair in fields.OrderBy(p => p.Key))
            {
                int w = writes.ContainsKey(pair.Key) ? writes[pair.Key] : 0;
                int ad = adds.ContainsKey(pair.Key) ? adds[pair.Key] : 0;
                int cl = clears.ContainsKey(pair.Key) ? clears[pair.Key] : 0;
                if (w + ad == 0) continue;
                var mark = ad > 0 && cl == 0 ? "GROWS-NEVER-CLEARED " : ad > 0 ? "grows " : "set ";
                Console.WriteLine(mark + pair.Value + "  writes=" + w + " adds=" + ad + " clears=" + cl);
            }
        }
    }
}
