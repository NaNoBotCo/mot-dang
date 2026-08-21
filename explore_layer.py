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
import zlib


def _js():
    """explore.js, exactly as it ships."""
    return (JS.replace("%INKS%", json.dumps(INKS, ensure_ascii=False))
              .replace("%MAXON%", str(MAX_ON))
              .replace("%DEFON%", json.dumps(DEFAULT_ON)))


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

    lede_th = ("เปิดแผนที่ เลือกชั้นที่อยากดู แตะจุดไหนก็ได้เพื่อดูว่าเป็นที่ไหน "
               "จะดูวัดกับร้านกาแฟพร้อมกันก็ได้ แล้วส่งลิงก์ให้เพื่อนได้เลย — "
               "มุมที่คุณเห็นอยู่คือลิงก์")
    lede_en = ("Open the map, switch on the shelves you want, and touch any dot to "
               "see what it is. Temples and coffee at the same time, if you like. "
               "The view you are looking at is a link — send it to somebody.")

    chips = []
    for row in rows:
        chips.append('<div class="xprov"><h2 class="xprovh">%s</h2><div class="xchips">'
                     % bi(row["th"], row["en"]))
        for it in row["items"]:
            chips.append(
                '<button type="button" class="xchip" data-x="%s" aria-pressed="false">'
                '<span class="xswatch" aria-hidden="true"></span>%s'
                '<span class="count">%s</span></button>'
                % (att(it["key"]), bi(it["th"], it["en"]), "{:,}".format(it["n"])))
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

    box = map_shell.mount("xmap", "".join(fallback), prov="cm", zoom=12.4,
                          cls="mdmap xmap", full=True)

    body = (
        f'<h1>{bi("แผนที่เมือง", "The city map")}</h1>'
        f'<p class="lede">{bi(lede_th, lede_en)}</p>'
        f'<div class="xbar">'
        f'<button type="button" id="xhere" class="xbtn">'
        f'{bi("📍 ใกล้ฉัน", "Near me")}</button>'
        f'<button type="button" id="xopen" class="xbtn" aria-pressed="false">'
        f'{bi("⏰ เปิดอยู่ตอนนี้", "Open now")}</button>'
        f'<button type="button" id="xshot" class="xbtn" hidden>'
        f'{bi("📷 ส่งภาพนี้", "Send this view")}</button>'
        f'<button type="button" id="xclear" class="xbtn">'
        f'{bi("ล้างที่เลือก", "Clear")}</button>'
        f'<span id="xcount" class="xcount" role="status"></span>'
        f'</div>'
        f'{box}'
        f'<p id="xhint" class="xhint">{bi("แตะจุดบนแผนที่เพื่อดูว่าเป็นที่ไหน", "Touch a dot to see what it is")}</p>'
        f'<div class="xpick">'
        f'<h2 class="xpickh">{bi("เลือกชั้นที่อยากเห็น", "Switch on a shelf")}'
        f' <span class="quiet">{bi("ครั้งละ ๖ ชั้น", "up to six at once")}</span></h2>'
        f'{"".join(chips)}'
        f'</div>'
        f'<div class="xdir">'
        f'<h2>{bi("หรือเดินดูตามสารบัญ", "Or walk the directory")}</h2>'
        f'<p class="quiet">{bi("ทุกชั้นบนแผนที่มีหน้ารายชื่อของตัวเอง — แผนที่ไม่ใช่ทางเดียวที่จะไปถึงข้อมูล", "Every shelf on the map has a list of its own. The map is never the only way to the information.")}</p>'
        f'{"".join(lists)}'
        f'</div>'
        f'{share_block(BASE + "map.html", bi_text("แผนที่เมืองเชียงใหม่ · เชียงราย", "The Chiang Mai and Chiang Rai city map"))}')

    # hub=True: this is a doorstep now, in the same sense the front page and
    # my.html are — somewhere a reader arrives rather than somewhere they land
    # from a search — so it keeps the full navigation.
    v = version()
    return page("แผนที่เมือง", body, depth=0, path="map.html", hub=True,
                desc=lede_th,
                extra_head=f'<link rel="stylesheet" href="explore.css?v={v}">'
                           f'<script src="explore.js?v={v}" defer></script>')


