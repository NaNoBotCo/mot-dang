#!/usr/bin/env python3
"""WO-69 / WO-71 — wire THE CARD into build.py, by anchor text, idempotently.

    python3 importers/apply_card_hook.py --check   # say what would change
    python3 importers/apply_card_hook.py           # apply

WHY A SCRIPT. build.py is edited by several sessions a day (its mtime was four
minutes old when this was written, and a build was running). A line-number
diff rots before it is applied; each edit below finds its anchor by TEXT,
refuses if the anchor is missing or matches twice, and is skipped when its
result is already in place. Run it in a quiet minute, then a scratch build.

WHAT IT WIRES (Michael, 2026-09-07: "if I see something I like on the list of
results, I want map controls, links to related (nearby / near-time) things,
interactivity, and relationships. All items should carry relational tags, and
discovery should EXPLICITLY allow finding by tags. Fewer words.")

  A. the index carries the relations: `t` tags, `tt` trade tags, `st` street,
     `ar` tambon/amphoe, `hk` opening schedule (replaces the unread `h`),
     each as an int into docs/data/search_tables.json.
  B. search.html: filter params (tag= sub= cat= st= ar= near=), a tag typed
     in the box lifted into a filter, a result CARD with chips, a lamp, a
     distance and a 📍, an in-place panel (mini map, three nearest, same
     kind nearby, events, add to plan), a lazy results map, a where-answer
     that folds everything past the third row, and the instructional
     sentences cut.
  C. the place page: our own map linked, the road row without its sentence,
     "more like this" ranked by distance, the three ways to wander, the
     reach hint and the event caveat gone, the trade tags linking to the
     tag filter.
"""
import os
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
BUILD = ROOT / "build.py"

# (name, anchor text that must appear exactly once, replacement, presence marker)
HOOKS = []


def hook(name, old, new, marker=None):
    # the presence marker is the head of the replacement — long enough that
    # no two hooks share it and no anchor is its own marker
    HOOKS.append((name, old, new, marker or new[:90]))


# ===========================================================================
# A. THE INDEX
# ===========================================================================
hook("search_tables() helper",
     "def search_start_html(pdoc):",
     '''def search_tables(data, T):
    """WO-69 — the tables a result card reads its chips from, and the id maps
    the index rows point into.

    Every relation a row carries is an INT into one of these lists — a tag
    slug repeated 7,820 times costs 197 KB, the same tags as ints cost 100 KB
    and the table 1.7 KB. Fetched only by search.html, beside the thesaurus.

      tags     [[slug, th, en, glyph], …]   the derived tags (tags_layer)
      trade    [[th, glossEn, reading], …]  attrs.tradeTags, the lexicon's words
      streets  [[slug, name, nameEn], …]    data/streets.json
      areas    [[tambon, amphoe, prov, reading], …]
      subs     {key: [th, en]}              one-language chip labels
      hours    [[[start, end], …], …]       open_lamps schedules, for the lamp
    """
    tags_rows, tag_id = [], {}
    for slug in (T or {}).get("order") or []:
        d = (T or {}).get("defs", {}).get(slug)
        if not d:
            continue
        tag_id[slug] = len(tags_rows)
        tags_rows.append([slug, d.get("th", ""), d.get("en", ""), d.get("glyph", "")])
    trade_rows, trade_id = [], {}
    for th, e in TRADE_LEX.items():
        if not isinstance(e, dict):
            continue
        trade_id[th] = len(trade_rows)
        trade_rows.append([th, e.get("gloss") or "", "" if e.get("suspect") else (e.get("reading") or "")])
    streets_rows, street_id = [], {}
    for s in STREETS:
        street_id[s["slug"]] = len(streets_rows)
        streets_rows.append([s["slug"], s.get("name") or "", s.get("nameEn") or ""])
    areas_rows, area_id = [], {}
    for prov, recs in data.items():
        for r in recs:
            al = r.get("attrs") or {}
            tb, am = str(al.get("tambon") or "").strip(), str(al.get("amphoe") or "").strip()
            if not (tb or am):
                continue
            k = (tb, am, prov)
            if k not in area_id:
                area_id[k] = len(areas_rows)
                areas_rows.append([tb, am, prov, lex_reading(tb or am, AREA_LEX)])
    subs = {k: [v.get("th", ""), v.get("en", "")] for k, v in SUB_LABELS.items()}
    hours_rows, hours_k = [], {}
    lamps_path = ROOT / "data" / "open_lamps.json"
    if lamps_path.exists():
        try:
            lamps = json.loads(lamps_path.read_text())
            hours_rows = lamps.get("schedules") or []
            hours_k = {p["id"]: p["k"] for p in (lamps.get("places") or [])
                       if isinstance(p, dict) and "id" in p and "k" in p}
        except (OSError, ValueError):
            pass
    tables = {"tags": tags_rows, "trade": trade_rows, "streets": streets_rows,
              "areas": areas_rows, "subs": subs, "hours": hours_rows}
    ids = {"tag": tag_id, "trade": trade_id, "street": street_id,
           "area": area_id, "hours": hours_k}
    return tables, ids


def search_start_html(pdoc):''')

hook("tables built before the province loop",
     '''    home_sections = []
    search_index = []
    held_names = []''',
     '''    home_sections = []
    search_index = []
    # WO-69 — the card's tables and id maps, once, before any row is written
    _SEARCH_TABLES, _SI = search_tables(data, globals().get("TAGS"))
    held_names = []''')

hook("index row: t / tt / st / ar",
     '''            if r.get("sub"):
                idx_entry["su"] = r["sub"]
            _k = []''',
     '''            if r.get("sub"):
                idx_entry["su"] = r["sub"]
            # WO-69 — THE RELATIONS A ROW CARRIES, as ints into
            # docs/data/search_tables.json. Tags and trade tags are what a
            # card's chip shows and what `tag=` filters on; the street or the
            # district is the second chip; the schedule index lights the lamp.
            _ti = [_SI["tag"][x] for x in _tags_layer.index_tags(globals(), r)
                   if x in _SI["tag"]]
            if _ti:
                idx_entry["t"] = _ti
            _tti, _tseen = [], set()
            for _t in (_al.get("tradeTags") or []):
                _t = _t.strip() if isinstance(_t, str) else ""
                if _t and _t not in _tseen and _t in _SI["trade"]:
                    _tseen.add(_t)
                    _tti.append(_SI["trade"][_t])
            if _tti:
                idx_entry["tt"] = _tti[:6]
            _st0 = STREET_OF.get(r["id"])
            if _st0 and _st0[0].get("slug") in _SI["street"]:
                idx_entry["st"] = _SI["street"][_st0[0]["slug"]]
            _ak = (str(_al.get("tambon") or "").strip(), str(_al.get("amphoe") or "").strip(), key)
            if (_ak[0] or _ak[1]) and _ak in _SI["area"]:
                idx_entry["ar"] = _SI["area"][_ak]
            _hk = _SI["hours"].get(r["id"])
            if _hk is not None:
                idx_entry["hk"] = _hk
            _k = []''')

hook("index row: hk replaces h",
     '''            if r.get("hours"):
                idx_entry["h"] = r["hours"]
''',
     '''            # `h` (the raw opening_hours string) was written here from
            # 2026-09-05 and read by nothing — 107 KB. `hk` above replaces it.
''')

hook("search_tables.json written beside index.json",
     '''    (DOCS / "data" / "index.json").write_text(
        json.dumps(search_index, ensure_ascii=False))
''',
     '''    (DOCS / "data" / "index.json").write_text(
        json.dumps(search_index, ensure_ascii=False))
    (DOCS / "data" / "search_tables.json").write_text(
        json.dumps(_SEARCH_TABLES, ensure_ascii=False))
''')

# ===========================================================================
# B. SEARCH.HTML — the served page
# ===========================================================================
hook("search.html body: controls, results map, map head",
     '''    (DOCS / "search.html").write_text(page(
        "ค้นหา",
        f'<h1>{bi("ผลการค้นหา", "Search results")} <span class="count" id="rescount"></span>'
        f'<span class="count resqual" id="resqual"></span></h1>'
        f'<ul class="dir" id="results">{search_start_html(_pdoc)}</ul>',
        depth=0, path="search.html", desc="ค้นหาในมดแดง"))''',
     '''    # WO-69. The results map is a box with NO data-mdmap attribute: page()
    # injects the ~1 MB MapLibre head whenever it sees one, and a search must
    # not pay for a map nobody asked for. The four files it would need are
    # baked as a JSON list; md.js loads them on the first tap of 🗺 or 📍.
    _maphead = json.dumps(_map_shell.head_urls(0)) if _map_shell.enabled() else "[]"
    (DOCS / "search.html").write_text(page(
        "ค้นหา",
        f'<h1>{bi("ผลการค้นหา", "Search results")} <span class="count" id="rescount"></span>'
        f'<span class="count resqual" id="resqual"></span>'
        f'<span class="rsctl"><button type="button" id="resmapbtn" aria-label="แผนที่ · map" hidden>🗺</button>'
        f'<button type="button" id="resnear" aria-label="ใกล้ฉัน · near me" hidden>📍</button></span></h1>'
        f'<div id="resmap" class="mdmap resmap" data-lat="18.78760" data-lng="98.99310" data-zoom="13" hidden>'
        f'<div class="mdmap-draw"></div></div>'
        f'<script type="application/json" id="maphead">{_maphead}</script>'
        f'<ul class="dir" id="results">{search_start_html(_pdoc)}</ul>',
        depth=0, path="search.html", desc="ค้นหาในมดแดง"))''')

