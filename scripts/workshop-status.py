#!/usr/bin/env python3
# Checks that every Workshop item is up to date with its latest release.
#   python scripts/workshop-status.py
# For each mod in config/workshop.json it reads, from Steam's public API, when the Workshop item was last updated
# and its preview image, and from GitHub (the gh CLI) the latest release and, up to its tag, the last commit that
# changed manifest.xml: the one that set the version, which always comes before the upload (the release commit
# itself may only add the Workshop link, which exists after the first upload). An item is current when it was
# updated after that commit and its preview shows the same pixels as the cover covers.py renders for the version in the
# mod's submodule, which is the released version. The previews are saved to dist/workshop-status/ with a sheet of all of
# them, sheet.png, to look at.
import os
import subprocess
import sys
import urllib.parse
import urllib.request
from collections.abc import Mapping, Sequence
from concurrent.futures import ThreadPoolExecutor
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Final

ROOT: Final = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, 'design'))
from PIL import Image  # noqa: E402

from typed import as_dict, as_int, as_list, as_str, load_json, member, parse_json, str_map  # noqa: E402

OUT: Final = 'dist/workshop-status'
EXPECTED: Final = os.path.join(OUT, 'expected')
STEAM_URL: Final = 'https://api.steampowered.com/ISteamRemoteStorage/GetPublishedFileDetails/v1/'


@dataclass(frozen=True)
class Details:
    """What Steam's public API says about one Workshop item."""
    time_updated: int
    preview_url: str | None


@dataclass(frozen=True)
class Release:
    tag: str | None
    version_set: datetime | None     # the last commit up to the tag that changed manifest.xml


@dataclass(frozen=True)
class Verdict:
    line: str
    ok: bool
    preview: str | None              # the saved preview image, if Steam has one


def same_pixels(a: str, b: str) -> bool:
    """Whether two PNGs show the same picture. Steam re-encodes uploaded previews, so their bytes never match."""
    with Image.open(a) as x, Image.open(b) as y:
        return x.size == y.size and x.convert('RGB').tobytes() == y.convert('RGB').tobytes()


def item_ids(raw: object) -> Mapping[str, str]:
    """Slug -> Workshop item id, from config/workshop.json."""
    items = as_dict(member(as_dict(raw, 'config/workshop.json'), 'items', 'config/workshop.json'), 'items')
    return {slug: as_str(member(as_dict(v, slug), 'id', slug), f'{slug}.id') for slug, v in items.items()}


# Steam's answer is an object with a `response.publishedfiledetails` list; entries are keyed by the item id they report.
def parse_details(raw: object) -> Mapping[str, Details]:
    response = as_dict(member(as_dict(raw, 'Steam response'), 'response', 'Steam response'), 'response')
    entries = [as_dict(d, 'publishedfiledetails') for d in as_list(member(response, 'publishedfiledetails', 'response'),
                                                                     'publishedfiledetails')]

    def details(d: Mapping[str, object]) -> Details:
        url = d.get('preview_url')
        return Details(as_int(d.get('time_updated', 0), 'time_updated'), as_str(url, 'preview_url') if url else None)

    return {as_str(member(d, 'publishedfileid', 'publishedfiledetails'), 'publishedfileid'): details(d) for d in entries}


# One POST for all items; the endpoint needs no API key for public items.
def fetch_details(ids: Mapping[str, str]) -> Mapping[str, Details]:
    form = {'itemcount': str(len(ids))} | {f'publishedfileids[{i}]': v for i, v in enumerate(ids.values())}
    with urllib.request.urlopen(STEAM_URL, urllib.parse.urlencode(form).encode()) as resp:
        return parse_details(parse_json(resp.read()))


