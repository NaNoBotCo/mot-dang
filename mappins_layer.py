#!/usr/bin/env python3
"""mappins_layer.py — the directory's places on every map, as icon pins, more of
them with every step in.

Nan, 2026-10-10: "All maps on motdang.net should show increasing detail as the
zoom level increases. This should be at least partially controlled by user
preferences. ... Pins should have names and locations, and be visible when
zoomed in." 2026-10-11: "Should be even MORE identified places at high zoom
levels. Places should also come with an icon marker as the pin ... a round
colored background and a contrast svg sprite as the visual indicator of place
type. ... up to 50 places per zoom on desktop and 20-30 on phone, with some
measures to avoid clutter."

One module, two readers:
  · every MapLibre map map_shell.py builds (place pages, /map.html, search,
    the doodle maps' Streets and Terrain views): map.js carries MAP_JS and
    calls MDPINS.paint(map, el) on load;
  · the doodle maps' own canvas (assets/sites/doodle-map/map.js), which loads
    /pins.js and draws with MDPINS.icon().

The pin: a disc in the category's colour, a white rim, and the category's
glyph from the site's own icon sprite (assets/icons.svg, the same marks the
directory rows wear) stroked in white. Every colour clears 4.5:1 against
white (tests/test_pins.py).

Clutter, in order: a cap per view by map size (50 wide, 25 phone, 12 card);
fewer while the view is still wide (the ramp in count()); the best-known
places first (the API's ant rank), so a lesser pin is the one that gives way;
a pin that would touch a drawn mark or another pin is not drawn; names only
from street level and only where they fit; a place a shelf already shows, or
the place the page is about, is skipped.

The reader's 'md-detail' choice (less / more / most, the doodle maps' Detail
chip) moves the zoom it starts at and halves the cap at 'less'.
"""

import json
import re
import zlib
from pathlib import Path

ROOT = Path(__file__).resolve().parent

# category → (sprite glyph, disc colour). Glyphs match build.CAT_ICON.
KINDS = {
    "wat": ("i-wat", "#A85A07"),
    "food": ("i-food", "#C2410C"),
    "massage": ("i-spa", "#0F766E"),
    "medical": ("i-health", "#B91C1C"),
    "cannabis": ("i-leaf", "#3F6212"),
    "essentials": ("i-bank", "#1E40AF"),
    "hotel": ("i-bed", "#6D28D9"),
    "school": ("i-school", "#4338CA"),
    "school-intl": ("i-school", "#4338CA"),
    "market": ("i-market", "#9A3412"),
    "shopping": ("i-gift", "#BE185D"),
    "realestate": ("i-home2", "#57534E"),
    "transport": ("i-ride", "#0369A1"),
    "repair": ("i-tools", "#44403C"),
    "beauty": ("i-beauty", "#A21CAF"),
    "tattoo": ("i-ink", "#1F2937"),
    "pets": ("i-pet", "#92400E"),
    "sport": ("i-fit", "#0E7490"),
    "muaythai": ("i-glove", "#991B1B"),
    "cooking": ("i-khrok", "#9A6700"),
    "chang": ("i-chang", "#475569"),
    "home-services": ("i-broom", "#155E75"),
    "community": ("i-people", "#4D7C0F"),
    "business": ("i-shop", "#334155"),
    "whats-on": ("i-film", "#9D174D"),
    "museums-galleries": ("i-museum", "#7E22CE"),
    "parks": ("i-park", "#166534"),
    "sights": ("i-star", "#BE123C"),
}
OTHER = ("i-pin", "#5B4636")


def _num(a, k, d=0.0):
    m = re.search(r'\b' + k + r'="([-\d.]+)"', a)
    return float(m.group(1)) if m else d


