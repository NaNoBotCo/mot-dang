#!/usr/bin/env python3
"""Mot Dang (มดแดง) — static site builder. data/canonical/*.json -> docs/ (GitHub Pages).

Thai-first, 1997 directory genre studied from the real thing (Yahoo!, April 1997):
search box up top, bold categories with teaser sub-links, counts in parens,
subcategory shelves, a random link, "how to include your site", and a
personalizable home (My Yahoo!) with a news ticker. EN is a client-side
display layer. No tracking, no third-party scripts, no external requests
on load; outbound links only. OSM attribution stays.
"""
import json
import shutil
from pathlib import Path

ROOT = Path(__file__).resolve().parent
DOCS = ROOT / "docs"
BUILD_DATE = "2026-07-27"
BASE = "https://motdang.net/"
KOFI = "https://ko-fi.com/defiantchiangmai"

CFG = json.loads((ROOT / "data" / "categories.json").read_text())
CATS = {c["key"]: c for c in CFG["categories"]}
CAT_ORDER = [c["key"] for c in CFG["categories"]]
PROVINCES = CFG["provinces"]

CSS = """
:root{--paper:#FBF6EE;--ink:#2A1E16;--ant:#C2401C;--ant-dark:#8F2E13;
--link:#1F3FBF;--visited:#6B3FA0;--soft:#EADFCE;--mute:#9B8B78;}
*{box-sizing:border-box}
body{margin:0;background:var(--paper);color:var(--ink);
font:19px/1.65 -apple-system,"Thonburi","Sarabun","Noto Sans Thai",sans-serif;}
main{max-width:960px;margin:0 auto;padding:1rem 1.2rem 4rem}
a{color:var(--link)} a:visited{color:var(--visited)}
a:hover{text-decoration-thickness:3px;text-decoration-color:var(--ant)}
header.site{border-bottom:4px double var(--ant);padding:.8rem 0 .7rem;margin-bottom:.6rem}
.masthead{display:flex;align-items:baseline;gap:.7rem;flex-wrap:wrap}
.logo{font-size:2rem;font-weight:800;color:var(--ant);text-decoration:none;letter-spacing:.5px}
.logo:visited{color:var(--ant)} .logo .ant{display:inline-block;transition:transform .35s}
.logo:hover .ant{transform:rotate(-20deg) translateY(-3px)}
.tagline{color:var(--ant-dark);font-size:.95rem}
.langbtn{margin-left:auto;border:2px solid var(--ant);background:none;color:var(--ant);
border-radius:999px;padding:.15rem .8rem;font:inherit;font-size:.9rem;cursor:pointer}
.langbtn:hover{background:var(--ant);color:var(--paper)}
form.seek{display:flex;gap:.5rem;margin:.7rem 0 .2rem}
form.seek input{flex:1;max-width:26rem;font:inherit;padding:.25rem .6rem;
border:2px solid var(--ant-dark);border-radius:.4rem;background:#fff;color:var(--ink)}
form.seek button{font:inherit;border:2px solid var(--ant);background:var(--ant);color:#fff;
border-radius:.4rem;padding:.25rem .9rem;cursor:pointer}
form.seek button:hover{background:var(--ant-dark)}
.svcbar{font-size:.9rem;margin:.2rem 0 0;color:var(--ant-dark)}
.en{display:none} body.lang-en .en{display:inline} body.lang-en .th{display:none}
h1{font-size:1.6rem;margin:.4rem 0} h2{font-size:1.25rem;border-bottom:2px solid var(--soft);
padding-bottom:.2rem;margin-top:1.6rem}
ul.dir{list-style:none;padding:0;column-width:22rem;column-gap:2.5rem}
ul.dir li{margin:.28rem 0;break-inside:avoid}
ul.cats{list-style:none;padding:0;column-width:26rem;column-gap:2.5rem}
ul.cats li{margin:.1rem 0 .8rem;break-inside:avoid}
ul.cats .teaser{display:block;font-size:.88rem;color:var(--mute)}
.count{color:var(--ant-dark);font-size:.9rem}
.shelf{color:var(--mute)} .shelf .soon{font-size:.8rem;background:var(--soft);
border-radius:.5rem;padding:0 .5rem;white-space:nowrap}
.badge{background:var(--soft);border-radius:.5rem;padding:0 .5rem;font-size:.8rem;white-space:nowrap}
.badge.pin{background:#F6D9CE;color:var(--ant-dark)}
.grow{color:var(--ant-dark);font-size:.9rem;font-style:italic}
.subshelf{background:#fff;border:1px solid var(--soft);border-radius:.7rem;
padding:.6rem 1rem;margin:.6rem 0 1rem}
.subshelf b a{font-weight:700}
.toolbar{display:flex;gap:.5rem;align-items:center;font-size:.9rem;margin:.4rem 0 .6rem;flex-wrap:wrap}
.toolbar button{font:inherit;font-size:.85rem;border:1.5px solid var(--ant-dark);
background:none;color:var(--ant-dark);border-radius:999px;padding:.05rem .7rem;cursor:pointer}
.toolbar button.on,.toolbar button:hover{background:var(--ant-dark);color:var(--paper)}
.dist{color:var(--ant-dark);font-size:.85rem}
.featured{border:2px solid var(--ant);border-radius:.8rem;padding:.9rem 1.1rem;margin:1rem 0;
background:#fff;box-shadow:3px 3px 0 var(--soft);transition:transform .18s,box-shadow .18s}
.featured:hover{transform:translate(-2px,-2px);box-shadow:6px 6px 0 var(--soft)}
.featured .star{color:var(--ant)}
dl{display:grid;grid-template-columns:max-content 1fr;gap:.25rem 1.2rem}
dt{color:var(--ant-dark);font-weight:600} dd{margin:0;overflow-wrap:anywhere}
.share{margin-top:1rem;font-size:.9rem}
.share a,.share button{margin-right:.7rem}
.share a.line{background:#06C755;color:#fff;padding:.12rem .7rem;border-radius:.5rem;
text-decoration:none;font-weight:600}
.share a.line:visited{color:#fff} .share a.line:hover{background:#04A648}
.adbox{border:1px solid var(--ant);border-radius:.6rem;background:#fff;
padding:.5rem .9rem;margin:1.1rem 0;font-size:.95rem}
.adbox .adlabel{display:block;font-size:.72rem;letter-spacing:.12em;color:var(--mute);
text-transform:uppercase;margin-bottom:.1rem}
.adbox .adsell{font-size:.78rem;margin-left:.6rem;color:var(--mute)}
.myhint{background:var(--soft);border-radius:.6rem;padding:.5rem .9rem;font-size:.9rem}
#bmform input{font:inherit;font-size:.9rem;padding:.2rem .5rem;border:1.5px solid var(--soft);
border-radius:.4rem;margin-right:.4rem;max-width:11rem}
#bmform button{font:inherit;font-size:.9rem;border:1.5px solid var(--ant);background:none;
color:var(--ant);border-radius:.4rem;padding:.15rem .7rem;cursor:pointer}
.bmdel{border:none;background:none;color:var(--mute);cursor:pointer;font-size:.8rem}
#mynotes{width:100%;min-height:7rem;font:inherit;font-size:.95rem;border:1.5px solid var(--soft);
border-radius:.5rem;padding:.5rem;background:#fff;color:var(--ink)}
#pinpick label{display:inline-block;margin:.15rem .9rem .15rem 0;font-size:.92rem;cursor:pointer}
.share button{font:inherit;font-size:.9rem;border:none;background:none;color:var(--link);
cursor:pointer;text-decoration:underline;padding:0}
.prov{color:var(--ant-dark);font-size:.85rem;border-top:1px dashed var(--soft);
margin-top:1.6rem;padding-top:.5rem}
footer{border-top:4px double var(--ant);margin-top:3rem;padding-top:.7rem;font-size:.85rem;
color:var(--ant-dark);position:relative;overflow:hidden}
.crumbs{font-size:.9rem;margin-bottom:.4rem}
#scurry{position:absolute;bottom:2px;left:-2rem;font-size:1.1rem;pointer-events:none}
#scurry.go{animation:scurry 3.5s linear}
@keyframes scurry{from{left:-2rem}to{left:105%}}
.module{border:1px solid var(--soft);border-radius:.7rem;background:#fff;
padding:.5rem 1rem;margin:.7rem 0}
.module h3{margin:.1rem 0 .3rem;font-size:1rem;color:var(--ant-dark)}
.tickerwrap{overflow:hidden;white-space:nowrap}
.ticker{display:inline-block;padding-left:100%;animation:tick 55s linear infinite;
animation-delay:-9s}
.tickerwrap:hover .ticker{animation-play-state:paused}
@keyframes tick{from{transform:translateX(0)}to{transform:translateX(-100%)}}
.ticker a{margin-right:2.5rem}
.ticker .src{color:var(--mute);font-size:.8rem}
#daycolor .swatch{display:inline-block;width:1em;height:1em;border-radius:50%;
vertical-align:-.15em;margin-right:.35em;border:1px solid var(--soft)}
.persona{font-size:.85rem;text-align:right}
.persona details{display:inline-block;text-align:left}
.persona label{display:block;cursor:pointer}
@media(max-width:600px){body{font-size:18px} ul.dir,ul.cats{column-width:auto}}
"""