# The commit that set the release's version, not the release date: a Workshop upload happens after that commit, so an item
# updated before it is stale. Needs the gh CLI; a repository without a release gives (None, None).
def latest_release(repo: str) -> Release:
    r = subprocess.run(['gh', 'release', 'view', '-R', 'KCN-judu/' + repo, '--json', 'tagName'],
                       capture_output=True, text=True)
    if r.returncode != 0:
        return Release(None, None)
    tag = as_str(member(as_dict(parse_json(r.stdout), 'gh release'), 'tagName', 'gh release'), 'tagName')
    c = subprocess.run(['gh', 'api', f'repos/KCN-judu/{repo}/commits?sha={tag}&path=manifest.xml&per_page=1',
                        '--jq', '.[0].commit.committer.date'], capture_output=True, text=True)
    if c.returncode != 0:
        return Release(tag, None)
    return Release(tag, datetime.fromisoformat(c.stdout.strip().replace('Z', '+00:00')))


def describe(slug: str, release: Release, updated: datetime, cover_ok: bool, content_ok: bool) -> str:
    released = release.version_set
    if released is None:
        return f"?    {slug:26} no release found"
    return (f"{'ok  ' if cover_ok and content_ok else 'OLD '} {slug:26} release {release.tag or '?':8} "
            f"version set {released:%Y-%m-%d %H:%M} UTC, Workshop updated {updated:%Y-%m-%d %H:%M} UTC"
            f"{'' if content_ok else '  (content older than the release)'}"
            f"{'' if cover_ok else '  (cover differs from the released version)'}")


# Compares one Workshop item with its repository's latest release: content by update time, cover by pixels against the cover
# rendered from the submodules (Steam re-encodes previews, see same_pixels).
def check(slug: str, item_id: str, repo: str, details: Mapping[str, Details]) -> Verdict:
    d = details.get(item_id, Details(0, None))
    cover_id = slug.replace('-', '_')
    updated = datetime.fromtimestamp(d.time_updated, timezone.utc)
    release = latest_release(repo)
    preview = os.path.join(OUT, cover_id + '.png')
    if d.preview_url:
        with urllib.request.urlopen(d.preview_url) as resp, open(preview, 'wb') as f:
            f.write(resp.read())
    want = os.path.join(EXPECTED, cover_id + '.png')
    cover_ok = os.path.isfile(preview) and os.path.isfile(want) and same_pixels(preview, want)
    content_ok = release.version_set is not None and updated >= release.version_set
    return Verdict(describe(slug, release, updated, cover_ok, content_ok), cover_ok and content_ok,
                   preview if d.preview_url else None)


# Two previews per row at 640x360, to eyeball the downloaded covers together.
def contact_sheet(tiles: Sequence[str]) -> Image.Image:
    images = [Image.open(t).convert('RGB').resize((640, 360), Image.Resampling.NEAREST) for t in tiles]
    rows = (len(images) + 1) // 2
    sheet = Image.new('RGB', (1280, 360 * rows), (0, 0, 0))
    for i, im in enumerate(images):
        sheet.paste(im, ((i % 2) * 640, (i // 2) * 360))
    return sheet


def main() -> int:
    os.chdir(ROOT)
    os.makedirs(EXPECTED, exist_ok=True)
    ids = item_ids(load_json('config/workshop.json'))
    repos = str_map(member(as_dict(load_json('config/repos.json'), 'config/repos.json'), 'repos', 'config/repos.json'), 'repos')

    # The covers of the released versions: the submodules hold what was released.
    subprocess.run([sys.executable, 'design/covers.py', EXPECTED], check=True, stdout=subprocess.DEVNULL)

    details = fetch_details(ids)
    # Each item costs two `gh` calls and a download: they are independent, so they run side by side, in order.
    with ThreadPoolExecutor() as pool:
        verdicts = list(pool.map(lambda kv: check(kv[0], kv[1], repos.get(kv[0], ''), details), ids.items()))
    for v in verdicts:
        print(v.line)
    tiles = [v.preview for v in verdicts if v.preview is not None]
    if tiles:
        contact_sheet(tiles).save(os.path.join(OUT, 'sheet.png'))
        print('previews in', OUT)
    return 0 if all(v.ok for v in verdicts) else 1


if __name__ == '__main__':
    sys.exit(main())
