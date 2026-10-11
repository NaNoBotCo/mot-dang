#!/usr/bin/env python3
"""The province road network as small squares, so a page can route from
wherever the reader stands by fetching only the squares around them.

Same junction graph and the same four permission bits as build_road_graph.py
(1 foot-fwd · 2 foot-back · 4 ride-fwd · 8 ride-back; oneway binds a scooter,
not a walker) — imported from it, not restated — over both provinces instead
of the old city.

Reads cache/roads-prov/<ISO>/*.json (crawl_roads_province.py, `out body geom`)
and, under it, the old-city crawl in cache/roads/ + cache/roads/wide/; with
--old-city it reads only the latter.

Writes
  cache/road_tiles/<ty>_<tx>.json   one square, TILE degrees a side
  cache/road_tiles/index.json       tile size, scale, every square that exists
  cache/road_graph_prov.json        the whole graph, road_graph.json's shape,
                                    for the build (loo_road.py) to route in

A square holds every edge with an end inside it, with both end nodes and the
interior geometry; the browser merges squares by node coordinate, so an edge
that crosses a seam is simply in both.

  python3 importers/build_road_tiles.py
"""
import json
import math
import re
import sys
from collections import Counter, defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(Path(__file__).resolve().parent))
from build_road_graph import perms, hav, SCALE  # noqa: E402

TILE = 0.01          # ≈ 1.1 km; the browser loads the few around the reader
OUT = ROOT / "cache" / "road_tiles"
GRAPH = ROOT / "cache" / "road_graph_prov.json"


def tile_of(lat, lng):
    return math.floor(lat / TILE), math.floor(lng / TILE)


def read_ways(old_city=False):
    ways, coords = {}, {}
    # The province squares first (newest), then the old-city crawl beneath
    # them: a way already read keeps its first copy, so the old city fills
    # only what the province crawl has not reached yet.
    files = [] if old_city else sorted((ROOT / "cache" / "roads-prov").glob("*/*.json"))
    files += sorted((ROOT / "cache" / "roads").glob("*.json")) + \
        sorted((ROOT / "cache" / "roads" / "wide").glob("*.json"))
    for f in files:
        d = json.loads(f.read_text())
        if d.get("remark"):
            raise SystemExit(f"{f} carries an Overpass remark — refetch it")
        for e in d.get("elements", []):
            if e["type"] == "way":
                if e["id"] in ways:
                    continue
                ways[e["id"]] = e
                for n, gpt in zip(e.get("nodes") or [], e.get("geometry") or []):
                    if gpt:
                        coords.setdefault(n, (gpt["lat"], gpt["lon"]))
            elif e["type"] == "node":
                coords.setdefault(e["id"], (e["lat"], e["lon"]))
    print(f"{len(files)} files → {len(ways):,} ways, {len(coords):,} nodes", flush=True)
    return ways, coords


def build(ways, coords):
    usable = []
    for w in ways.values():
        foot, ride, dirs = perms(w.get("tags") or {})
        if not (foot or ride):
            continue
        if any(n not in coords for n in w["nodes"]):
            continue
        usable.append((w, foot, ride, dirs))
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
    idx, nodes = {}, []
    for n in sorted(junction):
        idx[n] = len(nodes)
        nodes.append(coords[n])
    edges = []
    for w, foot, ride, (rdir, fdir) in usable:
        ns = w["nodes"]
        nm = road_name(w.get("tags") or {})
        span = [ns[0]]
        for n in ns[1:]:
            span.append(n)
            if n in junction:
                if len(span) > 1 and span[0] != n:
                    pts = [coords[x] for x in span]
                    length = sum(hav(pts[i], pts[i + 1]) for i in range(len(pts) - 1))
                    flags = ((1 if foot and fdir >= 0 else 0) | (2 if foot and fdir <= 0 else 0)
                             | (4 if ride and rdir >= 0 else 0) | (8 if ride and rdir <= 0 else 0))
                    if length > 0 and flags:
                        edges.append((idx[span[0]], idx[n], length, flags, pts, nm))
                span = [n]
    return nodes, edges