hook("empty search page: doors, no lede",
     '''    return (
        '<li class="richdoor">'
        f'<p class="rdhead">🐜 <b>{bi("ลองคำพวกนี้ดูก่อนก็ได้", "Try one of these")}</b></p>'
        f'<p class="rdlead">{bi("พิมพ์ชื่อร้าน ชื่อวัด ชื่อคลินิก หรือชื่อถนนก็ได้ ไทยหรืออังกฤษ สะกดไม่ตรงเป๊ะมดก็เดาให้", "Type a shop, a wat, a clinic, or a road — Thai or English, and the spelling need not be perfect.")}</p>'
        + (f'<p class="rddoors">{" ".join(pills)}</p>' if pills else "")
        + f'<p class="rddelight">{bi("ยังไม่รู้ว่ามดแดงคืออะไร", "Not sure what this place is yet?")} '
        f'<a href="what.html">{bi("เริ่มตรงนี้", "start here")}</a></p></li>'
        f'<li class="shelf">{bi("หรือเดินเข้าทางชั้นเลย", "or walk in through a shelf")}</li>'
        + shelves)''',
     '''    # WO-69 (Michael, 2026-09-07: "if you need to explain something using
    # words, you're fucking up"). The lede, the "try one of these", the
    # "not sure what this is? start here" and "or walk in through a shelf"
    # all came off. The doors and the shelves are the page.
    return (
        '<li class="richdoor">'
        + (f'<p class="rddoors">{" ".join(pills)}</p>' if pills else "")
        + '</li>'
        + shelves)''')

# ===========================================================================
# B. SEARCH JS — pipeline
# ===========================================================================
hook("F: the filters, read beside q",
     '''const q=new URLSearchParams(location.search).get('q')||'';
document.querySelector('form.seek input').value=q;''',
     '''const q=new URLSearchParams(location.search).get('q')||'';
// WO-69 — THE FILTERS. tag= sub= cat= st= ar= narrow; near=lat,lng is a point
// to measure from. Read here, beside q, so the pipeline block below stays
// free of the DOM and the two test harnesses can hand it an F of their own.
const QS=location.search;
const F=(()=>{const u=new URLSearchParams(QS);
const list=k=>(u.get(k)||'').split(',').map(s=>s.trim()).filter(Boolean);
const nr=(u.get('near')||'').split(',').map(Number);
const f={tag:list('tag'),sub:list('sub'),cat:list('cat'),st:list('st'),ar:list('ar'),
near:(nr.length===2&&nr.every(isFinite))?{lat:nr[0],lng:nr[1]}:null};
f.any=!!(f.tag.length||f.sub.length||f.cat.length||f.st.length||f.ar.length||f.near);
return f;})();
document.querySelector('form.seek input').value=q;''')

hook("the guard admits a filter with no words",
     '''if(!q)return;
// The two shortcut rows''',
     '''if(!q&&!F.any)return;
// The two shortcut rows''')

hook("the tables are fetched with the thesaurus",
     '''const [thesDoc,segText,shelfDoc,panelDoc,lmDoc]=await Promise.all([
mdJSON('data/search_thesaurus.json'),
fetch(RROOT+'data/search_segdict.txt').then(r=>r.ok?r.text():'').catch(()=>''),
mdJSON('data/search_shelves.json'),
mdJSON('data/search_panels.json'),
mdJSON('data/search_landmarks.json')]);''',
     '''const [thesDoc,segText,shelfDoc,panelDoc,lmDoc,tabDoc]=await Promise.all([
mdJSON('data/search_thesaurus.json'),
fetch(RROOT+'data/search_segdict.txt').then(r=>r.ok?r.text():'').catch(()=>''),
mdJSON('data/search_shelves.json'),
mdJSON('data/search_panels.json'),
mdJSON('data/search_landmarks.json'),
mdJSON('data/search_tables.json')]);
// WO-69 — the card's tables: tag / trade / street / area names and the
// opening schedules, each row an int in the index (see search_tables()).
const TAB=Object.assign({tags:[],trade:[],streets:[],areas:[],subs:{},hours:[]},tabDoc||{});
globalThis.MD_TAB=TAB;''')

hook("the index is shared with the card wiring",
     '''const idx=await loadIndex();
// Searching used to mean typing the name exactly''',
     '''const idx=await loadIndex();
globalThis.MD_IDX=idx;   // the card panel's "three nearest" reads it (wiring below the render block)
// Searching used to mean typing the name exactly''')

hook("the tag lift, before analysis",
     '''if(left)qFor=left;}}
let an=core.analyze(qFor,index);
let found=an.terms.length?index.search(an,0):[];''',
     '''if(left)qFor=left;}}
// WO-69 — A TAG IS A FILTER, NOT A WORD (Michael: "discovery should
// EXPLICITLY allow searching/finding by tags"). Three routes, in order:
//   1. tag= in the URL, and #word in the box — always a filter, cut from
//      the words like the landmark above;
//   2. a constraint searchcore already lifted (vegan, wifi, wheelchair,
//      delivery, open late) — mapped onto its tag below, once `an` exists;
//   3. a bare word that IS a tag's name (pizza, japanese, bitcoin, old city,
//      michelin) — a filter only when the filtered set is not empty.
// Routes 2 and 3 are SOFT: never to nothing. Route 1 is what the reader
// asked for by name and may honestly answer zero.
const TAGKEY={};
TAB.tags.forEach((t,i)=>{[t[0],t[1],t[2]].forEach(nm=>{const k=SEARCHCORE.norm(nm||'');if(k&&!TAGKEY[k])TAGKEY[k]={t:i};});});
TAB.trade.forEach((t,i)=>{const k=SEARCHCORE.norm(t[0]||'');if(k&&!TAGKEY[k])TAGKEY[k]={tt:i};});
const resolveTag=v=>{const k=SEARCHCORE.norm(v||'');if(!k)return null;
if(TAGKEY[k])return Object.assign({},TAGKEY[k]);
const ti=TAB.tags.findIndex(t=>t[0]===v);if(ti>=0)return {t:ti};
const si=TAB.trade.findIndex(t=>t[0]===v);if(si>=0)return {tt:si};return null;};
const FT=[];
const pushTag=x=>{if(x&&!FT.some(y=>y.t===x.t&&y.tt===x.tt&&y.none===x.none))FT.push(x);};
// a tag asked for BY NAME that no table knows is a hard filter nothing meets:
// zero rows, the chip struck through — never the whole catalogue
for(const v of F.tag)pushTag(resolveTag(v)||{none:v});
qFor=qFor.replace(/(^|\\s)#([^\\s#]+)/g,(m,a,w)=>{const r=resolveTag(w);if(r){pushTag(r);return a;}return m;}).replace(/\\s+/g,' ').trim();
// No words left and a filter in hand: the filter IS the query. Every row
// stands as an exact hit and the filter step below narrows it.
let an,found;
if(!qFor&&(F.any||FT.length)){an={terms:[],intent:{filters:{},phrases:[]},notes:[]};
found=idx.map(e=>({doc:e,score:0,tier:'exact',coverage:1}));}
else{an=core.analyze(qFor,index);found=an.terms.length?index.search(an,0):[];}
for(const t of an.terms){let hit=null;
for(const v of [t.raw].concat(t.variants||[])){const r=TAGKEY[SEARCHCORE.norm(v)];if(r&&r.t!=null){hit=r;break;}}
if(hit)pushTag({t:hit.t,soft:true,word:t.raw});}''')

hook("route 2: lifted constraints become tag filters",
     '''const IFILT=an.intent.filters||{};
const ivals=k=>[].concat(IFILT[k]||[]);
if(ivals('access').indexOf('parking')!==-1)wantShelves.add('parking');''',
     '''const IFILT=an.intent.filters||{};
const ivals=k=>[].concat(IFILT[k]||[]);
if(ivals('access').indexOf('parking')!==-1)wantShelves.add('parking');
const TAGOF={diet:{vegetarian:'vegetarian',vegan:'vegan',halal:'halal'},access:{wheelchair:'wheelchair'},
wifi:{yes:'wifi'},delivery:{yes:'delivery'},open:{late:'open-late'}};
for(const k in TAGOF)for(const v of ivals(k)){const slug=TAGOF[k][v];if(!slug)continue;
const ti=TAB.tags.findIndex(t=>t[0]===slug);if(ti>=0)pushTag({t:ti,soft:true,word:v});}''')

