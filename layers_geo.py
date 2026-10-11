#!/usr/bin/env python3
"""FOUR THINGS ON DISK THAT THE MAP HAS NEVER DRAWN.

notes/maps-grow-2026-09-08.txt §3a lists what the site already holds and has
never put on a map: 534 sois with geometry, the ย่าน boxes and circles, 68
landmarks, and the road graph. Every one of them was imported for some other
purpose — the sois to join places to streets, the zones to split a sub-shelf
that outgrew one page (WO-36), the landmarks to say "230 m north of Tha Phae
Gate" in words, the graph to plan a ride — and each ended up as a join table
serving a page, never as a shape a reader can see. The map is points only.

The tagline is รู้ทุกซอย. The sois have been on disk since WO-6 and the map
has never drawn one. That is the whole reason this file exists, and it is why
sois are first here.

WHAT THIS FILE DOES: it PROJECTS what is on disk into GeoJSON. It imports
nothing, fetches nothing, and invents no coordinate. Every number in this
docstring was counted from the files named, on 2026-09-08.

    docs/data/sois.geojson             534 features  368 kB  the named ways
    docs/data/zones.geojson             20 features   14 kB  10 boxes + 10 circles
    docs/data/landmarks.geojson         68 features   24 kB  the register as points
    docs/data/walk-bands.geojson         9 features  4.6 kB  the seed index
    docs/data/walk-bands-<seed>.geojson  3 features 71–110 kB  one seed's rings

Thirteen files, 1.20 MB in all, of which a map that draws sois, zones,
landmarks and the band index pulls 410 kB and fetches a seed's 5/10/15
rings only when somebody taps that gate.

WHAT WAS MEASURED

1. SOIS — data/streets.json, key `streets`, 1,077 named ways for the two
   provinces. 534 carry a `geom`; 543 are marked `offmap`. Every one of the
   534 is Chiang Mai — Chiang Rai holds 151 ways and geometry for none of
   them, because importers/build_streets.py has only ever been pointed at the
   CM road cache. 317 of the 534 are sois (432 of the 1,077 are, so 115 sois
   are names without a line). 495 carry an English name, 307 name a parent
   way, all 534 carry a length. 6,227 places stand along them.

   `geom` is a LIST OF PARTS, each part a list of [LAT, LNG] pairs — latitude
   first, which is the opposite of GeoJSON's order, and the trap this file
   exists to not fall into twice. 445 ways are one part; 89 come in 2 to 7
   pieces, because a named way that a road cuts in half is still one name.
   650 parts, 8,494 points in all, and no part has fewer than 2 points. So a
   one-part way is emitted as a LineString and a multi-part way as a
   MultiLineString: a soi that is genuinely in three pieces must not be drawn
   as one line joining them across the blocks in between.

   The whole set sits inside 18.756691–18.825284 N, 98.957222–99.016962 E.
   Three of those four edges are the road-graph box to six decimals; the west
   edge stops 410 m inside it. Same crawl, same afternoon, and the two layers
   can be trusted to line up.

2. ย่าน — data/curated/zones.json, key `cm`: 10 boxes and 10 circles, 20
   named parts of town. The boxes are the city (the moat rectangle and its
   named quarters), the circles the amphoe seats further out, radius 7 to 60
   km. They are approximations that people say out loud, not administrative
   boundaries, and the file's own note says so; the layer carries `shape`
   (box|circle) on every feature so a reader is never shown a circle round
   Chom Thong and left to think somebody surveyed it. A circle becomes a
   32-sided polygon: the drawn edge falls 34 m short of a 7 km circle and
   289 m short of the 60 km one, both far under the honesty of the circle.

   Zone boxes overlap by design (rim-ping runs 18.766–18.810 N and crosses
   three others) and zones.json resolves that by FIRST MATCH WINS, boxes
   before circles, top to bottom. That order is preserved as `order` on each
   feature so a map can draw and hit-test in the same order the classifier
   uses. Drawn any other way, the layer would disagree with the shelf.

3. LANDMARKS — data/curated/landmarks.json through bearings_layer.ctx(),
   which is the only correct reader: the register names RECORDS, never typed
   coordinates, and resolves each id against the catalogue at build time. 68
   landmarks, 0 unresolved: 19 temples, 8 markets, 7 malls, 5 gates, 5
   hospitals, 5 universities, 5 monuments, 4 moat corners, 3 parks, 2
   airports, 2 craft villages, 1 bridge, 1 terminal, 1 waterfall. Each keeps
   its `reach_m` — how far out that landmark can still tell you where you
   are — so a map can size the dot by the reach instead of by nothing.

4. WALK-TIME BANDS — data/road_graph.json: 9,767 junctions, 12,280 edges,
   675.9 km of road, bends delta-encoded at scale 100000. The flags carry the
   asymmetry that makes this worth doing at all: 2,456 edges are one-way to a
   scooter and 11 to a walker. 12,176 edges are walkable in at least one
   direction; 104 (flags=4) carry no foot bit at all and are dropped.

   Speed is 4.6 km/h, taken from MODES.foot in build.py's planner so that a
   band and a plan on the same page cannot disagree. 5/10/15 minutes is
   383/767/1150 m of walking.

   AN EDGE IS IN A BAND WHEN IT CAN BE WALKED END TO END within that many
   minutes. Nothing is clipped mid-block, which means the drawn boundary sits
   at junctions and the true reach runs up to one block further than the line
   — conservative, and stated rather than smoothed away.

   The bands are DISJOINT RINGS, each edge in the first band it falls in. From
   Tha Phae Gate that is 282 edges (8.8 km of street) in the first five
   minutes, 529 more (22.1 km) in the second five, 927 more (39.3 km) in the
   third — 1,738 edges, 70.2 km, once each. Drawn cumulatively the same edges
   are written 2,831 times and the nine seeds came to one 1.29 MB file.

   The shape is not a circle and the counts say so before any picture does:
   five minutes reaches 8.8 km of street from Tha Phae Gate and 4.5 km from
   แจ่งศรีภูมิ, the north-east moat corner — 800 m apart, and one of them
   reaches half as far. Why is a thing to look at on the map, not a thing to
   assert here.

   THE BOX IS 18.7567–18.8253 N, 98.9533–99.0170 E and outside it there is no
   graph, so walk_bands() RAISES OutsideGraph. It does not fall back to a
   circle. A circle drawn where the moat, the river and the one-way ring are
   is exactly the lie this layer was built to replace, and a fallback that
   looks like an answer is worse than a refusal that is one. The same refusal
   fires when a point inside the box has no walkable edge within 250 m.

   The site draws 16,665 place maps (notes §1). A band costs 0.04 s once the
   graph is loaded, so precomputing all of them is 11 minutes of build — and
   about 1.5 GB of GeoJSON at the 90 kB a seed measured here, which is the
   reason not to, not the time. So this ships as a FUNCTION plus bands for
   nine seeds — the five city gates and the four moat
   corners, the nine points of the wall, every one of them inside the box.
   42 of the 68 landmarks are inside it too; whether the other 33 in-box
   landmarks get bands is Nan's, not a decision taken here.

USAGE

    import layers_geo
    layers_geo.sois()                       # FeatureCollection
    layers_geo.zones()
    layers_geo.landmarks()
    layers_geo.walk_bands(18.7878, 98.9933) # Tha Phae Gate
    layers_geo.walk_bands(13.7563, 100.5018)  # raises OutsideGraph (Bangkok)
    layers_geo.wall_bands()                 # (index, {seed: rings})
    layers_geo.emit(globals())              # from build.py; writes docs/data/

    python3 layers_geo.py                   # every count, ~7 s
    python3 layers_geo.py 18.7878 98.9933   # one point's bands, or a refusal

NOT DONE HERE, and each is somebody's decision rather than a gap:
  · Chiang Rai has no way geometry on this disk. Not "CR has no sois".
  · No tambon polygons — that data is not held (notes §3b).
  · No bus geometry — 674 routes, names only.
  · No chip, no CSS, no JS. This file writes data. Wiring it into /map.html
    is a build.py edit, and build.py is another session's right now; the hook
    lines are written out in notes/maps-grow-2026-09-08.txt §8.
"""
import heapq
import json
import math
from pathlib import Path

