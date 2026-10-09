"""satellite_layer.py — the photograph under the map, and the door to it.

WHAT THIS IS
------------
The display half of `importers/build_satellite.py`. That importer binds
Sentinel-2 true colour over the two provinces into one raster .pmtiles in our
own bucket; this module draws it, under the labels, behind a [layers] control,
and prints the licence wherever it shows.

It is deliberately shaped like `geography_layer.py`'s doi.js half: it draws
INTO the shared map through `MDMAP.ready()`, the same door explore.js and
doi.js use. It never constructs a map. `map_shell.py` stays the only module
that constructs one, and `data/basemap.json` stays the only place a tile
archive is configured — this module reads the `satellite` block out of it
through `map_shell.config()` and adds no second source of truth.

ONE WIRING NOTE, SO NOBODY LOOKS FOR A BUG THAT IS NOT THERE. `map_shell.emit()`
puts the basemap url, the glyphs and the terrain block into `window.MDMAP_CFG`.
It knows nothing about satellite, and this module does not edit it to find
out: `emit()` below writes its own `window.MDSAT_CFG` prelude at the top of
satellite.js, exactly the shape map.js carries its own. When map_shell is not
being held open by another session, the tidier form is one key in that
module's `runtime` dict — `"satellite": cfg.get("satellite")` — and this
file's `_cfg_js()` can then be deleted. Either way the CONFIGURATION lives in
data/basemap.json and nowhere else, which is the rule that matters.

WHAT IT CAN AND CANNOT SHOW, AND WHY THE TOGGLE SAYS SO
--------------------------------------------------------
10 metres a pixel. A z14 tile at this latitude is 9.03 m/px, so the archive
is at its own grain there. What is legible: the moat, the Ping, reservoirs,
fields against forest, cleared ground, the shape and extent of a village,
roofs in bulk. What is NOT there, at all: one roof at a time, a shop sign, a
soi's shophouses, a temple's roofline, a person, a car. A satellite button
that does not say its resolution is promising Google's picture and handing
over ESA's, and the reader finds out by squinting at the old city. So the
control carries the sentence, in both languages, next to the toggle rather
than in a footnote.

THE CONTRAST PROBLEM, AND HOW IT IS SOLVED
-------------------------------------------
This is the real work in the file. The basemap's ink is tuned for cream
paper: casings are #B39058 mid-brown, road labels #8A7761, boundaries
#A38B62, and every label's halo is a 1.4–1.6 px cream. Every one of those
disappears over a photograph — the brown vanishes into forest and dry paddy,
and a 1.4 px halo is not enough separation against a picture with texture at
every scale.

Four moves, and one refusal:

  1. ORDER. The raster is inserted immediately before `water`, which puts it
     ABOVE the opaque paper fills (earth, landcover, landuse-green,
     landuse-built) and BELOW every line and every symbol. Roads and labels
     are never covered, at any zoom, by construction rather than by z-index
     luck. `water` and `buildings` are the two fills that would sit on top of
     it, so they are hidden while it is on — the photograph already shows the
     water, and a tan fill over roofs the picture cannot resolve is a claim
     dressed as a drawing. `water-line` stays: the moat and the Ping keep
     their drawn outline, which is what this city navigates by and which is
     two pixels wide at 10 m.

  2. THE PICTURE SITS BACK. `raster-brightness-max` 0.92 and
     `raster-saturation` -0.12. Not a scrim: a translucent grey rectangle
     over the whole map greys the photograph everywhere, including the nine
     tenths of it with nothing written on it. Pulling the imagery's top end
     down by 8% costs almost nothing to look at and buys the halos a fighting
     chance everywhere at once.

  3. THE INK GOES DARK, AND STAYS LIGHT WHERE IT WAS LIGHT. Road casings go
     to #2A1E16 at 0.6 opacity — a dark casing under the near-white road fill
     is how a road reads on any photograph, and #FFFDF8 / #FFFCF4 already sit
     on the light side of anything the ground can do. Road labels go from
     #8A7761 to #3E3428. Boundaries go the other way, to a pale #FFF3D8,
     because a boundary is drawn over hillside more often than over field.

  4. THE HALOS THICKEN. place-labels 1.6 → 2.4, road-labels 1.4 → 2.2, with
     a little blur. Dark text in a thick cream halo is legible over both dry
     stubble and closed canopy; light text in a dark halo is not, because
     this palette's text colours are the dark ones.

  Refused: recolouring the labels themselves to white. It would read as a
  different map rather than the same map with a photograph under it, and the
  moment the reader toggles back the type would change under them.

Every value above is SAVED before it is changed and restored on toggle-off,
so the drawn map that comes back is the drawn map that was there.

THE LICENCE, AND WHERE IT HAS TO APPEAR
----------------------------------------
Sentinel-2 is CC-BY-SA 3.0 IGO. The credit rides in three places, because a
map surface leaves by three doors:

  · the raster source's `attribution`, so MapLibre's own control carries it
    while the layer is on — the same non-compact, non-dismissible control the
    ODbL credit already uses;
  · a line under the control, in both languages, with the scene dates, so it
    is legible with the attribution control collapsed or scripting partial;
  · INTO THE PIXELS of the "send this view" picture. A picture travels with
    no page around it — the whole reason `map_ground.credit_mark()` exists —
    and the ODbL line is already drawn into that canvas by explore.js and
    here.js. The permanent form of this is one line in each of those two
    handlers, calling `MDSAT.stamp(canvas)`. Until those files are free to
    edit, `arm()` installs the same call by wrapping `toBlob` for exactly as
    long as the imagery is on, and takes the wrap off again when it goes off.
    Scoped to the moment the licence actually bites, and it names its own
    replacement rather than becoming the permanent arrangement by default.

ABSENCE IS A SUPPORTED STATE
-----------------------------
No `satellite` block in data/basemap.json, an empty url, a url pointing at an
archive that is not there — each one leaves the control unrendered and every
map exactly as it was. `enabled()` gates the build side; the preflight in the
JS gates the reader's side, with the same 128-byte ranged read doi.js makes,
for the same reason: a declared archive that 404s once shipped a bar of dead
buttons over a relief that drew nothing (2026-08-27). A button that cannot
act is worse than no button.
"""

