#!/usr/bin/env bash
# Sets the Workshop tags in config/workshop.json on every item, through the game's own
# Steamworks.NET. Needs the Steam client running and logged in as the items' owner.
#   scripts/workshop-tags.sh
set -euo pipefail
cd "$(dirname "$0")/.."
GAME="${GAME:-/d/SteamLibrary/steamapps/common/Probably Stolen}"
CSC="${CSC:-/c/Program Files (x86)/Microsoft Visual Studio/18/BuildTools/MSBuild/Current/Bin/Roslyn/csc.exe}"
M="$GAME/Probably Stolen_Data/Managed"
work="${TEMP:-/tmp}/psm_workshop_tags"
mkdir -p "$work"
cp "$M/com.rlabrecque.steamworks.net.dll" "$M/netstandard.dll" "$GAME/Probably Stolen_Data/Plugins/x86_64/steam_api64.dll" "$work/"
if [ ! -f "$work/WorkshopTags.exe" ] || [ tools/modding/WorkshopTags.cs -nt "$work/WorkshopTags.exe" ]; then
  cp tools/modding/WorkshopTags.cs "$work/"
  (cd "$work" && "$CSC" -nologo -langversion:latest -platform:x64 -out:WorkshopTags.exe \
    -r:com.rlabrecque.steamworks.net.dll "-r:$(cygpath -w "$M/netstandard.dll")" WorkshopTags.cs)
fi
appid=$(python -c "import json; print(json.load(open('config/workshop.json', encoding='utf-8'))['appid'])")
echo "$appid" > "$work/steam_appid.txt"
mapfile -t items < <(python -c "
import json
for i in json.load(open('config/workshop.json', encoding='utf-8'))['items'].values():
    print(i['id'] + '=' + ','.join(i['tags']))")
cd "$work" && ./WorkshopTags.exe "$appid" "${items[@]}"