ROOT = Path(__file__).resolve().parent

# Five decimals, the same cut build.geojson() makes: ~1.1 m at this latitude,
# finer than any pin here is surveyed to, and a third off the file a phone
# pulls over cell data.
PREC = 5

# 4.6 km/h — MODES.foot.kmh in build.py's route planner. Duplicated rather than
# imported so this module and its test run without loading the whole site;
# tests/test_layers_geo.py checks the two agree when build.py is importable.
WALK_KMH = 4.6
BANDS_MIN = (5, 10, 15)

# No walkable edge within this of the origin and the answer is a refusal, not
# a guess. 250 m is wider than any block in the old city.
SNAP_MAX_M = 250.0

CIRCLE_SIDES = 32          # a 32-gon: 21 m off a 7 km circle, 180 m off a 60 km one
KM_PER_DEG_LAT = 110.574   # WGS84 at 18.8° N
KM_PER_DEG_LNG = 111.320   # times cos(lat)

# The nine points of the wall. Every one is a landmark key in
# data/curated/landmarks.json and every one is inside the graph box — checked,
# not assumed, in seeds() below.
WALL_KEYS = ("tha-phae-gate", "chiang-mai-gate", "saen-pung-gate",
             "suan-dok-gate", "chang-phueak-gate",
             "chaeng-si-phum", "chaeng-katam", "chaeng-ku-hueang",
             "chaeng-hua-lin")


