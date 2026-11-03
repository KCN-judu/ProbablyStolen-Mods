// Usage: LocaleTraps.exe <Assembly-CSharp.dll> <targets.txt>  - patch targets that would freeze localized text
//
// targets.txt lists the methods a mod patches, one "Type Method" per line (nested types as Outer/Inner). Patching
// compiles the method, and compiling it runs the static constructor of a beforefieldinit type it uses. A mod starts
// before the game applies the player's language, so if that static constructor reads localized text (LocHelper or
// Unity Localization), the text stays in English for the whole session. The tool prints the types with such a static
// constructor, then each target that uses one, directly or through its own type. Those targets must be patched only
// once the language is applied, as Performance Fixes does with its language gate.
using System;
using System.Collections.Generic;
using System.IO;
using System.Linq;
using Mono.Cecil;

class LocaleTraps
{
    static bool ReadsLocalization(MethodDefinition cctor)
    {
        return cctor.Body.Instructions.Any(i =>
        {
            var r = i.Operand as MethodReference;
            return r != null && (r.DeclaringType.Name == "LocHelper" || r.DeclaringType.Name.Contains("Locali") || r.Name.Contains("Localized"));
        });
    }

    static void Main(string[] a)
    {
        var module = AssemblyDefinition.ReadAssembly(a[0]).MainModule;
        var traps = new HashSet<string>();
        foreach (var t in module.GetTypes())
        {
            var cctor = t.Methods.FirstOrDefault(m => m.Name == ".cctor" && m.HasBody);
            if (cctor != null && t.IsBeforeFieldInit && ReadsLocalization(cctor)) traps.Add(t.FullName);
        }
        Console.WriteLine("beforefieldinit types whose static constructor reads localized text: " + string.Join(", ", traps.OrderBy(x => x)));

        foreach (var line in File.ReadAllLines(a[1]))
        {
            var parts = line.Trim().Split(' ');
            if (parts.Length < 2) continue;
            var type = module.GetType(parts[0]) ?? module.GetType(parts[0].Replace('.', '/'));
            if (type == null) { Console.WriteLine(line + " -> type not found"); continue; }
            foreach (var m in type.Methods.Where(x => x.Name == parts[1] && x.HasBody))
            {
                var hits = new HashSet<string>();
                if (traps.Contains(type.FullName)) hits.Add(type.FullName + " (its own type)");
                foreach (var ins in m.Body.Instructions)
                {
                    var member = ins.Operand as MemberReference;
                    if (member != null && member.DeclaringType != null && traps.Contains(member.DeclaringType.FullName)) hits.Add(member.DeclaringType.FullName);
                    var tr = ins.Operand as TypeReference;
                    if (tr != null && traps.Contains(tr.FullName)) hits.Add(tr.FullName);
                }
                if (hits.Count > 0) Console.WriteLine(parts[0] + "::" + parts[1] + " -> " + string.Join(", ", hits));
            }
        }
    }
}
