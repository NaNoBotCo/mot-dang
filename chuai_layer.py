#!/usr/bin/env python3
"""/chuai.html — ช่วย, the lifeline page. And sw.js, so the site survives the network.

WO-57 item 1. THE PROBLEM IT ANSWERS. This site holds 124 hospitals, 469
health stations, 1,129 pharmacies and 435 fuel forecourts, and until now it
answered none of them without a network. The Ping runs high in September and
October, the smoke arrives in February, and the March 2025 Mandalay quake was
felt through this city — three hazards whose first shared symptom is that the
signal goes. A directory that only answers when the tower is up has not
answered the question that gets asked at the worst hour.

WHAT THIS PAGE IS. Numbers, places, distances, hours and sources. It is not a
clinician and it is not ปภ.: no triage, no "what to do if", no prediction.
data/curated/emergency.json already wrote that rule for the four numbers and
it governs the whole page.

WHY EVERYTHING IS BAKED INTO THE HTML. 2,227 rows — every hospital, health
station, pharmacy, fuel forecourt and mapped drinking-water point with a pin
— ride inline in one array, ~176 kB raw and ~30 kB over the wire. One request
means the page is whole the instant it lands, with no second fetch to fail and
no race with the service worker. The nearest-thing search runs on the device
against that array; the reader's position does not leave the browser, which is the
site's ordinary privacy rule and not a special promise for this page.

WHAT sw.js DOES, precisely, so nobody has to read the JavaScript to know:
  · precaches this page and the stylesheet on install — the lifeline;
  · serves navigations network-first, so an online reader is never stale;
  · falls back to the cache, and then to THIS PAGE, when the network fails —
    so any address on this site, typed with no signal, lands somewhere useful
    instead of on the browser's dinosaur;
  · keeps at most CAP recently-read pages, so a reader's phone does not fill;
  · is versioned on the build date plus a hash of its own text, so a rebuild
    retires the old cache rather than layering on it.

THE KILL SWITCH, since a service worker is the one thing here that can outlive
a bad deploy: delete docs/sw.js from the build and the next update check 404s,
which unregisters it and empties its caches. `emit()` also writes the page
without it if EMERGENCY is missing, and never the other way round.

Entry point: emit(globals_of_build, data).
"""
import json
import shutil
import zlib
from pathlib import Path

import shelflife

ROOT = Path(__file__).resolve().parent

# One row per lifeline kind. The order is the order they are drawn, which is
# the order somebody needs them in, which is not the order the catalogue keeps
# them in. `sub` is the catalogue's own key; nothing is re-classified here.
KINDS = [
    ("hospital",       "โรงพยาบาล",        "Hospital",        "🏥"),
    ("health-station", "รพ.สต. · อนามัย",  "Health station",  "🩺"),
    ("pharmacy",       "ร้านขายยา",         "Pharmacy",        "💊"),
    ("fuel",           "ปั๊มน้ำมัน",         "Fuel",            "⛽"),
    # NOT "water": the catalogue already spends that sub on parks — 98 lakes,
    # reservoirs and the Ping itself — and a first draft of this page served
    # แม่น้ำปิง as somewhere to drink. The key here must not be a catalogue
    # sub, because the loop below matches on exactly that.
    ("drinking-water", "น้ำดื่ม",           "Drinking water",  "🚰"),
]
KIND_IX = {k[0]: i for i, k in enumerate(KINDS)}

# Mapped drinking water was fetched by importers/fetch_water_points.py in
# August and then used by nothing. It is a lifeline layer and it was already
# on the disk, so it is drawn here from the snapshot rather than re-crawled.
WATER_SNAP = ROOT / "cache" / "overpass" / "cm" / "water_points.json"

CAP = 60  # runtime-cached pages held by the service worker

# WHICH ROWS COUNT AS A HOSPITAL HERE. Measured 2026-10-13: the catalogue's
# `hospital` sub held 671 pinned rows across cm/cr/pth, and only 56 carry a
# health-ministry code. The rest came in from OSM and the Overture directory
# under one word: 24 animal hospitals, ~360 clinics (beauty, LASIK, dental),
# health stations written out as โรงพยาบาลส่งเสริมสุขภาพตำบล, wards and
# buildings inside a hospital, and three pharmacies. "Nearest hospital" from
# that list could be a pet clinic. So this page sorts by the row's own name,
# for this page only — the catalogue keeps its classification.
import re as _re
_ANIMAL = _re.compile(r"สัตว์|\bpets?\b|animal|\bvet|veterin", _re.I)
_STATION = _re.compile(r"รพ\.?\s*สต|รพสต|เสริมสุขภาพ|สถานีอนามัย|health promoting|"
                       r"\bpcu\b|ศูนย์สุขภาพชุมชน|ศสช|health cent(?:re|er)", _re.I)
_SHOP = _re.compile(r"ร้านยา|ร้านขายยา|รวมยา|pharmacy|drugstore", _re.I)
_HOSP = _re.compile(r"โรงพยาบาล|โรงบาล|hospital|^รพ\.|\sรพ\.", _re.I)
_PART = _re.compile(r"^(แผนก|ตึก|อาคาร|หอผู้ป่วย|ห้อง|คลินิก|ศูนย์|งาน|mri\b)|department|\bward\b|"
                    r"\bclinic\b|\bopd\b", _re.I)


def lifeline_kind(r):
    """The kind this page files a catalogue row under, or None to leave it off."""
    subs = r.get("sub") or []
    k = next((s for s in subs if s in ("hospital", "health-station", "pharmacy", "fuel")), None)
    if k != "hospital":
        return k
    nm = " ".join(x for x in (r.get("name"), r.get("nameEn"), r.get("nameTh")) if x)
    if _ANIMAL.search(nm):
        return None
    if _STATION.search(nm):
        return "health-station"
    if _SHOP.search(nm):
        return "pharmacy"
    if _HOSP.search(nm) and not _PART.search(nm):
        return "hospital"
    # A clinic, a ward or a building inside a hospital: the catalogue files
    # clinics under its own `clinic` sub, and this page does not carry that
    # shelf, so these leave the page with it. The hospital itself is its own row.
    return None


def _haversine_note():
    """The distance shown is straight-line, and the page says so once."""
    return ("ระยะทางเป็นเส้นตรง ไม่ใช่ระยะทางถนน",
            "Distances are straight-line, not road distance")


# ------------------------------------------------------------------ the rows

def lifeline_rows(g, data):
    """[kind, name, lat*1e5, lng*1e5, phone|0, slug|0] for everything pinned.

    The slug is the place's own page on this site, so a reader with signal can
    open the record; a reader without one still has the name, the pin and the
    number. It rides only on hospitals and health stations: those are the rows
    whose record page carries something the list does not, and the slugs for
    the other 1,700 cost 60 kB on a page whose whole point is to arrive on a
    bad connection. Rows with no pin are left out — a lifeline row a map
    cannot draw is not a lifeline row — and the page prints how many."""
    place_slug = g["place_slug"]
    out, dropped = [], 0
    for p in g["PROVINCES"]:
        for r in data[p["key"]]:
            k = lifeline_kind(r)
            if k is None:
                continue
            if r.get("lat") is None or r.get("lng") is None:
                dropped += 1
                continue
            nm = (r.get("name") or r.get("nameTh") or r.get("nameEn") or "").strip()
            if not nm:
                dropped += 1
                continue
            out.append([KIND_IX[k], nm,
                        round(r["lat"] * 1e5), round(r["lng"] * 1e5),
                        (r.get("phone") or "").strip() or 0,
                        (f'{r["province"]}/p/{place_slug(r)}'
                         if k in ("hospital", "health-station") else 0)])
    n_water = 0
    if WATER_SNAP.exists():
        snap = json.loads(WATER_SNAP.read_text())
        for e in snap.get("elements", []):
            lat = e.get("lat") or (e.get("center") or {}).get("lat")
            lon = e.get("lon") or (e.get("center") or {}).get("lon")
            if lat is None or lon is None:
                continue
            t = e.get("tags") or {}
            nm = (t.get("name") or "").strip()
            if not nm:
                nm = ("ตู้น้ำดื่มหยอดเหรียญ" if t.get("vending") == "water"
                      else "จุดน้ำดื่ม")
            out.append([KIND_IX["drinking-water"], nm,
                        round(lat * 1e5), round(lon * 1e5), 0, 0])
            n_water += 1
    return out, dropped, n_water


