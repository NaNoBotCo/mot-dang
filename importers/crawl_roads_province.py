#!/usr/bin/env python3
"""Every road in Chiang Mai and Chiang Rai provinces, for road distance to the
nearest toilet wherever the reader stands.

crawl_roads.py covers the old city plus ~2 km, which is where plan.html routes.
Toilets are everywhere a person is — a fuel station on the Hang Dong road, a
wat in Mae Rim, the bus terminal in Chiang Rai — so this fetches both provinces
whole, as AREAS (ISO3166-2), cut into bbox tiles so no single answer times
Overpass out. A tile that times out or comes back with a `remark` is split in
four and retried; a remark is never cached, because Overpass reports a timeout
as HTTP 200 with an empty element list and the error hidden in `remark`.

`out body geom` gives each way its node ids (for junctions) and its geometry
in one answer, so no second node lookup.

  python3 -u importers/crawl_roads_province.py            # missing tiles only
  python3 -u importers/crawl_roads_province.py --fetch    # refetch everything

Cache: cache/roads-prov/<ISO>/<tile>.json — build_road_tiles.py reads these.
"""
import json
import sys
import time
import urllib.parse
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
CACHE = ROOT / "cache" / "roads-prov"
APIS = ["https://overpass-api.de/api/interpreter",
        ]  # kumi.systems unreachable 2026-10-02; add mirrors back when they answer
UA = ("mot-dang-directory/1.0 (+https://github.com/NaNoBotCo/mot-dang; "
      "one-off road-network harvest for road distance to toilets)")
PAUSE = 15
RETRY_PAUSE = 40

# Province bounding boxes, generous; the AREA filter does the real cutting.
PROVINCES = {
    "TH-50": {"s": 17.20, "n": 20.20, "w": 98.00, "e": 99.70},   # Chiang Mai
    "TH-57": {"s": 19.00, "n": 20.50, "w": 99.20, "e": 100.70},  # Chiang Rai
}
STEP = 0.1

HIGHWAY = ("motorway|trunk|primary|secondary|tertiary|unclassified|residential|"
           "living_street|service|pedestrian|footway|path|steps|track|cycleway|"
           "motorway_link|trunk_link|primary_link|secondary_link|tertiary_link|"
           "road|corridor")


class Remark(Exception):
    pass


def fetch(iso, bbox, timeout=170):
    # A plain bbox, not the province AREA: the area filter made the public
    # servers 504 on tiles with nothing in them. Roads a few km over a border
    # cost a router nothing; the province rule is for catalogue records.
    q = (f'[out:json][timeout:{timeout}];'
         f'way["highway"~"^({HIGHWAY})$"]({bbox});'
         f'out body geom qt;')
    body = ("data=" + urllib.parse.quote(q)).encode()
    last = None
    for attempt in range(3):
        api = APIS[(attempt + _turn[0]) % len(APIS)]
        req = urllib.request.Request(api, data=body, headers={"User-Agent": UA})
        try:
            with urllib.request.urlopen(req, timeout=timeout + 60) as r:
                d = json.load(r)
            if d.get("remark"):
                raise Remark(d["remark"])
            return d
        except Remark:
            raise
        except Exception as e:                       # noqa: BLE001
            last = e
            rest = RETRY_PAUSE * (attempt + 1)
            if attempt == 2:
                break
            print(f"    {e} on {api.split('/')[2]} — resting {rest}s", flush=True)
            time.sleep(rest)
    _turn[0] += 1
    raise Remark(f"gave up: {last}")


_turn = [0]


def crawl(iso, name, s, w, n, e, force, depth=0):
    out = CACHE / iso / f"{name}.json"
    if out.exists() and not force:
        return
    bbox = f"{s:.4f},{w:.4f},{n:.4f},{e:.4f}"
    try:
        d = fetch(iso, bbox)
    except Remark as r:
        if depth >= 4:
            raise
        print(f"  {iso} {name}: remark ({str(r)[:60]}) — splitting", flush=True)
        ms, mw = (s + n) / 2, (w + e) / 2
        for k, (a, b, c, dd) in enumerate([(s, w, ms, mw), (s, mw, ms, e),
                                           (ms, w, n, mw), (ms, mw, n, e)]):
            crawl(iso, f"{name}.{k}", a, b, c, dd, force, depth + 1)
            time.sleep(PAUSE)
        return
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(d, separators=(",", ":")))
    nw = sum(1 for x in d.get("elements", []) if x["type"] == "way")
    print(f"  {iso} {name}: {nw:,} ways, {out.stat().st_size / 1e6:.1f} MB", flush=True)
    time.sleep(PAUSE)


def order():
    """Every STEP square of both provinces, the ones holding the most toilet
    doors first — so a slow day on the public servers still covers the towns
    before the mountains."""
    weight = {}
    try:
        d = json.loads((ROOT / "docs" / "data" / "toilets.json").read_text())
        pts = [(r[1], r[2]) for r in d["places"]] + [(v[0], v[1]) for v in d["verified"]]
        for la, ln in pts:
            k = (int(la // STEP), int(ln // STEP))
            weight[k] = weight.get(k, 0) + 1
    except (OSError, ValueError, KeyError):
        pass
    sq = []
    for iso, b in PROVINCES.items():
        i0, i1 = int(b["s"] // STEP), int(-(-b["n"] // STEP))
        j0, j1 = int(b["w"] // STEP), int(-(-b["e"] // STEP))
        for i in range(i0, i1):
            for j in range(j0, j1):
                sq.append((-weight.get((i, j), 0), iso, i, j))
    seen, out = set(), []
    for w, iso, i, j in sorted(sq):
        if (i, j) in seen:          # the provinces' boxes overlap
            continue
        seen.add((i, j))
        out.append((iso, i, j, -w))
    return out


def main():
    force = "--fetch" in sys.argv[1:]
    todo = order()
    print(f"{len(todo)} squares, {sum(1 for t in todo if t[3])} with toilets", flush=True)
    for iso, i, j, w in todo:
        crawl(iso, f"{i}_{j}", i * STEP, j * STEP, (i + 1) * STEP, (j + 1) * STEP, force)
    print("done — building the squares", flush=True)
    import subprocess
    subprocess.run([sys.executable, str(ROOT / "importers" / "build_road_tiles.py")], check=False)


if __name__ == "__main__":
    main()