def _to_path(tag, a):
    """One sprite primitive as SVG path data, for Path2D."""
    if tag == "path":
        return re.search(r'\bd="([^"]+)"', a).group(1)
    if tag == "rect":
        x, y, w, h = _num(a, "x"), _num(a, "y"), _num(a, "width"), _num(a, "height")
        r = min(_num(a, "rx"), w / 2, h / 2)
        if not r:
            return f"M{x} {y}h{w}v{h}h{-w}Z"
        return (f"M{x + r} {y}h{w - 2 * r}a{r} {r} 0 0 1 {r} {r}v{h - 2 * r}"
                f"a{r} {r} 0 0 1 {-r} {r}h{-(w - 2 * r)}a{r} {r} 0 0 1 {-r} {-r}"
                f"v{-(h - 2 * r)}a{r} {r} 0 0 1 {r} {-r}Z")
    if tag in ("circle", "ellipse"):
        cx, cy = _num(a, "cx"), _num(a, "cy")
        rx = _num(a, "r") if tag == "circle" else _num(a, "rx")
        ry = _num(a, "r") if tag == "circle" else _num(a, "ry")
        return f"M{cx - rx} {cy}a{rx} {ry} 0 1 0 {2 * rx} 0a{rx} {ry} 0 1 0 {-2 * rx} 0Z"
    raise ValueError(tag)


def glyph(gid, sprite=None):
    """A sprite glyph as a list of path strings."""
    sprite = sprite or (ROOT / "assets" / "icons.svg").read_text()
    m = re.search(r'<g id="' + re.escape(gid) + r'">(.*?)</g>', sprite, re.S)
    if not m:
        raise KeyError(gid)
    return [_to_path(t, a) for t, a in re.findall(r'<(path|rect|circle|ellipse)\b([^>]*)/?>', m.group(1))]


def table():
    sprite = (ROOT / "assets" / "icons.svg").read_text()
    out = {k: [col, glyph(g, sprite)] for k, (g, col) in KINDS.items()}
    out["_"] = [OTHER[1], glyph(OTHER[0], sprite)]
    return out