JS = r"""
// ---- language toggle -------------------------------------------------
const B=document.body,btn=document.querySelector('.langbtn');
if(localStorage.getItem('md-lang')==='en')B.classList.add('lang-en');
btn&&btn.addEventListener('click',()=>{B.classList.toggle('lang-en');
localStorage.setItem('md-lang',B.classList.contains('lang-en')?'en':'th');});
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
resBox.innerHTML=hits.map(e=>`<li><a href="${RROOT}${e.p}/p/${e.id}.html">${e.n}</a>`+
`${e.e&&e.e!==e.n?' <span class="count">'+e.e+'</span>':''}`+
` <span class="count">· ${e.pv}</span></li>`).join('')||
(q?'<li class="shelf">ไม่พบ — ลองคำอื่น / nothing found, try another word</li>':'');})();}
// ---- random place (🎲) ----------------------------------------------
document.querySelectorAll('.rand').forEach(a=>{a.addEventListener('click',async e=>{
e.preventDefault();const idx=await loadIndex();
const pick=idx[Math.floor(Math.random()*idx.length)];
location.href=RROOT+pick.p+'/p/'+pick.id+'.html';});});
// ---- sort toolbar: name / distance ----------------------------------
const dirList=document.querySelector('ul.dir[data-sortable]');
if(dirList){
const items=[...dirList.children];
const byName=document.getElementById('sort-name'),byDist=document.getElementById('sort-dist');
byName&&byName.addEventListener('click',()=>{
items.sort((a,b)=>(a.dataset.n||'').localeCompare(b.dataset.n||'','th'));
items.forEach(li=>{const d=li.querySelector('.dist');d&&d.remove();dirList.appendChild(li);});
byName.classList.add('on');byDist.classList.remove('on');});
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
byDist.classList.add('on');byName.classList.remove('on');},
()=>alert('เปิดตำแหน่งที่ตั้งเพื่อเรียงตามระยะทาง / allow location to sort by distance'));});}
// ---- copy link --------------------------------------------------------
document.querySelectorAll('.copylink').forEach(b=>{b.addEventListener('click',async()=>{
await navigator.clipboard.writeText(b.dataset.url);
b.textContent=b.dataset.done;setTimeout(()=>b.textContent=b.dataset.label,1500);});});
// ---- home modules: day colour + ticker + personalize ------------------
const day=document.getElementById('daycolor');
if(day){const names=['อาทิตย์','จันทร์','อังคาร','พุธ','พฤหัสบดี','ศุกร์','เสาร์'];
const ens=['Sunday','Monday','Tuesday','Wednesday','Thursday','Friday','Saturday'];
const cols=[['แดง','red','#C22'],['เหลือง','yellow','#E7B10A'],['ชมพู','pink','#E77'],
['เขียว','green','#2A7'],['ส้ม','orange','#E80'],['ฟ้า','light blue','#59F'],['ม่วง','purple','#96C']];
const d=new Date().getDay(),c=cols[d];
day.innerHTML=`<span class="swatch" style="background:${c[2]}"></span>`+
`<span class="th">วัน${names[d]} — สีมงคลวันนี้: ${c[0]}</span>`+
`<span class="en">${ens[d]} — today's auspicious colour: ${c[1]}</span>`;}
// ---- my page: pins + updates + daily pick + bookmarks + notes ---------
const H=s=>String(s).replace(/[&<>"]/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;'}[c]));
const pinpick=document.getElementById('pinpick');
if(pinpick){
const PULSE=JSON.parse(document.getElementById('pulse').textContent);
const pins=new Set(JSON.parse(localStorage.getItem('md-pins')||'[]'));
const seen=JSON.parse(localStorage.getItem('md-seen')||'{}');
const shelf=document.getElementById('myshelf');
function renderPins(){shelf.innerHTML=[...pins].map(pc=>{
const[pv,cat]=pc.split('/');const m=PULSE[pv]&&PULSE[pv][cat];if(!m)return'';
const fresh=seen[pc]!=null&&m.n>seen[pc]?` <span class="badge">+${m.n-seen[pc]} ใหม่/new</span>`:'';
return `<li><a href="${pv}/${cat}/index.html"><b>${H(m.t)}</b></a> `+
`<span class="count">(${m.n.toLocaleString()}) · ${H(m.v)}</span>${fresh}</li>`;}).join('')||
'<li class="shelf">ยังไม่ได้ปักหมวด — เลือกด้านล่าง / no shelves pinned yet — pick below</li>';}
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
el.innerHTML=`<a href="${pick.p}/p/${pick.id}.html">${H(pick.n)}</a> <span class="count">· ${H(pick.pv)}</span>`;})();
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
if(persona){const mods=['m-ticker','m-day','m-rand'];
const hidden=JSON.parse(localStorage.getItem('md-mods')||'[]');
mods.forEach(id=>{const el=document.getElementById(id);if(!el)return;
if(hidden.includes(id))el.style.display='none';
const cb=persona.querySelector(`input[data-mod="${id}"]`);if(!cb)return;
cb.checked=!hidden.includes(id);
cb.addEventListener('change',()=>{const h=JSON.parse(localStorage.getItem('md-mods')||'[]');
const i=h.indexOf(id);if(cb.checked&&i>-1)h.splice(i,1);if(!cb.checked&&i===-1)h.push(id);
localStorage.setItem('md-mods',JSON.stringify(h));el.style.display=cb.checked?'':'none';});});}
"""


