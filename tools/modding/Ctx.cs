// Usage: Ctx.exe <dll> <regex-on-instruction> <after>  - prints methods with the N instructions after each match
// Shows what a matched instruction is followed by (e.g. which method consumes a loaded constant or field); only the
// callee name of each following call is printed. Assemblies next to <dll> are used to resolve references.
using System; using System.Linq; using System.Text.RegularExpressions; using Mono.Cecil; using System.IO;
class C { static void Main(string[] a) {
  var res = new DefaultAssemblyResolver(); res.AddSearchDirectory(Path.GetDirectoryName(Path.GetFullPath(a[0])));
  var asm = AssemblyDefinition.ReadAssembly(a[0], new ReaderParameters { AssemblyResolver = res });
  var re = new Regex(a[1]); int n = int.Parse(a[2]);
  foreach (var t in asm.MainModule.GetTypes()) foreach (var m in t.Methods.Where(x => x.HasBody)) {
    var ins = m.Body.Instructions; bool head = false;
    for (int i = 0; i < ins.Count; i++) if (re.IsMatch(ins[i].ToString())) {
      var tail = string.Join(" | ", ins.Skip(i + 1).Take(n).Select(x => x.OpCode + " " + (x.Operand is MethodReference ? ((MethodReference)x.Operand).Name : "")));
      if (!head) { Console.WriteLine(t.FullName + "::" + m.Name); head = true; }
      Console.WriteLine("    " + tail);
    }
  }
}}
