#!/usr/bin/env python3
"""home_layer.py — the front page of motdang.net, built from zero.

Nan, 2026-09-19: remove all body content and build from scratch — big
parallax pictures, what is close by and happening now or soon (geofencing,
counters, clocks, calendars), the minisites, some of the divination back,
uncluttered, few words, a very multilingual audience, no search box until
search is ready. Humans wander; deepen the wander.

Six scenes, one scroll, a picture behind each that moves slower than the
words. Every number is computed at build time or by the reader's clock; the
words on the page are the nine the redesign kept plus the names of things.

    python3 home_layer.py            # writes docs/index.html

build.py calls render() for index.html so the daily walk ships the same page.
Pictures: docs/site/hero/ (Nan's own frames, importers/make_hero.py) and the
Commons picks in docs/site/ with their credits. Nothing here fetches at load
except the pictures and, on a tap, nine cells of data/here/.
"""
import datetime
import html
import json
import math
import pathlib
import zoneinfo

ROOT = pathlib.Path(__file__).resolve().parent
DATA = ROOT / "data"
DOCS = ROOT / "docs"
TZ = zoneinfo.ZoneInfo("Asia/Bangkok")
BASE = "https://motdang.net/"

CITIES = (("cm", "เชียงใหม่", "Chiang Mai", 18.7883, 98.9853),
          ("cr", "เชียงราย", "Chiang Rai", 19.9094, 99.8325))

# WHICH PICTURE STANDS FOR WHICH SHELF.
#
# A tile is a promise: this is what is behind the word. The first pass of this
# table filled all twenty-eight rows because all twenty-eight could be filled,
# and the result was a mossy demon mask over Beauty & Hair, a temple guardian
# over Pets and a hillside of flowers over Elephants — every one of them an
# association that holds at one remove and collapses on contact. Nan kept a
# copy: archive.org/details/motdang-shelves-2026-09-19.
#
# So the rule now is the plain one. A shelf gets a photograph that shows the
# thing itself, or it gets no photograph. Nine of them get none, and a shelf
# with none draws as a plain panel carrying its name and its count. That is
# not a gap to be filled later with whatever is nearest; it is the answer
# until a picture of the thing exists.
#
# A value is a hero slug (Nan's own frame), ("site", slug) for one of the
# hand-picked Commons photographs in image_picks.json, or None.
SHELF_PIC = {
    "wat": "golden-chedi-flags",                  # her own: chedi, flags, wat ground
    "food": "khao-soi-plate",                     # her own: a plate of khao soi
    "massage": ("site", "classical-thai-massage-at-tara-angkor-hotel-5918685202"),
    "medical": None,                              # no photograph of a clinic
    "cannabis": None,
    "essentials": ("site", "religious-goods-at-7-11-in-chiang-mai-2"),
    "hotel": ("site", "chiang-mai-7-century-hostel-small-room"),
    "school": None,
    "school-intl": None,
    "market": ("site", "warorot-market-01"),
    "shopping": ("site", "chiang-mai-night-bazaar-thailand-frb-2012-6918118894"),
    "realestate": "skyline-towers",               # her own: the condo towers
    "transport": "motorbikes",                    # her own: a rank of parked bikes
    "repair": "wires-sky",                        # her own: the overhead tangle
    "beauty": None,                               # no photograph of a salon
    "tattoo": ("site", "sak-yant-chiang-mai-3"),  # a sak yant shop, at night
    "pets": None,
    "sport": None,
    "muaythai": ("site", "womens-muay-thai-teep"),
    "cooking": ("site", "thai-cooking-class-chiang-mai-thailand"),
    "chang": None,                                # every elephant on file is a statue
    "home-services": None,
    "community": ("site", "international-lahu-new-year-event-held-on-january-11-13-2024"),
    "business": ("site", "ceramic-production-molds-in-a-ceramics-workshop-in-chiang-ma"),
    "whats-on": "cabaret-curtain",                # her own: the cabaret's curtain
    "museums-galleries": ("site", "exhibit-at-lanna-folklife-museum-chiang-mai-thailand-3509800"),
    "parks": "great-tree",                        # her own: a big tree from under it
    "sights": "black-house",                      # her own: the Black House gate
}

# The minisites. `pic` is a hero slug or ("site", commons-slug).
MINISITES = [
    {"href": "loop/", "th": "ลูปแม่ฮ่องสอน", "en": "Mae Hong Son Loop", "pic": "flower-garden-hills"},
    {"href": "muay-thai/", "th": "มวยไทย", "en": "Muay Thai", "pic": ("site", "muay-thai-thai-boxing-kids-img-1824")},
    {"href": "https://wichaa.net/handpoke/", "th": "สักมือ", "en": "Hand Poke", "pic": ("site", "thai-tattoo-made-by-ajarn-prayot")},
    {"href": "festivals.html", "th": "เทศกาล", "en": "Festivals", "pic": ("site", "chiang-mai-procession-lantern-festival-thailand")},
    {"href": "merit.html", "th": "ไหว้พระ ๙ วัด", "en": "Nine Wats", "pic": "golden-chedi-1"},
    {"href": "horoscope.html", "th": "ดวง", "en": "Horoscope", "pic": ("site", "420-sak-yant-tattoo-32")},
    {"href": "foon.html", "th": "ฝุ่น", "en": "Dust", "pic": "pm25-sign"},
    {"href": "plan.html", "th": "วางแผนเดิน", "en": "Plan a walk", "pic": "lane-morning"},
    {"href": "toilets.html", "th": "ห้องน้ำ", "en": "Toilets", "pic": None},
    {"href": "chuai.html", "th": "ช่วย", "en": "Help, nearest", "pic": None},
]


def _j(p):
    return json.loads((DATA / p).read_text())


def esc(s):
    return html.escape(str(s), quote=True)


def bi(th, en):
    return f'<span class="th" lang="th">{esc(th)}</span><span class="en" lang="en">{esc(en)}</span>'


# ---------------------------------------------------------------- payload

def almanac(today, days=45):
    F = _j("fortune.json")["days"]
    S = _j("sky.json")["days"]
    out = []
    for i in range(days):
        d = (today + datetime.timedelta(days=i)).isoformat()
        f, s = F.get(d), S.get(d)
        if not f:
            break
        t, m = f["thai"], (s or {}).get("moon") or {}
        c, hx = f.get("chinese") or {}, f.get("hexagram") or {}
        night = f.get("thai_night") or {}
        out.append({
            "d": d, "dt": t["th"], "de": t["en"],
            "c": t["hex"], "ct": t["colour_th"], "ce": t["colour_en"],
            "pt": t["planet_th"], "pe": t["planet_en"],
            "bt": t["buddha_th"], "be": t["buddha_en"],
            "lk": t.get("lucky", {}).get("two") or [],
            "nt": night.get("colour_th"), "ne": night.get("colour_en"), "nc": night.get("hex"),
            "mi": m.get("illum"), "mw": bool(m.get("waxing")), "wp": bool(m.get("wan_phra")),
            "mt": m.get("thai_label_th"), "me": m.get("thai_label_en"),
            "za": c.get("animal"), "zp": c.get("pillar"), "zt": c.get("relation_th"), "ze": c.get("relation_en"),
            "hn": hx.get("number"), "hz": hx.get("zh"), "he": hx.get("en"),
        })
    return out


