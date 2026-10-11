#!/usr/bin/env python3
"""draw_layer.py — the reader's own GIS. Rungs R1 and R2 of the ladder in
`notes/maps-grow-2026-09-08.txt` §3c.

WHY THIS EXISTS
---------------
Every map on this site so far shows the reader what WE hold. A person standing
on a plot of land, walking a soi, or working out whether a shop's frontage is
wide enough has a question about a shape that is not in our database and never
will be. Google Earth answers it and wants an account; OsmAnd answers it and
wants an install. A page that already has a basemap on it can answer it in the
browser the reader already opened.

So: draw a point, a line or a polygon on the map; read its length or its area
back in the units this country actually uses; carry it away as a file that
opens in OsmAnd, Organic Maps or Google Earth; or send it as a link. Nothing
is stored anywhere but the reader's own browser, because there is nowhere to
store it — this site's worker is GET-only and the write path is R3, which is a
posture change and therefore Nan's (M3 in that note).

RAI FIRST, AND THE WHOLE LADDER
-------------------------------
An area in Thailand is not quoted in square metres and it is not quoted in
hectares. It is ไร่-งาน-ตารางวา: 1 ไร่ = 4 งาน = 400 ตารางวา = 1,600 m², and
1 ตารางวา = 4 m². A land office, a chanote and every conversation about a plot
use that ladder, so the readout leads with it and prints m² and ha after as the
gloss — the same shape as bi(), Thai first. A tool that answered "5,660 m²" to
a person holding a title deed would be a foreign tool.

WHAT THIS COSTS — MEASURED 2026-09-08, `gzip.compress(bytes, 9)` on the file
as served (no stored filename, which is what a server actually sends)
----------------------------------------------------------------------------
    terra-draw 1.33.0                     MIT   assets/vendor/terra-draw.js
                                          248,929 B raw   47,923 B gzipped
    terra-draw-maplibre-gl-adapter 1.4.1  MIT
                                          assets/vendor/terra-draw-maplibre.js
                                            8,845 B raw    2,846 B gzipped
    @turf/length 7.4.0 + @turf/area 7.4.0 MIT
                                          assets/vendor/mdturf.js (esbuild IIFE,
                                          global `mdturf`)
                                            5,673 B raw    2,247 B gzipped
                                    ----------------------------------------
                                    vendored total        53,016 B gzipped
    draw.js  (this file's JS)              28,467 B raw   10,643 B gzipped
    draw.css                                2,086 B raw    1,048 B gzipped
                                    ----------------------------------------
                                    THE WHOLE FEATURE      64,707 B gzipped

§3c estimated "roughly +60 kB". Measured: 64,707 B, and none of it loads on a
page without the bar. The note was close and it is now a number.

Licence texts ride beside them as `terra-draw.LICENSE.txt` and
`turf.LICENSE.txt`, the way `maplibre-gl.LICENSE.txt` already does. draw.js and
draw.css add their own bytes on top; `emit()` measures those at build time and
prints them, so nobody has to trust this docstring for the half that changes.

@turf/buffer WAS REFUSED, ON ITS MEASUREMENT
--------------------------------------------
§3c names "length, area, buffer". Bundling @turf/buffer 7.4.0 beside the other
two measured 67,265 B gzipped against 2,129 B without it — **@turf/buffer alone
is 65,136 B gzipped**, more than terra-draw and the adapter together, because
it pulls in turf-jsts. That is 1.2x the whole rest of this feature for one
operation, on a page CLAUDE.md's THE PHONE note already has carrying 270 kB of
MapLibre. The third option, priced rather than assumed: the buffer readers
actually ask for is a distance ring around a point ("how far is 500 m from
here"), /map.html already draws one from `explore_layer.RING_M`, and a geodesic
ring is fifteen lines of trigonometry with no dependency — `ring()` in the JS
below. A true offset polygon around a LINE or a POLYGON is what is not built,
and it is not built because nobody has asked for it. That is a fork in the
note, not a principle.

THE HASH — THE MEASURED CAP, NOT A GUESSED ONE
----------------------------------------------
§3c guessed "fine to ~40 vertices". Measured, with the encoding below, that is
low by an order of magnitude.

The encoding is Google's polyline algorithm — delta from the previous vertex,
zigzag, five bits a character — with one change: the output alphabet is
base64url (A-Za-z0-9-_) instead of polyline's 63..126, because that range
contains `[ \\ ] ^ { | }` and a backtick, none of them legal in a URL fragment,
and a browser turns each into three percent-encoded characters. Base64url is
entirely `unreserved` in RFC 3986, so a character encoded is a character in the
address bar.

MEASURED by `measured_cost()` below, over sketches at Chiang Mai latitude with
vertices 25 m, 70 m and 500 m apart, worst case over runs of 10 to 200 vertices:

    25 m spacing    3.70 chars per vertex
    70 m spacing    4.20 chars per vertex
    500 m spacing   4.60 chars per vertex

MAX_HASH_CHARS is 1,800 characters for the `d=` value. That holds a MEASURED
391 vertices at the worst spacing measured and 486 at the best — an order of
magnitude above the note's guess, and it leaves a whole URL (origin, path,
zoom, centre, six shelf keys, a tag and a ring) under about 1,950 characters.

WHAT I DID NOT MEASURE, and therefore do not assert: what LINE does to a long
link, and where each browser's own ceiling sits. The sandbox this was built in
refused a local HTTP server (a proxy answered 401 on 127.0.0.1), so the browser
probe never ran and there is no number here for it. 1,800 is a CHOSEN budget:
it comes from the 2,000-character figure proxies and link scrapers have assumed
since IE, and from this site printing QR codes (`make_handouts.py`) — a QR at
version 40, EC level M, holds 2,331 alphanumeric characters, so a 2,000-char
URL is at the edge of one that still scans. Above the cap the reader is told,
in both languages, to save a file instead, and the drawing is NOT put in the
hash: a truncated drawing in a link is worse than no link, because it looks
like it worked.

HOW IT MOUNTS
-------------
Through `MDMAP.ready(el, fn)` and no other way. This module constructs no map;
map_shell is the only module on this site that does. The listeners it adds of
its own go on the bar and on the `.mdmap` holder — never on the SVG inside it,
whose transform map.js owns and rewrites on every zoom.

Emitted: docs/draw.js (`?v=` from version()), docs/draw.css, and the three
vendored libraries plus their two licence files into docs/vendor/.
"""

import json
import math
import random
import zlib
from pathlib import Path

import glyphs_draw

ROOT = Path(__file__).resolve().parent

# The vendored libraries, and the licence text beside each. Same shape as
# map_shell.VENDOR and copied the same way: docs/ is wiped every build, so
# these are a copy each run and never a hand-placed folder that survives one
# build and vanishes at the next.
VENDOR = ("terra-draw.js", "terra-draw-maplibre.js", "mdturf.js",
          "terra-draw.LICENSE.txt", "turf.LICENSE.txt")

