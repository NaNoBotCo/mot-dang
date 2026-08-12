"""map_shell.py — the one place on this site where a map is constructed.

WHY THIS EXISTS
---------------
Every map here used to be drawn in Python as an inline SVG: the soi maps, the
merit rounds, the event maps, the plan sketch, and the "which way" panel on
the toilets page. That was a deliberate choice and it bought real things — the
pages print, they work with scripting off, and they make no request to anyone
else's server. It cost one thing, and a reader on r/chiangmai named it: pins
on a cream rectangle. The pins were right, the rings were right, the moat was
right when the moat was in frame, and standing anywhere else it read as a
broken map, because a map with no ground under it is not yet a map.

So the SVG stays and a basemap goes underneath it — not the other way round.
The drawn picture is the fallback: it is what prints, what a reader with no
script gets, and what shows while the tiles are still arriving. When the
basemap is available this module mounts MapLibre over the top of it, in the
same box, at the same centre.

WHY SELF-HOSTED TILES
---------------------
The obvious fix is a raster tile layer pointed at tile.openstreetmap.org. It
is three lines and it would have shipped the same afternoon. It also would
have made this the first page on the site to fetch anything from a third
party, on a site whose front page promises it follows no one around — and it
would have leaned on a donated CDN whose usage policy a growing directory is
built to violate.

Protomaps solves both: one .pmtiles file we host ourselves, fetched in ranges
by the client, no API key, no per-request billing, no rate limit, nobody's
logs but ours. The cost is honesty about the wording: this is first-party,
not zero-party. A page with a map on it now makes a request to our own bucket.
Pages without a map still make none, because none of this loads unless a map
is actually on the page.

CONFIGURATION
-------------
`data/basemap.json`, and its absence is a supported state:

    {"url": "https://tiles.example/cm-cr.pmtiles", "maxzoom": 15}

With no url, `enabled()` is False, nothing is emitted into any page, and every
map surface keeps the SVG it always had. That is what lets this module land
before the tiles exist, and it is what the site falls back to if the bucket
ever goes away.
"""

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parent

# The two centres the whole site defaults to — the same pair md.js and
# toilets.js use, and for the same reason: they are places people give
# directions from, and neither of them requires knowing where the reader is.
CENTERS = {
    "cm": {"lng": 98.9931, "lat": 18.7876, "th": "ประตูท่าแพ", "en": "Tha Phae Gate"},
    "cr": {"lng": 99.8325, "lat": 19.9094, "th": "หอนาฬิกาเชียงราย", "en": "Clock Tower"},
}

# ODbL requires the credit and requires it to stay visible. MapLibre's
# attribution control is configured non-compact and non-dismissible below;
# this is a licence condition, not chrome, and it is not ours to fold away.
ATTRIBUTION = '© <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors (ODbL)'

VENDOR = ("maplibre-gl.css", "maplibre-gl.js", "pmtiles.js")


def config():
    p = ROOT / "data" / "basemap.json"
    if not p.exists():
        return {}
    try:
        return json.loads(p.read_text())
    except (ValueError, OSError):
        return {}


def enabled():
    """True only when there is a tile file to point at AND the vendored
    libraries are actually present. Both halves matter: a page that loads
    MapLibre and then has no tiles to give it is worse than the SVG it
    replaced, and so is a style pointing at a bucket with nothing in it."""
    if not config().get("url"):
        return False
    return all((ROOT / "assets" / "vendor" / f).exists() for f in VENDOR)


def head(depth=0):
    """The tags a page needs before it may mount a map. Emitted only on pages
    that carry one — this is why it takes a depth and not a global flag."""
    if not enabled():
        return ""
    r = "../" * depth
    return (f'<link rel="stylesheet" href="{r}vendor/maplibre-gl.css">'
            f'<script src="{r}vendor/pmtiles.js" defer></script>'
            f'<script src="{r}vendor/maplibre-gl.js" defer></script>'
            f'<script src="{r}map.js" defer></script>')


