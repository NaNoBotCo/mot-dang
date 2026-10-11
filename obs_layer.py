"""Readers as rain gauges and flood gauges.

Nan, 2026-09-28: "add an 'is it raining now' button to feed the weather
machine, a 'how deep is your flooding' question for emergencies".

  rain   one tap: none / light / heavy.

Nan, 2026-09-29: "I don't want these to actually be tiles. I only want them to show
up when user feedback is useful to motdang's learning ... being constantly visible is
not magical." So on the home page the rain and Doi Suthep questions are one line under
the top lines, asked only when the answer teaches us something, one at a time, and
gone once answered:
  rain    the forecast is unsure for the reader's city this hour (3–7 in 10);
          not again for 4 hours.
  suthep  the reader is known to be within 16 km of the mountain (it is behind her in
          San Kamphaeng), and the air is the kind a look west can grade: CM PM2.5 25
          or over, or burning season Jan–Apr; once a day. "Not from here" silences it
          for that reader for good.
  flood  one tap on a picture: dry / ankle / knee / waist / chest / roof.
         Always on /chuai.html; on the home page only while a river gauge in
         data/ping.json stands at or above its own alert level (the register's
         level_limit — the state's threshold, not ours).

Both post to the claims Worker (/rain, /flood). The point is the reader's own
when MDLOC gives one, otherwise the Worker uses the edge's city-grade guess and
marks it "edge". weather-north pulls GET /rain hourly into its archive.
The JS rides at the end of md.js."""

WORKER = "https://mot-dang-claims.nanobotco.workers.dev"

RAIN = (("none", "ไม่ตก", "No"), ("light", "ปรอย ๆ", "Light"), ("heavy", "หนัก", "Heavy"))

# Water line on a 40×64 figure, measured from the feet (y=60) up.
FLOOD = (("dry", "แห้ง", "Dry", 0), ("ankle", "ข้อเท้า", "Ankle", 6),
         ("knee", "เข่า", "Knee", 18), ("waist", "เอว", "Waist", 30),
         ("chest", "อก", "Chest", 42), ("roof", "หลังคา", "Over my head", 62))


def _figure(line):
    water = (f'<rect x="0" y="{60 - line}" width="40" height="{line + 4}" fill="#4a90c8" opacity=".7"/>'
             if line else "")
    return ('<svg viewBox="0 0 40 64" width="40" height="64" aria-hidden="true">'
            '<circle cx="20" cy="9" r="6" fill="currentColor"/>'
            '<path d="M20 15v24M20 39l-7 21M20 39l7 21M20 22l-10 10M20 22l10 10" '
            'stroke="currentColor" stroke-width="3.2" stroke-linecap="round" fill="none"/>'
            f'{water}</svg>')


CSS = """
[data-obs][hidden]{display:none!important}
.obsbtns{display:flex;gap:6px;flex-wrap:wrap;margin:6px 0 4px}
.obsbtns button{font:inherit;font-size:.82rem;line-height:1.25;padding:7px 10px;border-radius:10px;
  border:2px solid var(--ink,#17110c);background:var(--panel,#fff);color:var(--ink,#17110c);cursor:pointer;min-height:44px}
.obsbtns button[aria-pressed="true"]{background:var(--sky,#0a66c2);color:#fff;border-color:var(--sky,#0a66c2)}
.obsbtns button:disabled{opacity:.55}
.floodq{border:2px solid var(--ink,#17110c);border-radius:14px;padding:12px 14px;margin:14px 0;background:var(--panel,#fff)}
.floodq h2{margin:0 0 4px;font-size:1.1rem}
.floodq .obsbtns button{display:flex;flex-direction:column;align-items:center;gap:2px;padding:6px 8px;color:var(--ink,#17110c)}
.floodq .obsbtns button[aria-pressed="true"]{color:#fff}
.obsline{display:inline-flex;align-items:center;min-height:44px;padding:7px 12px;border-radius:10px;
  background:#06c755;color:#fff;font-weight:600;text-decoration:none}
.ask[hidden],.ask .q[hidden]{display:none}
.ask{margin:.5rem 0 0;padding:.7rem .9rem;border:2px dashed var(--day,#0a66c2);border-radius:14px;
  background:var(--panel,#fff);position:relative;animation:askin .5s ease-out}
.ask .q>b{display:flex;gap:.4rem;align-items:center;font-size:1rem}
.ask .x{position:absolute;top:4px;right:6px;border:0;background:none;font-size:1.2rem;
  color:var(--mute,#6a5a49);cursor:pointer;min-width:44px;min-height:44px}
.ask .never{font:inherit;font-size:.8rem;border:0;background:none;padding:0;color:var(--mute,#6a5a49);
  text-decoration:underline;cursor:pointer}
.ask.done{animation:askout .6s ease-in 3s forwards}
@keyframes askin{from{opacity:0;transform:translateY(-4px)}to{opacity:1;transform:none}}
@keyframes askout{to{opacity:0;height:0;padding:0;margin:0;border-width:0;overflow:hidden}}
@media (prefers-reduced-motion:reduce){.ask,.ask.done{animation:none}}
.obsmsg{display:block;font-size:.85rem;color:var(--mute,#6a5a49)}
"""