hook("the filter step, before the coverage step",
     '''const whole=found.filter(r=>r.coverage>=1);
if(whole.length)found=whole;''',
     '''// WO-69 — THE FILTER STEP. A filter narrows; a mined shelf word only lifts
// (WO-68's rule). Applied BEFORE the loosen-by-steps below, so the tiers are
// settled over the rows that survive it, not over rows it was about to drop.
const FSUB=new Set(F.sub),FCAT=new Set(F.cat),FST=new Set(F.st),FAR=new Set(F.ar);
const arIdx=new Set();TAB.areas.forEach((a,i)=>{if(FAR.has(a[0])||FAR.has(a[1]))arIdx.add(i);});
const stIdx=new Set();TAB.streets.forEach((s,i)=>{if(FST.has(s[0]))stIdx.add(i);});
const hardTags=FT.filter(x=>!x.soft),softTags=FT.filter(x=>x.soft);
const hasTag=(e,x)=>x.none!=null?false:(x.t!=null?(e.t||[]).indexOf(x.t)!==-1:(e.tt||[]).indexOf(x.tt)!==-1);
const pass=e=>(!FSUB.size||(e.su||[]).some(s=>FSUB.has(s)))&&(!FCAT.size||(e.c||[]).some(c=>FCAT.has(c)))
&&(!stIdx.size||stIdx.has(e.st))&&(!arIdx.size||arIdx.has(e.ar))&&hardTags.every(x=>hasTag(e,x));
const HARD=!!(FSUB.size||FCAT.size||stIdx.size||arIdx.size||hardTags.length);
if(HARD)found=found.filter(r=>pass(r.doc));
for(const x of softTags){const f2=found.filter(r=>hasTag(r.doc,x));if(f2.length)found=f2;else x.dropped=true;}
const whole=found.filter(r=>r.coverage>=1);
if(whole.length)found=whole;''')

hook("the point P: a landmark, or near=",
     '''if(lm){const TIERS={exact:0,thesaurus:1,loose:2,partial:3};
for(const r of found){const e=r.doc;
r.m=(e.lat==null||e.lng==null)?null:distM(lm.lat,lm.lng,e.lat,e.lng);}''',
     '''// The point everything is measured from: the landmark the reader named, or
// the near= the page was opened with. One point, whichever was given.
const P=lm?{lat:lm.lat,lng:lm.lng,id:lm.id,th:lm.th,en:lm.en}:(F.near?{lat:F.near.lat,lng:F.near.lng}:null);
if(P){const TIERS={exact:0,thesaurus:1,loose:2,partial:3};
for(const r of found){const e=r.doc;
r.m=(e.lat==null||e.lng==null)?null:distM(P.lat,P.lng,e.lat,e.lng);}''')

hook("P hoists its own record",
     '''if(lm.id){const i=found.findIndex(r=>r.doc.id===lm.id);
if(i>0)found.unshift(found.splice(i,1)[0]);}}''',
     '''if(P.id){const i=found.findIndex(r=>r.doc.id===P.id);
if(i>0)found.unshift(found.splice(i,1)[0]);}}''')

hook("HITM from P",
     '''const HITM={};if(lm)for(const r of found.slice(0,200))HITM[r.doc.id]=r.m;''',
     '''const HITM={};if(P)for(const r of found.slice(0,200))HITM[r.doc.id]=r.m;''')

hook("WO-70: the rare word is the question",
     '''if(whole.length)found=whole;
// A STATED CONSTRAINT NARROWS; A SHELF WORD ONLY LIFTS.''',
     '''if(whole.length)found=whole;
// WO-70 — THE RARE WORD IS THE QUESTION (Michael, "best place to buy a
// Martin guitar": `buy` matched 261 rows, `martin` 4, `guitar` 4; every row
// had matched one word, all tied on coverage, and Guitar House came ~230th
// behind the cafés that matched "buy"). When no row matched every word, a
// word that matches four rows says more about what was wanted than one that
// matches two hundred — so the partial pile is ranked by the rarity of what
// each row matched, Σ log(N/df), and the matcher's own score breaks ties.
// Rows that matched every word are not touched.
if(found.length&&found[0].coverage<1&&an.terms.length>1){
const N=idx.length||1,DID=new Map(index.docs.map((d,i)=>[d,i]));
const DF=an.terms.map(t=>{const ids=new Set();for(const [nm] of index.fields){for(const d of index._resolve(t,nm,0).keys())ids.add(d);}
return {ids:ids,w:Math.log((N+1)/(ids.size+1))};});
for(const r of found){let s=0;const d=DID.get(r.doc);for(const f of DF)if(f.ids.has(d))s+=f.w;r.rare=s;}
found.sort((a,b)=>(b.rare-a.rare)||(b.score-a.score));}
// A STATED CONSTRAINT NARROWS; A SHELF WORD ONLY LIFTS.''')

# ===========================================================================
# B. SEARCH JS — render
# ===========================================================================
hook("the count counts a filter-only search too",
     '''document.getElementById('rescount').textContent=q?`${found.length}`:'';''',
     '''document.getElementById('rescount').textContent=(q||F.any)?`${found.length}`:'';''')

hook("status sentences become chips",
     '''const more=found.length>hits.length
?`<li class="shelf">${say('พิมพ์ให้เจาะจงขึ้นเพื่อแคบลง','add a word to narrow it')}</li>`:'';
const says=[];
const words=()=>an.terms.map(t=>t.raw).join(' + ');''',
     '''// WO-69: "add a word to narrow it" came off — the count already says.
const more='';
// WO-69 — HOW THE SEARCH READ YOU, AS CHIPS, NOT SENTENCES. A mended or
// loosened spelling is "≈ word"; a Thai query cut into words is the words;
// a search where no row matched everything is each word with its own count;
// a size or a constraint the page could not use is the word struck through;
// the landmark or the point everything is measured from is 📍 and its name.
// (Michael, 2026-09-07: "if you need to explain something using words,
// you're fucking up".) `says` holds chip HTML; `note` renders them in one
// row. The old sentences are gone, not hidden.
const hx=s=>String(s==null?'':s).replace(/[&<>"]/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;'}[c]));
const says=[];
const words=()=>an.terms.map(t=>t.raw).join(' + ');''')

hook("chip: mended / segmented / loose / landmark",
     '''if(an.notes.indexOf('mended')>=0)says.push(['สะกดใกล้เคียง — น่าจะหมายถึงคำนี้','near spelling — this looks like the word you meant']);
if(an.notes.indexOf('segmented')>=0)says.push(['แยกคำเป็น '+words(),'read as '+words()]);
if(worst==='loose')says.push(['สะกดใกล้เคียง — เรียงตามที่ใกล้ที่สุด','near spellings — closest first']);
// The landmark, and it goes FIRST because it decided the order of everything
// under it. A list silently sorted by distance is a list whose order the
// reader has to guess at.
if(lm)says.unshift(['วัดจาก'+lm.th+' — ใกล้ที่สุดก่อน',
'measured from '+(lm.en||lm.th)+' — nearest first']);''',
     '''if(an.notes.indexOf('mended')>=0||worst==='loose')says.push('≈ '+hx(an.terms.map(t=>t.raw).join(' ')));
if(an.notes.indexOf('segmented')>=0)says.push(an.terms.map(t=>hx(t.raw)).join(' + '));
// The point, and it goes FIRST because it decided the order of everything
// under it.
if(P)says.unshift('📍 '+(lm?mdBi(lm.th,lm.en||lm.th):''));''')

hook("chip: partial per-word counts",
     '''if(worst==='partial'){const per=an.terms.map(t=>{const ids=new Set();
for(const [nm] of index.fields){for(const d of index._resolve(t,nm,0).keys())ids.add(d);}
return t.raw+' '+ids.size;}).join(' · ');
says.push(['ไม่มีรายการที่ตรงทุกคำ ('+words()+') — แสดงที่ตรงบางคำ เรียงตามที่ตรงมากที่สุด: '+per,
'nothing matches all of '+words()+' — showing what matches some, most words first: '+per]);}
if(sizeDropped)says.push(['อ่าน "'+sizeDropped.join(' ')+'" ว่าเป็นไซส์ — ยังไม่มีร้านไหนในนี้บันทึกไซส์ไว้ จึงค้นจากคำที่เหลือ',
'read "'+sizeDropped.join(' ')+'" as a size — no listing here records sizes yet, so the search ran on the other words']);''',
     '''if(worst==='partial'){for(const t of an.terms){const ids=new Set();
for(const [nm] of index.fields){for(const d of index._resolve(t,nm,0).keys())ids.add(d);}
says.push(hx(t.raw)+' <span class="count">'+ids.size+'</span>');}}
if(sizeDropped)says.push('<s>'+hx(sizeDropped.join(' '))+'</s>');''')

hook("CANFILTER grows to every constraint the index answers",
     '''const CANFILTER={access:['parking']};''',
     '''const CANFILTER={access:['parking','wheelchair'],diet:['vegetarian','vegan','halal'],wifi:['yes'],delivery:['yes'],open:['late']};''')

