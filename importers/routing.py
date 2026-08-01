#!/usr/bin/env python3
"""Walk the road graph from Python, the same way plan.html walks it from JS.

`data/road_graph.json` was built for the browser and until now only the browser
read it. Anything generated at build time — the merit routes, and whatever comes
after them — needs the same answers, and needs them without asking the reader to
download half a megabyte of graph to see a number on a page.

This is a deliberate second implementation of logic that already exists in
`build.py`'s plan JS, so the two must agree. What has to stay in step:

  * **oneway binds ride and not foot.** Flags are 1=foot forward, 2=foot back,
    4=ride forward, 8=ride back. This is the whole reason the two modes give
    different answers, and the reason a shop thirty metres behind you on a
    one-way soi is a lap away on a scooter and nothing on foot.
  * **snapping costs something.** A stop is snapped to the nearest point on the
    nearest passable edge, and the walk-in from the stop to that point is added
    to every journey. Leave it out and a place set back from the street reads as
    standing on it.
  * **a stop is a point on an edge, not a junction.** Snapping to junctions
    alone throws away up to a block of accuracy per stop.

`tests/test_routing.py` covers the JS side. Parity between the two is checked by
`tests/test_route_parity.py`.

    from routing import Graph
    g = Graph.load()
    d = g.distance((18.79, 98.99), (18.78, 98.98), "foot")   # metres, or None
"""
import json
import math
from heapq import heappop, heappush
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent

FOOT_FWD, FOOT_BWD, RIDE_FWD, RIDE_BWD = 1, 2, 4, 8
MODES = {"foot": (FOOT_FWD, FOOT_BWD, 4.6), "ride": (RIDE_FWD, RIDE_BWD, 18.0)}


def hav(a, b):
    R = 6371000.0
    dla, dlo = math.radians(b[0] - a[0]), math.radians(b[1] - a[1])
    h = (math.sin(dla / 2) ** 2
         + math.cos(math.radians(a[0])) * math.cos(math.radians(b[0]))
         * math.sin(dlo / 2) ** 2)
    return 2 * R * math.asin(math.sqrt(h))


def _to_seg(p, a, b):
    """Metres from p to segment ab, and how far along ab the perpendicular
    foot falls. Flat local projection — over one road segment the curvature of
    the earth is not the error that matters."""
    kx = math.cos(math.radians(p[0])) * 111320.0
    ky = 110540.0
    ax, ay = (a[1] - p[1]) * kx, (a[0] - p[0]) * ky
    bx, by = (b[1] - p[1]) * kx, (b[0] - p[0]) * ky
    dx, dy = bx - ax, by - ay
    L = dx * dx + dy * dy
    t = 0.0 if not L else max(0.0, min(1.0, (-ax * dx - ay * dy) / L))
    cx, cy = ax + t * dx, ay + t * dy
    return math.hypot(cx, cy), t, math.sqrt(L)


class Snap(object):
    __slots__ = ("edge", "a", "b", "to_a", "to_b", "d")

    def __init__(self, edge, a, b, to_a, to_b, d):
        self.edge, self.a, self.b = edge, a, b
        self.to_a, self.to_b, self.d = to_a, to_b, d


