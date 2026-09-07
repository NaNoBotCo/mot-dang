#!/usr/bin/env python3
"""here_layer.py — /here.html, the site opening where the reader is standing.

WHY THIS EXISTS
---------------
Nan, 2026-09-06: "if I open motdang.net standing in the old city, I'd
appreciate it if it actually just loaded up a map to where I am, instead of
generic homepage boilerplate. Help me get oriented, tell me what's nearby,
navigate me, give me shareable information."

Every map on this site is a door into the directory; none of them opens on
the reader. /map.html has a near-me button, but it flies to a point and then
stops — it does not say where that point IS, or what is around it, or how to
get from it to anything. /chuai.html answers "what is nearest" for five
lifeline kinds and nothing else. This page is the general form of both: one
position, and from it four answers in order — where you are, what is around
you, how to reach it, and how to hand any of that to somebody else.

WHAT IT LOADS, AND WHY NOT MORE
-------------------------------
The catalogue is 22,000 pinned places. A phone in the old city should not
pull that down to learn about the six hundred within a kilometre, and it
should not pull down a whole shelf either (cm-food.geojson is 1.3 MB). So the
build tiles every pinned record into 0.01° cells — about 1.1 km on a side —
under data/here/, and the page fetches the nine cells around the reader:
their own and the eight neighbours, which guarantees at least 1.1 km of
coverage in every direction. Each row is one compact array; opening-hour
intervals travel inside it so "open now" is a subtraction on the device, not
a second request for a 680 kB file.

THE FOUR RULES THIS PAGE KEEPS
------------------------------
1. It asks for a position through MDLOC in md.js — the one door on this site
   that may put that question to a reader — and never on load, unless the
   reader has themselves set the switch on this page that says to. Even then,
   nothing is asked: the switch only takes effect once the browser already
   reports the permission as granted, so the OS dialog never appears
   unbidden. The switch is a preference (`md-here`), not a coordinate.
2. A position is never written to disk and never written into the URL by the
   page. The one link that carries a position is built by a tap on a button
   whose label says the link carries it. tests/test_here.py holds this: the
   JS may not call replaceState or pushState at all.
3. A place with no hours on record is not closed. Open/closed is shown only
   where the place itself posted hours; everything else says nothing.
4. Distances are straight lines and say so. The route planner is one tap
   away for the real walk; the phone's own map app is one tap away for
   turn-by-turn (a geo: link, exactly as near.js already offers).

THE HOMEPAGE HALF (not in this file)
------------------------------------
"Open motdang.net and land here" is one line in build.py's page() — a hop
from index.html to here.html when `md-here` is set AND the geolocation
permission is already granted AND the reader did not just come from here
(sessionStorage `md-stay`). It is a build.py edit, so it ships separately;
notes/here-2026-09-06.txt carries the exact snippet. Until then the switch
on this page does what its label says on THIS page: bookmark /here and it
opens on you.

Entry point: emit(globals_of_build, data). Writes docs/here.html, here.js,
here.css, data/here/<cell>.json, and (via nearby.py) near.js.
"""

import json
import math
import zlib
from pathlib import Path

import nearby

ROOT = Path(__file__).resolve().parent

# 0.01° — the cell. ~1,112 m north–south everywhere; ~1,053 m east–west at
# 18.8° N. Nine of these is a 3.2 km square, which is a fair morning's walk
# and a few hundred kilobytes at the old city's density, less anywhere else.
CELL = 0.01
CELL_DIR = "data/here"

# Kinds in the order a person standing on a pavement wants them. Anything in
# categories.json that is not named here still appears — after these, in
# catalogue order. This is a display order, not a filter.
PRIORITY = ["food", "wat", "essentials", "market", "massage", "medical",
            "sights", "shopping", "parks", "museums-galleries", "hotel",
            "transport", "cooking", "beauty", "muaythai", "whats-on", "sport",
            "tattoo", "cannabis", "school", "community", "pets", "repair",
            "home-services", "business", "realestate", "school-intl", "chang"]

# Same six inks as /map.html, for the same reason (see explore_layer.INKS).
# Imported rather than restated so the two maps can never disagree about
# what "ant red" is.
from explore_layer import INKS  # noqa: E402


def cell_key(lat, lng):
    """Which file a coordinate lives in. Mirrored exactly in the JS
    (Math.floor(lat*100)): multiply, not divide by 0.01, because the two
    are not the same number in floating point and a cell boundary is where
    that difference would put a place in a file the page never asks for."""
    return "%d_%d" % (math.floor(lat * 100), math.floor(lng * 100))


def _lamps():
    """place id -> opening intervals in minutes from Monday 00:00, from the
    same file the lamp map and /map.html read. Empty dict when absent."""
    p = ROOT / "data" / "open_lamps.json"
    if not p.exists():
        return {}
    try:
        d = json.loads(p.read_text())
    except (ValueError, OSError):
        return {}
    sched = d.get("schedules") or []
    out = {}
    for pl in d.get("places") or []:
        k = pl.get("k")
        if isinstance(k, int) and 0 <= k < len(sched) and pl.get("id"):
            out[pl["id"]] = sched[k]
    return out


def rows(g, data, lamps=None):
    """Every pinned, published place, bucketed by cell.

    Row = [lat, lng, prov, slug, nameTh, nameEn, cat, sub, rank, hours, tel]
      hours: list of [start, end] week-minute intervals, or 0 when the place
             has never said. 0 rather than [] so the JS can tell "no hours"
             from "posted hours, none today" without a second flag.
      tel:   the phone as written, or "".
    """
    CATS, place_slug = g["CATS"], g["place_slug"]
    name_pair, ant_rank, held = g["name_pair"], g["ant_rank"], g["held"]
    lamps = _lamps() if lamps is None else lamps
    cells = {}
    seen = set()
    for prov in ("cm", "cr"):
        for r in data.get(prov) or []:
            if r.get("lat") is None or r.get("lng") is None:
                continue
            if (r.get("geoPrecision") or "exact") == "needs-pin":
                continue
            if held(r):
                continue
            slug = place_slug(r)
            # One page, one row. The catalogue holds a few dozen records twice
            # under different ids (same name, same pin — 75 on 2026-09-06, all
            # in `repair`); they share a slug and therefore a page, and a list
            # that named the same shop twice would look like a bug in the list.
            if (prov, slug) in seen:
                continue
            seen.add((prov, slug))
            cats = r.get("cat") or []
            cat = next((c for c in cats if c in CATS), cats[0] if cats else "")
            sub = (r.get("sub") or [""])[0] or ""
            th, en = name_pair(r)
            la, ln = round(r["lat"], 5), round(r["lng"], 5)
            row = [la, ln, prov, slug, th, en, cat, sub, ant_rank(r) or 0,
                   lamps.get(r["id"], 0), (r.get("phone") or "").strip()]
            # Keyed on the ROUNDED pair, which is what the file holds and what
            # any reader of the file would compute: 18.789996 rounds to 18.79
            # and belongs to cell 1879, not 1878.
            cells.setdefault(cell_key(la, ln), []).append(row)
    return cells


