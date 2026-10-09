#!/usr/bin/env python3
"""home_next.py — the front page of motdang.net.

NaN, 2026-09-21: the 9/19 page is "a mouthful, and people struggle with
navigation because it doesn't flow"; then "github itself is a useful model for
discoverability of resources… like github but aesthetic, and include external
links as well as internal links"; then "the overall look should be exactly like
the minisites we already build, but it should contain motdang itself in a
discoverable way." On the result: "this looks perfect."

So: GitHub's structures — an About rail, topic chips, a repository-style index
of every shelf, pinned minisites, an outbound Elsewhere, and the harvesters'
own status — wearing the minisite stylesheet, vendored under assets/minisite/.

2026-09-24 (gemba — the one page people reach on their own): it answers before it
explains. Under the search, twelve needs as tiles that list the nearest few from the
reader's own position; the day as four tiles; the week folded to a few titles a day;
the index, the sources, the feeds and the roster closed at the foot.

THE STACK IS NEAR, THEN NOW, THEN SOON (NaN, same day). The only thing allowed
above it is a festival or event SHE calls out: set CALLOUT and it draws a band,
leave it None and nothing is drawn. Never fill it on my own judgement.
Besides that band, two one-line notices may sit there (NaN, 2026-09-26): rain in
the next hour, and the eve or day of a dated festival from festival_calendar.json.

The header carries the fleet search (motdang.net/find, live 2026-09-21), which
supersedes the 9/19 decision to keep the front page boxless.

    python3 home_next.py        # writes docs/index.html
    home_next.render()          # what build.py calls

Every number is read at build time from the file that owns it. Nothing here
fetches at load; the pictures are NaN's own frames already in docs/site/hero/.
"""
import collections
import datetime
import glob
import html
import json
import os
import pathlib
import sys

ROOT = pathlib.Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT))
import homebits  # noqa: E402
import shelflife  # noqa: E402
from homebits import icon  # noqa: E402
DATA = ROOT / "data"
DOCS = ROOT / "docs"
CSSDIR = ROOT / "assets" / "minisite"

BASE = "https://motdang.net/"
TODAY = datetime.date.today()

# THE STACK (NaN, 2026-09-21): near, then now, then soon. In that order, always.
# The one thing allowed above them is a called-out festival or event, and only when she
# says so — set CALLOUT to a dict and it draws a band over the whole stack.
#   CALLOUT = {"pic": "img/x.jpg", "kicker": "...", "head": "...", "line": "...",
#              "href": "...", "cta": "..."}
CALLOUT = None

# THE STRIP (NaN, 2026-09-28: "a thin page width banner with link up top" for the lantern
# festival). One line over the hero, full width, drawn until the day after `until`.
STRIP = {"until": "2026-11-25", "icon": "i-lantern",
         "th": "ยี่เป็ง – ลอยกระทง · 24–25 พ.ย.",
         "en": "Yi Peng & Loi Krathong · 24–25 Nov",
         "href": "https://motdang.net/festivals/yi-peng-loi-krathong.html"}


def strip_html():
    if not STRIP or TODAY.isoformat() > STRIP["until"]:
        return ""
    return (f'<a class="topstrip" href="{E(STRIP["href"])}">{icon(STRIP["icon"], 18)}'
            f'<span class="th" lang="th">{E(STRIP["th"])}</span> '
            f'<span class="en">{E(STRIP["en"])}</span> →</a>')


# THE SIGN (Nan, 2026-09-28: "a riff on the golden arches billions served… for bots. Should be
# featured prominently on the site."). One band under the hero, the count from data/served.json
# (served.py writes it each Monday), linking to /served/.
def served_band():
    try:
        d = json.loads((DATA / "served.json").read_text())
    except (OSError, ValueError):
        return ""
    m = int(d.get("millions", 0))
    if not m:
        return ""
    # Nan, 2026-09-28: "a little less flashy to humans … a little smaller and more
    # magical". Gold, not red, and a slow glint.
    arches = ('<svg viewBox="0 0 200 150" width="30" height="23" aria-hidden="true">'
              '<defs><linearGradient id="sgold" x1="0" x2="1"><stop offset="0" stop-color="#b8860b"/>'
              '<stop offset=".5" stop-color="#f6d77a"/><stop offset="1" stop-color="#b8860b"/></linearGradient></defs>'
              '<path d="M18 150 C18 -18 100 -18 100 150 M100 150 C100 -18 182 -18 182 150" fill="none" '
              'stroke="url(#sgold)" stroke-width="20"/></svg>')
    return (f'<a class="servedband" href="{BASE}served/">{arches}<span class="board">'
            f'<b>Over {m} million served</b>'
            f'<span class="th" lang="th">เสิร์ฟบอทไปแล้วกว่า {m} ล้านครั้ง</span></span>'
            f'<span class="for">บอท · for bots →</span></a>')


# The 1994 badge (Nan, 2026-09-28): the under-construction GIF, bottom of the page, into /roadworks/.
UNDER_CONSTRUCTION = (
    '<p class="uc"><a href="/roadworks/"><picture>'
    '<source srcset="/roadworks/construction@2x.png" media="(prefers-reduced-motion: reduce)">'
    '<img src="/roadworks/construction@2x.gif" width="88" height="31" alt="UNDER CONSTRUCTION" '
    'style="image-rendering:pixelated"></picture></a></p>')


def stats():
    """Every shelf, and what it holds. One pass over the two canonical files joined to
    the link-health sweep, cached against their mtimes because the pass costs ~40 s and
    the files change once a day."""
    import urllib.parse as up

    src = [DATA / "canonical/cm.json", DATA / "canonical/cr.json",
           DATA / "linkhealth.json", DATA / "categories.json"]
    stamp = [round(f.stat().st_mtime) if f.exists() else 0 for f in src]
    cache = ROOT / "cache" / "home_next_stats.json"
    if cache.exists():
        try:
            held = json.loads(cache.read_text())
            if held.get("stamp") == stamp:
                return held
        except (ValueError, KeyError):
            pass

    cats = {c["key"]: c for c in j("categories.json")["categories"]}
    lh = j("linkhealth.json")
    links, places = lh["links"], lh["places"]
    best = {}
    for url, rows in places.items():
        st = (links.get(url) or {}).get("status")
        for r in rows:
            pid = r["id"]
            if st == "ok":
                best[pid] = "ok"
            elif st == "social" and best.get(pid) != "ok":
                best[pid] = "social"
            else:
                best.setdefault(pid, st or "?")
    wl = j("wichaa_links.json")["links"]

    shelf = collections.defaultdict(collections.Counter)
    tot = {}
    for city in ("cm", "cr"):
        for r in j(f"canonical/{city}.json"):
            c = (r.get("cat") or [None])[0]
            tot[city] = tot.get(city, 0) + 1
            if c not in cats:
                continue
            sh = shelf[c]
            sh[city] += 1
            if r.get("lat"):
                sh["pin"] += 1
            if r.get("phone"):
                sh["tel"] += 1
            if r.get("hours"):
                sh["hrs"] += 1
            if r.get("website"):
                sh["web"] += 1
                st = best.get(r["id"])
                if st == "ok":
                    sh["live"] += 1
                elif st == "social":
                    sh["social"] += 1
            if r["id"] in wl:
                sh["wichaa"] += 1

    out = {
        "stamp": stamp,
        "totals": tot,
        "shelves": [{"key": k, "th": cats[k]["th"], "en": cats[k]["en"], **dict(shelf[k])}
                    for k in cats],
        "linkhealth": {
            "generated": lh["generated"],
            "urls": len(links),
            "ok": sum(1 for v in links.values() if v.get("status") == "ok"),
            "domains": len({up.urlsplit(u).netloc.lower().removeprefix("www.") for u in links}),
        },
        "wichaa": len(wl),
    }
    cache.parent.mkdir(exist_ok=True)
    cache.write_text(json.dumps(out, ensure_ascii=False))
    return out


def E(x):
    return html.escape("" if x is None else str(x), quote=True)


def j(p):
    return json.loads((DATA / p).read_text())


P = stats()
SHELVES = [s for s in P["shelves"] if s.get("cm", 0) + s.get("cr", 0) > 0]
SHELVES.sort(key=lambda s: -(s.get("cm", 0) + s.get("cr", 0)))
TOT = P["totals"]
ALL = TOT["cm"] + TOT["cr"]
LH = P["linkhealth"]
PINS = sum(s.get("pin", 0) for s in P["shelves"])
TELS = sum(s.get("tel", 0) for s in P["shelves"])
LIVE = sum(s.get("live", 0) for s in P["shelves"])

# The fleet search (motdang.net/find, live 2026-09-21) — its own crawl records the
# count, so the box can say what it holds without a number being typed in by hand.
_CRAWL = ROOT / "cache/fleetsearch/crawl.json"
FIND = json.loads(_CRAWL.read_text()) if _CRAWL.exists() else {}

_COUNTS = DATA / "amphoe_counts.json"
if _COUNTS.exists():
    AMPHOE_COUNTS = json.loads(_COUNTS.read_text())
else:
    import mapart  # noqa: E402
    AMPHOE_COUNTS = mapart.count_by_amphoe(mapart.Proj())
    _COUNTS.write_text(json.dumps(AMPHOE_COUNTS))

# WHAT THE SWEEP FOUND DEAD IS NOT LINKED. data/linkhealth.json carries a status per
# outbound URL; tests/test_publish_gate.py calls everything outside this set broken and
# holds the whole publish on it. An event whose newsletter gave a mangled address (the
# Drive link with "..." in it) still gets its row — it just does not get a link.
_ALIVE = {"ok", "social", "redirect-offsite", "walled"}
DEAD = {u.rstrip("/") for u, v in
        json.loads((DATA / "linkhealth.json").read_text())["links"].items()
        if v.get("status") not in _ALIVE}


def live(url):
    return bool(url) and url.rstrip("/") not in DEAD


AIR = j("air.json")
EVENTS = j("events.json")
SKY = j("sky.json")
FLEET = (json.loads((ROOT.parent / "index" / "data" / "fleet.json").read_text())
         if (ROOT.parent / "index" / "data" / "fleet.json").exists()
         else j("curated/fleet.json"))   # the roster's own copy first (see sites_layer.FLEET)

# ---- how fresh is the machine: every harvester writes a .meta.json
feeds, stale, failing = [], 0, 0
for p in sorted(glob.glob(str(DATA / "*.meta.json"))):
    m = json.loads(pathlib.Path(p).read_text())
    when = (m.get("last_success_at") or "")[:10]
    feeds.append((os.path.basename(p).replace(".meta.json", ""), when, m.get("row_count"),
                  m.get("consecutive_failures") or 0))
    if m.get("consecutive_failures"):
        failing += 1
    if when and (TODAY - datetime.date.fromisoformat(when)).days > 7:
        stale += 1

# ---- the minisites: sites_layer reads data/curated/sites.json (see pinned_cards)

SOURCES = [
    ("https://www.openstreetmap.org/copyright", "OpenStreetMap", "the pins, and much of the ground truth", "ODbL"),
    ("https://open-meteo.com/", "Open-Meteo Air Quality", "the PM2.5 model behind every dust figure", "CC BY 4.0"),
    ("https://podfoon.anamai.moph.go.th/", "กรมอนามัย · Dept. of Health", "the clean-room register, 2,428 rooms", "public"),
    # data.bopp-obec.info is where the register itself lives; it did not resolve from
    # here on 2026-09-21, so the credit points at the office instead.
    ("https://www.obec.go.th/", "สพฐ. · OBEC", "the school register", "public"),
]


# ---------------------------------------------------------------- pieces