# -------------------------------------------------------------------- the air

def air_line(g):
    """The PM2.5 reading as it stood when the site was built, dated.

    A modelled number hours old is worth printing and worth stamping; it is
    not worth presenting as this minute's air. air.json already carries the
    PCD band, the model's name and its licence, so all three are said."""
    src = ROOT / "data" / "air.json"
    if not src.exists():
        return ""
    bi, esc = g["bi"], g["esc"]
    air = json.loads(src.read_text())
    cm = next((p for p in air["places"] if p["id"] == "chiang-mai"), None)
    if not cm:
        return ""
    b = cm.get("band") or {}
    return shelflife.guard("air", air.get("generated"), f'<div class="ch-air" style="--band:{esc(b.get("colour", "#888"))}">'
            f'<span class="ch-airnum">{esc(str(cm.get("pm25")))}'
            f'<small> µg/m³</small></span>'
            f'<span class="ch-airband">{bi(b.get("th", ""), b.get("en", ""))}</span>'
            f'<span class="ch-airwhen">PM2.5 · {esc(cm.get("observed", ""))} · '
            f'{esc(air.get("model", ""))}</span></div>')


# ------------------------------------------------------------------ the page

def build_page(g, rows, dropped, n_water, districts=None):
    import obs_layer
    bi, esc, att = g["bi"], g["esc"], g["att"]
    page, share_block, BASE = g["page"], g["share_block"], g["BASE"]
    mark = g["mark"]
    EMERGENCY = g["EMERGENCY"]

    tel_cards = "".join(
        f'<a class="ch-tel" href="tel:{att(n["tel"])}">'
        f'<b>{esc(n["tel"])}</b>'
        f'<span class="ch-lbl">{bi(n["th"], n["en"])}</span>'
        + (f'<span class="ch-note">{bi(n.get("note_th", ""), n.get("note_en", ""))}</span>'
           if n.get("note_th") or n.get("note_en") else "")
        + '</a>'
        for n in EMERGENCY["numbers"])

    issuers = " · ".join(
        f'<a href="{att(n["issuer_url"])}" rel="noopener">{esc(n["issuer"])}</a>'
        for n in {x["issuer"]: x for x in EMERGENCY["numbers"]}.values())

    kind_chips = "".join(
        f'<button type="button" class="ch-chip" data-k="{i}" aria-pressed="true">'
        f'{em} {bi(th, en)}</button>'
        for i, (_, th, en, em) in enumerate(KINDS))

    counts = {}
    for r in rows:
        counts[r[0]] = counts.get(r[0], 0) + 1
    tally = " · ".join(
        f'{em} {counts.get(i, 0):,}' for i, (_, th, en, em) in enumerate(KINDS))

    dnote_th, dnote_en = _haversine_note()

    body = (
        f'<h1>🆘 {bi("ช่วย — เบอร์ฉุกเฉิน ที่ใกล้ที่สุด", "Help — numbers, and what is nearest")}</h1>'

        f'<div class="ch-emerg">{tel_cards}</div>'
        f'<p class="ch-issuers">{bi("เบอร์ออกโดย", "Numbers issued by")} {issuers}</p>'

        f'<h2>{bi("ที่ใกล้ฉัน", "Nearest to me")}</h2>'
        f'<button type="button" id="ch-locate" class="ch-go">'
        f'📍 {bi("หาที่ใกล้ฉัน", "Find what is nearest")}</button>'
        f'<p class="ch-privacy">'
        + mark("ⓘ " + bi("ค้นในหน้านี้", "the search runs in this page"),
               "หน้านี้ค้นในเครื่อง และไม่ต้องใช้เน็ตในการค้น",
               "the search runs on your device and needs no network to run")
        + '</p>'
        f'<div class="ch-chips">{kind_chips}</div>'
        f'<div id="ch-out" class="ch-out" aria-live="polite"></div>'
        f'<p class="ch-tally">{tally} · {bi(dnote_th, dnote_en)}</p>'
        # Nan, 2026-09-28: "a 'how deep is your flooding' question for emergencies".
        + obs_layer.flood_block() +

        f'<h2>{bi("อากาศ ตอนที่หน้านี้ถูกสร้าง", "The air, when this page was built")}</h2>'
        + air_line(g) +

        f'<h2>{bi("หน้านี้ใช้ได้ตอนเน็ตล่ม", "Works without a network")}</h2>'
        f'<p class="ch-off">'
        + bi("เปิดหน้านี้ครั้งเดียว แล้วมันจะอยู่ในเครื่องคุณ — เบอร์ ชื่อ พิกัด "
             "และการค้นหาที่ใกล้ที่สุด ทำงานได้โดยไม่ต้องมีสัญญาณ "
             "หน้าอื่นที่คุณเคยเปิดก็จะยังอ่านได้",
             "Open this page once and your phone keeps a copy. The numbers, the "
             "names, the pins and the nearest-thing search all work with no "
             "signal, and the other pages you have already read stay readable.")
        + f' <span class="ch-when">{bi("ข้อมูลชุดนี้ลงวันที่", "This copy is dated")} '
          f'{esc(g["BUILD_DATE"])}</span></p>'
        + (f'<p class="tinynote">{bi(f"อีก {dropped:,} แห่งยังไม่มีพิกัด จึงยังไม่อยู่ในหน้านี้ — ไม่ได้แปลว่าไม่มี", f"Another {dropped:,} places have no pin yet and so are not on this page — which is not a no.")}</p>'
           if dropped else "")
        + f'<p class="tinynote">{bi("จุดน้ำดื่มจาก OpenStreetMap (%d จุด ในเขตเมืองเชียงใหม่)" % n_water, "Drinking-water points from OpenStreetMap (%d, Mueang Chiang Mai)" % n_water)}</p>'

        + (f'<p class="ch-print"><a href="chuai.pdf">🖨 '
           + bi("แผ่นติดฝาบ้าน — พิมพ์ A4 ถ่ายเอกสารแจกได้ (PDF)",
                "The fridge-door sheet — A4, prints and photocopies in black (PDF)")
           + '</a></p>'
           if (ROOT / "assets" / "chuai" / "chuai.pdf").exists() else "")
        + (district_index(g, districts) if districts else "")
        + f'<p class="ch-more">'
        + bi("ตามฤดู", "By season") + ' · '
        + f'<a href="foon.html">🌫 ' + bi("ฝุ่น — ห้องปลอดฝุ่นใกล้ฉัน",
                                          "Smoke — the clean-air rooms near you") + '</a> · '
        + f'<a href="nam.html">🌊 ' + bi("น้ำ — แม่น้ำปิงตอนนี้",
                                         "Water — the Ping right now") + '</a></p>'
        + share_block(BASE + "chuai.html",
                      "ช่วย · เบอร์ฉุกเฉินและที่ใกล้ที่สุด — มดแดง")
    )

    payload = json.dumps(rows, ensure_ascii=False, separators=(",", ":"))
    inline = (f'<script id="ch-data" type="application/json">{payload}</script>'
              f'<script>{js(g)}</script><script>{obs_layer.js()}</script>')

    return page(
        "ช่วย — เบอร์ฉุกเฉิน โรงพยาบาล ร้านยา ปั๊ม น้ำดื่ม ที่ใกล้ที่สุด",
        body + inline, depth=0, path="chuai.html",
        desc="เบอร์ฉุกเฉิน 1669 191 199 1155 และโรงพยาบาล รพ.สต. ร้านขายยา ปั๊มน้ำมัน "
             "จุดน้ำดื่ม ที่ใกล้ที่สุด — ใช้ได้แม้ไม่มีสัญญาณ · Thai emergency numbers "
             "and the nearest hospital, health station, pharmacy, fuel and drinking "
             "water in Chiang Mai and Chiang Rai — works with no signal.",
        extra_head='<link rel="stylesheet" href="chuai.css">'
                   '<script src="near.js"></script>'
                   + (ld_tag(numbers_ld(g)) + ld_tag(dataset_ld(g, districts))
                      if districts else ""),
        crumbs='<a href="index.html">มดแดง</a> › ' + bi("ช่วย", "Help"))


