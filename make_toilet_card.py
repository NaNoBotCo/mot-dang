#!/usr/bin/env python3
"""The toilets share card — assets/og/toilets.png, 1200x630.

The toilets page is the site's flagship answer, and it is exactly the page
people share at the moment somebody needs it — into a LINE group, mid-errand.
Until now that share unfurled as the generic brand card. This card is the
page's own argument as a poster: the real pin constellation (every walk-in
point and every mapped toilet the site holds, drawn from the same baked file
the page reads), the two counts with their two voices, and the tier icons
that make the model legible at a glance.

Same method as make_og_cards.py, for the same reason: Pillow here has no
raqm, so Thai marks would land in the wrong places — the card is HTML and a
headless Chrome takes the picture. The map is inline SVG, so the pins are
data, not decoration.

Reads docs/data/toilets.json (the baked file), so run it AFTER a build; the
card then rides into docs/og/ on the next build like every other og card:

    python3 build.py && python3 make_toilet_card.py && python3 build.py

The second build is what points toilets.html/app.html og:image at the card
(they check assets/og/toilets.png exists). The card only needs redrawing
when the toilet data or the design changes, not every build.
"""
import json
import math
import shutil
import subprocess
import tempfile
from pathlib import Path

from PIL import Image

import map_ground
from make_og_cards import find_chrome, crop, W, SHOT_H

ROOT = Path(__file__).resolve().parent
SRC = ROOT / "docs" / "data" / "toilets.json"
OUT = ROOT / "assets" / "og" / "toilets.png"

# One glyph per walk-in tier, same order the page lists them. Emoji, because
# Chrome sets Apple Color Emoji and the card is a picture — the sprite-icon
# accessibility reasoning that bans emoji in site nav does not apply here.
TIER_GLYPH = [("fuel", "⛽"), ("wat", "🛕"), ("mall", "🏬"), ("market", "🧺"),
              ("park", "🌳"), ("hospital", "🏥"), ("university", "🎓"),
              ("terminal", "🚌"), ("museum", "🖼")]

# Chiang Mai city frame — the card shows the constellation where it is
# densest; CR's points are a second constellation 140 km away that would
# shrink both to specks. Framed on the middle 90% of the CM points so a few
# far-district outliers cannot zoom the city out to a speck either.
LAT_MIN = LAT_MAX = LNG_MIN = LNG_MAX = 0.0

MAP_W, MAP_H = 470, 446


def set_frame(model):
    global LAT_MIN, LAT_MAX, LNG_MIN, LNG_MAX
    lats, lngs = [], []
    for row in model["places"]:
        la, ln = row[1], row[2]
        if 18.5 <= la <= 19.1 and 98.7 <= ln <= 99.3:   # CM only
            lats.append(la)
            lngs.append(ln)
    for row in model["verified"]:
        la, ln = row[0], row[1]
        if 18.5 <= la <= 19.1 and 98.7 <= ln <= 99.3:
            lats.append(la)
            lngs.append(ln)
    lats.sort()
    lngs.sort()
    lo, hi = int(len(lats) * 0.05), int(len(lats) * 0.95)
    pad_la = (lats[hi] - lats[lo]) * 0.10
    pad_ln = (lngs[hi] - lngs[lo]) * 0.10
    LAT_MIN, LAT_MAX = lats[lo] - pad_la, lats[hi] + pad_la
    LNG_MIN, LNG_MAX = lngs[lo] - pad_ln, lngs[hi] + pad_ln


def project(lat, lng):
    """Equirectangular with cos(lat) correction, fitted to the panel."""
    kx = math.cos(math.radians((LAT_MIN + LAT_MAX) / 2))
    span_x = (LNG_MAX - LNG_MIN) * kx
    span_y = LAT_MAX - LAT_MIN
    scale = min(MAP_W / span_x, MAP_H / span_y)
    x = (lng - LNG_MIN) * kx * scale + (MAP_W - span_x * scale) / 2
    y = (LAT_MAX - lat) * scale + (MAP_H - span_y * scale) / 2
    return round(x, 1), round(y, 1)


