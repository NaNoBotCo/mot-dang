#!/usr/bin/env python3
"""Road distance to the nearest toilet — in the browser from wherever the
reader stands, and baked into every place page from the place itself.

Nan, 2026-10-02: toilets are "road distance away, not as the crow flies", and
findable from the front page and every place page. WO-93 plan B (precompute
offline) covers the place page; the reader's own position cannot be
precomputed, so the browser routes it over the squares of road network around
them (importers/build_road_tiles.py), fetching a few kilobytes, not the
province.

Both sides do the same arithmetic. A point joins the network where it projects
onto the nearest road edge — not the nearest junction, which on a long rural
road can be a kilometre off — and the short leg from the point to the road is
walked straight. On the edge itself the router may only go the ways the mode
allows: oneway binds a scooter, not a walker (build_road_graph.py).

    emit(g)                 docs/road-near.js + docs/data/roads/  (the tiles)
    prepare(rows)           build-time multi-source search from every
                            walk-in toilet, once, before place pages fork
    place_line(r, rel, bi)  the 🚻 line under a place's title
"""
import heapq
import json
import math
import shutil
from pathlib import Path

ROOT = Path(__file__).resolve().parent
TILES = ROOT / "cache" / "road_tiles"
GRAPH = ROOT / "cache" / "road_graph_prov.json"

WALK_M_PER_MIN = 80          # toilets_layer.WALK_M_PER_MIN
RIDE_M_PER_MIN = 300         # 18 km/h, plan.html's ride pace
SNAP_MAX_M = 400             # farther than this from any road: not on the network
PLACE_REACH_M = 5000         # a place page names a toilet within this walk

FOOT = (1, 2)
RIDE = (4, 8)


def _metres_xy(lat0):
    return 111320.0 * math.cos(math.radians(lat0)), 110574.0


def _hav(a_lat, a_lng, b_lat, b_lng):
    R = 6371000.0
    p1, p2 = math.radians(a_lat), math.radians(b_lat)
    h = (math.sin(math.radians(b_lat - a_lat) / 2) ** 2
         + math.cos(p1) * math.cos(p2) * math.sin(math.radians(b_lng - a_lng) / 2) ** 2)
    return 2 * R * math.asin(math.sqrt(h))


class Net:
    """The province graph with a grid over its edge segments, for projecting a
    point onto the nearest road."""
    CELL = 0.002

    def __init__(self, g):
        s = float(g["scale"])
        self.nodes = [(a / s, b / s) for a, b in g["nodes"]]
        self.edges = []          # (a, b, metres, flags, [(lat,lng)...] full polyline)
        for a, b, m, f, enc in g["edges"]:
            pts = [self.nodes[a]]
            la = ln = None
            for i in range(0, len(enc), 2):
                if la is None:
                    la, ln = enc[i], enc[i + 1]
                else:
                    la, ln = la + enc[i], ln + enc[i + 1]
                pts.append((la / s, ln / s))
            pts.append(self.nodes[b])
            self.edges.append((a, b, m, f, pts))
        self.grid = {}
        c = self.CELL
        for k, (_, _, _, _, pts) in enumerate(self.edges):
            for i in range(len(pts) - 1):
                (y1, x1), (y2, x2) = pts[i], pts[i + 1]
                for cy in range(math.floor(min(y1, y2) / c), math.floor(max(y1, y2) / c) + 1):
                    for cx in range(math.floor(min(x1, x2) / c), math.floor(max(x1, x2) / c) + 1):
                        self.grid.setdefault((cy, cx), set()).add(k)
        self.adj = {}

    def adjacency(self, mode, reverse=False):
        key = (mode, reverse)
        if key in self.adj:
            return self.adj[key]
        fwd, back = FOOT if mode == "foot" else RIDE
        adj = [[] for _ in self.nodes]
        for a, b, m, f, _ in self.edges:
            if f & fwd:
                (adj[b] if reverse else adj[a]).append(((a if reverse else b), m))
            if f & back:
                (adj[a] if reverse else adj[b]).append(((b if reverse else a), m))
        self.adj[key] = adj
        return adj

    def project(self, lat, lng, bits=3):
        """(edge, metres along it from its first node, metres off the road), or
        None when no road lies within SNAP_MAX_M."""
        kx, ky = _metres_xy(lat)
        c = self.CELL
        cy0, cx0 = math.floor(lat / c), math.floor(lng / c)
        best = None
        for ring in (1, 2):
            cand = set()
            for cy in range(cy0 - ring, cy0 + ring + 1):
                for cx in range(cx0 - ring, cx0 + ring + 1):
                    cand |= self.grid.get((cy, cx), set())
            for k in cand:
                a, b, m, f, pts = self.edges[k]
                if not f & bits:
                    continue
                geo = 0.0
                seg = []
                for i in range(len(pts) - 1):
                    (y1, x1), (y2, x2) = pts[i], pts[i + 1]
                    ax, ay = (x1 - lng) * kx, (y1 - lat) * ky
                    bx, by = (x2 - lng) * kx, (y2 - lat) * ky
                    dx, dy = bx - ax, by - ay
                    L2 = dx * dx + dy * dy
                    t = 0.0 if L2 == 0 else max(0.0, min(1.0, -(ax * dx + ay * dy) / L2))
                    px, py = ax + t * dx, ay + t * dy
                    d = math.hypot(px, py)
                    L = math.sqrt(L2)
                    seg.append((d, geo + t * L))
                    geo += L
                d, at = min(seg)
                if best is None or d < best[2]:
                    # scale the drawn length to the edge's stored metres
                    best = (k, at * (m / geo) if geo else 0.0, d)
            if best is not None and best[2] <= ring * c * ky * 0.9:
                break
        if best is None or best[2] > SNAP_MAX_M:
            return None
        return best


