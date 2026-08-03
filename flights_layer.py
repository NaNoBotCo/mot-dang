#!/usr/bin/env python3
"""Who flies here — the route board for CNX and CEI.

Not a flight tracker. The airports already have arrival boards for the next
hour; nobody keeps a plain answer to the season-sized question: which routes
come to our two airports at all, on which airlines, how often. That answer
changes a few times a year, which is exactly the cadence this site rebuilds
at, so it bakes flat like everything else — no external requests from the
published page.

Two kinds of number, one voice each:

  route    — a scheduled nonstop, from the season's published timetable.
             Carried in data/flights.json with per-route monthly arrival
             counts, an as_of date, and the source pages, hand-refreshed.
  season   — a window, not a promise of today: "ส.ค.–ต.ค." rows fly only in
             those months and say so on the row. An upcoming route renders
             with its start month and never a frequency it does not have yet.

Counts are ARRIVALS for the source month; every route here flies both ways.
That sentence is printed on the page rather than left for the reader to
wonder about.

The fare links are referral links (Travelpayouts marker in flights.json),
declared on the page in both languages. They are ordinary <a> tags: the page
makes no requests on the reader's behalf. flights.js only freshens the date
baked into each link so a reader a month after the build still lands on a
bookable date.

Emits: flights.html (the board), flights.css, flights.js, and
widgets/flights.html — a chromeless mini-board sized for the my.html iframe
gallery, noindexed so the sitemap only carries the real page.

Entry point: emit(globals_of_build, data).
"""
import datetime
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parent
MODEL = json.loads((ROOT / "data" / "flights.json").read_text())

AIRPORTS = MODEL["airports"]
AIRLINES = MODEL["airlines"]
ROUTES = MODEL["routes"]
AS_OF = MODEL["as_of"]
AFF = MODEL["affiliate"]

TH_MONTHS = ["", "ม.ค.", "ก.พ.", "มี.ค.", "เม.ย.", "พ.ค.", "มิ.ย.",
             "ก.ค.", "ส.ค.", "ก.ย.", "ต.ค.", "พ.ย.", "ธ.ค."]


# ----------------------------------------------------------------- wording

def freq_label(bi, per_month):
    """Monthly arrivals → a sentence a reader can hold. Rounded and marked ~
    on the page; the exact count lives in the data file, not in the copy."""
    if per_month >= 45:                       # clearly several a day
        n = round(per_month / 30)
        return bi(f"วันละ ~{n} เที่ยว", f"~{n}/day")
    if per_month >= 26:                       # about daily
        return bi("ราววันละเที่ยว", "~daily")
    n = max(1, round(per_month / 4.35))
    return bi(f"สัปดาห์ละ ~{n} เที่ยว", f"~{n}/wk")


def fare_href(origin, dest, depart):
    """Aviasales deep link, one adult, origin = our airport (the reader who
    books from this page mostly lives here). flights.js re-dates it later."""
    return (f'{AFF["host"]}/search/{origin}{depart:%d%m}{dest}1'
            f'?marker={AFF["marker"]}')


# ------------------------------------------------------------------- board

def route_card(g, r, build_day):
    bi, esc, att = g["bi"], g["esc"], g["att"]
    season = r.get("season")
    upcoming = bool(season and season.get("upcoming"))
    months = (season or {}).get("months", [])
    in_season = (not season) or (build_day.month in months and not upcoming)

    chips = []
    # A route out of its season this month has a zero count, and a zero count
    # is not a frequency — the window chip alone carries those rows.
    if not upcoming and r["per_month"] > 0:
        chips.append(f'<span class="fchip">{freq_label(bi, r["per_month"])}</span>')
    if season:
        cls = "schip on" if in_season and not upcoming else "schip"
        word = season["th"], season["en"]
        chips.append(f'<span class="{cls}" data-months="{att(",".join(map(str, months)))}"'
                     f'{" data-upcoming" if upcoming else ""}>'
                     f'🗓 {bi(word[0], word[1])}</span>')

    lines = "".join(
        f'<span class="al">{bi(AIRLINES[c]["th"], AIRLINES[c]["en"])}</span>'
        for c in r["airlines"])

    depart = build_day + datetime.timedelta(days=21)
    fare = (f'<a class="fare" href="{att(fare_href(r["airport"], r["iata"], depart))}"'
            f' data-org="{att(r["airport"])}" data-dst="{att(r["iata"])}"'
            f' rel="nofollow sponsored noopener" target="_blank">'
            f'{bi("เช็คราคา", "Check fares")} ✈</a>')

    return (f'<div class="route{"" if in_season else " off"}">'
            f'<div class="rhead"><span class="dest">{bi(r["th"], r["en"])}</span>'
            f'<span class="iata">{esc(r["iata"])}</span></div>'
            f'<div class="rmeta">{"".join(chips)}</div>'
            f'<div class="rlines">{lines}</div>'
            f'{fare}</div>')