def ground_image():
    """The city, at night, under the constellation.

    The panel was a dark rectangle with dots on it, which showed the SHAPE of
    the constellation and nothing about where any of it is: an outsider could
    not tell the old city from the airport. The same points over the night
    ground read as a city with a moat in it, and the shape survives, because
    the ground is held well below the lamps.

    Painted through this file's own project(), so a lamp and the soi under it
    are placed by one function. Returns an <image> element, or "" when there is
    no archive and the flat rectangle stands as it always has.
    """
    g = map_ground.shared(night=True)
    if not g.available:
        return ""
    kx = math.cos(math.radians((LAT_MIN + LAT_MAX) / 2))
    span_x = (LNG_MAX - LNG_MIN) * kx
    span_y = LAT_MAX - LAT_MIN
    scale = min(MAP_W / span_x, MAP_H / span_y)
    offx = (MAP_W - span_x * scale) / 2
    offy = (MAP_H - span_y * scale) / 2
    # project() letterboxes the frame, so the panel covers MORE ground than
    # LAT/LNG_MIN..MAX on one axis. Ask for what the panel actually shows by
    # inverting the corners, or the ground stops short of the edge.
    w = LNG_MIN + (0 - offx) / (kx * scale)
    e = LNG_MIN + (MAP_W - offx) / (kx * scale)
    n = LAT_MAX - (0 - offy) / scale
    s = LAT_MAX - (MAP_H - offy) / scale
    im = Image.new("RGB", (MAP_W, MAP_H), g.palette["paper"])
    if not g.paint(im, lambda p: project(p[0], p[1]), (s, w, n, e),
                   width_px=MAP_W, zoom=g.zoom_for((s, w, n, e), MAP_W, 256),
                   buildings=False, fade=0.75, contrast=1.25):
        return ""
    map_ground.credit_mark(im, dark=True, inset=14)
    return ('<image x="0" y="0" width="%d" height="%d" href="%s"/>'
            % (MAP_W, MAP_H, map_ground.data_uri(im)))


def map_svg(model):
    dots, lamps = [], []
    n_in = 0
    for row in model["places"]:
        lat, lng = row[1], row[2]
        if not (LAT_MIN <= lat <= LAT_MAX and LNG_MIN <= lng <= LNG_MAX):
            continue
        n_in += 1
        x, y = project(lat, lng)
        dots.append(f'<circle cx="{x}" cy="{y}" r="2.6" fill="#b3540f" opacity=".8"/>')
    for row in model["verified"]:
        lat, lng = row[0], row[1]
        if not (LAT_MIN <= lat <= LAT_MAX and LNG_MIN <= lng <= LNG_MAX):
            continue
        n_in += 1
        x, y = project(lat, lng)
        lamps.append(
            f'<circle cx="{x}" cy="{y}" r="5.5" fill="#f6b73c" opacity=".22"/>'
            f'<circle cx="{x}" cy="{y}" r="2.8" fill="#f6b73c"/>')
    moat = " ".join("%g,%g" % project(la, ln) for la, ln in model["moat"])
    return (
        f'<svg viewBox="0 0 {MAP_W} {MAP_H}" width="{MAP_W}" height="{MAP_H}" '
        'xmlns="http://www.w3.org/2000/svg">'
        f'<defs><clipPath id="panel"><rect width="{MAP_W}" height="{MAP_H}" rx="18"/>'
        '</clipPath></defs>'
        f'<g clip-path="url(#panel)">'
        f'<rect width="{MAP_W}" height="{MAP_H}" fill="#0d1420"/>{ground_image()}</g>'
        + "".join(dots) + "".join(lamps) +
        f'<polygon points="{moat}" fill="none" stroke="#a8c6ee" '
        'stroke-width="3" stroke-dasharray="8 6"/>'
        "</svg>"), n_in


