"""Traffic on every motdang map (Nan, 2026-10-03: "tom tom information should appear lots of places on the
site, such as any place id that includes a map").

map_shell.py appends map_js() to map.js, the one script behind every live map on the site (place pages, the
city map, listings, the toilet map …), and calls MDTRAFFIC.paint(map, el) when a map loads. It adds:

  · TomTom's flow tiles, green clear to red jammed, from /tt/flow/{z}/{x}/{y}.png — the motdang-traffic-tiles
    Worker (worker-tt/) holds her key as a secret and keeps each tile five minutes at the edge;
  · a traffic button on the map that turns them off and on (remembered per browser);
  · one line in the map's corner: the nearest road TomTom measured in the last two hours
    (data/traffic_now.json, importers/make_traffic_now.py, every 30 minutes), its speed and its free-flow speed;
  · the reader's own blue dot, when the tab holds a fix (sessionStorage md-here, written by md.js, locshare.js,
    front.js and the front-page map) — Nan, 2026-10-03: "I could share my location but I couldn't find myself".
"""

MAP_JS = r"""
/* traffic_map_layer.py — TomTom flow on every map, and the nearest measured road */
(function(){
var NOW=null;
function nowFile(){ if(!NOW) NOW=fetch('/data/traffic_now.json').then(function(r){return r.ok?r.json():null;}).catch(function(){return null;}); return NOW; }
function on(){ try{ return localStorage.getItem('md-tt')!=='off'; }catch(e){ return true; } }
function setOn(v){ try{ localStorage.setItem('md-tt', v?'on':'off'); }catch(e){} }
function bi(th,en){ return '<span class="bi"><span class="th" lang="th">'+th+'</span><span class="en" lang="en">'+en+'</span></span>'; }
function esc(s){ return String(s==null?'':s).replace(/[&<>"]/g,function(c){return{'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;'}[c];}); }
function km(a,b,c,d){ return Math.hypot((c-a)*111.32,(d-b)*111.32*Math.cos(a*Math.PI/180)); }
function firstSymbol(map){ var ls=map.getStyle().layers||[]; for(var i=0;i<ls.length;i++) if(ls[i].type==='symbol') return ls[i].id; return undefined; }
function addLayer(map){
  if(map.getLayer('tt-flow')) return;
  if(!map.getSource('tt')) map.addSource('tt',{type:'raster',tiles:[location.origin+'/tt/flow/{z}/{x}/{y}.png'],tileSize:256,minzoom:8,maxzoom:18,
    attribution:'Traffic © <a href="https://www.tomtom.com/" rel="noopener">TomTom</a>'});
  map.addLayer({id:'tt-flow',type:'raster',source:'tt',minzoom:10,paint:{'raster-opacity':0.85}},firstSymbol(map));
}
function line(el,map){
  var box=el.querySelector('.mdtt-line'); if(!box){ box=document.createElement('div'); box.className='mdtt-line'; el.appendChild(box); }
  nowFile().then(function(d){
    if(!d||!d.roads||!d.roads.length||Date.now()-Date.parse(d.generated)>2*3600e3){ box.hidden=true; return; }
    var c=map.getCenter(), best=null, bd=1e9;
    d.roads.forEach(function(r){ (r.line||[]).forEach(function(p){ var k=km(c.lat,c.lng,p[1],p[0]); if(k<bd){ bd=k; best=r; } }); });
    if(!best||bd>4||best.cur==null){ box.hidden=true; return; }
    var t=d.generated.slice(11,16), slow=best.ratio!=null&&best.ratio<0.6, mid=best.ratio!=null&&best.ratio<0.85;
    box.className='mdtt-line'+(slow?' slow':mid?' mid':'');
    box.innerHTML='<b>'+bi('ทางหลวง '+esc(best.route),'Route '+esc(best.route))+'</b> '+best.cur+' '+bi('กม./ชม.','km/h')+
      ' <small>'+bi('ถนนโล่ง '+best.free+' · วัดเมื่อ '+t,'free flow '+best.free+' · measured '+t)+'</small>';
    box.hidden=false;
  });
}
function Toggle(){}
Toggle.prototype.onAdd=function(map){
  var b=document.createElement('button'); b.type='button'; b.className='mdtt-btn';
  b.setAttribute('aria-pressed',String(on())); b.title='การจราจร · traffic';
  b.innerHTML='<svg viewBox="0 0 24 24" width="18" height="18" aria-hidden="true"><rect x="8" y="2" width="8" height="20" rx="3" fill="#2b2f36"/><circle cx="12" cy="6.5" r="2" fill="#e5455a"/><circle cx="12" cy="12" r="2" fill="#f5a34a"/><circle cx="12" cy="17.5" r="2" fill="#5fd18a"/></svg>';
  b.onclick=function(){ var v=!on(); setOn(v); b.setAttribute('aria-pressed',String(v)); if(map.getLayer('tt-flow')) map.setLayoutProperty('tt-flow','visibility',v?'visible':'none'); };
  var w=document.createElement('div'); w.className='maplibregl-ctrl maplibregl-ctrl-group'; w.appendChild(b); this._w=w; return w;
};
Toggle.prototype.onRemove=function(){ if(this._w&&this._w.parentNode) this._w.parentNode.removeChild(this._w); };
if(!document.getElementById('mdtt-css')){
  var s=document.createElement('style'); s.id='mdtt-css';
  s.textContent='.mdtt-btn{display:flex;align-items:center;justify-content:center}.mdtt-btn[aria-pressed=false] svg{opacity:.35}'+
    '.mdtt-line{position:absolute;right:6px;bottom:24px;z-index:3;max-width:calc(100% - 110px);background:rgba(10,13,19,.88);color:#fff;'+
    'border-radius:10px;padding:.3rem .55rem;font:600 .85rem/1.3 system-ui,sans-serif;border-left:5px solid #5fd18a;pointer-events:none}'+
    '.mdtt-line.mid{border-left-color:#f5a34a}.mdtt-line.slow{border-left-color:#e5455a}.mdtt-line small{display:block;font-weight:500;opacity:.9}'+
    '.mdtt-line .en{color:#fff}html.lang-both .mdtt-line .en::before{content:" · "}';
  document.head.appendChild(s);
}
/* the reader's own dot, from the tab's shared record (sessionStorage md-here, twenty minutes): whatever part
   of the site found them, every map shows them */
function hereDot(map){
  var h=null; try{ h=JSON.parse(sessionStorage.getItem('md-here')); }catch(e){}
  if(!h||Date.now()-h.t>20*60e3||map.getSource('md-here')) return;
  map.addSource('md-here',{type:'geojson',data:{type:'Feature',geometry:{type:'Point',coordinates:[h.lng,h.lat]},properties:{}}});
  map.addLayer({id:'md-here-acc',type:'circle',source:'md-here',paint:{'circle-color':'#1a73e8','circle-opacity':0.15,
    'circle-radius':['interpolate',['exponential',2],['zoom'],12,Math.max(6,(h.acc||30)/38),18,Math.max(10,(h.acc||30)/0.6)]}});
  map.addLayer({id:'md-here',type:'circle',source:'md-here',paint:{'circle-color':'#1a73e8','circle-radius':8,'circle-stroke-color':'#fff','circle-stroke-width':3}});
}
window.MDTRAFFIC={paint:function(map,el){
  try{ hereDot(map); }catch(e){}
  addEventListener('storage',function(e){ if(e.key==='md-here'){ try{ if(map.getLayer('md-here')){ map.removeLayer('md-here'); map.removeLayer('md-here-acc'); map.removeSource('md-here'); } hereDot(map); }catch(x){} } });
  try{ addLayer(map); if(!on()) map.setLayoutProperty('tt-flow','visibility','none'); }catch(e){}
  map.addControl(new Toggle(),'top-left');
  if(getComputedStyle(el).position==='static') el.style.position='relative';
  line(el,map);
  var t=null; map.on('moveend',function(){ clearTimeout(t); t=setTimeout(function(){ line(el,map); },300); });
}};
})();
"""


def map_js():
    return MAP_JS