JS = r"""/* mappins_layer.py — the directory's places as icon pins, more with every step in. */
(function(){
if(window.MDPINS)return;
var K=%KINDS%;
var LIVE=/(^|\.)motdang\.net$/.test(location.hostname)?'/':'https://motdang.net/';
function pref(){try{var p=localStorage.getItem('md-detail');if(p==='less'||p==='most')return p;}catch(e){}return 'more';}
/* how many a view carries: by the map's size (a card's small map 12, a phone 25, wider 50), halved at 'less' */
function cap(w,h){var n=w<640?(h&&h<320?12:25):50;return pref()==='less'?Math.ceil(n/2):n;}
/* fewer while the view is still wide: 45% at the floor, all of them two steps in */
function count(w,steps,h){if(steps<0)return 0;return Math.max(4,Math.round(cap(w,h)*Math.min(1,0.45+0.275*steps)));}
function kindOf(cats){cats=cats||[];for(var i=0;i<cats.length;i++)if(K[cats[i]])return cats[i];return '_';}
function thin(r){return / · [\d.,]+ ?(m|km|ม\.|กม\.) /.test((r.nameEn||'')+' '+(r.name||'')+' ');}
/* one pin, drawn once per kind and size and kept */
var CACHE={};
function icon(kind,d,R){
  var b=K[kind]||K._,key=kind+'|'+d+'|'+R;
  if(CACHE[key])return CACHE[key];
  var c=document.createElement('canvas'),x=c.getContext('2d'),h=d/2;
  c.width=c.height=Math.ceil(d*R);if(!x)return null;x.scale(R,R);
  x.beginPath();x.arc(h,h,h-0.5,0,6.2832);x.fillStyle='rgba(23,17,12,.45)';x.fill();
  x.beginPath();x.arc(h,h,h-1,0,6.2832);x.fillStyle='#fff';x.fill();
  x.beginPath();x.arc(h,h,h-2.6,0,6.2832);x.fillStyle=b[0];x.fill();
  if(window.Path2D){var g=d*0.6,s=g/24;x.save();x.translate(h-g/2,h-g/2);x.scale(s,s);
    x.strokeStyle='#fff';x.lineWidth=2.4;x.lineCap='round';x.lineJoin='round';
    b[1].forEach(function(p){x.stroke(new Path2D(p));});x.restore();}
  return (CACHE[key]=c);
}
function J(u){return fetch(u).then(function(r){if(!r.ok)throw 0;return r.json();});}
/* the places in a box, best known first */
function places(w,s,e,n,lim){
  return J(LIVE+'api/v1/places?bbox='+[w,s,e,n].map(function(v){return v.toFixed(4);}).join(',')+'&limit='+lim)
    .then(function(d){return (d.results||[]).filter(function(r){return r.lat!=null&&!thin(r);});});
}
function lang(){var h=document.documentElement,c=h.classList,l=h.getAttribute('data-lang')||h.lang||'';
  return c.contains('lang-en')||/^en/.test(l)&&!c.contains('lang-th')?'en':c.contains('lang-th')||/^th/.test(l)?'th':'';}
function names(r){
  var th=r.name||'',en=r.nameEn||'',L=lang();
  if(L==='en')return en||th;if(L==='th')return th||en;
  return th&&en&&th!==en?th+'\n'+en:th||en;
}
function item(r){
  var href=String(r.url||'').replace(/^https?:\/\/[^/]+\//,'/');
  return {name:names(r).replace('\n',' · '),sub:'',href:href,json:href.replace(/\.html$/,'.json'),lat:+r.lat,lng:+r.lng};
}

/* ---- every MapLibre map (map_shell.py calls paint on load) ---- */
var FONT=['NotoSans'];
((window.MDMAP_CFG&&MDMAP_CFG.layers)||[]).some(function(l){
  if(l.type==='symbol'&&l.layout&&l.layout['text-font']){FONT=l.layout['text-font'];return true;}});
var FLOOR={less:15,more:14,most:13};
var MUTE=new WeakMap(),REDO=new WeakMap(),ROWS=new WeakMap();
function paint(map,el){
  if(map.getSource('md-pins'))return;
  var R=Math.min(3,Math.max(2,window.devicePixelRatio||1)),D=map.getContainer().clientWidth<640?22:24;
  var skip=el&&el.id!=='xmap'&&el.querySelector&&el.querySelector('.mdmap-draw')&&isFinite(parseFloat(el.dataset.lat))?
    [parseFloat(el.dataset.lat),parseFloat(el.dataset.lng)]:null;
  map.on('styleimagemissing',function(e){
    if(!e.id||e.id.indexOf('mdp-')!==0||map.hasImage(e.id))return;
    var c=icon(e.id.slice(4),D,R);if(!c)return;
    map.addImage(e.id,c.getContext('2d').getImageData(0,0,c.width,c.height),{pixelRatio:R});});
  map.addSource('md-pins',{type:'geojson',data:{type:'FeatureCollection',features:[]}});
  var lay={id:'md-pins',type:'symbol',source:'md-pins',layout:{
    'icon-image':['concat','mdp-',['get','c']],'icon-size':['interpolate',['linear'],['zoom'],13,0.82,16,1],
    'icon-padding':4,'symbol-sort-key':['get','o']}};
  if(window.MDMAP_CFG&&MDMAP_CFG.glyphs){
    lay.layout['text-field']=['step',['zoom'],'',15.5,['get','n']];
    lay.layout['text-font']=FONT;lay.layout['text-size']=12;lay.layout['text-max-width']=9;
    lay.layout['text-variable-anchor']=['left','right','top','bottom'];lay.layout['text-radial-offset']=1.15;
    lay.layout['text-justify']='auto';lay.layout['text-optional']=true;
    lay.paint={'text-color':'#2b2118','text-halo-color':'#FFFCF6','text-halo-width':1.6};
  }
  /* under every layer a page adds after it: a shelf the reader chose wins */
  var first=(map.getStyle().layers||[]).filter(function(l){return l.id.indexOf('md-mine')===0;})[0];
  map.addLayer(lay,first&&first.id);
  var rows=[],key='',t=0;
  function data(){
    var m=MUTE.get(map)||{},f=[];
    rows.forEach(function(r,i){var k=kindOf(r.categories);if(m[k])return;
      f.push({type:'Feature',geometry:{type:'Point',coordinates:[+r.lng,+r.lat]},
        properties:{i:i,o:i,c:k,n:names(r)}});});
    var s=map.getSource('md-pins');if(s)s.setData({type:'FeatureCollection',features:f});
  }
  REDO.set(map,data);
  function want(){
    var z=map.getZoom(),steps=z-FLOOR[pref()],ct=map.getContainer(),n=count(ct.clientWidth,steps,ct.clientHeight);
    if(!n){if(rows.length){rows=[];key='';data();}return;}
    var b=map.getBounds(),W=b.getWest(),S=b.getSouth(),E=b.getEast(),N=b.getNorth(),g=(N-S)/10;
    W=Math.floor(W/g)*g;S=Math.floor(S/g)*g;E=Math.ceil(E/g)*g;N=Math.ceil(N/g)*g;
    var k=[n,W,S,E,N].map(function(v){return typeof v==='number'?v.toFixed(4):v;}).join('|');
    if(k===key)return;key=k;
    places(W,S,E,N,n+(skip?1:0)).then(function(rs){
      if(key!==k)return;
      if(skip)rs=rs.filter(function(r){return Math.abs(r.lat-skip[0])>3e-4||Math.abs(r.lng-skip[1])>3e-4;});
      rows=rs.slice(0,n);ROWS.set(map,rows);data();}).catch(function(){if(key===k)key='';});
  }
  map.on('moveend',function(){clearTimeout(t);t=setTimeout(want,300);});
  addEventListener('storage',function(e){if(e.key==='md-detail'){key='';want();}});
  new MutationObserver(data).observe(document.documentElement,{attributes:true,attributeFilter:['class','data-lang']});
  map.on('click','md-pins',function(e){
    var f=e.features&&e.features[0];if(!f)return;var r=rows[f.properties.i];if(!r)return;
    /* a page that answers its own taps (the doodle maps) reads the row with MDPINS.row */
    if(el&&el.hasAttribute&&el.hasAttribute('data-mdpins-own'))return;
    var it=item(r);
    if(window.MDX&&MDX.el===el&&MDX.openItem){MDX.openItem(it);return;}
    if(window.MDCARD){MDCARD.show(it,el);return;}
    if(it.href)location.href=it.href;});
  map.on('mouseenter','md-pins',function(){map.getCanvas().style.cursor='pointer';});
  map.on('mouseleave','md-pins',function(){map.getCanvas().style.cursor='';});
  want();
}
/* a shelf switched on draws its own dots: its kind's pins step aside */
function mute(map,kind,yes){var m=MUTE.get(map)||{};m[kind]=!!yes;MUTE.set(map,m);
  var f=REDO.get(map);if(f)f();}
/* explore.js asks before answering a tap, so one touch opens one sheet */
function hit(map,pt){if(!map.getLayer('md-pins'))return false;
  return map.queryRenderedFeatures([[pt.x-12,pt.y-12],[pt.x+12,pt.y+12]],{layers:['md-pins']}).length>0;}
function row(map,i){var r=ROWS.get(map);return r&&r[i];}
window.MDPINS={K:K,row:row,icon:icon,kindOf:kindOf,cap:cap,count:count,pref:pref,places:places,thin:thin,paint:paint,mute:mute,hit:hit};
})();
"""