# --------------------------------------------------------------------- the js

JS_TMPL = """
// chuai.js — inline, because a lifeline page that needs a second request is
// not one. The distance function, the bilingual spans and the locate button
// come from near.js (nearby.py); what is genuinely this page's own is which
// rows it draws and in what order.
//
// NEAREST *PER KIND*, not nearest overall. The first draft sorted everything
// into one list and, standing at Tha Phae, returned twenty-four pharmacies
// and no hospital — the shop on the corner crowding out the only row that
// matters at three in the morning. Each kind now keeps its own heading and
// its own %(PER)d nearest, so the hospital is always on the page.
(function(){
var N=window.MDNear;
var rows=JSON.parse(document.getElementById('ch-data').textContent);
var KIND=%(KIND)s, PER=%(PER)d;
var out=document.getElementById('ch-out');
var on=KIND.map(function(){return true;}),here=null;
function row(km,r){
 var la=r[2]/1e5,ln=r[3]/1e5;
 return '<div class="ch-row"><span class="ch-nm">'
  +(r[5]?'<a href="'+N.esc(r[5])+'.html">':'')+N.esc(r[1])+(r[5]?'</a>':'')
  +'</span><span class="ch-km">'+N.far(km)+'</span>'
  +N.tel(r[4])+N.pin(la,ln)+'</div>';}
function draw(){
 if(!here)return;
 var h='',any=false;
 for(var k=0;k<KIND.length;k++){
  if(!on[k])continue;
  var list=[];
  for(var i=0;i<rows.length;i++){var r=rows[i];if(r[0]!==k)continue;
   list.push([N.km(here[0],here[1],r[2]/1e5,r[3]/1e5),r]);}
  if(!list.length)continue;
  list.sort(function(a,b){return a[0]-b[0];});
  any=true;
  h+='<h3 class="ch-kh">'+KIND[k][0]+' '+N.bi(KIND[k][1],KIND[k][2])+'</h3>';
  for(var j=0;j<Math.min(list.length,PER);j++)h+=row(list[j][0],list[j][1]);}
 if(any){out.innerHTML=h;}
 else{N.say(out,'\u0E44\u0E21\u0E48\u0E21\u0E35\u0E43\u0E19\u0E0A\u0E19\u0E34\u0E14\u0E17\u0E35\u0E48\u0E40\u0E25\u0E37\u0E2D\u0E01',
                'nothing in the kinds you picked');}}
document.getElementById('ch-locate').addEventListener('click',function(){
 N.locate(out,function(pos){here=pos;draw();});});
Array.prototype.forEach.call(document.querySelectorAll('.ch-chip'),function(b){
 b.addEventListener('click',function(){var k=+b.dataset.k;on[k]=!on[k];
  b.setAttribute('aria-pressed',on[k]?'true':'false');draw();});});
})();
"""

PER = 4


def js(g):
    kind = [[em, th, en] for _, th, en, em in KINDS]
    return JS_TMPL % {"KIND": json.dumps(kind, ensure_ascii=False),
                      "PER": PER}


# -------------------------------------------------------------------- the css

CSS = """/* chuai.css — generated by chuai_layer.py */
.ch-emerg{display:grid;grid-template-columns:repeat(auto-fit,minmax(11rem,1fr));
gap:.6rem;margin:1rem 0 .5rem}
.ch-tel{display:flex;flex-direction:column;gap:.1rem;text-decoration:none;
background:var(--card);border:3px solid var(--ant-dark);border-radius:.8rem;
padding:.7rem .9rem;color:var(--ink);box-shadow:3px 3px 0 var(--card-alt);
transition:transform .12s ease}
.ch-tel:hover{transform:translateY(-2px)}
.ch-tel:active{transform:scale(.98)}
.ch-tel b{font-size:2.1rem;line-height:1.05;color:var(--ant-dark);
letter-spacing:.02em}
.ch-lbl{font-weight:700}
.ch-note{font-size:.85rem;color:var(--ink-soft)}
.ch-issuers{font-size:.85rem;color:var(--ink-soft)}
.ch-issuers a{color:inherit}
.ch-go{font-size:1.15rem;font-weight:700;color:var(--paper);
background:var(--ant-dark);border:3px solid var(--ant-dark);border-radius:2rem;
padding:.6rem 1.6rem;cursor:pointer;box-shadow:3px 3px 0 var(--card-alt)}
.ch-go:active{transform:scale(.97)}
.ch-privacy{margin:.45rem 0 .2rem;font-size:.88rem;color:var(--ink-soft)}
.ch-chips{display:flex;flex-wrap:wrap;gap:.4rem;margin:.7rem 0}
.ch-chip{font:inherit;font-size:.9rem;cursor:pointer;border-radius:2rem;
padding:.28rem .85rem;background:var(--card);border:2px solid var(--gloss);
color:var(--ink)}
.ch-chip[aria-pressed="true"]{border-color:var(--ant-dark);background:#fff;
font-weight:700}
.ch-chip[aria-pressed="false"]{opacity:.55}
.ch-out{margin:.6rem 0}
.ch-kh{margin:1.1rem 0 .25rem;font-size:1.05rem}
.ch-kh:first-child{margin-top:.3rem}
.ch-row{display:flex;align-items:baseline;gap:.5rem;flex-wrap:wrap;
padding:.42rem .2rem;border-bottom:1px solid var(--card-alt)}
.ch-nm{flex:1 1 12rem;font-weight:600}
.ch-nm a{color:var(--ink)}
.ch-km{flex:0 0 auto;font-variant-numeric:tabular-nums;color:var(--ink-soft)}
.ch-rt,.ch-rm{flex:0 0 auto;text-decoration:none;font-weight:700;
color:var(--ant-dark);border:2px solid var(--ant-dark);border-radius:2rem;
padding:.05rem .6rem;font-size:.85rem}
.ch-none{color:var(--ink-soft)}
.ch-tally{font-size:.85rem;color:var(--ink-soft)}
.ch-air{display:flex;flex-wrap:wrap;align-items:baseline;gap:.5rem .9rem;
border-left:6px solid var(--band);background:var(--card);padding:.6rem .9rem;
border-radius:.5rem}
.ch-airnum{font-size:1.9rem;font-weight:700;line-height:1}
.ch-airnum small{font-size:.9rem;font-weight:400;color:var(--ink-soft)}
.ch-airband{font-weight:700}
.ch-airwhen{font-size:.82rem;color:var(--ink-soft)}
.ch-off{max-width:56ch}
.ch-print a{font-weight:700}
.ch-more a{font-weight:700}
.ch-when{color:var(--ink-soft)}
@media print{
 .chipbar,.svcbar,.seek,.langgroup,.ribbon,.sharebl,.ch-go,.ch-chips{display:none}
 .ch-tel{border-width:2px;box-shadow:none;break-inside:avoid}
 .ch-tel b{font-size:1.9rem}
 a[href]:after{content:""}
}
"""


# ------------------------------------------------------------- the sw itself

