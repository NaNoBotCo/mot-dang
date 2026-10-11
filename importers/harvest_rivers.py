#!/usr/bin/env python3
"""The rivers, as lines — so a record can say it stands by one.

Nan, 2026-09-10 (search items in order, item 2: "records that carry more"):
riverside is a fact the pin implies, and nothing on this disk held a river
line to imply it from. One Overpass query for waterway=river across the two
provinces' extent (the basemap's own: 97.3,17.0 – 100.6,20.5), kept as
cache/water/rivers.json. ODbL — the credit the site already carries.

    python3 importers/harvest_rivers.py
"""
import json, pathlib, sys, urllib.parse, urllib.request

ROOT = pathlib.Path(__file__).resolve().parent.parent
OUT = ROOT / "cache" / "water" / "rivers.json"
# Four tiles and two mirrors: the whole extent in one query answered 504 on
# the first try. Named rivers only — the name is what the record will carry.
TILES = [(17.0, 97.3, 18.75, 99.0), (17.0, 99.0, 18.75, 100.6), (18.75, 97.3, 20.5, 99.0), (18.75, 99.0, 20.5, 100.6)]
MIRRORS = ["https://overpass-api.de/api/interpreter", "https://overpass.kumi.systems/api/interpreter",
           "https://lz4.overpass-api.de/api/interpreter"]
Q = '[out:json][timeout:180];way["waterway"="river"]["name"](%s,%s,%s,%s);out geom tags;'


def fetch(tile):
    q = Q % tile
    data = urllib.parse.urlencode({"data": q}).encode()
    last = None
    for url in MIRRORS:
        try:
            req = urllib.request.Request(url, data=data, headers={"User-Agent": "motdang-rivers/1.0 (+https://motdang.net)"})
            with urllib.request.urlopen(req, timeout=240) as r:
                return json.loads(r.read().decode("utf-8"))
        except Exception as e:      # a mirror that is busy is not a reason to stop
            last = e
            continue
    raise last


def main():
    ways, seen, stamp = [], set(), ""
    for tile in TILES:
        doc = fetch(tile)
        stamp = doc.get("osm3s", {}).get("timestamp_osm_base", "") or stamp
        for el in doc.get("elements", []):
            if el.get("type") != "way" or not el.get("geometry") or el["id"] in seen:
                continue
            seen.add(el["id"])
            tags = el.get("tags") or {}
            ways.append({"id": el["id"], "name": tags.get("name") or "", "nameEn": tags.get("name:en") or "",
                         "points": [(p["lat"], p["lon"]) for p in el["geometry"]]})
        print(f"  tile {tile}: {len(ways):,} ways so far", flush=True)
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps({"source": "OpenStreetMap via Overpass, ODbL", "query": Q, "tiles": TILES,
                               "fetched": stamp, "ways": ways}, ensure_ascii=False))
    named = sum(1 for w in ways if w["name"])
    print(f"  rivers: {len(ways):,} ways ({named:,} named), {sum(len(w['points']) for w in ways):,} points -> {OUT}")


if __name__ == "__main__":
    sys.exit(main())
