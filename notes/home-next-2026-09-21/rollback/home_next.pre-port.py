#!/usr/bin/env python3
"""home_next.py — the front page of motdang.net.

Nan, 2026-09-21: the 9/19 page is "a mouthful, and people struggle with
navigation because it doesn't flow"; then "github itself is a useful model for
discoverability of resources… like github but aesthetic, and include external
links as well as internal links"; then "the overall look should be exactly like
the minisites we already build, but it should contain motdang itself in a
discoverable way." On the result: "this looks perfect."

So: GitHub's structures — an About rail, topic chips, a repository-style index
of every shelf, pinned minisites, an outbound Elsewhere, and the harvesters'
own status — wearing the minisite stylesheet, vendored under assets/minisite/.

THE STACK IS NEAR, THEN NOW, THEN SOON (Nan, same day). The only thing allowed
above it is a festival or event SHE calls out: set CALLOUT and it draws a band,
leave it None and nothing is drawn. Never fill it on my own judgement.

The header carries the fleet search (motdang.net/find, live 2026-09-21), which
supersedes the 9/19 decision to keep the front page boxless.

    python3 home_next.py        # writes docs/index.html
    home_next.render()          # what build.py calls

Every number is read at build time from the file that owns it. Nothing here
fetches at load; the pictures are Nan's own frames already in docs/site/hero/.
"""
import collections
import datetime
import difflib
import glob
import html
import json
import os
import pathlib

ROOT = pathlib.Path(__file__).resolve().parent
DATA = ROOT / "data"
DOCS = ROOT / "docs"
CSSDIR = ROOT / "assets" / "minisite"

BASE = "https://motdang.net/"
TODAY = datetime.date.today()

# THE STACK (Nan, 2026-09-21): near, then now, then soon. In that order, always.
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


WORD = {25: "Twenty-five", 26: "Twenty-six", 27: "Twenty-seven", 28: "Twenty-eight",
        29: "Twenty-nine", 30: "Thirty"}


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
    ("loop/", "ลูปแม่ฮ่องสอน", "Mae Hong Son Loop", "1,864 curves, every town on the ring, and what the air is doing"),
    ("muay-thai/", "มวยไทย", "Muay Thai", "gyms, stadiums and the Lanna root of the sport"),
    ("https://wichaa.net/handpoke/", "สักมือ", "Hand Poke", "28 hand-tattooing traditions, worldwide"),
    ("festivals.html", "เทศกาล", "Festivals", "dated from official announcements, each with its source"),
    ("merit.html", "ไหว้พระ ๙ วัด", "Nine Wats", "the merit round, walkable, in order"),
    ("horoscope.html", "ดวง", "Horoscope", "day colour, planet, posture, the Chinese pillar"),
    ("foon.html", "ฝุ่น", "Dust", "PM2.5 now and the fourteen days behind it"),
    ("plan.html", "วางแผนเดิน", "Plan a walk", "a route through what is open"),
    ("toilets.html", "ห้องน้ำ", "Toilets", "mapped, with what each one has"),
    ("chuai.html", "ช่วย", "Help, nearest", "hospital, police, pharmacy, from where you stand"),
]

SOURCES = [
    ("https://www.openstreetmap.org/copyright", "OpenStreetMap", "the pins, and much of the ground truth", "ODbL"),
    ("https://open-meteo.com/", "Open-Meteo Air Quality", "the PM2.5 model behind every dust figure", "CC BY 4.0"),
    ("https://podfoon.anamai.moph.go.th/", "กรมอนามัย · Dept. of Health", "the clean-room register, 2,428 rooms", "public"),
    ("https://commons.wikimedia.org/", "Wikimedia Commons", "the borrowed photographs, each credited", "CC BY / BY-SA"),
    # data.bopp-obec.info is where the register itself lives; it did not resolve from
    # here on 2026-09-21, so the credit points at the office instead.
    ("https://www.obec.go.th/", "สพฐ. · OBEC", "the school register", "public"),
]


# ---------------------------------------------------------------- pieces