def airport_section(g, code, build_day):
    bi = g["bi"]
    ap = AIRPORTS[code]
    routes = sorted((r for r in ROUTES if r["airport"] == code),
                    key=lambda r: -r["per_month"])
    dom = [r for r in routes if r["dom"]]
    intl = [r for r in routes if not r["dom"]]
    per_day = round(sum(r["per_month"] for r in routes) / 30)
    n_airlines = len({c for r in routes for c in r["airlines"]})

    def group(title_th, title_en, rs):
        if not rs:
            return ""
        cards = "".join(route_card(g, r, build_day) for r in rs)
        return (f'<h3 class="gtitle">{bi(title_th, title_en)} '
                f'<span class="gcount">({len(rs)})</span></h3>'
                f'<div class="routegrid">{cards}</div>')

    return (f'<section class="apsection" id="{code.lower()}">'
            f'<div class="aphead"><h2>{bi(ap["th"], ap["en"])} '
            f'<span class="apcode">{code}</span></h2>'
            f'<p class="apsum">{bi(f"{len(routes)} จุดหมาย · {n_airlines} สายการบิน · ขาเข้าราววันละ {per_day} เที่ยว", f"{len(routes)} destinations · {n_airlines} airlines · ~{per_day} arrivals a day")}</p></div>'
            + group("ในประเทศ", "Domestic", dom)
            + group("ต่างประเทศ", "International", intl)
            + '</section>')


def build_board(g):
    bi, esc, att = g["bi"], g["esc"], g["att"]
    page, share_block, BASE = g["page"], g["share_block"], g["BASE"]
    build_day = datetime.date.fromisoformat(g["BUILD_DATE"])
    as_of = datetime.date.fromisoformat(AS_OF)
    as_of_th = f"{TH_MONTHS[as_of.month]} {as_of.year + 543}"

    lede_th = ("สายการบินไหนบินเข้า–ออกสนามบินบ้านเรา บ่อยแค่ไหน — "
               "เชียงใหม่และเชียงราย หน้าเดียวจบ ตามตารางฤดูกาล")
    lede_en = ("Every scheduled nonstop in and out of Chiang Mai and Chiang "
               "Rai — which airlines, how often — one page, kept to the "
               "season's timetable.")

    src_links = " · ".join(
        f'<a href="{att(s["url"])}" rel="noopener">{esc(s["name"])}</a>'
        for s in MODEL["sources"])
    foot = (
        '<div class="flightsfoot">'
        f'<p>{bi(f"ตารางเส้นทาง ณ {as_of_th} — จำนวนเที่ยวนับเฉพาะขาเข้า ทุกเส้นทางบินไป-กลับ ตารางฤดูกาลปรับได้ราวปีละสองครั้ง", "Route table as of the season published " + AS_OF + ". Counts are arrivals; every route flies both ways. Airlines re-cut timetables about twice a year.")}'
        f' <span class="src">{src_links}</span></p>'
        f'<p class="affnote">{bi("ปุ่มเช็คราคาเป็นลิงก์แนะนำ (affiliate) — ราคาที่เห็นเท่าเดิมทุกบาท ส่วนแบ่งเล็กน้อยช่วยดูแลมดแดง", "Fare buttons are referral links — the price you see is unchanged; a small share helps keep Mot Dang running.")}</p>'
        '</div>')

    body = (
        f'<h1>✈️ {bi("กระดานเที่ยวบิน เชียงใหม่ · เชียงราย", "Flights board — CNX & CEI")}</h1>'
        f'<p class="lede">{bi(lede_th, lede_en)}</p>'
        f'<nav class="apjump"><a href="#cnx">เชียงใหม่ CNX</a>'
        f'<a href="#cei">เชียงราย CEI</a></nav>'
        + airport_section(g, "CNX", build_day)
        + airport_section(g, "CEI", build_day)
        + foot
        + share_block(BASE + "flights.html",
                      "กระดานเที่ยวบินเชียงใหม่·เชียงราย · Mot Dang"))

    return page("กระดานเที่ยวบิน", body, depth=0, path="flights.html",
                desc=lede_th,
                extra_head='<link rel="stylesheet" href="flights.css">'
                           '<script src="flights.js" defer></script>')