class Graph(object):
    def __init__(self, doc):
        s = doc["scale"]
        self.area = doc["area"]
        self.nodes = [(p[0] / s, p[1] / s) for p in doc["nodes"]]
        self.edges = doc["edges"]
        self.geom = []
        self.adj = [[] for _ in self.nodes]
        for i, e in enumerate(self.edges):
            a, b, length, flags = e[0], e[1], e[2], e[3]
            deltas = e[4] if len(e) > 4 else []
            pts = [self.nodes[a]]
            la = ln = 0
            for k in range(0, len(deltas), 2):
                if k == 0:
                    la, ln = deltas[0], deltas[1]
                else:
                    la += deltas[k]
                    ln += deltas[k + 1]
                pts.append((la / s, ln / s))
            pts.append(self.nodes[b])
            self.geom.append(pts)
            self.adj[a].append((b, length, flags, i, True))
            self.adj[b].append((a, length, flags, i, False))
        # Coarse index so a snap does not walk 12,280 polylines. ~1.1 km cells;
        # the search widens until it finds something rather than assuming one
        # ring is enough.
        self.grid = {}
        for i, pts in enumerate(self.geom):
            for k in range(len(pts) - 1):
                p, q = pts[k], pts[k + 1]
                for cy in range(int(min(p[0], q[0]) / 0.01), int(max(p[0], q[0]) / 0.01) + 1):
                    for cx in range(int(min(p[1], q[1]) / 0.01), int(max(p[1], q[1]) / 0.01) + 1):
                        self.grid.setdefault((cy, cx), []).append((i, k))

    @classmethod
    def load(cls, path=None):
        p = Path(path) if path else (ROOT / "data" / "road_graph.json")
        if not p.exists():
            return None
        return cls(json.loads(p.read_text()))

    def contains(self, p):
        a = self.area
        return a["s"] < p[0] < a["n"] and a["w"] < p[1] < a["e"]

    def passable(self, flags, mode, forward):
        fwd, bwd, _ = MODES[mode]
        return (flags & (fwd if forward else bwd)) != 0

    def snap(self, p, mode):
        fwd, bwd, _ = MODES[mode]
        best = None
        for ring in (1, 2, 4):
            cy0, cx0 = int(p[0] / 0.01), int(p[1] / 0.01)
            for dy in range(-ring, ring + 1):
                for dx in range(-ring, ring + 1):
                    for (i, k) in self.grid.get((cy0 + dy, cx0 + dx), ()):
                        flags = self.edges[i][3]
                        if not (flags & (fwd | bwd)):
                            continue
                        pts = self.geom[i]
                        d, t, L = _to_seg(p, pts[k], pts[k + 1])
                        if best is None or d < best[0]:
                            run = 0.0
                            for j in range(k):
                                run += hav(pts[j], pts[j + 1])
                            best = (d, i, run + t * L)
            if best:
                break
        if not best:
            return None
        d, i, along = best
        total = sum(hav(self.geom[i][j], self.geom[i][j + 1])
                    for j in range(len(self.geom[i]) - 1))
        e = self.edges[i]
        return Snap(i, e[0], e[1], along, max(0.0, total - along), d)

    def costs_from(self, s, mode):
        """Cheapest cost from a snapped origin to every junction.

        One search answers every destination, which is what makes a matrix
        affordable: n origins instead of n squared pairs.
        """
        INF = float("inf")
        cost = [INF] * len(self.nodes)
        heap = []
        if self.passable(self.edges[s.edge][3], mode, False) or s.a == s.b:
            cost[s.a] = s.to_a
            heappush(heap, (s.to_a, s.a))
        if self.passable(self.edges[s.edge][3], mode, True):
            if s.to_b < cost[s.b]:
                cost[s.b] = s.to_b
                heappush(heap, (s.to_b, s.b))
        while heap:
            c, n = heappop(heap)
            if c > cost[n]:
                continue
            for (to, length, flags, _ei, forward) in self.adj[n]:
                if not self.passable(flags, mode, forward):
                    continue
                nc = c + length
                if nc < cost[to]:
                    cost[to] = nc
                    heappush(heap, (nc, to))
        return cost

    def cost_to(self, cost, t, mode):
        """Read a destination off a finished search. Both ends of the target's
        edge are candidates, but only the ends this mode may arrive at."""
        best = float("inf")
        if self.passable(self.edges[t.edge][3], mode, True):
            best = min(best, cost[t.a] + t.to_a)
        if self.passable(self.edges[t.edge][3], mode, False):
            best = min(best, cost[t.b] + t.to_b)
        return None if best == float("inf") else best

    def matrix(self, points, mode):
        """Full cost matrix in metres, snap walk-in included on both ends.

        None where no route exists — an unreachable pair is not a distance of
        zero and must never be allowed to look like the cheapest leg.
        """
        snaps = [self.snap(p, mode) for p in points]
        n = len(points)
        out = [[None] * n for _ in range(n)]
        for i, s in enumerate(snaps):
            if s is None:
                continue
            cost = self.costs_from(s, mode)
            for j, t in enumerate(snaps):
                if t is None:
                    continue
                if i == j:
                    out[i][j] = 0.0
                    continue
                c = self.cost_to(cost, t, mode)
                if c is not None:
                    out[i][j] = c + s.d + t.d
        return out

    def distance(self, a, b, mode):
        sa, sb = self.snap(a, mode), self.snap(b, mode)
        if not sa or not sb:
            return None
        c = self.cost_to(self.costs_from(sa, mode), sb, mode)
        return None if c is None else c + sa.d + sb.d


def order_loop(matrix):
    """A short closed order through every point. Nearest neighbour from each
    possible start, then 2-opt until it stops improving.

    Not the optimal tour and it does not claim to be: nine stops is small enough
    that 2-opt lands on or very near the best answer, and the failure mode of an
    approximation here is a slightly longer walk, not a wrong one.
    """
    n = len(matrix)
    if n < 3:
        return list(range(n))

    def leg(i, j):
        v = matrix[i][j]
        # An unroutable pair must not read as free. Charged high enough to be
        # avoided, low enough not to overflow the comparisons.
        return 1e7 if v is None else v

    def total(order):
        return sum(leg(order[i], order[(i + 1) % n]) for i in range(n))

    best_order, best_len = None, float("inf")
    for start in range(n):
        left = set(range(n))
        left.discard(start)
        order = [start]
        while left:
            cur = order[-1]
            nxt = min(left, key=lambda j: leg(cur, j))
            order.append(nxt)
            left.discard(nxt)
        improved = True
        while improved:
            improved = False
            for i in range(1, n - 1):
                for k in range(i + 1, n):
                    cand = order[:i] + order[i:k + 1][::-1] + order[k + 1:]
                    if total(cand) + 1e-9 < total(order):
                        order = cand
                        improved = True
        t = total(order)
        if t < best_len:
            best_order, best_len = order, t
    return best_order
