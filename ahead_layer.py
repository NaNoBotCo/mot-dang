"""ahead_layer.py — /ahead.html, ข้างหน้า · Ahead: turn the phone, see the picture taken that way.

NaN, 2026-09-28, on the compass idea: "that sounds fun. Can we scale it and start small?"
Small: it uses only the pictures whose facing direction is known (pics_layer rows with a
heading; importers/make_picture_meta.py fills them), and grows as rides add more.

On a tap the page asks for the reader's position (and, on iPhone, for the compass). It
fetches the picture cells around them (docs/data/pics/, pics_layer.py), draws every
picture within 400 m on a dial that turns with the phone, and shows large the one taken
in the direction the reader faces — near them, pointing the way they point. Each picture
opens its place page. Without a compass the dial holds north up and a tap picks.

The script holds the position in memory for the life of the page and writes it nowhere
(the same rule as here_layer.py); distances are straight lines.

Entry point: emit(g) with build.py's globals. Writes docs/ahead.html + docs/ahead.js.
"""

JS = r"""(function(){
var C=0.01,ABS=false,ME=null,FACE=null,ROWS=[],PICK=null,LOCK=false,IX=null,CELLS={},LAST=0;
var $=function(id){return document.getElementById(id);};
function esc(s){return String(s==null?'':s).replace(/[&<>"]/g,function(c){
 return {'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;'}[c];});}
function rad(x){return x*Math.PI/180;}
function m(a,b,c,d){var x=rad(c-a),y=rad(d-b)*Math.cos(rad((a+c)/2));return 6371000*Math.hypot(x,y);}
function brg(a,b,c,d){var y=Math.sin(rad(d-b))*Math.cos(rad(c)),
 x=Math.cos(rad(a))*Math.sin(rad(c))-Math.sin(rad(a))*Math.cos(rad(c))*Math.cos(rad(d-b));
 return (Math.atan2(y,x)*180/Math.PI+360)%360;}
function diff(a,b){var d=Math.abs(a-b)%360;return d>180?360-d:d;}
var DIRS=['เหนือ · N','ตะวันออกเฉียงเหนือ · NE','ตะวันออก · E','ตะวันออกเฉียงใต้ · SE',
 'ใต้ · S','ตะวันตกเฉียงใต้ · SW','ตะวันตก · W','ตะวันตกเฉียงเหนือ · NW'];
function dir(h){return DIRS[Math.round(h/45)%8];}
function far(d){return d<1000?Math.round(d/5)*5+' ม. · '+Math.round(d/5)*5+' m':(d/1000).toFixed(1)+' กม. · '+(d/1000).toFixed(1)+' km';}
var TH_M=['ม.ค.','ก.พ.','มี.ค.','เม.ย.','พ.ค.','มิ.ย.','ก.ค.','ส.ค.','ก.ย.','ต.ค.','พ.ย.','ธ.ค.'],
 EN_M=['Jan','Feb','Mar','Apr','May','Jun','Jul','Aug','Sep','Oct','Nov','Dec'];
function day(r){if(!r[6])return '';var mo=+r[6].slice(5,7)-1,d=+r[6].slice(8,10);
 return d+' '+TH_M[mo]+(r[7]?' '+r[7]+' น.':'')+' · '+d+' '+EN_M[mo]+(r[7]?', '+r[7]:'');}
function say(t){$('ahstate').innerHTML=t;}

function cell(k){if(!CELLS[k])CELLS[k]=fetch('data/pics/'+k+'.json').then(function(r){return r.ok?r.json():[];})
 .catch(function(){return [];});return CELLS[k];}
function load(){
 (IX||(IX=fetch('data/pics/index.json').then(function(r){return r.json();}))).then(function(ix){
  C=ix.cell;var cx=Math.floor(ME.lat/C),cy=Math.floor(ME.lon/C),ks=[];
  for(var i=-1;i<=1;i++)for(var j=-1;j<=1;j++){var k=(cx+i)+'_'+(cy+j);if(ix.cells[k])ks.push(k);}
  return Promise.all(ks.map(cell));})
 .then(function(all){ROWS=[].concat.apply([],all||[]).filter(function(r){return r[8]>=0;});paint(true);})
 .catch(function(){say('โหลดภาพไม่ได้ · the pictures did not load');});}

/* the one to show: near, in front of the reader, and looking the way they look */
function best(near){var f=FACE==null?null:FACE,b=null,bs=1e9;
 near.forEach(function(r){
  var s=r.d;
  if(f!=null){var off=r.d<25?0:diff(f,r.b),look=diff(f,r[8]);
   if(off>40||look>60)return;s=r.d*(1+off/40)*(1+look/60);}
  if(s<bs){bs=s;b=r;}});return b;}

function paint(force){
 if(!ME)return;var now=Date.now();if(!force&&now-LAST<250)return;LAST=now;
 var near=[];ROWS.forEach(function(r){r.d=m(ME.lat,ME.lon,r[0],r[1]);r.b=brg(ME.lat,ME.lon,r[0],r[1]);
  if(r.d<=400)near.push(r);});
 dial(near);
 if(!ROWS.length){say('ยังไม่มีภาพที่รู้ทิศแถวนี้ · no picture with a known direction near here yet');
  $('ahpic').hidden=true;return;}
 if(!near.length){say('ภาพที่รู้ทิศใกล้สุดอยู่ห่างเกิน 400 ม. · the nearest picture with a direction is more than 400 m away');
  $('ahpic').hidden=true;return;}
 var p=LOCK&&PICK?PICK:best(near);
 if(!p){
  /* nothing straight ahead: point the reader at the nearest one */
  var n=near.slice().sort(function(a,b){return a.d-b.d;})[0],t=((n.b-FACE+540)%360)-180;
  say(t>0?'หันขวา '+Math.round(t)+'° · turn right '+Math.round(t)+'°':'หันซ้าย '+Math.round(-t)+'° · turn left '+Math.round(-t)+'°');
  $('ahpic').hidden=true;PICK=null;return;}
 say(FACE==null?'ไม่มีเข็มทิศ · no compass here — north is up, tap a dot':'');
 if(p===PICK&&!force)return;PICK=p;show(p);}

function show(p){var box=$('ahpic');box.hidden=false;
 var full=p[2].replace('/band/','/site/');
 box.innerHTML='<a href="'+esc(p[3].replace(/^\//,''))+'"><img src="'+esc(full.replace(/^\//,''))+'" alt="'+esc(p[5]||p[4])+'"'+
  (p[10]?' width="'+p[10]+'" height="'+p[11]+'"':'')+'></a>'+
  '<p class="ahcap"><b>'+esc(p[4]||p[5])+'</b>'+(p[4]&&p[5]&&p[4]!==p[5]?'<span class="en" lang="en">'+esc(p[5])+'</span>':'')+
  '<i>'+far(p.d)+' · '+dir(p.b)+' · ภาพหันไป · facing '+dir(p[8])+'</i><i>'+esc(day(p))+'</i></p>';}

/* the dial: up is the way the reader faces (north without a compass); each dot a
   picture at its bearing and distance, with a tick for the way it looks */
function dial(near){var g=$('ahdots');if(!g)return;var up=FACE||0,R=110,out='';
 $('ahnorth').setAttribute('transform','rotate('+(-up)+' 120 120)');
 near.forEach(function(r,i){var a=rad(r.b-up),k=Math.min(r.d,400)/400*R,
  x=120+k*Math.sin(a),y=120-k*Math.cos(a),t=rad(r[8]-up);
  out+='<g class="dot'+(r===PICK?' on':'')+'" data-i="'+i+'"><line x1="'+x.toFixed(1)+'" y1="'+y.toFixed(1)+
   '" x2="'+(x+9*Math.sin(t)).toFixed(1)+'" y2="'+(y-9*Math.cos(t)).toFixed(1)+'"/><circle cx="'+x.toFixed(1)+
   '" cy="'+y.toFixed(1)+'" r="4.5"/></g>';});
 g.innerHTML=out;
 g.onclick=function(e){var el=e.target.closest('.dot');if(!el)return;PICK=near[+el.dataset.i];LOCK=true;
  show(PICK);dial(near);setTimeout(function(){LOCK=false;},6000);};}

function compass(e){var h=null;
 if(e.webkitCompassHeading!=null)h=e.webkitCompassHeading;
 else if(e.absolute&&e.alpha!=null)h=360-e.alpha;
 else return;
 if(e.type==='deviceorientation'&&e.webkitCompassHeading==null&&ABS)return;
 if(e.type==='deviceorientationabsolute')ABS=true;
 if(h==null)return;
 var so=(screen.orientation&&screen.orientation.angle)||window.orientation||0;
 FACE=(h+so+360)%360;$('ahface').textContent=dir(FACE)+' · '+Math.round(FACE)+'°';paint();}

function start(){
 var b=$('ahgo');b.disabled=true;say('กำลังหาตำแหน่ง · finding you…');
 /* iPhone asks first (inside this tap); elsewhere the events simply arrive. Both are
    heard: Android's absolute event, and iPhone's webkitCompassHeading on the plain one. */
 if(window.DeviceOrientationEvent&&DeviceOrientationEvent.requestPermission)
  DeviceOrientationEvent.requestPermission().catch(function(){});
 window.addEventListener('deviceorientationabsolute',compass);
 window.addEventListener('deviceorientation',compass);
 if(!navigator.geolocation){say('เบราว์เซอร์นี้ไม่บอกตำแหน่ง · this browser gives no position');b.disabled=false;return;}
 navigator.geolocation.watchPosition(function(p){
  var first=!ME;ME={lat:p.coords.latitude,lon:p.coords.longitude};
  $('ahwrap').hidden=false;b.hidden=true;if(first)load();else paint(true);
 },function(){say('ไม่ได้ตำแหน่ง · no position — location is off or was refused');b.disabled=false;},
 {enableHighAccuracy:true,maximumAge:5000,timeout:15000});}
$('ahgo').addEventListener('click',start);
})();
"""