CSS = """/* /map.html — the explore map. */
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

var INKS=%INKS%,MAX_ON=%MAXON%,DEFAULT_ON=%DEFON%;
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
function writeHash(map){
  if(!map)return;
  var c=map.getCenter();
  var h='#'+map.getZoom().toFixed(2)+'/'+c.lat.toFixed(5)+'/'+c.lng.toFixed(5)+
        (on.length?'/'+on.join(','):'');
  try{history.replaceState(null,'',h);}catch(e){}
}
function readHash(){
  var h=(location.hash||'').replace(/^#/,'');
  if(!h)return null;
  var p=h.split('/');
  var z=parseFloat(p[0]),la=parseFloat(p[1]),ln=parseFloat(p[2]);
  if(!isFinite(z)||!isFinite(la)||!isFinite(ln))return null;
  return {zoom:z,lat:la,lng:ln,on:(p[3]||'').split(',').filter(Boolean)};
}

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

MDMAP.ready(el,function(map){
  /* Where a reader was sent, or the whole of Chiang Mai. */
  var want=readHash();
  if(want){
    map.jumpTo({center:[want.lng,want.lat],zoom:want.zoom});
    on=want.on.slice(0,MAX_ON);
  }else{
    on=DEFAULT_ON.slice(0,MAX_ON);
  }

  function srcId(k){return 'x-'+k;}

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
    loaded[k]=true;
  }

  function recolour(){
    Object.keys(loaded).forEach(function(k){
      var ink=inkFor(k);
      if(!ink)return;
      if(map.getLayer(srcId(k)+'-dot'))
        map.setPaintProperty(srcId(k)+'-dot','circle-color',ink);
    });
  }

  function show(k,yes){
    /* '-open' belongs in this list: a shelf switched off and on again while
       the open-now rings are lit would otherwise come back without them,
       because only its dots were ever hidden. */
    ['-halo','-dot','-open'].forEach(function(sfx){
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
  function wireTap(){
    map.on('click',function(e){
      var ids=[];
      on.forEach(function(k){
        if(map.getLayer(srcId(k)+'-dot'))ids.push(srcId(k)+'-dot');});
      if(!ids.length)return;
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
      var nm=[pr.nameTh,pr.nameEn].filter(Boolean).join(' · ')||pr.name||'';
      if(window.MDCARD)MDCARD.show({
        name:nm,
        sub:(pr.province==='cr'?'เชียงราย · Chiang Rai':'เชียงใหม่ · Chiang Mai'),
        href:root()+pr.province+'/p/'+pr.slug+'.html',
        plan:pr.province+':'+pr.slug,
        rank:(pr.rank&&pr.rank!=='0'&&pr.rank!==0)?pr.rank:''},el);
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
      paintChips();recolour();writeHash(map);
    });
  });

  document.getElementById('xclear').addEventListener('click',function(){
    on.slice().forEach(function(k){show(k,false);});
    on=[];paintChips();writeHash(map);
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

  map.on('moveend',function(){writeHash(map);});
  wireTap();
  on.slice().forEach(function(k){load(k);});
  paintChips();
  writeHash(map);
});
})();
"""


def emit(g):
    docs = g["DOCS"]
    (docs / "explore.css").write_text(CSS)
    (docs / "explore.js").write_text(_js())
    (docs / "map.html").write_text(build_page(g))
    rows = _chip_rows(g)
    return {"page": 1, "chips": sum(len(r["items"]) for r in rows),
            "provinces": len(rows)}


if __name__ == "__main__":
    print("This layer runs from build.py — it needs its helpers. "
          "Run: python3 build.py")
