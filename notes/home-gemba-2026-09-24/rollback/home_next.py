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

THE STACK IS NEAR, THEN NOW, THEN SOON (NaN, same day). The only thing allowed
above it is a festival or event SHE calls out: set CALLOUT and it draws a band,
leave it None and nothing is drawn. Never fill it on my own judgement.

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
FLEET = j("curated/fleet.json")

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

# ---- the minisites, lifted from home_layer.MINISITES with a line added
PINNED = [
    ("loop/", "ลูปแม่ฮ่องสอน", "Mae Hong Son Loop", "i-route", "1,864 curves, every town on the ring, and what the air is doing"),
    ("muay-thai/", "มวยไทย", "Muay Thai", "i-glove", "gyms, stadiums and the Lanna root of the sport"),
    ("https://wichaa.net/handpoke/", "สักมือ", "Hand Poke", "i-ink", "28 hand-tattooing traditions, worldwide"),
    ("festivals.html", "เทศกาล", "Festivals", "i-party", "dated from official announcements, each with its source"),
    ("wats/", "ไหว้พระ ๙ วัด", "Nine Wats", "i-wat", "the wat rounds, walkable, in order"),
    ("horoscope.html", "ดวง", "Horoscope", "i-moon", "day colour, planet, posture, the Chinese pillar"),
    ("foon.html", "ฝุ่น", "Dust", "i-haze", "PM2.5 now and the fourteen days behind it"),
    ("plan.html", "วางแผนเดิน", "Plan a walk", "i-walk", "a route through what is open"),
    ("toilets.html", "ห้องน้ำ", "Toilets", "i-loo", "mapped, with what each one has"),
    ("chuai.html", "ช่วย", "Help, nearest", "i-sos", "hospital, police, pharmacy, from where you stand"),
]

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
    return f'<div class="chips">{"".join(out)}</div>'


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
    pages = n(FIND.get("pages", 0))
    hint = (f'<p class="qhint">{pages} pages, twenty sites.</p>'
            if big and FIND.get("pages") else "")
    return (f'<form class="{cls}" action="{BASE}find" method="get" role="search">'
            f'<label class="qbox">{icon("i-search", 26, "rowicon qi")}'
            f'<input type="search" name="q" aria-label="ค้นหา · search" '
            f'placeholder="ค้นหา · search"></label>'
            f'<button type="submit">{icon("i-search", 20)}'
            f'<span>ค้นหา · Search</span></button>'
            f'<button type="submit" name="lucky" value="1" class="alt">'
            f'{icon("i-dice", 20)}<span>ลองโชค · Lucky</span></button>'
            f'{hint}</form>')


DOORS = (("map.html", "แผนที่", "Map", "i-map"),
         ("here.html", "ตรงนี้", "Here", "i-here"),
         ("toilets.html", "ห้องน้ำ", "Toilets", "i-loo"),
         ("chuai.html", "ช่วย", "Help, nearest", "i-sos"))


