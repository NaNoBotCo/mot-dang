#!/usr/bin/env python3
"""ยี่เป็ง — the Yi Peng / Loi Krathong spread, one page (/yipeng.html).

The canon page (/festivals/yi-peng-loi-krathong.html) is the register's
entry: rule, venues, cost, verify. This page is the season laid out — the
moon and the arithmetic that names the night, the map of where the city
gathers, the three lights and the little raft with the manuscripts behind
them, the many ways to keep one full moon, the four notices the year still
owes, festival week as a frame, and the twelve weekly letters, each landing
on the page the day its send date passes.

Rules this page keeps, from the festival-push brief and the canon:

  * An unpublished notice is a NAMED EMPTY SLOT with the date we check it,
    never a guessed zone, hour, or day. The slots fill from
    data/festival_dates.json (the announcement harvester) — g["_ANNOUNCED"]
    — the moment a matching official row exists, with its source link.
  * Many ways, one full moon: riverbank, wat courtyard, a sill at home, the
    ticketed fields — listed at one size, ranked never.
  * Every claim carries its mark: canon / almanac / manuscript / organizer /
    tradition holds / inference / awaiting notice.
  * Photos are Nan's Commons picks (data/curated/image_picks.json) and each
    prints its artist and licence beside it. A light with no picture in the
    pool (ผางประทีป) gets no stand-in.
  * Auspicious register throughout; the zone notice is "where the sky is
    open", not a warning.

Entry point: emit(g, events, data) — hooked in build.py AFTER
festivals_layer.emit (it reads g["_ANNOUNCED"] that layer sets). Writes
yipeng.html, yipeng.css and data/yipeng.json. Standalone:

    python3 yipeng_layer.py                 # re-lay over a built docs/
    python3 yipeng_layer.py --out DIR       # render into DIR (no docs/ needed)
"""
import datetime
import json
import math
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parent
FEST_ID = "yi-peng-loi-krathong"
ANCHOR = datetime.date(2026, 11, 24)          # full moon, 12th central month
DRIP = ROOT / "data" / "curated" / "yipeng_drip.json"
PICKS = ROOT / "data" / "curated" / "image_picks.json"

# The photos, by slug in image_picks.json. Each use names what it shows.
PHOTO = {
    "hero": "festival-yi-peng-chiangmai-tailandia-16786888573",
    "khom_loi": "chiang-mai-loy-krathong-lantern-festival-thailand",
    "khom_khwaen": "lanna-lantern-in-phayao",
    "krathong": "chiang-mai-krathong-festival-thailand",
    "procession": "chiang-mai-procession-lantern-festival-thailand",
    "riverside": "chiang-mai-loy-krathong-lantern-festival-3-thailand",
}

# Where the city gathers. place_id → the register's own record (pinned by
# WO-2); a venue with no record carries its coordinate's provenance in
# `placed`, and the page prints it. Nawarat Bridge is a line in the
# landmark register's own words ("lines, not points — fork"), so its pin is
# hand-placed at the span's midpoint and says so.
VENUES = [
    {"key": "nawarat", "th": "แม่น้ำปิง สะพานนวรัฐ", "en": "Ping River at Nawarat Bridge",
     "lat": 18.7877, "lng": 99.0022, "placed": "hand",
     "note_th": "จุดลอยกระทงหลักของเมือง ริมน้ำสองฝั่งรอบสะพานคนแน่นที่สุด — ยืนบนสะพานเห็นทั้งกระทงในน้ำและโคมบนฟ้าพร้อมกัน",
     "note_en": "The city's main krathong bank; both riversides around the bridge are the busiest stretch — from the bridge you see krathongs on the water and lanterns overhead at once",
     "mark": "canon"},
    {"key": "thaphae", "th": "ประตูท่าแพ", "en": "Tha Phae Gate", "place_id": "cm-osm-node-1017379824",
     "note_th": "เวทีหลัก ขบวนแห่ ซุ้มโคม และการประกวด — จุดถ่ายรูปโคมแขวนที่คึกคักที่สุด",
     "note_en": "Main stage, parades, lantern arches and contests — the liveliest spot for the hanging-lantern displays",
     "mark": "canon"},
    {"key": "threekings", "th": "ข่วงอนุสาวรีย์สามกษัตริย์", "en": "Three Kings Monument", "place_id": "cm-osm-node-1619287904",
     "note_th": "พิธีเปิดและการแสดงวัฒนธรรม บรรยากาศงานเมืองแบบเป็นทางการ",
     "note_en": "Opening ceremonies and cultural performances — the formal civic side of the festival",
     "mark": "canon"},
    {"key": "phantao", "th": "วัดพันเตา", "en": "Wat Phan Tao", "place_id": "cm-osm-way-243018378",
     "note_th": "ลานวัดที่จุดผางประทีปและแขวนโคมตลอดสัปดาห์งาน — เวลาพิธีเย็นปี ๒๕๖๙ รอประกาศของวัด",
     "note_en": "Courtyard lit with ผางประทีป and hanging lanterns through festival week — 2569 evening times await the wat's own notice",
     "mark": "press"},
    {"key": "lokmoli", "th": "วัดโลกโมฬี", "en": "Wat Lok Moli", "place_id": "cm-osm-way-692137164",
     "note_th": "โคมแขวนใต้ชายคาและเจดีย์ในแสงประทีป — เวลาพิธีเย็นปี ๒๕๖๙ รอประกาศของวัด",
     "note_en": "Hanging lanterns under the eaves, the chedi in lamplight — 2569 evening times await the wat's own notice",
     "mark": "press"},
    {"key": "chaimongkhon", "th": "วัดชัยมงคล (ริมปิง)", "en": "Wat Chai Mongkhon (riverside)", "place_id": "cm-osm-way-406558246",
     "note_th": "วัดริมน้ำที่ลงลอยกระทงได้จากท่าวัด — ปีก่อน ๆ มีใบตองให้พับกระทงเอง",
     "note_en": "A riverside wat with its own landing to float from — in past years banana leaf was on hand to fold your own",
     "mark": "press"},
    {"key": "cad", "th": "ศูนย์วัฒนธรรมเชียงใหม่ (CAD Khomloy)", "en": "CAD Cultural Center (CAD Khomloy)", "place_id": "cm-newsletter-old-cm-cultural-center",
     "note_th": "งานปล่อยโคมขายบัตร ๒๔–๒๕ พ.ย. — ผู้จัดยืนยันวัน",
     "note_en": "Ticketed mass-release evenings, 24–25 Nov — organizer-confirmed dates",
     "mark": "organizer", "url": "https://yipenglanternfestival.in.th/"},
    {"key": "dhutanka", "th": "ลานนาธุตังคสถาน สันทราย (Yee Peng Lanna International)", "en": "Lanna Dhutanka, San Sai (Yee Peng Lanna International)",
     "note_th": "งานปล่อยโคมขายบัตร ๒๔–๒๕ พ.ย. ราว ๑๒.๐๐–๒๑.๐๐ น. ใกล้ ม.แม่โจ้ — ยังไม่มีหมุดในทะเบียน",
     "note_en": "Ticketed evenings, 24–25 Nov, about 12:00–21:00, near Mae Jo University — no pin in the register yet",
     "mark": "organizer", "url": "https://www.eventbrite.com/e/yeepeng-lanna-international-2026-chiang-mai-official-ticket-24-nov-2026-tickets-1978873470821"},
    {"key": "kok", "th": "ริมน้ำกก ฝั่งหมิ่น เชียงราย", "en": "Kok riverbank, Fang Min side, Chiang Rai", "place_id": "cr-osm-way-967447589",
     "note_th": "จุดลอยกระทงของเชียงราย — สวนสาธารณะริมน้ำกกหลังวัดฝั่งหมิ่น (หมุดคือวัด สวนอยู่ริมน้ำด้านหลัง) — วันปี ๒๕๖๙ รอเทศบาลนครเชียงราย",
     "note_en": "Chiang Rai's own krathong bank — the riverside park behind Wat Fang Min (the pin is the wat; the park is on the bank behind it) — 2569 dates await the municipality",
     "mark": "canon", "prov": "cr"},
]

