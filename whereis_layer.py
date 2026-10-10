#!/usr/bin/env python3
"""whereis_layer.py — one point, said every way a person or a map app reads one.

Nan, 2026-10-10: "We need 'share location' to work well with any mapping
function ... Stripped coordinates and geocoded addresses should be available
for sharing, along with Google short codes and other handy ways to describe
where a place is."

docs/whereis.js sets window.MDWHERE. Everything it needs is fetched the first
time a point is asked about, and each piece is optional: a piece that does not
load leaves its line out, and the rest still answer.

    MDWHERE.describe(lat, lng) -> Promise of {
      lat, lng,
      plain     "19.91720, 99.82510" — no label, no link: pastes into any map
      ll6       "19.917200,99.825100"
      plus      the full Plus Code, "7QG4WRV7+QX"
      plusShort the code Google Maps shows, "WRV7+QX Chiang Rai" (near CM/CR)
      addr      {th, en, tambon, amphoe, prov, post} from the tambon outline
                the point falls in, or null outside both provinces
      road      {th, en} the named road within 25 m (road-near.js), or null
      at        {th, en, d, u} a Mot Dang place within 40 m, or null
      mark      {th, en, d, line:{th,en}} the nearest landmark of
                data/landmarks.json, with distance and direction
      codes     coords.js format() rows (DMS, UTM, MGRS, geohash …)
      links     [{id, th, en, href}] — open the point in another map or app; given
                {gpid} (a record's Google place ID) Google Maps opens that listing
    }
    MDWHERE.message(d, {th, en, link}) -> the text a share sends

Sources, all already published by the build:
  /coords.js (coords_layer.py)      Plus Codes, DMS, UTM, the open-in links
  /data/landmarks.json (bearings)   what people give directions from
  /data/here/<cell>.json (here)     the places within a kilometre
  /road-near.js + /data/roads/      the road name under the point
  /data/whereis.json (this file)    tambon outlines, amphoe, postcode

The outlines are OCHA COD-AB (Royal Thai Survey Department), CC BY-IGO,
licence verified 2026-09-10 (data/admin_boundaries.json), simplified to about
53 m and stored here at 1e-4 degrees (about 11 m). A point within a few tens
of metres of a tambon line can fall on either side of it; the address says
which outline the point fell in, nothing finer. The postcode is the one most
records in that tambon carry (attrs.postcode); a tambon with no such record
has none.

Entry point: emit(g, data) — writes docs/whereis.js and docs/data/whereis.json.
"""
import json
from collections import Counter, defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parent
BOUNDARIES = ROOT / "data" / "admin_boundaries.json"
Q = 10000          # 1e-4 degrees


def _norm(s):
    """derive.normalise, restated: the names on records went through it."""
    return (s or "").replace("เเ", "แ").replace("ํา", "ำ").replace("​", "").strip()


def _postcodes(data):
    """(prov, amphoe, tambon) -> the postcode most records there carry."""
    votes = defaultdict(Counter)
    for prov in ("cm", "cr"):
        for r in data.get(prov) or []:
            a = r.get("attrs") or {}
            pc, tb, am = a.get("postcode"), a.get("tambon"), a.get("amphoe")
            if not (pc and tb and am) or not str(pc).isdigit() or len(str(pc)) != 5:
                continue
            votes[(prov, _norm(am), _norm(tb))][str(pc)] += 1
    return {k: c.most_common(1)[0][0] for k, c in votes.items()}


def _ring(ring):
    """[[lng, lat], ...] -> flat delta-coded ints, lat first."""
    out, pla, pln = [], 0, 0
    for i, pt in enumerate(ring):
        la, ln = round(pt[1] * Q), round(pt[0] * Q)
        if i == 0:
            out += [la, ln]
        else:
            out += [la - pla, ln - pln]
        pla, pln = la, ln
    return out


