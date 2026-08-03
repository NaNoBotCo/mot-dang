#!/usr/bin/env python3
"""The taste of the town, one still — assets/taste_poster.png.

Draws /taste.html's dot map with Pillow for og:image and shares. Same
projection source as everything else (data/road_graph.json), same family
colors as data/taste.json — read from that file, never restated here.

Optional asset like make_og_cards.py: needs Pillow; explains itself and
exits without it.

    python3 importers/make_taste_poster.py
"""
import json
import math
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent

try:
    from PIL import Image, ImageDraw, ImageFont
except ImportError:
    print("make_taste_poster: Pillow not installed — skipped")
    sys.exit(0)

TASTE = json.loads((ROOT / "data" / "taste.json").read_text())
RG = json.loads((ROOT / "data" / "road_graph.json").read_text())

S, N = RG["area"]["s"], RG["area"]["n"]
W, E = RG["area"]["w"], RG["area"]["e"]
COSLA = math.cos(math.radians((S + N) / 2))
PW, PAD = 560, 8
PH = round(PW * (N - S) / ((E - W) * COSLA))
BG, ROAD = (13, 20, 32), (34, 51, 74)


def px(la, ln):
    return (PAD + (ln - W) / (E - W) * PW,
            PAD + PH - (la - S) / (N - S) * PH)


def road_lines():
    rs = RG["scale"]
    rnodes = [(p[0] / rs, p[1] / rs) for p in RG["nodes"]]
    lines = []
    for e in RG["edges"]:
        pts = [rnodes[e[0]]]
        deltas = e[4] if len(e) > 4 else []
        la = ln = 0
        for k in range(0, len(deltas), 2):
            if k == 0:
                la, ln = deltas[0], deltas[1]
            else:
                la += deltas[k]
                ln += deltas[k + 1]
            pts.append((la / rs, ln / rs))
        pts.append(rnodes[e[1]])
        lines.append([px(a, b) for a, b in pts])
    return lines


def hex_rgb(h):
    h = h.lstrip("#")
    return tuple(int(h[i:i + 2], 16) for i in (0, 2, 4))


def glow(rgb):
    d = 16
    im = Image.new("RGBA", (d, d), (0, 0, 0, 0))
    dr = ImageDraw.Draw(im)
    c = d / 2
    for r, a in ((7, 40), (4.5, 110), (2.2, 255)):
        dr.ellipse([c - r, c - r, c + r, c + r], fill=rgb + (a,))
    return im


def main():
    colors = {f["key"]: hex_rgb(f["color"]) for f in TASTE["families"]}
    sprites = {k: glow(c) for k, c in colors.items()}
    im = Image.new("RGB", (PW + 2 * PAD, PH + 2 * PAD), BG)
    dr = ImageDraw.Draw(im)
    for line in road_lines():
        dr.line(line, fill=ROAD, width=1)
    im = im.convert("RGBA")
    for d in TASTE["dots"]:
        if not (S <= d["la"] <= N and W <= d["ln"] <= E):
            continue
        x, y = px(d["la"], d["ln"])
        im.alpha_composite(sprites[d["f"]], (int(x) - 8, int(y) - 8))
    im = im.convert("RGB")
    dr = ImageDraw.Draw(im)
    for cand in ("/System/Library/Fonts/Supplemental/Ayuthaya.ttf",):
        if Path(cand).exists():
            font = ImageFont.truetype(cand, 26)
            dr.text((PAD + 10, PH + PAD - 40), "รสเมือง",
                    fill=(220, 228, 240), font=font)
            break
    out = ROOT / "assets" / "taste_poster.png"
    im.save(out, optimize=True)
    print("taste_poster.png: %dx%d, %.0f KB"
          % (im.width, im.height, out.stat().st_size / 1024))


if __name__ == "__main__":
    main()