def map_js():
    return JS.replace("%KINDS%", json.dumps(table(), separators=(",", ":")))


def version():
    return "%08x" % (zlib.crc32(map_js().encode("utf-8")) & 0xFFFFFFFF)


def stamp_doodle(docs):
    """The doodle maps' pages name map.js with a hand-set ?v= (1010h), and map.js and
    pins.js are served stale-while-revalidate, so a returning reader kept the old
    drawing code after an edit under the same ?v= (Nan's screenshot of 2026-10-11:
    no pins at 125 m on a build that had them). Stamp both with their content."""
    docs = Path(docs)
    js = docs / "sites" / "doodle-map" / "map.js"
    if not js.exists():
        return 0
    src = js.read_text()
    src = re.sub(r"'/pins\.js(\?v=[0-9a-f]+)?'", "'/pins.js?v=%s'" % version(), src)
    js.write_text(src)
    v = "%08x" % (zlib.crc32(src.encode("utf-8")) & 0xFFFFFFFF)
    n = 0
    for page in (docs / "sites").glob("doodle-*/index.html"):
        t = page.read_text()
        t2 = re.sub(r'((?:\.\./doodle-map/)?map\.js)\?v=[0-9A-Za-z]+"', r'\1?v=' + v + '"', t)
        if t2 != t:
            page.write_text(t2)
            n += 1
    return n


def emit(docs):
    """/pins.js, for the doodle maps' canvas (map.js carries its own copy)."""
    (Path(docs) / "pins.js").write_text(map_js())


if __name__ == "__main__":
    import sys
    out = Path(sys.argv[1]) if len(sys.argv) > 1 else ROOT / "docs"
    emit(out)
    print(out / "pins.js", version())
