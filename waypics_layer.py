"""waypics_layer.py — the way to a place, in NaN's ride pictures (NaN, 2026-09-28).

A place page with coordinates, and at least one of her pictures near enough to
lie on a way there, carries one button. The tap fetches the reader's position
(only then), loads the wide road graph (only then), routes by road from the
reader to the place, and shows the ride pictures along that route in the order
the reader passes them, each a link to the page of what it shows.

    block(r, bi, svg_icon)  -> the button + an empty container, or ""
    emit(docs)              -> writes docs/waypics.js and docs/data/road_graph_wide.json

The page carries a few hundred bytes (the button and its onclick); the router
and the picture picking live in one shared file, fetched on the tap.

Graph: data/road_graph_wide.json (importers/crawl_roads.py --wide, then
importers/build_road_graph.py --wide) — road_graph.json's old-city box plus the
San Kamphaeng side to Chamcha market and the strip south of the ring, where the
23/24 Sep rides are. Outside it the answer is the straight line, and the strip
says so and shows the pictures within LAST_M of the place instead.

Which pages: inside the graph's area, a picture within NEAR_KM; outside it, a
picture within LAST_M (the only strip it can draw there).
"""

import json
import math
import shutil
import zlib
from pathlib import Path

import pics_layer

ROOT = Path(__file__).resolve().parent
GRAPH = ROOT / "data" / "road_graph_wide.json"
NEAR_KM = 3.0
LAST_M = 600
_GRID = 0.01

_STATE = {"grid": None, "area": None}


def _area():
    if _STATE["area"] is None:
        try:
            # The area sits at the end of a half-megabyte file; read it once.
            _STATE["area"] = json.loads(GRAPH.read_text()).get("area") or {}
        except (OSError, ValueError):
            _STATE["area"] = {}
    return _STATE["area"]


def _grid():
    """Pool positions in 0.01° buckets, built on the first page that asks."""
    if _STATE["grid"] is None:
        g = {}
        for row in pics_layer.rows():
            la, lo = row[0], row[1]
            g.setdefault((math.floor(la / _GRID), math.floor(lo / _GRID)), []).append((la, lo))
        _STATE["grid"] = g
    return _STATE["grid"]


def _hav_m(a_lat, a_lng, b_lat, b_lng):
    p1, p2 = math.radians(a_lat), math.radians(b_lat)
    dp, dl = math.radians(b_lat - a_lat), math.radians(b_lng - a_lng)
    h = math.sin(dp / 2) ** 2 + math.cos(p1) * math.cos(p2) * math.sin(dl / 2) ** 2
    return 2 * 6371000.0 * math.asin(math.sqrt(h))


def _any_within(lat, lng, metres):
    g = _grid()
    n = int(math.ceil(metres / 1000.0 / 1.05)) + 1      # 0.01° ≈ 1.05 km of longitude here
    ci, cj = math.floor(lat / _GRID), math.floor(lng / _GRID)
    for i in range(ci - n, ci + n + 1):
        for j in range(cj - n, cj + n + 1):
            for la, lo in g.get((i, j), ()):
                if _hav_m(lat, lng, la, lo) <= metres:
                    return True
    return False


def _in_area(lat, lng):
    a = _area()
    return bool(a) and a["s"] < lat < a["n"] and a["w"] < lng < a["e"]


def wanted(r):
    """True when this record's page gets the button."""
    la, lo = r.get("lat"), r.get("lng")
    if la is None or lo is None:
        return False
    try:
        la, lo = float(la), float(lo)
    except (TypeError, ValueError):
        return False
    if _in_area(la, lo):
        return _any_within(la, lo, NEAR_KM * 1000)
    return _any_within(la, lo, LAST_M)


def _att(s):
    return (str(s).replace("&", "&amp;").replace('"', "&quot;")
            .replace("<", "&lt;").replace(">", "&gt;"))


