#!/usr/bin/env python3
"""explore_layer.py — /map.html, the map as a way IN.

WHY THIS EXISTS
---------------
Every map on this site answered one question that had already been asked
somewhere else: here is the place whose page you are on, here is the shelf you
already chose, here is the round you already picked. A reader who wanted to
start from the city — "what is around me", "show me temples and coffee at the
same time", "what is over there" — had no door. The only way in was the
directory tree, and the maps were something the directory occasionally showed
you.

So this is the other door. It opens on a named landmark, paints whatever
shelves the reader turns on, and every view it can show is a link, so a map is
something a person can send.

WHAT IT DOES NOT DO
-------------------
It does not replace the directory, and the page says so by carrying the whole
shelf list under the map as ordinary links. That list is what a reader with
scripting off gets, what prints, and what a crawler reads — the same bargain
every other map here keeps, and the reason this page is allowed to be a map.

It also never asks where the reader is. The near-me button goes through MDLOC
in md.js, which is the one door to that prompt on this site, and until it is
pressed this page has no idea and does not want one.

THE ONE PLACE THIS BREAKS THE HOUSE PATTERN, AND WHY
----------------------------------------------------
Everywhere else, Python draws an SVG and the shell puts ground underneath.
That is right for a dozen marks and impossible for this: the explore map
paints thousands of points and repaints them every time a chip is tapped.
So this layer draws INTO the basemap through `MDMAP.ready()` — which is still
not a second map constructor, the thing CLAUDE.md forbids. map_shell remains
the only module that builds a map; this one asks it for the map it built.
"""

import json
import math
import zlib

import glyphs
import map_shell


def _js():
    """explore.js, exactly as it ships."""
    return (JS.replace("%INKS%", json.dumps(INKS, ensure_ascii=False))
              .replace("%MAXON%", str(MAX_ON))
              .replace("%DEFON%", json.dumps(DEFAULT_ON))
              .replace("%CITY%", json.dumps(CITY_VIEW)))


def version():
    """Content hash for the `?v=` on explore.js — same reasoning as
    map_shell.version(): this file is served with a week-long cache under a
    name that never changes, and a reader holding yesterday's copy against
    today's page is how a working map comes up empty."""
    return "%08x" % (zlib.crc32(_js().encode("utf-8")) & 0xFFFFFFFF)

# Six inks, and a hard cap at six shelves at once. Not an arbitrary limit: a
# reader cannot hold more than about six colours apart on a busy ground, and a
# seventh would have to repeat one, which would say two shelves are one shelf.
# Every value is picked to sit clear of the retuned ground (paper #FBF6EC,
# casing #B39058, water #8FAEC9) AND of the other five, and each is dark
# enough to read as a mark rather than as landcover.
INKS = [
    ("#C2401C", "แดงมด · ant red"),
    ("#1F6B57", "เขียวหยก · jade"),
    ("#14479B", "น้ำเงิน · blue"),
    ("#8A4E9E", "ม่วง · purple"),
    ("#B06A00", "ส้มเข้ม · amber"),
    ("#2A6E86", "ฟ้าคราม · teal"),
]
MAX_ON = len(INKS)

# What the map opens with. Not empty — an empty map is a page that asks the
# reader to guess what it is for — and not everything, which would pull down
# several megabytes onto a phone before it had earned the right to. Temples
# are the shelf this city is legible by, and they are the one every visitor
# and every local can place.
DEFAULT_ON = ["cm-wat"]

# The ring's radii, in metres: the distances a person thinks in on foot and
# on a motorbike. Same ladder as refine_layer.RADII, one step finer at the
# bottom because a map can show 300 m and a list cannot.
RING_M = ((300, "300 ม.", "300 m"), (500, "500 ม.", "500 m"), (1000, "1 กม.", "1 km"),
          (2000, "2 กม.", "2 km"), (5000, "5 กม.", "5 km"))

# The zoom a whole city reads at: the box is mounted with it, and a link
# with no view opens on it. The front page remembers the reader's city as
# localStorage md-city ("cm" / "cr", the province key); with one on record
# the map opens on that city's landmark instead of always on Chiang Mai.
CITY_ZOOM = 12.4
CITY_VIEW = {k: {"lng": c["lng"], "lat": c["lat"], "zoom": CITY_ZOOM}
             for k, c in map_shell.CENTERS.items()}


def _chip_rows(g):
    """Every shelf with enough placed points to be worth a chip, per province.

    A chip that lights up eleven dots across two provinces is a chip that
    makes the map look broken, so the floor is the same eight the shelf maps
    use. The count shown is the number of points the chip will actually add,
    never the shelf's total — a chip promising 4,151 and drawing 4,148 is a
    small lie that a reader can see.
    """
    CATS, CAT_ORDER = g["CATS"], g["CAT_ORDER"]
    by_cat = g["_EXPLORE_COUNTS"]
    rows = []
    for p in g["PROVINCES"]:
        pk = p["key"]
        items = []
        for c in CAT_ORDER:
            n = by_cat.get((pk, c), 0)
            if n < 8:
                continue
            items.append({"key": "%s-%s" % (pk, c), "prov": pk, "cat": c,
                          "th": CATS[c]["th"], "en": CATS[c]["en"], "n": n})
        if items:
            rows.append({"prov": pk, "th": p["th"], "en": p["en"], "items": items})
    return rows