# ------------------------------------------------------------------ build side

_NEAR = None      # per node: (metres to nearest toilet, toilet index)
_NET = None
_ROWS = []


def prepare(rows):
    """rows: [(lat, lng, payload)] — every door anyone may walk into. One
    search outward from all of them at once over the walking graph, reversed,
    so every junction learns its nearest toilet by road. Place pages then cost
    a projection each."""
    global _NEAR, _NET, _ROWS
    if not GRAPH.exists():
        print("  loo_road: no cache/road_graph_prov.json — place pages get no toilet line")
        return 0
    _NET = net = Net(json.loads(GRAPH.read_text()))
    _ROWS = rows
    radj = net.adjacency("foot", reverse=True)
    INF = float("inf")
    dist = [INF] * len(net.nodes)
    who = [-1] * len(net.nodes)
    pq = []
    for i, (lat, lng, _) in enumerate(rows):
        p = net.project(lat, lng)
        if p is None:
            continue
        k, at, off = p
        a, b, m, f, _ = net.edges[k]
        # reaching the toilet from a means walking a→b along the edge
        if f & 1 and off + at < dist[a]:
            dist[a], who[a] = off + at, i
            heapq.heappush(pq, (dist[a], a))
        if f & 2 and off + (m - at) < dist[b]:
            dist[b], who[b] = off + (m - at), i
            heapq.heappush(pq, (dist[b], b))
    while pq:
        d, u = heapq.heappop(pq)
        if d > dist[u] or d > PLACE_REACH_M:
            continue
        for v, w in radj[u]:
            nd = d + w
            if nd < dist[v]:
                dist[v], who[v] = nd, who[u]
                heapq.heappush(pq, (nd, v))
    _NEAR = (dist, who)
    return sum(1 for x in who if x >= 0)


def nearest(lat, lng):
    """(metres by road on foot, payload) of the nearest walk-in toilet, or None."""
    if _NEAR is None:
        return None
    p = _NET.project(lat, lng)
    if p is None:
        return None
    k, at, off = p
    a, b, m, f, _ = _NET.edges[k]
    dist, who = _NEAR
    best = None
    if f & 2 and who[a] >= 0:                 # walk toward a: b→a direction
        best = (off + at + dist[a], who[a])
    if f & 1 and who[b] >= 0:
        c = off + (m - at) + dist[b]
        if best is None or c < best[0]:
            best = (c, who[b])
    if best is None or best[0] > PLACE_REACH_M:
        return None
    return best[0], _ROWS[best[1]][2]