SW_SRC = """// sw.js — generated by chuai_layer.py. WO-57 item 1.
// Network-first for pages, cache as the safety net, and %(LIFE)s as the
// floor: any address on this site, opened with no signal, lands there.
// To retire this worker: delete sw.js from the build. The next update check
// 404s, the browser unregisters it, and these caches go with it.
var V='md-%(V)s', LIFE='%(LIFE)s', CAP=%(CAP)d;
var PRE=[LIFE,'/style.css','/chuai.css','/near.js'];
self.addEventListener('install',function(e){
 e.waitUntil(caches.open(V).then(function(c){
  return Promise.all(PRE.map(function(u){
   return c.add(new Request(u,{cache:'reload'})).catch(function(){});
  }));}).then(function(){return self.skipWaiting();}));});
self.addEventListener('activate',function(e){
 e.waitUntil(caches.keys().then(function(ks){
  return Promise.all(ks.map(function(k){
   return k===V?null:caches.delete(k);}));
 }).then(function(){return self.clients.claim();}));});
// The lifeline is never evicted: PRE is what makes this page answer with no
// signal, and a reader who has since browsed sixty pages needs it more, not
// less. Only the runtime pages are trimmed, oldest first.
function trim(c){c.keys().then(function(ks){
 var kill=ks.filter(function(r){
  return PRE.indexOf(new URL(r.url).pathname)<0;});
 for(var i=0;i<kill.length-CAP;i++)c.delete(kill[i]);});}
function keep(req,res){
 // A redirected response cannot be replayed for a navigation, and a 404 is
 // not worth holding — caching either would hand back the wrong page later.
 if(!res||!res.ok||res.redirected||res.type!=='basic')return;
 var copy=res.clone();
 caches.open(V).then(function(c){c.put(req,copy);trim(c);});}
function offline(){
 return new Response('offline',{status:503,
  headers:{'Content-Type':'text/plain; charset=utf-8'}});}
self.addEventListener('fetch',function(e){
 var req=e.request;
 if(req.method!=='GET')return;
 if(new URL(req.url).origin!==self.location.origin)return;
 if(req.mode==='navigate'){
  e.respondWith(fetch(req).then(function(res){keep(req,res);return res;})
   .catch(function(){
    return caches.match(req).then(function(hit){
     if(hit)return hit;
     return caches.match(LIFE).then(function(life){
      return life||offline();});});}));
  return;}
 e.respondWith(caches.match(req).then(function(hit){
  var net=fetch(req).then(function(res){keep(req,res);return res;})
   .catch(function(){return hit||offline();});
  return hit||net;}));});
"""


def sw_js(g):
    src = SW_SRC % {"V": "%s", "LIFE": "/chuai.html", "CAP": CAP}
    # Version = build date + a hash of the worker's own text, so an edit to
    # this file retires the old cache even inside one day's build.
    v = f'{g["BUILD_DATE"]}-{zlib.crc32(src.encode()) & 0xffffffff:08x}'
    return src % v


# ------------------------------------------------------- the help set, chuai/
#
# Nan, 2026-10-13: "Make the help page EXTREMELY helpful to meta's crawler."
#
# MEASURED FIRST (traffic_eye, 29 Sep–8 Oct): meta-externalagent asked for
# /chuai.html ~3,500 times a day, and for /chuai.css, /near.js, /style.css and
# /sw.js the same number of times. Its fetcher renders pages with JavaScript,
# so every page it rendered installed sw.js, and sw.js precaches this page.
# The page reached Meta once per render. What reached it was the four numbers
# and one JSON array in a <script> tag; the nearest-thing search answers only
# after a person taps "find what is nearest", which a crawler never does.
#
# So the answers are written out where a reader without a finger can read them:
#   chuai/                       the hub — what is here, counts, files, sources
#   chuai/<prov>-<amphoe>.html   every lifeline place in one district, as a
#                                table, each health station's nearest hospital,
#                                and schema.org JSON-LD for every row
#   chuai/answers.txt            all of it as plain sentences, Thai and English
#   chuai/lifeline.{json,csv,geojson}  the rows with every field, for code
# chuai.html itself gains only the district links, the file links and two
# small JSON-LD blocks: it is precached on every phone that opens any page,
# so its weight is paid by people, not by crawlers.
#
# The rule from emergency.json governs these pages too: numbers, places,
# distances, hours, sources. No triage, no advice, no "what to do if".

import csv
import io
import math
import re

SET = "chuai"
LIFE_KINDS = ("hospital", "health-station", "pharmacy", "fuel")
SCHEMA = {"hospital": "Hospital", "health-station": "MedicalClinic",
          "pharmacy": "Pharmacy", "fuel": "GasStation",
          "drinking-water": "Place"}
KIND_INFO = {k[0]: k for k in KINDS}
SINGULAR_EN = {"hospital": "hospital", "health-station": "health station",
               "pharmacy": "pharmacy", "fuel": "fuel forecourt"}
PLURAL_EN = {"hospital": "hospitals", "health-station": "health stations",
             "pharmacy": "pharmacies", "fuel": "fuel forecourts"}


def _km(a_lat, a_lng, b_lat, b_lng):
    rad = math.radians
    d1, d2 = rad(b_lat - a_lat), rad(b_lng - a_lng)
    h = (math.sin(d1 / 2) ** 2
         + math.cos(rad(a_lat)) * math.cos(rad(b_lat)) * math.sin(d2 / 2) ** 2)
    return 6371.0 * 2 * math.asin(math.sqrt(h))


def _source(r):
    """(label, licence) for a row's first source. A field row's `via` names
    our own working files, so it is said as what it is, not quoted."""
    s = (r.get("sources") or [{}])[0]
    t, via, lic = s.get("type"), s.get("via") or "", s.get("licence") or ""
    if t == "osm":
        return "OpenStreetMap", "ODbL"
    if t == "field":
        return "seen on site by Mot Dang", "CC BY 4.0"
    if t == "directory":
        return via or "directory", lic
    if t in ("register", "opendata"):
        return via or "state register", lic
    return (via or t or "")[:60], lic


def _second_name(name, en):
    en = (en or "").strip()
    return "" if not en or en.lower() in name.lower() else en


def _slugify(text):
    return re.sub(r"[^a-z0-9]+", "-", text.lower()).strip("-")


def full_rows(g, data):
    """Every pinned lifeline place with the fields a reader or a program can
    use. Same membership as lifeline_rows (same kinds, pinned, named), plus
    the drinking-water points, which carry no district."""
    import translit
    place_slug = g["place_slug"]
    prov_name = {p["key"]: p for p in g["PROVINCES"]}
    out = []
    for p in g["PROVINCES"]:
        for r in data[p["key"]]:
            k = lifeline_kind(r)
            if k is None or r.get("lat") is None or r.get("lng") is None:
                continue
            nm = (r.get("name") or r.get("nameTh") or r.get("nameEn") or "").strip()
            if not nm:
                continue
            a = r.get("attrs") or {}
            src, lic = _source(r)
            # One register still writes Wiang Chiang Rung as the minor
            # district it was before 2007; it is the same district.
            amphoe = re.sub(r"^(กิ่งอำเภอ|อำเภอ|อ\.)\s*", "", (a.get("amphoe") or "").strip())
            out.append({
                "id": r["id"], "kind": k, "name": nm,
                "name_en": _second_name(nm, r.get("nameEn")),
                "phone": (r.get("phone") or "").strip(),
                "lat": round(r["lat"], 6), "lng": round(r["lng"], 6),
                "pin": r.get("geoPrecision") or "",
                "province": p["key"], "province_th": p["th"], "province_en": p["en"],
                "amphoe": amphoe,
                "amphoe_en": translit.title(amphoe) if amphoe else "",
                "tambon": (a.get("tambon") or "").strip(),
                "address": (r.get("address") or "").strip(),
                "hours": (r.get("hours") or "").strip() if isinstance(r.get("hours"), str) else "",
                "sector": a.get("sector") or "",
                "url": g["BASE"] + f'{r["province"]}/p/{place_slug(r)}.html',
                "source": src, "licence": lic,
                "updated": r.get("updatedAt") or "",
            })
    if WATER_SNAP.exists():
        snap = json.loads(WATER_SNAP.read_text())
        for e in snap.get("elements", []):
            lat = e.get("lat") or (e.get("center") or {}).get("lat")
            lon = e.get("lon") or (e.get("center") or {}).get("lon")
            if lat is None or lon is None:
                continue
            t = e.get("tags") or {}
            nm = (t.get("name") or "").strip() or (
                "ตู้น้ำดื่มหยอดเหรียญ" if t.get("vending") == "water" else "จุดน้ำดื่ม")
            out.append({
                "id": f'osm-{e.get("type", "node")}-{e.get("id")}', "kind": "drinking-water",
                "name": nm, "name_en": "", "phone": "", "lat": round(lat, 6),
                "lng": round(lon, 6), "pin": "exact", "province": "cm", "province_th": prov_name["cm"]["th"],
                "province_en": prov_name["cm"]["en"], "amphoe": "", "amphoe_en": "",
                "tambon": "", "address": "", "hours": (t.get("opening_hours") or ""),
                "sector": "", "url": "", "source": "OpenStreetMap", "licence": "ODbL",
                "updated": "",
            })
    return out