def build(data):
    doc = json.loads(BOUNDARIES.read_text())
    levels = doc.get("levels") or {}
    post = _postcodes(data)
    amph, amph_ix = [], {}
    provs = [["เชียงใหม่", "Chiang Mai"], ["เชียงราย", "Chiang Rai"]]
    pix = {"cm": 0, "cr": 1}
    for f in (levels.get("amphoe") or {}).get("features") or []:
        p = f.get("properties") or {}
        key = (p.get("province"), _norm(p.get("name")))
        if key not in amph_ix:
            amph_ix[key] = len(amph)
            amph.append([_norm(p.get("name")), p.get("nameEn") or ""])
    tam = []
    for f in (levels.get("tambon") or {}).get("features") or []:
        p, g = f.get("properties") or {}, f.get("geometry") or {}
        prov = p.get("province")
        if prov not in pix:
            continue
        polys = [g["coordinates"]] if g.get("type") == "Polygon" else (g.get("coordinates") or [])
        rings = [_ring(poly[0]) for poly in polys if poly and len(poly[0]) > 2]
        if not rings:
            continue
        lats = [pt[1] for poly in polys for pt in poly[0]]
        lngs = [pt[0] for poly in polys for pt in poly[0]]
        ak = (prov, _norm(p.get("amphoe")))
        if ak not in amph_ix:
            amph_ix[ak] = len(amph)
            amph.append([_norm(p.get("amphoe")), p.get("amphoeEn") or ""])
        tam.append([_norm(p.get("name")), p.get("nameEn") or "", amph_ix[ak], pix[prov],
                    post.get((prov, _norm(p.get("amphoe")), _norm(p.get("name")))) or "",
                    [round(min(lats) * Q), round(min(lngs) * Q), round(max(lats) * Q), round(max(lngs) * Q)],
                    rings])
    return {
        "about": "Tambon outlines for /whereis.js (whereis_layer.py). Rows: [tambon th, tambon en, "
                 "amphoe index, province index, postcode, bbox s,w,n,e at 1e-4 deg, rings as "
                 "delta-coded lat,lng ints at 1e-4 deg].",
        "attribution": "Administrative boundaries: OCHA COD-AB Thailand, Royal Thai Survey Department, CC BY-IGO",
        "generated": doc.get("generated"),
        "q": Q, "prov": provs, "amphoe": amph, "tambon": tam,
    }


