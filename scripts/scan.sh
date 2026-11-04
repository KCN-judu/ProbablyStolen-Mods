#!/usr/bin/env bash
# Runs the game's own mod scanner (ModScanner.Scan) on a built mod folder, outside the game.
#   GAME=/path/to/"Probably Stolen" scripts/scan.sh mods/quick-call/out/quick_call
# A mod is ready when it prints "capabilities: none" and no HARD line. Outside the game the
# scanner may also report a TypeLoadException for netstandard types; that line is expected.
# A mod whose manifest.xml says <ModVersion>WIP</ModVersion> is scanned as a copy with version 0.1.0, because the
# scanner needs a real version; the mod's own manifest.xml is not changed (see design/version.py).
set -euo pipefail
cd "$(dirname "$0")/.."
GAME="${GAME:-/d/SteamLibrary/steamapps/common/Probably Stolen}"
CSC="${CSC:-/c/Program Files (x86)/Microsoft Visual Studio/18/BuildTools/MSBuild/Current/Bin/Roslyn/csc.exe}"
M="$GAME/Probably Stolen_Data/Managed"
work="${TEMP:-/tmp}/psm_scan"
mkdir -p "$work"
if [ ! -f "$work/ScanTest.exe" ] || [ tools/modding/ScanTest.cs -nt "$work/ScanTest.exe" ]; then
  cp tools/modding/ScanTest.cs "$work/"
  (cd "$work" && "$CSC" -nologo -langversion:latest -out:ScanTest.exe \
    "-r:$(cygpath -w "$M/Assembly-CSharp.dll")" "-r:$(cygpath -w "$M/netstandard.dll")" ScanTest.cs)
fi
mod="$(realpath "$1")"
if grep -q '<ModVersion>WIP</ModVersion>' "$mod/manifest.xml"; then
  copy="$work/wip/$(basename "$mod")"
  rm -rf "$copy" && mkdir -p "$work/wip" && cp -r "$mod" "$copy"
  sed -i 's:<ModVersion>WIP</ModVersion>:<ModVersion>0.1.0</ModVersion>:' "$copy/manifest.xml"
  echo "WIP: scanning a copy with version 0.1.0; the mod itself is unchanged"
  mod="$copy"
fi
"$work/ScanTest.exe" "$(cygpath -w "$M")" "$(cygpath -w "$mod")"
