#!/usr/bin/env python3
"""A front page for motdang.net in the minisite house style, with GitHub's
discoverability structures: an About rail, topic chips, a repository-style index
of every shelf, pinned minisites, and an outbound Elsewhere.

Reads mot-dang's data read-only (the tower is hot) and writes index.html here.
"""
import datetime
import difflib
import glob
import html
import json
import os
import pathlib
import subprocess
import sys

HERE = pathlib.Path(__file__).resolve().parent
MD = pathlib.Path.home() / "Developer/claude code projects/mot-dang"
KIT = pathlib.Path.home() / "Developer/claude code projects/mhs-loop/tools"
BANDS = pathlib.Path.home() / "Developer/claude code projects/site-kit"
sys.path.insert(0, str(KIT))
sys.path.insert(0, str(HERE))
import css as kit_css  # noqa: E402
import homebits  # noqa: E402
from homebits import icon  # noqa: E402

BASE = "https://motdang.net/"
TODAY = datetime.date.today()

# THE STACK (Nan, 2026-09-21): near, then now, then soon. In that order, always.
# The one thing allowed above them is a called-out festival or event, and only when she
# says so — set CALLOUT to a dict and it draws a band over the whole stack.
#   CALLOUT = {"pic": "img/x.jpg", "kicker": "...", "head": "...", "line": "...",
#              "href": "...", "cta": "..."}
CALLOUT = None


WORD = {25: "Twenty-five", 26: "Twenty-six", 27: "Twenty-seven", 28: "Twenty-eight",
        29: "Twenty-nine", 30: "Thirty"}


def E(x):
    return html.escape("" if x is None else str(x), quote=True)


def j(p):
    return json.loads((MD / "data" / p).read_text())


P = json.loads((HERE / "payload.json").read_text())
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
_CRAWL = MD / "cache/fleetsearch/crawl.json"
FIND = json.loads(_CRAWL.read_text()) if _CRAWL.exists() else {}

_COUNTS = HERE / "amphoe_counts.json"
if _COUNTS.exists():
    AMPHOE_COUNTS = json.loads(_COUNTS.read_text())
else:
    import mapart  # noqa: E402
    AMPHOE_COUNTS = mapart.count_by_amphoe(mapart.Proj())
    _COUNTS.write_text(json.dumps(AMPHOE_COUNTS))

AIR = j("air.json")
EVENTS = j("events.json")
SKY = j("sky.json")
FLEET = json.loads((MD / "data/curated/fleet.json").read_text())

# ---- how fresh is the machine: every harvester writes a .meta.json
feeds, stale, failing = [], 0, 0
for p in sorted(glob.glob(str(MD / "data/*.meta.json"))):
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
    ("merit.html", "ไหว้พระ ๙ วัด", "Nine Wats", "i-wat", "the merit round, walkable, in order"),
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
    ("https://commons.wikimedia.org/", "Wikimedia Commons", "the borrowed photographs, each credited", "CC BY / BY-SA"),
    # data.bopp-obec.info is where the register itself lives; it did not resolve from
    # here on 2026-09-21, so the credit points at the office instead.
    ("https://www.obec.go.th/", "สพฐ. · OBEC", "the school register", "public"),
]


# ---------------------------------------------------------------- pieces

def band(image, kicker="", head="", line="", big="", big_label="", cls="", tag="h2",
         href="", cta="", credit="", extra=""):
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
        out.append(f'<a class="chip" href="{BASE}cm/{E(s["key"])}/">'
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
            f'<tr><td class="nm"><a href="{BASE}cm/{E(s["key"])}/">'
            f'{icon(homebits.CAT_ICON[s["key"]], 18)}{bi(s["th"], s["en"])}</a></td>'
            f'<td class="r big">{n(tot)}</td>{pc("pin")}{pc("tel")}{pc("hrs")}{pc("live")}'
            + (f'<td class="r"><b>{n(wch)}</b></td>' if wch else '<td class="r z">—</td>')
            + "</tr>")
    return f'<div class="scroll"><table class="idx">{head}<tbody>{"".join(rows)}</tbody></table></div>'