hook("chip: constraints the page could not use; parking sentence gone",
     '''const asked=Object.keys(IFILT).filter(k=>!canFilter(k));
if(asked.length&&found.length){const ph=(an.intent.phrases||[]).join(', ');
for(const k of asked){const fs=FILTER_SAY[k];
says.push(fs?['อ่านคำขอ "'+ph+'" ได้ — '+fs[0],'understood "'+ph+'" — '+fs[1]]:
['อ่านคำขอ "'+ph+'" ได้ แต่หน้านี้ยังกรองตามนั้นไม่ได้ — ดูรายละเอียดในหน้าร้าน','understood "'+ph+'" — this page cannot filter on it yet; check the listing']);}}
// And when it CAN, it says what it did. A filter applied silently is as much
// of a guess to the reader as one dropped silently.
if(ivals('access').indexOf('parking')!==-1&&found.length)
says.push(['อ่านคำขอ "ที่จอดรถ" ได้ — ยกที่จอดรถขึ้นก่อน ที่เหลืออยู่ใต้หัวข้อชื่อพ้อง',
'understood "parking" — car parks first, everything else under the namesakes heading below']);
const note=says.map(s=>`<li class="shelf">${say(s[0],s[1])}</li>`).join('');''',
     '''const asked=Object.keys(IFILT).filter(k=>!canFilter(k));
if(asked.length&&found.length&&Object.keys(IFILT).every(k=>!canFilter(k)))
for(const ph of(an.intent.phrases||[]))says.push('<s>'+hx(ph)+'</s>');
const note=says.length?'<li class="shelf fbar rd">'+says.map(s=>'<span class="rchip">'+s+'</span>').join(' ')+'</li>':'';
// WO-69 — THE ACTIVE FILTERS, each a chip whose tap REMOVES it. No label.
const fbar=(()=>{const items=[];const u0=new URLSearchParams(QS);
const without=(k,v)=>{const u=new URLSearchParams(u0);const rest=(u.get(k)||'').split(',').filter(x=>x&&x!==v);
if(rest.length)u.set(k,rest.join(','));else u.delete(k);const s=u.toString();return RROOT+'search.html'+(s?'?'+s:'');};
for(const x of FT){const tg=x.t!=null?TAB.tags[x.t]:null,tr=x.tt!=null?TAB.trade[x.tt]:null;
const lab=tg?((tg[3]?tg[3]+' ':'')+mdBi(tg[1],tg[2])):hx(tr?tr[0]:(x.none||''));const val=tg?tg[0]:(tr?tr[0]:(x.none||''));
items.push('<a class="rchip on'+((x.dropped||x.none!=null)?' off':'')+'" href="'+without('tag',val)+'">'+lab+'</a>');}
for(const s of F.sub)items.push('<a class="rchip on" href="'+without('sub',s)+'">'+(TAB.subs[s]?mdBi(TAB.subs[s][0],TAB.subs[s][1]):hx(s))+'</a>');
for(const c of F.cat)items.push('<a class="rchip on" href="'+without('cat',c)+'">'+(MD_CATWORDS[c]||hx(c))+'</a>');
for(const s of F.st){const row=TAB.streets.find(x=>x[0]===s);items.push('<a class="rchip on" href="'+without('st',s)+'">'+(row?mdBi(row[1]||row[2],row[2]||row[1]):hx(s))+'</a>');}
for(const a of F.ar)items.push('<a class="rchip on" href="'+without('ar',a)+'">'+hx(a)+'</a>');
return items.length?'<li class="shelf fbar">'+items.join(' ')+'</li>':'';})();''')

hook("the card replaces the row",
     '''const dName=e=>(lm&&e.nm)?e.nm:e.n;
const dEn=e=>(lm&&e.em)?e.em:e.e;
const row=e=>`<li><a href="${RROOT}${e.p}/p/${e.s}.html">${dName(e)}</a>`+
`${dEn(e)&&dEn(e)!==dName(e)?' <span class="count">'+dEn(e)+'</span>':(e.r?' <span class="count roman">'+e.r+'</span>':'')}`+
`${lm&&HITM[e.id]!=null&&e.id!==lm.id?' <span class="count dist">· '+fmtM(HITM[e.id])+'</span>':''}`+
`${spanProv?' <span class="count">· '+e.pv+'</span>':''}`+
`${e.ob&&obAsked?' <span class="prov">'+(e.ob===2?mdBi('รพ.สต. — สถานีอนามัยประจำตำบล ฝากครรภ์และวางแผนครอบครัวเป็นงานประจำ','รพ.สต. — the local primary-care station; antenatal care and family planning are routine'):mdBi('โรงพยาบาลทั่วไป — ยังไม่ได้ยืนยันว่ามีแผนกสูตินรีเวช','general hospital — an OB-GYN department is not confirmed'))+'</span>':''}`+
`</li>`;''',
     '''const dName=e=>(lm&&e.nm)?e.nm:e.n;
const dEn=e=>(lm&&e.em)?e.em:e.e;
// WO-69 — THE CARD (Michael, 2026-09-07). A result is a place, not a link:
// its name, the reading or the English, the metres when a point is known,
// a lamp when we hold a schedule (lit = open now; unlit = closed now; none =
// nobody has recorded hours, which is not "closed"), up to three chips —
// the sub-shelf, the street or the district or the nearest landmark, the
// best tag — every chip a filter, and a 📍. The body opens in place (the
// wiring below the render marker): a mini map, the three nearest places we
// hold, the same kind nearby, what is on here, add to plan.
const WMIN=(()=>{const d=new Date();return ((d.getDay()+6)%7)*1440+d.getHours()*60+d.getMinutes();})();
const openNow=e=>{if(e.hk==null)return null;const sch=TAB.hours[e.hk];if(!sch)return null;
return sch.some(iv=>WMIN>=iv[0]&&WMIN<iv[1]);};
const nearLm=e=>{let b=null,bd=1500;for(const l of LMS){if(l.lat==null||l.lng==null)continue;
const d=distM(e.lat,e.lng,l.lat,l.lng);if(d<bd){bd=d;b=l;}}return b;};
// WHAT THIS PLACE IS, WHERE IT IS, WHAT ELSE IT IS — in that order, and
// every one of them a filter the reader can tap. The last is the shelf the
// sub-shelf hangs off, so a record with nothing but a name and a shelf still
// carries two: a guitar shop in Chiang Rai with no street, no tambon and no
// landmark within 1.5 km was showing one chip and reading like a bare link.
const chipsOf=e=>{const out=[];
const su=(e.su||[])[0];
if(su&&TAB.subs[su])out.push(['?sub='+encodeURIComponent(su),mdBi(TAB.subs[su][0],TAB.subs[su][1])]);
if(e.st!=null&&TAB.streets[e.st]){const s=TAB.streets[e.st];out.push(['?st='+encodeURIComponent(s[0]),mdBi(s[1]||s[2],s[2]||s[1])]);}
else if(e.ar!=null&&TAB.areas[e.ar]){const a=TAB.areas[e.ar];const nm=a[0]||a[1];out.push(['?ar='+encodeURIComponent(nm),mdBi(nm,a[3]||nm)]);}
else if(e.lat!=null){const nl=nearLm(e);if(nl)out.push(['?q='+encodeURIComponent(q)+'&near='+nl.lat+','+nl.lng,'📍 '+mdBi(nl.th,nl.en||nl.th)]);}
if(e.t&&e.t.length&&TAB.tags[e.t[0]]){const t=TAB.tags[e.t[0]];out.push(['?tag='+encodeURIComponent(t[0]),(t[3]?t[3]+' ':'')+mdBi(t[1],t[2])]);}
else if(e.tt&&e.tt.length&&TAB.trade[e.tt[0]]){const t=TAB.trade[e.tt[0]];out.push(['?tag='+encodeURIComponent(t[0]),hx(t[0])+(t[2]?' <span class="en roman">'+hx(t[2])+'</span>':'')]);}
if(e.c&&e.c[0]&&MD_CATWORDS[e.c[0]]&&!(su&&TAB.subs[su]&&out.length>=3))out.push(['?cat='+encodeURIComponent(e.c[0]),MD_CATWORDS[e.c[0]]]);
return out.slice(0,3);};
const row=e=>{const ch=chipsOf(e),on=openNow(e);
return `<li class="rcard" data-id="${hx(e.id)}"${e.lat!=null?` data-lat="${e.lat}" data-lng="${e.lng}"`:''} data-plan="${hx(e.p+':'+e.s)}">`+
`<a class="rname" href="${RROOT}${e.p}/p/${e.s}.html">${hx(dName(e))}</a>`+
`${dEn(e)&&dEn(e)!==dName(e)?' <span class="count">'+hx(dEn(e))+'</span>':(e.r?' <span class="count roman">'+hx(e.r)+'</span>':'')}`+
`${P&&HITM[e.id]!=null&&e.id!==P.id?' <span class="count dist u">· '+fmtM(HITM[e.id])+'</span>':''}`+
`${on===true?' <span class="lamp on"></span>':(on===false?' <span class="lamp off"></span>':'')}`+
`${spanProv?' <span class="count">· '+e.pv+'</span>':''}`+
`${e.ob&&obAsked?' <span class="prov">'+(e.ob===2?mdBi('รพ.สต. — สถานีอนามัยประจำตำบล ฝากครรภ์และวางแผนครอบครัวเป็นงานประจำ','รพ.สต. — the local primary-care station; antenatal care and family planning are routine'):mdBi('โรงพยาบาลทั่วไป — ยังไม่ได้ยืนยันว่ามีแผนกสูตินรีเวช','general hospital — an OB-GYN department is not confirmed'))+'</span>':''}`+
(ch.length?' <span class="rchips">'+ch.map(c=>`<a class="rchip" href="${RROOT}search.html${c[0]}">${c[1]}</a>`).join(' ')+'</span>':'')+
(e.lat!=null?'<button type="button" class="rpin" aria-label="แผนที่ · map">📍</button>':'')+
'<div class="rpanel" hidden></div></li>';};''')

