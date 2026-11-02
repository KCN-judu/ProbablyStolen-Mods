#!/usr/bin/env python3
# Writes a SteamCMD upload file for every packaged mod (dist/packages/<id>/) to
# dist/workshop/<id>.vdf, with the Workshop item id and title from config/workshop.json and
# the description from the mod's WORKSHOP.txt. Run scripts/package.sh first, then upload with
#   steamcmd +login <account> +workshop_build_item <path to .vdf> +quit
#   python scripts/workshop.py "1.0.1: what changed"
import io, json, os, re, sys

root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
os.chdir(root)
note = sys.argv[1] if len(sys.argv) > 1 else 'Update.'
conf = json.load(io.open('config/workshop.json', encoding='utf-8'))
os.makedirs('dist/workshop', exist_ok=True)
for slug, item in conf['items'].items():
    manifest = next(iter(sorted(os.listdir(f'mods/{slug}/out'))), None) if os.path.isdir(f'mods/{slug}/out') else None
    pkg = os.path.abspath(f'dist/packages/{manifest}') if manifest else None
    if not pkg or not os.path.isfile(os.path.join(pkg, 'manifest.xml')):
        print(f'{slug}: not packaged; run scripts/package.sh')
        continue
    desc = io.open(f'mods/{slug}/WORKSHOP.txt', encoding='utf-8').read().strip()
    if '"' in desc or '"' in note:
        sys.exit(f'{slug}: double quotes cannot appear in a VDF value')
    pkg = pkg.replace(os.sep, '/')
    vdf = f'''"workshopitem"
{{
  "appid"           "{conf['appid']}"
  "publishedfileid" "{item['id']}"
  "contentfolder"   "{pkg}"
  "previewfile"     "{pkg}/preview.png"
  "title"           "{item['title']}"
  "description"     "{desc}"
  "changenote"      "{note}"
}}
'''
    out = f'dist/workshop/{manifest}.vdf'
    io.open(out, 'w', encoding='utf-8', newline='\n').write(vdf)
    print(f'wrote {out} (item {item["id"]})')
