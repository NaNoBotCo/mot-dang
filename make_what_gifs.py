#!/usr/bin/env python3
"""Web-weight copies of the two demo loops, for what.html — assets/show/*.gif.

what.html is the page people are *sent*, which means it is opened on a phone,
on mobile data, in the middle of a conversation. assets/nitnoy.gif is 876 KB
and assets/plan-afternoon.gif is 189 KB at full size — a megabyte of loops on
a page whose whole job is to load before the reader loses interest.

So this makes smaller copies: half the frames for the day loop (a half-hour
step reads the same as a quarter-hour one when the city is the subject),
narrower pixels for both, and a shared 128-colour palette. Nothing is redrawn
here and no frame is invented — these are the same pictures the makers drew
from data/open_lamps.json and the road graph, only lighter.

The originals stay the originals: make_nitnoy_gif.py and make_plan_demo.py own
those, and this script refuses to run if they have not been made yet.

    python3 make_what_gifs.py

Run before build.py, which copies assets/show/ into docs/show/.
"""
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent
OUT = ROOT / "assets" / "show"

try:
    from PIL import Image
except ImportError:
    print("make_what_gifs: Pillow not installed — skipped "
          "(pip3 install --user Pillow)")
    sys.exit(0)

# (source, destination, target width, keep every Nth frame, palette size)
# The day loop is the expensive one: a thousand lights twinkling means almost
# every pixel changes between frames, so delta encoding saves little and the
# size has to come out of frames, pixels and colours instead. Every third
# frame is a 90-minute step, which still reads as a day passing. Measured:
# 877 KB at full rate, ~520 KB here.
JOBS = [
    ("nitnoy.gif", "day.gif", 400, 3, 96),
    ("plan-afternoon.gif", "plan.gif", 470, 1, 128),
]


def shrink(src, dst, width, step, colors):
    with Image.open(src) as im:
        n = getattr(im, "n_frames", 1)
        durations, frames = [], []
        for i in range(0, n, step):
            im.seek(i)
            # Frame duration is per-frame in a GIF, so dropping every other
            # frame without adding its time back speeds the loop up. The kept
            # frame inherits the time of the ones it replaces.
            d = 0
            for j in range(i, min(i + step, n)):
                im.seek(j)
                d += im.info.get("duration", 100)
            im.seek(i)
            f = im.convert("RGB")
            h = round(f.height * width / f.width)
            frames.append(f.resize((width, h), Image.LANCZOS))
            durations.append(d)
    if not frames:
        return None
    # One palette for the whole loop: a per-frame palette makes the ground
    # shimmer between frames, which on the day loop reads as the map itself
    # flickering rather than the shops opening.
    #
    # The palette is read from every frame stacked together, not from the
    # first one. Built from frame 0 it was sampled at midnight, when 218
    # places are open and nearly all of them are green — so the oranges of
    # the lunch hour and the purples of the bars had nowhere to land and the
    # whole day came out green. On this loop the colours ARE the meaning:
    # each one is a kind of place, so losing them loses the picture.
    strip = Image.new("RGB", (frames[0].width, frames[0].height * len(frames)))
    for i, f in enumerate(frames):
        strip.paste(f, (0, i * f.height))
    pal = strip.quantize(colors=colors, method=Image.Quantize.MEDIANCUT)
    conv = [f.quantize(palette=pal, dither=Image.Dither.NONE) for f in frames]
    # No disposal setting on purpose. "Restore to background" forces every
    # frame to be stored whole, which turned a 877 KB loop into 2.9 MB the
    # first time this ran; leaving it alone lets the writer store only the
    # rectangle that actually changed between frames.
    conv[0].save(dst, save_all=True, append_images=conv[1:],
                 duration=durations, loop=0, optimize=True)
    return dst


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    made = 0
    for src_name, dst_name, width, step, colors in JOBS:
        src = ROOT / "assets" / src_name
        if not src.exists():
            print("  ! %s missing — run its own maker first, skipped" % src_name)
            continue
        dst = OUT / dst_name
        shrink(src, dst, width, step, colors)
        print("  %-18s %6.0f KB -> %-9s %6.0f KB"
              % (src_name, src.stat().st_size / 1024,
                 dst_name, dst.stat().st_size / 1024))
        made += 1
    if not made:
        sys.exit("no source loops found in assets/ — nothing made.")


if __name__ == "__main__":
    main()
