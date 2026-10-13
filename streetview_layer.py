#!/usr/bin/env python3
"""streetview_layer.py — step down a street in Mapillary photos.

Her pick (a), 2026-10-13: street view from our own copies. The photos and the
index come from importers/harvest_streetview.py (on motdang-server):

  assets/streetphotos/sv/<imageId>.jpg   served on the streetphotos media route
  data/streetview/<cell>.json            one file per 0.01° cell

What this writes into docs/:
  streetview.js                          the viewer (window.MDSV), style included
  data/streetview/*.json                 the cells, as harvested
  streetphotos/sv/*.jpg                  through media_layer, like streetphoto_layer

Where it opens:
  · a "Street view" button on every MapLibre map (map_js(), bundled into /map.js):
    on, it draws the photo points and a tap opens the nearest photo;
  · the same button on the doodle maps (assets/sites/doodle-map/map.js);
  · a "Street view" button on a place page with a photo within NEAR_M (button_html()).

Every frame shows its year (Buddhist Era, with the Gregorian year), says when
it is older than STALE_YEARS, and names its photographer with the licence and
a link to the photo on Mapillary (CC BY-SA 4.0). The browser fetches the
photos and the cells from our own origin.
"""

import json
import math
import re
import shutil
import zlib
from pathlib import Path

import media_layer

ROOT = Path(__file__).resolve().parent
IMG_DIR = ROOT / "assets" / "streetphotos" / "sv"
IDX_DIR = ROOT / "data" / "streetview"
NEAR_M = 40.0
CELL = 0.01


def cell_of(lat, lng):
    return "%d_%d" % (math.floor(lat / CELL), math.floor(lng / CELL))


def _metres(lat1, lng1, lat2, lng2):
    r = 6371000.0
    dlat, dlng = math.radians(lat2 - lat1), math.radians(lng2 - lng1)
    a = (math.sin(dlat / 2) ** 2 + math.cos(math.radians(lat1))
         * math.cos(math.radians(lat2)) * math.sin(dlng / 2) ** 2)
    return 2 * r * math.asin(math.sqrt(a))


_CELLS = {}
_GRID = {}
G = 0.0004            # grid step, about 44 m: a 3×3 block covers NEAR_M


def _load(idx_dir=None):
    """Every cell under idx_dir, bucketed on a G-degree grid. Read once."""
    d = Path(idx_dir or IDX_DIR)
    k = str(d)
    if k not in _GRID:
        grid = {}
        for f in (sorted(d.glob("*.json")) if d.exists() else []):
            try:
                rows = json.loads(f.read_text())["img"]
            except (ValueError, OSError, KeyError):
                continue
            for row in rows:
                grid.setdefault((math.floor(row[1] / G), math.floor(row[2] / G)), []).append(row)
        _GRID[k] = grid
    return _GRID[k]


def nearest(lat, lng, idx_dir=None, near_m=NEAR_M):
    """The closest harvested photo to a point, or None."""
    if lat is None or lng is None:
        return None
    grid = _load(idx_dir)
    if not grid:
        return None
    gy, gx = math.floor(lat / G), math.floor(lng / G)
    reach = max(1, int(math.ceil(near_m / 44.0)))
    best, bd = None, near_m
    for dy in range(-reach, reach + 1):
        for dx in range(-reach, reach + 1):
            for row in grid.get((gy + dy, gx + dx), ()):
                d = _metres(lat, lng, row[1], row[2])
                if d <= bd:
                    best, bd = row, d
    return best


def button_html(rec, g, depth=2):
    """The place page's button. Empty when no photo stands within NEAR_M."""
    lat, lng = rec.get("lat"), rec.get("lng")
    row = nearest(lat, lng)
    if not row:
        return ""
    up = "../" * depth
    return ('<p class="svopen"><button type="button" class="svbtn" data-sv="%s,%s" '
            'data-svid="%s" aria-label="%s">%s</button></p>'
            '<script src="%sstreetview.js?v=%s" defer></script>'
            % (lat, lng, row[0],
               g["att"](g["bi_text"]("ดูภาพถนนตรงนี้", "Street view here")),
               ICON + g["bi"]("ภาพถนน", "Street view"), up, version()))


