#!/usr/bin/env bash
# Builds every mod in mods/ with its own build.sh. Pass --install to copy each into the game.
#   GAME=/path/to/"Probably Stolen" scripts/build-all.sh [--install]
set -euo pipefail
cd "$(dirname "$0")/.."
for mod in mods/*/; do
  [ -x "$mod/build.sh" ] || continue
  echo "== $(basename "$mod")"
  "$mod/build.sh" "$@"
done
