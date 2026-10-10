"""alpha_layer.py — the tester's thumb, and only for as long as the alpha lasts.

Nan, 2026-09-09: *"a thumbs up/thumbs down input for my testers who do searches
and use maps, and maybe even an upload for screenshots and text box to describe
what went wrong (things always go wrong). I want this to go away completely for
beta, but we aren't there yet."*

"Goes away completely" is the requirement that shapes the whole module, so it
is built as ONE switch and ONE file:

  * `data/alpha.json` off, or missing, or its `until` date past → `head()`
    returns the empty string, `emit()` writes nothing, and `docs/alpha.js`
    does not exist. Not a hidden div, not a dead listener, not a byte of CSS
    in style.css. `tests/test_alpha.py` checks the artefact in BOTH
    directions, because "we turned it off" is a claim about 23,000 files.
  * Nothing else in the tree knows this exists apart from two lines in
    build.py. Beta is: delete this file, delete those two lines, delete
    data/alpha.json, delete the worker's /alpha route.

`until` is a self-limiting date, not a policy: the failure this repo has paid
for over and over is that temporary furniture stays. When the date passes the
widget stops rendering and the build says so out loud, which is a reminder
rather than a decision — she moves the date, or lets it lapse.

WHO SEES IT. `audience: "testers"` (the default) means the thumb is drawn only
for a browser that has been handed a tester name once, by an invite link with
`?tester=beer` on it. Everyone else gets a site with nothing extra on it: the
script exits before it touches the DOM. `audience: "everyone"` drops that
check for a day of open testing.

WHAT A REPORT CARRIES, and why it carries it. A thumb with no context is a
number nobody can act on — the site already has four invitations that
converted zero times, so this one is built to arrive complete or not at all:
the URL (which is where `?q=` lives), the search box's current text, what the
page actually had on it, the map's centre and zoom if a map is mounted, every
JS error and every failed fetch since load, the last dozen taps, the viewport,
the language mode, the connection type, and the build date the tester was
looking at. That is the difference between "search is bad" and "search for
กีตาร์ at 19:40 returned 200 rows, none of them a guitar shop, on the 9 Sept
build, with two 404s from the index".

A picture rides with it — the tester's own screenshot, up to three, up to 6 MB
each — because half the bug reports this site will get are about something
being in the wrong place on a screen the size of a hand.
"""

import datetime
import functools
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parent

# Where a report goes. The claims worker already exists, already has KV, R2
# and a verified mail destination, so the alpha rides it rather than standing
# up a service that has to be torn down again in a month.
DEFAULT_ENDPOINT = "https://mot-dang-claims.nanobotco.workers.dev/alpha"


def config():
    """The switch file, or {} when there is none."""
    return dict(_config())


# Read once per process: page() asked on every page (2026-10-10).
@functools.lru_cache(maxsize=None)
def _config():
    p = ROOT / "data" / "alpha.json"
    if not p.exists():
        return {}
    try:
        cfg = json.loads(p.read_text())
    except (ValueError, OSError):
        return {}
    return cfg if isinstance(cfg, dict) else {}


def state(today=None):
    """(on, why) — the reason is printed by the build, so a widget that is
    silently off and a widget that is deliberately off never look the same."""
    cfg = config()
    if not cfg:
        return False, "no data/alpha.json"
    if not cfg.get("on"):
        return False, "data/alpha.json says on:false"
    until = str(cfg.get("until") or "")
    today = today or datetime.date.today().isoformat()
    if until and today > until:
        return False, f"expired — data/alpha.json until:{until}, today {today}"
    return True, f"on until {until}" if until else "on, no end date"


def enabled():
    return state()[0]


def head(depth=0):
    return tag("../" * depth)


def tag(r):
    """The one line page() emits. `r` is the page's own root prefix, which is
    "/" on the 404 and "../"*depth everywhere else — the same value the rest
    of the furniture is hung on."""
    if not enabled():
        return ""
    return '<script src="%salpha.js" defer></script>' % r


_V = []


def _version():
    if not _V:
        import zlib
        cfg = config()
        seed = JS + json.dumps(
            {k: cfg.get(k) for k in ("audience", "endpoint", "until")},
            sort_keys=True)
        _V.append(f"{zlib.crc32(seed.encode('utf-8')) & 0xFFFFFFFF:08x}")
    return _V[0]