JS = r"""/* whereis.js — one point, said every way a person or a map app reads it.
   Built by whereis_layer.py; read its docstring. window.MDWHERE. */
(function(){
'use strict';
if(window.MDWHERE)return;
var S=document.currentScript,BASE=(S&&S.src||'/').replace(/whereis\.js.*$/,'')||'/';
var memo={};
function J(u){return memo[u]||(memo[u]=fetch(BASE+u).then(function(r){if(!r.ok)throw 0;return r.json();})
  .catch(function(){delete memo[u];return null;}));}
function lib(src,name){if(window[name])return Promise.resolve(window[name]);
  return memo[src]||(memo[src]=new Promise(function(ok){var s=document.createElement('script');s.src=BASE+src;
    s.onload=function(){ok(window[name]||null);};s.onerror=function(){delete memo[src];ok(null);};document.head.appendChild(s);}));}
function late(p,ms){return Promise.race([p,new Promise(function(ok){setTimeout(function(){ok(null);},ms);})]);}
function hv(a,b,c,d){var p1=a*Math.PI/180,p2=c*Math.PI/180,dp=p2-p1,dl=(d-b)*Math.PI/180,
  h=Math.sin(dp/2)*Math.sin(dp/2)+Math.cos(p1)*Math.cos(p2)*Math.sin(dl/2)*Math.sin(dl/2);return 12742000*Math.asin(Math.sqrt(h));}
var WIND=[['ทางเหนือ','north'],['ทางตะวันออกเฉียงเหนือ','north-east'],['ทางตะวันออก','east'],['ทางตะวันออกเฉียงใต้','south-east'],
  ['ทางใต้','south'],['ทางตะวันตกเฉียงใต้','south-west'],['ทางตะวันตก','west'],['ทางตะวันตกเฉียงเหนือ','north-west']];
function wind(a,b,c,d){var x=(d-b)*Math.cos(a*Math.PI/180),y=c-a;return WIND[Math.round(((Math.atan2(x,y)*180/Math.PI+360)%360)/45)%8];}
function far(m){return m<1000?[Math.max(5,Math.round(m/5)*5)+' ม.',Math.max(5,Math.round(m/5)*5)+' m']
  :[(m/1000).toFixed(m<10000?1:0)+' กม.',(m/1000).toFixed(m<10000?1:0)+' km'];}
function f5(v){return (+v).toFixed(5);}
function f6(v){return (+v).toFixed(6);}

/* ---- the tambon a point falls in ---- */
var RINGS=null;
function rings(W){if(RINGS)return RINGS;RINGS=W.tambon.map(function(t){return t[6].map(function(a){
  var out=new Float64Array(a.length),la=0,ln=0;for(var i=0;i<a.length;i+=2){la+=a[i];ln+=a[i+1];out[i]=la/W.q;out[i+1]=ln/W.q;}return out;});});return RINGS;}
function inside(la,ln,r){var c=false;for(var i=0,j=r.length-2;i<r.length;j=i,i+=2){var a=r[i],b=r[i+1],p=r[j],q=r[j+1];
  if((a>la)!==(p>la)&&ln<(q-b)*(la-a)/((p-a)||1e-12)+b)c=!c;}return c;}
function admin(W,la,ln){if(!W)return null;var R=rings(W),qa=la*W.q,qn=ln*W.q;
  for(var i=0;i<W.tambon.length;i++){var t=W.tambon[i],bb=t[5];if(qa<bb[0]||qa>bb[2]||qn<bb[1]||qn>bb[3])continue;
    for(var k=0;k<R[i].length;k++)if(inside(la,ln,R[i][k])){
      var am=W.amphoe[t[2]]||['',''],pv=W.prov[t[3]]||['',''],post=t[4];
      return {tambon:[t[0],t[1]],amphoe:am,prov:pv,post:post,
        th:'ต.'+t[0]+' อ.'+am[0]+' จ.'+pv[0]+(post?' '+post:''),
        en:[t[1]||t[0],am[1]||am[0],pv[1]].join(', ')+(post?' '+post:'')};}}
  return null;}

/* ---- a Mot Dang place within 40 m: not a parking bay named for its distance from something else ---- */
function atPlace(rows,la,ln){if(!rows)return null;var best=null,bd=40;
  rows.forEach(function(r){if(r[6]==='transport'&&/parking/.test(r[7]||''))return;if(/ · /.test(r[5]||'')&&/ m | km /.test(r[5]))return;
    var d=hv(la,ln,r[0],r[1]);if(d<bd||(best&&Math.abs(d-bd)<6&&(r[8]||0)>(best.r[8]||0))){bd=Math.min(d,bd);best={r:r,d:d};}});
  if(!best)return null;var r=best.r;return {th:tidy(r[4]||r[5]),en:tidy(r[5]||r[4]),d:best.d,u:'/'+r[2]+'/p/'+r[3]+'.html'};}
/* a name copied from a map listing: "วัดร่องขุ่น - Wat Rong Khun - White Temple , Chiang Rai , Thailand" */
function tidy(s){return String(s||'').replace(/\s*,\s*(Chiang (Mai|Rai)|Thailand)\b[\s\S]*$/i,'').replace(/\s+,/g,',').trim();}

/* ---- the landmark people steer by ---- */
function landmark(L,la,ln){if(!L)return null;var list=(L.cm||[]).concat(L.cr||[]),best=null,bd=Infinity;
  list.forEach(function(k){var d=hv(la,ln,k.lat,k.lng);if(d<bd){bd=d;best=k;}});
  if(!best)return null;
  /* past ten kilometres, the town's own origin is more use than the nearest temple */
  if(bd>10000){var o=list.filter(function(k){return k.origin;}),ob=null,od=Infinity;
    o.forEach(function(k){var d=hv(la,ln,k.lat,k.lng);if(d<od){od=d;ob=k;}});if(ob){best=ob;bd=od;}}
  var w=wind(best.lat,best.lng,la,ln),f=far(bd);
  return {th:best.th,en:best.en,d:bd,
    line:bd<25?{th:'ที่'+best.th,en:'At '+best.en}:{th:'ห่าง'+best.th+' '+f[0]+' '+w[0],en:f[1]+' '+w[1]+' of '+best.en}};}

function roadAt(la,ln){return late(lib('road-near.js','MDROAD').then(function(M){if(!M||!M.along)return null;
  return M.along([[la,ln]]).then(function(A){var n=A&&A.name(la,ln);return n?{th:n[0]||n[1],en:n[1]||n[0],ref:n[2]||''}:null;});})
  .catch(function(){return null;}),5000);}

function links(C,la,ln,name,gpid){
  var ll=f6(la)+','+f6(ln),nm=name||'',out=[];
  /* a place with its Google place ID opens its own Google listing, not a pin at its coordinates */
  out.push({id:'google',th:'Google Maps',en:'Google Maps',href:gpid?'https://www.google.com/maps/search/?api=1&query='+encodeURIComponent(nm||ll)+'&query_place_id='+encodeURIComponent(gpid)
    :'https://www.google.com/maps/search/?api=1&query='+ll});
  out.push({id:'apple',th:'Apple Maps',en:'Apple Maps',href:'https://maps.apple.com/?ll='+ll+'&q='+encodeURIComponent(nm||ll)});
  out.push({id:'waze',th:'Waze',en:'Waze',href:'https://www.waze.com/ul?ll='+ll+'&navigate=yes&zoom=17'});
  var dp='grab://open?screenType=BOOKING&dropOffLatitude='+f6(la)+'&dropOffLongitude='+f6(ln)+'&dropOffAddress='+encodeURIComponent(nm);
  out.push({id:'grab',th:'เรียก Grab ไปที่นี่',en:'Grab, ride here',href:'https://grab.onelink.me/2695613898?af_dp='+encodeURIComponent(dp)+'&af_web_dp='+encodeURIComponent('https://www.grab.com/th/transport/')});
  ((C&&C.links(la,ln,nm))||[]).forEach(function(k){if(k.id==='google'||k.id==='apple'||k.id==='waze'||k.id==='umap')return;out.push(k);});
  out.push({id:'motdang',th:'แผนที่มดแดง',en:'Mot Dang map',href:'https://motdang.net/map.html?go='+ll});
  return out;}

function describe(lat,lng,opt){
  lat=+lat;lng=+lng;opt=opt||{};
  var cell=Math.floor(lat*100)+'_'+Math.floor(lng*100);
  return Promise.all([lib('coords.js','MDCOORDS'),J('data/whereis.json'),J('data/landmarks.json'),J('data/here/'+cell+'.json'),
      opt.road===false?null:roadAt(lat,lng)]).then(function(r){
    var C=r[0],codes=C?C.format(lat,lng):[],pick=function(k){var x=codes.filter(function(c){return c.kind===k;})[0];return x?x.text:'';};
    var d={lat:lat,lng:lng,plain:f5(lat)+', '+f5(lng),ll6:f6(lat)+','+f6(lng),
      plus:pick('pluscode'),plusShort:pick('pluscode_short'),addr:admin(r[1],lat,lng),road:r[4]||null,
      at:atPlace(r[3],lat,lng),mark:landmark(r[2],lat,lng),codes:codes,attribution:r[1]?r[1].attribution:''};
    d.gpid=opt.gpid||'';
    d.links=links(C,lat,lng,opt.name||(d.at&&d.at.en)||'',d.gpid);
    return d;});}

/* the human lines, in the reader's language or both */
/* a share that already names the place does not need "at <the place>" under it */
function atOf(d,name){return d.at&&!(name&&d.at.d<30)?d.at:null;}
function lines(d,lg,name){
  var two=function(o){return lg==='th'?o.th:lg==='en'?o.en:(o.th===o.en?o.en:o.th+' · '+o.en);},out=[],at=atOf(d,name);
  if(at){var f=far(at.d);
    if(at.th===at.en)out.push(at.d<15?at.en:at.en+' · '+(lg==='th'?f[0]:f[1]));
    else out.push(two(at.d<15?{th:'ที่ '+at.th,en:'At '+at.en}:{th:'ห่าง '+at.th+' '+f[0],en:f[1]+' from '+at.en}));}
  if(d.mark&&(!at||d.mark.d<3000)&&!(name&&d.mark.d<30))out.push(two(d.mark.line));
  if(d.road)out.push(two({th:d.road.th,en:d.road.en}));
  if(d.addr){if(lg!=='en')out.push(d.addr.th);if(lg!=='th')out.push(d.addr.en);}
  return out;}

/* the same lines as {th, en} pairs, for a page that shows one language at a time */
function pairs(d,name){var out=[],at=atOf(d,name);
  if(at){var f=far(at.d);out.push(at.d<15?{th:at.th,en:at.en}:{th:at.th+' · '+f[0],en:at.en+' · '+f[1]});}
  if(d.mark&&(!at||d.mark.d<3000)&&!(name&&d.mark.d<30))out.push(d.mark.line);
  if(d.road)out.push({th:d.road.th,en:d.road.en});
  return out;}

/* what a share sends: a heading, where it is in words, the codes any map reads, the links */
function message(d,o){o=o||{};var out=[];
  if(o.th||o.en)out.push(o.th&&o.en?o.th+' · '+o.en:(o.th||o.en));
  if(o.name)out.push(o.name);
  out=out.concat(lines(d,o.lang,o.name));
  out.push(d.plain+(d.plusShort?' · '+d.plusShort:d.plus?' · '+d.plus:''));
  out.push(d.gpid?'https://www.google.com/maps/search/?api=1&query='+encodeURIComponent(o.name||d.ll6)+'&query_place_id='+encodeURIComponent(d.gpid)
    :'https://www.google.com/maps/search/?api=1&query='+d.ll6);
  if(o.link)out.push(o.link);
  return out.join('\n');}

/* a Google place ID out of a Google Maps link (gplace.py's arithmetic): the feature ID's two halves,
   little-endian, in a five-byte protobuf frame, base64url */
function le8(hex){hex=hex.replace(/^0x/i,'');while(hex.length<16)hex='0'+hex;var o=[];for(var i=14;i>=0;i-=2)o.push(parseInt(hex.substr(i,2),16));return o;}
function b64u(b){var s='';for(var i=0;i<b.length;i++)s+=String.fromCharCode(b[i]);return btoa(s).replace(/\+/g,'-').replace(/\//g,'_').replace(/=+$/,'');}
function gplace(text){var t=String(text||'');try{t=decodeURIComponent(t);}catch(e){}
  var m=/(?:query_place_id=|place_id[:=]|placeid=)([0-9A-Za-z_\-]{16,})/.exec(t)||/(?:^|[^0-9A-Za-z_\-])(ChIJ[0-9A-Za-z_\-]{20,})/.exec(t);
  if(m)return m[1];
  var f=/(0x[0-9a-f]{1,16}):(0x[0-9a-f]{1,16})/i.exec(t);
  if(f&&parseInt(f[1],16)&&parseInt(f[2],16))return b64u([0x0a,0x12,0x09].concat(le8(f[1]),[0x11],le8(f[2])));
  return '';}
/* the Mot Dang record carrying that place ID: {u, n} or null */
function byGoogle(pid){return pid?J('data/gplace.json').then(function(m){var v=m&&m[pid];if(!v)return null;var i=v.indexOf('|');return {u:'/'+v.slice(0,i).replace('/','/p/')+'.html',n:v.slice(i+1)};}):Promise.resolve(null);}

window.MDWHERE={describe:describe,lines:lines,pairs:pairs,message:message,far:far,gplace:gplace,byGoogle:byGoogle};
})();
"""


