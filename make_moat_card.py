#!/usr/bin/env python3
"""The moat page's share card — assets/og/moat.png, 1200x630. WO-37.

The moat page answers the question this city sorts every address by, and it
is a page made to be shared mid-argument — ในเวียงก่อ? — into a LINE group.
Until now that share unfurled as the generic brand card. This card is the
page's argument as a poster: the real square over the night ground, its nine
named crossings lit, and the count of ways to read it.

Same method as make_toilet_card.py, for the same reasons: Pillow here has no
raqm so Thai marks land wrong — the card is HTML and a headless Chrome takes
the picture; the map is inline SVG so the crossings are data, not decoration.

Geometry comes from data/canonical/cm.json through the same pin ids build.py
holds in MOAT_CORNER_IDS / MOAT_CROSSING_IDS — the catalogue's own pins,
never typed here (ride_rules' 372 m lesson). Run any time; the card rides
into docs/og/ immediately and again on every later build:

    python3 make_moat_card.py
"""
import json
import math
import shutil
import subprocess
import tempfile
from pathlib import Path

from PIL import Image

import map_ground
from make_og_cards import find_chrome, crop, SHOT_H

ROOT = Path(__file__).resolve().parent
SRC = ROOT / "data" / "canonical" / "cm.json"
OUT = ROOT / "assets" / "og" / "moat.png"

# Same ids as build.py — nw, ne, se, sw and the five gates.
CORNER_IDS = ["cm-osm-way-317516852", "cm-osm-way-263459882",
              "cm-osm-way-791602197", "cm-osm-way-317516851"]
GATE_IDS = ["cm-osm-node-11229077788", "cm-osm-node-1017379824",
            "cm-osm-node-6107975995", "cm-osm-node-11226724529",
            "cm-osm-node-6717438786"]

MAP_W, MAP_H = 470, 470
LAT_MIN = LAT_MAX = LNG_MIN = LNG_MAX = 0.0


def set_frame(poly):
    global LAT_MIN, LAT_MAX, LNG_MIN, LNG_MAX
    pad = 0.0042                                    # ~460 m of night city
    LAT_MIN = min(p[0] for p in poly) - pad
    LAT_MAX = max(p[0] for p in poly) + pad
    LNG_MIN = min(p[1] for p in poly) - pad
    LNG_MAX = max(p[1] for p in poly) + pad


def project(lat, lng):
    kx = math.cos(math.radians((LAT_MIN + LAT_MAX) / 2))
    span_x = (LNG_MAX - LNG_MIN) * kx
    span_y = LAT_MAX - LAT_MIN
    scale = min(MAP_W / span_x, MAP_H / span_y)
    x = (lng - LNG_MIN) * kx * scale + (MAP_W - span_x * scale) / 2
    y = (LAT_MAX - lat) * scale + (MAP_H - span_y * scale) / 2
    return round(x, 1), round(y, 1)


def ground_image():
    """The old city at night under the square — same treatment as the
    toilets card, held well below the lamps. Returns "" when there is no
    tile archive and the flat night rectangle stands instead."""
    g = map_ground.shared(night=True)
    if not g.available:
        return ""
    kx = math.cos(math.radians((LAT_MIN + LAT_MAX) / 2))
    span_x = (LNG_MAX - LNG_MIN) * kx
    span_y = LAT_MAX - LAT_MIN
    scale = min(MAP_W / span_x, MAP_H / span_y)
    offx = (MAP_W - span_x * scale) / 2
    offy = (MAP_H - span_y * scale) / 2
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


def map_svg(poly, gates, corners):
    ring = " ".join("%g,%g" % project(la, ln) for la, ln in poly)
    lamps = []
    for la, ln, kind in ([(g[0], g[1], "gate") for g in gates]
                         + [(c[0], c[1], "corner") for c in corners]):
        x, y = project(la, ln)
        lamps.append(f'<circle cx="{x}" cy="{y}" r="9" fill="#f6b73c" opacity=".25"/>')
        if kind == "gate":
            lamps.append(f'<rect x="{x-4}" y="{y-4}" width="8" height="8" '
                         'fill="#f6b73c" stroke="#0d1420" stroke-width="1.5"/>')
        else:
            lamps.append(f'<circle cx="{x}" cy="{y}" r="4.4" fill="#f6b73c" '
                         'stroke="#0d1420" stroke-width="1.5"/>')
    cx, cy = project((min(p[0] for p in poly) + max(p[0] for p in poly)) / 2,
                     (min(p[1] for p in poly) + max(p[1] for p in poly)) / 2)
    return (
        f'<svg viewBox="0 0 {MAP_W} {MAP_H}" width="{MAP_W}" height="{MAP_H}" '
        'xmlns="http://www.w3.org/2000/svg">'
        f'<defs><clipPath id="panel"><rect width="{MAP_W}" height="{MAP_H}" rx="18"/>'
        '</clipPath></defs>'
        f'<g clip-path="url(#panel)">'
        f'<rect width="{MAP_W}" height="{MAP_H}" fill="#0d1420"/>{ground_image()}</g>'
        f'<polygon points="{ring}" fill="none" stroke="#a8c6ee" '
        'stroke-width="3.5" stroke-dasharray="9 6"/>'
        + "".join(lamps) +
        f'<text x="{cx}" y="{cy-4}" text-anchor="middle" fill="#f2e8d5" '
        'font-size="30" font-weight="700" font-family="Noto Sans Thai,sans-serif">ในเวียง</text>'
        f'<text x="{cx}" y="{cy+22}" text-anchor="middle" fill="#b9aa90" '
        'font-size="15" font-family="Noto Sans Thai,sans-serif">nai wiang</text>'
        "</svg>")