def esc(s):
    return (s or "").replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")


def att(s):
    return esc(s).replace('"', "&quot;")


def bi(th, en):
    return f'<span class="th">{esc(th)}</span><span class="en">{esc(en)}</span>'


def page(title, body, depth, crumbs="", path="", desc=""):
    r = "../" * depth
    url = BASE + path
    tt = esc(title) + " · มดแดง" if title != "มดแดง" else "มดแดง — สารบัญเมืองเชียงใหม่ · เชียงราย"
    d = att(desc or "มดแดง — สารบัญเมืองเชียงใหม่และเชียงราย แบบสมุดหน้าเมือง")
    return f"""<!DOCTYPE html>
<html lang="th" data-root="{r}"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>{tt}</title>
<meta name="description" content="{d}">
<meta property="og:site_name" content="มดแดง Mot Dang">
<meta property="og:title" content="{att(tt)}">
<meta property="og:description" content="{d}">
<meta property="og:type" content="website">
<meta property="og:url" content="{att(url)}">
<meta property="og:image" content="{BASE}card.png">
<meta name="twitter:card" content="summary_large_image">
<link rel="stylesheet" href="{r}style.css">
<link rel="icon" href="data:image/svg+xml,<svg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 100 100'><text y='.9em' font-size='90'>🐜</text></svg>">
</head><body>
<main>
<header class="site">
  <div class="masthead">
    <a class="logo" href="{r}index.html"><span class="ant">🐜</span> มดแดง</a>
    <span class="tagline">{bi("รู้ทุกซอย เหมือนมดแดง", "knows every soi, like a red ant")}</span>
    <button class="langbtn">TH / EN</button>
  </div>
  <form class="seek"><input type="search" placeholder="ค้นหาชื่อร้าน วัด คลินิก… / search"><button>{bi("ค้นหา", "Search")}</button></form>
  <div class="svcbar">
    <a href="{r}my.html">🏠 {bi("หน้าแรกของฉัน", "My page")}</a> ·
    <a href="{r}suggest.html">{bi("แนะนำร้าน", "Add your place")}</a> ·
    <a href="{r}contacts.html">☎️ {bi("เติมเบอร์-ไลน์", "Add contacts")}</a> ·
    <a href="#" class="rand">🎲 {bi("สุ่มพาไป", "Random place")}</a> ·
    <a href="{r}advertise.html">{bi("ลงโฆษณา", "Advertise")}</a> ·
    <a href="{KOFI}" rel="noopener">☕ {bi("เลี้ยงกาแฟมดแดง", "Buy the ants a coffee")}</a>
  </div>
</header>
{f'<nav class="crumbs">{crumbs}</nav>' if crumbs else ''}
{body}
<footer>
  {bi("สร้างจากข้อมูลเปิดและการเดินเก็บจริง · ปรับปรุง " + BUILD_DATE,
      "Built from open data and shoe-leather · updated " + BUILD_DATE)}<br>
  © <a href="https://www.openstreetmap.org/copyright" rel="noopener">OpenStreetMap contributors</a> (ODbL) ·
  <a href="https://github.com/NaNoBotCo/mot-dang" rel="noopener">GitHub</a> ·
  <a href="{KOFI}" rel="noopener">Ko-fi</a>
  <span id="scurry">🐜</span>
</footer>
</main>
<script src="{r}md.js"></script>
</body></html>"""


def load():
    return {p["key"]: json.loads((ROOT / "data" / "canonical" / f"{p['key']}.json").read_text())
            for p in PROVINCES}


