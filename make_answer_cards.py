#!/usr/bin/env python3
"""Share cards for the answer pages — assets/og/{festival-dates,open-now}.png.

Same family as the toilets card, same reasoning end to end: the share preview
is where most people meet the page, so each card is the page's own argument
drawn from the page's own data — never decoration. The festival card carries
the real year wheel (docs/festival-wheel.svg, inlined); the open-now card
carries the real 24-hour x 7-day open-count grid, computed from the same
open_lamps.json the page bakes from. Chrome takes the picture because Pillow
here has no raqm and Thai marks set wrong are worse than no card.

Reads built files, so run AFTER a build; the next build points the pages'
og:image at the cards (they check assets/og/ exists) and copies them into
docs/og/ like every other og asset:

    python3 build.py && python3 make_answer_cards.py && python3 build.py

Redraw only when the data or the design changes, not every build.

Layout rule learned on the toilets card, kept here: the Thai headline stays
one line (76px, nowrap), the English line stays short, and the caption under
the panel stays one line — anything taller shoves the footer past the rule.
"""
import datetime
import json
import re
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

from PIL import Image

import map_ground
from make_og_cards import find_chrome, crop, SHOT_H

ROOT = Path(__file__).resolve().parent
OG = ROOT / "assets" / "og"

PANEL_W = 470

FRAME = """<!DOCTYPE html><html lang="th"><head><meta charset="utf-8"><style>
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
.panel{{position:absolute;right:56px;top:80px;width:{panel_w}px}}
.panel .art{{display:block;border-radius:18px;overflow:hidden;
box-shadow:0 10px 34px #0004;line-height:0}}
.panel .art svg{{display:block;width:100%;height:auto}}
.cap{{font-size:18.5px;color:#6B5A48;margin-top:11px;line-height:1.35;
text-align:center;white-space:nowrap}}
{extra_css}
</style></head><body>
<div class="rule t"></div>
<div class="left">
  <div class="kicker"><span class="g">{kicker_glyph}</span><span>{kicker}</span></div>
  <h1>{h1}</h1>
  <div class="en">{en}</div>
  <div class="nums">{nums}</div>
  <div class="chips">{chips}</div>
  <div class="foot">
    <div class="brand">🐜 มดแดง<small>motdang.net/{path}</small></div>
  </div>
</div>
<div class="panel"><div class="art">{art}</div>
  <div class="cap">{caption}</div>
</div>
<div class="rule b"></div>
</body></html>"""


def num(b, span):
    return f'<div class="num"><b>{b}</b><span>{span}</span></div>'


def chip(s):
    return f'<span class="chip">{s}</span>'


# ------------------------------------------------------------ festival dates
def festival_card():
    wheel = (ROOT / "docs" / "festival-wheel.svg").read_text()
    wheel = re.sub(r"<\?xml[^>]*\?>", "", wheel)
    fests = json.loads((ROOT / "data" / "festivals.json").read_text())["festivals"]
    cal = json.loads((ROOT / "data" / "festival_calendar.json").read_text())
    today = datetime.date.today()
    years = {today.year, today.year + 1}
    dated = [r for r in cal["rows"] if r["year"] in years]
    be = f"{today.year + 543}–{today.year + 544}"
    return FRAME.format(
        panel_w=PANEL_W,
        extra_css=".panel .art{background:#fff;padding:6px}",
        kicker_glyph="🎉",
        kicker=f"เชียงใหม่ · เชียงราย — ปี {be} หน้าเดียว",
        h1="เทศกาลวันไหน",
        en=f"Festival dates {today.year}–{today.year + 1}, "
           "every date with its source",
        nums=num(str(len(fests)), "งานทั้งปี ทุกงานมีหน้าของตัวเอง<br>"
                                  "festivals, the whole year")
             + num(str(len(dated)), "วันตามปฏิทินที่ตรวจแล้ว<br>"
                                    "published dates, checked"),
        chips=chip("📌 ประกาศแล้ว") + chip("🌕 ตามปฏิทินจันทรคติ")
              + chip("🗓 วันเดิมทุกปี") + chip("⏳ รอประกาศ — บอกตรง ๆ"),
        path="festival-dates",
        art=wheel,
        caption="วงล้อทั้งปี — ทุกขีดคือหนึ่งงาน ขีดเล็กรอบขอบคือวันพระ",
    ), OG / "festival-dates.png"


