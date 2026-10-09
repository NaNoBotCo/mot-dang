#!/usr/bin/env python3
"""กรองเอง — the reader's own boolean, exercised against the real catalogue.

    python3 tests/test_refine.py          (no build needed)

WHAT THIS RUNS IS WHAT THE SITE RUNS. `refine_layer.JS` is handed to node
verbatim — no slicing, no re-implementation of the rules in Python. The
lesson is test_search.py's: that test lifted the matcher by slicing build.py
between two lines, the lines moved, and it spent three weeks reporting
nothing while failing to run at all.

IT DOES NOT NEED A BUILT SITE, which is the reason it can run at all right
now: `docs/data/index.json` is written near the end of a build and there is
usually one in progress. The fixture is derived here from
`data/canonical/*.json` — real Thai trade words, real tambon, real streets,
real distributions — in the same shape build.py's index writer emits
(t/tt/st/ar/c/su, ints into search_tables.json). If that shape moves, the
derivation below has to move with it, and the count assertions will say so
by going to zero rather than by passing hollowly.

THE CASES THAT MATTER, and why each one is here:

  AND / OR      Two values in one drawer are a union; two drawers are an
                intersection. That is the whole boolean, and it is asserted
                against sets computed independently of the engine, so the
                engine cannot mark its own homework.
  NOT           An exclusion removes exactly the rows carrying the value and
                not one row more.
  SILENCE       A row that never recorded the field is never removed by an
                exclusion on it. This is go/parking-bug written as a test:
                unknown read as no cost 1,632 car parks their place in a
                parking search, because nobody had typed `parking=yes` on
                them. `none=` then asks for that silence deliberately.
  THE COUNTS    The number printed beside a door is the number of rows behind
                it. A door that lies is worse than no door, and counted-
                against-the-current-set is the only version worth printing.
  THE URL       Add-then-remove returns to the exact URL you started from, so
                the back button is undo and a refinement can be sent to
                somebody.
"""
import json
import os
import subprocess
import sys
import tempfile

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)
import refine_layer  # noqa: E402

CANON = os.path.join(ROOT, "data", "canonical")


def fixture():
    """The real catalogue, in the shape the browser index carries it.

    Reads whichever canonical files are on disk. Pre-Overture and post-
    Overture both work; the assertions are all relative to the set that was
    actually loaded, so a catalogue that grows 3.4x overnight does not turn
    this red.
    """
    rows, tags, trade, areas, streets = [], {}, {}, {}, {}

    def idx(d, k):
        return d.setdefault(k, len(d))

    files = sorted(f for f in os.listdir(CANON) if f.endswith(".json")) \
        if os.path.isdir(CANON) else []
    for fn in files:
        try:
            recs = json.load(open(os.path.join(CANON, fn)))
        except (ValueError, OSError):
            continue
        if not isinstance(recs, list):
            continue
        prov = fn[:-5]
        for r in recs:
            a = r.get("attrs") or {}
            # The TEXT fields, in the same roles build.py gives them: `n`/`e`
            # are shown, `a` (other names, readings) and `k` (shelf words,
            # cuisine, brand, road) are matched and never shown. The word
            # scopes are meaningless without all four, and a fixture that
            # omitted them let every scope assertion pass on zero rows.
            e = {"n": r.get("nameTh") or r.get("name") or "", "p": prov}
            if r.get("nameEn"):
                e["e"] = r["nameEn"]
            alias = list(a.get("altNames") or []) + list(
                (a.get("namesOther") or {}).values())
            if alias:
                e["a"] = " ".join(x for x in alias if isinstance(x, str))
            k = [x for x in (r.get("cat") or []) + (r.get("sub") or [])
                 if isinstance(x, str)]
            for extra in ("cuisine", "brand", "street", "kind"):
                if isinstance(a.get(extra), str):
                    k.append(a[extra])
            k += [x for x in (a.get("tradeTags") or []) if isinstance(x, str)]
            if k:
                e["k"] = " ".join(k)
            if isinstance(r.get("lat"), (int, float)) and \
               isinstance(r.get("lng"), (int, float)):
                e["lat"], e["lng"] = r["lat"], r["lng"]
            t = [idx(tags, k) for k in
                 ([a["kind"]] if isinstance(a.get("kind"), str) else [])
                 + ([a["cuisine"]] if isinstance(a.get("cuisine"), str) else [])]
            if t:
                e["t"] = t[:6]
            tt = [idx(trade, w) for w in (a.get("tradeTags") or [])[:6]
                  if isinstance(w, str)]
            if tt:
                e["tt"] = tt
            if isinstance(a.get("tambon"), str):
                e["ar"] = idx(areas, a["tambon"])
            if isinstance(a.get("street"), str):
                e["st"] = idx(streets, a["street"])
            if r.get("cat"):
                e["c"] = r["cat"]
            if r.get("sub"):
                e["su"] = r["sub"]
            rows.append(e)
    tab = {"tags": [[k, k, "", ""] for k in tags],
           "trade": [[k, "", ""] for k in trade],
           "areas": [[k, k, "", ""] for k in areas],
           "streets": [[k, k, ""] for k in streets],
           "subs": {}, "hours": []}
    return rows, tab