def band(image, kicker="", head="", line="", big="", big_label="", cls="", tag="h2",
         href="", cta="", credit="", extra="", scene=""):
    """site-kit's four layers — photograph, scrim, tint, type — with the heading level
    left open so the hero can carry the page's h1."""
    inner = []
    if kicker:
        inner.append(f'<span class="kicker">{E(kicker)}</span>')
    if big:
        lab = f"<small>{E(big_label)}</small>" if big_label else ""
        inner.append(f'<p class="big">{E(big)}{lab}</p>')
    if head:
        inner.append(f"<{tag}>{head}</{tag}>")
    if line:
        inner.append(f"<p>{line}</p>")
    if href and cta:
        inner.append(f'<a class="btn" href="{E(href)}">{E(cta)}</a>')
    if extra:
        inner.append(extra)
    cred = f'<span class="cred">{credit}</span>' if credit else ""
    sc = f' data-scene="{E(scene)}"' if scene else ""
    return (f'<section class="band {E(cls)}"{sc} style="background-image:url({E(image)})">'
            f'<div class="in">{"".join(inner)}</div>{cred}</section>')


def bi(th, en):
    """Thai over English. Two lines, two weights — one label, not two."""
    return (f'<span class="bi"><span class="th" lang="th">{E(th)}</span>'
            f'<span class="en" lang="en">{E(en)}</span></span>')


def n(x):
    return f"{x:,}"


def chips():
    out = []
    for s in SHELVES:
        tot = s.get("cm", 0) + s.get("cr", 0)
        out.append(f'<a class="chip" href="{BASE}cm/{E(s["key"])}/" '
                   f'data-href="{BASE}{{c}}/{E(s["key"])}/">'
                   f'{icon(homebits.CAT_ICON[s["key"]], 20)}{bi(s["th"], s["en"])}'
                   f'<b>{n(tot)}</b></a>')
    return f'<div class="chips shelves">{"".join(out)}</div>'


def index_table():
    head = ("<thead><tr><th>ชั้น · Shelf</th><th class=r>records</th><th class=r>on the map</th>"
            "<th class=r>phone</th><th class=r>hours</th><th class=r>live site</th>"
            "<th class=r>wichaa</th></tr></thead>")
    rows = []
    for s in SHELVES:
        tot = s.get("cm", 0) + s.get("cr", 0)

        def pc(k):
            v = s.get(k, 0)
            if not v:
                return '<td class="r z">—</td>'
            return (f'<td class="r"><b>{n(v)}</b>'
                    f'<i>{round(100 * v / tot)}%</i></td>')
        wch = s.get("wichaa", 0)
        rows.append(
            f'<tr><td class="nm"><a href="{BASE}cm/{E(s["key"])}/" '
            f'data-href="{BASE}{{c}}/{E(s["key"])}/">'
            f'{icon(homebits.CAT_ICON[s["key"]], 18)}{bi(s["th"], s["en"])}</a></td>'
            f'<td class="r big">{n(tot)}</td>{pc("pin")}{pc("tel")}{pc("hrs")}{pc("live")}'
            + (f'<td class="r"><b>{n(wch)}</b></td>' if wch else '<td class="r z">—</td>')
            + "</tr>")
    return f'<div class="scroll"><table class="idx">{head}<tbody>{"".join(rows)}</tbody></table></div>'


def search_form(big=False):
    """The fleet search, motdang.net/find. NaN 2026-09-21: it supersedes every earlier
    answer about a box on the front page — and, the same day, the box was too small to
    use, so the page's own search is now the size of the thing it searches."""
    cls = "q big" if big else "q"
    return (f'<form class="{cls}" action="{BASE}find" method="get" role="search">'
            f'<label class="qbox">{icon("i-search", 26, "rowicon qi")}'
            f'<input type="search" name="q" aria-label="ค้นหา · search" '
            f'placeholder="ค้นหา · search"></label>'
            f'<button type="submit">{icon("i-search", 20)}'
            f'<span>ค้นหา · Search</span></button>'
            f'<button type="submit" name="lucky" value="1" class="alt">'
            f'{icon("i-dice", 20)}<span>ลองโชค · Lucky</span></button></form>')


# THE NEEDS a reader arrives with, the pressing ones first (gemba 2026-09-24: the front
# page is the one page humans reach on their own, so it answers before it explains).
# A tile with a match list answers from the reader's own position out of data/here/ —
# [shelf, sub] pairs, "" for the whole shelf. The two without one open a page that
# already answers from where the reader stands. With scripts off, or no position, a
# tile is a link to its shelf in the reader's province.
NEEDS = [
    ("toilet", "ห้องน้ำ", "Toilet", "i-loo", None, "toilets.html"),
    ("pharmacy", "ร้านยา", "Pharmacy", "i-pill", [["essentials", "pharmacy"]],
     "{c}/essentials/pharmacy/"),
    ("doctor", "หมอ", "Doctor", "i-health",
     [["medical", "clinic"], ["medical", "doctors"], ["medical", "hospital"]], "{c}/medical/"),
    ("help", "ช่วย", "Help", "i-sos", None, "chuai.html"),
    ("shop", "สะดวกซื้อ", "Mini-mart", "i-basket", [["essentials", "convenience"]],
     "{c}/essentials/convenience/"),
    ("bank", "ธนาคาร", "Bank", "i-bank", [["essentials", "bank"]], "{c}/essentials/bank/"),
    ("fuel", "ปั๊มน้ำมัน", "Fuel", "i-fuel", [["transport", "fuel"]], "{c}/transport/fuel/"),
    ("repair", "ซ่อมรถ", "Repair", "i-tools", [["repair", "auto"]], "{c}/repair/auto/"),
    ("food", "อาหาร", "Food", "i-food", [["food", ""]], "{c}/food/"),
    ("cafe", "กาแฟ", "Café", "i-coffee", [["food", "cafe"]], "{c}/food/cafe/"),
    ("massage", "นวด", "Massage", "i-spa", [["massage", ""]], "{c}/massage/"),
    ("stay", "ที่พัก", "Stay", "i-bed", [["hotel", ""]], "{c}/hotel/"),
    # The home-help board (motdang.net/home-help, its own Worker): people who
    # list themselves, and the shops. It sorts itself by the reader's position
    # on arrival with ?near=1. A thirteenth tile, so it spans the row (.wide).
    ("homehelp", "แม่บ้าน · คนสวน · ซักรีด · ช่าง", "Housekeepers · gardeners · laundry · handymen",
     "i-broom", None, "home-help/?near=1"),
]


def need_tiles():
    out = []
    for key, th, en, ic, match, href in NEEDS:
        if "{c}" in href:
            a = (f'<a class="need" data-k="{key}" href="{BASE}{E(href.replace("{c}", "cm"))}" '
                 f'data-href="{BASE}{E(href)}" data-need="{key}">')
        else:
            wide = " wide" if key == "homehelp" else ""
            a = f'<a class="need{wide}" data-k="{key}" href="{BASE}{E(href)}">'
        out.append(f'{a}{icon(ic, 30)}<span class="th" lang="th">{E(th)}</span>'
                   f'<span class="en" lang="en">{E(en)}</span></a>')
    return f'<nav class="needs" aria-label="ใกล้ฉัน · near me">{"".join(out)}</nav>'


def near_block():
    """NEAR — what the reader needs, answered from where they stand; then the map.
    The province pills are also the switch: the page's links follow whichever is on."""
    pills = "".join(
        f'<a class="pill" data-city="{k}" href="{BASE}{k}/">'
        f'<span class="th" lang="th">{E(th)}</span><span class="en" lang="en">{E(en)}</span>'
        f'<b>{n(TOT[k])}</b></a>'
        for k, th, en in (("cm", "เชียงใหม่", "Chiang Mai"), ("cr", "เชียงราย", "Chiang Rai")))
    # Server-side this says Chiang Mai, because that is what the page is if nothing
    # else is known. The script rewrites it from the edge, the reader's choice, or a tap.
    where = (f'<p class="wherenow" id="where">{icon("i-near", 18)}'
             f'<b>เชียงใหม่ · Chiang Mai</b>'
             f'<span class="src">ค่าเริ่มต้น · the default</span></p>')
    # THE READER'S OWN CHIP (NaN, 2026-09-21). The only thing in this row that is not
    # true for everybody, so it ships `hidden` and PLAN_CHIP_JS reveals it for a reader
    # who has a plan.
    doors = (f'<a class="btn alt" href="{BASE}here.html">{icon("i-here", 22)}'
             f'<span>ตรงนี้ · Here</span></a>'
             f'<a class="chip nnplan" href="{BASE}plan.html" hidden></a>')
    return (f'<div class="nearwrap"><div class="nearmain">'
            f'<div class="whererow">{where}<div class="pills">{pills}</div></div>'
            f'<div class="nearpics" id="nearpics" hidden></div>'
            f'{need_tiles()}'
            f'<button type="button" id="asknear" class="btn alt wide">{icon("i-here", 22)}'
            f'<span>แถวนี้มีอะไร · What is around me</span></button>'
            f'<ul class="nearlist" id="nearlist" hidden></ul>'
            f'</div><div class="nearmap">'
            f'{homebits.big_map(AMPHOE_COUNTS, "site/map/", DOCS / "site/map")}'
            f'<div class="maprow"><a class="btn" id="openmap" href="{BASE}map.html" '
            f'data-href="{BASE}map.html">{icon("i-map", 22)}'
            f'<span>แผนที่ · The live map</span></a>{doors}</div>'
            f'</div></div>')


# A plan lives in the reader's own browser and nowhere else, so no build can
# know whether there is one. Half a kilobyte inline rather than md.js: this
# page is deliberately script-free and a counter is not worth 290 KB on it.
# Reads one key, writes nothing, asks nothing, fetches nothing. With scripts
# off the chip stays hidden and the row is the row it always was.
PLAN_CHIP_JS = """<script>
(function(){var el=document.querySelector('.nnplan');if(!el)return;
function paint(){var n=0;
try{var v=JSON.parse(localStorage.getItem('md-plan'));n=Array.isArray(v)?v.length:0;}catch(e){}
el.hidden=!n;
el.innerHTML=n?'<svg class="rowicon" aria-hidden="true" width="18" height="18" viewBox="0 0 24 24"><use href="#i-map"></use></svg>'+
 'แผนของคุณ '+n+' จุด · your plan, '+n+(n>1?' stops':' stop'):'';}
paint();
window.addEventListener('storage',function(e){if(!e.key||e.key==='md-plan')paint();});
})();
</script>"""


# ---------------------------------------------------------------- the clock
# NaN, 2026-09-26, "I love all of these", to five things that answer from the
# reader's own day rather than the build's:
#   1. the page wears the day's colour (Wednesday night is Rahu's)
#   2. the need tiles reorder by the hour
#   3. SOON drops what is over today and counts down what is next
#   4. rain in the next hour puts one line at the top, with indoor shelves
#   5. the eve and the day of a festival put one line at the top, and a
#      no-alcohol day says so
# The build can be a day old by the time a reader arrives, so all five are
# decided in the reader's browser against the Bangkok clock, from data baked
# here. Nothing is fetched. With scripts off the page is the page it was.

# Thai day colours as surfaces: [fill, the ink that reads on it, Thai, English].
# Mon yellow, Tue pink, Thu orange and Fri sky take dark ink; the rest take white.
DAY_COLOURS = {
    0: ["#D6281F", "#ffffff", "สีแดง", "red"],
    1: ["#F5C400", "#17110c", "สีเหลือง", "yellow"],
    2: ["#F06BA8", "#17110c", "สีชมพู", "pink"],
    3: ["#13803F", "#ffffff", "สีเขียว", "green"],
    4: ["#F07F13", "#17110c", "สีส้ม", "orange"],
    5: ["#3FA9F5", "#17110c", "สีฟ้า", "sky blue"],
    6: ["#7B4FC0", "#ffffff", "สีม่วง", "purple"],
    "rahu": ["#4A4A4A", "#ffffff", "สีเทา", "grey"],
}

# The need tiles by the hour, Bangkok time. Keys are NEEDS keys; a key left out
# keeps its place after the named ones.
NEED_HOURS = [
    (5, 10, ["cafe", "food", "shop", "pharmacy", "toilet", "bank", "fuel"]),
    (10, 14, ["food", "cafe", "toilet", "pharmacy", "shop", "bank"]),
    (14, 17, ["cafe", "massage", "food", "toilet", "bank", "pharmacy"]),
    (17, 22, ["food", "massage", "shop", "pharmacy", "toilet", "fuel", "stay"]),
    (22, 29, ["help", "pharmacy", "shop", "doctor", "stay", "toilet", "fuel"]),
]