def _gates(g, data):
    """The five gates and four corners, from the catalogue, with the slug of
    each one's own page. Same ids the moat drawing uses; a gate missing from
    the records is a catalogue gap, never a literal typed here."""
    ids = list(g["MOAT_CROSSING_IDS"])
    corners = set(g["MOAT_CORNER_IDS"].values())
    by_id = {r["id"]: r for r in data.get("cm") or []}
    out = []
    for i in ids:
        r = by_id.get(i)
        if not r or r.get("lat") is None:
            continue
        th, en = g["name_pair"](r)
        if not th or not en:
            continue
        out.append([round(r["lat"], 5), round(r["lng"], 5), th, en,
                    "corner" if i in corners else "gate", g["place_slug"](r)])
    return out


def _zones():
    """ย่าน — the named parts of town, as data/curated/zones.json draws them.
    Boxes first, then circles, same precedence the shelf split uses."""
    p = ROOT / "data" / "curated" / "zones.json"
    if not p.exists():
        return {"boxes": [], "circles": []}
    z = json.loads(p.read_text()).get("cm") or {}
    boxes = [[b["lat"][0], b["lat"][1], b["lng"][0], b["lng"][1], b["th"], b["en"]]
             for b in z.get("boxes") or []]
    circles = [[c["lat"], c["lng"], c.get("r_km") or 8, c["th"], c["en"]]
               for c in z.get("circles") or []]
    return {"boxes": boxes, "circles": circles}


def _cat_labels(g):
    CATS, CAT_ORDER = g["CATS"], g["CAT_ORDER"]
    cats = {c: [CATS[c]["th"], CATS[c]["en"]] for c in CAT_ORDER}
    subs = {}
    for c in CAT_ORDER:
        for ch in CATS[c].get("children") or []:
            if ch.get("key") and ch.get("th"):
                subs[ch["key"]] = [ch["th"], ch.get("en") or ""]
    order = [c for c in PRIORITY if c in CATS] + \
            [c for c in CAT_ORDER if c not in PRIORITY]
    return cats, subs, order


def _js(g, data):
    cats, subs, order = _cat_labels(g)
    moat = [[round(p[0], 5), round(p[1], 5)] for p in (g["MOAT_POLY"] or [])]
    dump = lambda o: json.dumps(o, ensure_ascii=False, separators=(",", ":"))
    return (JS.replace("%GATES%", dump(_gates(g, data)))
              .replace("%ZONES%", dump(_zones()))
              .replace("%CATS%", dump(cats))
              .replace("%SUBS%", dump(subs))
              .replace("%ORDER%", dump(order))
              .replace("%MOAT%", dump(moat))
              .replace("%INKS%", dump([i[0] for i in INKS]))
              .replace("%BASE%", dump(g["BASE"])))


def version(js_text):
    """`?v=` for here.js and here.css — the site serves .js a week from cache
    under a fixed name, and a stale here.js against a fresh page is a page
    with no list. Hashed over the shipped text, embedded data included."""
    return "%08x" % (zlib.crc32((js_text + CSS).encode("utf-8")) & 0xFFFFFFFF)


def build_page(g, data, v, near_v):
    bi, bi_text, att, esc = g["bi"], g["bi_text"], g["att"], g["esc"]
    page, share_block, BASE = g["page"], g["share_block"], g["BASE"]
    map_shell = g["map_shell"]
    gates = _gates(g, data)
    zones = _zones()

    lede_th = ("แตะปุ่มเดียว แล้วหน้านี้จะบอกว่าคุณยืนอยู่ตรงไหนของเมือง "
               "มีอะไรอยู่ใกล้ ๆ ไปทางไหน และส่งให้เพื่อนได้ทั้งจุดที่ยืน ทั้งร้าน ทั้งภาพแผนที่")
    lede_en = ("One tap and this page says where in the city you are standing, "
               "what is around you and which way, and lets you send any of it on — "
               "the spot, the place, or the map itself.")

    # The drawn fallback in the map box: the moat and its gates. With tiles it
    # is covered within the second; without them it is what the reader keeps,
    # and it is not nothing — it is the one shape everybody here steers by.
    moat = g["MOAT_POLY"]
    fb = ['<svg viewBox="0 0 720 420" width="100%%" class="hdraw" role="img" '
          'aria-label="%s">' % att(bi_text(
              "แผนที่เมืองเก่าเชียงใหม่ — กดปุ่มด้านบนเพื่อหาตำแหน่งของคุณ",
              "The old city of Chiang Mai — press the button above to find yourself on it")),
          '<rect class="mdmap-bg" width="720" height="420" fill="#FBF6EE"/>']
    if moat:
        lat = [p[0] for p in moat]
        lng = [p[1] for p in moat]
        s_, n_ = min(lat), max(lat)
        w_, e_ = min(lng), max(lng)
        pad = max(n_ - s_, e_ - w_) * 0.6
        s_, n_, w_, e_ = s_ - pad, n_ + pad, w_ - pad, e_ + pad
        X = lambda ln: (ln - w_) / (e_ - w_) * 720
        Y = lambda la: (n_ - la) / (n_ - s_) * 420
        fb.append('<polygon class="mdmap-bg" points="%s" fill="none" '
                  'stroke="#6E8CA0" stroke-width="2.2" stroke-dasharray="5 4"/>'
                  % " ".join("%.1f,%.1f" % (X(p[1]), Y(p[0])) for p in moat))
        for gl in gates:
            if not (s_ <= gl[0] <= n_ and w_ <= gl[1] <= e_):
                continue
            gx, gy = X(gl[1]), Y(gl[0])
            fb.append('<g data-mdpin="%.1f,%.1f"><title>%s</title>'
                      '<path d="M%.1f %.1fl4.6 4.6-4.6 4.6-4.6-4.6z" fill="#FFFCF6" '
                      'stroke="#4A6373" stroke-width="1.7"/></g>'
                      % (gx, gy, att(bi_text(gl[2], gl[3])), gx, gy - 4.6))
    fb.append('</svg>')
    # Tha Phae Gate, the same default MDLOC falls back to: the map is never a
    # blank rectangle while it waits, and a reader who never presses the
    # button still gets the city.
    box = map_shell.mount("hmap", "".join(fb), prov="cm", zoom=15.2,
                          lat=18.7876, lng=98.9931, cls="mdmap hmap", full=True)

    # The fallback directory under the map — what a reader with scripting
    # off, or with no position to give, can still use. The gates link to
    # their own pages; the ย่าน names are the vocabulary the list above
    # speaks in, so they are printed even though they have no page of their own.
    glist = "".join(
        '<li><a href="cm/p/%s.html">%s</a> <span class="quiet">%s</span></li>'
        % (att(gl[5]), bi(gl[2], gl[3]),
           bi("แจ่ง", "corner") if gl[4] == "corner" else bi("ประตู", "gate"))
        for gl in gates)
    zlist = "".join('<li>%s</li>' % bi(z[4], z[5]) for z in zones["boxes"])

    body = (
        f'<h1>📍 {bi("ตรงนี้", "Here")}</h1>'
        f'<p class="lede">{bi(lede_th, lede_en)}</p>'
        f'<div class="hbar">'
        f'<button type="button" id="h-start" class="hbtn primary" data-gps-door>'
        f'{bi("📍 เริ่มจากตรงนี้", "Start where I am")}</button>'
        f'<button type="button" id="h-me" class="hbtn" hidden>'
        f'{bi("⌖ กลับมาที่ฉัน", "Back to me")}</button>'
        f'<button type="button" id="h-share" class="hbtn" hidden>'
        f'{bi("🔗 ส่งจุดนี้", "Send this spot")}</button>'
        f'<button type="button" id="h-shot" class="hbtn" hidden>'
        f'{bi("📷 ส่งภาพนี้", "Send this view")}</button>'
        f'<button type="button" id="h-face" class="hbtn" hidden aria-pressed="false">'
        f'{bi("🧭 หันตามเข็มทิศ", "Point as I turn")}</button>'
        f'<span id="h-status" class="hstatus" role="status"></span>'
        f'</div>'
        f'<div id="h-where" class="hwhere" hidden></div>'
        f'{box}'
        f'<p class="hhint">{bi("แตะจุดบนแผนที่เพื่อดูว่าเป็นที่ไหน · ระยะทางเป็นเส้นตรง", "Touch a dot to see what it is · distances are straight lines")}</p>'
        f'<div id="h-chips" class="hchips" aria-label="ชนิดที่แสดง · kinds shown"></div>'
        f'<div id="h-out" class="hout"></div>'
        f'<p id="h-sharebox" class="hsharebox" hidden></p>'
        f'<label class="hauto"><input type="checkbox" id="h-auto"> '
        f'{bi("เริ่มหาตำแหน่งทันทีเมื่อเปิดหน้านี้", "Start locating as soon as this page opens")}</label>'
        f'<p class="quiet hpriv">{bi("ตำแหน่งของคุณอยู่ในเครื่องคุณเท่านั้น ไม่ถูกส่งไปไหน ไม่ถูกเก็บ และไม่อยู่ในลิงก์ของหน้านี้ — ยกเว้นลิงก์ที่คุณกดปุ่ม “ส่งจุดนี้” สร้างเอง", "Your position stays on this device: not sent anywhere, not stored, and not in this page’s address — the only link that carries it is the one you make with “Send this spot”.")}</p>'
        f'<div class="hdir">'
        f'<h2>{bi("ประตูและแจ่งเมือง", "Gates and corners")}</h2>'
        f'<ul class="hgates">{glist}</ul>'
        f'<h2>{bi("ย่านที่หน้านี้รู้จัก", "The neighbourhoods this page speaks in")}</h2>'
        f'<ul class="hzones">{zlist}</ul>'
        f'<h2>{bi("ประตูอื่น", "Other doors")}</h2>'
        f'<ul class="hdoors">'
        f'<li><a href="map.html">{bi("แผนที่เมืองทั้งเมือง", "The whole city map")}</a></li>'
        f'<li><a href="plan.html">{bi("วางแผนเดินทาง — เดินกับขี่ให้คำตอบต่างกัน", "Plan a route — walking and riding answer differently")}</a></li>'
        f'<li><a href="toilets.html">{bi("ห้องน้ำใกล้ฉัน", "Toilets near you")}</a></li>'
        f'<li><a href="chuai.html">{bi("ช่วย — เบอร์ฉุกเฉินและที่ใกล้ที่สุด", "Help — emergency numbers and what is nearest")}</a></li>'
        f'</ul></div>'
        f'{share_block(BASE + "here.html", bi_text("ตรงนี้ — motdang.net", "Here — motdang.net"))}')

    # hub=False on purpose, though this is a doorstep: the full quick-action
    # grid is a screen and a half of furniture on a phone, and the whole point
    # of this page is that the map is the first thing under the header.
    return page("ตรงนี้ · Here", body, depth=0, path="here.html", hub=False,
                desc=lede_th,
                extra_head=f'<link rel="stylesheet" href="here.css?v={v}">'
                           f'<script src="near.js?v={near_v}" defer></script>'
                           f'<script src="here.js?v={v}" defer></script>')