def place_line(r, bi, att, esc, rel="../../"):
    """The 🚻 line under a place's title: the nearest door anyone may walk
    into, by road on foot from this place, and a door to the toilets page
    starting here. Every place with a position gets the door; the named
    toilet only when one is within PLACE_REACH_M by road."""
    if r.get("lat") is None:
        return ""
    name_th = r.get("nameTh") or r.get("name") or ""
    name_en = r.get("nameEn") or name_th
    import urllib.parse
    more = (f'{rel}toilets.html?at={r["lat"]:.5f},{r["lng"]:.5f}'
            f'&th={urllib.parse.quote(name_th[:80])}&en={urllib.parse.quote(name_en[:80])}')
    hit = nearest(r["lat"], r["lng"])
    if hit is None:
        return (f'<p class="looline"><a class="loomore" href="{att(more)}">🚻 '
                f'{bi("ห้องน้ำใกล้ที่นี่", "Toilets near here")}</a></p>')
    m, d = hit
    if d.get("id") and d["id"] == r.get("id"):
        return (f'<p class="looline">🚻 {bi("ที่แบบนี้มักมีห้องน้ำให้ใช้", "Places like this normally have a toilet")}'
                f' · <a class="loomore" href="{att(more)}">{bi("ที่อื่นใกล้ ๆ", "others nearby")}</a></p>')
    dist = f"{round(m / 10) * 10} ม." if m < 1000 else f"{m / 1000:.1f} กม."
    dist_en = f"{round(m / 10) * 10} m" if m < 1000 else f"{m / 1000:.1f} km"
    mins = max(1, round(m / WALK_M_PER_MIN))
    nm = bi(d["th"], d["en"]) if d["en"] else f'<span class="th">{esc(d["th"])}</span>'
    if d.get("href"):
        nm = f'<a href="{rel}{att(d["href"])}.html">{nm}</a>'
    return (f'<p class="looline">🚻 {bi("ห้องน้ำใกล้สุด", "Nearest toilet")}: {d["e"]} {nm}'
            f' · <b>{bi(dist + " ตามถนน", dist_en + " by road")}</b>'
            f' · {bi(f"เดิน ~{mins} นาที", f"~{mins} min walk")}'
            f' · <a class="loomore" href="{att(more)}">{bi("ที่อื่นจากตรงนี้", "more from here")}</a></p>')


# ------------------------------------------------------------------ browser side

def emit(g):
    """Copy the squares into docs and write the client. Returns the tile count."""
    docs = g["DOCS"]
    (docs / "road-near.js").write_text(JS)
    if not (TILES / "index.json").exists():
        return 0
    out = docs / "data" / "roads"
    out.mkdir(parents=True, exist_ok=True)
    n = 0
    for f in TILES.glob("*.json"):
        dst = out / f.name
        if not dst.exists() or dst.stat().st_size != f.stat().st_size \
                or dst.stat().st_mtime < f.stat().st_mtime:
            shutil.copy2(f, dst)
        n += 1
    return n - 1


DOOR_TILE = 0.01


def emit_doors(docs, rows):
    """The walk-in doors cut into the same ~1 km squares as the roads, so the
    front page can name the nearest one without the 1.4 MB toilets.json."""
    out = docs / "data" / "loo"
    out.mkdir(parents=True, exist_ok=True)
    sq = {}
    for lat, lng, d in rows:
        k = f"{math.floor(lat / DOOR_TILE)}_{math.floor(lng / DOOR_TILE)}"
        sq.setdefault(k, []).append([round(lat, 5), round(lng, 5), d["e"], d["th"], d["en"], d["href"],
                                     d.get("w") or 0])
    keep = set()
    for k, v in sq.items():
        body = json.dumps(v, ensure_ascii=False, separators=(",", ":"))
        f = out / f"{k}.json"
        keep.add(f.name)
        if not f.exists() or f.read_text() != body:
            f.write_text(body)
    for f in out.glob("*.json"):
        if f.name not in keep and f.name != "index.json":
            f.unlink()
    (out / "index.json").write_text(json.dumps({"tile": DOOR_TILE, "tiles": sorted(sq)},
                                               separators=(",", ":")))
    (docs / "loo-front.js").write_text(FRONT_JS)
    return len(sq)


