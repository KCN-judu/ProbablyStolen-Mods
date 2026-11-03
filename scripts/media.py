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
import os
import shutil
import subprocess
import sys
import tempfile


def ffmpeg():
    exe = os.environ.get('FFMPEG') or shutil.which('ffmpeg')
    if exe:
        return exe
    try:
        import imageio_ffmpeg
        return imageio_ffmpeg.get_ffmpeg_exe()
    except ImportError:
        sys.exit('ffmpeg not found: put it on PATH, set FFMPEG, or run python -m pip install imageio-ffmpeg')


def run(args):
    subprocess.run([ffmpeg(), '-hide_banner', '-loglevel', 'error', '-y'] + args, check=True)


def has_audio(path):
    r = subprocess.run([ffmpeg(), '-hide_banner', '-i', path], capture_output=True, text=True)
    return 'Audio:' in r.stderr


def cut(src, dst, keeps):
    audio = has_audio(src)
    parts, labels = [], []
    for i, keep in enumerate(keeps):
        start, _, end = keep.partition('-')
        rng = f'start={float(start)}' + ('' if end in ('', 'end') else f':end={float(end)}')
        parts.append(f'[0:v]trim={rng},setpts=PTS-STARTPTS[v{i}]')
        labels.append(f'[v{i}]')
        if audio:
            parts.append(f'[0:a]atrim={rng},asetpts=PTS-STARTPTS[a{i}]')
            labels.append(f'[a{i}]')
    graph = ';'.join(parts) + ';' + ''.join(labels) + f'concat=n={len(keeps)}:v=1:a={1 if audio else 0}[v]' + ('[a]' if audio else '')
    maps = ['-map', '[v]'] + (['-map', '[a]', '-c:a', 'aac', '-b:a', '192k'] if audio else [])
    run(['-i', src, '-filter_complex', graph] + maps +
        ['-c:v', 'libx264', '-crf', '16', '-preset', 'slow', '-pix_fmt', 'yuv420p', '-movflags', '+faststart', dst])
    print(f'wrote {dst}')


def gif(src, dst, fps, width, max_mb):
    budget = max_mb * 1024 * 1024
    with tempfile.TemporaryDirectory() as tmp:
        trial = os.path.join(tmp, 'trial.gif')
        for w in (width, width * 5 // 6, width * 3 // 4):
            for colors in (128, 96, 64, 48):
                run(['-i', src, '-vf', f'fps={fps},scale={w}:-2:flags=area,split[a][b];'
                     f'[a]palettegen=max_colors={colors}:stats_mode=diff[p];[b][p]paletteuse=dither=none:diff_mode=rectangle',
                     trial])
                size = os.path.getsize(trial)
                print(f'  {w} px wide, {colors} colours: {size / 1048576:.1f} MB')
                if size <= budget:
                    shutil.copyfile(trial, dst)
                    print(f'wrote {dst}: {fps} fps, {w} px wide, {colors} colours, {size / 1048576:.1f} MB')
                    return
    sys.exit(f'no setting fits {max_mb} MB at {fps} fps; shorten the video (cut) or allow more')


def main():
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = p.add_subparsers(dest='command', required=True)
    c = sub.add_parser('cut', help='keep time ranges of a video')
    c.add_argument('src'); c.add_argument('dst')
    c.add_argument('--keep', action='append', required=True, help='START-END in seconds, END may be "end"')
    g = sub.add_parser('gif', help='make a GIF under a size budget, keeping the frame rate')
    g.add_argument('src'); g.add_argument('dst')
    g.add_argument('--fps', type=int, default=20)
    g.add_argument('--width', type=int, default=960)
    g.add_argument('--max-mb', type=float, default=9.5)
    a = p.parse_args()
    if a.command == 'cut':
        cut(a.src, a.dst, a.keep)
    else:
        gif(a.src, a.dst, a.fps, a.width, a.max_mb)


if __name__ == '__main__':
    main()