class OutsideGraph(Exception):
    """Asked to walk where there is no road graph. See walk_bands()."""


# ------------------------------------------------------------------ helpers --

def _fc(features, **meta):
    fc = {"type": "FeatureCollection", "features": features}
    fc.update(meta)
    return fc


def _rt(v):
    return round(v, PREC)


def _metres(alat, alng, blat, blng):
    """Local flat projection. Over a city block the curvature of the earth is
    not the error that matters; over 60 km it still is not, at the precision a
    ย่าน circle claims."""
    kx = math.cos(math.radians((alat + blat) / 2)) * KM_PER_DEG_LNG * 1000
    return math.hypot((blng - alng) * kx, (blat - alat) * KM_PER_DEG_LAT * 1000)


def _clean(ring):
    """Round, then drop a point that has become its own neighbour. Rounding to
    5 dp collapses pairs that were 30 cm apart in the source; a repeated vertex
    is not wrong but it is weight, and some strict readers call a zero-length
    segment invalid."""
    out = []
    for lng, lat in ring:
        p = [_rt(lng), _rt(lat)]
        if not out or p != out[-1]:
            out.append(p)
    return out


# ------------------------------------------------------------------- 1 sois --

def sois(root=ROOT):
    """Named ways as lines. `geom` in streets.json is [[[lat, lng], …], …] —
    parts of pairs, LATITUDE FIRST — and GeoJSON wants [lng, lat], so the swap
    happens here, once, and the test checks the result lands in Thailand.

    `places` on the record is the join table: every place the street build
    could attach to this way, either by the place's own OSM address (stated) or
    by sitting within 30 m and nearer to this way than to any other (nearest).
    The layer publishes the COUNT, not the list — the list is 6,227 ids across
    the file and belongs to the API, not to a map layer a phone downloads.
    """
    doc = json.loads((root / "data" / "streets.json").read_text())
    feats = []
    dropped_parts = 0
    for st in doc.get("streets") or []:
        geom = st.get("geom")
        if not geom:
            continue
        parts = []
        for part in geom:
            line = _clean([(p[1], p[0]) for p in part])
            if len(line) < 2:
                dropped_parts += 1     # a part that rounding collapsed to a dot
                continue
            parts.append(line)
        if not parts:
            continue
        soi_no = st.get("soi")
        props = {
            "slug": st["slug"],
            "name": st.get("name"),
            "nameEn": st.get("nameEn") or None,
            "soi": bool(soi_no),
            "province": st.get("province") or "cm",
            "length": round(st["length"]) if st.get("length") else None,
            "parent": st.get("parent") or None,
            "places": len(st.get("places") or []),
        }
        # The soi NUMBER is what a reader says ("ซอย 7"), and it is a string in
        # streets.json because sois are numbered 1, 2, 7/1. Kept beside the
        # boolean rather than folded into it.
        if soi_no:
            props["soiNo"] = soi_no
        if st.get("key"):
            props["key"] = st["key"]
        feats.append({
            "type": "Feature",
            "geometry": ({"type": "LineString", "coordinates": parts[0]}
                         if len(parts) == 1
                         else {"type": "MultiLineString", "coordinates": parts}),
            "properties": props,
        })
    return _fc(feats,
               source="data/streets.json",
               generated=doc.get("generated"),
               note=("Named ways with geometry. A way in several parts is a "
                     "MultiLineString: the gaps are real. `places` counts what "
                     "the street build attached, by stated address or within "
                     "30 m; it is not a postal address."),
               dropped_parts=dropped_parts)


