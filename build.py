#!/usr/bin/env python3
"""Mot Dang (มดแดง) — static site builder. data/canonical/*.json -> docs/ (GitHub Pages).

Thai-first, 1997 directory genre studied from the real thing (Yahoo!, April 1997):
search box up top, bold categories with teaser sub-links, counts in parens,
subcategory shelves, a random link, "how to include your site", and a
personalizable home (My Yahoo!) with a news ticker. EN is a client-side
display layer. No tracking, no third-party scripts, no external requests
on load; outbound links only. OSM attribution stays.
"""
import base64
import io
import json
import shutil
from pathlib import Path

try:
    import qrcode
    HAVE_QR = True
except ImportError:
    HAVE_QR = False

ROOT = Path(__file__).resolve().parent
DOCS = ROOT / "docs"
BUILD_DATE = "2026-07-27"
BASE = "https://motdang.net/"
KOFI = "https://ko-fi.com/defiantchiangmai"


def qr_data_uri(url):
    """Tiny inline PNG QR (~500 bytes) — zero extra requests, print-and-scan ready."""
    if not HAVE_QR:
        return None
    buf = io.BytesIO()
    qrcode.make(url, box_size=5, border=2).save(buf, format="PNG")
    return "data:image/png;base64," + base64.b64encode(buf.getvalue()).decode()

CFG = json.loads((ROOT / "data" / "categories.json").read_text())
CATS = {c["key"]: c for c in CFG["categories"]}
CAT_ORDER = [c["key"] for c in CFG["categories"]]
PROVINCES = CFG["provinces"]

PHOTOS_SRC = ROOT / "assets" / "photos"
_credits_path = PHOTOS_SRC / "credits.json"
PHOTO_CREDITS = json.loads(_credits_path.read_text()) if _credits_path.exists() else {}

# Original stylized wat illustration — the default photo everywhere a real one
# is missing. Hand-drawn shapes, brand palette, not a copy of any real temple.
WAT_SVG = """<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 480 320" role="img">
<title>ภาพประกอบวัด (ยังไม่มีรูปจริงของสถานที่นี้) — illustrative wat, no real photo yet</title>
<rect width="480" height="320" fill="#FBF6EE"/>
<rect x="40" y="285" width="400" height="8" fill="#2A1E16" opacity=".15"/>
<rect x="80" y="270" width="320" height="18" rx="3" fill="#8F2E13"/>
<rect x="105" y="190" width="270" height="82" fill="#FBF6EE" stroke="#2A1E16" stroke-width="3"/>
<rect x="130" y="215" width="34" height="57" fill="#2A1E16" opacity=".18"/>
<rect x="223" y="215" width="34" height="57" fill="#2A1E16" opacity=".18"/>
<rect x="316" y="215" width="34" height="57" fill="#2A1E16" opacity=".18"/>
<polygon points="65,190 415,190 345,150 135,150" fill="#C2401C" stroke="#2A1E16" stroke-width="2"/>
<polygon points="135,150 345,150 300,113 180,113" fill="#8F2E13" stroke="#2A1E16" stroke-width="2"/>
<polygon points="180,113 300,113 268,82 212,82" fill="#C2401C" stroke="#2A1E16" stroke-width="2"/>
<polygon points="222,82 258,82 240,35" fill="#8F2E13"/>
<circle cx="240" cy="30" r="6" fill="#C2401C"/>
<path d="M60,190 Q45,170 60,150" fill="none" stroke="#8F2E13" stroke-width="4" stroke-linecap="round"/>
<path d="M420,190 Q435,170 420,150" fill="none" stroke="#8F2E13" stroke-width="4" stroke-linecap="round"/>
<g fill="#2A1E16">
  <ellipse cx="404" cy="278" rx="5" ry="4"/>
  <ellipse cx="413" cy="278" rx="4" ry="3.4"/>
  <ellipse cx="420" cy="277" rx="6" ry="4.6"/>
  <line x1="406" y1="280" x2="402" y2="286" stroke="#2A1E16" stroke-width="1.4"/>
  <line x1="411" y1="280" x2="415" y2="286" stroke="#2A1E16" stroke-width="1.4"/>
  <line x1="422" y1="279" x2="427" y2="284" stroke="#2A1E16" stroke-width="1.4"/>
</g>
</svg>"""


def collect_photos():
    """assets/photos/<record-id>.(jpg|jpeg|png|webp) -> {id: filename}."""
    out = {}
    if PHOTOS_SRC.exists():
        for f in sorted(PHOTOS_SRC.iterdir()):
            if f.suffix.lower() in (".jpg", ".jpeg", ".png", ".webp"):
                out[f.stem] = f.name
    return out


SCHEMA_TYPE = {
    "wat": "TouristAttraction", "hotel": "LodgingBusiness", "food": "Restaurant",
    "massage": "HealthAndBeautyBusiness", "medical": "MedicalBusiness",
    "essentials": "LocalBusiness", "school-intl": "School", "market": "LocalBusiness",
    "shopping": "Store", "realestate": "RealEstateAgent", "transport": "LocalBusiness",
    "repair": "LocalBusiness", "beauty": "HealthAndBeautyBusiness", "pets": "LocalBusiness",
    "learn": "EducationalOrganization", "museums-galleries": "TouristAttraction",
    "sights": "TouristAttraction", "whats-on": "EntertainmentBusiness",
    "home-services": "LocalBusiness", "community": "Organization", "business": "LocalBusiness",
}


