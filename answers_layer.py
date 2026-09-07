#!/usr/bin/env python3
"""คำตอบ — the answer pages: three landing surfaces for the questions this
directory can answer better than anything else.

  festival-dates.html  "ยี่เป็งปีนี้วันไหน" — every festival in the canon with
                       its date for this year and next, each date carrying its
                       voice: announced (harvested, sourced), lunar-published
                       (hand-checked against a published Thai calendar, in
                       data/festival_calendar.json), fixed-rule (computed from
                       the canon's own rule), or a customary window still
                       waiting on an announcement. A rule is not a date; a
                       date always says where it came from.

  open-now.html        "ตอนนี้เปิดอะไรบ้าง / what's open at 5am" — the city's
                       week as a static hour to hour answer, baked from the
                       same data/open_lamps.json the nitnoy map draws from.
                       Presence is the only claim: a place absent here is a
                       place whose hours nobody holds, never a closed one.

  lists/<slug>.html    "รายชื่อวัดเชียงใหม่ทั้งหมด" — the complete-list genre:
                       everything the catalogue holds for one category, count
                       first, alphabetical, every row a link to its place
                       page. The count is a promise: tests fail if the number
                       in the heading drifts from the rows on the page.

As everywhere: Thai canonical with EN as a display layer, nothing
that reports a reader to anybody, provenance stated, silence never dressed up
as "no". These pages carry no map, so they fetch nothing at read time.

Entry point: emit(globals_of_build, data) — call after festivals_layer.emit
(it reads g["_ANNOUNCED"]) and before the sitemap step so every page lands in
sitemap.xml on its own.
"""
import datetime
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parent

WEEK = 7 * 1440
WEEKDAY_TH = ["จันทร์", "อังคาร", "พุธ", "พฤหัสบดี", "ศุกร์", "เสาร์", "อาทิตย์"]
WEEKDAY_EN = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday",
              "Saturday", "Sunday"]
DAY_ABBR_TH = ["จ", "อ", "พ", "พฤ", "ศ", "ส", "อา"]

# Same families the nitnoy map uses, so a reader moving between the two pages
# meets the same words.
GROUP_TH = {"food": "ร้านอาหาร", "cafe": "คาเฟ่", "night": "บาร์-ผับ",
            "market": "ตลาด", "care": "นวด-ความงาม", "shop": "ของจำเป็น-ช้อป",
            "other": "อื่น ๆ"}
GROUP_EN = {"food": "food", "cafe": "cafés", "night": "bars", "market": "markets",
            "care": "massage & beauty", "shop": "essentials & shops",
            "other": "everything else"}

CSS = """
.qagrid{display:grid;gap:.8rem;
  grid-template-columns:repeat(auto-fill,minmax(15rem,1fr));margin:1rem 0}
.qacard{border:1px solid #0002;border-radius:12px;padding:.7rem .8rem;
  background:#fff}
.qacard b{display:block;margin-bottom:.2rem}
.qacard .qadate{font-size:1.05em}
.qacard .qayear{display:inline-block;min-width:3.2ch;color:#00000088}
.voice{display:inline-block;border-radius:999px;padding:0 .5rem;
  font-size:.78em;vertical-align:middle;white-space:nowrap}
.voice.announced{background:#3f7f4f22;color:#2c5e39}
.voice.lunar{background:#b8912e22;color:#7a5c12}
.voice.fixed{background:#3f5aa622;color:#2c4076}
.voice.waiting{background:#00000010;color:#00000099}
table.fdates{border-collapse:collapse;width:100%;margin:1rem 0}
table.fdates th,table.fdates td{border-bottom:1px solid #0002;
  padding:.45rem .5rem;text-align:left;vertical-align:top}
table.fdates th{font-size:.85em}
table.fdates td.fmon{white-space:nowrap;color:#00000099;font-size:.85em}
.hourwrap{overflow-x:auto}
table.hours{border-collapse:collapse;margin:1rem 0;
  font-variant-numeric:tabular-nums}
table.hours th,table.hours td{border:1px solid #0001;padding:.2rem .5rem;
  text-align:right}
table.hours th{background:#00000008}
table.hours td.hh{text-align:left;white-space:nowrap}
table.hours .hnow{background:#b3540f22;outline:2px solid #b3540f}
.opennote{border-left:3px solid #b3540f;padding:.3rem .7rem;
  background:#b3540f0d;border-radius:0 8px 8px 0;margin:1rem 0}
"""


# ------------------------------------------------------------------- dates
def _fmt_th(d):
    return f"{WEEKDAY_TH[d.weekday()]}ที่ {d.day} " \
           f"{MONTH_TH_[d.month]} {d.year + 543}"


