#!/usr/bin/env python3
# Writes a SteamCMD upload file for every packaged mod (dist/packages/<id>/) to
# dist/workshop/<id>.vdf, with the Workshop item id and title from config/workshop.json and
# the description from the mod's WORKSHOP.txt. Run scripts/package.sh first, then upload with
#   steamcmd +login <account> +workshop_build_item <path to .vdf> +quit
#   python scripts/workshop.py "1.0.1: what changed" [--only slug[,slug...]]
# --only writes the files of the mods named (performance-fixes, ...) and no others, so one release cannot upload
# another mod's package by mistake. A description over Steam's limit of 8,000 bytes (UTF-8) stops the script:
# SteamCMD would upload the content and preview and then fail with "Invalid Parameter".
import os
import sys
from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from typing import Final

ROOT: Final = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, 'design'))
from typed import as_dict, as_str, load_json, member, split_ids, take_option  # noqa: E402
from version import is_wip, read_version  # noqa: E402

LIMIT: Final = 8000
NEWLINE: Final = '\n'      # VDF files are written with LF on every platform


@dataclass(frozen=True)
class Item:
    id: str
    title: str


@dataclass(frozen=True)
class Config:
    appid: str
    items: Mapping[str, Item]


def parse_config(raw: object, where: str) -> Config:
    conf = as_dict(raw, where)
    items = as_dict(member(conf, 'items', where), f'{where}.items')

    def item(slug: str, value: object) -> Item:
        d = as_dict(value, f'{where}.items.{slug}')
        return Item(as_str(member(d, 'id', slug), f'{slug}.id'), as_str(member(d, 'title', slug), f'{slug}.title'))

    return Config(as_str(member(conf, 'appid', where), f'{where}.appid'),
                  {slug: item(slug, v) for slug, v in items.items()})


def read_text(path: str) -> str:
    with open(path, encoding='utf-8') as f:
        return f.read()


# A packaged mod has exactly one manifest folder; its name is the package's id.
def package_name(slug: str) -> str | None:
    """The first package manifest folder under mods/<slug>/out, if the mod was built."""
    out = f'mods/{slug}/out'
    return next(iter(sorted(os.listdir(out))), None) if os.path.isdir(out) else None


# The SteamCMD upload file. Values sit in double quotes with no escaping, hence the check in main() that rejects quotes.
def vdf(conf: Config, item: Item, pkg: str, desc: str, note: str) -> str:
    return f'''"workshopitem"
{{
  "appid"           "{conf.appid}"
  "publishedfileid" "{item.id}"
  "contentfolder"   "{pkg}"
  "previewfile"     "{pkg}/preview.png"
  "title"           "{item.title}"
  "description"     "{desc}"
  "changenote"      "{note}"
}}
'''


# Reads each mod's WORKSHOP.txt from its submodule and refuses descriptions over Steam's byte limit, so a long text fails here
# and not after SteamCMD has uploaded the content.
def main(argv: Sequence[str]) -> None:
    os.chdir(ROOT)
    only_arg, args = take_option(argv, '--only')
    only = split_ids(only_arg)
    note = args[0] if args else 'Update.'
    conf = parse_config(load_json('config/workshop.json'), 'config/workshop.json')
    if only and only - conf.items.keys():
        sys.exit('unknown mod(s): ' + ', '.join(sorted(only - conf.items.keys())))
    os.makedirs('dist/workshop', exist_ok=True)
    for slug, item in conf.items.items():
        if only and slug not in only:
            continue
        manifest = package_name(slug)
        pkg = os.path.abspath(f'dist/packages/{manifest}') if manifest else None
        if not manifest or not pkg or not os.path.isfile(os.path.join(pkg, 'manifest.xml')):
            print(f'{slug}: not packaged; run scripts/package.sh')
            continue
        # An unfinished mod is never uploaded: stop when either the package or the mod's own manifest says WIP.
        if is_wip(read_version(pkg)) or is_wip(read_version(f'mods/{slug}')):
            sys.exit(f'{slug}: its version is WIP, which is not released')
        desc = read_text(f'mods/{slug}/WORKSHOP.txt').strip()
        size = len(desc.encode('utf-8'))
        if size > LIMIT:
            sys.exit(f"{slug}: WORKSHOP.txt is {size} bytes, over Steam's limit of {LIMIT}; shorten it (keep What's new and the general features)")
        if '"' in desc or '"' in note:
            sys.exit(f'{slug}: double quotes cannot appear in a VDF value')
        out = f'dist/workshop/{manifest}.vdf'
        with open(out, 'w', encoding='utf-8', newline=NEWLINE) as f:
            f.write(vdf(conf, item, pkg.replace(os.sep, '/'), desc, note))
        print(f'wrote {out} (item {item.id})')


if __name__ == '__main__':
    main(sys.argv[1:])