# The rain line (Nan, 2026-09-28: no shelf links; make it true). It reads ECMWF IFS
# hours (make_weather.py) through weather-north's two-year check of what those
# chances turned out to mean at CNX and CEI (data/curated/rain_calibration.json).
RAIN_CAL = ROOT / "data" / "curated" / "rain_calibration.json"
RAIN_NEAR_KM = 60        # the line is about the city, so it shows to a reader near it
RAIN_STALE_H = 12        # or one who chose it; a forecast older than this says nothing


def _dow(d):
    """Python's Monday=0 to the Thai week's Sunday=0."""
    return (d.weekday() + 1) % 7


def day_vars():
    """The build day's colour, for a reader with scripts off."""
    fill, ink = DAY_COLOURS[_dow(TODAY)][:2]
    return f":root{{--day:{fill};--day-ink:{ink}}}"


def magic_json():
    W = json.loads((DATA / "weather.json").read_text())
    wx, ct = {}, {}
    for c in W.get("cities", []):
        k = {"chiang-mai": "cm", "chiang-rai": "cr"}.get(c.get("id"))
        if k and c.get("hours_ifs"):
            wx[k] = c["hours_ifs"]
        if k:
            ct[k] = [c["lat"], c["lng"], c["th"], c["en"]]
    try:
        cal = json.loads(RAIN_CAL.read_text())["bins"]
    except (OSError, ValueError, KeyError):
        cal, wx = {}, {}
    fest = {f["id"]: f for f in json.loads((DATA / "festivals.json").read_text())["festivals"]}
    horizon = (TODAY - datetime.timedelta(days=2)).isoformat()
    eves = []
    for r in json.loads((DATA / "festival_calendar.json").read_text())["rows"]:
        f = fest.get(r.get("festival_id"))
        if not f or not r.get("date_start") or (r.get("date_end") or r["date_start"]) < horizon:
            continue
        o = f.get("observance") or {}
        eves.append({"s": r["date_start"], "e": r.get("date_end") or r["date_start"],
                     "th": f["name_th"], "en": f["name_en"].split(" — ")[0],
                     "dry": bool(o.get("dry_day")),
                     "href": f"{BASE}festivals/{f['id']}.html"})
    # The full moons (NaN, 2026-09-27): a moon that is also a festival day hangs its
    # link on that festival's line; any other full moon gets a line of its own.
    import fullmoon_layer
    for d, (pth, pen) in fullmoon_layer.full_moon_dates().items():
        if d < horizon:
            continue
        href = f"{BASE}full-moon/{d}/"
        same = [x for x in eves if x["s"] == d]
        for x in same:
            x["moon"] = href
        if not same:
            eves.append({"s": d, "e": d, "th": "วันเพ็ญ " + pth, "en": "Full moon, " + pen,
                         "dry": False, "href": href, "fm": True})
    eves.sort(key=lambda x: x["s"])
    return json.dumps({
        "built": TODAY.isoformat(),
        "colours": {str(k): v for k, v in DAY_COLOURS.items()},
        "hours": NEED_HOURS,
        "wx": wx,
        "eves": eves[:24],
        "ic": {"rain": icon("i-rain", 20), "party": icon("i-party", 20),
               "moon": icon("i-fullmoon", 20)},
        "cal": cal, "ct": ct, "fetched": W.get("fetched"),
        "near": RAIN_NEAR_KM, "stale": RAIN_STALE_H,
    }, ensure_ascii=False, separators=(",", ":")).replace("</", "<\\/")


MAGIC_JS = r"""<script>
(function(){
var el=document.getElementById('md-magic');if(!el)return;
var M;try{M=JSON.parse(el.textContent);}catch(e){return;}
function bkk(){var d=new Date(Date.now()+7*36e5);
 return {iso:d.toISOString().slice(0,10),h:d.getUTCHours(),dow:d.getUTCDay(),
  min:d.getUTCHours()*60+d.getUTCMinutes(),
  tmr:new Date(d.getTime()+864e5).toISOString().slice(0,10)};}
function esc(s){return String(s==null?'':s).replace(/[&<>"]/g,function(c){
 return {'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;'}[c];});}
function hm(t){var p=(t||'').split(':');return p.length<2?null:(+p[0])*60+(+p[1]);}
function city(){var on=document.querySelector('.pill.on[data-city]');
 return on?on.dataset.city:'cm';}

/* 1 · the day's colour */
function colour(N){var c=M.colours[(N.dow===3&&N.h>=18)?'rahu':String(N.dow)];if(!c)return;
 var r=document.documentElement.style;r.setProperty('--day',c[0]);r.setProperty('--day-ink',c[1]);}

/* 2 · the need tiles by the hour */
function needs(N){var nav=document.querySelector('nav.needs');if(!nav)return;
 var h=N.h<5?N.h+24:N.h,order=null;
 M.hours.forEach(function(b){if(h>=b[0]&&h<b[1])order=b[2];});if(!order)return;
 var tiles=[].slice.call(nav.querySelectorAll('a[data-k]'));
 var rank=function(a){var i=order.indexOf(a.dataset.k);return i<0?99:i;};
 tiles.map(function(a,i){return [rank(a),i,a];})
  .sort(function(x,y){return x[0]-y[0]||x[1]-y[1];})
  .forEach(function(x){nav.appendChild(x[2]);});}

/* 3 · SOON against the reader's clock */
function soon(N){var ul=document.querySelector('main ul.agenda');if(!ul)return;
 ul.querySelectorAll('li.ag[data-d]').forEach(function(li){
  var d=li.dataset.d;li.hidden=d<N.iso;
  li.classList.toggle('now',d===N.iso);
  var tag=li.querySelector('.tag'),w=d===N.iso?'วันนี้ · today':d===N.tmr?'พรุ่งนี้ · tomorrow':'';
  if(w&&!tag){tag=document.createElement('p');tag.className='tag';
   li.querySelector('.agb').insertBefore(tag,li.querySelector('.agb').firstChild);}
  if(tag){if(w)tag.textContent=w;else tag.remove();}});
 [].slice.call(ul.children).forEach(function(m){if(!m.classList.contains('agm'))return;
  var n=m.nextElementSibling,any=false;
  while(n&&!n.classList.contains('agm')){if(!n.hidden)any=true;n=n.nextElementSibling;}
  m.hidden=!any;});
 ul.hidden=!ul.querySelector('li.ag:not([hidden])');
 var today=ul.querySelector('li.ag[data-d="'+N.iso+'"]');if(!today)return;
 var next=null;
 today.querySelectorAll('li[data-s]').forEach(function(li){
  var s=hm(li.dataset.s),e=li.dataset.e?hm(li.dataset.e):s+120;
  if(e<=s)e=s+120;
  if(N.min>=e){li.hidden=true;return;}
  var b=document.createElement('span');b.className='when';
  if(N.min>=s){b.textContent='ตอนนี้ · on now';li.insertBefore(b,li.firstChild);}
  else if(!next||s<hm(next.dataset.s))next=li;});
 if(next){var m=hm(next.dataset.s)-N.min,t=m<60?m+' นาที · in '+m+' min':
   Math.floor(m/60)+' ชม. '+(m%60?m%60+' นาที ':'')+'· in '+Math.floor(m/60)+' h'+(m%60?' '+m%60+' min':'');
  var b=document.createElement('span');b.className='when next';b.textContent='อีก '+t;
  next.insertBefore(b,next.firstChild);}
 /* keep the first few titles showing: pull from the "+N" fold what the clock took away */
 var top=today.querySelector('.agb>ul.ev');if(!top)return;
 var more=top.querySelector(':scope>li.more');if(!more)return;
 var shown=[].filter.call(top.children,function(li){return li!==more&&!li.hidden;}).length;
 var inner=more.querySelector('ul.ev'),want=6;
 [].slice.call(inner.children).forEach(function(li){
  if(li.hidden)return;if(shown<want){top.insertBefore(li,more);shown++;}});
 /* and the next one is never behind the fold */
 if(next&&inner.contains(next)){top.insertBefore(next,more);
  var vis=[].filter.call(top.children,function(li){return li!==more&&li!==next&&!li.hidden&&!li.querySelector('.when');});
  if(shown>=want&&vis.length){inner.insertBefore(vis[vis.length-1],inner.firstChild);}}
 var left=[].filter.call(inner.children,function(li){return !li.hidden;}).length;
 if(!left)more.hidden=true;else more.querySelector('summary').textContent='+'+left;}

/* the rain line has to be true for the reader who reads it: about the city they are
   near or chose, from a forecast fetched in the last few hours, in odds that two
   years of airport reports say that forecast actually earns (weather-north) */
function km(a,b,c,d){var R=6371,x=(c-a)*Math.PI/180,y=(d-b)*Math.PI/180;
 var s=Math.sin(x/2)*Math.sin(x/2)+Math.cos(a*Math.PI/180)*Math.cos(c*Math.PI/180)*Math.sin(y/2)*Math.sin(y/2);
 return 2*R*Math.asin(Math.sqrt(s));}
function forReader(c){
 var chose=null;try{chose=localStorage.getItem('md-city');}catch(e){}
 if(chose===c)return true;
 var m=((document.querySelector('meta[name=md-where]')||{}).content||'').split('|');
 if(m.length<3||!+m[1])return true;          /* nothing known: the line names its city */
 var C=M.ct[c];return !!C&&km(+m[1],+m[2],C[0],C[1])<=M.near;}
function rainChance(c,N){
 if(!M.fetched||Date.now()-Date.parse(M.fetched)>M.stale*36e5)return null;
 var H=M.wx[c]||[],B=M.cal[c]||[],key=N.iso+'T'+(N.h<10?'0':'')+N.h+':00',i=-1;
 if(!H.length||!B.length||!forReader(c))return null;
 for(var j=0;j<H.length;j++)if(H[j][0]===key){i=j;break;}
 if(i<0)return null;
 var best=0;H.slice(i,i+2).forEach(function(r){var p=r[1]||0,f=0;
  B.forEach(function(b){if(p>=b[0])f=b[1];});if(f>best)best=f;});
 return best;}

/* 4 + 5 · the lines at the top */
function lines(N){var box=document.getElementById('magic');if(!box)return;var out=[];
 M.eves.forEach(function(f){var on=f.s<=N.iso&&N.iso<=f.e,eve=f.s===N.tmr;
  if(!on&&!eve)return;
  out.push('<p class="mline fest">'+(f.fm?M.ic.moon:M.ic.party)+'<span><b>'+(on?'วันนี้ · Today':'พรุ่งนี้ · Tomorrow')+
   '</b> <a href="'+esc(f.href)+'">'+esc(f.th)+' · '+esc(f.en)+'</a>'+
   (f.moon?' <a href="'+esc(f.moon)+'">วันเพ็ญที่วัด · full moon at the wat</a>':'')+
   (f.dry?'<b class="dry">ห้ามขายเหล้าเบียร์ · no alcohol sales</b>':'')+'</span></p>');});
 var c=city(),ch=rainChance(c,N);
 if(ch!=null&&ch>=0.3){var C=M.ct[c],n=Math.round(ch*10);
  out.push('<p class="mline rain">'+M.ic.rain+'<span><b>'+(ch>=0.5?
   'ฝนน่าจะตกที่'+esc(C[2])+'ในชั่วโมงนี้ · Rain likely in '+esc(C[3])+' within the hour':
   'อาจมีฝนที่'+esc(C[2])+'ในชั่วโมงนี้ · Rain possible in '+esc(C[3])+' within the hour')+
   '</b> <span class="odds">ประมาณ '+n+' ใน 10 · about '+n+' in 10</span></span></p>');}
 box.innerHTML=out.join('');box.hidden=!out.length;
 window.MDRAINCH=ch;if(window.MDASK)window.MDASK();}

function paint(){var N=bkk();colour(N);needs(N);soon(N);lines(N);}
paint();
document.querySelectorAll('.pill[data-city]').forEach(function(p){
 p.addEventListener('click',function(){setTimeout(function(){lines(bkk());},0);});});
setInterval(function(){var N=bkk();colour(N);needs(N);lines(N);},6e4);
})();
</script>"""