def _fmt_en(d):
    return f"{WEEKDAY_EN[d.weekday()]}, {MONTH_EN_[d.month]} {d.day}, {d.year}"


MONTH_TH_ = MONTH_EN_ = None  # filled from build's globals in emit()


def _range_bi(g, a, b):
    da, db = datetime.date.fromisoformat(a), datetime.date.fromisoformat(b)
    th, en = _fmt_th(da), _fmt_en(da)
    if b != a:
        th += f" – {_fmt_th(db)}"
        en += f" – {_fmt_en(db)}"
    return th, en


def fixed_dates_for(f, year):
    """A (start, end) for a fixed-rule festival whose Thai window names real
    days — "13–15 เมษายน" yields Apr 13 + duration. The same parse the ICS
    uses; a window like "สุดสัปดาห์ที่ 3" is not a date and returns None."""
    import re
    months_th = ["มกราคม", "กุมภาพันธ์", "มีนาคม", "เมษายน", "พฤษภาคม",
                 "มิถุนายน", "กรกฎาคม", "สิงหาคม", "กันยายน", "ตุลาคม",
                 "พฤศจิกายน", "ธันวาคม"]
    m = re.search(r"(\d{1,2})(?:\s*[–—-]\s*\d{1,2})?\s+(" + "|".join(months_th)
                  + ")", f.get("window_th", ""))
    if not m:
        return None
    day, mon = int(m.group(1)), months_th.index(m.group(2)) + 1
    days = f.get("duration_days") or 1
    start = datetime.date(year, mon, day)
    return start, start + datetime.timedelta(days=days - 1)


def calendar_rows():
    """data/festival_calendar.json, keyed (festival_id, year). Only rows whose
    source id resolves — a date that cannot say where it came from does not
    reach a page."""
    p = ROOT / "data" / "festival_calendar.json"
    if not p.exists():
        return {}, {}
    doc = json.loads(p.read_text())
    sources = doc.get("sources", {})
    out = {}
    for r in doc.get("rows", []):
        if r.get("source") not in sources:
            continue
        out[(r["festival_id"], r["year"])] = r
    return out, sources


def _cell(g, f, year, cal, sources, ann_rows):
    """One festival-year answer: (html, voice, iso_start_or_None)."""
    bi, att, esc = g["bi"], g["att"], g["esc"]
    # 1 — an official announcement for that year beats everything
    for r in ann_rows:
        if r["date_start"][:4] == str(year):
            th, en = _range_bi(g, r["date_start"], r["date_end"])
            src = (f' <a href="{att(r["source_url"])}" rel="noopener nofollow">'
                   f'{bi("ประกาศ", "announcement")}</a>')
            return (f'{bi(esc(th), esc(en))} '
                    f'<span class="voice announced">📌 {bi("ประกาศแล้ว", "announced")}</span>{src}',
                    "announced", r["date_start"])
    # 2 — a hand-checked published lunar date
    r = cal.get((f["id"], year))
    if r:
        th, en = _range_bi(g, r["date_start"], r["date_end"])
        s = sources[r["source"]]
        badge = ('<span class="voice lunar">🌕 '
                 + bi("ตามปฏิทินจันทรคติ", "published lunar date") + "</span>")
        note = f' <span class="tinynote">{bi(esc(r.get("note_th", "")), esc(r.get("note_en", "")))}</span>' \
            if r.get("note_th") else ""
        src = (f' <a class="tinynote" href="{att(s["url"])}" rel="noopener nofollow">'
               f'{bi("ที่มา", "source")}</a>')
        return (f'{bi(esc(th), esc(en))} {badge}{note}{src}', "lunar",
                r["date_start"])
    # 3 — a fixed rule the canon itself can turn into days
    if f.get("timing_type") == "fixed":
        fx = fixed_dates_for(f, year)
        if fx:
            a, b = fx
            th, en = _range_bi(g, a.isoformat(), b.isoformat())
            return (f'{bi(esc(th), esc(en))} <span class="voice fixed">🗓 '
                    + bi("วันเดิมทุกปี", "same dates every year") + "</span>",
                    "fixed", a.isoformat())
    # 4 — the window, said as a window (canon strings arrive HTML-ready, the
    # same trust festivals_layer extends them — escaping again bakes &amp;)
    return (f'{bi(f["window_th"], f["window_en"])} '
            f'<span class="voice waiting">⏳ '
            + bi("รอประกาศของปีนั้น", "awaiting that year's announcement")
            + "</span>", "waiting", None)