def build_page(g):
    bi, bi_text, att, esc = g["bi"], g["bi_text"], g["att"], g["esc"]
    page, share_block, BASE = g["page"], g["share_block"], g["BASE"]
    map_shell = g["map_shell"]
    rows = _chip_rows(g)

    lede_th = "เปิดแผนที่ เลือกชั้นที่อยากดู แตะจุดไหนก็ได้เพื่อดูว่าเป็นที่ไหน"
    lede_en = ("Open the map, switch on the shelves you want, and touch any dot to "
               "see what it is.")

    chips = []
    for row in rows:
        chips.append('<div class="xprov"><h2 class="xprovh">%s</h2><div class="xchips">'
                     % bi(row["th"], row["en"]))
        for it in row["items"]:
            chips.append(
                '<button type="button" class="xchip" data-x="%s" data-total="%d" aria-pressed="false">'
                '<span class="xswatch" aria-hidden="true"></span>%s'
                '<span class="count">%s</span></button>'
                % (att(it["key"]), it["n"], bi(it["th"], it["en"]), "{:,}".format(it["n"])))
        chips.append('</div></div>')

    # The directory, under the map, as plain links. This is the fallback and
    # it is not a lesser one: it is the same list the front page offers, and
    # on a page that could otherwise be a blank rectangle to a reader with no
    # scripting it is the whole point.
    lists = []
    for row in rows:
        lists.append('<div class="xlist"><h3>%s</h3><ul>' % bi(row["th"], row["en"]))
        for it in row["items"]:
            lists.append('<li><a href="%s/%s/">%s <span class="count">%s</span></a></li>'
                         % (it["prov"], it["cat"], bi(it["th"], it["en"]),
                            "{:,}".format(it["n"])))
        lists.append('</ul></div>')

    # The drawn fallback inside the map box: the moat, so the box is never an
    # empty rectangle, and a line of words saying what this is. Deliberately
    # small — with tiles under it this is covered within the second, and with
    # no tiles it is what the reader keeps.
    moat = g["MOAT_POLY"]
    fallback = ['<svg viewBox="0 0 720 420" width="100%%" class="xdraw" role="img" '
                'aria-label="%s">' % att(bi_text(
                    "แผนที่เมืองเชียงใหม่และเชียงราย — เลือกชั้นที่อยากดูได้",
                    "A map of Chiang Mai and Chiang Rai — switch on the shelves you want")),
                '<rect class="mdmap-bg" width="720" height="420" fill="#FBF6EE"/>']
    if moat:
        lat = [p[0] for p in moat]
        lng = [p[1] for p in moat]
        s_, n_ = min(lat), max(lat)
        w_, e_ = min(lng), max(lng)
        pad = max(n_ - s_, e_ - w_) * 1.8
        s_, n_, w_, e_ = s_ - pad, n_ + pad, w_ - pad, e_ + pad
        pts = " ".join("%.1f,%.1f" % ((p[1] - w_) / (e_ - w_) * 720,
                                      (n_ - p[0]) / (n_ - s_) * 420) for p in moat)
        fallback.append('<polygon class="mdmap-bg" points="%s" fill="none" '
                        'stroke="#6E8CA0" stroke-width="2" stroke-dasharray="5 4"/>' % pts)
    fallback.append('</svg>')

    box = map_shell.mount("xmap", "".join(fallback), prov="cm", zoom=CITY_ZOOM,
                          cls="mdmap xmap", full=True)
    # The crosshair the ring is centred on: an overlay, drawn only while a
    # ring is on, and never a pin — it marks the middle of what you can see.
    box = box.replace('</div></div>', '</div><div class="xcross" id="xcross" hidden aria-hidden="true"></div></div>', 1)

    import mapfirst_layer
    body = (
        f'<h1>{bi("แผนที่เมือง", "The city map")}</h1>'
        f'{mapfirst_layer.search_html(bi, att, bi_text)}'
        # The map first, the controls under it, the shelves under those, the
        # words last: on a phone the map is on screen before anything has to
        # be read past.
        f'{box}'
        # WO-77 (Nan, 2026-09-08): glyphs, not emoji; the ring; what is on.
        f'<div class="xbar">'
        f'<button type="button" id="xhere" class="xbtn" title="{att(bi_text("ใกล้ฉัน", "near me"))}">'
        f'{glyphs.icon("i-here", 20)}{bi("ใกล้ฉัน", "Near me")}</button>'
        f'<button type="button" id="xopen" class="xbtn" aria-pressed="false" title="{att(bi_text("เปิดอยู่ตอนนี้", "open now"))}">'
        f'{glyphs.icon("i-lamp", 20)}{bi("เปิดอยู่", "Open now")}</button>'
        f'<button type="button" id="xev" class="xbtn" aria-pressed="false" title="{att(bi_text("งานในเมือง", "what is on"))}">'
        f'{glyphs.icon("i-cal", 20)}{bi("งาน", "What is on")}</button>'
        f'<label class="xbtn xring" title="{att(bi_text("ในระยะ", "within"))}">{glyphs.icon("i-ring", 20)}'
        f'<select id="xring" aria-label="{att(bi_text("ในระยะ", "within"))}">'
        f'<option value="">{att(bi_text("ในระยะ", "within"))}</option>'
        + "".join(f'<option value="{m}">{att(bi_text(th, en))}</option>' for m, th, en in RING_M)
        + '</select></label>'
        f'<button type="button" id="xshot" class="xbtn" hidden title="{att(bi_text("ส่งภาพนี้", "send this view"))}">'
        f'{glyphs.icon("i-camera", 20)}{bi("ส่งภาพ", "Send")}</button>'
        + mapfirst_layer.bar_html(bi, att, bi_text) +
        f'<button type="button" id="xclear" class="xbtn">'
        f'{glyphs.icon("i-x", 18)}{bi("ล้าง", "Clear")}</button>'
        f'<span id="xcount" class="xcount" role="status"></span>'
        f'<a id="xlist" class="xlist" hidden></a>'
        f'</div>'
        f'<p id="xhint" class="xhint">{bi("แตะจุดบนแผนที่เพื่อดูว่าเป็นที่ไหน", "Touch a dot to see what it is")}</p>'
        f'<div class="xpick">'
        f'<h2 class="xpickh">{bi("เลือกชั้นที่อยากเห็น", "Switch on a shelf")}'
        f' <span class="quiet">{bi("ครั้งละ ๖ ชั้น", "up to six at once")}</span></h2>'
        f'{"".join(chips)}'
        f'</div>'
        f'<p class="lede">{bi(lede_th, lede_en)}</p>'
        f'<div class="xdir">'
        f'<h2>{bi("หรือเดินดูตามสารบัญ", "Or walk the directory")}</h2>'
        f'<p class="quiet">{bi("ทุกชั้นบนแผนที่มีหน้ารายชื่อของตัวเอง — แผนที่ไม่ใช่ทางเดียวที่จะไปถึงข้อมูล", "Every shelf on the map has a list of its own. The map is not the only way to the information.")}</p>'
        f'{"".join(lists)}'
        f'</div>'
        f'{share_block(BASE + "map.html", bi_text("แผนที่เมืองเชียงใหม่ · เชียงราย", "The Chiang Mai and Chiang Rai city map"))}')

    # hub=True: this is a doorstep now, in the same sense the front page and
    # my.html are — somewhere a reader arrives rather than somewhere they land
    # from a search — so it keeps the full navigation.
    v = version()
    return page("แผนที่เมือง", body, depth=0, path="map.html", hub=True,
                desc=lede_th,
                extra_head=f'<link rel="stylesheet" href="explore.css">'
                           f'<script src="coords.js" defer></script>'
                           f'<script src="explore.js" defer></script>'
                           f'<script src="mapfirst.js" defer></script>')