def emit(g, data):
    docs = Path(g["DOCS"]) if isinstance(g, dict) else Path(g)
    if not BOUNDARIES.exists():
        (docs / "whereis.js").write_text(JS, encoding="utf-8")
        return "whereis.js written; no admin_boundaries.json, so no address lines"
    doc = build(data)
    (docs / "data").mkdir(parents=True, exist_ok=True)
    blob = json.dumps(doc, ensure_ascii=False, separators=(",", ":"))
    (docs / "data" / "whereis.json").write_text(blob, encoding="utf-8")
    (docs / "whereis.js").write_text(JS, encoding="utf-8")
    with_post = sum(1 for t in doc["tambon"] if t[4])
    # Google place ID → record, for a Google Maps link pasted into a map's search
    gp = {}
    for prov in ("cm", "cr"):
        for r in data.get(prov) or []:
            if r.get("googlePlaceId"):
                slug = (g.get("place_slug") or (lambda x: x["id"]))(r) if isinstance(g, dict) else r["id"]
                nm = r.get("nameEn") or r.get("name") or r.get("nameTh") or ""
                gp[r["googlePlaceId"]] = f"{prov}/{slug}|{nm}"
    (docs / "data" / "gplace.json").write_text(json.dumps(gp, ensure_ascii=False, separators=(",", ":")), encoding="utf-8")
    return (f"whereis.js + data/whereis.json ({len(blob.encode('utf-8')):,} bytes, "
            f"{len(doc['tambon'])} tambons, {with_post} with a postcode) + data/gplace.json ({len(gp)} Google place IDs)")


if __name__ == "__main__":
    import sys
    out = Path(sys.argv[1]) if len(sys.argv) > 1 else ROOT / "docs"
    data = {}
    for prov in ("cm", "cr"):
        p = ROOT / "data" / "canonical" / f"{prov}.json"
        if p.exists():
            d = json.loads(p.read_text())
            data[prov] = d if isinstance(d, list) else (d.get("places") or [])
    gids = ROOT / "data" / "curated" / "google_ids.json"
    if gids.exists():
        gd = json.loads(gids.read_text())
        for rs in data.values():
            for r in rs:
                if isinstance(gd.get(r.get("id")), dict):
                    r["googlePlaceId"] = gd[r["id"]]["placeId"]
    print(emit({"DOCS": out}, data))
