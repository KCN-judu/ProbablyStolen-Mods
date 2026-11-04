#!/usr/bin/env bash
# Collects every built mod (mods/*/out/<id>) into dist/packages/<id>/ with its README,
# CHANGELOG and Workshop text, and a zip of each: what a release or a Workshop upload needs.
# Each package gets its cover rendered fresh with the version in its manifest, so the Workshop preview,
# which an upload replaces every time, always shows the version it ships.
# A mod whose version is WIP is skipped: an unfinished mod is not packaged, so it cannot be uploaded or released.
#   scripts/package.sh
set -euo pipefail
cd "$(dirname "$0")/.."
out=dist/packages
rm -rf "$out" && mkdir -p "$out"
python design/covers.py design/out >/dev/null
for mod in mods/*/; do
  for built in "$mod"out/*/; do
    [ -f "$built/manifest.xml" ] || continue
    id=$(basename "$built")
    version=$(sed -n 's:.*<ModVersion>\(.*\)</ModVersion>.*:\1:p' "$built/manifest.xml")
    if [ "$version" = "WIP" ]; then echo "skipped $id: its version is WIP"; continue; fi
    cp -r "$built" "$out/$id"
    [ -f "design/out/$id.png" ] && cp "design/out/$id.png" "$out/$id/preview.png"
    cp "$mod/README.md" "$mod/CHANGELOG.md" "$mod/WORKSHOP.txt" "$mod/LICENSE" "$out/$id/" 2>/dev/null || true
    (cd "$out" && python -c "import shutil,sys; shutil.make_archive(sys.argv[1], 'zip', '.', sys.argv[2])" "$id-$version" "$id")
    echo "packaged $id $version"
  done
done