def near_block():
    """NEAR — the map at the size of the thing it draws, then where the reader is and
    what is around them. The province cards are also the switch: the page's links follow
    whichever one is on."""
    cards = []
    for k, th, en in (("cm", "เชียงใหม่", "Chiang Mai"), ("cr", "เชียงราย", "Chiang Rai")):
        cards.append(f'<a class="card place city" data-city="{k}" href="{BASE}{k}/">'
                     f'<h3>{bi(th, en)}</h3>'
                     f'<p class="fig">{n(TOT[k])}<small>สถานที่ · places</small></p></a>')
    doors = "".join(
        f'<a class="chip" href="{BASE}{h}">{icon(ic, 20)}{bi(th, en)}</a>'
        for h, th, en, ic in DOORS)
    # THE READER'S OWN CHIP (NaN, 2026-09-21). The only thing in this row that is not
    # true for everybody, so it ships `hidden` and PLAN_CHIP_JS reveals it for a reader
    # who has a plan.
    doors += f'<a class="chip nnplan" href="{BASE}plan.html" hidden></a>'
    # Server-side this says Chiang Mai, because that is what the page is if nothing
    # else is known. The script rewrites it from the edge, the reader's choice, or a tap.
    where = (f'<p class="wherenow" id="where">{icon("i-near", 18)}'
             f'<b>เชียงใหม่ · Chiang Mai</b>'
             f'<span class="src">ค่าเริ่มต้น · the default</span></p>')
    asks = (f'<div class="asks">'
            f'<button type="button" id="asknear" class="btn alt">{icon("i-here", 20)}'
            f'<span>แถวนี้มีอะไร · What is around me</span></button>'
            f'<button type="button" id="locate" class="btn alt">{icon("i-compass", 20)}'
            f'<span>ใช้ตำแหน่งจริง · Use my position</span></button></div>')
    return (f'<div class="mapband"><div class="in">'
            f'{homebits.big_map(AMPHOE_COUNTS, "site/map/", DOCS / "site/map")}'
            f'<div class="maprail">'
            f'{where}'
            f'<div class="grid two twocards">{"".join(cards)}</div>'
            f'<a class="btn wide" id="openmap" href="{BASE}map.html" '
            f'data-href="{BASE}map.html">{icon("i-map", 22)}'
            f'<span>เปิดแผนที่ · Open the live map</span></a>'
            f'{asks}'
            f'<ul class="nearlist" id="nearlist"></ul>'
            f'<p class="small mute">{n(PINS)} pins · {len(SHELVES)} shelves.</p>'
            f'<div class="chips">{doors}</div>'
            f'</div></div></div>')


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
el.textContent=n?'🗺 แผนของคุณ '+n+' จุด · your plan, '+n+(n>1?' stops':' stop'):'';}
paint();
window.addEventListener('storage',function(e){if(!e.key||e.key==='md-plan')paint();});
})();
</script>"""


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


def air_cards():
    out = []
    for p in AIR["places"][:2]:
        b = p["band"]
        out.append(f'<div class="card live" data-air="{"cm" if p["id"] == "chiang-mai" else "cr" if p["id"] == "chiang-rai" else ""}">'
                   f'<h3>{icon("i-air", 20)}{bi(p["th"], p["en"])}</h3>'
                   f'<p class="fig" style="--c:{E(b["colour"])}">{p["pm25"]:g}'
                   f'<small>PM2.5 µg/m³</small></p>'
                   f'<p class="small mute">{E(b["th"])} · {E(b["en"])} · '
                   f'{E(p["observed"][11:16])} น.</p></div>')
    return "".join(out)


def pinned_cards():
    out = []
    for href, th, en, ic, line in PINNED:
        ext = ' rel="noopener"' if href.startswith("http") else ""
        mark = (f'<span class="out" title="another site">{icon("i-arrow", 14)}</span>'
                if href.startswith("http") else "")
        url = href if href.startswith("http") else BASE + href
        out.append(f'<div class="card pin"><h3>{icon(ic, 22)}'
                   f'<a href="{E(url)}"{ext}>{E(en)}{mark}</a></h3>'
                   f'<p class="th" lang="th">{E(th)}</p><p>{E(line)}</p></div>')
    return f'<div class="grid">{"".join(out)}</div>'


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
        cls = "bad" if fails else ""
        rows.append(f'<tr class="{cls}"><td>{E(name)}</td><td class="r">{n(count or 0)}</td>'
                    f'<td class="r mono">{E(when)}</td>'
                    f'<td class="r">{icon("i-warn", 15) + " " + str(fails) if fails else "ok"}</td></tr>')
    return ('<div class="scroll"><table class="idx feeds"><thead><tr><th>feed</th>'
            '<th class=r>rows</th><th class=r>last good</th><th class=r></th></tr></thead>'
            f'<tbody>{"".join(rows)}</tbody></table></div>')


EXTRA = """
.band h1{font-family:var(--display);font-size:clamp(2.1rem,6.6vw,3.9rem);line-height:.98;
 margin:0 0 .5rem;border:0;color:#fff;text-transform:uppercase;letter-spacing:-.01em;
 text-shadow:0 2px 26px rgba(0,0,0,.6);max-width:22ch}