SUTHEP = (("clear", "ชัด", "Clear"), ("hazy", "มัว ๆ", "Hazy"), ("gone", "มองไม่เห็น", "Can't see it"))


def _btns(rows):
    return "".join(f'<button type="button" data-a="{k}">{th}<br>{en}</button>' for k, th, en in rows)


def ask_block(icon):
    """The home page's one question, hidden until the script decides it is worth asking."""
    return ('<div class="ask" id="ask" hidden>'
            '<button type="button" class="x" aria-label="ไม่ใช่ตอนนี้ · not now">×</button>'
            f'<div class="q" data-obs="rain" hidden><b>{icon("i-rain", 18)}'
            'ตรงที่คุณอยู่ ฝนตกไหม · Is it raining where you are?</b>'
            f'<span class="obsbtns">{_btns(RAIN)}</span>'
            '<span class="obsmsg" aria-live="polite">พยากรณ์ยังไม่แน่ใจ คำตอบคุณช่วยมดแดงได้ · '
            'the forecast isn\'t sure — your answer teaches Mot Dang</span></div>'
            f'<div class="q" data-obs="suthep" hidden><b>{icon("i-air", 18)}'
            'มองไปทางตะวันตก เห็นดอยสุเทพไหม · Look west — can you see Doi Suthep?</b>'
            f'<span class="obsbtns">{_btns(SUTHEP)}</span>'
            '<span class="obsmsg" aria-live="polite">ภูเขาบอกเรื่องควันได้ดีกว่าเครื่องวัด · '
            'the mountain reads the smoke better than a sensor</span>'
            '<button type="button" class="never">มองจากตรงนี้ไม่ได้อยู่แล้ว · I can\'t see it from here</button>'
            '</div></div>')


def flood_block(auto=False):
    btns = "".join(f'<button type="button" data-a="{k}">{_figure(line)}<span>{th}</span>'
                   f'<span>{en}</span></button>' for k, th, en, line in FLOOD)
    return (f'<section class="floodq" data-obs="flood"{" data-flood-auto hidden" if auto else ""}>'
            '<h2>น้ำท่วมตรงที่คุณอยู่ลึกแค่ไหน · How deep is the flooding where you are?</h2>'
            f'<div class="obsbtns">{btns}</div>'
            '<span class="obsmsg" aria-live="polite">แตะรูปที่ตรงที่สุด · tap the closest picture</span>'
            '<span class="obsmsg">ติดอยู่ ต้องการคนช่วย โทร <a href="tel:1784">1784</a> (ปภ.) · '
            '<a href="tel:1669">1669</a> · Trapped? Call 1784 or 1669</span>'
            + _line_row() + '</section>')


def _line_row():
    """Mark safe, ask for help, and flood warnings, through LINE (linedoor.py)."""  # stylecheck: allow — code docstring
    import linedoor
    if not linedoor.ON:
        return ""
    return ('<div class="obsbtns">'
            f'<a class="obsline" href="{linedoor.url(linedoor.SAFE)}" rel="noopener">ฉันปลอดภัย · I am safe</a>'
            f'<a class="obsline" href="{linedoor.url(linedoor.HELP)}" rel="noopener">ต้องการความช่วยเหลือ · I need help</a>'
            f'<a class="obsline" href="{linedoor.url(linedoor.HOME)}" rel="noopener">เตือนฉันเรื่องน้ำ · Warn me about water</a>'  # stylecheck: allow — a button label
            '</div><span class="obsmsg">ส่งผ่าน LINE ของมดแดง ครอบครัวได้ลิงก์ของคุณ · '
            'Sent through Mot Dang on LINE; your family gets your own link</span>')


