#!/usr/bin/env python3
"""The doi page's share card — assets/og/doi.png, 1200x630.

One card, drawn the way the shelf cards are drawn (Chrome renders, Pillow
crops), wearing the same paper and the same double rule so a shared link
reads as this site before a word is read. Its picture is not decoration:
the bottom band is the REAL west–east cut through ประตูท่าแพ, drawn from
data/terrain_profile.json — the same numbers the page prints. A card whose mountains were sketched by hand would not match them.

Needs Chrome and data/terrain_profile.json + data/terrain_meta.json
(importers/build_terrain.py writes both). Run after a terrain re-read:

    python3 make_doi_card.py

geography_layer.py picks the card up by existence — no card, and the page
rides the sights shelf card instead, so a build never waits on this.
"""
import json
import subprocess
import tempfile
from pathlib import Path

from make_og_cards import SHOT_H, crop, esc, find_chrome

ROOT = Path(__file__).resolve().parent
OUT = ROOT / "assets" / "og" / "doi.png"
META = ROOT / "data" / "terrain_meta.json"
PROFILE = ROOT / "data" / "terrain_profile.json"


def _fmt(n):
    return "{:,.0f}".format(float(n))


def _skyline(prof, width=1080, height=150):
    """The cut as a silhouette, baseline at 0 m, drawn to the card's width.
    preserveAspectRatio is none on purpose: this band is a skyline, and the
    vertical stretch is already the drawing's stated habit on the page."""
    ele = prof["ele"]
    top = 1800.0
    n = len(ele)
    pts = " ".join("%.1f,%.1f" % (i / (n - 1) * width,
                                  height - max(0.0, min(top, e)) / top * height)
                   for i, e in enumerate(ele))
    tick = prof.get("tick") or {}
    xg = ((tick.get("lng", 98.99) - prof["lon_a"])
          / (prof["lon_b"] - prof["lon_a"]) * width)
    return (f'<svg viewBox="0 0 {width} {height}" width="{width}" '
            f'height="{height}" preserveAspectRatio="none" '
            f'xmlns="http://www.w3.org/2000/svg">'
            f'<path d="M0,{height} L{pts.replace(" ", " L")} '
            f'L{width},{height} Z" fill="#59452F"/>'
            f'<line x1="{xg:.1f}" y1="{height}" x2="{xg:.1f}" '
            f'y2="{height - 26}" stroke="#C2401C" stroke-width="3"/></svg>')


TEMPLATE = """<!DOCTYPE html><html lang="th"><head><meta charset="utf-8"><style>
*{{box-sizing:border-box;margin:0;padding:0}}
html,body{{width:1200px;height:630px;overflow:hidden}}
body{{background:#FBF6EE;color:#2A1E16;
font-family:"Noto Sans Thai","IBM Plex Sans Thai","Sarabun","Arial Unicode MS",
 "Helvetica Neue",Arial,sans-serif;position:relative}}
.rule{{position:absolute;left:60px;right:60px;height:5px;
border-top:5px solid #C2401C;border-bottom:5px solid #C2401C;box-sizing:content-box}}
.rule.t{{top:44px}} .rule.b{{top:571px}}
.top{{position:absolute;left:60px;right:60px;top:82px;display:flex;
align-items:center;gap:16px;font-size:26px;color:#8F2E13}}
.glyph{{font-size:40px;line-height:1}}
.name{{position:absolute;left:60px;right:60px;top:138px;font-size:62px;
line-height:1.1;font-weight:700;white-space:nowrap;overflow:hidden}}
.en{{position:absolute;left:60px;right:60px;top:226px;font-size:34px;
color:#6B5A48;line-height:1.2}}
.count{{position:absolute;left:60px;right:60px;top:300px;font-size:34px;
font-weight:700;color:#C2401C}}
.count small{{font-size:24px;font-weight:400;color:#6B5A48;margin-left:10px}}
.sky{{position:absolute;left:60px;right:60px;bottom:59px;line-height:0}}
.foot{{position:absolute;left:60px;right:60px;top:352px;display:flex;
align-items:flex-start;justify-content:space-between;gap:24px}}
.url{{font-size:22px;color:#6B5A48;line-height:1.25}}
.brand{{text-align:right;font-size:32px;font-weight:700;color:#C2401C;
white-space:nowrap;line-height:1.15}}
.brand small{{display:block;font-size:20px;font-weight:400;color:#6B5A48;
letter-spacing:.06em}}
</style></head><body>
<div class="rule t"></div>
<div class="top"><span class="glyph">⛰</span><span>{kicker}</span></div>
<div class="name">{name}</div>
<div class="en">{en}</div>
<div class="count">{count}<small>{count_small}</small></div>
<div class="foot"><div class="url">motdang.net/doi.html</div>
<div class="brand">มดแดง<small>MOT DANG · CHIANG MAI + CHIANG RAI</small></div></div>
<div class="sky">{sky}</div>
<div class="rule b"></div>
</body></html>"""


def main():
    if not (META.exists() and PROFILE.exists()):
        raise SystemExit("no terrain readings on disk — "
                         "run importers/build_terrain.py first")
    meta = json.loads(META.read_text())
    prof = json.loads(PROFILE.read_text())
    hi = meta["highest_cell"]
    tp = meta["tha_phae"]
    html = TEMPLATE.format(
        kicker=esc("ภูมิประเทศสองจังหวัด · the shape of the land"),
        name=esc("ดอย — แผ่นดินเชียงใหม่ · เชียงราย"),
        en=esc("Relief map · 3D · the basin in cross-section"),
        count=esc("%s ม. ยอดสูงสุดที่อ่านได้" % _fmt(hi["ele"])),
        count_small=esc("พื้นแอ่งที่ประตูท่าแพ %s ม. · อ่านเมื่อ %s"
                        % (_fmt(tp["ele"]), meta.get("read", ""))),
        sky=_skyline(prof),
    )
    OUT.parent.mkdir(parents=True, exist_ok=True)
    chrome = find_chrome()
    tmp = Path(tempfile.mkdtemp(prefix="doicard-"))
    src = tmp / "card.html"
    src.write_text(html, encoding="utf-8")
    subprocess.run([
        chrome, "--headless", "--disable-gpu", "--hide-scrollbars",
        "--no-sandbox", "--force-device-scale-factor=1",
        "--window-size=1200,%d" % SHOT_H, "--screenshot=" + str(OUT),
        src.as_uri()],
        check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    crop(OUT)
    print("doi card -> %s (%d bytes)" % (OUT, OUT.stat().st_size))


if __name__ == "__main__":
    main()