# ------------------------------------------------------------------ 2 zones --

def _box_ring(b):
    s, n = b["lat"]
    w, e = b["lng"]
    return [[_rt(w), _rt(s)], [_rt(e), _rt(s)], [_rt(e), _rt(n)],
            [_rt(w), _rt(n)], [_rt(w), _rt(s)]]


def _circle_ring(lat, lng, r_km, sides=CIRCLE_SIDES):
    dlat = r_km / KM_PER_DEG_LAT
    dlng = r_km / (KM_PER_DEG_LNG * math.cos(math.radians(lat)))
    ring = []
    for i in range(sides):
        t = 2 * math.pi * i / sides
        ring.append([_rt(lng + dlng * math.sin(t)), _rt(lat + dlat * math.cos(t))])
    ring.append(ring[0])
    return ring


def zones(root=ROOT, province="cm"):
    """ย่าน as polygons. Boxes are rectangles in degrees, which is what they
    are on disk and what the classifier tests against — drawn as anything
    smoother, the layer would stop agreeing with the shelf it explains.

    `order` is the index in the file's own first-match-wins sequence, boxes
    before circles. The zones overlap; the order is the tie-break, and a map
    that draws or hit-tests in a different order gives a different answer from
    the one the site gives.
    """
    doc = json.loads((root / "data" / "curated" / "zones.json").read_text())
    z = doc.get(province) or {}
    feats = []
    order = 0
    for b in z.get("boxes") or []:
        feats.append({
            "type": "Feature",
            "geometry": {"type": "Polygon", "coordinates": [_box_ring(b)]},
            "properties": {"key": b["key"], "th": b["th"], "en": b["en"],
                           "anchors": b.get("anchors") or [],
                           "shape": "box", "province": province, "order": order},
        })
        order += 1
    for c in z.get("circles") or []:
        feats.append({
            "type": "Feature",
            "geometry": {"type": "Polygon",
                         "coordinates": [_circle_ring(c["lat"], c["lng"], c["r_km"])]},
            "properties": {"key": c["key"], "th": c["th"], "en": c["en"],
                           "anchors": c.get("anchors") or [],
                           "shape": "circle", "province": province, "order": order,
                           "r_km": c["r_km"],
                           "lat": _rt(c["lat"]), "lng": _rt(c["lng"])},
        })
        order += 1
    return _fc(feats,
               source="data/curated/zones.json",
               note=(doc.get("_note") or "")
               + " Circles are drawn as %d-sided polygons." % CIRCLE_SIDES)


# -------------------------------------------------------------- 3 landmarks --

def landmarks(root=ROOT, ctx=None):
    """The bearings register as points. The coordinates are NOT in
    landmarks.json — the register names records and bearings_layer.ctx()
    reads each pin from the catalogue at build time, which is the only way a
    landmark's coordinate stays right when the record is corrected. So this
    function goes through ctx() and never opens the register itself.

    `reach_m` is how far out this landmark can still orient somebody; the four
    moat corners reach less far than Tha Phae Gate, and a map may size the dot
    by that instead of by nothing.
    """
    if ctx is None:
        import bearings_layer
        ctx = bearings_layer.ctx()
    feats = []
    for prov, ls in ctx.landmarks.items():
        for l in ls:
            props = {"key": l["key"], "kind": l["kind"], "province": prov,
                     "th": l.get("th"), "en": l.get("en"),
                     "roman": l.get("roman") or None,
                     "reach_m": l.get("reach_m"), "at_m": l.get("at_m"),
                     "origin": bool(l.get("origin"))}
            rec = l.get("record") or {}
            if rec.get("id"):
                props["id"] = rec["id"]
            if l.get("osm"):
                # No record of its own yet — a temple still in cache/osm-worship.
                props["osm"] = l["osm"]
            feats.append({
                "type": "Feature",
                "geometry": {"type": "Point",
                             "coordinates": [_rt(l["lng"]), _rt(l["lat"])]},
                "properties": props,
            })
    return _fc(feats,
               source="data/curated/landmarks.json via bearings_layer.ctx()",
               unresolved=len(getattr(ctx, "unresolved", []) or []),
               note=("Each coordinate is read from the landmark's own record, "
                     "never typed into the register."))


