// Usage: Singletons.exe <Managed folder>  - the game's managers that point at themselves from a static field
//
// Lists every public MonoBehaviour of Assembly-CSharp with a static field of its own type (current, Instance,
// mInstance...), one "Type field" line each. Such a field keeps pointing at the destroyed manager, and through it at
// the store, until the next store sets it again; a mod that releases the store on leaving clears the ones that
// point at a destroyed object. Leave out the game's mod loader, mod security and Steam types, which mods may not
// touch.
using System;
using System.IO;
using System.Linq;
using Mono.Cecil;

class Singletons
{
    static bool IsMonoBehaviour(TypeDefinition t)
    {
        for (var b = t.BaseType; b != null;)
        {
            if (b.FullName == "UnityEngine.MonoBehaviour") return true;
            TypeDefinition d;
            try { d = b.Resolve(); } catch { return false; }
            b = d == null ? null : d.BaseType;
        }
        return false;
    }

    static void Main(string[] a)
    {
        var res = new DefaultAssemblyResolver();
        res.AddSearchDirectory(a[0]);
        var module = AssemblyDefinition.ReadAssembly(Path.Combine(a[0], "Assembly-CSharp.dll"),
            new ReaderParameters { AssemblyResolver = res }).MainModule;
        foreach (var t in module.GetTypes().Where(x => x.IsPublic && !x.HasGenericParameters && IsMonoBehaviour(x)))
            foreach (var f in t.Fields.Where(x => x.IsStatic && !x.IsLiteral && x.FieldType.FullName == t.FullName))
                Console.WriteLine(t.FullName + " " + f.Name);
    }
}
