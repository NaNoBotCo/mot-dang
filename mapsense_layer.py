"""mapsense_layer.py — what readers do on the maps, sent to the counter.

Nan, 2026-09-29: "CAN MOtdang learn from how humans and bots interact with
maps?" — then "everything": the view a reader settles on, the places they open,
pins, saves, shares, place IDs and coordinates pasted, and the words a map
search found nothing for (that last one is counted in the Worker, not here).

MAP_JS rides at the end of map.js, after mine_layer's. map_shell calls
MDSENSE.watch() when a map loads; mapfirst_layer.py and explore_layer.py call
MDSENSE.tell() at the moments below. The Worker (publish/worker.js, mapSense)
writes one traffic_eye row per event, sorted people/machine by the same
classifier as every arrival.

What goes: the event, the cell (lat/lng to two decimals, ~1.1 km), the zoom
rounded, a place key where a place was opened or saved, and the page's path.
Events queue in memory and leave in one sendBeacon when the page is hidden, or
every 20. The beacon fires on motdang.net hosts only, so a local test build
stays quiet.
"""

MAP_JS = r"""/* mapsense_layer.py — what readers do on the maps, one beacon per page. */
(function(){
var Q=[],SENT=0,CAP=120,last='';
var ON=/(^|\.)motdang\.net$/.test(location.hostname)&&navigator.sendBeacon;
function cell(lat,lng){return isFinite(lat)&&isFinite(lng)?(+lat).toFixed(2)+','+(+lng).toFixed(2):'';}
function flush(){if(!Q.length||!ON)return;
  var ev=Q.splice(0,40);
  try{navigator.sendBeacon('/api/map',new Blob([JSON.stringify(
    {pg:location.pathname.slice(0,96),ev:ev})],{type:'text/plain'}));}catch(e){}}
function tell(e,o){try{o=o||{};
  if(SENT>=CAP)return;
  var r={e:e};
  var c=o.c||cell(o.lat,o.lng);if(c)r.c=c;
  if(isFinite(o.z))r.z=Math.max(0,Math.min(22,Math.round(o.z)));
  if(o.k&&/^[a-z]{2}:[a-z0-9-]{1,90}$/.test(o.k))r.k=o.k;
  else if(o.d)r.d=String(o.d).toLowerCase().replace(/[^a-z0-9_-]/g,'').slice(0,24);
  Q.push(r);SENT++;
  if(Q.length>=20)flush();}catch(x){}}
/* The view a reader settles on: after a move they made, still for 1.5 s,
   and not the same cell and zoom as the last one sent. */
function watch(map){try{
  var mine=false,tmo=null;
  function settle(){var c=map.getCenter(),z=map.getZoom(),key=cell(c.lat,c.lng)+'/'+Math.round(z);
    if(key===last)return;last=key;tell('view',{lat:c.lat,lng:c.lng,z:z});}
  map.on('movestart',function(e){if(e&&e.originalEvent)mine=true;});
  map.on('moveend',function(e){if(e&&e.originalEvent)mine=true;
    if(!mine)return;mine=false;clearTimeout(tmo);tmo=setTimeout(settle,1500);});
}catch(x){}}
addEventListener('pagehide',flush);
document.addEventListener('visibilitychange',function(){if(document.visibilityState==='hidden')flush();});
window.MDSENSE={watch:watch,tell:tell};
})();
"""


def map_js():
    return MAP_JS
