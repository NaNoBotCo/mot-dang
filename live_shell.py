"""live_shell.py — the numbers that go stale, refreshed in the reader's browser.

WHY THIS EXISTS
---------------
The weather tile and the PM2.5 tile were baked at build time, and the build is
a thing a person runs by hand. On the day this was written the widget portal
was showing weather from six days earlier and air from three. Both tiles said
so honestly — "ข้อมูล 2026-08-05" — which made them truthful and useless.

PM2.5 is the sharp end. `importers/make_air.py` says it plainly: for about a
third of the year the number that governs what somebody in Chiang Mai does
with their day is not the temperature, it is the dust. A three-day-old dust
reading during burning season is not a cautious version of the right answer,
it is a different answer.

THE SHAPE
---------
This does not replace the baked data — it sits on top of it, the same way
map_shell sits on top of the drawn SVG:

  * The baked figures render at build time and are what the reader sees the
    instant the page opens. No spinner, no empty tile, no layout shift.
  * After load, if the reader has any of these tiles on screen, one request
    per tile goes to Open-Meteo for exactly the cities they chose to show.
  * On success the numbers are replaced in place and the footer stops saying
    "as of <date>" and starts saying "สด · live".
  * On any failure — offline, blocked, rate-limited, malformed — nothing
    happens at all. The baked numbers and their honest date stay exactly as
    they were. A stale figure that admits its age beats an error message.

So the page never depends on the network to be a page, and never shows a
number without saying how old it is. Those two properties are the point.

ONE SOURCE FOR THE SCALE
------------------------
The PM2.5 band table is imported from `importers/make_air.py` rather than
retyped here. If the browser banded a figure differently from the importer,
the tile would change colour the moment the live value landed — same air,
different verdict — and the reader would rightly stop believing the tile.
Same reasoning for the WMO code table, which is handed in from build.py.
"""

import importlib.util
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parent

# The two endpoints, matched to the ones the importers already use so the live
# figure and the baked figure come from the same model. Keyless, CC-BY 4.0.
WEATHER_URL = "https://api.open-meteo.com/v1/forecast"
AIR_URL = "https://air-quality-api.open-meteo.com/v1/air-quality"


def _bands():
    """The Thai PCD band table, taken from the importer that bakes it."""
    spec = importlib.util.spec_from_file_location(
        "_make_air", ROOT / "importers" / "make_air.py")
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return [{"ceil": (None if c == float("inf") else c), "key": k,
             "th": th, "en": en, "colour": col}
            for c, k, th, en, col in mod.BANDS]


def enabled():
    """On unless data/live.json says otherwise. The kill switch exists because
    this is the one thing on the site that talks to somebody else's server at
    read time, and turning it off must not require a code change."""
    p = ROOT / "data" / "live.json"
    if not p.exists():
        return True
    try:
        return bool(json.loads(p.read_text()).get("enabled", True))
    except (ValueError, OSError):
        return True


def head(depth=0):
    if not enabled():
        return ""
    return '<script src="%slive.js" defer></script>' % ("../" * depth)