def block(r, bi, svg_icon):
    if not wanted(r):
        return ""
    la, lo = float(r["lat"]), float(r["lng"])
    own = pics_layer._HREF.get(r.get("id"))
    own = ("/" + own + ".html") if own else ""
    # The onclick asks for the position at once, in the tap, and loads the
    # shared script; the script picks the pending tap up (window.MDWAY).
    label = bi("ทางมาที่นี่ เป็นภาพ", "The way here, in pictures")
    tap = ("if(window.MDWAY)return MDWAY(this);this.disabled=true;"
           "window.MDWAYP=new Promise(function(y,n){navigator.geolocation?"
           "navigator.geolocation.getCurrentPosition(y,n,{enableHighAccuracy:true,timeout:20000,maximumAge:60000}):n()});"
           "var s=document.createElement('script');s.src=this.dataset.js;document.head.appendChild(s)")
    return (f'<div class="waypics" data-to="{la:.6f},{lo:.6f}" data-own="{_att(own)}">'
            f'<button type="button" class="planbtn planbtn-lg waybtn" '
            f'data-js="../../waypics.js?v={JS_V}" onclick="{_att(tap)}">'
            f'{svg_icon("i-camera", 18, "rowicon planicon")}'
            f'<span>{label}</span></button>'
            f'<div class="wayout" hidden></div></div>')


def emit(docs):
    docs = Path(docs)
    (docs / "waypics.js").write_text(JS)
    out = ""
    if GRAPH.exists():
        (docs / "data").mkdir(parents=True, exist_ok=True)
        shutil.copyfile(GRAPH, docs / "data" / GRAPH.name)
        out = f", graph {GRAPH.stat().st_size / 1e6:.2f} MB"
    # Counted here, not in block(): place pages render in forked workers.
    got = [r for r in pics_layer._PLACES.values() if wanted(r)]
    inside = sum(1 for r in got if _in_area(float(r["lat"]), float(r["lng"])))
    return (f"  waypics: button on {len(got):,} place pages "
            f"({inside:,} routable, {len(got) - inside:,} last-stretch only){out}")