CSS = """
.ah{max-width:40rem;margin:0 auto}
.ah .lede{color:var(--mute);font-size:.9rem;margin:.2rem 0 1rem}
#ahgo{display:flex;align-items:center;justify-content:center;gap:.5rem;width:100%;font-size:1.05rem}
#ahwrap[hidden],#ahpic[hidden]{display:none}
.ahtop{display:flex;align-items:center;gap:1rem;flex-wrap:wrap;margin:.6rem 0}
.ahdial{width:min(240px,60vw);height:auto;flex:0 0 auto}
.ahdial .ring{fill:none;stroke:var(--mute);stroke-opacity:.45;stroke-width:1.2}
.ahdial .you{fill:var(--ink)}
.ahdial .cone{fill:var(--gold-light,#f2d27a);opacity:.55}
.ahdial #ahnorth text{font:700 12px var(--mono,monospace);fill:var(--mute);text-anchor:middle}
.ahdial .dot circle{fill:var(--accent,#c13a2e);stroke:var(--panel,#fff);stroke-width:1.5;cursor:pointer}
.ahdial .dot line{stroke:var(--accent,#c13a2e);stroke-width:2}
.ahdial .dot.on circle{fill:var(--ink);r:6.5}
#ahface{font-family:var(--mono,monospace);font-size:.9rem}
#ahstate{font-size:.85rem;color:var(--mute);min-height:1.2em}
#ahpic{border:2px solid var(--ink);background:var(--panel)}
#ahpic img{width:100%;height:auto;display:block}
.ahcap{padding:.5rem .7rem .6rem;margin:0}
.ahcap b{display:block}
.ahcap .en{display:block;font-size:.8em;color:var(--mute)}
.ahcap i{display:block;font-style:normal;font-family:var(--mono,monospace);font-size:.75rem;color:var(--mute);margin-top:.2rem}
.ahcred{font-size:.7rem;color:var(--mute)}
"""


