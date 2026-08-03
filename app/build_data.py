#!/usr/bin/env python3
"""Bake the app's offline data pack into app/www/data/.

The phone app draws its own map — every street line and building wall comes
from these files, baked at build time, so the installed app asks no tile
server for anything. Same privacy promise as the site, kept the same way:
by not making the request.

Sources, all already in the repo:
  cache/roads/*.json      — Overpass snapshot, moat + 2 km (crawl_roads.py)
  cache/buildings/*.json  — Overpass snapshot, same extent (fetched once)
  docs/data/toilets.json  + toilets-customers.json — the words we stand behind
  docs/data/{cm,cr}-*.geojson — landmark categories

Everything is emitted as .js files that assign window globals, because the
app loads from file:// inside a WebView, where <script src> works and
fetch() of local files does not.

Coordinates are quantized to 1e-5 degrees (about a metre) relative to the
extent's south-west corner, delta-encoded, so the whole city core packs
small and the APK's own zip does the rest.
"""
import json
import pathlib
import sys

ROOT = pathlib.Path(__file__).resolve().parent.parent
OUT = pathlib.Path(__file__).resolve().parent / "www" / "data"

# Two city cores, one coordinate system. CM matches importers/crawl_roads.py
# (the moat plus ~2 km each way); CR runs from the clock tower district down
# to Central Plaza, because a mall is a toilet anchor. Everything is
# quantized against CM's south-west corner — the shared origin is what lets
# one decoder in the app draw both cities.
AREAS = {
    "cm": {"s": 18.7635, "n": 18.8133, "w": 98.9600, "e": 99.0120,
           "roads": "roads", "buildings": "buildings"},
    "cr": {"s": 19.8620, "n": 19.9320, "w": 99.8000, "e": 99.8600,
           "roads": "roads-cr", "buildings": "buildings-cr"},
}
AREA = AREAS["cm"]  # the origin city
Q = 1e5  # quantum: 1e-5 degrees ≈ 1.1 m

# Landmark categories, in the order they gain labels as you zoom in.
# Toilets are not here — they are the point of the app, drawn above all this.
LANDMARK_CATS = [
    ("wat", "🛕", "วัด", "Temple"),
    ("sights", "📷", "ที่เที่ยว", "Sight"),
    ("museums-galleries", "🏛️", "พิพิธภัณฑ์", "Museum"),
    ("market", "🧺", "ตลาด", "Market"),
    ("parks", "🌳", "สวน", "Park"),
    ("shopping", "🛍️", "ช้อปปิ้ง", "Shopping"),
    ("transport", "🚌", "การเดินทาง", "Transport"),
]

ROAD_CLASSES = [
    # (class name, keys that fall into it)
    ("major", {"primary", "primary_link", "secondary", "secondary_link",
               "trunk", "trunk_link"}),
    ("minor", {"tertiary", "tertiary_link", "residential", "unclassified",
               "living_street"}),
    ("lane", {"service", "track"}),
    ("foot", {"footway", "path", "pedestrian", "steps"}),
]


def qxy(lat, lng):
    return round((lng - AREA["w"]) * Q), round((lat - AREA["s"]) * Q)


def pack_line(coords):
    """[(lat,lng)...] -> [x0, y0, dx1, dy1, ...] quantized ints."""
    out = []
    px = py = None
    for lat, lng in coords:
        x, y = qxy(lat, lng)
        if px is None:
            out += [x, y]
        else:
            if x == px and y == py:
                continue
            out += [x - px, y - py]
        px, py = x, y
    return out


def road_class(tag):
    for i, (_, keys) in enumerate(ROAD_CLASSES):
        if tag in keys:
            return i
    return None


def build_roads():
    """Both cache formats: CM's crawl stored ways + separate node elements;
    the CR fetch used `out geom`, where each way carries its own geometry."""
    roads = []
    for area in AREAS.values():
        ways, nodes = {}, {}
        tiles = sorted((ROOT / "cache" / area["roads"]).glob("*.json"))
        if not tiles:
            sys.exit(f"no cache/{area['roads']}/*.json — fetch them first")
        for tile in tiles:
            d = json.loads(tile.read_text())
            if d.get("remark"):
                sys.exit(f"{tile} carries an Overpass remark — refetch it: "
                         f"{d['remark']}")
            for e in d.get("elements", []):
                if e["type"] == "node":
                    nodes[e["id"]] = (e["lat"], e["lon"])
                elif e["type"] == "way":
                    ways[e["id"]] = e
        for w in ways.values():
            cls = road_class(w.get("tags", {}).get("highway"))
            if cls is None:
                continue
            if "geometry" in w:
                coords = [(g["lat"], g["lon"]) for g in w["geometry"]]
            else:
                coords = [nodes[n] for n in w["nodes"] if n in nodes]
            if len(coords) < 2:
                continue
            name = w["tags"].get("name", "")
            name_en = w["tags"].get("name:en", "")
            roads.append([cls, name, name_en, pack_line(coords)])
    return roads