def card_html(model):
    walkin = len(model["places"])
    mapped = len(model["verified"])
    svg, n_in = map_svg(model)
    chips = "".join(
        f'<span class="chip">{g} {next(t["th"] for t in model["tiers"] if t["key"] == k)}</span>'
        for k, g in TIER_GLYPH[:6])
    return f"""<!DOCTYPE html><html lang="th"><head><meta charset="utf-8"><style>
*{{box-sizing:border-box;margin:0;padding:0}}
html,body{{width:1200px;height:630px;overflow:hidden}}
body{{background:#FBF6EE;color:#2A1E16;position:relative;
font-family:"Noto Sans Thai","IBM Plex Sans Thai","Sarabun","Arial Unicode MS",
 "Helvetica Neue",Arial,sans-serif}}
.rule{{position:absolute;left:44px;right:44px;height:5px;box-sizing:content-box;
border-top:5px solid #C2401C;border-bottom:5px solid #C2401C}}
.rule.t{{top:32px}} .rule.b{{top:583px}}
.left{{position:absolute;left:60px;top:74px;bottom:72px;width:600px;
display:flex;flex-direction:column}}
.kicker{{font-size:25px;color:#8F2E13;display:flex;gap:12px;align-items:center;
white-space:nowrap}}
.kicker .g{{font-size:34px;line-height:1}}
h1{{font-size:76px;line-height:1.06;font-weight:800;margin:8px 0 4px;
letter-spacing:-1px;white-space:nowrap}}
.en{{font-size:26px;color:#6B5A48;line-height:1.25}}
.nums{{display:flex;gap:40px;margin:18px 0 0}}
.num b{{display:block;font-size:54px;line-height:1;color:#C2401C;
font-variant-numeric:tabular-nums}}
.num span{{display:block;font-size:20px;color:#6B5A48;margin-top:6px;
line-height:1.25}}
.chips{{margin-top:16px;display:flex;flex-wrap:wrap;gap:8px;max-width:560px}}
.chip{{font-size:19px;background:#F1E5D3;border-radius:999px;
padding:4px 14px;white-space:nowrap}}
.foot{{margin-top:auto;display:flex;align-items:flex-end;
justify-content:space-between}}
.brand{{font-size:30px;font-weight:700;color:#C2401C;line-height:1.15}}
.brand small{{display:block;font-size:19px;font-weight:400;color:#6B5A48;
letter-spacing:.05em}}
.mappanel{{position:absolute;right:56px;top:80px;width:{MAP_W}px}}
.mappanel svg{{display:block;box-shadow:0 10px 34px #0004;border-radius:18px}}
.cap{{font-size:18.5px;color:#6B5A48;margin-top:11px;line-height:1.35;
text-align:center}}
.cap i{{font-style:normal}}
.cap .amber{{color:#a97b12}} .cap .rust{{color:#b3540f}}
</style></head><body>
<div class="rule t"></div>
<div class="left">
  <div class="kicker"><span class="g">🚻</span>
    <span>เชียงใหม่ · เชียงราย — ทั้งเมือง หน้าเดียว</span></div>
  <h1>ห้องน้ำใกล้ฉัน</h1>
  <div class="en">Toilets near you — the whole city, mapped</div>
  <div class="nums">
    <div class="num"><b>{mapped}</b><span>จุดที่ปักหมุดไว้จริง<br>mapped for certain</span></div>
    <div class="num"><b>{walkin:,}</b><span>ที่ที่เดินเข้าไปได้เลย<br>walk-in places</span></div>
  </div>
  <div class="chips">{chips}</div>
  <div class="foot">
    <div class="brand">🐜 มดแดง<small>motdang.net/toilets</small></div>
  </div>
</div>
<div class="mappanel">{svg}
  <div class="cap"><i class="amber">●</i> ปักหมุดจริง · <i class="rust">●</i> เดินเข้าได้ · ▢ คูเมือง ({n_in:,} จุดในกรอบ)</div>
</div>
<div class="rule b"></div>
</body></html>"""


def main():
    if not SRC.exists():
        raise SystemExit("docs/data/toilets.json not found — run python3 build.py first")
    model = json.loads(SRC.read_text())
    set_frame(model)
    chrome = find_chrome()
    OUT.parent.mkdir(parents=True, exist_ok=True)
    tmp = Path(tempfile.mkdtemp(prefix="toiletcard-"))
    src = tmp / "card.html"
    src.write_text(card_html(model), encoding="utf-8")
    subprocess.run([
        chrome, "--headless", "--disable-gpu", "--hide-scrollbars",
        "--no-sandbox", "--force-device-scale-factor=1",
        "--window-size=1200,%d" % SHOT_H, "--screenshot=" + str(OUT),
        src.as_uri()],
        check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    crop(OUT)
    # ride into the current docs/ too, so a rebuild is not required just to
    # see the card — the next build copies it again like any og asset
    live = ROOT / "docs" / "og"
    if live.exists():
        shutil.copyfile(OUT, live / "toilets.png")
    print(f"wrote {OUT} ({OUT.stat().st_size // 1024} KB) "
          f"— {len(model['verified'])} mapped, {len(model['places']):,} walk-in drawn")


if __name__ == "__main__":
    main()