CSS = """/* /here.html — the page that opens on the reader. */
.hmap{height:min(56vh,520px);margin:.5rem 0 .3rem}
@media (min-width:760px){.hmap{height:min(62vh,640px)}}
.hmap .mdmap-draw{height:100%}
.hmap .hdraw{height:100%;object-fit:cover}
.hbar{display:flex;gap:.5rem;align-items:center;flex-wrap:wrap;margin:.6rem 0 .3rem}
.hbtn{min-height:44px;padding:.4rem .9rem;border-radius:.6rem;font:inherit;
  font-weight:700;border:2px solid var(--ant);background:#fff;color:var(--ant-dark);cursor:pointer}
.hbtn.primary{background:var(--ant);color:#fff}
.hbtn:hover{filter:brightness(.96)}
.hbtn[aria-busy="true"]{opacity:.6}
.hstatus{color:var(--ink-soft);font-size:.9rem}
.hwhere{margin:.4rem 0 .2rem;padding:.7rem .9rem;border-radius:.7rem;
  background:var(--card-alt);border:1.5px solid var(--warm-border);line-height:1.45}
.hwhere b{font-size:1.08rem}
.hwhere .hacc{color:var(--gloss);font-size:.85rem}
.hhint{color:var(--gloss);font-size:.88rem;margin:.1rem 0 .6rem}
.hchips{display:flex;flex-wrap:wrap;gap:.4rem;margin:.2rem 0 .6rem}
.hchip{display:inline-flex;align-items:center;gap:.4rem;min-height:44px;
  padding:.35rem .8rem;border-radius:999px;border:1.5px solid var(--warm-border);
  background:#fff;font:inherit;cursor:pointer;color:var(--ink)}
.hchip .count{color:var(--gloss);font-size:.82rem}
.hchip .hsw{width:12px;height:12px;border-radius:50%;flex:none;
  background:var(--warm-border);border:1px solid var(--dashed)}
.hchip[aria-pressed="true"]{border-color:var(--ink);border-width:2px;background:var(--card-alt);font-weight:700}
.hchip[aria-pressed="false"] .hsw{background:var(--warm-border)!important}
.hkind{margin:1rem 0 .3rem;font-size:1rem;line-height:1.35}
.hkind .hsw{width:12px;height:12px;border-radius:50%;display:inline-block;margin-right:.4rem;vertical-align:middle}
.hkind .quiet{display:block;font-weight:400;font-size:.85rem}
.hrow{display:grid;grid-template-columns:1.6rem 1fr auto;gap:.15rem .6rem;
  align-items:baseline;padding:.45rem 0;border-bottom:1px solid var(--warm-border)}
.hrow .hdirw{font-size:1.15rem;color:var(--ant-dark);text-align:center}
.hrow .hnm a{font-weight:700;text-decoration:none}
.hrow .hsub{color:var(--ink-soft);font-size:.86rem;margin-left:.3rem}
.hrow .hkm{white-space:nowrap;font-variant-numeric:tabular-nums;color:var(--ink-soft)}
.hrow .hacts{grid-column:2/4;display:flex;flex-wrap:wrap;gap:.3rem .9rem;font-size:.9rem}
.hrow .hacts a{min-height:32px;display:inline-flex;align-items:center;text-decoration:none}
.hopen{font-size:.82rem;border-radius:999px;padding:.05rem .5rem;border:1px solid}
.hopen.yes{color:#1F6B57;border-color:#1F6B57}
.hopen.no{color:#8A4E2A;border-color:#B39058}
.hsoon{font-size:.82rem;color:var(--ant-dark);white-space:nowrap}
.hdirw{display:inline-block;transition:transform .12s linear}
.hdirw.live{color:var(--ant)}
@media (prefers-reduced-motion:reduce){.hdirw{transition:none}}
.hmore{font:inherit;background:none;border:0;color:var(--ant-dark);cursor:pointer;
  min-height:40px;padding:.2rem .4rem;font-weight:700}
.hsharebox{margin:.6rem 0;padding:.6rem .8rem;border-radius:.6rem;background:var(--card-alt);
  border:1.5px dashed var(--warm-border);word-break:break-all;font-size:.92rem}
.hauto{display:flex;gap:.6rem;align-items:flex-start;margin:1rem 0 .3rem;min-height:44px}
.hauto input{width:22px;height:22px;flex:none;margin-top:.15rem}
.hpriv{font-size:.86rem}
.hdir{margin-top:1.4rem;border-top:2px solid var(--warm-border);padding-top:.8rem}
.hdir h2{font-size:1rem;margin:.7rem 0 .3rem}
.hgates,.hzones,.hdoors{list-style:none;padding:0;margin:0;display:flex;flex-wrap:wrap;gap:.25rem 1rem}
.hgates li,.hzones li,.hdoors li{font-size:.95rem}
@media print{.hbar,.hchips,.hauto{display:none}}
"""