# Pinned, and recorded where a reader of this file can see them without
# opening a minified bundle. Bumping a version here means re-vendoring the file
# AND re-measuring the byte cost in the docstring above.
LIBS = (
    ("terra-draw", "1.33.0", "MIT", "terra-draw.js"),
    ("terra-draw-maplibre-gl-adapter", "1.4.1", "MIT", "terra-draw-maplibre.js"),
    ("@turf/length", "7.4.0", "MIT", "mdturf.js"),
    ("@turf/area", "7.4.0", "MIT", "mdturf.js"),
)

# The licence band in words, riding inside every exported file exactly as it
# rides in the pixels of the shared picture (explore.js draws these same two
# lines under the canvas). ODbL requires the credit; the first line is who made
# the tool. Neither is decoration and neither is ours to fold into a link.
CREDIT = "มดแดง · Mot Dang · motdang.net"
ODBL = "© OpenStreetMap contributors (ODbL)"

# The cap on the `d=` value. See the docstring: a chosen budget, with the
# per-vertex cost under it measured.
MAX_HASH_CHARS = 1800

# 1 ไร่ = 4 งาน = 400 ตารางวา = 1,600 m²; 1 ตารางวา = 4 m².
RAI_M2 = 1600
NGAN_M2 = 400
WA_M2 = 4


def enabled():
    """True only when there is a basemap to draw on AND every vendored file is
    on disk. Both halves, for map_shell's reason — and one more of this
    module's own: every other map surface here degrades to a drawn SVG, and
    this one cannot. You cannot sketch on a picture, so a bar with no map under
    it is a row of dead buttons and is not emitted at all."""
    try:
        import map_shell
    except ImportError:
        return False
    if not map_shell.enabled():
        return False
    return all((ROOT / "assets" / "vendor" / f).exists() for f in VENDOR)


def _js():
    """draw.js, exactly as it ships."""
    return (JS.replace("%MAXHASH%", str(MAX_HASH_CHARS))
              .replace("%CREDIT%", json.dumps(CREDIT, ensure_ascii=False))
              .replace("%ODBL%", json.dumps(ODBL, ensure_ascii=False)))


def version():
    """Content hash for the `?v=` on draw.js and draw.css.

    Same reasoning as map_shell.version() and explore_layer.version(), and the
    same scar behind it: map.js shipped for weeks with a week-long cache and a
    name that never changed, so a reader who had opened any map page in the
    previous seven days kept an old copy against fresh HTML, the new API call
    threw, and the explore map came up with no dots and no chips. A map surface
    without a cache-buster is a production outage waiting for its seventh day.

    The constants are hashed with the code, because a changed cap or a changed
    credit line changes what this script DOES as surely as an edited line does.
    """
    payload = _js() + CSS + json.dumps(
        {"credit": CREDIT, "odbl": ODBL, "max": MAX_HASH_CHARS,
         "libs": LIBS, "glyphs": glyphs_draw.SPRITE},
        sort_keys=True, ensure_ascii=False)
    return "%08x" % (zlib.crc32(payload.encode("utf-8")) & 0xFFFFFFFF)


def head(depth=0):
    """The tags a page needs before it may offer drawing. Goes AFTER
    map_shell.head(): the adapter reads the `terraDraw` global, and MapLibre
    has to be the map that exists by the time MDMAP.ready fires. All of these
    are `defer`, so source order here is execution order.

    Emitted only on the page that carries the bar — hence a depth and not a
    global flag, which is map_shell's rule for the same reason."""
    if not enabled():
        return ""
    r = "../" * depth
    v = version()
    return (f'<link rel="stylesheet" href="{r}draw.css">'
            f'<script src="{r}vendor/terra-draw.js" defer></script>'
            f'<script src="{r}vendor/terra-draw-maplibre.js" defer></script>'
            f'<script src="{r}vendor/mdturf.js" defer></script>'
            f'<script src="{r}draw.js" defer></script>')


def head_urls(depth=0):
    """The same five files as a list, for a page that must not pay for any of
    this until a reader asks — search.html's pattern. One owner for the version
    hash, so the two can never disagree."""
    if not enabled():
        return []
    r = "../" * depth
    v = version()
    return [f"{r}draw.css", f"{r}vendor/terra-draw.js",
            f"{r}vendor/terra-draw-maplibre.js", f"{r}vendor/mdturf.js",
            f"{r}draw.js"]


def sprite_html():
    """The five marks this bar draws that neither existing sprite has.
    build.ICON_SPRITE and glyphs.SPRITE are already on every page; this adds
    five <g> and nothing more."""
    return glyphs_draw.sprite()


# The bar, in order. Each row: (id, glyph, Thai, English). The label is the
# accessible name — these controls carry no words, which is why every one of
# them passes `label=` into glyphs_draw.icon() rather than aria-hidden. The
# bilingual name also appears VISIBLY in the readout the moment a mode is
# chosen: CLAUDE.md counted 198,767 `title=` attributes on this site against
# zero `@media (hover: hover)` rules, so a tooltip here would be invisible to
# exactly the phone-first Thai reader it was written for.
TOOLS = (
    ("point", "i-pin", "จุด", "point"),
    ("linestring", "i-route", "เส้น", "line"),
    ("polygon", "i-poly", "รูปปิด", "area"),
    ("select", "i-cursor", "เลือก · ย้าย", "select and move"),
    ("erase", "i-erase", "ลบรูปที่เลือก", "delete the selected shape"),
    ("clear", "i-x", "ล้างทั้งหมด", "clear everything"),
)
SAVES = (("geojson", "GeoJSON"), ("gpx", "GPX"), ("kml", "KML"))