ICON = ('<svg viewBox="0 0 24 24" width="18" height="18" aria-hidden="true" '
        'style="vertical-align:-3px;margin-right:.35em"><circle cx="12" cy="5" r="2.6" '
        'fill="currentColor"/><path d="M8.5 9.5h7l-1 6h-1.5l-.6 6h-2.8l-.6-6H9.5z" '
        'fill="currentColor"/></svg>')


CSS = """/* streetview_layer — the place page's button */
.svopen{margin:.2rem 0 .9rem}
.svbtn{font:inherit;font-size:.92rem;padding:.45rem .9rem;border-radius:999px;
  border:1.5px solid var(--ink,#2b2118);background:var(--paper,#fffaf0);color:var(--ink,#2b2118);cursor:pointer}
.svbtn:hover,.svbtn:focus-visible{background:var(--ink,#2b2118);color:var(--paper,#fffaf0)}
"""


# The viewer. Loaded on demand by the maps and by the place page's button.
JS = r"""/* streetview.js — step down a street in photos (streetview_layer.py).
   Photos and cells come from this site: streetphotos/sv/<id>.jpg, data/streetview/<cell>.json. */
(function(){
if(window.MDSV)return;
var H=document.documentElement;
function base(){
  if(window.MDSV_BASE)return window.MDSV_BASE;
  var r=H.getAttribute('data-root');
  if(r!==null)return r;
  return /(^|\.)motdang\.net$|^(localhost|127\.0\.0\.1)$/.test(location.hostname)?'/':'https://motdang.net/';
}
function lang(){
  var c=H.classList;
  if(c.contains('lang-en')||H.getAttribute('data-lang')==='en')return 'en';
  if(c.contains('lang-th')||H.getAttribute('data-lang')==='th')return 'th';
  return 'both';
}
function L(th,en){var l=lang();return l==='en'?en:l==='th'?th:th+' · '+en;}
function L1(th,en){return lang()==='th'?th:en;}       /* short labels: one language */

/* ── cells ── */
var CELL=0.01,CELLS={},IMG={},SEQ={},BY={};
function ck(la,ln){return Math.floor(la/CELL)+'_'+Math.floor(ln/CELL);}
function cell(k){
  if(CELLS[k])return CELLS[k];
  return CELLS[k]=fetch(base()+'data/streetview/'+k+'.json').then(function(r){
    if(!r.ok)return null;return r.json();
  }).then(function(d){
    if(!d)return;
    (d.img||[]).forEach(function(i){
      if(IMG[i[0]])return;
      var s=d.seq[i[4]]||[null,0];
      var o={id:i[0],lat:i[1],lng:i[2],h:i[3],seq:i[4],ord:i[5],date:i[6],by:d.by[s[1]]};
      IMG[o.id]=o;(SEQ[o.seq]=SEQ[o.seq]||[]).push(o);
      SEQ[o.seq].dirty=1;
    });
  }).catch(function(){});
}
function around(la,ln){
  var y=Math.floor(la/CELL),x=Math.floor(ln/CELL),p=[];
  for(var dy=-1;dy<=1;dy++)for(var dx=-1;dx<=1;dx++)p.push(cell((y+dy)+'_'+(x+dx)));
  return Promise.all(p);
}
function seq(s){var a=SEQ[s];if(a&&a.dirty){a.sort(function(p,q){return p.ord-q.ord;});a.dirty=0;}return a||[];}
function m(a,b,c,d){var r=6371000,x=(d-b)*Math.PI/180*Math.cos((a+c)/2*Math.PI/180),y=(c-a)*Math.PI/180;return r*Math.sqrt(x*x+y*y);}
function brg(a,b,c,d){var x=(d-b)*Math.cos((a+c)/2*Math.PI/180),y=c-a;return (Math.atan2(x,y)*180/Math.PI+360)%360;}
function turn(a,b){if(a==null||b==null)return 0;var d=Math.abs(a-b)%360;return Math.min(d,360-d);}
function nearest(la,ln,max,f){
  var best=null,bd=max||40;
  for(var k in IMG){var o=IMG[k];if(f&&!f(o))continue;var d=m(la,ln,o.lat,o.lng);if(d<=bd){bd=d;best=o;}}
  return best;
}

/* ── the overlay ── */
var V=null,CUR=null,PUSHED=false;
function style(){
  if(document.getElementById('mdsv-css'))return;
  var s=document.createElement('style');s.id='mdsv-css';
  s.textContent=
  '.mdsv{position:fixed;inset:0;z-index:2147483000;background:#141210;color:#f4efe6;display:flex;flex-direction:column;font:15px/1.45 system-ui,-apple-system,"Noto Sans Thai",sans-serif}'+
  '.mdsv[hidden]{display:none}'+
  '.mdsv-pic{flex:1;position:relative;overflow:hidden;touch-action:pan-y}'+
  '.mdsv-pic img{position:absolute;inset:0;width:100%;height:100%;object-fit:contain;transition:opacity .18s,transform .25s}'+
  '.mdsv-pic img.go{opacity:.25;transform:scale(1.06)}'+
  '.mdsv-pic img.back{opacity:.25;transform:scale(.95)}'+
  '.mdsv-top{position:absolute;top:0;left:0;right:0;display:flex;gap:8px;padding:10px;justify-content:space-between;align-items:flex-start;pointer-events:none}'+
  '.mdsv-top>*{pointer-events:auto}'+
  '.mdsv button{font:inherit;cursor:pointer;border:0;border-radius:999px;background:rgba(20,18,16,.72);color:#fff;min-width:44px;min-height:44px;padding:0 14px}'+
  '.mdsv button:hover,.mdsv button:focus-visible{background:#f4efe6;color:#141210;outline:none}'+
  '.mdsv button[disabled]{opacity:.3;cursor:default}'+
  '.mdsv-top [data-a=x]{margin-left:auto}'+
  '.mdsv-toast{position:fixed;left:50%;bottom:24px;transform:translateX(-50%);z-index:2147483001;background:#141210;color:#f4efe6;padding:10px 16px;border-radius:999px;font:14px/1.4 system-ui,-apple-system,"Noto Sans Thai",sans-serif;box-shadow:0 4px 18px rgba(0,0,0,.25)}'+
  '.mdsv-dir{background:rgba(20,18,16,.72);border-radius:999px;padding:0 12px;line-height:44px;font-size:13px}'+
  '.mdsv-dir b{display:inline-block;transition:transform .25s}'+
  '.mdsv-nav{position:absolute;bottom:12px;left:0;right:0;display:flex;justify-content:center;gap:10px;pointer-events:none}'+
  '.mdsv-nav button{pointer-events:auto;font-size:20px;min-width:56px;min-height:56px}'+
  '.mdsv-cap{padding:10px 14px calc(10px + env(safe-area-inset-bottom));background:#141210;font-size:13px;color:#d9d1c3}'+
  '.mdsv-cap a{color:#f4efe6}'+
  '.mdsv-yrs{display:flex;flex-wrap:wrap;gap:6px;margin-top:6px}'+
  '.mdsv-yrs button{min-height:32px;min-width:0;padding:0 10px;font-size:13px;background:#2b2722}'+
  '.mdsv-yrs button[aria-pressed=true]{background:#f4efe6;color:#141210}'+
  '.mdsv-none{position:absolute;inset:0;display:flex;align-items:center;justify-content:center;text-align:center;padding:24px}';
  document.head.appendChild(s);
}
function build(){
  if(V)return V;
  style();
  V=document.createElement('div');V.className='mdsv';V.hidden=true;
  V.setAttribute('role','dialog');V.setAttribute('aria-modal','true');
  V.innerHTML='<div class="mdsv-pic"><img alt=""><div class="mdsv-top">'+
    '<span class="mdsv-dir" aria-live="polite"></span><button type="button" data-a="x"></button></div>'+
    '<div class="mdsv-nav"><button type="button" data-a="b">↓</button><button type="button" data-a="t">↻</button><button type="button" data-a="f">↑</button></div></div>'+
    '<div class="mdsv-cap"><div class="mdsv-when"></div><div class="mdsv-cred"></div><div class="mdsv-yrs"></div></div>';
  document.body.appendChild(V);
  V.querySelector('[data-a=x]').onclick=close;
  V.querySelector('[data-a=f]').onclick=function(){step(1);};
  V.querySelector('[data-a=b]').onclick=function(){step(-1);};
  V.querySelector('[data-a=t]').onclick=about;
  var img=V.querySelector('.mdsv-pic img');
  /* a tap on the photo walks on */
  img.onclick=function(){step(1);};
  var sx=null,sy=null;
  img.addEventListener('touchstart',function(e){sx=e.touches[0].clientX;sy=e.touches[0].clientY;},{passive:true});
  img.addEventListener('touchend',function(e){
    if(sx==null)return;var dx=e.changedTouches[0].clientX-sx,dy=e.changedTouches[0].clientY-sy;sx=null;
    if(Math.abs(dy)>60&&Math.abs(dy)>Math.abs(dx))step(dy<0?1:-1);
    else if(Math.abs(dx)>60)about();
  });
  document.addEventListener('keydown',function(e){
    if(V.hidden)return;
    if(e.key==='Escape')close();
    else if(e.key==='ArrowUp'||e.key==='ArrowRight')step(1);
    else if(e.key==='ArrowDown'||e.key==='ArrowLeft')step(-1);
    else return;
    e.preventDefault();
  });
  window.addEventListener('popstate',function(){if(!V.hidden){PUSHED=false;close();}});
  return V;
}
function labels(){
  V.querySelector('[data-a=x]').textContent=L1('ปิด','Close');
  V.querySelector('[data-a=x]').setAttribute('aria-label',L('ปิดภาพถนน','Close street view'));
  V.querySelector('[data-a=f]').setAttribute('aria-label',L('เดินหน้า','Forward'));
  V.querySelector('[data-a=b]').setAttribute('aria-label',L('ถอยหลัง','Back'));
  V.querySelector('[data-a=t]').setAttribute('aria-label',L('หันกลับ','Turn around'));
  V.setAttribute('aria-label',L('ภาพถนน','Street view'));
}
var DIRS=[['เหนือ','north'],['ตะวันออกเฉียงเหนือ','north-east'],['ตะวันออก','east'],['ตะวันออกเฉียงใต้','south-east'],
          ['ใต้','south'],['ตะวันตกเฉียงใต้','south-west'],['ตะวันตก','west'],['ตะวันตกเฉียงเหนือ','north-west']];
function when(o){
  if(!o.date)return L('ไม่รู้ว่าถ่ายเมื่อไหร่ — อาจเก่ามาก','Date unknown — it may be very old');
  var y=+o.date.slice(0,4),yr=(y+543)+' ('+y+')';
  var old=(Date.now()-Date.parse(o.date))>5*365.25*864e5;
  return old?L('ถ่ายเมื่อ พ.ศ. '+yr+' — ถนนอาจเปลี่ยนไปแล้ว','Taken in '+yr+' — the street may have changed since')
            :L('ถ่ายเมื่อ พ.ศ. '+yr,'Taken in '+yr);
}
function esc(s){return String(s).replace(/[&<>"]/g,function(c){return {'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;'}[c];});}
function show(o,how){
  CUR=o;build();labels();
  var img=V.querySelector('.mdsv-pic img'),none=V.querySelector('.mdsv-none');
  if(none)none.remove();
  img.hidden=false;
  if(how){img.classList.add(how);}
  var src=base()+'streetphotos/sv/'+o.id+'.jpg';
  var pre=new Image();pre.onload=pre.onerror=function(){img.src=src;img.classList.remove('go','back');};pre.src=src;
  img.alt=L('ภาพถนน','Street-level photo')+(o.date?' '+o.date.slice(0,4):'')+', '+o.by;
  var d=V.querySelector('.mdsv-dir');
  if(o.h!=null){var k=Math.round(o.h/45)%8;d.innerHTML='<b style="transform:rotate('+o.h+'deg)">↑</b> '+esc(L('หันไปทาง'+DIRS[k][0],'facing '+DIRS[k][1]));d.hidden=false;}
  else d.hidden=true;
  V.querySelector('.mdsv-when').textContent=when(o);
  V.querySelector('.mdsv-cred').innerHTML=
    '<a href="https://www.mapillary.com/app/user/'+encodeURIComponent(o.by)+'" rel="noopener nofollow" target="_blank">'+esc(o.by)+'</a> · '+
    '<a href="https://creativecommons.org/licenses/by-sa/4.0/" rel="noopener nofollow license" target="_blank">CC BY-SA 4.0</a> · '+
    '<a href="https://www.mapillary.com/app/?pKey='+encodeURIComponent(o.id)+'" rel="noopener nofollow" target="_blank">Mapillary</a>';
  around(o.lat,o.lng).then(function(){if(CUR===o){buttons();years();prefetch();}});
  buttons();years();
}
function idx(o){var a=seq(o.seq);for(var i=0;i<a.length;i++)if(a[i].id===o.id)return i;return -1;}
/* the next photo along: the next in this drive or walk, else the nearest photo
   of another one ahead within 30 m, looking the same way */
function next(o,dir){
  var a=seq(o.seq),i=idx(o)+dir;
  if(i>=0&&i<a.length)return a[i];
  var h=o.h==null?null:(dir>0?o.h:(o.h+180)%360);
  return nearest(o.lat,o.lng,30,function(p){
    if(p.seq===o.seq||m(o.lat,o.lng,p.lat,p.lng)<3)return false;
    if(h==null)return true;
    return turn(brg(o.lat,o.lng,p.lat,p.lng),h)<60&&turn(p.h,dir>0?o.h:p.h)<60;
  });
}
function back(o){
  if(o.h==null)return null;
  return nearest(o.lat,o.lng,20,function(p){return p.id!==o.id&&turn(p.h,o.h)>120;});
}
function step(dir){
  if(!CUR)return;var n=next(CUR,dir);
  if(n){if(navigator.vibrate)try{navigator.vibrate(8);}catch(e){}show(n,dir>0?'go':'back');}
}
function about(){var n=back(CUR);if(n)show(n);}
function buttons(){
  V.querySelector('[data-a=f]').disabled=!next(CUR,1);
  V.querySelector('[data-a=b]').disabled=!next(CUR,-1);
  V.querySelector('[data-a=t]').disabled=!back(CUR);
}
function prefetch(){[next(CUR,1),next(CUR,-1)].forEach(function(n){if(n){var i=new Image();i.src=base()+'streetphotos/sv/'+n.id+'.jpg';}});}
/* other drives and walks past this spot, one button per year */
function years(){
  var o=CUR,best={};
  for(var k in IMG){var p=IMG[k];if(p.seq===o.seq)continue;var d=m(o.lat,o.lng,p.lat,p.lng);if(d>15)continue;
    var sc=d+turn(p.h,o.h)/6;if(!best[p.seq]||sc<best[p.seq].sc)best[p.seq]={p:p,sc:sc};}
  var by={};
  Object.keys(best).forEach(function(s){var p=best[s].p,y=p.date?p.date.slice(0,4):'?';if(!by[y]||best[s].sc<by[y].sc)by[y]=best[s];});
  var ys=Object.keys(by).sort(),me=o.date?o.date.slice(0,4):'?',box=V.querySelector('.mdsv-yrs');
  if(!ys.length){box.innerHTML='';return;}
  if(ys.indexOf(me)<0)ys.push(me);ys.sort();
  box.innerHTML='<span>'+esc(L('ปีอื่นตรงนี้','Other years here'))+'</span>'+ys.map(function(y){
    return '<button type="button" data-y="'+y+'" aria-pressed="'+(y===me)+'">'+(y==='?'?'?':(lang()==='en'?y:(+y+543)))+'</button>';}).join('');
  box.querySelectorAll('button').forEach(function(b){b.onclick=function(){var y=b.getAttribute('data-y');if(y!==me&&by[y])show(by[y].p);};});
}
function none(){
  build();labels();CUR=null;
  V.querySelector('.mdsv-pic img').hidden=true;
  V.querySelector('.mdsv-dir').hidden=true;
  ['f','b','t'].forEach(function(a){V.querySelector('[data-a='+a+']').disabled=true;});
  V.querySelector('.mdsv-when').textContent='';V.querySelector('.mdsv-cred').textContent='';V.querySelector('.mdsv-yrs').innerHTML='';
  var n=document.createElement('div');n.className='mdsv-none';
  n.textContent=L('ยังไม่มีภาพถนนตรงนี้','No street photos here yet');
  V.querySelector('.mdsv-pic').appendChild(n);
}
var BACKTO=null,TT=null;
function toast(msg){
  style();var t=document.querySelector('.mdsv-toast');
  if(!t){t=document.createElement('div');t.className='mdsv-toast';t.setAttribute('role','status');document.body.appendChild(t);}
  t.textContent=msg;t.hidden=false;clearTimeout(TT);TT=setTimeout(function(){t.hidden=true;},2200);
}
/* at: {lat, lng, id?, max?, quiet?}. quiet: a map tap with nothing near says so in a line and stays on the map */
function open(at){
  var la=+at.lat,ln=+at.lng;
  if(at.quiet)return around(la,ln).then(function(){
    var o=(at.id&&IMG[at.id])||nearest(la,ln,at.max||40);
    if(!o){toast(L('ยังไม่มีภาพถนนตรงนี้ ลองแตะใกล้จุดสีน้ำเงิน','No street photos here yet. Tap near a blue dot.'));return false;}
    return open({lat:o.lat,lng:o.lng,id:o.id});
  });
  build();
  BACKTO=document.activeElement;
  if(V.hidden){V.hidden=false;try{history.pushState({mdsv:1},'');PUSHED=true;}catch(e){}}
  V.querySelector('[data-a=x]').focus();
  return around(la,ln).then(function(){
    var o=(at.id&&IMG[at.id])||nearest(la,ln,at.max||40);
    if(o)show(o);else none();
    return !!o;
  });
}
function close(){
  if(!V||V.hidden)return;
  V.hidden=true;CUR=null;
  if(PUSHED){PUSHED=false;try{history.back();}catch(e){}}
  if(BACKTO&&BACKTO.focus)try{BACKTO.focus();}catch(e){}
  if(window.MDSV.onclose)window.MDSV.onclose();
}
/* photo points inside a box, for a map to draw: loads at most 9 cells */
function points(w,s,e,n,cb){
  var y0=Math.floor(s/CELL),y1=Math.floor(n/CELL),x0=Math.floor(w/CELL),x1=Math.floor(e/CELL);
  if((y1-y0+1)*(x1-x0+1)>9){cb([]);return;}
  var p=[];for(var y=y0;y<=y1;y++)for(var x=x0;x<=x1;x++)p.push(cell(y+'_'+x));
  Promise.all(p).then(function(){
    var out=[];for(var k in IMG){var o=IMG[k];if(o.lat>=s&&o.lat<=n&&o.lng>=w&&o.lng<=e)out.push(o);}
    cb(out);
  });
}
/* the place page's button (streetview_layer.button_html) */
function wire(){
  document.querySelectorAll('[data-sv]').forEach(function(b){
    if(b.__sv)return;b.__sv=1;
    b.addEventListener('click',function(){var p=b.getAttribute('data-sv').split(',');open({lat:p[0],lng:p[1],id:b.getAttribute('data-svid')});});
  });
}
window.MDSV={open:open,close:close,points:points,wire:wire,L:L};
if(document.readyState==='loading')document.addEventListener('DOMContentLoaded',wire);else wire();
})();
"""


