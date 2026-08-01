#!/usr/bin/env python3
"""Turn the crawled OSM ways into a routable graph the browser can walk.

Two networks, one graph. A pedestrian and a scooter do not travel the same city:
the footbridge over the moat is a road to one and a wall to the other, the
flyover on ถนนมหิดล is tagged foot=no, and — the big one — **oneway binds a
scooter and not a walker**. That single asymmetry is what produces the U-turn
behaviour around the moat: on a one-way ring road, the thing thirty metres
behind you is a lap away.

So every edge carries four bits of permission (foot forward, foot back, ride
forward, ride back) and the router is handed a mode. Nothing about the moat is
special-cased any more; the gates and the footbridges are simply edges that
exist for one mode and not the other.

    python3 importers/crawl_roads.py        # first
    python3 importers/build_road_graph.py   # then this

Writes data/road_graph.json (and build.py copies it into docs/). Intermediate
"shape" nodes are folded into edge geometry, so the graph carries junctions
only — an order of magnitude fewer nodes to search, with the real road shape
kept for drawing.
"""
import json
import math
import sys
from collections import Counter, defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
CACHE = ROOT / "cache" / "roads"
OUT = ROOT / "data" / "road_graph.json"
SCALE = 100000          # coordinates stored as integers, 1e-5° ≈ 1.1 m

# ---------------------------------------------------------------- permissions
# A walker may not use a motorway or its ramps; in Thailand a motorcycle may not
# either (ทางหลวงพิเศษ), so both modes decline them and only cars would differ.
FOOT_NO = {"motorway", "motorway_link", "trunk", "trunk_link"}
RIDE_NO = {"footway", "path", "steps", "pedestrian", "corridor", "cycleway",
           "motorway", "motorway_link"}
# Ways that exist but are nobody's route: a parking aisle or a private driveway
# is not a way through, and letting the router use them invents shortcuts
# through other people's property.
SERVICE_NO = {"parking_aisle", "driveway", "drive-through", "emergency_access"}
BLOCKED = {"private", "no", "customers", "delivery", "permit"}
ALLOWED = {"yes", "permissive", "designated", "destination", "official", "public"}


def truthy_access(tags, keys, highway_default):
    """Resolve access for one mode: the most specific tag that is present wins,
    and only falls back to what the highway class implies."""
    for k in keys:
        v = tags.get(k)
        if v is None:
            continue
        if v in BLOCKED:
            return False
        if v in ALLOWED:
            return True
    return highway_default


def perms(tags):
    """(foot, ride, oneway_dir) — oneway_dir is +1, -1 or 0, for the ride mode
    only. A pedestrian is not bound by oneway unless oneway:foot says so."""
    hw = tags.get("highway")
    if not hw:
        return False, False, 0
    if tags.get("service") in SERVICE_NO:
        return False, False, 0
    # A general access=private closes a way to everyone unless a mode-specific
    # tag re-opens it, which truthy_access handles by checking those first.
    foot = truthy_access(tags, ("foot", "access"), hw not in FOOT_NO)
    ride = truthy_access(tags, ("motorcycle", "motor_vehicle", "vehicle", "access"),
                         hw not in RIDE_NO)
    ow = (tags.get("oneway") or "no").lower()
    if ow in ("yes", "true", "1"):
        d = 1
    elif ow in ("-1", "reverse"):
        d = -1
    else:
        d = 0
    # A very few ways are one-way on foot too (a turnstile, a one-way stair).
    fow = (tags.get("oneway:foot") or "no").lower()
    foot_dir = 1 if fow in ("yes", "true", "1") else (-1 if fow == "-1" else 0)
    return foot, ride, (d, foot_dir)


def hav(a, b):
    R = 6371000.0
    dla, dlo = math.radians(b[0] - a[0]), math.radians(b[1] - a[1])
    h = (math.sin(dla / 2) ** 2
         + math.cos(math.radians(a[0])) * math.cos(math.radians(b[0])) * math.sin(dlo / 2) ** 2)
    return 2 * R * math.asin(math.sqrt(h))


