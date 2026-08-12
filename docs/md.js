
// The markup twin of build.py's bi(). Anything the client fills in has to
// join its two languages the same way the server does, or a gloss hydrated by
// JS ends up jammed against the Thai ("สีส้มorange") in both-mode.
function mdBi(th,en){th=th==null?'':th;
if(!en)return '<span class="th" lang="th">'+th+'</span>';
var sep=/[·—–:-]\s*$/.test(th)?'':'<span class="th" lang="th"> · </span>';
return '<span class="bi"><span class="th" lang="th">'+th+'</span>'+
'<span class="en" lang="en">'+sep+en+'</span></span>';}

// ---- location: opt-in, never a gate -----------------------------------
// Every geolocation call on this site goes through here, for one reason: a
// browser permission prompt fired at a reader who has not asked for it is a
// hard stop, and in Thailand it is a hard stop that reads as a risk rather
// than a feature. People who back out of that dialog do not come back to the
// page — they leave, and nothing in our logs would ever tell us.
//
// So: nothing here runs on load. The prompt is reachable only from a tap on
// a control that says what it does, our own plain-language dialog goes in
// front of the browser's, and "no" is answered once and kept. Every caller
// gets a usable coordinate whether or not permission was ever granted,
// because the fallback is a named landmark, not an empty state.
const MDLOC=(()=>{
let OFF=false,gate=null;
// Two places people actually give directions from. The site spans two
// provinces, so the caller passes a latitude it already has on the page and
// gets back the right one — no third request to work out where "here" is.
const DEF={cm:{lat:18.7876,lng:98.9931,th:'ประตูท่าแพ',en:'Tha Phae Gate',src:'default'},
           cr:{lat:19.9094,lng:99.8325,th:'หอนาฬิกาเชียงราย',en:'Clock Tower',src:'default'}};
const near=lat=>(typeof lat==='number'&&lat>19.3)?DEF.cr:DEF.cm;
// A remembered origin is a place the reader chose, never a fix we were
// handed: a GPS coordinate is not written to disk anywhere on this site.
function origin(lat){
try{const v=JSON.parse(localStorage.getItem('md-origin'));
if(v&&typeof v.lat==='number'&&v.src!=='gps')return v;}catch(e){}
return near(lat);}
function remember(o){if(o&&o.src!=='gps'){
try{localStorage.setItem('md-origin',JSON.stringify(o));}catch(e){}}return o;}
// Said no once, asked never again — and the doors go with it, because a
// control that reopens a dialog the reader already refused is how a site
// teaches people to distrust it on sight.
function kill(){OFF=true;close();
document.querySelectorAll('[data-gps-door]').forEach(el=>el.remove());}
function close(){if(gate){gate.remove();gate=null;}}
function build(onYes){
gate=document.createElement('div');
gate.className='mdgate';gate.setAttribute('role','dialog');
gate.setAttribute('aria-modal','true');gate.setAttribute('aria-label',
'ใช้ตำแหน่งจริงของคุณไหม / Use your real location?');
gate.innerHTML='<div class="mdgatebox"><b>'+
mdBi('ใช้ตำแหน่งจริงของคุณไหม','Use your real location?')+'</b><p>'+
mdBi('ตำแหน่งของคุณอยู่ในเครื่องคุณเท่านั้น ไม่ถูกส่งออกไปไหน และไม่ถูกเก็บไว้ ใช้เพื่อเรียงลำดับในหน้านี้อย่างเดียว',
'Your location never leaves this device. It is not sent anywhere and not stored — it only sorts this page.')+
'</p><div class="mdgateacts"><button type="button" data-g="y">'+
mdBi('📍 ใช้ตำแหน่งของฉัน','Use my location')+'</button>'+
'<button type="button" data-g="n" class="mdgateno">'+mdBi('ไม่ต้อง','Not now')+
'</button></div></div>';
document.body.appendChild(gate);
gate.querySelector('[data-g="y"]').addEventListener('click',()=>{close();onYes();});
gate.querySelector('[data-g="n"]').addEventListener('click',kill);
gate.addEventListener('keydown',e=>{if(e.key==='Escape')close();});
gate.querySelector('[data-g="y"]').focus();}
// ok(point) on a real fix; nope() every other way this can end — refused,
// timed out, unsupported, or already denied at the OS level. Callers use
// nope() to fall back to something that works, never to show an error.
function ask(ok,nope){
if(OFF||!navigator.geolocation){nope&&nope();return;}
build(()=>{navigator.geolocation.getCurrentPosition(
p=>ok({lat:p.coords.latitude,lng:p.coords.longitude,src:'gps'}),
()=>{kill();nope&&nope();},
{enableHighAccuracy:true,timeout:10000,maximumAge:60000});});}
// Ask the browser what it already knows, so a door is never shown for a
// permission the OS has already refused.
if(navigator.permissions&&navigator.permissions.query){
try{navigator.permissions.query({name:'geolocation'}).then(st=>{
if(st.state==='denied')kill();
st.onchange=()=>{if(st.state==='denied')kill();};}).catch(()=>{});}catch(e){}}
return {ask,origin,remember,kill,near,get off(){return OFF;}};
})();