# The notices the year still owes, from findings/2026-dates.md. Each slot
# fills itself from g["_ANNOUNCED"] when an official row matches its hosts
# and words; until then it prints its expected window and the check date.
GATES = [
    {"key": "municipal", "th": "กำหนดการงานประเพณีเดือนยี่เป็งเชียงใหม่ ๒๕๖๙ (เทศบาลนคร)",
     "en": "Chiang Mai municipal festival program 2569",
     "window_th": "ปลายกันยายน – ตุลาคม", "window_en": "late September – October",
     "check": "2026-09-15", "hosts": ("chiangmai.prd.go.th", "cmcity.go.th", "gcc.go.th"),
     "words": ("ยี่เป็ง", "ลอยกระทง"), "not": ("โคม",),
     "pattern_url": "https://chiangmai.prd.go.th/th/content/category/detail/id/9/iid/426806",
     "pattern_th": "ปี ๒๕๖๘: ข่าวเตรียมงานออกปลายกันยายน–ตุลาคม สำหรับงาน ๔–๖ พ.ย.",
     "pattern_en": "2568: preparation news landed late Sept–Oct for a 4–6 Nov festival"},
    {"key": "zone", "th": "ประกาศเขตปล่อยโคม จ.เชียงใหม่ ๒๕๖๙ — ที่ที่ฟ้าเปิด",
     "en": "Release-zone notice 2569 — where the sky is open",
     "window_th": "ปลายตุลาคม – กลางพฤศจิกายน", "window_en": "late October – mid November",
     "check": "2026-10-20", "hosts": ("chiangmai.prd.go.th", "radiochiangmai.prd.go.th"),
     "words": ("โคม",), "not": (),
     "pattern_url": "https://chiangmai.prd.go.th/th/content/category/detail/id/9/iid/429884",
     "pattern_th": "ปี ๒๕๖๘: ประกาศออกปลายตุลาคม ราว ๑–๒ สัปดาห์ก่อนงาน",
     "pattern_en": "2568: the notice surfaced late October, 1–2 weeks before the festival"},
    {"key": "cr", "th": "งานเทศบาลนครเชียงราย ริมน้ำกก ๒๕๖๙",
     "en": "Chiang Rai municipal evening on the Kok, 2569",
     "window_th": "ตุลาคม", "window_en": "October",
     "check": "2026-10-01", "hosts": ("chiangraicity.go.th", "chiangrai.prd.go.th"),
     "words": ("ยี่เป็ง", "ลอยกระทง", "สะเปา"), "not": (),
     "pattern_url": "https://chiangraicity.go.th/news/detail/31989/data.html",
     "pattern_th": "ปีก่อน ๆ ตรงคืนเพ็ญ: ๔–๕ พ.ย. ๒๕๖๘ · ๑๕–๑๖ พ.ย. ๒๕๖๗",
     "pattern_en": "Past years on the full-moon nights: 4–5 Nov 2025 · 15–16 Nov 2024"},
    {"key": "wats", "th": "เวลาพิธีเย็นของวัด (วัดพันเตา วัดโลกโมฬี วัดชัยมงคล) ๒๕๖๙",
     "en": "Wat evening times 2569 (Wat Phan Tao, Wat Lok Moli, Wat Chai Mongkhon)",
     "window_th": "พฤศจิกายน", "window_en": "November",
     "check": "2026-11-10", "hosts": (), "words": (), "not": (),
     "pattern_url": "", "pattern_th": "วัดมักประกาศในสัปดาห์สุดท้ายก่อนงาน",
     "pattern_en": "Wats usually post these in the final weeks"},
]

# The manuscripts behind the page — Bot 02's table, verbatim from the lore
# draft (festival-push/drafts/wichaa-yi-peng.md), which cited the corpus.
MSS = [
    ("ms 5794", "อานิสงเดือนยี่ · อานิสงประทิศ", "วัดป่าซางน้อย เชียงใหม่ · จ.ศ. ๑๓๐๖ (1944)",
     "เดือนยี่กับประทีป เทศน์คู่กัน", "the second month + the lamp, preached together"),
    ("ms 24", "ปะทีปบูชา", "วัดพระสิงห์ เชียงใหม่ · ไม่ระบุปี",
     "อานิสงส์การบูชาประทีป", "lamp-worship anisong"),
    ("ms 2012 · ms 2202", "อานิสงตามประทีป", "วัดสูงเม่น แพร่ · จ.ศ. ๑๑๙๒ (1830) / ไม่ระบุปี",
     "บุญของการจุดประทีป มีปีจารึก", "lamp-merit preaching, dated span"),
    ("ms 2671", "อานิสงโจกตามประทีปน้ำมัน", "วัดพระบาทมิ่งเมือง แพร่ · จ.ศ. ๑๒๖๗ (1905)",
     "ประทีปน้ำมันโดยเฉพาะ", "the oil lamp specifically"),
    ("ms 209", "ดวงประทีปแก้ว", "วัดพระธาตุช้างค้ำ น่าน · พ.ศ. ๒๔๙๐ (1947)",
     "บุญของประทีป ฉบับน่าน", "lamp-merit preaching, Nan"),
    ("ms 6971 (หนังสือร่วมสมัย)", "จัดพิธีกรรมทางศาสนา ฉบับสมบูรณ์", "น. ๔๑–๔๒",
     "บทบูชากระทงประทีป ทั้งสองบทบาลี", "the Loi Krathong liturgy, both Pali verses"),
    ("ms 6966 (หนังสือร่วมสมัย)", "ประมวลคาถาตำราโบราณ", "น. ๑๓–๑๘",
     "คำอัญเชิญพระแม่คงคา มารยาทการอาบน้ำ", "พระแม่คงคา invocations; bathing courtesy"),
    ("ms 6983 (หนังสือร่วมสมัย)", "ตำราสร้างเครื่องรางของขลัง", "น. ๑๖๓–๑๖๔",
     "พิธีประทีปบูชา ตรรกะธงจุฬามณี", "ประทีปบูชา working rite; จุฬามณี banner logic"),
    ("ms 6968 (หนังสือร่วมสมัย)", "อภิมหามนต์คาถา", "น. ๑๗",
     "มหาราชครูอาง — ตำแหน่งครูบูชาด้วยแสงประทีป", "มหาราชครูอาง — the Lanna office of lamp-light worship"),
    ("ms 6989 (หนังสือร่วมสมัย)", "ตำรามหายันต์", "น. ๑๑–๑๒",
     "กระทงประทีปเป็นเครื่องมือค้นหา", "the krathong-lamp as a finding instrument"),
]

CSS = """
.yp-hero{position:relative;border-radius:1rem;overflow:hidden;margin:.4rem 0 1rem;background:#1a1410}
.yp-hero img{display:block;width:100%;height:auto;max-height:26rem;object-fit:cover;opacity:.92}
.yp-hero .yp-title{position:absolute;left:0;right:0;bottom:0;padding:1.2rem 1.1rem .9rem;
  background:linear-gradient(transparent,rgba(20,12,6,.86));color:#fff6e6}
.yp-hero h1{margin:0 0 .25rem;font-size:clamp(1.5rem,4.5vw,2.4rem);color:#fff6e6;text-shadow:0 1px 6px rgba(0,0,0,.6)}
.yp-hero .yp-sub{margin:0;font-size:1rem;opacity:.95}
.yp-count{display:inline-flex;gap:.5rem;align-items:baseline;margin-top:.5rem;padding:.35rem .8rem;border-radius:2rem;
  background:rgba(255,214,120,.18);border:1px solid rgba(255,214,120,.5);color:#ffe4a8;font-size:1.05rem}
.yp-count b{font-size:1.5rem;color:#ffd97a}
.yp-credit{color:var(--mute);font-size:.8rem;margin:.25rem 0 0}
.yp-credit a{color:var(--mute)}
.yp-nav{display:flex;flex-wrap:wrap;gap:.4rem;margin:.2rem 0 1rem}
.yp-nav a{padding:.3rem .7rem;border-radius:2rem;background:var(--soft);border:1px solid rgba(0,0,0,.07);text-decoration:none;font-size:.92rem}
.yp-mark{display:inline-block;font-size:.76rem;padding:.05rem .45rem;border-radius:1rem;background:var(--soft);color:var(--mute);border:1px solid rgba(0,0,0,.08);vertical-align:middle;margin-right:.3rem}
.yp-mark.org{background:rgba(184,145,46,.16)}
.yp-mark.wait{background:rgba(63,90,166,.12)}
.yp-mark.hand{background:rgba(180,52,26,.12)}
.yp-grid{display:grid;gap:.9rem;grid-template-columns:repeat(auto-fit,minmax(17rem,1fr));margin:.6rem 0}
.yp-card{padding:.9rem 1rem;border:1px solid rgba(0,0,0,.08);border-radius:.9rem;background:var(--card,#fff)}
.yp-card h3{margin:.1rem 0 .45rem}
.yp-card img{width:100%;height:auto;border-radius:.6rem;margin:.2rem 0 .5rem;aspect-ratio:3/2;object-fit:cover}
.yp-card .nopic{aspect-ratio:3/2;border-radius:.6rem;border:1px dashed rgba(0,0,0,.2);display:flex;align-items:center;justify-content:center;
  color:var(--mute);font-size:.9rem;text-align:center;padding:1rem;margin:.2rem 0 .5rem}
.yp-moon{display:grid;grid-template-columns:minmax(9rem,12rem) 1fr;gap:1rem;align-items:center;margin:.5rem 0}
.yp-moon svg{width:100%;height:auto}
.yp-months{display:grid;grid-template-columns:repeat(12,1fr);gap:2px;margin:.6rem 0;font-size:.78rem;text-align:center}
.yp-months div{padding:.35rem .1rem;background:var(--soft);border-radius:.3rem}
.yp-months div.is{background:rgba(184,145,46,.35);font-weight:600}
.yp-months small{display:block;color:var(--mute);font-size:.7rem}
.yp-quote{margin:.8rem 0;padding:.8rem 1rem;border-left:4px solid #B8912E;background:var(--soft);border-radius:0 .6rem .6rem 0;font-size:.98rem}
.yp-quote .pali{font-style:italic;letter-spacing:.01em}
table.yp-ways,table.yp-gates,table.yp-week,table.yp-mss{width:100%;border-collapse:collapse;margin:.5rem 0 1rem;font-size:.94rem}
.yp-ways th,.yp-ways td,.yp-gates th,.yp-gates td,.yp-week th,.yp-week td,.yp-mss th,.yp-mss td{padding:.5rem .55rem;border-bottom:1px solid rgba(0,0,0,.08);vertical-align:top;text-align:left}
.yp-week tr.full td{background:rgba(184,145,46,.14)}
.yp-week td.day{white-space:nowrap;font-weight:600}
.yp-wait{color:var(--mute)}
.yp-venues{list-style:none;padding:0;margin:.4rem 0}
.yp-venues li{padding:.5rem 0;border-bottom:1px solid rgba(0,0,0,.07)}
.yp-venues small{display:block;color:var(--mute);margin-top:.15rem}
.yp-issue{margin:.5rem 0;border:1px solid rgba(0,0,0,.08);border-radius:.8rem;background:var(--card,#fff)}
.yp-issue summary{padding:.7rem .9rem;cursor:pointer;font-weight:600}
.yp-issue summary small{font-weight:400;color:var(--mute);margin-left:.4rem}
.yp-issue .body{padding:0 1rem .9rem;white-space:pre-line;font-size:.97rem}
.yp-issue .body .en{white-space:normal;margin-top:.7rem;padding-top:.6rem;border-top:1px dashed rgba(0,0,0,.12);color:var(--mute);font-size:.92rem}
.yp-issue.future,.yp-issue.held{opacity:.85}
.yp-issue.future summary,.yp-issue.held summary{cursor:default;font-weight:500}
.yp-figure{margin:.6rem 0 1rem}
.yp-figure img{width:100%;height:auto;border-radius:.8rem}
.yp-home ol{padding-left:1.2rem}
.yp-home li{margin:.4rem 0}
@media (max-width:600px){.yp-moon{grid-template-columns:1fr}.yp-months{font-size:.68rem}}
@media (prefers-color-scheme:dark){.yp-card,.yp-issue{border-color:rgba(255,255,255,.1)}}
"""

