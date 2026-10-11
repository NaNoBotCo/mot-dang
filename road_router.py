"""road_router.py — the road graph, walked in Python (WO-93).

The browser has routed over data/road_graph.json since plan.html shipped; every
other "near me" surface still answers as-the-crow-flies, which is wrong in a city
built around a moat and one-way rings — the thing thirty metres behind a scooter
is a lap away. Plan B (Nan, 2026-09-25): precompute road distance OFFLINE so the
records carry it and the pages stay light, instead of shipping the half-megabyte
graph to every page.

This module is the shared engine. It loads the same graph the browser loads,
builds a mode-aware adjacency from the four permission bits, and answers
node-to-node and point-to-point road distance with Dijkstra — the same walk the
client does, in the language the build runs in.

    from road_router import RoadRouter
    r = RoadRouter.load()
    m = r.route_m((18.7877, 98.9933), (18.7840, 98.9990), mode="ride")
    #   metres by road, or None when a point is outside the graph's area or
    #   unreachable — the caller falls back to the crow then, and says so.

WHAT IT IS NOT. The graph covers the old city only (see .area); a point outside
it returns None, by design — past the routed area the answer is the straight
line, exactly as plan.html already says. oneway binds `ride` and not
`foot`, so ride distance is NOT symmetric and can far exceed the walk; that
asymmetry is the whole point, not a bug.
"""

import heapq
import json
import math
from pathlib import Path

ROOT = Path(__file__).resolve().parent

# Metres per minute, per mode — the pace plan.html routes at (foot 4.6 km/h,
# ride 18 km/h). Distance is what "nearest" sorts by; time is for display.
SPEED_M_PER_MIN = {"foot": 4600 / 60.0, "ride": 18000 / 60.0}

# The four permission bits an edge carries (graph["flags"] states them):
FOOT_FWD, FOOT_BACK, RIDE_FWD, RIDE_BACK = 1, 2, 4, 8
_MODE_BITS = {"foot": (FOOT_FWD, FOOT_BACK), "ride": (RIDE_FWD, RIDE_BACK)}


def _hav_m(a_lat, a_lng, b_lat, b_lng):
    """Great-circle metres — the same haversine near.js and bearings_layer use."""
    R = 6371000.0
    p1, p2 = math.radians(a_lat), math.radians(b_lat)
    dp = math.radians(b_lat - a_lat)
    dl = math.radians(b_lng - a_lng)
    h = math.sin(dp / 2) ** 2 + math.cos(p1) * math.cos(p2) * math.sin(dl / 2) ** 2
    return 2 * R * math.asin(math.sqrt(h))


class RoadRouter:
    def __init__(self, graph):
        self.scale = graph["scale"]
        self.area = graph["area"]                       # {s,w,n,e}
        # nodes as (lat, lng) floats
        s = float(self.scale)
        self.nodes = [(la / s, ln / s) for la, ln in graph["nodes"]]
        self._raw_edges = graph["edges"]
        # adjacency per mode, built lazily: {mode: [ [(to, metres), ...], ... ]}
        self._adj = {}

    @classmethod
    def load(cls, path=None):
        p = Path(path) if path else (ROOT / "data" / "road_graph.json")
        return cls(json.loads(p.read_text()))

    def _adjacency(self, mode):
        adj = self._adj.get(mode)
        if adj is not None:
            return adj
        fwd, back = _MODE_BITS[mode]
        adj = [[] for _ in self.nodes]
        for e in self._raw_edges:
            a, b, metres, perm = e[0], e[1], e[2], e[3]
            if perm & fwd:
                adj[a].append((b, metres))
            if perm & back:
                adj[b].append((a, metres))
        self._adj[mode] = adj
        return adj

    def in_area(self, lat, lng, margin=0.0):
        a = self.area
        return (a["s"] - margin <= lat <= a["n"] + margin
                and a["w"] - margin <= lng <= a["e"] + margin)

    def snap(self, lat, lng, max_m=250.0):
        """Nearest graph node to a point: (node_index, metres_to_it), or None
        when the closest junction is farther than max_m — a point that far from
        any road is not on this network, and snapping it would invent a route."""
        best_i, best_m = None, float("inf")
        for i, (nla, nln) in enumerate(self.nodes):
            # cheap planar prefilter before the haversine
            if abs(nla - lat) > 0.01 or abs(nln - lng) > 0.01:
                continue
            d = _hav_m(lat, lng, nla, nln)
            if d < best_m:
                best_i, best_m = i, d
        if best_i is None or best_m > max_m:
            return None
        return best_i, best_m

    def dijkstra(self, src_node, mode, targets=None, max_m=None):
        """Shortest road metres from src_node to every reachable node (or, when
        `targets` is given, until all of them are settled). Returns {node: metres}."""
        adj = self._adjacency(mode)
        dist = {src_node: 0.0}
        pq = [(0.0, src_node)]
        need = set(targets) if targets is not None else None
        seen = set()
        while pq:
            d, u = heapq.heappop(pq)
            if u in seen:
                continue
            seen.add(u)
            if need is not None:
                need.discard(u)
                if not need:
                    break
            if max_m is not None and d > max_m:
                continue
            for v, w in adj[u]:
                nd = d + w
                if nd < dist.get(v, float("inf")):
                    dist[v] = nd
                    heapq.heappush(pq, (nd, v))
        return dist

    def route_m(self, a, b, mode="ride"):
        """Road metres between two (lat, lng) points, including the short snap
        legs onto the network, or None when either point is off the graph or the
        two cannot be connected in this mode. `a`/`b` are (lat, lng)."""
        if not self.in_area(*a) or not self.in_area(*b):
            return None
        sa, sb = self.snap(*a), self.snap(*b)
        if sa is None or sb is None:
            return None
        (na, ma), (nb, mb) = sa, sb
        if na == nb:
            return ma + mb
        dist = self.dijkstra(na, mode, targets=(nb,))
        d = dist.get(nb)
        return None if d is None else ma + d + mb

    def minutes(self, metres, mode="ride"):
        return metres / SPEED_M_PER_MIN[mode]
