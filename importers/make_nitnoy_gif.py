#!/usr/bin/env python3
"""One Saturday in six seconds — the nitnoy stop-motion.

Draws the lamp map straight from data/open_lamps.json with Pillow, one frame
per half hour, and stitches the 48 into assets/nitnoy.gif: the morning kads
catch before dawn, the cafés at eight, the bars carry the night. Also saves
the 19:00 frame as assets/nitnoy_poster.png for og:image (link previews do
not animate; the site's own pages may use the GIF itself).

Same projection and same road underlay source as build.py's shared city
frame — the area box and edge deltas come from data/road_graph.json, so this
cannot drift from seven/walk/nitnoy.

Optional asset, same standing as make_og_cards.py: needs Pillow; without it
this script explains itself and exits, and nothing downstream cares.

    python3 importers/make_nitnoy_gif.py
"""
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent

try:
    from PIL import Image, ImageDraw, ImageFont
except ImportError:
    print("make_nitnoy_gif: Pillow not installed — skipped "
          "(pip3 install --user Pillow)")
    sys.exit(0)

LAMPS = json.loads((ROOT / "data" / "open_lamps.json").read_text())
RG = json.loads((ROOT / "data" / "road_graph.json").read_text())

GROUP_RGB = {
    "food": (246, 183, 60), "cafe": (240, 227, 176),
    "night": (177, 140, 255), "market": (255, 107, 94),
    "care": (255, 159, 199), "shop": (127, 216, 164),
    "other": (201, 212, 224),
}
NIGHT_BG = (13, 20, 32)
DAY_BG = (26, 38, 58)
ROAD_NIGHT = (34, 51, 74)
ROAD_DAY = (52, 72, 100)

S, N = RG["area"]["s"], RG["area"]["n"]
W, E = RG["area"]["w"], RG["area"]["e"]
import math
COSLA = math.cos(math.radians((S + N) / 2))
PW, PAD = 560, 8
PH = round(PW * (N - S) / ((E - W) * COSLA))
DAY = 5                     # Saturday — the liveliest day of the week
FRAME_MS = 110


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


def glow(rgb):
    d = 22
    im = Image.new("RGBA", (d, d), (0, 0, 0, 0))
    dr = ImageDraw.Draw(im)
    cx = d / 2
    for r, a in ((10, 30), (7, 70), (4.5, 140), (2.5, 255)):
        dr.ellipse([cx - r, cx - r, cx + r, cx + r], fill=rgb + (a,))
    return im


def blend(a, b, t):
    return tuple(round(x + (y - x) * t) for x, y in zip(a, b))


def daylight(minute):
    """0 = deep night, 1 = full day; dawn and dusk ease over an hour."""
    h = minute / 60.0
    if h < 5.5 or h >= 19.5:
        return 0.0
    if h < 6.5:
        return h - 5.5
    if h < 18.5:
        return 1.0
    return 19.5 - h


def main():
    roads = road_lines()
    sprites = {g: glow(c) for g, c in GROUP_RGB.items()}
    places = [(p["la"], p["ln"], p["g"], p["k"]) for p in LAMPS["places"]
              if S <= p["la"] <= N and W <= p["ln"] <= E]
    scheds = LAMPS["schedules"]

    font = None
    for cand in ("/System/Library/Fonts/Supplemental/Ayuthaya.ttf",):
        if Path(cand).exists():
            font = ImageFont.truetype(cand, 26)
            break

    frames = []
    poster = None
    for slot in range(48):
        minute = slot * 30
        t = daylight(minute)
        bg = blend(NIGHT_BG, DAY_BG, t)
        road = blend(ROAD_NIGHT, ROAD_DAY, t)
        im = Image.new("RGB", (PW + 2 * PAD, PH + 2 * PAD), bg)
        dr = ImageDraw.Draw(im)
        for line in roads:
            dr.line(line, fill=road, width=1)
        im = im.convert("RGBA")
        wk = DAY * 1440 + minute
        lit = 0
        for la, ln, g, k in places:
            if not any(a <= wk < b for a, b in scheds[k]):
                continue
            lit += 1
            x, y = px(la, ln)
            im.alpha_composite(sprites[g], (int(x) - 11, int(y) - 11))
        im = im.convert("RGB")
        dr = ImageDraw.Draw(im)
        label = "เสาร์ %02d:%02d" % (minute // 60, minute % 60)
        if font:
            dr.text((PAD + 10, PH + PAD - 40), label,
                    fill=(220, 228, 240), font=font)
            dr.text((PW + PAD - 10, PH + PAD - 40), "%d" % lit,
                    fill=(246, 183, 60), font=font, anchor="ra")
        frames.append(im)
        if minute == 1140:                       # 19:00 — the poster hour
            poster = im.copy()

    out = ROOT / "assets" / "nitnoy.gif"
    frames[0].save(out, save_all=True, append_images=frames[1:],
                   duration=FRAME_MS, loop=0, optimize=True)
    if poster is not None:
        poster.save(ROOT / "assets" / "nitnoy_poster.png", optimize=True)
    print("nitnoy.gif: %d frames, %dx%d, %.0f KB (+ poster)"
          % (len(frames), PW + 2 * PAD, PH + 2 * PAD,
             out.stat().st_size / 1024))


if __name__ == "__main__":
    main()