# ------------------------------------------------------------------ helpers

def _md(s, esc):
    """The few marks the drip uses: **bold**, *italic*, blank-line paragraphs.
    Everything is escaped first; only the marks become tags."""
    s = esc(s)
    s = re.sub(r"\*\*(.+?)\*\*", r"<b>\1</b>", s)
    s = re.sub(r"(?<!\*)\*(?!\*)(.+?)(?<!\*)\*(?!\*)", r"<i>\1</i>", s)
    return s


def moon_svg(today, bi_text, esc):
    """Tonight's disc and the full disc it is walking toward. Mean-synodic
    arithmetic on the same new-moon epoch build.py uses (coucal-clock's
    lunation), labelled as the approximation it is — the ephemeris
    instrument is wichaa.net/moon."""
    epoch = datetime.datetime(2026, 1, 18, 19, 52, tzinfo=datetime.timezone.utc)
    now = datetime.datetime(today.year, today.month, today.day, 12, tzinfo=datetime.timezone.utc)
    lun = ((now - epoch).total_seconds() / 86400.0) / 29.530588
    ph = lun % 1.0                       # 0 new, .5 full
    illum = (1 - math.cos(2 * math.pi * ph)) / 2
    waxing = ph < 0.5
    R = 44
    # Terminator as an ellipse whose x-radius runs -R..R with illumination.
    k = (2 * illum - 1)                  # -1 new … 0 half … 1 full
    rx = abs(k) * R
    # Lit half + terminator lobe, drawn as two arcs.
    if waxing:
        lit = (f"M50,{50 - R} A{R},{R} 0 0 1 50,{50 + R} "
               f"A{rx:.1f},{R} 0 0 {1 if k > 0 else 0} 50,{50 - R} Z")
    else:
        lit = (f"M50,{50 - R} A{R},{R} 0 0 0 50,{50 + R} "
               f"A{rx:.1f},{R} 0 0 {0 if k > 0 else 1} 50,{50 - R} Z")
    pct = int(round(illum * 100))
    label = bi_text(f"ดวงจันทร์คืนนี้ (โดยประมาณ) สว่าง {pct}% — {'ข้างขึ้น' if waxing else 'ข้างแรม'}",
                    f"Tonight's moon, approximately {pct}% lit, {'waxing' if waxing else 'waning'}")
    return (f'<svg role="img" aria-label="{esc(label)}" viewBox="0 0 100 100" xmlns="http://www.w3.org/2000/svg">'
            f'<circle cx="50" cy="50" r="{R}" fill="#2b2418"/>'
            f'<path d="{lit}" fill="#ffe9b0"/>'
            f'<circle cx="50" cy="50" r="{R}" fill="none" stroke="#B8912E" stroke-width="1.2"/>'
            f'</svg>'), pct, waxing


def _load_picks():
    try:
        d = json.loads(PICKS.read_text())
    except Exception:
        return {}
    return {p["slug"]: p for p in d.get("picks", []) if p.get("slug")}


def _photo(slug, picks, esc, att, bi_text, alt_th, alt_en, eager=False):
    p = picks.get(slug)
    if not p:
        return "", ""
    credit = (f'<p class="yp-credit">📷 <a href="{att(p.get("page", ""))}" rel="noopener nofollow">'
              f'{esc(p.get("artist", ""))}</a> · {esc(p.get("licence", ""))} · Wikimedia Commons</p>')
    img = (f'<img src="site/{esc(slug)}.jpg" alt="{att(bi_text(alt_th, alt_en))}" '
           f'loading="{"eager" if eager else "lazy"}" width="{p.get("width") or 1000}" height="{p.get("height") or 700}">')
    return img, credit


def _match_gate(gate, rows):
    """The announced rows that answer this gate: host and a word in the
    source name, minus the words the slot is not about."""
    out = []
    for r in rows:
        url = r.get("source_url", "")
        name = (r.get("source_name_th", "") + " " + r.get("title_th", "") + " " + r.get("note_th", ""))
        host_ok = any(h in url for h in gate["hosts"]) if gate["hosts"] else False
        word_ok = any(w in name for w in gate["words"]) if gate["words"] else False
        bad = any(w in name for w in gate["not"])
        if host_ok and word_ok and not bad:
            out.append(r)
    return out


def _thai_date(d, g):
    wd = ["จันทร์", "อังคาร", "พุธ", "พฤหัสบดี", "ศุกร์", "เสาร์", "อาทิตย์"][d.weekday()]
    return f'{wd} {d.day} {g["MONTH_TH"][d.month]} {d.year + 543}'


def _en_date(d):
    return d.strftime("%A %-d %B %Y")


# --------------------------------------------------------------------- emit