import json
import zlib
from pathlib import Path

import map_shell
import sat_glyphs

ROOT = Path(__file__).resolve().parent
SCENES = ROOT / "data" / "satellite_scenes.json"

# The credit, in the two forms it has to take. The HTML one goes to MapLibre's
# attribution control and to the line under the toggle; the plain one is what
# gets drawn into a picture's pixels, where there is no such thing as a link.
ATTRIBUTION_HTML = (
    'ภาพดาวเทียม · imagery: '
    '<a href="https://dataspace.copernicus.eu/" rel="noopener">Copernicus '
    'Sentinel-2</a>, ESA — '
    '<a href="https://creativecommons.org/licenses/by-sa/3.0/igo/" '
    'rel="noopener">CC BY-SA 3.0 IGO</a>')
ATTRIBUTION_TEXT = ("Contains modified Copernicus Sentinel data, "
                    "processed by ESA — CC BY-SA 3.0 IGO")


def config():
    """The satellite block out of data/basemap.json. {} when absent."""
    return map_shell.config().get("satellite") or {}


def scenes():
    """What the importer found. {} when it has not been run."""
    try:
        return json.loads(SCENES.read_text())
    except (OSError, ValueError):
        return {}


def enabled():
    """True only when there is an archive url AND the shared basemap is live.

    Both halves matter for the same reason map_shell.enabled() checks two:
    a raster layer with no basemap under it has no map to be a layer of, and
    a declared url with nothing behind it is a page of dead controls.
    """
    return bool(config().get("url")) and map_shell.enabled()


def dates():
    """The capture dates in the mosaic, oldest first — printed beside the
    credit. A picture of the ground is a picture of a MORNING, and a mosaic
    is a picture of several; saying which ones is the same discipline the
    food marks keep by printing their edition year."""
    d = scenes()
    out = sorted({s["date"] for sq in d.get("squares", [])
                  for s in sq.get("scenes", [])})
    return out