// ---- language: Thai, both, or English ---------------------------------
// Default is both. Someone who reads only one of the two should not have to
// find a control before the page makes sense to them. An earlier explicit
// choice — including 'th' or 'en' stored by the old two-way toggle — wins.
const B=document.body;
function mdSetLang(v){B.classList.remove('lang-en','lang-both');
if(v==='en')B.classList.add('lang-en');else if(v==='both')B.classList.add('lang-both');
try{localStorage.setItem('md-lang',v);}catch(e){}
document.querySelectorAll('.langbtn').forEach(b=>
b.setAttribute('aria-pressed',b.dataset.lang===v?'true':'false'));}
mdSetLang((()=>{let v=null;try{v=localStorage.getItem('md-lang');}catch(e){}
return (v==='th'||v==='en'||v==='both')?v:'both';})());
document.querySelectorAll('.langbtn').forEach(b=>
b.addEventListener('click',()=>mdSetLang(b.dataset.lang)));
// ---- hidden bell: the logo ant scurries ------------------------------
const logoAnt=document.querySelector('.logo .ant'),runner=document.getElementById('scurry');
logoAnt&&runner&&logoAnt.closest('.logo').addEventListener('click',()=>{
runner.classList.remove('go');void runner.offsetWidth;runner.classList.add('go');});
// ---- search ----------------------------------------------------------
const RROOT=document.documentElement.getAttribute('data-root')||'';
document.querySelectorAll('form.seek').forEach(f=>{f.addEventListener('submit',e=>{
e.preventDefault();const q=f.querySelector('input').value.trim();
if(q)location.href=RROOT+'search.html?q='+encodeURIComponent(q);});});
const resBox=document.getElementById('results');
async function loadIndex(){const r=await fetch(RROOT+'data/index.json');return r.json();}
if(resBox){(async()=>{
const q=new URLSearchParams(location.search).get('q')||'';
document.querySelector('form.seek input').value=q;
const idx=await loadIndex();const needle=q.toLowerCase();
const hits=q?idx.filter(e=>(e.n+' '+(e.e||'')+' '+(e.a||'')).toLowerCase().includes(needle)).slice(0,200):[];
document.getElementById('rescount').textContent=q?`${hits.length}`:'';
resBox.innerHTML=hits.map(e=>`<li><a href="${RROOT}${e.p}/p/${e.s}.html">${e.n}</a>`+
`${e.e&&e.e!==e.n?' <span class="count">'+e.e+'</span>':''}`+
` <span class="count">· ${e.pv}</span></li>`).join('')||
(q?'<li class="shelf">ไม่พบ — ลองคำอื่น / nothing found, try another word</li>':'');})();}
// ---- today's sky + fortune, chosen from a month baked at build time ---
// Nothing is fetched: build.py wrote 30 days into these files, so the page is
// right every morning without a rebuild and still makes no outside request.
const MD_TODAY=(()=>{const d=new Date();
return d.getFullYear()+'-'+String(d.getMonth()+1).padStart(2,'0')+'-'+String(d.getDate()).padStart(2,'0');})();
async function mdJSON(p){try{const r=await fetch(RROOT+p);return r.ok?await r.json():null;}
catch(e){return null;}}
// Today or nothing. This used to fall back to the earliest baked day, so once
// the window ran out every reader was quietly handed a month-old reading with
// today's date on it. A tile with no entry for today says so instead.
function mdPick(doc){if(!doc||!doc.days)return null;
return doc.days[MD_TODAY]||null;}
function mdStale(sel){document.querySelectorAll(sel).forEach(el=>{
if(el.querySelector('.wstale'))return;
const s=document.createElement('span');s.className='wfoot wstale';
s.innerHTML=mdBi('ยังไม่ได้อัปเดตสำหรับวันนี้','not updated for today');
el.appendChild(s);});}
// --- sky tile: moon + jupiter, drawn from baked positions
(async()=>{const host=document.getElementById('w-sky');if(!host)return;
const doc=await mdJSON('data/sky.json');const day=mdPick(doc);
if(!day){mdStale('#w-sky');return;}
const mc=host.querySelector('[data-skycap="moon"]');
// Through mdBi, not hand-built spans: building the pair by hand is what left
// "แรม 4 ค่ำWaning" jammed together with no separator, the same fault the
// Thai horoscope line had.
if(mc&&day.moon)mc.innerHTML=mdBi(
day.moon.phase_th+' · '+day.moon.thai_label_th+(day.moon.wan_phra?' · วันพระ':''),
day.moon.phase_en+' · '+day.moon.thai_label_en+(day.moon.wan_phra?' · wan phra':''));
const slides=[...host.querySelectorAll('.skyslide')];
const dots=[...host.querySelectorAll('[data-skydot]')];let si=0;
const go=i=>{si=(i+slides.length)%slides.length;
slides.forEach((s,n)=>{s.hidden=n!==si;});
dots.forEach((d,n)=>d.classList.toggle('on',n===si));};
dots.forEach(d=>d.addEventListener('click',()=>{go(+d.dataset.skydot);clearInterval(window.__skyT);}));
if(slides.length>1)window.__skyT=setInterval(()=>go(si+1),6000);})();
// --- fortune, horoscope, hexagram, and the day's colour
(async()=>{const doc=await mdJSON('data/fortune.json');const day=mdPick(doc);
if(!day){mdStale('#w-fortune,#w-horoscope,#w-divination');return;}
const t=day.thai;
// สีประจำวัน: the whole page borrows the day's colour
if(t&&t.hex)document.documentElement.style.setProperty('--day',t.hex);
const setF=(k,v)=>{const el=document.querySelector(`[data-fo="${k}"]`);if(el&&v!=null)el.textContent=v;};
if(t){setF('day_th',t.th);setF('strength',t.strength);setF('zodiac',t.zodiac_year_th);
const sw=document.querySelector('[data-fo="swatch"]');if(sw)sw.style.background=t.hex;
const bl=(sel,a,b)=>{const el=document.querySelector(sel);
if(el)el.innerHTML=mdBi(a,b);};
bl('[data-fo="colour"]',t.colour_th,t.colour_en);
bl('[data-fo="buddha"]',t.buddha_th,t.buddha_en);
bl('[data-fo="planet"]',t.planet_th,t.planet_en);
bl('[data-fo="how"]',t.lucky.how_th,t.lucky.how_en);
setF('nums',t.lucky.two.join(' ')+' · '+t.lucky.three);
const thl=document.querySelector('[data-ho="th_line"]');
// Through mdBi, not hand-built spans: the " · " that separates the two
// languages lives inside the English span and is itself marked Thai, so
// hand-rolling the markup ran the sentences together in ไทย + EN mode.
if(thl)thl.innerHTML=mdBi(
'วันนี้เป็น'+t.th+' สีประจำวันคือ'+t.colour_th+
' พระประจำวันคือ'+t.buddha_th+' กำลังพระเคราะห์ '+t.strength,
'Today is '+t.en+'. Its colour is '+t.colour_en+', its image is '+
t.buddha_en+', and its planetary strength is '+t.strength+'.');}
// european: reader picks a sign, choice is remembered
const eu=day.european;const pick=document.querySelector('[data-ho="signpick"]');
if(eu&&pick){const saved=localStorage.getItem('md.sign');
if(saved!==null&&eu.signs[+saved])pick.value=saved;
const drawEU=()=>{const s=eu.signs[+pick.value];if(!s)return;
const a=document.querySelector('[data-ho="eu_aspect"]'),l=document.querySelector('[data-ho="eu_line"]'),
m=document.querySelector('[data-ho="eu_moon"]');
if(a)a.innerHTML=mdBi(s.aspect_th,s.aspect_en);
if(l)l.innerHTML=mdBi(s.line_th,s.line_en);
if(m)m.innerHTML=mdBi('ดวงจันทร์อยู่'+eu.moon_sign_th,'The Moon is in '+eu.moon_sign_en);};
pick.addEventListener('change',()=>{try{localStorage.setItem('md.sign',pick.value);}catch(e){}drawEU();});
drawEU();}
// chinese
const cn=day.chinese;
if(cn){const p=document.querySelector('[data-ho="cn_pillar"]'),l=document.querySelector('[data-ho="cn_line"]');
if(p)p.textContent=cn.pillar+' · '+cn.animal;
if(l)l.innerHTML=mdBi(cn.relation_th||'',cn.relation_en||'');}
// hexagram: draw the six lines from the king wen number
const hx=day.hexagram;
if(hx&&hx.number){const box=document.querySelector('[data-hx="lines"]');
const set=(k,v)=>{const e=document.querySelector(`[data-hx="${k}"]`);if(e&&v!=null)e.textContent=v;};
set('zh',hx.zh);set('pinyin',hx.pinyin);set('en',hx.en);set('gloss',hx.gloss);
if(box&&hx.bits){box.innerHTML=hx.bits.slice().reverse().map((b,i)=>
`<span class="hxline ${b?'yang':'yin'} ${hx.moving&&hx.moving.includes(6-i)?'moving':''}"></span>`).join('');}}
// tabs
document.querySelectorAll('.hotab').forEach(b=>{b.addEventListener('click',()=>{
document.querySelectorAll('.hotab').forEach(x=>x.classList.remove('on'));b.classList.add('on');
document.querySelectorAll('.hopane').forEach(p=>{p.hidden=p.dataset.hopane!==b.dataset.hotab;});});});
})();
// --- katha carousel
(()=>{const cards=[...document.querySelectorAll('[data-kacard]')];
const dots=[...document.querySelectorAll('[data-kadot]')];if(!cards.length)return;let ki=0;
const go=i=>{ki=(i+cards.length)%cards.length;cards.forEach((c,n)=>{c.hidden=n!==ki;});
dots.forEach((d,n)=>d.classList.toggle('on',n===ki));};
dots.forEach(d=>d.addEventListener('click',()=>{go(+d.dataset.kadot);clearInterval(window.__kaT);}));
if(cards.length>1)window.__kaT=setInterval(()=>go(ki+1),9000);})();
// --- เซียมซี: shake, a stick falls, read the slip
(()=>{const host=document.getElementById('w-siamsi');if(!host)return;
let sticks=[];try{sticks=JSON.parse(host.dataset.siamsi||'[]');}catch(e){return;}
if(!sticks.length)return;
const tube=host.querySelector('[data-ss="tube"]'),out=host.querySelector('[data-ss="out"]'),
btn=host.querySelector('[data-ss="shake"]');
const V={'ดี':['ดี','good'],'กลาง':['กลาง','middling'],'ระวัง':['ระวัง','take care']};
btn.addEventListener('click',()=>{
if(tube.classList.contains('shaking'))return;
tube.classList.add('shaking');out.hidden=true;
setTimeout(()=>{tube.classList.remove('shaking');
const s=sticks[Math.floor(Math.random()*sticks.length)];
host.querySelector('[data-ss="num"]').textContent='ใบที่ '+s.n;
const v=V[s.verdict]||[s.verdict,s.verdict];
const vd=host.querySelector('[data-ss="verdict"]');
vd.innerHTML=mdBi(v[0],v[1]);
vd.className='ssverdict v-'+(s.verdict==='ดี'?'good':s.verdict==='ระวัง'?'care':'mid');
host.querySelector('[data-ss="text"]').innerHTML=
mdBi(s.th,s.en);
// the slip points somewhere in the directory: unhide the door for this verdict
host.querySelectorAll('.ssdoor').forEach(d=>{d.hidden=d.dataset.ssdoor!==s.verdict;});
out.hidden=false;},900);});})();
// ---- widgets: choices live in localStorage, no account, no tracking --
function wLoad(k,d){try{const v=JSON.parse(localStorage.getItem(k));
return Array.isArray(v)?v:d;}catch(e){return d;}}
function wSave(k,v){try{localStorage.setItem(k,JSON.stringify(v));}catch(e){}}
// gear buttons flip a tile to its picker
document.querySelectorAll('.wcog').forEach(b=>{b.addEventListener('click',()=>{
const p=document.querySelector(`.wpick[data-wpickfor="${b.dataset.wpick}"]`);
if(p)p.hidden=!p.hidden;});});
document.querySelectorAll('.wpick').forEach(p=>{p.addEventListener('click',e=>{
if(e.target===p)p.hidden=true;});});
// --- weather: rotate through the cities the reader picked
const wxPanes=[...document.querySelectorAll('.wxpane')];
if(wxPanes.length){
let wxSel=wLoad('md.wx',['chiang-mai','chiang-rai']);
const wxBoxes=[...document.querySelectorAll('[data-wxc]')];
const wxDraw=()=>{if(!wxSel.length)wxSel=['chiang-mai'];
wxPanes.forEach(p=>{p.hidden=true;});
let i=0;const show=()=>{const id=wxSel[i%wxSel.length];
wxPanes.forEach(p=>{p.hidden=p.dataset.wxpane!==id;});i++;};
show();clearInterval(window.__wxT);
if(wxSel.length>1)window.__wxT=setInterval(show,4000);};
wxBoxes.forEach(b=>{b.checked=wxSel.includes(b.dataset.wxc);
b.addEventListener('change',()=>{wxSel=wxBoxes.filter(x=>x.checked).map(x=>x.dataset.wxc);
wSave('md.wx',wxSel);wxDraw();});});
wxDraw();}
// --- air: same picker as the weather tile, its own stored choice
const airPanes=[...document.querySelectorAll('.airpane')];
if(airPanes.length){
let airSel=wLoad('md.air',['chiang-mai']);
const airBoxes=[...document.querySelectorAll('[data-airc]')];
const airDraw=()=>{if(!airSel.length)airSel=['chiang-mai'];
airPanes.forEach(p=>{p.hidden=true;});
let i=0;const show=()=>{const id=airSel[i%airSel.length];
airPanes.forEach(p=>{p.hidden=p.dataset.airpane!==id;});i++;};
show();clearInterval(window.__airT);
if(airSel.length>1)window.__airT=setInterval(show,4000);};
airBoxes.forEach(b=>{b.checked=airSel.includes(b.dataset.airc);
b.addEventListener('change',()=>{airSel=airBoxes.filter(x=>x.checked).map(x=>x.dataset.airc);
wSave('md.air',airSel);airDraw();});});
airDraw();}
// --- clocks: Intl does the conversion, so nothing is fetched
const tzRows=[...document.querySelectorAll('.tzrow')];
if(tzRows.length){
let tzSel=wLoad('md.tz',['chiang-mai','london','new-york']);
const tzBoxes=[...document.querySelectorAll('[data-tzc]')];
const shift=document.getElementById('tzshift'),shiftOut=document.getElementById('tzshiftout');
const tzDraw=()=>{const off=shift?parseInt(shift.value,10):0;
if(shiftOut)shiftOut.textContent=(off>0?'+':'')+off+'h';
const base=new Date(Date.now()+off*3600000);
tzRows.forEach(r=>{const on=tzSel.includes(r.dataset.tzrow);r.hidden=!on;
if(!on)return;
try{const f=new Intl.DateTimeFormat('en-GB',{timeZone:r.dataset.tz,hour:'2-digit',
minute:'2-digit',hour12:false});
const d=new Intl.DateTimeFormat('en-GB',{timeZone:r.dataset.tz,weekday:'short'});
r.querySelector('.tztime').textContent=f.format(base);
r.querySelector('.tzday').textContent=d.format(base);}catch(e){}});};
tzBoxes.forEach(b=>{b.checked=tzSel.includes(b.dataset.tzc);
b.addEventListener('change',()=>{tzSel=tzBoxes.filter(x=>x.checked).map(x=>x.dataset.tzc);
wSave('md.tz',tzSel);tzDraw();});});
if(shift)shift.addEventListener('input',tzDraw);
tzDraw();setInterval(tzDraw,15000);}
// --- cinema: one pane per screen
const cnPick=document.querySelector('.cnpick');
if(cnPick){const panes=[...document.querySelectorAll('[data-cnpane]')];
const cnDraw=()=>{panes.forEach(p=>{p.hidden=p.dataset.cnpane!==cnPick.value;});};
const saved=localStorage.getItem('md.cn');
if(saved&&[...cnPick.options].some(o=>o.value===saved))cnPick.value=saved;
cnPick.addEventListener('change',()=>{try{localStorage.setItem('md.cn',cnPick.value);}catch(e){}
cnDraw();});cnDraw();}
// --- showtimes: fade the screenings that have already started. Only when the
// baked sheet really is today's; on any other day the tile stops saying
// "today" — it retitles itself with the day the sheet belongs to and wears
// the same not-updated note the fortune tiles use. A four-day-old Saturday
// sheet presented as tonight is the tile lying.
(()=>{const host=document.getElementById('w-cinema');if(!host)return;
if(host.dataset.cndate!==MD_TODAY){
const h=host.querySelector('h3');
if(h&&host.dataset.cnth)h.innerHTML='🎬 '+mdBi(host.dataset.cnth,host.dataset.cnen||host.dataset.cnth);
mdStale('#w-cinema');return;}
const mark=()=>{const n=new Date(),hm=n.getHours()*60+n.getMinutes();
host.querySelectorAll('.cnt').forEach(el=>{const p=(el.dataset.t||'').split(':');
if(p.length!==2)return;
el.classList.toggle('past',(+p[0])*60+(+p[1])<hm);});};
mark();setInterval(mark,60000);})();
// --- weather: the conditions block is a snapshot. The footer already dates
// it; once the snapshot is not from today, say so where the eye is.
(()=>{const w=document.getElementById('w-weather');if(!w)return;
const g=(w.dataset.wxgen||'').slice(0,10);
if(g&&g!==MD_TODAY)mdStale('#w-weather');})();
// --- events carousel
const carousel=document.querySelector('[data-carousel]');
if(carousel){const slides=[...carousel.querySelectorAll('.evslide')];
const dots=[...document.querySelectorAll('[data-evdot]')];let ci=0;
const go=i=>{ci=(i+slides.length)%slides.length;
slides.forEach((s,n)=>{s.hidden=n!==ci;});
dots.forEach((d,n)=>d.classList.toggle('on',n===ci));};
dots.forEach(d=>d.addEventListener('click',()=>{go(+d.dataset.evdot);
clearInterval(window.__evT);}));
if(slides.length>1)window.__evT=setInterval(()=>go(ci+1),5000);}
// ---- events page filters --------------------------------------------
const evf=document.getElementById('evfilters');
if(evf){const cards=[...document.querySelectorAll('.evcard')];
evf.querySelectorAll('button').forEach(b=>{b.addEventListener('click',()=>{
evf.querySelectorAll('button').forEach(x=>x.classList.remove('on'));
b.classList.add('on');const f=b.dataset.evf;
cards.forEach(c=>{const rec=c.dataset.recurring==='1',map=c.dataset.mapped==='1';
const show=f==='all'||(f==='recurring'&&rec)||(f==='once'&&!rec)||(f==='mapped'&&map);
c.style.display=show?'':'none';});
// hide a day/month heading whose whole grid just went empty
document.querySelectorAll('.evgrid').forEach(g=>{
const any=[...g.children].some(c=>c.style.display!=='none');
g.style.display=any?'':'none';
const h=g.previousElementSibling;
if(h&&h.classList.contains('evday'))h.style.display=any?'':'none';});});});}
// ---- random place (🎲) ----------------------------------------------
document.querySelectorAll('.rand').forEach(a=>{a.addEventListener('click',async e=>{
e.preventDefault();const idx=await loadIndex();
const pick=idx[Math.floor(Math.random()*idx.length)];
location.href=RROOT+pick.p+'/p/'+pick.s+'.html';});});
// ---- sort toolbar: name / distance ----------------------------------
// ก→ฮ sorts by the name the reader can actually see. A row carries both, and
// in English-only mode sorting by the Thai one puts every list in an order
// that reads as no order at all.
function mdSortKey(el){
return (B.classList.contains('lang-en')&&el.dataset.ne)||el.dataset.n||'';}
const dirList=document.querySelector('ul.dir[data-sortable]');
if(dirList){
const items=[...dirList.children];
const byName=document.getElementById('sort-name'),byDist=document.getElementById('sort-dist');
byName&&byName.addEventListener('click',()=>{
items.sort((a,b)=>mdSortKey(a).localeCompare(mdSortKey(b),'th'));
items.forEach(li=>{const d=li.querySelector('.dist');d&&d.remove();dirList.appendChild(li);});
dirList.classList.remove('ranked');
document.querySelectorAll('.toolbar button').forEach(x=>x.classList.remove('on'));
byName.classList.add('on');});
// Sorting by distance from a point the reader granted us. The old version
// called getCurrentPosition straight off the tap and, when that was refused,
// raised an alert() — a dead end whose only cause was "no location", which
// is precisely the screen this site must never show.
const sortByDist=pt=>{const R=6371;
items.forEach(li=>{const lat=parseFloat(li.dataset.lat),lng=parseFloat(li.dataset.lng);
if(isNaN(lat)){li.dataset.km=1e9;return;}
const dLa=(lat-pt.lat)*Math.PI/180,dLo=(lng-pt.lng)*Math.PI/180;
const h=Math.sin(dLa/2)**2+Math.cos(pt.lat*Math.PI/180)*Math.cos(lat*Math.PI/180)*Math.sin(dLo/2)**2;
li.dataset.km=2*R*Math.asin(Math.sqrt(h));});
items.sort((a,b)=>a.dataset.km-b.dataset.km);
items.forEach(li=>{let d=li.querySelector('.dist');const km=parseFloat(li.dataset.km);
if(km<1e8){if(!d){d=document.createElement('span');d.className='dist';li.appendChild(d);}
d.textContent=' · '+(km<1?Math.round(km*1000)+' ม.':km.toFixed(1)+' กม.');}
dirList.appendChild(li);});
dirList.classList.remove('ranked');
document.querySelectorAll('.toolbar button').forEach(x=>x.classList.remove('on'));
byDist&&byDist.classList.add('on');};
// Refused, or already denied at the OS level. The list still sorts — by name,
// which is the order it was in — and the distance door removes itself rather
// than sitting there waiting to ask again.
const distDeclined=()=>{byName&&byName.click();};
byDist&&byDist.addEventListener('click',()=>{MDLOC.ask(sortByDist,distDeclined);});
// ---- ant rank sorts: most complete / recently walked / needs love ----
// The two completeness sorts also reveal the per-row 🐜N chips (.ranked on
// the list): once the reader has asked "which listings are filled in", the
// score is the subject and hiding it makes the sort look broken. Every other
// order puts the chips away again.
const btns=[...document.querySelectorAll('.toolbar button')];
const reorder=(btn,cmp,ants)=>{if(!btn)return;btn.addEventListener('click',()=>{
items.sort(cmp);
items.forEach(li=>{const d=li.querySelector('.dist');d&&d.remove();dirList.appendChild(li);});
dirList.classList.toggle('ranked',!!ants);
btns.forEach(x=>x&&x.classList.remove('on'));btn.classList.add('on');});};
const nm=(a,b)=>mdSortKey(a).localeCompare(mdSortKey(b),'th');
const rk=li=>parseInt(li.dataset.rank||'0',10);
reorder(document.getElementById('sort-rank'),(a,b)=>rk(b)-rk(a)||nm(a,b),true);
reorder(document.getElementById('sort-love'),(a,b)=>rk(a)-rk(b)||nm(a,b),true);
const rw=li=>parseInt(li.dataset.royal||'0',10);
reorder(document.getElementById('sort-royal'),(a,b)=>rw(b)-rw(a)||nm(a,b));
reorder(document.getElementById('sort-hon'),
(a,b)=>(parseInt(b.dataset.hon||'0',10)-parseInt(a.dataset.hon||'0',10))||rk(b)-rk(a)||nm(a,b));
reorder(document.getElementById('sort-fresh'),
(a,b)=>(b.dataset.upd||'').localeCompare(a.dataset.upd||'')||rk(b)-rk(a)||nm(a,b));
// ---- facet chips: keep only rows that have ALL the picked things ------
// AND, not OR, because the question is always "somewhere with a cash machine
// AND somewhere to sit", never "either one". The heading count follows the
// filter so it never contradicts what is on screen.
const fbar=document.querySelector('[data-facetbar]');
if(fbar){const on=new Set();const h1c=document.querySelector('h1 .count');
const total=items.length;
const paint=()=>{let shown=0;
items.forEach(li=>{const has=new Set((li.dataset.facets||'').split(' ').filter(Boolean));
const ok=[...on].every(f=>has.has(f));li.classList.toggle('fhide',!ok);if(ok)shown++;});
fbar.querySelectorAll('.fchip').forEach(b=>b.classList.toggle('on',on.has(b.dataset.f)));
if(h1c)h1c.textContent='('+shown.toLocaleString()+(shown<total?' / '+total.toLocaleString():'')+')';};
fbar.querySelectorAll('.fchip').forEach(b=>b.addEventListener('click',()=>{
const f=b.dataset.f;if(!f){on.clear();}else if(on.has(f)){on.delete(f);}else{on.add(f);}
paint();}));}}
// ---- copy link --------------------------------------------------------
document.querySelectorAll('.copylink').forEach(b=>{b.addEventListener('click',async()=>{
await navigator.clipboard.writeText(b.dataset.url);
b.textContent=b.dataset.done;setTimeout(()=>b.textContent=b.dataset.label,1500);});});
// ---- native share (Web Share API where supported) ---------------------
if(navigator.share){document.querySelectorAll('[data-native]').forEach(b=>{
b.style.display='';b.addEventListener('click',()=>{
navigator.share({title:b.dataset.title,url:b.dataset.url}).catch(()=>{});});});}
// ---- currency converter: recompute on input, baked rates, no live call --
// Stands on its own. It used to sit inside the day-colour block below, which
// is guarded on #daycolor — an element the home page does not carry — so on
// the one page that has the converter the listener was never attached and the
// figures sat frozen at whatever build.py baked for 100 baht.
const fxamount=document.getElementById('fxamount');
if(fxamount){const recalc=()=>{const amt=parseFloat(fxamount.value)||0;
document.querySelectorAll('.fxout').forEach(el=>{
el.textContent=(amt*parseFloat(el.dataset.rate)).toLocaleString(undefined,
{minimumFractionDigits:2,maximumFractionDigits:2});});};
fxamount.addEventListener('input',recalc);
fxamount.addEventListener('change',recalc);recalc();}
// ---- home modules: day colour + ticker + personalize ------------------
const day=document.getElementById('daycolor');
if(day){const names=['อาทิตย์','จันทร์','อังคาร','พุธ','พฤหัสบดี','ศุกร์','เสาร์'];
const ens=['Sunday','Monday','Tuesday','Wednesday','Thursday','Friday','Saturday'];
const cols=[['แดง','red','#C22'],['เหลือง','yellow','#E7B10A'],['ชมพู','pink','#E77'],
['เขียว','green','#2A7'],['ส้ม','orange','#E80'],['ฟ้า','light blue','#59F'],['ม่วง','purple','#96C']];
const d=new Date().getDay(),c=cols[d],be=new Date().getFullYear()+543;
day.innerHTML=`<span class="swatch" style="background:${c[2]}"></span>`+
`<span class="th">วัน${names[d]} — สีมงคลวันนี้: ${c[0]} · พ.ศ. ${be}</span>`+
`<span class="en">${ens[d]} — today's auspicious colour: ${c[1]} · B.E. ${be}</span>`;}
// ---- my page: pins + updates + daily pick + bookmarks + notes ---------
const H=s=>String(s).replace(/[&<>"]/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;'}[c]));
const pinpick=document.getElementById('pinpick');
if(pinpick){
const PULSE=JSON.parse(document.getElementById('pulse').textContent);
const DEFAULT_PINS=['cm/wat','cm/food','cr/wat'];
const rawPins=localStorage.getItem('md-pins');
const pins=new Set(rawPins===null?DEFAULT_PINS:JSON.parse(rawPins));
if(rawPins===null)localStorage.setItem('md-pins',JSON.stringify([...pins]));
const seen=JSON.parse(localStorage.getItem('md-seen')||'{}');
const shelf=document.getElementById('myshelf');
function unpin(pc){pins.delete(pc);localStorage.setItem('md-pins',JSON.stringify([...pins]));
const cb=pinpick.querySelector(`input[data-pc="${pc}"]`);if(cb)cb.checked=false;renderPins();}
async function renderPins(){
if(!pins.size){shelf.innerHTML='<p class="shelf">ยังไม่ได้ปักหมวด — เลือกด้านล่าง / no shelves pinned yet — pick below</p>';return;}
const idx=await loadIndex();
shelf.innerHTML=[...pins].map(pc=>{
const[pv,cat]=pc.split('/');const m=PULSE[pv]&&PULSE[pv][cat];if(!m)return'';
const fresh=seen[pc]!=null&&m.n>seen[pc]?` <span class="badge">+${m.n-seen[pc]} ใหม่/new</span>`:'';
const sample=idx.filter(e=>e.p===pv&&e.c&&e.c.includes(cat)).slice(0,3);
const preview=sample.map(e=>`<li><a href="${pv}/p/${e.s}.html">${H(e.n)}</a></li>`).join('')
||'<li class="shelf">🐜</li>';
return `<div class="topicwidget"><button class="unpin" data-pc="${pc}" title="ถอดปัก / unpin">✕</button>`+
`<h4><a href="${pv}/${cat}/index.html">${H(m.t)}</a> `+
`<span class="count">(${m.n.toLocaleString()}) · ${H(m.v)}</span>${fresh}</h4>`+
`<ul class="preview">${preview}</ul></div>`;}).join('');
shelf.querySelectorAll('.unpin').forEach(b=>b.addEventListener('click',()=>unpin(b.dataset.pc)));}
pinpick.querySelectorAll('input').forEach(cb=>{cb.checked=pins.has(cb.dataset.pc);
cb.addEventListener('change',()=>{cb.checked?pins.add(cb.dataset.pc):pins.delete(cb.dataset.pc);
localStorage.setItem('md-pins',JSON.stringify([...pins]));renderPins();});});
renderPins();
[...pins].forEach(pc=>{const[pv,cat]=pc.split('/');
if(PULSE[pv]&&PULSE[pv][cat])seen[pc]=PULSE[pv][cat].n;});
localStorage.setItem('md-seen',JSON.stringify(seen));
(async()=>{const el=document.getElementById('dailypick');if(!el)return;
const idx=await loadIndex();const pc=[...pins];
let pool=idx.filter(e=>e.c&&pc.some(p=>{const[pv,cat]=p.split('/');
return e.p===pv&&e.c.includes(cat);}));
if(!pool.length)pool=idx;
const t=new Date(),seed=t.getFullYear()*372+(t.getMonth()+1)*31+t.getDate();
const pick=pool[seed%pool.length];
el.innerHTML=`<a href="${pick.p}/p/${pick.s}.html">${H(pick.n)}</a> <span class="count">· ${H(pick.pv)}</span>`;})();
// ---- widget gallery: her other projects, opt-in iframes ----------------
const wgal=document.getElementById('widgetgallery');
if(wgal){const STARTERS=JSON.parse(document.getElementById('widgets-data').textContent);
const added=document.getElementById('widgetboxes');
function myWidgets(){return JSON.parse(localStorage.getItem('md-widgets')||'[]');}
function renderWidgets(){const list=myWidgets();
added.innerHTML=list.map((w,i)=>`<div class="widgetbox"><div class="wtitle">`+
`<span>${H(w.n)}</span><button data-i="${i}" title="เอาออก / remove">✕</button></div>`+
`<iframe src="${H(w.u)}" loading="lazy" sandbox="allow-scripts allow-same-origin allow-popups"></iframe></div>`).join('');
added.querySelectorAll('button').forEach(b=>b.addEventListener('click',()=>{
const list=myWidgets();list.splice(+b.dataset.i,1);
localStorage.setItem('md-widgets',JSON.stringify(list));renderWidgets();renderGallery();}));}
function addWidget(n,u){if(!u)return;const list=myWidgets();
if(list.some(w=>w.u===u))return;list.push({n,u});
localStorage.setItem('md-widgets',JSON.stringify(list));renderWidgets();renderGallery();}
function renderGallery(){const have=new Set(myWidgets().map(w=>w.u));
wgal.innerHTML=STARTERS.map(w=>`<button data-u="${H(w.url)}" data-n="${H(w.th)}"`+
`${have.has(w.url)?' disabled':''}>+ ${H(w.th)}</button>`).join('');
wgal.querySelectorAll('button:not(:disabled)').forEach(b=>b.addEventListener('click',()=>
addWidget(b.dataset.n,b.dataset.u)));}
renderWidgets();renderGallery();
const awf=document.getElementById('addwidgetform');
awf.addEventListener('submit',e=>{e.preventDefault();
const n=awf.querySelector('[name=n]').value.trim(),u=awf.querySelector('[name=u]').value.trim();
if(!n||!u)return;addWidget(n,u);awf.reset();});}
const bmList=document.getElementById('bmlist'),bmForm=document.getElementById('bmform');
function renderBm(){const bm=JSON.parse(localStorage.getItem('md-bm')||'[]');
bmList.innerHTML=bm.map((b,i)=>`<li><a href="${H(b.u)}" rel="noopener">${H(b.n)}</a> `+
`<button class="bmdel" data-i="${i}" title="ลบ">✕</button></li>`).join('')||
'<li class="shelf">ยังไม่มีลิงก์ / no links yet</li>';
bmList.querySelectorAll('.bmdel').forEach(btn=>btn.addEventListener('click',()=>{
const b=JSON.parse(localStorage.getItem('md-bm')||'[]');b.splice(+btn.dataset.i,1);
localStorage.setItem('md-bm',JSON.stringify(b));renderBm();}));}
renderBm();
bmForm.addEventListener('submit',e=>{e.preventDefault();
const n=bmForm.querySelector('[name=n]').value.trim(),u=bmForm.querySelector('[name=u]').value.trim();
if(!n||!u)return;const b=JSON.parse(localStorage.getItem('md-bm')||'[]');
b.push({n,u});localStorage.setItem('md-bm',JSON.stringify(b));bmForm.reset();renderBm();});
const notes=document.getElementById('mynotes');
notes.value=localStorage.getItem('md-notes')||'';
notes.addEventListener('input',()=>localStorage.setItem('md-notes',notes.value));
}
const persona=document.getElementById('persona');
if(persona){const mods=['m-ticker','m-day','m-rand','m-fx','m-gold','m-moon'];
const hidden=JSON.parse(localStorage.getItem('md-mods')||'[]');
mods.forEach(id=>{const el=document.getElementById(id);if(!el)return;
if(hidden.includes(id))el.style.display='none';
const cb=persona.querySelector(`input[data-mod="${id}"]`);if(!cb)return;
cb.checked=!hidden.includes(id);
cb.addEventListener('change',()=>{const h=JSON.parse(localStorage.getItem('md-mods')||'[]');
const i=h.indexOf(id);if(cb.checked&&i>-1)h.splice(i,1);if(!cb.checked&&i===-1)h.push(id);
localStorage.setItem('md-mods',JSON.stringify(h));el.style.display=cb.checked?'':'none';});});}
// ---- sortable tables (stats page) --------------------------------------
document.querySelectorAll('table.sortable').forEach(tbl=>{
const tbody=tbl.querySelector('tbody');
tbl.querySelectorAll('th').forEach((th,idx)=>{let asc=true;
th.addEventListener('click',()=>{
const rows=[...tbody.querySelectorAll('tr')],numeric=th.dataset.sort==='num';
rows.sort((a,b)=>{const av=a.children[idx],bv=b.children[idx];
const A=numeric?parseFloat(av.dataset.v??av.textContent):av.textContent;
const Bv=numeric?parseFloat(bv.dataset.v??bv.textContent):bv.textContent;
if(numeric)return asc?A-Bv:Bv-A;
return asc?String(A).localeCompare(String(Bv),'th'):String(Bv).localeCompare(String(A),'th');});
rows.forEach(r=>tbody.appendChild(r));
tbl.querySelectorAll('th').forEach(h=>h.classList.remove('sorted','asc'));
th.classList.add('sorted');if(asc)th.classList.add('asc');asc=!asc;});});});
// ---- crawl-request form: build a GitHub issue, no backend needed ------
const crawlForm=document.getElementById('crawlform');
if(crawlForm){crawlForm.addEventListener('submit',e=>{
e.preventDefault();
const area=crawlForm.area.value.trim(),cat=crawlForm.cat.value.trim(),
kind=crawlForm.kind.value,note=crawlForm.note.value.trim();
const title=`crawl request (${kind}): ${area||'?'} — ${cat||'?'}`;
const body=(note?note+'\n\n':'')+'(ส่งจากฟอร์มในเว็บ / sent from the site form)';
const url='https://github.com/NaNoBotCo/mot-dang/issues/new?title='+
encodeURIComponent(title)+'&body='+encodeURIComponent(body);
window.open(url,'_blank','noopener');
crawlForm.reset();});}
// ---- claim.html: find-or-paste an existing place, claim it, or edit it -
const claimFind=document.getElementById('claim-find');
if(claimFind){
const cfg=JSON.parse(document.getElementById('claim-cfg').textContent);
const WORKER=cfg.workerUrl,SITE='https://motdang.net/';
const FIELDS=['phone','lineId','facebook','instagram','whatsapp','email','website','hours','menu','note'];
// Facet ticks travel as an array, not as FIELDS entries — an empty array is a
// real answer ("I looked; it has none of these"), which a blank text input
// cannot express.
const getTicks=form=>[...form.querySelectorAll('input[name="facet"]:checked')].map(c=>c.value);
const setTicks=(form,vals)=>{const on=new Set(vals||[]);
form.querySelectorAll('input[name="facet"]').forEach(c=>{c.checked=on.has(c.value);});};
const params=new URLSearchParams(location.search);
const stepFind=claimFind,stepConfirm=document.getElementById('claim-confirm'),
stepSuccess=document.getElementById('claim-success'),stepEdit=document.getElementById('claim-edit');
function showStep(el){[stepFind,stepConfirm,stepSuccess,stepEdit].forEach(s=>{s.style.display=s===el?'':'none';});}
const editToken=params.get('edit');
if(editToken){
showStep(stepEdit);
const editForm=document.getElementById('editform'),editErr=document.getElementById('editerror');
(async()=>{try{
const res=await fetch(WORKER+'/edit/'+encodeURIComponent(editToken));
const data=await res.json();
if(!res.ok)throw new Error(data.error||'ลิงก์ใช้ไม่ได้ / invalid link');
FIELDS.forEach(f=>{if(data.claim[f])editForm[f].value=data.claim[f];});
setTicks(editForm,data.claim.facets);
}catch(err){editErr.textContent=err.message;}})();
editForm.addEventListener('submit',async e=>{
e.preventDefault();
const btn=editForm.querySelector('button.submit');
btn.disabled=true;editErr.style.color='';editErr.textContent='';
const body={};FIELDS.forEach(f=>{body[f]=editForm[f].value.trim();});
body.facets=getTicks(editForm);
try{
const res=await fetch(WORKER+'/edit/'+encodeURIComponent(editToken),{method:'POST',
headers:{'content-type':'application/json'},body:JSON.stringify(body)});
const data=await res.json();
if(!res.ok)throw new Error(data.error||'บันทึกไม่สำเร็จ / save failed');
editErr.style.color='#1a6b4a';editErr.textContent='✓ บันทึกแล้ว / saved';
}catch(err){editErr.textContent=err.message;}
btn.disabled=false;});
}else{
let picked=null;
const results=document.getElementById('claimresults'),search=document.getElementById('claimsearch'),
urlPaste=document.getElementById('claimurlpaste'),findErr=document.getElementById('claimfinderror');
function slugFromUrl(v){const m=v.trim().match(/\/(cm|cr)\/p\/([a-z0-9-]+)\.html/i);return m?m[2]:null;}
function pick(e){picked=e;
document.getElementById('claimwhoname').textContent=e.n;
document.getElementById('claimwhoprov').textContent='· '+e.pv;
document.getElementById('claimwholink').href=SITE+e.p+'/p/'+e.s+'.html';
showStep(stepConfirm);}
search&&search.addEventListener('input',async()=>{
const q=search.value.trim().toLowerCase();
if(!q){results.innerHTML='';return;}
const idx=await loadIndex();
const hits=idx.filter(e=>(e.n+' '+(e.e||'')).toLowerCase().includes(q)).slice(0,12);
results.innerHTML=hits.map(e=>`<li><button>${H(e.n)} <span class="count">· ${H(e.pv)}</span></button></li>`).join('');
results.querySelectorAll('button').forEach((b,i)=>b.addEventListener('click',()=>pick(hits[i])));});
urlPaste&&urlPaste.addEventListener('change',async()=>{
const slug=slugFromUrl(urlPaste.value);
findErr.textContent='';
if(!slug){findErr.textContent='หาไอดีจากลิงก์ไม่เจอ / could not read an id from that link';return;}
const idx=await loadIndex();const e=idx.find(x=>x.s===slug);
if(!e){findErr.textContent='ไม่พบที่นี่ในสารบัญ / not found in the directory';return;}
pick(e);});
document.getElementById('claimagain').addEventListener('click',()=>{picked=null;showStep(stepFind);});
const wantId=params.get('id');
if(wantId){(async()=>{const idx=await loadIndex();const e=idx.find(x=>x.id===wantId);if(e)pick(e);})();}
const claimForm=document.getElementById('claimform'),claimErr=document.getElementById('claimerror');
claimForm.addEventListener('submit',async e=>{
e.preventDefault();
if(!picked){claimErr.textContent='เลือกที่ตั้งก่อน / pick a place first';return;}
const body={placeId:picked.id};let any=false;
FIELDS.forEach(f=>{const v=claimForm[f].value.trim();if(v){body[f]=v;any=true;}});
// Ticks ride along but never satisfy `any` — a claim still needs a real way
// to reach the shop, or a passer-by could lock an owner out with one tick.
body.facets=getTicks(claimForm);
if(!any){claimErr.textContent='ใส่อย่างน้อยหนึ่งช่องทาง / fill in at least one channel';return;}
const btn=claimForm.querySelector('button.submit');
btn.disabled=true;btn.textContent='กำลังบันทึก… / saving…';claimErr.textContent='';
try{
const res=await fetch(WORKER+'/claim',{method:'POST',headers:{'content-type':'application/json'},body:JSON.stringify(body)});
const data=await res.json();
if(!res.ok)throw new Error(data.error||'บันทึกไม่สำเร็จ / something went wrong');
const viewUrl=SITE+picked.p+'/p/'+picked.s+'.html';
const vlink=document.getElementById('successviewlink');
vlink.href=viewUrl;vlink.textContent=viewUrl;
document.getElementById('successediturl').textContent=data.editUrl;
document.getElementById('successcopybtn').dataset.url=data.editUrl;
showStep(stepSuccess);
}catch(err){
claimErr.textContent=err.message;
btn.disabled=false;btn.textContent='🏪 ยืนยันฟรี · Claim it free';}});
}}
// ---- route plan: pick stops anywhere, see them together on plan.html --
// A plan is an ordered list of "province:slug" keys in localStorage. That is
// the whole state — the same string is what travels in a ?stops= share link,
// so a plan someone sends you and a plan you built yourself are the same
// object by the time either is drawn.
const PLAN_KEY='md-plan',PLAN_MAX=9;   // ไหว้พระ ๙ วัด is nine by definition
const WALK_KMH=4.6,RIDE_KMH=18;
function planGet(){try{const v=JSON.parse(localStorage.getItem(PLAN_KEY));
return Array.isArray(v)?v.slice(0,PLAN_MAX):[];}catch(e){return[];}}
function planSet(list){try{localStorage.setItem(PLAN_KEY,JSON.stringify(list.slice(0,PLAN_MAX)));}
catch(e){}planPaint();}
function planPaint(){const list=planGet(),have=new Set(list);
document.querySelectorAll('.planbtn[data-plan]').forEach(b=>{
const on=have.has(b.dataset.plan);b.classList.toggle('on',on);
b.setAttribute('aria-pressed',on?'true':'false');});
document.querySelectorAll('.plancount').forEach(el=>{
el.textContent=list.length||'';el.style.display=list.length?'':'none';});}
document.querySelectorAll('.planbtn[data-plan]').forEach(b=>{
b.addEventListener('click',e=>{e.preventDefault();
const k=b.dataset.plan,list=planGet(),i=list.indexOf(k);
if(i>-1)list.splice(i,1);
else if(list.length>=PLAN_MAX){alert('แผนหนึ่งเก็บได้ '+PLAN_MAX+' จุด / a plan holds '+PLAN_MAX+' stops');return;}
else list.push(k);
planSet(list);});});
planPaint();
// ---- plan.html itself --------------------------------------------------
const planSteps=document.getElementById('plansteps');
if(planSteps){(async()=>{
const CATL=JSON.parse(document.getElementById('cat-labels').textContent);
const SITE='https://motdang.net/';
const GEO=JSON.parse(document.getElementById('plan-geo').textContent);
const MOAT=GEO.moat;
// The moat ring as its four แจ่ง corners, in order. Slightly out of square,
// which is the point: an axis-aligned box puts Suan Dok Gate on the wrong
// side of the water it stands on.
const POLY=(GEO.poly||[]).map(p=>({lat:p[0],lng:p[1]}));
const POLY_EDGES=POLY.map((p,i)=>[p,POLY[(i+1)%POLY.length]]);
// The five gates and the four แจ่ง corners, as the catalogue pins them — the
// same records build.py routes a moat crossing by. Where a person gets over
// the water is the thing anybody here gives directions by, so any map showing
// a stretch of moat names the ways across it that stand on that map.
const GATES=(GEO.gates||[]).map(g=>({lat:g[0],lng:g[1],th:g[2],en:g[3],kind:g[4]}));
const elEmpty=document.getElementById('planempty'),elHas=document.getElementById('planhasstops'),
elTotal=document.getElementById('plantotal'),elMap=document.getElementById('planmap'),
elBanner=document.getElementById('planbanner');
let here=null; // the reader's own position, once they offer it
// A shared link wins over whatever is in this browser, but never silently:
// the banner says a plan arrived and offers to keep it before it overwrites.
const shared=new URLSearchParams(location.search).get('stops');
let stops=planGet(),incoming=null;
if(shared){const inc=shared.split(',').map(s=>s.trim()).filter(Boolean).slice(0,PLAN_MAX);
if(inc.length){incoming=inc;stops=inc;}}
function km(a,b){const R=6371,dLa=(b.lat-a.lat)*Math.PI/180,dLo=(b.lng-a.lng)*Math.PI/180;
const h=Math.sin(dLa/2)**2+Math.cos(a.lat*Math.PI/180)*Math.cos(b.lat*Math.PI/180)*Math.sin(dLo/2)**2;
return 2*R*Math.asin(Math.sqrt(h));}
function dist(d){return d<1?Math.round(d*1000)+' ม./m':d.toFixed(1)+' กม./km';}
function mins(d,kmh){const m=Math.round(d/kmh*60);return m<1?'<1':m;}
function segX(a,b,c,d){
const side=(p,q,r)=>(q.lng-p.lng)*(r.lat-p.lat)-(q.lat-p.lat)*(r.lng-p.lng);
const d1=side(c,d,a),d2=side(c,d,b),d3=side(a,b,c),d4=side(a,b,d);
return ((d1>0&&d2<0)||(d1<0&&d2>0))&&((d3>0&&d4<0)||(d3<0&&d4>0));}
// ---- the road graph: nobody can fly ----------------------------------
// Straight-line distance is wrong in a city and most wrong for the two people
// this page is for. There are buildings in the way, sois that do not join up,
// a one-way ring around the moat, and water you cross at a footbridge or a
// U-turn and nowhere else — and a footbridge is a road to a walker and a wall
// to a scooter. So we route on the real network, with a mode.
//
// The asymmetry that does most of the work: **oneway binds ride and not foot.**
// On a one-way ring road the shop thirty metres behind you is a lap away.
let GRAPH=null,GRAPH_STATE='cold';
const MODES={foot:{kmh:4.6,fwd:1,bwd:2,osrm:'foot'},
             ride:{kmh:18,fwd:4,bwd:8,osrm:'car'}};
async function loadGraph(){
if(GRAPH_STATE!=='cold')return GRAPH;
GRAPH_STATE='loading';
const g=await mdJSON('data/road_graph.json');
if(!g||!g.nodes||!g.edges){GRAPH_STATE='absent';return null;}
const S=g.scale;
const nodes=g.nodes.map(p=>[p[0]/S,p[1]/S]);
// Rebuild each edge's full polyline: its two junction ends with the road's
// bends, which arrive delta-encoded, threaded back between them.
const adj=nodes.map(()=>[]);
const geom=[];
g.edges.forEach((e,i)=>{
const a=e[0],b=e[1],len=e[2],flags=e[3],d=e[4]||[];
const pts=[nodes[a]];
let la=0,ln=0;
for(let k=0;k<d.length;k+=2){
if(k===0){la=d[0];ln=d[1];}else{la+=d[k];ln+=d[k+1];}
pts.push([la/S,ln/S]);}
pts.push(nodes[b]);
geom.push(pts);
adj[a].push([b,len,flags,i,1]);
adj[b].push([a,len,flags,i,0]);});
GRAPH={area:g.area,nodes:nodes,adj:adj,edges:g.edges,geom:geom};
GRAPH_STATE='ready';
return GRAPH;}
function inArea(p){const a=GRAPH&&GRAPH.area;
return !!a&&p.lat>a.s&&p.lat<a.n&&p.lng>a.w&&p.lng<a.e;}
function passable(flags,mode,fwd){const m=MODES[mode];
return (flags&(fwd?m.fwd:m.bwd))!==0;}
// Metres from p to the segment ab, and how far along ab the foot of that
// perpendicular falls. Local flat projection: over one road segment the
// curvature of the earth is not the error that matters.
function toSeg(p,a,b){
const kx=Math.cos(p.lat*Math.PI/180)*111320,ky=110540;
const px=0,py=0;
const ax=(a[1]-p.lng)*kx,ay=(a[0]-p.lat)*ky;
const bx=(b[1]-p.lng)*kx,by=(b[0]-p.lat)*ky;
const dx=bx-ax,dy=by-ay,L=dx*dx+dy*dy;
let t=L?((px-ax)*dx+(py-ay)*dy)/L:0;
t=Math.max(0,Math.min(1,t));
const cx=ax+t*dx,cy=ay+t*dy;
return {d:Math.hypot(cx-px,cy-py),t:t,seg:Math.sqrt(L)};}
// Snap a stop onto the network: nearest point on the nearest edge this mode may
// use, with the walk-in distance to each end of it. Snapping to junctions alone
// would throw away up to a block of accuracy on every stop.
function snap(p,mode){
if(!GRAPH)return null;
let best=null;
for(let i=0;i<GRAPH.geom.length;i++){
const flags=GRAPH.edges[i][3];
if(!passable(flags,mode,true)&&!passable(flags,mode,false))continue;
const pts=GRAPH.geom[i];
let run=0;
for(let k=0;k<pts.length-1;k++){
const r=toSeg(p,pts[k],pts[k+1]);
if(!best||r.d<best.d){
best={d:r.d,edge:i,fromA:run+r.t*r.seg,total:0};}
run+=r.seg;}
if(best&&best.edge===i){
let tot=0;
for(let k=0;k<pts.length-1;k++)tot+=toSeg(p,pts[k],pts[k+1]).seg;
best.total=tot;}}
if(!best)return null;
const e=GRAPH.edges[best.edge];
best.a=e[0];best.b=e[1];
best.toA=best.fromA;best.toB=Math.max(0,best.total-best.fromA);
return best;}
// A tiny binary heap — Dijkstra on ~10k junctions wants one, and an array sort
// per pop turns a millisecond into a second.
function Heap(){this.a=[];}
Heap.prototype.push=function(k,v){const a=this.a;a.push([k,v]);let i=a.length-1;
while(i>0){const p=(i-1)>>1;if(a[p][0]<=a[i][0])break;const t=a[p];a[p]=a[i];a[i]=t;i=p;}};
Heap.prototype.pop=function(){const a=this.a;if(!a.length)return null;
const top=a[0],last=a.pop();
if(a.length){a[0]=last;let i=0;
for(;;){const l=2*i+1,r=l+1;let m=i;
if(l<a.length&&a[l][0]<a[m][0])m=l;
if(r<a.length&&a[r][0]<a[m][0])m=r;
if(m===i)break;const t=a[m];a[m]=a[i];a[i]=t;i=m;}}
return top;};
// ---- cutting a road at a point ----------------------------------------
// A snapped stop stands part of the way along an edge, not at a junction, so
// the first and the last stretch of every journey is a PIECE of a road. The
// junction chain alone leaves those pieces out, and the straight stub then
// covers them — claiming a hundred metres of real street is "the walk in from
// the pin". Cut the edge instead and draw the ground that is actually walked.
function segLen(p,q){const kx=Math.cos((p[0]+q[0])/2*Math.PI/180)*111320,ky=110540;
return Math.hypot((q[1]-p[1])*kx,(q[0]-p[0])*ky);}
function edgeLen(pts){let t=0;for(let k=0;k<pts.length-1;k++)t+=segLen(pts[k],pts[k+1]);return t;}
function atAlong(pts,d){
let run=0;
for(let k=0;k<pts.length-1;k++){const L=segLen(pts[k],pts[k+1]);
if(run+L>=d){const t=L?(d-run)/L:0;
return [pts[k][0]+(pts[k+1][0]-pts[k][0])*t,pts[k][1]+(pts[k+1][1]-pts[k][1])*t];}
run+=L;}
return pts[pts.length-1];}
// The part of one edge between two distances along it, given in travel order.
function cutEdge(ei,d0,d1){
const pts=GRAPH.geom[ei],L=edgeLen(pts);
const a=Math.max(0,Math.min(L,Math.min(d0,d1))),b=Math.max(0,Math.min(L,Math.max(d0,d1)));
const out=[atAlong(pts,a)];
let run=0;
for(let k=0;k<pts.length-1;k++){run+=segLen(pts[k],pts[k+1]);
if(run>a+0.01&&run<b-0.01)out.push(pts[k+1]);}
out.push(atAlong(pts,b));
return d1<d0?out.reverse():out;}
function joinLine(line,pts){pts.forEach(pt=>{const last=line[line.length-1];
if(!last||Math.abs(last[0]-pt[0])>1e-9||Math.abs(last[1]-pt[1])>1e-9)line.push(pt);});
return line;}
// Dijkstra from both ends of the start edge to both ends of the goal edge.
// Directed: an edge is only traversable the way this mode is allowed to take
// it, which is where oneway earns its keep.
function route(from,to,mode){
if(!GRAPH||!from||!to)return null;
// Both stops on one stretch of road is only a straight answer if this mode may
// travel that way down it. On a one-way soi the shop thirty metres behind you
// is a lap away, so that case falls through to the search like any other.
if(from.edge===to.edge){
const fwd=to.fromA>=from.fromA;
if(passable(GRAPH.edges[from.edge][3],mode,fwd))
return {m:Math.abs(to.fromA-from.fromA),
path:cutEdge(from.edge,from.fromA,to.fromA),sameEdge:true};}
const N=GRAPH.nodes.length;
const cost=new Float64Array(N).fill(Infinity);
const prevN=new Int32Array(N).fill(-1),prevE=new Int32Array(N).fill(-1);
const h=new Heap();
// Leaving the start edge is only possible towards an end this mode may reach.
if(passable(GRAPH.edges[from.edge][3],mode,false)||from.a===from.b){
cost[from.a]=from.toA;h.push(from.toA,from.a);}
if(passable(GRAPH.edges[from.edge][3],mode,true)){
if(from.toB<cost[from.b]){cost[from.b]=from.toB;h.push(from.toB,from.b);}}
const goals={};
if(passable(GRAPH.edges[to.edge][3],mode,true))goals[to.a]=to.toA;
if(passable(GRAPH.edges[to.edge][3],mode,false))goals[to.b]=to.toB;
if(!Object.keys(goals).length)return null;
let bestGoal=null,bestCost=Infinity;
while(true){
const top=h.pop();
if(!top)break;
const c=top[0],n=top[1];
if(c>cost[n])continue;
if(c>=bestCost)break;
if(goals[n]!==undefined&&c+goals[n]<bestCost){bestCost=c+goals[n];bestGoal=n;}
const list=GRAPH.adj[n];
for(let i=0;i<list.length;i++){
const to2=list[i][0],len=list[i][1],flags=list[i][2],ei=list[i][3],fwd=list[i][4];
if(!passable(flags,mode,fwd===1))continue;
const nc=c+len;
if(nc<cost[to2]){cost[to2]=nc;prevN[to2]=n;prevE[to2]=ei;h.push(nc,to2);}}}
if(bestGoal===null)return null;
// Stitch the whole journey into one polyline: the piece of the first road from
// the stop out to the junction it leaves by, then the junction chain, then the
// piece of the last road in to the second stop. Leaving the two end pieces out
// drew a 1.8 km walk as 280 m of road and a straight line across the rest.
const chain=[];
let cur=bestGoal;
while(cur!==-1&&prevE[cur]!==-1){chain.push([prevE[cur],cur]);cur=prevN[cur];}
chain.reverse();
const line=[];
joinLine(line,cutEdge(from.edge,from.fromA,
(cur===from.a)?0:edgeLen(GRAPH.geom[from.edge])));
chain.forEach(([ei,into])=>{
const e=GRAPH.edges[ei],pts=GRAPH.geom[ei];
joinLine(line,(e[1]===into)?pts:pts.slice().reverse());});
joinLine(line,cutEdge(to.edge,
(bestGoal===to.a)?0:edgeLen(GRAPH.geom[to.edge]),to.fromA));
return {m:bestCost,path:line};}
// ---- the errand solver -------------------------------------------------
// Pick a pharmacy, an ATM and som tam by NAME and any tool will route between
// them. The question people actually have is the other way round: I need those
// three things, which ones make the shortest single trip? Choosing the nearest
// of each independently is not the same answer and is often a worse one — the
// nearest pharmacy can sit the wrong side of a one-way ring from everything
// else you need.
//
// Done in three parts. One Dijkstra per candidate fills a cost matrix (n
// searches, not n squared pairs). Then every combination of one-candidate-per
// errand is scored against that matrix, which is arithmetic. Then the order
// within the winning combination: exact for a small round, 2-opt beyond, since
// the cost of an approximation here is a slightly longer walk.
function costsFrom(s,mode){
if(!GRAPH||!s)return null;
const N=GRAPH.nodes.length,cost=new Float64Array(N).fill(Infinity),h=new Heap();
if(passable(GRAPH.edges[s.edge][3],mode,false)||s.a===s.b){cost[s.a]=s.toA;h.push(s.toA,s.a);}
if(passable(GRAPH.edges[s.edge][3],mode,true)&&s.toB<cost[s.b]){cost[s.b]=s.toB;h.push(s.toB,s.b);}
for(;;){const top=h.pop();if(!top)break;
const c=top[0],n=top[1];
if(c>cost[n])continue;
const list=GRAPH.adj[n];
for(let i=0;i<list.length;i++){
const to=list[i][0],len=list[i][1],flags=list[i][2],fwd=list[i][4];
if(!passable(flags,mode,fwd===1))continue;
const nc=c+len;
if(nc<cost[to]){cost[to]=nc;h.push(nc,to);}}}
return cost;}
function costTo(cost,t,mode){
if(!cost||!t)return null;
let best=Infinity;
if(passable(GRAPH.edges[t.edge][3],mode,true))best=Math.min(best,cost[t.a]+t.toA);
if(passable(GRAPH.edges[t.edge][3],mode,false))best=Math.min(best,cost[t.b]+t.toB);
return best===Infinity?null:best;}
// Unreachable is not free. Charged high enough that the search avoids it and
// low enough that sums stay comparable.
const NOWAY=1e7;
function matrixFor(points,mode){
const snaps=points.map(p=>snap(p,mode));
const n=points.length,M=[];
for(let i=0;i<n;i++){
const row=new Array(n).fill(null);
if(snaps[i]){const cost=costsFrom(snaps[i],mode);
for(let j=0;j<n;j++){
if(!snaps[j])continue;
if(i===j){row[j]=0;continue;}
const c=costTo(cost,snaps[j],mode);
if(c!==null)row[j]=c+snaps[i].d+snaps[j].d;}}
M.push(row);}
return M;}
function tourLen(M,order){let t=0;
for(let i=0;i<order.length-1;i++){const v=M[order[i]][order[i+1]];t+=(v===null?NOWAY:v);}
return t;}
// An open path, not a loop: an errand run ends where it ends. Start is pinned
// (where the reader is, or the first stop they chose); the rest is free.
function bestOrder(M,idx){
const rest=idx.slice(1);
if(rest.length<=6){
let best=null,bestLen=Infinity;
const perm=(arr,cur)=>{
if(!arr.length){const o=[idx[0]].concat(cur),L=tourLen(M,o);
if(L<bestLen){bestLen=L;best=o;}return;}
for(let i=0;i<arr.length;i++)perm(arr.slice(0,i).concat(arr.slice(i+1)),cur.concat([arr[i]]));};
perm(rest,[]);
return {order:best,len:bestLen};}
let order=[idx[0]],left=rest.slice();
while(left.length){const cur=order[order.length-1];
let bi=0,bd=Infinity;
left.forEach((j,i)=>{const v=M[cur][j],d=(v===null?NOWAY:v);if(d<bd){bd=d;bi=i;}});
order.push(left[bi]);left.splice(bi,1);}
let improved=true;
while(improved){improved=false;
for(let i=1;i<order.length-1;i++)for(let k=i+1;k<order.length;k++){
const cand=order.slice(0,i).concat(order.slice(i,k+1).reverse(),order.slice(k+1));
if(tourLen(M,cand)+1e-9<tourLen(M,order)){order=cand;improved=true;}}}
return {order:order,len:tourLen(M,order)};}
async function solveErrands(kinds,mode){
const idx=await loadIndex();
const area=GRAPH&&GRAPH.area;
if(!area)return null;
// Anchor the search: where the reader is, else the stops already chosen, else
// the middle of the area we can route in.
const anchor=here||(places.length?{lat:places[0].lat,lng:places[0].lng}
:{lat:(area.n+area.s)/2,lng:(area.w+area.e)/2});
const CAND=6;
const slots=[];
for(const k of kinds){
const pool=idx.filter(e=>e.lat!=null&&(e.c||[]).indexOf(k)>-1
&&e.lat>area.s&&e.lat<area.n&&e.lng>area.w&&e.lng<area.e);
pool.sort((a,b)=>km(anchor,a)-km(anchor,b));
if(!pool.length)return {missing:k};
slots.push(pool.slice(0,CAND));}
// Points: the fixed part of the round first, then every candidate.
const fixed=[anchor].concat(places.map(p=>({lat:p.lat,lng:p.lng})));
const pts=fixed.slice(),meta=[];
slots.forEach((pool,si)=>pool.forEach(e=>{meta.push({slot:si,e:e,i:pts.length});
pts.push({lat:e.lat,lng:e.lng});}));
const M=matrixFor(pts,mode);
// Every way of taking one candidate per errand. Six candidates over three
// errands is 216 combinations — small, and each is only a table lookup away
// from a score.
let best=null;
const walk=(si,chosen)=>{
if(si===slots.length){
const r=bestOrder(M,fixed.map((_,i)=>i).concat(chosen.map(m=>m.i)));
if(!best||r.len<best.len)best={len:r.len,order:r.order,chosen:chosen.slice()};
return;}
meta.filter(m=>m.slot===si).forEach(m=>{chosen.push(m);walk(si+1,chosen);chosen.pop();});};
walk(0,[]);
if(!best)return null;
// What the naive answer would have been, so the page can say whether asking
// the question this way actually bought anything.
const naive=slots.map((pool,si)=>meta.find(m=>m.slot===si&&m.e===pool[0]));
const nOrder=bestOrder(M,fixed.map((_,i)=>i).concat(naive.map(m=>m.i)));
return {best:best,naive:{len:nOrder.len},meta:meta,fixedCount:fixed.length};}
function osmDirections(a,b,mode){
return 'https://www.openstreetmap.org/directions?engine=fossgis_osrm_'+MODES[mode].osrm+
'&route='+a.lat.toFixed(5)+'%2C'+a.lng.toFixed(5)+'%3B'+b.lat.toFixed(5)+'%2C'+b.lng.toFixed(5);}
// One leg, both ways of travelling it. The two modes get different distances
// because they are genuinely different journeys — that is the whole point.
// A stop this far from any road we hold is not really on the network, and the
// straight walk-in charged for it is a guess. วัดเมืองลัง sits 450 m from the
// nearest junction in the graph while OSM has a footpath 10 m away, and the
// leg came out 916 m against a real walk of 4.3 km. One stop of the ninety on
// the merit rounds is in that state — rare enough to name on the page rather
// than hide, and never to pass off as a measured distance.
const FAR_FROM_ROAD=100;
function leg(a,b){
const out={crow:km(a,b),foot:null,ride:null,routed:false,far:0};
if(GRAPH_STATE!=='ready'||!inArea(a)||!inArea(b))return out;
for(const mode of ['foot','ride']){
const s=snap(a,mode),t=snap(b,mode);
if(!s||!t)continue;
const r=route(s,t,mode);
if(!r)continue;
// Add the walk-in from each stop to the road it was snapped to; otherwise a
// shop set back from the street reads as being on it.
out[mode]={km:(r.m+s.d+t.d)/1000,path:r.path,snap:Math.round(s.d+t.d)};
out.far=Math.max(out.far,Math.round(Math.max(s.d,t.d)));}
out.routed=!!(out.foot||out.ride);
return out;}
async function resolve(keys){
const idx=await loadIndex();
const bySlug={};idx.forEach(e=>{bySlug[e.p+':'+e.s]=e;});
const out=[];
for(const k of keys){const e=bySlug[k];
if(!e||e.lat==null)continue;
const rec={key:k,n:e.n,en:e.e,p:e.p,s:e.s,pv:e.pv,c:e.c||[],lat:e.lat,lng:e.lng};
// The slim index carries no address or phone. The per-place .json beside
// every page does, and eight of those is a cheap price for stop cards that
// are actually useful standing in the street.
const j=await mdJSON(e.p+'/p/'+e.s+'.json');
if(j){rec.addr=j.address||'';rec.chan=(j.channels||[]).slice(0,4);}
out.push(rec);}
return out;}
// Which network the reader is on. It decides what "nearest" means when the
// stops are reordered, and which of the two lines the page leads with.
let planMode=(()=>{try{return localStorage.getItem('md-planmode')==='ride'?'ride':'foot';}
catch(e){return 'foot';}})();
// The graph is half a megabyte, so it loads here and nowhere else on the site.
await loadGraph();
let places=await resolve(stops);
// Drop anything the index no longer knows, rather than leaving a hole.
if(places.length!==stops.length&&!incoming){stops=places.map(p=>p.key);planSet(stops);}
// Is a point inside the moat ring? Ray casting, because the ring is a little
// out of square and its bounding box puts Suan Dok Gate on the wrong bank.
function inRing(p){
if(POLY.length<3)return false;
let hit=false;
for(let i=0,j=POLY.length-1;i<POLY.length;j=i++){
const yi=POLY[i].lat,xi=POLY[i].lng,yj=POLY[j].lat,xj=POLY[j].lng;
if((xi>p.lng)!==(xj>p.lng)){
const ty=(yj-yi)*(p.lng-xi)/((xj-xi)||1e-12)+yi;
if(p.lat<ty)hit=!hit;}}
return hit;}
// Liang–Barsky, enough of it to keep a label on the canvas.
function clipToBox(p,q,W,H){
let t0=0,t1=1;const dx=q.x-p.x,dy=q.y-p.y;
const tests=[[-dx,p.x],[dx,W-p.x],[-dy,p.y],[dy,H-p.y]];
for(let i=0;i<tests.length;i++){
const pp=tests[i][0],qq=tests[i][1];
if(pp===0){if(qq<0)return null;continue;}
const r=qq/pp;
if(pp<0){if(r>t1)return null;if(r>t0)t0=r;}
else{if(r<t0)return null;if(r<t1)t1=r;}}
return [{x:p.x+t0*dx,y:p.y+t0*dy},{x:p.x+t1*dx,y:p.y+t1*dy}];}
// Where to write "the moat" so the words land on water that is on the page and
// not on top of a gate that is also naming itself. Pinning the label to the
// ring's northernmost corner dropped it off the top of the picture on five of
// the ten merit rounds — drawn water, no name — and putting it at the middle
// of the longest visible side then landed it on Chang Phueak Gate.
function moatLabelPoint(X,Y,W,H,taken){
let best=null,fallback=null;
POLY_EDGES.forEach(me=>{
const p={x:X(me[0].lng),y:Y(me[0].lat)},q={x:X(me[1].lng),y:Y(me[1].lat)};
const c=clipToBox(p,q,W,H);
if(!c)return;
const L=Math.hypot(c[1].x-c[0].x,c[1].y-c[0].y);
if(L<12)return;
const upright=Math.abs(c[1].y-c[0].y)>Math.abs(c[1].x-c[0].x);
if(!fallback||L>fallback.L)fallback={L:L,x:(c[0].x+c[1].x)/2,y:(c[0].y+c[1].y)/2,upright:upright};
[0.5,0.3,0.7,0.15,0.85].forEach(t=>{
const x=c[0].x+(c[1].x-c[0].x)*t,y=c[0].y+(c[1].y-c[0].y)*t;
if(x<40||x>W-40||y<18||y>H-14)return;
let clear=999;
(taken||[]).forEach(g=>{clear=Math.min(clear,Math.hypot(g[0]-x,g[1]-y));});
// Long side, well clear of any gate already naming itself.
const score=L+Math.min(clear,150)*3;
if(!best||score>best.score)best={score:score,x:x,y:y,upright:upright};});});
// Water on the page always gets its name, even when only a sliver of one side
// shows: a clamped label at the edge beats an unnamed blue dashed line.
const pick=best||fallback;
if(!pick)return null;
const py=Math.min(Math.max(pick.y,18),H-14);
if(pick.upright){const right=pick.x<W/2;   // the words go on whichever side has room
return [Math.min(Math.max(right?pick.x+8:pick.x-8,6),W-6),py,right?'start':'end'];}
return [Math.min(Math.max(pick.x,60),W-60),Math.max(py-7,16),'middle'];}
function svgMap(list,legs){
if(!list.length)return'';
// The stops set the frame — never the moat. Framing to the moat as well
// squeezes four stops 400m apart into a knot in the middle of a 1.6km
// square. The moat is drawn afterwards, clipped by the viewBox, so it is a
// landmark you recognise at the edge of the picture rather than the subject.
const pts=list.map(p=>({lat:p.lat,lng:p.lng}));
if(here)pts.push(here);
// Frame the roads the route actually uses, not just its stops: a leg that has
// to go round three blocks leaves the box drawn around its endpoints.
(legs||[]).forEach(l=>{if(!l)return;
['foot','ride'].forEach(m=>{if(l[m]&&l[m].path)l[m].path.forEach(
q=>pts.push({lat:q[0],lng:q[1]}));});});
let n=Math.max(...pts.map(p=>p.lat)),s=Math.min(...pts.map(p=>p.lat)),
w=Math.min(...pts.map(p=>p.lng)),e=Math.max(...pts.map(p=>p.lng));
// A single stop has no extent at all; give every plan a floor so one pin
// does not divide by zero and eight clustered pins are not a smudge.
const padLat=Math.max((n-s)*0.22,0.0022),padLng=Math.max((e-w)*0.22,0.0022);
n+=padLat;s-=padLat;w-=padLng;e+=padLng;
const kx=Math.cos((n+s)/2*Math.PI/180),W=760;
const H=Math.max(240,Math.min(520,W*((n-s)/((e-w)*kx||1e-9))));
const X=lng=>(lng-w)/(e-w)*W,Y=lat=>(n-lat)/(n-s)*H;
// The moat and its gates, worked out before the picture opens so the map can
// say in its own label what it is showing. The rule does not depend on where
// the route happens to sit: if a side of the moat crosses this frame it is
// drawn AND named, and every gate or แจ่ง corner standing inside the frame is
// drawn AND named. A frame wholly within the walls has no side to draw, so it
// gets the one fact in words instead.
const inFrame=p=>p.lat<n&&p.lat>s&&p.lng>w&&p.lng<e;
const cmHere=POLY.length&&list.some(p=>p.p==='cm');
const frame=[{lat:n,lng:w},{lat:n,lng:e},{lat:s,lng:e},{lat:s,lng:w}];
const frameEdges=frame.map((p,i)=>[p,frame[(i+1)%4]]);
const moatShows=!!cmHere&&(POLY.some(inFrame)
||POLY_EDGES.some(me=>frameEdges.some(fe=>segX(me[0],me[1],fe[0],fe[1]))));
// Only claim "inside the old city" when the frame really does sit in the ring.
// A plan out in Hang Dong also fails to show a side of the moat, and telling
// its reader they are inside the walls would simply be untrue.
const insideWalls=!!cmHere&&!moatShows&&frame.every(inRing);
const gatesHere=cmHere?GATES.filter(inFrame):[];
let aria='แผนที่ทริปของคุณ '+list.length+' จุด · map of your route, '+list.length+' stops';
if(moatShows)aria+=' — คูเมืองอยู่ในภาพ · the old city moat runs across it';
else if(insideWalls)aria+=' — ทั้งหมดอยู่ในเวียงเก่า · all of it inside the old city';
if(gatesHere.length)aria+=' — '+gatesHere.map(g=>g.th+' '+g.en).join(', ');
let o=['<svg viewBox="0 0 '+W+' '+Math.round(H)+'" width="100%" class="planmap" role="img" '+
'aria-label="'+H2(aria)+'">',
'<rect width="'+W+'" height="'+Math.round(H)+'" fill="#FBF6EE"/>'];
if(moatShows){
o.push('<path d="'+POLY.map((p,i)=>(i?'L':'M')+X(p.lng).toFixed(1)+' '+Y(p.lat).toFixed(1)).join(' ')+
'Z" fill="none" stroke="#2a78d6" stroke-width="2" stroke-dasharray="5 4" opacity=".55">'+
'<title>คูเมืองเชียงใหม่ (เส้นโดยประมาณ จากหมุดแจ่งทั้งสี่) · the old city moat, '+
'traced from the four แจ่ง corner pins</title></path>');
const lab=moatLabelPoint(X,Y,W,H,gatesHere.map(g=>[X(g.lng),Y(g.lat)]));
if(lab)o.push('<text x="'+lab[0].toFixed(1)+'" y="'+lab[1].toFixed(1)+'" text-anchor="'+lab[2]+
'" font-size="11" fill="#2a78d6" opacity=".9">คูเมือง · the moat</text>');}
else if(insideWalls)o.push('<text x="'+(W-12)+'" y="20" text-anchor="end" font-size="11" '+
'fill="#2a78d6" opacity=".8">ในเวียงเก่า · inside the old city</text>');
// A gate is a diamond on the water, named in both languages. Cream-filled so
// the route line reads through it, and drawn before the legs so a red walking
// line lies over the landmark rather than under it.
gatesHere.forEach(g=>{
const gx=X(g.lng),gy=Y(g.lat);
o.push('<path d="M'+gx.toFixed(1)+' '+(gy-6).toFixed(1)+'l6 6l-6 6l-6-6Z" fill="#FBF6EE" '+
'stroke="#2a78d6" stroke-width="2" opacity=".95"><title>'+H2(g.th+' · '+g.en)+
'</title></path>');
const gl=g.th+' · '+g.en,half=gl.length*3.1;
let ga='middle',gxl=gx;
if(gx-half<4){ga='start';gxl=4;}else if(gx+half>W-4){ga='end';gxl=W-4;}
// Under the gate normally; over it when a stop is standing where the words
// would go, since two names in one place is neither name.
const crowded=list.some(p=>Math.hypot(X(p.lng)-gx,Y(p.lat)-(gy+20))<46);
const gyl=crowded?Math.max(14,gy-12):Math.min(H-5,gy+20);
o.push('<text x="'+gxl.toFixed(1)+'" y="'+gyl.toFixed(1)+'" text-anchor="'+ga+
'" font-size="10" fill="#2a78d6" opacity=".9">'+H2(gl)+'</text>');});
// Draw the roads the route really follows. Both modes, because they diverge:
// where the walk and the ride part company is exactly the thing worth seeing.
// The scooter line goes down first and solid, the walking line over it dashed,
// so where they agree you read one road and where they differ you read two.
const drawPath=(pth,stroke,w,dash)=>{
if(!pth||pth.length<2)return;
const d=pth.map((q,i)=>(i?'L':'M')+X(q[1]).toFixed(1)+' '+Y(q[0]).toFixed(1)).join(' ');
o.push('<path d="'+d+'" fill="none" stroke="'+stroke+'" stroke-width="'+w+
'" stroke-linejoin="round" stroke-linecap="round"'+
(dash?' stroke-dasharray="'+dash+'"':'')+' opacity=".85"/>');};
let anyRouted=false,anyStraight=false;
(legs||[]).forEach(l=>{if(!l)return;
if(l.ride&&l.ride.path){drawPath(l.ride.path,'#1c5aa8',4,'');anyRouted=true;}
if(l.foot&&l.foot.path){drawPath(l.foot.path,'#a3231c',2.5,'6 4');anyRouted=true;}});
// The stub from a pin to the road it sits back from. Its length is already in
// the leg distance; without it drawn, a shop down a lane looks unreachable —
// the route line simply stops short of its own pin.
(legs||[]).forEach((l,i)=>{if(!l)return;
const pth=(l.foot&&l.foot.path)||(l.ride&&l.ride.path);
if(!pth||pth.length<2)return;
[[list[i],pth[0]],[list[i+1],pth[pth.length-1]]].forEach(([stop,end])=>{
if(!stop)return;
const dx=X(end[1])-X(stop.lng),dy=Y(end[0])-Y(stop.lat);
if(Math.hypot(dx,dy)<3)return;
o.push('<line x1="'+X(stop.lng).toFixed(1)+'" y1="'+Y(stop.lat).toFixed(1)+'" x2="'+
X(end[1]).toFixed(1)+'" y2="'+Y(end[0]).toFixed(1)+'" stroke="#8a7a62" stroke-width="1.5" '+
'stroke-dasharray="2 3" opacity=".7"><title>'+
'จากหมุดถึงถนน / from the pin out to the road</title></line>');});});
// A leg the graph could not route still needs a line, but a faint dotted one
// that does not pretend to be a road.
list.forEach((p,i)=>{const L=(legs||[])[i-1];
if(i&&L&&!L.routed){anyStraight=true;
const a=list[i-1];
o.push('<path d="M'+X(a.lng).toFixed(1)+' '+Y(a.lat).toFixed(1)+'L'+X(p.lng).toFixed(1)+
' '+Y(p.lat).toFixed(1)+'" fill="none" stroke="#8a7a62" stroke-width="2" '+
'stroke-dasharray="2 5" opacity=".8"><title>'+
'เส้นตรง ยังไม่ได้คิดตามถนน / straight line, not routed</title></path>');}});
if(here){o.push('<circle cx="'+X(here.lng).toFixed(1)+'" cy="'+Y(here.lat).toFixed(1)+
'" r="7" fill="#2a78d6" fill-opacity=".25" stroke="#2a78d6" stroke-width="2">'+
'<title>ตำแหน่งของคุณ · you are here</title></circle>');}
list.forEach((p,i)=>{const cx=X(p.lng),cy=Y(p.lat);
o.push('<circle cx="'+cx.toFixed(1)+'" cy="'+cy.toFixed(1)+'" r="13" fill="#a3231c" '+
'stroke="#7d1712" stroke-width="2"><title>'+H2(p.n)+'</title></circle>');
o.push('<text x="'+cx.toFixed(1)+'" y="'+(cy+5).toFixed(1)+'" text-anchor="middle" '+
'font-size="14" font-weight="700" fill="#fff">'+(i+1)+'</text>');
const label=p.n.length>24?p.n.slice(0,23)+'…':p.n;
let anchor='middle',lx=cx;const half=label.length*3.6;
if(cx-half<4){anchor='start';lx=4;}else if(cx+half>W-4){anchor='end';lx=W-4;}
o.push('<text x="'+lx.toFixed(1)+'" y="'+(cy-18).toFixed(1)+'" text-anchor="'+anchor+
'" font-size="12" fill="#2A1E16">'+H2(label)+'</text>');});
const kmDeg=111.32*kx,barKm=(e-w)*kx*111.32>6?2:0.5,barPx=barKm/kmDeg/(e-w)*W;
if(barPx<W*0.6){const by=Math.round(H-16);
o.push('<line x1="16" y1="'+by+'" x2="'+(16+barPx).toFixed(1)+'" y2="'+by+
'" stroke="#2A1E16" stroke-width="2"/>');
o.push('<text x="16" y="'+(by-5)+'" font-size="10" fill="#2A1E16">'+barKm+' กม./km</text>');}
// Two lines on one map need saying which is which.
if(anyRouted||anyStraight){let lx=W-14,ly=H-34;
const key=(stroke,wd,dash,label)=>{
o.push('<line x1="'+(lx-26)+'" y1="'+ly+'" x2="'+(lx-6)+'" y2="'+ly+'" stroke="'+stroke+
'" stroke-width="'+wd+'"'+(dash?' stroke-dasharray="'+dash+'"':'')+' stroke-linecap="round"/>');
o.push('<text x="'+(lx-32)+'" y="'+(ly+4)+'" text-anchor="end" font-size="10" fill="#2A1E16">'+
label+'</text>');ly+=14;};
if(anyRouted){key('#a3231c',2.5,'6 4','🚶 เดิน/walk');key('#1c5aa8',4,'','🛵 มอไซค์/scooter');}
if(anyStraight)key('#8a7a62',2,'2 5','เส้นตรง/straight');}
o.push('</svg>');return o.join('');}
function H2(s){return String(s).replace(/[&<>"]/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;'}[c]));}
function planUrl(){return SITE+'plan.html?stops='+encodeURIComponent(places.map(p=>p.key).join(','));}
// share_block bakes the bare plan.html URL into each pill's query string. Swap
// that placeholder for the real ?stops= link — percent-encoded, since it now
// carries a ? of its own and would otherwise truncate the outer share URL.
function repointShare(){const box=document.getElementById('planshare');if(!box)return;
const u=planUrl(),t='แผนเดินทาง '+places.length+' จุด · มดแดง';
box.querySelectorAll('a.pill').forEach(a=>{
if(!a.dataset.tpl)a.dataset.tpl=a.getAttribute('href');
a.setAttribute('href',a.dataset.tpl.split(SITE+'plan.html').join(encodeURIComponent(u)));});
box.querySelectorAll('[data-url]').forEach(b=>{b.dataset.url=u;
if(b.dataset.title!=null)b.dataset.title=t;});}
function textPlan(){
const lines=['แผนเดินทาง / My route — มดแดง motdang.net',''];
places.forEach((p,i)=>{lines.push((i+1)+'. '+p.n+(p.en&&p.en!==p.n?' ('+p.en+')':''));
if(p.addr)lines.push('   '+p.addr);
(p.chan||[]).forEach(c=>lines.push('   '+c.text));
lines.push('   '+SITE+p.p+'/p/'+p.s+'.html');
const nx=places[i+1];
if(nx){const L=leg(p,nx);
if(L.routed){
if(L.foot)lines.push('   ↓ เดิน/walk '+dist(L.foot.km)+' — '+mins(L.foot.km,MODES.foot.kmh)+' นาที/min');
else lines.push('   ↓ เดินไปไม่ได้ / not walkable');
if(L.ride)lines.push('     ขี่/scooter '+dist(L.ride.km)+' — '+mins(L.ride.km,MODES.ride.kmh)+' นาที/min');
else lines.push('     ขี่ไปไม่ได้ / no road for a scooter');
if(L.far>=FAR_FROM_ROAD){
lines.push('     จุดหนึ่งห่างถนนที่บันทึกไว้ '+L.far+' ม. ระยะจริงน่าจะไกลกว่านี้ / one stop is '+
L.far+' m from the nearest road on record, so the real distance is probably longer');
lines.push('     '+osmDirections(p,nx,'foot'));}
}else{
lines.push('   ↓ '+dist(L.crow)+' เส้นตรง ยังไม่ได้คิดตามถนน / straight line, not routed');
lines.push('     '+osmDirections(p,nx,'foot'));}}
lines.push('');});
lines.push('ลิงก์ทริปนี้ / this route: '+planUrl());
return lines.join('\n');}
// The demo teaches an empty page. Once there are real stops on the map it is
// just a second animated map competing with the true one, so it steps aside.
const elDemo=document.getElementById('plandemo');
function render(){
if(elDemo)elDemo.style.display=places.length?'none':'';
if(!places.length){elEmpty.style.display='';elHas.style.display='none';
if(incoming)elBanner.style.display='none';return;}
elEmpty.style.display='none';elHas.style.display='';
const legs=[];for(let i=1;i<places.length;i++)legs.push(leg(places[i-1],places[i]));
elMap.innerHTML=svgMap(places,legs);
// Totals per mode, and only over the legs that mode could actually route.
// Summing a routed leg with a crow-flies one would produce a number that is
// neither, so an unrouted leg is counted and named separately.
const sum=m=>legs.reduce((t,l)=>t+(l[m]?l[m].km:0),0);
const unrouted=legs.filter(l=>!l.routed).length;
const footTot=sum('foot'),rideTot=sum('ride');
const legIn=here&&places.length?leg(here,places[0]):null;
let tot='<b>'+places.length+' จุด / stops</b>';
if(places.length>1){
if(GRAPH_STATE==='ready'&&(footTot||rideTot)){
tot+=' · <span class="pmode foot">🚶 '+dist(footTot)+' · '+mins(footTot,MODES.foot.kmh)+' นาที/min</span>'+
' · <span class="pmode ride">🛵 '+dist(rideTot)+' · '+mins(rideTot,MODES.ride.kmh)+' นาที/min</span>';
if(rideTot>footTot*1.15)tot+=' <span class="tinynote">'+
'(มอไซค์ไกลกว่าเพราะถนนเดินรถทางเดียว / longer by scooter — one-way streets)</span>';
}else{
tot+=' · '+dist(footTot||rideTot||0);}}
else tot+=' · จุดเดียว / a single stop';
if(legIn&&legIn.foot)tot+=' · จากตำแหน่งคุณถึงจุดแรก '+dist(legIn.foot.km);
if(unrouted)tot+=' · <b>'+unrouted+' ช่วงอยู่นอกเขตคิดเส้นทาง</b> / '+unrouted+
' leg'+(unrouted>1?'s':'')+' outside the routed area';
elTotal.innerHTML=tot;
planSteps.innerHTML=places.map((p,i)=>{
const cats=(p.c||[]).map(c=>CATL[c]?CATL[c][0]:c).join(' · ');
const chan=(p.chan||[]).map(c=>'<a href="'+H2(c.href)+'" rel="noopener">'+H2(c.text)+'</a>').join('');
const L=legs[i];
let legHtml='';
if(L){
if(L.routed){
const f=L.foot,r=L.ride;
let rows='';
if(f)rows+='<span class="pleg foot">🚶 '+dist(f.km)+' · '+mins(f.km,MODES.foot.kmh)+' นาที/min</span>';
if(r)rows+='<span class="pleg ride">🛵 '+dist(r.km)+' · '+mins(r.km,MODES.ride.kmh)+' นาที/min</span>';
if(!f)rows+='<span class="pleg none">🚶 เดินไปไม่ได้ / not walkable</span>';
if(!r)rows+='<span class="pleg none">🛵 ขี่ไปไม่ได้ / no road for a scooter</span>';
let note='';
if(f&&r&&r.km>f.km*1.25)note='<span class="planvia">↳ '+
'ขี่ไกลกว่าเดิน '+dist(r.km-f.km)+' — ถนนทางเดียวหรือต้องกลับรถ / '+
'the ride is '+dist(r.km-f.km)+' longer: one-way, or a U-turn to get across</span>';
if(L.far>=FAR_FROM_ROAD){const A=places[i],B=places[i+1];
note+='<span class="planvia">↳ จุดหนึ่งในช่วงนี้อยู่ห่างถนนที่มดบันทึกไว้ '+L.far+
' ม. ระยะจริงน่าจะไกลกว่านี้ / one stop on this leg is '+L.far+
' m from the nearest road on record, so the real distance is probably longer '+
'<a class="planosm" href="'+H2(osmDirections(A,B,'foot'))+'" rel="noopener">'+
'🚶 ดูเส้นทางจริง/check it ↗</a></span>';}
legHtml='<li class="planleg">'+rows+note+'</li>';
}else{
const A=places[i],B=places[i+1];
legHtml='<li class="planleg out">↓ '+dist(L.crow)+' '+
'<span class="tinynote">เส้นตรง ยังไม่ได้คิดตามถนน / straight line, not routed</span> '+
'<a class="planosm" href="'+H2(osmDirections(A,B,'foot'))+'" rel="noopener">🚶 ดูเส้นทาง/directions ↗</a> '+
'<a class="planosm" href="'+H2(osmDirections(A,B,'ride'))+'" rel="noopener">🛵 ดูเส้นทาง/directions ↗</a></li>';}}
return '<li class="planstop"><span class="plannum">'+(i+1)+'</span>'+
'<div class="planbody"><h3><a href="'+RROOT+p.p+'/p/'+p.s+'.html">'+H2(p.n)+'</a></h3>'+
'<span class="plancat">'+H2(cats)+' · '+H2(p.pv)+'</span>'+
(p.addr?'<p class="planaddr">'+H2(p.addr)+'</p>':'')+
(chan?'<div class="planchan">'+chan+'</div>':'')+
'</div><div class="planacts">'+
'<button type="button" data-up="'+i+'" title="เลื่อนขึ้น / move up"'+(i?'':' disabled')+'>▲</button>'+
'<button type="button" data-down="'+i+'" title="เลื่อนลง / move down"'+(i<places.length-1?'':' disabled')+'>▼</button>'+
'<button type="button" class="plandel" data-del="'+i+'" title="เอาออก / remove">✕</button>'+
'</div></li>'+legHtml;}).join('');
planSteps.querySelectorAll('[data-up]').forEach(b=>b.addEventListener('click',()=>{
const i=+b.dataset.up;[places[i-1],places[i]]=[places[i],places[i-1]];commit();}));
planSteps.querySelectorAll('[data-down]').forEach(b=>b.addEventListener('click',()=>{
const i=+b.dataset.down;[places[i+1],places[i]]=[places[i],places[i+1]];commit();}));
planSteps.querySelectorAll('[data-del]').forEach(b=>b.addEventListener('click',()=>{
places.splice(+b.dataset.del,1);commit();}));
const dl=document.getElementById('plandlbtn');
if(dl){if(dl.dataset.blob)URL.revokeObjectURL(dl.dataset.blob);
const url=URL.createObjectURL(new Blob([textPlan()],{type:'text/plain;charset=utf-8'}));
dl.dataset.blob=url;dl.href=url;}
repointShare();}
// commit = the plan changed for real: remember it, redraw, and stop treating
// it as somebody else's shared link.
function commit(){incoming=null;elBanner.style.display='none';
planSet(places.map(p=>p.key));render();}
if(incoming){const mine=planGet();
elBanner.className='planbanner';elBanner.style.display='';
elBanner.innerHTML='<span>📩 <b>แผนที่มีคนแชร์มา '+incoming.length+' จุด</b> · '+
'A route someone shared with you'+(mine.length?' — แผนเดิมของคุณยังอยู่ / your own plan is untouched':'')+
'</span><button type="button" id="plankeep">💾 เก็บเป็นแผนของฉัน / Keep as mine</button>';
document.getElementById('plankeep').addEventListener('click',commit);}
document.querySelectorAll('.pmbtn').forEach(b=>b.addEventListener('click',()=>{
planMode=b.dataset.mode;
try{localStorage.setItem('md-planmode',planMode);}catch(e){}
document.querySelectorAll('.pmbtn').forEach(x=>{const on=x===b;
x.classList.toggle('on',on);x.setAttribute('aria-pressed',on?'true':'false');});
document.body.classList.toggle('mode-ride',planMode==='ride');
render();}));
document.body.classList.toggle('mode-ride',planMode==='ride');
document.querySelectorAll('.pmbtn').forEach(x=>{const on=x.dataset.mode===planMode;
x.classList.toggle('on',on);x.setAttribute('aria-pressed',on?'true':'false');});
document.getElementById('planclearbtn').addEventListener('click',()=>{
places=[];planSet([]);incoming=null;elBanner.style.display='none';render();});
// Where the run starts. With nothing granted the route simply begins at the
// first stop, which is a complete answer — so this button adds precision, it
// does not unlock the feature. Declining used to raise an alert() and leave
// the reader exactly where they were; it now starts the run from the landmark
// nearest the plan instead, and says which one.
const planLoc=document.getElementById('planlocbtn');
planLoc&&planLoc.addEventListener('click',()=>{MDLOC.ask(pt=>{
here=pt;planLoc.classList.add('on');render();},
()=>{const o=MDLOC.origin(places.length?places[0].lat:null);
here={lat:o.lat,lng:o.lng};MDLOC.remember(o);
planLoc.classList.add('on');
planLoc.innerHTML='📍 '+mdBi('เริ่มจาก'+o.th,'Starting from '+o.en);
render();});});
// Nearest-neighbour from wherever the run starts. Not the optimal tour, and
// it does not pretend to be — with eight stops it is close enough to save
// real riding, and it stays legible: "always go to the nearest one next".
// ---- errands: the UI over solveErrands ---------------------------------
const errSel=document.getElementById('planerrsel'),errAdd=document.getElementById('planerradd'),
errList=document.getElementById('planerrlist'),errSolve=document.getElementById('planerrsolve'),
errOut=document.getElementById('planerrout');
if(errSel&&errAdd){
let kinds=(()=>{try{const v=JSON.parse(localStorage.getItem('md-plan-kinds'));
return Array.isArray(v)?v.slice(0,4):[];}catch(e){return[];}})();
const labelOf=k=>{const o=[...errSel.options].find(o=>o.value===k);
return o?o.textContent.replace(/\s*\(\d+\)$/,''):k;};
function paintKinds(){
errList.innerHTML=kinds.map((k,i)=>'<li>'+H2(labelOf(k))+
' <button type="button" class="errdel" data-i="'+i+'" aria-label="'+
H2('เอาออก / remove')+'">✕</button></li>').join('');
errSolve.style.display=kinds.length?'':'none';
try{localStorage.setItem('md-plan-kinds',JSON.stringify(kinds));}catch(e){}
errList.querySelectorAll('.errdel').forEach(b=>b.addEventListener('click',()=>{
kinds.splice(+b.dataset.i,1);paintKinds();errOut.innerHTML='';}));}
errAdd.addEventListener('click',()=>{
const k=errSel.value;
// Four errands over six candidates each is already 1,296 combinations; past
// that the wait stops being worth the better answer.
if(!k||kinds.indexOf(k)>-1||kinds.length>=4)return;
kinds.push(k);paintKinds();errOut.innerHTML='';});
errSolve.addEventListener('click',async()=>{
errOut.innerHTML='<p class="tinynote">🐜 '+H2('มดกำลังลองทุกทาง…')+'</p>';
// Yield once so the message paints before the search blocks the thread.
await new Promise(r=>setTimeout(r,30));
const res=await solveErrands(kinds,planMode);
if(!res||res.missing){errOut.innerHTML='<p class="tinynote">'+
H2('ยังไม่มีข้อมูลพอในเขตที่มดเดินถนนไว้ / not enough of that kind inside the area we hold roads for')+
'</p>';return;}
const chosen=res.best.chosen;
const saved=res.naive.len-res.best.len;
const rows=chosen.map(m=>'<li><a href="'+m.e.p+'/p/'+m.e.s+'.html">'+H2(m.e.n)+'</a> '+
'<span class="tinynote">'+H2(labelOf(kinds[m.slot]))+'</span></li>').join('');
// Say plainly whether asking the question this way helped. Sometimes the
// nearest of each IS the best round, and claiming otherwise would be a lie
// dressed as a feature.
const verdict=saved>50
?'<p class="errsaved">'+H2('สั้นกว่าการเลือกที่ใกล้ที่สุดทีละอย่าง '+Math.round(saved)+' เมตร')+
' · '+H2('shorter than picking the nearest of each, by '+Math.round(saved)+' m')+'</p>'
:'<p class="tinynote">'+H2('รอบนี้ การเลือกที่ใกล้ที่สุดทีละอย่างก็สั้นพอ ๆ กัน')+
' · '+H2('here, picking the nearest of each is just as good')+'</p>';
errOut.innerHTML='<p class="errtotal"><b>'+H2(dist(res.best.len/1000))+'</b> '+
H2(planMode==='foot'?'เดินทั้งรอบ / walking the whole round':'ขี่รถทั้งรอบ / riding the whole round')+
'</p>'+verdict+'<ol class="errpicks">'+rows+'</ol>'+
'<button type="button" id="erradd2plan" class="pill dark">'+
H2('ใส่ทั้งหมดลงในแผน')+' · '+H2('Add them all to the plan')+'</button>';
document.getElementById('erradd2plan').addEventListener('click',()=>{
const add=chosen.map(m=>m.e.p+':'+m.e.s).filter(k=>stops.indexOf(k)<0);
stops=stops.concat(add).slice(0,PLAN_MAX);
planSet(stops);location.href='plan.html?stops='+encodeURIComponent(stops.join(','));});});
paintKinds();}
document.getElementById('planreorderbtn').addEventListener('click',()=>{
if(places.length<3)return;
const rest=places.slice();const out=[];
let cur=here||rest[0];
if(!here)out.push(rest.shift());
// Nearest by the network the reader is actually travelling on. Ordering by
// crow-flies would happily send a scooter the wrong way up a one-way soi.
const nearBy=(a,b)=>{const L=leg(a,b);
const r=L[planMode]||L.foot||L.ride;return r?r.km:L.crow;};
while(rest.length){let bi=0,bd=Infinity;
rest.forEach((p,i)=>{const d=nearBy(cur,p);if(d<bd){bd=d;bi=i;}});
cur=rest[bi];out.push(rest.splice(bi,1)[0]);}
places=out;commit();});
render();
})();}

// ---- reveal on scroll, and a little parallax -------------------------
// The two motions carried over from the design study. Both are decoration, so
// both are built to fail into "everything visible, nothing moving".
//
// The reveal rule lives behind .js-reveal on <html>, added here. If this file
// never runs — blocked, cached badly, thrown by an earlier error — the class
// is never added, the rule never matches, and the page is simply already
// there. A reveal effect that hides content by default and shows it from JS
// is the commonest way a pretty page ships blank; this cannot do that.
(function(){
if(window.matchMedia&&window.matchMedia('(prefers-reduced-motion: reduce)').matches)return;
const items=[].slice.call(document.querySelectorAll('[data-reveal]'));
const pxs=[].slice.call(document.querySelectorAll('[data-parallax]'));
if(!items.length&&!pxs.length)return;
document.documentElement.classList.add('js-reveal');
const show=el=>el.classList.add('shown');
// Belt and braces: whatever happens to the observer or the scroll handler,
// nothing stays hidden past six seconds.
setTimeout(()=>items.forEach(show),6000);
if('IntersectionObserver' in window){
const io=new IntersectionObserver((es,o)=>{es.forEach(e=>{
if(e.isIntersecting){show(e.target);o.unobserve(e.target);}});},
{rootMargin:'0px 0px -8% 0px'});
items.forEach(el=>io.observe(el));
}else items.forEach(show);
if(!pxs.length)return;
// Offset each element against its own container's distance from the middle of
// the screen, so the drift is symmetrical and nothing runs away down the page.
pxs.forEach(el=>{el.dataset.mdBase=el.style.transform||'';});
let ticking=false;
const onScroll=()=>{if(ticking)return;ticking=true;
requestAnimationFrame(()=>{ticking=false;const vh=window.innerHeight;
pxs.forEach(el=>{const p=(el.parentElement||el).getBoundingClientRect();
const mid=p.top+p.height/2-vh/2;
const y=-mid*parseFloat(el.dataset.parallax||'0.1');
el.style.transform='translateY('+y.toFixed(1)+'px) '+(el.dataset.mdBase||'');});});};
window.addEventListener('scroll',onScroll,{passive:true});
window.addEventListener('resize',onScroll,{passive:true});
onScroll();
})();