JS = r"""/* live.js — refresh the perishable tiles in the reader's browser.

   Nothing here runs unless one of those tiles is actually on the page, and
   nothing it does is required for the page to work. Every path that is not
   "the request came back and parsed" ends in leaving the baked numbers alone.
   A tile that says "as of Tuesday" is doing its job; a tile showing a spinner
   or an error where a number should be is not. */
(function(){
var C=window.MDLIVE_CFG||{};
/* Cheap exit for the ~30 pages that carry no widget at all. */
if(!document.querySelector('[data-wxpane],[data-airpane]'))return;

/* A local two-language span rather than md.js's mdBi. live.js and md.js are
   both deferred and md.js is emitted last, so leaning on it would be a load
   order gamble for four lines of markup. */
function esc(s){return String(s==null?'':s).replace(/[&<>"']/g,function(c){
  return {'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c];});}
function bi(th,en){return '<span class="bi"><span class="th" lang="th">'+esc(th)+
  '</span><span class="en" lang="en"><span class="th"> · </span>'+esc(en)+
  '</span></span>';}

function band(pm){
  if(pm==null||isNaN(pm))return null;
  var B=C.bands||[];
  for(var i=0;i<B.length;i++){if(B[i].ceil==null||pm<=B[i].ceil)return B[i];}
  return null;
}
function hhmm(iso){
  if(!iso)return '';
  var m=String(iso).match(/T(\d{2}:\d{2})/);
  return m?m[1]:'';
}
/* Only the cities the reader actually chose. md.js unhides the panes it finds
   in localStorage, so this both respects that choice and keeps the request
   to the few places somebody is looking at rather than all fifteen. */
function shown(sel){
  return [].slice.call(document.querySelectorAll(sel))
    .filter(function(el){return !el.hidden;});
}
function get(url){
  return fetch(url,{mode:'cors',credentials:'omit',cache:'no-store'})
    .then(function(r){if(!r.ok)throw 0;return r.json();});
}
/* Open-Meteo returns a bare object for one location and an array for many.
   Normalising here means the update paths never have to care. */
function rows(j){return Array.isArray(j)?j:[j];}

function foot(tile,observed){
  var f=tile.querySelector('.wfoot');if(!f)return;
  var t=hhmm(observed);
  f.innerHTML=bi('สด'+(t?' '+t+' น.':''),'live'+(t?' '+t:''))+' · Open-Meteo';
  tile.classList.add('is-live');
}

/* ---- weather ---------------------------------------------------------- */
function weather(){
  var panes=shown('[data-wxpane]');if(!panes.length)return;
  var want=panes.map(function(el){return el.dataset.wxpane;});
  var cities=(C.cities||[]).filter(function(c){return want.indexOf(c.id)>=0;});
  if(!cities.length)return;
  var qs='?latitude='+cities.map(function(c){return c.lat;}).join(',')+
    '&longitude='+cities.map(function(c){return c.lng;}).join(',')+
    '&current=temperature_2m,relative_humidity_2m,weather_code'+
    '&daily=temperature_2m_max,temperature_2m_min,weather_code'+
    '&timezone=auto&forecast_days=4';
  get(C.weatherUrl+qs).then(function(j){
    var out=rows(j),tile=document.getElementById('w-weather'),last='';
    cities.forEach(function(c,i){
      var d=out[i];if(!d||!d.current)return;
      var pane=document.querySelector('[data-wxpane="'+c.id+'"]');if(!pane)return;
      var code=d.current.weather_code,w=(C.wmo||{})[code]||(C.wmo||{})['-1']||['','',''];
      var t=d.current.temperature_2m;
      var q=function(s){return pane.querySelector(s);};
      if(q('.wxicon'))q('.wxicon').textContent=w[0];
      if(q('.wxtemp')&&t!=null)q('.wxtemp').innerHTML=Math.round(t)+'<sup>°C</sup>';
      if(q('.wxcond'))q('.wxcond').innerHTML=bi(w[1],w[2]);
      /* The forecast strip, rebuilt from today forward. The baked version
         picked days by comparing against BUILD_DATE; live, "today" is index
         0 of what the API just returned, so a stale build can no longer
         render a forecast made of days that already happened. */
      var dd=d.daily;
      if(q('.wxdays')&&dd&&dd.time){
        var out2='';
        for(var k=1;k<Math.min(4,dd.time.length);k++){
          var wk=(C.wmo||{})[dd.weather_code[k]]||['','',''];
          out2+='<span class="wxday"><b>'+wk[0]+'</b>'+
            Math.round(dd.temperature_2m_max[k])+'°</span>';
        }
        q('.wxdays').innerHTML=out2;
      }
      last=d.current.time||last;
    });
    if(tile)foot(tile,last);
  }).catch(function(){});
}

/* ---- the air ---------------------------------------------------------- */
function air(){
  var panes=shown('[data-airpane]');if(!panes.length)return;
  var want=panes.map(function(el){return el.dataset.airpane;});
  var places=(C.places||[]).filter(function(p){return want.indexOf(p.id)>=0;});
  if(!places.length)return;
  var qs='?latitude='+places.map(function(p){return p.lat;}).join(',')+
    '&longitude='+places.map(function(p){return p.lng;}).join(',')+
    '&current=pm2_5,pm10,us_aqi&hourly=pm2_5&past_days=7&forecast_days=1'+
    '&timezone=Asia/Bangkok';
  get(C.airUrl+qs).then(function(j){
    var out=rows(j),tile=document.getElementById('w-air'),last='';
    places.forEach(function(p,i){
      var d=out[i];if(!d||!d.current)return;
      var pane=document.querySelector('[data-airpane="'+p.id+'"]');if(!pane)return;
      var pm=d.current.pm2_5,b=band(pm);
      var q=function(s){return pane.querySelector(s);};
      if(q('.airnum')&&pm!=null){
        q('.airnum').innerHTML=Math.round(pm)+'<sup>µg/m³</sup>';
        if(b)q('.airnum').style.color=b.colour;
      }
      if(q('.airband')&&b)q('.airband').innerHTML=bi(b.th,b.en);
      /* Daily means from the hourly series, so the week of bars moves with
         the reading above it. A fresh number over a week-old chart would be
         a worse tile than either alone — the chart is the part that says
         whether to worry. */
      if(d.hourly&&d.hourly.time&&q('.airspark')){
        var by={},t=d.hourly.time,v=d.hourly.pm2_5;
        for(var k=0;k<t.length;k++){
          if(v[k]==null)continue;
          var day=t[k].slice(0,10);
          (by[day]=by[day]||[]).push(v[k]);
        }
        var keys=Object.keys(by).sort().slice(-7);
        var days=keys.map(function(dk){
          var a=by[dk];return a.reduce(function(x,y){return x+y;},0)/a.length;});
        if(days.length){
          var top=Math.max(Math.max.apply(null,days),40),bars='';
          days.forEach(function(val,k2){
            var h=Math.max(2,34*val/top),cb=band(val);
            bars+='<rect x="'+(k2*13)+'" y="'+(36-h).toFixed(1)+'" width="10" height="'+
              h.toFixed(1)+'" rx="2" fill="'+((cb&&cb.colour)||'#888')+'"></rect>';
          });
          var svg=q('.airspark');
          svg.setAttribute('viewBox','0 0 '+(days.length*13)+' 36');
          svg.innerHTML=bars;
          var lo=days[0],hi=days[days.length-1];
          var calm=b&&(b.key==='excellent'||b.key==='good');
          var tr=q('.airtrend');
          if(tr)tr.innerHTML=calm?bi('อากาศดีอยู่','the air is fine'):
            hi>lo*1.25?bi('แย่ลง','worsening'):
            hi<lo*0.8?bi('ดีขึ้น','improving'):bi('ทรงตัว','steady');
          /* The alt text has to move with the picture. A screen-reader
             description of last week's bars over this week's bars is the one
             failure nobody would ever see. */
          svg.setAttribute('aria-label',
            'PM2.5 '+days.length+' วัน · '+Math.round(lo)+'–'+Math.round(hi)+
            ' µg/m³ · latest '+Math.round(pm));
        }
      }
      last=d.current.time||last;
    });
    if(tile)foot(tile,last);
  }).catch(function(){});
}

/* After load, never before it. These tiles are already correct when the page
   paints; this is the part that can afford to wait. */
function go(){weather();air();}
if(document.readyState==='complete')setTimeout(go,0);
else addEventListener('load',function(){setTimeout(go,0);});
})();
"""