def version():
    """Content hash for the `?v=` on satellite.css and satellite.js.

    Same reasoning as map_shell.version(), and the same scar behind it: these
    are served under names that never change with a week-long cache, and a
    reader holding yesterday's copy against today's page is how a working
    map comes up empty. A production outage here was caused by exactly one
    map surface shipping without a `?v=`. The hash covers the runtime config
    as well as the code, because a changed archive url changes what the
    script DOES as surely as an edited line does.
    """
    payload = JS + CSS + json.dumps(
        {"cfg": config(), "read": scenes().get("read"), "dates": dates()},
        sort_keys=True, ensure_ascii=False)
    return "%08x" % (zlib.crc32(payload.encode("utf-8")) & 0xFFFFFFFF)


def head(depth=0):
    """The two tags a page needs. Emitted only where the control is."""
    if not enabled():
        return ""
    r = "../" * depth
    v = version()
    return (f'<link rel="stylesheet" href="{r}satellite.css">'
            f'<script src="{r}satellite.js" defer></script>')


def control(map_id, bi, esc, bi_text):
    """The [layers] bar for one map box.

    Rendered hidden. The JS un-hides it only after the archive has answered
    with its own PMTiles magic, so a reader never sees a switch that cannot
    throw. `bi` renders a Thai/English pair the way the rest of the site
    does; nothing here writes copy in one language only.
    """
    if not enabled():
        return ""
    ds = dates()
    when = ""
    if ds:
        when = (bi("ถ่ายเมื่อ " + " · ".join(ds[:4]) + ("…" if len(ds) > 4 else ""),
                   "captured " + " · ".join(ds[:4]) + ("…" if len(ds) > 4 else "")))
    return (
        f'<div class="satbar" data-mdsat-for="{esc(map_id)}" hidden>'
        f'<span class="satbar-h">{sat_glyphs.icon("i-layers", 20)}'
        f'{bi("ชั้นแผนที่", "layers")}</span>'
        f'<button type="button" class="satbtn" data-mdsat-mode="map" '
        f'aria-pressed="true">{bi("แผนที่วาด", "drawn map")}</button>'
        f'<button type="button" class="satbtn satbtn-img" data-mdsat-mode="sat" '
        f'aria-pressed="false">{sat_glyphs.icon("i-satellite", 18)}'
        f'{bi("ภาพถ่ายดาวเทียม", "satellite")}</button>'
        f'<p class="satnote">'
        f'{bi("๑ จุดภาพ = ๑๐ เมตร เห็นคูเมือง แม่น้ำปิง อ่างเก็บน้ำ ทุ่งนา ป่า และหลังคารวม ๆ กัน ไม่เห็นหลังคาทีละหลัง ป้ายร้าน รถ หรือคน", "One pixel is 10 metres. The moat, the Ping, reservoirs, fields, forest, roofs in bulk. Not one roof at a time, not a shop sign, not a car, not a person.")}'
        f'</p>'
        f'<p class="satcredit" hidden>{ATTRIBUTION_HTML}'
        + (f' · {when}' if when else '') + '</p>'
        f'</div>')


def sprite():
    """The two marks, for a page that carries this control. Kept separate
    from build.ICON_SPRITE and glyphs.SPRITE so a page pays only for what it
    draws — and so nothing here has to edit either of them."""
    return sat_glyphs.SPRITE if enabled() else ""


# --------------------------------------------------------------------- CSS
CSS = """/* satellite.css — the [layers] control. */
.satbar{display:flex;gap:.5rem;align-items:center;flex-wrap:wrap;
  margin:.55rem 0 .2rem}
.satbar-h{display:inline-flex;align-items:center;gap:.3rem;font-weight:700;
  color:var(--ink-soft,#6B5A48);font-size:.95rem}
.satbtn{min-height:44px;padding:.4rem .85rem;border-radius:.6rem;font:inherit;
  font-weight:700;border:2px solid var(--ant,#C2401C);background:#fff;
  color:var(--ant-dark,#8E2F14);cursor:pointer;
  display:inline-flex;align-items:center;gap:.35rem}
.satbtn:hover{background:var(--row-hover,#FFF3EC)}
.satbtn[aria-pressed="true"]{background:var(--ant,#C2401C);color:#fff}
.satbtn[aria-pressed="true"] .rowicon{color:#fff}
/* The sentence about what 10 m can and cannot show is part of the control,
   not a footnote under it: it has to be read before the toggle is pressed,
   so it takes the whole row and does not shrink away on a phone. */
.satnote{flex:1 0 100%;margin:.15rem 0 0;font-size:.86rem;line-height:1.45;
  color:var(--ink-soft,#6B5A48)}
.satcredit{flex:1 0 100%;margin:.1rem 0 0;font-size:.8rem;
  color:var(--ink-soft,#6B5A48)}
.satcredit a{color:inherit}
@media (prefers-reduced-motion:reduce){.satbtn{transition:none}}
"""


