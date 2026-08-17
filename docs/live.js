window.MDLIVE_CFG={"weatherUrl":"https://api.open-meteo.com/v1/forecast","airUrl":"https://air-quality-api.open-meteo.com/v1/air-quality","cities":[{"id":"chiang-mai","lat":18.7883,"lng":98.9853},{"id":"chiang-rai","lat":19.9105,"lng":99.8406},{"id":"pai","lat":19.3583,"lng":98.4392},{"id":"mae-hong-son","lat":19.302,"lng":97.9654},{"id":"lampang","lat":18.2888,"lng":99.4909},{"id":"bangkok","lat":13.7563,"lng":100.5018},{"id":"phuket","lat":7.8804,"lng":98.3923},{"id":"udon-thani","lat":17.4138,"lng":102.787},{"id":"singapore","lat":1.3521,"lng":103.8198},{"id":"tokyo","lat":35.6762,"lng":139.6503},{"id":"london","lat":51.5072,"lng":-0.1276},{"id":"berlin","lat":52.52,"lng":13.405},{"id":"new-york","lat":40.7128,"lng":-74.006},{"id":"los-angeles","lat":34.0522,"lng":-118.2437},{"id":"sydney","lat":-33.8688,"lng":151.2093}],"places":[{"id":"chiang-mai","lat":18.7883,"lng":98.9853},{"id":"chiang-rai","lat":19.9105,"lng":99.8406},{"id":"pai","lat":19.3583,"lng":98.4392},{"id":"mae-hong-son","lat":19.302,"lng":97.9654},{"id":"lamphun","lat":18.5744,"lng":99.0087},{"id":"lampang","lat":18.2888,"lng":99.4909},{"id":"mae-sai","lat":20.4293,"lng":99.8814},{"id":"doi-inthanon","lat":18.5885,"lng":98.4867},{"id":"bangkok","lat":13.7563,"lng":100.5018}],"wmo":{"0":["☀️","แดดจ้า","Clear"],"1":["🌤","แดดบางส่วน","Mainly clear"],"2":["⛅","มีเมฆบางส่วน","Partly cloudy"],"3":["☁️","เมฆมาก","Overcast"],"45":["🌫","หมอก","Fog"],"48":["🌫","หมอกน้ำแข็ง","Rime fog"],"51":["🌦","ฝนปรอยเบา","Light drizzle"],"53":["🌦","ฝนปรอย","Drizzle"],"55":["🌧","ฝนปรอยหนัก","Heavy drizzle"],"61":["🌦","ฝนเล็กน้อย","Light rain"],"63":["🌧","ฝน","Rain"],"65":["🌧","ฝนหนัก","Heavy rain"],"71":["🌨","หิมะเล็กน้อย","Light snow"],"73":["🌨","หิมะ","Snow"],"75":["❄️","หิมะหนัก","Heavy snow"],"80":["🌦","ฝนไล่ช้าง","Rain showers"],"81":["🌧","ฝนไล่ช้างหนัก","Heavy showers"],"82":["⛈","ฝนกระหน่ำ","Violent showers"],"95":["⛈","พายุฝนฟ้าคะนอง","Thunderstorm"],"96":["⛈","พายุลูกเห็บ","Thunderstorm, hail"],"99":["⛈","พายุลูกเห็บหนัก","Thunderstorm, heavy hail"]},"bands":[{"ceil":15.0,"key":"excellent","th":"ดีมาก","en":"Very good","colour":"#3bb2d0"},{"ceil":25.0,"key":"good","th":"ดี","en":"Good","colour":"#4caf50"},{"ceil":37.5,"key":"moderate","th":"ปานกลาง","en":"Moderate","colour":"#f6c445"},{"ceil":75.0,"key":"unhealthy","th":"เริ่มมีผลต่อสุขภาพ","en":"Starting to affect health","colour":"#f08a3c"},{"ceil":null,"key":"hazardous","th":"มีผลต่อสุขภาพ","en":"Affects health","colour":"#d1495b"}]};
/* live.js — refresh the perishable tiles in the reader's browser.

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