hook("a landmark OR a point flattens the list",
     '''const groupHtml=list=>{if(lm)return list.map(row).join('');''',
     '''const groupHtml=list=>{if(P)return list.map(row).join('');''')

hook("nothing found: the shelves, no sentence",
     '''return '<li class="shelf">ไม่พบคำนี้ — ลองดูตามหมวด หรือบอกมดให้ไปเก็บ · '+
'nothing under that word — try a shelf, or send the ants to find it</li>'+top+''',
     '''return top+''')

hook("stuck: the two links, no sentence",
     '''const stuck=partial?'<li class="shelf stuck">'+
say('ยังไม่ตรงที่ถามใช่ไหม — ถามมดเป็นประโยคได้เลย มดอ่านออก',
'not what you asked for? put it to the ants as a sentence — they read whole questions')+
askDoor+
' · <a href="'+RROOT+'suggest.html?kind=crawl&t='+encodeURIComponent('crawl request (search): '+q)+'">'+
mdBi('หรือส่งมดไปเก็บข้อมูลนี้','or send the ants to go and find it')+'</a></li>':'';''',
     '''const stuck=partial?'<li class="shelf stuck">'+askDoor.replace(/^ · /,'')+
(askDoor?' · ':'')+'<a href="'+RROOT+'suggest.html?kind=crawl&t='+encodeURIComponent('crawl request (search): '+q)+'">'+
mdBi('ส่งมดไปเก็บ','send the ants')+'</a></li>':'';''')

hook("the page is assembled: fbar, the fold, the map",
     '''document.body.classList.toggle('mdshort',hits.length>0&&hits.length<=4);
resBox.innerHTML=(hits.length?note+stuck+panelHtml+groupHtml(onHits)+divider+groupHtml(nameHits)+more
:note+stuck+panelHtml+doors());''',
     '''document.body.classList.toggle('mdshort',hits.length>0&&hits.length<=4);
// WO-69 — THE WHERE-ANSWER (P5). A point and a kind both named: the three
// nearest are the answer and everything past them folds under a number.
// A WHERE-QUESTION: a point, and something asked for beside it. Either the
// landmark was lifted OUT of the query (words were left behind) or the page
// was opened at a point. A query that is ONLY a landmark is not folded — the
// reader asked what stands there, and that is the whole list.
const askedHere=!!(P&&((lm&&qFor!==q)||F.near));
const foldN=(askedHere&&onHits.length>3)?3:0;
const listHtml=foldN
?groupHtml(onHits.slice(0,foldN))+'<li class="shelf fold"><details><summary><span class="count">+'+(onHits.length-foldN+nameHits.length)+'</span></summary><ul class="dir cards">'+groupHtml(onHits.slice(foldN))+divider+groupHtml(nameHits)+'</ul></details></li>'
:groupHtml(onHits)+divider+groupHtml(nameHits);
resBox.className='dir cards';
resBox.innerHTML=(hits.length?fbar+note+stuck+panelHtml+listHtml+more
:fbar+note+stuck+panelHtml+((FT.length||F.any)?'<li class="shelf"><span class="count">0</span></li>':doors()));
if(typeof mdResMap==='function')mdResMap(hits,P,askedHere);''')

hook("the held row: a name and a badge",
     ''' li.innerHTML=mdBi('มดมีชื่อนี้อยู่ — แต่ยังไม่มีอะไรให้ใช้','the ants hold this name — and nothing yet you could use')+
  ' · <a href="'+RROOT+hit[1]+'">'+hit[0]+'</a> — '+
  mdBi('ยังไม่มีพิกัด เบอร์โทร หรือเวลาเปิด จึงไม่ขึ้นในผลค้นหา','no location, phone or opening hours yet, so it stays out of the results')+
  ' · <a href="'+RROOT+'pins.html">'+mdBi('ช่วยเติมให้ที','help fill it in')+'</a>';''',
     ''' li.innerHTML='<a href="'+RROOT+hit[1]+'">'+hit[0]+'</a> <span class="badge pin">'+mdBi('ยังไม่มีพิกัด','no pin')+'</span>'+
  ' · <a href="'+RROOT+'pins.html">'+mdBi('ช่วยเติม','fill it in')+'</a>';''')

