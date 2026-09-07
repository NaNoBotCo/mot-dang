#!/usr/bin/env python3
"""tapcard.py — one card for every map on this site.

WHY THIS EXISTS
---------------
Nan, 2026-09-07: *"If you click a point on a motdang map, it should allow you
to explore information about what you clicked."*

It could not. Measured that evening: of 25,889 pages carrying a map, a tap
answered on place pages (the five neighbour dots and nothing else), 95 shelf
maps, /map.html (only the shelves switched on, and it opens with one),
/here.html, the results map and /toilets. It answered nothing on 534 soi maps,
9 event maps, the merit round, /doi.html, /plan.html or the homepage postcard.
When it did answer it said name · shelf · 🐜 · distance — and the record it was
reading held tags (7,856 records), a street (6,980), opening hours (4,359) and
a district (3,852) that the card never showed. Meanwhile a tap on a RESULT ROW
opened a panel with a map, the three nearest and events. Two cards for one
object, and the one that explored could not be reached from a map.

So this module owns the card, and md.js's MDCARD becomes the fallback for the
moment tap.js has not arrived. Nothing here builds a map: map_shell stays the
one constructor, and every surface reaches this through MDTAP.show().

NAN'S CALLS, 2026-09-07 — and what each one is in the code
----------------------------------------------------------
SHAPE — mine to decide, on disability, on a reader who does not know the site,
and on a phone with no signal. A sheet at the bottom on a phone, a panel docked
bottom-right on a wide screen, and NEVER a centred modal:
  * a modal covers the thing you just pointed at, and comparing two dots is the
    whole gesture;
  * nothing here traps focus or dims the page — the map stays live under the
    card, so a reader who opened it by accident is not stuck (WCAG 2.1.2);
  * it grows with the reader's own type size and scrolls inside itself, so it
    still works at 200% text on a 320 px screen (1.4.4, 1.4.10) — which is why
    every size below is in rem and the height is a max, not a height;
  * every target is 44 px (2.5.5), and the close button is a real button;
  * it costs one fetch of a table this site already ships, and nothing at all
    on a page whose reader never touches a map.

BARE GROUND — silence. A tap that hits nothing opens nothing.

THINGS NOT HELD — silence. A named building in the tiles that is not one
of our records is not tappable and says nothing about itself.

TAGS — the chips filter the map. Where a surface can filter itself it passes a
filter function and the chip narrows what is drawn; where it cannot (a place
map has five dots), the chip goes to the same filter on the results map, which
can. A tag nobody has answers zero, and the card says zero rather than quietly
showing everything.

WALKING THE CARD — the three nearest move the card in place, and history moves
with it: every card is a pushState, so the phone's own Back button walks the
trail backwards and the first Back closes the card. That is the closest thing
to an ADA convention for changing content in place — the change is on request,
it is announced, and it is reversible with the control the reader already knows
(WCAG 3.2.5, 2.4.3, and Android's back-button expectation).

ALL SURFACES — this ships in <head> on every page that mounts a map, decided by
page() looking for data-mdmap in the finished body, so a map built next year
gets the card without anyone remembering to ask for it.
"""

import zlib


def version():
    """Content hash for the ?v= on tap.css/tap.js.

    Same reasoning as map_shell.version(): these are served under names that
    never change with a week-long cache, and a phone holding yesterday's copy
    against today's page is exactly how the August walk found a dead map.
    """
    return "%08x" % (zlib.crc32((CSS + JS).encode("utf-8")) & 0xFFFFFFFF)


def head(depth=0):
    """The two tags, for page() to put in front of md.js."""
    r = "../" * depth
    v = version()
    return (f'<link rel="stylesheet" href="{r}tap.css?v={v}">'
            f'<script src="{r}tap.js?v={v}" defer></script>')


def emit(g):
    docs = g["DOCS"]
    (docs / "tap.css").write_text(CSS)
    (docs / "tap.js").write_text(JS)
    return {"css": len(CSS), "js": len(JS), "v": version()}