def matches(r, m):
    if not m:
        return False
    if "lens" in m:
        return m["lens"] in r["attrs"].get("lens", [])
    if "sub" in m:
        return m["sub"] in r.get("sub", [])
    if "attr" in m:
        return r["attrs"].get(m["attr"]) == m["value"]
    return False


def name_of(r):
    return r.get("name") or r.get("nameEn") or r["id"]


def has_contact(r):
    a = r.get("attrs", {})
    return bool(r.get("phone") or r.get("website") or a.get("lineId")
                or a.get("facebook") or a.get("instagram") or a.get("email")
                or a.get("whatsapp"))


def entry_li(r, href):
    star = '<span class="star">★</span> ' if r.get("featured") else ""
    pin = ' <span class="badge pin">' + bi("รอปักหมุด", "pin wanted") + "</span>" \
        if r.get("geoPrecision") == "needs-pin" else ""
    lat = f' data-lat="{r["lat"]}" data-lng="{r["lng"]}"' if r.get("lat") is not None else ""
    return (f'<li data-n="{att(name_of(r))}"{lat}>{star}'
            f'<a href="{href}">{esc(name_of(r))}</a>{pin}</li>')


def geojson(records):
    return {"type": "FeatureCollection", "features": [
        {"type": "Feature",
         "geometry": {"type": "Point", "coordinates": [r["lng"], r["lat"]]},
         "properties": {"id": r["id"], "name": name_of(r), "cat": r["cat"],
                        "province": r["province"]}}
        for r in records if r.get("lat") is not None]}


def toolbar():
    return (f'<div class="toolbar">{bi("เรียงตาม", "Sort by")}: '
            f'<button id="sort-name" class="on">{bi("ก→ฮ ชื่อ", "A→Z name")}</button>'
            f'<button id="sort-dist">📍 {bi("ใกล้ฉัน", "Near me")}</button></div>')


def listing_page(title_th, title_en, records, depth, prov, crumbs, path, extra_top=""):
    lis = "".join(entry_li(r, "../" * (depth - 1) + f"p/{r['id']}.html") for r in records)
    body = (f"<h1>{bi(title_th, title_en)} "
            f'<span class="count">({len(records):,})</span></h1>'
            f"{extra_top}{ad_box(path, depth)}{toolbar()}"
            f'<ul class="dir" data-sortable>{lis}</ul>'
            f"{share_block(BASE + path, title_th)}")
    return page(title_th, body, depth, crumbs=crumbs, path=path,
                desc=f"{title_th} — {len(records)} แห่ง · มดแดง")


ADS = json.loads((ROOT / "data" / "ads.json").read_text())


def ad_box(path, depth):
    import zlib
    ad = ADS[zlib.crc32(path.encode()) % len(ADS)]
    href = "../" * depth + ad["url"] if ad.get("house") else ad["url"]
    rel = "" if ad.get("house") else ' rel="noopener"'
    return (f'<div class="adbox"><span class="adlabel">— {esc("ผู้สนับสนุน")} · sponsor —</span>'
            f'<a href="{att(href)}"{rel}><b>{bi(ad["th"], ad["en"])}</b></a>'
            f'<a class="adsell" href="{"../" * depth}advertise.html">'
            + bi("ลงโฆษณาที่นี่", "advertise here") + "</a></div>")


def share_block(url, name):
    u = att(url)
    return (f'<p class="share">{bi("บอกต่อ", "Share")}: '
            f'<a class="line" href="https://social-plugins.line.me/lineit/share?url={u}" rel="noopener">LINE</a>'
            f'<a href="https://www.facebook.com/sharer/sharer.php?u={u}" rel="noopener">Facebook</a>'
            f'<a href="https://twitter.com/intent/tweet?url={u}&text={att(name)}" rel="noopener">X</a>'
            f'<button class="copylink" data-url="{u}" data-label="คัดลอกลิงก์" data-done="คัดลอกแล้ว ✓">คัดลอกลิงก์</button></p>')