# The questions people actually type, answered in the first screenful. Order
# is search volume, not the calendar: Yi Peng first.
QUICK = ["yi-peng-loi-krathong", "songkran-pi-mai-muang", "makha-bucha",
         "visakha-bucha", "khao-phansa", "ok-phansa", "chinese-new-year",
         "inthakhin"]


def festival_dates_page(g, data):
    bi, esc, att = g["bi"], g["esc"], g["att"]
    fests = g["FESTIVALS"]
    ann_all = g.get("_ANNOUNCED") or {}
    cal, sources = calendar_rows()
    today = datetime.date.fromisoformat(g["BUILD_DATE"])
    years = [today.year, today.year + 1]
    by_id = {f["id"]: f for f in fests}

    # ---- quick answers ----------------------------------------------------
    cards, faq = [], []
    for fid in QUICK:
        f = by_id.get(fid)
        if not f:
            continue
        lines = []
        for y in years:
            html, voice, iso = _cell(g, f, y, cal, sources, ann_all.get(fid) or [])
            lines.append(f'<div><span class="qayear">{y + 543}</span> {html}</div>')
            if iso:
                import html as _html
                d = datetime.date.fromisoformat(iso)
                # canon strings are HTML-ready; JSON-LD wants plain text
                nth, nen = _html.unescape(f["name_th"]), _html.unescape(f["name_en"])
                faq.append({
                    "@type": "Question",
                    "name": f'{nth} {y + 543} ตรงกับวันไหน ({nen} {y} date)',
                    "acceptedAnswer": {"@type": "Answer", "text":
                        f'{nth} ปี {y + 543} ตรงกับ{_fmt_th(d)} — '
                        f'{nen} {y} falls on {_fmt_en(d)}.'}})
        cards.append(
            f'<div class="qacard"><b><a href="festivals/{f["id"]}.html">'
            f'{bi(f["name_th"], f["name_en"])}</a></b>'
            f'<div class="qadate">{"".join(lines)}</div></div>')

    # ---- the full table, in calendar order --------------------------------
    rows = []
    for f in sorted(fests, key=lambda f: (f["month"], f["id"])):
        cells = "".join(
            f"<td>{_cell(g, f, y, cal, sources, ann_all.get(f['id']) or [])[0]}</td>"
            for y in years)
        rows.append(
            f'<tr><td class="fmon">{g["MONTH_TH"][f["month"]]}</td>'
            f'<td><a href="festivals/{f["id"]}.html">'
            f'{bi(f["name_th"], f["name_en"])}</a></td>{cells}</tr>')
    yhead = "".join(f"<th>พ.ศ. {y + 543} · {y}</th>" for y in years)

    n_dated = sum(1 for f in fests for y in years
                  if _cell(g, f, y, cal, sources,
                           ann_all.get(f["id"]) or [])[1] != "waiting")
    intro_th = (f"วันเทศกาลของเชียงใหม่-เชียงราย ปี {years[0] + 543} และ {years[1] + 543} "
                "รวมไว้หน้าเดียว — วันพระใหญ่ตามปฏิทินจันทรคติ ยี่เป็ง-ลอยกระทง สงกรานต์ "
                "และงานประจำปีทั้ง 33 รายการ ทุกวันที่บอกที่มาของตัวเองเสมอ "
                "และงานที่ยังไม่ประกาศ หน้านี้ก็บอกตรง ๆ ว่ายังไม่ประกาศ")
    intro_en = (f"Every Chiang Mai and Chiang Rai festival date for {years[0]} and "
                f"{years[1]} on one page — the lunar holy days, Yi Peng & Loy "
                "Krathong, Songkran, and all 33 entries of the recurring canon. "
                "Every date states where it came from, and a festival that has "
                "not been announced yet says so plainly.")
    legend = (f'<p class="tinynote">'
              f'<span class="voice announced">📌 {bi("ประกาศแล้ว", "announced")}</span> '
              f'{bi("มีประกาศทางการของปีนั้น พร้อมลิงก์", "an official announcement for that year, linked")} · '
              f'<span class="voice lunar">🌕 {bi("ตามปฏิทินจันทรคติ", "published lunar date")}</span> '
              f'{bi("วันตามปฏิทินจันทรคติที่เผยแพร่แล้ว ตรวจกับแหล่งที่ลิงก์ไว้", "a published Thai lunar-calendar date, checked against the linked source")} · '
              f'<span class="voice fixed">🗓 {bi("วันเดิมทุกปี", "fixed")}</span> '
              f'{bi("วันคงที่ตามธรรมเนียม", "the same civil dates every year")} · '
              f'<span class="voice waiting">⏳ {bi("รอประกาศ", "awaiting announcement")}</span> '
              f'{bi("บอกช่วงตามธรรมเนียมไว้ก่อน ยังไม่ใช่วันจริง", "the customary window only — not yet a date")}</p>')
    candor = bi(
        "หมายเหตุความซื่อตรง: หน้านี้ไม่เดาวันจากกฎจันทรคติเอง วันที่ทุกวันมาจากประกาศทางการ "
        "หรือปฏิทินที่เผยแพร่แล้วเท่านั้น (ไฟล์ข้อมูลคือ festival_calendar.json พร้อมที่มาต่อแถว) "
        "งานหมู่บ้าน-งานจังหวัดที่ประกาศเป็นปี ๆ ไป ให้ยึดประกาศของผู้จัดเป็นหลักเสมอ",
        "Where this comes from: this page does not derive a date from the lunar rule "
        "itself. Every date is either an official announcement or a published "
        "calendar, checked by hand (the data file is festival_calendar.json, one "
        "source per row). For the fairs announced year by year, the organiser's "
        "announcement always wins.")

    ld = {"@context": "https://schema.org", "@type": "FAQPage",
          "mainEntity": faq[:10]}
    body = (
        f'<h1>📅 {bi("วันเทศกาลปี " + str(years[0] + 543) + "–" + str(years[1] + 543), "Festival dates " + str(years[0]) + "–" + str(years[1]))}</h1>'
        f'<p>{bi(intro_th, intro_en)}</p>'
        f'<div class="qagrid">{"".join(cards)}</div>'
        f'{legend}'
        f'<h2>{bi("ทั้ง 33 รายการ เรียงตามเดือน", "All 33, month by month")}</h2>'
        f'<div class="hourwrap"><table class="fdates">'
        f'<tr><th>{bi("เดือน", "Month")}</th><th>{bi("งาน", "Festival")}</th>{yhead}</tr>'
        f'{"".join(rows)}</table></div>'
        f'<p class="tinynote">{n_dated}/{len(fests) * 2} '
        f'{bi("ช่องปี-งานข้างบนมีวันจริงแล้ว ที่เหลือรอประกาศ", "festival-year cells above carry real dates; the rest await announcements")} · '
        f'🗓 <a href="festivals.ics">festivals.ics</a> '
        f'{bi("สมัครรับในแอปปฏิทินได้เลย", "subscribe in your calendar app")} · '
        f'<a href="festivals.html">{bi("อ่านเรื่องแต่ละงาน + วงล้อทั้งปี", "each festival in full, plus the year wheel")}</a> · '
        f'<a href="data/festival_calendar.json">festival_calendar.json</a></p>'
        f'<p class="myhint">{candor}</p>'
        + g["share_block"](g["BASE"] + "festival-dates.html",
                           "วันเทศกาลเชียงใหม่-เชียงราย · Festival dates — มดแดง"))
    head = ('<link rel="stylesheet" href="answers.css">'
            '<script type="application/ld+json">'
            + json.dumps(ld, ensure_ascii=False) + "</script>")
    og = ("og/festival-dates.png"
          if (ROOT / "assets" / "og" / "festival-dates.png").exists() else None)
    return g["page"](
        f"วันเทศกาลปี {years[0] + 543}-{years[1] + 543} เชียงใหม่-เชียงราย ยี่เป็ง สงกรานต์ วันพระใหญ่",
        body, depth=0, path="festival-dates.html", og=og,
        desc=f"ยี่เป็ง-ลอยกระทง {years[0] + 543} วันไหน? สงกรานต์ วันพระใหญ่ และเทศกาลทั้ง 33 งาน "
             f"ของเชียงใหม่-เชียงราย ปี {years[0] + 543}-{years[1] + 543} พร้อมที่มาทุกวัน · "
             f"Chiang Mai festival dates {years[0]}-{years[1]}",
        extra_head=head,
        crumbs=f'<a href="index.html">มดแดง</a> › '
               f'<a href="festivals.html">{g["bi"]("เทศกาล-ฤดูกาล", "Festivals")}</a> › '
               + g["bi"]("วันเทศกาล", "Dates"))