def districts_of(rows):
    """[(slug, province, province_th, province_en, amphoe_th, amphoe_en, rows)]
    in province order, then by how many lifeline places the district holds."""
    by = {}
    for r in rows:
        if r["kind"] == "drinking-water" or not r["amphoe"]:
            continue
        by.setdefault((r["province"], r["amphoe"]), []).append(r)
    order = {}
    for r in rows:
        order.setdefault(r["province"], len(order))
    out, seen = [], set()
    for (prov, amp), rs in sorted(by.items(), key=lambda kv: (order[kv[0][0]], -len(kv[1]), kv[0][1])):
        slug = f'{prov}-{_slugify(rs[0]["amphoe_en"]) or "district"}'
        while slug in seen:
            slug += "-2"
        seen.add(slug)
        out.append((slug, prov, rs[0]["province_th"], rs[0]["province_en"],
                    amp, rs[0]["amphoe_en"], rs))
    return out


def nearest_hospitals(rows):
    """{health-station id: (hospital row, km)} — straight line, among hospital
    rows in the same province. A health station's own record cannot say where
    its referral hospital is; distance is what this site can say."""
    hosp = {}
    for r in rows:
        if r["kind"] == "hospital":
            hosp.setdefault(r["province"], []).append(r)
    out = {}
    for r in rows:
        if r["kind"] != "health-station":
            continue
        best = None
        for h in hosp.get(r["province"], []):
            km = _km(r["lat"], r["lng"], h["lat"], h["lng"])
            if best is None or km < best[1]:
                best = (h, km)
        if best:
            out[r["id"]] = best
    return out


# ------------------------------------------------------------- JSON-LD bits

def ld_tag(obj):
    txt = json.dumps(obj, ensure_ascii=False, separators=(",", ":"))
    return '<script type="application/ld+json">' + txt.replace("</", "<\\/") + "</script>"


def numbers_ld(g):
    E = g["EMERGENCY"]["numbers"]
    return {"@context": "https://schema.org", "@type": "ItemList",
            "name": "Thai emergency numbers · เบอร์ฉุกเฉิน",
            "itemListElement": [
                {"@type": "ListItem", "position": i + 1,
                 "item": {"@type": "ContactPoint", "telephone": n["tel"],
                          "contactType": n["en"], "name": n["th"],
                          "areaServed": "TH",
                          "description": n.get("note_en") or n["en"],
                          "provider": {"@type": "GovernmentOrganization",
                                       "name": n["issuer"], "url": n["issuer_url"]}}}
                for i, n in enumerate(E)]}


def dataset_ld(g, districts):
    B = g["BASE"]
    n = sum(len(d[6]) for d in districts)
    return {"@context": "https://schema.org", "@type": "Dataset",
            "name": "Lifeline places — hospitals, health stations, pharmacies, fuel, drinking water · ช่วย",
            "description": (f"{n:,} pinned hospitals, health stations (รพ.สต.), pharmacies and fuel "
                            "forecourts in northern Thailand with phone, district, sub-district, "
                            "coordinates, hours where known and per-row source, plus mapped "
                            "drinking-water points, and the Thai emergency numbers."),
            "url": B + "chuai/", "dateModified": g["BUILD_DATE"],
            "isAccessibleForFree": True,
            "license": "https://creativecommons.org/licenses/by/4.0/",
            "creator": {"@type": "Organization", "name": "มดแดง Mot Dang", "url": B},
            "spatialCoverage": {"@type": "Place", "name": ", ".join(sorted({d[3] for d in districts}))},
            "inLanguage": ["th", "en"],
            "distribution": [
                {"@type": "DataDownload", "encodingFormat": f, "contentUrl": B + "chuai/" + fn}
                for fn, f in (("lifeline.json", "application/json"),
                              ("lifeline.csv", "text/csv"),
                              ("lifeline.geojson", "application/geo+json"),
                              ("answers.txt", "text/plain"))]}


def place_ld(r):
    item = {"@type": SCHEMA[r["kind"]], "name": r["name"],
            "geo": {"@type": "GeoCoordinates", "latitude": r["lat"], "longitude": r["lng"]},
            "address": {"@type": "PostalAddress", "addressCountry": "TH",
                        "addressRegion": r["province_en"],
                        **({"addressLocality": r["amphoe_en"]} if r["amphoe_en"] else {}),
                        **({"streetAddress": r["address"]} if r["address"] else {})}}
    if r["name_en"]:
        item["alternateName"] = r["name_en"]
    if r["phone"]:
        item["telephone"] = r["phone"]
    if r["hours"]:
        item["openingHours"] = r["hours"]
    if r["url"]:
        item["url"] = r["url"]
    return item


# ------------------------------------------------------------- the pages

def _tel_links(g, phone):
    att, esc = g["att"], g["esc"]
    parts = [p.strip() for p in re.split(r"[,;/]", phone) if p.strip()]
    return " · ".join(f'<a href="tel:{att(re.sub(r"[^0-9+]", "", p))}">{esc(p)}</a>' for p in parts)


def _numbers_strip(g):
    att, esc, bi = g["att"], g["esc"], g["bi"]
    return ('<p class="cs-nums">' + "".join(
        f'<a href="tel:{att(n["tel"])}"><b>{esc(n["tel"])}</b> {bi(n["th"], n["en"])}</a>'
        for n in g["EMERGENCY"]["numbers"]) + "</p>")


def _row_table(g, rs, r_prefix):
    bi, esc, att = g["bi"], g["esc"], g["att"]
    head = (f'<tr><th>{bi("ชื่อ", "Name")}</th><th>{bi("โทร", "Phone")}</th>'
            f'<th>{bi("ตำบล", "Sub-district")}</th><th>{bi("เวลา", "Hours")}</th>'
            f'<th>{bi("พิกัด", "Coordinates")}</th></tr>')
    body = []
    for r in sorted(rs, key=lambda x: (x["tambon"], x["name"])):
        nm = esc(r["name"]) + (f' <small>{esc(r["name_en"])}</small>' if r["name_en"] else "")
        if r["url"]:
            nm = f'<a href="{att(r["url"])}">{nm}</a>'
        ll = f'{r["lat"]:.5f},{r["lng"]:.5f}'
        approx = "≈ " if r["pin"] and r["pin"] != "exact" else ""
        body.append(
            f'<tr><td>{nm}' + (f'<br><small>{esc(r["address"])}</small>' if r["address"] else "")
            + (f'</td><td>{_tel_links(g, r["phone"])}</td>' if r["phone"] else '</td><td class="cs-no">—</td>')
            + (f'<td>ต.{esc(r["tambon"])}</td>' if r["tambon"] else '<td class="cs-no">—</td>')
            + (f'<td>{esc(r["hours"])}</td>' if r["hours"] else '<td class="cs-no">—</td>')
            + f'<td>{approx}<a href="geo:{ll}?q={ll}">{ll}</a></td></tr>')
    return f'<div class="cs-wrap"><table class="cs-t cs-list">{head}{"".join(body)}</table></div>'