def detail_page(r, prov_cfg):
    rows = []
    cats = " · ".join(
        f'<a href="../{c}/index.html">{bi(CATS[c]["th"], CATS[c]["en"])}</a>' for c in r["cat"])
    rows.append(f"<dt>{bi('หมวด', 'Category')}</dt><dd>{cats}</dd>")
    if r.get("nameEn") and r.get("nameEn") != r.get("name"):
        rows.append(f"<dt>{bi('ชื่ออังกฤษ', 'English name')}</dt><dd>{esc(r['nameEn'])}</dd>")
    if r.get("address"):
        rows.append(f"<dt>{bi('ที่อยู่', 'Address')}</dt><dd>{esc(r['address'])}</dd>")
    if r.get("phone"):
        rows.append(f"<dt>{bi('โทร', 'Phone')}</dt><dd><a href=\"tel:{att(r['phone'])}\">{esc(r['phone'])}</a></dd>")
    if r.get("website"):
        rows.append(f"<dt>{bi('เว็บ', 'Website')}</dt><dd><a href=\"{att(r['website'])}\" rel=\"nofollow noopener\">{esc(r['website'])}</a></dd>")
    if r.get("hours"):
        rows.append(f"<dt>{bi('เวลาเปิด', 'Hours')}</dt><dd>{esc(r['hours'])}</dd>")
    line_id = r.get("attrs", {}).get("lineId")
    if line_id:
        lid = line_id.lstrip("@~")
        rows.append(f'<dt>LINE</dt><dd><a class="line" style="background:#06C755;color:#fff;'
                    f'padding:.05rem .6rem;border-radius:.5rem;text-decoration:none" '
                    f'href="https://line.me/R/ti/p/~{att(lid)}" rel="noopener">@{esc(lid)}</a></dd>')
    fb = r.get("attrs", {}).get("facebook")
    if fb:
        fb_url = fb if fb.startswith("http") else f"https://www.facebook.com/{fb}"
        rows.append(f'<dt>Facebook</dt><dd><a href="{att(fb_url)}" rel="nofollow noopener">{esc(fb_url.rstrip("/").rsplit("/", 1)[-1])}</a></dd>')
    ig = r.get("attrs", {}).get("instagram")
    if ig:
        ig_url = ig if ig.startswith("http") else f"https://www.instagram.com/{ig.lstrip('@')}"
        rows.append(f'<dt>Instagram</dt><dd><a href="{att(ig_url)}" rel="nofollow noopener">@{esc(ig_url.rstrip("/").rsplit("/", 1)[-1])}</a></dd>')
    wa = r.get("attrs", {}).get("whatsapp")
    if wa:
        rows.append(f'<dt>WhatsApp</dt><dd><a href="https://wa.me/{att(wa.lstrip("+").replace(" ", ""))}" rel="noopener">{esc(wa)}</a></dd>')
    em = r.get("attrs", {}).get("email")
    if em:
        rows.append(f'<dt>{bi("อีเมล", "Email")}</dt><dd><a href="mailto:{att(em)}">{esc(em)}</a></dd>')
    bw = r.get("attrs", {}).get("brandWebsite")
    if bw:
        rows.append(f'<dt>{bi("เว็บของแบรนด์", "Brand site")}</dt>'
                    f'<dd><a href="{att(bw)}" rel="nofollow noopener">{esc(bw)}</a></dd>')
    if r.get("lat") is not None:
        osm = f"https://www.openstreetmap.org/?mlat={r['lat']}&mlon={r['lng']}#map=18/{r['lat']}/{r['lng']}"
        gmap = f"https://maps.google.com/?q={r['lat']},{r['lng']}"
        approx = " " + bi("(โดยประมาณ)", "(approximate)") if r["geoPrecision"] == "approx" else ""
        rows.append(f'<dt>{bi("แผนที่", "Map")}</dt><dd><a href="{osm}" rel="noopener">OpenStreetMap</a> · '
                    f'<a href="{gmap}" rel="noopener">Google Maps</a>{approx}</dd>')
    else:
        rows.append(f'<dt>{bi("แผนที่", "Map")}</dt><dd><span class="badge pin">'
                    + bi("รอปักหมุด — ช่วยบอกพิกัดได้", "pin wanted — tell us where!") + "</span></dd>")
    blurb = ""
    if r.get("blurb_th") or r.get("blurb_en"):
        blurb = f'<p class="featured"><span class="star">★</span> {bi(r.get("blurb_th") or "", r.get("blurb_en") or "")}</p>'
    contact_cta = ""
    if not has_contact(r):
        issue = ("https://github.com/NaNoBotCo/mot-dang/issues/new?title="
                 + att(f"contact: {name_of(r)} ({r['id']})")
                 + "&body=" + att("เบอร์โทร / LINE / เว็บ / Facebook ของที่นี่คือ…"))
        cta = bi("รู้เบอร์โทร LINE หรือเพจของที่นี่ไหม — บอกมดแดงหน่อย ลงให้ฟรี",
                 "Know a phone, LINE, or page for this place? Tell the ants — listed free.")
        contact_cta = (f'<p class="myhint">☎️ {cta} '
                       f'<a href="{issue}" rel="noopener">{bi("ส่งเลย", "Send it")}</a> · '
                       f'{bi("เจ้าของร้านยิ่งยินดี", "Owners most welcome")}</p>')
    src = (r.get("sources") or [{}])[0]
    prov_line = {"osm": bi("ข้อมูลจาก OpenStreetMap", "Data from OpenStreetMap"),
                 "field": bi("ข้อมูลเก็บภาคสนาม", "Field-collected data"),
                 "curated": bi("ข้อมูลคัดสรรโดยทีมมดแดง", "Curated by the Mot Dang team")}.get(
        src.get("type"), bi("ข้อมูลเปิด", "Open data"))
    fetched = f" · {esc(src['fetched'])}" if src.get("fetched") else ""
    path = f"{r['province']}/p/{r['id']}.html"
    crumbs = (f'<a href="../../index.html">{bi("หน้าแรก", "Home")}</a> › '
              f'<a href="../index.html">{bi(prov_cfg["th"], prov_cfg["en"])}</a> › {esc(name_of(r))}')
    body = (f"<h1>{esc(name_of(r))}</h1>{blurb}<dl>{''.join(rows)}</dl>{contact_cta}"
            f"{share_block(BASE + path, name_of(r))}{ad_box(path, 2)}"
            f'<p class="prov">{prov_line}{fetched}</p>')
    desc = r.get("blurb_th") or f"{CATS[r['cat'][0]]['th']} · {prov_cfg['th']} · มดแดง"
    return page(name_of(r), body, depth=2, crumbs=crumbs, path=path, desc=desc)


def cat_shelf_html(prov_key, cat, live, count, teasers=True, muted_ok=True):
    """One Yahoo-style category entry: bold link (count) + teaser line, or a wireframe shelf."""
    c = CATS[cat]
    teaser = ""
    if teasers and c.get("teaser_th"):
        teaser = f'<span class="teaser">{bi(c["teaser_th"], c.get("teaser_en", ""))}</span>'
    if live:
        return (f'<li><b><a href="{prov_key}/{cat}/index.html">{bi(c["th"], c["en"])}</a></b> '
                f'<span class="count">({count:,})</span>{teaser}</li>')
    if not muted_ok:
        return ""
    return (f'<li class="shelf"><b>{bi(c["th"], c["en"])}</b> '
            f'<span class="soon">🐜 {bi("มดกำลังไปเก็บ", "ants on the way")}</span>{teaser}</li>')