def main():
    tiles = sorted(CACHE.glob("*.json"))
    if not tiles:
        print("no tiles in cache/roads/ — run importers/crawl_roads.py first", file=sys.stderr)
        return 1

    ways, coords = {}, {}
    for t in tiles:
        for e in json.loads(t.read_text())["elements"]:
            if e["type"] == "way":
                ways.setdefault(e["id"], e)
            elif e["type"] == "node":
                coords.setdefault(e["id"], (e["lat"], e["lon"]))
    print(f"{len(tiles)} tiles → {len(ways):,} ways, {len(coords):,} nodes")

    # Only ways somebody can actually travel, and only whole ones: a way missing
    # a node's coordinates would route through a hole.
    usable, missing = [], 0
    for w in ways.values():
        foot, ride, dirs = perms(w.get("tags") or {})
        if not (foot or ride):
            continue
        if any(n not in coords for n in w["nodes"]):
            missing += 1
            continue
        usable.append((w, foot, ride, dirs))
    print(f"routable ways: {len(usable):,}" + (f"  ({missing} skipped, node gaps)" if missing else ""))

    # A junction is a node two ways share, or the end of one. Everything else is
    # a bend in the road, and belongs in the geometry rather than the search.
    seen = Counter()
    for w, *_ in usable:
        for n in set(w["nodes"]):
            seen[n] += 1
    junction = set()
    for w, *_ in usable:
        ns = w["nodes"]
        junction.add(ns[0])
        junction.add(ns[-1])
        for n in ns[1:-1]:
            if seen[n] > 1:
                junction.add(n)

    idx, node_out = {}, []
    for n in sorted(junction):
        idx[n] = len(node_out)
        node_out.append(coords[n])

    # Split each way at its junctions; every span between two of them is an edge.
    edges = []
    for w, foot, ride, (rdir, fdir) in usable:
        ns = w["nodes"]
        span = [ns[0]]
        for n in ns[1:]:
            span.append(n)
            if n in junction:
                if len(span) > 1 and span[0] != n:
                    pts = [coords[x] for x in span]
                    length = sum(hav(pts[i], pts[i + 1]) for i in range(len(pts) - 1))
                    if length > 0:
                        f_f = foot and fdir >= 0
                        f_b = foot and fdir <= 0
                        r_f = ride and rdir >= 0
                        r_b = ride and rdir <= 0
                        flags = (1 if f_f else 0) | (2 if f_b else 0) \
                                | (4 if r_f else 0) | (8 if r_b else 0)
                        if flags:
                            edges.append((idx[span[0]], idx[n], length, flags, pts))
                span = [n]

    # Delta-encoded integer geometry: the interior bends only, since both ends
    # are already node coordinates the reader has.
    def enc(pts):
        out, prev = [], None
        for lat, lng in pts[1:-1]:
            la, ln = round(lat * SCALE), round(lng * SCALE)
            if prev is None:
                out += [la, ln]
            else:
                out += [la - prev[0], ln - prev[1]]
            prev = (la, ln)
        return out

    edge_out = [[a, b, round(l, 1), f, enc(p)] for a, b, l, f, p in edges]

    lats = [c[0] for c in node_out]
    lngs = [c[1] for c in node_out]
    graph = {
        "generated": None,     # stamped by the caller, not by a clock in here
        "scale": SCALE,
        "area": {"s": min(lats), "n": max(lats), "w": min(lngs), "e": max(lngs)},
        "nodes": [[round(la * SCALE), round(ln * SCALE)] for la, ln in node_out],
        "edges": edge_out,
        "flags": "1=foot forward, 2=foot back, 4=ride forward, 8=ride back",
        "note": ("Junction graph for offline route planning. oneway binds ride "
                 "and not foot, which is what makes a one-way ring road cost a "
                 "scooter a lap and a walker nothing."),
    }
    OUT.write_text(json.dumps(graph, separators=(",", ":")))

    # What did we actually get? Degree and per-mode reachability are the numbers
    # that say whether this graph can route at all.
    deg = defaultdict(int)
    fmode = rmode = 0
    for a, b, l, f, _ in edges:
        deg[a] += 1
        deg[b] += 1
        if f & 3:
            fmode += 1
        if f & 12:
            rmode += 1
    oneway_ride = sum(1 for *_, f, _ in edges if (f & 12) in (4, 8))
    size = OUT.stat().st_size / 1e6
    print(f"graph: {len(node_out):,} junctions, {len(edges):,} edges  →  {size:.2f} MB")
    print(f"  walkable edges {fmode:,} · rideable {rmode:,} · one-way for a scooter {oneway_ride:,}")
    print(f"  mean junction degree {sum(deg.values()) / max(len(deg), 1):.2f}")
    print(f"  dead ends {sum(1 for v in deg.values() if v == 1):,}")
    print(f"wrote {OUT.relative_to(ROOT)}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