# ----------------------------------------------------------------- open now
def heat_svg(lamps):
    """The week as 24 rows x 7 days, cell brightness = places open."""
    scheds = lamps["schedules"]
    counts = [[0] * 7 for _ in range(24)]
    for p in lamps["places"]:
        s = scheds[p["k"]]
        for h in range(24):
            for d in range(7):
                t = d * 1440 + h * 60 + 30
                if any(a <= t < b for a, b in s):
                    counts[h][d] += 1
    peak = max(max(row) for row in counts)
    w, h = PANEL_W, 446
    left, top = 46, 30
    cw = (w - left - 12) / 7
    ch = (h - top - 12) / 24
    cells = []
    for hr in range(24):
        for d in range(7):
            f = counts[hr][d] / peak
            # dark harbour -> ember -> lamplight, the nitnoy palette
            r_ = int(13 + (246 - 13) * f)
            g_ = int(20 + (183 - 20) * f)
            b_ = int(32 + (60 - 32) * f)
            cells.append(
                f'<rect x="{left + d * cw:.1f}" y="{top + hr * ch:.1f}" '
                f'width="{cw - 2:.1f}" height="{ch - 2:.1f}" rx="2.5" '
                f'fill="rgb({r_},{g_},{b_})"/>')
    days = "".join(
        f'<text x="{left + (i + .5) * cw:.1f}" y="21" font-size="14" '
        f'text-anchor="middle" fill="#8fa3bd">{d}</text>'
        for i, d in enumerate(["จ", "อ", "พ", "พฤ", "ศ", "ส", "อา"]))
    hours = "".join(
        f'<text x="{left - 8}" y="{top + (hr + .7) * ch:.1f}" font-size="13" '
        f'text-anchor="end" fill="#8fa3bd">{hr:02d}</text>'
        for hr in (0, 6, 12, 18, 23))
    return (
        f'<svg viewBox="0 0 {w} {h}" xmlns="http://www.w3.org/2000/svg">'
        f'<rect width="{w}" height="{h}" fill="#0d1420"/>'
        + days + hours + "".join(cells) + "</svg>")


def open_now_card():
    import answers_layer
    lamps = json.loads((ROOT / "data" / "open_lamps.json").read_text())
    scheds = lamps["schedules"]
    allday = dawn = late = 0
    for p in lamps["places"]:
        s = scheds[p["k"]]
        if answers_layer._covers_week(s):
            allday += 1
        else:
            if answers_layer._open_days_at(s, 5 * 60 + 30) >= 4:
                dawn += 1
            if answers_layer._open_days_at(s, 30) >= 3:
                late += 1
    return FRAME.format(
        panel_w=PANEL_W,
        extra_css="",
        kicker_glyph="🕰",
        kicker="เชียงใหม่ — ทั้งเมือง ชั่วโมงต่อชั่วโมง",
        h1="ตอนนี้เปิดอะไร",
        en="What is open in Chiang Mai, hour by hour",
        nums=num(f"{len(lamps['places']):,}",
                 "ที่ที่เรารู้เวลาเปิด-ปิดจริง<br>places with known hours")
             + num(str(allday), "เปิดตลอด 24 ชั่วโมง<br>never close at all"),
        chips=chip(f"🌅 ก่อน 6 โมงเช้า {dawn} ที่")
              + chip(f"🌙 หลังเที่ยงคืน {late} ที่")
              + chip("🏮 กาดเช้า-คาเฟ่-บาร์ ครบ"),
        path="open-now",
        art=heat_svg(lamps),
        caption="ทั้งสัปดาห์ในภาพเดียว — ยิ่งสว่าง ยิ่งเปิดมาก",
    ), OG / "open-now.png"