def build():
    if DOCS.exists():
        shutil.rmtree(DOCS)
    DOCS.mkdir()
    (DOCS / ".nojekyll").write_text("")
    (DOCS / "CNAME").write_text(BASE.split("//")[1].strip("/") + "\n")
    (DOCS / "style.css").write_text(CSS)
    (DOCS / "md.js").write_text(JS)
    (DOCS / "data").mkdir()
    card = ROOT / "assets" / "card.png"
    if card.exists():
        shutil.copy(card, DOCS / "card.png")

    data = load()
    home_sections = []
    search_index = []
    pulse = {}

    for p in PROVINCES:
        key, records = p["key"], data[p["key"]]
        pdir = DOCS / key
        (pdir / "p").mkdir(parents=True)
        counts = {}
        for r in records:
            for c in r["cat"]:
                counts[c] = counts.get(c, 0) + 1
            search_index.append({"id": r["id"], "n": name_of(r), "e": r.get("nameEn"),
                                 "p": key, "pv": p["th"], "c": r["cat"]})
        live_cats = [c for c in CAT_ORDER if counts.get(c)]
        pulse[key] = {c: {"n": counts[c], "t": CATS[c]["th"], "v": p["th"]}
                      for c in live_cats}

        grow = f' <span class="grow">{bi("— กำลังเติบโต", "— growing")}</span>' \
            if p["mode"] == "wireframe" else ""
        # home: full build-out shows every shelf incl. wireframes; wireframe province shows live only
        shelf_lis = "".join(
            cat_shelf_html(key, c, c in live_cats, counts.get(c, 0),
                           muted_ok=(p["mode"] == "full")) for c in CAT_ORDER)
        home_sections.append(
            f'<h2><a href="{key}/index.html">{bi(p["th"], p["en"])}</a> '
            f'<span class="count">({len(records):,})</span>{grow}</h2>'
            f'<ul class="cats">{shelf_lis}</ul>')

        featured = [r for r in records if r.get("featured")]
        feat_html = ""
        if featured:
            cards = "".join(
                f'<div class="featured"><span class="star">★</span> '
                f'<a href="p/{r["id"]}.html"><strong>{esc(name_of(r))}</strong></a><br>'
                f'{bi(r.get("blurb_th") or "", r.get("blurb_en") or "")}</div>'
                for r in featured)
            feat_html = f'<h2>{bi("ที่น่าไป", "Places to visit")}</h2>{cards}'

        prov_shelves = "".join(
            cat_shelf_html(key, c, c in live_cats, counts.get(c, 0),
                           muted_ok=(p["mode"] == "full"))
            .replace(f'href="{key}/', 'href="') for c in CAT_ORDER)
        crumbs = f'<a href="../index.html">{bi("หน้าแรก", "Home")}</a> › {bi(p["th"], p["en"])}'
        (pdir / "index.html").write_text(page(
            p["th"],
            f'<h1>{bi(p["th"], p["en"])} <span class="count">({len(records):,})</span>{grow}</h1>'
            f'{feat_html}{ad_box(key + "/index.html", 1)}'
            f'<h2>{bi("หมวด", "Categories")}</h2><ul class="cats">{prov_shelves}</ul>'
            f'{share_block(BASE + key + "/index.html", "มดแดง " + p["th"])}',
            depth=1, crumbs=crumbs, path=f"{key}/index.html",
            desc=f"สารบัญ{p['th']} {len(records):,} แห่ง · มดแดง"))

        for c in live_cats:
            cdef = CATS[c]
            in_cat = sorted([r for r in records if c in r["cat"]],
                            key=lambda r: (not r.get("featured"), name_of(r)))
            (pdir / c).mkdir()
            # subcategory shelf (Yahoo genre: bold sub-links with counts; wireframes muted)
            sub_bits = []
            for child in cdef.get("children", []):
                in_sub = [r for r in in_cat if matches(r, child.get("match"))]
                if in_sub:
                    (pdir / c / child["key"]).mkdir(parents=True, exist_ok=True)
                    (pdir / c / child["key"] / "index.html").write_text(listing_page(
                        child["th"], child["en"],
                        sorted(in_sub, key=lambda r: (not r.get("featured"), name_of(r))),
                        depth=3, prov=key,
                        crumbs=(f'<a href="../../../index.html">{bi("หน้าแรก", "Home")}</a> › '
                                f'<a href="../../index.html">{bi(p["th"], p["en"])}</a> › '
                                f'<a href="../index.html">{bi(cdef["th"], cdef["en"])}</a> › '
                                f'{bi(child["th"], child["en"])}'),
                        path=f"{key}/{c}/{child['key']}/index.html"))
                    sub_bits.append(f'<b><a href="{child["key"]}/index.html">'
                                    f'{bi(child["th"], child["en"])}</a></b> '
                                    f'<span class="count">({len(in_sub):,})</span>')
                elif p["mode"] == "full":
                    sub_bits.append(f'<span class="shelf">{bi(child["th"], child["en"])} '
                                    f'<span class="soon">🐜</span></span>')
            subshelf = f'<div class="subshelf">{" · ".join(sub_bits)}</div>' if sub_bits else ""

            gj = geojson(in_cat)
            gj_name = f"{key}-{c}.geojson"
            (DOCS / "data" / gj_name).write_text(json.dumps(gj, ensure_ascii=False))
            dl = (f'<p class="prov"><a href="../../data/{gj_name}">⬇ GeoJSON</a> '
                  f'({len(gj["features"]):,} {bi("จุด", "points")})</p>')
            crumbs = (f'<a href="../../index.html">{bi("หน้าแรก", "Home")}</a> › '
                      f'<a href="../index.html">{bi(p["th"], p["en"])}</a> › {bi(cdef["th"], cdef["en"])}')
            lis = "".join(entry_li(r, f"../p/{r['id']}.html") for r in in_cat)
            body = (f'<h1>{bi(cdef["th"], cdef["en"])} <span class="count">({len(in_cat):,})</span></h1>'
                    f'{subshelf}{ad_box(f"{key}/{c}/index.html", 2)}{toolbar()}'
                    f'<ul class="dir" data-sortable>{lis}</ul>{dl}'
                    f'{share_block(BASE + f"{key}/{c}/index.html", cdef["th"] + " " + p["th"])}')
            (pdir / c / "index.html").write_text(page(
                cdef["th"], body, depth=2, crumbs=crumbs, path=f"{key}/{c}/index.html",
                desc=f"{cdef['th']} {p['th']} — {len(in_cat)} แห่ง · มดแดง"))

        for r in records:
            (pdir / "p" / f"{r['id']}.html").write_text(detail_page(r, p))

    # ---- home ----------------------------------------------------------
    ticker_items = json.loads((ROOT / "data" / "ticker.json").read_text()) \
        if (ROOT / "data" / "ticker.json").exists() else []
    tick_html = ""
    if ticker_items:
        bits = []
        for i in ticker_items:
            rel = "" if i["url"].endswith(".html") else ' rel="noopener"'
            src = f'<span class="src">{esc(i["src"])}</span> ' if i.get("src") else ""
            bits.append(f'<a href="{att(i["url"])}"{rel}>{bi(i["th"], i["en"])}</a>{src}')
        links = "".join(bits)
        tick_html = (f'<div class="module" id="m-ticker"><h3>{bi("ข่าววิ่ง", "News ticker")}</h3>'
                     f'<div class="tickerwrap"><span class="ticker">{links}</span></div></div>')
    day_html = (f'<div class="module" id="m-day"><h3>{bi("วันนี้", "Today")}</h3>'
                f'<p id="daycolor" style="margin:.2rem 0"></p></div>')
    total = len(search_index)
    rand_html = (f'<div class="module" id="m-rand"><h3>{bi("เดินเล่น", "Wander")}</h3>'
                 f'<p style="margin:.2rem 0"><a href="#" class="rand">🎲 '
                 f'{bi(f"สุ่มพาไปที่ใดที่หนึ่งใน {total:,} แห่ง", f"Take me somewhere — {total:,} places")}</a></p></div>')
    persona_html = (
        '<div class="persona" id="persona"><details><summary>⚙ '
        + bi("ปรับแต่งหน้าแรก", "Personalize") + "</summary>"
        + "".join(f'<label><input type="checkbox" data-mod="m-{k}"> {bi(th, en)}</label>'
                  for k, th, en in [("ticker", "ข่าววิ่ง", "News ticker"),
                                    ("day", "วันนี้-สีมงคล", "Today & colour"),
                                    ("rand", "เดินเล่น", "Wander")])
        + "</details></div>")
    intro_th = ("สารบัญเมืองเชียงใหม่และเชียงราย — วัด ร้าน หมอ ตลาด และของดีทุกซอย "
                "เรียงเป็นหมวดให้เปิดหาได้เหมือนสมุดหน้าเมือง")
    intro_en = ("A city directory for Chiang Mai and Chiang Rai — wats, shops, doctors, "
                "markets, and the good things down every soi, sorted the old way.")
    (DOCS / "index.html").write_text(page(
        "มดแดง",
        f"<p>{bi(intro_th, intro_en)}</p>{persona_html}{tick_html}{day_html}{rand_html}"
        + ad_box("index.html", 0) + "".join(home_sections)
        + share_block(BASE, "มดแดง — สารบัญเมืองเชียงใหม่ · เชียงราย"),
        depth=0, path="", desc=intro_th))

    # ---- my page: the personal start page, the pre-Google way -----------
    pick_groups = []
    for p in PROVINCES:
        boxes = "".join(
            f'<label><input type="checkbox" data-pc="{p["key"]}/{c}"> '
            f'{bi(CATS[c]["th"], CATS[c]["en"])} '
            f'<span class="count">({pulse[p["key"]][c]["n"]:,})</span></label>'
            for c in CAT_ORDER if c in pulse[p["key"]])
        pick_groups.append(f'<p><b>{bi(p["th"], p["en"])}</b><br>{boxes}</p>')
    my_hint_th = ("ตั้งหน้านี้เป็นหน้าแรกของเบราว์เซอร์ แล้วออกท่องเว็บจากที่นี่ทุกวัน — "
                  "ทุกการตั้งค่าอยู่ในเครื่องของคุณเท่านั้น มดแดงไม่ตามรอยใคร")
    my_hint_en = ("Set this as your browser's home page and start every day here — "
                  "your choices live only on this device. Mot Dang follows no one around.")
    my_body = (
        f'<h1>🏠 {bi("หน้าแรกของฉัน", "My page")}</h1>'
        f'<p class="myhint">💡 {bi(my_hint_th, my_hint_en)}</p>'
        f'<div class="module"><h3>{bi("ของดีวันนี้", "Pick of the day")}</h3>'
        f'<p id="dailypick" style="margin:.2rem 0">…</p></div>'
        f'<div class="module"><h3>{bi("หมวดที่ปักไว้", "Pinned shelves")}</h3>'
        f'<ul class="dir" id="myshelf"></ul>'
        f'<details id="pinpick"><summary>📌 {bi("เลือกหมวดมาปัก", "Choose shelves to pin")}</summary>'
        f'{"".join(pick_groups)}</details></div>'
        f'<div class="module"><h3>{bi("ลิงก์ของฉัน", "My links")}</h3>'
        f'<form id="bmform"><input name="n" placeholder="ชื่อ / name">'
        f'<input name="u" placeholder="https://…"><button>{bi("เพิ่ม", "Add")}</button></form>'
        f'<ul class="dir" id="bmlist"></ul></div>'
        f'<div class="module"><h3>{bi("โน้ตติดหน้าแรก", "Sticky notes")}</h3>'
        f'<textarea id="mynotes" placeholder="จดอะไรก็ได้… / jot anything…"></textarea></div>'
        f"{tick_html}{day_html}{rand_html}"
        f'<script type="application/json" id="pulse">{json.dumps(pulse, ensure_ascii=False)}</script>')
    (DOCS / "my.html").write_text(page("หน้าแรกของฉัน", my_body, depth=0, path="my.html",
                                       desc=my_hint_th))

    # ---- contact drive: the gap, shown plainly and made joinable --------
    all_recs = [r for p in PROVINCES for r in data[p["key"]]]
    have = [r for r in all_recs if has_contact(r)]
    pct = 100 * len(have) // len(all_recs)
    by_shelf = {}
    for r in all_recs:
        for c in r["cat"]:
            s = by_shelf.setdefault((r["province"], c), [0, 0])
            s[1] += 1
            if has_contact(r):
                s[0] += 1
    pnames = {p["key"]: (p["th"], p["en"]) for p in PROVINCES}
    rows_html = "".join(
        f'<li><a href="{pv}/{c}/index.html"><b>{bi(CATS[c]["th"], CATS[c]["en"])}</b></a> '
        f'<span class="count">· {bi(*pnames[pv])} · {h}/{t} = {100 * h // t}%</span> '
        f'<span class="shelf">{"🐜" * (1 + (100 * h // t) // 25)}</span></li>'
        for (pv, c), (h, t) in sorted(by_shelf.items(), key=lambda kv: (kv[1][0] / kv[1][1], -kv[1][1])))
    drive_th = (f"ตอนนี้มีข้อมูลติดต่อแล้ว {len(have):,} จาก {len(all_recs):,} แห่ง ({pct}%) — "
                "อีกเยอะที่ยังขาด เบอร์โทร ไลน์ เพจ หรือเว็บของร้านไหนก็ได้ ส่งมาได้เลย ลงให้ฟรีเสมอ "
                "เจ้าของร้านยิ่งยินดี ช่วยกันคนละนิด สารบัญเมืองก็ครบขึ้นทุกวัน")
    drive_en = (f"{len(have):,} of {len(all_recs):,} places ({pct}%) have a way to reach them. "
                "The rest need one. A phone, a LINE id, a page, a website — any of it, for any "
                "place. Free to list, always. Shop owners especially welcome.")
    (DOCS / "contacts.html").write_text(page(
        "ช่วยเติมข้อมูลติดต่อ",
        f'<h1>☎️ {bi("ช่วยเติมข้อมูลติดต่อ", "Help fill in the contacts")}</h1>'
        f'<p class="myhint">{bi(drive_th, drive_en)}</p>'
        f'<p><a href="https://github.com/NaNoBotCo/mot-dang/issues/new" rel="noopener">'
        f'<b>{bi("ส่งข้อมูลติดต่อ", "Send a contact")}</b></a> · '
        f'<a href="{KOFI}" rel="noopener">{bi("ทางโคฟาย", "via Ko-fi")}</a> · '
        f'<a href="https://www.openstreetmap.org/" rel="noopener">'
        f'{bi("หรือเติมลง OpenStreetMap โดยตรง", "or add it straight to OpenStreetMap")}</a></p>'
        f'<h2>{bi("หมวดที่ยังขาดมากที่สุด", "Shelves that need it most")}</h2>'
        f'<ul class="dir">{rows_html}</ul>'
        f'{share_block(BASE + "contacts.html", "ช่วยเติมข้อมูลติดต่อ · มดแดง")}',
        depth=0, path="contacts.html", desc=drive_th))

    # ---- advertise: the 1997-innocent ad policy --------------------------
    adv_body = (
        f'<h1>{bi("ลงโฆษณากับมดแดง", "Advertise with Mot Dang")}</h1>'
        f'<p>{bi("โฆษณาแบบปีหนึ่งเก้าเก้าเจ็ด — สุภาพ ชัดเจน ไม่ตามรอยใคร", "Ads the 1997 way — polite, clearly marked, tracking no one.")}</p>'
        f'<ul>'
        f'<li>{bi("ข้อความล้วน หรือภาพนิ่งขนาดพองาม — ไม่มีป๊อปอัป ไม่มีวิดีโอเด้ง", "Text, or one tasteful still picture — no popups, nothing that jumps at you")}</li>'
        f'<li>{bi("เหมาจ่ายรายเดือน ราคาเดียว คุยกันได้", "One flat monthly rate, friendly to talk about")}</li>'
        f'<li>{bi("ทุกชิ้นติดป้าย ผู้สนับสนุน เสมอ", "Every placement is marked ผู้สนับสนุน · sponsor, every time")}</li>'
        f'<li>{bi("โฆษณาไม่มีวันเปลี่ยนลำดับหรือเนื้อหาสารบัญ — สารบัญคือสารบัญ", "Ads never change listing order or content — the directory is the directory")}</li>'
        f'</ul>'
        f'<p>{bi("สนใจ? ทักมาทาง", "Interested? Reach us via")} '
        f'<a href="https://github.com/NaNoBotCo/mot-dang/issues/new" rel="noopener">GitHub</a> · '
        f'<a href="{KOFI}" rel="noopener">Ko-fi</a></p>')
    (DOCS / "advertise.html").write_text(page("ลงโฆษณา", adv_body, depth=0, path="advertise.html",
                                              desc="ลงโฆษณากับมดแดง — โฆษณาแบบปี 1997 สุภาพ ไม่ตามรอยใคร"))

    # ---- search + suggest ----------------------------------------------
    (DOCS / "data" / "index.json").write_text(
        json.dumps(search_index, ensure_ascii=False))
    (DOCS / "search.html").write_text(page(
        "ค้นหา",
        f'<h1>{bi("ผลการค้นหา", "Search results")} <span class="count" id="rescount"></span></h1>'
        '<ul class="dir" id="results"></ul>',
        depth=0, path="search.html", desc="ค้นหาในมดแดง"))
    suggest_th = ("มดแดงรับฟังเสมอ — ร้านของคุณ ที่ที่คุณรัก หรือหมุดที่ยังไม่ปัก "
                  "ส่งมาได้ ลงสารบัญฟรี ทีมงานตรวจทานทุกรายการก่อนขึ้นหน้า")
    suggest_en = ("Mot Dang is all ears — your shop, a place you love, or a pin we're missing. "
                  "Listings are free; every entry is reviewed before it goes up.")
    (DOCS / "suggest.html").write_text(page(
        "แนะนำร้าน",
        f'<h1>{bi("แนะนำร้าน-เพิ่มที่ของคุณ", "Add your place")}</h1>'
        f"<p>{bi(suggest_th, suggest_en)}</p>"
        f'<p><a href="https://github.com/NaNoBotCo/mot-dang/issues/new" rel="noopener">'
        f'{bi("ส่งผ่าน GitHub", "Suggest via GitHub")}</a> · '
        f'<a href="{KOFI}" rel="noopener">{bi("ฝากข้อความทาง Ko-fi", "Message us on Ko-fi")}</a></p>'
        f"<p>{bi('เร็วๆ นี้: ฟอร์มแนะนำในหน้านี้เลย', 'Coming soon: a suggestion form right here.')}</p>",
        depth=0, path="suggest.html", desc=suggest_th))

    n_pages = sum(1 for _ in DOCS.rglob("*.html"))
    print(f"built {n_pages:,} pages -> docs/")


if __name__ == "__main__":
    build()