MAGIC_CSS = """
/* ---- the day's colour (NaN, 2026-09-26) — surfaces only: links keep --hot,
   which is tuned for text on both grounds, and --day never carries body text. */
header.top{box-shadow:0 4px 0 var(--day)}
main>h2{border-bottom-color:var(--day);border-bottom-width:4px}
.btn:not(.alt),form.q button:not(.alt){background:var(--day);color:var(--day-ink)}
.btn:not(.alt):hover{color:var(--day-ink)}
.btn:not(.alt) .rowicon,form.q button:not(.alt) .rowicon{color:var(--day-ink)}
li.ag.now{background:color-mix(in srgb,var(--day) 12%,transparent);
 box-shadow:inset 4px 0 0 var(--day)}
a.pill.on{border-color:var(--day);box-shadow:3px 3px 0 var(--day)}
/* ---- the lines at the top: rain, a festival's eve */
.magic{margin:1.2rem 0 0;display:grid;gap:.5rem}
.magic[hidden]{display:none}
.mline{display:flex;gap:.6rem;align-items:flex-start;margin:0;padding:.7rem .9rem;
 border:2px solid var(--ink);border-left:8px solid var(--day);background:var(--panel);
 font-size:1rem;line-height:1.5}
.mline>.rowicon{flex:0 0 auto;margin-top:.15rem}
.mline a{display:inline-flex;align-items:center;gap:.25rem;margin-right:.6rem;font-weight:700}
.mline .odds{display:block;font-size:.85rem;color:var(--mute)}
.mline .dry{display:block}
/* the number and its name flow as one line of text, so a wrap never strands a label */
.tile.sos .sub{display:block}
/* ---- SOON against the clock */
ul.ev .when{display:inline-block;margin-right:.4rem;padding:0 .35rem;border-radius:99px;
 font-family:var(--display);font-size:.7rem;font-weight:800;letter-spacing:.04em;
 background:var(--chip);color:var(--ink);border:1px solid var(--line)}
ul.ev .when.next{background:var(--day);color:var(--day-ink);border-color:var(--day)}
.agb .fmday{margin:.1rem 0 .2rem;font-size:.82rem}
.agb .fmday a,.day .fmday a{font-weight:700;text-decoration:none}
.agb .fmday .rowicon,.day .fmday .rowicon{color:var(--sun);vertical-align:-.2em}
ul.ev li[hidden],li.ag[hidden],li.agm[hidden],li.more[hidden],ul.agenda[hidden]{display:none}
"""


def soon_rows(k=7):
    """SOON — dated things, nearest first, each with the source that announced it.
    The de-duplication lives in homebits, where the calendar reads it too."""
    rows = []

    def away(d):
        n_ = (datetime.date.fromisoformat(d) - TODAY).days
        return "today" if not n_ else f"+{n_}d"

    _, _, byday = homebits._cal_data()
    flat = [(d, e) for d, evs in byday.items() if d >= TODAY.isoformat() for e in evs]
    for d, e in sorted(flat, key=lambda r: (r[0], (r[1].get("title") or "")))[:k]:
        t = (e.get("title") or "").strip()
        title = E(t if len(t) < 84 else t[:81] + "…")
        if live(e.get("url")):
            title = (f'<a href="{E(e["url"])}" rel="noopener">{title}'
                     f'<span class="out">{icon("i-arrow", 13)}</span></a>')
        rows.append((d, "", f'<tr><td class="mono">{E(d)}</td>'
                            f'<td class="r away">{away(d)}</td><td>{title}</td></tr>'))
    wp = next_wan_phra()
    if wp:
        d, label = wp
        rows.append((d, "a", f'<tr class="alm"><td class="mono">{E(d)}</td>'
                             f'<td class="r away">{away(d)}</td>'
                             f'<td>วันพระ · wan phra, {E(label)}</td></tr>'))
    rows.sort(key=lambda r: (r[0], r[1]))
    return ('<div class="scroll"><table class="idx soon"><thead><tr><th>date</th>'
            '<th class="r">away</th><th>what</th></tr></thead>'
            f'<tbody>{"".join(r[2] for r in rows)}</tbody></table></div>')


def next_wan_phra():
    days = SKY["days"]
    for i in range(1, 32):
        d = (TODAY + datetime.timedelta(days=i)).isoformat()
        m = (days.get(d) or {}).get("moon") or {}
        if m.get("wan_phra"):
            return d, m.get("thai_label_th") or ""
    return None


def obs_layer_ask():
    import obs_layer
    return obs_layer.ask_block(icon)


def now_tiles():
    """NOW — the dust in both cities, the day, and the number to call. Four tiles,
    each one a door: the dust opens the fourteen days behind it, the day opens the
    horoscope, and every number dials."""
    out = []
    for p in AIR["places"][:2]:
        b = p["band"]
        k = "cm" if p["id"] == "chiang-mai" else "cr" if p["id"] == "chiang-rai" else ""
        out.append(shelflife.guard("air", AIR.get("generated"),
                   f'<a class="tile" href="{BASE}foon.html" data-air="{k}">'
                   f'<span class="lab">{icon("i-air", 16)}ฝุ่น · {E(p["en"])}</span>'
                   f'<b style="--c:{E(b["colour"])}">{p["pm25"]:g}</b>'
                   f'<span class="sub">PM2.5 · {E(b["th"])} · {E(b["en"])}</span></a>'))
    F, S = homebits._cal_data()[:2]
    t = (F.get(TODAY.isoformat()) or {}).get("thai") or {}
    m = (S.get(TODAY.isoformat()) or {}).get("moon") or {}
    dot = (f'<span class="col" style="--c:{E(t["hex"])}"></span>{E(t.get("colour_th", ""))}'
           if t.get("hex") else "")
    lun = (f'{homebits.moon(m.get("illum"), m.get("waxing"), 8)}'
           f'{"วันพระ " if m.get("wan_phra") else ""}{E(m.get("thai_label_th", ""))}'
           if m else "")
    out.append(f'<a class="tile" href="{BASE}horoscope.html">'
               f'<span class="lab">{icon("i-cal", 16)}วันนี้ · Today</span>'
               f'<b>{TODAY.day}</b>'
               f'<span class="sub">{E(homebits.TH_MONTH[TODAY.month])} {TODAY.year + 543} · '
               f'{E(TODAY.strftime("%a %b"))}</span>'
               f'<span class="sub">{dot} {lun}</span></a>')
    # One number to a line (NaN, 2026-09-26): run together, the wrap left
    # "ดับเพลิง · 1155" on a line of its own, which reads as fire = 1155.
    out.append(f'<div class="tile sos"><span class="lab">{icon("i-sos", 16)}ฉุกเฉิน · Emergency</span>'
               f'<b><a href="tel:1669">1669</a></b>'
               f'<span class="sub">รถพยาบาล · ambulance</span>'
               f'<span class="sub"><a href="tel:191">191</a> ตำรวจ · police</span>'
               f'<span class="sub"><a href="tel:199">199</a> ดับเพลิง · fire</span>'
               f'<span class="sub"><a href="tel:1155">1155</a> ตำรวจท่องเที่ยว</span>'
               f'</div>')
    import obs_layer  # Nan 2026-09-28: flood while a gauge is over its level
    return (f'<div class="tiles" id="aircards">{"".join(out)}</div>'
            + obs_layer.flood_block(auto=True))


# the ones the page already opens from a tile or a button further up
ABOVE = {"festivals.html", "horoscope.html", "foon.html", "toilets.html", "chuai.html"}


def pinned_cards():
    """The six from the register (sites_layer.best): Nan's picks, the newest, the most
    read. The row stays six long however many sites there are; the rest are one tap
    away on /sites/."""
    import sites_layer
    grid = sites_layer.front_cards(icon, BASE, TODAY, 6, skip=ABOVE,
                                   docs=DOCS if DOCS.is_dir() else None)
    n_all = sites_layer.count()
    return (grid + f'<p class="calmore"><a class="btn" href="{BASE}sites/">'
            f'{icon("i-grid", 20)}ทุกเว็บ · All {n_all} sites →</a></p>')


def roster_rows():
    out = []
    for s in FLEET["sites"]:
        if s["id"] == "motdang":
            continue
        th = f' <span class="th" lang="th">{E(s["th"])}</span>' if s.get("th") else ""
        out.append(f'<li><a href="{E(s["url"])}" rel="noopener">{E(s["name"])}</a>{th}'
                   f'<span class="note">{E(s.get("note", ""))}</span></li>')
    return f'<ul class="links">{"".join(out)}</ul>'


def source_rows():
    out = []
    for url, name, what, lic in SOURCES:
        out.append(f'<li><a href="{E(url)}" rel="noopener">{E(name)}</a>'
                   f'<span class="note">{E(what)} · {E(lic)}</span></li>')
    return f'<ul class="links">{"".join(out)}</ul>'


def feed_rows():
    rows = []
    for name, when, count, fails in sorted(feeds, key=lambda r: r[1], reverse=True):
        if fails:
            continue
        rows.append(f'<tr><td>{E(name)}</td><td class="r">{n(count or 0)}</td>'
                    f'<td class="r mono">{E(when)}</td></tr>')
    return ('<div class="scroll"><table class="idx feeds"><thead><tr><th>feed</th>'
            '<th class=r>rows</th><th class=r>updated</th></tr></thead>'
            f'<tbody>{"".join(rows)}</tbody></table></div>')