# ------------------------------------------------------------- mini widget

def build_widget(g):
    """The iframe-sized board for the my.html gallery: standalone, inline
    styles, noindex. Numbers only — the full page holds the words."""
    bi_text, esc, att = g["bi_text"], g["esc"], g["att"]
    BASE = g["BASE"]
    rows = []
    for code in ("CNX", "CEI"):
        routes = sorted((r for r in ROUTES if r["airport"] == code),
                        key=lambda r: -r["per_month"])
        per_day = round(sum(r["per_month"] for r in routes) / 30)
        top = " · ".join(esc(r["th"]) for r in routes[:3])
        rows.append(
            f'<div class="ap"><div class="c"><b>{code}</b>'
            f'<span>{esc(AIRPORTS[code]["th"])}</span></div>'
            f'<div class="n">{len(routes)} จุดหมาย · ~{per_day} เที่ยว/วัน</div>'
            f'<div class="t">{top}</div></div>')
    title = bi_text("กระดานเที่ยวบิน เชียงใหม่·เชียงราย", "Flights board CNX & CEI")
    return f"""<!DOCTYPE html>
<html lang="th"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<meta name="robots" content="noindex,follow">
<title>{esc(title)}</title>
<style>
body{{margin:0;font-family:system-ui,-apple-system,'Noto Sans Thai',sans-serif;
background:#faf5ea;color:#2a1e16;padding:.6rem .7rem;font-size:.86rem}}
.ap{{background:#fffdf7;border:2px solid #2a1e16;border-radius:.6rem;
padding:.45rem .6rem;margin:0 0 .5rem;box-shadow:2px 2px 0 #e8dcc3}}
.c{{display:flex;gap:.45rem;align-items:baseline}}
.c b{{font-size:1.05rem;color:#8f2a21}} .c span{{opacity:.85}}
.n{{font-weight:600;margin:.1rem 0}} .t{{opacity:.75;font-size:.8rem}}
a{{display:inline-block;color:#8f2a21;font-weight:700;text-decoration:none;
border:2px solid #8f2a21;border-radius:2rem;padding:.2rem .8rem;
transition:transform .12s ease,background .12s ease}}
a:hover{{background:#8f2a21;color:#faf5ea;transform:translateY(-1px)}}
a:active{{transform:scale(.96)}}
</style></head><body>
<div style="font-weight:700;margin:0 0 .45rem">✈️ {esc("เที่ยวบินบ้านเรา")}</div>
{"".join(rows)}
<a href="{att(BASE)}flights.html" target="_blank" rel="noopener">เปิดกระดานเต็ม →</a>
</body></html>
"""


# --------------------------------------------------------------------- css