FRONT_JS = r"""/* loo-front.js — the nearest toilet by road, named on the front page under
   Near. Only when this browser has already allowed location: the front page
   asks nobody anything; the 🚻 button in the bar is the door for everyone
   else. Loads road-near.js and the few squares of roads and doors around the
   reader. */
(function(){
var el=document.getElementById('looNear');if(!el||!navigator.permissions||!navigator.geolocation)return;
function esc(s){return String(s==null?'':s).replace(/[&<>"']/g,function(c){
  return {'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c];});}
function bi(th,en){return '<span class="bi"><span class="th" lang="th">'+esc(th)+'</span><span class="en" lang="en">'+esc(en)+'</span></span>';}
function hav(a,b,c,d){var R=6371000,p1=a*Math.PI/180,p2=c*Math.PI/180,dp=(c-a)*Math.PI/180,dl=(d-b)*Math.PI/180,
  h=Math.sin(dp/2)*Math.sin(dp/2)+Math.cos(p1)*Math.cos(p2)*Math.sin(dl/2)*Math.sin(dl/2);return 2*R*Math.asin(Math.sqrt(h));}
function script(){return window.MDROAD?Promise.resolve():new Promise(function(ok,no){
  var s=document.createElement('script');s.src='/road-near.js';s.onload=ok;s.onerror=no;document.head.appendChild(s);});}
function doors(la,ln,reach){return fetch('/data/loo/index.json').then(function(r){return r.json();}).then(function(I){
  var T=I.tile,set={},ks=[];I.tiles.forEach(function(k){set[k]=1;});
  var dy=reach/110574,dx=reach/(111320*Math.cos(la*Math.PI/180));
  for(var y=Math.floor((la-dy)/T);y<=Math.floor((la+dy)/T);y++)for(var x=Math.floor((ln-dx)/T);x<=Math.floor((ln+dx)/T);x++)
    if(set[y+'_'+x])ks.push(y+'_'+x);
  return Promise.all(ks.map(function(k){return fetch('/data/loo/'+k+'.json').then(function(r){return r.ok?r.json():[];}).catch(function(){return [];});}));
}).then(function(a){return [].concat.apply([],a);});}
function fmt(m){return m<1000?[Math.round(m/10)*10+' ม.',Math.round(m/10)*10+' m']:[(m/1000).toFixed(1)+' กม.',(m/1000).toFixed(1)+' km'];}
navigator.permissions.query({name:'geolocation'}).then(function(st){
  if(st.state!=='granted')return;
  navigator.geolocation.getCurrentPosition(function(p){
    var la=p.coords.latitude,ln=p.coords.longitude;
    (function step(reach){
      Promise.all([script(),doors(la,ln,reach)]).then(function(r){
        /* the class's usual hours, Bangkok time: a wat at 2 a.m. is not the answer */
        var h=(new Date().getUTCHours()+7)%24+new Date().getUTCMinutes()/60;
        function open(w){if(!w)return true;return w[1]<=w[0]?(h>=w[0]||h<w[1]):(h>=w[0]&&h<w[1]);}
        var all=r[1].map(function(d){return {d:d,c:hav(la,ln,d[0],d[1])};}),on=all.filter(function(x){return open(x.d[6]);});
        var D=(on.length?on:all).sort(function(a,b){return a.c-b.c;}).slice(0,40);
        if(!D.length){if(reach<5000)step(5000);return;}
        return MDROAD.from(la,ln,{mode:'foot',reach:reach}).then(function(R){
          var best=null;D.forEach(function(x){x.r=R?R.to(x.d[0],x.d[1]):null;
            var m=x.r!=null?x.r:Infinity;if(m<(best?best.m:Infinity))best={m:m,d:x.d};});
          if(!best&&reach<5000){step(5000);return;}
          if(!best)return;
          var d=best.d,f=fmt(best.m),mins=Math.max(1,Math.round(best.m/80)),
              nm=d[4]?bi(d[3],d[4]):esc(d[3]),href=d[5]?'/'+d[5]+'.html':'/toilets.html';
          el.innerHTML='🚻 '+bi('ห้องน้ำใกล้สุด','Nearest toilet')+': '+esc(d[2])+' <a href="'+esc(href)+'">'+nm+'</a> · <b>'+
            bi(f[0]+' ตามถนน · เดิน ~'+mins+' นาที',f[1]+' by road · ~'+mins+' min walk')+'</b> · <a href="/toilets.html">'+
            bi('ที่อื่น','more')+'</a>';
          el.hidden=false;});
      }).catch(function(){});
    })(1800);
  },function(){},{maximumAge:600000,timeout:8000});
}).catch(function(){});
})();
"""