def body(icon):
    return f"""<div class="ah">
<h1><span class="th" lang="th">ข้างหน้า</span> <span class="en" lang="en">Ahead</span></h1>
<p class="lede"><span class="th" lang="th">หันโทรศัพท์ไปทางไหน ก็เห็นภาพที่ถ่ายไว้ทางนั้น ใกล้ตัวคุณ</span>
<span class="en" lang="en"> · turn your phone and see the picture taken the way you face, near you</span></p>
<button type="button" id="ahgo" class="btn">{icon("i-compass", 24)}<span>เริ่ม · Start</span></button>
<div id="ahwrap" hidden>
 <div class="ahtop">
  <svg class="ahdial" viewBox="0 0 240 240" role="img" aria-label="เข็มทิศและภาพรอบตัว · compass and the pictures around you">
   <circle class="ring" cx="120" cy="120" r="110"/><circle class="ring" cx="120" cy="120" r="55"/>
   <path class="cone" d="M120 120 L82 16 A110 110 0 0 1 158 16 Z"/>
   <g id="ahnorth"><text x="120" y="24">N</text><text x="120" y="226">S</text>
    <text x="220" y="124">E</text><text x="20" y="124">W</text></g>
   <g id="ahdots"></g><circle class="you" cx="120" cy="120" r="5"/>
  </svg>
  <div><p id="ahface"></p><p id="ahstate"></p>
  <p class="ahcred">วงนอก 400 ม. · outer ring 400 m · ระยะเส้นตรง · straight-line</p></div>
 </div>
 <div id="ahpic" hidden></div>
 <p class="ahcred">ภาพ · pictures NaN Peacock, CC BY 4.0</p>
</div>
</div>
<style>{CSS}</style>
<script src="ahead.js" defer></script>"""


def emit(g):
    docs = g["DOCS"]
    (docs / "ahead.js").write_text(JS)
    icon = g["svg_icon"]
    html = g["page"]("ข้างหน้า · Ahead — มดแดง", body(icon), 0, path="ahead.html",
                     desc="หันโทรศัพท์ไปทางไหน ก็เห็นภาพที่ถ่ายไว้ทางนั้น · Turn your phone and see "
                          "the picture taken the way you face, near you, in Chiang Mai.")
    (docs / "ahead.html").write_text(html)
    return "  ahead: ahead.html + ahead.js"
