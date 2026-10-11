#!/usr/bin/env python3
"""make_band_pics.py — small copies of the front-page band's photographs.

OPTIONAL, like make_og_cards.py and make_shelf_cards.py: it needs Pillow, and
build.py falls back to the full picture when this has not run
(`band_pic_file`). Nothing in the walk waits on it.

WHY. The 145 pictures Nan picked ship at their full size — 238 KB on average,
which is right for a picture somebody has scrolled to on a shelf page and
wrong for one standing at the very top of the front page. A 520 px-wide copy
of the widest card this band draws (168 CSS px, so 520 covers a 3× screen)
comes in around 50 KB. Same picture, same credit, same licence.

Redraws only what is missing or older than its source, so it is cheap enough
to run every walk.
"""

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
PICKS = ROOT / "data" / "curated" / "image_picks.json"
OWN = ROOT / "data" / "curated" / "own_pictures.json"
SRC = ROOT / "assets" / "site"
PLACE_SRC = ROOT / "assets" / "photos"
OUT = ROOT / "assets" / "band"
PLACE_OUT = OUT / "place"
WIDTH = 520


def main():
    try:
        from PIL import Image
    except ImportError:
        print("Pillow not installed — the band will use the full pictures.",
              file=sys.stderr)
        return 0
    if not PICKS.exists():
        print("no data/curated/image_picks.json", file=sys.stderr)
        return 0
    picks = [p for p in json.loads(PICKS.read_text())["picks"] if p.get("usable")]
    # Her own pictures too: the front page's "pictures near you" strip and the
    # route strip draw them at card size (pics_layer.thumb_of).
    if OWN.exists():
        picks += [p for p in json.loads(OWN.read_text())["picks"] if p.get("usable")]
    OUT.mkdir(parents=True, exist_ok=True)
    made = kept = 0
    for p in picks:
        src = SRC / (p["slug"] + ".jpg")
        if not src.exists():
            continue
        dst = OUT / (p["slug"] + ".jpg")
        if dst.exists() and dst.stat().st_mtime >= src.stat().st_mtime:
            kept += 1
            continue
        with Image.open(src) as im:
            im = im.convert("RGB")
            if im.width > WIDTH:
                im = im.resize((WIDTH, max(1, round(im.height * WIDTH / im.width))),
                               Image.LANCZOS)
            im.save(dst, "JPEG", quality=78, optimize=True, progressive=True)
        made += 1
    # The place photographs too — the band's ที่วันนี้ card draws one of the
    # 112 in assets/photos/, which average half a megabyte each.
    PLACE_OUT.mkdir(parents=True, exist_ok=True)
    if PLACE_SRC.exists():
        for src in sorted(PLACE_SRC.iterdir()):
            if src.suffix.lower() not in (".jpg", ".jpeg", ".png", ".webp"):
                continue
            dst = PLACE_OUT / (src.stem + ".jpg")
            if dst.exists() and dst.stat().st_mtime >= src.stat().st_mtime:
                kept += 1
                continue
            with Image.open(src) as im:
                im = im.convert("RGB")
                if im.width > WIDTH:
                    im = im.resize((WIDTH, max(1, round(im.height * WIDTH / im.width))),
                                   Image.LANCZOS)
                im.save(dst, "JPEG", quality=78, optimize=True, progressive=True)
            made += 1
    tot = sum(f.stat().st_size for f in OUT.rglob("*.jpg"))
    print(f"band pictures: {made} drawn, {kept} already current, "
          f"{tot / 1024:.0f} KB for {len(list(OUT.rglob('*.jpg')))} files")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