def building_tiles():
    for area in AREAS.values():
        tiles = sorted((ROOT / "cache" / area["buildings"]).glob("*.json"))
        if not tiles:
            sys.exit(f"no cache/{area['buildings']}/*.json — fetch them first")
        for t in tiles:
            yield t


def build_buildings():
    seen, polys, named = set(), [], []
    for tile in building_tiles():
        d = json.loads(tile.read_text())
        if d.get("remark"):
            sys.exit(f"{tile.name} carries an Overpass remark — refetch it: "
                     f"{d['remark']}")
        for e in d.get("elements", []):
            if e["type"] != "way" or e["id"] in seen or "geometry" not in e:
                continue
            seen.add(e["id"])
            coords = [(g["lat"], g["lon"]) for g in e["geometry"]]
            if len(coords) < 4:
                continue
            packed = pack_line(coords)
            if len(packed) < 8:
                continue  # collapsed below the quantum
            polys.append(packed)
            tags = e.get("tags", {})
            nm = tags.get("name", "")
            if nm:
                clat = sum(c[0] for c in coords) / len(coords)
                clng = sum(c[1] for c in coords) / len(coords)
                x, y = qxy(clat, clng)
                named.append([x, y, nm, tags.get("name:en", "")])
    return polys, named


def build_landmarks():
    cats, items = [], []
    for i, (key, emoji, th, en) in enumerate(LANDMARK_CATS):
        cats.append({"key": key, "emoji": emoji, "th": th, "en": en})
        for prov in ("cm", "cr"):
            p = ROOT / "docs" / "data" / f"{prov}-{key}.geojson"
            if not p.exists():
                continue
            d = json.loads(p.read_text())
            for f in d.get("features", []):
                if f["geometry"]["type"] != "Point":
                    continue
                lng, lat = f["geometry"]["coordinates"]
                pr = f.get("properties", {})
                nm_th = pr.get("nameTh") or pr.get("name") or ""
                nm_en = pr.get("nameEn") or ""
                if not nm_th and not nm_en:
                    continue
                items.append([i, round(lat, 5), round(lng, 5),
                              nm_th, nm_en, pr.get("id") or ""])
    return cats, items


def emit(name, var, obj):
    OUT.mkdir(parents=True, exist_ok=True)
    body = json.dumps(obj, ensure_ascii=False, separators=(",", ":"))
    (OUT / name).write_text(f"window.{var}={body};\n")
    print(f"  {name}: {len(body) / 1e6:.2f} MB")


def main():
    roads = build_roads()
    polys, named = build_buildings()
    print(f"roads: {len(roads)}  buildings: {len(polys)}  named: {len(named)}")
    union = [min(a["s"] for a in AREAS.values()),
             min(a["w"] for a in AREAS.values()),
             max(a["n"] for a in AREAS.values()),
             max(a["e"] for a in AREAS.values())]
    emit("basemap.js", "BASEMAP", {
        "origin": [AREA["s"], AREA["w"]],
        "extent": union,
        "extents": {k: [a["s"], a["w"], a["n"], a["e"]]
                    for k, a in AREAS.items()},
        "q": Q,
        "roadClasses": [c for c, _ in ROAD_CLASSES],
        "roads": roads,
        "buildings": polys,
        "bnames": named,
    })
    cats, items = build_landmarks()
    print(f"landmarks: {len(items)}")
    emit("landmarks.js", "LANDMARKS", {"cats": cats, "items": items})
    toilets = json.loads((ROOT / "docs" / "data" / "toilets.json").read_text())
    customers = json.loads(
        (ROOT / "docs" / "data" / "toilets-customers.json").read_text())
    emit("toilets.js", "TOILETS", toilets)
    emit("toilets-customers.js", "TOILETS_CUSTOMERS", customers)


if __name__ == "__main__":
    main()