# ---------------------------------------------------------------- open now
def _covers_week(sched):
    got = 0
    for a, b in sorted(sched):
        if a > got:
            return False
        got = max(got, b)
    return got >= WEEK


def _open_days_at(sched, minute):
    """How many of the 7 days this place is open at the given minute-of-day."""
    return sum(1 for d in range(7)
               for a, b in sched if a <= d * 1440 + minute < b)


def open_now_page(g, data):
    bi, esc = g["bi"], g["esc"]
    src = ROOT / "data" / "open_lamps.json"
    if not src.exists():
        return None
    lamps = json.loads(src.read_text())
    scheds = lamps["schedules"]
    by_id = {r["id"]: r for p in g["PROVINCES"] for r in data[p["key"]]}

    def rec_li(p):
        r = by_id.get(p["id"])
        if r is None:
            return None
        return g["entry_li"](r, f'{r["province"]}/p/{g["place_slug"](r)}.html')

    def section(title_th, title_en, q_th, q_en, places, cap=60):
        places = sorted(places, key=lambda p: p["n"])
        lis = [x for x in (rec_li(p) for p in places[:cap]) if x]
        more = ""
        if len(places) > cap:
            more = (f'<p class="tinynote">{bi("แสดง %d จากทั้งหมด %d แห่ง — ดูครบทุกดวงบนแผนที่ที่" % (cap, len(places)), "showing %d of %d — every lamp is on the map at" % (cap, len(places)))} '
                    f'<a href="nitnoy.html">เมืองหลับนิดหน่อย</a></p>')
        counts = {}
        for p in places:
            counts[p["g"]] = counts.get(p["g"], 0) + 1
        chips = " · ".join(
            f'{GROUP_TH[k]} {v}' for k, v in
            sorted(counts.items(), key=lambda kv: -kv[1]))
        return (f'<h2>{bi(title_th, title_en)} '
                f'<span class="count">({len(places):,})</span></h2>'
                f'<p>{bi(q_th, q_en)}</p>'
                f'<p class="tinynote">{chips}</p>'
                f'<ul class="dir">{"".join(lis)}</ul>{more}')

    allday, dawn, late = [], [], []
    for p in lamps["places"]:
        s = scheds[p["k"]]
        if _covers_week(s):
            allday.append(p)
        else:
            if _open_days_at(s, 5 * 60 + 30) >= 4:
                dawn.append(p)
            if _open_days_at(s, 0 * 60 + 30) >= 3:
                late.append(p)

    # the hour × day table — the whole week's pulse, baked
    counts = [[0] * 7 for _ in range(24)]
    for k in range(len(lamps["places"])):
        s = scheds[lamps["places"][k]["k"]]
        for h in range(24):
            for d in range(7):
                t = d * 1440 + h * 60 + 30
                if any(a <= t < b for a, b in s):
                    counts[h][d] += 1
    thead = "".join(f"<th>{d}</th>" for d in DAY_ABBR_TH)
    trows = "".join(
        f'<tr data-h="{h}"><td class="hh">{h:02d}:00–{(h + 1) % 24:02d}:00</td>'
        + "".join(f'<td data-d="{d}">{counts[h][d]:,}</td>' for d in range(7))
        + "</tr>" for h in range(24))

    n = len(lamps["places"])
    silence = bi(
        f"กติกาของหน้านี้: เรานับเฉพาะ {n:,} แห่งที่มดแดงถือเวลาเปิด-ปิดอยู่จริง "
        "ร้านที่ไม่อยู่ในหน้านี้คือร้านที่ยังไม่มีใครเก็บเวลาให้ ไม่ใช่ร้านที่ปิด — "
        "ความเงียบไม่ใช่คำว่าไม่",
        f"The rule of this page: it counts only the {n:,} places whose opening "
        "hours the catalogue actually holds. A place missing from this page is a "
        "place whose hours nobody has recorded — never a closed one. Silence is "
        "not a no.")

    js = """
(function(){
var p=new Intl.DateTimeFormat('en-GB',{timeZone:'Asia/Bangkok',
  hour:'2-digit',weekday:'short',hour12:false}).formatToParts(new Date()),o={};
p.forEach(function(t){o[t.type]=t.value;});
var d={Mon:0,Tue:1,Wed:2,Thu:3,Fri:4,Sat:5,Sun:6}[o.weekday],h=(+o.hour)%24;
var row=document.querySelector('tr[data-h="'+h+'"]');
if(!row)return;
var cell=row.querySelector('td[data-d="'+d+'"]');
if(cell)cell.classList.add('hnow');
var el=document.getElementById('now-figure');
if(el&&cell)el.textContent=cell.textContent;
var lbl=document.getElementById('now-label');
if(lbl)lbl.textContent=['จันทร์','อังคาร','พุธ','พฤหัสบดี','ศุกร์','เสาร์','อาทิตย์'][d]
  +' '+('0'+h).slice(-2)+':00 น.';
})();"""

    body = (
        f'<h1>🕰 {bi("ตอนนี้ที่เชียงใหม่เปิดอะไรบ้าง", "What is open in Chiang Mai right now?")}</h1>'
        f'<p>{bi("คำตอบแบบทั้งเมือง ไม่ใช่ทีละร้าน — ร้านไหนตื่นก่อนฟ้าสาง ร้านไหนอยู่ถึงหลังเที่ยงคืน และตารางทั้งสัปดาห์ว่าแต่ละชั่วโมงเมืองนี้มีอะไรเปิดกี่แห่ง อบจากเวลาเปิด-ปิดจริงในสารบัญ", "The whole-city answer, not one shop at a time: who wakes before dawn, who stays past midnight, and an hour-by-hour table of how much of the city is open, baked from the real opening hours in the catalogue.")}</p>'
        f'<div class="opennote"><b><span id="now-figure">—</span></b> '
        f'{bi("แห่งเปิดอยู่ในชั่วโมงนี้", "places open this hour")} '
        f'<span class="tinynote" id="now-label"></span> · '
        f'<a href="nitnoy.html">{bi("ดูเป็นแผนที่โคมไฟขยับได้", "watch it as the animated lamp map")}</a></div>'
        f'<p class="tinynote">{silence}</p>'
        + section("เปิดตลอด 24 ชั่วโมง", "Open 24 hours",
                  "หิวตอนตีสาม หายาตอนตีสี่ — รายชื่อที่ไม่ปิดเลยทั้งสัปดาห์",
                  "Hungry at 3am, need a pharmacy at 4 — the places that never close at all.",
                  allday)
        + section("เช้ามืด ก่อน 6 โมง", "Before six in the morning",
                  "กาดเช้าติดไฟก่อนฟ้าสาง คาเฟ่รุ่นตื่นเช้า — เปิดตั้งแต่ 05:30 อย่างน้อย 4 วันต่อสัปดาห์",
                  "The morning kads catch light before dawn, plus the early-bird cafés — open by 05:30 at least four days a week.",
                  dawn)
        + section("หลังเที่ยงคืน", "After midnight",
                  "ยังเปิดอยู่ตอน 00:30 อย่างน้อย 3 คืนต่อสัปดาห์",
                  "Still going at 00:30 at least three nights a week.",
                  late)
        + f'<h2>{bi("ทั้งสัปดาห์ ชั่วโมงต่อชั่วโมง", "The whole week, hour by hour")}</h2>'
        f'<p>{bi("แต่ละช่องคือจำนวนที่เปิดในชั่วโมงนั้นของวันนั้น ช่องที่ไฮไลต์คือตอนนี้", "Each cell is how many places are open in that hour of that day; the highlighted cell is now.")}</p>'
        f'<div class="hourwrap"><table class="hours">'
        f'<tr><th>{bi("เวลา", "Hour")}</th>{thead}</tr>{trows}</table></div>'
        f'<p class="tinynote">{bi("ข้อมูลเดียวกับหน้า", "Same data as")} '
        f'<a href="nitnoy.html">เมืองหลับนิดหน่อย</a> · '
        f'<a href="toilets.html">{bi("ห้องน้ำใกล้ฉัน", "toilets near you")}</a> · '
        f'<a href="plan.html">{bi("วางแผนเดินทาง", "plan a route")}</a> · '
        f'<a href="data/open_lamps.json">open_lamps.json</a> '
        f'({bi("ปรับปรุง", "updated")} {esc(lamps.get("generated", ""))})</p>'
        + g["share_block"](g["BASE"] + "open-now.html",
                           "ตอนนี้ที่เชียงใหม่เปิดอะไรบ้าง · What's open in Chiang Mai — มดแดง")
        + f"<script>{js}</script>")
    og = ("og/open-now.png"
          if (ROOT / "assets" / "og" / "open-now.png").exists() else None)
    return g["page"](
        "ตอนนี้เปิดอะไร เชียงใหม่ — เช้ามืด หลังเที่ยงคืน เปิด 24 ชม.",
        body, depth=0, path="open-now.html", og=og,
        desc=f"ตีห้าเชียงใหม่มีอะไรเปิด? หลังเที่ยงคืนกินอะไรได้? ร้าน 24 ชั่วโมงอยู่ไหน? "
             f"คำตอบจากเวลาเปิด-ปิดจริง {n:,} แห่ง · What's open in Chiang Mai at 5am, "
             "after midnight, or 24 hours — from real opening hours.",
        extra_head='<link rel="stylesheet" href="answers.css">',
        crumbs='<a href="index.html">มดแดง</a> › '
               + g["bi"]("ตอนนี้เปิดอะไร", "Open now"))


