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
import tempfile
from pathlib import Path

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


# ------------------------------------------------------------------- driver
def main():
    chrome = find_chrome()
    OG.mkdir(parents=True, exist_ok=True)
    tmp = Path(tempfile.mkdtemp(prefix="answercards-"))
    for html, dest in (festival_card(), open_now_card()):
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
