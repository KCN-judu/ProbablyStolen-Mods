#!/usr/bin/env python3
"""Prepares comparison videos for release pages: cuts parts out of a video and makes GIFs under a size budget.

    python scripts/media.py cut in.mp4 out.mp4 --keep 0-1.5 --keep 4.667-end
    python scripts/media.py gif in.mp4 out.gif [--fps 20] [--width 960] [--max-mb 9.5]

cut keeps the given time ranges (seconds, "end" for the end) in order and joins them, video and audio, as H.264
at near-lossless quality; the source is never changed. Shortening a cover or a title card is one cut.

gif converts a video for Discord, GitHub or the documentation. The frame rate is kept, because a GIF that drops
frames hides the stutters a comparison is meant to show; to fit the budget it lowers the number of colours first
(128, 96, 64, 48) and only then the width. Pixel art stays crisp at half of 1080p (960), so that is the default
width. Discord's upload limit without Nitro is 10 MB, hence the default budget.

Needs ffmpeg: on PATH, in the FFMPEG environment variable, or from the imageio-ffmpeg package
(python -m pip install imageio-ffmpeg).
"""
import argparse
import importlib
import os
import shutil
import subprocess
import sys
import tempfile
from collections.abc import Sequence
from dataclasses import dataclass
from functools import cache
from typing import cast


# ffmpeg is looked up once: FFMPEG, then PATH, then the binary bundled with the optional imageio-ffmpeg package.
@cache
def ffmpeg() -> str:
    exe = os.environ.get('FFMPEG') or shutil.which('ffmpeg')
    if exe:
        return exe
    try:
        found: object = importlib.import_module('imageio_ffmpeg').get_ffmpeg_exe()
    except ImportError:
        found = None
    if not isinstance(found, str):
        sys.exit('ffmpeg not found: put it on PATH, set FFMPEG, or run python -m pip install imageio-ffmpeg')
    return found


# -y overwrites the output; -loglevel error keeps ffmpeg quiet so the script's own progress lines stay readable.
def run(args: Sequence[str]) -> None:
    subprocess.run([ffmpeg(), '-hide_banner', '-loglevel', 'error', '-y', *args], check=True)


# Probes with `ffmpeg -i` (no output file, so it exits non-zero on purpose) and reads the stream list from stderr; no ffprobe needed.
def has_audio(path: str) -> bool:
    r = subprocess.run([ffmpeg(), '-hide_banner', '-i', path], capture_output=True, text=True)
    return 'Audio:' in r.stderr


def trim_range(keep: str) -> str:
    """'START-END' in seconds, END possibly 'end', as the arguments of the trim filters."""
    start, _, end = keep.partition('-')
    return f'start={float(start)}' + ('' if end in ('', 'end') else f':end={float(end)}')


def filter_graph(keeps: Sequence[str], audio: bool) -> str:
    """The filter graph that trims every kept range of the video (and audio) and concatenates them."""
    ranges = [trim_range(k) for k in keeps]
    parts = [p for i, rng in enumerate(ranges)
             for p in [f'[0:v]trim={rng},setpts=PTS-STARTPTS[v{i}]'] + ([f'[0:a]atrim={rng},asetpts=PTS-STARTPTS[a{i}]'] if audio else [])]
    labels = ''.join(f'[v{i}]' + (f'[a{i}]' if audio else '') for i in range(len(ranges)))
    return ';'.join(parts) + ';' + labels + f'concat=n={len(ranges)}:v=1:a={1 if audio else 0}[v]' + ('[a]' if audio else '')


# Re-encodes (libx264 crf 16, AAC 192k) because a cut between keyframes cannot be stream-copied; +faststart lets web players start early.
def cut(src: str, dst: str, keeps: Sequence[str]) -> None:
    audio = has_audio(src)
    maps = ['-map', '[v]'] + (['-map', '[a]', '-c:a', 'aac', '-b:a', '192k'] if audio else [])
    run(['-i', src, '-filter_complex', filter_graph(keeps, audio), *maps,
         '-c:v', 'libx264', '-crf', '16', '-preset', 'slow', '-pix_fmt', 'yuv420p', '-movflags', '+faststart', dst])
    print(f'wrote {dst}')


# One shared palette for the whole clip (stats_mode=diff favours moving areas), no dithering and rectangle diffs keep flat UI colours
# clean and the file small.
def gif_filter(fps: int, w: int, colors: int) -> str:
    return (f'fps={fps},scale={w}:-2:flags=area,split[a][b];'
            f'[a]palettegen=max_colors={colors}:stats_mode=diff[p];[b][p]paletteuse=dither=none:diff_mode=rectangle')


# Tries the widest/most colourful setting first and steps down (width, then colours) until the file fits the budget; the frame rate
# is never reduced, so the clip keeps its timing.
def gif(src: str, dst: str, fps: int, width: int, max_mb: float) -> None:
    budget = max_mb * 1024 * 1024
    with tempfile.TemporaryDirectory() as tmp:
        trial = os.path.join(tmp, 'trial.gif')
        for w in (width, width * 5 // 6, width * 3 // 4):
            for colors in (128, 96, 64, 48):
                run(['-i', src, '-vf', gif_filter(fps, w, colors), trial])
                size = os.path.getsize(trial)
                print(f'  {w} px wide, {colors} colours: {size / 1048576:.1f} MB')
                if size <= budget:
                    shutil.copyfile(trial, dst)
                    print(f'wrote {dst}: {fps} fps, {w} px wide, {colors} colours, {size / 1048576:.1f} MB')
                    return
    sys.exit(f'no setting fits {max_mb} MB at {fps} fps; shorten the video (cut) or allow more')


@dataclass(frozen=True)
class CutCommand:
    src: str
    dst: str
    keeps: Sequence[str]


@dataclass(frozen=True)
class GifCommand:
    src: str
    dst: str
    fps: int
    width: int
    max_mb: float


def parse_args(argv: Sequence[str]) -> CutCommand | GifCommand:
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = p.add_subparsers(dest='command', required=True)
    c = sub.add_parser('cut', help='keep time ranges of a video')
    c.add_argument('src')
    c.add_argument('dst')
    c.add_argument('--keep', action='append', required=True, help='START-END in seconds, END may be "end"')
    g = sub.add_parser('gif', help='make a GIF under a size budget, keeping the frame rate')
    g.add_argument('src')
    g.add_argument('dst')
    g.add_argument('--fps', type=int, default=20)
    g.add_argument('--width', type=int, default=960)
    g.add_argument('--max-mb', type=float, default=9.5)
    a = p.parse_args(argv)
    if a.command == 'cut':
        return CutCommand(str(a.src), str(a.dst), [str(k) for k in cast('list[object]', a.keep)])
    return GifCommand(str(a.src), str(a.dst), int(a.fps), int(a.width), float(a.max_mb))


def main(argv: Sequence[str]) -> None:
    cmd = parse_args(argv)
    if isinstance(cmd, CutCommand):
        cut(cmd.src, cmd.dst, cmd.keeps)
    else:
        gif(cmd.src, cmd.dst, cmd.fps, cmd.width, cmd.max_mb)


if __name__ == '__main__':
    main(sys.argv[1:])