def controls_html(g, map_id="xmap"):
    """The bar, the readout and the file input, as markup — built in Python
    like explore_layer's chips, so a reader with no scripting sees nothing
    half-built and a crawler reads no dead controls. It ships `hidden`; draw.js
    unhides it once the map, the libraries and the adapter are all really
    there, which is the same bargain explore.js keeps with its chips.

    `data-mddraw-for` names the map this bar drives. draw.js finds the holder
    by that id and goes in through MDMAP.ready(); it never queries for a map
    and never makes one.
    """
    bi, bi_text, att = g["bi"], g["bi_text"], g["att"]
    ic = glyphs_draw.icon
    btns = "".join(
        f'<button type="button" class="mdd-btn" data-mdd="{k}" aria-pressed="false">'
        f'{ic(gl, 24, label=att(bi_text(th, en)))}</button>'
        for k, gl, th, en in TOOLS)
    saves = "".join(
        f'<button type="button" class="mdd-btn mdd-save" data-mdd-save="{k}">'
        f'{ic("i-download", 22, label=att(bi_text("บันทึกเป็น " + nm, "save as " + nm)))}'
        f'<span class="mdd-fmt">{nm}</span></button>'
        for k, nm in SAVES)
    note_th = ("รูปที่วาดเก็บไว้ในเบราว์เซอร์นี้ · ไฟล์ที่บันทึกเปิดได้ใน "
               "OsmAnd, Organic Maps และ Google Earth · ทุกไฟล์มีบรรทัด " + ODBL + " อยู่ข้างใน")
    note_en = ("What you draw is saved in this browser. Saved files open in OsmAnd, Organic "
               "Maps and Google Earth, and every one of them carries the " + ODBL
               + " line inside it.")
    return (
        f'<div class="mdd" data-mddraw-for="{map_id}" hidden>'
        f'<h2 class="mdd-h">{bi("วาดเอง วัดเอง", "Draw it, measure it")}</h2>'
        f'<div class="mdd-bar" role="group" '
        f'aria-label="{att(bi_text("เครื่องมือวาด", "drawing tools"))}">{btns}</div>'
        f'<p class="mdd-say" id="mdd-say" role="status" aria-live="polite">'
        f'{bi("แตะเครื่องมือ แล้วแตะบนแผนที่", "Touch a tool, then touch the map")}</p>'
        f'<div class="mdd-bar mdd-out">{saves}'
        f'<button type="button" class="mdd-btn mdd-save" data-mdd="open">'
        f'{ic("i-upload", 22, label=att(bi_text("เปิดไฟล์ที่มีอยู่", "open a file you already have")))}'
        f'<span class="mdd-fmt">{bi("เปิดไฟล์", "open")}</span></button>'
        f'<button type="button" class="mdd-btn mdd-save" data-mdd="link">'
        f'{ic("i-link", 22, label=att(bi_text("คัดลอกลิงก์รูปที่วาด", "copy a link to this drawing")))}'
        f'<span class="mdd-fmt">{bi("ลิงก์", "link")}</span></button>'
        f'<input type="file" id="mdd-file" class="mdd-file" '
        f'accept=".geojson,.json,.gpx,.kml,application/geo+json,application/gpx+xml,'
        f'application/vnd.google-earth.kml+xml,text/xml" '
        f'aria-label="{att(bi_text("เลือกไฟล์ GeoJSON GPX หรือ KML", "choose a GeoJSON, GPX or KML file"))}">'
        f'</div>'
        f'<p class="mdd-note quiet">{bi(note_th, note_en)}</p>'
        f'{sprite_html()}</div>')


# ─────────────────────────────────────────────────────────── measurement ────

def _enc_prototype(coords):
    """The hash encoder's coordinate half, in Python.

    It exists to make the numbers in the docstring re-takeable and to give
    tests/test_draw.py something to check the JS against on a fixed input —
    not as a second implementation anybody calls. If the two ever disagree the
    test fails, which is the point.
    """
    A = "ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789-_"

    def num(v):
        # Zigzag exactly as the JS does it: ~(v<<1) for a negative, v<<1 for a
        # positive. The other spelling (~v << 1) is off by one and would decode
        # a metre out.
        v = ~(v << 1) if v < 0 else (v << 1)
        out = ""
        while v >= 0x20:
            out += A[0x20 | (v & 0x1F)]
            v >>= 5
        return out + A[v]

    plat = plng = 0
    out = ""
    for lng, lat in coords:
        la, ln = round(lat * 1e5), round(lng * 1e5)
        out += num(la - plat) + num(ln - plng)
        plat, plng = la, ln
    return out


def _walk(n, step_m, seed=7):
    """A wandering sketch at Chiang Mai latitude — a route someone traced, not
    a straight line, because a straight line encodes far too well and would
    flatter the measurement."""
    rnd = random.Random(seed)
    lat, lng, b = 18.7876, 98.9931, 0.0
    pts = []
    for _ in range(n):
        b += rnd.uniform(-1.1, 1.1)
        d = step_m / 111320.0
        lat += d * math.cos(b)
        lng += d * math.sin(b) / math.cos(math.radians(lat))
        pts.append((lng, lat))
    return pts


def measured_cost():
    """Re-run the per-vertex measurement quoted in the docstring. Worst case
    over runs of 10 to 200 vertices, at three spacings. Returns
    {spacing_m: chars_per_vertex}."""
    out = {}
    for step in (25, 70, 500):
        worst = 0.0
        for n in (10, 20, 40, 100, 200):
            worst = max(worst, len(_enc_prototype(_walk(n, step))) / n)
        out[step] = round(worst, 2)
    return out