CSS = """/* flights.css — generated by flights_layer.py */
.lede{max-width:44rem}
.apjump{display:flex;gap:.6rem;margin:.8rem 0 1.4rem}
.apjump a{border:2px solid var(--ink);border-radius:2rem;padding:.35rem 1rem;
text-decoration:none;color:var(--ink);font-weight:600;background:var(--card);
transition:transform .15s ease,background .15s ease,color .15s ease}
.apjump a:hover{background:var(--ink);color:var(--paper);transform:translateY(-2px)}
.apsection{margin:0 0 2.2rem}
.aphead h2{margin:0 0 .15rem}
.apcode{font-size:.75em;background:var(--ant-dark);color:var(--paper);
border-radius:.4rem;padding:.08em .45em;vertical-align:.12em;letter-spacing:.05em}
.apsum{margin:.1rem 0 .9rem;color:var(--ink-soft)}
.gtitle{margin:1.1rem 0 .55rem}
.gcount{color:var(--gloss);font-weight:400}
.routegrid{display:grid;grid-template-columns:repeat(auto-fill,minmax(15.5rem,1fr));
gap:.7rem}
.route{position:relative;display:flex;flex-direction:column;gap:.35rem;
background:var(--card);border:2px solid var(--ink);border-radius:.7rem;
padding:.6rem .7rem .65rem;box-shadow:3px 3px 0 var(--card-alt);
transition:transform .15s ease,box-shadow .15s ease}
.route:hover{transform:translateY(-3px);box-shadow:5px 6px 0 var(--card-alt)}
.route.off{background:var(--card-alt);opacity:.85}
.rhead{display:flex;align-items:baseline;gap:.5rem;justify-content:space-between}
.dest{font-weight:700;line-height:1.25}
.iata{flex:0 0 auto;font-size:.72rem;font-weight:700;letter-spacing:.06em;
border:1.5px solid var(--ink);border-radius:.35rem;padding:.05em .35em;
color:var(--ink-soft)}
.rmeta{display:flex;flex-wrap:wrap;gap:.35rem}
.fchip,.schip{font-size:.78rem;border-radius:2rem;padding:.12em .6em;
background:var(--card-alt);border:1.5px solid var(--gloss);color:var(--ink)}
.schip{border-style:dashed}
.schip.on{border-style:solid;border-color:var(--ant-dark);background:#fff}
.rlines{display:flex;flex-wrap:wrap;gap:.25rem .6rem;font-size:.82rem;
color:var(--ink-soft)}
.al{white-space:nowrap}
.fare{align-self:flex-start;margin-top:.15rem;font-size:.85rem;font-weight:700;
color:var(--ant-dark);text-decoration:none;border:2px solid var(--ant-dark);
border-radius:2rem;padding:.22rem .85rem;background:#fff;
transition:transform .12s ease,background .12s ease,color .12s ease}
.fare:hover{background:var(--ant-dark);color:var(--paper);transform:translateY(-1px)}
.fare:active{transform:scale(.95)}
.flightsfoot{margin:1.6rem 0 1rem;font-size:.85rem;color:var(--ink-soft);
max-width:46rem}
.flightsfoot .src a{color:var(--ink-soft)}
.affnote{border-left:3px solid var(--gold,#c9a227);padding-left:.6rem}
"""

# ---------------------------------------------------------------------- js

JS = """// flights.js — generated by flights_layer.py
// The page is baked; this only keeps two things fresh between builds:
// fare links get a bookable date ~3 weeks from the reader's today, and
// seasonal chips light up when the reader's month is inside the window.
(function(){
var d=new Date();d.setDate(d.getDate()+21);
var mm=String(d.getMonth()+1).padStart(2,'0'),dd=String(d.getDate()).padStart(2,'0');
document.querySelectorAll('a.fare[data-org]').forEach(function(a){
  var u=new URL(a.href);
  u.pathname='/search/'+a.dataset.org+dd+mm+a.dataset.dst+'1';
  a.href=u.toString();});
var month=new Date().getMonth()+1;
document.querySelectorAll('.schip[data-months]').forEach(function(ch){
  if(ch.hasAttribute('data-upcoming'))return;
  var on=ch.dataset.months.split(',').indexOf(String(month))>=0;
  ch.classList.toggle('on',on);
  var card=ch.closest('.route');if(card)card.classList.toggle('off',!on);});
})();
"""


# -------------------------------------------------------------------- emit

def emit(g, data):
    docs = g["DOCS"]
    (docs / "flights.css").write_text(CSS)
    (docs / "flights.js").write_text(JS)
    (docs / "flights.html").write_text(build_board(g))
    (docs / "widgets").mkdir(exist_ok=True)
    (docs / "widgets" / "flights.html").write_text(build_widget(g))
    n = {"CNX": 0, "CEI": 0}
    for r in ROUTES:
        n[r["airport"]] += 1
    return (f'{n["CNX"]} CNX + {n["CEI"]} CEI routes, '
            f'{len(AIRLINES)} airlines, as of {AS_OF}')


if __name__ == "__main__":
    print("This layer runs from build.py — it needs its helpers. "
          "Run: python3 build.py")
