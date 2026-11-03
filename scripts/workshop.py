#!/usr/bin/env python3
# Writes a SteamCMD upload file for every packaged mod (dist/packages/<id>/) to
# dist/workshop/<id>.vdf, with the Workshop item id and title from config/workshop.json and
# the description from the mod's WORKSHOP.txt. Run scripts/package.sh first, then upload with
#   steamcmd +login <account> +workshop_build_item <path to .vdf> +quit
#   python scripts/workshop.py "1.0.1: what changed" [--only slug[,slug...]]
# --only writes the files of the mods named (performance-fixes, ...) and no others, so one release cannot upload
# another mod's package by mistake. A description over Steam's limit of 8,000 bytes (UTF-8) stops the script:
# SteamCMD would upload the content and preview and then fail with "Invalid Parameter".
import io, json, os, re, sys

LIMIT = 8000

root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
os.chdir(root)
args = sys.argv[1:]
only = None
if '--only' in args:
    i = args.index('--only')
    only = set(args[i + 1].split(','))
    del args[i:i + 2]
note = args[0] if args else 'Update.'
conf = json.load(io.open('config/workshop.json', encoding='utf-8'))
if only and only - set(conf['items']):
    sys.exit('unknown mod(s): ' + ', '.join(sorted(only - set(conf['items']))))
os.makedirs('dist/workshop', exist_ok=True)
for slug, item in conf['items'].items():
    if only and slug not in only:
        continue
    manifest = next(iter(sorted(os.listdir(f'mods/{slug}/out'))), None) if os.path.isdir(f'mods/{slug}/out') else None
    pkg = os.path.abspath(f'dist/packages/{manifest}') if manifest else None
    if not pkg or not os.path.isfile(os.path.join(pkg, 'manifest.xml')):
        print(f'{slug}: not packaged; run scripts/package.sh')
        continue
    desc = io.open(f'mods/{slug}/WORKSHOP.txt', encoding='utf-8').read().strip()
    size = len(desc.encode('utf-8'))
    if size > LIMIT:
        sys.exit(f"{slug}: WORKSHOP.txt is {size} bytes, over Steam's limit of {LIMIT}; shorten it (keep What's new and the general features)")
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