def open_slots():
    """Per city, per weekday, 96 quarter-hour counts of places open."""
    o = _j("open_lamps.json")
    sched, places = o["schedules"], o["places"]
    use = {}
    for p in places:
        use[(p["p"], p["k"])] = use.get((p["p"], p["k"]), 0) + 1
    out = {}
    for city in ("cm", "cr"):
        grid = [[0] * 96 for _ in range(7)]
        for (p, k), n in use.items():
            if p != city:
                continue
            for a, b in sched[k]:
                s = a // 15
                e = max(s + 1, math.ceil(b / 15))
                for q in range(s, min(e, 7 * 96)):
                    grid[q // 96][q % 96] += n
        out[city] = grid
    markets = [{"n": p["n"], "p": p["p"], "iv": sched[p["k"]]}
               for p in places if p.get("g") == "market"]
    with_hours = {c: sum(1 for p in places if p["p"] == c) for c in ("cm", "cr")}
    return out, markets, with_hours


def events(today, days=21):
    rows = _j("events.json")["events"]
    by = {}
    for i in range(days):
        d = today + datetime.timedelta(days=i)
        items = []
        for e in rows:
            st = e.get("start") or ""
            if e.get("recurring") and e.get("weekday") is not None:
                if e["weekday"] != d.weekday():
                    continue
            elif st[:10] != d.isoformat():
                continue
            m = None
            if not e.get("all_day") and len(st) >= 16:
                m = int(st[11:13]) * 60 + int(st[14:16])
            t = (e.get("title") or "").strip()
            items.append({"t": t if len(t) <= 58 else t[:56].rstrip() + "…", "v": (e.get("venue_name") or "")[:40],
                          "m": m, "u": e.get("url") or ""})
        seen, uniq = set(), []
        for it in sorted(items, key=lambda x: (x["m"] is None, x["m"] or 0)):
            k = (it["t"], it["v"])
            if k in seen:
                continue
            seen.add(k)
            uniq.append(it)
        by[d.isoformat()] = uniq[:12]
    return by


def festivals(today):
    fs = _j("festivals.json")["festivals"]
    dated = {}
    for r in _j("festival_dates.json")["rows"]:
        if r.get("date_start") and r["date_start"] >= today.isoformat():
            dated.setdefault(r["festival_id"], r["date_start"])
    out = []
    for f in fs:
        start = dated.get(f["id"])
        months = f.get("months") or [f.get("month")]
        out.append({"id": f["id"], "th": f["name_th"], "en": f["name_en"],
                    "s": start, "m": [m for m in months if m], "p": f.get("province")})
    return out


def wan_phra(today):
    S = _j("sky.json")["days"]
    return [d for d, v in sorted(S.items())
            if d >= today.isoformat() and (v.get("moon") or {}).get("wan_phra")][:8]


def weather_air():
    W = {c["id"]: c for c in _j("weather.json")["cities"]}
    A = {p["id"]: p for p in _j("air.json")["places"]}
    out = {}
    for key, _, _, _, _ in CITIES:
        wid = {"cm": "chiang-mai", "cr": "chiang-rai"}[key]
        w, a = W.get(wid) or {}, A.get(wid) or {}
        out[key] = {"t": w.get("temp"), "code": w.get("code"), "obs": w.get("observed"),
                    "days": [{"d": x["date"], "hi": x["max"], "lo": x["min"], "code": x["code"]}
                             for x in (w.get("days") or [])[:4]],
                    "pm": a.get("pm25"), "band": (a.get("band") or {}).get("key"),
                    "bc": (a.get("band") or {}).get("colour"),
                    "bt": (a.get("band") or {}).get("th"), "be": (a.get("band") or {}).get("en")}
    return out


def cleanrooms():
    rows = _j("cleanrooms.json").get("rooms") or []
    return {"cm": sum(1 for r in rows if r.get("p") == "cm"),
            "cr": sum(1 for r in rows if r.get("p") == "cr")}


def showtimes(today):
    s = _j("showtimes.json")
    d = today.isoformat()
    n = 0
    for c in s.get("cinemas") or []:
        n += len((c.get("days") or {}).get(d) or [])
    return {"d": d, "n": n}


def totals():
    cats = {c["key"]: c for c in _j("categories.json")["categories"]}
    order = list(cats)
    out, shelves = {}, {}
    for key, _, _, _, _ in CITIES:
        recs = _j(f"canonical/{key}.json")
        out[key] = len(recs)
        for r in recs:
            c = (r.get("cat") or [None])[0]
            if c in cats:
                shelves.setdefault(c, {"cm": 0, "cr": 0})[key] += 1
    return out, [(k, cats[k]["th"], cats[k]["en"], shelves.get(k, {"cm": 0, "cr": 0})) for k in order]


def heroes():
    return json.loads((DOCS / "site" / "hero" / "index.json").read_text())


def picks():
    return _j("curated/image_picks.json")["picks"]


def emergency():
    return [{"tel": n["tel"], "th": n["th"], "en": n["en"]}
            for n in _j("curated/emergency.json")["numbers"]]


# ---------------------------------------------------------------- pictures

class Art:
    """Which picture stands where, and who to credit for it."""

    def __init__(self):
        self.heroes = {h["slug"]: h for h in heroes()}
        self.picks = {p["slug"]: p for p in picks()}
        self.used_commons = {}

    def hero(self, slug):
        h = self.heroes[slug]
        return {"j": f'site/hero/{slug}.jpg', "w": f'site/hero/{slug}.webp',
                "W": h["w"], "H": h["h"], "by": "nan"}

    def commons(self, slug):
        p = self.picks[slug]
        self.used_commons[slug] = p
        return {"j": f'site/{slug}.jpg', "w": "", "W": p["width"], "H": p["height"], "by": slug}

    def flat(self):
        """Every frame of Nan's, as the page carries them: the two files, the
        hour pool, the scene it was chosen for, the iconic flag, and — only
        where the picks marked the frame public — a coordinate at three
        decimals. That coordinate is the whole geofence: a reader standing at
        a wat gets the frames shot near it."""
        out = []
        for h in self.heroes.values():
            if not h.get("bg"):
                continue
            row = self.hero(h["slug"])
            row.pop("by", None)
            row.update(p=h["pool"], s=h["scene"])
            if h.get("ic"):
                row["ic"] = 1
            if h.get("la") is not None:
                row["la"], row["lo"] = h["la"], h["lo"]
            out.append(row)
        return out

    def for_shelf(self, key):
        """The shelf's photograph, or None — and None is an answer."""
        want = SHELF_PIC.get(key)
        return self.any(want) if want else None

    def any(self, ref):
        return self.commons(ref[1]) if isinstance(ref, tuple) else self.hero(ref)

    def credits_html(self):
        rows = "".join(
            f'<li><a href="{esc(p["page"])}" rel="noopener">{esc(p["title"].removeprefix("File:"))}</a> — '
            f'{esc(p.get("artist") or "")}, {esc(p.get("licence") or "")}</li>'
            for p in self.used_commons.values())
        return (f'<!-- stylecheck: allow-start --><details class="credits"><summary>{bi("ภาพ", "Pictures")}</summary>'
                f'<p>{bi("ภาพถ่ายในหน้านี้: Nan", "Photographs on this page: Nan")} · CC BY 4.0</p>'
                f'<ul>{rows}</ul><p><a href="pictures.html">{bi("ภาพทั้งหมด", "All pictures")}</a></p></details><!-- stylecheck: allow-end -->')


def pic_tag(art, ref, cls="bg", eager=False, alt=""):
    a = art.any(ref) if not isinstance(ref, dict) else ref
    src = f'<source type="image/webp" srcset="{a["w"]}">' if a["w"] else ""
    load = 'fetchpriority="high"' if eager else 'loading="lazy" decoding="async"'
    return (f'<picture class="{cls}">{src}<img src="{a["j"]}" width="{a["W"]}" height="{a["H"]}" '
            f'alt="{esc(alt)}" {load}></picture>')


# ---------------------------------------------------------------- the page

def render(today=None):
    today = today or datetime.datetime.now(TZ).date()
    art = Art()
    tot, shelves = totals()
    slots, markets, with_hours = open_slots()
    wa = weather_air()
    cr = cleanrooms()
    alm = almanac(today)
    ev = events(today)
    be = today.year + 543

    payload = {
        "today": today.isoformat(), "be": be,
        "alm": alm, "open": slots, "markets": markets, "withHours": with_hours,
        "ev": ev, "fest": festivals(today), "wp": wan_phra(today),
        "wa": wa, "clean": cr, "shows": showtimes(today), "tot": tot,
        "pics": art.flat(),
        "sos": emergency(),
        "cities": [{"k": k, "th": th, "en": en, "lat": la, "lon": lo} for k, th, en, la, lo in CITIES],
    }

    # Server-side frame per scene: a fixed choice per build date, so a reader
    # with no script still sees a picture. The script re-picks by the hour.
    def first(scene, pool):
        p = payload["pics"]
        cand = ([x for x in p if x["s"] == scene and x["p"] == pool]
                or [x for x in p if x["s"] == scene] or p)
        return cand[today.toordinal() % len(cand)]

    lang_html = ('<div class="langs" role="group" aria-label="ภาษา Language">'
                 '<button type="button" data-lang="th" aria-pressed="false">ไทย</button>'
                 '<button type="button" data-lang="both" aria-pressed="true">+EN</button>'
                 '<button type="button" data-lang="en" aria-pressed="false">EN</button></div>')
    read_html = ('<button type="button" class="readbtn" data-read aria-pressed="false" '
                 'title="อ่านง่าย · Easy read" aria-label="อ่านง่าย · Easy read">อา</button>')

    pills = "".join(
        f'<a class="city" data-city="{k}" href="{k}/">{esc(th)}<span class="en" lang="en"> {esc(en)}</span>'
        f'<b>{tot[k]:,}</b></a>' for k, th, en, _, _ in CITIES)

    sos_rows = "".join(f'<a href="tel:{esc(n["tel"])}"><b>{esc(n["tel"])}</b> {bi(n["th"], n["en"])}</a>'
                       for n in payload["sos"])

    deep = ""
    for m in MINISITES:
        ext = ' rel="noopener"' if m["href"].startswith("http") else ""
        pic = pic_tag(art, art.any(m["pic"])) if m["pic"] else '<span class="bg flat"></span>'
        deep += (f'<a class="tile{"" if m["pic"] else " bare"}" href="{esc(m["href"])}"{ext}>{pic}'
                 f'<span class="lbl">{bi(m["th"], m["en"])}</span></a>')

    wander = ""
    for key, th, en, n in shelves:
        a = art.for_shelf(key)
        pic = pic_tag(art, a) if a else '<span class="bg flat"></span>'
        wander += (f'<a class="tile shelf{"" if a else " bare"}" data-shelf="{key}" data-cm="{n["cm"]}" data-cr="{n["cr"]}" href="cm/{key}/">'
                   f'{pic}<span class="lbl">{bi(th, en)}<b class="n">{n["cm"]:,}</b></span></a>')

    desc = ("มดแดง — สารบัญเมืองเชียงใหม่และเชียงราย ตอนนี้ ใกล้ๆ วันนี้ · "
            "Mot Dang — Chiang Mai and Chiang Rai: now, near, today.")
    og = art.hero("golden-chedi-flags")["j"]

    page = f"""<!DOCTYPE html>
<html lang="th" class="lang-both" data-root=""><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1,viewport-fit=cover">
<title>มดแดง — เชียงใหม่ · เชียงราย · Mot Dang — Chiang Mai & Chiang Rai</title>
<meta name="description" content="{esc(desc)}">
<meta name="md-where" content="">
<link rel="canonical" href="{BASE}">
<meta property="og:site_name" content="มดแดง Mot Dang">
<meta property="og:title" content="มดแดง · Mot Dang">
<meta property="og:description" content="{esc(desc)}">
<meta property="og:type" content="website">
<meta property="og:url" content="{BASE}">
<meta property="og:image" content="{BASE}{og}">
<meta property="og:locale" content="th_TH">
<meta property="og:locale:alternate" content="en_GB">
<meta name="twitter:card" content="summary_large_image">
<meta name="theme-color" content="#1a1410">
<link rel="alternate" type="application/rss+xml" title="มดแดง — ของเด่น" href="rss.xml">
<link rel="icon" type="image/svg+xml" href="logo/motdang-favicon.svg">
<link rel="icon" type="image/png" sizes="32x32" href="logo/motdang-mark-32.png">
<link rel="apple-touch-icon" href="logo/motdang-mark-180.png">
<script>try{{var _r=document.documentElement,_l=localStorage.getItem('md-lang');if(localStorage.getItem('md-read')==='1')_r.classList.add('easyread');if(_l==='en'||_l==='th'){{_r.classList.remove('lang-both');_r.classList.add('lang-'+_l)}}if(_l==='en')_r.lang='en'}}catch(e){{}}</script>
<style>{FACES}
{CSS}</style>
<script type="application/ld+json">{json.dumps({"@context": "https://schema.org", "@type": "WebSite", "name": "มดแดง Mot Dang", "alternateName": "Mot Dang", "url": BASE, "inLanguage": ["th", "en"]}, ensure_ascii=False)}</script>
</head><body>
<a class="skip" href="#now">{bi("ข้ามไปเนื้อหา", "Skip to content")}</a>
<header class="top">{read_html}{lang_html}</header>
<main>
<section class="s hero" id="top">
{pic_tag(art, first("hero", "day"), eager=True)}
<div class="scrim"></div>
<div class="in">
<div class="plate hero">
<h1 class="wordmark"><span class="wth">มดแดง</span><span class="wrom">MOT DANG</span></h1>
<p class="nowline" aria-live="off">
<a class="clock" href="widgets.html#w-clocks"><time id="clock">--:--</time><span class="bedate" id="bedate"></span></a>
<a class="colour" id="colour" href="horoscope.html"><i></i></a>
<a class="moon" id="moon" href="widgets.html#w-sky"></a>
<a class="temp" id="temp" href="widgets.html#w-weather"></a>
<a class="pm" id="pm" href="foon.html"></a>
</p>
<nav class="cities" aria-label="จังหวัด Province">{pills}</nav>
</div>
</div>
<a class="down" href="#now" aria-label="ต่อ · more">⌄</a>
</section>

<section class="s now" id="now">
{pic_tag(art, first("now", "day"))}
<div class="scrim"></div>
<div class="in">
<div class="plate">
<h2>{bi("ตอนนี้", "Now")}</h2>
<ol class="counters" id="counters"></ol>
<!-- stylecheck: allow-start --><details class="sos"><summary>{bi("ฉุกเฉิน", "Emergency")}</summary><div class="sheet">{sos_rows}
<a href="chuai.html">{bi("ช่วย — ที่ใกล้ที่สุด", "Help — what is nearest")} →</a></div></details><!-- stylecheck: allow-end -->
</div>
</div>
</section>

<section class="s near" id="near">
{pic_tag(art, first("near", "day"))}
<div class="scrim"></div>
<div class="in">
<div class="plate">
<h2>{bi("ใกล้ๆ", "Near")}</h2>
<p class="where" id="where"></p>
<button type="button" class="locate" id="locate">📍 <span>{bi("ที่ฉันยืนอยู่", "Where I stand")}</span></button>
<ol class="nearlist" id="nearlist"></ol>
<p class="doors"><a href="map.html">{bi("แผนที่", "Map")}</a> · <a href="here.html">{bi("ตรงนี้", "Here")}</a> · <a href="toilets.html">{bi("ห้องน้ำ", "Toilets")}</a></p>
</div>
</div>
</section>

<section class="s day" id="day">
{pic_tag(art, first("day", "day"))}
<div class="scrim"></div>
<div class="in">
<div class="plate">
<h2>{bi("วันนี้", "Today")}</h2>
<details class="card" id="daycard"><summary id="daysum"></summary><div class="more" id="daymore"></div>
<p class="doors"><a href="horoscope.html">{bi("ดวง", "Horoscope")}</a> · <a href="merit.html">{bi("ไหว้พระ ๙ วัด", "Nine wats")}</a> · <a href="widgets.html#w-katha">{bi("คาถา", "Katha")}</a> · <a href="widgets.html#w-lottery">{bi("หวย", "Lottery")}</a> · <a href="widgets.html#w-siamsi">{bi("เซียมซี", "Siam si")}</a></p></details>
</div>
</div>
</section>

<section class="s deep" id="deep">
<div class="in">
<h2>{bi("เจาะลึก", "Deep")}</h2>
<div class="tiles">{deep}</div>
</div>
</section>

<section class="s wander" id="wander">
<div class="in">
<h2><span class="th" lang="th">ทุกชั้น ทุกหมวด</span><span class="en" lang="en">every shelf</span></h2>
<div class="tiles small" id="shelves">{wander}</div>
<p class="doors"><a class="dice" href="random">🎲 {bi("พาไป", "Take me somewhere")}</a> · <a href="all.html">{bi("ทั้งหมด", "All")} →</a></p>
</div>
</section>
</main>

<footer class="door" id="door">
{pic_tag(art, first("door", "dusk"))}
<div class="scrim"></div>
<div class="in">
<div class="plate">
<p class="glyphs"><a href="add.html">{bi("เพิ่มข้อมูล", "Add a place")}</a> · <a href="https://ask.motdang.net" rel="noopener">{bi("คุยกับมด", "Chat with the ants")}</a> · <a href="source/">{bi("โค้ดและข้อมูลดิบ", "Source")}</a> · <a href="elsewhere.html">{bi("ที่อื่นของเรา", "Elsewhere")}</a> · <a href="api/">API</a></p>
<p class="lic"><a href="https://creativecommons.org/licenses/by/4.0/" rel="license noopener">CC BY 4.0</a> · <a href="https://www.openstreetmap.org/copyright" rel="noopener">© OSM</a> · <time datetime="{today.isoformat()}">{be}-{today.month:02d}-{today.day:02d}</time></p>
{art.credits_html()}
</div>
</div>
</footer>
<!-- stylecheck: allow-start -->
<script type="application/json" id="md-home">{json.dumps(payload, ensure_ascii=False, separators=(",", ":"))}</script>
<!-- stylecheck: allow-end -->
<script>{JS}</script>
</body></html>
"""
    return page


FACES = (ROOT / "assets" / "fonts" / "_faces.css").read_text()

GRAIN = ("url(\"data:image/svg+xml;utf8,<svg xmlns='http://www.w3.org/2000/svg' width='160' height='160'>"
         "<filter id='n'><feTurbulence type='fractalNoise' baseFrequency='.9' numOctaves='2' stitchTiles='stitch'/>"
         "<feColorMatrix values='0 0 0 0 0.5 0 0 0 0 0.5 0 0 0 0 0.5 0 0 0 .55 0'/></filter>"
         "<rect width='160' height='160' filter='url(%23n)'/></svg>\")")

CSS = r"""
:root{
 --ink:#f8f2e6;--dim:#ddd4c3;--ant:#e0483a;--gold:#f1c453;--night:#15110e;
 /* THE ONE SURFACE. Every word on this page sits on this colour, never on a
    photograph. At .84 over the worst case a photograph can be (pure white)
    the composite is rgb(56,54,52), which carries --ink at 9.7:1 and --dim at
    7.2:1 — so legibility does not depend on which frame the hour picked.
    tests/test_home.py computes both ratios against that worst case. */
 --plate:rgba(18,14,11,.84);--hair:rgba(255,255,255,.14);
 --th:'Prompt','Sarabun',system-ui,sans-serif;--tx:'Sarabun','Atkinson Hyperlegible',system-ui,sans-serif;--mono:'JetBrains Mono',ui-monospace,monospace}
*{box-sizing:border-box}html{scroll-behavior:smooth;background:var(--night)}
@media (prefers-reduced-motion:reduce){html{scroll-behavior:auto}}
body{margin:0;font-family:var(--tx);color:var(--ink);background:var(--night);line-height:1.45;-webkit-font-smoothing:antialiased}
html.easyread body{font-family:'Atkinson Hyperlegible','Sarabun',sans-serif;font-size:1.12em;line-height:1.6}
a{color:inherit;text-decoration:none}a:hover{text-decoration:underline;text-underline-offset:.22em}
:focus-visible{outline:3px solid var(--gold);outline-offset:3px;border-radius:6px}
.skip{position:absolute;left:-999px;top:0;background:#fff;color:#000;padding:10px 16px}.skip:focus{left:10px;top:10px;z-index:99}
.th,.en{display:inline}html.lang-th .en{display:none}html.lang-en .th{display:none}
html.lang-both .th+.en::before{content:" · "}

/* ---- the header: two controls, on their own plates ---- */
.top{position:fixed;inset:0 0 auto 0;z-index:5;display:flex;justify-content:space-between;align-items:center;
 padding:max(12px,env(safe-area-inset-top)) clamp(14px,3vw,28px) 0;pointer-events:none}
.top>*{pointer-events:auto}
.readbtn,.langs button{font:inherit;font-family:var(--th);font-size:15px;border:1px solid var(--hair);
 background:rgba(18,14,11,.78);backdrop-filter:blur(10px);color:var(--ink);border-radius:999px;
 padding:9px 15px;min-height:44px;cursor:pointer}
.langs{display:inline-flex;border-radius:999px;overflow:hidden;border:1px solid var(--hair);background:rgba(18,14,11,.78);backdrop-filter:blur(10px)}
.langs button{border:0;border-left:1px solid var(--hair);border-radius:0;background:transparent;backdrop-filter:none}
.langs button:first-child{border-left:0}
.langs button[aria-pressed=true],.readbtn[aria-pressed=true]{background:var(--ink);color:#15110e;font-weight:600}

/* ---- a scene: a big picture, and words that never sit on it ---- */
.s,.door{position:relative;min-height:100svh;display:grid;align-items:center;overflow:hidden;isolation:isolate}
.s.deep,.s.wander{min-height:0;background:var(--night)}
.bg{position:absolute;inset:-10% 0;z-index:-2;margin:0}
.bg img{width:100%;height:100%;object-fit:cover;display:block;will-change:transform;filter:brightness(.88) saturate(1.06)}
.bg.flat{background:linear-gradient(160deg,#2b231c 0%,#1d1713 100%)}
.tile.bare{border:1px solid var(--hair)}
.tile.bare::after{background:none}
.tile.bare .lbl{position:static;display:grid;align-content:end;height:100%;background:none;backdrop-filter:none;padding:clamp(12px,1.4vw,18px)}
.scrim{position:absolute;inset:0;z-index:-1;background:
 radial-gradient(130% 100% at 50% 50%,rgba(21,17,14,0) 38%,rgba(21,17,14,.42) 100%),
 linear-gradient(180deg,rgba(21,17,14,.34) 0%,rgba(21,17,14,0) 22%,rgba(21,17,14,0) 72%,rgba(21,17,14,.72) 100%)}
.scrim::after{content:"";position:absolute;inset:0;background-image:GRAIN;opacity:.14;mix-blend-mode:overlay;pointer-events:none}
.in{width:min(1240px,100%);margin:0 auto;padding:clamp(104px,17vh,190px) clamp(18px,5vw,64px) clamp(72px,13vh,130px)}
.plate{max-width:880px;margin:0 auto;background:var(--plate);backdrop-filter:blur(16px) saturate(1.15);
 border:1px solid var(--hair);border-radius:28px;padding:clamp(24px,3.2vw,44px);
 box-shadow:0 34px 90px rgba(0,0,0,.5)}
h2{font-family:var(--th);font-weight:600;font-size:clamp(13px,1.3vw,16px);letter-spacing:.24em;text-transform:uppercase;
 color:var(--dim);margin:0 0 clamp(20px,2.6vw,30px)}
html.lang-both h2 .th+.en::before{content:" · "}

/* ---- the hero ---- */
.hero .in{display:grid;justify-items:center}
.plate.hero{display:grid;gap:clamp(20px,2.8vw,32px);justify-items:center;text-align:center;
 max-width:min(720px,100%);padding:clamp(30px,4vw,52px) clamp(26px,5vw,60px)}
.wordmark{margin:0;display:grid;gap:8px;justify-items:center;font-family:var(--th);font-weight:600}
.wth{font-size:clamp(50px,9vw,104px);line-height:1;color:#fff}
.wrom{font-size:clamp(11px,1vw,14px);letter-spacing:.46em;margin-left:.46em;font-weight:400;color:var(--dim)}
.nowline{margin:0;display:flex;flex-wrap:wrap;justify-content:center;align-items:center;gap:12px clamp(16px,2.4vw,28px);
 font-family:var(--mono);font-size:clamp(15px,1.5vw,19px)}
.nowline a{display:inline-flex;align-items:center;gap:8px;min-height:44px;padding:0 2px}
.clock time{font-size:clamp(26px,3.2vw,40px);font-weight:700}
.bedate{font-size:.66em;color:var(--dim);margin-left:10px}
.colour i{display:block;width:20px;height:20px;border-radius:50%;border:2px solid rgba(255,255,255,.8)}
.moon svg{width:24px;height:24px}
.pm b{font-weight:700;padding:2px 9px;border-radius:7px;color:#15110e}
.cities{display:inline-flex;border:1px solid var(--hair);border-radius:999px;overflow:hidden}
.city{padding:12px clamp(16px,2.2vw,24px);min-height:48px;display:inline-flex;align-items:center;gap:9px;
 font-family:var(--th);font-size:clamp(15px,1.5vw,18px);border-left:1px solid var(--hair);white-space:nowrap}
html.lang-both .city .en,html.lang-both .moon .en{display:none}
.city:first-child{border-left:0}
.city b{font-family:var(--mono);font-weight:400;font-size:.76em;color:var(--dim)}
.city.on{background:var(--ink);color:#15110e}.city.on b{color:#4a443a}
.down{position:absolute;left:50%;bottom:max(18px,env(safe-area-inset-bottom));transform:translateX(-50%);
 width:48px;height:48px;display:grid;place-items:center;border-radius:50%;background:rgba(18,14,11,.78);
 backdrop-filter:blur(10px);border:1px solid var(--hair);font-size:26px;line-height:1;color:var(--ink);
 animation:bob 2.6s ease-in-out infinite}
@keyframes bob{50%{transform:translate(-50%,7px)}}
@media (prefers-reduced-motion:reduce){.down{animation:none}}

/* ---- rows: hairlines on the plate, no cards inside cards ---- */
.counters,.nearlist{list-style:none;margin:0;padding:0;display:grid}
.counters li,.nearlist li{border-top:1px solid var(--hair)}
.counters li:first-child,.nearlist li:first-child{border-top:0}
.counters li a,.nearlist li a{display:grid;grid-template-columns:auto minmax(0,1fr);gap:clamp(16px,2vw,24px);
 align-items:center;padding:clamp(16px,2vw,22px) 4px;min-height:64px}
.counters li a:hover,.nearlist li a:hover{text-decoration:none}
.counters li a:hover .t,.nearlist li a:hover .nm{text-decoration:underline;text-underline-offset:.22em}
.counters .big{font-family:var(--mono);font-size:clamp(28px,3.4vw,42px);font-weight:700;line-height:1;
 min-width:2.4ch;text-align:center;color:var(--gold)}
.counters .lbl,.nearlist .lbl{display:grid;gap:5px;min-width:0;overflow-wrap:anywhere}
.counters .t{font-size:clamp(16px,1.7vw,20px);font-weight:600;line-height:1.3}
.counters .lbl small,.nearlist .lbl small{color:var(--dim);font-size:clamp(13px,1.2vw,15px)}
.counters li.red{background:rgba(196,42,32,.34);border-radius:16px;border-top-color:transparent;margin:6px 0}
.counters li.red+li{border-top-color:transparent}
.counters li.red a{padding-left:16px;padding-right:16px}
.counters li.red .big{color:#fff}
.counters .curve{grid-column:1/-1;height:30px;display:flex;align-items:flex-end;gap:1px;opacity:.65;margin-top:4px}
.curve i{flex:1;background:var(--dim);border-radius:2px 2px 0 0;min-height:1px}
.curve i.on{background:var(--gold);opacity:1}
.sos{margin-top:clamp(20px,2.6vw,28px)}
.sos summary{list-style:none;cursor:pointer;display:inline-flex;align-items:center;gap:10px;min-height:48px;
 padding:10px 20px;border-radius:999px;border:1px solid var(--ant);color:#fff;background:rgba(196,42,32,.42);
 font-family:var(--th);font-size:16px}
.sos summary::-webkit-details-marker{display:none}.sos summary::before{content:"\260E";font-size:19px}
.sos .sheet{display:grid;gap:8px;margin-top:14px}
.sos .sheet a{display:block;padding:13px 16px;background:rgba(255,255,255,.07);border-radius:14px}
.sos .sheet b{font-family:var(--mono);color:var(--gold);margin-right:10px}

/* ---- near ---- */
.where{margin:0 0 14px;font-family:var(--mono);font-size:clamp(14px,1.3vw,16px);color:var(--dim)}
.locate{font:inherit;font-family:var(--th);font-size:16px;border:1px solid var(--hair);background:rgba(255,255,255,.08);
 color:var(--ink);border-radius:999px;padding:12px 22px;min-height:48px;cursor:pointer}
.locate[disabled]{opacity:.6}
.nearlist{margin-top:8px}
.nearlist li a{grid-template-columns:auto minmax(0,1fr) auto}
.nearlist .nm{font-size:clamp(16px,1.6vw,19px)}
.nearlist .d{font-family:var(--mono);font-size:14px;color:var(--dim)}
.nearlist .k{font-size:24px;width:32px;text-align:center}
.nearlist .open{color:var(--gold);font-size:13px}
.doors{margin:clamp(20px,2.6vw,28px) 0 0;color:var(--dim);font-family:var(--th);font-size:clamp(14px,1.4vw,17px);
 display:flex;flex-wrap:wrap;gap:6px 14px}
.doors a{padding:8px 0;color:var(--ink)}

/* ---- today ---- */
.card{border:0;padding:0;background:transparent}
.card summary{list-style:none;cursor:pointer;display:grid;grid-template-columns:auto minmax(0,1fr);
 gap:clamp(16px,2vw,24px);align-items:center;min-height:68px;padding:4px}
.card summary::-webkit-details-marker{display:none}
.card .sw{width:clamp(46px,5vw,60px);aspect-ratio:1;border-radius:50%;border:3px solid rgba(255,255,255,.8)}
.card .head{display:grid;gap:5px}
.card .head b{font-family:var(--th);font-size:clamp(20px,2.4vw,28px);font-weight:600}
.card .head small{color:var(--dim);font-size:clamp(13px,1.3vw,16px)}
.card .more{margin-top:clamp(18px,2.2vw,24px);display:grid;gap:14px;border-top:1px solid var(--hair);padding-top:clamp(18px,2.2vw,24px)}
.card .more p{margin:0;display:grid;grid-template-columns:clamp(84px,9vw,120px) minmax(0,1fr);gap:16px;align-items:baseline}
.card .more .k{font-family:var(--mono);color:var(--gold);font-size:13px;letter-spacing:.08em}
.card .more .lk{font-family:var(--mono);font-size:clamp(20px,2.4vw,28px);font-weight:700}

/* ---- the tiles ---- */
.deep .in,.wander .in{padding-top:clamp(64px,9vh,110px);padding-bottom:clamp(48px,7vh,90px)}
.deep h2,.wander h2{max-width:880px;margin-left:auto;margin-right:auto}
.tiles{display:grid;grid-template-columns:repeat(2,1fr);gap:clamp(12px,1.6vw,20px)}
@media (min-width:700px){.tiles{grid-template-columns:repeat(3,1fr)}.tiles.small{grid-template-columns:repeat(4,1fr)}}
@media (min-width:1100px){.tiles{grid-template-columns:repeat(4,1fr)}.tiles.small{grid-template-columns:repeat(5,1fr)}}
.tile{position:relative;display:block;aspect-ratio:4/3;border-radius:20px;overflow:hidden;background:#2a221c;isolation:isolate}
.tiles.small .tile{aspect-ratio:1}
.tile .bg{inset:0}
.tile .bg img{filter:brightness(.95) saturate(1.05);transition:transform .7s cubic-bezier(.2,.8,.2,1)}
.tile:hover .bg img,.tile:focus-visible .bg img{transform:scale(1.06)}
.tile .lbl{position:absolute;left:0;right:0;bottom:0;z-index:1;padding:clamp(10px,1.2vw,15px) clamp(12px,1.4vw,18px);
 background:rgba(18,14,11,.88);backdrop-filter:blur(8px);font-family:var(--th);font-weight:600;
 font-size:clamp(14px,1.5vw,18px);line-height:1.25}
.tiles.small .lbl{font-size:clamp(13px,1.3vw,16px)}
.tile .n{display:block;font-family:var(--mono);font-weight:400;font-size:.76em;color:var(--dim);margin-top:3px}
html.lang-both .tile .lbl .th+.en::before{content:"";display:block}
html.lang-both .tile .lbl .en{font-weight:400;font-size:.84em;color:var(--dim)}
.tile:hover{text-decoration:none}
.wander .doors,.deep .doors{max-width:880px;margin-left:auto;margin-right:auto;justify-content:center}
.dice{font-family:var(--th)}

/* ---- the door ---- */
.door{min-height:70svh}
.door .plate{max-width:760px;text-align:center;display:grid;gap:12px}
.door p{margin:0}
.door .glyphs{display:flex;flex-wrap:wrap;justify-content:center;gap:6px 14px;font-family:var(--th);font-size:15px}
.door .lic{color:var(--dim);font-family:var(--mono);font-size:13px}
.credits{margin-top:10px;color:var(--dim);font-size:13px}
.credits summary{cursor:pointer;min-height:44px;display:flex;align-items:center;justify-content:center}
.credits ul{text-align:left;padding-left:20px;max-height:220px;overflow:auto;line-height:1.6}

@media (prefers-reduced-motion:reduce){.bg{inset:0}.bg img{transform:none!important}.tile .bg img{transition:none}}
""".replace("GRAIN", GRAIN)

JS = r"""
(function(){
'use strict';
var D=JSON.parse(document.getElementById('md-home').textContent);
var H=document.documentElement;
var TH=H.classList.contains('lang-th'),EN=H.classList.contains('lang-en');
function bi(t,e){return '<span class="th" lang="th">'+t+'</span><span class="en" lang="en">'+e+'</span>';}
function esc(s){return String(s==null?'':s).replace(/[&<>"]/g,function(c){return {'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;'}[c];});}
function store(k,v){try{v==null?localStorage.removeItem(k):localStorage.setItem(k,v);}catch(e){}}
function read(k){try{return localStorage.getItem(k);}catch(e){return null;}}

/* ---- language and easy read: the same two keys every page on the site keeps */
document.querySelectorAll('.langs button').forEach(function(b){b.addEventListener('click',function(){
  var l=b.dataset.lang;H.classList.remove('lang-th','lang-en','lang-both');H.classList.add('lang-'+l);H.lang=l==='en'?'en':'th';
  store('md-lang',l==='both'?null:l);document.querySelectorAll('.langs button').forEach(function(x){x.setAttribute('aria-pressed',x===b);});});});
(function(){var l=read('md-lang')||'both';document.querySelectorAll('.langs button').forEach(function(x){x.setAttribute('aria-pressed',x.dataset.lang===l);});})();
var rb=document.querySelector('[data-read]');rb.setAttribute('aria-pressed',H.classList.contains('easyread'));
rb.addEventListener('click',function(){var on=!H.classList.contains('easyread');H.classList.toggle('easyread',on);store('md-read',on?'1':null);rb.setAttribute('aria-pressed',on);});

/* ---- the reader's clock, in Bangkok time whatever the phone says */
function now(){var s=new Date().toLocaleString('en-GB',{timeZone:'Asia/Bangkok',hour12:false});
  var m=s.match(/(\d\d)\/(\d\d)\/(\d{4}),? (\d\d):(\d\d)/);var d=new Date(Date.UTC(+m[3],+m[2]-1,+m[1],+m[4],+m[5]));
  return {iso:m[3]+'-'+m[2]+'-'+m[1],h:+m[4],mi:+m[5],min:+m[4]*60+ +m[5],wd:(d.getUTCDay()+6)%7,utc:d,y:+m[3],mo:+m[2],da:+m[1]};}
function pool(h){return h>=5&&h<10?'morning':h<17?'day':h<19?'dusk':'night';}
var T=now();
function tick(){T=now();var el=document.getElementById('clock');el.textContent=('0'+T.h).slice(-2)+':'+('0'+T.mi).slice(-2);el.setAttribute('datetime',T.iso+'T'+el.textContent);
  document.getElementById('bedate').textContent=(T.y+543)+'-'+('0'+T.mo).slice(-2)+'-'+('0'+T.da).slice(-2);}
tick();setInterval(tick,15000);

/* ---- the pictures ------------------------------------------------------
   Every frame is Nan's own, and most carry a coordinate at three decimals.
   So the page can answer the question a reader never asks out loud: show me
   where I am. Standing at a wat, the frames shot at that wat win; a few
   kilometres out, the ones from that part of town; past fifty, only the
   iconic set, because a reader in Bangkok wants the city at its best rather
   than a lane they have never walked. Position is the exact fix when they
   have tapped for one, otherwise the edge's guess, otherwise nothing. */
var RM=matchMedia('(prefers-reduced-motion: reduce)').matches;
var SCENES=['hero','now','near','day','door'],FIX=null;
function frameScore(f,scene,P,want,portrait){
  var s=1;
  if(f.s===scene)s*=1.8;
  if(f.p===want)s*=1.5;
  if(portrait!=null)s*=(portrait?(f.H>=f.W):(f.W>f.H))?1.25:1;
  if(P){
    if(FAR&&!FIX)return f.ic?s:0;
    if(f.la==null)s*=0.85;
    else{var d=km(P.lat,P.lon,f.la,f.lo);
      s*= d<1?14: d<5?7: d<15?3: d<50?1.2: (f.ic?0.8:0.15);}
  }else s*=f.ic?1.3:1;
  return s;
}
function paint(){
  var want=pool(T.h),P=FIX||(EDGE?{lat:EDGE.lat,lon:EDGE.lon}:null);
  var portrait=innerHeight>innerWidth,used={},seed=T.utc.getUTCDate()*7+Math.floor(T.h/3);
  SCENES.forEach(function(scene,si){
    var best=null,bs=0,n=0;
    D.pics.forEach(function(f,i){
      if(used[f.j])return;
      var v=frameScore(f,scene,P,want,portrait);
      if(v<=0)return;
      /* the seed breaks ties, so the same hour of the same day is stable and
         the next one is not */
      v*=1+(((i*31+seed+si*7)%17)/160);
      if(v>bs){bs=v;best=f;}
      n++;});
    if(!best)return;
    used[best.j]=1;
    var sec=document.querySelector(scene==='door'?'footer.door':'.s.'+scene);
    if(!sec)return;
    var img=sec.querySelector(':scope>.bg img'),src=sec.querySelector(':scope>.bg source');
    if(!img||img.getAttribute('src')===best.j)return;
    img.width=best.W;img.height=best.H;if(src)src.srcset=best.w;img.src=best.j;});
}

/* ---- parallax: the picture drifts a little slower than the words */
if(!RM){var secs=[].slice.call(document.querySelectorAll('.s,.door')),vis=new Set();
  var io=new IntersectionObserver(function(es){es.forEach(function(e){e.isIntersecting?vis.add(e.target):vis.delete(e.target);});});
  secs.forEach(function(s){io.observe(s);});var raf=0;
  function move(){raf=0;var vh=innerHeight;vis.forEach(function(s){var r=s.getBoundingClientRect();var p=(r.top+r.height/2-vh/2)/vh;var img=s.querySelector(':scope>.bg img');if(img)img.style.transform='translate3d(0,'+(p*8).toFixed(2)+'%,0)';});}
  addEventListener('scroll',function(){if(!raf)raf=requestAnimationFrame(move);},{passive:true});move();}

/* ---- where: the reader's choice, else the edge's guess, else Chiang Mai */
var META=(document.querySelector('meta[name=md-where]').content||'').split('|');
var EDGE=META.length>=3&&+META[1]?{city:META[0],lat:+META[1],lon:+META[2],tz:META[3]||''}:null;
function km(a,b,c,d){var R=6371,x=(c-a)*Math.PI/180,y=(d-b)*Math.PI/180;var s=Math.sin(x/2)*Math.sin(x/2)+Math.cos(a*Math.PI/180)*Math.cos(c*Math.PI/180)*Math.sin(y/2)*Math.sin(y/2);return 2*R*Math.asin(Math.sqrt(s));}
var FAR=false;
function guessCity(){var c=read('md-city');if(c==='cm'||c==='cr')return c;if(EDGE){var best=null,bd=1e9;D.cities.forEach(function(x){var d=km(EDGE.lat,EDGE.lon,x.lat,x.lon);if(d<bd){bd=d;best=x.k;}});if(bd<120)return best;FAR=true;}return 'cm';}
var CITY=guessCity();
function setCity(c,remember){CITY=c;if(remember)store('md-city',c);document.querySelectorAll('.city').forEach(function(a){a.classList.toggle('on',a.dataset.city===c);});
  document.querySelectorAll('.tile.shelf').forEach(function(t){t.href=c+'/'+t.dataset.shelf+'/';var n=t.querySelector('.n');if(n)n.textContent=(+t.dataset[c]).toLocaleString();});
  document.querySelector('.dice').href='random?city='+c;render();}
document.querySelectorAll('.city').forEach(function(a){a.addEventListener('click',function(e){e.preventDefault();setCity(a.dataset.city,true);});});

/* ---- now: the counters */
function fmtIn(min){if(min<60)return bi(min+' นาที',min+' min');var h=Math.floor(min/60),m=min%60;return bi(h+' ชม. '+(m?m+' น.':''),h+' h '+(m?m+' m':''));}
function daysTo(iso){var a=Date.UTC(T.y,T.mo-1,T.da),p=iso.split('-'),b=Date.UTC(+p[0],+p[1]-1,+p[2]);return Math.round((b-a)/864e5);}
function openNow(){var g=D.open[CITY];if(!g)return null;var q=Math.floor(T.min/15);return {n:g[T.wd][q],row:g[T.wd]};}
function nextEvent(){var keys=Object.keys(D.ev).sort();for(var i=0;i<keys.length;i++){var k=keys[i];if(k<T.iso)continue;var items=D.ev[k];for(var j=0;j<items.length;j++){var it=items[j];if(k===T.iso&&it.m!=null&&it.m<T.min-30)continue;if(k===T.iso&&it.m==null)continue;return {d:k,it:it,dd:daysTo(k)};}}return null;}
function nextMarket(){var best=null;D.markets.forEach(function(m){if(m.p!==CITY)return;m.iv.forEach(function(iv){var start=iv[0],nowW=T.wd*1440+T.min;var wait=start-nowW;if(iv[1]>nowW&&start<=nowW)wait=0;else if(wait<0)wait+=10080;if(!best||wait<best.wait)best={wait:wait,m:m,iv:iv};});});return best;}
function nextFest(){var out=[];D.fest.forEach(function(f){if(f.p&&f.p!==CITY&&f.p!=='both')return;var when=null,dd=null;if(f.s){dd=daysTo(f.s);if(dd<-2)return;when=f.s;}else{var m=f.m[0];if(!m)return;var y=T.y+(m<T.mo?1:0);var d=y+'-'+('0'+m).slice(-2)+'-01';dd=daysTo(d);if(m===T.mo)dd=0;}
  out.push({f:f,dd:dd,dated:!!f.s});});out.sort(function(a,b){return a.dd-b.dd;});return out.slice(0,2);}
function wdName(w){return [['จ.','Mon'],['อ.','Tue'],['พ.','Wed'],['พฤ.','Thu'],['ศ.','Fri'],['ส.','Sat'],['อา.','Sun']][w];}
function hm(m){m%=1440;return ('0'+Math.floor(m/60)).slice(-2)+':'+('0'+m%60).slice(-2);}
function render(){var L=[],wa=D.wa[CITY]||{},h=T.h;
  var bad=wa.band&&['moderate','unhealthy','very-unhealthy','hazardous','unhealthy-sensitive'].some(function(k){return (wa.band||'').indexOf(k)>=0;})||(wa.pm!=null&&wa.pm>37.5);
  if(bad)L.push({cls:'red',href:'foon.html',big:Math.round(wa.pm),t:bi('ฝุ่น PM2.5 '+(wa.bt||''),'PM2.5 '+(wa.be||'')),s:bi(D.clean[CITY]+' ห้องปลอดฝุ่น','clean-air rooms: '+D.clean[CITY])});
  if(h>=22||h<5){var s=D.sos[0];L.push({cls:'red',href:'tel:'+s.tel,big:s.tel,t:bi(s.th,s.en),s:bi('ร้านยา 24 ชม. → ช่วย','24-hour pharmacies → Help')});}
  var o=openNow();if(o){var curve='<span class="curve">'+o.row.map(function(v,i){var mx=Math.max.apply(null,o.row)||1;return '<i class="'+(i===Math.floor(T.min/15)?'on':'')+'" style="height:'+Math.max(4,Math.round(v/mx*100))+'%"></i>';}).join('')+'</span>';
    L.push({href:CITY+'/',big:o.n.toLocaleString(),t:bi('เปิดอยู่ตอนนี้','open right now'),s:bi('จาก '+D.withHours[CITY].toLocaleString()+' แห่งที่บอกเวลาเปิด','of '+D.withHours[CITY].toLocaleString()+' with posted hours'),extra:curve});}
  var ev=nextEvent();if(ev){var it=ev.it,when=ev.dd===0?fmtIn(it.m-T.min<0?0:it.m-T.min):ev.dd===1?bi('พรุ่งนี้'+(it.m!=null?' '+hm(it.m):''),'tomorrow'+(it.m!=null?' '+hm(it.m):'')):bi(wdName(new Date(ev.d).getUTCDay()===0?6:new Date(ev.d).getUTCDay()-1)[0]+(it.m!=null?' '+hm(it.m):''),wdName(new Date(ev.d).getUTCDay()===0?6:new Date(ev.d).getUTCDay()-1)[1]+(it.m!=null?' '+hm(it.m):''));
    L.push({href:it.u||'events.html',ext:!!it.u,big:'',t:esc(it.t),s:when+(it.v?' · '+esc(it.v):''),glyph:'🎪'});}
  var mk=nextMarket();if(mk){var w=mk.wait;var whenM=w===0?bi('เปิดอยู่','open now'):w<1440?fmtIn(w):bi(wdName(Math.floor(mk.iv[0]/1440))[0]+' '+hm(mk.iv[0]),wdName(Math.floor(mk.iv[0]/1440))[1]+' '+hm(mk.iv[0]));
    L.push({href:CITY+'/market/',big:'',glyph:'🏮',t:esc(mk.m.n),s:whenM});}
  if(D.shows.d===T.iso&&D.shows.n)L.push({href:CITY+'/whats-on/',big:D.shows.n,t:bi('รอบหนังวันนี้','films showing today'),s:''});
  var wp=D.wp.filter(function(d){return d>=T.iso;})[0];if(wp){var dd=daysTo(wp);L.push({href:'merit.html',glyph:'🌕',big:dd===0?'':dd,t:bi('วันพระ','Wan phra'),s:dd===0?bi('วันนี้','today'):bi('อีก '+dd+' วัน','in '+dd+' days')});}
  nextFest().forEach(function(x){L.push({href:'festivals/'+x.f.id+'.html',glyph:'🎊',big:x.dated&&x.dd>0?x.dd:'',t:bi(x.f.th,x.f.en),s:x.dated?(x.dd<=0?bi('กำลังจัด','on now'):bi('อีก '+x.dd+' วัน','in '+x.dd+' days')):x.dd===0?bi('เดือนนี้','this month'):bi('ราวเดือน '+['','ม.ค.','ก.พ.','มี.ค.','เม.ย.','พ.ค.','มิ.ย.','ก.ค.','ส.ค.','ก.ย.','ต.ค.','พ.ย.','ธ.ค.'][x.f.m[0]],'around '+['','Jan','Feb','Mar','Apr','May','Jun','Jul','Aug','Sep','Oct','Nov','Dec'][x.f.m[0]])});});
  document.getElementById('counters').innerHTML=L.slice(0,4).map(function(r){return '<li class="'+(r.cls||'')+'"><a href="'+esc(r.href)+'"'+(r.ext?' rel="noopener"':'')+'><span class="big">'+(r.big!==''&&r.big!=null?r.big:(r.glyph||''))+'</span><span class="lbl"><span class="t">'+r.t+'</span><small>'+(r.s||'')+'</small></span>'+(r.extra||'')+'</a></li>';}).join('');
  /* the top line */
  var t=document.getElementById('temp');t.innerHTML=wa.t!=null?Math.round(wa.t)+'°':'';var pm=document.getElementById('pm');pm.innerHTML=wa.pm!=null?'<b style="background:'+esc(wa.bc||'#ccc')+'">'+Math.round(wa.pm)+'</b>':'';pm.title=(wa.bt||'')+' · '+(wa.be||'')+' PM2.5';
  var w=document.getElementById('where');var c=D.cities.filter(function(x){return x.k===CITY;})[0];w.innerHTML=(FAR&&EDGE.city?esc(EDGE.city)+' → ':'')+bi(c.th,c.en);}

/* ---- today */
function moonSvg(illum,waxing){var r=10,cx=12,cy=12;var k=(illum==null?0.5:illum);var x=r*(1-2*k);var sweep=waxing?1:0;var d='M'+cx+' '+(cy-r)+'A'+r+' '+r+' 0 0 '+sweep+' '+cx+' '+(cy+r)+'A'+Math.abs(x)+' '+r+' 0 0 '+(k>0.5?sweep:1-sweep)+' '+cx+' '+(cy-r)+'Z';
  return '<svg viewBox="0 0 24 24" aria-hidden="true"><circle cx="12" cy="12" r="10" fill="none" stroke="rgba(255,255,255,.6)"/><path d="'+d+'" fill="#f6efe2"/></svg>';}
function today(){var a=null;for(var i=0;i<D.alm.length;i++)if(D.alm[i].d===T.iso){a=D.alm[i];break;}
  var col=document.getElementById('colour');var mo=document.getElementById('moon');
  if(!a){document.getElementById('daycard').hidden=true;col.hidden=true;mo.hidden=true;return;}
  var night=T.h>=18&&a.dt==='วันพุธ'&&a.nc;var hex=night?a.nc:a.c;
  col.style.color=hex;col.querySelector('i').style.background=hex;col.title=(night?a.nt:a.ct)+' · '+(night?a.ne:a.ce);col.setAttribute('aria-label',col.title);
  mo.innerHTML=moonSvg(a.mi,a.mw)+'<span class="th" lang="th">'+esc(a.mt||'')+'</span><span class="en" lang="en">'+esc(a.me||'')+'</span>';
  document.getElementById('daysum').innerHTML='<span class="sw" style="color:'+hex+';background:'+hex+'"></span><span class="head"><b>'+bi(a.dt,a.de)+'</b><small>'+bi((night?a.nt:a.ct)+' · '+(night?'พระราหู':a.pt),(night?a.ne:a.ce)+' · '+(night?'Rahu':a.pe))+(a.wp?' · '+bi('วันพระ','wan phra'):'')+'</small></span>';
  var rows=[];rows.push('<p><span class="k">'+bi('ปาง','Buddha')+'</span><span>'+bi(a.bt,a.be)+'</span></p>');
  rows.push('<p><span class="k">'+bi('จันทร์','Moon')+'</span><span>'+bi(a.mt||'',a.me||'')+'</span></p>');
  if(a.lk&&a.lk.length)rows.push('<p><span class="k">'+bi('เลข','Lucky')+'</span><span class="lk">'+a.lk.join(' · ')+'</span></p>');
  if(a.za)rows.push('<p><span class="k">'+esc(a.zp||'')+'</span><span>'+bi(a.zt||'',a.za+' — '+(a.ze||''))+'</span></p>');
  if(a.hn)rows.push('<p><span class="k">'+a.hn+' '+esc(a.hz||'')+'</span><span>'+esc(a.he||'')+'</span></p>');
  document.getElementById('daymore').innerHTML=rows.join('');}

/* ---- near: nine cells around the reader, only when they ask */
var NEAR=null;
function cellKey(la,ln){return Math.floor(la*100)+'_'+Math.floor(ln*100);}
function kinds(h){if(h<10)return ['food','wat','market','massage','medical'];if(h<15)return ['food','shopping','massage','wat','medical'];if(h<20)return ['food','market','massage','whats-on','medical'];return ['food','medical','essentials','whats-on','hotel'];}
function isOpen(hours){if(!hours||hours===0)return null;var w=T.wd*1440+T.min;for(var i=0;i<hours.length;i++)if(hours[i][0]<=w&&w<hours[i][1])return true;return false;}
var GL={'food':'🍜','wat':'🛕','market':'🏮','massage':'💆','medical':'🩺','shopping':'🛍','whats-on':'🎪','essentials':'🧺','hotel':'🛏'};
function showNear(lat,lon){var keys=[];for(var i=-1;i<=1;i++)for(var j=-1;j<=1;j++)keys.push(cellKey(lat+i*0.01,lon+j*0.01));
  Promise.all(keys.map(function(k){return fetch('data/here/'+k+'.json').then(function(r){return r.ok?r.json():[];}).catch(function(){return [];});})).then(function(all){
    var rows=[].concat.apply([],all).map(function(r){return {la:r[0],ln:r[1],p:r[2],slug:r[3],th:r[4],en:r[5],cat:r[6],rank:r[8],hours:r[9],d:km(lat,lon,r[0],r[1])};});
    rows.sort(function(a,b){return a.d-b.d;});var out=[],seen={};kinds(T.h).forEach(function(k){var best=null;for(var i=0;i<rows.length;i++){var r=rows[i];if(r.cat!==k||seen[r.slug])continue;var o=isOpen(r.hours);if(o===false)continue;if(!best||(o===true&&isOpen(best.hours)!==true))best=r;if(o===true)break;}if(best){seen[best.slug]=1;out.push([k,best]);}});
    document.getElementById('nearlist').innerHTML=out.map(function(x){var k=x[0],r=x[1];var o=isOpen(r.hours);return '<li><a href="'+r.p+'/p/'+esc(r.slug)+'.html"><span class="k">'+GL[k]+'</span><span class="lbl"><span>'+esc(r.th||r.en)+(r.en&&r.th?'<span class="en" lang="en"> '+esc(r.en)+'</span>':'')+'</span>'+(o===true?'<span class="open">'+bi('เปิดอยู่','open')+'</span>':'')+'</span><span class="d">'+(r.d<1?Math.round(r.d*1000)+' m':r.d.toFixed(1)+' km')+'</span></a></li>';}).join('')||'<li><a href="here.html">'+bi('ไม่พบในระยะ 1 กม. → ตรงนี้','Nothing within 1 km → Here')+'</a></li>';
    var m=document.querySelector('.near .doors a');if(m)m.href='map.html#'+lat.toFixed(4)+','+lon.toFixed(4);});}
document.getElementById('locate').addEventListener('click',function(){var b=this;if(!navigator.geolocation){b.hidden=true;return;}b.disabled=true;
  navigator.geolocation.getCurrentPosition(function(p){b.disabled=false;b.hidden=true;FIX={lat:p.coords.latitude,lon:p.coords.longitude};paint();showNear(p.coords.latitude,p.coords.longitude);},function(){b.disabled=false;},{maximumAge:60000,timeout:8000});});
try{if(navigator.permissions)navigator.permissions.query({name:'geolocation'}).then(function(s){if(s.state==='granted')document.getElementById('locate').click();});}catch(e){}

setCity(CITY,false);today();paint();setInterval(function(){render();today();},60000);
})();
"""


def main():
    out = DOCS / "index.html"
    out.write_text(render())
    print(f"{out} — {out.stat().st_size // 1024} KB")


if __name__ == "__main__":
    main()
