#!/usr/bin/env python3
# Checks that every Workshop item is up to date with its latest release.
#   python scripts/workshop-status.py
# For each mod in config/workshop.json it reads, from Steam's public API, when the Workshop item was last updated
# and its preview image, and from GitHub (the gh CLI) the latest release and, up to its tag, the last commit that
# changed manifest.xml: the one that set the version, which always comes before the upload (the release commit
# itself may only add the Workshop link, which exists after the first upload). An item is current when it was
# updated after that commit and its preview is byte for byte the cover covers.py renders for the version in the
# mod's submodule, which is the released version. The previews are saved to dist/workshop-status/ with a sheet of all of
# them, sheet.png, to look at.
import io, json, os, subprocess, sys, urllib.parse, urllib.request
from datetime import datetime, timezone

root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
os.chdir(root)
sys.path.insert(0, os.path.join(root, 'design'))
from PIL import Image

out = 'dist/workshop-status'
expected = os.path.join(out, 'expected')
os.makedirs(expected, exist_ok=True)
conf = json.load(io.open('config/workshop.json', encoding='utf-8'))
repos = json.load(io.open('config/repos.json', encoding='utf-8'))['repos']

# The covers of the released versions: the submodules hold what was released.
subprocess.run([sys.executable, 'design/covers.py', expected], check=True, stdout=subprocess.DEVNULL)

slugs = list(conf['items'])
form = {'itemcount': len(slugs)}
for i, slug in enumerate(slugs):
    form[f'publishedfileids[{i}]'] = conf['items'][slug]['id']
url = 'https://api.steampowered.com/ISteamRemoteStorage/GetPublishedFileDetails/v1/'
details = json.load(urllib.request.urlopen(url, urllib.parse.urlencode(form).encode()))['response']['publishedfiledetails']
by_id = {d['publishedfileid']: d for d in details}


def latest_release(repo):
    r = subprocess.run(['gh', 'release', 'view', '-R', 'KCN-judu/' + repo, '--json', 'tagName'],
                       capture_output=True, text=True)
    if r.returncode != 0:
        return None, None
    tag = json.loads(r.stdout)['tagName']
    c = subprocess.run(['gh', 'api', f'repos/KCN-judu/{repo}/commits?sha={tag}&path=manifest.xml&per_page=1',
                        '--jq', '.[0].commit.committer.date'], capture_output=True, text=True)
    if c.returncode != 0:
        return tag, None
    return tag, datetime.fromisoformat(c.stdout.strip().replace('Z', '+00:00'))


ok = True
tiles = []
for slug in slugs:
    item = conf['items'][slug]
    d = by_id.get(item['id'], {})
    cover_id = slug.replace('-', '_')
    updated = datetime.fromtimestamp(d.get('time_updated', 0), timezone.utc)
    tag, released = latest_release(repos.get(slug, ''))
    preview = os.path.join(out, cover_id + '.png')
    if d.get('preview_url'):
        io.open(preview, 'wb').write(urllib.request.urlopen(d['preview_url']).read())
        tiles.append(preview)
    want = os.path.join(expected, cover_id + '.png')
    cover_ok = os.path.isfile(preview) and os.path.isfile(want) and \
        io.open(preview, 'rb').read() == io.open(want, 'rb').read()
    content_ok = released is not None and updated >= released
    ok &= cover_ok and content_ok
    print(f"{'ok  ' if cover_ok and content_ok else 'OLD '} {slug:26} release {tag or '?':8} "
          f"version set {released:%Y-%m-%d %H:%M} UTC, Workshop updated {updated:%Y-%m-%d %H:%M} UTC"
          f"{'' if content_ok else '  (content older than the release)'}"
          f"{'' if cover_ok else '  (cover differs from the released version)'}" if released else
          f"?    {slug:26} no release found")

if tiles:
    images = [Image.open(t).convert('RGB').resize((640, 360), Image.NEAREST) for t in tiles]
    rows = (len(images) + 1) // 2
    sheet = Image.new('RGB', (1280, 360 * rows), (0, 0, 0))
    for i, im in enumerate(images):
        sheet.paste(im, ((i % 2) * 640, (i // 2) * 360))
    sheet.save(os.path.join(out, 'sheet.png'))
    print('previews in', out)
sys.exit(0 if ok else 1)