_JS = r"""
// ---- rain + flood from readers (obs_layer.py) --------------------------
(function(){
var W='%WORKER%';
if(!document.querySelector('[data-obs]'))return;
var st=document.createElement('style');st.textContent=%CSS%;document.head.appendChild(st);
function send(box,kind,a,btn){
  var btns=box.querySelectorAll('button[data-a]'),msg=box.querySelector('.obsmsg');
  btns.forEach(function(b){b.disabled=true;b.setAttribute('aria-pressed',b===btn?'true':'false');});
  if(msg)msg.textContent='กำลังส่ง… · sending…';
  function post(pt){
    var body={answer:a};if(pt){body.lat=pt.lat;body.lng=pt.lng;}
    fetch(W+'/'+kind,{method:'POST',headers:{'content-type':'application/json'},body:JSON.stringify(body)})
      .then(function(r){return r.json();}).then(function(d){
        if(!d.ok)throw new Error(d.error||'');
        if(kind==='suthep')return fetch(W+'/suthep?hours=3').then(function(r){return r.json();}).then(function(x){
          var t={clear:0,hazy:0,gone:0};(x.reports||[]).forEach(function(r){if(t[r.answer]!=null)t[r.answer]++;});
          msg.textContent='ขอบคุณ · Thanks — ๓ ชม.นี้ · last 3 h: ชัด '+t.clear+' · มัว '+t.hazy+' · ไม่เห็น '+t.gone+
            ' (clear '+t.clear+', hazy '+t.hazy+', can\'t see '+t.gone+')';});
        if(kind==='rain')return fetch(W+'/rain?hours=1').then(function(r){return r.json();}).then(function(x){
          var n=(x.reports||[]).filter(function(r){return Math.abs(r.lat-d.lat)<0.06&&Math.abs(r.lng-d.lng)<0.06&&r.answer!=='none';}).length;
          msg.textContent='ขอบคุณ · Thanks'+(n?' — ชั่วโมงนี้ '+n+' คนแถวนี้บอกว่าฝนตก · '+n+' near you said rain this hour':'');});
        msg.textContent='ส่งแล้ว ขอบคุณ · Sent, thank you';})
      .then(function(){var ask=box.closest('.ask');if(ask){ask.classList.add('done');
        ask.addEventListener('animationend',function(e){if(e.animationName==='askout')ask.hidden=true;});}})
      .catch(function(e){btns.forEach(function(b){b.disabled=false;});
        msg.textContent='ส่งไม่ได้ ลองอีกครั้ง · could not send, try again';});
  }
  if(window.MDLOC)window.MDLOC.ask(function(pt){post(pt);},function(){post(null);});
  else if(navigator.geolocation)navigator.geolocation.getCurrentPosition(
    function(p){post({lat:p.coords.latitude,lng:p.coords.longitude});},function(){post(null);},
    {timeout:8000,maximumAge:600000});
  else post(null);
}
document.querySelectorAll('[data-obs]').forEach(function(box){
  var kind=box.getAttribute('data-obs');
  box.querySelectorAll('button[data-a]').forEach(function(b){
    b.addEventListener('click',function(){send(box,kind,b.getAttribute('data-a'),b);});});
});
/* The home page's question (Nan 2026-09-29): only when the answer teaches us something. */
function ls(k,v){try{if(v===undefined)return localStorage.getItem(k);localStorage.setItem(k,v);}catch(e){}return null;}
function ago(k){return (Date.now()-(+ls(k)||0))/36e5;}
var ask=document.getElementById('ask');
if(ask){
  var where=((document.querySelector('meta[name=md-where]')||{}).content||'').split('|');
  function suthepUseful(){
    if(ls('md-nosuthep')||ago('md-ask-suthep')<20)return false;
    if(ls('md-city')==='cr'||where.length<3||!+where[1])return false;
    var dy=(+where[1]-18.8048)*111,dx=(+where[2]-98.9217)*105;
    if(Math.sqrt(dx*dx+dy*dy)>16)return false;
    var pm=parseFloat(((document.querySelector('[data-air=cm] b')||{}).textContent)||'');
    var mo=new Date(Date.now()+7*36e5).getUTCMonth();
    return pm>=25||mo<=3;}
  function rainUseful(){var ch=window.MDRAINCH;
    return ch!=null&&ch>=0.3&&ch<=0.7&&ago('md-ask-rain')>=4;}
  var shown=null;
  window.MDASK=function(){
    if(shown)return;
    var k=rainUseful()?'rain':suthepUseful()?'suthep':null;if(!k)return;
    shown=k;ls('md-ask-'+k,String(Date.now()));
    ask.querySelector('.q[data-obs='+k+']').hidden=false;ask.hidden=false;};
  ask.querySelector('.x').addEventListener('click',function(){ask.hidden=true;});
  ask.querySelector('.never').addEventListener('click',function(){ls('md-nosuthep','1');ask.hidden=true;});
  window.MDASK();}
/* The home page shows the flood question while any river gauge is at or over its own alert level. */
var auto=document.querySelector('[data-flood-auto]');
if(auto){
  fetch('data/ping.json').then(function(r){return r.json();}).then(function(d){
    var hi=(d.stations||[]).some(function(s){return s.level!=null&&s.limit!=null&&s.level>=s.limit;});
    if(hi)auto.hidden=false;}).catch(function(){});}
})();
"""


def js():
    import json
    return _JS.replace("%WORKER%", WORKER).replace("%CSS%", json.dumps(CSS))