def hash_capacity(cost=None):
    """How many vertices MAX_HASH_CHARS holds, at the measured costs."""
    m = cost or measured_cost()
    return {"cap_chars": MAX_HASH_CHARS,
            "vertices_worst": int(MAX_HASH_CHARS // max(m.values())),
            "vertices_best": int(MAX_HASH_CHARS // min(m.values())),
            "chars_per_vertex": m}


# ─────────────────────────────────────────────────────────────────── CSS ────

CSS = """/* draw.css — the reader's own GIS. Loaded only on a page with the bar. */
.mdd{margin:.6rem 0 1.1rem}
.mdd[hidden]{display:none}
.mdd-h{font-size:1.05rem;margin:.2rem 0 .45rem}
.mdd-bar{display:flex;gap:.45rem;align-items:center;flex-wrap:wrap;margin:.35rem 0}
/* 44 px, both ways, on every control. The phone is the device, a fingertip is
   about 9 mm, and a 32 px button on top of a map is a button that mis-taps
   into a pan. Walked at 375x812: six tools wrap to two rows of three and the
   readout stays above the fold with the map. */
.mdd-btn{display:inline-flex;align-items:center;justify-content:center;gap:.35rem;
  min-height:44px;min-width:44px;padding:.35rem .6rem;border-radius:.6rem;
  font:inherit;font-weight:700;border:2px solid var(--warm-border,#e0d6c4);
  background:#fff;color:var(--ant-dark,#8c2d12);cursor:pointer}
.mdd-btn:hover{background:var(--row-hover,#faf4e8)}
.mdd-btn:focus-visible{outline:3px solid var(--ant,#c2401c);outline-offset:2px}
.mdd-btn[aria-pressed="true"]{border-color:var(--ink,#2a1e16);
  background:var(--card-alt,#fffdf8)}
.mdd-btn[disabled]{opacity:.45;cursor:default}
.mdd-btn .rowicon{color:var(--ant-dark,#8c2d12)}
.mdd-fmt{font-size:.85rem;font-weight:700}
.mdd-save{padding:.35rem .7rem}
/* The readout does the talking. A title= on this site is invisible to the
   reader it was written for — 198,767 of them against zero hover rules — so
   the name of the tool, and every number, lands here in both languages.
   Its height is reserved so the bar does not jump when a number arrives. */
.mdd-say{margin:.35rem 0 .5rem;min-height:2.6em;font-size:.95rem;
  color:var(--ink,#2a1e16);line-height:1.35}
.mdd-say b{font-weight:700}
.mdd-gloss{color:var(--gloss,#6b5a48);font-size:.88em}
.mdd-warn{color:var(--ant-dark,#8c2d12);font-weight:700}
.mdd-file{position:absolute;width:1px;height:1px;overflow:hidden;
  clip:rect(0 0 0 0);white-space:nowrap}
.mdd-note{font-size:.85rem;margin:.3rem 0 0;color:var(--gloss,#6b5a48)}
/* A drawing prints with the map. The bar does not. */
@media print{.mdd-bar,.mdd-note{display:none}}
"""

# ──────────────────────────────────────────────────────────────────── JS ────

JS = r"""/* draw.js — R1 and R2 of the reader-GIS ladder. Runs on any page carrying
   the bar draw_layer.controls_html() writes, which today is /map.html.

   THREE THINGS THIS FILE WILL NOT DO.

   1. Construct a map. map_shell is the only map constructor on this site, and
      the way in is MDMAP.ready(el, fn). If MDMAP is missing, or the tiles
      never arrive, ready() never fires, the bar stays hidden, and that is
      correct: there is nothing to sketch on. Every other map surface here
      degrades to a drawn SVG; this one has no such fallback and does not
      pretend to one.
   2. Bind to the drawn SVG. map.js owns the transform of everything inside
      .mdmap-draw and rewrites it on every zoom and every retarget. Our
      listeners go on the bar and on the .mdmap holder, and nowhere else.
   3. Send anything anywhere. There is no fetch and no beacon in this file.
      The drawing lives in the reader's browser, in the URL, or in a file they
      saved. */
(function(){
var bar=document.querySelector('.mdd[data-mddraw-for]');
if(!bar)return;
var el=document.getElementById(bar.getAttribute('data-mddraw-for'));
/* Every piece has to be here. A half-loaded bar is worse than none: the
   reader taps, nothing happens, and they conclude the site is broken rather
   than that a script did not arrive. */
if(!el||!window.MDMAP||!window.terraDraw||!window.terraDrawMaplibreGlAdapter||
   !window.mdturf)return;

var CREDIT=%CREDIT%, ODBL=%ODBL%, MAXHASH=%MAXHASH%;
var ATTRIB=CREDIT+' · '+ODBL;

/* ---- units ------------------------------------------------------------
   ไร่-งาน-ตารางวา first. 1 ไร่ = 4 งาน = 400 ตร.ว. = 1,600 m²; 1 ตร.ว. = 4 m².
   Under a งาน the upper rungs are noise, so a small plot is quoted in ตารางวา
   alone — which is how a small plot is quoted. */
function nf(n,d){return n.toLocaleString(undefined,
  {maximumFractionDigits:(d===undefined?0:d)});}
function fmtArea(m2){
  var rai=Math.floor(m2/1600),rest=m2-rai*1600;
  var ngan=Math.floor(rest/400);rest-=ngan*400;
  var wa=rest/4,th;
  if(m2<400)th=nf(wa,1)+' ตร.ว.';
  else if(!rai)th=ngan+' งาน '+nf(wa,0)+' ตร.ว.';
  else th=nf(rai)+' ไร่ '+ngan+' งาน '+nf(wa,0)+' ตร.ว.';
  var en=nf(m2,(m2<1000?1:0))+' m²';
  if(m2>=10000)en+=' · '+nf(m2/10000,2)+' ha';
  return {th:th,en:en};
}
function fmtLen(m){
  return {th:(m<1000?nf(m,(m<100?1:0))+' ม.':nf(m/1000,2)+' กม.'),
          en:(m<1000?nf(m,(m<100?1:0))+' m':nf(m/1000,2)+' km')};
}
/* The one buffer shipped, and the only one anybody has asked for: a geodesic
   ring of r metres around a point. @turf/buffer measured 65,017 B gzipped for
   the general case; this is fifteen lines and answers the question the ring on
   /map.html already answers. Exported on MDDRAW rather than wired to a button,
   so the refusal above has its alternative in the file and not only in a note. */
function ring(lng,lat,r,steps){
  var n=steps||64,R=6371000,out=[],d=r/R;
  var la=lat*Math.PI/180,lo=lng*Math.PI/180;
  for(var i=0;i<=n;i++){
    var b=2*Math.PI*i/n;
    var la2=Math.asin(Math.sin(la)*Math.cos(d)+Math.cos(la)*Math.sin(d)*Math.cos(b));
    var lo2=lo+Math.atan2(Math.sin(b)*Math.sin(d)*Math.cos(la),
                          Math.cos(d)-Math.sin(la)*Math.sin(la2));
    out.push([lo2*180/Math.PI,la2*180/Math.PI]);
  }
  return {type:'Feature',properties:{},geometry:{type:'Polygon',coordinates:[out]}};
}

/* ---- the hash encoding ------------------------------------------------
   Google's polyline algorithm at precision 5 (about 1.1 m — a sketch, not a
   survey), with the output alphabet swapped to base64url. Polyline's own
   63..126 range contains [ \ ] ^ ` { | }, none of them legal in a fragment,
   and a browser turns each into three percent-encoded characters — which is
   how a "compact" encoding ends up longer than the JSON it replaced. */
var A64='ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789-_';
var R64={};for(var _i=0;_i<64;_i++){R64[A64.charAt(_i)]=_i;}
var TYPE={Point:'p',LineString:'l',Polygon:'a'};
var UNTYPE={p:'Point',l:'LineString',a:'Polygon'};
var MODE={Point:'point',LineString:'linestring',Polygon:'polygon'};

function encNum(v){
  v=(v<0)?~(v<<1):(v<<1);
  var s='';
  while(v>=0x20){s+=A64.charAt(0x20|(v&0x1f));v>>>=5;}
  return s+A64.charAt(v);
}
function encCoords(cs,st){
  var s='';
  for(var i=0;i<cs.length;i++){
    var la=Math.round(cs[i][1]*1e5),ln=Math.round(cs[i][0]*1e5);
    s+=encNum(la-st.lat)+encNum(ln-st.lng);
    st.lat=la;st.lng=ln;
  }
  return s;
}
function decCoords(s,st){
  var out=[],i=0;
  while(i<s.length){
    var vals=[],k;
    for(k=0;k<2;k++){
      var shift=0,res=0,c;
      do{
        if(i>=s.length)return out;
        c=R64[s.charAt(i++)];
        if(c===undefined)return out;
        res|=(c&0x1f)<<shift;shift+=5;
      }while(c>=0x20);
      vals.push((res&1)?~(res>>1):(res>>1));
    }
    st.lat+=vals[0];st.lng+=vals[1];
    out.push([st.lng/1e5,st.lat/1e5]);
  }
  return out;
}
/* A drawing as one URL-safe token: "1", then ".<type><coords>" per shape. The
   leading 1 is the format version, so a later change is detectable rather than
   silently mis-parsed. A polygon's ring is stored WITHOUT its closing
   duplicate and closed again on the way back: one vertex saved per polygon,
   and it removes the only way a hand-edited hash can yield an open ring. */
function encode(features){
  var st={lat:0,lng:0},parts=['1'];
  for(var i=0;i<features.length;i++){
    var g=features[i].geometry;if(!g)continue;
    var t=TYPE[g.type];if(!t)continue;
    var cs;
    if(g.type==='Point'){cs=[g.coordinates];}
    else if(g.type==='LineString'){cs=g.coordinates;}
    else{
      cs=g.coordinates[0].slice();
      if(cs.length>1&&cs[0][0]===cs[cs.length-1][0]&&cs[0][1]===cs[cs.length-1][1])cs.pop();
    }
    if(!cs.length)continue;
    parts.push(t+encCoords(cs,st));
  }
  return parts.length>1?parts.join('.'):'';
}
function decode(s){
  if(!s)return [];
  var parts=String(s).split('.');
  if(parts.shift()!=='1')return [];
  var st={lat:0,lng:0},out=[];
  for(var i=0;i<parts.length;i++){
    var p=parts[i];if(!p)continue;
    var t=UNTYPE[p.charAt(0)];if(!t)continue;
    var cs=decCoords(p.slice(1),st);
    if(!cs.length)continue;
    var geom;
    if(t==='Point')geom={type:'Point',coordinates:cs[0]};
    else if(t==='LineString')geom={type:'LineString',coordinates:cs};
    else{var r=cs.slice();r.push([r[0][0],r[0][1]]);
         geom={type:'Polygon',coordinates:[r]};}
    out.push({type:'Feature',properties:{},geometry:geom});
  }
  return out;
}

/* ---- the three files --------------------------------------------------
   The licence band goes INSIDE each one, the same way explore.js draws it into
   the pixels of a shared picture: a file travels with no page around it, so the
   credit travels in the file or it does not travel at all. */
function stamp(){return new Date().toISOString().slice(0,10);}
function xml(s){return String(s).replace(/&/g,'&amp;').replace(/</g,'&lt;')
  .replace(/>/g,'&gt;').replace(/"/g,'&quot;');}
function shapeName(f,i){
  var t=f.geometry.type;
  return (t==='Point'?'จุด · point ':(t==='LineString'?'เส้น · line ':'รูปปิด · area '))+(i+1);
}
function coordStr(c){return c[0]+','+c[1];}

function toGeoJSON(features){
  /* RFC 7946 §6.1 allows foreign members, and `attribution` / `license` are
     where the consumers that show credit look. Both go on each feature too, so
     one feature copied out of the collection still carries them. */
  var fs=[];
  for(var i=0;i<features.length;i++){
    fs.push({type:'Feature',
      properties:{name:shapeName(features[i],i),attribution:ATTRIB,license:ODBL},
      geometry:features[i].geometry});
  }
  return JSON.stringify({type:'FeatureCollection',attribution:ATTRIB,license:ODBL,
    creator:CREDIT,generated:stamp(),features:fs},null,1);
}
function toGPX(features){
  /* GPX 1.1 has no polygon. A drawn area therefore leaves as a CLOSED track,
     which is what OsmAnd and Organic Maps draw, and comes back from fromText()
     as a line. That is a real one-way loss and it is said here out loud rather
     than discovered by somebody whose field boundary reopened. */
  var out='<?xml version="1.0" encoding="UTF-8"?>\n<!-- '+xml(ATTRIB)+' -->\n'+
    '<gpx version="1.1" creator="'+xml(CREDIT)+'" '+
    'xmlns="http://www.topografix.com/GPX/1/1">\n'+
    '<metadata><name>'+xml(CREDIT)+'</name><desc>'+xml(ATTRIB)+'</desc>'+
    '<copyright author="OpenStreetMap contributors">'+
    '<license>https://opendatacommons.org/licenses/odbl/1-0/</license>'+
    '</copyright><time>'+stamp()+'T00:00:00Z</time></metadata>\n';
  for(var i=0;i<features.length;i++){
    var g=features[i].geometry,nm=xml(shapeName(features[i],i));
    if(g.type==='Point'){
      out+='<wpt lat="'+g.coordinates[1]+'" lon="'+g.coordinates[0]+'">'+
        '<name>'+nm+'</name><desc>'+xml(ATTRIB)+'</desc></wpt>\n';
    }else{
      var cs=(g.type==='LineString')?g.coordinates:g.coordinates[0];
      out+='<trk><name>'+nm+'</name><desc>'+xml(ATTRIB)+'</desc><trkseg>';
      for(var j=0;j<cs.length;j++){
        out+='<trkpt lat="'+cs[j][1]+'" lon="'+cs[j][0]+'"></trkpt>';
      }
      out+='</trkseg></trk>\n';
    }
  }
  return out+'</gpx>\n';
}
function toKML(features){
  /* KML 2.2 carries all three shapes, so this is the lossless one of the two
     XML formats. Coordinates are lng,lat — the opposite order to GPX's
     attributes, which is the single most common way a hand-written exporter
     puts a Chiang Mai polygon in Somalia. */
  var out='<?xml version="1.0" encoding="UTF-8"?>\n<!-- '+xml(ATTRIB)+' -->\n'+
    '<kml xmlns="http://www.opengis.net/kml/2.2"><Document>\n'+
    '<name>'+xml(CREDIT)+'</name>\n'+
    '<description>'+xml(ATTRIB)+'</description>\n';
  for(var i=0;i<features.length;i++){
    var g=features[i].geometry,nm=xml(shapeName(features[i],i)),body;
    if(g.type==='Point'){
      body='<Point><coordinates>'+coordStr(g.coordinates)+'</coordinates></Point>';
    }else if(g.type==='LineString'){
      body='<LineString><tessellate>1</tessellate><coordinates>'+
        g.coordinates.map(coordStr).join(' ')+'</coordinates></LineString>';
    }else{
      body='<Polygon><outerBoundaryIs><LinearRing><coordinates>'+
        g.coordinates[0].map(coordStr).join(' ')+
        '</coordinates></LinearRing></outerBoundaryIs></Polygon>';
    }
    out+='<Placemark><name>'+nm+'</name><description>'+xml(ATTRIB)+
      '</description>'+body+'</Placemark>\n';
  }
  return out+'</Document></kml>\n';
}

/* ---- reading the same three back ---------------------------------------
   WHY NOT DOMParser. It is in every browser and it would be the obvious
   reader. It is not in node, and tests/test_draw.py runs these exact
   functions under node to prove the round trip — so a DOMParser reader would
   have forced a second, regex implementation for the test, which is the
   "two sources of truth for one thing" scar CLAUDE.md already names. One
   scanner, exercised by the test that matters, is the smaller error and it is
   priced: what it gives up is entity decoding inside coordinates and CDATA
   around them, neither of which any of the three exporters here, nor OsmAnd,
   Organic Maps or Google Earth, produces. A file it cannot read is REFUSED
   out loud rather than half-read. */
function num(s){var v=parseFloat(s);return isFinite(v)?v:null;}
function attr(tag,n){
  var m=tag.match(new RegExp('\\b'+n+'\\s*=\\s*"([^"]*)"'))||
        tag.match(new RegExp("\\b"+n+"\\s*=\\s*'([^']*)'"));
  return m?m[1]:null;
}
function ptsFromCoordText(t){
  var out=[],raw=t.replace(/\s+/g,' ').trim().split(' ');
  for(var i=0;i<raw.length;i++){
    if(!raw[i])continue;
    var p=raw[i].split(',');
    var x=num(p[0]),y=num(p[1]);
    if(x===null||y===null)continue;
    out.push([x,y]);
  }
  return out;
}
function parseGeoJSON(text){
  var j=JSON.parse(text),fs=[];
  var list=(j.type==='FeatureCollection')?j.features:
           (j.type==='Feature')?[j]:(j.type&&j.coordinates)?
           [{type:'Feature',properties:{},geometry:j}]:[];
  for(var i=0;i<list.length;i++){
    var g=list[i]&&list[i].geometry;
    if(!g||!TYPE[g.type])continue;
    fs.push({type:'Feature',properties:{},geometry:{type:g.type,coordinates:g.coordinates}});
  }
  return fs;
}
function parseGPX(text){
  var fs=[],m;
  var wpt=/<(?:\w+:)?wpt\b([^>]*)>/gi;
  while((m=wpt.exec(text))){
    var la=num(attr(m[1],'lat')),lo=num(attr(m[1],'lon'));
    if(la===null||lo===null)continue;
    fs.push({type:'Feature',properties:{},geometry:{type:'Point',coordinates:[lo,la]}});
  }
  /* A trkseg and an rte are the same shape to us: an ordered run of points.
     A closed run is NOT re-promoted to a polygon — GPX did not say polygon,
     and inventing one would be this site guessing at a reader's intent. */
  var segs=/<(?:\w+:)?(trkseg|rte)\b[^>]*>([\s\S]*?)<\/(?:\w+:)?\1>/gi;
  while((m=segs.exec(text))){
    var pts=[],p,rx=/<(?:\w+:)?(?:trkpt|rtept)\b([^>]*)>/gi;
    while((p=rx.exec(m[2]))){
      var a=num(attr(p[1],'lat')),b=num(attr(p[1],'lon'));
      if(a===null||b===null)continue;
      pts.push([b,a]);
    }
    if(pts.length>1)fs.push({type:'Feature',properties:{},
      geometry:{type:'LineString',coordinates:pts}});
  }
  return fs;
}
function parseKML(text){
  var fs=[],m,pm=/<Placemark\b[^>]*>([\s\S]*?)<\/Placemark>/gi;
  while((m=pm.exec(text))){
    var body=m[1],c;
    if(/<Polygon\b/i.test(body)){
      c=body.match(/<outerBoundaryIs>[\s\S]*?<coordinates>([\s\S]*?)<\/coordinates>/i)||
        body.match(/<coordinates>([\s\S]*?)<\/coordinates>/i);
      if(!c)continue;
      var r=ptsFromCoordText(c[1]);
      if(r.length<3)continue;
      if(r[0][0]!==r[r.length-1][0]||r[0][1]!==r[r.length-1][1])r.push([r[0][0],r[0][1]]);
      fs.push({type:'Feature',properties:{},geometry:{type:'Polygon',coordinates:[r]}});
    }else if(/<LineString\b/i.test(body)){
      c=body.match(/<coordinates>([\s\S]*?)<\/coordinates>/i);
      if(!c)continue;
      var l=ptsFromCoordText(c[1]);
      if(l.length>1)fs.push({type:'Feature',properties:{},
        geometry:{type:'LineString',coordinates:l}});
    }else if(/<Point\b/i.test(body)){
      c=body.match(/<coordinates>([\s\S]*?)<\/coordinates>/i);
      if(!c)continue;
      var q=ptsFromCoordText(c[1]);
      if(q.length)fs.push({type:'Feature',properties:{},
        geometry:{type:'Point',coordinates:q[0]}});
    }
  }
  return fs;
}
/* Sniffed on CONTENT, never on the extension. A file that has been through
   LINE, a download folder and a file picker often arrives as "document.txt"
   or with no extension at all, and refusing it on its name would refuse a
   file we can read perfectly. */
function fromText(text){
  var t=String(text).replace(/^\uFEFF/,'').replace(/^\s+/,'');
  try{
    if(t.charAt(0)==='{'||t.charAt(0)==='[')return parseGeoJSON(t);
    if(/<\s*kml\b/i.test(t))return parseKML(t);
    if(/<\s*gpx\b/i.test(t))return parseGPX(t);
  }catch(e){return null;}
  return null;
}

/* ---- handing a file over ----------------------------------------------
   A Blob and an <a download>. No server touches the bytes; the file is made
   in the browser and given to the browser. revokeObjectURL on a timer rather
   than immediately, because Safari has historically cancelled a download whose
   object URL was revoked in the same tick. */
function save(fname,text,mime){
  try{
    var b=new Blob([text],{type:mime});
    var u=URL.createObjectURL(b),a=document.createElement('a');
    a.href=u;a.download=fname;a.style.display='none';
    document.body.appendChild(a);a.click();
    setTimeout(function(){URL.revokeObjectURL(u);a.parentNode&&a.parentNode.removeChild(a);},1500);
    return true;
  }catch(e){return false;}
}

/* ---- the drawing in the address bar ------------------------------------
   explore_layer's scheme: #zoom/lat/lng/shelves/k=v&k=v — the drawing is `d=`
   in that fifth part. Read and written by read-modify-write over whatever
   else is in there, so a ring or a tag set by another layer survives us and
   we survive it.

   ONE THING TO KNOW: on /map.html explore.js rewrites the hash on every
   moveend from its OWN state, which does not include `d=`. Without the
   one-line hook in explore_layer's viewParams() (see the notes file), a
   drawing drops out of the URL the first time the reader pans. It is not a
   silent failure — the link button re-writes it — but it is the reason the
   hook exists. */
function hashParts(){
  return (location.hash||'').replace(/^#/,'').split('/');
}
function readHashDrawing(){
  var p=hashParts(),q=(p[4]||'').split('&');
  for(var i=0;i<q.length;i++){
    if(q[i].indexOf('d=')===0)return decode(q[i].slice(2));
  }
  return [];
}
function writeHashDrawing(token){
  var p=hashParts();
  if(p.length<4)return false;            /* no view in the bar yet — leave it */
  var q=(p[4]||'').split('&').filter(function(s){return s&&s.indexOf('d=')!==0;});
  if(token)q.push('d='+token);
  p[4]=q.join('&');
  if(!p[4])p.length=4;
  try{history.replaceState(null,'','#'+p.join('/'));return true;}catch(e){return false;}
}

/* The public face. Exported before ready() fires, so explore.js's hook can
   ask for hashPart() on its very first writeHash — and so the exporters and
   the codec can be exercised by tests/test_draw.py under node, where there is
   no map and no DOM at all. */
var current=[];           /* the drawing, as plain GeoJSON features */
var rewrite=null;         /* explore.js's writeHash, when it has handed it over */
window.MDDRAW={
  MAX:MAXHASH, CREDIT:CREDIT, ODBL:ODBL, ATTRIB:ATTRIB,
  encode:encode, decode:decode,
  toGeoJSON:toGeoJSON, toGPX:toGPX, toKML:toKML, fromText:fromText,
  ring:ring, fmtArea:fmtArea, fmtLen:fmtLen,
  features:function(){return current.slice();},
  /* '' when there is nothing to say, and '' when the drawing is over the cap
     — which is the refusal, not a truncation. Takes an explicit feature list
     so tests/test_draw.py can put an oversized drawing through the SAME
     predicate the page uses, rather than a copy of it that could drift. */
  hashPart:function(fs){
    var t=encode(fs||current);
    return (t&&t.length<=MAXHASH)?('d='+t):'';
  },
  /* explore.js hands over its own writeHash so there is ONE writer of the
     hash on that page instead of two racing. */
  attach:function(fn){rewrite=fn;}
};

/* ---- the map, and only through the one door ---------------------------- */
MDMAP.ready(el,function(map){
var say=document.getElementById('mdd-say');
var fileIn=document.getElementById('mdd-file');
var td,selected=null,over=false;

/* terra-draw's adapter takes the map object we were handed. It is not a
   second constructor: it adds sources and layers to the style map_shell
   built, which is exactly what explore.js does with its dots. */
try{
  td=new terraDraw.TerraDraw({
    adapter:new terraDrawMaplibreGlAdapter.TerraDrawMapLibreGLAdapter({map:map}),
    modes:[
      new terraDraw.TerraDrawPointMode(),
      new terraDraw.TerraDrawLineStringMode(),
      new terraDraw.TerraDrawPolygonMode(),
      new terraDraw.TerraDrawSelectMode({flags:{
        point:{feature:{draggable:true}},
        linestring:{feature:{draggable:true,coordinates:{midpoints:true,draggable:true,deletable:true}}},
        polygon:{feature:{draggable:true,coordinates:{midpoints:true,draggable:true,deletable:true}}}
      }})
    ]
  });
  td.start();
  td.setMode('static');
}catch(e){return;}          /* no bar rather than a broken bar */

bar.hidden=false;

function pretty(f){
  /* terra-draw keeps its own working geometry in the same store: the
     midpoints and selection handles it draws while a shape is being edited.
     Those are Points and they would be exported as if a reader had placed
     them, so they are dropped here — the only place that judgement is made. */
  var pr=f.properties||{};
  if(pr.midPoint||pr.selectionPoint)return null;
  if(!f.geometry||!TYPE[f.geometry.type])return null;
  return {type:'Feature',properties:{},geometry:f.geometry};
}
function snapshot(){
  var out=[],s=[];
  try{s=td.getSnapshot()||[];}catch(e){s=[];}
  for(var i=0;i<s.length;i++){var f=pretty(s[i]);if(f)out.push(f);}
  return out;
}
function measure(f){
  var g=f.geometry;
  if(g.type==='LineString'){
    var m=mdturf.length(f,{units:'kilometers'})*1000;
    var L=fmtLen(m);
    return {th:'ยาว '+L.th,en:L.en};
  }
  if(g.type==='Polygon'){
    var a=mdturf.area(f),A=fmtArea(a);
    var per=mdturf.length({type:'Feature',properties:{},
      geometry:{type:'LineString',coordinates:g.coordinates[0]}},{units:'kilometers'})*1000;
    var P=fmtLen(per);
    return {th:'เนื้อที่ '+A.th+' · รอบรูป '+P.th,en:A.en+' · perimeter '+P.en};
  }
  return {th:g.coordinates[1].toFixed(5)+', '+g.coordinates[0].toFixed(5),en:''};
}
function esc(s){return String(s).replace(/&/g,'&amp;').replace(/</g,'&lt;');}
function tell(th,en,cls){
  if(!say)return;
  say.innerHTML='<b'+(cls?' class="'+cls+'"':'')+'>'+esc(th)+'</b>'+
    (en?' <span class="mdd-gloss">· '+esc(en)+'</span>':'');
}
/* Every number the bar prints, recomputed from the store — never carried
   forward from the last time, because a dragged vertex changes an area and a
   remembered number would be a wrong one shown confidently. */
function report(){
  current=snapshot();
  var lines=0,polys=0,pts=0,totalM=0,totalA=0,last=null;
  for(var i=0;i<current.length;i++){
    var f=current[i],t=f.geometry.type;
    if(t==='LineString'){lines++;totalM+=mdturf.length(f,{units:'kilometers'})*1000;}
    else if(t==='Polygon'){polys++;totalA+=mdturf.area(f);}
    else pts++;
    last=f;
  }
  var token=encode(current);
  over=token.length>MAXHASH;
  if(rewrite){try{rewrite();}catch(e){}}
  else writeHashDrawing(over?'':token);

  if(!current.length){
    tell('แตะเครื่องมือ แล้วแตะบนแผนที่','Touch a tool, then touch the map');
    return;
  }
  var th=[],en=[];
  if(last){var m=measure(last);th.push(m.th);if(m.en)en.push(m.en);}
  if(polys>1||(polys===1&&lines))
    {var A=fmtArea(totalA);th.push('รวม '+A.th);en.push('total '+A.en);}
  if(lines>1){var L=fmtLen(totalM);th.push('รวม '+L.th);en.push('total '+L.en);}
  th.push(current.length+' รูป');en.push(current.length+' shape'+(current.length>1?'s':''));
  if(over){
    /* THE REFUSAL, out loud and in both languages. A drawing this big is not
       squeezed, sampled or silently dropped from the link: the reader is told
       the number and pointed at the file, which has no cap at all. */
    th.push('ใหญ่เกินจะใส่ในลิงก์ ('+token.length+' ตัวอักษร เกิน '+MAXHASH+') — บันทึกเป็นไฟล์แทน');
    en.push('too big for a link ('+token.length+' characters, cap '+MAXHASH+') — save a file instead');
  }
  tell(th.join(' · '),en.join(' · '),over?'mdd-warn':'');
}

try{td.on('change',report);}catch(e){}
try{td.on('select',function(id){selected=id;});}catch(e){}
try{td.on('deselect',function(){selected=null;});}catch(e){}

/* Restore whatever the link was carrying. addFeatures needs terra-draw's own
   mode name on each feature, which is the one property the codec does not
   store — the geometry type implies it. */
function load(features,replace){
  if(!features||!features.length)return 0;
  if(replace)try{td.clear();}catch(e){}
  var add=[];
  for(var i=0;i<features.length;i++){
    var g=features[i].geometry;
    if(!g||!MODE[g.type])continue;
    add.push({type:'Feature',properties:{mode:MODE[g.type]},geometry:g});
  }
  if(!add.length)return 0;
  try{td.addFeatures(add);}catch(e){return 0;}
  report();
  return add.length;
}
/* ---- the bar ----------------------------------------------------------
   One listener on the bar, not six on six buttons: the bar is the thing that
   exists for the whole life of the page. Nothing here is bound to the SVG
   inside .mdmap-draw, which map.js rewrites. */
var TOOLNAMES={point:['จุด','point'],linestring:['เส้น','line'],
  polygon:['รูปปิด','area'],select:['เลือก · ย้าย','select and move']};
function pressed(k){
  var bs=bar.querySelectorAll('[data-mdd]');
  for(var i=0;i<bs.length;i++){
    var v=bs[i].getAttribute('data-mdd');
    bs[i].setAttribute('aria-pressed',(v===k)?'true':'false');
  }
}
function mode(k){
  try{td.setMode(k);}catch(e){return;}
  pressed(k);
  var n=TOOLNAMES[k];
  if(n)tell(n[0],n[1]);
}
bar.addEventListener('click',function(ev){
  var b=ev.target.closest?ev.target.closest('button'):null;
  if(!b||!bar.contains(b))return;
  var k=b.getAttribute('data-mdd'),fmt=b.getAttribute('data-mdd-save');
  if(fmt){exportAs(fmt);return;}
  if(!k)return;
  if(k==='clear'){
    try{td.clear();}catch(e){}
    selected=null;mode('static');pressed('');report();return;
  }
  if(k==='erase'){
    if(selected===null||selected===undefined){
      tell('เลือกรูปก่อน แล้วค่อยลบ','Select a shape first, then delete it');
      return;
    }
    try{td.removeFeatures([selected]);}catch(e){}
    selected=null;report();return;
  }
  if(k==='open'){if(fileIn)fileIn.click();return;}
  if(k==='link'){copyLink();return;}
  mode(k);
});

/* ---- carrying it away -------------------------------------------------- */
function exportAs(fmt){
  if(!current.length){
    tell('ยังไม่มีอะไรให้บันทึก','Nothing drawn yet');return;
  }
  var d=stamp(),f,text,mime;
  if(fmt==='gpx'){f='motdang-'+d+'.gpx';text=toGPX(current);
    mime='application/gpx+xml';}
  else if(fmt==='kml'){f='motdang-'+d+'.kml';text=toKML(current);
    mime='application/vnd.google-earth.kml+xml';}
  else{f='motdang-'+d+'.geojson';text=toGeoJSON(current);
    mime='application/geo+json';}
  if(save(f,text,mime))
    tell('บันทึกแล้ว · '+f,'saved — it opens in OsmAnd, Organic Maps or Google Earth');
  else
    tell('เบราว์เซอร์นี้บันทึกไฟล์ไม่ได้','This browser would not hand the file over');
}
function copyLink(){
  var t=encode(current);
  if(!t){tell('ยังไม่มีอะไรให้ส่ง','Nothing drawn yet');return;}
  if(t.length>MAXHASH){
    tell('ใหญ่เกินจะใส่ในลิงก์ ('+t.length+' ตัวอักษร) — บันทึกเป็นไฟล์แทน',
         'too big for a link ('+t.length+' characters) — save a file instead','mdd-warn');
    return;
  }
  if(rewrite){try{rewrite();}catch(e){}}else writeHashDrawing(t);
  var url=location.href;
  if(navigator.clipboard&&navigator.clipboard.writeText){
    navigator.clipboard.writeText(url).then(function(){
      tell('คัดลอกลิงก์แล้ว','link copied');
    },function(){tell('ลิงก์อยู่ในแถบที่อยู่แล้ว','the link is in the address bar');});
  }else{
    tell('ลิงก์อยู่ในแถบที่อยู่แล้ว','the link is in the address bar');
  }
}

/* ---- reading one back -------------------------------------------------- */
if(fileIn){
  fileIn.addEventListener('change',function(){
    var f=fileIn.files&&fileIn.files[0];
    if(!f)return;
    var done=function(text){
      var got=fromText(text);
      if(!got||!got.length){
        /* Refused out loud. Half-reading a file a reader trusted is how a
           boundary comes back with three of its five corners. */
        tell('อ่านไฟล์นี้ไม่ได้ — รองรับ GeoJSON, GPX และ KML',
             'Could not read that file. GeoJSON, GPX and KML are what this reads.',
             'mdd-warn');
        fileIn.value='';return;
      }
      var n=load(got,false);
      tell('เพิ่ม '+n+' รูปจากไฟล์',n+' shape'+(n>1?'s':'')+' added from the file');
      fileIn.value='';
    };
    if(f.text)f.text().then(done,function(){done('');});
    else{var r=new FileReader();r.onload=function(){done(r.result);};r.readAsText(f);}
  });
}

load(readHashDrawing(),true);
report();
});
})();
"""


def emit(g):
    """Write draw.js and draw.css, and copy the vendored libraries and their
    licences into docs/vendor/ beside MapLibre's.

    Silent no-op when disabled, which is the state the site ships in if the
    basemap is switched off or a vendored file is missing — the same supported
    absence map_shell.emit() keeps.

    The byte costs come back measured rather than remembered: the docstring's
    table is for the libraries, which only change when somebody re-vendors
    them, but draw.js changes every time this file does and a number in a
    comment would be wrong by the next commit.
    """
    docs = g["DOCS"]
    if not enabled():
        return {"enabled": False}
    import gzip
    js, css = _js(), CSS
    (docs / "draw.js").write_text(js)
    (docs / "draw.css").write_text(css)
    vend = docs / "vendor"
    vend.mkdir(exist_ok=True)
    lib_gz = 0
    for f in VENDOR:
        src = ROOT / "assets" / "vendor" / f
        if not src.exists():
            continue
        b = src.read_bytes()
        (vend / f).write_bytes(b)
        if f.endswith(".js"):
            lib_gz += len(gzip.compress(b, 9))

    def gz(s):
        return len(gzip.compress(s.encode("utf-8"), 9))

    return {"enabled": True,
            "version": version(),
            "libs_gz": lib_gz,
            "draw_js_gz": gz(js),
            "draw_css_gz": gz(css),
            "total_gz": lib_gz + gz(js) + gz(css),
            "hash": hash_capacity()}


if __name__ == "__main__":
    import sys
    print("draw_layer — the reader's own GIS (R1+R2).", file=sys.stderr)
    print("enabled:", enabled(), file=sys.stderr)
    print("version:", version(), file=sys.stderr)
    print("hash:", json.dumps(hash_capacity(), ensure_ascii=False), file=sys.stderr)
    print("This layer runs from build.py — it needs its helpers. "
          "Run: python3 build.py", file=sys.stderr)