def mount(map_id, fallback_svg="", *, prov="cm", zoom=14,
          lat=None, lng=None, label="", cls="mdmap", mpu=None):
    """A map surface: the drawn SVG, and the hooks for MapLibre to cover it.

    The SVG goes INSIDE the container rather than beside it. That ordering is
    the whole fallback story — it is what renders first, what prints, what a
    reader with scripting off keeps, and what fills the box during the moment
    the first tiles are in flight. map.js only ever adds a sibling on top.
    """
    c = CENTERS.get(prov) or CENTERS["cm"]
    la = c["lat"] if lat is None else lat
    ln = c["lng"] if lng is None else lng
    attrs = (f'id="{map_id}" class="{cls}" data-mdmap="1" '
             f'data-lat="{la:.5f}" data-lng="{ln:.5f}" data-zoom="{zoom}"')
    # Metres per viewBox unit, for the maps drawn at build time. Those know
    # their own scale in geography but not in pixels — the SVG is laid out at
    # whatever width the column gives it — so the zoom cannot be worked out
    # until the page is on screen. Handing over metres-per-unit lets map.js
    # finish the sum at runtime and keeps the two pictures at one scale. A
    # browser-drawn map passes nothing here and calls MDMAP.retarget instead,
    # because its scale changes every time it redraws.
    if mpu:
        attrs += f' data-mpu="{mpu:.6f}"'
    if label:
        attrs += f' data-label="{label}"'
    return (f'<div {attrs}>'
            f'<div class="mdmap-draw">{fallback_svg}</div>'
            f'</div>')


# --------------------------------------------------------------------- JS