def district_page(g, d, near, others):
    slug, prov, pth, pen, ath, aen, rs = d
    bi, esc, page = g["bi"], g["esc"], g["page"]
    count = {}
    for r in rs:
        count[r["kind"]] = count.get(r["kind"], 0) + 1
    phones = sum(1 for r in rs if r["phone"])
    summary_en = (f"{aen} district (อำเภอ{ath}), {pen} province: "
                  + ", ".join(f'{count[k]} {(PLURAL_EN[k] if count[k] != 1 else SINGULAR_EN[k])}'
                              for k in LIFE_KINDS if count.get(k))
                  + f". {phones} of them have a phone number on record.")
    summary_th = (f"อำเภอ{ath} จังหวัด{pth}: "
                  + " ".join(f'{KIND_INFO[k][1]} {count[k]} แห่ง' for k in LIFE_KINDS if count.get(k))
                  + f" — มีเบอร์โทร {phones} แห่ง")
    parts = [f'<h1>{bi(f"ช่วย · อำเภอ{ath} จ.{pth}", f"Help · {aen} district, {pen}")}</h1>',
             _numbers_strip(g),
             f'<p class="cs-sum">{bi(summary_th, summary_en)}</p>']
    for k in LIFE_KINDS:
        ks = [r for r in rs if r["kind"] == k]
        if not ks:
            continue
        _, th, en, _em = KIND_INFO[k]
        parts.append(f'<h2 id="{k}">{bi(f"{th} ในอำเภอ{ath} ({len(ks)})", f"{en} in {aen} ({len(ks)})")}</h2>')
        parts.append(_row_table(g, ks, "../"))
    hs = [r for r in rs if r["kind"] == "health-station" and r["id"] in near]
    if hs:
        parts.append(f'<h2 id="nearest-hospital">{bi("รพ.สต. แต่ละแห่ง กับโรงพยาบาลที่ใกล้ที่สุด", "Each health station and its nearest hospital")}</h2>')
        rows_ = []
        for r in sorted(hs, key=lambda x: x["name"]):
            h, km = near[r["id"]]
            rows_.append(f'<tr><td>{esc(r["name"])}</td><td>{esc(h["name"])}'
                         + (f' · {_tel_links(g, h["phone"])}' if h["phone"] else "")
                         + f'</td><td>{km:.1f} km</td></tr>')
        parts.append(f'<div class="cs-wrap"><table class="cs-t cs-list"><tr><th>{bi("รพ.สต.", "Health station")}</th>'
                     f'<th>{bi("โรงพยาบาลที่ใกล้ที่สุด", "Nearest hospital")}</th><th>{bi("ระยะ", "Distance")}</th></tr>'
                     + "".join(rows_) + "</table></div>")
    dn_th, dn_en = _haversine_note()
    parts.append(f'<p class="tinynote">{bi(dn_th, dn_en)} · '
                 + bi("≈ คือพิกัดโดยประมาณ", "≈ marks an approximate pin") + ' · '
                 + bi("อำเภอและตำบลอ่านจากที่อยู่ของแต่ละแห่ง",
                      "District and sub-district are read from each place's own address")
                 + f' · {bi("ข้อมูลชุดนี้ลงวันที่", "This copy is dated")} {esc(g["BUILD_DATE"])}</p>')
    parts.append(f'<p class="ch-more"><a href="../chuai.html">{bi("ช่วย — ค้นที่ใกล้ฉัน ใช้ได้แม้ไม่มีเน็ต", "Help — find what is nearest, works offline")}</a>'
                 f' · <a href="index.html">{bi("ทุกอำเภอ และไฟล์ข้อมูล", "Every district, and the data files")}</a></p>')
    sib = [o for o in others if o[1] == prov and o[0] != slug]
    if sib:
        parts.append(f'<p class="cs-sib">{bi(f"อำเภออื่นใน จ.{pth}", f"Other districts in {pen}")}: '
                     + " · ".join(f'<a href="{o[0]}.html">{bi(o[4], o[5])}</a>' for o in sib) + "</p>")
    ld = {"@context": "https://schema.org", "@type": "ItemList",
          "name": f"Hospitals, health stations, pharmacies and fuel in {aen}, {pen}",
          "numberOfItems": len(rs),
          "itemListElement": [{"@type": "ListItem", "position": i + 1, "item": place_ld(r)}
                              for i, r in enumerate(rs)]}
    return page(
        f"ช่วย · อำเภอ{ath} — โรงพยาบาล รพ.สต. ร้านยา ปั๊ม · Help · {aen}",
        "".join(parts), depth=1, path=f"{SET}/{slug}.html",
        desc=f"{summary_th} · {summary_en} Thai emergency numbers 1669 191 199 1784 1155.",
        extra_head='<link rel="stylesheet" href="../chuai.css">' + ld_tag(ld),
        crumbs=(f'<a href="../index.html">มดแดง</a> › <a href="../chuai.html">{bi("ช่วย", "Help")}</a>'
                f' › <a href="index.html">{bi("ทุกอำเภอ", "Districts")}</a> › {bi(ath, aen)}'))


def answers_txt(g, rows, districts, near):
    """Every answer on these pages as plain sentences. A program reading this
    file has nothing to strip and nothing to render."""
    E = g["EMERGENCY"]["numbers"]
    B = g["BASE"]
    L = [f"# ช่วย · Help — Mot Dang (motdang.net), as plain text",
         f"# Dated {g['BUILD_DATE']}. Source page: {B}chuai.html · districts: {B}chuai/",
         "# Numbers, places, distances, hours and sources. Distances are straight-line.",
         "# Licence: CC BY 4.0 for the compilation; OpenStreetMap-derived rows ODbL; each row names its source.",
         "",
         "## Thai emergency numbers · เบอร์ฉุกเฉิน",
         ""]
    for n in E:
        L.append(f"- {n['tel']}: {n['en']} · {n['th']}"
                 + (f" — {n['note_en']}" if n.get("note_en") else "")
                 + f" (issued by {n['issuer']}, {n['issuer_url']})")
    L += ["", "Q: What number do I call for an ambulance in Chiang Mai or Chiang Rai?",
          "A: 1669, free from any network, 24 hours (สพฉ., https://www.niems.go.th/).",
          "Q: Is there an English-speaking police line?",
          "A: 1155, with English-speaking officers (กองบัญชาการตำรวจท่องเที่ยว, https://tourist.police.go.th/).",  # stylecheck: allow — the agency’s own web address
          "Q: Flood, wildfire or earthquake?",
          "A: 1784, the disaster hotline of the Department of Disaster Prevention and Mitigation.",
          ""]
    for slug, prov, pth, pen, ath, aen, rs in districts:
        L += [f"## {aen} district, {pen} · อำเภอ{ath} จังหวัด{pth}",
              f"Page: {B}{SET}/{slug}.html", ""]
        for k in LIFE_KINDS:
            ks = sorted((r for r in rs if r["kind"] == k), key=lambda x: (not x["phone"], x["name"]))
            if not ks:
                continue
            _, th, en, _em = KIND_INFO[k]
            L.append(f"### {en} in {aen} · {th} ({len(ks)})")
            for r in ks:
                bits = [r["name"] + (f" ({r['name_en']})" if r["name_en"] else "")]
                bits.append(f"tel {r['phone']}" if r["phone"] else "no phone on record")
                if r["tambon"]:
                    bits.append(f"ต.{r['tambon']}")
                if r["hours"]:
                    bits.append(f"hours {r['hours']}")
                bits.append(f"{r['lat']:.5f},{r['lng']:.5f}"
                            + (" (pin approximate)" if r["pin"] and r["pin"] != "exact" else ""))
                if r["url"]:
                    bits.append(r["url"])
                L.append("- " + " · ".join(bits))
            L.append("")
        hs = [r for r in rs if r["kind"] == "health-station" and r["id"] in near]
        if hs:
            L.append(f"### Nearest hospital to each health station in {aen} · โรงพยาบาลที่ใกล้ รพ.สต. ที่สุด")
            for r in sorted(hs, key=lambda x: x["name"]):
                h, km = near[r["id"]]
                L.append(f"- {r['name']} → {h['name']}, {km:.1f} km"
                         + (f", tel {h['phone']}" if h["phone"] else ""))
            L.append("")
    w = [r for r in rows if r["kind"] == "drinking-water"]
    if w:
        L += [f"## Drinking-water points, Mueang Chiang Mai · จุดน้ำดื่ม ({len(w)}, from OpenStreetMap)", ""]
        L += [f"- {r['name']} · {r['lat']:.5f},{r['lng']:.5f}" for r in w]
    return "\n".join(L) + "\n"