EXTRA = """
.topstrip{display:flex;justify-content:center;align-items:center;flex-wrap:wrap;gap:.2rem .5rem;
 background:var(--ink);color:var(--bg);padding:.4rem 1rem;font-size:.86rem;font-weight:700;
 text-decoration:none;text-align:center;line-height:1.3}
.topstrip svg{color:var(--sun);flex:none}
.topstrip+main{margin-top:0}
.topstrip .th,.topstrip .en{color:inherit}
.topstrip:hover,.topstrip:focus-visible{background:var(--hot);color:#fff}
.servedband{display:flex;align-items:center;justify-content:center;gap:.5rem;flex-wrap:wrap;
 margin:.6rem auto .2rem;padding:.3rem .8rem;max-width:max-content;background:transparent;
 border:0;border-bottom:1px dashed #c9a13b;text-decoration:none;color:var(--mute);opacity:.88}
.servedband svg{flex:none;filter:drop-shadow(0 0 3px rgba(246,215,122,.55))}
.servedband .board{display:flex;flex-direction:column;align-items:center;line-height:1.15;text-align:center}
.servedband b{font-family:var(--display);text-transform:uppercase;letter-spacing:.08em;font-size:.8rem;font-weight:600}
.servedband .th{font-size:.72rem}
.servedband .for{font-size:.7rem;color:#9a7412}
.servedband:hover,.servedband:focus-visible{opacity:1;color:var(--ink)}
@media (prefers-reduced-motion:no-preference){
 .servedband svg{animation:sglint 6s ease-in-out infinite}
 @keyframes sglint{0%,100%{filter:drop-shadow(0 0 2px rgba(246,215,122,.35))}50%{filter:drop-shadow(0 0 7px rgba(246,215,122,.9))}}}
.uc{text-align:center;margin:1.4rem 0 .8rem}
.uc img{width:106px;height:37px;opacity:.82;border-radius:3px;filter:saturate(.85);
 transition:opacity .4s,filter .4s}
.uc a:hover img,.uc a:focus-visible img{opacity:1;filter:saturate(1) drop-shadow(0 0 6px rgba(246,215,122,.8))}
.band h1{font-family:var(--display);font-size:clamp(2.1rem,6.6vw,3.9rem);line-height:.98;
 margin:0 0 .5rem;border:0;color:#fff;text-transform:uppercase;letter-spacing:-.01em;
 text-shadow:0 2px 26px rgba(0,0,0,.6);max-width:22ch}
.band h1 .en{color:#fff}
.band .th,.band .en{color:inherit}
/* ---- additions for the front page: the About rail, the chips, the index */
.pin h3 .newtag{font-size:.62rem;letter-spacing:.05em;background:var(--hot);color:#fff;
 padding:.05rem .35rem;margin-left:.4rem;vertical-align:middle;font-family:var(--display)}
.rail{display:grid;grid-template-columns:1fr 20rem;gap:1.6rem;align-items:start;margin:1.4rem 0}
@media(max-width:52rem){.rail{grid-template-columns:1fr}}
.about{border:2px solid var(--line);background:var(--panel);padding:.9rem 1rem}
.about h3{margin:0 0 .5rem}
.about dl{margin:0;display:grid;grid-template-columns:1fr auto;gap:.28rem .6rem;font-size:.86rem}
.about dt{color:var(--mute)}
.about dd{margin:0;text-align:right;font-family:var(--display);font-size:1.02rem;font-weight:800}
.about .btns{margin:.9rem 0 .2rem;gap:.4rem}
.about .btn{font-size:.82rem;padding:.3rem .6rem}
.bi{display:inline-flex;flex-direction:column;line-height:1.15}
.bi .th{font-family:var(--thai);font-size:.98em}
.bi .en{font-size:.72em;letter-spacing:.04em;text-transform:uppercase;color:var(--mute);font-weight:700}
.chips{display:flex;flex-wrap:wrap;gap:.4rem;margin:1rem 0 1.6rem}
.chip{display:inline-flex;align-items:center;gap:.45rem;border:2px solid var(--line);
 background:var(--chip);padding:.3rem .55rem;text-decoration:none;color:var(--ink)}
.chip:hover{border-color:var(--hot);color:var(--ink);background:var(--panel)}
/* .chip sets display, which beats the browser's own [hidden] rule — without this the
   reader's plan chip draws as an empty box for everybody who has no plan. */
.chip[hidden]{display:none}
.chip b{font-family:var(--mono);font-size:.78rem;color:var(--mute)}
.chip:hover b{color:var(--hot)}
.scroll{overflow-x:auto;-webkit-overflow-scrolling:touch;margin:1rem 0 2rem;
 border:2px solid var(--line)}
/* The table already scrolls sideways inside its own box, so a shelf name has no
   reason to break across three lines on a phone — it made every row four deep. */
table.idx td.nm .bi span{white-space:nowrap}
table.idx{width:100%;border-collapse:collapse;font-size:.88rem;background:var(--panel)}
table.idx th{text-align:left;font-size:.64rem;letter-spacing:.12em;text-transform:uppercase;
 color:var(--mute);border-bottom:2px solid var(--ink);padding:.5rem .6rem;white-space:nowrap;
 position:sticky;top:0;background:var(--panel)}
table.idx td{border-bottom:1px solid var(--line);padding:.42rem .6rem;vertical-align:middle}
table.idx td.r,table.idx th.r{text-align:right}
table.idx td.nm a{text-decoration:none;color:var(--ink)}
table.idx td.nm a:hover{color:var(--hot)}
table.idx td.big{font-family:var(--display);font-size:1.16rem;font-weight:800}
table.idx td i{display:block;font-style:normal;font-size:.62rem;color:var(--mute);font-family:var(--mono)}
table.idx td.z{color:var(--line)}
table.idx tr:hover td{background:color-mix(in srgb,var(--sun) 10%,transparent)}
table.idx tr.bad td:last-child{color:var(--hot);font-weight:800}
table.feeds{font-size:.8rem}
.mono{font-family:var(--mono);font-size:.78rem}
/* THE SEARCH (NaN, 2026-09-21: "search bar way too small"). The header box is now
   a 24 rem field with 18 px type, and the hero carries the same form at poster size,
   because the box is the front door to 105,000 pages. */
form.q{display:flex;gap:.4rem;flex:1 1 24rem;min-width:0;margin:0;align-items:stretch;
 flex-wrap:wrap}
.qbox{display:flex;align-items:center;gap:.5rem;flex:1 1 15rem;min-width:0;
 border:2px solid var(--line);background:var(--panel);padding:0 .6rem}
.qbox:focus-within{border-color:var(--ink);box-shadow:2px 2px 0 var(--ink)}
.qbox .qi{color:var(--mute);flex:0 0 auto}
form.q input[type=search]{flex:1 1 auto;min-width:0;font:inherit;font-size:1rem;
 padding:.5rem 0;border:0;background:transparent;color:var(--ink);
 border-radius:0;-webkit-appearance:none}
form.q input[type=search]:focus{outline:0}
form.q button{display:inline-flex;align-items:center;gap:.4rem;font-family:var(--display);
 font-size:.86rem;font-weight:800;letter-spacing:.06em;
 text-transform:uppercase;padding:.42rem .8rem;border:2px solid var(--ink);background:var(--hot);
 color:#fff;cursor:pointer;white-space:nowrap}
form.q button.alt{background:var(--bg);color:var(--ink)}
form.q button:hover{box-shadow:2px 2px 0 var(--ink)}
.band form.q.big{max-width:48rem;margin:1.5rem 0 0;gap:.5rem}
.q.big .qbox{flex:1 1 20rem;padding:0 .9rem;border:3px solid #fff;
 background:rgba(253,251,244,.97);box-shadow:0 6px 30px rgba(0,0,0,.35)}
.q.big .qbox .qi{color:var(--road)}
.q.big input[type=search]{font-size:clamp(1.1rem,2.6vw,1.5rem);padding:.72rem 0;color:#17110c}
.q.big button{font-size:1rem;padding:.6rem 1.1rem;border-width:3px}
.q.big .qhint{flex:1 0 100%;margin:.6rem 0 0;max-width:46rem;font:500 .94rem/1.5 var(--body);
 letter-spacing:0;text-transform:none}
@media(max-width:52rem){
 form.q{order:3;flex:1 0 100%;margin:.4rem 0 .1rem}
 form.q button.alt{display:none}
 .q.big button.alt{display:inline-flex}
}

/* ---- the marks. One sprite, subset into the page; never an emoji. */
.rowicon{fill:none;stroke:currentColor;stroke-width:1.6;stroke-linecap:round;
 stroke-linejoin:round;flex:0 0 auto}
header.top nav a{display:inline-flex;align-items:center;gap:.3rem}
header.top nav .rowicon{color:var(--mute)}
header.top nav a:hover .rowicon{color:var(--hot)}
.chip .rowicon{color:var(--mute)}
.chip:hover .rowicon{color:var(--hot)}
.card h3{display:flex;align-items:center;gap:.45rem}
.card.pin h3 .rowicon{color:var(--hot)}
table.idx td.nm a{display:inline-flex;align-items:center;gap:.45rem}
table.idx td.nm .rowicon{color:var(--mute)}
table.idx tr:hover td.nm .rowicon{color:var(--hot)}
.out{display:inline-flex;vertical-align:-.16em;color:var(--mute);margin-left:.2rem}
.out .rowicon{transform:rotate(-45deg)}
table.idx tr.bad td:last-child .rowicon{color:var(--hot)}

/* ---- THE MAP. Full bleed, and the picture is the size of the thing it draws. */
.mapband{margin-left:calc(50% - 50vw);margin-right:calc(50% - 50vw);width:100vw;
 background:var(--chip);border-top:3px solid var(--ink);border-bottom:3px solid var(--ink);
 padding:clamp(1.1rem,3.4vw,2.4rem) 1rem;margin-block:1.4rem 2.2rem}
.mapband>.in{max-width:84rem;margin:0 auto;display:grid;
 grid-template-columns:auto minmax(16rem,21rem);gap:clamp(1rem,3vw,2.4rem);
 align-items:start;justify-content:center}
figure.bigmap{margin:0;min-width:0}
.bigmap .plate{position:relative;height:min(88vh,58rem);width:auto;margin:0 auto;
 background:var(--panel);border:3px solid var(--ink);box-shadow:7px 7px 0 var(--line)}
.bigmap .plate img{position:absolute;inset:0;width:100%;height:100%;display:block;
 object-fit:contain}
.bigmap .over{position:absolute;inset:0;width:100%;height:100%}
.amps path{fill:color-mix(in srgb,var(--sun) 7%,transparent);
 stroke:color-mix(in srgb,var(--ink) 26%,transparent);
 stroke-width:1.2;
 vector-effect:non-scaling-stroke}
.amps a:hover path,.amps a:focus-visible path{
 fill:color-mix(in srgb,var(--hot) 13%,transparent);stroke:var(--ink);stroke-width:2.6}
.city circle{fill:none;stroke:var(--hot);stroke-width:3;vector-effect:non-scaling-stroke}
.city .dot{fill:var(--hot)}
.city text{paint-order:stroke;stroke:var(--bg);stroke-width:7px;stroke-linejoin:round;
 fill:var(--ink);font-weight:800}
.city .cth{font-family:var(--thai);font-size:40px}
.city .cen{font-family:var(--display);font-size:30px;letter-spacing:.06em;
 text-transform:uppercase;fill:var(--mute)}
.bigmap figcaption{display:flex;align-items:center;gap:.4rem;flex-wrap:wrap;
 margin:.6rem auto 0;font-size:.78rem;color:var(--mute);max-width:40rem}
.bigmap figcaption .rowicon{color:var(--hot)}
.bigmap figcaption .src{flex:1 0 100%;font-size:.64rem;line-height:1.4}
.maprail{display:flex;flex-direction:column;gap:.8rem;min-width:0}
.maprail .twocards{gap:.6rem}
.maprail .chips{margin:.2rem 0 0}
.btn.wide{display:flex;align-items:center;justify-content:center;gap:.5rem;width:100%;
 text-align:center}
@media(max-width:60rem){
 .mapband>.in{grid-template-columns:1fr}
 .bigmap .plate{height:auto;width:100%}
}

/* ---- THE CALENDAR. Two months, and every square carries the day it is. */
/* one month per row: at 68 rem that is a 170 px column, which is the width an
   event title needs. Two months side by side put it at 50 px and shredded them. */
.cals{display:grid;gap:1.4rem;margin:1rem 0 2rem}
.month h3{display:flex;align-items:baseline;gap:.5rem;margin:0 0 .4rem;
 font-family:var(--display);text-transform:uppercase;letter-spacing:.02em}
.month h3 .en{font-size:.8em;color:var(--mute)}
.month h3 .be{margin-left:auto;font-family:var(--mono);font-size:.62rem;color:var(--mute);
 text-transform:none;letter-spacing:0}
.cal{border:2px solid var(--ink);background:var(--panel)}
.wds,.days{display:grid;grid-template-columns:repeat(7,1fr)}
.wd{padding:.26rem .15rem;text-align:center;border-bottom:2px solid var(--ink);
 font-size:.56rem;letter-spacing:.1em;text-transform:uppercase;color:var(--mute)}
.wd .th{display:block;font-size:.82rem;color:var(--ink);font-weight:700}
.days{grid-auto-rows:minmax(8.4rem,auto)}
.day{padding:.34rem .4rem;font-size:.74rem;min-width:0;
 border-right:1px solid var(--line);border-bottom:1px solid var(--line)}
.days>.day:nth-child(7n){border-right:0}
.day.oth{background:color-mix(in srgb,var(--chip) 60%,transparent);opacity:.45}
.day.past{opacity:.6}
.day.phra{background:color-mix(in srgb,var(--sun) 13%,transparent)}
.day.now{outline:3px solid var(--hot);outline-offset:-3px;
 background:color-mix(in srgb,var(--hot) 8%,transparent);opacity:1}
.day .hd{display:flex;align-items:center;gap:.28rem}
.day .hd b{font-family:var(--display);font-size:1.2rem;line-height:1}
.day .col{width:.66rem;height:.66rem;border-radius:50%;background:var(--c);
 border:1px solid rgba(0,0,0,.28);flex:0 0 auto}
.day .moon{margin-left:auto;flex:0 0 auto}
.moon .dark{fill:color-mix(in srgb,var(--road) 78%,var(--panel))}
.moon .lit{fill:#f6e6b4}
.moon .rim{fill:none;stroke:color-mix(in srgb,var(--ink) 35%,transparent);stroke-width:1}
.day .lun{margin:.16rem 0 0;font-size:.6rem;line-height:1.3;color:var(--mute)}
.day .lun .rowicon{color:var(--sun);vertical-align:-.2em;margin-right:.1rem}
.day.phra .lun{color:var(--ink)}
.day ul.ev{list-style:none;margin:.24rem 0 0;padding:0;font-size:.64rem;line-height:1.3}
.day ul.ev li{border-top:1px solid var(--line);padding:.14rem 0}
.day ul.ev a{text-decoration:none;box-shadow:inset 0 -1px 0 var(--chip)}
.day ul.ev a:hover{box-shadow:inset 0 -1px 0 var(--hot)}
.day ul.ev .more{color:var(--mute);font-family:var(--mono);font-size:.56rem}
.day .tag{margin:.18rem 0 0;font-family:var(--display);font-weight:800;font-size:.6rem;
 letter-spacing:.1em;text-transform:uppercase;color:var(--hot)}
@media (prefers-color-scheme:dark){:root:not([data-theme="light"]) .moon .lit{fill:var(--sun)}}
:root[data-theme="dark"] .moon .lit{fill:var(--sun)}
/* ---- SEVEN DAYS, DOWN THE PAGE (NaN, 2026-09-22: the calendar "doesn't fully
   render contents — everything gets cut off", and the front page should carry the
   next seven days with the longer views one click away). The grid is the wide
   drawing; the agenda is the same days in a shape a phone can finish. */
ul.agenda{list-style:none;margin:.8rem 0 1.2rem;padding:0;
 border:2px solid var(--ink);background:var(--panel)}
ul.agenda>li.ag{display:grid;grid-template-columns:4.2rem 1fr;gap:.6rem;
 padding:.5rem .7rem;border-bottom:1px solid var(--line)}
ul.agenda>li:last-child{border-bottom:0}
li.agm{padding:.34rem .7rem;line-height:1.4;border-bottom:2px solid var(--ink);
 background:color-mix(in srgb,var(--chip) 70%,transparent);
 font-family:var(--display);font-size:.72rem;font-weight:800;letter-spacing:.1em;
 text-transform:uppercase}
li.agm .en{color:var(--mute)}
li.ag.phra{background:color-mix(in srgb,var(--sun) 13%,transparent)}
li.ag.now{background:color-mix(in srgb,var(--hot) 8%,transparent);
 box-shadow:inset 3px 0 0 var(--hot)}
.agd{display:flex;flex-direction:column;align-items:center;gap:.1rem}
.agd b{font-family:var(--display);font-size:1.7rem;font-weight:800;line-height:1}
.agd .wd{font-size:.56rem;line-height:1.25;letter-spacing:.08em;text-transform:uppercase;
 color:var(--mute);display:flex;flex-direction:column;align-items:center}
.agd .wd .th{font-family:var(--thai);font-size:.76rem;line-height:1.25;color:var(--ink);
 letter-spacing:0}
.agd .col{width:.6rem;height:.6rem;border-radius:50%;background:var(--c);
 border:1px solid rgba(0,0,0,.28);margin-top:.15rem}
.agb{min-width:0}
.agb .tag{display:inline-block;margin:0;padding:0;background:none;font-family:var(--display);
 font-weight:800;font-size:.6rem;line-height:1.4;letter-spacing:.1em;text-transform:uppercase;
 color:var(--hot)}
.agb .lun{display:flex;align-items:center;gap:.4rem;margin:.1rem 0 0;font-size:.76rem;
 line-height:1.45;color:var(--mute);min-height:1.2rem}
li.ag.phra .agb .lun{color:var(--ink)}
.agb .lun .rowicon{color:var(--sun);vertical-align:-.2em}
.agb ul.ev{list-style:none;margin:.3rem 0 0;padding:0;font-size:.84rem}
.agb ul.ev li{line-height:1.4}
.agb ul.ev li{border-top:1px solid var(--line);padding:.24rem 0}
.agb ul.ev a{text-decoration:none;box-shadow:inset 0 -2px 0 var(--chip)}
.agb ul.ev a:hover{box-shadow:inset 0 -2px 0 var(--hot)}
.calmore{margin:.2rem 0 2rem}
.calmore .btn{display:inline-flex;align-items:center;gap:.5rem}
.calagenda{display:none}
@media(max-width:46rem){
 .calgrid{display:none}
 .calagenda{display:block}
}
.grid.two{grid-template-columns:repeat(auto-fit,minmax(min(18rem,100%),1fr))}
.grid{grid-template-columns:repeat(auto-fill,minmax(min(16.5rem,100%),1fr))}
a.card.place{text-decoration:none;color:var(--ink);display:block}
a.card.place:hover{border-color:var(--hot)}
a.card.place .fig{font-family:var(--display);font-size:2.4rem;font-weight:800;line-height:1;margin:.3rem 0 0}
a.card.place .fig small{display:block;font-family:var(--body);font-size:.6rem;font-weight:800;
 letter-spacing:.16em;text-transform:uppercase;color:var(--mute);margin-top:.4rem}
table.soon td{font-size:.86rem}
table.soon td.away{font-family:var(--mono);font-size:.72rem;color:var(--mute);white-space:nowrap}
table.soon tr.alm td{background:color-mix(in srgb,var(--sun) 12%,transparent)}
table.soon a{text-decoration:none;box-shadow:inset 0 -2px 0 var(--chip)}
table.soon a:hover{box-shadow:inset 0 -2px 0 var(--hot)}
.card.live .fig{font-family:var(--display);font-size:2.6rem;font-weight:800;line-height:1;
 margin:.3rem 0 .2rem;color:var(--c,var(--ink))}
.card.live .fig small{display:block;font-family:var(--body);font-size:.62rem;font-weight:800;
 letter-spacing:.18em;text-transform:uppercase;color:var(--mute);margin-top:.35rem}
/* min() so a 320 px phone gets one column instead of a sideways scroll: a bare
   minmax(20rem,…) track is 360 px wide and cannot shrink below it. */
ul.links{list-style:none;padding:0;margin:.6rem 0 1.4rem;display:grid;
 grid-template-columns:repeat(auto-fill,minmax(min(20rem,100%),1fr));gap:.1rem 1.4rem}
ul.links li{border-bottom:1px solid var(--line);padding:.42rem 0;display:flex;
 flex-wrap:wrap;gap:.1rem .5rem;align-items:baseline}
ul.links a{font-weight:700;text-decoration:none;box-shadow:inset 0 -2px 0 var(--chip)}
ul.links a:hover{box-shadow:inset 0 -2px 0 var(--hot)}
ul.links .note{color:var(--mute);font-size:.8rem;flex:1 1 12rem}
.out{color:var(--mute);font-size:.8em}
.lead-n{font-family:var(--display);font-weight:800}

/* ---- THE GEOFENCE (grafted from home_layer, 2026-09-21 evening). The page says
   where it thinks the reader is and how it knows; the province cards are the switch;
   the nearest-open list is fetched only when asked. */
.wherenow{display:flex;align-items:center;gap:.45rem;flex-wrap:wrap;margin:0;
 border:2px solid var(--ink);background:var(--panel);padding:.5rem .6rem}
.wherenow b{font-family:var(--display);font-size:1.05rem;letter-spacing:.01em}
.wherenow .rowicon{color:var(--hot)}
.wherenow .d{font-family:var(--mono);font-size:.72rem;color:var(--mute)}
.wherenow .src{flex:1 0 100%;font-size:.62rem;letter-spacing:.1em;text-transform:uppercase;
 color:var(--mute)}
a.card.place.city.on{border-color:var(--hot);box-shadow:4px 4px 0 var(--hot)}
.asks{display:flex;flex-wrap:wrap;gap:.4rem}
.asks .btn{flex:1 1 11rem;display:inline-flex;align-items:center;justify-content:center;
 gap:.4rem;font-size:.8rem;padding:.45rem .7rem;border-width:2px;box-shadow:3px 3px 0 var(--ink);
 cursor:pointer;text-align:center}
.asks .btn[disabled]{opacity:.55;cursor:progress}
ul.nearlist{list-style:none;margin:.2rem 0 0;padding:0;font-size:.84rem}
ul.nearlist li{border-bottom:1px solid var(--line)}
ul.nearlist a{display:flex;align-items:center;gap:.5rem;padding:.42rem .2rem;
 text-decoration:none;color:var(--ink)}
ul.nearlist a:hover{background:var(--chip);color:var(--ink)}
ul.nearlist .rowicon{color:var(--mute);flex:0 0 auto}
ul.nearlist .lbl{flex:1 1 auto;min-width:0}
ul.nearlist .lbl .en{display:block;font-size:.74em;color:var(--mute)}
ul.nearlist .open{font-size:.6rem;font-weight:800;letter-spacing:.06em;text-transform:uppercase;
 color:var(--jade);white-space:nowrap}
ul.nearlist .d{font-family:var(--mono);font-size:.72rem;color:var(--mute);white-space:nowrap}
ul.nearlist .wait{color:var(--mute);padding:.4rem .2rem;font-size:.78rem}
#me .halo{fill:color-mix(in srgb,var(--hot) 20%,transparent);stroke:var(--hot);stroke-width:2;
 vector-effect:non-scaling-stroke}
#me .pip{fill:var(--hot);stroke:var(--panel);stroke-width:2;vector-effect:non-scaling-stroke}

/* ---- THE BAR, out of the way (NaN, 2026-09-21: "menu bar and top bits should
   collapse/disappear on scroll, elegantly"). kit.css already hides it on a phone via
   body.nav-away; this carries the same move to every width and folds the nav and the
   language switch away first, so the bar thins before it leaves. */
header.top{transition:transform .26s cubic-bezier(.4,0,.2,1),box-shadow .26s ease}
header.top nav a .en{margin-left:.25rem}
@media(max-width:52rem){
 header.top .in{gap:.3rem .5rem;align-items:center}
 header.top .brand{flex:1 1 auto}
 header.top nav{flex:1 0 100%;order:3;display:flex;flex-wrap:nowrap;overflow-x:auto;
  scrollbar-width:none;gap:.1rem;-webkit-overflow-scrolling:touch}
 header.top nav::-webkit-scrollbar{display:none}
 header.top nav a{flex:0 0 auto;padding:.3rem .42rem;font-size:.72rem}
 header.top nav a .en{display:none}
 header.top .langsw{flex:0 0 auto;margin:0}
}
body.nav-away header.top{transform:translateY(-102%)}
body.nav-tight header.top{box-shadow:0 10px 24px -14px var(--shadow)}
header.top nav,header.top .langsw{transition:opacity .18s ease,max-height .26s ease,
 margin .26s ease}
body.nav-tight header.top nav,body.nav-tight header.top .langsw{
 opacity:0;max-height:0;margin-block:0;overflow:hidden;pointer-events:none}
@media (prefers-reduced-motion:reduce){
 header.top,header.top nav,header.top .langsw{transition:none}
}

/* ---- GEMBA 2026-09-24: the one page people reach on their own. It answers first:
   the needs as tiles under the search, the day as four tiles, the week folded, and
   the reference material closed at the foot. */
a.skip{position:absolute;left:-9999px;top:.4rem;z-index:99}
a.skip:focus{left:.5rem;background:var(--bg);color:var(--ink);padding:.4rem .7rem;
 border:2px solid var(--ink)}
main>.band.hero:first-child{margin-top:-1rem}
.band.hero{min-height:clamp(270px,44vh,480px);margin-bottom:0}
.band.hero .in{padding-block:clamp(1.2rem,4vw,3.2rem)}
.band.hero p{margin:0}
main>h2{margin-top:1.9rem}
main>h2#near{margin-top:1.1rem}
@media(max-width:52rem){
 .band.hero .kicker{letter-spacing:.14em;margin-bottom:.4rem}
 .band.hero h1{font-size:2.2rem}
 .band form.q.big{margin-top:.9rem}
 .q.big .qbox{flex:1 0 100%}
 .q.big input[type=search]{padding:.5rem 0}
 .q.big button{flex:1 1 0;justify-content:center;gap:.3rem;padding:.5rem .3rem;
  font-size:.76rem;letter-spacing:.02em}
}

.nearwrap{display:grid;grid-template-columns:minmax(0,1fr) minmax(15rem,21rem);
 gap:clamp(1rem,2.6vw,1.8rem);align-items:start}
@media(max-width:52rem){.nearwrap{grid-template-columns:1fr}}
.nearmain,.nearmap{display:flex;flex-direction:column;gap:.7rem;min-width:0}
.nearmap .bigmap .plate{height:auto;width:100%}
.maprow{display:flex;flex-wrap:wrap;gap:.4rem}
.maprow .btn{flex:1 1 auto;display:inline-flex;align-items:center;justify-content:center;
 gap:.45rem;margin:0;font-size:.86rem;padding:.5rem .7rem}
.maprow .chip{flex:1 0 100%}
.whererow{display:flex;flex-wrap:wrap;gap:.3rem .6rem;align-items:center}
.whererow .wherenow{flex:1 1 12rem;border:0;background:none;padding:0;gap:.1rem .4rem;
 font-size:.8rem;line-height:1.3}
.whererow .wherenow b{font-size:.9rem}
.whererow .wherenow .src{flex:0 1 auto;font-size:.56rem}
.pills{display:flex;gap:.35rem;flex:1 1 14rem}
a.pill{flex:1 1 0;display:flex;flex-direction:column;justify-content:center;
 border:2px solid var(--line);background:var(--panel);padding:.2rem .55rem;
 text-decoration:none;color:var(--ink)}
a.pill .th{font-family:var(--thai);font-weight:700;font-size:.92rem;line-height:1.25}
a.pill .en,a.pill b{font-size:.58rem;letter-spacing:.08em;text-transform:uppercase;
 color:var(--mute);font-weight:700;line-height:1.3}
a.pill b{font-family:var(--mono);letter-spacing:0}
a.pill:hover{border-color:var(--ink)}
a.pill.on{border-color:var(--hot);box-shadow:3px 3px 0 var(--hot)}
.needs{display:grid;grid-template-columns:repeat(4,minmax(0,1fr));gap:.4rem}
@media(min-width:40rem){.needs{grid-template-columns:repeat(6,minmax(0,1fr))}}
.needs .need.wide{grid-column:1/-1;flex-direction:row;justify-content:center;gap:.6rem}
a.need{display:flex;flex-direction:column;align-items:center;justify-content:center;
 gap:.12rem;min-height:5rem;padding:.45rem .15rem;border:2px solid var(--line);
 background:var(--panel);color:var(--ink);text-decoration:none;text-align:center}
a.need .rowicon{color:var(--hot);margin-bottom:.1rem}
a.need .th{font-family:var(--thai);font-size:.88rem;font-weight:700;line-height:1.2}
a.need .en{font-size:.56rem;letter-spacing:.07em;text-transform:uppercase;color:var(--mute);
 font-weight:700;line-height:1.2}
a.need:hover,a.need.on{border-color:var(--ink);box-shadow:3px 3px 0 var(--ink)}
a.need.on{background:var(--chip)}
#asknear{display:flex;align-items:center;justify-content:center;gap:.5rem;margin:0;
 font-size:.8rem;padding:.5rem .6rem;cursor:pointer}
#asknear[disabled]{opacity:.55;cursor:progress}
ul.nearlist{border:2px solid var(--ink);background:var(--panel);margin:0}
ul.nearlist[hidden]{display:none}
.nearpics[hidden]{display:none}
.nearpics{margin:.2rem 0 .8rem;min-width:0}
.nearpics .pichead{display:flex;flex-wrap:wrap;align-items:center;gap:.4rem;margin:0 0 .35rem;
font-weight:800;font-size:.9rem}
.nearpics .pichead .src{font-weight:400;font-size:.7rem;color:var(--mute)}
.nearpics .pics{display:flex;gap:.5rem;overflow-x:auto;scroll-snap-type:x mandatory;
padding-bottom:.35rem;-webkit-overflow-scrolling:touch}
.nearpics a.pic{flex:0 0 auto;width:min(46vw,190px);scroll-snap-align:start;text-decoration:none;
color:var(--ink);border:2px solid var(--ink);background:var(--panel);display:flex;flex-direction:column}
.nearpics a.pic img{width:100%;height:auto;aspect-ratio:4/3;object-fit:cover;display:block}
.nearpics .cap{padding:.3rem .4rem .4rem;font-size:.74rem;line-height:1.25}
.nearpics .cap b{display:-webkit-box;-webkit-line-clamp:2;-webkit-box-orient:vertical;overflow:hidden}
.nearpics .cap i{display:flex;flex-wrap:wrap;align-items:center;gap:.2rem;font-style:normal;
font-family:var(--mono);font-size:.66rem;color:var(--mute);margin-top:.2rem}
.nearpics .piccred{font-size:.64rem;color:var(--mute);margin:.1rem 0 0}
.band a.bandpin{position:absolute;z-index:1;right:.6rem;bottom:.35rem;display:inline-flex;align-items:center;gap:.3rem;
background:rgba(250,245,234,.82);color:#2a1e16;font-size:.68rem;padding:.2rem .6rem;border-radius:999px;
text-decoration:none;border:1px solid rgba(42,30,22,.18)}
.band a.bandpin b{font-family:var(--mono);font-weight:700}
ul.nearlist li{display:flex;align-items:stretch}
ul.nearlist li:last-child{border-bottom:0}
ul.nearlist a.go{flex:1 1 auto;min-width:0;padding:.5rem .6rem}
ul.nearlist .lbl{line-height:1.3;font-family:var(--body);font-weight:700;
 text-transform:none;letter-spacing:0;font-size:.9rem}
ul.nearlist .lbl .en{font-weight:500;text-transform:none;letter-spacing:0;font-size:.74rem}
ul.nearlist a.tel{flex:0 0 auto;width:3rem;justify-content:center;padding:0;
 border-left:1px solid var(--line);color:var(--jade)}
ul.nearlist a.tel .rowicon{color:var(--jade)}
ul.nearlist li.head{align-items:center;gap:.4rem;padding:.45rem .6rem;
 border-bottom:2px solid var(--ink);font-family:var(--display);font-weight:800;
 font-size:.74rem;letter-spacing:.08em;text-transform:uppercase;line-height:1.3}
ul.nearlist li.head .rowicon{color:var(--hot)}
ul.nearlist li.head .crow{margin-left:auto;font-family:var(--mono);font-weight:500;
 letter-spacing:0;text-transform:none;font-size:.68rem;color:var(--mute)}
ul.nearlist li.all a{flex:1 1 auto;justify-content:flex-end;padding:.4rem .6rem;
 font-size:.74rem;font-weight:800;letter-spacing:.06em;text-transform:uppercase;color:var(--hot)}
ul.nearlist li.all a .rowicon{color:var(--hot)}

.tiles{display:grid;grid-template-columns:repeat(2,minmax(0,1fr));gap:.5rem;margin:.6rem 0}
@media(min-width:52rem){.tiles{grid-template-columns:repeat(4,minmax(0,1fr))}}
.tile{display:flex;flex-direction:column;gap:.12rem;border:2px solid var(--line);
 background:var(--panel);padding:.5rem .7rem;color:var(--ink);text-decoration:none;min-width:0}
a.tile:hover{border-color:var(--ink);color:var(--ink)}
.tile .lab{display:flex;align-items:center;gap:.3rem;font-size:.6rem;font-weight:800;
 letter-spacing:.08em;text-transform:uppercase;color:var(--mute);line-height:1.3}
.tile .lab .rowicon{color:var(--hot)}
.tile b{font-family:var(--display);font-size:2.2rem;font-weight:800;line-height:1.05;
 color:var(--c,var(--ink))}
.tile b a{color:var(--hot);text-decoration:none}
.tile .sub{display:flex;align-items:center;gap:.3rem;flex-wrap:wrap;font-size:.72rem;
 color:var(--mute);line-height:1.4}
.tile .sub a{color:var(--ink);font-weight:800}
.tile .col{width:.6rem;height:.6rem;border-radius:50%;background:var(--c);
 border:1px solid rgba(0,0,0,.28)}

.agb ul.ev li.more{padding:.2rem 0}
.agb ul.ev details{border:0;padding:0;margin:0;background:none}
.agb ul.ev summary{display:inline-block;margin:0;font-family:var(--mono);font-size:.74rem;
 font-weight:800;letter-spacing:0;text-transform:none;color:var(--hot);line-height:1.4}
.agb ul.ev details[open]>summary{margin-bottom:.2rem}
.agb ul.ev details ul.ev{margin:0}
@media(min-width:60rem){
 main>ul.agenda{columns:2;column-gap:0}
 main>ul.agenda>li{break-inside:avoid}
 main>ul.agenda>li.ag{border-left:1px solid var(--line)}
 main>ul.agenda>li.agm{column-span:all}
 .nearmap .bigmap .plate{height:min(27rem,68vh);width:auto;margin:0 auto}
}
.calmore{display:flex;flex-wrap:wrap;gap:.5rem}
.calmore .btn{margin:0;font-size:.82rem;padding:.45rem .75rem}

.chips.shelves{display:grid;grid-template-columns:repeat(auto-fill,minmax(min(9rem,100%),1fr));
 gap:.35rem;margin:.6rem 0 1rem}
@media(min-width:52rem){.chips.shelves{grid-template-columns:repeat(auto-fill,minmax(12.5rem,1fr))}}
.chips.shelves .chip{display:grid;grid-template-columns:auto minmax(0,1fr);
 column-gap:.4rem;align-items:center;padding:.3rem .45rem;min-width:0}
.chips.shelves .chip .rowicon{grid-row:span 2}
.chips.shelves .chip .bi{min-width:0}
.chips.shelves .chip .bi span{line-height:1.25}
.chips.shelves .chip b{grid-column:2;font-size:.66rem;line-height:1.3}
.grid.pins{grid-template-columns:repeat(auto-fill,minmax(min(14.5rem,100%),1fr));gap:.5rem}
.card.pin{padding:.55rem .7rem}
.card.pin h3{margin:0;font-size:.95rem}
.card.pin .th{margin:0;font-size:.8rem}
.card.pin p{font-size:.78rem;margin:.1rem 0 0;line-height:1.4}

details.fold{margin:1rem 0;border:2px solid var(--line);background:var(--panel);
 padding:.55rem .8rem}
details.fold>summary{display:flex;align-items:center;gap:.5rem;margin:0;
 font-family:var(--display);font-size:.9rem;line-height:1.4}
details.fold>summary .rowicon{color:var(--hot)}
details.fold>summary b{font-family:var(--mono);font-size:.74rem;color:var(--mute)}
details.fold[open]>summary{margin-bottom:.6rem}
.aboutdl{margin:0;display:grid;grid-template-columns:1fr auto;gap:.28rem .6rem;
 font-size:.86rem;max-width:28rem}
.aboutdl dt{color:var(--mute)}
.aboutdl dd{margin:0;text-align:right;font-family:var(--display);font-weight:800}
details.fold .btns{display:flex;margin:.8rem 0}
main>.band:last-child{margin-bottom:0}
main:has(>.band:last-child){padding-bottom:0}
footer.bot{margin-top:0}
details.fold .btn{font-size:.82rem;padding:.3rem .7rem}
"""