# ---- the wiring: what a card does when touched (outside the tested block) --
hook("card wiring",
     '''mdHeldRow(q,resBox);})();}
let MD_HELD=null,MD_HELD_TRIED=false;''',
     '''mdHeldRow(q,resBox);})();}
// ---- WO-69: what a card does when touched -------------------------------
// Outside the render block on purpose: the DOM stub tests/test_search_page.py
// runs the block under has no addEventListener, and the block emits markup
// only. Position from MDLOC lives in memory and never in the URL.
(function(){
const box=document.getElementById('results');if(!box)return;
const RR=document.documentElement.getAttribute('data-root')||'';
let hitsNow=[],pointNow=null,mapOpen=false,mapReady=false,booted=false,cardMapEl=null,evGJ=null,evTried=false,grid=null;
const R2D=Math.PI/180;
const dM=(a,b,c,d)=>{const x=(c-a)*R2D*6371000,y=(d-b)*R2D*6371000*Math.cos((a+c)/2*R2D);return Math.sqrt(x*x+y*y);};
const fm=m=>m<1000?mdBi(Math.round(m/10)*10+' ม.',Math.round(m/10)*10+' m'):mdBi((m/1000).toFixed(1)+' กม.',(m/1000).toFixed(1)+' km');
const hx=s=>String(s==null?'':s).replace(/[&<>"]/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;'}[c]));
// the four map files, loaded on the first tap and never before
function mapBoot(then){if(booted){then&&then();return;}booted=true;
let urls=[];try{urls=JSON.parse(document.getElementById('maphead').textContent);}catch(e){}
if(!urls.length){then&&then();return;}
const css=urls.filter(u=>/\\.css/.test(u)),js=urls.filter(u=>!/\\.css/.test(u));
css.forEach(u=>{const l=document.createElement('link');l.rel='stylesheet';l.href=RR+u;document.head.appendChild(l);});
let i=0;const next=()=>{if(i>=js.length){then&&then();return;}
const s=document.createElement('script');s.src=RR+js[i++];s.async=false;s.onload=next;s.onerror=next;document.head.appendChild(s);};
next();}
// the results map
const rm=document.getElementById('resmap'),rmBtn=document.getElementById('resmapbtn'),nearBtn=document.getElementById('resnear');
const gjOf=list=>({type:'FeatureCollection',features:list.filter(e=>e.lat!=null&&e.lng!=null).slice(0,200).map(e=>({type:'Feature',
geometry:{type:'Point',coordinates:[e.lng,e.lat]},properties:{id:e.id,n:e.n,e:e.e||'',p:e.p,s:e.s,su:(e.su||[])[0]||''}}))});
function drawMap(){if(!rm||!window.MDMAP)return;
const gj=gjOf(hitsNow);
window.MDMAP.ready(rm,map=>{
if(map.getSource('res'))map.getSource('res').setData(gj);
else{map.addSource('res',{type:'geojson',data:gj});
map.addLayer({id:'res-halo',type:'circle',source:'res',paint:{'circle-radius':['interpolate',['linear'],['zoom'],10,3.2,14,5.4,17,8],'circle-color':'#FFFCF6','circle-opacity':.85}});
map.addLayer({id:'res-dot',type:'circle',source:'res',paint:{'circle-radius':['interpolate',['linear'],['zoom'],10,2.4,14,4,17,6],'circle-color':'#C2401C','circle-opacity':.95}});
map.on('click',ev=>{const R=22,pt=ev.point;const f=map.queryRenderedFeatures([[pt.x-R,pt.y-R],[pt.x+R,pt.y+R]],{layers:['res-dot']});
if(!f.length)return;const pr=f[0].properties||{};
if(window.MDCARD)window.MDCARD.show({name:[pr.n,pr.e].filter(Boolean).join(' · '),sub:(window.MD_TAB&&window.MD_TAB.subs[pr.su])?window.MD_TAB.subs[pr.su].join(' · '):'',
href:RR+pr.p+'/p/'+pr.s+'.html',plan:pr.p+':'+pr.s,dist:pointNow?fm(dM(pointNow.lat,pointNow.lng,f[0].geometry.coordinates[1],f[0].geometry.coordinates[0])):''},rm);});
map.on('mousemove',ev=>{const f=map.queryRenderedFeatures(ev.point,{layers:['res-dot']});map.getCanvas().style.cursor=f.length?'pointer':'';});}
const pts=gj.features.map(f=>f.geometry.coordinates);
if(pointNow)map.jumpTo({center:[pointNow.lng,pointNow.lat],zoom:15});
else if(pts.length){const b=[[Math.min(...pts.map(p=>p[0])),Math.min(...pts.map(p=>p[1]))],[Math.max(...pts.map(p=>p[0])),Math.max(...pts.map(p=>p[1]))]];
try{map.fitBounds(b,{padding:24,maxZoom:16,duration:0});}catch(e){}}
mapReady=true;});}
// A MAP THAT NEVER ARRIVES MUST NOT LEAVE A HOLE. MDMAP.ready() fires only
// when the basemap's style loads, and never when the tiles fail — which is
// correct, and which would otherwise leave 280 px of empty box above the
// answer on exactly the connection this site is for. If it has not drawn in
// eight seconds the box closes again and the reader is left with the list,
// which was the answer all along.
function openMap(){if(!rm)return;mapOpen=true;rm.hidden=false;
const t=setTimeout(()=>{if(!mapReady){rm.hidden=true;mapOpen=false;}},8000);
mapBoot(()=>{rm.setAttribute('data-mdmap','1');if(window.MDMAP&&window.MDMAP.mount)window.MDMAP.mount(rm);
drawMap();const w=setInterval(()=>{if(mapReady){clearTimeout(t);clearInterval(w);}},400);
setTimeout(()=>clearInterval(w),9000);});}
function closeMap(){mapOpen=false;if(rm)rm.hidden=true;}
window.mdResMap=function(hits,P,openNow){hitsNow=hits||[];pointNow=P||pointNow;
if(rmBtn)rmBtn.hidden=!hitsNow.some(e=>e.lat!=null);
if(nearBtn)nearBtn.hidden=!hitsNow.some(e=>e.lat!=null)||!window.MDLOC;
if(openNow&&hitsNow.length)openMap();else if(mapOpen)drawMap();};
rmBtn&&rmBtn.addEventListener('click',()=>{mapOpen?closeMap():openMap();});
// near me: the position sorts the cards on the page and centres the map;
// it is never written to the URL or to storage (MDLOC's own rule)
nearBtn&&nearBtn.addEventListener('click',()=>{if(!window.MDLOC)return;
window.MDLOC.ask(pt=>{pointNow={lat:pt.lat,lng:pt.lng};
const cards=[...box.querySelectorAll('li.rcard')];
for(const c of cards){const la=parseFloat(c.dataset.lat),ln=parseFloat(c.dataset.lng);
let d=isFinite(la)&&isFinite(ln)?dM(pt.lat,pt.lng,la,ln):null;c._m=d;
let sp=c.querySelector('.dist');if(d!=null){if(!sp){sp=document.createElement('span');sp.className='count dist u';c.querySelector('.rname').after(sp);}sp.innerHTML='· '+fm(d);}}
box.querySelectorAll('li.shelf:not(.fbar):not(.stuck):not(.tellants):not(.held):not(.fold):not(.namesake)').forEach(li=>{if(li.querySelector('a[href*="/"]')&&!li.querySelector('.rchip'))li.remove();});
cards.sort((a,b)=>((a._m==null)-(b._m==null))||((a._m||0)-(b._m||0))).forEach(c=>box.appendChild(c));
openMap();});});
// the card body
function nearest3(e){if(!window.MD_IDX)return[];
if(!grid){grid=new Map();for(const x of window.MD_IDX){if(x.lat==null||x.lng==null)continue;
const k=Math.round(x.lat*200)+':'+Math.round(x.lng*200);(grid.get(k)||grid.set(k,[]).get(k)).push(x);}}
const la=Math.round(e.lat*200),ln=Math.round(e.lng*200),out=[];
for(let i=-1;i<=1;i++)for(let j=-1;j<=1;j++)for(const x of(grid.get((la+i)+':'+(ln+j))||[])){if(x.id===e.id)continue;out.push([dM(e.lat,e.lng,x.lat,x.lng),x]);}
return out.sort((a,b)=>a[0]-b[0]).slice(0,3);}
function fill(card){const id=card.dataset.id,e=(window.MD_IDX||[]).find(x=>x.id===id);const pn=card.querySelector('.rpanel');if(!e||!pn)return;
const T=window.MD_TAB||{subs:{}};const su=(e.su||[])[0]||(e.c||[])[0];
let h='';
if(e.lat!=null){h+='<div class="cardmapslot"></div>';
// NO METRES INSIDE THE NOISE OF A PIN. 2,958 rows sit on a coordinate
// shared with another record — a tambon or postcode centroid stacks every
// place it placed on one point, and one Chiang Rai centroid carries 145.
// Three neighbours reading "0 ม." is a false fact stated three times; the
// places are real and the distance between them is not known.
const nb=nearest3(e);if(nb.length)h+='<p class="rnear">'+nb.map(([d,x])=>'<a href="'+RR+x.p+'/p/'+x.s+'.html">'+hx(x.n)+'</a>'+(d>=25?' <span class="count dist u">'+fm(d)+'</span>':'')).join(' · ')+'</p>';
if(su)h+='<p class="rsame"><a href="'+RR+'search.html?'+(e.su&&e.su[0]?'sub=':'cat=')+encodeURIComponent(su)+'&near='+e.lat+','+e.lng+'">'+(T.subs[su]?mdBi(T.subs[su][0],T.subs[su][1]):(MD_CATWORDS[su]||hx(su)))+' 📍</a></p>';}
h+='<p class="rdo"><button type="button" class="planbtn planbtn-lg" data-plan="'+hx(card.dataset.plan)+'"><span class="off-label">'+mdBi('เพิ่มลงแผน','Add to plan')+'</span><span class="on-label">'+mdBi('อยู่ในแผน','In plan')+'</span></button>'+
' <a class="ropen" href="'+RR+e.p+'/p/'+e.s+'.html">'+mdBi('เปิดหน้านี้','Open this page')+'</a></p>';
h+='<p class="revents"></p>';
pn.innerHTML=h;
const pb=pn.querySelector('.planbtn');if(pb&&typeof planGet==='function'){pb.addEventListener('click',ev=>{ev.preventDefault();ev.stopPropagation();
const k=pb.dataset.plan,list=planGet(),i=list.indexOf(k);if(i>-1)list.splice(i,1);else if(list.length<PLAN_MAX)list.push(k);planSet(list);});planPaint();}
if(e.lat!=null){const slot=pn.querySelector('.cardmapslot');
if(!cardMapEl){cardMapEl=document.createElement('div');cardMapEl.id='cardmap';cardMapEl.className='mdmap cardmap';cardMapEl.innerHTML='<div class="mdmap-draw"></div>';}
cardMapEl.dataset.lat=e.lat;cardMapEl.dataset.lng=e.lng;cardMapEl.dataset.zoom='16';slot.appendChild(cardMapEl);
mapBoot(()=>{if(!window.MDMAP)return;const m=window.MDMAP.map(cardMapEl);
if(m){m.resize();m.jumpTo({center:[e.lng,e.lat],zoom:16});}
else{cardMapEl.setAttribute('data-mdmap','1');window.MDMAP.mount&&window.MDMAP.mount(cardMapEl);}});
const ev=pn.querySelector('.revents');const paint=()=>{if(!evGJ)return;const mine=(evGJ.features||[]).filter(f=>(f.properties||{}).placeId===id);
ev.innerHTML=mine.map(f=>'🎪 '+hx(f.properties.title||'')+(f.properties.start?' <span class="count">'+hx(f.properties.start)+'</span>':'')).join('<br>');};
if(evGJ)paint();else if(!evTried){evTried=true;fetch(RR+'data/events.geojson').then(r=>r.ok?r.json():null).then(d=>{evGJ=d;paint();}).catch(()=>{});}}}
box.addEventListener('click',ev=>{const t=ev.target;
const pin=t.closest&&t.closest('.rpin');const card=t.closest&&t.closest('li.rcard');
if(!card)return;
if(pin){ev.preventDefault();const la=parseFloat(card.dataset.lat),ln=parseFloat(card.dataset.lng);
openMap();if(window.MDMAP&&rm){window.MDMAP.ready(rm,map=>{map.jumpTo({center:[ln,la],zoom:16});
if(window.MDCARD){const e=(window.MD_IDX||[]).find(x=>x.id===card.dataset.id)||{};window.MDCARD.show({name:[e.n,e.e].filter(Boolean).join(' · '),sub:'',href:RR+e.p+'/p/'+e.s+'.html',plan:card.dataset.plan},rm);}});}
return;}
if(t.closest('a')||t.closest('button')||t.closest('.rpanel'))return;
const pn=card.querySelector('.rpanel');if(!pn)return;
const open=!pn.hidden;
box.querySelectorAll('li.rcard.open').forEach(c=>{c.classList.remove('open');const p=c.querySelector('.rpanel');if(p)p.hidden=true;});
if(!open){card.classList.add('open');if(!pn.innerHTML)fill(card);else if(cardMapEl&&pn.contains(cardMapEl)===false&&pn.querySelector('.cardmapslot')){pn.querySelector('.cardmapslot').appendChild(cardMapEl);}
pn.hidden=false;
if(cardMapEl&&window.MDMAP){const e=(window.MD_IDX||[]).find(x=>x.id===card.dataset.id);const m=window.MDMAP.map(cardMapEl);if(m&&e&&e.lat!=null){m.resize();m.jumpTo({center:[e.lng,e.lat],zoom:16});}}}});
})();
let MD_HELD=null,MD_HELD_TRIED=false;''')