# ---------------------------------------------------------------------- JS
JS = r"""/* satellite.js — the photograph under the map, under the labels.
   Runs only where a [layers] control was rendered, and only once map.js has
   mounted the shared basemap. Draws INTO that map through MDMAP.ready();
   never constructs one. */
(function(){
var C=window.MDSAT_CFG||{};
/* Absent or empty url is the documented off switch, and it is checked before
   anything else so an unconfigured page costs one property read. */
if(!C.url||!window.MDMAP)return;
var bars=[].slice.call(document.querySelectorAll('[data-mdsat-for]'));
if(!bars.length)return;

/* Resolved against the SITE root, exactly as map.js and doi.js resolve
   theirs — the pmtiles protocol handler does not resolve anything, and a
   relative path is correct only from the root. */
var ROOT=document.documentElement.getAttribute('data-root')||'';
var ABS=new URL(C.url,new URL(ROOT||'./',location.href)).href;

var SRC='mdsat-src',LYR='mdsat-img';
/* Insert before the first of these that exists. This is the ordering rule:
   above the paper fills, below every line and every label. If a retuned
   style renames all of them the raster lands on top, which is visible and
   fixable rather than silently absent — the same failure mode doi.js chose
   for its hillshade anchor. */
var UNDER=['water','water-line','buildings','roads-casing','roads-minor',
           'roads-major','roads-highway','boundaries','place-labels',
           'road-labels'];
/* Fills that would sit ON TOP of the raster and hide it. */
var HIDE=['water','buildings'];

/* Every paint value this layer changes, and what it changes it to. Read the
   docstring in satellite_layer.py for why each one. The ORIGINALS are read
   off the live map before anything is set, so toggling off restores the map
   that was there rather than a guess at what it looked like. */
var INK=[
  ['roads-casing','line-color','#2A1E16'],
  ['roads-casing','line-opacity',0.6],
  ['road-labels','text-color','#3E3428'],
  ['road-labels','text-halo-width',2.2],
  ['road-labels','text-halo-blur',0.4],
  ['place-labels','text-halo-width',2.4],
  ['place-labels','text-halo-blur',0.4],
  ['boundaries','line-color','#FFF3D8'],
  ['boundaries','line-opacity',0.8]
];

function nearestLayer(map){
  for(var i=0;i<UNDER.length;i++)if(map.getLayer(UNDER[i]))return UNDER[i];
  return undefined;
}

/* ---- the credit, drawn INTO a picture -------------------------------------
   A picture travels with no page around it, so the credit travels in the
   pixels. Same shape as map_ground.credit_mark(): a plate in the corner,
   sized to the picture, so it survives a screenshot and a repost. */
function stamp(canvas){
  var x;
  try{x=canvas.getContext('2d');}catch(e){return false;}
  if(!x)return false;
  var w=canvas.width,h=canvas.height;
  var s=Math.max(10,Math.round(Math.min(w,h)*0.026));
  x.save();
  x.font='500 '+s+'px system-ui,sans-serif';
  var t=%TEXT%;
  var tw=x.measureText(t).width,pad=Math.max(3,Math.round(Math.min(w,h)*0.008));
  /* Bottom LEFT: explore.js already writes its own band along the bottom and
     the ODbL line sits at the left of it, so the left edge of the picture
     above that band is the one place nothing else is drawn. */
  var bx=pad,by=h-Math.round(s*3.2)-pad;
  x.fillStyle='rgba(252,249,242,0.92)';
  x.fillRect(bx,by,tw+2*pad,s+2*pad);
  x.fillStyle='#6B5A48';
  x.fillText(t,bx+pad,by+pad+s*0.82);
  x.restore();
  return true;
}

/* Installed only while the imagery is on, which is exactly when the licence
   bites, and taken off again when it goes off.

   THE PERMANENT FORM OF THIS IS ONE LINE in explore.js's and here.js's
   share handlers — `if(window.MDSAT)MDSAT.stamp(c);` right before the
   toBlob call — and MDSAT.stamp is exported below so that line can be added
   the moment those files are free. Until then this wrap does the same job
   without reaching into a file somebody else is holding. It restores only
   its own wrap, so a later wrapper is never clobbered. */
var _toBlob=null;
function wrapPicture(){
  if(_toBlob||!window.HTMLCanvasElement)return;
  _toBlob=HTMLCanvasElement.prototype.toBlob;
  var mine=function(cb,type,q){
    /* The map's own GL canvas has no 2d context and getContext throws or
       returns null there — stamp() answers false and nothing happens. Small
       canvases are icons and swatches, not pictures of a map. */
    try{if(this.width>=320&&this.height>=320)stamp(this);}catch(e){}
    return _toBlob.call(this,cb,type,q);
  };
  mine.__mdsat=1;
  HTMLCanvasElement.prototype.toBlob=mine;
}
function unwrapPicture(){
  if(!_toBlob)return;
  if(HTMLCanvasElement.prototype.toBlob&&
     HTMLCanvasElement.prototype.toBlob.__mdsat)
    HTMLCanvasElement.prototype.toBlob=_toBlob;
  _toBlob=null;
}

function wire(bar){
  var box=document.getElementById(bar.getAttribute('data-mdsat-for'));
  if(!box)return;
  var credit=bar.querySelector('.satcredit');
  var btns=[].slice.call(bar.querySelectorAll('[data-mdsat-mode]'));

  MDMAP.ready(box,function(map){
    var saved=null,on=false;

    function arm(){
      if(!map.getSource(SRC)){
        map.addSource(SRC,{type:'raster',url:'pmtiles://'+ABS,tileSize:256,
          minzoom:C.minzoom||7,maxzoom:C.maxzoom||13,
          /* The licence condition, on the source, so MapLibre's own
             non-compact attribution control carries it for as long as the
             layer is in the style. */
          attribution:C.attribution||''});
        map.addLayer({id:LYR,type:'raster',source:SRC,
          layout:{visibility:'none'},
          paint:{'raster-opacity':1,'raster-fade-duration':180,
            /* The picture sits back a touch so the ink over it reads —
               8% off the top end and a little saturation, rather than a
               grey scrim over a photograph that is mostly unlabelled. */
            'raster-brightness-max':0.92,'raster-saturation':-0.12}},
          nearestLayer(map));
      }
      bar.hidden=false;
    }

    function readOriginals(){
      var o={paint:[],vis:[]};
      INK.forEach(function(t){
        if(!map.getLayer(t[0]))return;
        var v;
        try{v=map.getPaintProperty(t[0],t[1]);}catch(e){v=undefined;}
        o.paint.push([t[0],t[1],v]);
      });
      HIDE.forEach(function(id){
        if(!map.getLayer(id))return;
        var v='visible';
        try{v=map.getLayoutProperty(id,'visibility')||'visible';}catch(e){}
        o.vis.push([id,v]);
      });
      return o;
    }

    function set(want){
      if(want===on)return;
      on=want;
      if(on){
        if(!saved)saved=readOriginals();
        INK.forEach(function(t){
          if(map.getLayer(t[0]))map.setPaintProperty(t[0],t[1],t[2]);});
        HIDE.forEach(function(id){
          if(map.getLayer(id))map.setLayoutProperty(id,'visibility','none');});
        map.setLayoutProperty(LYR,'visibility','visible');
        wrapPicture();
      }else{
        map.setLayoutProperty(LYR,'visibility','none');
        if(saved){
          saved.paint.forEach(function(t){
            if(map.getLayer(t[0]))map.setPaintProperty(t[0],t[1],t[2]);});
          saved.vis.forEach(function(t){
            if(map.getLayer(t[0]))map.setLayoutProperty(t[0],'visibility',t[1]);});
        }
        unwrapPicture();
      }
      if(credit)credit.hidden=!on;
      btns.forEach(function(b){
        b.setAttribute('aria-pressed',
          (b.getAttribute('data-mdsat-mode')==='sat')===on?'true':'false');});
      box.classList.toggle('mdsat-on',on);
    }

    btns.forEach(function(b){b.addEventListener('click',function(){
      set(b.getAttribute('data-mdsat-mode')==='sat');});});

    /* NOTHING ABOVE RUNS UNTIL THE ARCHIVE ANSWERS. A declared archive can
       still be absent where it counts — not uploaded, wrong path, symlink
       gone — while addSource succeeds and every tile request quietly 404s.
       That shipped once on the terrain layer (2026-08-27): a bar of controls
       over a relief that drew nothing. One 128-byte ranged read settles it:
       a PMTiles file opens with its own name. Same read the pmtiles client
       is about to make anyway on the days it answers; on the days it does
       not, it is the ONLY request, in place of a screenful of failures. */
    fetch(ABS,{headers:{Range:'bytes=0-127'}}).then(function(r){
      if(!r.ok)throw 0;
      /* Our worker answers ranges with 206, so the body IS the 128 bytes.
         A host ignoring Range answers 200 with the whole archive behind it —
         never arrayBuffer() that; read one chunk and hang up. */
      if(r.status===206)return r.arrayBuffer().then(function(a){
        return new Uint8Array(a);});
      if(!r.body)throw 0;
      var rd=r.body.getReader(),got=[];
      function pull(){return rd.read().then(function(c){
        if(c.value)for(var i=0;i<c.value.length&&got.length<7;i++)got.push(c.value[i]);
        if(got.length>=7||c.done){try{rd.cancel()}catch(e){}return got;}
        return pull();});}
      return pull();
    }).then(function(b){
      var m='';for(var i=0;i<7&&i<b.length;i++)m+=String.fromCharCode(b[i]);
      if(m!=='PMTiles')throw 0;
      arm();
    }).catch(function(e){/* no photograph today; the drawn map stands */});
  });
}

bars.forEach(wire);

/* The hook the share handlers should call once they are free to take a line:
   explore.js and here.js both build their picture on a 2d canvas and write
   the ODbL credit into it; `MDSAT.stamp(c)` puts the ESA one in beside it. */
window.MDSAT={stamp:stamp,on:function(){return !!_toBlob;}};
})();
"""


