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
against that array; the reader's position is never sent anywhere, which is the
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
            subs = r.get("sub") or []
            k = next((s for s in subs if s in KIND_IX), None)
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
    return (f'<div class="ch-air" style="--band:{esc(b.get("colour", "#888"))}">'
            f'<span class="ch-airnum">{esc(str(cm.get("pm25")))}'
            f'<small> µg/m³</small></span>'
            f'<span class="ch-airband">{bi(b.get("th", ""), b.get("en", ""))}</span>'
            f'<span class="ch-airwhen">PM2.5 · {esc(cm.get("observed", ""))} · '
            f'{esc(air.get("model", ""))}</span></div>')


# ------------------------------------------------------------------ the page

def build_page(g, rows, dropped, n_water):
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
        + mark("ⓘ " + bi("ตำแหน่งอยู่ในเครื่องคุณเท่านั้น", "your position stays on your device"),
               "หน้านี้ค้นในเครื่อง ไม่ส่งพิกัดไปที่ใด และไม่ต้องใช้เน็ตในการค้น",
               "the search runs on your device; no coordinates are sent anywhere, "
               "and it needs no network to run")
        + '</p>'
        f'<div class="ch-chips">{kind_chips}</div>'
        f'<div id="ch-out" class="ch-out" aria-live="polite"></div>'
        f'<p class="ch-tally">{tally} · {bi(dnote_th, dnote_en)}</p>'

        f'<h2>{bi("อากาศ ตอนที่หน้านี้ถูกสร้าง", "The air, when this page was built")}</h2>'
        + air_line(g) +

        f'<h2>{bi("หน้านี้ใช้ได้ตอนเน็ตล่ม", "Works without a network")}</h2>'
        f'<p class="ch-off">'
        + bi("เปิดหน้านี้ครั้งเดียว แล้วมันจะอยู่ในเครื่องคุณ — เบอร์ ชื่อ พิกัด "
             "และการค้นหาที่ใกล้ที่สุด ทำงานได้โดยไม่ต้องมีสัญญาณ "
             "หน้าอื่นที่คุณเคยเปิดก็จะยังอ่านได้",
             "Open this page once and it stays on your device. The numbers, the "
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
              f'<script>{js(g)}</script>')

    return page(
        "ช่วย — เบอร์ฉุกเฉิน โรงพยาบาล ร้านยา ปั๊ม น้ำดื่ม ที่ใกล้ที่สุด",
        body + inline, depth=0, path="chuai.html",
        desc="เบอร์ฉุกเฉิน 1669 191 199 1155 และโรงพยาบาล รพ.สต. ร้านขายยา ปั๊มน้ำมัน "
             "จุดน้ำดื่ม ที่ใกล้ที่สุด — ใช้ได้แม้ไม่มีสัญญาณ · Thai emergency numbers "
             "and the nearest hospital, health station, pharmacy, fuel and drinking "
             "water in Chiang Mai and Chiang Rai — works with no signal.",
        extra_head='<link rel="stylesheet" href="chuai.css">'
                   '<script src="near.js"></script>',
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


# -------------------------------------------------------------------- emit

def emit(g, data):
    DOCS = g["DOCS"]
    import nearby
    nearby.emit(DOCS)
    rows, dropped, n_water = lifeline_rows(g, data)
    (DOCS / "chuai.css").write_text(CSS)
    html = build_page(g, rows, dropped, n_water)
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
            f"page {kb:.0f} kB, sw.js cap {CAP}")


if __name__ == "__main__":
    print("This layer runs from build.py — it needs its helpers. "
          "Run: python3 build.py")