NAV = [("#near", "ใกล้ๆ", "near", "i-near"), ("#now", "ตอนนี้", "now", "i-clock"),
       ("#soon", "เร็วๆ นี้", "soon", "i-cal"), ("#shelves", "หมวด", "shelves", "i-layers"),
       ("#deep", "เว็บ", "sites", "i-grid")]

def nav_html(prefix=""):
    """The bar's own links. A page that is not the front page reaches them through it."""
    return "".join(
        f'<a href="{prefix}{h}">{icon(ic, 18)}<span class="th" lang="th">{E(th)}</span>'
        f'<span class="en">{E(en)}</span></a>' for h, th, en, ic in NAV)

hero = band(
    "site/hero/temple-square-dusk.jpg", cls="hero", tag="h1", scene="hero",
    kicker="เชียงใหม่ · เชียงราย — Chiang Mai & Chiang Rai",
    head='มดแดง <span class="en">Mot Dang</span>',
    line=f"{n(ALL)} places · {len(SHELVES)} shelves",
    extra=search_form(big=True))

endband = band(
    "site/hero/sunset-trees-1.jpg", cls="short", scene="door",
    kicker="ประตู · the door",
    head='เพิ่มหรือแก้ <span class="en">Add or fix a place</span>',
    href=BASE + "add.html", cta="เพิ่มข้อมูล · Add something")