def search_form(big=False):
    """The fleet search, motdang.net/find. Nan 2026-09-21: it supersedes every earlier
    answer about a box on the front page — and, the same day, the box was too small to
    use, so the page's own search is now the size of the thing it searches."""
    cls = "q big" if big else "q"
    pages = n(FIND.get("pages", 0))
    hint = (f'<p class="qhint">{pages} pages across twenty sites — places, festivals, '
            f'articles, the lot.</p>' if big and FIND.get("pages") else "")
    return (f'<form class="{cls}" action="{BASE}find" method="get" role="search">'
            f'<label class="qbox">{icon("i-search", 26, "rowicon qi")}'
            f'<input type="search" name="q" aria-label="ค้นหา · search" '
            f'placeholder="ค้นหา · search"></label>'
            f'<button type="submit">{icon("i-search", 20)}'
            f'<span>ค้นหา · Search</span></button>'
            f'<button type="submit" name="lucky" value="1" class="alt">'
            f'{icon("i-dice", 20)}<span>ลองโชค · Lucky</span></button>'
            f'{hint}</form>')


DOORS = (("map.html", "แผนที่", "Map", "i-map"), ("here.html", "ตรงนี้", "Here", "i-here"),
         ("toilets.html", "ห้องน้ำ", "Toilets", "i-loo"),
         ("chuai.html", "ช่วย", "Help, nearest", "i-sos"))


