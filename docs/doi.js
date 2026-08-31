/* doi.js — /doi.html only. The third dimension, opt-in. */
(function(){
var box=document.getElementById('doimap');
if(!box||!window.MDMAP||!window.MDMAP_CFG)return;
var T=window.MDMAP_CFG.terrain;
if(!T||!T.url)return;
MDMAP.ready(box,function(map){
  /* Resolved against the SITE root, exactly as map.js resolves the basemap —
     the same two traps, the same cure. */
  var ROOT=document.documentElement.getAttribute('data-root')||'';
  var ABS=new URL(T.url,new URL(ROOT||'./',location.href)).href;
  function arm(){
  if(!map.getSource('doidem')){
    map.addSource('doidem',{type:'raster-dem',url:'pmtiles://'+ABS,
      encoding:T.encoding||'terrarium',tileSize:256,maxzoom:T.maxzoom||12,
      attribution:'ความสูง · elevation: Mapzen terrain tiles / SRTM (NASA, USGS)'});
    /* Hillshade sits under the water, so rivers and the moat keep their ink
       over the relief. The first of these ids present wins; a retuned style
       that renames them all leaves the shading on top of fills, which is
       visible and shippable rather than silently absent. */
    var before=null;
    ['water','water-line','buildings','roads-casing','roads-minor']
      .some(function(id){if(map.getLayer(id)){before=id;return true}return false;});
    map.addLayer({id:'doi-hills',type:'hillshade',source:'doidem',paint:{
      'hillshade-exaggeration':0.58,
      'hillshade-illumination-anchor':'map',
      'hillshade-illumination-direction':335,
      'hillshade-shadow-color':'#59452F',
      'hillshade-highlight-color':'#FFFDF4',
      'hillshade-accent-color':'#6E5A40'}},before||undefined);
  }
  /* The controls appear only now — a button that cannot act yet is worse
     than no button, and with no basemap none of these can act. */
  var bar=document.getElementById('doibar');
  if(bar)bar.hidden=false;
  function rm(){return matchMedia('(prefers-reduced-motion:reduce)').matches;}

  var b3=document.getElementById('doi3d'),on=false;
  function set3d(want){
    on=want;
    if(on){
      map.setTerrain({source:'doidem',exaggeration:1.35});
      map[rm()?'jumpTo':'easeTo']({pitch:60,duration:rm()?0:900});
    }else{
      map[rm()?'jumpTo':'easeTo']({pitch:0,duration:rm()?0:700});
      map.setTerrain(null);
    }
    if(b3)b3.setAttribute('aria-pressed',on?'true':'false');
    box.classList.toggle('doi-3d',on);
  }
  if(b3)b3.addEventListener('click',function(){set3d(!on);});

  /* Where the sun actually is over the basin, right now — no library, no
     request, fifteen lines of spherical arithmetic on the reader's own
     clock. Coarse on purpose (no equation of time, ±3° or so), which for a
     light direction is indistinguishable. Below the horizon the map light
     stands in: the hillshade never pretends the sun is up at night. */
  function sunAz(){
    var d=new Date(),rad=Math.PI/180,lat=18.79,lng=98.99;
    var start=Date.UTC(d.getUTCFullYear(),0,0);
    var day=(Date.UTC(d.getUTCFullYear(),d.getUTCMonth(),d.getUTCDate())-start)/864e5;
    var decl=-23.44*Math.cos(rad*(360/365)*(day+10));
    var solarT=d.getUTCHours()+d.getUTCMinutes()/60+lng/15;
    var H=(solarT-12)*15*rad,la=lat*rad,de=decl*rad;
    var alt=Math.asin(Math.sin(la)*Math.sin(de)+Math.cos(la)*Math.cos(de)*Math.cos(H));
    if(alt<0)return 335;
    var az=Math.acos((Math.sin(de)-Math.sin(alt)*Math.sin(la))/
                     (Math.cos(alt)*Math.cos(la)));
    if(Math.sin(H)>0)az=2*Math.PI-az;
    return az/rad;
  }
  var seg=[].slice.call(document.querySelectorAll('#doibar .doilight'));
  seg.forEach(function(b){b.addEventListener('click',function(){
    var az=b.dataset.az==='now'?sunAz():(parseFloat(b.dataset.az)||335);
    if(map.getLayer('doi-hills'))
      map.setPaintProperty('doi-hills','hillshade-illumination-direction',az);
    seg.forEach(function(o){o.setAttribute('aria-pressed',o===b?'true':'false');});
  });});

  /* Colour by height — a hypsometric tint the style spec only recently
     learned. Tried, never assumed: if this MapLibre cannot draw the layer
     type, the catch keeps the button hidden and the page has simply never
     offered it. The palette is the paper's own, basin cream to summit pale. */
  var tint=document.getElementById('doitint');
  if(tint)try{
    map.addLayer({id:'doi-tint',type:'color-relief',source:'doidem',paint:{
      'color-relief-opacity':0.55,
      'color-relief-color':['interpolate',['linear'],['elevation'],
        300,'#F3EBD9',600,'#E8D9B4',1000,'#D9C08C',
        1500,'#C09E6B',2000,'#9C7B50',2600,'#FFFDF4']
    }},'doi-hills');
    map.setLayoutProperty('doi-tint','visibility','none');
    tint.hidden=false;
    tint.addEventListener('click',function(){
      var on=tint.getAttribute('aria-pressed')==='true';
      map.setLayoutProperty('doi-tint','visibility',on?'none':'visible');
      tint.setAttribute('aria-pressed',on?'false':'true');
    });
  }catch(e){/* older engine: no tint, no button, nothing missing */}

  /* The one flight on the page, and the reader books it. The coordinate is
     the instrument's own — data-lat/lng come from terrain_meta.json through
     the page, so the button and the facts card can never disagree. */
  var fly=document.getElementById('doitop');
  if(fly)fly.addEventListener('click',function(){
    var la=parseFloat(fly.dataset.lat),ln=parseFloat(fly.dataset.lng);
    if(!isFinite(la)||!isFinite(ln))return;
    if(!on)set3d(true);
    map[rm()?'jumpTo':'flyTo']({center:[ln,la],zoom:11.6,
      duration:rm()?0:2600});
  });
  }

  /* Nothing above runs until the archive itself has answered. The config
     declares the DEM at build time, and a declared archive can still be
     absent where it counts — not yet uploaded, wrong path, symlink gone —
     while addSource succeeds and every tile request quietly 404s. That
     shipped once (2026-08-27): relief drawing nothing, and this bar offering
     a 3D button that could not act. So one 128-byte ranged read settles it
     first: a PMTiles file opens with its own name, and unless the first
     seven bytes say so, the page simply keeps its drawn cross-section —
     the same supported absence as an empty terrain url. On the days the
     archive does answer, these bytes are the header pmtiles.js is about to
     fetch anyway, so the cost is one small request; on the days it does
     not, this is the ONLY request, in place of a screenful of failed tile
     fetches under a bar of dead controls. */
  fetch(ABS,{headers:{Range:'bytes=0-127'}}).then(function(r){
    if(!r.ok)throw 0;
    /* Our worker answers ranges with 206, so the whole body IS the 128
       bytes asked for. A host that ignored Range answers 200 with all
       161 MB behind it — never arrayBuffer() that; read one chunk off the
       stream and hang up. */
    if(r.status===206)return r.arrayBuffer().then(function(a){return new Uint8Array(a);});
    if(!r.body)throw 0;
    var rd=r.body.getReader(),got=[];
    function pull(){return rd.read().then(function(c){
      if(c.value)for(var i=0;i<c.value.length&&got.length<7;i++)got.push(c.value[i]);
      if(got.length>=7||c.done){try{rd.cancel()}catch(e){}return got;}
      return pull();
    });}
    return pull();
  }).then(function(b){
    var m='';for(var i=0;i<7&&i<b.length;i++)m+=String.fromCharCode(b[i]);
    if(m!=='PMTiles')throw 0;
    arm();
  }).catch(function(e){/* no relief today; the drawn basin stands */});
});
})();