# Bundled into /map.js (map_shell.emit): a Street view button on every MapLibre map.
MAP_JS = r"""/* street view on MapLibre maps (streetview_layer.py) */
window.MDSVMAP={paint:function(map,el){
  if(el.__svm)return;el.__svm=1;
  var H=document.documentElement,R=H.getAttribute('data-root')||'';
  function L(th,en){var c=H.classList;return c.contains('lang-en')?en:c.contains('lang-th')?th:th+' · '+en;}
  var on=false,lib=null;
  function load(){return lib||(lib=new Promise(function(ok){
    if(window.MDSV)return ok(window.MDSV);
    var s=document.createElement('script');s.src=R+'streetview.js';
    s.onload=function(){ok(window.MDSV);};s.onerror=function(){ok(null);};document.head.appendChild(s);}));}
  var EMPTY={type:'FeatureCollection',features:[]};
  function draw(){
    if(!on||map.getZoom()<14){var s=map.getSource('md-sv');if(s)s.setData(EMPTY);return;}
    var b=map.getBounds();
    load().then(function(S){if(!S)return;S.points(b.getWest(),b.getSouth(),b.getEast(),b.getNorth(),function(rows){
      var s=map.getSource('md-sv');if(!s||!on)return;
      s.setData({type:'FeatureCollection',features:rows.map(function(o){return {type:'Feature',properties:{},geometry:{type:'Point',coordinates:[o.lng,o.lat]}};})});
    });});
  }
  function layer(){
    if(map.getSource('md-sv'))return;
    map.addSource('md-sv',{type:'geojson',data:EMPTY});
    map.addLayer({id:'md-sv',type:'circle',source:'md-sv',paint:{
      'circle-radius':['interpolate',['linear'],['zoom'],14,1.6,18,4],
      'circle-color':'#1f6fd1','circle-opacity':0.8,
      'circle-stroke-color':'#fff','circle-stroke-width':['interpolate',['linear'],['zoom'],14,0,17,1]}});
  }
  var btn;
  function set(v){
    on=v;btn.setAttribute('aria-pressed',on);
    map.getCanvas().style.cursor=on?'crosshair':'';
    if(on){load();layer();if(map.getZoom()<15.5)map.easeTo({zoom:15.5});}
    draw();
  }
  function Ctl(){}
  Ctl.prototype.onAdd=function(){
    var d=document.createElement('div');d.className='maplibregl-ctrl maplibregl-ctrl-group md-svctl';
    btn=document.createElement('button');btn.type='button';btn.setAttribute('aria-pressed','false');
    btn.setAttribute('aria-label',L('ภาพถนน','Street view'));btn.title=L('ภาพถนน','Street view');
    btn.innerHTML='<svg viewBox="0 0 24 24" width="20" height="20" aria-hidden="true"><circle cx="12" cy="5" r="2.6" fill="currentColor"/><path d="M8.5 9.5h7l-1 6h-1.5l-.6 6h-2.8l-.6-6H9.5z" fill="currentColor"/></svg>';
    btn.onclick=function(){set(!on);};
    d.appendChild(btn);
    var st=document.createElement('style');
    st.textContent='.md-svctl button[aria-pressed=true]{background:#1f6fd1;color:#fff}.md-svctl button{color:#2b2118}';
    d.appendChild(st);
    return d;
  };
  Ctl.prototype.onRemove=function(){};
  try{map.addControl(new Ctl(),'top-left');}catch(e){return;}
  map.on('moveend',draw);
  map.on('click',function(e){
    if(!on)return;
    load().then(function(S){if(S)S.open({lat:e.lngLat.lat,lng:e.lngLat.lng,max:60,quiet:1});});
  });
}};
"""