FIELDS = ["id", "kind", "name", "name_en", "phone", "lat", "lng", "pin", "province",
          "province_en", "amphoe", "amphoe_en", "tambon", "address", "hours",
          "sector", "url", "source", "licence", "updated"]


def data_files(g, rows):
    meta = {"name": "ช่วย · Mot Dang lifeline places", "dated": g["BUILD_DATE"],
            "page": g["BASE"] + "chuai.html", "count": len(rows),
            "kinds": {k[0]: {"th": k[1], "en": k[2]} for k in KINDS},
            "fields": FIELDS,
            "notes": ["Rows with no pin are not here.",
                      "kind is filed by the row's own name: a hospital is a row named as one; animal hospitals, clinics and wards inside a hospital are left out.",
                      "amphoe and tambon are read from each place's own address.",
                      "Distances anywhere in this set are straight-line.",
                      "pin is the record's own precision: exact, or approx for a pin placed from an address."],
            "licence": "CC BY 4.0 (https://creativecommons.org/licenses/by/4.0/) for the compilation; "
                       "OpenStreetMap-derived rows ODbL; each row names its source and licence.",
            "emergency_numbers": [{k: n.get(k, "") for k in ("tel", "th", "en", "note_en", "issuer", "issuer_url")}
                                  for n in g["EMERGENCY"]["numbers"]]}
    js = json.dumps({"meta": meta, "rows": [{f: r[f] for f in FIELDS} for r in rows]},
                    ensure_ascii=False, separators=(",", ":"))
    buf = io.StringIO()
    w = csv.writer(buf)
    w.writerow(FIELDS)
    for r in rows:
        w.writerow([r[f] for f in FIELDS])
    gj = json.dumps({"type": "FeatureCollection", "name": meta["name"], "dated": meta["dated"],
                     "licence": meta["licence"],
                     "features": [{"type": "Feature",
                                   "geometry": {"type": "Point", "coordinates": [r["lng"], r["lat"]]},
                                   "properties": {f: r[f] for f in FIELDS if f not in ("lat", "lng")}}
                                  for r in rows]},
                    ensure_ascii=False, separators=(",", ":"))
    return js, buf.getvalue(), gj


def hub_page(g, rows, districts):
    bi, esc, page, B = g["bi"], g["esc"], g["page"], g["BASE"]
    provs = []
    for d in districts:
        if d[1] not in [p[0] for p in provs]:
            provs.append((d[1], d[2], d[3]))
    count = {}
    for r in rows:
        count[(r["province"], r["kind"])] = count.get((r["province"], r["kind"]), 0) + 1
    head = "<tr><th></th>" + "".join(f"<th>{bi(k[1], k[2])}</th>" for k in KINDS) + "</tr>"
    trs = "".join(f"<tr><th>{bi(pth, pen)}</th>"
                  + "".join(f'<td>{count.get((pk, k[0]), 0):,}</td>' for k in KINDS) + "</tr>"
                  for pk, pth, pen in provs)
    dl = []
    for pk, pth, pen in provs:
        ds = [d for d in districts if d[1] == pk]
        dl.append(f'<h3>{bi(f"จังหวัด{pth} · {len(ds)} อำเภอ", f"{pen} · {len(ds)} districts")}</h3><ul class="cs-dl">'
                  + "".join(f'<li><a href="{d[0]}.html">{bi("อ." + d[4], d[5])}</a> <small>{len(d[6])}</small></li>'
                            for d in ds) + "</ul>")
    files = [("answers.txt", "ทุกคำตอบเป็นประโยคธรรมดา ไทยและอังกฤษ",
              "every answer as plain sentences, Thai and English"),
             ("lifeline.json", "ทุกแถวพร้อมทุกช่อง และคำอธิบายช่อง",
              "every row with every field, and what the fields mean"),
             ("lifeline.csv", "ตารางเดียวกัน เปิดในสเปรดชีตได้", "the same table, for a spreadsheet"),
             ("lifeline.geojson", "เป็นจุดบนแผนที่ ลากใส่โปรแกรมแผนที่ได้",
              "as map points, for any GIS or map library")]
    n = sum(1 for r in rows if r["kind"] != "drinking-water")
    body = (
        f'<h1>{bi("ช่วย · ทุกอำเภอ และไฟล์ข้อมูล", "Help · every district, and the data")}</h1>'
        + _numbers_strip(g)
        + f'<p>{bi(f"โรงพยาบาล รพ.สต. ร้านขายยา และปั๊มน้ำมัน {n:,} แห่งที่มีพิกัด แยกตามอำเภอ พร้อมเบอร์โทร ตำบล เวลาเปิด และแหล่งที่มาของแต่ละแห่ง", f"{n:,} pinned hospitals, health stations, pharmacies and fuel forecourts, sorted by district, with phone, sub-district, hours and each place’s source.")}</p>'
        + "<p>" + bi("โรงพยาบาลในชุดนี้คือแถวที่ชื่อเป็นโรงพยาบาล — โรงพยาบาลสัตว์ คลินิก และแผนกในโรงพยาบาลไม่อยู่ในชุดนี้ รพ.สต. ที่ชื่อว่าโรงพยาบาลส่งเสริมสุขภาพตำบลอยู่กับ รพ.สต.", "A hospital in this set is a row whose own name says hospital. Animal hospitals, clinics, and wards inside a hospital are not in this set; health stations named โรงพยาบาลส่งเสริมสุขภาพตำบล are filed with the health stations.") + "</p>"
        + f'<div class="cs-wrap"><table class="cs-t">{head}{trs}</table></div>'
        + f'<h2>{bi("แยกตามอำเภอ", "By district")}</h2>' + "".join(dl)
        + f'<h2 id="files">{bi("ไฟล์ข้อมูล", "Data files")}</h2><ul>'
        + "".join(f'<li><a href="{fn}">{fn}</a> — {bi(th, en)}</li>' for fn, th, en in files) + "</ul>"
        + f'<h2>{bi("คำถามที่หน้าเหล่านี้ตอบได้", "Questions these pages answer")}</h2><ul class="cs-q">'
        + "".join(f"<li>{bi(th, en)}</li>" for th, en in (
            ("เรียกรถพยาบาลเบอร์อะไร", "What number calls an ambulance? — 1669"),
            ("โรงพยาบาลในอำเภอนี้มีที่ไหนบ้าง เบอร์อะไร", "Which hospitals are in this district, and their numbers"),
            ("รพ.สต. นี้ใกล้โรงพยาบาลไหนที่สุด ห่างกี่กิโล", "Which hospital is nearest to this health station, and how far"),
            ("ร้านขายยาที่มีเวลาเปิดบันทึกไว้", "Which pharmacies have their hours on record"),
            ("ปั๊มน้ำมันในตำบลนี้", "Fuel forecourts in this sub-district"),
            ("จุดน้ำดื่มในเมืองเชียงใหม่", "Drinking-water points in Mueang Chiang Mai"))) + "</ul>"
        + f'<h2>{bi("ที่มา", "Sources")}</h2><p>'
        + bi("แต่ละแถวบอกแหล่งของตัวเอง: ทะเบียนหน่วยบริการสาธารณสุข (data.go.th) OpenStreetMap ไดเรกทอรี Overture และสิ่งที่มดแดงเห็นเองหน้าร้าน",
             "Each row names its own source: the health-facility registers on data.go.th, OpenStreetMap, the Overture directory, and signs Mot Dang read on site.")
        + f' {esc(g.get("LICENSE_LINE_EN", ""))}</p>'
        + f'<p class="tinynote">{bi("ข้อมูลชุดนี้ลงวันที่", "This copy is dated")} {esc(g["BUILD_DATE"])} · '
        + bi("อ้างอิง: มดแดง motdang.net/chuai/", "Cite as: Mot Dang, motdang.net/chuai/") + "</p>"
        + f'<p class="ch-more"><a href="../chuai.html">{bi("ช่วย — ค้นที่ใกล้ฉัน ใช้ได้แม้ไม่มีเน็ต", "Help — find what is nearest, works offline")}</a></p>')
    return page(
        "ช่วย · ทุกอำเภอ — โรงพยาบาล รพ.สต. ร้านยา ปั๊ม น้ำดื่ม และไฟล์ข้อมูล",
        body, depth=1, path=f"{SET}/index.html",
        desc=(f"โรงพยาบาล รพ.สต. ร้านขายยา ปั๊มน้ำมัน {n:,} แห่ง แยกตามอำเภอ พร้อมเบอร์โทรและพิกัด · "
              f"{n:,} hospitals, health stations, pharmacies and fuel forecourts in northern Thailand "
              "by district, with phones and coordinates, as pages, plain text, JSON, CSV and GeoJSON."),
        extra_head='<link rel="stylesheet" href="../chuai.css">' + ld_tag(dataset_ld(g, districts)),
        crumbs=f'<a href="../index.html">มดแดง</a> › <a href="../chuai.html">{bi("ช่วย", "Help")}</a> › {bi("ทุกอำเภอ", "Districts")}')