def near_block():
    """NEAR — the map first, at the size of the thing it draws, then the two provinces
    and the doors that answer from where you stand."""
    cards = []
    for k, th, en in (("cm", "เชียงใหม่", "Chiang Mai"), ("cr", "เชียงราย", "Chiang Rai")):
        cards.append(f'<a class="card place" href="{BASE}{k}/"><h3>{bi(th, en)}</h3>'
                     f'<p class="fig">{n(TOT[k])}<small>สถานที่ · places</small></p></a>')
    doors = "".join(
        f'<a class="chip" href="{BASE}{h}">{icon(ic, 20)}{bi(th, en)}</a>'
        for h, th, en, ic in DOORS)
    # THE READER'S OWN CHIP (Nan, 2026-09-21). The only thing in this row that is not
    # true for everybody, so it ships `hidden` and PLAN_CHIP_JS — which lives in
    # home_next.py, the page this draft feeds — reveals it for a reader who has a plan.
    doors += f'<a class="chip nnplan" href="{BASE}plan.html" hidden></a>'
    return (f'<div class="mapband"><div class="in">'
            f'{homebits.big_map(AMPHOE_COUNTS, "img/", HERE / "img")}'
            f'<div class="maprail">'
            f'<div class="grid two twocards">{"".join(cards)}</div>'
            f'<a class="btn wide" href="{BASE}map.html">{icon("i-map", 22)}'
            f'<span>เปิดแผนที่ · Open the live map</span></a>'
            f'<p class="small mute">The live map carries {n(PINS)} pins, '
            f'{len(SHELVES)} shelves to switch between, and a ring on what is open now.</p>'
            f'<div class="chips">{doors}</div>'
            f'</div></div></div>')


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
        out.append(f'<div class="card live"><h3>{icon("i-air", 20)}{bi(p["th"], p["en"])}</h3>'
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
/* THE SEARCH (Nan, 2026-09-21: "search bar way too small"). The header box is now
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
.days{grid-auto-rows:8.4rem}
.day{padding:.34rem .4rem;font-size:.74rem;overflow:hidden;
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
@media(max-width:46rem){
 .days{grid-auto-rows:5.2rem}
 .day{font-size:.66rem;padding:.24rem .26rem}
 .day ul.ev{display:none}
 .day .lun{font-size:.54rem}
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

NAV = [("#near", "ใกล้ๆ", "near", "i-near"), ("#now", "ตอนนี้", "now", "i-clock"),
       ("#soon", "เร็วๆ นี้", "soon", "i-cal"), ("#shelves", "หมวด", "shelves", "i-layers"),
       ("#index", "สารบัญ", "index", "i-list"), ("#deep", "เจาะลึก", "deep", "i-star"),
       ("#elsewhere", "ที่อื่น", "elsewhere", "i-globe")]

nav = "".join(f'<a href="{h}">{icon(ic, 18)}<span class="th" lang="th">{E(th)}</span> {E(en)}</a>'
              for h, th, en, ic in NAV)

hero = band(
    "img/temple-square-dusk.jpg", cls="tall", tag="h1",
    kicker="เชียงใหม่ · เชียงราย — Chiang Mai & Chiang Rai",
    head='มดแดง <span class="en">Mot Dang</span>',
    line=f"{n(ALL)} places in two provinces, {n(PINS)} of them on the map. "
         f"{len(SHELVES)} shelves, and every one says what it holds before you open it.",
    extra=search_form(big=True),
    credit='Nan · <a href="https://creativecommons.org/licenses/by/4.0/">CC BY 4.0</a>')

midband = band(
    "img/khao-soi-plate.jpg", cls="short",
    big=n(TOT["cm"]), big_label="in Chiang Mai alone",
    credit='Nan · <a href="https://creativecommons.org/licenses/by/4.0/">CC BY 4.0</a>')

endband = band(
    "img/sunset-trees-1.jpg", cls="short",
    kicker="ประตู · the door",
    head="Add a place, or take the whole thing",
    line="Everything here is CC BY 4.0, and the API answers without a key.",
    href=BASE + "api/", cta="The API",
    credit='Nan · <a href="https://creativecommons.org/licenses/by/4.0/">CC BY 4.0</a>')

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
<p>The whole catalogue, drawn — one dot per place, so the cities and the roads between
them are the shops along them. Tap a district to open it in the live map.</p>
{near_block()}

<h2 id="now">ตอนนี้ <span class="en">Now</span></h2>
<div class="grid">
  {air_cards()}
  <div class="card live"><h3>{icon('i-cal', 20)}{bi('วันนี้', 'Today')}</h3>
    <p class="fig">{TODAY.day}<small>{E(TODAY.strftime('%B %Y'))} · พ.ศ. {TODAY.year + 543}</small></p>
    <p class="small mute">the whole catalogue rebuilt this morning</p></div>
  <div class="card live"><h3>{icon('i-sos', 20)}{bi('ฉุกเฉิน', 'Emergency')}</h3>
    <p class="fig"><a href="tel:1669">1669</a><small>ambulance · เจ็บป่วยฉุกเฉิน</small></p>
    <p class="small mute">191 ตำรวจ · 199 ดับเพลิง · 1155 ตำรวจท่องเที่ยว</p></div>
</div>

<h2 id="soon">เร็วๆ นี้ <span class="en">Soon</span></h2>
<p>Two months, drawn. Each square carries the day's colour, the moon as it will be
that night, and anything dated into it.</p>
{homebits.calendar(TODAY, k_events=2)}

<h3>รายการ <span class="en">The same days, as a list</span></h3>
<p>Nearest first. Each carries the source that announced it.</p>
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
<meta name="description" content="A directory of Chiang Mai and Chiang Rai: {n(ALL)} places, {len(SHELVES)} shelves, {n(PINS)} on the map.">
<style>{kit_css.CSS}
{(BANDS / 'bands.css').read_text()}
{EXTRA}</style>
</head><body>
{homebits.sprite_defs()}
<a class="skip" href="#about">ข้ามไปเนื้อหา · Skip to content</a>
<header class="top"><div class="in">
  <a class="brand" href="{BASE}">MOT <b>DANG</b></a>
  {search_form()}
  <nav>{nav}</nav>
  <div class="langsw"><a href="#" aria-current="true">TH+EN</a></div>
</div></header>
<main>{body}</main>
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
(HERE / "index.html").write_text(page)
print("wrote", HERE / "index.html", len(page), "bytes")
print("shelves", len(SHELVES), "feeds", len(feeds), "failing", failing, "stale", stale)
