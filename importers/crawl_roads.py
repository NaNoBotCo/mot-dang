#!/usr/bin/env python3
"""The road network around the old city, so the planner can stop pretending
people can fly.

Every distance on plan.html used to be a straight line. Nobody walks a straight
line: there are buildings in the way, sois that do not join up, a one-way ring
around the moat, and a moat you cross at a foot bridge or a U-turn and nowhere
else. A foot bridge is also not available to a scooter. All of that is in
OpenStreetMap already, as ways with tags — so fetch the ways and let
build_road_graph.py turn them into something A* can walk.

Scope is the old city plus roughly a 2 km ring, chosen with the user: that is
where somebody on foot or on a scooter actually runs errands. Outside the box
the planner links out rather than guessing.

Manners, same as crawl_overpass.py: snapshot-first, one tile at a time, long
pauses, identified User-Agent, mirror rotation and lengthening rests on 429/504.
Split into tiles because one 5.5 km box of every highway is a big enough answer
to time Overpass out — and a tile that fails can be retried on its own.

  python3 importers/crawl_roads.py            # fetch only missing tiles
  python3 importers/crawl_roads.py --fetch    # refetch everything (slow, on purpose)
  python3 importers/crawl_roads.py --tiles 4  # finer split if tiles keep timing out

Cache: cache/roads/<n>-<e>.json — build_road_graph.py reads these.
"""
import json
import sys
import time
import urllib.parse
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
APIS = ["https://overpass-api.de/api/interpreter",
        "https://overpass.kumi.systems/api/interpreter"]
UA = ("mot-dang-directory/1.0 (+https://github.com/NaNoBotCo/mot-dang; "
      "gentle one-off road-network harvest for offline route planning)")
PAUSE = 15
RETRY_PAUSE = 45

# The old city moat is 18.7816–18.7952 N, 98.9790–98.9930 E. Add ~2 km on every
# side: 2 km is 0.0181° of latitude, and 0.0190° of longitude at this latitude.
AREA = {"s": 18.7635, "n": 18.8133, "w": 98.9600, "e": 99.0120}

# Everything a person on foot or on a scooter can legally be on, plus the
# barriers worth knowing about. Deliberately broad — build_road_graph.py decides
# which mode may use what, and it is cheaper to filter locally than to re-crawl.
HIGHWAY = ("motorway|trunk|primary|secondary|tertiary|unclassified|residential|"
           "living_street|service|pedestrian|footway|path|steps|track|cycleway|"
           "motorway_link|trunk_link|primary_link|secondary_link|tertiary_link|"
           "road|corridor")


def tiles(n):
    """n x n boxes covering AREA, each as an Overpass bbox string."""
    out = []
    dlat = (AREA["n"] - AREA["s"]) / n
    dlng = (AREA["e"] - AREA["w"]) / n
    for i in range(n):
        for j in range(n):
            s = AREA["s"] + i * dlat
            w = AREA["w"] + j * dlng
            # Overlap each tile slightly so a way crossing a seam is complete in
            # at least one tile and the graph does not come out cut into squares.
            pad_lat, pad_lng = dlat * 0.02, dlng * 0.02
            out.append((f"{i}-{j}",
                        f"{s - pad_lat:.5f},{w - pad_lng:.5f},"
                        f"{s + dlat + pad_lat:.5f},{w + dlng + pad_lng:.5f}"))
    return out


def fetch(name, bbox):
    # `out body` for the ways (we need their node order), then `>` to pull in
    # every node they reference, then `out skel qt` for those nodes' coordinates.
    q = (f'[out:json][timeout:180];'
         f'way["highway"~"^({HIGHWAY})$"]({bbox});'
         f'out body;>;out skel qt;')
    body = ("data=" + urllib.parse.quote(q)).encode()
    last = None
    for attempt in range(6):
        api = APIS[attempt % len(APIS)]
        req = urllib.request.Request(api, data=body, headers={"User-Agent": UA})
        try:
            with urllib.request.urlopen(req, timeout=300) as r:
                return json.load(r)
        except Exception as e:                       # noqa: BLE001 — any failure rests
            last = e
            rest = RETRY_PAUSE * (attempt + 1)
            print(f"  {name}: {e} on {api.split('/')[2]} — resting {rest}s", flush=True)
            time.sleep(rest)
    raise last


def main():
    args = sys.argv[1:]
    force = "--fetch" in args
    n = 3
    if "--tiles" in args:
        n = int(args[args.index("--tiles") + 1])
    cache = ROOT / "cache" / "roads"
    cache.mkdir(parents=True, exist_ok=True)
    todo = [(name, bbox) for name, bbox in tiles(n)
            if force or not (cache / f"{name}.json").exists()]
    if not todo:
        print(f"roads: all {n * n} tiles cached — nothing to fetch (--fetch to refresh)")
        return
    print(f"roads: {len(todo)}/{n * n} tiles to fetch, {PAUSE}s between each — slow on purpose")
    ways = nodes = 0
    for i, (name, bbox) in enumerate(todo):
        data = fetch(name, bbox)
        (cache / f"{name}.json").write_text(json.dumps(data, ensure_ascii=False))
        els = data.get("elements", [])
        w = sum(1 for e in els if e["type"] == "way")
        nd = sum(1 for e in els if e["type"] == "node")
        ways += w
        nodes += nd
        size = (cache / f"{name}.json").stat().st_size / 1e6
        print(f"  tile {name}: {w:,} ways, {nd:,} nodes, {size:.1f} MB", flush=True)
        if i < len(todo) - 1:
            time.sleep(PAUSE)
    print(f"roads: done — {ways:,} way rows, {nodes:,} node rows in cache/roads/")
    print("       next: python3 importers/build_road_graph.py")


if __name__ == "__main__":
    main()
