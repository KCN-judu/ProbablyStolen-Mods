#!/usr/bin/env bash
# Creates or updates the Steam Workshop collection of the mods, through the game's own Steamworks.NET:
# title, description (config/collection-description.txt), cover (design/collection_cover.py), tags and the mods
# in the order of config/workshop.json "collection". A new collection's id is written back to that file.
# Needs the Steam client running and logged in as the owner.
#   scripts/workshop-collection.sh [public|friends|private]   # visibility; left as it is when not given
set -euo pipefail
cd "$(dirname "$0")/.."
GAME="${GAME:-/d/SteamLibrary/steamapps/common/Probably Stolen}"
CSC="${CSC:-/c/Program Files (x86)/Microsoft Visual Studio/18/BuildTools/MSBuild/Current/Bin/Roslyn/csc.exe}"
M="$GAME/Probably Stolen_Data/Managed"
work="${TEMP:-/tmp}/psm_workshop_collection"
mkdir -p "$work"
cp "$M/com.rlabrecque.steamworks.net.dll" "$M/netstandard.dll" "$GAME/Probably Stolen_Data/Plugins/x86_64/steam_api64.dll" "$work/"
if [ ! -f "$work/WorkshopCollection.exe" ] || [ tools/modding/WorkshopCollection.cs -nt "$work/WorkshopCollection.exe" ]; then
  cp tools/modding/WorkshopCollection.cs "$work/"
  (cd "$work" && "$CSC" -nologo -langversion:latest -platform:x64 -out:WorkshopCollection.exe \
    -r:com.rlabrecque.steamworks.net.dll "-r:$(cygpath -w "$M/netstandard.dll")" WorkshopCollection.cs)
fi
python design/collection_cover.py design/out >/dev/null
cp config/collection-description.txt design/out/collection.png "$work/"

mapfile -t conf < <(python -c "
import json
c = json.load(open('config/workshop.json', encoding='utf-8'))
col = c['collection']
print(c['appid']); print(col.get('id') or '0'); print(col['title']); print(','.join(col['tags']))
for slug in col['items']: print(c['items'][slug]['id'])" | tr -d '\r')
appid=${conf[0]}; id=${conf[1]}; title=${conf[2]}; tags=${conf[3]}; children=("${conf[@]:4}")
echo "$appid" > "$work/steam_appid.txt"
visibility="${1:-keep}"
out=$(cd "$work" && ./WorkshopCollection.exe "$appid" "$id" "$title" collection-description.txt collection.png "$visibility" "$tags" "${children[@]}") || { echo "$out"; exit 1; }
echo "$out"
new=$(echo "$out" | sed -n 's/^collection \([0-9]*\).*/\1/p' | tr -d '\r')
if [ -n "$new" ] && [ "$new" != "$id" ]; then
  python -c "
import json, sys
p = 'config/workshop.json'
c = json.load(open(p, encoding='utf-8'))
c['collection']['id'] = sys.argv[1]
open(p, 'w', encoding='utf-8', newline='\n').write(json.dumps(c, ensure_ascii=False, indent=2) + '\n')" "$new"
  echo "stored collection id $new in config/workshop.json"
fi
