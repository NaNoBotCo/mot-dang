
// The markup twin of build.py's bi(). Anything the client fills in has to
// join its two languages the same way the server does, or a gloss hydrated by
// JS ends up jammed against the Thai ("สีส้มorange") in both-mode.
function mdBi(th,en){th=th==null?'':th;if(!en)return '<span class="th">'+th+'</span>';
var sep=/[·—–:-]\s*$/.test(th)?'':'<span class="th"> · </span>';
return '<span class="bi"><span class="th">'+th+'</span><span class="en">'+sep+en+'</span></span>';}

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
const hits=q?idx.filter(e=>(e.n+' '+(e.e||'')).toLowerCase().includes(needle)).slice(0,200):[];
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
function mdPick(doc){if(!doc||!doc.days)return null;
return doc.days[MD_TODAY]||doc.days[Object.keys(doc.days).sort()[0]]||null;}
// --- sky tile: moon + jupiter, drawn from baked positions
(async()=>{const host=document.getElementById('w-sky');if(!host)return;
const doc=await mdJSON('data/sky.json');const day=mdPick(doc);if(!day)return;
const moonArt=host.querySelector('[data-skyart="moon"]');
const jupArt=host.querySelector('[data-skyart="jupiter"]');
if(day.svg_moon&&moonArt)moonArt.innerHTML=day.svg_moon;
if(day.svg_jupiter&&jupArt)jupArt.innerHTML=day.svg_jupiter;
const mc=host.querySelector('[data-skycap="moon"]');
if(mc&&day.moon)mc.innerHTML='<span class="th">'+day.moon.phase_th+' · '+day.moon.thai_label_th+
(day.moon.wan_phra?' · วันพระ':'')+'</span><span class="en">'+day.moon.phase_en+' · '+
day.moon.thai_label_en+(day.moon.wan_phra?' · wan phra':'')+'</span>';
const slides=[...host.querySelectorAll('.skyslide')];
const dots=[...host.querySelectorAll('[data-skydot]')];let si=0;
const go=i=>{si=(i+slides.length)%slides.length;
slides.forEach((s,n)=>{s.hidden=n!==si;});
dots.forEach((d,n)=>d.classList.toggle('on',n===si));};
dots.forEach(d=>d.addEventListener('click',()=>{go(+d.dataset.skydot);clearInterval(window.__skyT);}));
if(slides.length>1)window.__skyT=setInterval(()=>go(si+1),6000);})();
// --- fortune, horoscope, hexagram, and the day's colour
(async()=>{const doc=await mdJSON('data/fortune.json');const day=mdPick(doc);if(!day)return;
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
if(thl)thl.innerHTML='<span class="th">วันนี้เป็น'+t.th+' สีประจำวันคือ'+t.colour_th+
' พระประจำวันคือ'+t.buddha_th+' กำลังพระเคราะห์ '+t.strength+'</span>'+
'<span class="en">Today is '+t.en+'. Its colour is '+t.colour_en+', its image is '+
t.buddha_en+', and its planetary strength is '+t.strength+'.</span>';}
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
const dirList=document.querySelector('ul.dir[data-sortable]');
if(dirList){
const items=[...dirList.children];
const byName=document.getElementById('sort-name'),byDist=document.getElementById('sort-dist');
byName&&byName.addEventListener('click',()=>{
items.sort((a,b)=>(a.dataset.n||'').localeCompare(b.dataset.n||'','th'));
items.forEach(li=>{const d=li.querySelector('.dist');d&&d.remove();dirList.appendChild(li);});
document.querySelectorAll('.toolbar button').forEach(x=>x.classList.remove('on'));
byName.classList.add('on');});
byDist&&byDist.addEventListener('click',()=>{
navigator.geolocation.getCurrentPosition(pos=>{
const{latitude:la,longitude:lo}=pos.coords,R=6371;
items.forEach(li=>{const lat=parseFloat(li.dataset.lat),lng=parseFloat(li.dataset.lng);
if(isNaN(lat)){li.dataset.km=1e9;return;}
const dLa=(lat-la)*Math.PI/180,dLo=(lng-lo)*Math.PI/180;
const h=Math.sin(dLa/2)**2+Math.cos(la*Math.PI/180)*Math.cos(lat*Math.PI/180)*Math.sin(dLo/2)**2;
li.dataset.km=2*R*Math.asin(Math.sqrt(h));});
items.sort((a,b)=>a.dataset.km-b.dataset.km);
items.forEach(li=>{let d=li.querySelector('.dist');const km=parseFloat(li.dataset.km);
if(km<1e8){if(!d){d=document.createElement('span');d.className='dist';li.appendChild(d);}
d.textContent=' · '+(km<1?Math.round(km*1000)+' ม.':km.toFixed(1)+' กม.');}
dirList.appendChild(li);});
document.querySelectorAll('.toolbar button').forEach(x=>x.classList.remove('on'));
byDist.classList.add('on');},
()=>alert('เปิดตำแหน่งที่ตั้งเพื่อเรียงตามระยะทาง / allow location to sort by distance'));});
// ---- ant rank sorts: most complete / recently walked / needs love ----
const btns=[...document.querySelectorAll('.toolbar button')];
const reorder=(btn,cmp)=>{if(!btn)return;btn.addEventListener('click',()=>{
items.sort(cmp);
items.forEach(li=>{const d=li.querySelector('.dist');d&&d.remove();dirList.appendChild(li);});
btns.forEach(x=>x&&x.classList.remove('on'));btn.classList.add('on');});};
const nm=(a,b)=>(a.dataset.n||'').localeCompare(b.dataset.n||'','th');
const rk=li=>parseInt(li.dataset.rank||'0',10);
reorder(document.getElementById('sort-rank'),(a,b)=>rk(b)-rk(a)||nm(a,b));
reorder(document.getElementById('sort-love'),(a,b)=>rk(a)-rk(b)||nm(a,b));
const rw=li=>parseInt(li.dataset.royal||'0',10);
reorder(document.getElementById('sort-royal'),(a,b)=>rw(b)-rw(a)||nm(a,b));
reorder(document.getElementById('sort-hon'),
(a,b)=>(parseInt(b.dataset.hon||'0',10)-parseInt(a.dataset.hon||'0',10))||rk(b)-rk(a)||nm(a,b));
reorder(document.getElementById('sort-fresh'),
(a,b)=>(b.dataset.upd||'').localeCompare(a.dataset.upd||'')||rk(b)-rk(a)||nm(a,b));}
// ---- copy link --------------------------------------------------------
document.querySelectorAll('.copylink').forEach(b=>{b.addEventListener('click',async()=>{
await navigator.clipboard.writeText(b.dataset.url);
b.textContent=b.dataset.done;setTimeout(()=>b.textContent=b.dataset.label,1500);});});
// ---- native share (Web Share API where supported) ---------------------
if(navigator.share){document.querySelectorAll('[data-native]').forEach(b=>{
b.style.display='';b.addEventListener('click',()=>{
navigator.share({title:b.dataset.title,url:b.dataset.url}).catch(()=>{});});});}
// ---- home modules: day colour + ticker + personalize ------------------
const day=document.getElementById('daycolor');
if(day){const names=['อาทิตย์','จันทร์','อังคาร','พุธ','พฤหัสบดี','ศุกร์','เสาร์'];
const ens=['Sunday','Monday','Tuesday','Wednesday','Thursday','Friday','Saturday'];
const cols=[['แดง','red','#C22'],['เหลือง','yellow','#E7B10A'],['ชมพู','pink','#E77'],
['เขียว','green','#2A7'],['ส้ม','orange','#E80'],['ฟ้า','light blue','#59F'],['ม่วง','purple','#96C']];
// ---- currency converter: recompute on input, baked rates, no live call --
const fxamount=document.getElementById('fxamount');
if(fxamount){const recalc=()=>{const amt=parseFloat(fxamount.value)||0;
document.querySelectorAll('.fxout').forEach(el=>{
el.textContent=(amt*parseFloat(el.dataset.rate)).toLocaleString(undefined,
{minimumFractionDigits:2,maximumFractionDigits:2});});};
fxamount.addEventListener('input',recalc);recalc();}
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
const FIELDS=['phone','lineId','facebook','instagram','whatsapp','email','website','hours'];
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
}catch(err){editErr.textContent=err.message;}})();
editForm.addEventListener('submit',async e=>{
e.preventDefault();
const btn=editForm.querySelector('button.submit');
btn.disabled=true;editErr.style.color='';editErr.textContent='';
const body={};FIELDS.forEach(f=>{body[f]=editForm[f].value.trim();});
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