JS = r"""/* here.js — /here.html only. See here_layer.py for the four rules.

   Nothing in this file runs a geolocation request on load unless the reader
   set the switch on this page AND the browser already reports the permission
   as granted. Nothing here writes a position anywhere but the screen. */
(function(){
var GATES=%GATES%,ZONES=%ZONES%,CATS=%CATS%,SUBS=%SUBS%,ORDER=%ORDER%,
    MOAT=%MOAT%,INKS=%INKS%,BASE=%BASE%;
var PER=3,PER_MORE=10,MOVE_M=25;
var el=document.getElementById('hmap'),out=document.getElementById('h-out'),
    where=document.getElementById('h-where'),chipsEl=document.getElementById('h-chips'),
    status=document.getElementById('h-status'),bStart=document.getElementById('h-start'),
    bMe=document.getElementById('h-me'),bShare=document.getElementById('h-share'),
    bShot=document.getElementById('h-shot'),bFace=document.getElementById('h-face'),
    shareBox=document.getElementById('h-sharebox'),
    autoBox=document.getElementById('h-auto');
var here=null;          /* {lat,lng,acc,src} — 'gps' or 'link' */
var cells={};           /* key -> rows, [] once fetched and empty */
var rows=[];            /* every row in the loaded cells */
var off={};             /* cat -> true when the reader switched it off */
var more={};            /* cat -> true when expanded */
var map=null,watchId=null,flown=false;

function root(){return document.documentElement.getAttribute('data-root')||'';}
function bi(th,en){return window.MDNear?MDNear.bi(th,en):th+' · '+en;}
function esc(t){return window.MDNear?MDNear.esc(t):String(t==null?'':t);}
function say(th,en){if(!status)return;status.innerHTML=(th||en)?bi(th,en):'';}
/* A passing message ("looking around you…") clears itself; a standing one
   (the door is gone, the signal dropped) stays until something replaces it. */
var passing=false;
function busy(th,en){say(th,en);passing=true;}
function unbusy(){if(passing){say('','');passing=false;}}

/* ---- geometry --------------------------------------------------------- */
function km(a,b,c,d){return MDNear.km(a,b,c,d);}
function bearing(a,b,c,d){var t=Math.PI/180,y=Math.sin((d-b)*t)*Math.cos(c*t),
  x=Math.cos(a*t)*Math.sin(c*t)-Math.sin(a*t)*Math.cos(c*t)*Math.cos((d-b)*t);
  return (Math.atan2(y,x)*180/Math.PI+360)%360;}
var ARROWS=['↑','↗','→','↘','↓','↙','←','↖'];
var WINDS=[['ทิศเหนือ','north'],['ตะวันออกเฉียงเหนือ','north-east'],['ตะวันออก','east'],
  ['ตะวันออกเฉียงใต้','south-east'],['ทิศใต้','south'],['ตะวันตกเฉียงใต้','south-west'],
  ['ตะวันตก','west'],['ตะวันตกเฉียงเหนือ','north-west']];
function sector(brg){return Math.round(brg/45)%8;}
function inMoat(la,ln){if(!MOAT||MOAT.length<3)return false;
  var inside=false;
  for(var i=0,j=MOAT.length-1;i<MOAT.length;j=i++){
    var yi=MOAT[i][0],xi=MOAT[i][1],yj=MOAT[j][0],xj=MOAT[j][1];
    if(((yi>la)!==(yj>la))&&(ln<(xj-xi)*(la-yi)/(yj-yi)+xi))inside=!inside;}
  return inside;}
function zoneOf(la,ln){
  var i,b;
  for(i=0;i<ZONES.boxes.length;i++){b=ZONES.boxes[i];
    if(la>=b[0]&&la<=b[1]&&ln>=b[2]&&ln<=b[3])return {th:b[4],en:b[5],kind:'box'};}
  for(i=0;i<ZONES.circles.length;i++){b=ZONES.circles[i];
    if(km(la,ln,b[0],b[1])<=b[2])return {th:b[3],en:b[4],kind:'circle'};}
  return null;}
function moatCentre(){var la=0,ln=0;MOAT.forEach(function(p){la+=p[0];ln+=p[1];});
  return [la/MOAT.length,ln/MOAT.length];}
function far(k){return MDNear.far(k);}
function farText(k){return k<1?Math.round(k*1000)+' m':k.toFixed(1)+' km';}

/* ---- where am I ------------------------------------------------------- */
function describe(){
  if(!here){where.hidden=true;return;}
  var la=here.lat,ln=here.lng,parts=[];
  var z=zoneOf(la,ln),inside=inMoat(la,ln);
  if(inside)parts.push('<b>'+bi('คุณอยู่ในคูเมือง — เมืองเก่าเชียงใหม่','You are inside the moat — the old city of Chiang Mai')+'</b>');
  else if(z&&z.kind==='box')parts.push('<b>'+bi('คุณอยู่แถว'+z.th,'You are around '+z.en)+'</b>');
  else if(z)parts.push('<b>'+bi('คุณอยู่แถว'+z.th,'You are around '+z.en)+'</b>');
  /* The nearest gate or corner, as a distance and a direction FROM you: the
     sentence a local would give. Only when it is walkable; a gate eleven
     kilometres away orients nobody. */
  var best=null,bd=Infinity;
  GATES.forEach(function(g){var d=km(la,ln,g[0],g[1]);if(d<bd){bd=d;best=g;}});
  if(best&&bd<3){
    var s=sector(bearing(la,ln,best[0],best[1]));
    parts.push(bi(best[2]+' อยู่ห่างไป '+farText(bd).replace(' m',' ม.').replace(' km',' กม.')+' ทาง'+WINDS[s][0]+' '+ARROWS[s],
                  best[3]+' is '+farText(bd)+' to your '+WINDS[s][1]+' '+ARROWS[s]));
  }else if(MOAT.length){
    var c=moatCentre(),dk=km(la,ln,c[0],c[1]),s2=sector(bearing(la,ln,c[0],c[1]));
    if(!z)parts.push('<b>'+bi('คุณอยู่นอกเมือง','You are out of town')+'</b>');
    parts.push(bi('เมืองเก่าอยู่ห่างไป '+dk.toFixed(1)+' กม. ทาง'+WINDS[s2][0]+' '+ARROWS[s2],
                  'the old city is '+dk.toFixed(1)+' km to your '+WINDS[s2][1]+' '+ARROWS[s2]));
  }
  if(here.src==='link')parts.push('<span class="hacc">'+bi('จุดนี้มาจากลิงก์ที่ส่งมา ไม่ใช่ตำแหน่งของคุณ','this spot came from a link you were sent, not from your device')+'</span>');
  else if(here.acc)parts.push('<span class="hacc">'+bi('แม่นราว ±'+Math.round(here.acc)+' ม.','accurate to about ±'+Math.round(here.acc)+' m')+'</span>');
  where.innerHTML=parts.join('<br>');where.hidden=false;}

/* ---- the cells -------------------------------------------------------- */
function cellKey(la,ln){return Math.floor(la*100)+'_'+Math.floor(ln*100);}
function cellsAround(la,ln){var a=Math.floor(la*100),b=Math.floor(ln*100),ks=[];
  for(var i=-1;i<=1;i++)for(var j=-1;j<=1;j++)ks.push((a+i)+'_'+(b+j));return ks;}
function loadCells(ks,then){
  var want=ks.filter(function(k){return !(k in cells);});
  if(!want.length){then();return;}
  var n=want.length;
  want.forEach(function(k){
    cells[k]=null;  /* in flight */
    fetch(root()+'data/here/'+k+'.json').then(function(r){return r.ok?r.json():[];})
      .catch(function(){return [];})
      .then(function(rs){cells[k]=Array.isArray(rs)?rs:[];if(--n===0){merge();then();}});
  });}
function merge(){rows=[];Object.keys(cells).forEach(function(k){if(cells[k])rows=rows.concat(cells[k]);});}

/* ---- open now ---------------------------------------------------------
   Minutes since Monday 00:00 in ASIA/BANGKOK, which is the shop's clock and
   not the reader's. This used to read new Date().getDay(), which is right
   standing in Chiang Mai and wrong from anywhere else — a reader in London
   saw a shop marked shut while it was serving. md.js publishes the one
   reading the whole site uses (window.MDHOURS); the local fallback is there
   for the case where here.js runs before it and is the same arithmetic.
   Returns 1 open, 0 posted-hours-but-closed, null when the place never said —
   and null draws NOTHING, by rule. */
function weekMinute(){
  if(window.MDHOURS&&MDHOURS.now){var w=MDHOURS.now();if(w!==null)return w;}
  var d=new Date();return ((d.getDay()+6)%7)*1440+d.getHours()*60+d.getMinutes();}
function openState(r){var s=r[9];if(!s||!s.length)return null;var now=weekMinute();
  for(var i=0;i<s.length;i++)if(now>=s[i][0]&&now<s[i][1])return 1;return 0;}
/* How long until that changes, when it is soon. Standing on a pavement, the
   difference between open and open-for-six-more-minutes is the whole
   decision. Empty string when there is no schedule, or when the next edge is
   further off than an hour — that is the opening times, not news. */
function closingSoon(r){
  var s=r[9];if(!s||!s.length||!window.MDHOURS||!MDHOURS.edge)return '';
  var now=weekMinute(),d=MDHOURS.edge(s,now);
  if(d===null||d>60)return '';
  return openState(r)===1?bi('ปิดใน '+d+' นาที','closes in '+d+' min')
                         :bi('เปิดใน '+d+' นาที','opens in '+d+' min');}

/* ---- the list --------------------------------------------------------- */
function catLabel(c){var l=CATS[c];return l?bi(l[0],l[1]):esc(c);}
function ranked(){
  if(!here)return [];
  var by={};
  rows.forEach(function(r){var d=km(here.lat,here.lng,r[0],r[1]);
    (by[r[6]]=by[r[6]]||[]).push([d,r]);});
  var cats=Object.keys(by);
  cats.sort(function(a,b){var ia=ORDER.indexOf(a),ib=ORDER.indexOf(b);
    if(ia<0)ia=999;if(ib<0)ib=999;return ia-ib;});
  cats.forEach(function(c){by[c].sort(function(a,b){return a[0]-b[0];});});
  return cats.map(function(c){return {cat:c,list:by[c]};});}
function inkFor(c,groups){var i=-1;for(var k=0;k<groups.length;k++)if(groups[k].cat===c){i=k;break;}
  return i>-1&&i<INKS.length?INKS[i]:'#6B5A48';}
function row(d,r){
  var la=r[0],ln=r[1],nm=[r[4],r[5]].filter(Boolean),href=root()+r[2]+'/p/'+esc(r[3])+'.html';
  var brg=bearing(here.lat,here.lng,la,ln),s=sector(brg),st=openState(r),soon=closingSoon(r);
  var sub=r[7]&&SUBS[r[7]]?'<span class="hsub">'+bi(SUBS[r[7]][0],SUBS[r[7]][1])+'</span>':'';
  var a=la.toFixed(5),b=ln.toFixed(5),label=encodeURIComponent(nm[0]||'');
  return '<div class="hrow">'+
    '<span class="hdirw" data-brg="'+brg.toFixed(1)+'" data-glyph="'+ARROWS[s]+'" title="'+esc(WINDS[s][1])+'" aria-label="'+esc(WINDS[s][0]+' · '+WINDS[s][1])+'">'+ARROWS[s]+'</span>'+
    '<span class="hnm"><a href="'+href+'">'+(nm.length>1?bi(esc(nm[0]),esc(nm[1])):esc(nm[0]||r[3]))+'</a>'+sub+
      (r[8]?' <span class="quiet">🐜'+r[8]+'</span>':'')+'</span>'+
    '<span class="hkm">'+far(d)+'</span>'+
    '<span class="hacts">'+
      (st===1?'<span class="hopen yes">'+bi('เปิดอยู่','open now')+'</span>':'')+
      (st===0?'<span class="hopen no">'+bi('ปิดอยู่ (ตามเวลาที่แจ้ง)','closed now (by its posted hours)')+'</span>':'')+
      (soon?'<span class="hsoon">'+soon+'</span>':'')+
      '<a href="geo:'+a+','+b+'?q='+a+','+b+'('+label+')">🧭 '+bi('นำทาง','navigate')+'</a>'+
      '<a href="'+root()+'plan.html?stops='+encodeURIComponent(r[2]+':'+r[3])+'">🚶 '+bi('วางแผนเดิน','route')+'</a>'+
      (r[10]?MDNear.tel(r[10]):'')+
    '</span></div>';}
function draw(){
  if(!here)return;
  var groups=ranked(),h='',c='';
  groups.forEach(function(g,i){
    var ink=inkFor(g.cat,groups),on=!off[g.cat];
    c+='<button type="button" class="hchip" data-c="'+esc(g.cat)+'" aria-pressed="'+(on?'true':'false')+'">'+
       '<span class="hsw" style="background:'+ink+'"></span>'+catLabel(g.cat)+
       '<span class="count">'+g.list.length+'</span></button>';
    if(!on)return;
    var n=more[g.cat]?PER_MORE:PER;
    h+='<h3 class="hkind"><span class="hsw" style="background:'+ink+'"></span>'+catLabel(g.cat)+
       ' <span class="quiet">'+bi('ใกล้สุด '+Math.min(n,g.list.length)+' จาก '+g.list.length,'nearest '+Math.min(n,g.list.length)+' of '+g.list.length)+'</span></h3>';
    for(var j=0;j<Math.min(n,g.list.length);j++)h+=row(g.list[j][0],g.list[j][1]);
    if(g.list.length>n)h+='<button type="button" class="hmore" data-more="'+esc(g.cat)+'">'+bi('ดูเพิ่ม','more')+' ↓</button>';
    else if(more[g.cat]&&g.list.length>PER)h+='<button type="button" class="hmore" data-more="'+esc(g.cat)+'">'+bi('ย่อ','fewer')+' ↑</button>';
  });
  chipsEl.innerHTML=c;
  if(!rows.length)h='<p class="quiet">'+bi('ยังไม่มีที่ไหนในสารบัญของเราภายในราว ๑ กม. จากตรงนี้ — ไม่ได้แปลว่าไม่มีอะไร แปลว่ามดยังไม่เคยมา','Nothing in our catalogue within about a kilometre of here — which says the ant has not walked here yet, not that there is nothing.')+'</p>';
  out.innerHTML=h;
  paintPoints(groups);
  /* draw() rewrites every row, so a live compass has just lost its arrows.
     They are redrawn from the same data-brg the fresh markup carries. */
  if(typeof faceDraw==='function'&&faceOn)faceDraw();}
chipsEl.addEventListener('click',function(e){var b=e.target.closest('.hchip');if(!b)return;
  var c=b.dataset.c;off[c]=!off[c];draw();});
out.addEventListener('click',function(e){var b=e.target.closest('.hmore');if(!b)return;
  var c=b.dataset.more;more[c]=!more[c];draw();});

/* ---- the map ---------------------------------------------------------- */
function ring(la,ln,m){var pts=[],R=6371000,t=Math.PI/180;
  for(var i=0;i<=40;i++){var a=i/40*2*Math.PI;
    pts.push([ln+(m*Math.sin(a))/(R*Math.cos(la*t))/t,la+(m*Math.cos(a))/R/t]);}
  return {type:'Feature',geometry:{type:'Polygon',coordinates:[pts]},properties:{}};}
function paintYou(){
  if(!map||!here)return;
  var you={type:'FeatureCollection',features:[{type:'Feature',properties:{},
    geometry:{type:'Point',coordinates:[here.lng,here.lat]}}]};
  var rg={type:'FeatureCollection',features:here.acc?[ring(here.lat,here.lng,Math.min(here.acc,400))]:[]};
  if(!map.getSource('h-ring')){
    map.addSource('h-ring',{type:'geojson',data:rg});
    map.addLayer({id:'h-ring',type:'fill',source:'h-ring',paint:{'fill-color':'#14479B','fill-opacity':.12}});
    map.addSource('h-you',{type:'geojson',data:you});
    map.addLayer({id:'h-you-halo',type:'circle',source:'h-you',paint:{'circle-radius':11,'circle-color':'#FFFCF6','circle-opacity':.9}});
    map.addLayer({id:'h-you',type:'circle',source:'h-you',paint:{'circle-radius':7,'circle-color':'#14479B','circle-stroke-color':'#fff','circle-stroke-width':2}});
  }else{map.getSource('h-ring').setData(rg);map.getSource('h-you').setData(you);}
  if(!flown||here.src==='link'){flown=true;
    map.jumpTo({center:[here.lng,here.lat],zoom:here.acc&&here.acc>250?15:16.3});}}
function paintPoints(groups){
  if(!map)return;
  var feats=[];
  groups.forEach(function(g){if(off[g.cat])return;var ink=inkFor(g.cat,groups);
    g.list.forEach(function(p){var r=p[1];feats.push({type:'Feature',
      geometry:{type:'Point',coordinates:[r[1],r[0]]},
      properties:{th:r[4]||'',en:r[5]||'',prov:r[2],slug:r[3],rank:r[8],cat:r[6],d:p[0],ink:ink}});});});
  var fc={type:'FeatureCollection',features:feats};
  if(!map.getSource('h-pts')){
    map.addSource('h-pts',{type:'geojson',data:fc});
    map.addLayer({id:'h-pts-halo',type:'circle',source:'h-pts',paint:{
      'circle-radius':['interpolate',['linear'],['zoom'],13,3.4,16,5.6,18,8],'circle-color':'#FFFCF6','circle-opacity':.85}},
      map.getLayer('h-ring')?'h-ring':undefined);
    map.addLayer({id:'h-pts',type:'circle',source:'h-pts',paint:{
      'circle-radius':['interpolate',['linear'],['zoom'],13,2.2,16,3.8,18,5.8],'circle-color':['get','ink'],'circle-opacity':.95}},
      map.getLayer('h-ring')?'h-ring':undefined);
    map.on('click',function(e){
      var R=22,pt=e.point;
      var f=map.queryRenderedFeatures([[pt.x-R,pt.y-R],[pt.x+R,pt.y+R]],{layers:['h-pts']});
      if(!f.length)return;
      var best=f[0],bd=Infinity;
      f.forEach(function(ft){var p=map.project(ft.geometry.coordinates);
        var dd=(p.x-pt.x)*(p.x-pt.x)+(p.y-pt.y)*(p.y-pt.y);if(dd<bd){bd=dd;best=ft;}});
      var pr=best.properties||{},nm=[pr.th,pr.en].filter(Boolean).join(' · ');
      var l=CATS[pr.cat];
      if(window.MDCARD)MDCARD.show({name:nm,sub:l?(l[0]+' · '+l[1]):'',
        href:root()+pr.prov+'/p/'+pr.slug+'.html',plan:pr.prov+':'+pr.slug,
        rank:pr.rank?pr.rank:'',dist:farText(+pr.d)+' '+ARROWS[sector(bearing(here.lat,here.lng,best.geometry.coordinates[1],best.geometry.coordinates[0]))]},el);
    });
    map.on('mousemove',function(e){var f=map.queryRenderedFeatures(e.point,{layers:['h-pts']});
      map.getCanvas().style.cursor=f.length?'pointer':'';});
  }else map.getSource('h-pts').setData(fc);}
if(el&&window.MDMAP)MDMAP.ready(el,function(m){map=m;if(here){paintYou();draw();}});

/* ---- the compass -------------------------------------------------------
   RULE 5, and it keeps the other four. The row arrows are already right: each
   one points along the true bearing from the reader to the place, drawn as one
   of eight glyphs. What they cannot know is which way the reader is FACING, so
   ↗ means north-east and the reader has to find north themselves.

   This asks the device. It is the only capability on this page that md.js does
   not already own, so it is the only one behind its own button: iOS will not
   hand over orientation except from inside a tap, and a page that asked on
   load would be asking a question nobody invited. Refused, unsupported, or
   simply silent, every arrow stays exactly as it was — the static bearing is
   the answer, and the live one is a better way of reading the same number.

   The heading never leaves the device, is never stored and never goes into a
   URL. Same rules as the position it turns beside. */
var facing=null, faceOn=false, faceEv=null;
function headingOf(e){
  /* iOS reports true north directly. Elsewhere alpha is degrees anticlockwise
     from north, so it is subtracted rather than added — getting this backwards
     gives an arrow that turns the wrong way, which reads as broken rather than
     as wrong. `absolute` false means the zero is wherever the device was when
     it started and is not a compass at all. */
  if(typeof e.webkitCompassHeading==='number'&&!isNaN(e.webkitCompassHeading))
    return e.webkitCompassHeading;
  if(typeof e.alpha!=='number'||isNaN(e.alpha))return null;
  if(e.absolute===false)return null;
  return (360-e.alpha)%360;}
function faceDraw(){
  var els=document.querySelectorAll('.hdirw');
  for(var i=0;i<els.length;i++){var el=els[i],b=parseFloat(el.getAttribute('data-brg'));
    if(isNaN(b))continue;
    if(faceOn&&facing!==null){
      /* One glyph, turned. Rotating ↗ by the heading would read as a compass
         needle pointing north-east of north-east. */
      el.textContent='↑';el.classList.add('live');
      el.style.transform='rotate('+(((b-facing)%360+360)%360).toFixed(1)+'deg)';
    }else{
      el.textContent=el.getAttribute('data-glyph')||'↑';
      el.classList.remove('live');el.style.transform='';}}}
function faceStop(){
  faceOn=false;facing=null;
  if(faceEv){window.removeEventListener(faceEv,onFace,true);faceEv=null;}
  if(bFace){bFace.setAttribute('aria-pressed','false');
    bFace.innerHTML=bi('🧭 หันตามเข็มทิศ','Point as I turn');}
  faceDraw();}
var faceLast=0;
function onFace(e){
  var h=headingOf(e);if(h===null)return;
  /* Sixteen frames a second is smooth and a phone compass is noisier than
     that anyway; redrawing on every event repaints the whole list. */
  var t=Date.now();if(t-faceLast<60)return;faceLast=t;
  facing=h;faceDraw();}
function faceStart(){
  var go=function(){
    faceEv=('ondeviceorientationabsolute' in window)?'deviceorientationabsolute':'deviceorientation';
    window.addEventListener(faceEv,onFace,true);
    faceOn=true;
    if(bFace){bFace.setAttribute('aria-pressed','true');
      bFace.innerHTML=bi('🧭 หยุดหมุน','Stop turning');}
    /* Nothing may arrive at all — a laptop has no magnetometer and fires no
       event. Say so once rather than leaving a pressed button over arrows
       that never move. */
    setTimeout(function(){if(faceOn&&facing===null){faceStop();
      say('เครื่องนี้ไม่มีเข็มทิศ — ลูกศรยังบอกทิศจริงอยู่',
          'no compass on this device — the arrows still give the true bearing');}},1600);};
  var D=window.DeviceOrientationEvent;
  if(!D){say('เครื่องนี้ไม่มีเข็มทิศ — ลูกศรยังบอกทิศจริงอยู่',
             'no compass on this device — the arrows still give the true bearing');return;}
  if(typeof D.requestPermission==='function'){
    /* Must be inside the tap. Awaiting anything first loses the gesture. */
    D.requestPermission().then(function(st){
      if(st==='granted')go();
      else say('ไม่เป็นไร — ลูกศรบอกทิศจริงอยู่แล้ว',
               'that is fine — the arrows already give the true bearing');
    }).catch(function(){say('ไม่เป็นไร — ลูกศรบอกทิศจริงอยู่แล้ว',
               'that is fine — the arrows already give the true bearing');});
  }else go();}
if(bFace)bFace.addEventListener('click',function(){faceOn?faceStop():faceStart();});

/* ---- a position arrives ------------------------------------------------ */
function setHere(p){
  var moved=here?km(here.lat,here.lng,p.lat,p.lng)*1000:Infinity;
  var newCells=!here||cellKey(here.lat,here.lng)!==cellKey(p.lat,p.lng);
  here=p;
  describe();paintYou();
  bMe.hidden=false;bShare.hidden=false;
  if(bFace&&window.DeviceOrientationEvent)bFace.hidden=false;
  if(newCells||!rows.length){
    busy('กำลังดูว่ามีอะไรใกล้ ๆ…','looking around you…');
    loadCells(cellsAround(p.lat,p.lng),function(){unbusy();draw();});
  }else if(moved>MOVE_M)draw();}
function watch(){
  if(watchId!==null||!navigator.geolocation)return;
  if(bStart)bStart.setAttribute('aria-busy','true');
  watchId=navigator.geolocation.watchPosition(function(pos){
    if(bStart){bStart.removeAttribute('aria-busy');
      bStart.innerHTML=bi('📍 กำลังตามตำแหน่งอยู่','Following your position');
      bStart.disabled=true;}
    setHere({lat:pos.coords.latitude,lng:pos.coords.longitude,acc:pos.coords.accuracy,src:'gps'});
  },function(){
    if(bStart)bStart.removeAttribute('aria-busy');
    if(!here)say('ยังไม่ได้ตำแหน่ง — ลองอีกครั้ง หรือเปิด GPS','no position yet — try again, or switch GPS on');
    else say('สัญญาณหายชั่วคราว','signal lost for the moment');
  },{enableHighAccuracy:true,maximumAge:5000,timeout:20000});}
function stopWatch(){if(watchId!==null&&navigator.geolocation){navigator.geolocation.clearWatch(watchId);watchId=null;}}
document.addEventListener('visibilitychange',function(){
  if(document.hidden)stopWatch();else if(here&&here.src==='gps'&&!watchId)watch();});
window.addEventListener('pagehide',stopWatch);

/* The button: through MDLOC, the one door. Its dialog handles the asking and
   the remembering of "no"; once it has said yes the OS permission is granted
   and the watch below will not prompt again.

   The button may already be GONE: it carries data-gps-door, and MDLOC removes
   every such door the moment the browser reports the permission denied (or
   the reader once said no). Then this page says so, once, instead of standing
   there with nothing to press. */
if(!bStart){
  say('เครื่องนี้ไม่อนุญาตให้เว็บนี้รู้ตำแหน่ง — แผนที่และรายชื่อยังใช้ได้ หรือเปิดลิงก์ที่มีจุดส่งมา',
      'this device does not let this site know its position — the map still works, and so does a link somebody sent you');}
if(bStart)bStart.addEventListener('click',function(){
  if(!window.MDLOC){watch();return;}
  bStart.setAttribute('aria-busy','true');
  MDLOC.ask(function(pt){setHere({lat:pt.lat,lng:pt.lng,acc:null,src:'gps'});watch();},
            function(){bStart.removeAttribute('aria-busy');
              say('ไม่ได้ตำแหน่ง — แผนที่ยังใช้ได้ กดจุดใดก็ได้','no position — the map still works, touch any dot');});});
if(bMe)bMe.addEventListener('click',function(){if(map&&here)map.easeTo({center:[here.lng,here.lat],zoom:Math.max(map.getZoom(),16),
  duration:matchMedia('(prefers-reduced-motion:reduce)').matches?0:600});});

/* ---- send this spot ----------------------------------------------------
   The ONE link on this site that carries a position, built here and only
   here, on a tap, with the button saying so. Four decimals: about eleven
   metres, which is where the reader is and not which doorway. */
function spotUrl(){return BASE+'here.html#'+here.lat.toFixed(4)+'/'+here.lng.toFixed(4);}
bShare.addEventListener('click',function(){
  if(!here)return;
  var u=spotUrl(),txt='ตรงนี้ · Here — motdang.net';
  var done=function(){shareBox.hidden=false;shareBox.innerHTML=
    bi('ลิงก์นี้มีตำแหน่งของคุณ','This link carries your position')+'<br><a href="'+esc(u)+'">'+esc(u)+'</a>';};
  if(navigator.share){navigator.share({title:txt,text:txt,url:u}).then(done).catch(done);}
  else if(navigator.clipboard&&navigator.clipboard.writeText){
    navigator.clipboard.writeText(u).then(function(){done();shareBox.innerHTML+='<br>'+bi('คัดลอกแล้ว','copied');},done);}
  else done();});

/* ---- send this view --------------------------------------------------
   Same bargain as /map.html: a link does not unfurl in LINE, a picture does,
   so the picture carries its own caption and the ODbL credit in the pixels.
   Offered only where a file can actually be handed to another app. */
function canShareFiles(){try{return !!(navigator.canShare&&navigator.canShare(
  {files:[new File([new Blob([1])],'a.png',{type:'image/png'})]}));}catch(e){return false;}}
if(el&&window.MDMAP&&canShareFiles()){
  bShot.hidden=false;
  bShot.addEventListener('click',function(){
    if(!map)return;
    bShot.setAttribute('aria-busy','true');
    var src=map.getCanvas(),w=src.width,h=src.height,r=window.devicePixelRatio||1,band=Math.round(46*r);
    var c=document.createElement('canvas');c.width=w;c.height=h+band;
    var x=c.getContext('2d');
    x.fillStyle='#FBF6EC';x.fillRect(0,0,c.width,c.height);x.drawImage(src,0,0);
    x.fillStyle='#FFFDF8';x.fillRect(0,h,w,band);
    x.fillStyle='#2A1E16';x.font='700 '+Math.round(15*r)+'px system-ui,sans-serif';
    var cap=where&&!where.hidden?where.textContent.replace(/\s+/g,' ').trim():'';
    x.fillText(('มดแดง · motdang.net — '+(cap||'ตรงนี้ · here')).slice(0,90),Math.round(10*r),h+Math.round(19*r));
    x.fillStyle='#6B5A48';x.font=Math.round(12*r)+'px system-ui,sans-serif';
    x.fillText('© OpenStreetMap contributors (ODbL)',Math.round(10*r),h+Math.round(37*r));
    c.toBlob(function(b){bShot.removeAttribute('aria-busy');if(!b)return;
      var f=new File([b],'motdang-here.png',{type:'image/png'});
      navigator.share({files:[f],title:'มดแดง · Mot Dang',text:BASE+'here.html'}).catch(function(){});},'image/png');
  });}

/* ---- the switch --------------------------------------------------------
   A preference, never a coordinate. On: this page starts locating on open —
   but only once the browser already says the permission is granted, so the
   switch can never make a dialog appear on its own. The homepage hop reads
   the same key (see here_layer.py, "the homepage half"). */
var AUTO='md-here';
function autoOn(){try{return localStorage.getItem(AUTO)==='auto';}catch(e){return false;}}
if(autoBox){autoBox.checked=autoOn();
  autoBox.addEventListener('change',function(){
    try{if(autoBox.checked)localStorage.setItem(AUTO,'auto');else localStorage.removeItem(AUTO);}catch(e){}
    if(autoBox.checked&&!here)say('ครั้งหน้าหน้านี้จะเริ่มหาตำแหน่งเอง ถ้าเครื่องอนุญาตไว้แล้ว','next time this page will start on its own, once the device has allowed it');});}

/* A link that goes back to the front page should stay there. The homepage
   hop reads this flag once and clears it. */
document.addEventListener('click',function(e){var a=e.target.closest('a[href$="index.html"],a[href="./"],a[href="/"]');
  if(a){try{sessionStorage.setItem('md-stay','1');}catch(x){}}},true);

/* ---- how the page starts ---------------------------------------------- */
function fromHash(){var m=(location.hash||'').match(/^#(-?\d+(?:\.\d+)?)\/(-?\d+(?:\.\d+)?)$/);
  if(!m)return null;var la=+m[1],ln=+m[2];
  if(!(la>5&&la<21&&ln>97&&ln<106))return null;return {lat:la,lng:ln,acc:null,src:'link'};}
function boot(){
  if(!window.MDNear){window.addEventListener('load',boot,{once:true});return;}
  var link=fromHash();
  if(link){setHere(link);return;}
  if(autoOn()&&navigator.permissions&&navigator.permissions.query){
    try{navigator.permissions.query({name:'geolocation'}).then(function(st){
      if(st.state==='granted')watch();}).catch(function(){});}catch(e){}}
}
if(window.MDNear)boot();else window.addEventListener('load',boot,{once:true});
})();
"""


def emit(g, data):
    docs = g["DOCS"]
    lamps = _lamps()
    cells = rows(g, data, lamps)
    cdir = docs / CELL_DIR
    cdir.mkdir(parents=True, exist_ok=True)
    n = 0
    for k, rs in cells.items():
        (cdir / (k + ".json")).write_text(json.dumps(rs, ensure_ascii=False,
                                                     separators=(",", ":")))
        n += len(rs)
    js = _js(g, data)
    v = version(js)
    near_v = "%08x" % (zlib.crc32(nearby.JS.encode("utf-8")) & 0xFFFFFFFF)
    nearby.emit(docs)
    (docs / "here.js").write_text(js)
    (docs / "here.css").write_text(CSS)
    (docs / "here.html").write_text(build_page(g, data, v, near_v))
    return {"page": 1, "cells": len(cells), "places": n,
            "with_hours": sum(1 for rs in cells.values() for r in rs if r[9]),
            "gates": len(_gates(g, data))}


if __name__ == "__main__":
    print("This layer runs from build.py — it needs its helpers. "
          "Run: python3 build.py")
