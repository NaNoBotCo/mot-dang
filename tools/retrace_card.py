#!/usr/bin/env python3
"""assets/sites/retrace/card.jpg (1200x630): the old city drawn from the site's own road and water data,
three numbered wats joined by the marigold band, and the title."""
import json
import math
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont

ROOT = Path(__file__).resolve().parent.parent
SITE = ROOT / "assets" / "sites" / "retrace"
W, H = 1200, 630
LAT0, LNG0 = 18.788, 98.9875
KY = 110574
KX = 111320 * math.cos(math.radians(LAT0))
S3 = 3  # supersample


def main():
    rd = json.loads((SITE / "data" / "roads.json").read_text())
    wt = json.loads((SITE / "data" / "water.json").read_text())
    pl = json.loads((SITE / "data" / "places.json").read_text())
    S = rd["scale"]
    nodes = rd["nodes"]
    img = Image.new("RGB", (W * S3, H * S3), "#efe5cf")
    d = ImageDraw.Draw(img)
    # map window: right 62% of the card, metres per pixel 2.9
    m = 1.25
    cx, cy = -318, -92
    ox = W * 0.73

    def P(x, y):
        return ((x - cx) / m + ox) * S3, ((y - cy) / m + H / 2) * S3

    def xy(la, lo):
        return (lo / S - LNG0) * KX, -(la / S - LAT0) * KY

    for r in wt["rings"]:
        la = lo = 0
        pts = []
        for i in range(0, len(r), 2):
            la, lo = (r[0], r[1]) if i == 0 else (la + r[i], lo + r[i + 1])
            pts.append(P(*xy(la, lo)))
        d.polygon(pts, fill="#a9d3cc", outline="#86b9b0")
    roads = []
    for e in rd["edges"]:
        a, b, ln, fl, dl = e
        la, lo = nodes[a]
        pts = [xy(la, lo)]
        la2 = lo2 = 0
        for k in range(0, len(dl), 2):
            la2, lo2 = (dl[0], dl[1]) if k == 0 else (la2 + dl[k], lo2 + dl[k + 1])
            pts.append(xy(la2, lo2))
        la, lo = nodes[b]
        pts.append(xy(la, lo))
        roads.append((fl, [P(*p) for p in pts]))
    for fl, pts in roads:
        if not fl & 12:
            d.line(pts, fill="#d3c19b", width=2 * S3 // 2)
    for fl, pts in roads:
        if fl & 12:
            d.line(pts, fill="#c9b88f", width=int(8.5 * S3), joint="curve")
    for fl, pts in roads:
        if fl & 12:
            d.line(pts, fill="#fffaf0", width=int(6 * S3), joint="curve")
    wats = {r[0]: r for r in pl if r[1] == "w"}
    pick = [k for k in ("cm-osm-way-242930163", "cm-osm-way-242929634", "cm-osm-way-242929545") if k in wats]
    pts = []
    for k in pick:
        r = wats[k]
        pts.append(P((r[3] - LNG0) * KX, -(r[2] - LAT0) * KY))
    if len(pts) == 3:
        d.line(pts, fill="#f5c85a", width=int(46 * S3), joint="curve")
        d.line(pts, fill="#7a3b00", width=int(3 * S3))
        f = ImageFont.truetype("/System/Library/Fonts/Supplemental/Arial Black.ttf", 22 * S3)
        for i, (x, y) in enumerate(pts):
            d.ellipse((x - 20 * S3, y - 20 * S3, x + 20 * S3, y + 20 * S3), fill="#f2a900", outline="#2b1a00", width=4 * S3)
            d.text((x, y), str(i + 1), font=f, fill="#000", anchor="mm")
    # left panel
    d.rectangle((0, 0, int(W * 0.46) * S3, H * S3), fill="#17120d")
    d.polygon([(int(W * 0.46) * S3, 0), (int(W * 0.46 + 38) * S3, 0), (int(W * 0.46) * S3, H * S3)], fill="#17120d")
    big = ImageFont.truetype("/System/Library/Fonts/Supplemental/Arial Black.ttf", 86 * S3)
    th = ImageFont.truetype("/System/Library/Fonts/Thonburi.ttc", 70 * S3, index=1)
    sm = ImageFont.truetype("/System/Library/Fonts/Thonburi.ttc", 30 * S3, index=0)
    d.text((50 * S3, 96 * S3), "CHIANG MAI OLD CITY", font=ImageFont.truetype("/System/Library/Fonts/HelveticaNeue.ttc", 24 * S3, index=1), fill="#f2a900")
    d.text((46 * S3, 170 * S3), "RETRACE", font=big, fill="#f3ecd8")
    for i, ln in enumerate(["Tap the wats you passed.", "See the walk, the sun, the street."]):
        d.text((50 * S3, (330 + i * 42) * S3), ln, font=ImageFont.truetype("/System/Library/Fonts/HelveticaNeue.ttc", 30 * S3), fill="#eadfc8")
    d.rounded_rectangle((48 * S3, 500 * S3, 330 * S3, 560 * S3), radius=12 * S3, fill="#f2a900", outline="#000", width=3 * S3)
    d.text((189 * S3, 530 * S3), "motdang.net/sites/retrace", font=ImageFont.truetype("/System/Library/Fonts/HelveticaNeue.ttc", 22 * S3, index=1), fill="#000", anchor="mm")
    out = img.resize((W, H), Image.LANCZOS)
    out.save(SITE / "card.jpg", quality=88, optimize=True)
    print((SITE / "card.jpg").stat().st_size)


if __name__ == "__main__":
    main()