# ------------------------------------------------- shared constellation art
def constellation(points, panel_h=446, moat=True, r=2.6):
    """Lat/lng points as glowing dots on the dark harbour, percentile-framed
    (middle 90% + 10% pad) so far-district outliers cannot shrink the city.
    points = [(lat, lng, color)]; returns (svg, n_in_frame)."""
    lats = sorted(p[0] for p in points)
    lngs = sorted(p[1] for p in points)
    lo, hi = int(len(lats) * 0.05), int(len(lats) * 0.95)
    pad_la = (lats[hi] - lats[lo]) * 0.10 or 0.01
    pad_ln = (lngs[hi] - lngs[lo]) * 0.10 or 0.01
    la0, la1 = lats[lo] - pad_la, lats[hi] + pad_la
    ln0, ln1 = lngs[lo] - pad_ln, lngs[hi] + pad_ln
    import math
    kx = math.cos(math.radians((la0 + la1) / 2))
    span_x, span_y = (ln1 - ln0) * kx, la1 - la0
    scale = min(PANEL_W / span_x, panel_h / span_y)

    def pj(la, ln):
        x = (ln - ln0) * kx * scale + (PANEL_W - span_x * scale) / 2
        y = (la1 - la) * scale + (panel_h - span_y * scale) / 2
        return round(x, 1), round(y, 1)

    # The city under the constellation. Without it these cards showed the
    # SHAPE of a scatter and nothing about where any of it is — an outsider
    # could not tell the old city from the airport, and the same picture would
    # have served for any town on earth. The ground is held well below the
    # dots: it is the room they stand in, not the subject.
    ground = ""
    g = map_ground.shared(night=True)
    if g.available:
        # pj() letterboxes, so the panel shows MORE ground than la0..la1 on one
        # axis. Invert the corners for what is really in frame.
        w_ln = ln0 + (0 - (PANEL_W - span_x * scale) / 2) / (kx * scale)
        e_ln = ln0 + (PANEL_W - (PANEL_W - span_x * scale) / 2) / (kx * scale)
        n_la = la1 - (0 - (panel_h - span_y * scale) / 2) / scale
        s_la = la1 - (panel_h - (panel_h - span_y * scale) / 2) / scale
        bbox = (s_la, w_ln, n_la, e_ln)
        im = Image.new("RGB", (PANEL_W, panel_h), g.palette["paper"])
        if g.paint(im, lambda p: pj(p[0], p[1]), bbox, width_px=PANEL_W,
                   zoom=g.zoom_for(bbox, PANEL_W, 256), buildings=False,
                   fade=0.75, contrast=1.25):
            map_ground.credit_mark(im, dark=True, inset=14)
            ground = ('<image x="0" y="0" width="%d" height="%d" href="%s"/>'
                      % (PANEL_W, panel_h, map_ground.data_uri(im)))

    dots, n_in = [], 0
    for la, ln, color in points:
        if not (la0 <= la <= la1 and ln0 <= ln <= ln1):
            continue
        n_in += 1
        x, y = pj(la, ln)
        dots.append(f'<circle cx="{x}" cy="{y}" r="{r * 2.1:.1f}" '
                    f'fill="{color}" opacity=".18"/>'
                    f'<circle cx="{x}" cy="{y}" r="{r}" fill="{color}"/>')
    moat_svg = ""
    if moat:
        ring = json.loads(
            (ROOT / "docs" / "data" / "toilets.json").read_text())["moat"]
        if all(la0 <= la <= la1 and ln0 <= ln <= ln1 for la, ln in ring):
            pts = " ".join("%g,%g" % pj(la, ln) for la, ln in ring)
            moat_svg = (f'<polygon points="{pts}" fill="none" stroke="#a8c6ee" '
                        'stroke-width="3" stroke-dasharray="8 6"/>')
    return (
        f'<svg viewBox="0 0 {PANEL_W} {panel_h}" '
        'xmlns="http://www.w3.org/2000/svg">'
        f'<rect width="{PANEL_W}" height="{panel_h}" fill="#0d1420"/>'
        + ground + "".join(dots) + moat_svg + "</svg>"), n_in