# --------------------------------------------------------------------- CSS
# Every colour is one of the site's own tokens, so the card is the same paper
# as the page under it and a retune of the palette carries it along. The one
# literal is the shadow, which is a shadow of the ink.
CSS = """/* tap.css — the card a touch on any map opens. */
.mdtap{position:fixed;z-index:60;left:0;right:0;bottom:0;
  background:var(--card);color:var(--ink);
  border-top:3px double var(--ant);
  box-shadow:0 -.4rem 1.6rem rgba(42,30,22,.18);
  max-height:58vh;overflow-y:auto;overscroll-behavior:contain;
  padding:.85rem 1rem 1.1rem;font-size:1rem;line-height:1.45}
.mdtap[hidden]{display:none}
/* A wide screen has room beside the map, so the card stops covering it. Docked
   bottom-right rather than centred for the same reason the sheet sits low: the
   thing the reader pointed at is usually above their finger, not under it. */
@media (min-width:900px){
  .mdtap{left:auto;right:1rem;bottom:1rem;width:23rem;
    border:2px solid var(--warm-border);border-top:3px double var(--ant);
    border-radius:.7rem;max-height:min(70vh,34rem);
    box-shadow:0 .5rem 1.8rem rgba(42,30,22,.22)}
}
.mdtap-head{display:flex;gap:.5rem;align-items:flex-start}
.mdtap-back,.mdtap-x{flex:none;min-width:44px;min-height:44px;border:0;
  background:none;font:inherit;font-size:1.4rem;line-height:1;cursor:pointer;
  color:var(--ink-soft);border-radius:.4rem}
.mdtap-back:hover,.mdtap-x:hover{background:var(--row-hover);color:var(--ink)}
.mdtap-x{margin-left:auto}
.mdtap-name{font-size:1.18rem;font-weight:800;margin:.15rem 0 0;
  overflow-wrap:anywhere}
.mdtap-name:focus{outline:3px solid var(--ant);outline-offset:2px}
.mdtap-en{color:var(--ink-soft);font-size:.95rem;margin:.1rem 0 0;
  overflow-wrap:anywhere}
.mdtap-rom{color:var(--gloss);font-size:.85rem;margin:.05rem 0 0;font-style:italic}
.mdtap-facts{display:flex;flex-wrap:wrap;gap:.35rem;margin:.55rem 0 0}
.mdtap-fact{display:inline-flex;align-items:center;gap:.3rem;font-size:.85rem;
  border:1.5px solid var(--warm-border);border-radius:999px;
  padding:.2rem .6rem;background:var(--card-alt);color:var(--ink)}
/* A tag is a control, so it is a fingertip tall and says so by being a button
   or a link. A fact is not a control and never pretends to be one. */
.mdtap-tag{display:inline-flex;align-items:center;gap:.35rem;min-height:44px;
  padding:.3rem .8rem;border-radius:999px;border:1.5px solid var(--warm-border);
  background:#fff;color:var(--ink);font:inherit;font-size:.9rem;cursor:pointer;
  text-decoration:none}
.mdtap-tag:hover{border-color:var(--ant);background:var(--row-hover)}
.mdtap-tag[aria-pressed="true"]{background:var(--ink);color:var(--card);
  border-color:var(--ink);font-weight:700}
.mdtap-lamp{display:inline-flex;align-items:center;gap:.4rem;font-size:.92rem;
  margin:.5rem 0 0}
.mdtap-lamp b{width:.65rem;height:.65rem;border-radius:50%;display:inline-block;
  flex:none}
.mdtap-open b{background:#1f6b57}
.mdtap-shut b{background:var(--dashed)}
.mdtap-filt{display:flex;flex-wrap:wrap;gap:.4rem;align-items:center;
  margin:.5rem 0 0;font-size:.85rem;color:var(--ink-soft)}
.mdtap-filt a,.mdtap-filt button{font:inherit;font-size:.85rem;
  min-height:44px;display:inline-flex;align-items:center;padding:0 .5rem;
  border:0;background:none;color:var(--ant-dark);cursor:pointer;
  text-decoration:underline}
.mdtap-near{margin:.7rem 0 0;border-top:1.5px solid var(--warm-border);
  padding-top:.5rem}
.mdtap-near h3{font-size:.8rem;font-weight:700;letter-spacing:.03em;
  color:var(--ink-soft);margin:0 0 .2rem}
.mdtap-near ul{list-style:none;margin:0;padding:0}
.mdtap-near button{display:flex;width:100%;gap:.6rem;align-items:baseline;
  text-align:left;min-height:44px;border:0;background:none;font:inherit;
  padding:.35rem .3rem;border-radius:.4rem;cursor:pointer;color:var(--ink)}
.mdtap-near button:hover{background:var(--row-hover)}
.mdtap-near .far{margin-left:auto;color:var(--gloss);font-size:.85rem;
  white-space:nowrap}
.mdtap-do{display:flex;flex-wrap:wrap;gap:.45rem;margin:.75rem 0 0}
.mdtap-do a,.mdtap-do button{display:inline-flex;align-items:center;
  min-height:44px;padding:.35rem .9rem;border-radius:999px;font:inherit;
  font-size:.92rem;border:2px solid var(--warm-border);background:#fff;
  color:var(--ink);cursor:pointer;text-decoration:none}
.mdtap-do .mdtap-go{background:var(--ant);border-color:var(--ant);color:#fff;
  font-weight:700}
.mdtap-do .mdtap-go:hover{background:var(--ant-dark);border-color:var(--ant-dark)}
.mdtap-do .on{background:var(--card-alt);border-color:var(--ink)}
.mdtap :focus-visible{outline:3px solid var(--ant);outline-offset:2px}
/* The dot that was touched, marked on whatever kind of map it was. */
.mdtap-lit{outline:3px solid var(--ant-dark);outline-offset:2px;border-radius:50%}
@media (prefers-reduced-motion:no-preference){
  .mdtap{animation:mdtap-in .14s ease-out}
  @keyframes mdtap-in{from{transform:translateY(.6rem);opacity:.4}
    to{transform:none;opacity:1}}
}
@media print{.mdtap{display:none}}
"""