# ------------------------------------------------------- 4 walk-time bands --

_GRAPH = None


def graph(root=ROOT, force=False):
    """The road graph, decoded once per process.

    Returns a dict: area, nodes [(lat, lng)], adj (per node, list of
    (other, metres, flags, edge index, forward?)), geom (per edge, the full
    polyline with its junction ends threaded back on), lengths.

    The decode mirrors loadGraph() in build.py so the Python bands and the
    browser's plan stand on the same rebuilt polylines. Bends arrive
    delta-encoded and the first pair is absolute, which is easy to get wrong
    and silent when you do: the first bend would land in the Gulf of Thailand
    and the road would still draw.
    """
    global _GRAPH
    if _GRAPH is not None and not force:
        return _GRAPH
    g = json.loads((root / "data" / "road_graph.json").read_text())
    S = g["scale"]
    nodes = [(p[0] / S, p[1] / S) for p in g["nodes"]]
    adj = [[] for _ in nodes]
    geom = []
    lengths = []
    for i, e in enumerate(g["edges"]):
        a, b, ln, flags = e[0], e[1], e[2], e[3]
        d = e[4] or []
        pts = [nodes[a]]
        la = lo = 0
        for k in range(0, len(d), 2):
            if k == 0:
                la, lo = d[0], d[1]
            else:
                la += d[k]
                lo += d[k + 1]
            pts.append((la / S, lo / S))
        pts.append(nodes[b])
        geom.append(pts)
        lengths.append(ln)
        adj[a].append((b, ln, flags, i, True))
        adj[b].append((a, ln, flags, i, False))
    _GRAPH = {"area": g["area"], "nodes": nodes, "adj": adj, "geom": geom,
              "lengths": lengths, "edges": g["edges"],
              "generated": g.get("generated"), "scale": S}
    return _GRAPH


def in_graph(lat, lng, root=ROOT):
    a = graph(root)["area"]
    return a["s"] < lat < a["n"] and a["w"] < lng < a["e"]


def _foot_ok(flags, forward):
    return bool(flags & (1 if forward else 2))


def _to_seg(plat, plng, a, b):
    """Metres from p to segment ab, and how far along ab the foot falls."""
    kx = math.cos(math.radians(plat)) * KM_PER_DEG_LNG * 1000
    ky = KM_PER_DEG_LAT * 1000
    ax, ay = (a[1] - plng) * kx, (a[0] - plat) * ky
    bx, by = (b[1] - plng) * kx, (b[0] - plat) * ky
    dx, dy = bx - ax, by - ay
    L = dx * dx + dy * dy
    t = ((-ax) * dx + (-ay) * dy) / L if L else 0.0
    t = max(0.0, min(1.0, t))
    cx, cy = ax + t * dx, ay + t * dy
    return math.hypot(cx, cy), t, math.sqrt(L)


def _snap(G, lat, lng):
    """Nearest point on the nearest foot-passable edge, and the walk from it to
    each junction. Snapping to junctions alone throws away up to a block on
    every origin, and a block is a quarter of the 5-minute band."""
    best = None
    for i, pts in enumerate(G["geom"]):
        flags = G["edges"][i][3]
        if not (flags & 3):
            continue
        run = 0.0
        for k in range(len(pts) - 1):
            d, t, seg = _to_seg(lat, lng, pts[k], pts[k + 1])
            if best is None or d < best[0]:
                best = (d, i, run + t * seg)
            run += seg
        if best and best[0] == 0.0:
            break
    if best is None or best[0] > SNAP_MAX_M:
        return None
    d, i, along = best
    # The polyline's own metric length and the edge's stored length can differ
    # by a metre or two; scale so the two walk-ins always sum to the length the
    # graph costs.
    total = 0.0
    pts = G["geom"][i]
    for k in range(len(pts) - 1):
        total += _to_seg(pts[k][0], pts[k][1], pts[k], pts[k + 1])[2]
    ln = G["lengths"][i]
    frac = (along / total) if total else 0.0
    return {"edge": i, "off_m": d, "to_a": ln * frac, "to_b": ln * (1 - frac)}