# ===========================================================================
# B. CSS
# ===========================================================================
hook("P2: one unit per computed value, everywhere",
     '''html.lang-both .dist .en{display:none}''',
     '''html.lang-both .dist .en{display:none}
html.lang-both .u .en{display:none}
/* WO-69 — the card */
ul.dir.cards{column-width:auto;column-count:1;max-width:44rem}
li.rcard{position:relative;padding:.45rem 2.4rem .45rem 0;border-bottom:1px solid var(--warm-border);margin:0;break-inside:avoid}
li.rcard .rname{font-weight:600}
li.rcard .rchips{display:block;margin-top:.15rem}
.rchip{display:inline-block;font-size:.78rem;line-height:1.5;border:1px solid var(--warm-border);border-radius:999px;
padding:0 .55rem;margin:.1rem .15rem 0 0;color:var(--ink);text-decoration:none;background:var(--card);white-space:nowrap}
.rchip:hover{border-color:var(--ant)}
.rchip.on{background:var(--ant);color:#fff;border-color:var(--ant-dark)}
.rchip.on.off{opacity:.45;text-decoration:line-through}
.rchip s{opacity:.6}
li.shelf.fbar{margin:.2rem 0 .5rem}
li.shelf.fbar.rd .rchip{border-style:dashed}
.lamp{display:inline-block;width:.6rem;height:.6rem;border-radius:50%;margin-left:.3rem;vertical-align:middle;background:#cfc9bd}
.lamp.on{background:#1F6B57;box-shadow:0 0 0 2px rgba(31,107,87,.18)}
.rpin{position:absolute;right:0;top:.35rem;border:1.5px solid var(--warm-border);background:var(--card);border-radius:50%;
width:2rem;height:2rem;cursor:pointer;font-size:1rem;line-height:1}
.rpin:hover{border-color:var(--ant)}
.rpanel{margin:.5rem 0 .2rem;padding:.4rem .6rem;border:1px solid var(--warm-border);border-radius:12px;background:var(--card)}
.rpanel p{margin:.3rem 0}
.rpanel .rnear a{font-weight:600}
.rpanel .rdo .ropen{margin-left:.6rem}
.cardmap{height:160px;margin:.2rem 0 .4rem}
.resmap{height:280px;margin:.4rem 0 .6rem}
.resmap[hidden]{display:none}
.rsctl{float:right;font-size:1rem}
.rsctl button{border:1.5px solid var(--warm-border);background:var(--card);border-radius:50%;width:2.1rem;height:2.1rem;cursor:pointer;margin-left:.3rem;font-size:1rem;line-height:1}
.rsctl button:hover{border-color:var(--ant)}
li.shelf.fold details summary{cursor:pointer;list-style:none;display:inline-block;padding:.2rem .7rem;border:1px solid var(--warm-border);border-radius:999px}
li.shelf.fold details summary::-webkit-details-marker{display:none}
li.shelf.fold ul.dir.cards{margin-top:.4rem}
.tagseek{font-size:.75rem;margin:0 .45rem 0 .1rem;text-decoration:none}''')

# ===========================================================================
# C. THE PLACE PAGE
# ===========================================================================
hook("trade tags link to the tag filter",
     '''        href = f'{"../" * 2}search.html?q={att(urllib.parse.quote(t))}\'''',
     '''        href = f'{"../" * 2}search.html?tag={att(urllib.parse.quote(t))}\'''')

hook("the road row: the road and the count, no sentence",
     '''        near = ""
        if entry.get("via") == "nearest" and entry.get("d") is not None:
            near = (f' <span class="tinynote">'
                    + bi(f"(ติดถนนนี้ที่สุด ห่าง {int(entry['d'])} ม.)",
                         f"(nearest road, {int(entry['d'])} m away)") + "</span>")
        rows.append(
            f"<dt>{bi('ถนน', 'Road')}</dt>"
            f'<dd><a href="{att(street_href(st, 2))}">{esc(st["name"])}</a>{near}<br>'
            f'<span class="tinynote">'
            + bi(f"ดูอีก {len(st['places']) - 1:,} ที่บนถนนเดียวกัน เรียงตามลำดับที่เดินผ่าน",
                 f"See {len(st['places']) - 1:,} more on the same road, in walking order")
            + "</span></dd>")''',
     '''        # WO-69: the road, how far to it when it is only the nearest line,
        # and how many neighbours the road page holds — as a count on the
        # link, not a sentence under it.
        near = ""
        if entry.get("via") == "nearest" and entry.get("d") is not None:
            _dm = int(entry["d"])
            near = f' <span class="count dist u">· {bi(f"{_dm} ม.", f"{_dm} m")}</span>'
        rows.append(
            f"<dt>{bi('ถนน', 'Road')}</dt>"
            f'<dd><a href="{att(street_href(st, 2))}">{esc(st["name"])}'
            f' <span class="count">({len(st["places"]) - 1:,})</span></a>{near}</dd>')''')

hook("the map row opens our own map first",
     '''        rows.append(f'<dt>{bi("แผนที่", "Map")}</dt><dd><a href="{osm}" rel="noopener">OpenStreetMap</a> · '
                    f'<a href="{gmap}" rel="noopener">Google Maps</a>{approx}</dd>')''',
     '''        rows.append(f'<dt>{bi("แผนที่", "Map")}</dt><dd>'
                    f'<a href="../../map.html#16/{r["lat"]:.5f}/{r["lng"]:.5f}">{bi("แผนที่เมือง", "City map")}</a> · '
                    f'<a href="{osm}" rel="noopener">OpenStreetMap</a> · '
                    f'<a href="{gmap}" rel="noopener">Google Maps</a>{approx}</dd>')''')

hook("the reach hint is gone",
     '''    hint = ""
    if pills and live[0]["kind"] in ("phone", "line"):
        hint = ('<span class="tinynote">'
                + bi("เรียงตามช่องทางที่ติดต่อติดจริง", "ordered by what actually gets an answer")''',
     '''    hint = ""
    # WO-69: "ordered by what actually gets an answer" came off — the order
    # is the order, and a sentence about it is a sentence (Michael, 9/7).
    if False and pills and live[0]["kind"] in ("phone", "line"):
        hint = ('<span class="tinynote">'
                + bi("เรียงตามช่องทางที่ติดต่อติดจริง", "ordered by what actually gets an answer")''')

hook("the event caveat is gone",
     '''    return (f'<div class="whatson"><h2>🎪 {bi("ที่นี่มีอะไร", "What is on here")}</h2>'
            f'<ul>{"".join(rows)}</ul>'
            f'<p class="tinynote">{caveat} · '
            f'<a href="{r}events.html">{bi("ดูงานทั้งหมด", "all events")}</a></p></div>')''',
     '''    # WO-69: the "check with the organiser" caveat came off (Michael, 9/7).
    return (f'<div class="whatson"><h2>🎪 {bi("ที่นี่มีอะไร", "What is on here")}</h2>'
            f'<ul>{"".join(rows)}</ul>'
            f'<p class="tinynote"><a href="{r}events.html">{bi("ดูงานทั้งหมด", "all events")}</a></p></div>')''')

hook("the facet panel label without its tap-note",
     '''    label = mark(bi(fs["th"], fs["en"]),
                 "มีเท่าที่รู้ ไม่ได้แปลว่าอย่างอื่นไม่มี — แตะป้ายเพื่อดูว่ารู้มาจากไหน",
                 "What we know of — not what the shop lacks. Tap a tag for where it came from.",
                 cls="mklabel")''',
     '''    # WO-69: the tap-note ("what we know of — not what the shop lacks…")
    # came off; each pill still carries its provenance in title=.
    label = f'<span class="mklabel">{bi(fs["th"], fs["en"])}</span>'
''')

hook("related: the same kind, nearest first",
     '''            related = sorted(
                (x for x in by_sub.get(sub_key, []) if x["id"] != r["id"]),
                key=lambda x: (-ant_rank(x), name_of(x)))[:5]''',
     '''            # WO-69/71: the label says ที่คล้ายกันแถวนี้ — "round here" — so
            # the same kind is ranked by DISTANCE from this pin when it has
            # one (ant-rank breaks ties; ant-rank alone when it does not).
            _cand = [x for x in by_sub.get(sub_key, []) if x["id"] != r["id"]]
            if r.get("lat") is not None and r.get("lng") is not None:
                def _dk(x, _la=r["lat"], _ln=r["lng"]):
                    if x.get("lat") is None or x.get("lng") is None:
                        return (1, 0, -ant_rank(x), name_of(x))
                    _dy = (x["lat"] - _la) * 111000
                    _dx = (x["lng"] - _ln) * 111000 * 0.95
                    return (0, (_dx * _dx + _dy * _dy) ** 0.5, -ant_rank(x), name_of(x))
                related = sorted(_cand, key=_dk)[:5]
            else:
                related = sorted(_cand, key=lambda x: (-ant_rank(x), name_of(x)))[:5]''')

