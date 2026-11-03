#!/usr/bin/env bash
# Checks a mod's working copy before a release, in the order of the release steps, and stops nothing: every check
# runs and the summary lists what is not ready.
#   scripts/release-check.sh ../ProbablyStolen-PerformanceFixes/PerformanceFixes
# The folder is the mod's own (the one with manifest.xml and build.sh). Checks:
#   - CHANGELOG.md has an entry for the version in manifest.xml;
#   - the headless tests pass (tests/run.sh, when the mod has them) and the mod builds;
#   - the game's scanner finds no capability and no HARD line;
#   - the documentation passes lunadoc's check and every catalog is fully translated;
#   - WORKSHOP.txt is under Steam's 8,000-byte limit and starts with What's new for this version;
#   - preview.png and doc/attachments/cover.png are the cover of this version (render and copy them with
#     python design/covers.py design/out --checkouts <folder> --sync --only <id>);
#   - nothing is left uncommitted, and no tag of this version exists yet.
set -uo pipefail
cd "$(dirname "$0")/.."
collection=$(pwd)
mod=$(cd "$1" && pwd)
checkouts=$(dirname "$(dirname "$mod")")
problems=()
note() { problems+=("$1"); echo "  NOT READY: $1"; }
step() { echo "== $1"; }

version=$(sed -n 's:.*<ModVersion>\(.*\)</ModVersion>.*:\1:p' "$mod/manifest.xml")
echo "$(basename "$mod") $version"

step "changelog"
grep -q "^## $version\b" "$mod/CHANGELOG.md" || note "CHANGELOG.md has no '## $version' entry"

step "tests and build"
if [ -f "$mod/tests/run.sh" ]; then
  (cd "$mod" && bash tests/run.sh >"${TEMP:-/tmp}/release-tests.txt" 2>&1) || note "tests fail (see ${TEMP:-/tmp}/release-tests.txt)"
fi
(cd "$mod" && bash build.sh >/dev/null 2>&1) || note "build fails"
out=$(ls -d "$mod"/out/*/ 2>/dev/null | head -1)
id=$(basename "${out:-none}")

step "scanner"
if [ -n "$out" ]; then
  scan=$(bash scripts/scan.sh "$out" 2>&1 | grep -v TypeLoad)
  echo "$scan" | grep -q "^capabilities: none" || note "scanner: $(echo "$scan" | head -1)"
  echo "$scan" | grep -q "HARD" && note "scanner reports a HARD line"
fi

step "documentation"
node tools/lunadoc/cli.mjs check "$mod" --doc "$mod/doc" 2>&1 | tail -1 | grep -q "^0 errors" || note "documentation check fails"
node tools/lunadoc/cli.mjs status "$mod" --doc "$mod/doc" 2>&1 | grep -v "100.0%" | grep -q "%" && note "documentation not fully translated"

step "Workshop text"
bytes=$(wc -c < "$mod/WORKSHOP.txt")
[ "$bytes" -le 8000 ] || note "WORKSHOP.txt is $bytes bytes, over 8000"
grep -q "What's new in $version" "$mod/WORKSHOP.txt" || note "WORKSHOP.txt has no \"What's new in $version\""

step "cover"
render="${TEMP:-/tmp}/release-covers"
python design/covers.py "$render" --checkouts "$checkouts" >/dev/null 2>&1
for target in preview.png doc/attachments/cover.png; do
  [ -f "$mod/$target" ] || continue
  cmp -s "$render/$id.png" "$mod/$target" || note "$target is not the $version cover"
done

step "git"
dirty=$(cd "$mod" && git status --porcelain | grep -v "^?? out/" | wc -l)
[ "$dirty" -eq 0 ] || note "$dirty uncommitted change(s)"
(cd "$mod" && git rev-parse -q --verify "refs/tags/v$version" >/dev/null) && note "tag v$version already exists"

echo
if [ ${#problems[@]} -eq 0 ]; then
  echo "ready to release $id $version"
else
  echo "${#problems[@]} thing(s) to fix before releasing $id $version"
  exit 1
fi