JS = r"""/* road-near.js — road distance from one point to many, in the browser.
   Fetches the ~1 km squares of road network around the origin
   (data/roads/<y>_<x>.json), runs one shortest-path search outward from it,
   then answers any destination in reach. Same arithmetic as loo_road.py:
   points join the network where they project onto the nearest road edge,
   oneway binds a scooter and not a walker.

   MDROAD.from(lat,lng,{mode:'foot'|'ride',reach:metres}) → Promise of
     null (no roads here) or R:
     R.to(lat,lng)   → metres by road, or null past reach / off the network
     R.path(lat,lng) → [[lat,lng],...] the route, for drawing
   MDROAD.along([[lat,lng],...]) → Promise of null or A, over the squares the
   line passes through (plan.html's spoken turns):
     A.name(lat,lng)     → [th,en,ref] of the named road within 25 m, or null
     A.junction(lat,lng) → true where three or more roads meet
*/
(function(){
var S=document.currentScript,BASE=(S&&S.src||'').replace(/road-near\.js.*$/,'');
var IDX=null,TILES={};
function getIdx(){return IDX||(IDX=fetch(BASE+'data/roads/index.json').then(function(r){
  if(!r.ok)throw 0;return r.json();}).then(function(j){j.set={};
  j.tiles.forEach(function(k){j.set[k]=1;});return j;}).catch(function(){IDX=null;return null;}));}
/* at most eight squares in flight: a long leg asks for a hundred, and a
   browser handed them all at once refuses some (ERR_INSUFFICIENT_RESOURCES) */
var FLY=0,WAIT=[];
function slot(){return FLY<8?(FLY++,Promise.resolve()):new Promise(function(ok){WAIT.push(ok);});}
function free(){var n=WAIT.shift();if(n)n();else FLY--;}
function getTile(k){return TILES[k]||(TILES[k]=slot().then(function(){return fetch(BASE+'data/roads/'+k+'.json');})
  .then(function(r){free();return r.ok?r.json():null;},function(){free();delete TILES[k];return null;}));}

function Heap(){this.k=[];this.v=[];}
Heap.prototype.push=function(key,val){var k=this.k,v=this.v,i=k.length;k.push(key);v.push(val);
  while(i>0){var p=(i-1)>>1;if(k[p]<=key)break;k[i]=k[p];v[i]=v[p];i=p;}k[i]=key;v[i]=val;};
Heap.prototype.pop=function(){var k=this.k,v=this.v,top=v[0],tk=k[0],lk=k.pop(),lv=v.pop(),n=k.length;
  if(n){var i=0;for(;;){var l=2*i+1,r=l+1,m=i,mk=lk;
    if(l<n&&k[l]<mk){m=l;mk=k[l];}if(r<n&&k[r]<mk){m=r;mk=k[r];}
    if(m===i)break;k[i]=k[m];v[i]=v[m];i=m;}k[i]=lk;v[i]=lv;}
  this.lastKey=tk;return top;};

function build(tiles,SC){
  var key={},lat=[],lng=[],E=[],seen={};
  function node(q){var kk=q[0]*1e8+q[1],id=key[kk];
    if(id===undefined){id=key[kk]=lat.length;lat.push(q[0]/SC);lng.push(q[1]/SC);}return id;}
  tiles.forEach(function(t){if(!t)return;var ids=t.n.map(node);
    t.e.forEach(function(e,j){var a=ids[e[0]],b=ids[e[1]],sk=a+','+b+','+e[2];
      if(seen[sk])return;seen[sk]=1;
      var pts=[[lat[a],lng[a]]],g=e[4],la=0,ln=0;
      for(var i=0;i<g.length;i+=2){if(i===0){la=g[0];ln=g[1];}else{la+=g[i];ln+=g[i+1];}
        pts.push([la/SC,ln/SC]);}
      pts.push([lat[b],lng[b]]);
      E.push({a:a,b:b,m:e[2],f:e[3],p:pts,nm:(t.w&&t.ni&&t.ni[j]>=0)?t.w[t.ni[j]]:null});});});
  /* grid over segments, ~110 m cells, for projection */
  var C=0.001,grid={};
  E.forEach(function(e,k){var p=e.p;for(var i=0;i<p.length-1;i++){
    var y0=Math.floor(Math.min(p[i][0],p[i+1][0])/C),y1=Math.floor(Math.max(p[i][0],p[i+1][0])/C),
        x0=Math.floor(Math.min(p[i][1],p[i+1][1])/C),x1=Math.floor(Math.max(p[i][1],p[i+1][1])/C);
    for(var y=y0;y<=y1;y++)for(var x=x0;x<=x1;x++){var c=y+'_'+x;(grid[c]||(grid[c]=[])).push(k);}}});
  return {lat:lat,lng:lng,E:E,grid:grid,C:C};
}

/* the roads this mode may use within 400 m of a point, nearest first, at
   most six */
function near(G,la,ln,bits){
  var kx=111320*Math.cos(la*Math.PI/180),ky=110574,C=G.C,cy=Math.floor(la/C),cx=Math.floor(ln/C),R=5,by={},out=[];
  for(var y=cy-R;y<=cy+R;y++)for(var x=cx-R;x<=cx+R;x++){var L=G.grid[y+'_'+x];if(!L)continue;
    for(var j=0;j<L.length;j++){var k=L[j];if(by[k]||!(G.E[k].f&bits))continue;
      var e=G.E[k],p=e.p,geo=0,bd=1e18,bat=0;
      for(var i=0;i<p.length-1;i++){
        var ax=(p[i][1]-ln)*kx,ay=(p[i][0]-la)*ky,bx=(p[i+1][1]-ln)*kx,bY=(p[i+1][0]-la)*ky,
            dx=bx-ax,dy=bY-ay,L2=dx*dx+dy*dy,t=L2?Math.max(0,Math.min(1,-(ax*dx+ay*dy)/L2)):0,
            px=ax+t*dx,py=ay+t*dy,d=Math.sqrt(px*px+py*py),sl=Math.sqrt(L2);
        if(d<bd){bd=d;bat=geo+t*sl;}geo+=sl;}
      by[k]={k:k,at:geo?bat*e.m/geo:0,off:bd,geo:geo};if(bd<=400)out.push(by[k]);}}
  out.sort(function(a,b){return a.off-b.off;});
  return out.slice(0,6);
}

/* the polyline of edge e from fraction `from` to `to` (metres along), in order */
function piece(e,from,to){
  var p=e.p,geo=0,lens=[],tot=0,i;
  for(i=0;i<p.length-1;i++){var d=Math.hypot((p[i+1][0]-p[i][0])*110574,
    (p[i+1][1]-p[i][1])*111320*Math.cos(p[i][0]*Math.PI/180));lens.push(d);tot+=d;}
  var s=tot?e.m/tot:1;function at(m){var g=m/s,acc=0;
    for(var j=0;j<lens.length;j++){if(acc+lens[j]>=g){var t=lens[j]?(g-acc)/lens[j]:0;
      return [j,[p[j][0]+t*(p[j+1][0]-p[j][0]),p[j][1]+t*(p[j+1][1]-p[j][1])]];}acc+=lens[j];}
    return [lens.length-1,p[p.length-1]];}
  var A=at(Math.min(from,to)),B=at(Math.max(from,to)),out=[A[1]];
  for(i=A[0]+1;i<=B[0];i++)out.push(p[i]);out.push(B[1]);
  return from<=to?out:out.reverse();
}

function hv(a,b,c,d){var p1=a*Math.PI/180,p2=c*Math.PI/180,dp=p2-p1,dl=(d-b)*Math.PI/180,
  h=Math.sin(dp/2)*Math.sin(dp/2)+Math.cos(p1)*Math.cos(p2)*Math.sin(dl/2)*Math.sin(dl/2);
  return 12742000*Math.asin(Math.sqrt(h));}
/* opt.to=[lat,lng]: one destination, so only the squares in an ellipse round
   the two ends are fetched — a road more than a third longer than the crow,
   plus a kilometre, is not looked for — and reach becomes that bound. */
function from(la,ln,opt){
  opt=opt||{};var mode=opt.mode==='ride'?'ride':'foot',reach=opt.reach||2500,
      FW=mode==='ride'?4:1,BK=mode==='ride'?8:2,to=opt.to,
      bound=to?hv(la,ln,to[0],to[1])*1.35+1000:0;
  if(to)reach=bound;
  return getIdx().then(function(I){if(!I)return null;
    var T=I.tile,dy=reach/110574+T,dx=reach/(111320*Math.cos(la*Math.PI/180))+T,ks=[];
    for(var y=Math.floor((la-dy)/T);y<=Math.floor((la+dy)/T);y++)
      for(var x=Math.floor((ln-dx)/T);x<=Math.floor((ln+dx)/T);x++){
        if(!I.set[y+'_'+x])continue;
        if(to){var cy=(y+.5)*T,cx=(x+.5)*T;
          if(hv(cy,cx,la,ln)+hv(cy,cx,to[0],to[1])>bound+1600)continue;}
        ks.push(y+'_'+x);}
    if(!ks.length)return null;
    return Promise.all(ks.map(getTile)).then(function(ts){
      /* The nearest road to a pin can be a car-park lane or a courtyard path
         that joins nothing (Central Festival's pin sits on one), and a search
         seeded there finds no road to anywhere. So: seed the nearest; if the
         search settles under a hundred junctions, try the next road out (up
         to four), and keep the run that reached the most. The far end is the
         nearest road the search did reach. Never several seeds at once — on
         the moat that let a scooter start on the other carriageway. */
      var G=build(ts,I.scale),os=near(G,la,ln,FW|BK);if(!os.length)return null;
      var n=G.lat.length,adj=[],i;for(i=0;i<n;i++)adj.push([]);
      G.E.forEach(function(e,k){if(e.f&FW)adj[e.a].push(k);if(e.f&BK)adj[e.b].push(k);});
      function run(o){var dist=new Float64Array(n).fill(Infinity),prev=new Int32Array(n).fill(-1),
          H=new Heap(),oe=G.E[o.k],cnt=0;
        /* leave the origin's edge toward b (forward) or a (back) */
        if(oe.f&FW){dist[oe.b]=o.off+oe.m-o.at;H.push(dist[oe.b],oe.b);}
        if(oe.f&BK&&o.off+o.at<dist[oe.a]){dist[oe.a]=o.off+o.at;H.push(dist[oe.a],oe.a);}
        while(H.k.length){var u=H.pop(),du=H.lastKey;if(du>dist[u]||du>reach)continue;cnt++;
          var L=adj[u];for(var j=0;j<L.length;j++){var e=G.E[L[j]],v=e.a===u?e.b:e.a,nd=du+e.m;
            if(e.a===u&&e.b===u)continue;
            if(nd<dist[v]){dist[v]=nd;prev[v]=L[j];H.push(nd,v);}}}
        return {o:o,dist:dist,prev:prev,cnt:cnt};}
      var S=null;
      for(i=0;i<os.length&&i<4;i++){var r0=run(os[i]);if(!S||r0.cnt>S.cnt)S=r0;if(S.cnt>=100)break;}
      var o=S.o,oe=G.E[o.k],dist=S.dist,prev=S.prev;
      function best(tla,tln){var ts2=near(G,tla,tln,FW|BK);
        for(var q=0;q<ts2.length;q++){var t=ts2[q],e=G.E[t.k],c=[];
          if(t.k===o.k){ /* same edge: straight along it, if the mode goes that way */
            if(t.at>=o.at?(e.f&FW):(e.f&BK))c.push({m:o.off+Math.abs(t.at-o.at)+t.off,same:1,t:t});}
          if(e.f&FW&&dist[e.a]<Infinity)c.push({m:dist[e.a]+t.at+t.off,end:e.a,t:t,dir:1});
          if(e.f&BK&&dist[e.b]<Infinity)c.push({m:dist[e.b]+e.m-t.at+t.off,end:e.b,t:t,dir:-1});
          if(!c.length)continue;c.sort(function(x,y){return x.m-y.m;});
          return c[0].m>reach?null:c[0];}
        return null;}
      return {mode:mode,reach:reach,
        to:function(a,b){var r=best(a,b);return r?r.m:null;},
        path:function(a,b){var r=best(a,b);if(!r)return null;
          if(r.same)return [[la,ln]].concat(piece(oe,o.at,r.t.at),[[a,b]]);
          var e=G.E[r.t.k],tail=piece(e,r.dir>0?0:e.m,r.t.at).concat([[a,b]]);
          var segs=[],u=r.end;
          while(prev[u]>=0){var pe=G.E[prev[u]],fw=pe.b===u;
            segs.unshift(fw?pe.p:pe.p.slice().reverse());u=fw?pe.a:pe.b;}
          var head=u===oe.b?piece(oe,o.at,oe.m):piece(oe,o.at,0),out=[[la,ln]].concat(head);
          segs.forEach(function(s){out=out.concat(s.slice(1));});
          return out.concat(tail.slice(1));}};
    });
  });
}
function along(line){
  return getIdx().then(function(I){if(!I||!line||!line.length)return null;
    var T=I.tile,want={},ks=[];
    line.forEach(function(q){var y=Math.floor(q[0]/T),x=Math.floor(q[1]/T);
      for(var dy=-1;dy<=1;dy++)for(var dx=-1;dx<=1;dx++){var k=(y+dy)+'_'+(x+dx);
        if(!want[k]&&I.set[k]){want[k]=1;ks.push(k);}}});
    if(!ks.length)return null;
    return Promise.all(ks.map(getTile)).then(function(ts){
      var G=build(ts,I.scale),deg=new Int32Array(G.lat.length),at={};
      G.E.forEach(function(e){if(e.a!==e.b){deg[e.a]++;deg[e.b]++;}});
      for(var i=0;i<G.lat.length;i++)at[Math.round(G.lat[i]*1e6)+','+Math.round(G.lng[i]*1e6)]=i;
      return {
        junction:function(la,ln){var i=at[Math.round(la*1e6)+','+Math.round(ln*1e6)];
          return i!==undefined&&deg[i]>=3;},
        name:function(la,ln){var kx=111320*Math.cos(la*Math.PI/180),ky=110574,C=G.C,
            cy=Math.floor(la/C),cx=Math.floor(ln/C),best=null,bd=25,seen={};
          for(var y=cy-1;y<=cy+1;y++)for(var x=cx-1;x<=cx+1;x++){var L=G.grid[y+'_'+x];if(!L)continue;
            for(var j=0;j<L.length;j++){var k=L[j];if(seen[k])continue;seen[k]=1;var e=G.E[k];if(!e.nm)continue;
              for(var s=0;s<e.p.length-1;s++){var p=e.p[s],q=e.p[s+1],
                  ax=(p[1]-ln)*kx,ay=(p[0]-la)*ky,bx=(q[1]-ln)*kx,by=(q[0]-la)*ky,dx=bx-ax,dy=by-ay,
                  L2=dx*dx+dy*dy,t=L2?Math.max(0,Math.min(1,-(ax*dx+ay*dy)/L2)):0,
                  d=Math.hypot(ax+t*dx,ay+t*dy);
                if(d<bd){bd=d;best=e.nm;}}}}
          return best;}};});});
}
window.MDROAD={from:from,along:along,walkPerMin:80,ridePerMin:300};
})();
"""