def geo_json():
    """What the geofence needs, baked: her frames with their coordinates, the two city
    centres, and the drawn map's own projection."""
    cities = [{"k": k, "th": th, "en": en, "lat": lat, "lon": lon}
              for th, en, lat, lon, k in homebits.mapart.CITY]
    needs = {k: {"th": th, "en": en, "ic": ic, "m": m, "href": BASE + href}
             for k, th, en, ic, m, href in NEEDS if m}
    return json.dumps(homebits.geo_payload(SHELVES, homebits.projection(), cities, needs),
                      ensure_ascii=False, separators=(",", ":"))


def render():
    desc = (f"มดแดง — สารบัญเชียงใหม่และเชียงราย {n(ALL)} แห่ง {len(SHELVES)} หมวด · "
            f"Mot Dang — a directory of Chiang Mai and Chiang Rai: {n(ALL)} places, "
            f"{len(SHELVES)} shelves, {n(PINS)} on the map.")
    callout_band = band(
        CALLOUT["pic"], cls="short", kicker=CALLOUT.get("kicker", ""),
        head=E(CALLOUT.get("head", "")), line=E(CALLOUT.get("line", "")),
        href=CALLOUT.get("href", ""), cta=CALLOUT.get("cta", "")) if CALLOUT else ""

    body = f"""
    {hero}
    {served_band()}

    {callout_band}
    <div class="magic" id="magic" hidden aria-live="polite"></div>
    {obs_layer_ask()}
    <h2 id="near"><span class="th" lang="th">ใกล้ๆ</span> <span class="en">Near</span></h2>
    {near_block()}

    <h2 id="now"><span class="th" lang="th">ตอนนี้</span> <span class="en">Now</span></h2>
    {now_tiles()}

    <h2 id="soon"><span class="th" lang="th">เร็วๆ นี้</span> <span class="en">Soon</span></h2>
    {homebits.agenda(TODAY, 7, alive=live, fold=(6, 3))}
    <p class="calmore"><a class="btn" href="{BASE}calendar.html">{icon('i-cal', 20)}
    ปฏิทินเต็ม · The whole calendar</a>
    <a class="btn alt" href="{BASE}festivals.html">{icon('i-party', 20)}
    เทศกาล · Festivals</a></p>

    <h2 id="shelves"><span class="th" lang="th">หมวด</span> <span class="en">Every shelf</span></h2>
    {chips()}

    <h2 id="deep"><span class="th" lang="th">เว็บเด่น</span> <span class="en">Sites</span></h2>
    {pinned_cards()}

    <details class="fold" id="elsewhere">
      <summary>{icon('i-globe', 18)}ที่อื่น · Elsewhere <b>{len(FLEET["sites"]) - 1}</b></summary>
      {roster_rows()}
    </details>

    <details class="fold" id="about">
      <summary>{icon('i-list', 18)}เกี่ยวกับ · About</summary>
      <dl class="aboutdl">
        <dt>records</dt><dd>{n(ALL)}</dd>
        <dt>เชียงใหม่ Chiang Mai</dt><dd>{n(TOT['cm'])}</dd>
        <dt>เชียงราย Chiang Rai</dt><dd>{n(TOT['cr'])}</dd>
        <dt>shelves</dt><dd>{len(SHELVES)}</dd>
        <dt>on the map</dt><dd>{n(PINS)}</dd>
        <dt>with a phone</dt><dd>{n(TELS)}</dd>
        <dt>outbound links live</dt><dd>{n(LIVE)}</dd>
        <dt><a href="{BASE}find">pages you can search</a></dt><dd>{n(FIND.get("pages", 0))}</dd>
      </dl>
      <p class="btns"><a class="btn" href="{BASE}api/">API</a>
      <a class="btn alt" href="{BASE}source/">Source</a></p>

      <h3 id="index"><span class="th" lang="th">สารบัญ</span> <span class="en">The index</span></h3>
      {index_table()}

      <h3 id="sources"><span class="th" lang="th">ที่มา</span> <span class="en">Sources</span></h3>
      {source_rows()}
      <p class="small">ลิงก์ออก · outbound, {E(LH['generated'])}: <b class="lead-n">{n(LH['ok'])}</b>
      of {n(LH['urls'])} answered, {n(LH['domains'])} domains.
      <a href="{BASE}reach.html">The link-rot study</a>.</p>

      <h3><span class="th" lang="th">เครื่อง</span> <span class="en">The machine</span></h3>
      {feed_rows()}
    </details>

    {UNDER_CONSTRUCTION}
    {endband}
    """

    return shell(body, desc, geo=True, top=strip_html())


