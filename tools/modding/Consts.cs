// Usage: Consts.exe <dll>  - prints every constant field of the assembly as Type.field = value
// (const values are inlined by the compiler, so IL dumps show the number without its name; this recovers the name).
using System; using System.Linq; using Mono.Cecil;
class C { static void Main(string[] a) {
  var asm = AssemblyDefinition.ReadAssembly(a[0]);
  foreach (var t in asm.MainModule.GetTypes()) foreach (var f in t.Fields.Where(x => x.HasConstant))
    Console.WriteLine(t.Name + "." + f.Name + " = " + f.Constant);
}}