CSS = """/* A tile whose figures came from the network this minute. Deliberately
   quiet — a small mark on the footer, not a badge: the reader is here for the
   number, and the freshness only matters when they go looking for it. */
.wtile.is-live .wfoot{color:#3f7a4a}
.wtile.is-live .wfoot::before{content:"● ";font-size:.7em;vertical-align:.18em}
"""


def emit(g):
    """Write live.js with the city table, the WMO words and the PCD bands
    baked in, so the browser bands and names a figure exactly as the importer
    would have."""
    docs = g["DOCS"]
    if not enabled():
        return {"enabled": False}

    cities = [{"id": c["id"], "lat": c["lat"], "lng": c["lng"]}
              for c in (g.get("WEATHER_CITIES") or []) if c.get("lat") is not None]
    places = [{"id": p["id"], "lat": p["lat"], "lng": p["lng"]}
              for p in (g.get("AIR_PLACES") or []) if p.get("lat") is not None]
    # build.py's WMO table, keyed as strings for JSON.
    wmo = {str(k): [v[0], v[1], v[2]] for k, v in (g.get("WMO") or {}).items()}

    cfg = {"weatherUrl": WEATHER_URL, "airUrl": AIR_URL,
           "cities": cities, "places": places, "wmo": wmo, "bands": _bands()}
    (docs / "live.js").write_text(
        "window.MDLIVE_CFG=" + json.dumps(cfg, ensure_ascii=False,
                                          separators=(",", ":")) + ";\n" + JS)
    return {"enabled": True, "cities": len(cities), "places": len(places)}