def _dijkstra(G, snap, budget):
    """Metres on foot from the snapped origin to every junction within budget.

    Seeded from BOTH ends of the snapped edge, each at its walk-in distance,
    and each only if the walk from the snap point to that end is legal on foot
    — 11 edges in this graph are one-way to a walker, and seeding both ends
    blind would let a walker leave up a stair they cannot use.
    """
    e = G["edges"][snap["edge"]]
    a, b, flags = e[0], e[1], e[3]
    dist = {}
    pq = []
    # snap point -> a is travelling against the edge's forward direction
    if _foot_ok(flags, False) and snap["to_a"] <= budget:
        dist[a] = snap["to_a"]
        heapq.heappush(pq, (snap["to_a"], a))
    if _foot_ok(flags, True) and snap["to_b"] <= budget:
        if dist.get(b, 1e18) > snap["to_b"]:
            dist[b] = snap["to_b"]
            heapq.heappush(pq, (snap["to_b"], b))
    while pq:
        d, u = heapq.heappop(pq)
        if d > dist.get(u, 1e18):
            continue
        for (v, ln, flags, _ei, fwd) in G["adj"][u]:
            if not _foot_ok(flags, fwd):
                continue
            nd = d + ln
            if nd <= budget and nd < dist.get(v, 1e18):
                dist[v] = nd
                heapq.heappush(pq, (nd, v))
    return dist


def walk_bands(lat, lng, minutes=BANDS_MIN, kmh=WALK_KMH, root=ROOT,
               props=None):
    """5/10/15 minutes on foot from one point, as a MultiLineString per band.

    RAISES OutsideGraph when the point is outside the crawled box, or inside it
    but more than SNAP_MAX_M from any walkable edge. It does not draw a circle.
    A circle here would be wrong in exactly the places this layer is for — the
    moat, the river, the sois that do not join up — and a wrong shape that
    looks like an answer is worse than no shape at all.

    An edge is in the band when it can be WALKED END TO END inside the budget.
    Nothing is clipped mid-block, so the drawn edge of a band sits at
    junctions and the real reach runs up to one block further.
    """
    G = graph(root)
    a = G["area"]
    if not in_graph(lat, lng, root):
        raise OutsideGraph(
            "no road graph at %.5f,%.5f — data/road_graph.json covers "
            "%.4f–%.4f N, %.4f–%.4f E (the old city plus about 2 km) and "
            "nothing outside it. No band drawn."
            % (lat, lng, a["s"], a["n"], a["w"], a["e"]))
    sn = _snap(G, lat, lng)
    if sn is None:
        raise OutsideGraph(
            "inside the graph box at %.5f,%.5f but no walkable road within "
            "%d m. No band drawn." % (lat, lng, SNAP_MAX_M))
    mins = sorted(minutes)
    budgets = [m / 60.0 * kmh * 1000.0 for m in mins]
    dist = _dijkstra(G, sn, budgets[-1])

    # THE BANDS ARE DISJOINT RINGS, not three nested copies. Drawn cumulatively
    # the same edge is written three times: measured at Tha Phae Gate that is
    # 2,831 edge-drawings against 1,738 real edges, and the one file came out
    # at 1.29 MB — on a site where Nan said this morning that "1.5 mb before
    # an answer is a problem that needs fixed" (indexsplit_layer.py).
    # So each edge appears in exactly one band, the first it falls in, and a
    # reader wanting "everything within 15 minutes" unions the three. Nothing
    # is lost and the overdraw goes with it.
    taken = set()
    feats = []
    prev = 0
    for m, budget in zip(mins, budgets):
        lines = []
        metres = 0.0
        for i, e in enumerate(G["edges"]):
            if i in taken:
                continue
            u, v, ln, flags = e[0], e[1], e[2], e[3]
            ok = ((_foot_ok(flags, True) and dist.get(u, 1e18) + ln <= budget)
                  or (_foot_ok(flags, False) and dist.get(v, 1e18) + ln <= budget))
            if not ok:
                continue
            line = _clean([(p[1], p[0]) for p in G["geom"][i]])
            if len(line) < 2:
                continue
            taken.add(i)
            lines.append(line)
            metres += ln
        p = {"minutes": m, "fromMin": prev, "budget_m": round(budget),
             "kmh": kmh, "edges": len(lines), "street_m": round(metres),
             "snap_off_m": round(sn["off_m"], 1),
             "lat": _rt(lat), "lng": _rt(lng)}
        if props:
            p.update(props)
        feats.append({"type": "Feature",
                      "geometry": {"type": "MultiLineString", "coordinates": lines},
                      "properties": p})
        prev = m
    # Widest ring first, so a painter honouring file order lays the far band
    # down before the near one.
    feats.reverse()
    return _fc(feats, source="data/road_graph.json", area=a,
               note=("Disjoint rings: `minutes` is the ring's upper bound and "
                     "`fromMin` its lower, so union them for everything within "
                     "15 minutes. An edge is in a ring when it can be walked "
                     "end to end within that many minutes. Junction-edged, "
                     "never clipped mid-block."))