def card_html(poly, gates, corners, perimeter_m):
    svg = map_svg(poly, gates, corners)
    return f"""<!DOCTYPE html><html lang="th"><head><meta charset="utf-8"><style>
*{{box-sizing:border-box;margin:0;padding:0}}
html,body{{width:1200px;height:630px;overflow:hidden}}
body{{background:#FBF6EE;color:#2A1E16;position:relative;
font-family:"Noto Sans Thai","IBM Plex Sans Thai","Sarabun","Arial Unicode MS",
 "Helvetica Neue",Arial,sans-serif}}
.rule{{position:absolute;left:44px;right:44px;height:5px;box-sizing:content-box;
border-top:5px solid #C2401C;border-bottom:5px solid #C2401C}}
.rule.t{{top:32px}} .rule.b{{top:583px}}
.left{{position:absolute;left:60px;top:74px;bottom:72px;width:590px;
display:flex;flex-direction:column}}
.kicker{{font-size:25px;color:#8F2E13;display:flex;gap:12px;align-items:center;
white-space:nowrap}}
.kicker .g{{font-size:34px;line-height:1}}
h1{{font-size:76px;line-height:1.04;font-weight:800;margin:8px 0 6px;
letter-spacing:-1px}}
.en{{font-size:26px;color:#6B5A48;line-height:1.3}}
.nums{{display:flex;gap:44px;margin:20px 0 0}}
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
.mappanel{{position:absolute;right:56px;top:64px;width:{MAP_W}px}}
.mappanel svg{{display:block;box-shadow:0 10px 34px #0004;border-radius:18px}}
.cap{{font-size:18.5px;color:#6B5A48;margin-top:11px;line-height:1.35;
text-align:center}}
</style></head><body>
<div class="rule t"></div>
<div class="left">
  <div class="kicker"><span class="g">🏯</span>
    <span>เชียงใหม่ — คำถามแรกของทุกที่อยู่</span></div>
  <h1>ในเวียง หรือ<br>นอกเวียง?</h1>
  <div class="en">Inside the walls, or out?<br>Nine ways to tell.</div>
  <div class="nums">
    <div class="num"><b>9</b><span>ทางรู้ ไล่จากไกลถึงใกล้<br>ways to know, far to near</span></div>
    <div class="num"><b>{perimeter_m:,.0f}</b><span>เมตรรอบคู — ชั่วโมงเศษเดินกลับที่เดิม<br>metres around the water</span></div>
  </div>
  <div class="chips">
    <span class="chip">⛰ ดูดอย</span>
    <span class="chip">↻ ดูทิศรถ</span>
    <span class="chip">± นับสะพาน</span>
    <span class="chip">📍 ถามเครื่อง</span>
  </div>
  <div class="foot">
    <div class="brand">🐜 มดแดง<small>motdang.net/moat</small></div>
  </div>
</div>
<div class="mappanel">{svg}
  <div class="cap">▢ คูเมือง · สี่แจ่ง ห้าประตู — เก้าทางข้ามที่เรียกชื่อได้</div>
</div>
<div class="rule b"></div>
</body></html>"""


def main():
    if not SRC.exists():
        raise SystemExit("data/canonical/cm.json not found")
    by_id = {r["id"]: r for r in json.loads(SRC.read_text())}
    poly = [(by_id[i]["lat"], by_id[i]["lng"]) for i in CORNER_IDS]
    gates = [(by_id[i]["lat"], by_id[i]["lng"]) for i in GATE_IDS]
    corners = [(la, ln) for la, ln in poly]
    kx = math.cos(math.radians(sum(p[0] for p in poly) / 4))
    perimeter = sum(math.hypot((poly[i][0] - poly[(i + 1) % 4][0]) * 111320,
                               (poly[i][1] - poly[(i + 1) % 4][1]) * 111320 * kx)
                    for i in range(4))
    set_frame(poly)
    chrome = find_chrome()
    OUT.parent.mkdir(parents=True, exist_ok=True)
    tmp = Path(tempfile.mkdtemp(prefix="moatcard-"))
    src = tmp / "card.html"
    src.write_text(card_html(poly, gates, corners, perimeter), encoding="utf-8")
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
        shutil.copyfile(OUT, live / "moat.png")
    print(f"wrote {OUT} ({OUT.stat().st_size // 1024} KB) — "
          f"9 crossings lit, ring {perimeter:,.0f} m")


if __name__ == "__main__":
    main()