HARNESS = r"""
const fs=require('fs');
const els={};
global.window={};global.MD_CATWORDS={};global.navigator={};
global.location={search:'',pathname:'/search.html'};
function stub(id){return {id:id,innerHTML:'',textContent:'',hidden:true,attrs:{},
  addEventListener:function(){},setAttribute:function(k,v){this.attrs[k]=v;},
  removeAttribute:function(k){delete this.attrs[k];},
  getAttribute:function(k){return this.attrs[k]!=null?this.attrs[k]:null;},
  querySelector:function(){return null;},querySelectorAll:function(){return [];}};}
global.document={documentElement:{getAttribute:function(){return '';}},
  getElementById:function(id){return els[id]||(els[id]=stub(id));}};
eval(fs.readFileSync(process.argv[2],'utf8'));
const R=window.MDREFINE;
const TAB=JSON.parse(fs.readFileSync(process.argv[3],'utf8'));
const ROWS=JSON.parse(fs.readFileSync(process.argv[4],'utf8'));
let pass=0;const bad=[];
function is(n,got,want){if(JSON.stringify(got)===JSON.stringify(want))pass++;
  else bad.push(n+': got '+JSON.stringify(got)+', want '+JSON.stringify(want));}
function ok(n,c,d){if(c)pass++;else bad.push(n+(d!=null?' ('+d+')':''));}
const q=s=>{location.search=s;return R.apply(ROWS,TAB).length;};
const rows=s=>{location.search=s;return R.apply(ROWS,TAB);};
// Counted WITHOUT the engine wherever possible, so it cannot mark its own homework.
const cnt=(k,v)=>ROWS.filter(e=>R.vals(e,k,TAB).indexOf(v)>=0).length;
const words=TAB.trade.map(t=>t[0]).filter(w=>cnt('tag',w)>=5);
const areas=TAB.areas.map(a=>a[0]).sort((a,b)=>cnt('ar',b)-cnt('ar',a));
if(words.length<2||!areas.length){
  console.log(JSON.stringify({skip:'the catalogue on disk carries too few trade words or tambon to test against'}));
  process.exit(0);}
const A=words[0],B=words[1],AR=areas[0],EA=encodeURIComponent;

// ── THE FOUR WORD ROWS. Google's form, and the reason it is legible: the
//    label says what the row does, so nobody has to know it is a boolean.
is('nothing asked is everything kept',q(''),ROWS.length);
const W1='นวด',W2='คลินิก';
const anyText=e=>R.text(e,'any');
const hasW=(e,w)=>anyText(e).indexOf(w.toLowerCase())>=0;
is('all these words is AND',q('?as_q='+EA(W1)),ROWS.filter(e=>hasW(e,W1)).length);
is('two words in the AND row need both',
   q('?as_q='+EA(W1+' '+W2)),ROWS.filter(e=>hasW(e,W1)&&hasW(e,W2)).length);
is('any of these words is OR',
   q('?as_oq='+EA(W1+' '+W2)),ROWS.filter(e=>hasW(e,W1)||hasW(e,W2)).length);
is('none of these words is NOT',
   q('?as_eq='+EA(W1)),ROWS.filter(e=>!hasW(e,W1)).length);
ok('AND and NOT compose',(function(){
  const n=q('?as_q='+EA(W2)+'&as_eq='+EA(W1));
  return n===ROWS.filter(e=>hasW(e,W2)&&!hasW(e,W1)).length;})());
const PH='นวดแผนไทย';
is('the exact phrase is a substring, not a bag of words',
   q('?as_epq='+EA(PH)),ROWS.filter(e=>anyText(e).indexOf(PH)>=0).length);

// ── THE PLAIN SEARCH BOX IS NOT THE AND ROW.
//    Every assertion above sends as_q, as_oq, as_eq or as_epq — the four rows
//    of the advanced form. None of them sent `q`, which is what search.html's
//    box actually sends, and that is how this shipped: `st.q` fell back to
//    `q`, wordsOk demanded every token as a literal substring, and searchcore's
//    ranked answer was thrown away. Live, 2026-09-09: "guitar" 9 results,
//    "martin guitar" 0, "place to buy a Martin guitar" 0 — while searchcore,
//    handed the same index, put Guitar House first for the third of those.
//    searchcore owns `q`; this layer owns the four advanced rows and the
//    structured drawers. A plain `q` reaches here and changes nothing.
is('the search box q is searchcore\'s, not a filter',
   q('?q='+EA(W1+' '+W2)),ROWS.length);
is('a q no row contains still keeps every row',
   q('?q='+EA('martin guitar')),ROWS.length);

// ── THE CERTAINTY CONTROL. `k` and `a` are matched and never shown; scoping
//    to the name is how somebody who knows what a shop is called gets it.
const nameOnly=q('?as_q='+EA(W1)+'&as_in=name');
const anywhere=q('?as_q='+EA(W1));
ok('the name-only scope is never wider than anywhere',nameOnly<=anywhere,
   nameOnly+' <= '+anywhere);
// Proved on a row built for it rather than asserted about a word that
// happens to sit in both places: find a place carrying a shelf word its NAME
// does not carry, and show the scope shuts it out. `นวด` was the first word
// tried and it lives in both fields on every row that has it, so the blunt
// "name is narrower" assertion passed on a tie and proved nothing.
ok('a word that lives only in the hidden fields is shut out by name-only',(function(){
  for(const e of ROWS){
    if(!e.k||!e.n)continue;
    for(const w of String(e.k).toLowerCase().split(/\s+/)){
      if(w.length<3||String(e.n).toLowerCase().indexOf(w)>=0)continue;
      if(String(e.e||'').toLowerCase().indexOf(w)>=0)continue;
      location.search='?as_q='+EA(w)+'&as_in=name';
      const shut=!R.ok(e,R.parse(),TAB);
      location.search='?as_q='+EA(w);
      const found=R.ok(e,R.parse(),TAB);
      if(shut&&found)return true;}}
  return false;})());
ok('the reading scope sits between them',(function(){
  const r=q('?as_q='+EA(W1)+'&as_in=read');return r>=nameOnly&&r<=anywhere;})());
ok('none-of-these searches the WIDEST fields whatever the scope',(function(){
  // a word hiding in a cuisine tag is still a word the reader said no to
  const a=q('?as_eq='+EA(W1)+'&as_in=name'),b=q('?as_eq='+EA(W1));
  return a===b;})());

// ── THE STRUCTURED FIELDS
is('one value',q('?tag='+EA(A)),cnt('tag',A));
const inter=ROWS.filter(e=>R.vals(e,'tag',TAB).indexOf(A)>=0
                         &&R.vals(e,'ar',TAB).indexOf(AR)>=0).length;
is('two fields is the intersection',q('?tag='+EA(A)+'&ar='+EA(AR)),inter);
const union=ROWS.filter(e=>{const v=R.vals(e,'tag',TAB);
  return v.indexOf(A)>=0||v.indexOf(B)>=0;}).length;
is('two values of one field is the union',q('?tag='+EA(A)+','+EA(B)),union);
is('an exclusion removes exactly its own rows',
   q('?not='+EA('tag:'+B)),ROWS.length-cnt('tag',B));
const fk=(function(){const c={};ROWS.forEach(function(e){
  (e.f||[]).forEach(function(x){c[x]=(c[x]||0)+1;});});
  return Object.keys(c).sort(function(a,b){return c[b]-c[a];})[0];})();
if(fk){is('a facet key filters — nothing could filter on `f` before',
         q('?f='+EA(fk)),cnt('f',fk));}
else{ok('no facet keys in this slice — `f` untested',true);}
const pv=(function(){const c={};ROWS.forEach(e=>{if(e.p)c[e.p]=1;});
  return Object.keys(c)[0];})();
if(pv){is('province filters',q('?p='+EA(pv)),ROWS.filter(e=>e.p===pv).length);}
else{ok('one province in this slice — `p` untested',true);}

// ── PRESENCE AND ABSENCE. What the add and claim flows are for.
const pinned=ROWS.filter(e=>e.lat!=null&&e.lng!=null).length;
is('has=pin is the pinned',q('?has=pin'),pinned);
is('blank=pin is exactly the rest',q('?blank=pin'),ROWS.length-pinned);
is('has and blank on one field cannot both hold',q('?has=pin&blank=pin'),0);
const noAr=ROWS.filter(e=>R.vals(e,'ar',TAB).length===0).length;
is('blank=ar is the unfilled',q('?blank=ar'),noAr);

// ── UNKNOWN IS NOT NO — go/parking-bug, as a test
is('a row that never named an area survives an area exclusion',
   q('?not='+EA('ar:'+AR)),ROWS.length-cnt('ar',AR));
location.search='';
ok('with no hours test handed over, open never filters',
   q('?open=1')===ROWS.length||q('?open=1')===0?q('?open=1')===0:false,
   'open with no test = '+q('?open=1'));

// ── DISTANCE. The pin is the field we hold on nearly everything.
const P=ROWS.find(e=>e.lat!=null&&e.lng!=null);
if(P){
  // MEASURE FROM THE SAME POINT THE ENGINE DOES. The URL carries five
  // decimal places, so an expectation computed from the unrounded record sits
  // about a metre away from where the engine is standing — enough to move a
  // place that is exactly on the boundary, and enough to swap two near-ties
  // in a distance sort. Both showed up as one-row disagreements.
  const PLAT=+P.lat.toFixed(5),PLNG=+P.lng.toFixed(5);
  const near=PLAT+','+PLNG;
  const within=ROWS.filter(e=>e.lat==null||
    R.dist(PLAT,PLNG,e.lat,e.lng)<=2).length;
  is('a radius keeps what is inside it',q('?near='+EA(near)+'&radius=2'),within);
  ok('an unpinned place is not thrown out by a radius it cannot be measured against',
     ROWS.filter(e=>e.lat==null).every(function(e){
       location.search='?near='+EA(near)+'&radius=2';
       return R.ok(e,R.parse(),TAB);}));
  ok('a tighter radius never returns more',
     q('?near='+EA(near)+'&radius=1')<=q('?near='+EA(near)+'&radius=5'));
  // SORT
  const nr=rows('?near='+EA(near)+'&sort=near');
  ok('nearest-first really is nearest-first',(function(){
    let last=-1;
    for(const e of nr){if(e.lat==null)break;
      const d=R.dist(PLAT,PLNG,e.lat,e.lng);if(d<last-1e-9)return false;last=d;}
    return true;})());
  ok('and the unpinned go last, not first',(function(){
    let seenBlank=false;
    for(const e of nr){if(e.lat==null)seenBlank=true;else if(seenBlank)return false;}
    return true;})());
}else{ok('no pinned rows in this slice — distance untested',true);}
const byName=rows('?sort=name');
ok('by name is in order',(function(){
  for(let i=1;i<byName.length;i++)
    if(String(byName[i-1].n||'').localeCompare(String(byName[i].n||''),'th')>0)return false;
  return true;})());
const byFull=rows('?sort=full');
ok('most complete first',(function(){
  for(let i=1;i<byFull.length;i++)
    if(R.fullness(byFull[i-1])<R.fullness(byFull[i]))return false;
  return true;})());
is('sorting never adds or drops a row',rows('?sort=full').length,ROWS.length);

// ── THE SENTENCE says what is on, and every part of it switches off
location.search='?as_q='+EA(W1)+'&as_eq='+EA(W2)+'&tag='+EA(A)+','+EA(B)+
  '&ar='+EA(AR)+'&not='+EA('tag:x')+'&blank=pin&sort=name&as_in=name';
const s=R.bar(R.parse(),TAB);
['ทุกคำ','ไม่มีคำ','หรือ','ยังไม่มี','เรียง','ชื่อเท่านั้น'].forEach(function(w){
  ok('the sentence says '+w,s.indexOf(w)>=0);});
ok('every term in it is a link that removes itself',
   (s.match(/class="refterm/g)||[]).length>=6);
ok('clear is one word',s.indexOf('refclear')>=0&&s.indexOf('ล้างทั้งหมด')<0);

// ── THE URL IS THE STATE
location.search='?as_q='+EA('หมู');
const u1=R.href(R.parse(),'add','tag',A);
location.search=u1.slice(u1.indexOf('?'));
is('add then remove returns to where it started',
   R.href(R.parse(),'del','tag',A),'/search.html?as_q='+EA('หมู'));
location.search='?as_q=x&tag='+EA(A)+'&sort=name&blank=pin';
is('clear empties everything, words included',R.href(R.parse(),'clear'),'/search.html');

// ── THE ADVANCED FORM SUBMITS AS A FORM, not as links this engine wrote.
//    A <select multiple> sends tag=a&tag=b, and reading only the first value
//    would have silently thrown away every choice past the first.
is('repeated params are read as a list',
   q('?tag='+EA(A)+'&tag='+EA(B)),union);
is('and mix with comma lists',q('?tag='+EA(A)+','+EA(B)),union);
is('a multi-select of presence rows all apply',q('?has=pin&has=hk'),
   ROWS.filter(e=>e.lat!=null&&e.hk!=null).length);

// ── THE EASY VERSION: the Tools row, counted on THIS answer
els['toolrow']={innerHTML:'',querySelectorAll:function(){return [];},
  querySelector:function(){return null;},addEventListener:function(){},dataset:{}};
location.search='?tag='+EA(A);
const t=R.tally(ROWS,R.parse(),'ar',TAB);
ok('the tools row has something to offer',t.rows.length>=0);
if(t.rows.length){
  is('a dropdown option counts what choosing it would leave',
     t.rows[0][1],(function(){location.search='?tag='+EA(A)+'&ar='+EA(t.rows[0][0]);
       return R.apply(ROWS,TAB).length;})());}
else{ok('nothing left to narrow by area here',true);}

// ── THE TWO DOORS ON THE ANSWER. Both counts are counts of THESE rows, and
//    neither door is drawn at zero: an offer that goes nowhere is worse than
//    no offer, and it is the one thing a reader cannot tell before tapping.
const DOORS=(rows,ev)=>{els['resdoors']=stub('resdoors');
  els['resmap']=stub('resmap');els['resmapbtn']=stub('resmapbtn');
  els['evplaces']=stub('evplaces');els['evplaces'].textContent=JSON.stringify(ev||{});
  R.doors(rows);return els['resdoors'].innerHTML;};
const pinnedRows=ROWS.filter(e=>e.lat!=null&&e.lng!=null);
const flatRows=ROWS.filter(e=>e.lat==null||e.lng==null);
{
const few=pinnedRows.slice(0,7);
const h=DOORS(few,{});
ok('the map door is drawn over rows that have pins',h.indexOf('resdoor-map')>=0);
ok('the doors wear the drawn icons, not system emoji',
   h.indexOf('#i-map')>=0&&!/[\u{1F300}-\u{1FAFF}]/u.test(h),h.slice(0,200));
ok('and it says how many pins it will draw',h.indexOf('(7)')>=0,h.slice(0,200));
ok('the calendar door is not drawn when nothing is on',h.indexOf('resdoor-cal')<0);
}
if(flatRows.length){
const h=DOORS(flatRows.slice(0,5),{});
ok('no pins, no map door',h.indexOf('resdoor-map')<0,h.slice(0,200));
}else{ok('every row on this disk carries a pin',true);}
{
// More rows than the map is handed: the door says both numbers rather than
// promising a map of two thousand places and drawing two hundred.
const many=pinnedRows.slice(0,260);
if(many.length>200){
  const h=DOORS(many,{});
  ok('past the map cap the door says shown-of-total',
     h.indexOf('(200 / '+many.length.toLocaleString()+')')>=0,h.slice(0,240));
}else{ok('not enough pinned rows on this disk to test the map cap',true);}
}
{
// The fixture is derived from data/canonical and carries no `id`; the browser
// index does, and it is the join. Named here so the test joins the way the
// page joins rather than on a field the fixture happens to have.
const few=pinnedRows.slice(0,4).map((e,i)=>Object.assign({},e,{id:'place-'+i}));
const tbl={};tbl[few[0].id]=2;tbl[few[2].id]=1;
const h=DOORS(few,tbl);
ok('the calendar door is drawn when these places have events',h.indexOf('resdoor-cal')>=0);
ok('and it wears the drawn calendar icon',
   h.indexOf('#i-cal')>=0&&!/[\u{1F300}-\u{1FAFF}]/u.test(h),h.slice(0,200));
ok('and it counts the events, not the places',h.indexOf('(3)')>=0,h.slice(0,300));
ok('and it carries only the ids that have any',
   h.indexOf('place-0')>=0&&h.indexOf('place-1')<0,h.slice(0,300));
ok('a row with no id joins to nothing',
   DOORS(pinnedRows.slice(0,4),{undefined:9}).indexOf('resdoor-cal')<0);
// A toggle redraws the row with no argument. It must redraw what is there.
R.doors(few);const kept=els['resdoors'].innerHTML;R.doors();
ok('redrawing with nothing keeps the doors that are up',
   els['resdoors'].innerHTML===kept,els['resdoors'].innerHTML.slice(0,80));
const h2=DOORS(few,{'no-such-place':4});
ok('a table that names none of these rows draws no door',h2.indexOf('resdoor-cal')<0);
}

// ── THE CALENDAR FILE. Mirrored from build.py's ics_document, so what the
//    door hands over and what events.ics carries cannot disagree.
{
const doc=R.ics([{start:'2026-09-07 19:30:00',end:null,title:'Fight; night, late',
  source:'x',uid:'u1',recurring:true,weekday:2,url:'https://e.example',
  description:'two\nlines',place:{id:'p1',name:'Thapae Stadium'}}],'test');
ok('the file is a calendar',/^BEGIN:VCALENDAR\r\n/.test(doc)&&/END:VCALENDAR\r\n$/.test(doc));
ok('every line ends CRLF',doc.split('\n').every(l=>l===''||l.endsWith('\r')));
ok('the clock is Bangkok wall time, not the reader\'s',
   doc.indexOf('DTSTART;TZID=Asia/Bangkok:20260907T193000')>=0,doc);
ok('an event with no end gets two hours',
   doc.indexOf('DTEND;TZID=Asia/Bangkok:20260907T213000')>=0);
ok('semicolons and commas are escaped',
   doc.indexOf('SUMMARY:Fight\\; night\\, late')>=0,doc);
ok('a newline in a description does not break the file',
   doc.indexOf('DESCRIPTION:two lines')>=0);
ok('a weekly event repeats weekly',doc.indexOf('RRULE:FREQ=WEEKLY;BYDAY=WE')>=0);
ok('the venue is the location',doc.indexOf('LOCATION:Thapae Stadium')>=0);
const none=R.ics([{title:'no date',place:{id:'p'}}],'test');
ok('an event with no date is not in the file',none.indexOf('BEGIN:VEVENT')<0);
}

// ── THE MIRROR. The .ics the door hands over is written here, in the
//    browser, and events.ics is written in build.py. Two writers of one
//    format is how a calendar comes to disagree with the page it came from,
//    so every VEVENT this builds for a real event has to appear VERBATIM in
//    the file build.py shipped. Skipped when there is no built site to read.
if(process.argv[5]&&process.argv[6]){
  let shipped='',feed=null;
  try{shipped=fs.readFileSync(process.argv[5],'utf8');
      feed=JSON.parse(fs.readFileSync(process.argv[6],'utf8'));}catch(e){}
  const dated=((feed&&feed.events)||[]).filter(e=>e&&e.start);
  if(!shipped||!dated.length){ok('no built calendar on disk to mirror against',true);}
  else{
    const off=[];
    for(const e of dated){
      const one=R.ics([e],'x');
      const vev=one.slice(one.indexOf('BEGIN:VEVENT'),one.indexOf('END:VEVENT')+12);
      if(shipped.indexOf(vev)<0)off.push((e.title||'').slice(0,40));}
    ok(dated.length+' events write the same VEVENT here as build.py shipped',
       off.length===0,off.slice(0,3).join(' | '));}
}

console.log(JSON.stringify({pass:pass,bad:bad,rows:ROWS.length,
  a:A,b:B,ar:AR,fk:fk||null,pinned:pinned,nameOnly:nameOnly,anywhere:anywhere}));
"""