def emit(g, events, data):
    page, bi, esc, att = g["page"], g["bi"], g["esc"], g["att"]
    bi_text = g.get("bi_text") or (lambda th, en: f"{th} · {en}")
    BASE, DOCS = g["BASE"], g["DOCS"]
    today = datetime.date.fromisoformat(g["BUILD_DATE"])
    picks = _load_picks()
    fest = next((f for f in g["FESTIVALS"] if f["id"] == FEST_ID), None)
    if fest is None:
        raise SystemExit("yipeng_layer: canon has no " + FEST_ID)
    ann = (g.get("_ANNOUNCED") or {}).get(FEST_ID) or []

    by_id, prov_of = {}, {}
    for p in g["PROVINCES"]:
        for r in data[p["key"]]:
            by_id[r["id"]] = r
            prov_of[r["id"]] = p["key"]

    (DOCS / "yipeng.css").write_text(CSS)

    # ---- hero + countdown ----------------------------------------------
    days = (ANCHOR - today).days
    if days > 0:
        count_th, count_en, n = "อีก", "days to the full moon", days
    elif days == 0:
        count_th, count_en, n = "คืนนี้", "tonight", ""
    else:
        count_th, count_en, n = "ผ่านไปแล้ว", "days since", -days
    hero_img, hero_credit = _photo(PHOTO["hero"], picks, esc, att, bi_text,
                                   "โคมลอยขึ้นฟ้าคืนยี่เป็ง เชียงใหม่", "Sky lanterns rising on a Yi Peng night, Chiang Mai", eager=True)
    hero = (f'<div class="yp-hero">{hero_img}<div class="yp-title">'
            f'<h1>🏮 {bi("ยี่เป็ง – ลอยกระทง ๒๕๖๙", "Yi Peng &amp; Loi Krathong 2026")}</h1>'
            f'<p class="yp-sub">{bi("คืนเพ็ญเดือนยี่ — " + _thai_date(ANCHOR, g), "Full moon of the second Lanna month — " + _en_date(ANCHOR))}</p>'
            f'<div class="yp-count" data-anchor="{ANCHOR.isoformat()}">'
            f'<span class="th">{count_th}</span> <b class="n">{n}</b> <span class="u">{bi("วัน", count_en) if n != "" else bi("", "")}</span></div>'
            f'</div></div>{hero_credit}')

    nav = "".join(f'<a href="#{k}">{bi(th, en)}</a>' for k, th, en in [
        ("moon", "คืนไหน", "the night"), ("map", "แผนที่", "the map"), ("lights", "โคมสามดวง", "three lights"),
        ("krathong", "กระทง", "the raft"), ("ways", "หลายทาง", "many ways"), ("notices", "ประกาศ", "notices"),
        ("week", "สัปดาห์งาน", "festival week"), ("letters", "จดหมายรายสัปดาห์", "the letters"),
        ("sources", "ที่มา", "sources")])

    # ---- the night: moon, arithmetic, calendar rows ---------------------
    msvg, pct, waxing = moon_svg(today, bi_text, esc)
    phase_th = "ข้างขึ้น" if waxing else "ข้างแรม"
    phase_en = "waxing" if waxing else "waning"
    moon_line_th = f"ดวงจันทร์คืนนี้สว่างราว {pct}% ({phase_th}) — คำนวณอย่างหยาบจากรอบจันทร์เฉลี่ย เครื่องมือจริงอยู่ที่"
    moon_line_en = f"Tonight’s moon is about {pct}% lit ({phase_en}) — mean-cycle arithmetic; the real instrument is"
    import answers_layer
    cal, cal_src = answers_layer.calendar_rows()
    cal_rows = [(cal[(FEST_ID, y)], cal_src[cal[(FEST_ID, y)]["source"]])
                for y in (today.year, today.year + 1) if (FEST_ID, y) in cal]
    cal_html = ""
    if cal_rows:
        lis = []
        for r, s in cal_rows:
            d0 = datetime.date.fromisoformat(r["date_start"])
            d1 = datetime.date.fromisoformat(r["date_end"])
            th = _thai_date(d0, g) + ("" if d0 == d1 else f' – {d1.day} {g["MONTH_TH"][d1.month]}')
            en = _en_date(d0) + ("" if d0 == d1 else f" – {d1.day} {d1.strftime('%B')}")
            lis.append(f'<li><span class="yp-mark">{bi("ปฏิทิน", "almanac")}</span><b>{bi(th, en)}</b> — '
                       f'{bi(esc(r.get("note_th", "")), esc(r.get("note_en", "")))} '
                       f'<a href="{att(s["url"])}" rel="noopener nofollow">{bi("ที่มา", "source")}</a></li>')
        cal_html = f'<ul class="instances">{"".join(lis)}</ul>'
    months = []
    for c in range(1, 13):
        lanna = (c + 1) % 12 + 1        # central month c is Lanna month c+2
        name = {1: "เจียง", 2: "ยี่"}.get(lanna, f"{lanna}")
        cls = ' class="is"' if c == 12 else ""
        months.append(f'<div{cls}>{c}<small>เดือน{name}</small></div>')
    night = (
        f'<h2 id="moon">🌕 {bi("คืนไหน", "Which night")}</h2>'
        f'<div class="yp-moon">{msvg}<div>'
        f'<p>{bi("<b>เป็ง</b> คือคำเมืองว่า <i>เพ็ญ</i> — <b>ยี่</b> คือ <i>ที่สอง</i> ยี่เป็งจึงคือคืนเพ็ญเดือนยี่ตรงตัว ล้านนานับเดือนเร็วกว่าภาคกลางสองเดือน เดือนสิบสองของภาคกลาง — เดือนลอยกระทง — จึงเป็นเดือนยี่ของทางเหนือพอดี", "<b>Peng</b> is the northern word for the <i>full moon</i>; <b>yi</b> is <i>second</i>. Yi Peng is, exactly, the full moon of the second month — and the Lanna count runs two months ahead of the central one, so the 12th central month, the month of Loi Krathong, is the north’s second month.", raw=True)}</p>'
        f'<p class="tinynote"><span class="yp-mark">{bi("ปฏิทิน", "almanac")}</span>'
        f'{bi(moon_line_th, moon_line_en)} '
        f'<a href="https://wichaa.net/moon">wichaa.net/moon</a></p></div></div>'
        f'<div class="yp-months">{"".join(months)}</div>'
        f'<p class="tinynote">{bi("แถวบน = เดือนจันทรคติภาคกลาง · แถวล่าง = ชื่อเดือนล้านนา (เจียง ยี่ สาม …) · ช่องเข้ม = เดือนสิบสอง ที่ทางเหนือเรียกเดือนยี่", "Top = central lunar month · below = the Lanna month name (chiang, yi, three …) · the shaded cell is the 12th month, which the north calls yi")}</p>'
        f'{cal_html}'
        f'<p class="tinynote"><a href="festival-dates.html">{bi("วันเทศกาลทุกงาน ปีนี้และปีหน้า", "All festival dates, this year and next")} →</a> · '
        f'<a href="festivals/{FEST_ID}.html">{bi("หน้าทะเบียนของงานนี้", "the register entry")} →</a></p>')

    # ---- the map ---------------------------------------------------------
    located, rows = [], []
    for v in VENUES:
        r = by_id.get(v.get("place_id") or "")
        lat = v.get("lat") if v.get("lat") is not None else (r.get("lat") if r else None)
        lng = v.get("lng") if v.get("lng") is not None else (r.get("lng") if r else None)
        pv = v.get("prov") or (prov_of.get(r["id"]) if r else "cm")
        link = ""
        if r:
            link = f' — <a href="{pv}/p/{g["place_slug"](r)}.html">{bi("ดูหน้าสถานที่", "place page")}</a>'
        elif v.get("url"):
            link = f' — <a href="{att(v["url"])}" rel="noopener nofollow">{bi("หน้าผู้จัด", "organizer page")}</a>'
        if v.get("url") and r:
            link += f' · <a href="{att(v["url"])}" rel="noopener nofollow">{bi("หน้าผู้จัด", "organizer")}</a>'
        mark = {"canon": ("ทะเบียน", "canon", ""), "organizer": ("ผู้จัด", "organizer", " org"),
                "press": ("ข่าว/แนวปฏิบัติ", "press", " wait")}[v["mark"]]
        placed = (f' <span class="yp-mark hand">{bi("หมุดวางมือ — กลางสะพาน ไม่ใช่ระเบียน", "hand-placed pin at the span’s midpoint, not a record")}</span>'
                  if v.get("placed") == "hand" else "")
        unpinned = "" if lat is not None else f' <span class="yp-mark wait">{bi("ยังไม่มีหมุด", "no pin yet")}</span>'
        rows.append(f'<li><span class="yp-mark{mark[2]}">{bi(mark[0], mark[1])}</span><b>{bi(v["th"], v["en"])}</b>{link}{placed}{unpinned}'
                    f'<small>{bi(v["note_th"], v["note_en"])}</small></li>')
        if lat is not None and lng is not None and pv == "cm":
            located.append({"place": {"id": v.get("place_id") or "yp-" + v["key"], "lat": lat, "lng": lng,
                                      "name": g["name_text"](r) if r else v["th"]}})
    map_html = g["event_map_svg"](located) if located else ""
    map_sec = (f'<h2 id="map">📍 {bi("แผนที่ — เมืองมารวมกันตรงไหน", "The map — where the city gathers")}</h2>'
               f'{map_html}'
               f'<p class="tinynote">{bi("หมุดเชียงใหม่ในกรอบคูเมือง เชียงรายอยู่ในรายการข้างล่าง (ร้อยกิโลเมตรไม่ควรอยู่ในกรอบเดียวกัน) · ลากดูได้เมื่อแผนที่พื้นโหลด ก่อนนั้นคือภาพวาด", "Chiang Mai pins framed against the moat; Chiang Rai stays in the list (a hundred kilometres do not belong in one frame) · pan once the basemap arrives; until then it is the drawing")}</p>'
               f'<ul class="yp-venues">{"".join(rows)}</ul>')

    # ---- three lights ------------------------------------------------
    loi_img, loi_cr = _photo(PHOTO["khom_loi"], picks, esc, att, bi_text, "โคมลอยเหนือเมืองเชียงใหม่ คืนลอยกระทง", "Sky lanterns over Chiang Mai on the Loi Krathong night")
    kw_img, kw_cr = _photo(PHOTO["khom_khwaen"], picks, esc, att, bi_text, "โคมล้านนาแขวน ที่กว๊านพะเยา", "A hanging Lanna lantern at Kwan Phayao")
    lights = (
        f'<h2 id="lights">🏮 {bi("โคมสามดวง — ฟ้า ชายคา ขอบหน้าต่าง", "Three lights — sky, eave, sill")}</h2>'
        f'<div class="yp-grid">'
        f'<div class="yp-card">{loi_img}{loi_cr}<h3>{bi("โคมลอย — ดวงที่ขึ้นฟ้า", "โคมลอย — the lantern that rises")}</h3>'
        f'<p><span class="yp-mark">{bi("ประเพณีว่า", "tradition holds")}</span>{bi("เป็นการถวายแสงขึ้นสู่พระเกตุแก้วจุฬามณีบนสวรรค์ชั้นดาวดึงส์ ที่คนเดินไปไหว้ไม่ถึง แสงจึงต้องบินไปแทน", "an offering of light sent up toward the Culamani reliquary in Tavatimsa, which no pilgrim can walk to — so the light must fly")}</p>'
        f'<p><span class="yp-mark">{bi("ทะเบียน", "canon")}</span>{bi(fest["auspicious_th"], fest["auspicious_en"])}</p>'
        f'<p class="tinynote">{bi("ปล่อยที่ไหน เมื่อไร — ดูช่องประกาศเขตปล่อยโคมข้างล่าง", "Where and when to release — see the sky notice below")} <a href="#notices">↓</a></p></div>'
        f'<div class="yp-card">{kw_img}{kw_cr}<h3>{bi("โคมแขวน — ดวงใต้ชายคา", "โคมแขวน — the eave lantern")}</h3>'
        f'<p><span class="yp-mark">{bi("ประเพณีว่า", "tradition holds")}</span>{bi("แสงที่ถวายไว้อย่างสงบ ประดับประตู ชายคา และซุ้มวิหารตลอดสัปดาห์งาน เชื้อเชิญบุญมาถึงประตู — ดวงที่อยู่บ้านของโคมลอย ไม่ต้องรอประกาศใด", "light offered in stillness, dressing gates, eaves and viharn doorways through festival week, welcoming merit to the door — the stay-home sibling of the sky lantern; it needs no notice")}</p></div>'
        f'<div class="yp-card"><div class="nopic">{bi("ยังไม่มีภาพผางประทีปในคลังภาพของเรา — ช่องนี้ว่างไว้ ไม่ใส่ภาพแทน", "No photo of ผางประทีป in our pool yet — the slot stays empty rather than take a stand-in")}</div>'
        f'<h3>{bi("ผางประทีป — ชั้นที่เก่าที่สุด", "ผางประทีป — the oldest layer")}</h3>'
        f'<p><span class="yp-mark">{bi("ใบลาน", "manuscript")}</span>{bi("ถ้วยดินใส่น้ำมันหรือขี้ผึ้ง ไส้หนึ่งเส้น เรียงบนขอบหน้าต่าง ขั้นบันได ลานเจดีย์ — และในคลังใบลาน นี่คือดวงที่ลึกที่สุด: อานิสงส์การจุดประทีปเทศน์ไว้ที่วัดสูงเม่น (๒๓๗๓) วัดพระสิงห์ วัดพระบาทมิ่งเมือง (๒๔๔๘) วัดพระธาตุช้างค้ำ (๒๔๙๐) และวัดป่าซางน้อย (๒๔๘๗) — ห้าวัด สามจังหวัด", "a clay cup of oil or wax with one wick, in rows along a sill, a stair, a chedi terrace — and in the manuscript record the deepest light of the three: lamp-merit sermons at Wat Sung Men (1830), Wat Phra Sing, Wat Phra Bat Ming Mueang (1905), Wat Phra That Chang Kham (1947) and Wat Pa Sak Noi (1944) — five temples, three provinces")}</p>'
        f'<p><span class="yp-mark">{bi("อนุมาน", "inference")}</span>{bi("ดวงไฟที่ถ่อมที่สุดของเทศกาล คือดวงที่มีคนเขียนถึงมากที่สุด", "the humblest flame of the festival is the one most written about")}</p></div>'
        f'</div>')

    # ---- the raft ----------------------------------------------------------
    kr_img, kr_cr = _photo(PHOTO["krathong"], picks, esc, att, bi_text, "กระทงในน้ำ คืนลอยกระทง เชียงใหม่", "Krathongs on the water, Loi Krathong night, Chiang Mai")
    raft = (
        f'<h2 id="krathong">🌊 {bi("กระทง — แพน้อยกับคำขอขมา", "The raft, and the pardon")}</h2>'
        f'<div class="yp-figure">{kr_img}{kr_cr}</div>'
        f'<p><span class="yp-mark">{bi("ทะเบียน", "canon")}</span>{bi("กระทงแบบดั้งเดิมคือหยวกกล้วยฝานเป็นแว่น ห่อใบตองพับ ปักดอกไม้ ธูป เทียน และมักมีเหรียญหนึ่งเหรียญ", "the classic krathong is a slice of banana trunk dressed with folded leaf, a flower, incense, a candle, often a coin")}</p>'
        f'<p><span class="yp-mark">{bi("ประเพณีว่า", "tradition holds")}</span>{bi("สิ่งที่ลอยไปคือคำขอขมาต่อ <b>พระแม่คงคา</b> — ขอบคุณสำหรับน้ำตลอดปี และขออภัยสำหรับสิ่งที่เราทิ้งลงไป", "what floats away is a pardon asked of <b>Mae Khongkha</b>, the mother of waters — thanks for the year’s water, and forgiveness for what we have put into her", raw=True)} '
        f'<span class="yp-mark">{bi("ทะเบียน", "canon")}</span>{bi(fest["auspicious_th"].split(" ส่วน")[0], fest["auspicious_en"].split(";")[0])}</p>'
        f'<p><span class="yp-mark">{bi("หนังสือร่วมสมัย", "contributed volume")}</span>{bi("ในบทสวดที่เป็นทางการ กระทงมีอีกชื่อหนึ่ง — <b>กระทงประทีป</b> — กระทง<i>ดวงไฟ</i> ถวายรอยพระพุทธบาทริมแม่น้ำนัมมทา (จัดพิธีกรรมทางศาสนา ฉบับสมบูรณ์ — คลังวิชชา ms 6971 น. ๔๑–๔๒)", "in the formal liturgy the raft has a second name — <b>krathong pratip</b>, a <i>lamp</i>-krathong offered to the Buddha’s footprint on the far Narmada (ms 6971, pp. 41–42, in the wichaa corpus)", raw=True)}</p>'
        f'<div class="yp-quote"><span class="pali">มะยัง โภนโต · อิมินา ปะทีเปนะ · นัมมะทายะ นะทิยา · วาลิกาปุลิเน · มุนิโน · ปาทะวะลัญชัง · อะภิปูเชมะ …</span><br>'
        f'{bi("“ด้วยดวงประทีปนี้ ข้าพเจ้าทั้งหลายขอบูชารอยพระพุทธบาท อันประดิษฐานเหนือหาดทรายแห่งแม่น้ำนัมมทา”", "“With this lamp we worship the footprint of the Sage, set upon the sandy bank of the river Nammada.”")}</div>'
        f'<p><span class="yp-mark">{bi("อนุมาน", "inference")}</span>{bi("สองความหมายไม่ได้แย่งกัน แต่ซ้อนกัน — กระทงใบเดียวพาไปทั้งคู่ และไม่มีใครริมน้ำต้องเลือก", "the two are layers, not rivals — one float carries both, and nobody on the riverbank is asked to choose")}</p>'
        f'<div class="yp-card yp-home"><h3>{bi("พับเอง ทำที่บ้าน", "Fold your own, at home")}</h3>'
        f'<ol>'
        f'<li>{bi("<b>ใบตอง ไม่ใช่โฟม</b> ใบตองย่อยสลายได้ โฟมไม่ได้ — วัดริมน้ำหลายแห่งแจกใบตองให้พับเองฟรี", "<b>Leaf, not foam.</b> Leaf breaks down; foam does not — several riverside wats hand out banana leaf so you can fold your own, free", raw=True)} <span class="yp-mark">{bi("ทะเบียน", "canon")}</span></li>'
        f'<li>{bi("<b>ฝานหยวกกล้วย</b>เป็นแว่นหนาสักสองนิ้ว ห่อขอบด้วยใบตองพับกลีบ กลัดด้วยไม้กลัด", "<b>Slice a banana trunk</b> about two fingers thick, wrap the rim in folded leaf petals, pin with bamboo pins", raw=True)}</li>'
        f'<li>{bi("<b>ปักดอกไม้ ธูป เทียน</b> — และเหรียญหนึ่งเหรียญถ้าถือตามบ้าน", "<b>Set a flower, incense, a candle</b> — and one coin if your house keeps that", raw=True)}</li>'
        f'<li>{bi("<b>จุดผางประทีป</b>ตอนเดือนขึ้น เรียงบนขอบหน้าต่าง ขั้นบันได เสาประตู วางบนจานกันหยด ห่างผ้าม่านสักฝ่ามือ ลมแรงย้ายเข้าใน", "<b>Light the ผางประทีป</b> at moonrise along a sill, a stair, a gate post — on a plate, a hand’s width from any curtain; if the wind is up, bring them in", raw=True)}</li>'
        f'<li>{bi("<b>แขวนโคมหนึ่งดวง</b>ใต้ชายคา ไว้ทั้งคืน", "<b>Hang one lantern</b> at the eave, through the night", raw=True)}</li>'
        f'<li>{bi("<b>กล่าวคำขอขมาต่อพระแม่คงคา</b> ด้วยคำของท่านเอง หรือบทบาลีข้างบน แล้วปล่อยกระทงจากท่าน้ำ", "<b>Speak the pardon to Mae Khongkha</b> in your own words, or the Pali above, and set the raft on the water", raw=True)} <span class="yp-mark">{bi("ประเพณีว่า", "tradition holds")}</span></li>'
        f'</ol></div>')

    # ---- many ways, one moon -----------------------------------------------
    ways_rows = [
        ("ริมน้ำและกลางเมือง — สะพานนวรัฐ ประตูท่าแพ สามกษัตริย์", "Riverbank and city — Nawarat Bridge, Tha Phae Gate, Three Kings",
         "๒๔–๒๕ พ.ย. (งานเมืองรอประกาศ)", "24–25 Nov (city program awaited)",
         "เข้าฟรี · กระทง ๓๐–๑๐๐ บาท (หรือพับเองฟรี) · โคมลอย ๕๐–๑๐๐ บาท — ราคาปี ๒๕๖๘", "Free · krathong ฿30–100 (or fold your own free) · sky lantern ฿50–100 — 2568 prices",
         "ทะเบียน", "canon", ""),
        ("ลานวัด — โคมใต้ชายคา ประทีปบนลานเจดีย์", "Wat courtyard — lanterns at the eaves, lamps on the terrace",
         "ตลอดสัปดาห์งาน (เวลาพิธีรอวัด)", "Through festival week (times await each wat)",
         "เข้าฟรี · แต่งกายสุภาพ ถอดรองเท้าก่อนขึ้นวิหาร ขออนุญาตก่อนถ่ายคนที่กำลังไหว้", "Free · dress modestly, shoes off before the viharn, ask before photographing anyone at prayer",
         "ประเพณีว่า", "tradition", ""),
        ("ที่บ้าน — ผางประทีปบนขอบหน้าต่าง โคมแขวนหนึ่งดวง", "At home — ผางประทีป on the sill, one hanging lantern",
         "คืนเพ็ญ", "The full-moon night",
         "ไม่กี่สิบบาท · ไม่ต้องมีงาน ไม่ต้องมีแม่น้ำ ไม่ต้องรอประกาศ", "A few tens of baht · no venue, no river, no notice needed",
         "ใบลาน", "manuscript", ""),
        ("CAD Khomloy Sky Lantern Festival — ศูนย์วัฒนธรรมเชียงใหม่", "CAD Khomloy Sky Lantern Festival — CAD Cultural Center",
         "๒๔ และ ๒๕ พ.ย.", "24 and 25 Nov",
         "บัตร ๔,๙๐๐–๑๕,๙๐๐ บาท · <a href=\"https://yipenglanternfestival.in.th/\" rel=\"noopener nofollow\">หน้าผู้จัด</a>", "Tickets ฿4,900–15,900 · <a href=\"https://yipenglanternfestival.in.th/\" rel=\"noopener nofollow\">organizer</a>",
         "ผู้จัด", "organizer", " org"),
        ("Yee Peng Lanna International — ลานนาธุตังคสถาน สันทราย", "Yee Peng Lanna International — Lanna Dhutanka, San Sai",
         "๒๔ และ ๒๕ พ.ย. ราว ๑๒.๐๐–๒๑.๐๐ น. · ธีม “Six Senses”", "24 and 25 Nov, about 12:00–21:00 · theme “Six Senses”",
         "ราคาบัตร: ยังไม่ได้เก็บ (ผู้จัดขายผ่าน Eventbrite) · <a href=\"https://www.eventbrite.com/e/yeepeng-lanna-international-2026-chiang-mai-official-ticket-24-nov-2026-tickets-1978873470821\" rel=\"noopener nofollow\">หน้าผู้จัด</a>", "Ticket price: not captured (organizer sells on Eventbrite) · <a href=\"https://www.eventbrite.com/e/yeepeng-lanna-international-2026-chiang-mai-official-ticket-24-nov-2026-tickets-1978873470821\" rel=\"noopener nofollow\">organizer</a>",
         "ผู้จัด", "organizer", " org"),
        ("เชียงราย — ริมน้ำกก ฝั่งหมิ่น", "Chiang Rai — the Kok riverbank, Fang Min",
         "รอเทศบาลนครเชียงราย (ปีก่อน ๆ ตรงคืนเพ็ญ)", "Awaits the municipality (past years on the full-moon nights)",
         "เข้าฟรี · กระทงใหญ่กลางน้ำ สะเปาจากริมตลิ่ง — ตามประกาศปีก่อน ๆ", "Free · a grand krathong midstream, สะเปา rafts from the bank — per past years’ notices",
         "ประกาศเทศบาล (ปีก่อน)", "municipal, past years", " wait"),
    ]
    ways = (f'<h2 id="ways">🌕 {bi("หลายทาง เพ็ญเดียว", "Many ways, one full moon")}</h2>'
            f'<p>{bi("คืนวันที่ ๒๔ พฤศจิกายนมีหลายวิธีที่จะอยู่ในคืนนั้น และทุกวิธีคือยี่เป็งเหมือนกัน ต่างกันแค่ขนาดของงาน ท่านเลือกตามแรง ตามเวลา ตามกระเป๋าของท่านเอง", "There are several ways to be inside the night of 24 November, and each of them is Yi Peng — they differ in scale, not in kind. Choose by your own energy, evening and purse.")}</p>'
            f'<table class="yp-ways"><thead><tr><th>{bi("ทาง", "the way")}</th><th>{bi("เมื่อไร", "when")}</th><th>{bi("จ่ายอะไร", "what you pay")}</th></tr></thead><tbody>'
            + "".join(f'<tr><td><span class="yp-mark{cls}">{bi(mth, men)}</span>{bi(a, b)}</td><td>{bi(c, d)}</td><td>{bi(e, f, raw=True)}</td></tr>'
                      for a, b, c, d, e, f, mth, men, cls in ways_rows)
            + f'</tbody></table>'
            f'<p class="tinynote"><span class="yp-mark">{bi("ทะเบียน — ช่องตรวจสอบ", "canon — verify field")}</span>{bi(fest["verify_th"], fest["verify_en"])}</p>')

    # ---- the notices the year still owes -------------------------------
    gate_rows, gate_state = [], {}
    for gt in GATES:
        hits = _match_gate(gt, ann)
        chk = datetime.date.fromisoformat(gt["check"])
        if hits:
            r = hits[0]
            d0 = datetime.date.fromisoformat(r["date_start"])
            d1 = datetime.date.fromisoformat(r["date_end"])
            th = _thai_date(d0, g) + ("" if d0 == d1 else f' – {d1.day} {g["MONTH_TH"][d1.month]}')
            en = _en_date(d0) + ("" if d0 == d1 else f" – {d1.day} {d1.strftime('%B')}")
            status = (f'<span class="yp-mark org">{bi("ประกาศแล้ว", "announced")}</span><b>{bi(th, en)}</b><br>'
                      f'<span class="tinynote">{bi("ประกาศโดย " + esc(r.get("source_name_th", "")), "announced by " + esc(r.get("source_name_en", "")))} — '
                      f'<a href="{att(r["source_url"])}" rel="noopener nofollow">{bi("ดูประกาศ", "the announcement")}</a></span>')
            gate_state[gt["key"]] = "announced"
        else:
            when = (bi("เราไปดูตั้งแต่ " + _thai_date(chk, g), "we check from " + _en_date(chk)) if today < chk
                    else bi("กำลังดูอยู่ทุกสัปดาห์ตั้งแต่ " + _thai_date(chk, g), "checking weekly since " + _en_date(chk)))
            status = (f'<span class="yp-mark wait">{bi("ยังไม่ประกาศ", "not yet announced")}</span>'
                      f'{bi("คาดว่าออก " + gt["window_th"], "expected " + gt["window_en"])}<br><span class="tinynote">{when}</span>')
            gate_state[gt["key"]] = "waiting"
        pat = (f'<a href="{att(gt["pattern_url"])}" rel="noopener nofollow">{bi(gt["pattern_th"], gt["pattern_en"])}</a>'
               if gt["pattern_url"] else bi(gt["pattern_th"], gt["pattern_en"]))
        gate_rows.append(f'<tr><td>{bi(gt["th"], gt["en"])}</td><td>{status}</td><td class="yp-wait">{pat}</td></tr>')
    notices = (f'<h2 id="notices">📣 {bi("ยังไม่ประกาศ", "Not yet announced")}</h2>'
               f'<p>{bi("ทุกปีทางราชการประกาศสี่อย่างนี้ในเดือนสุดท้าย ๆ ก่อนงาน หน้านี้จะเติมช่องเองทันทีที่ประกาศจริงเข้าระบบ พร้อมลิงก์ไปที่ประกาศ", "Each year four official notices land in the final weeks before the festival. This page fills each slot on its own the moment the real notice enters the system, with the link.")}</p>'
               f'<table class="yp-gates"><thead><tr><th>{bi("ประกาศ", "notice")}</th><th>{bi("สถานะ", "status")}</th><th>{bi("รูปแบบปีก่อน", "last year’s pattern")}</th></tr></thead><tbody>{"".join(gate_rows)}</tbody></table>'
               f'<p class="tinynote">{bi("ถ้าประกาศออกก่อนหน้านี้จะทัน — ถามคนขายโคมที่แผง วัดที่ท่านไป หรือที่พักของท่านได้เลย คนในพื้นที่รู้กันดีว่าคืนนั้นฟ้าเปิดตรงไหน · เห็นประกาศก่อนเรา บอกมดได้ที่", "If a notice lands before this page catches it, ask the stall you buy from, the wat you visit, or your host — local people know which sky is open that night · saw a notice before we did? tell the ants at")} <a href="list-your-event.html">{bi("หน้าลงงาน", "the listing page")}</a></p>')

    # ---- festival week, as a frame -------------------------------------------
    def wait(th, en):
        return f'<span class="yp-mark wait">{bi("รอประกาศ", "awaiting notice")}</span><span class="yp-wait">{bi(th, en)}</span>'
    def org(th, en):
        return f'<span class="yp-mark org">{bi("ผู้จัด", "organizer")}</span>{bi(th, en)}'
    def canon(th, en):
        return f'<span class="yp-mark">{bi("ทะเบียน", "canon")}</span>{bi(th, en)}'
    week_rows = [
        (datetime.date(2026, 11, 22), False, [wait("กำหนดการเมือง ๒๕๖๙ — ปีก่อน ๆ มีขบวนแห่ ประกวดกระทงใหญ่ ซุ้มโคม", "2569 city program — past years brought parades, the grand krathong contest, lantern arches")]),
        (datetime.date(2026, 11, 23), False, [wait("กำหนดการเมือง ๒๕๖๙", "2569 city program"), canon("คืนก่อนเพ็ญ — จดหมายฉบับสุดท้ายออกวันนี้", "the eve — the season’s last letter lands today")]),
        (ANCHOR, True, [canon("คืนเพ็ญ — ริมน้ำปิง สะพานนวรัฐ · ประตูท่าแพ · ข่วงสามกษัตริย์ เข้าฟรี", "the full moon — the Ping at Nawarat Bridge · Tha Phae Gate · Three Kings, free"),
                        org("CAD Khomloy คืนที่ ๑ · Yee Peng Lanna วันที่ ๑ ราว ๑๒.๐๐–๒๑.๐๐ น.", "CAD Khomloy night one · Yee Peng Lanna day one, about 12:00–21:00"),
                        wait("เวลาพิธีเย็นของวัดพันเตา วัดโลกโมฬี วัดชัยมงคล", "evening times at Wat Phan Tao, Wat Lok Moli, Wat Chai Mongkhon")]),
        (datetime.date(2026, 11, 25), False, [org("CAD Khomloy คืนที่ ๒ · Yee Peng Lanna วันที่ ๒", "CAD Khomloy night two · Yee Peng Lanna day two"), wait("งานเมืองคืนที่สอง", "the city’s second evening")]),
        (datetime.date(2026, 11, 26), False, [wait("วันปิดงาน", "closing day")]),
    ]
    wk_html = "".join(
        f'<tr class="{"full" if full else ""}"><td class="day">{bi(_thai_date(d, g).split(" ")[0] + " " + str(d.day), d.strftime("%a %-d"))}'
        f'{" 🌕" if full else ""}</td><td>{"<br>".join(items)}</td></tr>'
        for d, full, items in week_rows)
    wk_html += (f'<tr><td class="day">{bi("เชียงราย", "Chiang Rai")}</td><td>{wait("เทศบาลนครเชียงราย ริมน้ำกก — ปีก่อน ๆ ตรงคืนเพ็ญ", "the municipal evening on the Kok — past years on the full-moon nights")}</td></tr>')
    week = (f'<h2 id="week">📅 {bi("สัปดาห์ยี่เป็ง วันต่อวัน", "Festival week, day by day")}</h2>'
            f'<p>{bi("ทั้งสัปดาห์วางรอบคืนเพ็ญวันอังคารที่ ๒๔ สิ่งที่ยืนยันแล้วพิมพ์ไว้ สิ่งที่รอประกาศบอกว่ารออะไร — ช่องไหนไม่มีประกาศจนถึงวันงาน ช่องนั้นหายไป ไม่ใช่ถูกเดา", "The week arranges itself around the full moon on Tuesday the 24th. What is confirmed is printed; what waits says what it waits on — a slot with no notice by the day disappears rather than gets guessed.")}</p>'
            f'<table class="yp-week"><tbody>{wk_html}</tbody></table>')

    # ---- the twelve letters ------------------------------------------------
    drip = json.loads(DRIP.read_text()) if DRIP.exists() else {"issues": []}
    issues = drip.get("issues", [])
    landed = [i for i in issues if datetime.date.fromisoformat(i["send"]) <= today and not i["held"]]
    latest = landed[-1]["wk"] if landed else None
    iss_html = []
    for i in issues:
        sd = datetime.date.fromisoformat(i["send"])
        title = f'{esc(i["title_th"])}<small>· {esc(i["title_en"])}</small>'
        when = bi(_thai_date(sd, g), _en_date(sd))
        if sd > today:
            iss_html.append(f'<details class="yp-issue future"><summary>✉️ {title}<small>— {bi("จะออก " + _thai_date(sd, g), "lands " + _en_date(sd))}</small></summary></details>')
        elif i["held"]:
            waits = " · ".join(esc(w) for w in i["waits_on"])
            iss_html.append(f'<details class="yp-issue held"><summary>✉️ {title}<small>— {bi("รอประกาศ", "waiting on")}: {waits}</small></summary></details>')
        else:
            body = _md(i["body_th"], esc)
            en = _md(i["en"], esc)
            iss_html.append(f'<details class="yp-issue"{" open" if i["wk"] == latest else ""}><summary>✉️ {title}<small>— {when}</small></summary>'
                            f'<div class="body">{body}<div class="en">{en}</div></div></details>')
    letters = (f'<h2 id="letters">✉️ {bi("จดหมายรายสัปดาห์ — สิบสองฉบับ", "The weekly letters — twelve")}</h2>'
               f'<p>{bi("ตั้งแต่ ๑ กันยายนถึงคืนก่อนเพ็ญ สัปดาห์ละฉบับ เล่าเรื่องยี่เป็งไปทีละเรื่อง ฉบับที่ถึงวันแล้วอ่านได้ตรงนี้ ฉบับที่รอประกาศบอกไว้ว่ารออะไร", "From 1 September to the eve, one letter a week, one part of the festival at a time. A letter whose day has come reads here; one waiting on a notice says what it waits for.")} '
               f'{bi("อยากได้ทางอีเมล →", "By email →")} <a href="https://wichaa.net/support">{bi("สมัครรับจดหมาย", "join the list")}</a></p>'
               + "".join(iss_html))

    # ---- sources -------------------------------------------------------------
    mss_rows = "".join(f'<tr><td>{esc(a)}</td><td>{esc(b)}<br><small>{esc(c)}</small></td><td>{bi(d, e)}</td></tr>' for a, b, c, d, e in MSS)
    pc_img, pc_cr = _photo(PHOTO["procession"], picks, esc, att, bi_text, "ขบวนแห่โคม คืนยี่เป็ง เชียงใหม่", "A lantern procession on a Yi Peng night, Chiang Mai")
    sources = (f'<h2 id="sources">📜 {bi("ที่มา", "Sources")}</h2>'
               f'<div class="yp-figure">{pc_img}{pc_cr}</div>'
               f'<table class="yp-mss"><thead><tr><th>{bi("เอกสาร", "source")}</th><th>{bi("ชื่อ · ที่เก็บ · ปี", "title · keeping temple · date")}</th><th>{bi("ให้อะไรกับหน้านี้", "what it gave this page")}</th></tr></thead><tbody>{mss_rows}</tbody></table>'
               f'<p class="tinynote">{bi("ใบลานอยู่ในคลังวิชชา (wichaa.net) — ฉบับโบราณจาก DLNTM/CrossAsia อักษรธรรมล้านนา และหนังสือร่วมสมัยที่ได้รับมอบ รอยต่อคือที่มา · คำว่า ผางประทีป และ ยี่เป็ง ยังไม่ปรากฏในตัวบทใบลานที่คลังถืออยู่ (เดือนยี่มาถึงคลังผ่านชื่อเรื่อง ms 5794 เท่านั้น) — บอกไว้ตรง ๆ ไม่แต่งเติม", "The manuscripts live in the wichaa corpus (wichaa.net) — antique palm-leaf from DLNTM/CrossAsia in Tham Lanna script, and contributed modern volumes; the seam is the provenance · the words ผางประทีป and ยี่เป็ง do not yet occur in any manuscript text the corpus holds (the second month reaches it only through ms 5794’s title) — said plainly, not smoothed over")}</p>'
               f'<p class="tinynote">{bi("ทะเบียนประเพณี: ", "Festival register: ")}<a href="festivals/{FEST_ID}.html">festivals/{FEST_ID}.html</a> · '
               f'{bi("วันที่: ปฏิทินจันทรคติที่เผยแพร่แล้ว + ประกาศทางการเมื่อออก", "dates: published lunar calendars + official notices as they land")} (<a href="data/festival_dates.json">festival_dates.json</a>) · '
               f'{bi("ข้อมูลหน้านี้ทั้งหมด", "everything on this page as data")}: <a href="data/yipeng.json">yipeng.json</a> · '
               f'{bi("ภาพ: Wikimedia Commons ตามที่ระบุใต้ภาพ — เครดิตทั้งหมดที่", "pictures: Wikimedia Commons as credited under each — all credits at")} <a href="pictures.html">pictures.html</a></p>'
               f'<p class="myhint">{bi("ฤดูนี้ทำงานอย่างไร: หน้านี้ + จดหมายรายสัปดาห์ร่างโดยชุดบอต Festival Push (ส.ค.–พ.ย. ๒๕๖๙) จากทะเบียน ใบลาน และประกาศจริงเท่านั้น วันที่ที่ยังไม่ประกาศไม่มีทางถูกเดา — ถ้าเห็นช่องว่าง นั่นคือความจริง ณ วันที่สร้างหน้า", "How this season works: the page and the weekly letters are drafted by the Festival Push bots (Aug–Nov 2026) from the register, the manuscripts and real notices only. An unannounced date is never guessed — an empty slot is the truth on the build date.")} '
               f'{bi("สร้าง " + g["BUILD_DATE"], "built " + g["BUILD_DATE"])}</p>')

    # ---- countdown script ------------------------------------------------
    js = r"""<script>(function(){var el=document.querySelector('.yp-count');if(!el)return;
var a=el.getAttribute('data-anchor').split('-');var t=Date.UTC(+a[0],a[1]-1,+a[2])-7*3600e3; /* midnight Asia/Bangkok */
function tick(){var now=Date.now();var d=Math.floor((t-now)/864e5);var n=el.querySelector('.n'),th=el.querySelector('.th');
if(d>0){th.textContent='อีก';n.textContent=d;}else if(now<t+864e5){th.textContent='คืนนี้';n.textContent='';}else{th.textContent='ผ่านไปแล้ว';n.textContent=Math.floor((now-t)/864e5);}}
tick();setInterval(tick,6e4);})();</script>"""

    # ---- JSON-LD ------------------------------------------------------------
    ld = {"@context": "https://schema.org", "@type": "Festival",
          "name": "ยี่เป็ง – ลอยกระทง เชียงใหม่ 2569 · Yi Peng & Loi Krathong, Chiang Mai 2026",
          "startDate": "2026-11-24", "endDate": "2026-11-25", "url": BASE + "yipeng.html",
          "eventStatus": "https://schema.org/EventScheduled",
          "eventAttendanceMode": "https://schema.org/OfflineEventAttendanceMode",
          "isAccessibleForFree": True,
          "location": {"@type": "Place", "name": "Chiang Mai", "address": {"@type": "PostalAddress", "addressLocality": "Chiang Mai", "addressCountry": "TH"}},
          "description": fest["blurb_en"],
          "subEvent": [
              {"@type": "Event", "name": "CAD Khomloy Sky Lantern Festival", "startDate": "2026-11-24", "endDate": "2026-11-25",
               "url": "https://yipenglanternfestival.in.th/", "isAccessibleForFree": False,
               "location": {"@type": "Place", "name": "CAD Cultural Center, Chiang Mai"}},
              {"@type": "Event", "name": "Yee Peng Lanna International 2026", "startDate": "2026-11-24T12:00:00+07:00", "endDate": "2026-11-25T21:00:00+07:00",
               "url": "https://www.eventbrite.com/e/yeepeng-lanna-international-2026-chiang-mai-official-ticket-24-nov-2026-tickets-1978873470821",
               "isAccessibleForFree": False, "location": {"@type": "Place", "name": "Lanna Dhutanka, San Sai, Chiang Mai"}}]}
    head = ('<link rel="stylesheet" href="festivals.css"><link rel="stylesheet" href="yipeng.css">'
            f'<script type="application/ld+json">{json.dumps(ld, ensure_ascii=False)}</script>')
    og = f"site/{PHOTO['hero']}.jpg" if PHOTO["hero"] in picks else None

    body = (hero + f'<nav class="yp-nav" aria-label="sections">{nav}</nav>'
            + night + map_sec + lights + raft + ways + notices + week + letters + sources
            + g["share_block"](BASE + "yipeng.html", "ยี่เป็ง – ลอยกระทง ๒๕๖๙ · Yi Peng & Loi Krathong 2026 — มดแดง", qr=True)
            + js)
    crumbs = (f'<a href="index.html">มดแดง</a> › <a href="festivals.html">{bi("เทศกาล-ฤดูกาล", "Festivals")}</a> › '
              f'{bi("ยี่เป็ง ๒๕๖๙", "Yi Peng 2026")}')
    desc = ("ยี่เป็ง–ลอยกระทง เชียงใหม่ ๒๕๖๙ — คืนเพ็ญ 24 พ.ย. แผนที่ที่ทาง โคมสามดวง กระทง ราคา ประกาศเขตปล่อยโคม และจดหมายรายสัปดาห์ · "
            "Yi Peng & Loi Krathong, Chiang Mai 2026 — the full moon of 24 Nov, the map, the three lights, the krathong, prices, the release-zone notice, and twelve weekly letters.")
    html = page("ยี่เป็ง – ลอยกระทง ๒๕๖๙ · Yi Peng 2026", body, depth=0, crumbs=crumbs,
                path="yipeng.html", desc=desc, extra_head=head, og=og)
    (DOCS / "yipeng.html").write_text(html)

    (DOCS / "data").mkdir(exist_ok=True)
    (DOCS / "data" / "yipeng.json").write_text(json.dumps({
        "festival": FEST_ID, "anchor": ANCHOR.isoformat(), "built": g["BUILD_DATE"],
        "venues": VENUES, "gates": [{**{k: v for k, v in gt.items() if k not in ("hosts", "words", "not")}, "state": gate_state[gt["key"]]} for gt in GATES],
        "announced": ann, "letters": [{k: i[k] for k in ("wk", "send", "title_th", "title_en", "held", "waits_on")} for i in issues],
        "manuscripts": MSS, "photos": {k: picks.get(v, {}).get("page") for k, v in PHOTO.items()},
    }, ensure_ascii=False, indent=1))
    return {"page": "yipeng.html", "pins": len(located), "letters_landed": len(landed),
            "gates_announced": sum(1 for s in gate_state.values() if s == "announced")}


def main():
    import sys
    sys.path.insert(0, str(ROOT))
    import build  # importing does not build
    out = None
    if "--out" in sys.argv:
        out = Path(sys.argv[sys.argv.index("--out") + 1]).resolve()
        out.mkdir(parents=True, exist_ok=True)
    elif not (build.DOCS / "index.html").exists():
        raise SystemExit("docs/ is not built yet — run python3 build.py first, or pass --out DIR")
    data = build.load()
    g = dict(vars(build))
    if out:
        g["DOCS"] = out
    events = build.enrich_events(data, build.PHOTO_FILES)
    import festivals_layer
    g["_ANNOUNCED"] = festivals_layer.announced_dates()
    print(emit(g, events, data))


if __name__ == "__main__":
    main()