# -------------------------------------------------------------------- lists
# One row per list page. Adding a list = adding a row; the page, the hub link
# and the tests all follow the row.
LISTS = [
    {"slug": "wat-chiang-mai", "prov": "cm", "cat": "wat",
     "th": "วัดในเชียงใหม่", "en": "wats in Chiang Mai",
     "noun_th": "วัด", "noun_en": "wat"},
    {"slug": "wat-chiang-rai", "prov": "cr", "cat": "wat",
     "th": "วัดในเชียงราย", "en": "wats in Chiang Rai",
     "noun_th": "วัด", "noun_en": "wat"},
    {"slug": "massage-chiang-mai", "prov": "cm", "cat": "massage",
     "th": "ร้านนวด-สปาในเชียงใหม่", "en": "massage & spa in Chiang Mai",
     "noun_th": "ร้าน", "noun_en": "shop"},
    {"slug": "tattoo-chiang-mai", "prov": "cm", "cat": "tattoo",
     "th": "ร้านสักในเชียงใหม่", "en": "tattoo studios in Chiang Mai",
     "noun_th": "ร้าน", "noun_en": "studio"},
]


def _thai_sort_key(g, r):
    """ก→ฮ, with the leading-vowel rule: เชียงใหม่ files under ช, not เ."""
    n = g["name_text"](r)
    if n and n[0] in "เแโใไ" and len(n) > 1:
        return n[1] + n
    return n