def seeds(root=ROOT, ctx=None):
    """The nine points of the wall — five gates and four moat corners — as
    (key, th, en, lat, lng), each checked to be inside the graph box rather
    than assumed to be. A key that is not in the register, or a point that is
    outside the box, is dropped and counted, never quietly moved.
    """
    fc = landmarks(root, ctx)
    by_key = {f["properties"]["key"]: f for f in fc["features"]}
    out, missing = [], []
    for k in WALL_KEYS:
        f = by_key.get(k)
        if not f:
            missing.append((k, "not in the register"))
            continue
        lng, lat = f["geometry"]["coordinates"]
        if not in_graph(lat, lng, root):
            missing.append((k, "outside the graph box"))
            continue
        out.append({"key": k, "th": f["properties"]["th"],
                    "en": f["properties"]["en"],
                    "kind": f["properties"]["kind"], "lat": lat, "lng": lng})
    return out, missing


def band_file(key):
    return "walk-bands-%s.geojson" % key


def wall_bands(root=ROOT, ctx=None, minutes=BANDS_MIN):
    """Bands for the nine points of the wall — ONE FILE PER SEED, plus a small
    index. Returns (index FeatureCollection, {key: FeatureCollection}).

    One combined file is 670 kB even as disjoint rings, and a reader who taps
    a gate wants that gate. So the index is nine points with the counts on
    them — about 5 kB, cheap enough to load with the map — and each seed's
    rings are a separate file the chip fetches when it is tapped. This is the
    same shape the shelf GeoJSONs already have (`<key>-<cat>.geojson`), and it
    is the difference between a layer a phone can carry and one it cannot.
    """
    got, missing = seeds(root, ctx)
    per = {}
    idx = []
    for s in got:
        fc = walk_bands(s["lat"], s["lng"], minutes=minutes, root=root,
                        props={"seed": s["key"], "seedTh": s["th"],
                               "seedEn": s["en"]})
        per[s["key"]] = fc
        idx.append({
            "type": "Feature",
            "geometry": {"type": "Point",
                         "coordinates": [_rt(s["lng"]), _rt(s["lat"])]},
            "properties": {
                "seed": s["key"], "th": s["th"], "en": s["en"],
                "kind": s["kind"], "file": band_file(s["key"]),
                "kmh": WALK_KMH,
                "bands": [{"minutes": f["properties"]["minutes"],
                           "fromMin": f["properties"]["fromMin"],
                           "edges": f["properties"]["edges"],
                           "street_m": f["properties"]["street_m"]}
                          for f in sorted(fc["features"],
                                          key=lambda f: f["properties"]["minutes"])],
            },
        })
    index = _fc(idx, source="data/road_graph.json", area=graph(root)["area"],
                seeds=len(got), missing=[list(m) for m in missing],
                note=("Walk-time bands from the nine points of the old city "
                      "wall, on foot at %.1f km/h. Each point names the file "
                      "holding its 5/10/15 minute rings. The graph covers the "
                      "old city plus about 2 km and nothing further; there is "
                      "no band for a place outside it, and no circle drawn in "
                      "its place." % WALK_KMH))
    return index, per