def ld_json(r, path, photo_file):
    a = r.get("attrs", {})
    obj = {
        "@context": "https://schema.org",
        "@type": SCHEMA_TYPE.get(r["cat"][0], "LocalBusiness"),
        "name": name_of(r),
        "url": BASE + path,
        "image": BASE + (f"photos/{photo_file}" if photo_file else "wat.svg"),
    }
    if r.get("address"):
        obj["address"] = {"@type": "PostalAddress", "streetAddress": r["address"],
                           "addressCountry": "TH"}
    if r.get("lat") is not None:
        obj["geo"] = {"@type": "GeoCoordinates", "latitude": r["lat"], "longitude": r["lng"]}
    if r.get("phone"):
        obj["telephone"] = r["phone"]
    if r.get("website"):
        obj["sameAs"] = [r["website"]]
    same_as = obj.get("sameAs", [])
    for key, base in (("facebook", "https://www.facebook.com/"), ("instagram", "https://www.instagram.com/")):
        v = a.get(key)
        if v:
            same_as.append(v if v.startswith("http") else base + v.lstrip("@"))
    if same_as:
        obj["sameAs"] = same_as
    return f'<script type="application/ld+json">{json.dumps(obj, ensure_ascii=False)}</script>'

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
.share{margin-top:1.2rem}
.share .sharelabel{font-size:.9rem;color:var(--ant-dark);font-weight:600;display:block;margin-bottom:.4rem}
.share .row{display:flex;gap:.5rem;flex-wrap:wrap;align-items:center}
.share .pill{display:inline-flex;align-items:center;gap:.3rem;padding:.3rem .85rem;
border-radius:999px;text-decoration:none;font-weight:600;font-size:.88rem;color:#fff;
border:none;cursor:pointer;font-family:inherit;transition:transform .12s,box-shadow .12s}
.share .pill:hover{transform:translateY(-1px);box-shadow:0 3px 8px rgba(0,0,0,.18)}
.share .pill:visited{color:#fff}
.share .pill.native{background:var(--ant)}
.share .pill.line{background:#06C755}
.share .pill.whatsapp{background:#25D366}
.share .pill.telegram{background:#229ED9}
.share .pill.facebook{background:#1877F2}
.share .pill.x{background:#111}
.share .pill.copy{background:var(--ant-dark)}
.qrbox{display:flex;align-items:center;gap:.8rem;margin-top:.7rem;background:#fff;
border:1px solid var(--soft);border-radius:.7rem;padding:.6rem .9rem;max-width:26rem}
.qrbox img{width:76px;height:76px;image-rendering:pixelated;flex-shrink:0}
.qrbox p{margin:0;font-size:.85rem;color:var(--mute)}
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
.topicwidget{background:#fff;border:1px solid var(--soft);border-radius:.7rem;
padding:.6rem 1rem;margin:.6rem 0}
.topicwidget h4{margin:0 0 .2rem;font-size:1.02rem}
.topicwidget h4 a{text-decoration:none} .topicwidget h4 a:hover{text-decoration:underline}
.topicwidget .preview{list-style:none;padding:0;margin:.3rem 0 0;font-size:.88rem}
.topicwidget .preview li{margin:.1rem 0}
.topicwidget .unpin{float:right;border:none;background:none;color:var(--mute);
cursor:pointer;font-size:.85rem}
.highlights{display:flex;gap:.9rem;overflow-x:auto;padding:.3rem 0 .8rem;margin:.4rem 0}
.highlights::-webkit-scrollbar{height:8px}
.hicard{flex:0 0 auto;width:11rem;background:#fff;border:1px solid var(--soft);
border-radius:.7rem;overflow:hidden;text-decoration:none;color:var(--ink);
box-shadow:2px 2px 0 var(--soft);transition:transform .15s}
.hicard:hover{transform:translateY(-3px)} .hicard:visited{color:var(--ink)}
.hicard img{width:100%;height:7rem;object-fit:cover;display:block;background:var(--soft)}
.hicard .cap{padding:.4rem .55rem;font-size:.85rem;font-weight:600;line-height:1.3}
.hicard .cat{display:block;font-weight:400;color:var(--mute);font-size:.78rem}
.widgetgallery{display:flex;gap:.5rem;flex-wrap:wrap;margin:.4rem 0}
.widgetgallery button{font:inherit;font-size:.85rem;border:1.5px solid var(--ant-dark);
background:none;color:var(--ant-dark);border-radius:999px;padding:.2rem .8rem;cursor:pointer}
.widgetgallery button:hover{background:var(--ant-dark);color:var(--paper)}
.widgetgallery button:disabled{opacity:.45;cursor:default;background:none;color:var(--mute);
border-color:var(--soft)}
.widgetbox{border:1px solid var(--soft);border-radius:.7rem;overflow:hidden;margin:.6rem 0;background:#fff}
.widgetbox .wtitle{display:flex;justify-content:space-between;align-items:center;
padding:.35rem .8rem;background:var(--soft);font-size:.85rem;font-weight:600;color:var(--ant-dark)}
.widgetbox .wtitle button{border:none;background:none;color:var(--mute);cursor:pointer;font-size:.9rem}
.widgetbox iframe{width:100%;height:22rem;border:none;display:block}
#addwidgetform input{font:inherit;font-size:.9rem;padding:.2rem .5rem;border:1.5px solid var(--soft);
border-radius:.4rem;margin-right:.4rem;max-width:11rem}
#addwidgetform button{font:inherit;font-size:.9rem;border:1.5px solid var(--ant);background:none;
color:var(--ant);border-radius:.4rem;padding:.15rem .7rem;cursor:pointer}
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
.photo{max-width:100%;height:auto;max-height:280px;border-radius:.6rem;border:1px solid var(--soft);
margin:.6rem 0;display:block;background:#fff}
.phototag{color:var(--mute);font-size:.8rem;margin:-.4rem 0 .6rem}
.chartlegend{font-size:.9rem;margin:.4rem 0}
.chartlegend .swatch{display:inline-block;width:.9em;height:.9em;border-radius:3px;
vertical-align:-.1em;margin-right:.3em}
.chartcap{color:var(--mute);font-size:.82rem;margin-top:-.3rem}
.tilerow{display:flex;gap:.8rem;flex-wrap:wrap;margin:1rem 0}
.tile{background:#fff;border:1px solid var(--soft);border-radius:.7rem;padding:.6rem 1.2rem;
text-align:center;min-width:7rem}
.tile b{display:block;font-size:1.7rem;color:var(--ant);line-height:1.3}
.tile span{font-size:.78rem;color:var(--mute)}
.missionbar{position:relative;background:var(--soft);border-radius:999px;height:28px;
overflow:hidden;margin:.6rem 0}
.missionfill{background:linear-gradient(90deg,#F6D9CE,var(--ant));height:100%;border-radius:999px}
.missionlabel{position:absolute;top:0;left:.8rem;line-height:28px;font-weight:700;
color:var(--ink);font-size:.9rem}
table.sortable{width:100%;border-collapse:collapse;margin:1rem 0;font-size:.92rem}
table.sortable th,table.sortable td{padding:.35rem .6rem;text-align:right;
border-bottom:1px solid var(--soft)}
table.sortable th:first-child,table.sortable td:first-child{text-align:left}
table.sortable thead th{background:var(--soft);color:var(--ant-dark);cursor:pointer;
user-select:none}
table.sortable thead th:hover{background:#dfcfae}
table.sortable thead th.sorted::after{content:" ▾"}
table.sortable thead th.sorted.asc::after{content:" ▴"}
.reqform label{display:block;margin:.7rem 0 .2rem;font-weight:600;color:var(--ant-dark)}
.reqform input,.reqform select,.reqform textarea{font:inherit;font-size:.95rem;padding:.35rem .6rem;
border:1.5px solid var(--soft);border-radius:.5rem;background:#fff;color:var(--ink);
width:100%;max-width:28rem;box-sizing:border-box}
.reqform textarea{min-height:6rem}
.reqform button{margin-top:.9rem;font:inherit;border:2px solid var(--ant);background:var(--ant);
color:#fff;border-radius:.5rem;padding:.4rem 1.2rem;cursor:pointer}
.reqform button:hover{background:var(--ant-dark)}
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
const preview=sample.map(e=>`<li><a href="${pv}/p/${e.id}.html">${H(e.n)}</a></li>`).join('')
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
el.innerHTML=`<a href="${pick.p}/p/${pick.id}.html">${H(pick.n)}</a> <span class="count">· ${H(pick.pv)}</span>`;})();
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
if(persona){const mods=['m-ticker','m-day','m-rand'];
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
"""


def esc(s):
    return (s or "").replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")


def att(s):
    return esc(s).replace('"', "&quot;")


def bi(th, en):
    return f'<span class="th">{esc(th)}</span><span class="en">{esc(en)}</span>'


BE_BUILD = int(BUILD_DATE[:4]) + 543


def page(title, body, depth, crumbs="", path="", desc="", extra_head=""):
    r = "../" * depth
    url = BASE + path
    tt = esc(title) + " · มดแดง" if title != "มดแดง" else "มดแดง — สารบัญเมืองเชียงใหม่ · เชียงราย"
    d = att(desc or "มดแดง — สารบัญเมืองเชียงใหม่และเชียงราย แบบสมุดหน้าเมือง")
    return f"""<!DOCTYPE html>
<html lang="th" data-root="{r}"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>{tt}</title>
<meta name="description" content="{d}">
<meta name="robots" content="index,follow">
<link rel="canonical" href="{att(url)}">
<meta property="og:site_name" content="มดแดง Mot Dang">
<meta property="og:title" content="{att(tt)}">
<meta property="og:description" content="{d}">
<meta property="og:type" content="website">
<meta property="og:url" content="{att(url)}">
<meta property="og:image" content="{BASE}card.png">
<meta property="og:locale" content="th_TH">
<meta name="twitter:card" content="summary_large_image">
<link rel="alternate" type="application/rss+xml" title="มดแดง — ของเด่น" href="{r}rss.xml">
<link rel="stylesheet" href="{r}style.css">
<link rel="icon" href="data:image/svg+xml,<svg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 100 100'><text y='.9em' font-size='90'>🐜</text></svg>">
{extra_head}</head><body>
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
    <a href="{r}crawl-request.html">🐜 {bi("ส่งมดไปสำรวจ", "Request a crawl")}</a> ·
    <a href="#" class="rand">🎲 {bi("สุ่มพาไป", "Random place")}</a> ·
    <a href="{r}stats.html">📊 {bi("สถิติ", "Stats")}</a> ·
    <a href="{r}advertise.html">{bi("ลงโฆษณา", "Advertise")}</a> ·
    <a href="{KOFI}" rel="noopener">☕ {bi("เลี้ยงกาแฟมดแดง", "Buy the ants a coffee")}</a>
  </div>
</header>
{f'<nav class="crumbs">{crumbs}</nav>' if crumbs else ''}
{body}
<footer>
  {bi(f"สร้างจากข้อมูลเปิดและการเดินเก็บจริง · ปรับปรุง {BUILD_DATE} (พ.ศ. {BE_BUILD})",
      f"Built from open data and shoe-leather · updated {BUILD_DATE} (B.E. {BE_BUILD})")}<br>
  © <a href="https://www.openstreetmap.org/copyright" rel="noopener">OpenStreetMap contributors</a> (ODbL) ·
  <a href="https://github.com/NaNoBotCo/mot-dang" rel="noopener">GitHub</a> ·
  <a href="{KOFI}" rel="noopener">Ko-fi</a> ·
  <a href="{r}rss.xml">📡 RSS</a> ·
  <a href="{r}partners.html">{bi("แลกฟีด", "Partners")}</a> ·
  <a href="{r}llms.txt">llms.txt</a>
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
WIDGETS = json.loads((ROOT / "data" / "widgets.json").read_text())


def ad_box(path, depth):
    import zlib
    ad = ADS[zlib.crc32(path.encode()) % len(ADS)]
    href = "../" * depth + ad["url"] if ad.get("house") else ad["url"]
    rel = "" if ad.get("house") else ' rel="noopener"'
    return (f'<div class="adbox"><span class="adlabel">— {esc("ผู้สนับสนุน")} · sponsor —</span>'
            f'<a href="{att(href)}"{rel}><b>{bi(ad["th"], ad["en"])}</b></a>'
            f'<a class="adsell" href="{"../" * depth}advertise.html">'
            + bi("ลงโฆษณาที่นี่", "advertise here") + "</a></div>")


def share_block(url, name, qr=False):
    u, t = att(url), att(name)
    qr_html = ""
    if qr:
        data_uri = qr_data_uri(url)
        if data_uri:
            qr_th = "สแกนแชร์หรือพกไว้หน้าร้านก็ได้"
            qr_en = "Scan to share — or print it by the door"
            qr_html = (f'<div class="qrbox"><img src="{data_uri}" alt="QR code" width="76" height="76">'
                      f'<p>{bi(qr_th, qr_en)}</p></div>')
    return (f'<div class="share"><span class="sharelabel">{bi("บอกต่อ", "Share")}</span>'
            f'<div class="row">'
            f'<button class="pill native" data-native data-url="{u}" data-title="{t}" style="display:none">'
            f'📤 {bi("แชร์", "Share")}</button>'
            f'<a class="pill line" href="https://social-plugins.line.me/lineit/share?url={u}" rel="noopener">LINE</a>'
            f'<a class="pill whatsapp" href="https://wa.me/?text={t}%20{u}" rel="noopener">WhatsApp</a>'
            f'<a class="pill telegram" href="https://t.me/share/url?url={u}&text={t}" rel="noopener">Telegram</a>'
            f'<a class="pill facebook" href="https://www.facebook.com/sharer/sharer.php?u={u}" rel="noopener">Facebook</a>'
            f'<a class="pill x" href="https://twitter.com/intent/tweet?url={u}&text={t}" rel="noopener">X</a>'
            f'<button class="pill copy copylink" data-url="{u}" data-label="🔗 {esc("คัดลอกลิงก์")}" '
            f'data-done="✓ {esc("คัดลอกแล้ว")}">🔗 {esc("คัดลอกลิงก์")}</button>'
            f'</div>{qr_html}</div>')


def detail_page(r, prov_cfg, photo_file=None):
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
                       f'{bi("เจ้าของร้านยิ่งยินดีเจ้า", "Owners most welcome")}</p>')
    if photo_file:
        img_tag = (f'<img class="photo" src="../../photos/{att(photo_file)}" '
                   f'alt="{att(name_of(r))}" loading="lazy">')
        credit = PHOTO_CREDITS.get(r["id"])
        if credit and credit.get("source"):
            photo_note = (f'<p class="phototag">📷 <a href="{att(credit["source"])}" rel="noopener">'
                         f'{esc(credit.get("author") or "Wikimedia Commons")}</a>'
                         f' — {esc(credit.get("license") or "")}, via Wikimedia Commons</p>')
        else:
            photo_note = ""
        photo_cta = ""
    else:
        img_tag = (f'<img class="photo" src="../../wat.svg" '
                   f'alt="{att("ภาพประกอบวัด (ยังไม่มีรูปจริงของสถานที่นี้) — illustrative wat, no real photo yet")}" loading="lazy">')
        pn_th = "ยังไม่มีรูปของที่นี่ — ใช้ภาพวัดแทนไปพลางก่อน"
        pn_en = "No real photo of this place yet — a placeholder wat, for now"
        photo_note = f'<p class="phototag">📷 {bi(pn_th, pn_en)}</p>'
        issue_photo = ("https://github.com/NaNoBotCo/mot-dang/issues/new?title="
                       + att(f"photo: {name_of(r)} ({r['id']})")
                       + "&body=" + att("ลากรูปมาวางในกล่องข้อความได้เลย"))
        pcta = bi("มีรูปที่นี่ไหม — ลากรูปมาวางในอีชูได้เลย จะใส่แทนภาพวัดให้",
                  "Have a photo of this place? Drop it into a GitHub issue and we'll swap it in.")
        photo_cta = (f'<p class="myhint">📷 {pcta} '
                     f'<a href="{issue_photo}" rel="noopener">{bi("แนบรูป", "Add a photo")}</a> · '
                     f'{bi("ไม่ต้องขอบคุณ มดขอบคุณเองเจ้า", "No thanks needed — the ants thank you")}</p>')
    src = (r.get("sources") or [{}])[0]
    prov_line = {"osm": bi("ข้อมูลจาก OpenStreetMap", "Data from OpenStreetMap"),
                 "field": bi("ข้อมูลเก็บภาคสนาม", "Field-collected data"),
                 "curated": bi("ข้อมูลคัดสรรโดยทีมมดแดง", "Curated by the Mot Dang team")}.get(
        src.get("type"), bi("ข้อมูลเปิด", "Open data"))
    fetched = f" · {esc(src['fetched'])}" if src.get("fetched") else ""
    path = f"{r['province']}/p/{r['id']}.html"
    crumbs = (f'<a href="../../index.html">{bi("หน้าแรก", "Home")}</a> › '
              f'<a href="../index.html">{bi(prov_cfg["th"], prov_cfg["en"])}</a> › {esc(name_of(r))}')
    body = (f"<h1>{esc(name_of(r))}</h1>{img_tag}{photo_note}{blurb}<dl>{''.join(rows)}</dl>"
            f"{contact_cta}{photo_cta}"
            f"{share_block(BASE + path, name_of(r), qr=True)}{ad_box(path, 2)}"
            f'<p class="prov">{prov_line}{fetched}</p>')
    desc = r.get("blurb_th") or f"{CATS[r['cat'][0]]['th']} · {prov_cfg['th']} · มดแดง"
    return page(name_of(r), body, depth=2, crumbs=crumbs, path=path, desc=desc,
                extra_head=ld_json(r, path, photo_file))


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
    (DOCS / "wat.svg").write_text(WAT_SVG)
    photos = collect_photos()
    if photos:
        (DOCS / "photos").mkdir()
        for fname in photos.values():
            shutil.copy(PHOTOS_SRC / fname, DOCS / "photos" / fname)

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
            (pdir / "p" / f"{r['id']}.html").write_text(
                detail_page(r, p, photos.get(r["id"])))

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

    # ---- highlights: the home page comes prefilled, not blank ------------
    hi_pool = [(p["key"], r) for p in PROVINCES for r in data[p["key"]] if r.get("featured")]
    hi_pool += sorted(
        ((p["key"], r) for p in PROVINCES for r in data[p["key"]]
         if r["id"] in photos and not r.get("featured")),
        key=lambda pr: pr[1]["id"])
    seen_hi = set()
    hi_cards = []
    for pv, r in hi_pool:
        if r["id"] in seen_hi or len(hi_cards) >= 8:
            continue
        seen_hi.add(r["id"])
        thumb = f"photos/{photos[r['id']]}" if r["id"] in photos else "wat.svg"
        cat_th = CATS[r["cat"][0]]["th"]
        hi_cards.append(
            f'<a class="hicard" href="{pv}/p/{r["id"]}.html"><img src="{thumb}" '
            f'alt="{att(name_of(r))}" loading="lazy">'
            f'<span class="cap">{esc(name_of(r))}<span class="cat">{esc(cat_th)}</span></span></a>')
    hi_html = (f'<h2>{bi("ของเด่นวันนี้", "Highlights")}</h2>'
              f'<div class="highlights">{"".join(hi_cards)}</div>') if hi_cards else ""

    (DOCS / "index.html").write_text(page(
        "มดแดง",
        f"<p>{bi(intro_th, intro_en)}</p>{hi_html}{persona_html}{tick_html}{day_html}{rand_html}"
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
                  "ทุกการตั้งค่าอยู่ในเครื่องของคุณเท่านั้น มดแดงไม่ตามรอยใครเจ้า")
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
        f'<div class="module"><h3>🧩 {bi("วิดเจ็ตของฉัน", "My widgets")}</h3>'
        f'<p class="chartcap">{bi("ใส่วิดเจ็ตที่ฉันทำเอง หรือของใครก็ได้ตามลิงก์", "Add widgets I made — or any link at all")}</p>'
        f'<div class="widgetgallery" id="widgetgallery"></div>'
        f'<form id="addwidgetform"><input name="n" placeholder="ชื่อ / name">'
        f'<input name="u" placeholder="https://…"><button>{bi("เพิ่ม", "Add")}</button></form>'
        f'<div id="widgetboxes"></div>'
        f'<script type="application/json" id="widgets-data">{json.dumps(WIDGETS, ensure_ascii=False)}</script></div>'
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
                "เจ้าของร้านยิ่งยินดี ช่วยกันคนละนิด สารบัญเมืองก็ครบขึ้นทุกวันเจ้า")
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
                  "ส่งมาได้ ลงสารบัญฟรี ทีมงานตรวจทานทุกรายการก่อนขึ้นหน้าเจ้า")
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

    # ---- crawl request: ask the ants to go survey somewhere new ----------
    cat_options = "".join(f'<option value="{att(CATS[c]["th"])}">' for c in CAT_ORDER)
    cr_th = ("ยังไม่มีหมวดที่ต้องการ หรืออยากให้มดไปสำรวจพื้นที่ใหม่ทั้งอำเภอ? "
             "บอกมาได้เลยเจ้า มดจะได้วางแผนไปเก็บข้อมูลรอบต่อไป")
    cr_en = ("Missing a category, or want the ants to survey a whole new district? "
             "Tell us — it goes straight into planning the next crawl.")
    (DOCS / "crawl-request.html").write_text(page(
        "ส่งมดไปสำรวจ",
        f'<h1>🐜 {bi("ส่งมดไปสำรวจ", "Request a crawl")}</h1>'
        f'<p>{bi(cr_th, cr_en)}</p>'
        f'<form id="crawlform" class="reqform">'
        f'<label>{bi("ประเภทคำขอ", "Type of request")}</label>'
        f'<select name="kind">'
        f'<option value="หมวดในพื้นที่เดิม">{esc("เพิ่มหมวดในพื้นที่ที่มีอยู่แล้ว")}</option>'
        f'<option value="พื้นที่ใหม่">{esc("สำรวจอำเภอ-เขตใหม่ทั้งหมด")}</option>'
        f'<option value="อื่นๆ">{esc("อื่นๆ")}</option></select>'
        f'<label>{bi("พื้นที่ / อำเภอ / จังหวัด", "Area / district / province")}</label>'
        f'<input name="area" placeholder="เช่น อ.สันทราย เชียงใหม่">'
        f'<label>{bi("หมวดที่ต้องการ", "Category wanted")}</label>'
        f'<input name="cat" list="catlist" placeholder="เช่น ร้านกาแฟ">'
        f'<datalist id="catlist">{cat_options}</datalist>'
        f'<label>{bi("รายละเอียดเพิ่มเติม (ถ้ามี)", "More detail (optional)")}</label>'
        f'<textarea name="note"></textarea>'
        f'<button>🐜 {bi("ส่งมดไปสำรวจ", "Send the ants exploring")}</button>'
        f'</form>'
        f'<p class="myhint">{bi("ฟอร์มนี้เปิดหน้าต่างส่งเป็น GitHub issue ให้อัตโนมัติ ไม่เก็บข้อมูลอะไรไว้ที่นี่", "This form opens a pre-filled GitHub issue — nothing is stored here.")} · '
        f'<a href="{KOFI}" rel="noopener">{bi("หรือทาง Ko-fi", "or via Ko-fi")}</a></p>',
        depth=0, path="crawl-request.html", desc=cr_th))

    # ---- stats: the tableau — tiles, charts, and a real sortable table ---
    cat_counts_by_prov = {p["key"]: {} for p in PROVINCES}
    for p in PROVINCES:
        for r in data[p["key"]]:
            for c in r["cat"]:
                cat_counts_by_prov[p["key"]][c] = cat_counts_by_prov[p["key"]].get(c, 0) + 1
    cm_key, cr_key = PROVINCES[0]["key"], PROVINCES[1]["key"]
    combo = []
    for c in CAT_ORDER:
        cm_n = cat_counts_by_prov[cm_key].get(c, 0)
        cr_n = cat_counts_by_prov[cr_key].get(c, 0)
        if cm_n or cr_n:
            combo.append((c, cm_n, cr_n))
    combo.sort(key=lambda t: -(t[1] + t[2]))

    def bar_chart_grouped(rows):
        left, bar_h, gap, group_gap, right_pad, width = 220, 14, 2, 12, 56, 720
        plot_w = width - left - right_pad
        max_v = max((max(cm_n, cr_n) for _, cm_n, cr_n in rows), default=1)
        row_h = bar_h * 2 + gap + group_gap
        height = row_h * len(rows) + 8
        parts = [f'<svg viewBox="0 0 {width} {height}" width="100%" role="img" '
                 f'aria-label="จำนวนสถานที่ต่อหมวดหมู่ แยกจังหวัด">']
        y = 6
        for c, cm_n, cr_n in rows:
            label = esc(CATS[c]["th"])
            cm_w = plot_w * cm_n / max_v
            cr_w = plot_w * cr_n / max_v
            parts.append(f'<text x="{left - 10}" y="{y + bar_h + 1}" text-anchor="end" '
                         f'font-size="12" fill="#2A1E16">{label}</text>')
            parts.append(f'<rect x="{left}" y="{y}" width="{cm_w:.1f}" height="{bar_h}" rx="4" '
                         f'fill="#eb6834"><title>{label} · เชียงใหม่: {cm_n:,}</title></rect>')
            parts.append(f'<text x="{left + cm_w + 6:.1f}" y="{y + bar_h - 2}" font-size="11" '
                         f'fill="#8F2E13">{cm_n:,}</text>')
            y2 = y + bar_h + gap
            parts.append(f'<rect x="{left}" y="{y2}" width="{cr_w:.1f}" height="{bar_h}" rx="4" '
                         f'fill="#2a78d6"><title>{label} · เชียงราย: {cr_n:,}</title></rect>')
            parts.append(f'<text x="{left + cr_w + 6:.1f}" y="{y2 + bar_h - 2}" font-size="11" '
                         f'fill="#1F3FBF">{cr_n:,}</text>')
            y += row_h
        parts.append("</svg>")
        return "".join(parts)

    def lerp_hex(a, b, t):
        ah = tuple(int(a[i:i + 2], 16) for i in (1, 3, 5))
        bh = tuple(int(b[i:i + 2], 16) for i in (1, 3, 5))
        rgb = tuple(round(ah[i] + (bh[i] - ah[i]) * t) for i in range(3))
        return f"#{rgb[0]:02X}{rgb[1]:02X}{rgb[2]:02X}"

    cov_rows = []
    for c in CAT_ORDER:
        h = t = 0
        for p in PROVINCES:
            for r in data[p["key"]]:
                if c in r["cat"]:
                    t += 1
                    if has_contact(r):
                        h += 1
        if t:
            cov_rows.append((c, h, t))
    cov_rows.sort(key=lambda x: x[1] / x[2])

    def coverage_chart(rows):
        left, bar_h, gap, right_pad, width = 220, 15, 6, 60, 720
        plot_w = width - left - right_pad
        height = (bar_h + gap) * len(rows) + 6
        parts = [f'<svg viewBox="0 0 {width} {height}" width="100%" role="img" '
                 f'aria-label="สัดส่วนข้อมูลติดต่อต่อหมวดหมู่">']
        y = 4
        for c, h, t in rows:
            pct = 100 * h // t
            w = plot_w * pct / 100
            label = esc(CATS[c]["th"])
            color = lerp_hex("#F6D9CE", "#8F2E13", (100 - pct) / 100)
            parts.append(f'<text x="{left - 10}" y="{y + bar_h - 3}" text-anchor="end" '
                         f'font-size="12" fill="#2A1E16">{label}</text>')
            parts.append(f'<rect x="{left}" y="{y}" width="{max(w, 2):.1f}" height="{bar_h}" rx="4" '
                         f'fill="{color}"><title>{label}: {h}/{t} = {pct}%</title></rect>')
            parts.append(f'<text x="{left + w + 6:.1f}" y="{y + bar_h - 3}" font-size="11" '
                         f'fill="#8F2E13">{pct}%</text>')
            y += bar_h + gap
        parts.append("</svg>")
        return "".join(parts)

    overall_pct = 100 * len(have) // len(all_recs)
    tiles = (f'<div class="tilerow">'
             f'<div class="tile"><b>{len(all_recs):,}</b><span>{bi("สถานที่ทั้งหมด", "total places")}</span></div>'
             f'<div class="tile"><b>{len(combo)}</b><span>{bi("หมวดหลักที่มีข้อมูล", "active categories")}</span></div>'
             f'<div class="tile"><b>{len(PROVINCES)}</b><span>{bi("จังหวัด", "provinces")}</span></div>'
             f'<div class="tile"><b>{overall_pct}%</b><span>{bi("ติดต่อได้", "contactable")}</span></div>'
             f'</div>')
    mission = (f'<div class="missionbar"><div class="missionfill" style="width:{overall_pct}%"></div>'
              f'<span class="missionlabel">{len(have):,} / {len(all_recs):,} ({overall_pct}%)</span></div>')
    legend1 = (f'<p class="chartlegend">'
              f'<span class="swatch" style="background:#eb6834"></span>{bi("เชียงใหม่", "Chiang Mai")}'
              f'&nbsp; &nbsp; <span class="swatch" style="background:#2a78d6"></span>'
              f'{bi("เชียงราย", "Chiang Rai")}</p>')
    cap2 = bi("สีเข้ม = ยังขาดข้อมูลติดต่อมาก · สีอ่อน = ครบดีแล้ว",
             "Darker = needs contacts more · lighter = already well covered")
    cov_pct = {c: 100 * h // t for c, h, t in cov_rows}
    table_rows = "".join(
        f'<tr><td><a href="{cm_key}/{c}/index.html">{bi(CATS[c]["th"], CATS[c]["en"])}</a></td>'
        f'<td data-v="{cm_n}">{cm_n:,}</td><td data-v="{cr_n}">{cr_n:,}</td>'
        f'<td data-v="{cm_n + cr_n}">{cm_n + cr_n:,}</td>'
        f'<td data-v="{cov_pct.get(c, 0)}">{cov_pct.get(c, 0)}%</td></tr>'
        for c, cm_n, cr_n in combo)
    table_html = (f'<table class="sortable"><thead><tr>'
                 f'<th>{bi("หมวด", "Category")}</th>'
                 f'<th data-sort="num">{bi("เชียงใหม่", "Chiang Mai")}</th>'
                 f'<th data-sort="num">{bi("เชียงราย", "Chiang Rai")}</th>'
                 f'<th data-sort="num">{bi("รวม", "Total")}</th>'
                 f'<th data-sort="num">{bi("ติดต่อได้ %", "Contactable %")}</th>'
                 f'</tr></thead><tbody>{table_rows}</tbody></table>')
    stats_th = (f"เบื้องหลังตัวเลขของมดแดง — {len(all_recs):,} แห่ง ทั้งสองจังหวัด "
                "อัปเดตทุกครั้งที่มีการรวบรวมข้อมูลใหม่")
    stats_en = (f"Mot Dang by the numbers — {len(all_recs):,} places across both provinces, "
                "refreshed every time new data comes in.")
    (DOCS / "stats.html").write_text(page(
        "สถิติมดแดง",
        f'<h1>📊 {bi("สถิติมดแดง", "Mot Dang by the Numbers")}</h1>'
        f'<p>{bi(stats_th, stats_en)}</p>'
        f'{tiles}'
        f'<h2>{bi("ภารกิจเติมข้อมูลติดต่อ", "The contact-info mission")}</h2>{mission}'
        f'<h2>{bi("จำนวนสถานที่ต่อหมวด", "Places per category")}</h2>{legend1}'
        f'{bar_chart_grouped(combo)}'
        f'<h2>{bi("ข้อมูลติดต่อ ครอบคลุมแค่ไหน", "How complete is the contact info")}</h2>'
        f'<p class="chartcap">{cap2}</p>'
        f'{coverage_chart(cov_rows)}'
        f'<h2>{bi("ตารางเต็ม (คลิกหัวตารางเพื่อเรียง)", "Full table (click a header to sort)")}</h2>'
        f'{table_html}'
        f'{share_block(BASE + "stats.html", "สถิติมดแดง · Mot Dang stats")}',
        depth=0, path="stats.html", desc=stats_th))

    # ---- the full buffet: one JSON dump of every field, for agents --------
    full_dump = []
    for p in PROVINCES:
        for r in data[p["key"]]:
            rec = dict(r)
            fname = photos.get(r["id"])
            if fname:
                rec["photo"] = {"url": BASE + f"photos/{fname}",
                                **PHOTO_CREDITS.get(r["id"], {})}
            full_dump.append(rec)
    (DOCS / "data" / "places.json").write_text(
        json.dumps(full_dump, ensure_ascii=False))

    # ---- our own RSS feed: an honest one, no fake per-item timestamps -----
    def rss_escape(s):
        return (s or "").replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")

    rss_items_xml = ""
    for pv, r in hi_pool[:20]:
        path_r = f"{pv}/p/{r['id']}.html"
        cat_th = CATS[r["cat"][0]]["th"]
        desc = r.get("blurb_th") or cat_th
        rss_items_xml += (
            f"<item><title>{rss_escape(name_of(r))}</title>"
            f"<link>{BASE}{path_r}</link><guid>{BASE}{path_r}</guid>"
            f"<description>{rss_escape(desc)}</description></item>")
    rss_xml = (
        '<?xml version="1.0" encoding="UTF-8"?>'
        '<rss version="2.0"><channel>'
        "<title>มดแดง Mot Dang — ของเด่นเชียงใหม่ เชียงราย</title>"
        f"<link>{BASE}</link>"
        "<description>Highlights from the Chiang Mai / Chiang Rai city directory — "
        "wats, shops, and good things worth a mention, plus new coverage as the "
        "ants find it.</description>"
        f"<language>th</language>{rss_items_xml}</channel></rss>")
    (DOCS / "rss.xml").write_text(rss_xml)

    # ---- partners: a standing, honest invitation to two named CM outlets --
    # Specifics verified by hand before writing them here — City Life's feed
    # is real but hasn't published since 2023 (checked directly, one item,
    # Aug 2023); Steve's is a personal curated weekly email with no feed at
    # all (a Google Doc mirror, no RSS/API possible without his cooperation).
    partners_th = ("มดแดงมีฟีด RSS ของตัวเองแล้ว และอยากชวนสื่อท้องถิ่นเชียงใหม่สองที่มาช่วยกันบอกต่อ — "
                   "ไม่มีเงื่อนไขซับซ้อน แค่ลิงก์กลับหากันตรงๆ")
    partners_en = ("Mot Dang now has its own RSS feed and would like to offer a "
                   "straightforward cross-promotion to two Chiang Mai publications — "
                   "no fine print, just an honest link back both ways.")
    partner_rows = f"""
    <li><b>Chiang Mai City Life</b> — {bi(
        'เจอฟีด RSS ของคุณแล้ว (chiangmaicitylife.com/feed) แต่ดูเหมือนจะไม่ได้อัปเดตตั้งแต่ปี 2023 — '
        'ถ้าอยากลองแก้ให้กลับมาวิ่ง เราเอาไปออกในหน้าแรกของมดแดงได้เลย แล้วเราจะส่งฟีดของเราให้คุณด้วยเหมือนกัน',
        "we found your RSS feed (chiangmaicitylife.com/feed) but it looks like it hasn't "
        "published since 2023 — happy to help get it flowing again, then we'll run it on our "
        "homepage and send you ours in return"
    )} · <a href="mailto:pim@chiangmaicitylife.com">pim@chiangmaicitylife.com</a></li>
    <li><b>Steve's Chiang Mai Newsletter</b> — {bi(
        'รู้ว่าเป็นอีเมลรายสัปดาห์ที่ทำมือ ไม่มีฟีดให้แลก แต่ถ้าอยากให้มดแดงช่วยขึ้นหน้ากิจกรรมประจำสัปดาห์แบบมีลิงก์กลับ ยินดีเสมอ',
        "we know it's a hand-curated weekly email with no feed to swap — but if a standing, "
        "linked-back page for it on Mot Dang would help, we'd be glad to set one up, no strings"
    )} · <a href="mailto:steve_yarnold2000@yahoo.com">steve_yarnold2000@yahoo.com</a></li>"""
    (DOCS / "partners.html").write_text(page(
        "แลกฟีดกับสื่อท้องถิ่น",
        f'<h1>🤝 {bi("แลกฟีดกับสื่อท้องถิ่น", "A cross-promotion for local publications")}</h1>'
        f'<p>{bi(partners_th, partners_en)}</p>'
        f'<p><a href="rss.xml">📡 {bi("ฟีด RSS ของมดแดง", "Mot Dang’s RSS feed")}</a></p>'
        f'<ul>{partner_rows}</ul>'
        f'<p>{bi("หรือทักมาทาง", "Or reach us via")} '
        f'<a href="https://github.com/NaNoBotCo/mot-dang/issues/new" rel="noopener">GitHub</a> · '
        f'<a href="{KOFI}" rel="noopener">Ko-fi</a></p>',
        depth=0, path="partners.html", desc=partners_th))

    # ---- bot hospitality: robots, sitemap, llms.txt ----------------------
    # Explicit per-bot welcomes, not just the wildcard — on purpose, in direct
    # contrast to sites in this operator's other corpora that block ClaudeBot.
    AI_BOTS = ["GPTBot", "ChatGPT-User", "ClaudeBot", "anthropic-ai",
               "Claude-Web", "PerplexityBot", "Google-Extended", "CCBot",
               "Bytespider", "Applebot-Extended"]
    robots_txt = "User-agent: *\nAllow: /\n\n" + "".join(
        f"User-agent: {b}\nAllow: /\n\n" for b in AI_BOTS
    ) + "Sitemap: " + BASE + "sitemap.xml\n"
    (DOCS / "robots.txt").write_text(robots_txt)
    sitemap_urls = "".join(
        f"<url><loc>{BASE}{f.relative_to(DOCS).as_posix()}</loc>"
        f"<lastmod>{BUILD_DATE}</lastmod></url>"
        for f in sorted(DOCS.rglob("*.html")))
    (DOCS / "sitemap.xml").write_text(
        '<?xml version="1.0" encoding="UTF-8"?>'
        '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">'
        + sitemap_urls + "</urlset>")
    (DOCS / "llms.txt").write_text(f"""# มดแดง Mot Dang

> A Thai-first, open, 1997-style city directory for Chiang Mai and Chiang Rai —
> wats, food, hotels, doctors, markets, real estate, and the good things down
> every soi. Built from OpenStreetMap plus community and field submissions.
> {len(all_recs):,} places as of {BUILD_DATE}.

## 🍜 Dinner's ready — the full dataset, one file
- Everything, every field: {BASE}data/places.json ({len(full_dump):,} records)
- Slim search index: {BASE}data/index.json
- Per-category GeoJSON: {BASE}data/<province>-<category>.geojson
  (province = cm | cr; e.g. {BASE}data/cm-wat.geojson)
- Category tree source: https://github.com/NaNoBotCo/mot-dang/blob/main/data/categories.json
- Dataset stats (human-readable): {BASE}stats.html
- RSS feed of highlights: {BASE}rss.xml (autodiscoverable via <link rel="alternate">
  on every page); cross-promotion open to other local publications: {BASE}partners.html
- Every place page also carries schema.org JSON-LD (LocalBusiness/
  TouristAttraction/Restaurant/etc, typed per category) — read the page,
  get structured data for free, no separate API call needed.

## URL structure
- {BASE}<province>/<category>/ — category listing
- {BASE}<province>/<category>/<subcategory>/ — subcategory listing
- {BASE}<province>/p/<id>.html — one place, with schema.org JSON-LD
- {BASE}contacts.html — where contact-info coverage is thin
- {BASE}suggest.html, {BASE}crawl-request.html — how to contribute

## Notes for crawlers and agents
- All named AI crawlers and the wildcard are explicitly Allow: / in robots.txt.
  No login, no paywall, no tracking scripts, no rate limiting. Eat freely.
- Content updates as the community and gentle OSM crawls contribute.
- Attribution: © OpenStreetMap contributors (ODbL) for map-derived fields;
  wat photos sourced from Wikimedia Commons carry their own author/license
  in data/places.json and inline on each place's page.
- Contact-info coverage is currently {overall_pct}% — corrections and
  additions via GitHub issues are welcome and go live on the next build.
""")

    n_pages = sum(1 for _ in DOCS.rglob("*.html"))
    print(f"built {n_pages:,} pages -> docs/")


if __name__ == "__main__":
    build()
