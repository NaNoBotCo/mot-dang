window.MDMAP_CFG={"url":"https://pub-b9aec74c6c794863bea9c1ce6a1faa3e.r2.dev/tiles/cm-cr.pmtiles","attribution":"© <a href=\"https://www.openstreetmap.org/copyright\">OpenStreetMap</a> contributors (ODbL)","glyphs":"https://protomaps.github.io/basemaps-assets/fonts/{fontstack}/{range}.pbf","layers":[{"id":"earth","type":"background","paint":{"background-color":"#FBF6EC"}},{"id":"landcover","type":"fill","source":"p","source-layer":"landcover","paint":{"fill-color":["match",["get","kind"],"grassland","#EFF2E4","forest","#E6EDDB","scrub","#EDF0E2","farmland","#F4F1E2","#F2EEE2"],"fill-opacity":0.55}},{"id":"landuse-green","type":"fill","source":"p","source-layer":"landuse","filter":["in",["get","kind"],["literal",["park","forest","garden","recreation_ground","pitch","cemetery","grass"]]],"paint":{"fill-color":"#E7EEDC"}},{"id":"landuse-built","type":"fill","source":"p","source-layer":"landuse","filter":["in",["get","kind"],["literal",["school","university","hospital","industrial","commercial","retail"]]],"paint":{"fill-color":"#F5EEE1"}},{"id":"water","type":"fill","source":"p","source-layer":"water","paint":{"fill-color":"#CFDCE8"}},{"id":"water-line","type":"line","source":"p","source-layer":"water","_note":"There is no physical_line layer in this schema — rivers, streams and canals are line features inside 'water' alongside the polygons. The Ping and the moat's feeder canals come through here.","filter":["in",["get","kind"],["literal",["river","stream","canal"]]],"paint":{"line-color":"#BFD0E0","line-width":["interpolate",["linear"],["zoom"],10,0.6,15,2.6]}},{"id":"buildings","type":"fill","source":"p","source-layer":"buildings","minzoom":14,"paint":{"fill-color":"#EFE6D6","fill-outline-color":"#E4D8C4","fill-opacity":["interpolate",["linear"],["zoom"],14,0,15.2,0.85]}},{"id":"roads-casing","type":"line","source":"p","source-layer":"roads","minzoom":11,"layout":{"line-cap":"round","line-join":"round"},"paint":{"line-color":"#E0D2BB","line-width":["interpolate",["exponential",1.5],["zoom"],11,["match",["get","kind"],"highway",2.4,"major_road",1.6,0.6],17,["match",["get","kind"],"highway",15,"major_road",11,6]]}},{"id":"roads-minor","type":"line","source":"p","source-layer":"roads","filter":["==",["get","kind"],"minor_road"],"minzoom":12,"layout":{"line-cap":"round","line-join":"round"},"paint":{"line-color":"#FFFDF8","line-width":["interpolate",["exponential",1.5],["zoom"],12,0.4,17,4.4]}},{"id":"roads-major","type":"line","source":"p","source-layer":"roads","filter":["==",["get","kind"],"major_road"],"layout":{"line-cap":"round","line-join":"round"},"paint":{"line-color":"#FFFCF4","line-width":["interpolate",["exponential",1.5],["zoom"],11,1.1,17,9]}},{"id":"roads-highway","type":"line","source":"p","source-layer":"roads","filter":["==",["get","kind"],"highway"],"layout":{"line-cap":"round","line-join":"round"},"paint":{"line-color":"#F7E7CB","line-width":["interpolate",["exponential",1.5],["zoom"],9,1.2,17,13]}},{"id":"boundaries","type":"line","source":"p","source-layer":"boundaries","paint":{"line-color":"#C9B79B","line-width":0.9,"line-dasharray":[3,2.5]}},{"id":"place-labels","type":"symbol","source":"p","source-layer":"places","filter":["in",["get","kind"],["literal",["locality","neighbourhood","suburb","village","town","city"]]],"layout":{"text-field":["format",["coalesce",["get","name"],["get","name:en"]],{},"\n",{},["coalesce",["get","name:en"],""],{"font-scale":0.82}],"text-font":["Noto Sans Regular"],"text-size":["interpolate",["linear"],["zoom"],10,11,15,14],"text-anchor":"center","text-max-width":8},"paint":{"text-color":"#5A4838","text-halo-color":"#FBF6EC","text-halo-width":1.6}},{"id":"road-labels","type":"symbol","source":"p","source-layer":"roads","minzoom":14,"filter":["in",["get","kind"],["literal",["major_road","minor_road"]]],"layout":{"symbol-placement":"line","text-field":["coalesce",["get","name"],["get","name:en"]],"text-font":["Noto Sans Regular"],"text-size":11},"paint":{"text-color":"#8A7761","text-halo-color":"#FFFDF8","text-halo-width":1.4}}]};
/* map.js — the only map constructor on this site.

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
    dragRotate:false,pitchWithRotate:false,touchPitch:false
  });
  /* Top-LEFT. Three of the four corners are already spoken for: the drawings
     put their north arrow top-right, the credit sits bottom-right, and the
     soi and event maps put a scale bar bottom-left. That last collision was
     invisible while the drawing painted over the controls, and became a
     zoom button sitting on top of "100 ม./m" the moment the controls were
     lifted above it. No compass — rotation is off. */
  map.addControl(new maplibregl.NavigationControl({showCompass:false}),'top-left');
  /* Both bottom corners come out of the map's own layer and up into the
     container. MapLibre keeps its controls inside the layer that sits UNDER
     the drawing — which is the right way round for pins over streets, and the
     wrong way round for these: now that the drawing pans across the whole box,
     a pin can come to rest on top of the ODbL credit. That credit is a licence
     condition rather than decoration and nothing may cover it, and a reader
     cannot use a zoom button they cannot see either. Only the parent changes;
     MapLibre keeps its own references and still takes these nodes away itself
     when the map is removed. */
  ['bottom-right','top-left'].forEach(function(c){
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
    /* Whatever camera we have arrived at, that is where the drawing belongs.
       Harmlessly repeated when the branch above already retargeted — same
       camera in, same anchor out. It is here for the mounts that pass no
       scale at all and are simply framed correctly from the start. */
    anchorNow();
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