def district_index(g, districts):
    """The short block chuai.html carries: one link per district, the files."""
    bi = g["bi"]
    provs = []
    for d in districts:
        if d[1] not in [p[0] for p in provs]:
            provs.append((d[1], d[2], d[3]))
    out = [f'<h2>{bi("แยกตามอำเภอ", "By district")}</h2>']
    for pk, pth, pen in provs:
        out.append(f'<p class="cs-sib"><b>{bi(pth, pen)}</b>: ' + " · ".join(
            f'<a href="{SET}/{d[0]}.html">{bi(d[4], d[5])}</a>' for d in districts if d[1] == pk) + "</p>")
    out.append(f'<p class="tinynote"><a href="{SET}/">{bi("ทุกอำเภอ", "All districts")}</a> · '
               f'<a href="{SET}/answers.txt">answers.txt</a> · <a href="{SET}/lifeline.json">JSON</a> · '
               f'<a href="{SET}/lifeline.csv">CSV</a> · <a href="{SET}/lifeline.geojson">GeoJSON</a></p>')
    return "".join(out)


def llms_section(g, districts=None):
    B = g["BASE"]
    return (f"\n## 🆘 ช่วย · Help — emergency numbers and lifeline places\n"
            f"{B}chuai.html — the five Thai emergency numbers, and the nearest hospital, health "
            "station, pharmacy, fuel and drinking water, searched on the device; it works with no network.\n"
            f"{B}chuai/ — the same places by district, as tables with schema.org JSON-LD.\n"
            f"{B}chuai/answers.txt — every answer as plain sentences, Thai and English.\n"
            f"{B}chuai/lifeline.json · lifeline.csv · lifeline.geojson — every row, every field, "
            "per-row source and licence.\n")


CS_CSS = """
.cs-nums{display:flex;flex-wrap:wrap;gap:.3rem .9rem;font-size:.95rem}
.cs-nums a{text-decoration:none;color:var(--ink)}
.cs-nums b{color:var(--ant-dark);font-size:1.15rem}
.cs-sum{font-weight:600}
.cs-wrap{overflow-x:auto;-webkit-overflow-scrolling:touch;margin:.4rem 0 1rem}
.cs-t{border-collapse:collapse;width:100%;font-size:.9rem}
.cs-t th,.cs-t td{text-align:left;vertical-align:top;padding:.35rem .45rem;
border-bottom:1px solid var(--card-alt)}
.cs-t th{background:var(--card);font-weight:700}
.cs-t td small{color:var(--ink-soft)}
.cs-t td:nth-child(5){white-space:nowrap;font-variant-numeric:tabular-nums}
.cs-dl{columns:14rem;padding-left:1.1rem}
h1{overflow-wrap:anywhere}
@media (max-width:640px){
 .cs-list,.cs-list tbody,.cs-list tr{display:block}
 .cs-list tr:first-child{display:none}
 .cs-list tr{padding:.5rem .1rem;border-bottom:1px solid var(--card-alt)}
 .cs-list td{display:inline;border:0;padding:0 .7rem 0 0}
 .cs-list td:first-child{display:block;margin-bottom:.15rem}
 .cs-list td.cs-no{display:none}
 .cs-wrap{overflow-x:visible}
}
.cs-sib{line-height:1.9}
"""


def emit_set(g, rows):
    """Writes docs/chuai/. Returns (districts, one-line summary)."""
    DOCS = g["DOCS"]
    out = DOCS / SET
    out.mkdir(parents=True, exist_ok=True)
    districts = districts_of(rows)
    near = nearest_hospitals(rows)
    for d in districts:
        (out / f"{d[0]}.html").write_text(district_page(g, d, near, districts))
    (out / "index.html").write_text(hub_page(g, rows, districts))
    (out / "answers.txt").write_text(answers_txt(g, rows, districts, near))
    js, cs, gj = data_files(g, rows)
    (out / "lifeline.json").write_text(js)
    (out / "lifeline.csv").write_text(cs)
    (out / "lifeline.geojson").write_text(gj)
    return districts, f"chuai/: {len(districts)} district pages, {len(rows):,} rows in the files"


# -------------------------------------------------------------------- emit

def emit(g, data):
    DOCS = g["DOCS"]
    import nearby
    nearby.emit(DOCS)
    rows, dropped, n_water = lifeline_rows(g, data)
    (DOCS / "chuai.css").write_text(CSS + CS_CSS)
    districts, set_note = emit_set(g, full_rows(g, data))
    html = build_page(g, rows, dropped, n_water, districts)
    (DOCS / "chuai.html").write_text(html)
    (DOCS / "sw.js").write_text(sw_js(g))
    # WO-57 item 3. The sheet ships beside the page for the same reason
    # /tawai.html ships carve-words.pdf: the person who needs it is standing
    # at a printer, or handing paper to somebody with no phone at all.
    sheet = ROOT / "assets" / "chuai" / "chuai.pdf"
    if sheet.exists():
        shutil.copyfile(sheet, DOCS / "chuai.pdf")
    kb = len(html.encode()) / 1024
    by = {}
    for r in rows:
        by[r[0]] = by.get(r[0], 0) + 1
    tally = " ".join(f"{KINDS[i][0]}:{by.get(i, 0)}" for i in range(len(KINDS)))
    return (f"{len(rows):,} lifeline rows ({tally}), {dropped:,} unpinned, "
            f"page {kb:.0f} kB, sw.js cap {CAP}; {set_note}")


if __name__ == "__main__":
    print("This layer runs from build.py — it needs its helpers. "
          "Run: python3 build.py")
