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
import zlib
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

# The fence, and the floor. cm-cr.pmtiles is extracted to 97.3,17.0,100.6,20.5
# and holds the two provinces and nothing else, so a camera outside it shows
# blank paper — which reads to a reader as a map that has broken rather than a
# map that was never asked to go there. These are that extract with a margin
# of about half a degree, in MapLibre's [[W,S],[E,N]] order, and a zoom floor
# that stops the pinch-out that ends on an empty planet. Overridable from
# data/basemap.json for the day a third province arrives.
BOUNDS = [[96.9, 16.6], [101.0, 20.9]]
MIN_ZOOM = 7.2

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


def version():
    """A content hash of exactly what map.js will contain.

    WHY THIS EXISTS, and it cost a real bug: map.js is served with a week-long
    cache and its name never changes, so a reader who had opened any map page
    in the previous seven days kept their old copy — while the HTML around it
    was fresh. Found on a phone: the page had this module's newest API called
    from explore.js and an old map.js without it, so the call threw and the
    explore map came up with no dots, no chips and no share button, on a site
    where every other file was correct. `md.js` and `live.js` have carried a
    `?v=` since they were written; map.js was the one script that did not.

    The hash covers the runtime config as well as the code, because a changed
    tile URL or a retuned style layer changes what this script *does* just as
    surely as an edited line does. Same crc32 shape as build.py's `_asset_v`,
    kept here rather than imported so this module still stands alone.
    """
    cfg = config()
    payload = JS + json.dumps(
        {"url": cfg.get("url"), "glyphs": cfg.get("glyphs"),
         "bounds": cfg.get("bounds") or BOUNDS,
         "minZoom": cfg.get("minZoom") or MIN_ZOOM,
         "terrain": cfg.get("terrain"),
         "style": _style_layers_raw()},
        sort_keys=True, ensure_ascii=False)
    return "%08x" % (zlib.crc32(payload.encode("utf-8")) & 0xFFFFFFFF)


def _style_layers_raw():
    p = ROOT / "data" / "basemap_style.json"
    try:
        return json.loads(p.read_text()).get("layers", [])
    except (OSError, ValueError):
        return []


def head(depth=0):
    """The tags a page needs before it may mount a map. Emitted only on pages
    that carry one — this is why it takes a depth and not a global flag."""
    if not enabled():
        return ""
    r = "../" * depth
    v = version()
    # The vendored libraries are pinned files that only change when they are
    # deliberately replaced, so they keep plain names; map.js is ours and
    # changes whenever this module or the basemap config does.
    return (f'<link rel="stylesheet" href="{r}vendor/maplibre-gl.css">'
            f'<script src="{r}vendor/pmtiles.js" defer></script>'
            f'<script src="{r}vendor/maplibre-gl.js" defer></script>'
            f'<script src="{r}map.js?v={v}" defer></script>')


def mount(map_id, fallback_svg="", *, prov="cm", zoom=14,
          lat=None, lng=None, label="", cls="mdmap", mpu=None, full=False):
    """A map surface: the drawn SVG, and the hooks for MapLibre to cover it.

    The SVG goes INSIDE the container rather than beside it. That ordering is
    the whole fallback story — it is what renders first, what prints, what a
    reader with scripting off keeps, and what fills the box during the moment
    the first tiles are in flight. map.js only ever adds a sibling on top.

    ONE THING THE DRAWING OWES THE SHELL. Once a basemap is live the drawing
    travels with the ground, zoom included, so every shape in it grows. That
    is right for anything measured in metres — range rings, the moat, a route,
    a scale bar's own line — and wrong for anything that is a symbol: a pin
    stands over one doorway and a label is meant to be read, and neither wants
    to be four times the size at z+2. Tag those with

        data-mdpin="x,y"      (x,y in viewBox units: the point it pivots on)

    and map.js holds them at the size they were drawn. The attribute may go on
    the shape itself or on a <g> wrapping a shape and its label. map.js owns
    the `transform` attribute of whatever carries it, so a mark that already
    needs a transform of its own gets a wrapper. Tag nothing and the picture
    still works — it simply zooms as a whole, which is the honest default.

    A third kind is not on the ground at all — a north arrow, a scale bar,
    anything belonging to the frame rather than the city. Tag those

        data-mdfix="1"        (held where AND as it was drawn)

    and they stay in their corner however far the reader pans. One thing to
    know before reaching for it: a drawn scale bar is only true at the zoom
    it was drawn at, so give it class="mdmap-scale" as well and the shell
    hides it whenever the reader has zoomed away from that. Pinning a bar
    without that trades a wandering bar for a wrong one.
    """
    c = CENTERS.get(prov) or CENTERS["cm"]
    la = c["lat"] if lat is None else lat
    ln = c["lng"] if lng is None else lng
    attrs = (f'id="{map_id}" class="{cls}" data-mdmap="1" '
             f'data-lat="{la:.5f}" data-lng="{ln:.5f}" data-zoom="{zoom}"')
    # A map that IS the page, rather than a picture inside an article. Two
    # fingers is the right bargain for a band a reader is scrolling past; on a
    # page whose whole purpose is the map it is an obstacle, so one finger
    # pans there and the page keeps almost nothing to scroll.
    if full:
        attrs += ' data-mdfull="1"'
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