# -------------------------------------------------------------------- taste
def taste_card():
    taste = json.loads((ROOT / "data" / "taste.json").read_text())
    color = {f["key"]: f["color"] for f in taste["families"]}
    # CM dots only for the art — a frame over both provinces is a rice field
    # between two specks (the cross-province trap the stats page hit too)
    points = [(d["la"], d["ln"], color.get(d["f"], "#8f9bab"))
              for d in taste["dots"] if d["p"] == "cm"]
    art, n_in = constellation(points, r=2.4)
    fams = [f for f in taste["families"] if f["key"] != "other"][:4]
    chips = "".join(
        chip(f'<i style="color:{f["color"]}">●</i> {f["th"]} {f["n"]}')
        for f in fams)
    tokens = len({d["t"] for d in taste["dots"]})
    return FRAME.format(
        panel_w=PANEL_W,
        extra_css=".chip i{font-style:normal;margin-right:2px}",
        kicker_glyph="🍜",
        kicker="เชียงใหม่ · เชียงราย — เมืองนี้รสอะไร",
        h1="รสเมือง",
        en="The taste of the town — every kitchen a dot of light",
        nums=num(f"{len(taste['dots']):,}", "ร้านที่บอกแนวรสของตัวเอง<br>"
                                            "places with a stated cuisine")
             + num(str(tokens), "แนวรสที่ต่างกัน<br>distinct cuisines"),
        chips=chips,
        path="taste",
        art=art,
        caption=f"หนึ่งจุด หนึ่งร้าน สีคือสายรส — {n_in:,} จุดในกรอบเมืองเชียงใหม่",
    ), OG / "taste.png"


# --------------------------------------------------------------------- walk
def walk_card():
    """The card borrows the page's own ATM contour map — the SVG is lifted
    straight out of built docs/walk.html, so the preview can never disagree
    with the page. Portrait map, so the panel narrows to keep the height."""
    h = (ROOT / "docs" / "walk.html").read_text()
    i = h.find("ATMs")
    j = h.find("<svg", i)
    k = h.find("</svg>", j)
    if j < 0 or k < 0:
        raise SystemExit("walk.html has no ATM map svg — run build.py first")
    art = h[j:k + 6]
    wj = json.loads((ROOT / "docs" / "data" / "walk.json").read_text())
    L = wj["layers"]
    total = sum(x["sitesTotal"] for x in L.values())
    return FRAME.format(
        panel_w=386,
        extra_css=".panel .art{background:#0d1420}",
        kicker_glyph="🚶",
        kicker="เชียงใหม่ — เดินตามถนนจริง ข้ามคูเมืองที่สะพาน",
        h1="แผนที่ระยะเดิน",
        en="The city at walking pace — real streets, real distances",
        nums=num(f"{total:,}", "จุดบริการ 4 อย่างทั่วเมือง<br>"
                               "service points, four kinds")
             + num("4", "แผนที่เต็มหน้า<br>full-page maps"),
        chips=chip(f"🏧 ตู้เอทีเอ็ม {L['atm']['sitesTotal']}")
              + chip(f"💊 ร้านยา {L['pharmacy']['sitesTotal']}")
              + chip(f"🚻 ห้องน้ำ {L['toilets']['sitesTotal']}")
              + chip(f"🚰 น้ำดื่ม {L['water']['sitesTotal']}"),
        path="walk",
        art=art,
        caption="แผนที่ตู้เอทีเอ็ม — สีเข้ม = หลายตู้ในระยะเดิน ~10 นาที",
    ), OG / "walk.png"