# ------------------------------------------------------------------- emit --

def emit(g):
    """Four GeoJSON files into docs/data/. Writes data only — no page, no chip,
    no CSS. Wiring is a build.py edit and build.py belongs to another session;
    the hook lines are in notes/maps-grow-2026-09-08.txt §8.

    A missing input is reported, never faked: each layer is written only if its
    file is on disk, and the status string says which ones were skipped. The
    disk is a subset of what is held.
    """
    DOCS = g["DOCS"]
    root = g.get("ROOT") or ROOT
    out = DOCS / "data"
    out.mkdir(parents=True, exist_ok=True)
    bits = []

    def write(name, fc):
        (out / name).write_text(json.dumps(fc, ensure_ascii=False))
        return len(fc["features"])

    if (root / "data" / "streets.json").exists():
        fc = sois(root)
        multi = sum(1 for f in fc["features"]
                    if f["geometry"]["type"] == "MultiLineString")
        bits.append("sois %d (%d multi-part)" % (write("sois.geojson", fc), multi))
    else:
        bits.append("sois SKIPPED — no data/streets.json")

    if (root / "data" / "curated" / "zones.json").exists():
        bits.append("zones %d" % write("zones.geojson", zones(root)))
    else:
        bits.append("zones SKIPPED — no data/curated/zones.json")

    try:
        fc = landmarks(root)
        bits.append("landmarks %d" % write("landmarks.geojson", fc))
    except Exception as exc:                     # register or catalogue absent
        bits.append("landmarks SKIPPED — %s" % exc)

    if (root / "data" / "road_graph.json").exists():
        index, per = wall_bands(root)
        write("walk-bands.geojson", index)
        rings = sum(write(band_file(k), fc) for k, fc in per.items())
        bits.append("walk-bands %d seeds, %d rings" % (index["seeds"], rings))
        if index["missing"]:
            bits.append("seeds missing: %s" % index["missing"])
    else:
        bits.append("walk-bands SKIPPED — no data/road_graph.json")

    return " · ".join(bits)


if __name__ == "__main__":
    import sys

    if len(sys.argv) >= 3:
        la, ln = float(sys.argv[1]), float(sys.argv[2])
        try:
            fc = walk_bands(la, ln)
        except OutsideGraph as exc:
            print("REFUSED:", exc)
            sys.exit(1)
        for f in fc["features"]:
            p = f["properties"]
            print("%2d min  %5d m budget  %4d edges  %6d m of street"
                  % (p["minutes"], p["budget_m"], p["edges"], p["street_m"]))
        sys.exit(0)

    s = sois()
    print("sois        %4d features, %d multi-part, %d parts dropped"
          % (len(s["features"]),
             sum(1 for f in s["features"]
                 if f["geometry"]["type"] == "MultiLineString"),
             s["dropped_parts"]))
    z = zones()
    print("zones       %4d features (%d boxes, %d circles)"
          % (len(z["features"]),
             sum(1 for f in z["features"] if f["properties"]["shape"] == "box"),
             sum(1 for f in z["features"] if f["properties"]["shape"] == "circle")))
    lm = landmarks()
    print("landmarks   %4d features, %d unresolved"
          % (len(lm["features"]), lm["unresolved"]))
    got, missing = seeds()
    print("seeds       %4d of %d in the graph box %s"
          % (len(got), len(WALL_KEYS), missing or ""))
    index, per = wall_bands()
    print("walk-bands  %4d seeds, %d rings"
          % (len(index["features"]), sum(len(f["features"]) for f in per.values())))
    for f in index["features"]:
        p = f["properties"]
        print("   %-20s " % p["seed"]
              + "  ".join("%2d min %4d edges %6d m"
                          % (b["minutes"], b["edges"], b["street_m"])
                          for b in p["bands"]))