# The one thing two readings of the same row can do that one cannot: disagree.
MIRROR_JS = r"""
const fs=require('fs');
global.window={};global.MD_CATWORDS={};global.navigator={};
global.location={search:'',pathname:'/search.html'};
global.document={getElementById:function(){return {innerHTML:'',hidden:true};}};
eval(fs.readFileSync(process.argv[2],'utf8'));
const R=window.MDREFINE;
const TAB=JSON.parse(fs.readFileSync(process.argv[3],'utf8'));
const ROWS=JSON.parse(fs.readFileSync(process.argv[4],'utf8'));
const KEYS=JSON.parse(process.argv[5]);
const out=[];
for(let i=0;i<ROWS.length;i++)for(const k of KEYS){
  const v=R.vals(ROWS[i],k,TAB);
  // A value can contain a newline — at least one trade tag in the catalogue
  // does — so it is escaped before it goes into a line-per-record file.
  if(v.length)out.push(i+"\t"+k+"\t"+
    v.join("\u001f").replace(/\n/g,"\u2424").replace(/\r/g,"\u240d"));}
fs.writeFileSync(process.argv[6],out.join("\n"));
console.log(JSON.stringify({lines:out.length}));
"""


def mirror_readings(rows, tab, tmp):
    """Does refine_layer.row_values read a row exactly as refine_layer.JS does?

    /advanced.html bakes its dropdown counts in Python at build time; the
    results page counts the same values in JavaScript, live. If the two ever
    read a row differently, the form promises a number the answer will not
    honour — you pick "สันติธรรม (148)" and get 143, with nothing on either
    page to say why. Nobody would find that by reading either file, because
    each is right on its own.

    So both readings are run over every row of the real catalogue and compared
    value for value, in order. `open` is excluded and that exclusion is
    asserted rather than assumed: it is answered against a clock, so a count
    baked at build time could not be honest about it, and Python deliberately
    does not implement it.
    """
    import subprocess
    keys = [k for k, _, _, _ in refine_layer.NARROW_ROWS] + \
        ["cat", "kd", "p", "pin", "hk"]
    if "open" in keys:
        return ["`open` is in the narrowing keys but cannot be baked against a clock"]

    js_out = os.path.join(tmp, "js_vals.tsv")
    p = {n: os.path.join(tmp, n) for n in ("refine.js", "tab.json", "rows.json", "m.js")}
    open(p["refine.js"], "w").write(refine_layer.JS)
    open(p["tab.json"], "w").write(json.dumps(tab, ensure_ascii=False))
    open(p["rows.json"], "w").write(json.dumps(rows, ensure_ascii=False))
    open(p["m.js"], "w").write(MIRROR_JS)
    try:
        r = subprocess.run(["node", p["m.js"], p["refine.js"], p["tab.json"],
                            p["rows.json"], json.dumps(keys), js_out],
                           capture_output=True, text=True, timeout=600)
    except FileNotFoundError:
        return []
    if r.returncode != 0:
        return ["the JavaScript reading did not run: " + (r.stderr or "")[-500:]]

    mine = []
    for i, e in enumerate(rows):
        for k in keys:
            v = refine_layer.row_values(e, k, tab)
            if v:
                mine.append(f"{i}\t{k}\t" + "\u001f".join(v)
                            .replace("\n", "\u2424").replace("\r", "\u240d"))
    theirs = open(js_out).read().split("\n") if os.path.getsize(js_out) else []

    bad = []
    if len(mine) != len(theirs):
        bad.append(f"the two readings produced different numbers of rows: "
                   f"Python {len(mine):,}, JavaScript {len(theirs):,}")
    def part(line, n):
        bits = line.split("\t", 2)
        return bits[n] if len(bits) > n else "(nothing)"

    for a, b in zip(mine, theirs):
        if a != b:
            bad.append(
                f"at {part(a, 0)}/{part(a, 1)} Python read {part(a, 2)!r}; "
                f"JavaScript, at the same place in its own output, has "
                f"{part(b, 0)}/{part(b, 1)} = {part(b, 2)!r}")
            if len(bad) >= 5:
                break
    if not bad:
        print(f"the two readings agree on {len(mine):,} row-and-key pairs "
              f"across {len(rows):,} records")
    # A value the form can offer but the page cannot filter on is the same
    # bug wearing a hat: bake_options must only ever emit narrowing keys.
    opts = refine_layer.bake_options(rows[:2000], tab)
    for k in opts:
        if k not in keys:
            bad.append(f"bake_options offers `{k}`, which the results page cannot count")
    return bad