JS = r"""/* map.js — the only map constructor on this site.

   Nothing here asks for a location, on mount or ever. A map that needs to
   know where you are before it will draw is a map that shows a permission
   dialog to somebody who wanted to look at a street, and this site's whole
   position is that the picture comes first and the coordinate is optional.
   Every mount below opens on a named landmark.

   Nothing here mounts above the fold either, or before the box is on screen.
   MapLibre is not small, and a directory page whose listings are the point
   should not spend its first paint on a picture the reader has not scrolled
   to yet. */
(function(){
if(!window.maplibregl||!window.pmtiles)return;
var CFG=window.MDMAP_CFG||{};
if(!CFG.url)return;

/* One protocol registration for the whole page, however many maps are on it.
   Registering twice throws, and the soi pages carry more than one. */
var proto=new pmtiles.Protocol();
maplibregl.addProtocol('pmtiles',proto.tile);

/* Absolute, and resolved against the SITE root rather than the current page.

   Two separate traps, both of which produce a map that quietly never draws:

   1. The protocol handler takes what follows pmtiles:// and hands it straight
      to fetch. It does not resolve anything, so the URL has to arrive whole.
   2. Resolving it against location.href is not enough. A relative tiles path
      is correct only from the site root; from /cm/soi/<road>.html it becomes
      /cm/soi/tiles/... and 404s. That is 460 of the 461 map pages here.

   data-root is on <html>, set by page() to the same "../" prefix every other
   relative link on the page uses, so this lands where the assets actually are
   at whatever depth. An absolute URL — the R2 one, in production — resolves
   to itself and is unaffected by any of this. */
var ROOT=document.documentElement.getAttribute('data-root')||'';
var ABS=new URL(CFG.url,new URL(ROOT||'./',location.href)).href;

function style(){
  return {version:8,glyphs:CFG.glyphs||null,sources:{p:{type:'vector',
    url:'pmtiles://'+ABS,attribution:CFG.attribution||''}},
    layers:CFG.layers||[]};
}

var reg=new WeakMap();

function build(el){
  var draw=el.querySelector('.mdmap-draw');
  var live=document.createElement('div');
  live.className='mdmap-live';
  el.appendChild(live);
  var map=new maplibregl.Map({
    container:live,
    style:style(),
    center:[parseFloat(el.dataset.lng),parseFloat(el.dataset.lat)],
    zoom:parseFloat(el.dataset.zoom)||14,
    /* The credit is a licence condition. Non-compact so it is legible
       rather than a dismissible ⓘ, and the close button is never wired. */
    attributionControl:{compact:false},
    /* No geolocate control. There is exactly one door to the permission
       prompt on this site and it is not a map button — see MDLOC in md.js. */
    dragRotate:false,pitchWithRotate:false,touchPitch:false
  });
  /* Bottom-left, not top-right: the drawing layers put their north arrow in
     the top-right corner and the credit sits bottom-right, so this is the
     one corner nothing else has claimed. No compass — rotation is off. */
  map.addControl(new maplibregl.NavigationControl({showCompass:false}),'bottom-left');
  reg.set(el,map);
  /* A tap on the ground, reported to whichever layer owns this box. MapLibre
     does not fire this after a drag, so panning never moves anybody's
     starting point by accident. */
  map.on('click',function(e){
    el.dispatchEvent(new CustomEvent('mdmap:click',
      {detail:{lat:e.lngLat.lat,lng:e.lngLat.lng}}));
  });
  map.on('load',function(){
    /* A build-time drawing knows its scale in metres per viewBox unit but not
       in pixels. Now that it is laid out, finish the sum: how wide the SVG
       actually got versus how wide its viewBox says it is. */
    if(el.dataset.mpu){
      var svg=el.querySelector('.mdmap-draw svg'),vb=svg&&svg.getAttribute('viewBox');
      var shownW=svg&&svg.getBoundingClientRect().width;
      if(vb&&shownW){
        var vbW=parseFloat(vb.split(/[\s,]+/)[2]);
        if(vbW>0)window.MDMAP.retarget(el,parseFloat(el.dataset.lat),
          parseFloat(el.dataset.lng),parseFloat(el.dataset.mpu)*(vbW/shownW));
      }
    }
    el.classList.add('mdmap-on');
    /* The drawn SVG stays in the DOM — it is what prints, and it is what
       comes back if the tiles ever stop resolving. It is only hidden from
       sight, and only once there is something real underneath. */
    if(draw)draw.setAttribute('aria-hidden','true');
  });
  map.on('error',function(){
    /* Tiles unreachable, bucket moved, offline. Take the live layer away and
       leave the reader exactly what they had before any of this existed. A
       blank grey canvas would be strictly worse than the picture we drew. */
    el.classList.remove('mdmap-on');
    if(draw)draw.removeAttribute('aria-hidden');
    if(live.parentNode)live.parentNode.removeChild(live);
    try{map.remove();}catch(e){}
  });
  return map;
}

/* Mount when the box comes into view, not on load — MapLibre is a megabyte,
   and a directory page whose listings are the point should not spend its
   first paint on a map nobody has scrolled to.

   Two mechanisms, not one, guarded by the same WeakSet so a box can only be
   built once. IntersectionObserver is the efficient path; a plain rect check
   on scroll is the one that actually always works. The observer is not
   reliable enough to be the only trigger — it can be delayed, throttled, or
   in some embedded and headless browsers never fire at all, and when it does
   not fire the symptom is a map that neither loads nor errors. A basemap that
   silently fails to appear is the exact bug this whole module exists to fix,
   so it does not get to depend on one callback firing. */
var seen=new WeakSet();
function inView(el){
  var r=el.getBoundingClientRect();
  if(!r.width&&!r.height)return false;
  var h=window.innerHeight||document.documentElement.clientHeight;
  var w=window.innerWidth||document.documentElement.clientWidth;
  return r.top<h+200&&r.bottom>-200&&r.left<w+200&&r.right>-200;
}
function maybe(el){
  if(seen.has(el)||!inView(el))return;
  seen.add(el);build(el);
}
function sweep(){document.querySelectorAll('[data-mdmap]').forEach(maybe);}

if(window.IntersectionObserver){
  var io=new IntersectionObserver(function(es){
    es.forEach(function(e){
      if(!e.isIntersecting||seen.has(e.target))return;
      seen.add(e.target);io.unobserve(e.target);build(e.target);});
  },{rootMargin:'200px'});
  document.querySelectorAll('[data-mdmap]').forEach(function(el){io.observe(el);});
}
/* The API the drawing layers use. A layer keeps drawing its own SVG exactly
   as it always did; all it has to do to sit on real ground is tell the shell
   where that drawing is centred and how far across it reaches. Nothing here
   requires a layer to know what MapLibre is. */
window.MDMAP={
  /* True once this box has a live basemap under it — the flag a layer checks
     before deciding whether to draw its own cream background. */
  live:function(el){return !!reg.get(el);},
  /* Point the basemap at the same place and the same scale as the drawing
     over it. metresPerCssPx is the drawing's own scale, so the two agree by
     construction rather than by a constant somebody has to keep in sync.

     Web Mercator vs the equirectangular projection the SVG layers use: over
     a box a few hundred metres across at this latitude the two differ by
     well under a pixel, so the pins land where the streets are. */
  retarget:function(el,lat,lng,metresPerCssPx){
    var m=reg.get(el);if(!m)return false;
    var z=Math.log(156543.03392*Math.cos(lat*Math.PI/180)/metresPerCssPx)/Math.LN2;
    m.jumpTo({center:[lng,lat],zoom:Math.max(1,Math.min(22,z))});
    return true;
  }
};

/* The backstop. Passive so it never costs a frame of scroll. */
addEventListener('scroll',sweep,{passive:true});
addEventListener('resize',sweep,{passive:true});
setTimeout(sweep,0);

/* And the one that matters on a slow connection. A map box has no height
   until the layer that owns it has drawn into it, and those layers fetch
   their data first — so at load every container measures zero, counts as out
   of view, and is correctly skipped. If the box is already on screen when
   the data lands, no scroll ever follows to try again, and the basemap under
   an already-visible map would never mount at all. Watching for the box to
   gain a size catches exactly that, whichever layer fills it and however
   long its fetch took. */
if(window.ResizeObserver){
  var ro=new ResizeObserver(function(es){
    es.forEach(function(e){
      if(seen.has(e.target))return;
      maybe(e.target);
      if(seen.has(e.target))ro.unobserve(e.target);});
  });
  document.querySelectorAll('[data-mdmap]').forEach(function(el){ro.observe(el);});
}
})();
"""