.band h1 .en{color:#fff}
.band .th,.band .en{color:inherit}
/* ---- additions for the front page: the About rail, the chips, the index */
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
"""

NAV = [("#near", "ใกล้ๆ", "near", "i-near"), ("#now", "ตอนนี้", "now", "i-clock"),
       ("#soon", "เร็วๆ นี้", "soon", "i-cal"), ("#shelves", "หมวด", "shelves", "i-layers"),
       ("#index", "สารบัญ", "index", "i-list"), ("#deep", "เจาะลึก", "deep", "i-star"),
       ("#elsewhere", "ที่อื่น", "elsewhere", "i-globe")]

def nav_html(prefix=""):
    """The bar's own links. A page that is not the front page reaches them through it."""
    return "".join(
        f'<a href="{prefix}{h}">{icon(ic, 18)}<span class="th" lang="th">{E(th)}</span>'
        f'<span class="en">{E(en)}</span></a>' for h, th, en, ic in NAV)

hero = band(
    "site/hero/temple-square-dusk.jpg", cls="tall", tag="h1", scene="hero",
    kicker="เชียงใหม่ · เชียงราย — Chiang Mai & Chiang Rai",
    head='มดแดง <span class="en">Mot Dang</span>',
    line=f"{n(ALL)} places · {len(SHELVES)} shelves · {n(PINS)} on the map",
    extra=search_form(big=True))

midband = band(
    "site/hero/khao-soi-plate.jpg", cls="short", scene="day",
    big=n(TOT["cm"]), big_label="in Chiang Mai alone")

endband = band(
    "site/hero/sunset-trees-1.jpg", cls="short", scene="door",
    kicker="ประตู · the door",
    head="Add a place, or take the whole thing",
    line="The API answers without a key.",
    href=BASE + "api/", cta="The API")

def geo_json():
    """What the geofence needs, baked: her frames with their coordinates, the two city
    centres, and the drawn map's own projection."""
    cities = [{"k": k, "th": th, "en": en, "lat": lat, "lon": lon}
              for th, en, lat, lon, k in homebits.mapart.CITY]
    return json.dumps(homebits.geo_payload(SHELVES, homebits.projection(), cities),
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

    <div class="rail" id="about">
      <div>
        <h2>สารบัญเมือง · A city index</h2>
        <p class="lede">Chiang Mai and Chiang Rai: shops, wats, clinics, markets, schools,
        repairs. Rebuilt daily.</p>
        <p>One shelf, one page. The index says what each holds before you open it.</p>
        <div class="btns">
          <a class="btn" href="#index">The whole index</a>
          <a class="btn alt" href="#shelves">Jump to a shelf</a>
        </div>
      </div>
      <aside class="about">
        <h3>About</h3>
        <dl>
          <dt>records</dt><dd>{n(ALL)}</dd>
          <dt>เชียงใหม่ Chiang Mai</dt><dd>{n(TOT['cm'])}</dd>
          <dt>เชียงราย Chiang Rai</dt><dd>{n(TOT['cr'])}</dd>
          <dt>shelves</dt><dd>{len(SHELVES)}</dd>
          <dt>on the map</dt><dd>{n(PINS)}</dd>
          <dt>with a phone</dt><dd>{n(TELS)}</dd>
          <dt>outbound links live</dt><dd>{n(LIVE)}</dd>
          <dt>data feeds</dt><dd>{len(feeds)}</dd>
          <dt><a href="{BASE}find">pages you can search</a></dt><dd>{n(FIND.get("pages", 0))}</dd>
        </dl>
        <div class="btns">
          <a class="btn" href="{BASE}api/">API</a>
          <a class="btn alt" href="{BASE}source/">Source</a>
        </div>
        <p class="small mute">CC BY 4.0 · © OpenStreetMap contributors ·
        rebuilt {E(TODAY.isoformat())}</p>
      </aside>
    </div>

    {callout_band}
    <h2 id="near">ใกล้ๆ <span class="en">Near</span></h2>
    <p>One dot per place. Tap a district for the live map.</p>
    {near_block()}

    <h2 id="now">ตอนนี้ <span class="en">Now</span></h2>
    <div class="grid" id="aircards">
      {air_cards()}
      <div class="card live"><h3>{icon('i-cal', 20)}{bi('วันนี้', 'Today')}</h3>
        <p class="fig">{TODAY.day}<small>{E(TODAY.strftime('%B %Y'))} · พ.ศ. {TODAY.year + 543}</small></p>
        <p class="small mute">the whole catalogue rebuilt this morning</p></div>
      <div class="card live"><h3>{icon('i-sos', 20)}{bi('ฉุกเฉิน', 'Emergency')}</h3>
        <p class="fig"><a href="tel:1669">1669</a><small>ambulance · เจ็บป่วยฉุกเฉิน</small></p>
        <p class="small mute">191 ตำรวจ · 199 ดับเพลิง · 1155 ตำรวจท่องเที่ยว</p></div>
    </div>

    <h2 id="soon">เร็วๆ นี้ <span class="en">Soon</span></h2>
    <p>The next seven days.</p>
    {homebits.agenda(TODAY, 7, alive=live)}
    <p class="calmore"><a class="btn" href="{BASE}calendar.html">{icon('i-cal', 20)}
    ปฏิทินเต็ม · The whole calendar</a></p>

    <h2 id="shelves">หมวด <span class="en">Every shelf</span></h2>
    <p>Largest first, both provinces.</p>
    {chips()}

    {midband}

    <h2 id="index">สารบัญ <span class="en">The index</span></h2>
    <p>Each percentage is of that shelf's own records.</p>
    {index_table()}

    <h2 id="deep">เจาะลึก <span class="en">Pinned</span></h2>

    {pinned_cards()}

    <h2 id="elsewhere">ที่อื่น <span class="en">Elsewhere</span></h2>

    {roster_rows()}

    <h3>ลิงก์ออก <span class="en">Outbound</span></h3>
    <p>Last sweep {E(LH['generated'])}: <b class="lead-n">{n(LH['ok'])}</b> of
    {n(LH['urls'])} answered, {n(LH['domains'])} domains.
    <a href="{BASE}reach.html">The link-rot study</a>.</p>

    <h2 id="sources">ที่มา <span class="en">Sources</span></h2>
    {source_rows()}

    <h3>เครื่อง <span class="en">The machine</span></h3>
    <p>{len(feeds)} feeds.
    {"All current." if not (stale or failing) else f"{failing} failing, {stale} older than a week."}</p>
    {feed_rows()}

    {endband}
    """

    return shell(body, desc, geo=True)


def shell(body, desc, title="มดแดง Mot Dang — เชียงใหม่ · เชียงราย", canon=BASE, geo=False,
          skip="#about", prefix=""):
    """One head, one bar, one footer, for the front page and the calendar page.

    translate="no" + the notranslate meta (NaN, 2026-09-22: the site translates
    itself and "google does worse"). Chrome and Safari both read them, and neither
    then offers to translate a page that is already bilingual.
    """
    navbar = nav_html(prefix)
    geo_bits = (f'<script type="application/json" id="md-geo">{geo_json()}</script>'
                f'{homebits.GEO_JS}{PLAN_CHIP_JS}') if geo else ""
    return f"""<!DOCTYPE html>
    <html lang="th" translate="no" class="notranslate"><head><meta charset="utf-8">
    <meta name="viewport" content="width=device-width,initial-scale=1,viewport-fit=cover">
<meta name="google" content="notranslate">
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
    <style>{(CSSDIR / "kit.css").read_text()}
    {(CSSDIR / "bands.css").read_text()}
    {EXTRA}</style>
    </head><body>
<script type="application/json" id="md-home">{{"built":"{E(TODAY.isoformat())}","be":{TODAY.year + 543},"generator":"home_next.py","shelves":{len(SHELVES)},"records":{ALL},"find":{FIND.get("pages", 0)}}}</script>
{homebits.sprite_defs()}
    <a class="skip" href="{skip}">ข้ามไปเนื้อหา · Skip to content</a>
    <header class="top"><div class="in">
      <a class="brand" href="{BASE}">MOT <b>DANG</b></a>
      <nav>{navbar}</nav>
      <div class="langsw"><a href="#" aria-current="true">TH+EN</a></div>
    </div></header>
    <main>{body}</main>
    {geo_bits}
    {homebits.HEADER_JS}
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
    """


def calendar_page():
    """The lengthier view the front page's seven days link to (NaN, 2026-09-22).

    The months are drawn wide and listed narrow — the same days either way, because a
    seven-column grid on a phone is the thing that was cutting the contents off.
    """
    months = homebits.horizon(homebits._cal_data()[2], TODAY)
    days = (datetime.date(TODAY.year + (TODAY.month + months - 1) // 12,
                          (TODAY.month + months - 1) % 12 + 1, 1) - TODAY).days
    body = f"""
    <h1>ปฏิทิน <span class="en">The calendar</span></h1>
    <p class="lede">{months} months. Day colour, the moon as it will be that night,
    วันพระ, and everything dated into them.</p>
    <p class="calmore"><a class="btn alt" href="{BASE}">{icon('i-arrow', 18)}
    หน้าแรก · Back to the front page</a></p>

    <div class="calgrid">{homebits.calendar(TODAY, months=months, k_events=3, alive=live)}</div>
    <div class="calagenda">{homebits.agenda(TODAY, days, alive=live, marked_after=14)}</div>

    <h2 id="list">รายการ <span class="en">As a list</span></h2>
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
