#!/usr/bin/env bash
# Collects every built mod (mods/*/out/<id>) into dist/packages/<id>/ with its README,
# CHANGELOG and Workshop text, and a zip of each: what a release or a Workshop upload needs.
#   scripts/package.sh
set -euo pipefail
cd "$(dirname "$0")/.."
out=dist/packages
rm -rf "$out" && mkdir -p "$out"
for mod in mods/*/; do
  for built in "$mod"out/*/; do
    [ -f "$built/manifest.xml" ] || continue
    id=$(basename "$built")
    version=$(sed -n 's:.*<ModVersion>\(.*\)</ModVersion>.*:\1:p' "$built/manifest.xml")
    cp -r "$built" "$out/$id"
    cp "$mod/README.md" "$mod/CHANGELOG.md" "$mod/WORKSHOP.txt" "$mod/LICENSE" "$out/$id/" 2>/dev/null || true
    (cd "$out" && python -c "import shutil,sys; shutil.make_archive(sys.argv[1], 'zip', '.', sys.argv[2])" "$id-$version" "$id")
    echo "packaged $id $version"
  done
done