hook("related renders with metres; the three ways to wander",
     '''    related_html = ""
    if related:
        items = "".join(
            f'<li><a href="{place_slug(x)}.html">{name_bi(x)}</a></li>' for x in related)
        related_html = (f'<div class="related"><h2>'
                         + bi("ที่คล้ายกันแถวนี้", "More like this")
                         + f"</h2><ul>{items}</ul></div>")''',
     '''    related_html = ""
    if related:
        def _mtxt(x):
            if r.get("lat") is None or x.get("lat") is None or x.get("lng") is None:
                return ""
            _dy = (x["lat"] - r["lat"]) * 111000
            _dx = (x["lng"] - r["lng"]) * 111000 * 0.95
            _m = (_dx * _dx + _dy * _dy) ** 0.5
            _v = f"{int(round(_m / 10) * 10)}" if _m < 1000 else f"{_m / 1000:.1f}"
            return (f' <span class="count dist u">· {bi(_v + " ม.", _v + " m")}</span>' if _m < 1000
                    else f' <span class="count dist u">· {bi(_v + " กม.", _v + " km")}</span>')
        items = "".join(
            f'<li><a href="{place_slug(x)}.html">{name_bi(x)}</a>{_mtxt(x)}</li>' for x in related)
        related_html = (f'<div class="related"><h2>'
                         + bi("ที่คล้ายกันแถวนี้", "More like this")
                         + f"</h2><ul>{items}</ul></div>")
    # WO-71 — THE THREE WAYS TO WANDER (Nan, 2026-09-06, notes/now-near §6):
    # the nine nearest places we hold, as text with metres — the same nine
    # the map draws; the same kind nearby, one link; and 🎲. Nothing else.
    wander_html = ""
    if r.get("lat") is not None and r.get("lng") is not None:
        _span = PLACE_MAP_SPAN.get(r.get("geoPrecision") or "exact", 520)
        _dlat = _span / 111000.0
        _dlng = _span / (111000.0 * 0.95)
        # FIVE, not the nine the map draws. Nan's §6 said print the same
        # nine; nine names plus the bearings line plus the shelf row put the
        # median place page at 155 words against a 140 cap that exists to
        # stop exactly this. The map still shows all nine, each a link.
        _nb = neighbours_in(r["lat"], r["lng"], _dlat * 1.6, _dlng * 1.6, r["id"], limit=5)
        _nbs = []
        for _x in _nb:
            _dy = (_x["lat"] - r["lat"]) * 111000
            _dx = (_x["lng"] - r["lng"]) * 111000 * 0.95
            _m = int(round(((_dx * _dx + _dy * _dy) ** 0.5) / 10) * 10)
            _nbs.append(f'<li><a href="{place_slug(_x)}.html">{name_bi(_x)}</a>'
                        f' <span class="count dist u">· {bi(f"{_m} ม.", f"{_m} m")}</span></li>')
        _sk = (r.get("sub") or [None])[0]
        _same = ""
        if _sk and _sk in SUB_LABELS:
            _same = (f'<p class="wander-same"><a href="../../search.html?sub={urllib.parse.quote(_sk)}'
                     f'&near={r["lat"]:.5f},{r["lng"]:.5f}">'
                     f'{bi(SUB_LABELS[_sk].get("th", _sk), SUB_LABELS[_sk].get("en", _sk))} 📍</a></p>')
        elif r.get("cat"):
            _ck = r["cat"][0]
            _same = (f'<p class="wander-same"><a href="../../search.html?cat={urllib.parse.quote(_ck)}'
                     f'&near={r["lat"]:.5f},{r["lng"]:.5f}">'
                     f'{bi(CATS[_ck]["th"], CATS[_ck]["en"]) if _ck in CATS else esc(_ck)} 📍</a></p>')
        if _nbs or _same:
            wander_html = (f'<div class="wander">'
                           + (f'<ul class="wander-near">{"".join(_nbs)}</ul>' if _nbs else "")
                           + _same
                           + f'<p class="wander-rand"><a href="../../{RAND_FALLBACK}">🎲 {bi("สุ่มพาไป", "Take me somewhere")}</a></p>'
                           + '</div>')''')

hook("the body carries the three ways under the map",
     '''    body = (f"<h1>{name_bi(r)}</h1>{plan_cta}{honour_panel(r)}{facet_panel(r)}{seven_band(r)}{tag_pills(r)}"
            f"{img_tag}{locator}{blurb}"''',
     '''    body = (f"<h1>{name_bi(r)}</h1>{plan_cta}{honour_panel(r)}{facet_panel(r)}{seven_band(r)}{tag_pills(r)}"
            f"{img_tag}{locator}{wander_html}{blurb}"''')

hook("wander CSS",
     '''.tagseek{font-size:.75rem;margin:0 .45rem 0 .1rem;text-decoration:none}''',
     '''.tagseek{font-size:.75rem;margin:0 .45rem 0 .1rem;text-decoration:none}
.wander{margin:.4rem 0 .8rem}
.wander ul.wander-near{list-style:none;padding:0;margin:0;columns:2;column-gap:1.2rem}
.wander ul.wander-near li{margin:.12rem 0;break-inside:avoid;font-size:.92rem}
.wander .wander-same,.wander .wander-rand{margin:.3rem 0 0;font-size:.92rem}''')

hook("the duplicate district row on a wat",
     '''    if a.get("tambon") or a.get("amphoe"):
        where = " · ".join(x for x in (
            f"ต.{esc(a['tambon'])}" if a.get("tambon") else "",
            f"อ.{esc(a['amphoe'])}" if a.get("amphoe") else "") if x)
        rows.append(f"<dt>{bi('ตำบล-อำเภอ', 'Tambon and amphoe')}</dt>"
                    f"<dd>{where}</dd>")''',
     '''    # WO-71: the ตำบล · อำเภอ row is printed once for every record, with
    # readings, from attrs (detail_page) — the register's copy was a second
    # row saying the same thing on every wat page.
''')


hook("More like this is retired; the three ways replace it",
     '''    related_html = ""
    if related:
        def _mtxt(x):''',
     '''    # WO-71 — "More like this" is RETIRED, not moved. Nan\'s design note
    # (notes/now-near-2026-09-06 §6) says a place page carries THREE ways to
    # wander and nothing else; this was a fourth, and the weakest — five
    # places on the same sub-shelf anywhere in the province, ranked by how
    # complete their records are. What it was for is now the "same kind
    # nearby" link below, which hands the reader ALL of them, nearest first,
    # on a page with a map. Two lists of other places under one record is
    # the clutter this pass is about.
    related_html = ""
    if False:
        def _mtxt(x):''')

hook("the related computation goes with it",
     '''            # WO-69/71: the label says ที่คล้ายกันแถวนี้ — "round here" — so
            # the same kind is ranked by DISTANCE from this pin when it has
            # one (ant-rank breaks ties; ant-rank alone when it does not).
            _cand = [x for x in by_sub.get(sub_key, []) if x["id"] != r["id"]]
            if r.get("lat") is not None and r.get("lng") is not None:
                def _dk(x, _la=r["lat"], _ln=r["lng"]):
                    if x.get("lat") is None or x.get("lng") is None:
                        return (1, 0, -ant_rank(x), name_of(x))
                    _dy = (x["lat"] - _la) * 111000
                    _dx = (x["lng"] - _ln) * 111000 * 0.95
                    return (0, (_dx * _dx + _dy * _dy) ** 0.5, -ant_rank(x), name_of(x))
                related = sorted(_cand, key=_dk)[:5]
            else:
                related = sorted(_cand, key=lambda x: (-ant_rank(x), name_of(x)))[:5]''',
     '''            # WO-71: nothing renders `related` any more (see detail_page),
            # so nothing is computed for it — this ran 25,856 times a build.
            related = None''')

# ===========================================================================
def main():
    check = "--check" in sys.argv
    src = BUILD.read_text(encoding="utf-8")
    out = src
    applied, skipped, bad = [], [], []
    for name, old, new, marker in HOOKS:
        if marker and marker in out:
            skipped.append(name)
            continue
        n = out.count(old)
        if n != 1:
            bad.append(f"{name}: anchor matches {n} times (want 1)")
            continue
        out = out.replace(old, new, 1)
        applied.append(name)
    for a in applied:
        print("  would add" if check else "  added", a)
    for s in skipped:
        print("  already in place:", s)
    for b in bad:
        print("  REFUSED:", b)
    if bad:
        print("nothing written")
        sys.exit(1)
    if check:
        print("nothing written")
        return
    if applied:
        BUILD.write_text(out, encoding="utf-8")
        print(f"build.py: {len(applied)} hook(s) applied")
    else:
        print("nothing to do")


if __name__ == "__main__":
    main()