THAI = re.compile(r"[\u0E00-\u0E7F]")


def road_name(tags):
    """[th, en, ref] for plan.html's spoken turns, or None for a nameless way."""
    name = (tags.get("name") or "").strip()
    th = (tags.get("name:th") or "").strip() or (name if THAI.search(name) else "")
    en = (tags.get("name:en") or "").strip() or (name if name and not THAI.search(name) else "")
    ref = (tags.get("ref") or "").split(";")[0].strip()
    return [th, en, ref] if (th or en or ref) else None


def enc(pts):
    out, prev = [], None
    for lat, lng in pts[1:-1]:
        la, ln = round(lat * SCALE), round(lng * SCALE)
        out += [la, ln] if prev is None else [la - prev[0], ln - prev[1]]
        prev = (la, ln)
    return out


def main():
    nodes, edges = build(*read_ways("--old-city" in sys.argv[1:]))
    print(f"graph: {len(nodes):,} junctions, {len(edges):,} edges", flush=True)

    q = [[round(la * SCALE), round(ln * SCALE)] for la, ln in nodes]
    edge_out = [[a, b, round(m, 1), f, enc(p)] for a, b, m, f, p, _ in edges]
    lats = [c[0] for c in nodes]
    lngs = [c[1] for c in nodes]
    GRAPH.write_text(json.dumps({
        "scale": SCALE,
        "area": {"s": min(lats), "n": max(lats), "w": min(lngs), "e": max(lngs)},
        "nodes": q, "edges": edge_out,
        "flags": "1=foot forward, 2=foot back, 4=ride forward, 8=ride back"},
        separators=(",", ":")))

    by_tile = defaultdict(list)
    for k, (a, b, m, f, p, _) in enumerate(edges):
        ts = {tile_of(*nodes[a]), tile_of(*nodes[b])}
        for t in ts:
            by_tile[t].append(k)
    OUT.mkdir(parents=True, exist_ok=True)
    for old in OUT.glob("*.json"):
        old.unlink()
    sizes = []
    for (ty, tx), ks in by_tile.items():
        local, nl = {}, []
        es = []
        # Names ride beside the edges, not in them: e[] keeps the five fields
        # every reader of these squares already unpacks. w = the square's road
        # names, ni[k] = edge k's index into it, -1 for a nameless way.
        names, ni, wi = [], [], {}
        for k in ks:
            a, b = edge_out[k][0], edge_out[k][1]
            for n in (a, b):
                if n not in local:
                    local[n] = len(nl)
                    nl.append(q[n])
            es.append([local[a], local[b]] + edge_out[k][2:])
            nm = edges[k][5]
            if nm:
                key = "\t".join(nm)
                if key not in wi:
                    wi[key] = len(names)
                    names.append(nm)
                ni.append(wi[key])
            else:
                ni.append(-1)
        sq = {"n": nl, "e": es}
        if names:
            sq["w"], sq["ni"] = names, ni
        body = json.dumps(sq, ensure_ascii=False, separators=(",", ":"))
        (OUT / f"{ty}_{tx}.json").write_text(body, encoding="utf-8")
        sizes.append(len(body))
    keys = sorted(f"{ty}_{tx}" for ty, tx in by_tile)
    (OUT / "index.json").write_text(json.dumps({
        "tile": TILE, "scale": SCALE,
        "flags": "1=foot forward, 2=foot back, 4=ride forward, 8=ride back",
        "tiles": keys}, separators=(",", ":")))
    sizes.sort()
    print(f"tiles: {len(keys):,}, total {sum(sizes) / 1e6:.1f} MB, "
          f"median {sizes[len(sizes) // 2] / 1e3:.0f} KB, max {sizes[-1] / 1e3:.0f} KB")
    print(f"graph → {GRAPH.relative_to(ROOT)} {GRAPH.stat().st_size / 1e6:.1f} MB")


if __name__ == "__main__":
    main()