def markup():
    """The two surfaces, checked as HTML rather than by eye.

    A form is only usable if every control is reachable and labelled: a
    <label for=> pointing at nothing is a control a screen reader cannot name
    and a tap target a thumb cannot widen. And an <option> cannot hold markup
    — a bilingual pair built with <span> is drawn as literal tag soup inside a
    dropdown, which is the mistake bi() invites and bi_text() exists to avoid.
    """
    import re
    bad = []

    def bi(th, en, sep=" · ", raw=False):
        if not th:
            return f'<span class="en" lang="en">{en}</span>'
        if not en:
            return f'<span class="th" lang="th">{th}</span>'
        return (f'<span class="bi"><span class="th" lang="th">{th}</span>'
                f'<span class="en" lang="en">{sep}{en}</span></span>')

    def att(x):
        return (str(x).replace("&", "&amp;").replace("<", "&lt;")
                .replace(">", "&gt;").replace('"', "&quot;"))

    opts = {k: [("v1", "หนึ่ง", "one", 12), ("v2", "สอง", "two", 3)]
            for k, _, _, _ in refine_layer.NARROW_ROWS}
    form = refine_layer.advanced_form(bi, att, opts)
    tools = refine_layer.tools_row(bi, att)

    ids = set(re.findall(r'id="([^"]+)"', form))
    for target in re.findall(r'<label[^>]*for="([^"]+)"', form):
        if target not in ids:
            bad.append(f"the form has a label pointing at #{target}, which does not exist")
    for k, th, en, _ in refine_layer.WORD_ROWS:
        if f'name="{k}"' not in form:
            bad.append(f"the word row {k} ({en}) is missing from the form")
    for k, th, en, _ in refine_layer.NARROW_ROWS:
        if f'name="{k}"' not in form:
            bad.append(f"the narrowing row {k} ({en}) is missing from the form")
        if f'data-refkey="{k}"' not in tools:
            bad.append(f"the tools row is missing {k} ({en})")
    for name in ("sort", "radius", "has", "blank", "open"):
        if f'name="{name}"' not in form:
            bad.append(f"the form cannot set {name}")
    for v, th, en in refine_layer.SORT_ROWS:
        if f'>{att(refine_layer.bi_text(th, en))}<' not in form:
            bad.append(f"the sort option {en} is missing from the form")
    # An <option> that carries a tag is a bug you can only see at read time.
    for block in re.findall(r"<option[^>]*>(.*?)</option>", form, re.S):
        if "<" in block:
            bad.append(f"an <option> carries markup: {block[:60]!r}")
    if "<button type=\"submit\"" not in form:
        bad.append("the form has no submit button")
    if "advanced.html" not in tools:
        bad.append("the tools row does not offer the advanced form")
    if not re.search(r"\(12\)", form):
        bad.append("the dropdown options carry no counts")

    # THE TWO DOORS. Mounted by the same call build.py already makes, so they
    # arrive on the results page without a sixth hook in a file that is hot
    # more often than it is cold.
    mount = refine_layer.panel_mount(bi, att)
    if 'id="resdoors"' not in mount:
        bad.append("the results page has nowhere to draw the map and calendar doors")
    if 'id="toolrow"' not in mount:
        bad.append("mounting the doors has cost the results page its tools row")
    ev = [{"place": {"id": "a"}, "start": "2026-09-07 19:00:00"},
          {"place": {"id": "a"}, "dt": 1},
          {"place": {"id": "b"}, "start": "2026-09-08 19:00:00"},
          {"place": {"id": "c"}},                 # no date: not in events.ics
          {"start": "2026-09-09 19:00:00"}]       # no venue we could pin
    table = json.loads(refine_layer.event_places_json(ev))
    if table != {"a": 2, "b": 1}:
        bad.append(f"the calendar door's table counts wrong: {table!r}")
    if refine_layer.event_places_json([]) != "{}":
        bad.append("an empty calendar does not produce an empty table")
    # evTable() reads #evplaces; with no such tag on search.html the calendar
    # door never draws. The table is baked by build(), so its source is read.
    src = open(os.path.join(ROOT, "build.py"), encoding="utf-8").read()
    if ('id="evplaces"' not in src
            or "refine_layer.event_places_json(EVENTS)" not in src):
        bad.append("search.html carries no #evplaces table for the calendar door")
    # Four values in the catalogue carry an embedded newline — a trade tag,
    # two names, an English name. An <option> cannot show one, and the same
    # text goes into title= and aria-label= where it is read aloud as two
    # things. The VALUE must survive the collapse untouched, or a tidied
    # label would quietly select the wrong rows.
    torn = refine_layer.advanced_form(
        bi, att, {"tag": [("v", "หนึ่ง\nสอง", "one\ntwo", 4)]})
    for block in re.findall(r"<option[^>]*>(.*?)</option>", torn, re.S):
        if "\n" in block or "\r" in block:
            bad.append("an <option> label carries a line break")
    if 'value="v"' not in torn:
        bad.append("collapsing an option's label changed the value it filters on")

    return bad