JS = r"""/* alpha.js — the tester's thumb. Nothing here is part of the site; it is
   scaffolding around it for the length of the alpha, and it is written only
   while data/alpha.json says on.

   Order matters twice over. In this file, the error and fetch capture go in
   before anything else, because the errors worth reporting are usually the
   ones that fired while the page was still loading. In page(), the tag is
   the FIRST script in the head, so this deferred file runs ahead of live.js
   and md.js and is watching before they do anything. What it still cannot
   see is an inline script that throws during parse — catching those needs a
   synchronous hook in the head on all 23,000 pages, and that is bytes on
   every reader's page for four testers' benefit. */
(function(){
var C=window.MDALPHA_CFG||{};
var MAXNOTE=4000, MAXSHOTS=3, MAXBYTES=6*1024*1024, MAXTRAIL=12, MAXERRS=6;
var T0=Date.now();

function ls(k,v){try{if(v===undefined)return localStorage.getItem(k);
localStorage.setItem(k,v);return v;}catch(e){return null;}}
function since(){return Date.now()-T0;}
function push(a,v){a.push(v);if(a.length>MAXERRS*2)a.shift();}
function cut(s,n){s=String(s==null?'':s);return s.length>n?s.slice(0,n)+'…':s;}

/* ---- who is this ------------------------------------------------------
   A name arrives once, on the invite link, and is kept on the device. It is
   taken out of the address bar straight away so a tester who shares a URL
   from their browser does not hand their name to whoever they send it to. */
var who=ls('md-alpha-who')||'';
try{
  var u=new URL(location.href), t=u.searchParams.get('tester');
  if(t){who=cut(t,40);ls('md-alpha-who',who);
    u.searchParams.delete('tester');
    history.replaceState(null,'',u.pathname+(u.search||'')+(u.hash||''));}
}catch(e){}
var active=!!who||C.audience==='everyone';
if(!who)who='';

/* ---- what went wrong, captured whether or not anybody taps ------------- */
var errs=[],nets=[],trail=[];
if(active){
  addEventListener('error',function(e){
    if(e&&e.target&&e.target!==window&&e.target.tagName){
      push(errs,{m:'failed to load',f:cut(e.target.src||e.target.href||e.target.tagName,160),at:since()});
      return;}
    push(errs,{m:cut(e&&e.message,200),
      f:cut((e&&e.filename)||'',160)+':'+((e&&e.lineno)||0)+':'+((e&&e.colno)||0),at:since()});
  },true);
  addEventListener('unhandledrejection',function(e){
    var r=e&&e.reason;
    push(errs,{m:'promise: '+cut((r&&r.message)||r,200),at:since()});
  });
  /* A fetch that comes back 404 or never comes back at all is invisible to
     the reader and is exactly what a "the map is empty" report is made of. */
  var F=window.fetch;
  if(F)window.fetch=function(){
    var a=arguments,t=Date.now();
    var u=String((a[0]&&a[0].url)||a[0]||'');
    if(C.endpoint&&u.indexOf(C.endpoint)===0)return F.apply(this,a);
    return F.apply(this,a).then(function(r){
      if(!r.ok)push(nets,{u:cut(u,180),s:r.status,ms:Date.now()-t});
      return r;},function(err){
      push(nets,{u:cut(u,180),s:'failed',e:cut(err&&err.message,120),ms:Date.now()-t});
      throw err;});};
}
if(!active)return;

/* ---- the last dozen taps ---------------------------------------------- */
addEventListener('click',function(e){
  var el=e.target&&e.target.closest?e.target.closest('a,button,[role=button],summary,input,select'):null;
  if(!el)return;
  var d='';for(var i=0;i<el.attributes.length;i++){var at=el.attributes[i];
    if(at.name.indexOf('data-')===0&&at.value)d+=' '+at.name+'='+cut(at.value,24);}
  trail.push({t:el.tagName.toLowerCase(),
    x:cut((el.textContent||el.value||el.getAttribute('aria-label')||'').trim(),40),
    h:cut(el.getAttribute('href')||'',100),d:d.trim(),at:since()});
  if(trail.length>MAXTRAIL)trail.shift();
},true);
addEventListener('submit',function(e){
  var f=e.target,q=f&&f.querySelector&&f.querySelector('input[name=q],input[type=search]');
  trail.push({t:'submit',x:cut(q?q.value:'',60),h:cut((f&&f.getAttribute('action'))||'',100),at:since()});
  if(trail.length>MAXTRAIL)trail.shift();
},true);

/* ---- what was on the screen at the moment of the thumb ----------------- */
function ctx(){
  var o={url:location.href,ref:cut(document.referrer,200),
    title:cut(document.title,120),
    h1:cut((document.querySelector('h1')||{}).textContent||'',120),
    lang:(document.documentElement.className.match(/lang-\w+/)||[''])[0],
    view:innerWidth+'x'+innerHeight+'@'+(devicePixelRatio||1),
    ua:cut(navigator.userAgent,220),
    sw:!!(navigator.serviceWorker&&navigator.serviceWorker.controller),
    ms:since()};
  try{var c=navigator.connection;if(c)o.net=(c.effectiveType||'')+(c.saveData?' save-data':'');}catch(e){}
  var q=document.querySelector('input[type=search],input[name=q]');
  if(q&&q.value)o.q=cut(q.value,120);
  /* What the page actually had on it. A count is the whole argument in a
     "search found nothing" report, and a zero is as much of an answer as a
     thousand. */
  var counts={};
  [['rows','[data-facets]'],['shown','[data-facets]:not(.fhide)'],
   ['cards','.card'],['results','#results li,[data-results] li'],
   ['maps','[data-mdmap="1"]']].forEach(function(p){
    try{counts[p[0]]=document.querySelectorAll(p[1]).length;}catch(e){}});
  o.counts=counts;
  /* Where the map was pointing. Asked of the map object rather than read off
     the drawing, because the reader may have panned away from both. */
  var maps=[];
  try{
    document.querySelectorAll('[data-mdmap="1"]').forEach(function(el){
      var m=window.MDMAP&&window.MDMAP.map&&window.MDMAP.map(el);
      if(m&&m.getCenter){var c=m.getCenter();
        maps.push({lat:+c.lat.toFixed(5),lng:+c.lng.toFixed(5),
          z:+m.getZoom().toFixed(2),live:true});}
      else maps.push({live:false,drawn:!!el.querySelector('svg')});});
  }catch(e){}
  if(maps.length)o.map=maps.slice(0,3);
  if(errs.length)o.errs=errs.slice(-MAXERRS);
  if(nets.length)o.nets=nets.slice(-MAXERRS);
  if(trail.length)o.trail=trail.slice(-MAXTRAIL);
  return o;
}

/* ---- the thumb --------------------------------------------------------
   Bottom LEFT, deliberately: MapLibre puts the OSM attribution at the bottom
   right of every map box on this site and that is a licence condition, not
   decoration. Nothing of ours covers it. */
var CSS='.mdal{position:fixed;left:.6rem;bottom:.6rem;z-index:61;display:flex;gap:.35rem;'
+'font:16px/1.4 system-ui,-apple-system,sans-serif}'
+'.mdal.up{bottom:3.4rem}'
+'.mdal button{width:52px;height:52px;border:2px solid var(--ink,#2a1e16);border-radius:14px;'
+'background:var(--card,#fffdf7);color:var(--ink,#2a1e16);display:grid;place-items:center;'
+'cursor:pointer;box-shadow:0 2px 0 var(--ink,#2a1e16);padding:0}'
+'.mdal button:focus-visible{outline:3px solid var(--ant,#c13a2e);outline-offset:2px}'
+'.mdal button svg{width:26px;height:26px;fill:currentColor}'
+'.mdal .no{color:var(--ant,#c13a2e)}'
+'.mdal-say{position:fixed;left:.6rem;bottom:4.2rem;z-index:61;max-width:18rem;'
+'background:var(--ink,#2a1e16);color:var(--paper,#faf5ea);padding:.5rem .7rem;'
+'border-radius:10px;font:16px/1.4 system-ui,sans-serif}'
+'.mdal-sheet{position:fixed;inset:0;z-index:62;background:rgba(0,0,0,.45);'
+'display:flex;align-items:flex-end;justify-content:center}'
+'.mdal-box{background:var(--paper,#faf5ea);color:var(--ink,#2a1e16);width:100%;'
+'max-width:34rem;max-height:92vh;overflow:auto;border-radius:16px 16px 0 0;'
+'padding:1rem 1rem 1.2rem;font:17px/1.5 system-ui,-apple-system,sans-serif;'
+'border-top:4px double var(--ant,#c13a2e)}'
+'.mdal-box h2{margin:.1rem 0 .5rem;font-size:1.15rem}'
+'.mdal-box p{margin:.3rem 0;color:var(--ink-soft,#544636);font-size:.95rem}'
+'.mdal-box textarea{width:100%;min-height:7rem;font:17px/1.45 system-ui,sans-serif;'
+'padding:.6rem;border:2px solid var(--ink,#2a1e16);border-radius:10px;'
+'background:var(--card,#fffdf7);color:inherit;box-sizing:border-box}'
+'.mdal-box input[type=file]{display:block;margin:.6rem 0;font-size:.95rem;width:100%}'
+'.mdal-row{display:flex;gap:.5rem;margin-top:.7rem;flex-wrap:wrap}'
+'.mdal-row button{flex:1 1 8rem;min-height:48px;font:600 17px system-ui,sans-serif;'
+'border:2px solid var(--ink,#2a1e16);border-radius:10px;cursor:pointer;'
+'background:var(--card,#fffdf7);color:var(--ink,#2a1e16)}'
+'.mdal-row .go{background:var(--ant,#c13a2e);color:#fff;border-color:var(--ant-dark,#8f2a21)}'
+'.mdal-ctx{font-size:.85rem;color:var(--gloss,#685845);word-break:break-word;margin-top:.6rem}'
+'@media (prefers-reduced-motion:no-preference){.mdal-box{animation:mdalup .18s ease-out}'
+'@keyframes mdalup{from{transform:translateY(14px)}}}';
var st=document.createElement('style');st.textContent=CSS;

var UP='<svg viewBox="0 0 24 24" aria-hidden="true"><path d="M2 20h3V9H2v11zm19-9.5c0-.83-.67-1.5-1.5-1.5h-5.1l.8-3.8.02-.26c0-.3-.13-.6-.34-.8L13.9 3l-5.5 5.5c-.27.27-.44.65-.44 1.06V18c0 .83.67 1.5 1.5 1.5h7.2c.62 0 1.15-.37 1.38-.9l2.42-5.66c.07-.18.11-.37.11-.57v-1.87z"/></svg>';
var DOWN='<svg viewBox="0 0 24 24" aria-hidden="true"><path d="M22 4h-3v11h3V4zM3 13.5c0 .83.67 1.5 1.5 1.5h5.1l-.8 3.8-.02.26c0 .3.13.6.34.8L10.1 21l5.5-5.5c.27-.27.44-.65.44-1.06V6c0-.83-.67-1.5-1.5-1.5H7.34c-.62 0-1.15.37-1.38.9L3.54 11.06c-.07.18-.11.37-.11.57v1.87z"/></svg>';

function el(tag,cls,html){var n=document.createElement(tag);
if(cls)n.className=cls;if(html!=null)n.innerHTML=html;return n;}

function say(text,ms){
  var n=el('div','mdal-say');n.setAttribute('role','status');n.textContent=text;
  document.body.appendChild(n);
  setTimeout(function(){n.remove();},ms||4000);
}

/* ---- sending ----------------------------------------------------------
   One request carries the verdict, the note, the context and the pictures,
   so there is no half-arrived report and no second call to fail on its own.
   A send that does not land is kept on the device and goes with the next
   page the tester opens — the tester is told which of the two happened. */
function queued(){try{return JSON.parse(ls('md-alpha-q')||'[]');}catch(e){return [];}}
function queue(rec){var q=queued();q.push(rec);ls('md-alpha-q',JSON.stringify(q.slice(-20)));}

function post(rec,files){
  var fd=new FormData();
  fd.append('report',JSON.stringify(rec));
  (files||[]).forEach(function(f,i){fd.append('shot'+i,f,f.name||('shot'+i));});
  return fetch(C.endpoint,{method:'POST',body:fd}).then(function(r){
    if(!r.ok)throw new Error('http '+r.status);return r.json();});
}

function report(verdict,note,files){
  var rec={v:verdict,who:who,note:cut(note||'',MAXNOTE),
    at:new Date().toISOString(),build:C.build||'',ctx:ctx()};
  var n=(files||[]).length;
  return post(rec,files).then(function(){
    say(n?'ส่งแล้ว พร้อมรูป · sent, with the picture':'ส่งแล้ว ขอบคุณ · sent, thank you');
    flush();
  },function(){
    queue(rec);
    say(n?'เก็บไว้ในเครื่อง จะส่งใหม่หน้าถัดไป (รูปต้องแนบใหม่) · held on this device — it goes with the next page you open, the picture needs attaching again'
        :'เก็บไว้ในเครื่อง จะส่งใหม่หน้าถัดไป · held on this device — it goes with the next page you open',7000);
  });
}

function flush(){
  var q=queued();if(!q.length)return;
  ls('md-alpha-q','[]');
  q.forEach(function(rec){post(rec,[]).catch(function(){queue(rec);});});
}

/* ---- the sheet -------------------------------------------------------- */
function sheet(verdict){
  var wrap=el('div','mdal-sheet');
  var box=el('div','mdal-box');
  box.setAttribute('role','dialog');
  box.setAttribute('aria-modal','true');
  box.setAttribute('aria-label','รายงานรุ่นทดสอบ Alpha report');
  var c=ctx();
  box.appendChild(el('h2',null,verdict==='up'
    ? 'ดี · That worked'
    : 'มีอะไรผิด · Something went wrong'));
  box.appendChild(el('p',null,'บอกว่าเกิดอะไรขึ้น · Say what happened. '
    +'แนบภาพหน้าจอได้ · A screenshot helps.'));
  var ta=document.createElement('textarea');
  ta.setAttribute('aria-label','สิ่งที่เกิดขึ้น What happened');
  ta.placeholder=verdict==='up'?'อะไรที่ใช้ได้ · what worked':'ค้นหาอะไร แล้วได้อะไร · what you searched for, and what came back';
  box.appendChild(ta);
  var fi=document.createElement('input');
  fi.type='file';fi.accept='image/*';fi.multiple=true;
  fi.setAttribute('aria-label','ภาพหน้าจอ Screenshot');
  box.appendChild(fi);
  var ctxLine=el('div','mdal-ctx');
  ctxLine.textContent='ส่งไปด้วย · sent with it: '+c.url
    +(c.q?' · '+c.q:'')
    +' · '+c.view
    +(c.errs?' · '+c.errs.length+' error'+(c.errs.length>1?'s':''):'')
    +(c.map?(c.map[0].live?' · map z'+c.map[0].z:' · map with no tiles'):'');
  box.appendChild(ctxLine);
  var row=el('div','mdal-row');
  var go=el('button','go');go.type='button';go.textContent='ส่ง · Send';
  var no=el('button');no.type='button';no.textContent='ปิด · Close';
  row.appendChild(go);row.appendChild(no);
  box.appendChild(row);
  wrap.appendChild(box);
  function close(){wrap.remove();document.removeEventListener('keydown',esc);}
  function esc(e){if(e.key==='Escape')close();}
  document.addEventListener('keydown',esc);
  wrap.addEventListener('click',function(e){if(e.target===wrap)close();});
  no.addEventListener('click',close);
  go.addEventListener('click',function(){
    var files=[].slice.call(fi.files||[]).slice(0,MAXSHOTS)
      .filter(function(f){return f.size<=MAXBYTES;});
    var over=[].slice.call(fi.files||[]).length-files.length;
    go.disabled=true;go.textContent='กำลังส่ง · sending…';
    report(verdict,ta.value,files).then(function(){
      close();
      if(over)say('รูป '+over+' ไฟล์ใหญ่เกิน 6 MB ไม่ได้ส่ง · '+over+' picture(s) over 6 MB were not sent',6000);
    });
  });
  document.body.appendChild(wrap);
  ta.focus();
}

function mount(){
  document.head.appendChild(st);
  var bar=el('div','mdal');
  bar.setAttribute('aria-label','รุ่นทดสอบ Alpha feedback');
  /* A map box puts MapLibre's scale bar in this exact corner. The attribution
     opposite it is the licence condition and is never covered; the scale bar
     is not, but there is no reason to sit on it either. */
  if(document.querySelector('[data-mdmap="1"]'))bar.className='mdal up';
  var up=el('button','yes',UP);
  up.type='button';up.title='ใช้ได้ · this worked';
  up.setAttribute('aria-label','ใช้ได้ · this worked');
  var down=el('button','no',DOWN);
  down.type='button';down.title='มีอะไรผิด · something is wrong';
  down.setAttribute('aria-label','มีอะไรผิด · something is wrong');
  /* A thumb up is one tap and it is gone; a thumb down opens the box,
     because a thumb down with nothing written on it is the one report
     nobody can act on. */
  up.addEventListener('click',function(){report('up','',[]);});
  down.addEventListener('click',function(){sheet('down');});
  bar.appendChild(up);bar.appendChild(down);
  document.body.appendChild(bar);
  flush();
}

if(document.readyState==='loading')addEventListener('DOMContentLoaded',mount);
else mount();
})();
"""


def emit(g):
    """Write docs/alpha.js, or nothing at all."""
    docs = g["DOCS"]
    on, why = state(g.get("BUILD_DATE"))
    if not on:
        return {"on": False, "why": why}
    cfg = config()
    runtime = {"endpoint": cfg.get("endpoint") or DEFAULT_ENDPOINT,
               "audience": cfg.get("audience") or "testers",
               "build": g.get("BUILD_DATE", "")}
    (docs / "alpha.js").write_text(
        "window.MDALPHA_CFG=" + json.dumps(runtime, ensure_ascii=False,
                                           separators=(",", ":")) + ";\n" + JS)
    return {"on": True, "why": why, "audience": runtime["audience"],
            "endpoint": runtime["endpoint"]}