def map_js():
    return MAP_JS.replace("R+'streetview.js'", "R+'streetview.js?v=%s'" % version())


def version():
    return "%08x" % (zlib.crc32(JS.encode("utf-8")) & 0xFFFFFFFF)


def emit(g):
    """docs/streetview.js, the cells, and the photos the cells name."""
    docs = Path(g["DOCS"])
    (docs / "streetview.js").write_text(JS)
    cells = sorted(IDX_DIR.glob("*.json")) if IDX_DIR.exists() else []
    out = docs / "data" / "streetview"
    out.mkdir(parents=True, exist_ok=True)
    n = 0
    for c in cells:
        try:
            rows = json.loads(c.read_text())["img"]
        except (ValueError, OSError, KeyError):
            continue
        shutil.copy(c, out / c.name)
        for row in rows:
            src = IMG_DIR / ("%s.jpg" % row[0])
            if not src.exists():
                continue
            rel = "streetphotos/sv/%s" % src.name
            if media_layer.on():
                media_layer.put(src, docs, rel)
            else:
                dest = docs / rel
                if not (dest.exists() and dest.stat().st_size == src.stat().st_size):
                    dest.parent.mkdir(parents=True, exist_ok=True)
                    shutil.copy(src, dest)
            n += 1
    # the doodle maps load the viewer by name; stamp it with this version
    dm = docs / "sites" / "doodle-map" / "map.js"
    if dm.exists():
        t = dm.read_text()
        t2 = re.sub(r"streetview\.js(\?v=[0-9a-f]+)?'", "streetview.js?v=%s'" % version(), t)
        if t2 != t:
            dm.write_text(t2)
            import mappins_layer
            mappins_layer.stamp_doodle(docs)
    return {"cells": len(cells), "photos": n}