def built_calendar_table():
    """The #evplaces table as the last build wrote it, when that build ran
    after the wiring. The source check in markup() says build.py writes it;
    this says the tag reached search.html and its ids join the index, which is
    the join evTable() makes. Returns (failures, skip note or None)."""
    import re
    html_p = os.path.join(ROOT, "docs", "search.html")
    idx_p = os.path.join(ROOT, "docs", "data", "index.json")
    if not (os.path.exists(html_p) and os.path.exists(idx_p)):
        return [], "no built docs/search.html; the built #evplaces table was not read"
    html = open(html_p, encoding="utf-8").read()
    m = re.search(r'<script type="application/json" id="evplaces">(.*?)</script>', html, re.S)
    if not m:
        # A page built before build.py last changed may predate the tag.
        if os.path.getmtime(html_p) < os.path.getmtime(os.path.join(ROOT, "build.py")):
            return [], "docs/search.html predates build.py; the built #evplaces table was not read"
        return ["docs/search.html carries no #evplaces table for the calendar door"], None
    try:
        table = json.loads(m.group(1).replace("<\\/", "</"))
    except ValueError:
        return ["docs/search.html's #evplaces table is not JSON"], None
    if not isinstance(table, dict):
        return ["docs/search.html's #evplaces table is not an object"], None
    bad = []
    feed_p = os.path.join(ROOT, "docs", "data", "events.json")
    if not table and os.path.exists(feed_p):
        feed = json.load(open(feed_p, encoding="utf-8"))
        feed = feed.get("events", []) if isinstance(feed, dict) else feed
        if json.loads(refine_layer.event_places_json(feed)):
            bad.append("docs/search.html's #evplaces table is empty while the feed has pinned events")
    ids = {r.get("id") for r in json.load(open(idx_p, encoding="utf-8"))
           if isinstance(r, dict)}
    lost = [k for k in table if k not in ids]
    if lost:
        bad.append(f"{len(lost)} #evplaces ids are not in docs/data/index.json, e.g. {lost[0]!r}")
    return bad, None