def band(image, kicker="", head="", line="", big="", big_label="", cls="", tag="h2",
         href="", cta="", credit=""):
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
    cred = f'<span class="cred">{credit}</span>' if credit else ""
    return (f'<section class="band {E(cls)}" style="background-image:url({E(image)})">'
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
        out.append(f'<a class="chip" href="{BASE}cm/{E(s["key"])}/">{bi(s["th"], s["en"])}'
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
            f'<tr><td class="nm"><a href="{BASE}cm/{E(s["key"])}/">{bi(s["th"], s["en"])}</a></td>'
            f'<td class="r big">{n(tot)}</td>{pc("pin")}{pc("tel")}{pc("hrs")}{pc("live")}'
            + (f'<td class="r"><b>{n(wch)}</b></td>' if wch else '<td class="r z">—</td>')
            + "</tr>")
    return f'<div class="scroll"><table class="idx">{head}<tbody>{"".join(rows)}</tbody></table></div>'


def search_form(big=False):
    """The fleet search, motdang.net/find. Nan 2026-09-21: it supersedes every earlier
    answer about a box on the front page."""
    cls = "q big" if big else "q"
    return (f'<form class="{cls}" action="{BASE}find" method="get" role="search">'
            f'<input type="search" name="q" aria-label="ค้นหา · search" '
            f'placeholder="ค้นหา · search">'
            f'<button type="submit">ค้นหา · Search</button>'
            f'<button type="submit" name="lucky" value="1" class="alt">ลองโชค · Lucky</button>'
            f'</form>')


def near_block():
    """NEAR — the two cities, and the four doors that answer from where you stand."""
    cards = []
    for k, th, en in (("cm", "เชียงใหม่", "Chiang Mai"), ("cr", "เชียงราย", "Chiang Rai")):
        cards.append(f'<a class="card place" href="{BASE}{k}/"><h3>{bi(th, en)}</h3>'
                     f'<p class="fig">{n(TOT[k])}<small>สถานที่ · places</small></p></a>')
    doors = "".join(
        f'<a class="chip" href="{BASE}{h}">{bi(th, en)}</a>'
        for h, th, en in (("map.html", "แผนที่", "Map"), ("here.html", "ตรงนี้", "Here"),
                          ("toilets.html", "ห้องน้ำ", "Toilets"), ("chuai.html", "ช่วย", "Help, nearest")))
    # THE READER'S OWN CHIP (Nan, 2026-09-21). It is the only thing in this row
    # that is not true for everybody, so it is `hidden` in the served HTML and
    # revealed by PLAN_CHIP_JS only for a reader who already has a plan.
    # Drawn here rather than by nownear_layer.strip(): that line also carries
    # the weather, the air reading and ตรงนี้, and this page already prints all
    # three — a second PM2.5 two headings above the first reads as a bug. What
    # the old strip had and this page did not is the plan, so that is what
    # comes back.
    doors += f'<a class="chip nnplan" href="{BASE}plan.html" hidden></a>'
    return f'<div class="grid two">{"".join(cards)}</div><div class="chips">{doors}</div>'


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


def _same_event(a, b):
    """The newsletter says 'Payap presents Lanna Thai Music', the calendar says
    'Lanna Thai Music: An Interactive Lecture…'. One event, two spellings. The shared
    run of characters is what gives it away."""
    m = difflib.SequenceMatcher(None, a, b, autojunk=False).find_longest_match(
        0, len(a), 0, len(b))
    return m.size >= 14


def soon_rows(k=7):
    """SOON — dated things, nearest first. Events carry the source that announced them."""
    rows = []

    def away(d):
        n_ = (datetime.date.fromisoformat(d) - TODAY).days
        return "today" if not n_ else f"+{n_}d"

    ev = sorted((e for e in EVENTS["events"] if (e.get("start") or "")[:10] >= TODAY.isoformat()),
                key=lambda e: e["start"])
    # The same event arrives from a newsletter AND from its own calendar, under two
    # spellings. Keep one per day: the longer title wins, and a row with a source link
    # beats one without.
    kept = {}
    for e in ev:
        t = (e.get("title") or "").strip()
        if not t:
            continue
        d = e["start"][:10]
        low = t.lower()
        drop = None
        for (dd, tt), prev in kept.items():
            if dd != d:
                continue
            a, b = low, tt.lower()
            if _same_event(low, tt.lower()):
                keep_new = (bool(e.get("url")), len(t)) > (bool(prev.get("url")), len(tt))
                if not keep_new:
                    drop = "skip"
                else:
                    drop = (dd, tt)
                break
        if drop == "skip":
            continue
        if drop:
            kept.pop(drop)
        kept[(d, t)] = e
    for (d, t), e in sorted(kept.items())[:k]:
        title = E(t if len(t) < 84 else t[:81] + "…")
        if e.get("url"):
            title = f'<a href="{E(e["url"])}" rel="noopener">{title} <span class="out">↗</span></a>'
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
        out.append(f'<div class="card live"><h3>{bi(p["th"], p["en"])}</h3>'
                   f'<p class="fig" style="--c:{E(b["colour"])}">{p["pm25"]:g}'
                   f'<small>PM2.5 µg/m³</small></p>'
                   f'<p class="small mute">{E(b["th"])} · {E(b["en"])} · '
                   f'{E(p["observed"][11:16])} น.</p></div>')
    return "".join(out)


def pinned_cards():
    out = []
    for href, th, en, line in PINNED:
        ext = ' rel="noopener"' if href.startswith("http") else ""
        mark = ' <span class="out" title="another site">↗</span>' if href.startswith("http") else ""
        url = href if href.startswith("http") else BASE + href
        out.append(f'<div class="card"><h3><a href="{E(url)}"{ext}>{E(en)}{mark}</a></h3>'
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
                    f'<td class="r">{"✕ " + str(fails) if fails else "ok"}</td></tr>')
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
.chip b{font-family:var(--mono);font-size:.78rem;color:var(--mute)}
.chip:hover b{color:var(--hot)}
/* .chip is display:inline-flex, which beats the [hidden] attribute — without
   this the reader's plan chip shows on every visit as an empty box. */
.chip[hidden]{display:none}
.chip.nnplan{border-color:var(--hot);font-family:var(--mono);font-size:.82rem}
.scroll{overflow-x:auto;margin:1rem 0 2rem;border:2px solid var(--line)}
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
form.q{display:flex;gap:.35rem;flex:1 1 18rem;min-width:0;margin:0;align-items:stretch}
form.q input[type=search]{flex:1 1 auto;min-width:0;font:inherit;font-size:.92rem;
 padding:.3rem .55rem;border:2px solid var(--line);background:var(--panel);color:var(--ink);
 border-radius:0;-webkit-appearance:none}
form.q input[type=search]:focus{border-color:var(--ink);outline:0}
form.q button{font-family:var(--display);font-size:.78rem;font-weight:800;letter-spacing:.06em;
 text-transform:uppercase;padding:.3rem .7rem;border:2px solid var(--ink);background:var(--hot);
 color:#fff;cursor:pointer;white-space:nowrap}
form.q button.alt{background:var(--bg);color:var(--ink)}
form.q button:hover{box-shadow:2px 2px 0 var(--ink)}
@media(max-width:52rem){
 form.q{order:3;flex:1 0 100%;margin:.4rem 0 .1rem}
 form.q button.alt{display:none}
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
"""

NAV = [("#near", "ใกล้ๆ", "near"), ("#now", "ตอนนี้", "now"), ("#soon", "เร็วๆ นี้", "soon"),
       ("#shelves", "หมวด", "shelves"), ("#index", "สารบัญ", "index"),
       ("#deep", "เจาะลึก", "deep"), ("#elsewhere", "ที่อื่น", "elsewhere")]

nav = "".join(f'<a href="{h}"><span class="th" lang="th">{E(th)}</span> {E(en)}</a>' for h, th, en in NAV)

hero = band(
    "site/hero/temple-square-dusk.jpg", cls="tall", tag="h1",
    kicker="เชียงใหม่ · เชียงราย — Chiang Mai & Chiang Rai",
    head='มดแดง <span class="en">Mot Dang</span>',
    line=f"{n(ALL)} places in two provinces, {n(PINS)} of them on the map. "
         f"{len(SHELVES)} shelves, and every one says what it holds before you open it.",
    credit='Nan · <a href="https://creativecommons.org/licenses/by/4.0/">CC BY 4.0</a>')

midband = band(
    "site/hero/khao-soi-plate.jpg", cls="short",
    big=n(TOT["cm"]), big_label="in Chiang Mai alone",
    credit='Nan · <a href="https://creativecommons.org/licenses/by/4.0/">CC BY 4.0</a>')

endband = band(
    "site/hero/sunset-trees-1.jpg", cls="short",
    kicker="ประตู · the door",
    head="Add a place, or take the whole thing",
    line="Everything here is CC BY 4.0, and the API answers without a key.",
    href=BASE + "api/", cta="The API",
    credit='Nan · <a href="https://creativecommons.org/licenses/by/4.0/">CC BY 4.0</a>')

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
        <p class="lede">Mot Dang is a directory of Chiang Mai and Chiang Rai — shops, wats,
        clinics, markets, schools, repairs — kept in one file per province and rebuilt
        every day.</p>
        <p>Each shelf below is a page. The table says what that page can do for you before
        you open it: how many of its records carry a pin, a phone, opening hours, a website
        that answered when it was last checked.</p>
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
    <p>Pick a province, or go straight to the four that answer from where you stand.</p>
    {near_block()}

    <h2 id="now">ตอนนี้ <span class="en">Now</span></h2>
    <div class="grid">
      {air_cards()}
      <div class="card live"><h3>{bi('วันนี้', 'Today')}</h3>
        <p class="fig">{TODAY.day}<small>{E(TODAY.strftime('%B %Y'))} · พ.ศ. {TODAY.year + 543}</small></p>
        <p class="small mute">the whole catalogue rebuilt this morning</p></div>
      <div class="card live"><h3>{bi('ฉุกเฉิน', 'Emergency')}</h3>
        <p class="fig"><a href="tel:1669">1669</a><small>ambulance · เจ็บป่วยฉุกเฉิน</small></p>
        <p class="small mute">191 ตำรวจ · 199 ดับเพลิง · 1155 ตำรวจท่องเที่ยว</p></div>
    </div>

    <h2 id="soon">เร็วๆ นี้ <span class="en">Soon</span></h2>
    <p>Dated, nearest first. Each carries the source that announced it.</p>
    {soon_rows()}

    <h2 id="shelves">หมวด <span class="en">Every shelf</span></h2>
    <p>{WORD[len(SHELVES)]} of them, largest first. The number is every record on that shelf in
    both provinces.</p>
    {chips()}

    {midband}

    <h2 id="index">สารบัญ <span class="en">The index</span></h2>
    <p>What each shelf actually holds. A percentage is of that shelf's own records — so
    <b>food</b> knows where nearly everything is and can phone most of it, while
    <b>hours</b> is the field the whole catalogue is thinnest on.</p>
    {index_table()}

    <h2 id="deep">เจาะลึก <span class="en">Pinned</span></h2>
    <p>Ten things built out past a list.</p>
    {pinned_cards()}

    <h2 id="elsewhere">ที่อื่น <span class="en">Elsewhere</span></h2>
    <p>Sites that share this one's data and its licence.</p>
    {roster_rows()}

    <h3>ลิงก์ออก <span class="en">Outbound</span></h3>
    <p>Every website a record carries gets checked, and the ones that stopped answering are
    counted rather than quietly dropped. Last sweep {E(LH['generated'])}:
    <b class="lead-n">{n(LH['ok'])}</b> of {n(LH['urls'])} answered, across
    {n(LH['domains'])} domains.
    <a href="{BASE}reach.html">The link-rot study</a>.</p>

    <h2 id="sources">ที่มา <span class="en">Sources</span></h2>
    {source_rows()}

    <h3>เครื่อง <span class="en">The machine</span></h3>
    <p>{len(feeds)} feeds harvest on their own clocks.
    {"All current." if not (stale or failing) else f"{failing} failing, {stale} older than a week."}</p>
    {feed_rows()}

    {endband}
    """

    page = f"""<!DOCTYPE html>
    <html lang="th"><head><meta charset="utf-8">
    <meta name="viewport" content="width=device-width,initial-scale=1,viewport-fit=cover">
    <title>มดแดง Mot Dang — เชียงใหม่ · เชียงราย</title>
    <meta name="description" content="{E(desc)}">
<link rel="canonical" href="{BASE}">
<link rel="icon" href="{BASE}logo/motdang-favicon.svg" type="image/svg+xml">
<meta property="og:site_name" content="มดแดง Mot Dang">
<meta property="og:title" content="มดแดง · Mot Dang">
<meta property="og:description" content="{E(desc)}">
<meta property="og:type" content="website">
<meta property="og:url" content="{BASE}">
<meta property="og:image" content="{BASE}site/hero/temple-square-dusk.jpg">
<meta name="twitter:card" content="summary_large_image">
    <style>{(CSSDIR / "kit.css").read_text()}
    {(CSSDIR / "bands.css").read_text()}
    {EXTRA}</style>
    </head><body>
<script type="application/json" id="md-home">{{"built":"{E(TODAY.isoformat())}","be":{TODAY.year + 543},"generator":"home_next.py","shelves":{len(SHELVES)},"records":{ALL},"find":{FIND.get("pages", 0)}}}</script>
    <a class="skip" href="#about">ข้ามไปเนื้อหา · Skip to content</a>
    <header class="top"><div class="in">
      <a class="brand" href="{BASE}">MOT <b>DANG</b></a>
      {search_form()}
      <nav>{nav}</nav>
      <div class="langsw"><a href="#" aria-current="true">TH+EN</a></div>
    </div></header>
    <main>{body}</main>
    {PLAN_CHIP_JS}
    <footer class="bot"><div class="in">
      <p><b>มดแดง Mot Dang</b> — เชียงใหม่ · เชียงราย. Built by NaN,
      <a href="https://wichaa.net/">wichaa.net</a>. Text and data
      <a href="https://creativecommons.org/licenses/by/4.0/">CC BY 4.0</a>;
      pins and much of the ground truth © OpenStreetMap contributors, ODbL.
      Photographs on this page by Nan, CC BY 4.0.</p>
      <p class="small"><a href="{BASE}find">ค้นหา · search</a> ·
      <a href="{BASE}find?adv=1">ตรรกะ · boolean</a> ·
      <a href="{BASE}advanced.html">กรองสถานที่ · place filters</a> ·
      <a href="{BASE}api/">API</a> · Rebuilt {E(TODAY.isoformat())} · พ.ศ. {TODAY.year + 543}</p>
    </div></footer>
    </body></html>
    """
    return page


if __name__ == "__main__":
    out = DOCS / "index.html"
    out.write_text(render())
    print("wrote", out, out.stat().st_size, "bytes")