CSS = """/* The map box. The drawn SVG and the live tiles occupy the same square;
   the live one is stacked over it and only becomes visible once it has
   actually loaded, so there is never a moment of empty grey. */
.mdmap{position:relative;margin:.9rem 0 .2rem}
.mdmap-draw{position:relative;z-index:1}
/* Descendant selector, deliberately: MapLibre's own stylesheet is loaded
   after this one and sets .maplibregl-map{position:relative}. At equal
   specificity that wins, the live layer stops being absolutely positioned,
   inset:0 no longer applies, and the box collapses to zero height — tiles
   fetch, the map "loads", and nothing is ever visible. Two classes beat one. */
.mdmap .mdmap-live{position:absolute;inset:0;z-index:2;opacity:0;
  transition:opacity .35s ease;border-radius:14px;overflow:hidden}
.mdmap.mdmap-on .mdmap-live{opacity:1}
/* Once there is real ground, the drawing goes back ON TOP of it — pins over
   streets is the entire point, and a basemap that buries the pins has just
   traded one broken map for another. The drawing stops eating pointer events
   so the map can be panned, except on the pins themselves, which still do
   what they always did. */
.mdmap.mdmap-on .mdmap-draw{z-index:3;pointer-events:none}
.mdmap.mdmap-on .mdmap-draw .loopin{pointer-events:auto}
/* The drawn cream background and its border are the "no ground" state. With
   tiles underneath they are exactly what must not be painted. */
.mdmap.mdmap-on .mdmap-bg{display:none}
.mdmap .maplibregl-ctrl-attrib{font-size:11px;background:rgba(255,253,248,.88)}
/* Never let the credit be folded away: ODbL asks for it to be visible, and a
   collapsed ⓘ on a phone is not visible. */
.mdmap .maplibregl-ctrl-attrib-button{display:none!important}
.mdmap .maplibregl-ctrl-attrib.maplibregl-compact-show .maplibregl-ctrl-attrib-inner{
  display:block!important}
@media print{.mdmap-live{display:none!important}
  .mdmap-draw{position:static}}
@media (prefers-reduced-motion:reduce){.mdmap-live{transition:none}}
"""


def emit(g):
    """Write map.js and the runtime config. Silent no-op when disabled, which
    is the state the site ships in until a .pmtiles file actually exists."""
    docs = g["DOCS"]
    if not enabled():
        return {"enabled": False}
    cfg = config()
    style_path = ROOT / "data" / "basemap_style.json"
    layers = []
    if style_path.exists():
        try:
            layers = json.loads(style_path.read_text()).get("layers", [])
        except (ValueError, OSError):
            layers = []
    # Labels are symbol layers, and MapLibre cannot draw one without a glyph
    # URL to fetch the font PBFs from. The usual answer is Protomaps' public
    # font host — which is exactly the third-party request self-hosting the
    # tiles was meant to avoid, and it would leak every map view to a server
    # that is not ours. So: no self-hosted glyphs, no labels. An unlabelled
    # street grid under our own pins is still an enormous improvement on
    # cream, and the pins carry their own names already.
    glyphs = cfg.get("glyphs")
    dropped = 0
    if not glyphs:
        keep = [ly for ly in layers if ly.get("type") != "symbol"]
        dropped = len(layers) - len(keep)
        layers = keep
    runtime = {"url": cfg["url"], "attribution": ATTRIBUTION,
               "glyphs": glyphs, "layers": layers}
    (docs / "map.js").write_text(
        "window.MDMAP_CFG=" + json.dumps(runtime, ensure_ascii=False,
                                         separators=(",", ":")) + ";\n" + JS)
    vend = docs / "vendor"
    vend.mkdir(exist_ok=True)
    for f in VENDOR:
        src = ROOT / "assets" / "vendor" / f
        if src.exists():
            (vend / f).write_bytes(src.read_bytes())
    return {"enabled": True, "layers": len(layers), "url": cfg["url"],
            "labels": bool(glyphs), "dropped_label_layers": dropped}
