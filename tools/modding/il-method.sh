#!/usr/bin/env bash
# Prints one method from a full IL dump written by Inspect.exe, compactly: namespaces of common types shortened,
# indentation and IL offsets of branch targets kept so branches can be followed.
#   Inspect.exe Assembly-CSharp.dll all.txt "." "."      # once: every type, with the IL of every method
#   tools/modding/il-method.sh all.txt PixelWindow Show   # every overload of PixelWindow.Show
# The type is its full name as the dump prints it (nested types as Outer/Inner).
set -euo pipefail
[ $# -eq 3 ] || { echo "usage: $0 <dump.txt> <Type> <Method>" >&2; exit 2; }
awk -v t="$2" -v m="$3" '
/^TYPE /{ split($0, a, " "); intype = (a[2] == t); p = 0; next }
intype && index($0, "  M ") == 1 { p = (index($0, " " m "(") > 0); if (p) print; next }
p' "$1" | sed -E 's/^ +/  /; s/System\.Collections\.Generic\.//g; s/System\.//g; s/UnityEngine\.//g'