CSS = """/* /map.html — the explore map. */
.xpin{width:26px;height:26px;border-radius:50%;padding:0;cursor:pointer;
  background:var(--hot,#e0322b);border:4px solid #FFFCF6;
  box-shadow:0 0 0 2px var(--ink,#17110c),0 0 0 9px rgba(224,50,43,.28)}
@media (prefers-reduced-motion:no-preference){.xpin{animation:xpinpulse 2.4s ease-out 3}}
@keyframes xpinpulse{0%{box-shadow:0 0 0 2px var(--ink,#17110c),0 0 0 0 rgba(224,50,43,.55)}
  100%{box-shadow:0 0 0 2px var(--ink,#17110c),0 0 0 22px rgba(224,50,43,0)}}
.xmap{height:min(62vh,560px);margin:.5rem 0 .3rem}
@media (min-width:760px){.xmap{height:min(68vh,680px)}}
.xmap .mdmap-draw{height:100%}
.xmap .xdraw{height:100%;object-fit:cover}
.xbar{display:flex;gap:.5rem;align-items:center;flex-wrap:wrap;margin:.6rem 0 .2rem}
.xbtn{min-height:44px;padding:.4rem .9rem;border-radius:.6rem;font:inherit;
  font-weight:700;border:2px solid var(--ant);background:#fff;color:var(--ant-dark);
  cursor:pointer}
.xbtn:hover{background:var(--row-hover)}
.xbtn[aria-busy="true"]{opacity:.6}
.xcount{color:var(--ink-soft);font-size:.9rem}
.xhint{color:var(--gloss);font-size:.88rem;margin:.1rem 0 .8rem}
.xpick{margin:.6rem 0 1.2rem}
.xpickh{font-size:1.05rem;margin:.2rem 0 .5rem}
.xprovh{font-size:.92rem;margin:.6rem 0 .3rem;color:var(--ink-soft);font-weight:700}
.xchips{display:flex;flex-wrap:wrap;gap:.4rem}
/* A chip is a fingertip tall, and carries the ink its dots will be drawn in
   once it is on — so the map and the chip row are one legend. */
.xchip{display:inline-flex;align-items:center;gap:.4rem;min-height:44px;
  padding:.35rem .8rem;border-radius:999px;border:1.5px solid var(--warm-border);
  background:#fff;font:inherit;cursor:pointer;color:var(--ink)}
.xchip:hover{border-color:var(--ant)}
.xchip .count{color:var(--gloss);font-size:.82rem}
.xswatch{width:12px;height:12px;border-radius:50%;flex:none;
  background:var(--warm-border);border:1px solid var(--dashed)}
.xchip[aria-pressed="true"]{border-color:var(--ink);border-width:2px;
  background:var(--card-alt);font-weight:700}
.xchip[aria-pressed="true"] .xswatch{border-color:rgba(0,0,0,.35)}
.xchip[disabled]{opacity:.45;cursor:default}
.xdir{margin-top:1.4rem;border-top:2px solid var(--warm-border);padding-top:.8rem}
.xlist{margin:.5rem 0}
.xlist h3{font-size:.95rem;margin:.4rem 0 .2rem;color:var(--ink-soft)}
.xlist ul{list-style:none;padding:0;margin:0;display:flex;flex-wrap:wrap;gap:.2rem .9rem}
.xlist li{font-size:.95rem}
/* With scripting the chips ARE the picker, so the plain list below is the
   directory rather than a duplicate control. Without scripting nothing is
   hidden and the list is the only way through — which is the point. */
.xbtn .rowicon{margin-right:.35rem;vertical-align:-.2em;color:var(--ant-dark)}
.xbtn[aria-pressed="true"]{background:var(--card-alt);border-color:var(--ink)}
.xring{display:inline-flex;align-items:center;gap:.2rem;padding-right:.5rem}
.xring select{font:inherit;border:0;background:transparent;color:var(--ant-dark);
  font-weight:700;min-height:40px;max-width:9rem}
.xlist{font-size:.9rem;color:var(--ant-dark)}
.xlist[hidden]{display:none}
/* the crosshair: centre of the view, only while a ring is on */
.xcross{position:absolute;left:50%;top:50%;width:22px;height:22px;margin:-11px 0 0 -11px;
  pointer-events:none;z-index:3}
.xcross::before,.xcross::after{content:"";position:absolute;background:var(--ink);opacity:.8}
.xcross::before{left:10px;top:0;width:2px;height:22px}
.xcross::after{top:10px;left:0;height:2px;width:22px}
.xcross[hidden]{display:none}
.xmap{position:relative}
@media print{.xbar,.xpick{display:none}}
"""