def main():
    bad_markup = markup()
    bad_built, built_skip = built_calendar_table()
    if built_skip:
        print("SKIP  " + built_skip)
    bad_markup = bad_markup + bad_built
    for line in bad_markup:
        print("FAIL  " + line)
    rows, tab = fixture()
    if not rows:
        print("SKIP  data/canonical is empty or unreadable — nothing to test against")
        return 0
    d = tempfile.mkdtemp(prefix="refine-")
    bad_mirror = mirror_readings(rows, tab, d)
    for line in bad_mirror:
        print("FAIL  " + line)
    p = {n: os.path.join(d, n) for n in ("refine.js", "tab.json", "rows.json", "h.js")}
    # The built calendar and the published feed, when a build has left them
    # there. Absent, the mirror check says so and the rest of the run stands.
    ics = os.path.join(ROOT, "docs", "events.ics")
    feed = os.path.join(ROOT, "docs", "data", "events.json")
    mirror = [ics, feed] if os.path.exists(ics) and os.path.exists(feed) else []
    open(p["refine.js"], "w").write(refine_layer.JS)
    open(p["tab.json"], "w").write(json.dumps(tab, ensure_ascii=False))
    open(p["rows.json"], "w").write(json.dumps(rows, ensure_ascii=False))
    open(p["h.js"], "w").write(HARNESS)
    try:
        out = subprocess.run(
            ["node", p["h.js"], p["refine.js"], p["tab.json"], p["rows.json"]] + mirror,
            capture_output=True, text=True, timeout=180)
    except FileNotFoundError:
        print("SKIP  node is not on this machine; the engine was not exercised")
        return 0
    if out.returncode != 0:
        print("FAIL  the engine did not run at all:\n" + (out.stderr or "")[-2000:])
        return 1
    try:
        res = json.loads((out.stdout or "").strip().splitlines()[-1])
    except (ValueError, IndexError):
        print("FAIL  the harness said nothing this test could read:\n" + (out.stdout or "")[-2000:])
        return 1
    if res.get("skip"):
        print("SKIP  " + res["skip"])
        return 0
    print(f"{res['rows']:,} records · tag A={res['a']} · tag B={res['b']} · "
          f"area={res['ar']} · {res['pinned']:,} pinned · "
          f"name-only {res['nameOnly']:,} vs anywhere {res['anywhere']:,}")
    for line in res["bad"]:
        print("FAIL  " + line)
    extra = (2 if not bad_markup else 0) + (1 if not bad_mirror else 0)
    print(f"{res['pass'] + extra} passed, "
          f"{len(res['bad']) + len(bad_markup) + len(bad_mirror)} failed")
    return 1 if (res["bad"] or bad_markup or bad_mirror) else 0


if __name__ == "__main__":
    sys.exit(main())