JS = r"""/* waypics.js — the way to a place, in NaN's ride pictures (waypics_layer.py).
   Loaded by the tap on .waybtn; routes over data/road_graph_wide.json (the
   plan.html router, ported), then keeps the pictures from data/pics/ that lie
   along the route and face the way the reader travels. */
(function(){
'use strict';
var MODES={foot:{mpm:4600/60,fwd:1,bwd:2},ride:{mpm:18000/60,fwd:4,bwd:8}};
var NEAR_M=30,FACE_DEG=70,SAME_M=40,LAST_M=600,SNAP_M=250,OWN_MAX=3,MAX_CARDS=24;
var RAD=Math.PI/180;
function hav(a,b){var dLa=(b[0]-a[0])*RAD,dLo=(b[1]-a[1])*RAD;
 var h=Math.sin(dLa/2)*Math.sin(dLa/2)+Math.cos(a[0]*RAD)*Math.cos(b[0]*RAD)*Math.sin(dLo/2)*Math.sin(dLo/2);
 return 2*6371000*Math.asin(Math.sqrt(h));}
function segLen(p,q){var kx=Math.cos((p[0]+q[0])/2*RAD)*111320,ky=110540;
 return Math.hypot((q[1]-p[1])*kx,(q[0]-p[0])*ky);}
function edgeLen(pts){var t=0;for(var k=0;k<pts.length-1;k++)t+=segLen(pts[k],pts[k+1]);return t;}
function bearing(a,b){var y=Math.sin((b[1]-a[1])*RAD)*Math.cos(b[0]*RAD),
 x=Math.cos(a[0]*RAD)*Math.sin(b[0]*RAD)-Math.sin(a[0]*RAD)*Math.cos(b[0]*RAD)*Math.cos((b[1]-a[1])*RAD);
 return (Math.atan2(y,x)/RAD+360)%360;}
function angDiff(a,b){var d=Math.abs(a-b)%360;return d>180?360-d:d;}
/* ---- the graph, as plan.html builds it -------------------------------- */
function build(g){var S=g.scale,nodes=g.nodes.map(function(p){return [p[0]/S,p[1]/S];});
 var adj=nodes.map(function(){return [];}),geom=[];
 g.edges.forEach(function(e,i){var a=e[0],b=e[1],d=e[4]||[],pts=[nodes[a]],la=0,ln=0;
  for(var k=0;k<d.length;k+=2){if(k===0){la=d[0];ln=d[1];}else{la+=d[k];ln+=d[k+1];}pts.push([la/S,ln/S]);}
  pts.push(nodes[b]);geom.push(pts);
  adj[a].push([b,e[2],e[3],i,1]);adj[b].push([a,e[2],e[3],i,0]);});
 return {area:g.area,nodes:nodes,adj:adj,edges:g.edges,geom:geom,main:{}};}
function inArea(G,p){var a=G&&G.area;return !!a&&p[0]>a.s&&p[0]<a.n&&p[1]>a.w&&p[1]<a.e;}
function passable(flags,mode,fwd){var m=MODES[mode];return (flags&(fwd?m.fwd:m.bwd))!==0;}
function toSeg(p,a,b){var kx=Math.cos(p[0]*RAD)*111320,ky=110540;
 var ax=(a[1]-p[1])*kx,ay=(a[0]-p[0])*ky,bx=(b[1]-p[1])*kx,by=(b[0]-p[0])*ky;
 var dx=bx-ax,dy=by-ay,L=dx*dx+dy*dy,t=L?(-ax*dx-ay*dy)/L:0;t=Math.max(0,Math.min(1,t));
 return {d:Math.hypot(ax+t*dx,ay+t*dy),t:t,seg:Math.sqrt(L)};}
/* The biggest connected run of road this mode may use: a pin inside a wat's
   courtyard footway otherwise snaps onto a network that joins nothing. */
function mainComponent(G,mode){if(G.main[mode])return G.main[mode];
 var m=MODES[mode],n=G.nodes.length,seen=new Uint8Array(n),best=null,bestN=0;
 for(var s=0;s<n;s++){if(seen[s])continue;var stack=[s],group=[];seen[s]=1;
  while(stack.length){var v=stack.pop();group.push(v);var av=G.adj[v];
   for(var k=0;k<av.length;k++){var e=av[k];if(!(e[2]&(m.fwd|m.bwd))||seen[e[0]])continue;seen[e[0]]=1;stack.push(e[0]);}}
  if(group.length>bestN){bestN=group.length;best=group;}}
 var inMain=new Uint8Array(n);if(best)for(var k2=0;k2<best.length;k2++)inMain[best[k2]]=1;
 var keep=new Uint8Array(G.edges.length);
 for(var i=0;i<G.edges.length;i++){var ed=G.edges[i];if((ed[3]&(m.fwd|m.bwd))&&inMain[ed[0]]&&inMain[ed[1]])keep[i]=1;}
 G.main[mode]=keep;return keep;}
function snap(G,p,mode){var keep=mainComponent(G,mode),best=null;
 for(var i=0;i<G.geom.length;i++){if(!keep[i])continue;var pts=G.geom[i];
  if(Math.abs(pts[0][0]-p[0])>0.02||Math.abs(pts[0][1]-p[1])>0.02)continue;
  var run=0,hit=false;
  for(var k=0;k<pts.length-1;k++){var r=toSeg(p,pts[k],pts[k+1]);
   if(!best||r.d<best.d){best={d:r.d,edge:i,fromA:run+r.t*r.seg};hit=true;}run+=r.seg;}
  if(hit)best.total=run;}
 if(!best)return null;var e=G.edges[best.edge];
 best.a=e[0];best.b=e[1];best.toA=best.fromA;best.toB=Math.max(0,best.total-best.fromA);return best;}
function Heap(){this.a=[];}
Heap.prototype.push=function(k,v){var a=this.a;a.push([k,v]);var i=a.length-1;
 while(i>0){var p=(i-1)>>1;if(a[p][0]<=a[i][0])break;var t=a[p];a[p]=a[i];a[i]=t;i=p;}};
Heap.prototype.pop=function(){var a=this.a;if(!a.length)return null;var top=a[0],last=a.pop();
 if(a.length){a[0]=last;var i=0;for(;;){var l=2*i+1,r=l+1,m=i;
  if(l<a.length&&a[l][0]<a[m][0])m=l;if(r<a.length&&a[r][0]<a[m][0])m=r;
  if(m===i)break;var t=a[m];a[m]=a[i];a[i]=t;i=m;}}return top;};
function atAlong(pts,d){var run=0;
 for(var k=0;k<pts.length-1;k++){var L=segLen(pts[k],pts[k+1]);
  if(run+L>=d){var t=L?(d-run)/L:0;return [pts[k][0]+(pts[k+1][0]-pts[k][0])*t,pts[k][1]+(pts[k+1][1]-pts[k][1])*t];}
  run+=L;}return pts[pts.length-1];}
function cutEdge(G,ei,d0,d1){var pts=G.geom[ei],L=edgeLen(pts);
 var a=Math.max(0,Math.min(L,Math.min(d0,d1))),b=Math.max(0,Math.min(L,Math.max(d0,d1)));
 var out=[atAlong(pts,a)],run=0;
 for(var k=0;k<pts.length-1;k++){run+=segLen(pts[k],pts[k+1]);if(run>a+0.01&&run<b-0.01)out.push(pts[k+1]);}
 out.push(atAlong(pts,b));return d1<d0?out.reverse():out;}
function joinLine(line,pts){pts.forEach(function(pt){var l=line[line.length-1];
 if(!l||Math.abs(l[0]-pt[0])>1e-9||Math.abs(l[1]-pt[1])>1e-9)line.push(pt);});return line;}
function route(G,from,to,mode){
 if(from.edge===to.edge){var fw=to.fromA>=from.fromA;
  if(passable(G.edges[from.edge][3],mode,fw))return {m:Math.abs(to.fromA-from.fromA),path:cutEdge(G,from.edge,from.fromA,to.fromA)};}
 var N=G.nodes.length,cost=new Float64Array(N).fill(Infinity),prevN=new Int32Array(N).fill(-1),prevE=new Int32Array(N).fill(-1),h=new Heap();
 if(passable(G.edges[from.edge][3],mode,false)||from.a===from.b){cost[from.a]=from.toA;h.push(from.toA,from.a);}
 if(passable(G.edges[from.edge][3],mode,true)&&from.toB<cost[from.b]){cost[from.b]=from.toB;h.push(from.toB,from.b);}
 var goals={};
 if(passable(G.edges[to.edge][3],mode,true))goals[to.a]=to.toA;
 if(passable(G.edges[to.edge][3],mode,false))goals[to.b]=to.toB;
 if(!Object.keys(goals).length)return null;
 var bestGoal=null,bestCost=Infinity;
 for(;;){var top=h.pop();if(!top)break;var c=top[0],n=top[1];
  if(c>cost[n])continue;if(c>=bestCost)break;
  if(goals[n]!==undefined&&c+goals[n]<bestCost){bestCost=c+goals[n];bestGoal=n;}
  var list=G.adj[n];
  for(var i=0;i<list.length;i++){var t2=list[i][0],nc=c+list[i][1];
   if(!passable(list[i][2],mode,list[i][4]===1))continue;
   if(nc<cost[t2]){cost[t2]=nc;prevN[t2]=n;prevE[t2]=list[i][3];h.push(nc,t2);}}}
 if(bestGoal===null)return null;
 var chain=[],cur=bestGoal;
 while(cur!==-1&&prevE[cur]!==-1){chain.push([prevE[cur],cur]);cur=prevN[cur];}
 chain.reverse();var line=[];
 joinLine(line,cutEdge(G,from.edge,from.fromA,(cur===from.a)?0:edgeLen(G.geom[from.edge])));
 chain.forEach(function(x){var e=G.edges[x[0]],pts=G.geom[x[0]];joinLine(line,(e[1]===x[1])?pts:pts.slice().reverse());});
 joinLine(line,cutEdge(G,to.edge,(bestGoal===to.a)?0:edgeLen(G.geom[to.edge]),to.fromA));
 return {m:bestCost,path:line};}
/* ---- the pictures along a route --------------------------------------
   A row: [lat,lng,thumb,href,th,en,date,hh:mm,heading|-1,slug,w,h]. Kept when
   it stands within NEAR_M of the line and, where its heading is known, faces
   within FACE_DEG of the way the reader travels there. Ordered by how far
   along the way; the same href again within SAME_M is the same view. */
function pick(path,rows,skip){var n=path.length;if(n<2)return [];
 var kx=Math.cos(path[0][0]*RAD)*111320,ky=110540;
 var xy=path.map(function(p){return [p[1]*kx,p[0]*ky];}),cum=[0],brg=[];
 for(var k=0;k<n-1;k++){cum.push(cum[k]+Math.hypot(xy[k+1][0]-xy[k][0],xy[k+1][1]-xy[k][1]));brg.push(bearing(path[k],path[k+1]));}
 var out=[],seen={};
 rows.forEach(function(r){if((skip&&r[3]===skip)||seen[r[9]])return;
  var px=r[1]*kx,py=r[0]*ky,best=null;
  for(var k=0;k<n-1;k++){var ax=xy[k][0],ay=xy[k][1],bx=xy[k+1][0],by=xy[k+1][1];
   if(px<Math.min(ax,bx)-NEAR_M||px>Math.max(ax,bx)+NEAR_M||py<Math.min(ay,by)-NEAR_M||py>Math.max(ay,by)+NEAR_M)continue;
   var dx=bx-ax,dy=by-ay,L=dx*dx+dy*dy,t=L?((px-ax)*dx+(py-ay)*dy)/L:0;t=t<0?0:t>1?1:t;
   var d=Math.hypot(ax+t*dx-px,ay+t*dy-py);
   if(d>NEAR_M||(r[8]>=0&&L&&angDiff(r[8],brg[k])>FACE_DEG))continue;
   if(!best||d<best.d)best={d:d,along:cum[k]+t*Math.sqrt(L)};}
  if(best){seen[r[9]]=1;out.push({r:r,along:best.along,d:best.d});}});
 out.sort(function(a,b){return a.along-b.along;});
 var keep=[],last={};
 out.forEach(function(o){var p=last[o.r[3]];if(p!=null&&o.along-p<SAME_M)return;last[o.r[3]]=o.along;keep.push(o);});
 /* A dense stretch (Chamcha gave 85) thins to one card per stretch of the way,
    about MAX_CARDS in all: the one nearest the line, a known heading first. */
 var gap=Math.max(SAME_M,cum[n-1]/MAX_CARDS),slot={};
 keep.forEach(function(o){var k=Math.floor(o.along/gap),s=o.d+(o.r[8]>=0?0:12),b=slot[k];
  if(!b||s<b.s)slot[k]={o:o,s:s};});
 keep=Object.keys(slot).map(function(k){return slot[k].o;}).sort(function(a,b){return a.along-b.along;});
 return {pics:keep,length:cum[n-1]};}
/* The place's own pictures, and the ones within LAST_M of it by distance. */
function around(to,rows,own){var near=[],mine=[],seen={};
 rows.forEach(function(r){if(seen[r[9]])return;seen[r[9]]=1;var d=hav(to,[r[0],r[1]]);
  if(own&&r[3]===own&&d<=LAST_M)mine.push({r:r,d:d});else if(d<=LAST_M)near.push({r:r,d:d});});
 near.sort(function(a,b){return a.d-b.d;});
 mine.sort(function(a,b){return (b.r[6]+b.r[7])<(a.r[6]+a.r[7])?-1:1;});
 var keep=[],last={};
 near.forEach(function(o){var p=last[o.r[3]];if(p!=null&&Math.abs(o.d-p)<SAME_M)return;last[o.r[3]]=o.d;keep.push(o);});
 return {near:keep,own:mine.slice(0,OWN_MAX)};}
function cellKeys(ix,s,w,n,e){var C=ix.cell,ks=[];
 for(var i=Math.floor(s/C);i<=Math.floor(n/C);i++)for(var j=Math.floor(w/C);j<=Math.floor(e/C);j++){
  var k=i+'_'+j;if(ix.cells[k])ks.push(k);}return ks;}
function bbox(pts,pad){var s=90,n=-90,w=180,e=-180;
 pts.forEach(function(p){s=Math.min(s,p[0]);n=Math.max(n,p[0]);w=Math.min(w,p[1]);e=Math.max(e,p[1]);});
 return [s-pad,w-pad,n+pad,e+pad];}
/* Everything the page asks, one call: reader P, place T, both [lat,lng]. */
function plan(G,P,T,mode){
 var why=null,res=null,a=null,b=null;
 if(!G)why='nograph';else if(!inArea(G,P))why='you';else if(!inArea(G,T))why='place';
 else{a=snap(G,P,mode);b=snap(G,T,mode);
  if(!a||a.d>SNAP_M)why='you';else if(!b||b.d>SNAP_M)why='place';
  else{res=route(G,a,b,mode);if(!res)why='noroute';}}
 if(!res)return {why:why,crow:hav(P,T)};
 var path=[P].concat(res.path,[T]);
 return {m:res.m+a.d+b.d,path:path};}
var W={build:build,snap:snap,route:route,pick:pick,around:around,plan:plan,cellKeys:cellKeys,
 bbox:bbox,hav:hav,MODES:MODES,LAST_M:LAST_M};
if(typeof module!=='undefined'&&module.exports){module.exports=W;return;}
/* ---- the page -------------------------------------------------------- */
var ROOT=document.documentElement.getAttribute('data-root')||'';
function bi(th,en){return window.mdBi?window.mdBi(th,en):th+' · '+en;}
function icon(n,s){return window.mdIcon?window.mdIcon(n,s):'';}
function esc(s){return String(s==null?'':s).replace(/[&<>"']/g,function(c){
 return {'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c];});}
function getJSON(p){return fetch(ROOT+p).then(function(r){return r.ok?r.json():null;}).catch(function(){return null;});}
var GP=null,IX=null,PC={};
function graph(){if(!GP)GP=getJSON('data/road_graph_wide.json').then(function(g){return g&&g.nodes?build(g):null;});return GP;}
function index(){if(!IX)IX=getJSON('data/pics/index.json');return IX;}
function cell(k){if(!PC[k])PC[k]=getJSON('data/pics/'+k+'.json').then(function(r){return r||[];});return PC[k];}
function rowsIn(b){return index().then(function(ix){if(!ix)return [];
 return Promise.all(cellKeys(ix,b[0],b[1],b[2],b[3]).slice(0,400).map(cell))
  .then(function(a){return [].concat.apply([],a);});});}
function len(m){if(m<1000){var r=Math.max(10,Math.round(m/10)*10);return [r+' ม.',r+' m'];}
 var k=(m/1000).toFixed(m<10000?1:0);return [k+' กม.',k+' km'];}
var TH_M=['ม.ค.','ก.พ.','มี.ค.','เม.ย.','พ.ค.','มิ.ย.','ก.ค.','ส.ค.','ก.ย.','ต.ค.','พ.ย.','ธ.ค.'],
 EN_M=['Jan','Feb','Mar','Apr','May','Jun','Jul','Aug','Sep','Oct','Nov','Dec'];
function day(r){var iso=r[6];if(!iso)return '';var m=+iso.slice(5,7)-1,d=+iso.slice(8,10),t=r[7]?' '+esc(r[7]):'';
 return bi(d+' '+TH_M[m]+t,d+' '+EN_M[m]+t);}
function card(r,th,en){var u=function(p){return esc(ROOT+String(p).replace(/^\//,''));};
 return '<a class="pic" href="'+u(r[3])+'"><img src="'+u(r[2])+'" alt="'+esc(r[5]||r[4])+'" loading="lazy"'+
  (r[10]?' width="'+r[10]+'" height="'+r[11]+'"':'')+'><span class="cap"><b>'+esc(r[4]||r[5])+'</b><i>'+
  bi(th,en)+'</i><i>'+day(r)+'</i></span></a>';}
var CSS='.waypics .wayout[hidden]{display:none}.waypics .wayout{margin:.35rem 0 .8rem;min-width:0}'+
'.waypics .pichead{margin:0 0 .35rem;font-weight:800;font-size:.92rem;line-height:1.3}'+
'.waypics .pichead .rowicon{vertical-align:-4px;margin-right:.3rem}'+
'.waypics .src,.waypics .note,.waypics .piccred{font-weight:400;font-size:.72rem;color:var(--mute)}.waypics .src{display:block}'+
'.waypics .note{margin:.1rem 0 .4rem}.waypics .piccred{margin:.1rem 0 0}'+
'.waypics .pics{display:flex;gap:.5rem;overflow-x:auto;scroll-snap-type:x mandatory;padding-bottom:.35rem;-webkit-overflow-scrolling:touch}'+
'.waypics a.pic{flex:0 0 auto;width:min(46vw,190px);scroll-snap-align:start;text-decoration:none;color:var(--ink);'+
'border:2px solid var(--ink);background:var(--card);display:flex;flex-direction:column}'+
'.waypics a.pic.here{border-color:var(--ant)}'+
'.waypics a.pic img{width:100%;height:auto;aspect-ratio:4/3;object-fit:cover;display:block}'+
'.waypics .cap{padding:.3rem .4rem .4rem;font-size:.74rem;line-height:1.25}'+
'.waypics .cap b{display:-webkit-box;-webkit-line-clamp:2;-webkit-box-orient:vertical;overflow:hidden}'+
'.waypics .cap i{display:flex;flex-wrap:wrap;align-items:center;gap:.2rem;font-style:normal;'+
'font-family:ui-monospace,Menlo,monospace;font-size:.66rem;color:var(--mute);margin-top:.2rem}'+
'.waypics .modes{display:flex;gap:.4rem;margin:.1rem 0 .4rem}'+
'.waypics .modes button{font:inherit;font-size:.78rem;border:1.5px solid var(--warm-border);background:var(--card);'+
'color:var(--ink);border-radius:.5rem;padding:.25rem .6rem;display:inline-flex;align-items:center;gap:.3rem;cursor:pointer}'+
'.waypics .modes button[aria-pressed=true]{border-color:var(--ant);color:var(--ant-dark);font-weight:700}';
function style(){if(document.getElementById('waypics-css'))return;var s=document.createElement('style');
 s.id='waypics-css';s.textContent=CSS;document.head.appendChild(s);}
var WHY={you:['ตำแหน่งของคุณอยู่นอกแผนที่ถนนของเรา','You are outside our road map'],
 place:['ที่นี่อยู่นอกแผนที่ถนนของเรา','This place is outside our road map'],
 noroute:['หาทางบนถนนไม่เจอ','No way found by road'],
 nograph:['โหลดแผนที่ถนนไม่ได้','The road map did not load']};
function say(out,html){out.innerHTML=html;out.hidden=false;}
var CRED='<p class="piccred">ภาพ · pictures NaN Peacock, CC BY 4.0</p>';
function draw(box,P,mode){var out=box.querySelector('.wayout'),T=box.dataset.to.split(',').map(Number),own=box.dataset.own||'';
 say(out,'<p class="note">'+bi('กำลังหาทาง','Finding the way')+'…</p>');
 graph().then(function(G){var R=plan(G,P,T,mode);
  var b=R.path?bbox(R.path,0.0005):bbox([T],0.0065);
  var bt=bbox([T],0.0065);b=[Math.min(b[0],bt[0]),Math.min(b[1],bt[1]),Math.max(b[2],bt[2]),Math.max(b[3],bt[3])];
  return rowsIn(b).then(function(rows){var A=around(T,rows,own),html='';
   var ownCards=A.own.map(function(o){return card(o.r,'ถึงแล้ว','arrived').replace('class="pic"','class="pic here"');}).join('');
   if(R.path){var K=pick(R.path,rows,own),L=len(R.m),mins=Math.max(1,Math.round(R.m/MODES[mode].mpm));
    var mv=mode==='ride'?['ขี่ '+mins+' นาที',mins+' min by scooter']:['เดิน '+mins+' นาที',mins+' min on foot'];
    html='<p class="pichead">'+icon('i-route',18)+bi('ทางมาที่นี่ '+L[0],'The way here, '+L[1])+
     '<span class="src">'+bi(mv[0],mv[1])+' · '+bi('ภาพตามทาง '+K.pics.length,K.pics.length+' pictures on the way')+'</span></p>'+
     '<div class="modes">'+['ride','foot'].map(function(m){return '<button type="button" data-mode="'+m+'" aria-pressed="'+(m===mode)+'">'+
      (m==='ride'?icon('i-scooter',16)+bi('ขี่','Ride'):icon('i-walk',16)+bi('เดิน','Walk'))+'</button>';}).join('')+'</div>';
    var cards=K.pics.map(function(o){var l=len(o.along);return card(o.r,'ในอีก '+l[0],'in '+l[1]);}).join('');
    if(!cards){html+='<p class="note">'+bi('ทางนี้ไม่ผ่านภาพของแนน ภาพใกล้ที่นี่','Her pictures miss this way; these are near the place')+'</p>';
     cards=A.near.slice(0,20).map(function(o){var l=len(o.d);return card(o.r,'ห่างจากที่นี่ '+l[0],l[1]+' from here');}).join('');}
    html+=(cards||ownCards?'<div class="pics">'+cards+ownCards+'</div>'+CRED:'');}
   else{var C=len(R.crow),w=WHY[R.why]||WHY.noroute;
    html='<p class="pichead">'+icon('i-route',18)+bi('ช่วงสุดท้าย','The last stretch')+
     '<span class="src">'+bi(w[0],w[1])+' · '+bi('ระยะเส้นตรง '+C[0],'straight-line '+C[1])+'</span></p>';
    var near=A.near.slice(0,20).map(function(o){var l=len(o.d);return card(o.r,'ห่างจากที่นี่ '+l[0],l[1]+' from here');}).join('');
    html+=(near||ownCards)?'<div class="pics">'+near+ownCards+'</div>'+CRED:
     '<p class="note">'+bi('ไม่มีภาพของแนนในระยะ 600 ม.','None of her pictures within 600 m')+'</p>';}
   say(out,html);
   out.querySelectorAll('.modes button').forEach(function(bt){bt.addEventListener('click',function(){
    if(bt.dataset.mode!==mode)draw(box,P,bt.dataset.mode);});});});});}
function go(btn){style();var box=btn.closest('.waypics');if(!box)return;var out=box.querySelector('.wayout');
 btn.disabled=true;graph();
 var pos=window.MDWAYP||new Promise(function(y,n){navigator.geolocation?navigator.geolocation.getCurrentPosition(y,n,
  {enableHighAccuracy:true,timeout:20000,maximumAge:60000}):n();});
 window.MDWAYP=null;
 say(out,'<p class="note">'+bi('กำลังหาตำแหน่งของคุณ','Finding where you are')+'…</p>');
 pos.then(function(p){btn.disabled=false;draw(box,[p.coords.latitude,p.coords.longitude],'ride');},
  function(){btn.disabled=false;say(out,'<p class="note">'+bi('ไม่ได้ตำแหน่ง ลองอนุญาตตำแหน่งแล้วแตะอีกครั้ง',
   'No position; allow location and tap again')+'</p>');});}
window.MDWAY=go;
var pend=document.querySelector('.waypics .waybtn[disabled]');if(pend)go(pend);
})();
"""

JS_V = f"{zlib.crc32(JS.encode('utf-8')) & 0xFFFFFFFF:08x}"