# -------------------------------------------------------------------- reach
# The page's own three colours, so the card and the chart under it speak one
# language. BROKEN is copied from build.py deliberately rather than imported —
# importing build.py runs a build — and tests/test_reach_card.py fails if the
# two ever drift, because a card that counts "broken" differently from the page
# it previews is the same defect as a price welded to the wrong duration.
REACH_OK, REACH_BROKEN, REACH_SOCIAL = "#3B5A4A", "#8F2E13", "#1877F2"
BROKEN = {"tls", "dns", "down", "timeout", "gone", "http-error", "server-error",
          "parked", "empty", "error"}


def dotfield(working, broken, social, cols=33, cell=14.2, r=4.6):
    """Every checked link as one dot, grouped in reading order. The bar on the
    page says the same thing in three rectangles; here you can count the dead
    ones, which is the whole argument."""
    runs = [(working, REACH_OK), (broken, REACH_BROKEN), (social, REACH_SOCIAL)]
    total = working + broken + social
    rows = -(-total // cols)
    w, h = cols * cell, rows * cell
    out = [f'<svg viewBox="0 0 {w:.0f} {h:.0f}" width="100%">',
           f'<rect width="{w:.0f}" height="{h:.0f}" fill="#FBF6EE"/>']
    i = 0
    for n, colour in runs:
        for _ in range(n):
            cx = (i % cols) * cell + cell / 2
            cy = (i // cols) * cell + cell / 2
            out.append(f'<circle cx="{cx:.1f}" cy="{cy:.1f}" r="{r}" fill="{colour}"/>')
            i += 1
    out.append("</svg>")
    return "".join(out)


def reach_card():
    lh = json.loads((ROOT / "data" / "linkhealth.json").read_text())
    tally = {}
    for v in lh["links"].values():
        tally[v.get("status", "?")] = tally.get(v.get("status", "?"), 0) + 1
    n_links = sum(tally.values())
    n_social = tally.get("social", 0)
    n_sites = n_links - n_social
    n_broken = sum(tally.get(k, 0) for k in BROKEN)
    n_working = n_sites - n_broken
    pct = round(100 * n_broken / n_sites) if n_sites else 0
    # Named failure modes, biggest first — "broken" as a single word invites the
    # reader to assume we mean 404s, and the truth is mostly lapsed domains.
    labels = {"dns": "โดเมนหายไป", "gone": "หน้าหายไป 404",
              "http-error": "ขึ้นข้อผิดพลาด",
              "timeout": "ไม่ตอบสนอง", "tls": "ใบรับรองเสีย", "empty": "หน้าว่าง",
              "parked": "ประกาศขาย", "server-error": "เครื่องมีปัญหา",
              "error": "ลิงก์เสีย", "down": "ไม่รับการเชื่อมต่อ"}
    top = sorted(((tally.get(k, 0), k) for k in BROKEN), reverse=True)[:4]
    return FRAME.format(
        panel_w=PANEL_W,
        extra_css=".panel .art{background:#FBF6EE;padding:10px}",
        kicker_glyph="🔗",
        kicker=f"เชียงใหม่ · เชียงราย — เปิดจริงทีละลิงก์ {lh['generated']}",
        h1="ลิงก์ที่เปิดไม่ได้",
        en=f"Of the {n_sites:,} genuine business websites in this "
           f"directory, {n_broken:,} ({pct}%) no longer answer.",
        nums=num(f"{pct}%", "ของเว็บทางการที่เปิดไม่ได้แล้ว<br>"
                            "of official sites are broken")
             + num(f"{n_links:,}", "ลิงก์ที่เปิดตรวจจริง<br>links opened by hand"),
        # "404 31" read as one number; every chip keeps a separator now.
        chips="".join(chip(f"{labels.get(k, k)} · {n}") for n, k in top if n),
        path="reach",
        art=dotfield(n_working, n_broken, n_social),
        caption="หนึ่งจุด = หนึ่งลิงก์ · แดง = เปิดไม่ได้ · ฟ้า = เป็นเพจ ไม่ใช่เว็บ",
    ), OG / "reach.png"


# ------------------------------------------------------------------- nitnoy
# The page's own group palette, so the card and the map speak one language.
NITNOY_GROUPS = [("food", "#f6b73c", "ร้านอาหาร"), ("cafe", "#f0e3b0", "คาเฟ่"),
                 ("night", "#b18cff", "บาร์-ผับ"), ("market", "#ff6b5e", "ตลาด"),
                 ("care", "#ff9fc7", "นวด-ความงาม"),
                 ("shop", "#7fd8a4", "ของจำเป็น-ช้อป"),
                 ("other", "#c9d4e0", "อื่น ๆ")]


def nitnoy_card():
    """The lamps as they burn on a Saturday at 19:00 — the same moment the
    page's film strip freezes for its poster, so the two previews agree."""
    lamps = json.loads((ROOT / "data" / "open_lamps.json").read_text())
    scheds = lamps["schedules"]
    color = {k: c for k, c, _ in NITNOY_GROUPS}
    t = 5 * 1440 + 19 * 60          # Saturday 19:00, minute-of-week
    points, lit = [], {}
    for p in lamps["places"]:
        if p.get("p") != "cm":
            continue
        if not any(a <= t < b for a, b in scheds[p["k"]]):
            continue
        lit[p["g"]] = lit.get(p["g"], 0) + 1
        points.append((p["la"], p["ln"], color.get(p["g"], "#c9d4e0")))
    art, n_in = constellation(points, r=2.4)
    chips = "".join(
        chip(f'<i style="color:{c}">●</i> {th} {lit[k]}')
        for k, c, th in NITNOY_GROUPS if lit.get(k))
    return FRAME.format(
        panel_w=PANEL_W,
        extra_css="h1{font-size:62px}.chip i{font-style:normal;margin-right:2px}",
        kicker_glyph="🏮",
        kicker="เชียงใหม่ — เมืองนี้กำลังทำอะไรอยู่",
        h1="เมืองหลับนิดหน่อย",
        en="The city that sleeps nitnoy — its lamps, hour by hour",
        nums=num(f"{len(lamps['places']):,}",
                 "โคมทั้งหมด — ร้านที่รู้เวลาเปิดจริง<br>lamps with known hours")
             + num(f"{len(points):,}",
                   "ดวงสว่างอยู่ คืนวันเสาร์หนึ่งทุ่ม<br>alight on a Saturday at 19:00"),
        chips=chips,
        path="nitnoy",
        art=art,
        caption=f"โคมทุกดวงคือร้านจริง สีคือหมวด — {n_in:,} ดวงในกรอบ",
    ), OG / "nitnoy.png"


# -------------------------------------------------------------------- lists
LIST_COLOR = {"wat-chiang-mai": "#f6b73c", "wat-chiang-rai": "#f6b73c",
              "massage-chiang-mai": "#ff9fc7", "tattoo-chiang-mai": "#b98bff"}
LIST_GLYPH = {"wat-chiang-mai": "🛕", "wat-chiang-rai": "🛕",
              "massage-chiang-mai": "💆", "tattoo-chiang-mai": "🪡"}


def _list_records():
    import answers_layer
    data = {p: json.loads((ROOT / "data" / "canonical" / f"{p}.json").read_text())
            for p in ("cm", "cr")}
    out = []
    for L in answers_layer.LISTS:
        recs = [r for r in data[L["prov"]] if L["cat"] in (r.get("cat") or [])]
        out.append((L, recs))
    return out


def list_cards():
    cards = []
    lists = _list_records()
    for L, recs in lists:
        color = LIST_COLOR.get(L["slug"], "#f6b73c")
        pts = [(r["lat"], r["lng"], color) for r in recs
               if r.get("lat") is not None]
        art, n_in = constellation(pts, moat=(L["prov"] == "cm"))
        n = len(recs)
        cards.append((FRAME.format(
            panel_w=PANEL_W,
            extra_css="",
            kicker_glyph="📜",
            kicker="รายชื่อครบ — ทุกแห่งที่มดแดงถือข้อมูล",
            h1=L["th"],
            en=f"All {n} {L['en']} — the complete list",
            nums=num(f"{n:,}", "แห่ง ครบทุกชื่อ นับแล้วตรงหน้า<br>"
                               "of them — the count is a promise")
                 + num("ก→ฮ", "เรียงตามอักษร ทุกชื่อคือลิงก์<br>"
                              "alphabetical, every name a link"),
            chips=chip(f"{LIST_GLYPH.get(L['slug'], '📜')} {L['th']}")
                  + chip("🐜 OpenStreetMap + เดินเก็บจริง"),
            path=f"lists/{L['slug']}",
            art=art,
            caption=f"ทุกจุดคือหนึ่งชื่อในรายการ — {n_in:,} จุดในกรอบ",
        ), OG / f"list-{L['slug']}.png"))
    # the hub: the three Chiang Mai lists as coloured layers of one city
    pts = []
    for L, recs in lists:
        if L["prov"] != "cm":
            continue
        color = LIST_COLOR.get(L["slug"], "#f6b73c")
        pts += [(r["lat"], r["lng"], color) for r in recs
                if r.get("lat") is not None]
    art, n_in = constellation(pts)
    total = sum(len(recs) for _, recs in lists)
    chips = "".join(
        chip(f'{LIST_GLYPH.get(L["slug"], "📜")} {L["th"]} {len(recs):,}')
        for L, recs in lists)
    cards.append((FRAME.format(
        panel_w=PANEL_W,
        extra_css="",
        kicker_glyph="📜",
        kicker="เชียงใหม่ · เชียงราย — ไม่ใช่สิบอันดับ แต่ทั้งหมด",
        h1="รายชื่อครบ",
        en="The complete lists — not a top ten, everything",
        nums=num(str(len(lists)), "หมวดที่ทำรายชื่อครบแล้ว<br>complete lists so far")
             + num(f"{total:,}", "แห่งรวม ทุกชื่อคือลิงก์<br>places, every name a link"),
        chips=chips,
        path="lists/",
        art=art,
        caption="วัด นวด สัก — สามชั้นของเมืองเดียวกัน สีละหมวด",
    ), OG / "lists.png"))
    return cards


# ------------------------------------------------------------------- driver
MAKERS = {"festival-dates": festival_card, "open-now": open_now_card,
          "taste": taste_card, "walk": walk_card, "nitnoy": nitnoy_card,
          "reach": reach_card}


def main():
    # --only <name>[,<name>] draws one card. Several of these read built pages
    # out of docs/, which another build wipes and rewrites, so redrawing one
    # card should not require the whole set to be buildable at that moment.
    argv = sys.argv[1:]
    want = None
    if "--only" in argv:
        want = {n.strip() for n in argv[argv.index("--only") + 1].split(",")}
        unknown = want - set(MAKERS) - {"lists"}
        if unknown:
            raise SystemExit("unknown card(s): %s — have: %s, lists"
                             % (", ".join(sorted(unknown)), ", ".join(sorted(MAKERS))))
    chrome = find_chrome()
    OG.mkdir(parents=True, exist_ok=True)
    tmp = Path(tempfile.mkdtemp(prefix="answercards-"))
    cards = [fn() for name, fn in MAKERS.items() if want is None or name in want]
    if want is None or "lists" in want:
        cards += list_cards()
    for html, dest in cards:
        src = tmp / "card.html"
        src.write_text(html, encoding="utf-8")
        subprocess.run([
            chrome, "--headless", "--disable-gpu", "--hide-scrollbars",
            "--no-sandbox", "--force-device-scale-factor=1",
            "--window-size=1200,%d" % SHOT_H, "--screenshot=" + str(dest),
            src.as_uri()],
            check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        crop(dest)
        live = ROOT / "docs" / "og"
        if live.exists():
            shutil.copyfile(dest, live / dest.name)
        print(f"wrote {dest} ({dest.stat().st_size // 1024} KB)")
    shutil.rmtree(tmp, ignore_errors=True)


if __name__ == "__main__":
    main()
