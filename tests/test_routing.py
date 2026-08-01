#!/usr/bin/env python3
"""Does the road graph actually encode two different cities?

The planner's whole claim is that a walker and a scooter travel different
networks: a footbridge is a road to one and a wall to the other, and oneway
binds the scooter and not the walker. If that asymmetry is not really in the
graph, the page is showing two numbers that only look different.

Mirrors md.js: same flag bits, same directed Dijkstra, same permission test —
so if these pass and the page disagrees, the port is what is wrong.

Run: python3 tests/test_routing.py
"""
import heapq
import json
import math
import sys
from collections import defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
GRAPH = ROOT / "data" / "road_graph.json"
FAILED = []

FOOT_FWD, FOOT_BWD, RIDE_FWD, RIDE_BWD = 1, 2, 4, 8
BITS = {"foot": (FOOT_FWD, FOOT_BWD), "ride": (RIDE_FWD, RIDE_BWD)}


def check(label, ok, detail=""):
    print(f"  {'ok  ' if ok else 'FAIL'}  {label}" + (f"  — {detail}" if detail else ""))
    if not ok:
        FAILED.append(label)


def hav(a, b):
    R = 6371000.0
    dla, dlo = math.radians(b[0] - a[0]), math.radians(b[1] - a[1])
    h = (math.sin(dla / 2) ** 2
         + math.cos(math.radians(a[0])) * math.cos(math.radians(b[0])) * math.sin(dlo / 2) ** 2)
    return 2 * R * math.asin(math.sqrt(h))


if not GRAPH.exists():
    print("no data/road_graph.json — run crawl_roads.py then build_road_graph.py",
          file=sys.stderr)
    sys.exit(1)

g = json.loads(GRAPH.read_text())
S = g["scale"]
nodes = [(p[0] / S, p[1] / S) for p in g["nodes"]]
edges = g["edges"]

print("graph shape")
check("nodes and edges present", len(nodes) > 1000 and len(edges) > 1000,
      f"{len(nodes):,} junctions, {len(edges):,} edges")
check("every edge indexes real nodes",
      all(0 <= e[0] < len(nodes) and 0 <= e[1] < len(nodes) for e in edges))
check("every edge has positive length", all(e[2] > 0 for e in edges))
check("every edge is usable by somebody", all(e[3] & 15 for e in edges))

# --- the two networks are genuinely different -------------------------------
print("\ntwo networks, not one")
walk_only = [e for e in edges if (e[3] & 3) and not (e[3] & 12)]
ride_only = [e for e in edges if (e[3] & 12) and not (e[3] & 3)]
oneway_ride = [e for e in edges if (e[3] & 12) in (RIDE_FWD, RIDE_BWD)]
oneway_foot = [e for e in edges if (e[3] & 3) in (FOOT_FWD, FOOT_BWD)]
check("there are walk-only edges (footways, steps, footbridges)",
      len(walk_only) > 200, f"{len(walk_only):,}")
check("there are edges no walker may use (flyovers, foot=no)",
      len(ride_only) > 0, f"{len(ride_only):,}")
check("a meaningful number of edges are one-way for a scooter",
      len(oneway_ride) > 500, f"{len(oneway_ride):,}")
check("oneway almost never binds a walker",
      len(oneway_foot) < len(oneway_ride) / 20,
      f"{len(oneway_foot):,} foot vs {len(oneway_ride):,} ride")

# --- routing ---------------------------------------------------------------
adj = defaultdict(list)
for i, e in enumerate(edges):
    a, b, ln, fl = e[0], e[1], e[2], e[3]
    adj[a].append((b, ln, fl, True))
    adj[b].append((a, ln, fl, False))


def passable(flags, mode, fwd):
    f, bw = BITS[mode]
    return bool(flags & (f if fwd else bw))


def nearest(pt, mode):
    best, bi = None, None
    for i, n in enumerate(nodes):
        if not any(passable(e[2], mode, e[3]) for e in adj[i]):
            continue
        d = hav(pt, n)
        if best is None or d < best:
            best, bi = d, i
    return bi, best


def route(a, b, mode):
    dist = {a: 0.0}
    pq = [(0.0, a)]
    while pq:
        c, n = heapq.heappop(pq)
        if n == b:
            return c
        if c > dist.get(n, math.inf):
            continue
        for to, ln, fl, fwd in adj[n]:
            if not passable(fl, mode, fwd):
                continue
            nc = c + ln
            if nc < dist.get(to, math.inf):
                dist[to] = nc
                heapq.heappush(pq, (nc, to))
    return None


print("\nrouting behaves like a city")
# Two stops either side of the east moat — the case the user flagged. Straight
# line 419 m; on the ground it is neither that nor the same for both modes.
A = (18.79167, 98.99147)   # Backstreet Barber Shop, inside the wall
B = (18.79081, 98.99534)   # Karinthip Village, across the water
crow = hav(A, B)
res = {}
for mode in ("foot", "ride"):
    na, da = nearest(A, mode)
    nb, db = nearest(B, mode)
    m = route(na, nb, mode)
    res[mode] = None if m is None else m + da + db
    check(f"{mode}: a route exists across the moat", res[mode] is not None,
          "" if res[mode] is None else f"{res[mode]:.0f} m")

if res["foot"] and res["ride"]:
    check("both modes are longer than the crow's line",
          res["foot"] > crow and res["ride"] > crow,
          f"crow {crow:.0f} m · walk {res['foot']:.0f} m · ride {res['ride']:.0f} m")
    check("the scooter's way round is longer than the walker's",
          res["ride"] > res["foot"],
          f"ride {res['ride']:.0f} m vs walk {res['foot']:.0f} m "
          f"(+{res['ride'] - res['foot']:.0f} m)")

# A walker and a scooter starting from the same door should not agree on
# everything, or the two modes are decorative. Sample real pairs and count.
places = json.loads((ROOT / "data" / "canonical" / "cm.json").read_text())
area = g["area"]


def inside(r):
    return (r.get("lat") is not None and area["s"] < r["lat"] < area["n"]
            and area["w"] < r["lng"] < area["e"])


pool = [r for r in places if inside(r)]
pool.sort(key=lambda r: r["id"])
pairs, differ, both = 0, 0, 0
for i in range(0, min(len(pool), 400), 40):
    for j in range(i + 20, min(len(pool), 400), 80):
        a, b = pool[i], pool[j]
        if hav((a["lat"], a["lng"]), (b["lat"], b["lng"])) > 2500:
            continue
        pairs += 1
        got = {}
        for mode in ("foot", "ride"):
            na, _ = nearest((a["lat"], a["lng"]), mode)
            nb, _ = nearest((b["lat"], b["lng"]), mode)
            got[mode] = route(na, nb, mode)
        if got["foot"] and got["ride"]:
            both += 1
            if abs(got["foot"] - got["ride"]) > 25:
                differ += 1

check("sampled real pairs routed for both modes", both >= 5, f"{both}/{pairs} pairs")
check("the two modes usually disagree on distance", both and differ / both > 0.5,
      f"{differ}/{both} differ by more than 25 m")

print()
if FAILED:
    print(f"{len(FAILED)} failed:")
    for f in FAILED:
        print("  -", f)
    sys.exit(1)
print("all routing checks pass")
