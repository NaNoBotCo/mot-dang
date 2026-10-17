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
# A gold own page (Nan, 2026-10-14): a gold disc with a dark glyph, a little larger
# than the rest. Dark on gold, as the gold buttons are.
GOLD = ("#F4B400", "#2B1A00")


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
    out["^"] = list(GOLD)          # the gold disc and its glyph colour, not a kind
    return out


JS = r"""/* mappins_layer.py — the directory's places as icon pins, more with every step in. */
(function(){
if(window.MDPINS)return;
var K=%KINDS%;
var LIVE=/(^|\.)motdang\.net$/.test(location.hostname)?'/':'https://motdang.net/';
function pref(){try{var p=localStorage.getItem('md-detail');if(p==='less'||p==='most')return p;}catch(e){}return 'more';}
/* how many a view carries, the same at every zoom (Nan, 2026-10-11: "every zoom level has about 50 places
   visible on desktop, maybe a couple fewer on phone"): by the map's size (a card's small map 12, a phone 45,
   wider 50), halved at 'less', half again at 'most' */
function cap(w,h){var n=w<640?(h&&h<320?12:45):50,p=pref();return p==='less'?Math.ceil(n/2):p==='most'?Math.round(n*1.5):n;}
function count(w,steps,h){return cap(w,h);}
function kindOf(cats){cats=cats||[];for(var i=0;i<cats.length;i++)if(K[cats[i]]&&cats[i]!=='^')return cats[i];return '_';}
function thin(r){return / · [\d.,]+ ?(m|km|ม\.|กม\.) /.test((r.nameEn||'')+' '+(r.name||'')+' ');}
/* one pin, drawn once per kind and size and kept */
var CACHE={};
function icon(kind,d,R,gold){
  var b=K[kind]||K._,key=kind+'|'+d+'|'+R+(gold?'|g':'');
  if(CACHE[key])return CACHE[key];
  var c=document.createElement('canvas'),x=c.getContext('2d'),h=d/2;
  c.width=c.height=Math.ceil(d*R);if(!x)return null;x.scale(R,R);
  x.beginPath();x.arc(h,h,h-0.5,0,6.2832);x.fillStyle='rgba(23,17,12,.45)';x.fill();
  x.beginPath();x.arc(h,h,h-1,0,6.2832);x.fillStyle='#fff';x.fill();
  if(gold){x.beginPath();x.arc(h,h,h-2.2,0,6.2832);x.fillStyle='#8A6500';x.fill();}
  x.beginPath();x.arc(h,h,h-(gold?3.4:2.6),0,6.2832);x.fillStyle=gold?K['^'][0]:b[0];x.fill();
  if(window.Path2D){var g=d*0.6,s=g/24;x.save();x.translate(h-g/2,h-g/2);x.scale(s,s);
    x.strokeStyle=gold?K['^'][1]:'#fff';x.lineWidth=2.4;x.lineCap='round';x.lineJoin='round';
    b[1].forEach(function(p){x.stroke(new Path2D(p));});x.restore();}
  return (CACHE[key]=c);
}
function J(u){return fetch(u).then(function(r){if(!r.ok)throw 0;return r.json();});}
/* The gold own pages (ownpage_layer.py, /ownpages-gold.json): a few places, each drawn as a gold pin with its name
   ahead of the view's others. Rows are shaped like the API's so the maps treat them the same. */
var GOLD={rows:[],ids:{}};
var GOLDP=J(LIVE+'ownpages-gold.json').then(function(d){
  GOLD.rows=((d&&d.rows)||[]).filter(function(g){return g&&g.id&&isFinite(g.lat)&&isFinite(g.lng);}).map(function(g){
    return {id:g.id,url:'/'+g.u,name:g.th||g.en,nameEn:g.en,categories:g.cat||[],lat:+g.lat,lng:+g.lng,gold:1,own:g.own};});
  GOLD.rows.forEach(function(g){GOLD.ids[g.id]=1;});return GOLD;
}).catch(function(){return GOLD;});
function goldIn(w,s,e,n){return GOLD.rows.filter(function(g){return g.lng>=w&&g.lng<=e&&g.lat>=s&&g.lat<=n;});}
/* the places in a box, best known first */
function places(w,s,e,n,lim){
  return J(LIVE+'api/v1/places?bbox='+[w,s,e,n].map(function(v){return v.toFixed(4);}).join(',')+'&limit='+lim)
    .then(function(d){return (d.results||[]).filter(function(r){return r.lat!=null&&!thin(r);});}).then(readings);
}
/* Nan, 2026-10-11: "All names should be transliterated on the english speaking map pages if no english
   version exists." A Thai-only name reads by its RTGS reading in English (/readings.js, readings_layer.py),
   waited for at most 0.8 s */
var RJS=null;
function readings(rows){
  if(lang()==='th')return rows;
  RJS=RJS||new Promise(function(ok){if(window.MDREAD)return ok(MDREAD);var s=document.createElement('script');
    s.src=LIVE+'readings.js';s.onload=function(){ok(window.MDREAD||null);};s.onerror=function(){ok(null);};document.head.appendChild(s);});
  return Promise.race([RJS.then(function(R){return R?R.want(rows.filter(function(r){return !r.nameEn;})):0;}),
    new Promise(function(ok){setTimeout(ok,800);})]).then(function(){return rows;},function(){return rows;});
}
/* the box in nine cells, each cell's best known taken in turn: the whole box at once puts them all in the old city,
   where they hide each other */
function spread(w,s,e,n,lim){
  var per=Math.ceil(lim/9),cw=(e-w)/3,ch=(n-s)/3,q=[];
  for(var i=0;i<9;i++){var x=w+(i%3)*cw,y=s+Math.floor(i/3)*ch;q.push(places(x,y,x+cw,y+ch,per).catch(function(){return [];}));}
  return Promise.all(q).then(function(g){var out=[],ids={};
    for(var k=0;k<per;k++)g.forEach(function(c){var r=c[k];if(r&&!ids[r.id]){ids[r.id]=1;out.push(r);}});return out;});
}
function reading(r){return window.MDREAD&&!r.nameEn?MDREAD.of(r.id):'';}
function lang(){var h=document.documentElement,c=h.classList,l=h.getAttribute('data-lang')||h.lang||'';
  return c.contains('lang-en')||/^en/.test(l)&&!c.contains('lang-th')?'en':c.contains('lang-th')||/^th/.test(l)?'th':'';}
function names(r){
  var th=r.name||'',en=r.nameEn||'',L=lang();
  if(L==='en')return en||reading(r)||th;if(L==='th')return th||en;
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
var MUTE=new WeakMap(),REDO=new WeakMap(),ROWS=new WeakMap();
function paint(map,el){
  if(map.getSource('md-pins'))return;
  var R=Math.min(3,Math.max(2,window.devicePixelRatio||1)),D=map.getContainer().clientWidth<640?22:24;
  var skip=el&&el.id!=='xmap'&&el.querySelector&&el.querySelector('.mdmap-draw')&&isFinite(parseFloat(el.dataset.lat))?
    [parseFloat(el.dataset.lat),parseFloat(el.dataset.lng)]:null;
  map.on('styleimagemissing',function(e){
    if(!e.id||e.id.indexOf('mdp-')!==0||map.hasImage(e.id))return;
    var g=e.id.indexOf('mdp-^')===0,c=g?icon(e.id.slice(5),D+4,R,true):icon(e.id.slice(4),D,R);if(!c)return;
    map.addImage(e.id,c.getContext('2d').getImageData(0,0,c.width,c.height),{pixelRatio:R});});
  map.addSource('md-pins',{type:'geojson',data:{type:'FeatureCollection',features:[]}});
  var lay={id:'md-pins',type:'symbol',source:'md-pins',layout:{
    'icon-image':['concat','mdp-',['get','c']],'icon-size':['interpolate',['linear'],['zoom'],13,0.82,16,1],
    'icon-padding':4,'symbol-sort-key':['get','o']}};
  if(window.MDMAP_CFG&&MDMAP_CFG.glyphs){
    lay.layout['text-field']=['get','n'];
    lay.layout['text-font']=FONT;lay.layout['text-size']=['case',['has','g'],13.5,12];lay.layout['text-max-width']=9;
    lay.layout['text-variable-anchor']=['left','right','top','bottom'];lay.layout['text-radial-offset']=1.15;
    lay.layout['text-justify']='auto';lay.layout['text-optional']=true;
    lay.paint={'text-color':'#2b2118','text-halo-color':'#FFFCF6','text-halo-width':1.6};
  }
  /* under every layer a page adds after it: a shelf the reader chose wins */
  var first=(map.getStyle().layers||[]).filter(function(l){return l.id.indexOf('md-mine')===0;})[0];
  map.addLayer(lay,first&&first.id);
  /* rows holds spares: a pin that collides is hidden, so the view takes more rows until about n show */
  var rows=[],key='',t=0,take=0,goal=0,tops=0;
  function data(){
    var m=MUTE.get(map)||{},f=[];
    rows.slice(0,take).forEach(function(r,i){var k=kindOf(r.categories);if(m[k]&&!r.gold)return;
      var p={i:i,o:i,c:r.gold?'^'+k:k,n:names(r)};if(r.gold)p.g=1;
      f.push({type:'Feature',geometry:{type:'Point',coordinates:[+r.lng,+r.lat]},properties:p});});
    var s=map.getSource('md-pins');if(s)s.setData({type:'FeatureCollection',features:f});
  }
  REDO.set(map,data);
  function want(){
    var ct=map.getContainer(),n=count(ct.clientWidth,0,ct.clientHeight);
    var b=map.getBounds(),W=b.getWest(),S=b.getSouth(),E=b.getEast(),N=b.getNorth(),g=(N-S)/10;
    W=Math.floor(W/g)*g;S=Math.floor(S/g)*g;E=Math.ceil(E/g)*g;N=Math.ceil(N/g)*g;
    var k=[n,W,S,E,N].map(function(v){return typeof v==='number'?v.toFixed(4):v;}).join('|');
    if(k===key)return;key=k;
    spread(W,S,E,N,Math.min(200,n*3)).then(function(rs){
      if(key!==k)return;
      var gs=goldIn(W,S,E,N);if(gs.length){var gi={};gs.forEach(function(g){gi[g.id]=1;});rs=gs.concat(rs.filter(function(r){return !gi[r.id];}));}
      if(skip)rs=rs.filter(function(r){return Math.abs(r.lat-skip[0])>3e-4||Math.abs(r.lng-skip[1])>3e-4;});
      rows=rs;take=Math.min(n,rows.length);goal=n;tops=0;ROWS.set(map,rows);data();}).catch(function(){if(key===k)key='';});
  }
  map.on('idle',function(){
    if(!take||take>=rows.length||tops>=4||!map.getLayer('md-pins'))return;
    var shown=map.queryRenderedFeatures({layers:['md-pins']}).length;
    if(shown>=goal-2)return;
    tops++;take=Math.min(rows.length,take+goal-shown);data();});
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
  GOLDP.then(function(){if(GOLD.rows.length){key='';want();}});
}
/* a shelf switched on draws its own dots: its kind's pins step aside */
function mute(map,kind,yes){var m=MUTE.get(map)||{};m[kind]=!!yes;MUTE.set(map,m);
  var f=REDO.get(map);if(f)f();}
/* explore.js asks before answering a tap, so one touch opens one sheet */
function hit(map,pt){if(!map.getLayer('md-pins'))return false;
  return map.queryRenderedFeatures([[pt.x-12,pt.y-12],[pt.x+12,pt.y+12]],{layers:['md-pins']}).length>0;}
function row(map,i){var r=ROWS.get(map);return r&&r[i];}
window.MDPINS={K:K,gold:GOLD,goldP:GOLDP,goldIn:goldIn,row:row,icon:icon,kindOf:kindOf,cap:cap,count:count,pref:pref,places:places,spread:spread,thin:thin,paint:paint,mute:mute,hit:hit};
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