# ---------------------------------------------------------------------- JS
# ES5 on purpose. Two thirds of this site's readers are on Android phones that
# skew mid and budget, and the card is the one script that runs on a page whose
# reader has already waited for a megabyte of MapLibre.
JS = r"""/* tap.js — what a touch on any map is worth.
   Built 2026-09-07. See tapcard.py for why each rule is the rule. */
(function(){
if(!document.addEventListener)return;

var ROOT=function(){return document.documentElement.getAttribute('data-root')||'';};
var TAB=null,tabTried=false,tabWaiting=[];

/* The words behind the numbers. The index carries a tag, a street, a district
   and an opening schedule as INTS into one table this site already ships for
   search; the card fetches it once, on the first touch that needs it, and
   never on a page whose reader only reads. Until it lands the card renders
   without those lines rather than waiting — the name was the question. */
function tables(then){
  if(TAB){then(TAB);return;}
  tabWaiting.push(then);
  if(tabTried)return;
  tabTried=true;
  try{
    var x=new XMLHttpRequest();
    x.open('GET',ROOT()+'data/search_tables.json',true);
    x.onload=function(){
      if(x.status>=200&&x.status<300){
        try{TAB=JSON.parse(x.responseText);}catch(e){TAB=null;}
      }
      var w=tabWaiting;tabWaiting=[];
      for(var i=0;i<w.length;i++)if(TAB)w[i](TAB);
    };
    x.onerror=function(){tabWaiting=[];};
    x.send();
  }catch(e){}
}

/* ---- the sentences this site says about distance ---------------------- */
var R2D=Math.PI/180;
function metres(a,b,c,d){
  var x=(c-a)*R2D*6371000,y=(d-b)*R2D*6371000*Math.cos((a+c)/2*R2D);
  return Math.sqrt(x*x+y*y);
}
function far(m){
  return m<950?Math.round(m/10)*10+' ม./m':(m/1000).toFixed(1)+' กม./km';
}
var ARROWS=['↑','↗','→','↘','↓','↙','←','↖'];
function arrow(a,b,c,d){
  var y=Math.sin((d-b)*R2D)*Math.cos(c*R2D);
  var x=Math.cos(a*R2D)*Math.sin(c*R2D)-Math.sin(a*R2D)*Math.cos(c*R2D)*Math.cos((d-b)*R2D);
  return ARROWS[Math.round(((Math.atan2(y,x)/R2D+360)%360)/45)%8];
}
/* Two records on one coordinate is not a distance. 2,958 pinned rows share a
   point with another record — a tambon centroid stacks everything it placed —
   so under 25 m the card says nothing rather than "0 ม." three times. */
var SAME=25;

/* Open now, off the same week-minute intervals the lamps are drawn from.
   A place with no hours recorded is NOT closed, and gets no lamp at all. */
function openNow(hk){
  if(!TAB||!TAB.hours)return null;
  var iv=TAB.hours[hk];
  if(!iv||!iv.length)return null;
  var d=new Date(),wm=((d.getDay()+6)%7)*1440+d.getHours()*60+d.getMinutes();
  for(var i=0;i<iv.length;i++){
    var seg=iv[i];
    if(seg&&seg.length===2&&typeof seg[0]==='number'){
      if(wm>=seg[0]&&wm<seg[1])return true;
    }else if(seg&&seg.length){
      for(var j=0;j<seg.length;j++)
        if(wm>=seg[j][0]&&wm<seg[j][1])return true;
    }
  }
  return false;
}

function esc(s){
  return String(s==null?'':s).replace(/[&<>"]/g,function(c){
    return {'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;'}[c];});
}
function bi(th,en){
  return '<span lang="th">'+esc(th)+'</span> · <span lang="en">'+esc(en)+'</span>';
}

/* ---- the plan, which md.js owns ---------------------------------------
   It exposes MDPLAN where it can; where it cannot the card reads and writes
   the same key by the same rules, and repaints the buttons md.js painted. */
var PLAN_KEY='md-plan',PLAN_MAX=9;
function planGet(){
  if(window.MDPLAN&&window.MDPLAN.get)return window.MDPLAN.get();
  try{var v=JSON.parse(localStorage.getItem(PLAN_KEY));
    return Object.prototype.toString.call(v)==='[object Array]'?v.slice(0,PLAN_MAX):[];
  }catch(e){return[];}
}
function planSet(list){
  if(window.MDPLAN&&window.MDPLAN.set){window.MDPLAN.set(list);return;}
  try{localStorage.setItem(PLAN_KEY,JSON.stringify(list.slice(0,PLAN_MAX)));}catch(e){}
  var have={},i;
  for(i=0;i<list.length;i++)have[list[i]]=1;
  var btns=document.querySelectorAll('.planbtn[data-plan]');
  for(i=0;i<btns.length;i++){
    var on=!!have[btns[i].getAttribute('data-plan')];
    btns[i].className=on?(btns[i].className.replace(/\s*\bon\b/,'')+' on')
                        :btns[i].className.replace(/\s*\bon\b/,'');
    btns[i].setAttribute('aria-pressed',on?'true':'false');
  }
  var cnt=document.querySelectorAll('.plancount');
  for(i=0;i<cnt.length;i++){
    cnt[i].textContent=list.length||'';
    cnt[i].style.display=list.length?'':'none';
  }
}

/* ---- the card ---------------------------------------------------------- */
var el=null,body=null,cur=null,lastFocus=null;
var trail=[],seq=0,ours=0;      /* the walk, and how many history entries are ours */
var surface=null;               /* {filter, near, mark} of the map that opened it */
var filterOn=null;

function build(){
  if(el)return el;
  el=document.createElement('div');
  el.className='mdtap';
  el.hidden=true;
  /* A region, not a dialog: nothing is trapped, the map underneath stays
     live, and a reader can tab straight past it. */
  el.setAttribute('role','region');
  el.setAttribute('aria-label','จุดที่แตะบนแผนที่ · the point you touched');
  el.innerHTML='<div class="mdtap-body"></div>';
  body=el.firstChild;
  document.body.appendChild(el);
  el.addEventListener('click',onClick);
  document.addEventListener('keydown',function(ev){
    /* Escape closes — it does not walk back one. A reader pressing it wants
       out of the card, and the trail is still on the Back button. */
    if(ev.key==='Escape'&&!el.hidden)close();
  });
  return el;
}

/* What the card knows how to say about one place. Everything is read off the
   mark that was touched or the row behind it; nothing here invents a fact. */
function render(){
  var it=cur;if(!it)return;
  var h='';
  h+='<div class="mdtap-head">';
  if(trail.length>1)
    h+='<button type="button" class="mdtap-back" data-act="back" ' +
       'aria-label="ย้อนกลับ · Back">←</button>';
  h+='<button type="button" class="mdtap-x" data-act="close" '+
     'aria-label="ปิด · Close">×</button></div>';
  h+='<p class="mdtap-name" tabindex="-1">'+esc(it.name)+'</p>';
  if(it.nameEn&&it.nameEn!==it.name)
    h+='<p class="mdtap-en">'+esc(it.nameEn)+'</p>';
  if(it.rom&&it.rom!==it.nameEn&&it.rom!==it.name)
    h+='<p class="mdtap-rom">'+esc(it.rom)+'</p>';

  var facts=[];
  var sub=words(it);
  if(sub)facts.push(esc(sub[0])+' · '+esc(sub[1]));
  var where=place(it);
  if(where)facts.push(esc(where));
  if(it.dist)facts.push(esc(it.dist));
  if(it.rank)facts.push('🐜'+esc(it.rank));
  if(facts.length){
    h+='<p class="mdtap-facts">';
    for(var i=0;i<facts.length;i++)h+='<span class="mdtap-fact">'+facts[i]+'</span>';
    h+='</p>';
  }

  if(it.hk!=null&&TAB){
    var o=openNow(it.hk);
    if(o!==null)
      h+='<p class="mdtap-lamp '+(o?'mdtap-open':'mdtap-shut')+'"><b></b>'+
         (o?bi('เปิดอยู่','open now'):bi('ปิดอยู่','closed now'))+'</p>';
  }

  h+=tagsHTML(it);
  h+=nearHTML(it);

  h+='<p class="mdtap-do">';
  if(it.href)
    h+='<a class="mdtap-go" href="'+esc(it.href)+'">'+bi('เปิดหน้านี้','Open')+'</a>';
  if(it.plan){
    var inplan=indexOf(planGet(),it.plan)>-1;
    h+='<button type="button" class="mdtap-plan planbtn'+(inplan?' on':'')+
       '" data-act="plan" data-plan="'+esc(it.plan)+'" aria-pressed="'+
       (inplan?'true':'false')+'">'+
       (inplan?bi('อยู่ในแผน','In plan'):bi('🧭 เพิ่มลงแผน','Add to plan'))+'</button>';
  }
  if(it.lat!=null&&it.lng!=null)
    h+='<a href="geo:'+it.lat+','+it.lng+'?q='+encodeURIComponent(it.name)+'">'+
       bi('📍 นำทาง','Directions')+'</a>';
  h+='</p>';
  body.innerHTML=h;
}

function words(it){
  if(it.subWords)return it.subWords;
  if(it.su&&TAB&&TAB.subs&&TAB.subs[it.su])return TAB.subs[it.su];
  if(it.sub){
    var p=String(it.sub).split(' · ');
    return p.length>1?p:[it.sub,''];
  }
  return null;
}
/* Where it is, in one phrase: the street it is on, or the tambon it is in.
   Not both — the card is a card. */
function place(it){
  if(it.where)return it.where;
  if(TAB){
    if(it.st!=null&&TAB.streets&&TAB.streets[it.st])
      return TAB.streets[it.st][1]||TAB.streets[it.st][2];
    if(it.ar!=null&&TAB.areas&&TAB.areas[it.ar])
      return TAB.areas[it.ar][0]+' '+TAB.areas[it.ar][1];
  }
  return it.area||'';
}

/* THE CHIPS FILTER THE MAP. Where the surface that opened the card can narrow
   itself it hands us a filter(); the chip then narrows what is drawn and says
   how many are left, and a tag nobody has says zero rather than quietly
   showing everything. Where it cannot — a place map draws five dots — the chip
   is a link to the same filter on the results map, which can. */
function tagsHTML(it){
  if(!it.t||!it.t.length||!TAB||!TAB.tags)return '';
  var h='<p class="mdtap-facts">',n=0;
  for(var i=0;i<it.t.length&&n<5;i++){
    var t=TAB.tags[it.t[i]];
    if(!t)continue;
    n++;
    var label=(t[3]?t[3]+' ':'')+esc(t[1]);
    if(surface&&surface.filter)
      h+='<button type="button" class="mdtap-tag" data-act="filter" data-tag="'+
         it.t[i]+'" aria-pressed="'+(filterOn===it.t[i]?'true':'false')+'">'+
         label+'</button>';
    else
      h+='<a class="mdtap-tag" href="'+ROOT()+'search.html?tag='+
         encodeURIComponent(t[0])+
         (it.lat!=null?'&near='+it.lat+','+it.lng:'')+'">'+label+'</a>';
  }
  h+='</p>';
  if(!n)return '';
  if(filterOn!=null&&surface&&surface.filter){
    var c=surface.count==null?'':surface.count;
    var tg=TAB.tags[filterOn];
    h+='<p class="mdtap-filt"><span role="status">'+
       (c===0?bi('ไม่มีที่ไหนในกรอบนี้','none on this map'):
              esc(String(c))+' '+bi('จุด','places'))+'</span>'+
       '<a href="'+ROOT()+'search.html?tag='+encodeURIComponent(tg?tg[0]:'')+
       (it.lat!=null?'&near='+it.lat+','+it.lng:'')+'">'+
       bi('เรียงตามระยะ','nearest first')+'</a>'+
       '<button type="button" data-act="unfilter">'+bi('ล้าง','clear')+'</button></p>';
  }
  return h;
}

/* The three nearest, and tapping one MOVES THE CARD — no page load, and the
   phone's own Back button undoes it. */
function nearHTML(it){
  var list=surface&&surface.near?surface.near(it):null;
  if(!list||!list.length)return '';
  var h='<div class="mdtap-near"><h3>'+bi('ใกล้ที่นี่','Nearest to it')+
        '</h3><ul>';
  for(var i=0;i<list.length&&i<3;i++){
    var m=list[i][0],o=list[i][1];
    h+='<li><button type="button" data-act="walk" data-i="'+i+'"><span>'+
       esc(o.name)+'</span>'+(m>=SAME?'<span class="far">'+esc(far(m))+'</span>':'')+
       '</button></li>';
  }
  NEAR=list;
  return h+'</ul></div>';
}
var NEAR=null;

function indexOf(a,v){
  for(var i=0;i<a.length;i++)if(a[i]===v)return i;
  return -1;
}

/* ---- the walk, and the Back button ------------------------------------ */
function show(item,opener,opts){
  if(!item||!item.name)return;
  build();
  opts=opts||{};
  /* A card opened by a different map must not inherit the last one's
     neighbours or its filter — MDCARD's callers pass no surface at all. */
  if(opts.surface!==undefined)surface=opts.surface;
  else if(!opts.walk)surface=null;
  if(!opts.walk){trail=[];ours=0;filterOn=null;}
  trail.push(item);
  cur=item;
  lastFocus=opener||document.activeElement;
  el.hidden=false;
  mark();
  var need=(item.t&&item.t.length)||item.hk!=null||item.st!=null||
           item.ar!=null||item.su;
  render();
  if(need&&!TAB)tables(function(){if(cur===item)render();});
  /* One history entry per card. The first Back closes the card, the next
     walks the trail backwards — the behaviour a phone's own back gesture
     already promises, and the only "undo" a reader is guaranteed to know. */
  try{history.pushState({mdtap:++seq},'');ours++;}catch(e){}
  focusName();
}
function focusName(){
  var n=body&&body.querySelector('.mdtap-name');
  if(n){try{n.focus({preventScroll:true});}catch(e){try{n.focus();}catch(e2){}}}
}
function hide(restore){
  if(!el||el.hidden)return;
  el.hidden=true;
  unmark();
  cur=null;trail=[];
  if(restore!==false&&lastFocus&&lastFocus.focus){try{lastFocus.focus();}catch(e){}}
  lastFocus=null;
}
/* Closing gives back every history entry the walk took, so the reader's Back
   button lands where they were before the first touch rather than replaying
   the walk they just closed. */
function close(){
  var n=ours;ours=0;
  hide();
  if(n>0){try{history.go(-n);}catch(e){}}
}
/* Back, from the ← in the card: one step of the walk, and the history entry
   goes with it so the two never disagree. */
function back(){
  if(ours>0){try{history.back();return;}catch(e){}}
  popTo(trail.length-2);
}
function popTo(i){
  if(i<0){hide();return;}
  trail=trail.slice(0,i+1);
  cur=trail[i];
  render();mark();focusName();
}
window.addEventListener('popstate',function(ev){
  if(!el||el.hidden)return;
  var st=ev.state&&ev.state.mdtap;
  if(ours>0)ours--;
  if(!st){hide();return;}
  popTo(trail.length-2);
});

/* The dot that was touched, marked on the map it was touched on. Only where
   the surface told us which element it is — a card never draws on a map. */
var lit=null;
function mark(){
  unmark();
  if(!cur||!surface||!surface.mark)return;
  var m=surface.mark(cur);
  if(!m||!m.classList)return;
  m.classList.add('mdtap-lit');lit=m;
}
function unmark(){if(lit&&lit.classList)lit.classList.remove('mdtap-lit');lit=null;}

/* ---- what the card's own buttons do ----------------------------------- */
function onClick(ev){
  var t=ev.target,b=t.closest?t.closest('[data-act]'):null;
  if(!b)return;
  var act=b.getAttribute('data-act');
  if(act==='close'){ev.preventDefault();close();return;}
  if(act==='back'){ev.preventDefault();back();return;}
  if(act==='plan'){
    ev.preventDefault();
    var k=b.getAttribute('data-plan'),list=planGet(),i=indexOf(list,k);
    if(i>-1)list.splice(i,1);
    else if(list.length>=PLAN_MAX){
      alert('แผนหนึ่งเก็บได้ '+PLAN_MAX+' จุด / a plan holds '+PLAN_MAX+' stops');
      return;}
    else list.push(k);
    planSet(list);render();return;}
  if(act==='filter'||act==='unfilter'){
    ev.preventDefault();
    if(!surface||!surface.filter)return;
    var tag=act==='filter'?+b.getAttribute('data-tag'):null;
    filterOn=(act==='filter'&&filterOn===tag)?null:tag;
    surface.count=surface.filter(filterOn);
    render();return;}
  if(act==='walk'){
    ev.preventDefault();
    var n=NEAR&&NEAR[+b.getAttribute('data-i')];
    if(n)show(n[1],b,{walk:true});
    return;}
}

/* ---- wiring a map ------------------------------------------------------
   A surface hands over three things and keeps none of them: how to find the
   marks it drew, how to turn one into an item, and (when it can) how to
   narrow itself. A tap that hits no mark does nothing at all — bare ground
   says nothing, and a named building in the tiles that is not one of our
   records is not ours to describe. */
function wire(holder,cfg){
  if(!holder||holder._mdtap)return;
  holder._mdtap=true;
  cfg=cfg||{};
  var reach=cfg.reach||34;      /* a fingertip's radius, in CSS px */
  function marks(){return cfg.marks?cfg.marks():[];}
  function nearestTo(cx,cy){
    var best=null,bd=reach*reach,list=marks();
    for(var i=0;i<list.length;i++){
      var r=list[i].getBoundingClientRect();
      if(!r.width&&!r.height)continue;
      var dx=r.left+r.width/2-cx,dy=r.top+r.height/2-cy,d=dx*dx+dy*dy;
      if(d<bd){bd=d;best=list[i];}
    }
    return best;
  }
  function open(mark,opener){
    var item=cfg.item?cfg.item(mark):null;
    if(!item)return false;
    show(item,opener||holder,{surface:{
      filter:cfg.filter||null,
      near:cfg.near||null,
      mark:cfg.markOf||null
    }});
    return true;
  }
  holder.addEventListener('click',function(ev){
    /* A mark that is a real link stays a real link for every gesture that
       means "open this somewhere else". */
    if(ev.metaKey||ev.ctrlKey||ev.shiftKey||ev.altKey||ev.button)return;
    var direct=ev.target.closest?ev.target.closest('[data-mdtap],[data-mdrow]'):null;
    var m=direct||nearestTo(ev.clientX,ev.clientY);
    if(!m)return;                       /* bare ground: silence */
    /* Only once the mark has actually produced a card is the reader's click
       taken away from it — a mark we cannot describe stays the link it was. */
    if(open(m,m===direct?m:holder))ev.preventDefault();
  });
  holder._mdtapOpen=open;
}

/* ---- the surfaces that need no code of their own -----------------------
   Anything whose marks carry data-mdtap (a dot that knows its own record) or
   data-mdrow (a dot paired with a row in the list below it, which is the
   pattern the shelf maps already use). Soi maps, event maps and the merit
   round arrive here without a line of their own. */
function fromEl(a){
  if(!a)return null;
  var d=function(k){return a.getAttribute('data-'+k);};
  var lat=parseFloat(d('lat')),lng=parseFloat(d('lng'));
  var t=d('t'),item={
    name:(d('n')||'').split(' · ')[0]||d('n')||'',
    nameEn:d('ne')||((d('n')||'').split(' · ')[1]||''),
    rom:d('rom')||'',
    sub:d('sub')||'',
    su:d('su')||'',
    rank:(d('rank')&&d('rank')!=='0')?d('rank'):'',
    plan:d('plan')||'',
    area:d('area')||'',
    href:a.getAttribute('href')||d('href')||'',
    lat:isFinite(lat)?lat:null,
    lng:isFinite(lng)?lng:null
  };
  if(t)item.t=t.split(',').map(Number);
  if(d('st')!=null)item.st=+d('st');
  if(d('ar')!=null)item.ar=+d('ar');
  if(d('hk')!=null)item.hk=+d('hk');
  return item.name?item:null;
}
function rowsOf(holder){
  var box=holder.closest?holder.closest('.mdmapwrap,section,main,body'):null;
  return (box||document).querySelectorAll('li[data-n]');
}
function autoWire(){
  var holders=document.querySelectorAll('.mdmap'),i;
  for(i=0;i<holders.length;i++)(function(holder){
    var marked=holder.querySelectorAll('[data-mdtap]');
    if(marked.length){
      wire(holder,{
        marks:function(){return holder.querySelectorAll('[data-mdtap]');},
        item:fromEl,
        near:function(it){return nearestOf(holder.querySelectorAll('[data-mdtap]'),it);},
        markOf:function(it){return it._el||null;}
      });
      return;
    }
    var rowed=holder.querySelectorAll('[data-mdrow]');
    if(rowed.length){
      var rows=rowsOf(holder);
      wire(holder,{
        marks:function(){return holder.querySelectorAll('[data-mdrow]');},
        item:function(m){
          var row=rows[+m.getAttribute('data-mdrow')];
          return row?fromRow(row,m):null;
        },
        near:null,
        markOf:null
      });
    }
  })(holders[i]);
}
function fromRow(row,mark){
  var a=row.querySelector('a[href]'),b=row.querySelector('.planbtn[data-plan]');
  var it=fromEl(row)||{};
  it.name=(row.getAttribute('data-n')||'').split(' · ')[0]||it.name;
  if(a&&!it.href)it.href=a.getAttribute('href');
  if(b&&!it.plan)it.plan=b.getAttribute('data-plan');
  if(mark){
    var la=parseFloat(mark.getAttribute('data-lat')),
        ln=parseFloat(mark.getAttribute('data-lng'));
    if(isFinite(la)){it.lat=la;it.lng=ln;}
  }
  return it.name?it:null;
}
/* The nearest others among marks we can see, for the walk. Distances are only
   claimed when both ends are known. */
function nearestOf(list,it){
  if(it.lat==null)return null;
  var out=[];
  for(var i=0;i<list.length;i++){
    var o=fromEl(list[i]);
    if(!o||o.lat==null||o.name===it.name)continue;
    o._el=list[i];
    out.push([metres(it.lat,it.lng,o.lat,o.lng),o]);
  }
  out.sort(function(a,b){return a[0]-b[0];});
  return out.slice(0,3);
}

var MDTAP={
  show:function(item,opener,opts){show(item,opener,opts);},
  hide:function(){hide();},
  wire:wire,
  fromEl:fromEl,
  /* Kept at this name because three maps already ask the card for the
     sentence rather than working it out themselves. */
  gap:function(a,b){return far(metres(a.lat,a.lng,b.lat,b.lng));},
  metres:metres,
  arrow:arrow,
  far:far
};
window.MDTAP=MDTAP;
/* Every map on this site already calls MDCARD. It keeps its name, and gets
   this card — while md.js's own MDCARD stays exactly where it is, so a phone
   that never received tap.js still gets an answer when it touches a dot. */
window.MDCARD=MDTAP;

if(document.readyState==='loading')
  document.addEventListener('DOMContentLoaded',autoWire);
else autoWire();
})();
"""


if __name__ == "__main__":
    print("This layer runs from build.py. Run: python3 build.py")