def _cfg_js():
    """The prelude satellite.js carries its own config in.

    See the module docstring: map_shell.emit() owns MDMAP_CFG and is not
    being edited from here, so this script carries its own the same way
    map.js does. The VALUES all come from data/basemap.json — there is still
    exactly one place a tile archive is configured.
    """
    cfg = config()
    runtime = {
        "url": cfg.get("url"),
        "minzoom": cfg.get("minzoom", 7),
        "maxzoom": cfg.get("maxzoom", 13),
        "attribution": ATTRIBUTION_HTML,
        "licence": cfg.get("licence") or "CC BY-SA 3.0 IGO",
        "dates": dates(),
    }
    return ("window.MDSAT_CFG=" + json.dumps(runtime, ensure_ascii=False,
                                             separators=(",", ":")) + ";\n")


def emit(g):
    """Write satellite.css and satellite.js. Silent no-op when disabled,
    which is the state the site ships in until the archive exists."""
    docs = g["DOCS"]
    if not enabled():
        return {"enabled": False}
    (docs / "satellite.css").write_text(CSS)
    (docs / "satellite.js").write_text(
        _cfg_js() + JS.replace("%TEXT%",
                               json.dumps(ATTRIBUTION_TEXT, ensure_ascii=False)))
    # What the page prints and what a reader can check the mosaic against.
    # Copied each run like every other data file, because docs/ is wiped.
    n = 0
    doc = scenes()
    if doc:
        (docs / "data").mkdir(exist_ok=True)
        (docs / "data" / "satellite_scenes.json").write_text(
            json.dumps(doc, ensure_ascii=False, indent=1))
        n = sum(len(sq.get("scenes", [])) for sq in doc.get("squares", []))
    return {"enabled": True, "url": config().get("url"),
            "maxzoom": config().get("maxzoom", 13),
            "scenes": n, "dates": dates(), "v": version()}
