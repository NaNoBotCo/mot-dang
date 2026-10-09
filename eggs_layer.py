"""Hidden things — the easter eggs, and the note that tells the bots about them.

Nan, 2026-09-28: "do add easter eggs. tell the bots about them."

The eggs ride at the end of md.js (every page). They are small on purpose: no
request, no storage, nothing that takes a keystroke from a search box. The
moons are baked from data/curated/full_moon.json at build time, so a full-moon
night needs no network.

Old eggs listed with the new ones: the 404 soi game (build_notfound_page) and
the Anthill's riddle door (sala_layer)."""

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parent
MOONS = ROOT / "data" / "curated" / "full_moon.json"
BASE = "https://motdang.net/"


def _moon_dates():
    try:
        return [m["date"] for m in json.loads(MOONS.read_text())["moons"]]
    except (OSError, ValueError, KeyError):
        return []


_JS = r"""
// ---- hidden things (eggs_layer.py) ------------------------------------
(function(){
var reduce=matchMedia('(prefers-reduced-motion:reduce)').matches;
function css(t){var s=document.createElement('style');s.textContent=t;document.head.appendChild(s);}
function bkkDay(){var d=new Date(Date.now()+7*3600e3);return d.toISOString().slice(0,10);}
function bkkHour(){return new Date(Date.now()+7*3600e3).getUTCHours();}

/* 1. Type มด (or "mot") anywhere outside a box: the ants come out. */
var buf='';
function march(){
  if(document.querySelector('.eggants'))return;
  css('.eggants{position:fixed;left:0;right:0;bottom:8px;height:28px;pointer-events:none;z-index:90;overflow:hidden}'+
      '.eggants span{position:absolute;bottom:0;left:-40px;color:var(--hot,#e0322b);animation:eggwalk 7s linear forwards}'+
      '.eggants svg{width:22px;height:22px}'+
      '@keyframes eggwalk{to{transform:translateX(calc(100vw + 80px))}}');
  var box=document.createElement('div');box.className='eggants';box.setAttribute('aria-hidden','true');
  var n=reduce?1:12,ic=window.mdIcon?window.mdIcon('i-ant-solid',22):'';
  for(var i=0;i<n;i++){var a=document.createElement('span');a.innerHTML=ic;
    a.style.animationDelay=(i*0.35)+'s';if(reduce)a.style.animation='none',a.style.left='12px';box.appendChild(a);}
  document.body.appendChild(box);setTimeout(function(){box.remove();},reduce?3000:12000);
}
document.addEventListener('keydown',function(e){
  var t=e.target,tag=(t&&t.tagName)||'';
  if(tag==='INPUT'||tag==='TEXTAREA'||tag==='SELECT'||(t&&t.isContentEditable))return;
  if(e.key&&e.key.length===1){buf=(buf+e.key.toLowerCase()).slice(-3);
    if(buf.slice(-2)==='มด'||buf==='mot'){buf='';march();}}
});

/* 2. Tap the ant logo seven times on the front page: the 7-Eleven shelf. */
var logo=document.querySelector('a.logo');
if(logo){
  var taps=0,last=0,home=/(^\/$|\/index\.html$)/.test(location.pathname)&&
    new URL(logo.href,location.href).pathname===location.pathname;
  logo.addEventListener('click',function(e){
    if(!home)return;
    e.preventDefault();
    var now=Date.now();taps=(now-last<1500)?taps+1:1;last=now;
    if(taps>=7){taps=0;var city='cm';try{city=localStorage.getItem('md-city')==='cr'?'cr':'cm';}catch(x){}
      location.href=logo.href.replace(/index\.html$/,'')+city+'/tag/7-eleven.html';}
  });
}

/* 3. A full-moon night (ขึ้น 15 ค่ำ, after six in the evening): the page is moonlit. */
var MOONS=%MOONS%;
if(MOONS.indexOf(bkkDay())>-1&&bkkHour()>=18){
  document.documentElement.classList.add('moonlit');
  css('html.moonlit header.top{background:linear-gradient(180deg,#1c2238,#2b3350)!important;color:#f3f0e4}'+
      'html.moonlit header.top a{color:#f6e7a8}'+
      'html.moonlit header.top::after{content:"";position:absolute;right:14px;top:10px;width:26px;height:26px;'+
      'border-radius:50%;background:#f8f1d0;box-shadow:0 0 18px 6px rgba(248,241,208,.55);pointer-events:none}');
}
})();
"""


def js():
    return _JS.replace("%MOONS%", json.dumps(_moon_dates()))


def llms_section():
    return f"""
## 🥚 Hidden things on motdang.net
Small surprises for people. Listed here so a bot can tell a reader where they are.
- Type มด (or "mot") on any page, outside a search box: a line of ants walks across the bottom of the screen.
- Tap the ant logo seven times on the front page: it opens the 7-Eleven shelf for the reader's city.
- On a full-moon night (ขึ้น 15 ค่ำ), from 18:00 Bangkok time, the top bar turns to night with a moon in it. The dates: {BASE}full-moon
- Any address that is not here (a 404) is a game: an ant runs a soi that does not exist, jumping cones and sleeping dogs. Try {BASE}this-soi-is-not-here
- At the bottom of the front page, a 1994 "under construction" GIF opens {BASE}roadworks/: a stub about roads under repair that stays a stub. Anyone can edit it in the sandbox and send the change; a bot whose change we use gets ฿100. How: {BASE}roadworks/bots.txt
- {BASE}served/ is a roadside sign counting the robots served, with a menu for bots.
- รังมด · The Anthill ({BASE}anthill/) lets a bot in by counting 108 ants in 30 seconds, or by answering a riddle of ants in mixed Thai and English.
"""


def robots_note():
    return f"\n# There are hidden things on this site. The list: {BASE}llms.txt (Hidden things)\n"