def list_page(g, data, L):
    bi, esc = g["bi"], g["esc"]
    recs = [r for r in data[L["prov"]] if L["cat"] in (r.get("cat") or [])]
    recs.sort(key=lambda r: _thai_sort_key(g, r))
    n = len(recs)
    lis = "".join(g["entry_li"](r, f'../{L["prov"]}/p/{g["place_slug"](r)}.html')
                  for r in recs)
    prov_th = {"cm": "เชียงใหม่", "cr": "เชียงราย"}[L["prov"]]
    answer_th = (f'{L["th"]}เท่าที่มดแดงถือข้อมูลอยู่ตอนนี้มี {n:,} แห่ง — '
                 f"รายชื่อครบทุกแห่งอยู่ข้างล่างนี้ เรียง ก→ฮ กดชื่อไหนก็เข้าไปดูหน้าของที่นั่นได้ "
                 f"(ที่อยู่ เบอร์ พิกัด เท่าที่เรามี)")
    answer_en = (f"The catalogue currently holds {n:,} {L['en']} — the complete "
                 "list is below, ก→ฮ, and every name links to that place's own "
                 "page with whatever address, phone and pin we hold.")
    candor = bi(
        f"ตัวเลข {n:,} คือ “เท่าที่เราถือข้อมูล” ไม่ใช่คำประกาศว่าทั้งจังหวัดมีเท่านี้ — "
        f"ถ้า{L['noun_th']}ไหนหายไป ช่วยบอกมดที่หน้าเพิ่มข้อมูลได้เลย เพิ่มแล้วรายชื่อนี้จะครบขึ้นทุกรอบ",
        f"That {n:,} means “what we hold”, not a claim that the province stops "
        f"there — if a {L['noun_en']} is missing, tell the ants on the add-a-place "
        "page and this list gets more complete every rebuild.")
    ld = {"@context": "https://schema.org", "@type": "ItemList",
          "name": f'{L["th"]} — {L["en"]}', "numberOfItems": n,
          "itemListElement": [
              {"@type": "ListItem", "position": i + 1,
               "url": g["BASE"] + f'{L["prov"]}/p/{g["place_slug"](r)}.html',
               "name": g["name_text"](r)} for i, r in enumerate(recs)]}
    body = (
        f'<h1>📜 {bi("รายชื่อ" + L["th"], "Every one of the " + L["en"])} '
        f'<span class="count">({n:,})</span></h1>'
        f'<p>{bi(answer_th, answer_en)}</p>'
        f'<p class="tinynote">{candor} · '
        f'<a href="../add.html">{bi("เพิ่มข้อมูล", "add a place")}</a></p>'
        + g["toolbar"](recs) + g["facet_chips"](recs)
        + f'<ul class="dir" data-sortable>{lis}</ul>'
        f'<p class="tinynote">{bi("อยากกรอง-เรียง-ดูตามหมวดย่อย เปิดที่ชั้นหมวดได้", "For subcategory shelves and filters, use the category page")}: '
        f'<a href="../{L["prov"]}/{L["cat"]}/index.html">{esc(prov_th)}</a> · '
        f'{bi("ที่มา: OpenStreetMap + การเดินเก็บและการแจ้งของผู้อ่าน · ปรับปรุง", "From OpenStreetMap plus field and reader submissions · updated")} '
        f'{g["BUILD_DATE"]}</p>'
        + g["share_block"](g["BASE"] + f'lists/{L["slug"]}.html',
                           f'รายชื่อ{L["th"]} ({n} แห่ง) — มดแดง'))
    head = ('<link rel="stylesheet" href="../answers.css">'
            '<script type="application/ld+json">'
            + json.dumps(ld, ensure_ascii=False) + "</script>")
    og = (f'og/list-{L["slug"]}.png'
          if (ROOT / "assets" / "og" / f'list-{L["slug"]}.png').exists() else None)
    return g["page"](
        f'รายชื่อ{L["th"]}ทั้งหมด {n} แห่ง (พ.ศ. {int(g["BUILD_DATE"][:4]) + 543})',
        body, depth=1, path=f'lists/{L["slug"]}.html', og=og,
        desc=f'รายชื่อ{L["th"]}ครบทั้ง {n} แห่ง เรียง ก→ฮ พร้อมลิงก์ไปหน้าแต่ละแห่ง · '
             f'All {n} {L["en"]} — the complete list, every name a link.',
        extra_head=head,
        crumbs=f'<a href="../index.html">มดแดง</a> › '
               + g["bi"]("รายชื่อครบ", "Complete lists") + " › " + esc(L["th"]))