# The front page names the site and the two cities it is about. The search box
# reads ?q= client-side, so SearchAction needs no server behind it.
HOME_LD = '<script type="application/ld+json">' + json.dumps({
    "@context": "https://schema.org", "@type": "Organization", "@id": BASE + "#org",
    "name": "มดแดง Mot Dang", "alternateName": "Mot Dang", "url": BASE,
    "logo": BASE + "logo/motdang-mark-512.png",
    "sameAs": ["https://github.com/NaNoBotCo/mot-dang"],
}, ensure_ascii=False) + '</script>' + '<script type="application/ld+json">' + json.dumps({
    "@context": "https://schema.org", "@type": "WebSite", "publisher": {"@id": BASE + "#org"},
    "name": "มดแดง Mot Dang", "alternateName": "Mot Dang", "url": BASE,
    "inLanguage": ["th", "en"],
    "about": [
        {"@type": "City", "name": "Chiang Mai", "alternateName": "เชียงใหม่",
         "sameAs": "https://www.wikidata.org/wiki/Q52028"},
        {"@type": "City", "name": "Chiang Rai", "alternateName": "เชียงราย",
         "sameAs": "https://www.wikidata.org/wiki/Q856772"}],
    "potentialAction": {
        "@type": "SearchAction",
        "target": {"@type": "EntryPoint",
                   "urlTemplate": BASE + "search.html?q={search_term_string}"},
        "query-input": "required name=search_term_string"},
}, ensure_ascii=False) + '</script>'


def shell(body, desc, title="มดแดง Mot Dang — เชียงใหม่ · เชียงราย · Chiang Mai & Chiang Rai",
          canon=BASE, geo=False,
          skip="#near", prefix="", top=""):
    """One head, one bar, one footer, for the front page and the calendar page.

    translate="no" + the notranslate meta (NaN, 2026-09-22: the site translates
    itself and "google does worse"). Chrome and Safari both read them, and neither
    then offers to translate a page that is already bilingual.
    """
    navbar = nav_html(prefix)
    geo_bits = (f'<script type="application/json" id="md-geo">{geo_json()}</script>'
                f'{homebits.GEO_JS}{PLAN_CHIP_JS}'
                f'<script type="application/json" id="md-magic">{magic_json()}</script>'
                f'{MAGIC_JS}') if geo else ""
    return homebits.pair_bare(f"""<!DOCTYPE html>
    <html lang="th" translate="no" class="notranslate lang-both"><head><meta charset="utf-8">
    <meta name="viewport" content="width=device-width,initial-scale=1,viewport-fit=cover">
<meta name="google" content="notranslate">
{homebits.LANG_HEAD}
    <title>{E(title)}</title>
    <meta name="description" content="{E(desc)}">
<link rel="canonical" href="{E(canon)}">
<meta name="md-where" content="">
<link rel="icon" href="{BASE}logo/motdang-favicon.svg" type="image/svg+xml">
<meta property="og:site_name" content="มดแดง Mot Dang">
<meta property="og:title" content="{E(title)}">
<meta property="og:description" content="{E(desc)}">
<meta property="og:type" content="website">
<meta property="og:url" content="{E(canon)}">
<meta property="og:image" content="{BASE}site/hero/temple-square-dusk.jpg">
<meta name="twitter:card" content="summary_large_image">
{HOME_LD if canon == BASE else ""}
    <style>{(CSSDIR / "kit.css").read_text()}
    {(CSSDIR / "bands.css").read_text()}
    {EXTRA}
    {day_vars()}{MAGIC_CSS}{homebits.LANG_CSS}</style>
    </head><body>
<script type="application/json" id="md-home">{{"built":"{E(TODAY.isoformat())}","be":{TODAY.year + 543},"generator":"home_next.py","shelves":{len(SHELVES)},"records":{ALL},"find":{FIND.get("pages", 0)}}}</script>
{homebits.sprite_defs()}
    <a class="skip" href="{skip}">ข้ามไปเนื้อหา · Skip to content</a>
    <header class="top"><div class="in">
      <a class="brand" href="{BASE}">MOT <b>DANG</b></a>
      <nav>{navbar}</nav>
      {homebits.LANG_SWITCH}
    </div></header>
    {top}
    <main>{body}</main>
    {geo_bits}
    {homebits.HEADER_JS}{homebits.LANG_JS}
    <footer class="bot"><div class="in">
      <p><b>มดแดง Mot Dang</b> — เชียงใหม่ · เชียงราย. Built by NaN,
      <a href="https://wichaa.net/">wichaa.net</a>. Text and data
      <a href="https://creativecommons.org/licenses/by/4.0/">CC BY 4.0</a>;
      pins and much of the ground truth © OpenStreetMap contributors, ODbL.</p>
      <p class="small"><a href="{BASE}find">ค้นหา · search</a> ·
      <a href="{BASE}find?adv=1">ตรรกะ · boolean</a> ·
      <a href="{BASE}advanced.html">กรองสถานที่ · place filters</a> ·
      <a href="{BASE}api/">API</a> · Rebuilt {E(TODAY.isoformat())} · พ.ศ. {TODAY.year + 543}</p>
    </div></footer>
    </body></html>
   """)


def calendar_page():
    """The lengthier view the front page's seven days link to (NaN, 2026-09-22).

    The months are drawn wide and listed narrow — the same days either way, because a
    seven-column grid on a phone is the thing that was cutting the contents off.
    """
    months = homebits.horizon(homebits._cal_data()[2], TODAY)
    days = (datetime.date(TODAY.year + (TODAY.month + months - 1) // 12,
                          (TODAY.month + months - 1) % 12 + 1, 1) - TODAY).days
    body = f"""
    <h1><span class="th" lang="th">ปฏิทิน</span> <span class="en">The calendar</span></h1>
    <p class="lede">{months} months. Day colour, the moon as it will be that night,
    วันพระ, and everything dated into them.</p>
    <p class="calmore"><a class="btn alt" href="{BASE}">{icon('i-arrow', 18)}
    หน้าแรก · Back to the front page</a></p>

    <div class="calgrid">{homebits.calendar(TODAY, months=months, k_events=3, alive=live)}</div>
    <div class="calagenda">{homebits.agenda(TODAY, days, alive=live, marked_after=14)}</div>

    <h2 id="list"><span class="th" lang="th">รายการ</span> <span class="en">As a list</span></h2>
    <p>Nearest first, each with the source that announced it.</p>
    {soon_rows(k=60)}
    """
    desc = (f"ปฏิทินเชียงใหม่และเชียงราย {months} เดือน — วันพระ ดวงจันทร์ และงานที่มีวันที่ · "
            f"The Mot Dang calendar: {months} months of wan phra, the moon, and every "
            f"dated thing in Chiang Mai and Chiang Rai.")
    return shell(body, desc, title="ปฏิทิน · The Mot Dang calendar",
                 canon=BASE + "calendar.html", skip="#list", prefix=BASE)


if __name__ == "__main__":
    out = DOCS / "index.html"
    out.write_text(render())
    print("wrote", out, out.stat().st_size, "bytes")
    cal = DOCS / "calendar.html"
    cal.write_text(calendar_page())
    print("wrote", cal, cal.stat().st_size, "bytes")