JS = r"""/* explore.js — /map.html only.

   The map draws into the basemap rather than over it (see explore_layer.py for
   why this one page is allowed to). Everything it paints comes from the
   per-shelf GeoJSON files build.py already writes, fetched only when a reader
   asks for that shelf — nothing here pulls down a shelf nobody switched on. */
(function(){
var el=document.getElementById('xmap');
/* No basemap — the archive is unreachable, or this browser could not have it.
   The page still works: the shelf list below is the whole directory and it is
   plain links. What must NOT happen is chips sitting there looking like
   buttons and doing nothing when touched, so they are turned off and told
   why, and the reader is pointed at the list that does work. Silence here
   would read as a broken page rather than a page in its other mode. */
if(!el||!window.MDMAP){
  var picker=document.querySelector('.xpick');
  if(picker){
    picker.querySelectorAll('.xchip').forEach(function(b){
      b.disabled=true;b.setAttribute('aria-disabled','true');});
    var say=document.createElement('p');
    say.className='quiet';
    say.textContent='ตอนนี้ยังเปิดแผนที่ไม่ได้ — เลื่อนลงไปดูรายชื่อตามหมวดได้เลย · '+
      'The map cannot open just now. The shelves below are the same places, as a list.';
    picker.insertBefore(say,picker.firstChild.nextSibling);
  }
  ['xhere','xopen','xshot','xclear'].forEach(function(id){
    var b=document.getElementById(id);if(b)b.hidden=true;});
  return;
}

var INKS=%INKS%,MAX_ON=%MAXON%,DEFAULT_ON=%DEFON%,CITY=%CITY%;
/* MDVIEW (WO-74 L0): the view beyond zoom/centre/shelves — a tag, a ring,
   the events door — lives in the hash's fifth part as k=v&k=v, so a view
   with a ring on it is still one link. Absent parts mean off. */
var view={tag:'',r:0,ev:false,pin:''};
var gjs={};              /* key -> the GeoJSON kept, for counting in view */
var chips=[].slice.call(document.querySelectorAll('.xchip'));
var elCount=document.getElementById('xcount');
var on=[];               /* keys, in the order switched on — ink follows order */
var loaded={};           /* key -> true once its source is added */
var busy={};

function root(){return document.documentElement.getAttribute('data-root')||'';}
function inkFor(k){var i=on.indexOf(k);return i<0?null:INKS[i%INKS.length][0];}

/* ---- the address bar IS the view -------------------------------------
   #zoom/lat/lng/shelf,shelf. Written with replaceState so panning does not
   fill the reader's back button with a thousand entries, and read on load so
   a link somebody was sent opens on what they were shown. */
function viewParams(){
  var q=[];
  if(view.tag)q.push('tag='+encodeURIComponent(view.tag));
  if(view.r)q.push('r='+view.r);
  if(view.ev)q.push('ev=1');
  if(view.pin)q.push('pin='+encodeURIComponent(view.pin));
  /* mapfirst.js adds its own (dropped pins, the search) through this. */
  if(window.MDX_EXTRA){var ex=window.MDX_EXTRA();if(ex)q.push(ex);}
  return q.join('&');
}
function writeHash(map){
  if(!map)return;
  var c=map.getCenter(),vp=viewParams();
  var h='#'+map.getZoom().toFixed(2)+'/'+c.lat.toFixed(5)+'/'+c.lng.toFixed(5)+
        '/'+on.join(',')+(vp?'/'+vp:'');
  if(!on.length&&!vp)h=h.replace(/\/$/,'');
  try{history.replaceState(null,'',h);}catch(e){}
}
function readHash(){
  var h=(location.hash||'').replace(/^#/,'');
  if(!h)return null;
  var p=h.split('/');
  var z=parseFloat(p[0]),la=parseFloat(p[1]),ln=parseFloat(p[2]);
  if(!isFinite(z)||!isFinite(la)||!isFinite(ln))return null;
  var out={zoom:z,lat:la,lng:ln,on:(p[3]||'').split(',').filter(Boolean),tag:'',r:0,ev:false,pin:''};
  (p[4]||'').split('&').forEach(function(kv){
    var i=kv.indexOf('=');if(i<0)return;
    var k=kv.slice(0,i),v=decodeURIComponent(kv.slice(i+1));
    if(k==='tag')out.tag=v;
    else if(k==='r'){var r=parseInt(v,10);if(r>0&&r<=50000)out.r=r;}
    else if(k==='ev')out.ev=v==='1';
    else if(k==='pin'&&/^c[mr]:[a-z0-9-]+$/.test(v))out.pin=v;});
  return out;
}
/* Does a feature pass the view's own filters — the tag, and the ring? */
function tagOk(f){
  if(!view.tag)return true;
  var t=f.properties&&f.properties.t;
  return !!(t&&t.indexOf(view.tag)>-1);
}
function metres(a,b,c,d){
  var R=6371000,x=(c-a)*Math.PI/180,y=(d-b)*Math.PI/180;
  var h=Math.sin(x/2)*Math.sin(x/2)+Math.cos(a*Math.PI/180)*Math.cos(c*Math.PI/180)*Math.sin(y/2)*Math.sin(y/2);
  return 2*R*Math.asin(Math.sqrt(h));
}
function fmtM(m){return m<950?m+' ม. · m':(m/1000)+' กม. · km';}

function paintChips(){
  chips.forEach(function(b){
    var k=b.dataset.x,ink=inkFor(k);
    b.setAttribute('aria-pressed',ink?'true':'false');
    b.querySelector('.xswatch').style.background=ink||'';
    b.disabled=!ink&&on.length>=MAX_ON;
  });
  if(elCount){
    elCount.textContent=on.length?
      (on.length+'/'+MAX_ON+' ชั้น · shelves'):'';
  }
}
/* THE CHIPS COUNT WHAT IS ON SCREEN (WO-74 L3). A chip for a shelf that is
   loaded says how many of its dots are inside the view — and inside the
   ring, and carrying the tag — over the shelf's total. A shelf not yet
   loaded keeps its total: we have not fetched it, and a number we have not
   counted is not printed. Re-counted on every move, from the GeoJSON kept
   in memory, never from the tiles. */
function countInView(map){
  var b=map.getBounds(),c=map.getCenter(),seen=0;
  chips.forEach(function(ch){
    var k=ch.dataset.x,gj=gjs[k],el=ch.querySelector('.count'),tot=ch.dataset.total||'';
    if(!gj||on.indexOf(k)<0){el.textContent=Number(tot).toLocaleString();return;}
    var n=0;
    gj.features.forEach(function(f){
      var x=f.geometry.coordinates;
      if(x[0]<b.getWest()||x[0]>b.getEast()||x[1]<b.getSouth()||x[1]>b.getNorth())return;
      if(!tagOk(f))return;
      if(view.r&&metres(c.lat,c.lng,x[1],x[0])>view.r)return;
      n++;});
    seen+=n;
    el.textContent=n.toLocaleString()+' / '+Number(tot).toLocaleString();
  });
  return seen;
}

/* No view in the link: the box is built on the remembered city rather than
   on Chiang Mai and moved after. map.js reads data-lat/lng/zoom when it
   builds, and it builds from the observer, the scroll sweep or a zero timer —
   all after this script has run — so the map opens on the city, fetches that
   city's tiles only, and the camera it starts on is the one ◎ hands back. */
if(!readHash()){
  var c0=null;try{c0=localStorage.getItem('md-city');}catch(e){}
  var v0=c0&&Object.prototype.hasOwnProperty.call(CITY,c0)&&CITY[c0];
  if(v0){el.dataset.lat=v0.lat;el.dataset.lng=v0.lng;el.dataset.zoom=v0.zoom;}
}

MDMAP.ready(el,function(map){
  /* Where a reader was sent, or the whole of Chiang Mai. */
  var want=readHash();
  if(want){
    map.jumpTo({center:[want.lng,want.lat],zoom:want.zoom});
    on=want.on.slice(0,MAX_ON);
    view.tag=want.tag;view.r=want.r;view.ev=want.ev;view.pin=want.pin;
  }else{
    on=DEFAULT_ON.slice(0,MAX_ON);
    /* No view in the link: the city the front page remembers (md-city, the
       province key), on its landmark at the city zoom. No memory, no move.
       The box is normally built on it already (above); this is for a box
       built before this script ran. */
    var city=null;try{city=localStorage.getItem('md-city');}catch(e){}
    var cv=city&&Object.prototype.hasOwnProperty.call(CITY,city)&&CITY[city];
    if(cv)map.jumpTo({center:[cv.lng,cv.lat],zoom:cv.zoom});
  }

  function srcId(k){return 'x-'+k;}

  /* The view's filter as a MapLibre expression: the tag, then the ring.
     The ring uses the engine's own distance so what is drawn and what is
     counted cannot disagree. */
  function filterExpr(){
    var parts=['all'];
    if(view.tag)parts.push(['in',view.tag,['coalesce',['get','t'],['literal',[]]]]);
    if(view.r){var c=map.getCenter();
      parts.push(['<=',['distance',{type:'Point',coordinates:[c.lng,c.lat]}],view.r]);}
    return parts.length>1?parts:null;
  }
  function refilter(){
    var fx=filterExpr();
    Object.keys(loaded).forEach(function(k){
      ['-halo','-dot','-stack','-name'].forEach(function(sfx){
        var id=srcId(k)+sfx;if(!map.getLayer(id))return;
        var base=(sfx==='-stack')?['>',['coalesce',['get','k'],1],1]:null;
        var f=fx?(base?['all',base,fx]:fx):base;
        map.setFilter(id,f||null);});});
  }

  var FONT=['NotoSans'];
  ((window.MDMAP_CFG&&MDMAP_CFG.layers)||[]).some(function(l){
    if(l.type==='symbol'&&l.layout&&l.layout['text-font']){FONT=l.layout['text-font'];return true;}});
  var RANK=['to-number',['get','rank'],0];
  var NAME=['case',['all',['to-boolean',['get','nameTh']],['to-boolean',['get','nameEn']]],
    ['concat',['get','nameTh'],'\n',['get','nameEn']],
    ['coalesce',['get','nameTh'],['get','nameEn'],['get','name'],'']];
  function rk(n){return ['case',['>=',RANK,n],NAME,''];}

  function addLayer(k,gj){
    var id=srcId(k);
    if(map.getSource(id))return;
    map.addSource(id,{type:'geojson',data:gj});
    /* A halo under the dot, for the same reason every pin on this site wears
       one: the ground has real ink in it now. */
    map.addLayer({id:id+'-halo',type:'circle',source:id,paint:{
      'circle-radius':['interpolate',['linear'],['zoom'],10,3.2,14,5.4,17,8],
      'circle-color':'#FFFCF6','circle-opacity':.85}});
    map.addLayer({id:id+'-dot',type:'circle',source:id,paint:{
      'circle-radius':['interpolate',['linear'],['zoom'],10,2,14,3.6,17,5.6],
      'circle-color':inkFor(k)||'#C2401C','circle-opacity':.95}});
    /* STACKS CONFESS (WO-74 L2): a pin that several rows share wears a
       hollow ring sized by how many stand on it, so a mall drawn as one dot
       is not mistaken for one shop. Only rows with k>1 — the GeoJSON writes
       `k` on those alone. */
    map.addLayer({id:id+'-stack',type:'circle',source:id,
      filter:['>',['coalesce',['get','k'],1],1],paint:{
        'circle-radius':['interpolate',['linear'],['get','k'],2,7,10,11,50,16],
        'circle-color':'rgba(0,0,0,0)',
        'circle-stroke-color':inkFor(k)||'#C2401C','circle-stroke-width':1.6,
        'circle-stroke-opacity':.7}},id+'-halo');
    /* NAMES BY ZOOM (Michael, 2026-09-29): the most-ranked names first, more
       with every step in, all of them from 17. Saved places are named from
       the widest view (mine_layer.py) and win every collision. */
    if(window.MDMAP_CFG&&MDMAP_CFG.glyphs)map.addLayer({id:id+'-name',type:'symbol',source:id,
      layout:{'text-field':['step',['zoom'],rk(5),14,rk(4),15,rk(3),16,rk(2),17,NAME],
        'text-font':FONT,'text-size':12.5,'text-max-width':8,
        'text-variable-anchor':['left','right','top','bottom'],'text-radial-offset':.7,
        'text-justify':'auto','symbol-sort-key':['-',0,RANK]},
      paint:{'text-color':inkFor(k)||'#C2401C','text-halo-color':'#FFFCF6','text-halo-width':1.8}});
    loaded[k]=true;gjs[k]=gj;
    refilter();
  }

  function recolour(){
    Object.keys(loaded).forEach(function(k){
      var ink=inkFor(k);
      if(!ink)return;
      if(map.getLayer(srcId(k)+'-dot'))
        map.setPaintProperty(srcId(k)+'-dot','circle-color',ink);
      if(map.getLayer(srcId(k)+'-stack'))
        map.setPaintProperty(srcId(k)+'-stack','circle-stroke-color',ink);
      if(map.getLayer(srcId(k)+'-name'))
        map.setPaintProperty(srcId(k)+'-name','text-color',ink);
    });
  }

  function show(k,yes){
    /* '-open' belongs in this list: a shelf switched off and on again while
       the open-now rings are lit would otherwise come back without them,
       because only its dots were ever hidden. */
    ['-halo','-dot','-open','-stack','-name'].forEach(function(sfx){
      if(map.getLayer(srcId(k)+sfx))
        map.setLayoutProperty(srcId(k)+sfx,'visibility',yes?'visible':'none');
    });
  }

  function load(k,then){
    if(loaded[k]){show(k,true);recolour();if(then)then();return;}
    if(busy[k])return;
    busy[k]=true;
    var b=document.querySelector('.xchip[data-x="'+k+'"]');
    if(b)b.setAttribute('aria-busy','true');
    fetch(root()+'data/'+k+'.geojson').then(function(r){
      if(!r.ok)throw new Error(r.status);return r.json();})
      .then(function(gj){addLayer(k,gj);recolour();
        /* A shelf switched on while "open now" is already lit gets its rings
           straight away, rather than only after the next tap of the button. */
        if(openOn){openLayerFor(k);markOpen();}
        if(then)then();})
      .catch(function(){
        /* A shelf that will not load is taken back off rather than left as a
           chip that claims to be showing something. */
        var i=on.indexOf(k);if(i>-1)on.splice(i,1);
        paintChips();
        if(elCount)elCount.textContent='ชั้นนี้โหลดไม่ได้ · that shelf did not load';
      })
      .then(function(){busy[k]=false;if(b)b.removeAttribute('aria-busy');});
  }

  /* ---- a dot answers ---------------------------------------------------
     Same card as every other map on this site, so what a touch is worth does
     not change from page to page. */
  /* A pin as the card reads it. The GeoJSON carries only name, shelf and
     rank; `json` points the card at the place's own record, which it fetches
     on the touch for the phone, the website, the address and a photo
     (Nan's friend, 2026-09-28: "a lot of dots but no previews"). */
  function pinItem(ft){
    var pr=ft.properties||{},xy=ft.geometry.coordinates;
    var k=parseInt(pr.k||'1',10)||1;
    return {
      name:[pr.nameTh,pr.nameEn].filter(Boolean).join(' · ')||pr.name||'',
      sub:(pr.province==='cr'?'เชียงราย · Chiang Rai':'เชียงใหม่ · Chiang Mai'),
      href:root()+pr.province+'/p/'+pr.slug+'.html',
      json:root()+pr.province+'/p/'+pr.slug+'.json',
      plan:pr.province+':'+pr.slug,
      rank:(pr.rank&&pr.rank!=='0'&&pr.rank!==0)?pr.rank:'',
      lat:xy[1],lng:xy[0],
      /* the stack's confession, and the list of what shares this pin */
      more:k>1?('+'+(k-1)+' ที่หมุดเดียวกัน · '+(k-1)+' more at this pin'):'',
      moreHref:k>1?(root()+'search.html?near='+xy[1].toFixed(5)+','+xy[0].toFixed(5)+'&radius=0.03&sort=full'):''};
  }
  /* The three nearest among the shelves switched on, so the card can walk. */
  function pinsNear(it){
    if(it.lat==null)return null;
    var out=[],cos=Math.cos(it.lat*Math.PI/180);
    on.forEach(function(k){
      var gj=gjs[k];if(!gj||!gj.features)return;
      gj.features.forEach(function(ft){
        var c=ft.geometry&&ft.geometry.coordinates;if(!c)return;
        var dy=(c[1]-it.lat)*111320,dx=(c[0]-it.lng)*111320*cos;
        var m=Math.sqrt(dx*dx+dy*dy);
        if(m>3000||(ft.properties||{}).slug&&it.plan===(ft.properties.province+':'+ft.properties.slug))return;
        out.push([m,ft]);});});
    out.sort(function(a,b){return a[0]-b[0];});
    return out.slice(0,3).map(function(p){return [p[0],pinItem(p[1])];});
  }
  /* Map-first (Michael, 2026-09-28): on this page a place opens in the sheet
     mapfirst.js draws over the map; the card is the fallback. */
  function openItem(it){
    if(window.MDMAPSHEET)return window.MDMAPSHEET.show(it,{near:pinsNear});
    if(window.MDSENSE)MDSENSE.tell('open',{k:it.plan,lat:it.lat,lng:it.lng,z:map.getZoom()});
    if(window.MDCARD)window.MDCARD.show(it,el,{surface:{near:pinsNear}});
  }
  window.MDX={map:map,el:el,openItem:openItem,pinsNear:pinsNear,pinItem:pinItem,
    writeHash:function(){writeHash(map);},root:root};
  try{document.dispatchEvent(new Event('mdx-ready'));}catch(e){}
  /* window.MDCARD, never the bare name: md.js declares `const MDCARD` at the
     top level, and that binding shadows the window property tap.js replaces,
     so a bare MDCARD here opened the fallback card with a name and nothing
     else under it. */
  function wireTap(){
    map.on('click',function(e){
      var ids=[];
      on.forEach(function(k){
        if(map.getLayer(srcId(k)+'-dot'))ids.push(srcId(k)+'-dot');});
      if(view.ev&&map.getLayer('x-ev-dot'))ids.push('x-ev-dot');
      if(!ids.length)return;
      /* a saved place under the finger answers for itself (mine_layer.py) */
      if(window.MDMINE&&MDMINE.hit(map,e.point))return;
      /* A fingertip, not a pixel: query a box around the touch and take the
         nearest, so a near miss still names the thing that was aimed at. */
      var R=22,pt=e.point;
      var f=map.queryRenderedFeatures(
        [[pt.x-R,pt.y-R],[pt.x+R,pt.y+R]],{layers:ids});
      if(!f.length)return;
      var best=f[0],bd=Infinity;
      f.forEach(function(ft){
        var p=map.project(ft.geometry.coordinates);
        var d=(p.x-pt.x)*(p.x-pt.x)+(p.y-pt.y)*(p.y-pt.y);
        if(d<bd){bd=d;best=ft;}});
      var pr=best.properties||{};
      if(pr.title!==undefined&&pr.slug===undefined){
        /* an event: the venue and when; its page is its row in the front
           page's calendar (front.js reads #ev=, the title slugged as
           front_layer._slug does) */
        var evk=String(pr.title||'').toLowerCase().replace(/[^a-z0-9]+/g,'-').replace(/^-+|-+$/g,'').slice(0,80)||'x';
        if(window.MDCARD)window.MDCARD.show({name:pr.title||'',
          sub:[pr.venue,String(pr.start||'').slice(0,16)].filter(Boolean).join(' · '),
          href:root()+'./#ev='+evk},el);
        return;}
      openItem(pinItem(best));
    });
    map.on('mousemove',function(e){
      var ids=[];
      on.forEach(function(k){
        if(map.getLayer(srcId(k)+'-dot'))ids.push(srcId(k)+'-dot');});
      if(!ids.length)return;
      var f=ids.length?map.queryRenderedFeatures(e.point,{layers:ids}):[];
      map.getCanvas().style.cursor=f.length?'pointer':'';
    });
  }

  chips.forEach(function(b){
    b.addEventListener('click',function(){
      var k=b.dataset.x,i=on.indexOf(k);
      if(i>-1){on.splice(i,1);show(k,false);}
      else{
        if(on.length>=MAX_ON)return;
        on.push(k);load(k);
      }
      paintChips();recolour();sayCount();writeHash(map);
    });
  });

  document.getElementById('xclear').addEventListener('click',function(){
    on.slice().forEach(function(k){show(k,false);});
    on=[];view.tag='';paintChips();sayCount();writeHash(map);
  });

  /* Near me goes through the one door on this site that may ask. */
  var here=document.getElementById('xhere');
  here.addEventListener('click',function(){
    if(!window.MDLOC)return;
    here.setAttribute('aria-busy','true');
    MDLOC.ask(function(pt){
      here.removeAttribute('aria-busy');
      map.flyTo({center:[pt.lng,pt.lat],zoom:15,
        duration:matchMedia('(prefers-reduced-motion:reduce)').matches?0:900});
    },function(){
      here.removeAttribute('aria-busy');
      if(elCount)elCount.textContent='ยังไม่ได้บอกตำแหน่ง · no position given';
    });
  });

  /* ---- what is open, right now -----------------------------------------
     THE RULE THIS IS BUILT ON, and it is not a detail: a place with no
     opening hours on record is NOT closed. Most places here have never told
     anybody their hours, and a map that dimmed them would be publishing a
     claim about several thousand businesses that nobody made. So this
     EMPHASISES what we know is open and touches nothing else — no dot is
     ever hidden or dimmed by it — and the counter says how many places that
     is, so the reader can see for themselves how partial the knowledge is.

     The schedules are the same file the lamp map reads: intervals in minutes
     from Monday midnight, so "now" is one sum in the reader's own clock and
     no request to anybody. */
  var openBtn=document.getElementById('xopen'),openIds=null,openOn=false;
  function weekMinute(){
    var d=new Date();
    return ((d.getDay()+6)%7)*1440+d.getHours()*60+d.getMinutes();
  }
  function markOpen(){
    Object.keys(loaded).forEach(function(k){
      var id=srcId(k)+'-open';
      if(!map.getLayer(id))return;
      map.setFilter(id,(openOn&&openIds&&openIds.length)
        ?['in',['get','id'],['literal',openIds]]:['==',['literal',0],1]);
    });
  }
  function openLayerFor(k){
    var id=srcId(k);
    if(map.getLayer(id+'-open'))return;
    /* A ring around the dot rather than a different colour: the colour is
       already saying which shelf this is, and a mark may only carry one
       meaning at a time. Added under the dot so the dot stays on top. */
    map.addLayer({id:id+'-open',type:'circle',source:id,
      filter:['==',['literal',0],1],paint:{
        'circle-radius':['interpolate',['linear'],['zoom'],10,5.5,14,8.5,17,12],
        'circle-color':'rgba(0,0,0,0)',
        'circle-stroke-color':'#1F6B57','circle-stroke-width':2.2,
        'circle-stroke-opacity':.9}},id+'-dot');
  }
  function loadOpen(then){
    if(openIds)return then&&then();
    fetch(root()+'data/open_lamps.json').then(function(r){return r.json();})
      .then(function(d){
        var now=weekMinute(),ids=[];
        (d.places||[]).forEach(function(p){
          var s=(d.schedules||[])[p.k];
          if(!s)return;
          for(var i=0;i<s.length;i++){
            if(now>=s[i][0]&&now<s[i][1]){ids.push(p.id);break;}
          }
        });
        openIds=ids;
        if(then)then();
      }).catch(function(){openIds=[];if(then)then();});
  }
  if(openBtn)openBtn.addEventListener('click',function(){
    openOn=!openOn;
    openBtn.setAttribute('aria-pressed',openOn?'true':'false');
    if(!openOn){markOpen();if(elCount)elCount.textContent='';return;}
    openBtn.setAttribute('aria-busy','true');
    loadOpen(function(){
      openBtn.removeAttribute('aria-busy');
      Object.keys(loaded).forEach(openLayerFor);
      markOpen();
      if(elCount)elCount.textContent=openIds.length
        ? ('วงเขียว = รู้ว่าเปิดอยู่ '+openIds.length.toLocaleString()+
           ' แห่ง · green ring = known open; the rest have never said')
        : 'ยังไม่รู้เวลาเปิดของที่ไหนตอนนี้ · no hours on record for now';
    });
  });

  /* ---- send this view ---------------------------------------------------
     A link is the better thing to send and the page already makes one. But a
     link pasted into a LINE chat does not unfurl, and the picture is what
     people actually look at — the same reasoning that put a share card on
     every shelf. So this hands over the view itself: what is on screen, the
     shelves named along the bottom, and the ODbL credit drawn INTO the
     pixels, because a picture travels with no page around it.

     Offered only where the browser can actually pass a file to another app.
     A button that silently does nothing is worse than no button, so it is
     hidden until canShare says yes. */
  var shot=document.getElementById('xshot');
  function canShareFiles(){
    try{return !!(navigator.canShare&&navigator.canShare(
      {files:[new File([new Blob([1])],'a.png',{type:'image/png'})]}));}
    catch(e){return false;}
  }
  if(shot&&canShareFiles()){
    shot.hidden=false;
    shot.addEventListener('click',function(){
      shot.setAttribute('aria-busy','true');
      var src=map.getCanvas();
      var w=src.width,h=src.height,r=(window.devicePixelRatio||1);
      var band=Math.round(46*r);
      var c=document.createElement('canvas');
      c.width=w;c.height=h+band;
      var x=c.getContext('2d');
      x.fillStyle='#FBF6EC';x.fillRect(0,0,c.width,c.height);
      x.drawImage(src,0,0);
      /* The band under the picture: what these dots are, then who the map
         belongs to. Both are conditions of using this data, not decoration. */
      x.fillStyle='#FFFDF8';x.fillRect(0,h,w,band);
      x.fillStyle='#2A1E16';
      x.font='700 '+Math.round(15*r)+'px system-ui,sans-serif';
      var names=on.map(function(k){
        var b=document.querySelector('.xchip[data-x="'+k+'"]');
        return b?b.textContent.replace(/\s+/g,' ').replace(/[\d,]+$/,'').trim():k;});
      x.fillText(('มดแดง · motdang.net'+(names.length?' — '+names.join(', '):''))
        .slice(0,90),Math.round(10*r),h+Math.round(19*r));
      x.fillStyle='#6B5A48';
      x.font=Math.round(12*r)+'px system-ui,sans-serif';
      x.fillText('© OpenStreetMap contributors (ODbL)',Math.round(10*r),h+Math.round(37*r));
      c.toBlob(function(b){
        shot.removeAttribute('aria-busy');
        if(!b)return;
        var f=new File([b],'motdang-map.png',{type:'image/png'});
        navigator.share({files:[f],title:'มดแดง · Mot Dang',
          text:location.href}).catch(function(){});
      },'image/png');
    });
  }

  /* ---- the ring (WO-74 E2: the tool shows its own reach) ---------------
     A dashed circle of a chosen radius around the CENTRE OF THE VIEW — pan
     the map and the ring goes with the crosshair. What it filters it also
     counts, and the count is a link to the same answer as a list:
     search.html with near= and radius=, which is the list twin (L5) of
     exactly this view. */
  var ringSel=document.getElementById('xring'),cross=document.getElementById('xcross');
  var listA=document.getElementById('xlist');
  function ringPoly(c,r){
    var pts=[],n=72,lat=c.lat*Math.PI/180;
    for(var i=0;i<=n;i++){var a=i/n*2*Math.PI;
      var dy=r*Math.cos(a)/111320,dx=r*Math.sin(a)/(111320*Math.cos(lat));
      pts.push([c.lng+dx,c.lat+dy]);}
    return {type:'Feature',geometry:{type:'Polygon',coordinates:[pts]}};
  }
  function drawRing(){
    var id='x-ring';
    if(!view.r){if(map.getLayer(id))map.setLayoutProperty(id,'visibility','none');
      if(cross)cross.hidden=true;return;}
    var gj=ringPoly(map.getCenter(),view.r);
    if(!map.getSource(id)){
      map.addSource(id,{type:'geojson',data:gj});
      map.addLayer({id:id,type:'line',source:id,paint:{
        'line-color':'#2A1E16','line-width':1.6,'line-dasharray':[3,2.2],'line-opacity':.75}});
    }else{map.getSource(id).setData(gj);map.setLayoutProperty(id,'visibility','visible');}
    if(cross)cross.hidden=false;
  }
  function sayCount(){
    var n=countInView(map);
    if(!elCount)return;
    var c=map.getCenter(),bits=[];
    if(on.length)bits.push(n.toLocaleString()+(view.r?' ในระยะ '+fmtM(view.r):' ในมุมนี้ · in view'));
    if(view.tag)bits.push('ป้าย '+view.tag);
    elCount.textContent=bits.join(' · ');
    /* the list twin of this view: the same shelves, the same ring */
    if(listA){
      var cats=on.map(function(k){return k.replace(/^c[mr]-/,'');});
      var show=on.length&&view.r;
      listA.hidden=!show;
      if(show){
        listA.href=root()+'search.html?near='+c.lat.toFixed(5)+','+c.lng.toFixed(5)+
          '&radius='+(view.r/1000)+'&cat='+encodeURIComponent(cats.join(','))+
          (view.tag?'&tag='+encodeURIComponent(view.tag):'');
        listA.textContent='ดูเป็นรายการ · as a list';}}
  }
  if(ringSel){
    ringSel.value=view.r?String(view.r):'';
    ringSel.addEventListener('change',function(){
      view.r=parseInt(ringSel.value,10)||0;
      drawRing();refilter();sayCount();writeHash(map);});
  }

  /* ---- what is on (WO-77: the calendar door, on the map) ---------------
     The events GeoJSON build.py already writes, drawn in the day's gold as
     a seventh ink that is not a shelf. A tap names the event and its venue. */
  var evBtn=document.getElementById('xev');
  function loadEvents(then){
    var id='x-ev';
    if(map.getSource(id)){map.setLayoutProperty(id+'-dot','visibility','visible');
      if(map.getLayer(id+'-halo'))map.setLayoutProperty(id+'-halo','visibility','visible');
      return then&&then();}
    fetch(root()+'data/events.geojson').then(function(r){return r.json();}).then(function(gj){
      map.addSource(id,{type:'geojson',data:gj});
      map.addLayer({id:id+'-halo',type:'circle',source:id,paint:{
        'circle-radius':['interpolate',['linear'],['zoom'],10,5,14,8,17,11],
        'circle-color':'#FFFCF6','circle-opacity':.9}});
      map.addLayer({id:id+'-dot',type:'circle',source:id,paint:{
        'circle-radius':['interpolate',['linear'],['zoom'],10,3,14,5,17,7],
        'circle-color':'#B8912E','circle-stroke-color':'#2A1E16','circle-stroke-width':1}});
      gjs['ev']=gj;if(then)then();}).catch(function(){view.ev=false;paintEv();});
  }
  function paintEv(){if(evBtn)evBtn.setAttribute('aria-pressed',view.ev?'true':'false');}
  function showEv(){
    if(view.ev)loadEvents();
    else ['-dot','-halo'].forEach(function(s){if(map.getLayer('x-ev'+s))map.setLayoutProperty('x-ev'+s,'visibility','none');});
    paintEv();
  }
  if(evBtn)evBtn.addEventListener('click',function(){view.ev=!view.ev;showEv();writeHash(map);});

  /* the tap also answers on events: their layer joins the query list */
  var _origWireTap=wireTap;
  wireTap=function(){_origWireTap();};

  /* ---- the place a reader came from -----------------------------------
     Michael, 2026-09-28: "I like to see where everything is." A place page
     sends #16/lat/lng/<its shelf>/pin=cm:<slug>, so the map opens on the
     place, marked, with its shelf lit around it and its card open — and the
     card's nearest-three walks on from there. */
  var pinItemNow=null;
  function pinCard(){if(pinItemNow)openItem(pinItemNow);}
  function pinPlace(){
    if(!view.pin)return;
    var pk=view.pin.split(':'),prov=pk[0],slug=pk[1],c0=map.getCenter();
    var mk=document.createElement('button');
    mk.type='button';mk.className='xpin';
    mk.setAttribute('aria-label','ที่นี่ · this place');
    mk.addEventListener('click',function(e){e.stopPropagation();pinCard();});
    if(window.maplibregl&&maplibregl.Marker)
      new maplibregl.Marker({element:mk,anchor:'center'}).setLngLat([c0.lng,c0.lat]).addTo(map);
    var shelfReady=!on.length,rec=null;
    function go(){if(rec&&shelfReady)pinCard();}
    if(on.length)load(on[0],function(){shelfReady=true;sayCount();go();});
    setTimeout(function(){shelfReady=true;go();},2500);
    fetch(root()+prov+'/p/'+slug+'.json').then(function(r){return r.json();}).then(function(d){
      var lat=d.lat!=null?d.lat:c0.lat,lng=d.lng!=null?d.lng:c0.lng;
      pinItemNow={name:[d.nameTh,d.nameEn].filter(Boolean).join(' · ')||d.name||'',
        sub:(prov==='cr'?'เชียงราย · Chiang Rai':'เชียงใหม่ · Chiang Mai'),
        href:root()+prov+'/p/'+slug+'.html',json:root()+prov+'/p/'+slug+'.json',
        plan:prov+':'+slug,rank:d.antRank||'',lat:lat,lng:lng,more:'',moreHref:''};
      rec=d;go();}).catch(function(){});
  }

  map.on('moveend',function(){drawRing();refilter();sayCount();writeHash(map);});
  map.on('move',function(){if(view.r)drawRing();});
  wireTap();
  pinPlace();
  on.slice().forEach(function(k){load(k,sayCount);});
  paintChips();
  if(view.r)drawRing();
  if(view.ev)showEv();
  writeHash(map);
});
})();
"""


def emit(g):
    docs = g["DOCS"]
    (docs / "explore.css").write_text(CSS)
    (docs / "explore.js").write_text(_js())
    import mapfirst_layer, coords_layer
    mapfirst_layer.emit(docs)
    coords_layer.emit(docs)
    (docs / "map.html").write_text(build_page(g))
    rows = _chip_rows(g)
    return {"page": 1, "chips": sum(len(r["items"]) for r in rows),
            "provinces": len(rows)}


if __name__ == "__main__":
    print("This layer runs from build.py — it needs its helpers. "
          "Run: python3 build.py")