def lists_hub(g, data):
    bi, esc = g["bi"], g["esc"]
    rows = []
    for L in LISTS:
        n = sum(1 for r in data[L["prov"]] if L["cat"] in (r.get("cat") or []))
        rows.append(f'<li><a href="{L["slug"]}.html">{bi("รายชื่อ" + L["th"], L["en"].capitalize())}</a> '
                    f'<span class="count">({n:,})</span></li>')
    body = (
        f'<h1>📜 {bi("รายชื่อครบทั้งหมวด", "The complete lists")}</h1>'
        f'<p>{bi("บางคำถามไม่ได้อยากได้ “10 อันดับ” แต่อยากได้ทั้งหมด — หมวดไหนสำคัญพอ มดแดงทำเป็นรายชื่อครบหน้าเดียว นับจำนวนตรงหัวเรื่อง เรียง ก→ฮ ทุกชื่อกดเข้าไปดูหน้าของที่นั่นได้", "Some questions do not want a top ten — they want everything. These pages are the complete list for one category on one page: the count in the heading, ก→ฮ, every name a link to that place page.")}</p>'
        f'<ul class="dir">{"".join(rows)}</ul>'
        f'<p class="tinynote">{bi("อยากได้หมวดไหนเพิ่ม บอกมดได้ที่", "Want another category listed? Tell the ants at")} '
        f'<a href="../crawl-request.html">{bi("ส่งมดไปสำรวจ", "request a crawl")}</a></p>'
        + g["share_block"](g["BASE"] + "lists/index.html",
                           "รายชื่อครบทั้งหมวด — มดแดง"))
    og = ("og/lists.png"
          if (ROOT / "assets" / "og" / "lists.png").exists() else None)
    return g["page"]("รายชื่อครบทั้งหมวด", body, depth=1, path="lists/index.html",
                     og=og,
                     desc="รายชื่อครบทั้งหมวดของมดแดง — วัด นวด สัก ครบทุกแห่งที่เราถือข้อมูล หน้าเดียวจบ",
                     extra_head='<link rel="stylesheet" href="../answers.css">',
                     crumbs='<a href="../index.html">มดแดง</a> › '
                            + g["bi"]("รายชื่อครบ", "Complete lists"))


# ------------------------------------------------------------------- driver
def emit(g, data):
    global MONTH_TH_, MONTH_EN_
    MONTH_TH_, MONTH_EN_ = g["MONTH_TH"], g["MONTH_EN"]
    DOCS = g["DOCS"]
    (DOCS / "answers.css").write_text(CSS)

    out = {}
    (DOCS / "festival-dates.html").write_text(festival_dates_page(g, data))
    out["festival-dates"] = 1

    on = open_now_page(g, data)
    if on is None:
        out["open-now"] = "SKIPPED — no data/open_lamps.json"
    else:
        (DOCS / "open-now.html").write_text(on)
        out["open-now"] = 1

    ldir = DOCS / "lists"
    ldir.mkdir(exist_ok=True)
    for L in LISTS:
        (ldir / f'{L["slug"]}.html').write_text(list_page(g, data, L))
    (ldir / "index.html").write_text(lists_hub(g, data))
    out["lists"] = len(LISTS)
    return out