/* The glyph URL has the same site-root problem as the tiles and one extra
   twist: it is a TEMPLATE. {fontstack} and {range} are placeholders MapLibre
   substitutes verbatim when it asks for a font, and running the whole string
   through URL() percent-encodes the braces into %7B — which fetches a file
   nobody has ever written and leaves every map on the site unlabelled, with
   no error to show for it. So only the part before the first brace is
   resolved, and the template tail is put back untouched. An absolute URL
   still resolves to itself, so the rollback keeps working. */
var GLYPHS=(function(){
  var g=CFG.glyphs;if(!g)return null;
  var i=g.indexOf('{');
  if(i<0)return new URL(g,new URL(ROOT||'./',location.href)).href;
  return new URL(g.slice(0,i),new URL(ROOT||'./',location.href)).href+g.slice(i);
})();

function style(){
  return {version:8,glyphs:GLYPHS,sources:{p:{type:'vector',
    url:'pmtiles://'+ABS,attribution:CFG.attribution||''}},
    layers:CFG.layers||[]};
}

var reg=new WeakMap();
/* Per-box: the function that re-fixes the drawing to the ground. Kept apart
   from reg so live() and retarget() keep reading exactly what they read. */
var anch=new WeakMap();

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
    dragRotate:false,pitchWithRotate:false,touchPitch:false,
    /* ---- WHOSE GESTURE IS IT -------------------------------------------
       Nearly everyone here is holding a phone, and a map that pans on one
       finger takes the page's scroll away from them: a thumb that lands on
       the map band mid-page stops the page and drags Chiang Mai instead.
       The reader did not ask to move the map; they asked to keep reading.
       Cooperative gestures give the map two fingers and give the page back
       its one, and say so on screen in the reader's own language the first
       time a single finger tries. Same bargain on a mouse: the wheel scrolls
       the page, ctrl+wheel zooms the map.
       This is why the expand control below matters — two fingers are the
       right default in a band inside an article, and full-screen is where a
       reader who came to look at the map gets everything back. */
    cooperativeGestures:!el.dataset.mdfull,
    /* Only on the map that IS the page. Keeping the drawing buffer is what
       lets that page hand the reader a picture of what they are looking at —
       without it the canvas reads back empty — and it costs memory on every
       map that will never be asked for one, which on a mid-range Android is
       not a cost to pay on twelve thousand place pages. */
    preserveDrawingBuffer:!!el.dataset.mdfull,
    /* ---- RAILS ---------------------------------------------------------
       The archive holds Chiang Mai and Chiang Rai and nothing else, so
       every camera outside it shows blank paper that reads as a broken map.
       maxBounds is the two provinces with a margin; minZoom stops the
       zoom-out that ends in an empty planet. A reader cannot get lost
       somewhere we have nothing to show them. */
    maxBounds:CFG.bounds||[[96.9,16.6],[101.0,20.9]],
    minZoom:CFG.minZoom||7.2,
    /* The gesture prompt is the one piece of MapLibre's own copy a reader
       here will read, so it arrives in both languages like everything else
       on this site — Thai first. Written as instructions, not apologies. */
    locale:{
      'CooperativeGesturesHandler.WindowsHelpText':
        'กด Ctrl ค้างแล้วเลื่อนเพื่อซูม · Use Ctrl + scroll to zoom the map',
      'CooperativeGesturesHandler.MacHelpText':
        'กด ⌘ ค้างแล้วเลื่อนเพื่อซูม · Use ⌘ + scroll to zoom the map',
      'CooperativeGesturesHandler.MobileHelpText':
        'ใช้สองนิ้วเลื่อนแผนที่ · Use two fingers to move the map',
      'NavigationControl.ZoomIn':'ซูมเข้า · Zoom in',
      'NavigationControl.ZoomOut':'ซูมออก · Zoom out',
      'FullscreenControl.Enter':'ดูเต็มจอ · View full screen',
      'FullscreenControl.Exit':'ออกจากเต็มจอ · Leave full screen'
    }
  });
  /* dragRotate:false is the MOUSE. Touch rotation lives on its own handler
     and is on by default, which on a phone is not a feature anybody asked
     for — and here it is worse than unwanted: sync() below fixes the drawing
     to the ground with a translate and a uniform scale, arithmetic that is
     only true at bearing 0. Let a casual two-finger twist through and every
     pin, ring and moat drawn over the tiles skews off the streets it names,
     with no compass on screen to put it back. */
  map.touchZoomRotate.disableRotation();
  /* Top-LEFT. Three of the four corners are already spoken for: the drawings
     put their north arrow top-right, the credit sits bottom-right, and the
     soi and event maps put a scale bar bottom-left. That last collision was
     invisible while the drawing painted over the controls, and became a
     zoom button sitting on top of "100 ม./m" the moment the controls were
     lifted above it. No compass — rotation is off. */
  map.addControl(new maplibregl.NavigationControl({showCompass:false}),'top-left');
  /* Full screen, because cooperative gestures are a bargain and this is the
     other half of it: two fingers inside a band on a page, and everything
     back — one finger, the whole screen — for a reader who came to look at
     the map. On a phone this is the difference between a 337x159 strip and a
     map. Feature-detected: iOS Safari on iPhone has never allowed an element
     to go full screen, and a button that does nothing is worse than no
     button, so there it is simply not offered. */
  if(document.fullscreenEnabled||document.webkitFullscreenEnabled)
    map.addControl(new maplibregl.FullscreenControl({container:el}),'top-left');
  /* Where the reader started. A map with rails still lets somebody wander
     two provinces away from the place the page is about, and until now there
     was no way back but reloading the page. */
  function Home(){}
  Home.prototype.onAdd=function(m){
    var d=document.createElement('div');
    d.className='maplibregl-ctrl maplibregl-ctrl-group';
    var b=document.createElement('button');
    b.type='button';b.className='mdmap-home';
    b.title='กลับจุดเริ่มต้น · Back to the start';
    b.setAttribute('aria-label','กลับจุดเริ่มต้น · Back to the start');
    b.innerHTML='<span aria-hidden="true">◎</span>';
    b.addEventListener('click',function(){
      if(!home)return;
      m.easeTo({center:home.center,zoom:home.zoom,duration:
        matchMedia('(prefers-reduced-motion:reduce)').matches?0:420});
    });
    d.appendChild(b);this._d=d;return d;};
  Home.prototype.onRemove=function(){if(this._d&&this._d.parentNode)
    this._d.parentNode.removeChild(this._d);};
  map.addControl(new Home(),'top-left');
  /* A live scale bar, true at every zoom. The drawn bars in the SVGs are
     true only at the scale they were drawn at — which is why the shell has
     always hidden them the moment somebody zoomed — so with a basemap under
     it this one takes over and the drawn one stands down (see the CSS). The
     drawing keeps its own bar for print and for the no-tiles state, where it
     is the only map there is. Metric only: nobody here measures a soi in
     miles. */
  map.addControl(new maplibregl.ScaleControl({maxWidth:110,unit:'metric'}),'bottom-left');
  /* Both bottom corners come out of the map's own layer and up into the
     container. MapLibre keeps its controls inside the layer that sits UNDER
     the drawing — which is the right way round for pins over streets, and the
     wrong way round for these: now that the drawing pans across the whole box,
     a pin can come to rest on top of the ODbL credit. That credit is a licence
     condition rather than decoration and nothing may cover it, and a reader
     cannot use a zoom button they cannot see either. Only the parent changes;
     MapLibre keeps its own references and still takes these nodes away itself
     when the map is removed. */
  ['bottom-right','bottom-left','top-left'].forEach(function(c){
    var n=live.querySelector('.maplibregl-ctrl-'+c);
    if(n)el.appendChild(n);
  });
  reg.set(el,map);

  /* ---- keeping the drawing and the ground in register -------------------
     The drawn SVG is a picture in screen space. The tiles under it are not.
     Placed once and then left alone, the ground slid out from under the pins
     the first moment anybody swiped: the streets moved, the pins stayed
     nailed to the box, and the reader lost the one thing the basemap was
     added to give them. A map whose marks do not travel with its ground is
     not showing two things at once, it is showing two different places.

     So the drawing is re-fixed to the ground on every camera change. With
     rotation and pitch off, MapLibre's projection across one small box is a
     plain translate-and-uniform-scale — which is a single CSS transform, no
     redraw, no reprojection, and no work asked of any drawing layer. Keep
     the coordinate the drawing was centred on and the zoom it was laid out
     at; after that the drawing simply goes wherever that coordinate has
     moved to on screen, at 2^Δzoom the size. */
  var anchor=null;
  /* The camera the reader was given, kept so ◎ can hand it back. Declared
     here beside the anchor because the two are the same idea: one is where
     the drawing belongs, the other is where the reader belongs. */
  var home=null;
  function sync(){
    if(!anchor||!draw)return;
    var p=map.project([anchor.lng,anchor.lat]);
    var k=Math.pow(2,map.getZoom()-anchor.z);
    var tx=p.x-k*anchor.x,ty=p.y-k*anchor.y;
    draw.style.transform='translate('+tx.toFixed(2)+'px,'+ty.toFixed(2)+
      'px) scale('+k.toFixed(6)+')';
    marks(k);
    corner(k,tx,ty);
    /* One state class, so a layer can style whatever it drew that is only
       true at the scale it was drawn at. The scale bars use it. */
    el.classList.toggle('mdmap-zoomed',k!==1);
    /* Also published for anyone who would rather do their own arithmetic. */
    el.style.setProperty('--mdmap-k',k.toFixed(6));
    el.dispatchEvent(new CustomEvent('mdmap:sync',{detail:{k:k}}));
  }
  /* ---- what grows with the ground, and what does not -------------------
     Zooming in makes the ground bigger, and the drawing over it has to grow
     by the same factor or it stops being the same map. But only half of what
     is drawn is ground. A range ring is a distance and is right to grow. The
     moat is a place and is right to grow. A pin is not a distance — it is one
     symbol standing over one doorway, and blown up four times it becomes a
     dinner plate covering the street it was meant to point at. Same for every
     label: text scaled 4× stops being readable and starts being wallpaper.

     So the two are told apart by declaration, since nothing in an SVG says
     which a shape is. Any element carrying data-mdpin="x,y" is held at the
     size it was drawn, pivoting on the point it names — so the pin keeps its
     tip on the doorway while everything under it opens out. Everything else
     scales, which is the right default: a layer that says nothing gets the
     honest picture, just larger.

     The transform attribute of a tagged element belongs to this module and
     will be overwritten. A layer that needs its own placement transform
     should tag a wrapper <g> instead — see the scale bars in build.py. */
  var tagged=[],fixt=[],ppu=1,q0x=0,q0y=0;
  function readMarks(){
    tagged=[];fixt=[];
    if(!draw)return;
    draw.querySelectorAll('[data-mdpin]').forEach(function(g){
      var v=(g.getAttribute('data-mdpin')||'').split(',');
      var x=parseFloat(v[0]),y=parseFloat(v[1]);
      if(isFinite(x)&&isFinite(y))tagged.push([g,x,y]);
    });
    /* ---- and the corner furniture ------------------------------------
       A north arrow is not on the ground at all. It belongs to the frame,
       and a frame that sails off to the north-east the moment somebody
       swipes was never a frame. Same for a scale bar. These stay put.

       Two numbers are all that is needed to hold them there, and both are
       read once, here, while the drawing is still untransformed: how many
       CSS pixels one viewBox unit is worth, and where the box's own top-left
       corner falls in viewBox units. Everything after that is arithmetic on
       numbers sync already has, so a pan costs no measuring — reading layout
       back on every frame of a drag is how a map starts to stutter. */
    var root=draw.querySelector('svg');
    fixt=[].slice.call(draw.querySelectorAll('[data-mdfix]'));
    if(root&&fixt.length&&root.getScreenCTM){
      var M=root.getScreenCTM(),b=draw.getBoundingClientRect();
      /* Both read in the same breath, so the page's own scroll is in both
         and cancels — this must not shift when the reader scrolls past. */
      if(M&&M.a&&M.d){ppu=M.a;q0x=(b.left-M.e)/M.a;q0y=(b.top-M.f)/M.d;}
    }
  }
  /* Undo the box's transform exactly, in the SVG's own units: shrink by k
     about the corner the box scales from, then take back the pan. */
  function corner(k,tx,ty){
    for(var i=0;i<fixt.length;i++){
      if(k===1&&!tx&&!ty){fixt[i].removeAttribute('transform');continue;}
      fixt[i].setAttribute('transform','translate('+
        (((k-1)*q0x-tx/ppu)/k).toFixed(3)+' '+(((k-1)*q0y-ty/ppu)/k).toFixed(3)+
        ') scale('+(1/k).toFixed(6)+')');
    }
  }
  function marks(k){
    /* At rest the attribute is removed rather than set to an identity
       transform: this is also what prints, and a printed page should carry
       the drawing exactly as it was drawn. */
    for(var i=0;i<tagged.length;i++){
      var t=tagged[i];
      if(k===1)t[0].removeAttribute('transform');
      else t[0].setAttribute('transform','translate('+t[1]+' '+t[2]+') scale('+
        (1/k).toFixed(6)+') translate('+(-t[1])+' '+(-t[2])+')');
    }
  }
  /* Taken afresh whenever the camera is pointed at the drawing deliberately:
     once on load, and again on every retarget a layer makes after redrawing
     itself. Those are the only moments the two pictures are known to agree,
     so they are the only moments worth measuring. The transform is cleared
     BEFORE the measurement — anchoring to an already-shifted drawing would
     bake in the shift and compound it on the next pan. */
  function anchorNow(){
    if(!draw)return;
    draw.style.transformOrigin='0 0';
    draw.style.transform='none';
    var c=map.getCenter(),p=map.project(c);
    anchor={lat:c.lat,lng:c.lng,z:map.getZoom(),x:p.x,y:p.y};
    /* The only moment the tagged elements can have changed is a redraw, and
       a redraw is always followed by a retarget, which lands here. So the
       list is gathered once and reused for every frame of every pan after. */
    readMarks();
    marks(1);
    corner(1,0,0);
    el.classList.remove('mdmap-zoomed');
    el.style.setProperty('--mdmap-k','1');
    el.dispatchEvent(new CustomEvent('mdmap:sync',{detail:{k:1}}));
  }
  anch.set(el,anchorNow);
  map.on('move',sync);

  /* A tap on the ground, reported to whichever layer owns this box. MapLibre
     does not fire this after a drag, so panning never moves anybody's
     starting point by accident. */
  map.on('click',function(e){
    el.dispatchEvent(new CustomEvent('mdmap:click',
      {detail:{lat:e.lngLat.lat,lng:e.lngLat.lng}}));
  });
  /* Framing the two pictures against each other. Done at load, and again
     whenever the BOX changes size — going full screen is exactly that, and
     the drawing is laid out at 100% width, so its metres-per-pixel changes
     with the box. Re-anchoring without re-deriving the scale would leave a
     drawing scaled for a 337 px strip sitting over a full-screen city. */
  function frame(){
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
    /* Before the anchor is taken, because growing the type changes nothing
       about where the drawing sits but everything about whether it can be
       read — and because the anchor measurement wants a settled picture. */
    legible();
    /* Whatever camera we have arrived at, that is where the drawing belongs.
       Harmlessly repeated when the branch above already retargeted — same
       camera in, same anchor out. It is here for the mounts that pass no
       scale at all and are simply framed correctly from the start. */
    anchorNow();
    /* And that camera is "the start" the ◎ button returns to. Re-taken on a
       reframe on purpose: after a full-screen toggle the start is the newly
       framed picture, not the strip the reader left behind. */
    home={center:map.getCenter(),zoom:map.getZoom()};
  }
  /* ---- type that survives the phone ------------------------------------
     A drawing is laid out at whatever width the column gives it. A place map
     is 640 units wide and a 375 px phone gives it 337 — so the 10.5-unit
     Thai a neighbour is named in arrives as about five and a half pixels,
     which for a script with tone marks above and vowels below is not small
     type, it is a texture. The names were there and could not be read.

     So any group that declares a floor in data-minpx gets grown until it
     meets it. Growing type on a picture whose labels were placed by a
     collision algorithm at the OLD size will make some of them touch, and a
     name printed through another name is worse than a name not printed at
     all — so after growing, any label overlapping one already kept is put
     away. Earlier in the document wins, which on these maps is the better
     place: the most complete listings and the nearest neighbours are drawn
     first. Everything is restored before measuring so this is idempotent.

     Only ever grows. On a wide screen the drawing is at or above its drawn
     size, nothing is under its floor, and nothing here changes anything. */
  function legible(){
    if(!draw)return;
    var svg=draw.querySelector('svg');if(!svg)return;
    var vb=(svg.getAttribute('viewBox')||'').split(/[\s,]+/);
    var vbW=parseFloat(vb[2]),shown=svg.getBoundingClientRect().width;
    if(!(vbW>0)||!(shown>0))return;
    var perPx=vbW/shown;                       /* drawing units per CSS pixel */
    var groups=draw.querySelectorAll('[data-minpx]');
    var kept=[];
    for(var i=0;i<groups.length;i++){
      var g=groups[i],min=parseFloat(g.getAttribute('data-minpx'))||11;
      /* The size it was drawn at, remembered once so repeat runs measure the
         original rather than the last thing this function did. */
      if(!g.dataset.mdfs){
        var fs=parseFloat(g.getAttribute('font-size')||
          getComputedStyle(g).fontSize)||10.5;
        g.dataset.mdfs=fs;
      }
      var drawn=parseFloat(g.dataset.mdfs);
      var want=min*perPx;                      /* the floor, in drawing units */
      g.setAttribute('font-size',(want>drawn?want:drawn).toFixed(2));
      /* Also thicken the halo behind the type by the same proportion, or a
         grown label sits on the ground with a stroke sized for smaller
         letters and the city shows through the middle of the words. */
      var st=parseFloat(g.getAttribute('stroke-width')||'0');
      if(st&&want>drawn){
        if(!g.dataset.mdsw)g.dataset.mdsw=st;
        g.setAttribute('stroke-width',
          (parseFloat(g.dataset.mdsw)*(want/drawn)).toFixed(2));
      }
      var texts=g.matches('text')?[g]:g.querySelectorAll('text');
      for(var j=0;j<texts.length;j++){
        var t=texts[j];
        t.style.display='';                    /* measure what was hidden too */
        if(want<=drawn)continue;
        var b;try{b=t.getBBox();}catch(e){continue;}
        if(!b||!b.width)continue;
        var hit=false;
        for(var q=0;q<kept.length;q++){
          var o=kept[q];
          if(b.x<o.x+o.width&&o.x<b.x+b.width&&
             b.y<o.y+o.height&&o.y<b.y+b.height){hit=true;break;}
        }
        if(hit)t.style.display='none';
        else kept.push({x:b.x,y:b.y,width:b.width,height:b.height});
      }
    }
  }
  /* Straight away, before a single tile has been asked for. The type is too
     small to read on a phone whether or not there is ground under it, and the
     drawing is what a reader looks at for the whole time the first tiles are
     in flight — which on a mid-tier phone on cell data is the part of the
     visit that actually happens. It is also the picture that stays for good
     if the tiles never arrive. Idempotent, so the later calls cost nothing. */
  legible();
  /* MapLibre fires this whenever its container changes size — entering and
     leaving full screen, and an orientation turn on a phone. */
  map.on('resize',frame);
  map.on('load',function(){
    el.classList.add('mdmap-on');
    frame();
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
    /* The drawing is the whole picture again, so it goes back where it was
       drawn. A pan inherited from a basemap that is no longer there would
       leave the fallback sitting crooked in its own box. */
    if(draw){draw.style.transform='none';draw.removeAttribute('aria-hidden');}
    marks(1);
    corner(1,0,0);
    /* The drawing is the whole map again, so its names have to be readable at
       the size the box actually is — the box may have changed since it was
       first measured, and this is now the picture the reader is keeping. */
    legible();
    el.classList.remove('mdmap-zoomed');
    anchor=null;
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
    /* Re-take the anchor. A layer calls this the instant after it has redrawn
       itself, which makes it the one moment the drawing and the ground are
       known to line up — and therefore the only moment worth measuring from.
       It also clears any pan the reader had made, which is right: they have
       just been handed a new picture, centred somewhere new. */
    var a=anch.get(el);if(a)a();
    return true;
  },
  /* How much bigger the ground is now than when the drawing was laid out.
     1 until somebody zooms. Companion to the mdmap:sync event, for a layer
     that would rather ask than listen. */
  scale:function(el){
    var v=parseFloat(el.style.getPropertyValue('--mdmap-k'));
    return v>0?v:1;
  },
  /* ---- for a layer that draws INTO the map rather than over it ----------
     Everything else on this site draws its own SVG and lets the shell put
     ground underneath. That is right for a picture with a dozen marks on it,
     and wrong for the explore map, which paints eighteen thousand points and
     re-paints them every time a chip is tapped — work MapLibre does on the
     GPU and an SVG layer cannot do at all.

     Such a layer needs the map object, and there is exactly one rule about
     how it gets it: not by constructing one. This site has ONE map
     constructor and this module is it, so the way in is to ask here and be
     called back when the style is ready to take sources.

     ready() fires immediately if the map is already loaded, and never fires
     if the tiles fail — which is the correct behaviour, because a layer that
     paints into a basemap has nothing to paint into when there is no
     basemap. Such a layer owes its reader a fallback that does not need one;
     /map.html keeps its list of shelves for exactly that. */
  ready:function(el,fn){
    var m=reg.get(el);
    if(!m){
      /* The box may not have been mounted yet — it mounts when it comes into
         view. Wait for the element to gain a map rather than making one. */
      var tries=0,t=setInterval(function(){
        var mm=reg.get(el);
        if(mm){clearInterval(t);window.MDMAP.ready(el,fn);}
        else if(++tries>400)clearInterval(t);   /* ~40 s, then give up quietly */
      },100);
      return false;
    }
    if(m.isStyleLoaded&&m.isStyleLoaded())fn(m);
    else m.once('load',function(){fn(m);});
    return true;
  },
  /* The map itself, for a layer that already knows it is mounted. Returns
     undefined rather than throwing when it is not. */
  map:function(el){return reg.get(el);}
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
/* WHAT KEEPS ITS FINGER. The line above hands the whole box to the map so it
   can be panned, and everything drawn on top of it goes deaf at the same
   moment — including the things that were drawn precisely to be touched. That
   is how the neighbour links on 12,309 place pages came to be unclickable in
   the only state a reader ever sees them: they are real records with pages of
   their own, they were drawn as links, and the basemap silently took the
   pointer away from them the instant it arrived.
   So the rule is stated by what a mark IS, not by which layer wrote it: a
   link inside a drawing is a door and keeps its pointer, and `.loopin` keeps
   the name it already had for the marks that answer without being links. Both
   are narrow — the ground between them stays deaf, so a drag anywhere else
   still pans the map. */
.mdmap.mdmap-on .mdmap-draw a,
.mdmap.mdmap-on .mdmap-draw .loopin{pointer-events:auto}
/* A drawn dot is 3.6 units across and a fingertip is not. The anchor carries
   an invisible disc sized in the drawing's own units (build.py works out what
   44 CSS px is worth there), and it must stay touchable while staying unseen
   — `fill:none` would make it deaf again, so it is painted and made
   transparent instead. */
.mdmap-draw a .hit{fill:#000;fill-opacity:0;stroke:none}
.mdmap-draw a:focus-visible .hit{fill-opacity:.10;outline:none}
.mdmap-draw a:focus-visible circle:not(.hit){stroke:#2A1E16;stroke-width:2.4}
/* map.js slides the drawing with the ground, so it no longer sits neatly
   inside its own box — clip it to the same rounded rectangle the tiles use,
   or a panned picture spills over the corners and past the credit. Promoted
   to its own layer only while there is a basemap to move it against; a soi
   page carrying several maps should not hold a compositor layer for each of
   them when none of them can move. */
.mdmap.mdmap-on{overflow:hidden;border-radius:14px}
.mdmap.mdmap-on .mdmap-draw{will-change:transform}
/* An SVG clips to its viewBox, and that is exactly wrong for a drawing being
   slid about over a basemap. Two things need to escape it. The corner
   furniture, which has to move the OPPOSITE way to the pan to stay put, and
   so goes straight out of the frame the moment anybody drags — a scale bar
   already at the foot of the viewBox has nowhere to go but past the bottom
   edge. And the drawn marks themselves, which stop at the frame they were
   drawn for: letting them out means panning toward a pin reveals it instead
   of showing bare ground where it should be. The box still clips, so nothing
   escapes onto the page. Only while a basemap is live — with no tiles the
   drawing is the whole picture and its frame is the picture's edge. */
.mdmap.mdmap-on .mdmap-draw svg{overflow:visible}
/* The drawn cream background and its border are the "no ground" state. With
   tiles underneath they are exactly what must not be painted. */
.mdmap.mdmap-on .mdmap-bg{display:none}
/* A drawn scale bar is true at exactly one zoom: the one it was drawn at.
   Held in the corner it keeps its length while the ground under it grows,
   and a bar that says 200 m over 400 m of street is worse than no bar — so
   away it goes until the reader is back at the scale it was measured for. A
   redraw always retargets, which is what brings it back. This never fires
   without a basemap, so the printed page and the no-tiles fallback — where
   the drawing is the only map there is — keep their bar always. */
.mdmap.mdmap-zoomed .mdmap-scale{display:none}
/* And once there is a basemap, a LIVE bar is measuring the same ground at
   every zoom, so the drawn one stands down entirely rather than waiting to
   be caught out — two bars in one corner, one of them true only sometimes,
   is a worse map than either alone. It comes back on paper and with no
   tiles, where it is the only bar there is. */
.mdmap.mdmap-on .mdmap-scale{display:none}
/* Controls a fingertip can hit. MapLibre draws 29 px buttons; the guideline
   is 44 and the audience is holding a phone in the street. Only the buttons
   grow — the scale bar and the credit are read, not pressed. */
.mdmap .maplibregl-ctrl-group button{width:44px;height:44px}
.mdmap .maplibregl-ctrl-group button .maplibregl-ctrl-icon{transform:scale(1.18)}
.mdmap .mdmap-home{font-size:19px;line-height:1;color:#2A1E16;
  display:grid;place-items:center}
/* The gesture note MapLibre shows over the map when one finger tries to pan.
   Its default is a dark scrim with white text; on this paper it reads as an
   error, so it is dressed as the site's own quiet card. */
.mdmap .maplibregl-cooperative-gesture-screen{background:rgba(42,30,22,.62);
  font-family:inherit;font-size:15px;line-height:1.5;padding:1rem}
.mdmap .maplibregl-cooperative-gesture-screen .maplibregl-desktop-message,
.mdmap .maplibregl-cooperative-gesture-screen .maplibregl-mobile-message{
  background:#FFFDF8;color:#2A1E16;border-radius:12px;padding:.6rem 1rem;
  box-shadow:0 6px 18px rgba(42,30,22,.22);max-width:22rem}
@media (prefers-reduced-motion:reduce){
  .mdmap .maplibregl-cooperative-gesture-screen{transition:none}}
/* The live bar, lifted out of the map layer with the other controls so the
   drawing cannot pan across it. */
.mdmap>.maplibregl-ctrl-bottom-left{z-index:4}
.mdmap:not(.mdmap-on)>.maplibregl-ctrl-bottom-left{display:none}
.mdmap .maplibregl-ctrl-scale{background:rgba(255,253,248,.88);
  border-color:#8A7761;color:#2A1E16;font-size:11px}
/* Lifted out of the map layer by map.js so the drawing can never pan across
   them. MapLibre's own rules still place them in their corners; all they need
   here is to sit above the drawing rather than below it. */
.mdmap>.maplibregl-ctrl-top-left,
.mdmap>.maplibregl-ctrl-bottom-right{z-index:4}
/* Out of the live layer, they no longer fade in with it — so they are held
   back until there is a basemap for them to belong to. A zoom button over a
   picture that cannot zoom, and a tile credit with no tiles under it, both
   arrive before the thing they are for. */
.mdmap:not(.mdmap-on)>.maplibregl-ctrl-top-left,
.mdmap:not(.mdmap-on)>.maplibregl-ctrl-bottom-right{display:none}
.mdmap .maplibregl-ctrl-attrib{font-size:11px;background:rgba(255,253,248,.88)}
/* Never let the credit be folded away: ODbL asks for it to be visible, and a
   collapsed ⓘ on a phone is not visible. */
.mdmap .maplibregl-ctrl-attrib-button{display:none!important}
.mdmap .maplibregl-ctrl-attrib.maplibregl-compact-show .maplibregl-ctrl-attrib-inner{
  display:block!important}
/* Full screen: the box becomes the window, and the rounded corners it wore
   as a card in an article stop making sense against the screen edge. The
   drawing is re-framed against the ground by map.js on the resize, so
   nothing here has to reposition it — only the chrome changes. */
.mdmap:fullscreen{width:100%;height:100%;border-radius:0;margin:0;
  background:#FBF6EC}
.mdmap:fullscreen .mdmap-live{border-radius:0}
.mdmap:-webkit-full-screen{width:100%;height:100%;border-radius:0;margin:0}
/* On paper the tiles are gone and the drawing is the map again, so it prints
   from its own origin — never from wherever the reader happened to leave it. */
@media print{.mdmap-live{display:none!important}
  .mdmap-draw{position:static;transform:none!important}
  /* And the frame goes back on. On paper there is no panning to escape, so
     everything the viewBox was cropping would simply spill across the page. */
  .mdmap-draw svg{overflow:hidden!important}}
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
    # The rails travel with the config rather than living as literals in the
    # JS: the archive's own coverage is a property of the tile file, so the
    # day a third province is added, the fence moves in the same file that
    # names the new tiles.
    runtime = {"url": cfg["url"], "attribution": ATTRIBUTION,
               "glyphs": glyphs, "layers": layers,
               "bounds": cfg.get("bounds") or BOUNDS,
               "minZoom": cfg.get("minZoom") or MIN_ZOOM,
               # The elevation archive, passed through verbatim for the one
               # page that reads it (doi.js). Configured beside the basemap
               # url above so this module stays the only place tiles are set
               # up; map.js itself never touches it.
               "terrain": cfg.get("terrain")}
    (docs / "map.js").write_text(
        "window.MDMAP_CFG=" + json.dumps(runtime, ensure_ascii=False,
                                         separators=(",", ":")) + ";\n" + JS)
    vend = docs / "vendor"
    vend.mkdir(exist_ok=True)
    for f in VENDOR:
        src = ROOT / "assets" / "vendor" / f
        if src.exists():
            (vend / f).write_bytes(src.read_bytes())
    # The label type, when it is ours. docs/ is wiped every build, so this is
    # a copy each run like the fonts and the vendored libraries — never a
    # hand-placed folder that survives one build and vanishes at the next.
    fonts = 0
    if glyphs and "{fontstack}" in glyphs and not glyphs.startswith("http"):
        gsrc = ROOT / "assets" / "glyphs"
        for pbf in sorted(gsrc.glob("*/*.pbf")):
            dest = docs / "glyphs" / pbf.parent.name
            dest.mkdir(parents=True, exist_ok=True)
            (dest / pbf.name).write_bytes(pbf.read_bytes())
            fonts += 1
    return {"enabled": True, "layers": len(layers), "url": cfg["url"],
            "labels": bool(glyphs), "dropped_label_layers": dropped,
            "glyph_files": fonts}
